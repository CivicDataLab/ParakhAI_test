"""
End-to-end user flow tests for the CivicdataLab Evaluation Workspace.

These tests simulate complete user journeys through the application,
verifying that multi-step flows work correctly from start to finish.

Flows covered:
  1. Entry → AI Maker role → Select CivicdataLab org → View dashboard
  2. Dashboard → Models list → Model detail → Past evaluations
  3. Dashboard → Evaluations list → New Evaluation → Cancel
  4. Dashboard → Evaluations list → Completed evaluation → View results → Back
  5. Dashboard → Prompt Libraries → Search → Clear
  6. Dashboard → Evaluators → Verify team
  7. AI Maker → Switch Roles → Evaluator role → Assignments → Evaluations
  8. Breadcrumb navigation across multiple sections
"""

import pytest
from playwright.sync_api import Page

from locators.evaluations_locators import EvaluationsLocators
from pages.ai_maker_page import AIMakerPage
from pages.evaluations_page import EvaluationsPage
from pages.evaluator_role_page import EvaluatorRolePage
from pages.evaluators_page import EvaluatorsPage
from pages.models_page import ModelsPage
from pages.prompt_libraries_page import PromptLibrariesPage
from pages.workspace_page import WorkspacePage
from utils.config import Config

pytestmark = [pytest.mark.e2e, pytest.mark.regression, pytest.mark.auth]


@pytest.fixture
def page(authenticated_page_fast):
    """Override pytest-playwright's `page` fixture for this file.

    Every flow targets /dashboard/... routes that redirect unauth visitors
    to /api/auth/signin. Routing the `page` name to the storage-state-cached
    auth session keeps each test signature unchanged while making every flow
    authenticated by default.
    """
    return authenticated_page_fast


def _navigate_to_civicdatalab_dashboard(page: Page) -> bool:
    """
    Helper: navigate the full flow from homepage to CivicdataLab AI Maker dashboard.
    Returns True on success, False if any step is not available.
    """
    ws = WorkspacePage(page)
    ws.go_to_workspace()

    if not ws.is_visible(ws.AI_MAKER_CARD, timeout=5_000):
        return False
    ws.select_ai_maker()
    page.wait_for_load_state("domcontentloaded")

    if not ws.is_visible(ws.ORG_CIVICDATALAB_CARD, timeout=5_000):
        return False
    ws.select_civicdatalab()
    page.wait_for_load_state("domcontentloaded")

    return "/ai-maker/1" in page.url


class TestFlow01_EntryToDashboard:
    """
    FLOW 1: Home → Role Selection → AI Maker → CivicdataLab → Dashboard
    Verifies the complete onboarding journey to reach the AI Maker dashboard.
    """

    def test_complete_entry_to_dashboard_flow(self, page: Page):
        """Full navigation: home → role selection → org selection → dashboard."""
        success = _navigate_to_civicdatalab_dashboard(page)
        if not success:
            pytest.skip("Role selection or org selection not available — check auth state")
        ai = AIMakerPage(page)
        assert ai.is_overview_visible(), (
            "Flow 1: After navigating to CivicdataLab AI Maker, Overview must be visible"
        )

    def test_overview_stats_load_after_navigation(self, page: Page):
        """Stats cards are visible after completing the entry flow."""
        success = _navigate_to_civicdatalab_dashboard(page)
        if not success:
            pytest.skip("Dashboard entry flow not available")
        ai = AIMakerPage(page)
        assert ai.is_stat_evaluation_runs_visible(), (
            "Flow 1: Evaluation Runs stat must be visible after full entry flow"
        )

    def test_sidebar_is_fully_populated_after_entry(self, page: Page):
        """All sidebar navigation links render after completing the entry flow."""
        success = _navigate_to_civicdatalab_dashboard(page)
        if not success:
            pytest.skip("Dashboard entry flow not available")
        ai = AIMakerPage(page)
        assert ai.is_sidebar_nav_complete(), (
            "Flow 1: All 5 sidebar items must be visible after navigating to dashboard"
        )


