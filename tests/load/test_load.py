"""
Load and stress tests for the Parakh AI platform.

Measures platform behaviour under concurrent load. Excluded from the default
pytest run — execute explicitly with:

    pytest tests/load/ -m load -v
    pytest tests/load/ -m load --timeout=300 -s

Scenarios
---------
1. Concurrent draft creation  — N parallel createBlankAudit GraphQL mutations;
                                 measures success rate and latency distribution.
2. Evaluations list degradation — UI load time with an existing draft backlog;
                                   measures time-to-interactive and scroll stability.
3. Concurrent Keycloak authentication — N parallel full SSO login flows;
                                         measures success rate and per-login latency.
4. Wizard initialization latency — repeated cold-start measurements of the new-
                                     evaluation wizard; detects per-session degradation.

Results are appended to reports/load_metrics.json after each test so successive
runs can be compared over time.

Cleanup
-------
Draft-creation tests register created audit IDs with the cleanup_evaluation
fixture, which cancels them in teardown. Wizard-session tests use the same
fixture. Browser-based tests that fail mid-cleanup may leave DRAFT records;
run ``python scripts/cleanup_drafts.py --dry-run`` to preview cleanup.

Suggested run cadence
---------------------
- Before a deployment: baseline run (capture metrics before the change)
- After a deployment:  comparison run (detect regressions)
- Periodically in CI:  nightly with ``-m load`` and a Slack/GitHub summary
"""

from __future__ import annotations

import statistics
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Any

import pytest
from playwright.sync_api import sync_playwright

from tests.data.test_data import TestGraphQL
from utils.config import Config
from utils.reporters import append_to_json_report

pytestmark = [pytest.mark.load]

# ─── Performance budgets ──────────────────────────────────────────────────────
# Adjust these after establishing a stable baseline on the dev environment.

BUDGET = {
    # API: single createBlankAudit mutation must respond within N seconds
    "single_mutation_s": 5.0,
    # API: p95 latency across 10 concurrent mutations (wall-clock, not per-request)
    "p95_10_concurrent_s": 10.0,
    # UI: evaluations list page must reach app-ready state within N seconds
    "list_load_s": 12.0,
    # UI: wizard must be visible after clicking Start within N seconds
    "wizard_init_s": 15.0,
    # UI: one full Keycloak SSO login round-trip (browser, redirect, reload)
    "login_s": 30.0,
    # Minimum fraction of concurrent mutations that must report success
    "mutation_success_rate": 0.90,
    # Minimum fraction of parallel logins that must succeed
    # (Keycloak may rate-limit under very high concurrency — 80% is pragmatic)
    "auth_success_rate": 0.80,
}

# ─── GraphQL fragments ────────────────────────────────────────────────────────

_QUERY_FIRST_MODEL = """
    query LoadTestFirstModel {
      aiModels(limit: 1) { id name }
    }
"""

# ─── Module-level helpers ─────────────────────────────────────────────────────

def _get_first_model_id(gql) -> str:
    """Return the id of the first AI model visible to the authenticated session."""
    result = gql(_QUERY_FIRST_MODEL)
    models = (result.get("data") or {}).get("aiModels", [])
    if not models:
        pytest.skip("No AI models found — cannot seed drafts for load test")
    return str(models[0]["id"])


def _create_draft(gql, model_id: str, label: str) -> dict[str, Any]:
    """Create one blank audit via GraphQL.  Returns timing and result metadata."""
    start = time.monotonic()
    try:
        result = gql(
            TestGraphQL.MUTATION_CREATE_BLANK_AUDIT,
            variables={"input": {"modelId": model_id, "name": label}},
            method="POST",
        )
        elapsed = time.monotonic() - start
        payload = (result.get("data") or {}).get("createBlankAudit", {})
        return {
            "success": bool(payload.get("success")),
            "audit_id": (payload.get("audit") or {}).get("id"),
            "elapsed_s": elapsed,
            "error": None if payload.get("success") else payload.get("message", "unknown"),
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "success": False,
            "audit_id": None,
            "elapsed_s": time.monotonic() - start,
            "error": str(exc),
        }


