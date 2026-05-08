"""
Shared pytest fixtures for the Parakh test framework.

Fixture scopes:
  session  — created once per pytest run (browser launch args, API session)
  function — created/torn-down for every test (page, browser context)

Authenticated fixtures:
  authenticated_page    — page already logged in as the active test user (USER_1)
  authenticated_page_u2 — page logged in as the secondary test user (USER_2)
"""

import pytest
import requests
from playwright.sync_api import Browser, BrowserContext, Page

from pages.home_page import HomePage
from pages.login_page import LoginPage
from utils.config import Config
from utils.helpers import take_screenshot

# ── Base URL ──────────────────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def base_url() -> str:
    return Config.BASE_URL


# ── Browser launch args ───────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def browser_type_launch_args():
    """Override pytest-playwright defaults with values from Config / .env."""
    return {
        "headless": Config.HEADLESS,
        "slow_mo": Config.SLOW_MO,
    }


# ── Browser context (desktop) ─────────────────────────────────────────────────


@pytest.fixture(scope="function")
def browser_context(browser: Browser) -> BrowserContext:
    """Fresh desktop browser context per test (1440×900, en-US locale)."""
    context = browser.new_context(
        viewport={
            "width": Config.VIEWPORT_WIDTH,
            "height": Config.VIEWPORT_HEIGHT,
        },
        ignore_https_errors=True,
        java_script_enabled=True,
        locale="en-US",
    )
    context.set_default_timeout(Config.TIMEOUT)
    yield context
    context.close()


# ── Page (desktop) ────────────────────────────────────────────────────────────


@pytest.fixture(scope="function")
def page(browser_context: BrowserContext, request) -> Page:
    """
    New page per test.

    On failure:
      - Captures a full-page PNG screenshot.
      - Appends the file path to request.node.user_properties so that
        pytest-json-report includes it in the JSON output automatically.
    """
    pg = browser_context.new_page()
    pg.set_default_timeout(Config.TIMEOUT)

    # Auto-accept native browser dialogs (window.confirm / window.alert / prompt).
    # The wizard's "Cancel Evaluation" button calls window.confirm — without this
    # handler Playwright auto-DISMISSES (returns false), the cancel never fires,
    # and any test that relies on cancellation hangs waiting for URL change.
    pg.on("dialog", lambda dialog: dialog.accept())

    yield pg

    if Config.SCREENSHOT_ON_FAILURE and getattr(request.node, "rep_call", None) is not None:
        if request.node.rep_call.failed:
            path = take_screenshot(pg, f"FAIL_{request.node.name}")
            request.node.user_properties.append(("screenshot", str(path)))

    pg.close()


# ── Mobile / Tablet pages ─────────────────────────────────────────────────────


@pytest.fixture(scope="function")
def mobile_page(browser: Browser) -> Page:
    """Page with a 390×844 viewport emulating iPhone 14 Pro."""
    context = browser.new_context(
        viewport={"width": 390, "height": 844},
        user_agent=(
            "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) "
            "Version/16.0 Mobile/15E148 Safari/604.1"
        ),
        ignore_https_errors=True,
    )
    context.set_default_timeout(Config.TIMEOUT)
    pg = context.new_page()
    yield pg
    context.close()


@pytest.fixture(scope="function")
def tablet_page(browser: Browser) -> Page:
    """Page with a 768×1024 viewport emulating an iPad."""
    context = browser.new_context(
        viewport={"width": 768, "height": 1024},
        ignore_https_errors=True,
    )
    context.set_default_timeout(Config.TIMEOUT)
    pg = context.new_page()
    yield pg
    context.close()


# ── Authenticated pages ───────────────────────────────────────────────────────