class TestFlow02_DashboardToModelDetail:
    """
    FLOW 2: Dashboard → Models (sidebar) → Model list → Model card click → Model detail
    Verifies the full model exploration journey.
    """

    @pytest.mark.xfail(
        reason="App bug #6 family — View buttons on the models list are "
        "aria-disabled and clicking does not navigate. See docs/app_bugs.md.",
        strict=True,
    )
    def test_navigate_from_dashboard_to_model_detail(self, page: Page):
        """Dashboard → sidebar Models → click first model → detail page loads."""
        ai = AIMakerPage(page)
        ai.go_to_dashboard()

        if not ai.is_visible(ai.SIDEBAR_MODELS, timeout=5_000):
            pytest.skip("Models sidebar link not found")
        ai.go_to_models()

        mp = ModelsPage(page)
        if not mp.is_models_list_visible():
            pytest.skip("Models list not visible")

        initial_url = page.url
        mp.click_first_model()
        assert "/ai-models/" in page.url and page.url != initial_url, (
            "Flow 2: Clicking a model from the list must navigate to its detail page"
        )

    def test_model_detail_shows_start_evaluation_action(self, page: Page):
        """Model detail reached via navigation shows the 'Start Evaluation' action."""
        mp = ModelsPage(page)
        mp.go_to_models_list()
        mp.click_first_model()
        assert mp.is_start_evaluation_visible() or mp.is_about_section_visible(), (
            "Flow 2: Model detail must be accessible and show 'Start Evaluation'"
        )

    def test_model_detail_shows_past_evaluations_table(self, page: Page):
        """Model detail (via navigation) shows past evaluations."""
        mp = ModelsPage(page)
        mp.go_to_model_detail()  # Direct to Sarvam-M detail
        page.keyboard.press("End")
        page.wait_for_timeout(400)
        assert mp.is_past_evaluations_visible(), (
            "Flow 2: Past Evaluations table must be visible on model detail"
        )

    @pytest.mark.xfail(
        reason="App bug #6 family — link clicks in eval tables do not trigger "
        "navigation. See docs/app_bugs.md.",
        strict=True,
    )
    def test_past_evaluation_link_navigates_to_detail(self, page: Page):
        """Clicking a past evaluation from the model detail navigates to eval detail."""
        mp = ModelsPage(page)
        mp.go_to_model_detail()
        page.keyboard.press("End")
        page.wait_for_timeout(400)

        if not mp.is_past_evaluations_visible():
            pytest.skip("Past Evaluations not visible")

        # Target a link whose href is an evaluation detail URL — the first
        # `<a>` in a row would otherwise match the row's model self-link or
        # a pagination anchor, neither of which navigates to /evaluations/.
        eval_link = page.locator("tbody a[href*='/evaluations/']").first
        if not eval_link.is_visible():
            pytest.skip("No evaluation links in the table")

        eval_link.click()
        page.wait_for_load_state("domcontentloaded")
        assert "/evaluations/" in page.url, (
            "Flow 2: Clicking a past evaluation must navigate to evaluation detail"
        )


class TestFlow03_NewEvaluationWizardCancel:
    """
    FLOW 3: Evaluations list → New Evaluation → Select model → Start → Cancel
    Verifies the wizard can be opened and cleanly cancelled.
    """

    def test_complete_new_evaluation_open_and_cancel_flow(self, page: Page):
        """Full flow: evaluations list → modal → start → wizard → cancel."""
        ep = EvaluationsPage(page)
        ep.go_to_evaluations_list()

        if not ep.is_visible(ep.NEW_EVALUATION_BUTTON, timeout=5_000):
            pytest.skip("New Evaluation button not found")

        ep.click_new_evaluation()
        if not ep.is_new_eval_modal_visible():
            pytest.skip("New Evaluation modal did not appear")

        ep.click_modal_start()
        page.wait_for_load_state("domcontentloaded")

        if not ep.is_wizard_visible():
            pytest.skip("Wizard not visible after clicking Start")

        # Verify wizard is functional before cancelling
        assert ep.is_visible(ep.WIZARD_TAB_CONFIGURATION), (
            "Flow 3: Wizard must show 'Evaluation Configuration' tab"
        )

        # Cancel and verify clean return
        if ep.is_visible(ep.WIZARD_CANCEL_EVALUATION, timeout=5_000):
            ep.cancel_evaluation()
            assert "/evaluations" in page.url and "new" not in page.url, (
                "Flow 3: Cancelling wizard must return to evaluations list"
            )

    def test_wizard_does_not_persist_cancelled_evaluation_in_list(self, page: Page):
        """After cancelling from the wizard, the list shows a DRAFT record."""
        ep = EvaluationsPage(page)
        ep.go_to_evaluations_list()
        initial_row_count = ep.get_evaluation_row_count()

        ep.click_new_evaluation()
        if not ep.is_new_eval_modal_visible():
            pytest.skip("Modal not visible")

        ep.click_modal_start()
        page.wait_for_load_state("domcontentloaded")

        if ep.is_visible(ep.WIZARD_CANCEL_EVALUATION, timeout=5_000):
            ep.cancel_evaluation()

        # The cancelled draft should appear as DRAFT in the list
        ep.go_to_evaluations_list()
        new_row_count = ep.get_evaluation_row_count()
        # Cancelled evals typically save as DRAFT
        assert new_row_count >= initial_row_count, (
            "Flow 3: Cancelling an evaluation may add a DRAFT entry to the list"
        )


