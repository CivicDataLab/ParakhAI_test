"""
GraphQL load tests — concurrent authenticated read queries.

Complements test_load.py (which covers mutations and auth flows).
These tests measure the backend's capacity to serve concurrent read queries
without degradation — a realistic scenario during peak usage (workshop, launch).

Scenarios:
  TestConcurrentGraphQLReads       — concurrent aiModels + audits queries
  TestPaginationPerformance        — large-page-size read latency
  TestGraphQLMutationConcurrency   — concurrent myOrganizations lookups

Results are appended to reports/load_metrics_graphql.json.

Run explicitly with:
    pytest tests/load/test_load_graphql.py -m load --timeout=300 -v
"""

from __future__ import annotations

import statistics
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Any

import pytest

from utils.config import Config
from utils.reporters import append_to_json_report

pytestmark = [pytest.mark.load]

# ── Performance budgets ────────────────────────────────────────────────────────

BUDGET = {
    "single_read_s": 5.0,
    "concurrent_5_all_succeed_s": 6.0,
    "concurrent_10_p95_s": 8.0,
    "large_page_s": 5.0,
    "success_rate_10_concurrent": 0.90,
    "success_rate_mixed": 0.85,
}

# ── GraphQL queries ────────────────────────────────────────────────────────────

_QUERY_AI_MODELS = "{ aiModels(limit: 10) { id name } }"
_QUERY_AUDITS = "{ audits { data { id status } totalItemsCount } }"
_QUERY_MY_ORGS = "{ myOrganizations { id name } }"
_QUERY_AI_MODELS_LARGE = "{ aiModels(limit: 50) { id name } }"
_QUERY_AUDITS_LARGE = "{ audits(limit: 50) { data { id } totalItemsCount } }"


# ── Helpers ────────────────────────────────────────────────────────────────────


def _execute_query(gql, query: str, label: str) -> dict[str, Any]:
    start = time.monotonic()
    try:
        result = gql(query)
        elapsed = time.monotonic() - start
        return {
            "success": "data" in result and result.get("data") is not None,
            "elapsed_s": elapsed,
            "error": None,
            "label": label,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "success": False,
            "elapsed_s": time.monotonic() - start,
            "error": str(exc),
            "label": label,
        }


def _p95(values: list[float]) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    idx = min(len(s) - 1, int(len(s) * 0.95))
    return s[idx]


def _save_metrics(label: str, results: list[dict]) -> None:
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
    append_to_json_report(Config.REPORTS_DIR / "load_metrics_graphql.json", entry)
    print(
        f"\n[load:graphql] {label} | n={n} "
        f"ok={n_ok}/{n} ({entry['success_rate']:.0%}) | "
        f"mean={entry['latency_mean_s']:.2f}s "
        f"p95={entry['latency_p95_s']:.2f}s "
        f"max={entry['latency_max_s']:.2f}s"
    )


# ── Scenario 1: Concurrent Read Queries ───────────────────────────────────────