def _do_login(page: Page, email: str, password: str) -> None:
    """
    Navigate to the homepage, click Login, and complete the Keycloak SSO form.
    Skips the test gracefully if the login UI is not reachable.
    """
    home = HomePage(page)
    home.go_to_home()

    if not home.is_visible(home.NAV_LOGIN_BUTTON, timeout=8_000):
        pytest.skip("Login button not visible — cannot create authenticated session")

    home.click_login()
    page.wait_for_load_state("domcontentloaded")

    login = LoginPage(page)
    # Some flows route through a provider-selection page before the Keycloak form.
    login.click_provider_if_present()
    if not login.is_email_field_visible():
        pytest.skip("Login form not rendered — cannot create authenticated session")

    login.login(email, password)
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(1_500)  # allow SSO redirect / cookie set to settle

    # TODO: TEMP — platform requires a reload after SSO redirect to render
    # correctly. Use 'load' — app has background polling that prevents networkidle.
    # Remove once fixed.
    page.reload(wait_until="load", timeout=Config.TIMEOUT)
    page.wait_for_timeout(2_000)


def _make_auth_page(
    browser_context: BrowserContext,
    request,
    email: str,
    password: str,
    label: str,
) -> Page:
    """Shared factory used by both authenticated_page fixtures."""
    pg = browser_context.new_page()
    pg.set_default_timeout(Config.TIMEOUT)
    # Auto-accept native dialogs — see comment in `page` fixture above for why.
    pg.on("dialog", lambda dialog: dialog.accept())
    _do_login(pg, email, password)

    yield pg

    if Config.SCREENSHOT_ON_FAILURE and getattr(request.node, "rep_call", None) is not None:
        if request.node.rep_call.failed:
            path = take_screenshot(pg, f"FAIL_{label}_{request.node.name}")
            request.node.user_properties.append(("screenshot", str(path)))

    pg.close()


@pytest.fixture(scope="function")
def authenticated_page(browser_context: BrowserContext, request) -> Page:
    """
    Desktop page pre-authenticated as TEST_USER_1 (slot 1).

    The test is skipped automatically if credentials are not configured.
    """
    user = Config.active_test_user()
    if not user["email"] or user["email"].endswith("@example.com"):
        pytest.skip(
            "TEST_EMAIL_1 / TEST_PASSWORD_1 not configured — "
            "set them in .env to run authenticated tests."
        )
    yield from _make_auth_page(browser_context, request, user["email"], user["password"], "AUTH")


@pytest.fixture(scope="function")
def authenticated_page_u2(browser_context: BrowserContext, request) -> Page:
    """
    Desktop page pre-authenticated as TEST_USER_2 (slot 2).

    Use for multi-user / parallel scenarios where both accounts must be
    active simultaneously.
    """
    if not Config.TEST_EMAIL_2 or Config.TEST_EMAIL_2.endswith("@example.com"):
        pytest.skip(
            "TEST_EMAIL_2 / TEST_PASSWORD_2 not configured — "
            "set them in .env to run secondary-user tests."
        )
    yield from _make_auth_page(
        browser_context, request, Config.TEST_EMAIL_2, Config.TEST_PASSWORD_2, "AUTH_U2"
    )


# ── API client ────────────────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def api_client() -> requests.Session:
    """
    Pre-configured requests.Session shared across all API tests.

    Redirects are followed by default (max_redirects=5). Tests that need to
    inspect raw redirect responses should pass allow_redirects=False at the
    call site — this short-circuits before max_redirects is consulted and
    returns the 3xx response directly with no exception.
    """
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "ParakhTestFramework/1.0",
            "Accept": "text/html,application/json,*/*",
        }
    )
    session.max_redirects = 5
    yield session
    session.close()


# ── GraphQL client ────────────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def graphql_client(api_client):
    """
    Session-scoped callable for GraphQL requests.

    Usage::
        def test_something(graphql_client):
            data = graphql_client("{ hello }")
            data = graphql_client(QUERY, variables={"limit": 5}, token="Bearer ...")
    """
    import json as _json

    from utils.config import Config

    def _call(query: str, variables=None, token: str = None) -> dict:
        # Strawberry GraphQL on this platform requires GET with Accept: application/json.
        # POST requests are rejected by CSRF protection.
        headers = {"Accept": "application/json"}
        if token:
            headers["Authorization"] = token
        params: dict = {"query": query}
        if variables:
            params["variables"] = _json.dumps(variables)
        resp = api_client.get(
            Config.graphql_endpoint(),
            params=params,
            headers=headers,
            timeout=20,
        )
        assert resp.status_code == 200, (
            f"GraphQL returned {resp.status_code}: {resp.text[:300]}"
        )
        return resp.json()

    return _call