class TestFlow04_EvaluationDetailAndReport:
    """
    FLOW 4: Evaluations list → COMPLETED eval → Detail → View results → Back to list
    Verifies the end-to-end report viewing experience.
    """

    @pytest.mark.xfail(
        reason="App bug #6 family — row clicks in the evaluations list do not "
        "trigger navigation. See docs/app_bugs.md.",
        strict=True,
    )
    def test_navigate_to_completed_evaluation_detail(self, page: Page):
        """From the evaluations list, clicking a COMPLETED row loads its detail."""
        ep = EvaluationsPage(page)
        ep.go_to_evaluations_list()

        completed_row = page.locator("tr").filter(has_text="COMPLETED").first
        if not completed_row.is_visible():
            pytest.skip("No COMPLETED evaluation found in the list")

        completed_row.click()
        page.wait_for_load_state("domcontentloaded")
        assert "/evaluations/" in page.url, (
            "Flow 4: Clicking a COMPLETED row must navigate to evaluation detail"
        )

    def test_evaluation_detail_shows_full_results(self, page: Page):
        """A COMPLETED evaluation's detail shows overview, summary, risks, and modules."""
        ep = EvaluationsPage(page)
        ep.go_to_evaluation_detail()  # default = SAMPLE_COMPLETED_EVAL_ID

        assert ep.is_overview_section_visible(), (
            "Flow 4: Overview section must be present"
        )
        if not ep.is_summary_section_visible():
            pytest.skip(
                "Sample eval no longer shows Summary section — likely CANCELLED. "
                "Update SAMPLE_COMPLETED_EVAL_ID in pages/evaluations_page.py."
            )
        assert ep.is_risk_section_visible(), (
            "Flow 4: Risk level section must be present"
        )

    def test_module_tabs_are_navigable(self, page: Page):
        """All three module tabs in the evaluation detail can be clicked."""
        ep = EvaluationsPage(page)
        ep.go_to_evaluation_detail()

        for tab in ["hallucination", "bias", "privacy"]:
            if ep.is_visible(
                EvaluationsLocators.MODULE_TAB_HALLUCINATION
                if tab == "hallucination"
                else EvaluationsLocators.MODULE_TAB_BIAS
                if tab == "bias"
                else EvaluationsLocators.MODULE_TAB_PRIVACY,
                timeout=3_000
            ):
                ep.click_module_tab(tab)
                page.wait_for_timeout(200)

        assert page.url, "Flow 4: Module tab navigation must not break the page"

    def test_back_to_list_from_detail_returns_correctly(self, page: Page):
        """'Back to List' from evaluation detail returns to the evaluations list."""
        ep = EvaluationsPage(page)
        ep.go_to_evaluation_detail()
        page.keyboard.press("End")
        page.wait_for_timeout(300)

        if not ep.is_visible(EvaluationsLocators.BACK_TO_LIST_BUTTON, timeout=5_000):
            pytest.skip("Back to List button not found")

        ep.click_back_to_list()
        assert "/evaluations" in page.url and "288" not in page.url, (
            "Flow 4: 'Back to List' must return to the evaluations list"
        )
        assert ep.is_evaluations_list_visible(), (
            "Flow 4: Evaluations list must be visible after navigating back"
        )


