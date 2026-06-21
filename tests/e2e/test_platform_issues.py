"""
Tests for platform-level issues discovered during MCP exploration on 2026-06-22.

Covers:
  - Homepage meta description spelling
  - 404 page branding/navigation
  - Mobile hamburger menu accessibility and navigation content
  - Session verification timeout threshold
  - Unauthenticated /dashboard redirect UX
"""

import re
import time

import pytest
from playwright.sync_api import Page

from pages.home_page import HomePage
from utils.config import Config

pytestmark = [pytest.mark.e2e, pytest.mark.regression]


# ── Homepage meta / SEO ───────────────────────────────────────────────────────


class TestHomepageSEO:
    """Homepage meta-data correctness."""

    def test_meta_description_has_no_typo(self, page: Page):
        """'Participatory' must be spelled correctly in the meta description."""
        home = HomePage(page)
        home.go_to_home()
        meta = page.evaluate(
            "() => document.querySelector('meta[name=\"description\"]')?.content || ''"
        )
        assert meta, "Homepage must have a meta description tag"
        assert "paricipatory" not in meta.lower(), (
            f"Meta description contains typo 'Paricipatory': '{meta}'. "
            "Should be 'Participatory'."
        )

    def test_meta_description_mentions_ai_evaluation(self, page: Page):
        home = HomePage(page)
        home.go_to_home()
        meta = page.evaluate(
            "() => document.querySelector('meta[name=\"description\"]')?.content || ''"
        ) or ""
        assert any(kw in meta.lower() for kw in ("ai", "evaluat", "parakh", "civic")), (
            f"Meta description should mention AI evaluation context. Got: '{meta}'"
        )

    def test_og_title_is_present(self, page: Page):
        home = HomePage(page)
        home.go_to_home()
        og = page.evaluate(
            "() => document.querySelector('meta[property=\"og:title\"]')?.content || ''"
        )
        assert og, "Homepage should have an Open Graph title for social sharing"


# ── 404 page ──────────────────────────────────────────────────────────────────


class TestNotFoundPage:
    """The 404 page should be branded and helpful, not bare Next.js default."""

    def test_404_page_shows_not_found_message(self, page: Page):
        page.goto(Config.url("/this-page-does-not-exist-xyz-123"))
        page.wait_for_load_state("domcontentloaded")
        content = page.content().lower()
        assert "404" in content or "not found" in content, (
            "Visiting a non-existent URL must show a 404/not-found message"
        )

    @pytest.mark.xfail(reason="404 page is bare Next.js default with no home link — app bug")
    def test_404_page_has_home_navigation_link(self, page: Page):
        """Custom 404 should have a link back to the homepage."""
        page.goto(Config.url("/this-page-does-not-exist-xyz-123"))
        page.wait_for_load_state("domcontentloaded")
        home_link = page.locator(
            "a[href='/'], a:has-text('Home'), a:has-text('Go to home'), button:has-text('Home')"
        )
        assert home_link.count() > 0, (
            "404 page must have a navigation link back to the homepage"
        )

    @pytest.mark.xfail(reason="404 page is bare Next.js default with no branding — app bug")
    def test_404_page_has_logo_or_branding(self, page: Page):
        """Custom 404 should show the ParakhAI logo/brand."""
        page.goto(Config.url("/this-page-does-not-exist-xyz-123"))
        page.wait_for_load_state("domcontentloaded")
        brand = page.locator("img[alt*='ParakhAI'], img[alt*='Parakh'], nav, header")
        assert brand.count() > 0, (
            "404 page must show the platform logo/navigation, not a bare error page"
        )


# ── Mobile hamburger menu ──────────────────────────────────────────────────────