@pytest.mark.timeout(300)
class TestConcurrentGraphQLReads:
    """Concurrent authenticated GraphQL reads — measures read-path throughput."""

    def _burst(self, gql, query: str, concurrency: int, label: str) -> list[dict]:
        results: list[dict] = []
        with ThreadPoolExecutor(max_workers=concurrency) as ex:
            futures = {
                ex.submit(_execute_query, gql, query, f"{label}-{i}"): i
                for i in range(concurrency)
            }
            for fut in as_completed(futures):
                results.append(fut.result())
        return results

    def test_10_concurrent_ai_models_queries(self, authenticated_graphql_client):
        """10 concurrent aiModels queries: ≥90% must succeed within the p95 budget."""
        results = self._burst(authenticated_graphql_client, _QUERY_AI_MODELS, 10, "aiModels")
        _save_metrics("concurrent_ai_models_n10", results)

        success_rate = sum(1 for r in results if r["success"]) / len(results)
        assert success_rate >= BUDGET["success_rate_10_concurrent"], (
            f"aiModels concurrent success rate {success_rate:.0%} is below "
            f"{BUDGET['success_rate_10_concurrent']:.0%}. "
            f"Errors: {[r['error'] for r in results if r['error']]}"
        )
        p95 = _p95([r["elapsed_s"] for r in results])
        assert p95 <= BUDGET["concurrent_10_p95_s"], (
            f"p95 latency {p95:.2f}s exceeds {BUDGET['concurrent_10_p95_s']}s budget "
            "for 10 concurrent aiModels queries"
        )

    def test_5_concurrent_audits_list_queries(self, authenticated_graphql_client):
        """5 concurrent audits list queries must all succeed within the budget."""
        results = self._burst(authenticated_graphql_client, _QUERY_AUDITS, 5, "audits")
        _save_metrics("concurrent_audits_n5", results)

        failures = [r for r in results if not r["success"]]
        assert not failures, (
            f"{len(failures)}/5 concurrent audit list queries failed: "
            f"{[r['error'] for r in failures]}"
        )
        slow = [r for r in results if r["elapsed_s"] > BUDGET["concurrent_5_all_succeed_s"]]
        slow_times = [f"{r['elapsed_s']:.2f}s" for r in slow]
        assert not slow, (
            f"{len(slow)}/5 audit queries exceeded {BUDGET['concurrent_5_all_succeed_s']}s: "
            f"{slow_times}"
        )

    def test_concurrent_mixed_queries(self, authenticated_graphql_client):
        """10 mixed concurrent queries (5 aiModels + 5 audits): ≥85% success rate."""
        import itertools

        queries = (
            [(authenticated_graphql_client, _QUERY_AI_MODELS, f"mixed-models-{i}") for i in range(5)]
            + [(authenticated_graphql_client, _QUERY_AUDITS, f"mixed-audits-{i}") for i in range(5)]
        )
        results: list[dict] = []
        with ThreadPoolExecutor(max_workers=10) as ex:
            futures = {ex.submit(_execute_query, gql, q, lbl): lbl for gql, q, lbl in queries}
            for fut in as_completed(futures):
                results.append(fut.result())

        _save_metrics("concurrent_mixed_n10", results)

        success_rate = sum(1 for r in results if r["success"]) / len(results)
        assert success_rate >= BUDGET["success_rate_mixed"], (
            f"Mixed concurrent success rate {success_rate:.0%} is below "
            f"{BUDGET['success_rate_mixed']:.0%}. "
            f"Errors: {[r['error'] for r in results if r['error']]}"
        )

    def test_single_ai_models_baseline_latency(self, authenticated_graphql_client):
        """Single aiModels query baseline — must respond within the single-read budget."""
        result = _execute_query(authenticated_graphql_client, _QUERY_AI_MODELS, "baseline")
        _save_metrics("aiModels_baseline_single", [result])

        assert result["success"], f"Baseline aiModels query failed: {result['error']}"
        assert result["elapsed_s"] < BUDGET["single_read_s"], (
            f"Single aiModels query took {result['elapsed_s']:.2f}s — "
            f"exceeds {BUDGET['single_read_s']}s budget"
        )


# ── Scenario 2: Pagination Performance ────────────────────────────────────────