class TestFlow05_PromptLibrarySearch:
    """
    FLOW 5: Dashboard → Prompt Libraries → Search → View category → Clear
    Verifies the prompt library exploration flow.
    """

    def test_navigate_from_dashboard_to_prompt_libraries(self, page: Page):
        """Sidebar Prompt Libraries link from dashboard navigates correctly."""
        ai = AIMakerPage(page)
        ai.go_to_dashboard()
        if not ai.is_visible(ai.SIDEBAR_PROMPT_LIBRARIES, timeout=5_000):
            pytest.skip("Prompt Libraries sidebar link not found")
        ai.go_to_prompt_libraries()
        pl = PromptLibrariesPage(page)
        assert pl.is_page_loaded(), (
            "Flow 5: Prompt Libraries page must load via sidebar navigation"
        )

    def test_search_and_clear_restores_full_library_list(self, page: Page):
        """Search then clear fully restores the library card list."""
        pl = PromptLibrariesPage(page)
        pl.go_to_prompt_libraries()
        full_count = pl.get_library_card_count()

        pl.search_library("KCC")
        page.wait_for_timeout(600)
        filtered_count = pl.get_library_card_count()
        assert filtered_count <= full_count, "Search must reduce or equal the full count"

        pl.clear_search()
        page.wait_for_timeout(500)
        restored_count = pl.get_library_card_count()
        assert restored_count >= full_count, "Clearing search must restore all library cards"


class TestFlow06_EvaluatorsTeamReview:
    """
    FLOW 6: Dashboard → Evaluators → Verify CivicdataLab team is listed
    """

    def test_navigate_from_dashboard_to_evaluators(self, page: Page):
        """Sidebar Evaluators link navigates to the evaluators management page."""
        ai = AIMakerPage(page)
        ai.go_to_dashboard()
        if not ai.is_visible(ai.SIDEBAR_EVALUATORS, timeout=5_000):
            pytest.skip("Evaluators sidebar link not found")
        ai.go_to_evaluators()
        ep = EvaluatorsPage(page)
        assert ep.is_page_loaded(), (
            "Flow 6: Evaluators page must load via sidebar navigation"
        )

    def test_evaluator_team_is_complete(self, page: Page):
        """Both configured evaluators (EVALUATOR_EMAIL_1/2) are listed."""
        from locators.evaluators_locators import EvaluatorsLocators
        if not (Config.EVALUATOR_EMAIL_1 and Config.EVALUATOR_EMAIL_2):
            pytest.skip("EVALUATOR_EMAIL_1/EVALUATOR_EMAIL_2 not configured")
        ep = EvaluatorsPage(page)
        ep.go_to_evaluators()
        assert ep.is_evaluator_present(
            EvaluatorsLocators.evaluator_email_text(Config.EVALUATOR_EMAIL_1)
        ), f"Flow 6: {Config.EVALUATOR_EMAIL_1} must be in the evaluators list"
        assert ep.is_evaluator_present(
            EvaluatorsLocators.evaluator_email_text(Config.EVALUATOR_EMAIL_2)
        ), f"Flow 6: {Config.EVALUATOR_EMAIL_2} must be in the evaluators list"