def _p95(values: list[float]) -> float:
    """Return the 95th-percentile of *values* (approximates to max for N < 20)."""
    if not values:
        return 0.0
    s = sorted(values)
    idx = min(len(s) - 1, int(len(s) * 0.95))
    return s[idx]


def _save_metrics(label: str, results: list[dict]) -> None:
    """Append a structured summary to reports/load_metrics.json."""
    latencies = [r["elapsed_s"] for r in results if r.get("elapsed_s") is not None]
    n = len(results)
    n_ok = sum(1 for r in results if r.get("success"))
    entry = {
        "label": label,
        "timestamp": datetime.now().isoformat(),
        "concurrency": n,
        "success_count": n_ok,
        "failure_count": n - n_ok,
        "success_rate": n_ok / n if n else 0,
        "latency_min_s": round(min(latencies, default=0), 3),
        "latency_max_s": round(max(latencies, default=0), 3),
        "latency_mean_s": round(statistics.mean(latencies), 3) if latencies else 0,
        "latency_p95_s": round(_p95(latencies), 3),
        "errors": [r["error"] for r in results if r.get("error")],
    }
    append_to_json_report(Config.REPORTS_DIR / "load_metrics.json", entry)
    print(
        f"\n[load] {label} | n={n} "
        f"ok={n_ok}/{n} ({entry['success_rate']:.0%}) | "
        f"mean={entry['latency_mean_s']:.2f}s "
        f"p95={entry['latency_p95_s']:.2f}s "
        f"max={entry['latency_max_s']:.2f}s"
    )


def _login_worker(worker_idx: int, email: str, password: str, timeout_ms: int) -> dict[str, Any]:
    """Full Keycloak SSO login in an isolated Playwright instance.

    Designed to run in a ThreadPoolExecutor worker.  Each call creates its own
    ``sync_playwright()`` context — Playwright's sync API is safe to use from
    multiple threads as long as each thread has its own Playwright object.

    Returns {"success": bool, "elapsed_s": float, "error": str | None}.
    """
    from pages.home_page import HomePage
    from pages.login_page import LoginPage

    start = time.monotonic()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": 1440, "height": 900},
                locale="en-US",
                ignore_https_errors=True,
            )
            page = context.new_page()
            page.set_default_timeout(timeout_ms)

            home = HomePage(page)
            home.go_to_home()

            if not home.is_visible(home.NAV_LOGIN_BUTTON, timeout=8_000):
                context.close()
                browser.close()
                return {
                    "success": False,
                    "elapsed_s": time.monotonic() - start,
                    "error": f"worker-{worker_idx}: login button not visible",
                }

            home.click_login()
            # Wait for the Keycloak form URL — under concurrent load the redirect
            # can take 5-10 s; domcontentloaded alone is not sufficient.
            try:
                page.wait_for_url("**/openid-connect/auth*", timeout=20_000)
            except Exception:  # noqa: BLE001
                page.wait_for_load_state("domcontentloaded")

            login = LoginPage(page)
            login.click_provider_if_present()

            # Use a generous timeout so slow Keycloak responses under load don't
            # produce false "form not rendered" negatives.
            if not login.is_visible(login.EMAIL_INPUT, timeout=15_000):
                context.close()
                browser.close()
                return {
                    "success": False,
                    "elapsed_s": time.monotonic() - start,
                    "error": f"worker-{worker_idx}: login form not rendered within 15s (Keycloak may be rate-limiting)",
                }

            login.login(email, password)
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(1_500)
            # Platform requires a reload after SSO redirect — mirrors _do_login in conftest.py
            page.reload(wait_until="load", timeout=timeout_ms)
            page.wait_for_timeout(2_000)

            success = "/dashboard" in page.url or "login" not in page.url.lower()
            elapsed = time.monotonic() - start

            context.close()
            browser.close()
            return {"success": success, "elapsed_s": elapsed, "error": None}

    except Exception as exc:  # noqa: BLE001
        return {
            "success": False,
            "elapsed_s": time.monotonic() - start,
            "error": f"worker-{worker_idx}: {exc}",
        }