# ── Sandbox org guards ────────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def sandbox_org() -> str:
    """Return the sandbox org slug; skip the test when unset.

    All write-marked regression tests reach for this fixture so they
    auto-skip cleanly outside CI runs that have configured the secret.
    """
    if not Config.SANDBOX_ORG_SLUG:
        pytest.skip(
            "SANDBOX_ORG_SLUG not configured — write-side regression tests "
            "skip to avoid mutating real production org data."
        )
    return Config.SANDBOX_ORG_SLUG


@pytest.fixture(autouse=True)
def forbid_outside_sandbox(request):
    """Autouse guard for `regression_write` tests.

    Aborts a test before any action runs if SANDBOX_ORG_SLUG is unset.
    Read-only tests (no `regression_write` marker) are unaffected.
    """
    if request.node.get_closest_marker("regression_write") is None:
        return
    if not Config.SANDBOX_ORG_SLUG:
        pytest.skip(
            "SANDBOX_ORG_SLUG not set — `regression_write` test skipped to "
            "prevent unintended writes against a non-sandbox org."
        )


# ── Authenticated session caching (storage_state) ─────────────────────────────


@pytest.fixture(scope="session")
def authenticated_storage_state(browser: Browser, tmp_path_factory) -> str:
    """Run Keycloak login once and cache the resulting storage state.

    Subsequent contexts can be seeded with this state instead of running the
    full SSO flow per test. Returns the path to the saved JSON, or skips when
    credentials aren't configured.
    """
    user = Config.active_test_user()
    if not user["email"] or user["email"].endswith("@example.com"):
        pytest.skip(
            "TEST_EMAIL_1 / TEST_PASSWORD_1 not configured — cannot cache "
            "an authenticated storage state."
        )

    state_path = tmp_path_factory.mktemp("auth") / "storage_state.json"
    context = browser.new_context(
        viewport={"width": Config.VIEWPORT_WIDTH, "height": Config.VIEWPORT_HEIGHT},
        ignore_https_errors=True,
        locale="en-US",
    )
    context.set_default_timeout(Config.TIMEOUT)
    pg = context.new_page()
    pg.set_default_timeout(Config.TIMEOUT)
    try:
        _do_login(pg, user["email"], user["password"])
        context.storage_state(path=str(state_path))
    finally:
        context.close()
    return str(state_path)


@pytest.fixture(scope="function")
def authenticated_page_fast(
    browser: Browser, authenticated_storage_state: str, request
) -> Page:
    """Page seeded from the cached storage state — no per-test SSO round-trip.

    Use this for tests that only need *some* logged-in session (the vast
    majority). Tests that exercise the actual login flow should use the
    existing `authenticated_page` fixture which logs in fresh.
    """
    context = browser.new_context(
        viewport={"width": Config.VIEWPORT_WIDTH, "height": Config.VIEWPORT_HEIGHT},
        ignore_https_errors=True,
        locale="en-US",
        storage_state=authenticated_storage_state,
    )
    context.set_default_timeout(Config.TIMEOUT)
    pg = context.new_page()
    pg.set_default_timeout(Config.TIMEOUT)

    yield pg

    if Config.SCREENSHOT_ON_FAILURE and getattr(request.node, "rep_call", None) is not None:
        if request.node.rep_call.failed:
            path = take_screenshot(pg, f"FAIL_FAST_{request.node.name}")
            request.node.user_properties.append(("screenshot", str(path)))

    context.close()


# ── Authenticated GraphQL client (cookie-seeded, supports POST) ───────────────