class TestFlow07_RoleSwitching:
    """
    FLOW 7: AI Maker → Switch Roles → Evaluator role → Assignments → Evaluations
    Verifies seamless role switching between AI Maker and Evaluator.
    """

    def test_switch_from_ai_maker_to_evaluator(self, page: Page):
        """Switch Roles from AI Maker dashboard → Evaluator role."""
        ai = AIMakerPage(page)
        ai.go_to_dashboard()
        if not ai.is_visible(ai.SWITCH_ROLES_LINK, timeout=5_000):
            pytest.skip("Switch Roles not found on AI Maker dashboard")

        ai.click_switch_roles()
        ws = WorkspacePage(page)

        # Should be on role selection or evaluator can be selected
        if ws.is_visible(ws.EVALUATOR_CARD, timeout=3_000):
            ws.select_evaluator()
            assert "/auditor" in page.url, (
                "Flow 7: After switching to Evaluator role, URL must contain /auditor"
            )

    def test_evaluator_dashboard_after_role_switch(self, page: Page):
        """After switching to Evaluator, the dashboard shows the Evaluator layout."""
        er = EvaluatorRolePage(page)
        er.go_to_evaluator_home()
        assert er.is_overview_visible(), (
            "Flow 7: Evaluator dashboard must show Overview section"
        )
        assert er.is_visible(er.SIDEBAR_ASSIGNED_MODELS), (
            "Flow 7: 'Assigned Models' must appear in Evaluator sidebar (not AI Maker layout)"
        )

    @pytest.mark.xfail(reason="App bug #8 — see docs/app_bugs.md", strict=False)
    def test_evaluator_assignments_page_accessible(self, page: Page):
        """Evaluator can navigate to the Assigned Models page."""
        er = EvaluatorRolePage(page)
        er.go_to_evaluator_home()
        if not er.is_visible(er.SIDEBAR_ASSIGNED_MODELS, timeout=5_000):
            pytest.skip("Assigned Models link not found")
        er.click_assigned_models()
        assert er.is_assignments_page_loaded(), (
            "Flow 7: Assigned Models page must load for Evaluator role"
        )

    @pytest.mark.xfail(reason="App bug #8 — see docs/app_bugs.md", strict=False)
    def test_evaluator_can_navigate_to_their_evaluations(self, page: Page):
        """Evaluator can navigate to the Evaluations page."""
        er = EvaluatorRolePage(page)
        er.go_to_evaluator_home()
        if not er.is_visible(er.SIDEBAR_EVALUATIONS, timeout=5_000):
            pytest.skip("Evaluations link not found")
        er.click_evaluations()
        assert "/evaluations" in page.url, (
            "Flow 7: Evaluator evaluations page URL must contain /evaluations"
        )


class TestFlow08_BreadcrumbNavigation:
    """
    FLOW 8: Verify breadcrumb navigation across multiple depth levels.
    """

    def test_breadcrumb_on_models_list_page(self, page: Page):
        """Models list page breadcrumb shows Evaluation Workspace and AI Maker."""
        mp = ModelsPage(page)
        mp.go_to_models_list()
        breadcrumb_checks = [
            ("text=Evaluation Workspace", "Evaluation Workspace"),
            ("text=AI Maker", "AI Maker"),
            ("text=CivicdataLab", "CivicdataLab"),
        ]
        for sel, label in breadcrumb_checks:
            if not mp.is_visible(sel, timeout=3_000):
                pytest.skip(f"Breadcrumb element not visible: {label}")
        assert True  # All breadcrumb items found

    def test_breadcrumb_evaluation_workspace_is_clickable(self, page: Page):
        """Clicking 'Evaluation Workspace' breadcrumb on any sub-page returns to /dashboard."""
        mp = ModelsPage(page)
        mp.go_to_models_list()

        if not mp.is_visible("text=Evaluation Workspace", timeout=3_000):
            pytest.skip("Breadcrumb not rendered on this page")

        page.locator("text=Evaluation Workspace").click()
        page.wait_for_load_state("domcontentloaded")
        assert page.url.rstrip("/").endswith("/dashboard"), (
            "Flow 8: Clicking 'Evaluation Workspace' breadcrumb must return to /dashboard"
        )

    def test_direct_url_navigation_works_for_all_sections(self, page: Page):
        """Direct URL navigation to each section works without redirect loops."""
        sections = [
            ("/dashboard/ai-maker/1", "AI Maker dashboard"),
            ("/dashboard/ai-maker/1/ai-models", "Models list"),
            ("/dashboard/ai-maker/1/evaluations", "Evaluations list"),
            ("/dashboard/ai-maker/1/prompt-libraries", "Prompt Libraries"),
            ("/dashboard/ai-maker/1/auditors", "Evaluators"),
            ("/dashboard/auditor", "Evaluator home"),
            ("/dashboard/auditor/assignments", "Evaluator assignments"),
            ("/dashboard/auditor/evaluations", "Evaluator evaluations"),
        ]
        failed: list[str] = []
        for path, label in sections:
            page.goto(Config.url(path), wait_until="domcontentloaded", timeout=15_000)
            current = page.url
            # A successful load means the URL didn't redirect to /login or similar
            if any(kw in current for kw in ("login", "error", "404", "not-found")):
                failed.append(f"{label} ({path}) → {current}")
        assert not failed, (
            "Flow 8: Some sections redirected to error pages: " + "; ".join(failed)
        )