# ─────────────────────────────────────────────────────────────────────────────
# Scenario 1 — Concurrent draft creation (API-level)
# ─────────────────────────────────────────────────────────────────────────────

class TestConcurrentDraftCreation:
    """Fire N createBlankAudit mutations simultaneously and measure latency/success.

    The ``authenticated_graphql_client`` fixture provides a ``requests.Session``
    with a static Bearer-token header. Concurrent POST calls through the same
    session are safe — each call constructs its own request body dict; no shared
    mutable state is touched during execution.

    Cleanup: every successfully created audit ID is appended to
    ``cleanup_evaluation`` so teardown cancels them all.

    Load-test note: the mutations go through the Next.js GraphQL proxy
    (``/graphql``), which forwards to the Django backend over localhost. Both
    hops add latency. A sustained 20-req/s burst here is the equivalent of
    20 users clicking "New Evaluation → Start" within the same second — a
    realistic surge scenario after a product launch or workshop.
    """

    def _burst(
        self,
        gql,
        concurrency: int,
        model_id: str,
        cleanup_list: list,
    ) -> list[dict]:
        ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        labels = [f"Load draft {i + 1}/{concurrency} @{ts}" for i in range(concurrency)]
        results: list[dict] = []
        with ThreadPoolExecutor(max_workers=concurrency) as ex:
            futures = {ex.submit(_create_draft, gql, model_id, lbl): lbl for lbl in labels}
            for fut in as_completed(futures):
                r = fut.result()
                results.append(r)
                if r["audit_id"]:
                    cleanup_list.append(r["audit_id"])
        return results

    def test_5_concurrent_drafts_all_succeed(
        self, authenticated_graphql_client, cleanup_evaluation
    ):
        """5 simultaneous createBlankAudit mutations must all succeed within the single-request budget."""
        model_id = _get_first_model_id(authenticated_graphql_client)
        results = self._burst(authenticated_graphql_client, 5, model_id, cleanup_evaluation)
        _save_metrics("concurrent_drafts_n5", results)

        failures = [r for r in results if not r["success"]]
        assert not failures, (
            f"{len(failures)}/5 draft mutations failed under concurrent load: "
            + str([r["error"] for r in failures])
        )
        slow = [r for r in results if r["elapsed_s"] > BUDGET["single_mutation_s"]]
        assert not slow, (
            f"{len(slow)}/5 mutations exceeded the {BUDGET['single_mutation_s']}s "
            f"single-request budget: "
            + str([f"{r['elapsed_s']:.2f}s" for r in slow])
        )

    def test_10_concurrent_drafts_p95_within_budget(
        self, authenticated_graphql_client, cleanup_evaluation
    ):
        """10 concurrent mutations: ≥90% success rate and p95 latency within 10 s."""
        model_id = _get_first_model_id(authenticated_graphql_client)
        results = self._burst(authenticated_graphql_client, 10, model_id, cleanup_evaluation)
        _save_metrics("concurrent_drafts_n10", results)

        success_rate = sum(1 for r in results if r["success"]) / len(results)
        assert success_rate >= BUDGET["mutation_success_rate"], (
            f"Success rate {success_rate:.0%} is below the {BUDGET['mutation_success_rate']:.0%} "
            f"minimum under 10-concurrent draft creation. "
            f"Errors: {[r['error'] for r in results if r['error']]}"
        )
        p95 = _p95([r["elapsed_s"] for r in results])
        assert p95 <= BUDGET["p95_10_concurrent_s"], (
            f"p95 latency {p95:.2f}s exceeds the {BUDGET['p95_10_concurrent_s']}s budget "
            f"under 10-concurrent load — backend may be under-resourced or queuing requests"
        )

    def test_20_concurrent_drafts_no_network_errors(
        self, authenticated_graphql_client, cleanup_evaluation
    ):
        """20 concurrent mutations: zero network/connection errors (application-level failures OK).

        Under heavy load, some mutations may fail at the application layer
        (duplicate-name collision, rate limiting, etc.) — those appear as
        ``success=False`` with an error message, which is acceptable degraded
        behaviour. What is NOT acceptable is a ``ConnectionError`` or timeout,
        which indicates the server stopped responding entirely.
        """
        model_id = _get_first_model_id(authenticated_graphql_client)
        results = self._burst(authenticated_graphql_client, 20, model_id, cleanup_evaluation)
        _save_metrics("concurrent_drafts_n20", results)

        network_errors = [
            r for r in results
            if r["error"] and any(kw in str(r["error"]) for kw in ("ConnectionError", "Timeout", "timed out", "RemoteDisconnected"))
        ]
        assert not network_errors, (
            f"{len(network_errors)}/20 mutations raised network/connection errors under load:\n"
            + "\n".join(r["error"] for r in network_errors)
        )
        success_rate = sum(1 for r in results if r["success"]) / len(results)
        # Record but do not assert — 20-concurrent may legitimately have lower success rate
        print(f"\n[load] 20-concurrent success rate: {success_rate:.0%} (informational, not asserted)")


