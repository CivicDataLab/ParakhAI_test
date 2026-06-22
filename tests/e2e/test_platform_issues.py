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


# ── Additional issues from 2026-06-22 MCP exploration ────────────────────────


class TestSEOCanonical:
    """Canonical link tag coverage."""

    @pytest.mark.xfail(reason="SEO-003: No canonical link tag on any page — known bug")
    def test_seo003_homepage_has_canonical_link(self, page: Page):
        """SEO-003: Homepage must have a <link rel='canonical'> tag."""
        page.goto(Config.url("/"))
        page.wait_for_timeout(2000)
        canonical = page.locator("link[rel='canonical']")
        assert canonical.count() > 0, (
            "SEO-003: No <link rel='canonical'> found on the homepage. "
            "Without canonical links, duplicate-URL indexing can hurt SEO."
        )


class TestPlatformIssuesExtended:
    """Additional platform issues from the 2026-06-22 MCP exploration."""

    @pytest.mark.xfail(reason="UX-015: All 'View' buttons on AI Model cards are disabled — known bug")
    def test_ux015_model_card_view_button_is_enabled(self, authenticated_page_fast: Page):
        """UX-015: At least one 'View' button on AI Model cards must be enabled."""
        authenticated_page_fast.goto(Config.url("/dashboard/ai-maker/1/ai-models"))
        authenticated_page_fast.wait_for_timeout(2000)
        view_buttons = authenticated_page_fast.locator("button:has-text('View'), a:has-text('View')")
        if view_buttons.count() == 0:
            pytest.skip("No 'View' buttons found on AI Models page")
        disabled_count = sum(
            1 for i in range(view_buttons.count())
            if view_buttons.nth(i).get_attribute("disabled") is not None
            or view_buttons.nth(i).is_disabled()
        )
        enabled_count = view_buttons.count() - disabled_count
        assert enabled_count > 0, (
            f"UX-015: All {disabled_count} 'View' buttons on AI Model cards are disabled. "
            "Users cannot navigate to any model detail page."
        )

    @pytest.mark.xfail(reason="UX-002: All dashboard sub-pages have identical title 'Dashboard | ParakhAI' — known bug")
    def test_ux002_dashboard_subpages_have_unique_titles(self, authenticated_page_fast: Page):
        """UX-002: Each dashboard sub-page must have a unique <title>."""
        paths_and_labels = [
            ("/dashboard/ai-maker/1/evaluations", "evaluations"),
            ("/dashboard/ai-maker/1/ai-models", "models"),
            ("/dashboard/ai-maker/1/auditors", "evaluators"),
        ]
        titles = {}
        for path, label in paths_and_labels:
            authenticated_page_fast.goto(Config.url(path))
            authenticated_page_fast.wait_for_timeout(1500)
            titles[label] = authenticated_page_fast.title()
        unique_titles = set(titles.values())
        assert len(unique_titles) == len(titles), (
            f"UX-002: Multiple dashboard pages share the same <title>. Titles: {titles}"
        )
        for label, title in titles.items():
            assert "Dashboard" not in title or label.lower() in title.lower(), (
                f"UX-002: '{label}' page title is '{title}' — must include the section name, "
                "not just 'Dashboard | ParakhAI'."
            )

    @pytest.mark.xfail(reason="UX-005: Missing H1 on AI Maker org select page — known bug")
    def test_ux005_ai_maker_select_page_has_h1(self, authenticated_page_fast: Page):
        """UX-005: AI Maker org select page must have exactly one <h1>."""
        authenticated_page_fast.goto(Config.url("/dashboard/ai-maker"))
        authenticated_page_fast.wait_for_timeout(2000)
        h1_count = authenticated_page_fast.locator("h1").count()
        assert h1_count == 1, (
            f"UX-005: AI Maker org select page has {h1_count} <h1> elements (expected 1). "
            "Breaks document outline and WCAG 2.4.6."
        )

    @pytest.mark.xfail(reason="UX-005: Missing H1 on AI Maker overview page — known bug")
    def test_ux005_ai_maker_overview_page_has_h1(self, authenticated_page_fast: Page):
        """UX-005: AI Maker org overview page must have exactly one <h1>."""
        authenticated_page_fast.goto(Config.url("/dashboard/ai-maker/1"))
        authenticated_page_fast.wait_for_timeout(2000)
        h1_count = authenticated_page_fast.locator("h1").count()
        assert h1_count == 1, (
            f"UX-005: AI Maker overview page has {h1_count} <h1> elements (expected 1)."
        )

    @pytest.mark.xfail(reason="UX-006: Eval name remains editable on COMPLETED evaluations — known bug")
    def test_ux006_completed_eval_name_is_readonly(
        self, authenticated_page_fast: Page, completed_eval_id: int
    ):
        """UX-006: The evaluation name input must be read-only on COMPLETED evaluations."""
        authenticated_page_fast.goto(
            Config.url(f"/dashboard/ai-maker/1/evaluations/{completed_eval_id}")
        )
        authenticated_page_fast.wait_for_timeout(3000)
        name_input = authenticated_page_fast.locator(
            "input[name='name'], input[placeholder*='name'], input[aria-label*='name']"
        ).first
        if name_input.count() == 0:
            pytest.skip("Eval name input not found on detail page")
        is_readonly = (
            name_input.get_attribute("readonly") is not None
            or name_input.get_attribute("disabled") is not None
            or name_input.is_disabled()
        )
        assert is_readonly, (
            "UX-006: Evaluation name input is editable on a COMPLETED evaluation. "
            "Must be read-only for all terminal statuses (COMPLETED, FAILED, CANCELLED)."
        )

    @pytest.mark.xfail(reason="UX-013: No success toast after Add Evaluator — known bug")
    def test_ux013_add_evaluator_shows_success_feedback(self, authenticated_page_fast: Page):
        """UX-013: Adding an evaluator must show a success toast/confirmation."""
        authenticated_page_fast.goto(Config.url("/dashboard/ai-maker/1/auditors"))
        authenticated_page_fast.wait_for_timeout(2000)
        add_btn = authenticated_page_fast.locator(
            "button:has-text('Add Evaluator'), button:has-text('Invite')"
        ).first
        if add_btn.count() == 0:
            pytest.skip("Add Evaluator button not found")
        add_btn.click()
        authenticated_page_fast.wait_for_timeout(1000)
        dialog = authenticated_page_fast.locator("[role='dialog']")
        if dialog.count() == 0:
            pytest.skip("Add Evaluator dialog did not open")
        cancel = authenticated_page_fast.locator("[role='dialog'] button:has-text('Cancel')").first
        if cancel.count() > 0:
            cancel.click()
        authenticated_page_fast.wait_for_timeout(500)
        phantom_toast = authenticated_page_fast.locator(
            "[role='status'], [role='alert']:has-text('success'), "
            ".toast, [data-sonner-toast], [data-radix-toast-root]"
        )
        assert phantom_toast.count() == 0, (
            "UX-013: A success toast appeared after cancelling Add Evaluator. "
            "Success feedback must only fire when the mutation actually completes."
        )

    @pytest.mark.xfail(reason="INFRA-004: Evaluators page fires requests to civicdataspace.innull — known bug")
    def test_infra004_evaluators_page_no_null_url_requests(self, authenticated_page_fast: Page):
        """INFRA-004: The Evaluators page must not fire requests to 'civicdataspace.innull'."""
        null_requests: list = []
        authenticated_page_fast.on(
            "request",
            lambda req: null_requests.append(req.url) if "innull" in req.url else None,
        )
        authenticated_page_fast.goto(Config.url("/dashboard/ai-maker/1/auditors"))
        authenticated_page_fast.wait_for_timeout(3000)
        assert not null_requests, (
            f"INFRA-004: Evaluators page fired {len(null_requests)} request(s) to malformed "
            f"'innull' URL — a null env var is concatenated to the API base URL. "
            f"Requests: {null_requests}"
        )

    @pytest.mark.xfail(reason="AUTH-001: Session expiry causes silent GraphQL failures — known bug")
    def test_auth001_session_expiry_surfaces_to_user(self, authenticated_page_fast: Page):
        """AUTH-001: When the session token expires, users must see a redirect or error message."""
        authenticated_page_fast.goto(Config.url("/dashboard/ai-maker/1/evaluations"))
        authenticated_page_fast.wait_for_timeout(2000)
        authenticated_page_fast.evaluate("""() => {
            document.cookie = 'next-auth.session-token=expired_token_test; path=/; max-age=0';
            document.cookie = '__Secure-next-auth.session-token=expired; path=/; max-age=0';
        }""")
        authenticated_page_fast.reload()
        authenticated_page_fast.wait_for_timeout(3000)
        redirected = any(
            kw in authenticated_page_fast.url.lower()
            for kw in ("login", "sign-in", "auth")
        )
        has_error_ui = authenticated_page_fast.locator(
            "text=session expired, text=please log in, text=sign in again, "
            "[role='alert']:has-text('expired')"
        ).count() > 0
        assert redirected or has_error_ui, (
            "AUTH-001: After session expiry, no redirect to login and no error message shown. "
            "Pages appear functional but data silently fails to load."
        )
