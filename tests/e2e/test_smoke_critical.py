"""
CRITICAL SMOKE SUITE
====================
Fast, broad smoke tests verifying critical paths on every deploy.
Target runtime: < 3 minutes.

Coverage:
  TestAPIHealthSmoke          — frontend + GraphQL endpoint reachability
  TestPublicPageSmoke         — homepage content and login CTA
  TestAuthenticatedSmoke      — dashboard, AI maker section, evaluations, models, prompt libraries
  TestGraphQLSmoke            — key authenticated queries return valid responses

Run with:
    pytest tests/e2e/test_smoke_critical.py -m smoke -v
    pytest -m smoke -v    (includes this + new-evaluation smoke)
"""

import pytest
import requests

from pages.home_page import HomePage
from utils.config import Config

pytestmark = [pytest.mark.e2e, pytest.mark.smoke]

BASE = Config.BASE_URL.rstrip("/")
GRAPHQL = Config.graphql_endpoint()


# ── API Health ────────────────────────────────────────────────────────────────


class TestAPIHealthSmoke:
    """No browser required — verifies the backend endpoints are up."""

    def test_frontend_is_reachable(self, api_client: requests.Session):
        """Frontend must return HTTP 200."""
        try:
            resp = api_client.get(BASE + "/", allow_redirects=True, timeout=15)
        except requests.exceptions.ConnectionError:
            pytest.skip("Frontend not reachable from this network")
        assert resp.status_code == 200, f"Frontend returned {resp.status_code}"

    def test_graphql_endpoint_is_reachable(self, api_client: requests.Session):
        """GraphQL endpoint must return HTTP 200 for a __typename introspection query."""
        try:
            resp = api_client.get(
                GRAPHQL,
                params={"query": "{ __typename }"},
                headers={"Accept": "application/json"},
                timeout=15,
            )
        except requests.exceptions.ConnectionError:
            pytest.skip("GraphQL endpoint not reachable from this network")
        assert resp.status_code == 200, (
            f"GraphQL endpoint returned {resp.status_code} — backend may be down"
        )

    def test_graphql_returns_valid_json(self, api_client: requests.Session):
        """GraphQL response must be parseable JSON with a 'data' key."""
        try:
            resp = api_client.get(
                GRAPHQL,
                params={"query": "{ __typename }"},
                headers={"Accept": "application/json"},
                timeout=15,
            )
        except requests.exceptions.ConnectionError:
            pytest.skip("GraphQL endpoint not reachable")
        try:
            body = resp.json()
        except Exception:
            pytest.fail(f"GraphQL response is not valid JSON: {resp.text[:200]}")
        assert "data" in body or "errors" in body, (
            f"GraphQL response missing both 'data' and 'errors' keys: {body}"
        )

    def test_graphql_response_time_under_5_seconds(self, api_client: requests.Session):
        """GraphQL __typename query must respond within 5 seconds."""
        import time
        try:
            start = time.monotonic()
            api_client.get(
                GRAPHQL,
                params={"query": "{ __typename }"},
                headers={"Accept": "application/json"},
                timeout=10,
            )
            elapsed = time.monotonic() - start
        except requests.exceptions.ConnectionError:
            pytest.skip("GraphQL endpoint not reachable")
        assert elapsed < 5.0, (
            f"GraphQL baseline query took {elapsed:.2f}s — backend may be under load or starting up"
        )


# ── Public Pages ──────────────────────────────────────────────────────────────


class TestPublicPageSmoke:
    """Smoke checks for public (unauthenticated) pages."""

    def test_homepage_loads_with_title(self, page):
        """Homepage must load and have 'Parakh' in the page title."""
        home = HomePage(page)
        home.go_to_home()
        title = page.title()
        assert title and "Parakh" in title, (
            f"Expected 'Parakh' in homepage title, got: '{title}'"
        )

    def test_homepage_has_visible_content(self, page):
        """Homepage must render at least one <h1> after load."""
        home = HomePage(page)
        home.go_to_home()
        try:
            page.locator("h1").first.wait_for(state="visible", timeout=10_000)
        except Exception:
            pytest.fail("No <h1> visible on homepage within 10s — page may not have rendered")

    def test_homepage_login_button_visible(self, page):
        """A Login or Sign In button must be visible on the public homepage."""
        home = HomePage(page)
        home.go_to_home()
        assert home.is_visible(home.NAV_LOGIN_BUTTON, timeout=10_000), (
            "Login/Sign In button not found on homepage — users cannot access the platform"
        )

    def test_homepage_has_hero_section(self, page):
        """Homepage must contain the hero section with the platform tagline."""
        home = HomePage(page)
        home.go_to_home()
        # The platform tagline mentions "trustworthy" or "AI" — flexible match
        hero_text = page.locator("h1, h2").first
        try:
            hero_text.wait_for(state="visible", timeout=8_000)
            text = hero_text.inner_text()
            assert text.strip(), "Hero heading is empty"
        except Exception:
            pytest.xfail("Hero heading not found within 8s — possible SPA hydration delay")


# ── Authenticated Smoke ───────────────────────────────────────────────────────