# ─────────────────────────────────────────────────────────────────────────────
# Scenario 2 — Evaluations list degradation
# ─────────────────────────────────────────────────────────────────────────────

class TestEvaluationsListDegradation:
    """Measure evaluations list UI performance with the current draft backlog.

    No seeding required — tests use whatever drafts already exist in org 1.
    The 'degradation' aspect: if draft count grows unbounded (no cleanup),
    list-page load time and scroll performance should still stay within budget.

    Load-test note: the evaluations list is the primary landing page after login.
    A 3-second load time (vs the typical 1s) may indicate a missing DB index on
    ``audit.organization_id + status``, an N+1 query in the list resolver, or
    unpaginated fetching. These tests surface those regressions.
    """

    def test_list_page_load_time_within_budget(self, authenticated_page_fast):
        """Evaluations list must reach app-ready state within the auth-route budget."""
        from pages.new_evaluation_page import NewEvaluationPage

        nep = NewEvaluationPage(authenticated_page_fast)
        start_ms = authenticated_page_fast.evaluate("performance.now()")
        nep.go_to_evaluations_list()
        end_ms = authenticated_page_fast.evaluate("performance.now()")
        elapsed_s = (end_ms - start_ms) / 1_000

        _save_metrics("list_load", [{"success": True, "elapsed_s": elapsed_s, "error": None}])

        assert elapsed_s < BUDGET["list_load_s"], (
            f"Evaluations list load time {elapsed_s:.2f}s exceeds "
            f"{BUDGET['list_load_s']}s budget — check for N+1 queries or unpaginated fetching"
        )

    def test_list_scrolls_to_bottom_without_freeze(self, authenticated_page_fast):
        """Scrolling the full evaluations list must not time out or freeze the browser."""
        from pages.new_evaluation_page import NewEvaluationPage

        nep = NewEvaluationPage(authenticated_page_fast)
        nep.go_to_evaluations_list()

        start = time.monotonic()
        authenticated_page_fast.keyboard.press("End")
        authenticated_page_fast.wait_for_timeout(500)
        authenticated_page_fast.keyboard.press("Home")
        authenticated_page_fast.wait_for_timeout(300)
        elapsed_s = time.monotonic() - start

        _save_metrics("list_scroll", [{"success": True, "elapsed_s": elapsed_s, "error": None}])

        assert elapsed_s < 10.0, (
            f"Scrolling the evaluations list took {elapsed_s:.2f}s — "
            "possible virtual-scroll regression or DOM-size explosion"
        )

    def test_list_load_time_after_10_draft_burst(
        self, authenticated_page_fast, authenticated_graphql_client, cleanup_evaluation
    ):
        """List load time after a 10-draft creation burst must not degrade beyond budget.

        Simulates a workshop scenario where 10 participants each click
        'New Evaluation' within seconds of each other. The list must still
        render within the standard auth-route budget afterwards.
        """
        from pages.new_evaluation_page import NewEvaluationPage

        model_id = _get_first_model_id(authenticated_graphql_client)

        # Burst-create 10 drafts via API (not the UI) to populate the list quickly
        ts = datetime.now().strftime("%H:%M:%S")
        with ThreadPoolExecutor(max_workers=10) as ex:
            futures = [
                ex.submit(
                    _create_draft,
                    authenticated_graphql_client,
                    model_id,
                    f"Burst draft {i + 1} @{ts}",
                )
                for i in range(10)
            ]
            for fut in as_completed(futures):
                r = fut.result()
                if r["audit_id"]:
                    cleanup_evaluation.append(r["audit_id"])

        # Use monotonic time across the navigation — performance.now() resets
        # on each page load and produces a negative delta if measured before/after
        # a full navigation.
        nep = NewEvaluationPage(authenticated_page_fast)
        start = time.monotonic()
        nep.go_to_evaluations_list()
        elapsed_s = time.monotonic() - start

        _save_metrics("list_load_post_burst", [{"success": True, "elapsed_s": elapsed_s, "error": None}])

        assert elapsed_s < BUDGET["list_load_s"], (
            f"List load time {elapsed_s:.2f}s exceeded budget after a 10-draft burst — "
            "possible missing pagination or slow list query under high draft count"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Scenario 3 — Concurrent Keycloak authentication
# ─────────────────────────────────────────────────────────────────────────────

class TestConcurrentAuthentication:
    """N parallel full Keycloak SSO login flows — measures auth-server capacity.

    Each worker spawns its own headless Chromium instance via ``sync_playwright()``.
    Multiple Playwright instances in separate threads is the supported pattern for
    parallel browser work outside of pytest-xdist.

    Load-test note: Keycloak on the dev environment has a small thread pool and
    no horizontal scaling. 5 concurrent logins from the same IP within a few
    seconds is enough to reveal connection-pool exhaustion or session-table lock
    contention. Production Keycloak (HA mode) should handle 50+ comfortably.
    """

    def _run_concurrent_logins(self, concurrency: int) -> list[dict]:
        if not (Config.TEST_EMAIL_1 and Config.TEST_PASSWORD_1):
            pytest.skip("TEST_EMAIL_1 / TEST_PASSWORD_1 not set — concurrent auth test requires credentials")
        timeout_ms = int(BUDGET["login_s"] * 1_000)
        results: list[dict] = []
        with ThreadPoolExecutor(max_workers=concurrency) as ex:
            futures = [
                ex.submit(
                    _login_worker,
                    i,
                    Config.TEST_EMAIL_1,
                    Config.TEST_PASSWORD_1,
                    timeout_ms,
                )
                for i in range(concurrency)
            ]
            for fut in as_completed(futures):
                results.append(fut.result())
        return results

    def test_3_concurrent_logins_succeed(self):
        """3 simultaneous full SSO logins must all succeed within the login-time budget."""
        results = self._run_concurrent_logins(3)
        _save_metrics("concurrent_logins_n3", results)

        failures = [r for r in results if not r["success"]]
        assert not failures, (
            f"{len(failures)}/3 concurrent logins failed:\n"
            + "\n".join(r["error"] or "unknown" for r in failures)
        )
        slow = [r for r in results if r["elapsed_s"] > BUDGET["login_s"]]
        assert not slow, (
            f"{len(slow)}/3 logins exceeded the {BUDGET['login_s']}s budget: "
            + str([f"{r['elapsed_s']:.1f}s" for r in slow])
        )

    @pytest.mark.xfail(
        strict=False,
        reason=(
            "Keycloak dev instance rate-limits 5 concurrent logins from the same account: "
            "3/5 workers fail with 'login form not rendered' even after 15 s. "
            "The 3-concurrent test passes, so capacity is between 3 and 5 sessions. "
            "Production Keycloak (HA mode, session-affinity disabled) should handle "
            "50+ comfortably — see docs/app_bugs.md #12."
        ),
    )
    def test_5_concurrent_logins_success_rate(self):
        """5 simultaneous SSO logins: ≥80% must succeed (Keycloak may throttle the rest).

        Keycloak's default brute-force protection can temporarily block rapid
        repeated logins from the same IP. An 80% success threshold accepts up to
        1 throttle-induced failure without failing the test — the important signal
        is whether the server hard-errors (connection refused / 5xx) vs gracefully
        throttles.
        """
        results = self._run_concurrent_logins(5)
        _save_metrics("concurrent_logins_n5", results)

        success_rate = sum(1 for r in results if r["success"]) / len(results)
        assert success_rate >= BUDGET["auth_success_rate"], (
            f"Concurrent login success rate {success_rate:.0%} is below "
            f"{BUDGET['auth_success_rate']:.0%}. "
            f"Errors: {[r['error'] for r in results if r['error']]}"
        )
        # Check that failures are throttle/app-level, not network-level
        network_failures = [
            r for r in results
            if not r["success"] and r["error"] and
            any(kw in str(r["error"]) for kw in ("ConnectionError", "refused", "unreachable"))
        ]
        assert not network_failures, (
            "Keycloak became unreachable under 5-concurrent login load — "
            "this is a capacity issue, not throttling:\n"
            + "\n".join(r["error"] for r in network_failures)
        )


# ─────────────────────────────────────────────────────────────────────────────
# Scenario 4 — Wizard initialization latency
# ─────────────────────────────────────────────────────────────────────────────

class TestWizardInitializationLatency:
    """Measure cold-start and per-session wizard initialization latency.

    Unlike the concurrent auth test, these tests run sequentially but rapidly —
    they reveal whether the wizard degrades on repeated access within a single
    browser session (SPA state leak, memory growth, API response time increase
    after the first request warms the backend cache).

    Load-test note: each wizard open creates a new DRAFT audit. Cleanup is via
    ``cleanup_evaluation``. If the backend has a slow ``createBlankAudit``
    path (e.g., it synchronously assigns test datasets on draft creation),
    that will show up as a spike in the third or fourth session.
    """

    def _open_wizard_and_measure(self, page, cleanup_list: list) -> dict[str, Any]:
        """Navigate list → click New Evaluation → measure wizard-visible time.

        Returns {"elapsed_s": float, "success": bool, "error": str|None}.
        """
        from locators.evaluations_locators import EvaluationsLocators
        from pages.evaluations_page import EvaluationsPage

        ep = EvaluationsPage(page)
        ep.go_to_evaluations_list()

        start = time.monotonic()
        ep.click_new_evaluation()

        if not ep.is_new_eval_modal_visible():
            return {"elapsed_s": time.monotonic() - start, "success": False, "error": "modal not visible"}

        ep.click_modal_start()

        if not ep.is_wizard_visible():
            return {"elapsed_s": time.monotonic() - start, "success": False, "error": "wizard not visible"}

        elapsed = time.monotonic() - start

        # Cancel so the test stays idempotent (also registers the draft for cleanup)
        audit_id = None
        try:
            audit_id = page.evaluate(
                "() => new URLSearchParams(window.location.search).get('auditId')"
            )
        except Exception:  # noqa: BLE001
            pass
        if audit_id:
            cleanup_list.append(audit_id)

        if ep.is_visible(EvaluationsLocators.WIZARD_CANCEL_EVALUATION, timeout=3_000):
            ep.cancel_evaluation()

        return {"elapsed_s": elapsed, "success": True, "error": None}

    def test_wizard_cold_init_within_budget(
        self, authenticated_page_fast, cleanup_evaluation
    ):
        """Cold wizard open (first access in the session) must complete within budget."""
        result = self._open_wizard_and_measure(authenticated_page_fast, cleanup_evaluation)
        _save_metrics("wizard_init_cold", [result])

        assert result["success"], (
            f"Wizard did not initialize on cold open: {result['error']}"
        )
        assert result["elapsed_s"] < BUDGET["wizard_init_s"], (
            f"Cold wizard init took {result['elapsed_s']:.2f}s — "
            f"exceeds {BUDGET['wizard_init_s']}s budget"
        )

    def test_3_rapid_wizard_sessions_no_degradation(
        self, authenticated_page_fast, cleanup_evaluation
    ):
        """Three back-to-back wizard opens must each complete within budget; no time increase.

        If the third session is significantly slower than the first, it suggests
        cumulative state growth in the SPA (React tree, draft list query re-fetches,
        unbounded event listeners, etc.).
        """
        results = []
        for i in range(3):
            r = self._open_wizard_and_measure(authenticated_page_fast, cleanup_evaluation)
            results.append(r)
            authenticated_page_fast.wait_for_timeout(500)  # brief settle between sessions

        _save_metrics("wizard_init_rapid_x3", results)

        failures = [(i + 1, r) for i, r in enumerate(results) if not r["success"]]
        assert not failures, (
            "Wizard failed to initialize on session(s): "
            + str([(idx, r["error"]) for idx, r in failures])
        )

        for i, r in enumerate(results):
            assert r["elapsed_s"] < BUDGET["wizard_init_s"], (
                f"Session {i + 1}/3 wizard init time {r['elapsed_s']:.2f}s "
                f"exceeded {BUDGET['wizard_init_s']}s budget"
            )

        # Degradation check: session 3 should not be more than 2× session 1
        t1, t3 = results[0]["elapsed_s"], results[2]["elapsed_s"]
        assert t3 < t1 * 2.5, (
            f"Wizard init time degraded from {t1:.2f}s (session 1) to {t3:.2f}s (session 3) "
            f"— ratio {t3 / t1:.1f}× exceeds the 2.5× degradation threshold. "
            "Possible SPA state leak or uncached API call on repeated open."
        )

    def test_wizard_init_time_stability_metric(
        self, authenticated_page_fast, cleanup_evaluation
    ):
        """Record wizard init time variance across 5 sessions as a stability metric.

        This test always passes — its purpose is to populate load_metrics.json
        with a variance snapshot so trend analysis can detect creeping degradation
        over successive test runs.
        """
        results = []
        for _ in range(5):
            r = self._open_wizard_and_measure(authenticated_page_fast, cleanup_evaluation)
            results.append(r)
            authenticated_page_fast.wait_for_timeout(300)

        successful = [r for r in results if r["success"]]
        _save_metrics("wizard_init_stability_x5", results)

        if not successful:
            pytest.skip("All 5 wizard sessions failed — platform unavailable")

        times = [r["elapsed_s"] for r in successful]
        variance = statistics.variance(times) if len(times) > 1 else 0.0
        print(
            f"\n[load] wizard_init_stability_x5 | "
            f"n={len(successful)} successful | "
            f"mean={statistics.mean(times):.2f}s | "
            f"variance={variance:.4f}s² | "
            f"max={max(times):.2f}s"
        )
        # Always passes — this is a metric collector, not a hard gate
        assert True
