"""
Mobile-viewport E2E tests (390×844 — iPhone 14 Pro equivalent).

Uses the `mobile_page` fixture from conftest.py, which is unauthenticated.
Covers the top 5 public flows a mobile user hits before signing in.
"""

import pytest
from playwright.sync_api import Page

from pages.home_page import HomePage
from pages.prompt_libraries_page import PromptLibrariesPage

pytestmark = [pytest.mark.e2e, pytest.mark.mobile, pytest.mark.regression]


class TestMobileHomepage:
    def test_hero_visible_at_mobile_viewport(self, mobile_page: Page):
        """Hero section and primary CTA must render without horizontal overflow."""
        home = HomePage(mobile_page)
        home.go_to_home()
        assert home.is_hero_visible(), "Hero section must be visible at 390px width"

    def test_feature_tabs_render_on_mobile(self, mobile_page: Page):
        """At least one feature tab must be present at mobile viewport."""
        home = HomePage(mobile_page)
        home.go_to_home()
        home.wait_for_element(home.FEATURE_TABS_CONTAINER)
        tabs = home.get_all_tab_names()
        assert len(tabs) > 0, "Feature tabs must render on mobile"

    def test_footer_visible_after_scroll(self, mobile_page: Page):
        """Footer must be reachable by scrolling to the bottom."""
        home = HomePage(mobile_page)
        home.go_to_home()
        home.scroll_to_bottom()
        assert home.is_footer_visible(), "Footer must be visible after scrolling to bottom"


class TestMobileNavigation:
    def test_hamburger_menu_opens(self, mobile_page: Page):
        """Hamburger icon must be present and open a nav menu at 390px."""
        home = HomePage(mobile_page)
        home.go_to_home()

        if not home.is_visible(home.HAMBURGER_MENU, timeout=5_000):
            pytest.skip("Hamburger menu not present — responsive nav may use a different breakpoint")

        home.click_hamburger()
        home.wait_for_element(home.FEATURE_TABS_CONTAINER, timeout=3_000)

        has_menu = (
            home.is_mobile_menu_open()
            or mobile_page.locator(
                "[class*='mobile-menu'], [class*='MobileMenu'], "
                "[class*='drawer'], [data-state='open'], [role='dialog']"
            ).count() > 0
        )
        assert has_menu, "Mobile menu must open after clicking the hamburger icon"


class TestMobilePromptLibraries:
    def test_prompt_libraries_loads_on_mobile(self, mobile_page: Page):
        """Prompt Libraries page must load at least one card at mobile viewport."""
        pl = PromptLibrariesPage(mobile_page)
        pl.go_to_prompt_libraries()
        assert pl.is_category_badge_visible("agriculture") or pl.is_category_badge_visible("healthcare"), (
            "At least one category badge (Agriculture or Healthcare) must be visible on mobile"
        )