class TestMobileMenu:
    """Mobile hamburger menu must be accessible and contain navigation items."""

    @pytest.mark.mobile
    def test_hamburger_menu_is_visible_on_mobile(self, mobile_page: Page):
        mobile_page.goto(Config.BASE_URL)
        mobile_page.wait_for_load_state("domcontentloaded")
        hamburger = mobile_page.locator(
            "button[aria-label*='menu' i], button[aria-label*='Menu' i], "
            "button:has-text('Open menu'), button[class*='hamburger']"
        )
        assert hamburger.count() > 0, "Hamburger menu button must be visible at 390px"

    @pytest.mark.mobile
    @pytest.mark.xfail(reason="Mobile menu dialog missing DialogTitle — a11y bug (Radix UI)")
    def test_mobile_menu_dialog_has_accessible_title(self, mobile_page: Page):
        """Mobile menu dialog must have a DialogTitle for screen readers."""
        mobile_page.goto(Config.BASE_URL)
        mobile_page.wait_for_load_state("domcontentloaded")
        hamburger = mobile_page.locator(
            "button[aria-label*='menu' i], button:has-text('Open menu')"
        ).first
        if hamburger.count() == 0:
            pytest.skip("Hamburger button not found at mobile viewport")
        hamburger.click()
        mobile_page.wait_for_timeout(500)
        dialog = mobile_page.locator("[role='dialog']")
        assert dialog.count() > 0, "Mobile menu must render as a dialog"
        title = mobile_page.locator("[role='dialog'] h1, [role='dialog'] h2, [role='dialog'] [role='heading']")
        assert title.count() > 0, (
            "Mobile menu dialog must have a heading/DialogTitle for accessibility"
        )

    @pytest.mark.mobile
    @pytest.mark.xfail(reason="Mobile menu only shows profile icon, no nav links — app bug")
    def test_mobile_menu_has_navigation_links(self, mobile_page: Page):
        """Authenticated mobile menu must show navigation options."""
        mobile_page.goto(Config.BASE_URL)
        mobile_page.wait_for_load_state("domcontentloaded")
        hamburger = mobile_page.locator(
            "button[aria-label*='menu' i], button:has-text('Open menu')"
        ).first
        if hamburger.count() == 0:
            pytest.skip("Hamburger button not found at mobile viewport")
        hamburger.click()
        mobile_page.wait_for_timeout(500)
        nav_links = mobile_page.locator(
            "[role='dialog'] a, [role='dialog'] nav a, [role='dialog'] button:not([aria-label*='close' i])"
        )
        assert nav_links.count() >= 2, (
            f"Mobile menu must have at least 2 navigation items, found {nav_links.count()}"
        )

    @pytest.mark.mobile
    def test_mobile_menu_can_be_closed_with_escape(self, mobile_page: Page):
        mobile_page.goto(Config.BASE_URL)
        mobile_page.wait_for_load_state("domcontentloaded")
        hamburger = mobile_page.locator(
            "button[aria-label*='menu' i], button:has-text('Open menu')"
        ).first
        if hamburger.count() == 0:
            pytest.skip("Hamburger button not found")
        hamburger.click()
        mobile_page.wait_for_timeout(300)
        mobile_page.keyboard.press("Escape")
        mobile_page.wait_for_timeout(300)
        dialog = mobile_page.locator("[role='dialog']:visible")
        assert dialog.count() == 0, "Pressing Escape must close the mobile menu dialog"


# ── Unauthenticated redirect UX ───────────────────────────────────────────────


class TestUnauthenticatedAccessUX:
    """Accessing authenticated routes without login should give clear feedback."""

    def test_unauthenticated_dashboard_redirects(self, page: Page):
        """Visiting /dashboard without auth must not show the dashboard content."""
        page.goto(Config.url("/dashboard"))
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(1000)
        assert "/dashboard" not in page.url or page.locator("text=Verifying").count() > 0 or \
               page.locator("button:has-text('LOGIN')").count() > 0, (
            "Unauthenticated /dashboard must redirect to login or show session check"
        )

    @pytest.mark.xfail(reason="Redirect shows homepage silently with no login prompt — UX bug")
    def test_unauthenticated_redirect_shows_login_prompt(self, page: Page):
        """Visiting a protected URL should show an explicit 'please log in' message."""
        page.goto(Config.url("/dashboard/ai-maker/1/evaluations"))
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(2000)
        login_hint = page.locator(
            "text=Please log in, text=Sign in to continue, text=Authentication required, "
            "button:has-text('LOGIN'), a:has-text('Login')"
        )
        assert login_hint.count() > 0, (
            "After redirect from protected URL, user must see an explicit login prompt"
        )


# ── Session verification performance ──────────────────────────────────────────


class TestSessionVerificationPerformance:
    """Session verification should complete within a reasonable time threshold."""

    def test_session_verification_completes_within_15s(self, authenticated_page_fast: Page):
        page = authenticated_page_fast
        start = time.time()
        page.goto(Config.url("/dashboard"))
        page.wait_for_timeout(500)
        try:
            page.locator("text=Verifying your session...").first.wait_for(
                state="hidden", timeout=15_000
            )
        except Exception:
            elapsed = time.time() - start
            pytest.fail(
                f"Session verification took >{elapsed:.1f}s (threshold: 15s). "
                "This indicates a slow auth check or DB connection pool exhaustion."
            )
        elapsed = time.time() - start
        assert elapsed < 20, f"Session verification must complete within 20s, took {elapsed:.1f}s"