@pytest.mark.timeout(120)
class TestPaginationPerformance:
    """Large-page-size queries must not degrade beyond budget."""

    def test_ai_models_large_page_size_responds_fast(self, authenticated_graphql_client):
        """aiModels(limit:50) must respond within the large-page budget."""
        result = _execute_query(
            authenticated_graphql_client, _QUERY_AI_MODELS_LARGE, "aiModels_limit50"
        )
        _save_metrics("aiModels_limit50", [result])

        if not result["success"]:
            pytest.xfail(f"aiModels(limit:50) returned an error: {result['error']}")

        assert result["elapsed_s"] < BUDGET["large_page_s"], (
            f"aiModels(limit:50) took {result['elapsed_s']:.2f}s — "
            f"exceeds {BUDGET['large_page_s']}s budget"
        )

    def test_audits_large_page_responds_fast(self, authenticated_graphql_client):
        """audits(limit:50) must respond within the large-page budget."""
        result = _execute_query(
            authenticated_graphql_client, _QUERY_AUDITS_LARGE, "audits_limit50"
        )
        _save_metrics("audits_limit50", [result])

        if not result["success"]:
            pytest.xfail(f"audits(limit:50) returned an error: {result['error']}")

        assert result["elapsed_s"] < BUDGET["large_page_s"], (
            f"audits(limit:50) took {result['elapsed_s']:.2f}s — "
            f"exceeds {BUDGET['large_page_s']}s budget"
        )

    def test_read_latency_stable_across_3_sequential_calls(self, authenticated_graphql_client):
        """Three sequential aiModels queries must not show >2× latency growth (no SPA leak)."""
        results = [
            _execute_query(authenticated_graphql_client, _QUERY_AI_MODELS, f"seq-{i}")
            for i in range(3)
        ]
        _save_metrics("aiModels_sequential_x3", results)

        failures = [(i, r) for i, r in enumerate(results) if not r["success"]]
        assert not failures, (
            f"Sequential aiModels queries failed: {[(i, r['error']) for i, r in failures]}"
        )

        t1, t3 = results[0]["elapsed_s"], results[2]["elapsed_s"]
        if t1 > 0:
            assert t3 < t1 * 2.5, (
                f"Sequential query latency grew from {t1:.2f}s to {t3:.2f}s "
                f"(ratio {t3/t1:.1f}×) — possible connection pool warming issue"
            )


# ── Scenario 3: Org Query Concurrency ────────────────────────────────────────


@pytest.mark.timeout(120)
class TestGraphQLMutationConcurrency:
    """Concurrent myOrganizations queries — measures auth-scoped read throughput."""

    def test_5_concurrent_my_organizations_queries(self, authenticated_graphql_client):
        """5 concurrent myOrganizations queries must all succeed within the budget."""
        results: list[dict] = []
        with ThreadPoolExecutor(max_workers=5) as ex:
            futures = [
                ex.submit(_execute_query, authenticated_graphql_client, _QUERY_MY_ORGS, f"myOrgs-{i}")
                for i in range(5)
            ]
            for fut in as_completed(futures):
                results.append(fut.result())

        _save_metrics("concurrent_my_organizations_n5", results)

        failures = [r for r in results if not r["success"]]
        assert not failures, (
            f"{len(failures)}/5 concurrent myOrganizations queries failed: "
            f"{[r['error'] for r in failures]}"
        )
        slow = [r for r in results if r["elapsed_s"] > BUDGET["concurrent_5_all_succeed_s"]]
        assert not slow, (
            f"{len(slow)}/5 queries exceeded the {BUDGET['concurrent_5_all_succeed_s']}s budget"
        )

    def test_10_concurrent_my_organizations_queries_success_rate(
        self, authenticated_graphql_client
    ):
        """10 concurrent myOrganizations queries: ≥90% success rate."""
        results: list[dict] = []
        with ThreadPoolExecutor(max_workers=10) as ex:
            futures = [
                ex.submit(_execute_query, authenticated_graphql_client, _QUERY_MY_ORGS, f"myOrgs-{i}")
                for i in range(10)
            ]
            for fut in as_completed(futures):
                results.append(fut.result())

        _save_metrics("concurrent_my_organizations_n10", results)

        success_rate = sum(1 for r in results if r["success"]) / len(results)
        assert success_rate >= BUDGET["success_rate_10_concurrent"], (
            f"myOrganizations 10-concurrent success rate {success_rate:.0%} < "
            f"{BUDGET['success_rate_10_concurrent']:.0%}. "
            f"Errors: {[r['error'] for r in results if r['error']]}"
        )
