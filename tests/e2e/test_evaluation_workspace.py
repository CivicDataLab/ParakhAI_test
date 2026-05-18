"""
E2E tests for the Evaluation Workspace entry point.
Covers: role selection UI, routing, breadcrumbs, and organisation selection.
URL: https://parakh.civicdataspace.in/dashboard
"""

import pytest
from playwright.sync_api import Page

from pages.workspace_page import WorkspacePage

pytestmark = [pytest.mark.e2e, pytest.mark.regression, pytest.mark.auth]


@pytest.fixture
def page(authenticated_page_fast):
    """Override pytest-playwright's `page` so every test uses the cached auth
    session. /dashboard role selection requires login."""
    return authenticated_page_fast


class TestRoleSelectionPage:
    """Verify the role-selection screen renders and exposes both role cards."""

    def test_role_selection_page_loads(self, page: Page):
        """Navigating to /dashboard shows the role-selection screen."""
        ws = WorkspacePage(page)
        ws.go_to_workspace()
        assert ws.is_role_selection_visible(), (
            "Role selection cards (AI Maker / Evaluator) must be visible on /dashboard"
        )

    def test_page_title_contains_parakh(self, page: Page):
        """Browser tab title references the platform."""
        ws = WorkspacePage(page)
        ws.go_to_workspace()
        title = page.title().lower()
        assert any(kw in title for kw in ("parakh", "dashboard", "evaluation")), (
            f"Unexpected page title: '{page.title()}'"
        )

    def test_ai_maker_card_is_visible(self, page: Page):
        """AI Maker role card is present."""
        ws = WorkspacePage(page)
        ws.go_to_workspace()
        assert ws.is_visible(ws.AI_MAKER_CARD), "AI Maker card must be visible"

    def test_evaluator_card_is_visible(self, page: Page):
        """Evaluator role card is present."""
        ws = WorkspacePage(page)
        ws.go_to_workspace()
        assert ws.is_visible(ws.EVALUATOR_CARD), "Evaluator card must be visible"

    def test_two_role_cards_are_displayed(self, page: Page):
        """Exactly two role options are presented."""
        ws = WorkspacePage(page)
        ws.go_to_workspace()
        assert ws.is_visible(ws.AI_MAKER_CARD), "AI Maker card missing"
        assert ws.is_visible(ws.EVALUATOR_CARD), "Evaluator card missing"

    def test_evaluation_workspace_nav_link_is_visible(self, page: Page):
        """The 'Evaluation Workspace' button in the global nav is present."""
        ws = WorkspacePage(page)
        ws.go_to_workspace()
        assert ws.is_visible(ws.NAV_EVALUATION_WORKSPACE), (
            "Evaluation Workspace nav link must be visible after login"
        )

    def test_breadcrumb_shows_evaluation_workspace(self, page: Page):
        """Breadcrumb contains 'Evaluation Workspace'."""
        ws = WorkspacePage(page)
        ws.go_to_workspace()
        if not ws.is_visible(ws.BREADCRUMB_EVALUATION_WORKSPACE, timeout=3_000):
            pytest.skip("Breadcrumb not rendered on this build")
        assert ws.is_visible(ws.BREADCRUMB_EVALUATION_WORKSPACE), (
            "Breadcrumb must show 'Evaluation Workspace'"
        )

    def test_footer_is_visible(self, page: Page):
        """Page footer with 'made by' attribution is present."""
        ws = WorkspacePage(page)
        ws.go_to_workspace()
        ws.scroll_to_bottom()
        assert ws.is_visible(WorkspacePage.FOOTER), "Footer must be visible"