@pytest.fixture(scope="session")
def authenticated_graphql_client(authenticated_storage_state: str):
    """Session-scoped GraphQL client authenticated with the cached storage state.

    Reads cookies and any access token from the storage_state JSON, builds a
    requests.Session with appropriate headers, and exposes a callable that
    supports both GET (queries) and POST (mutations).

    Usage::
        def test_something(authenticated_graphql_client):
            data = authenticated_graphql_client(QUERY)
            data = authenticated_graphql_client(MUTATION, variables={...}, method="POST")
    """
    import json as _json
    from pathlib import Path

    state = _json.loads(Path(authenticated_storage_state).read_text())

    session = requests.Session()
    session.headers.update({"Accept": "application/json"})

    # Seed cookies from the storage_state.
    for c in state.get("cookies", []):
        session.cookies.set(
            c["name"],
            c["value"],
            domain=c.get("domain"),
            path=c.get("path", "/"),
        )

    # Try to extract a bearer token from any localStorage entries that look like
    # NextAuth or Keycloak tokens. The frontend stores `accessToken` in the
    # session object.
    for origin in state.get("origins", []):
        for entry in origin.get("localStorage", []):
            name = entry.get("name", "")
            value = entry.get("value", "")
            if "token" in name.lower() and value and value.count(".") == 2:
                # JWT shape — use it as the bearer token.
                session.headers["Authorization"] = f"Bearer {value}"
                break

    def _call(query: str, variables=None, method: str = "GET") -> dict:
        body = {"query": query}
        if variables:
            body["variables"] = variables
        endpoint = Config.graphql_endpoint()
        if method.upper() == "POST":
            resp = session.post(
                endpoint,
                json=body,
                headers={"Content-Type": "application/json"},
                timeout=20,
            )
        else:
            params = {"query": query}
            if variables:
                params["variables"] = _json.dumps(variables)
            resp = session.get(endpoint, params=params, timeout=20)
        assert resp.status_code == 200, (
            f"GraphQL {method} returned {resp.status_code}: {resp.text[:300]}"
        )
        return resp.json()

    yield _call
    session.close()


# ── Cleanup helpers for write-side tests ──────────────────────────────────────


@pytest.fixture(scope="function")
def cleanup_evaluation(authenticated_graphql_client):
    """Yield a list of audit IDs; teardown attempts to cancel each one.

    Tests append created audit IDs as they go. After the test finishes,
    each ID is sent through `updateAudit(status="CANCELLED")`. Cleanup
    failures log a `LEAKED_EVALUATION:<id>` line but never fail the test.
    """
    created: list[str] = []
    yield created
    from tests.data.test_data import TestGraphQL

    for audit_id in created:
        try:
            authenticated_graphql_client(
                TestGraphQL.MUTATION_UPDATE_AUDIT,
                variables={"input": {"auditId": audit_id, "status": "CANCELLED"}},
                method="POST",
            )
        except Exception as exc:  # noqa: BLE001
            print(f"LEAKED_EVALUATION:{audit_id} ({exc})")


@pytest.fixture(scope="function")
def cleanup_evaluator(authenticated_graphql_client, sandbox_org):
    """Yield a list of (organization_id, user_id) tuples; teardown removes each."""
    created: list[tuple[str, str]] = []
    yield created
    from tests.data.test_data import TestGraphQL

    for org_id, user_id in created:
        try:
            authenticated_graphql_client(
                TestGraphQL.MUTATION_REMOVE_AUDITOR_FROM_ORGANIZATION,
                variables={"organizationId": org_id, "userId": user_id},
                method="POST",
            )
        except Exception as exc:  # noqa: BLE001
            print(f"LEAKED_EVALUATOR:{org_id}/{user_id} ({exc})")


@pytest.fixture(scope="function")
def cleanup_assignment(authenticated_graphql_client):
    """Yield a list of assignment IDs; teardown sets each to DECLINED.

    There's no delete-assignment mutation, so we move them to DECLINED so
    the sandbox org's PENDING list stays clean.
    """
    created: list[str] = []
    yield created
    from tests.data.test_data import TestGraphQL

    for assignment_id in created:
        try:
            authenticated_graphql_client(
                TestGraphQL.MUTATION_UPDATE_AUDITOR_ASSIGNMENT_STATUS,
                variables={"assignmentId": assignment_id, "status": "DECLINED"},
                method="POST",
            )
        except Exception as exc:  # noqa: BLE001
            print(f"LEAKED_ASSIGNMENT:{assignment_id} ({exc})")


# ── pytest hooks ──────────────────────────────────────────────────────────────


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Attach the per-phase outcome to the item so fixtures can inspect it."""
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)