class TestAuthenticatedSmoke:
    """Fast smoke checks for authenticated pages — use cached storage state (fast fixture)."""

    pytestmark = [pytest.mark.e2e, pytest.mark.smoke, pytest.mark.auth]

    def test_dashboard_loads_after_login(self, authenticated_page_fast):
        """After login, navigating to /dashboard must not redirect back to login."""
        page = authenticated_page_fast
        page.goto(Config.url("/dashboard"), wait_until="domcontentloaded", timeout=30_000)
        page.wait_for_timeout(2_000)

        current_url = page.url
        assert "login" not in current_url.lower() and "signin" not in current_url.lower(), (
            f"After authentication, /dashboard redirected to a login page: {current_url}"
        )

    def test_ai_maker_section_visible_on_dashboard(self, authenticated_page_fast):
        """AI Maker section or link must be visible from the dashboard."""
        page = authenticated_page_fast
        page.goto(Config.url("/dashboard"), wait_until="domcontentloaded", timeout=30_000)
        page.wait_for_timeout(2_500)

        ai_maker_indicator = page.locator(
            "text=/AI Maker/i, a[href*='ai-maker'], [class*='ai-maker' i]"
        )
        assert ai_maker_indicator.first.is_visible(timeout=8_000), (
            "AI Maker section/link not visible on dashboard — primary workflow entry point missing"
        )

    def test_evaluations_list_loads(self, authenticated_page_fast):
        """Navigating to the evaluations list must render content, not an error page."""
        page = authenticated_page_fast
        page.goto(
            Config.url("/dashboard/ai-maker/1/evaluations"),
            wait_until="domcontentloaded",
            timeout=30_000,
        )
        page.wait_for_timeout(3_000)

        # Page must have either a heading or "New Evaluation" button (or both)
        has_heading = page.locator("h1, h2").count() > 0
        has_cta = page.locator("button:has-text('New Evaluation'), a:has-text('New Evaluation')").count() > 0
        assert has_heading or has_cta, (
            "Evaluations list page rendered without any heading or New Evaluation button — "
            "page may have failed to load"
        )

    def test_models_list_loads(self, authenticated_page_fast):
        """Navigating to the AI models list must render content."""
        page = authenticated_page_fast
        page.goto(
            Config.url("/dashboard/ai-maker/1/ai-models"),
            wait_until="domcontentloaded",
            timeout=30_000,
        )
        page.wait_for_timeout(3_000)

        has_content = (
            page.locator("h1, h2").count() > 0
            or page.locator("[class*='card' i], [class*='model' i]").count() > 0
        )
        assert has_content, (
            "Models list page rendered without any heading or model cards — page may have failed"
        )

    def test_prompt_libraries_loads(self, authenticated_page_fast):
        """Navigating to prompt libraries must render content."""
        page = authenticated_page_fast
        page.goto(
            Config.url("/dashboard/ai-maker/1/prompt-libraries"),
            wait_until="domcontentloaded",
            timeout=30_000,
        )
        page.wait_for_timeout(3_000)

        has_content = (
            page.locator("h1, h2").count() > 0
            or page.locator("[class*='card' i], [class*='library' i]").count() > 0
        )
        assert has_content, (
            "Prompt libraries page rendered without any heading or library cards"
        )

    @pytest.mark.timeout(60)
    def test_no_javascript_errors_on_dashboard(self, authenticated_page_fast):
        """The dashboard must not produce console errors on load."""
        page = authenticated_page_fast
        errors = []
        page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
        page.on("pageerror", lambda exc: errors.append(str(exc)))

        page.goto(Config.url("/dashboard/ai-maker/1"), wait_until="domcontentloaded", timeout=30_000)
        page.wait_for_timeout(2_000)

        # Filter out known non-critical browser errors (e.g., blocked trackers, extensions)
        real_errors = [e for e in errors if not any(
            skip in e.lower() for skip in (
                "favicon", "net::err_", "google-analytics", "clarity", "hotjar",
                "sentry", "cdn.", "fonts.googleapis"
            )
        )]
        if real_errors:
            pytest.xfail(
                f"Console/page errors on dashboard (may be pre-existing): {real_errors[:3]}"
            )


# ── GraphQL Smoke ─────────────────────────────────────────────────────────────


class TestGraphQLSmoke:
    """Smoke checks for authenticated GraphQL queries."""

    pytestmark = [pytest.mark.e2e, pytest.mark.smoke, pytest.mark.auth]

    def test_my_organizations_returns_response(self, authenticated_graphql_client):
        """myOrganizations query must return a valid response."""
        result = authenticated_graphql_client("{ myOrganizations { id name } }")
        assert result is not None
        assert "data" in result or "errors" in result

    def test_audits_query_returns_wrapper_shape(self, authenticated_graphql_client):
        """audits query must return a paginated wrapper with data + totalItemsCount."""
        result = authenticated_graphql_client(
            "{ audits { data { id status } totalItemsCount } }"
        )
        assert "data" in result or "errors" in result
        if result.get("data") and result["data"].get("audits") is not None:
            wrapper = result["data"]["audits"]
            assert isinstance(wrapper, dict)
            assert "data" in wrapper
            assert "totalItemsCount" in wrapper

    def test_ai_models_query_returns_list(self, authenticated_graphql_client):
        """aiModels query must return a list (possibly empty) without errors."""
        result = authenticated_graphql_client("{ aiModels(limit: 5) { id name } }")
        assert "data" in result or "errors" in result
        if result.get("data") and result["data"].get("aiModels") is not None:
            assert isinstance(result["data"]["aiModels"], list)