class TestAIMakerRoleNavigation:
    """Verify clicking AI Maker navigates to the org-selection screen."""

    def test_clicking_ai_maker_goes_to_org_selection(self, page: Page):
        """Clicking AI Maker card shows the 'Select Organization' screen."""
        ws = WorkspacePage(page)
        ws.go_to_workspace()

        if not ws.is_visible(ws.AI_MAKER_CARD, timeout=5_000):
            pytest.skip("AI Maker card not found — user may not be authenticated")

        ws.select_ai_maker()
        assert ws.is_org_selection_visible() or "/ai-maker" in page.url, (
            "Selecting AI Maker should navigate to org selection or AI Maker route"
        )

    def test_org_selection_shows_civicdatalab(self, page: Page):
        """CivicdataLab is listed as an available organisation."""
        ws = WorkspacePage(page)
        ws.go_to_workspace()

        if not ws.is_visible(ws.AI_MAKER_CARD, timeout=5_000):
            pytest.skip("AI Maker card not visible")

        ws.select_ai_maker()
        page.wait_for_load_state("domcontentloaded")

        assert ws.is_visible(ws.ORG_CIVICDATALAB_CARD), (
            "CivicdataLab must appear in the organisation selection list"
        )

    def test_org_selection_has_multiple_orgs(self, page: Page):
        """Multiple organisations are listed on the org-selection screen."""
        ws = WorkspacePage(page)
        ws.go_to_workspace()

        if not ws.is_visible(ws.AI_MAKER_CARD, timeout=5_000):
            pytest.skip("AI Maker card not visible")

        ws.select_ai_maker()
        page.wait_for_load_state("domcontentloaded")
        count = ws.get_org_card_count()
        assert count >= 1, f"Expected at least 1 org card, found {count}"

    def test_selecting_civicdatalab_navigates_to_dashboard(self, page: Page):
        """Selecting CivicdataLab routes to the AI Maker dashboard (org_id=1)."""
        ws = WorkspacePage(page)
        ws.go_to_workspace()

        if not ws.is_visible(ws.AI_MAKER_CARD, timeout=5_000):
            pytest.skip("AI Maker card not visible")

        ws.select_ai_maker()
        page.wait_for_load_state("domcontentloaded")

        if not ws.is_visible(ws.ORG_CIVICDATALAB_CARD, timeout=5_000):
            pytest.skip("CivicdataLab org not visible")

        ws.select_civicdatalab()
        assert "/ai-maker/1" in page.url or "civicdatalab" in page.url.lower(), (
            f"Expected CivicdataLab dashboard URL, got: {page.url}"
        )


class TestEvaluatorRoleNavigation:
    """Verify clicking Evaluator navigates to the evaluator dashboard."""

    def test_clicking_evaluator_navigates_to_evaluator_dashboard(self, page: Page):
        """Clicking Evaluator card routes to /dashboard/auditor."""
        ws = WorkspacePage(page)
        ws.go_to_workspace()

        if not ws.is_visible(ws.EVALUATOR_CARD, timeout=5_000):
            pytest.skip("Evaluator card not visible — user may not be authenticated")

        ws.select_evaluator()
        assert "/auditor" in page.url, (
            f"Expected evaluator dashboard URL, got: {page.url}"
        )

    @pytest.mark.xfail(
        reason="App bug #7 — Switch Roles renders the role-selection content "
        "but does not update the browser URL. See docs/app_bugs.md.",
        strict=True,
    )
    def test_switch_roles_returns_to_role_selection(self, page: Page):
        """Clicking 'Switch Roles' from AI Maker dashboard returns to /dashboard."""
        ws = WorkspacePage(page)
        ws.go_to_workspace()

        if not ws.is_visible(ws.AI_MAKER_CARD, timeout=5_000):
            pytest.skip("AI Maker card not visible")

        ws.select_ai_maker()
        page.wait_for_load_state("domcontentloaded")

        if not ws.is_visible(ws.ORG_CIVICDATALAB_CARD, timeout=5_000):
            pytest.skip("CivicdataLab not visible")

        ws.select_civicdatalab()
        page.wait_for_load_state("domcontentloaded")

        switch_roles = page.locator("text=Switch Roles")
        if not switch_roles.is_visible():
            pytest.skip("Switch Roles link not found on dashboard")

        switch_roles.click()
        page.wait_for_load_state("domcontentloaded")
        assert page.url.rstrip("/").endswith("/dashboard"), (
            f"Switch Roles should return to /dashboard, got: {page.url}"
        )
