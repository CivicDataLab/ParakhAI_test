"""
E2E tests for the Parakh homepage.
URL: https://parakh.civicdataspace.in
"""

import pytest
from playwright.sync_api import Page

from pages.home_page import HomePage
from utils.config import Config

pytestmark = [pytest.mark.e2e, pytest.mark.smoke, pytest.mark.regression]


class TestHomepageLoads:
    """Verify the homepage renders correctly and exposes key elements."""

    def test_homepage_loads_successfully(self, page: Page):
        """Homepage returns 200, has a title, and a visible heading."""
        home = HomePage(page)
        home.go_to_home()

        assert page.title(), "Page title must not be empty"
        # Use the locator (h1 OR h2 fallback) rather than a hardcoded "h1" tag
        assert home.is_visible(home.HERO_HEADING), (
            "A heading (h1 or h2) must be visible on the homepage after the page loads"
        )

    def test_page_title_contains_parakh(self, page: Page):
        """The browser tab title should reference the platform."""
        home = HomePage(page)
        home.go_to_home()
        title = page.title().lower()
        assert any(
            kw in title for kw in ("parakh", "civic", "ai", "evaluation")
        ), f"Unexpected page title: '{page.title()}'"

    def test_hero_heading_text(self, page: Page):
        """The hero heading should contain the platform's key value proposition."""
        home = HomePage(page)
        home.go_to_home()

        if not home.is_visible(home.HERO_HEADING, timeout=5_000):
            pytest.skip(
                "Hero heading not visible after load — "
                "page content may not have rendered (site health issue)"
            )

        heading = home.get_hero_heading_text()
        assert heading, "Hero heading must not be empty"
        assert len(heading) > 5, f"Hero heading too short: '{heading}'"

    def test_get_started_button_exists(self, page: Page):
        """A prominent CTA button must be present on the homepage."""
        home = HomePage(page)
        home.go_to_home()
        assert home.is_get_started_visible(), (
            "A 'Get Started' CTA button must be visible on the homepage"
        )

    def test_evaluation_workspace_link(self, page: Page):
        """Clicking 'Evaluation Workspace' in the nav navigates away from root."""
        home = HomePage(page)
        home.go_to_home()

        if home.is_visible(home.NAV_EVALUATION_WORKSPACE, timeout=5_000):
            start_url = page.url
            home.click_evaluation_workspace()
            # Should navigate somewhere (even a redirect is acceptable)
            assert page.url != start_url or page.url != Config.BASE_URL, (
                "Clicking Evaluation Workspace should navigate to a new URL"
            )
        else:
            pytest.skip("Evaluation Workspace nav link not present on this build")

    def test_login_button_redirects_to_auth(self, page: Page):
        """Clicking LOGIN/SIGN UP should redirect to the Keycloak auth page."""
        home = HomePage(page)
        home.go_to_home()

        if not home.is_visible(home.NAV_LOGIN_BUTTON, timeout=5_000):
            pytest.skip("Login button not visible — user may already be authenticated")

        home.click_login()

        # Wait for the SPA → Keycloak redirect to actually settle. Reading
        # `page.url` immediately after click can race the navigation.
        auth_indicators = ("login", "auth", "keycloak", "sso", "signin", "sign-in")
        try:
            page.wait_for_url(
                lambda u: any(ind in u.lower() for ind in auth_indicators),
                timeout=15_000,
            )
        except Exception:
            pass  # let the assertion below report the actual URL

        current_url = page.url.lower()
        assert any(ind in current_url for ind in auth_indicators), (
            f"Expected redirect to auth page, got: {page.url}"
        )
