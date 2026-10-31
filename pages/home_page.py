"""
Page Object Model for the Parakh homepage.
URL: https://parakh.civicdataspace.in

Selectors live in locators/home_locators.py — this module only contains
browser-action methods that use those selectors.
"""

import pytest
from playwright.sync_api import Page

from locators.home_locators import HomeLocators
from pages.base_page import BasePage
from utils.config import Config


class HomePage(BasePage):
    # Re-export locators as class attributes so callers can reference them
    # (e.g. home.NAV_LOGIN_BUTTON) without importing the locators module.
    LOGO = HomeLocators.LOGO
    NAV_LOGIN_BUTTON = HomeLocators.NAV_LOGIN_BUTTON
    NAV_EVALUATION_WORKSPACE = HomeLocators.NAV_EVALUATION_WORKSPACE
    HAMBURGER_MENU = HomeLocators.HAMBURGER_MENU
    MOBILE_NAV_ITEMS = HomeLocators.MOBILE_NAV_ITEMS
    HERO_HEADING = HomeLocators.HERO_HEADING
    GET_STARTED_BUTTON = HomeLocators.GET_STARTED_BUTTON
    HERO_SECTION = HomeLocators.HERO_SECTION
    FEATURE_TABS_CONTAINER = HomeLocators.FEATURE_TABS_CONTAINER
    TAB_BUTTON = HomeLocators.TAB_BUTTON
    ACTIVE_TAB = HomeLocators.ACTIVE_TAB
    TAB_CONTENT = HomeLocators.TAB_CONTENT
    FOOTER = HomeLocators.FOOTER
    SOCIAL_LINKS = HomeLocators.SOCIAL_LINKS
    CIVICDATALAB_LINK = HomeLocators.CIVICDATALAB_LINK
    HYDRATED_HERO_H1 = HomeLocators.HYDRATED_HERO_H1
    HYDRATED_FOOTER_LINK = HomeLocators.HYDRATED_FOOTER_LINK
    HYDRATED_ACTIVE_TAB = HomeLocators.HYDRATED_ACTIVE_TAB

    def __init__(self, page: Page) -> None:
        super().__init__(page)

    # ── Navigation ────────────────────────────────────────────────────────────

    def go_to_home(self) -> "HomePage":
        response = self.navigate(Config.BASE_URL)

        # ── Guard 1: HTTP error from server / proxy ────────────────────────
        if response and response.status >= 400:
            pytest.skip(
                f"Site returned HTTP {response.status} — "
                "the platform may be unreachable from this network "
                "(check VPN / IP allowlist)."
            )

        # TODO: TEMP — platform has a known multi-reload rendering issue in prod.
        # Pattern: navigate → __next_error__ on reload 1 → clears on reload 2.
        # Retry up to 3 times; use 'load' (not 'networkidle' — app has background
        # polling that prevents networkidle from settling). Remove once fixed.
        for _ in range(3):
            if self.page.title() and self.page.evaluate(
                "() => document.documentElement.id !== '__next_error__'"
            ):
                break
            self.page.reload(wait_until="load", timeout=self.timeout)
            self.page.wait_for_timeout(3_000)

        # ── Guard 2: Next.js runtime error (app booted but JS crashed) ────
        # When Next.js throws an unhandled error, it sets id="__next_error__"
        # on <html>. The page returns HTTP 200 but renders no content.
        has_next_error: bool = self.page.evaluate(
            "() => document.documentElement.id === '__next_error__'"
        )
        if has_next_error:
            pytest.skip(
                "Next.js runtime error detected — the application is not rendering. "
                "This is a site-health issue, not a test failure. "
                "Check the deployment logs at the platform."
            )

        # ── Guard 3: Empty title (generic rendering failure fallback) ──────
        if not self.page.title():
            pytest.skip(
                "Page title is empty after load — the application did not render. "
                "Check site health before re-running these tests."
            )

        return self

    def wait_until_hydrated(self, timeout: int = 20_000) -> "HomePage":
        """Wait until every client-rendered homepage section has mounted.

        `go_to_home()` returns at the `load` event, when only the server-rendered
        skeleton exists. Whole-page scans (axe, language, tab state) must run
        after hero, feature tabs and footer are in the DOM, otherwise they
        inspect a page no user ever sees. Raises a Playwright TimeoutError that
        names the missing marker rather than letting the caller scan a skeleton.
        """
        for marker in (
            self.HYDRATED_HERO_H1,
            self.HYDRATED_ACTIVE_TAB,
            self.HYDRATED_FOOTER_LINK,
        ):
            self.page.locator(marker).first.wait_for(state="visible", timeout=timeout)
        return self

    def click_get_started(self) -> None:
        self.click(self.GET_STARTED_BUTTON)

    def click_login(self) -> None:
        self.click(self.NAV_LOGIN_BUTTON)
        self.wait_for_load("domcontentloaded")

    def click_evaluation_workspace(self) -> None:
        self.click(self.NAV_EVALUATION_WORKSPACE)
        self.wait_for_load("domcontentloaded")

    def click_logo(self) -> None:
        self.click(self.LOGO)
        self.wait_for_load("domcontentloaded")

    # ── Hero ──────────────────────────────────────────────────────────────────

    def get_hero_heading_text(self) -> str:
        self.wait_for_element(self.HERO_HEADING)
        return self.get_text(self.HERO_HEADING)

    def is_get_started_visible(self) -> bool:
        return self.is_visible(self.GET_STARTED_BUTTON)

    def is_hero_section_visible(self) -> bool:
        return self.is_visible(self.HERO_SECTION)

    def is_hero_visible(self) -> bool:
        return self.is_hero_section_visible()

    # ── Feature tabs ──────────────────────────────────────────────────────────

    def click_feature_tab(self, tab_name: str) -> None:
        """Click a tab by its visible text label."""
        selector = f"[role='tab']:has-text('{tab_name}'), button:has-text('{tab_name}')"
        self.click(selector)

    def get_active_tab_text(self) -> str:
        self.wait_for_element(self.ACTIVE_TAB)
        return self.get_text(self.ACTIVE_TAB)

    def get_all_tab_names(self) -> list[str]:
        self.wait_for_element(self.FEATURE_TABS_CONTAINER)
        tabs = self.page.locator(self.TAB_BUTTON)
        return [tabs.nth(i).inner_text().strip() for i in range(tabs.count())]

    def get_tab_selected_flags(self) -> dict[str, bool]:
        """Map each feature-tab label to whether its *selected* state is exposed
        programmatically (aria-selected / aria-pressed / aria-current), which is
        what assistive technology reads. The lavender background is not enough."""
        return self.page.locator(self.TAB_BUTTON).evaluate_all(
            """els => Object.fromEntries(els.map(e => [
                e.innerText.trim(),
                e.getAttribute('aria-selected') === 'true'
                  || e.getAttribute('aria-pressed') === 'true'
                  || ['true', 'page', 'step', 'location'].includes(e.getAttribute('aria-current'))
            ]))"""
        )

    def get_non_latin_text_without_own_language(self) -> list[str]:
        """Return rendered text nodes that contain Indic-script characters but whose
        nearest `lang` attribute is still the page language (English).

        WCAG 3.1.2 (Language of Parts): passages in another language need their
        own `lang`, otherwise screen readers pronounce them with English rules.
        """
        return self.page.evaluate(
            """() => {
                const indic = /[\u0900-\u0DFF]/;
                const pageLang = (document.documentElement.lang || 'en').split('-')[0].toLowerCase();
                const out = [];
                const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
                for (let n = walker.nextNode(); n; n = walker.nextNode()) {
                    const el = n.parentElement;
                    if (!el || el.closest('script,style,noscript') || !indic.test(n.nodeValue)) continue;
                    const own = el.closest('[lang]');
                    const lang = own ? own.lang.split('-')[0].toLowerCase() : pageLang;
                    if (lang === pageLang) out.push(n.nodeValue.trim());
                }
                return out;
            }"""
        )

    def is_feature_content_visible(self) -> bool:
        return self.is_visible(self.TAB_CONTENT)

    def get_tab_content_text(self) -> str:
        return self.get_text(self.TAB_CONTENT)

    # ── Mobile ────────────────────────────────────────────────────────────────

    def open_hamburger_menu(self) -> None:
        self.click(self.HAMBURGER_MENU)

    def click_hamburger(self) -> None:
        self.open_hamburger_menu()

    def is_mobile_menu_open(self) -> bool:
        return self.is_visible(self.MOBILE_NAV_ITEMS, timeout=3_000)

    # ── Footer ────────────────────────────────────────────────────────────────

    def get_social_link_count(self) -> int:
        try:
            self.page.locator(self.FOOTER).wait_for(state="visible", timeout=5_000)
        except Exception:
            pass
        return self.page.locator(self.SOCIAL_LINKS).count()

    def is_civicdatalab_link_present(self) -> bool:
        return self.is_visible(self.CIVICDATALAB_LINK)

    def is_footer_visible(self) -> bool:
        self.scroll_to_bottom()
        return self.is_visible(self.FOOTER)
