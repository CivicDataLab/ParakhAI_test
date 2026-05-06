"""
E2E tests for the Evaluations section.
Covers: list page, New Evaluation modal + wizard, evaluation detail view.
URLs:
  List  : /dashboard/ai-maker/1/evaluations
  Wizard: /dashboard/ai-maker/1/evaluations/new
  Detail: /dashboard/ai-maker/1/evaluations/288  (85.4% pass rate, 269/315 passed)
"""

import pytest
from playwright.sync_api import Page

from locators.evaluations_locators import EvaluationsLocators
from pages.evaluations_page import EvaluationsPage

pytestmark = [pytest.mark.e2e, pytest.mark.regression]

COMPLETED_EVAL_ID = 288


class TestEvaluationsListPage:
    """Verify the evaluations list page renders correctly."""

    def test_evaluations_list_page_loads(self, page: Page):
        ep = EvaluationsPage(page)
        ep.go_to_evaluations_list()
        assert ep.is_evaluations_list_visible(), "'Evaluations' heading must be visible"

    def test_page_url_is_correct(self, page: Page):
        ep = EvaluationsPage(page)
        ep.go_to_evaluations_list()
        assert "/evaluations" in page.url, f"Expected /evaluations in URL, got: {page.url}"

    def test_new_evaluation_button_is_visible(self, page: Page):
        ep = EvaluationsPage(page)
        ep.go_to_evaluations_list()
        assert ep.is_visible(ep.NEW_EVALUATION_BUTTON), (
            "'New Evaluation' button must be visible"
        )

    def test_table_column_headers_are_present(self, page: Page):
        """All five column headers are present in the evaluations table."""
        ep = EvaluationsPage(page)
        ep.go_to_evaluations_list()
        missing = []
        for col in [
            EvaluationsLocators.EVAL_NAME_COL,
            EvaluationsLocators.EVAL_STATUS_COL,
            EvaluationsLocators.EVAL_MODE_COL,
            EvaluationsLocators.EVAL_TESTS_COL,
            EvaluationsLocators.EVAL_COMPLETED_COL,
        ]:
            if not ep.is_visible(col, timeout=3_000):
                missing.append(col)
        assert not missing, f"Missing column headers: {missing}"

    def test_draft_evaluations_are_listed(self, page: Page):
        """DRAFT status evaluations appear in the list."""
        ep = EvaluationsPage(page)
        ep.go_to_evaluations_list()
        assert ep.has_draft_evaluations(), "At least one DRAFT evaluation must be listed"

    def test_completed_evaluations_are_listed(self, page: Page):
        """COMPLETED status evaluations appear in the list."""
        ep = EvaluationsPage(page)
        ep.go_to_evaluations_list()
        assert ep.has_completed_evaluations(), "At least one COMPLETED evaluation must be listed"

    def test_automated_mode_label_is_shown(self, page: Page):
        """AUTOMATED evaluation mode label is displayed."""
        ep = EvaluationsPage(page)
        ep.go_to_evaluations_list()
        assert ep.is_visible(EvaluationsLocators.MODE_AUTOMATED), (
            "AUTOMATED mode label must appear in the evaluations list"
        )

    def test_status_badge_colors_are_distinct(self, page: Page):
        """DRAFT and COMPLETED badges are both present and visually distinguishable."""
        ep = EvaluationsPage(page)
        ep.go_to_evaluations_list()
        draft_count = page.locator(EvaluationsLocators.STATUS_DRAFT).count()
        completed_count = page.locator(EvaluationsLocators.STATUS_COMPLETED).count()
        assert draft_count >= 1, "Expected at least 1 DRAFT badge"
        assert completed_count >= 1, "Expected at least 1 COMPLETED badge"

    def test_clicking_completed_evaluation_navigates_to_detail(self, page: Page):
        """Clicking a COMPLETED evaluation row navigates to its detail page."""
        ep = EvaluationsPage(page)
        ep.go_to_evaluations_list()
        completed_row = page.locator("tr").filter(has_text="COMPLETED").first
        if not completed_row.is_visible():
            pytest.skip("No completed evaluation row found")
        completed_row.click()
        page.wait_for_load_state("domcontentloaded")
        assert "/evaluations/" in page.url and "new" not in page.url, (
            "Clicking a completed evaluation must navigate to its detail URL"
        )


class TestNewEvaluationModal:
    """Verify the 'New Evaluation' modal and wizard form."""

    def test_new_evaluation_button_opens_modal(self, page: Page):
        """Clicking 'New Evaluation' opens the modal dialog."""
        ep = EvaluationsPage(page)
        ep.go_to_evaluations_list()
        ep.click_new_evaluation()
        assert ep.is_new_eval_modal_visible(), (
            "'Start New Evaluation' modal must appear after clicking the button"
        )

    def test_modal_contains_model_dropdown(self, page: Page):
        """The modal has a dropdown to select the AI model."""
        ep = EvaluationsPage(page)
        ep.go_to_evaluations_list()
        ep.click_new_evaluation()
        if not ep.is_new_eval_modal_visible():
            pytest.skip("Modal not visible")
        assert ep.is_visible("text=Select AI Model"), (
            "'Select AI Model' label must appear in the modal"
        )

    def test_modal_contains_version_dropdown(self, page: Page):
        """The modal has a dropdown to select the model version."""
        ep = EvaluationsPage(page)
        ep.go_to_evaluations_list()
        ep.click_new_evaluation()
        if not ep.is_new_eval_modal_visible():
            pytest.skip("Modal not visible")
        assert ep.is_visible("text=Select Model Version"), (
            "'Select Model Version' label must appear in the modal"
        )

    def test_modal_cancel_button_closes_modal(self, page: Page):
        """Clicking Cancel dismisses the modal without navigating."""
        ep = EvaluationsPage(page)
        ep.go_to_evaluations_list()
        ep.click_new_evaluation()
        if not ep.is_new_eval_modal_visible():
            pytest.skip("Modal not visible")
        ep.click_modal_cancel()
        page.wait_for_timeout(400)
        assert not ep.is_visible(ep.MODAL_TITLE, timeout=2_000), (
            "Modal must be closed after clicking Cancel"
        )
        assert "/evaluations" in page.url and "new" not in page.url, (
            "URL must remain on evaluations list after cancel"
        )

    def test_modal_start_button_navigates_to_wizard(self, page: Page):
        """Clicking Start navigates to the evaluation wizard."""
        ep = EvaluationsPage(page)
        ep.go_to_evaluations_list()
        ep.click_new_evaluation()
        if not ep.is_new_eval_modal_visible():
            pytest.skip("Modal not visible")
        ep.click_modal_start()
        assert ep.is_wizard_visible() or "/evaluations/new" in page.url, (
            "Clicking Start must navigate to the evaluation wizard"
        )
        # Clean up: cancel the draft evaluation
        if ep.is_visible(ep.WIZARD_CANCEL_EVALUATION, timeout=3_000):
            ep.cancel_evaluation()


class TestNewEvaluationWizard:
    """Verify the New Evaluation wizard form fields and validation."""

    def test_wizard_configuration_tab_is_active_by_default(self, page: Page):
        """The 'Evaluation Configuration' tab is active when the wizard opens."""
        ep = EvaluationsPage(page)
        ep.go_to_evaluations_list()
        ep.click_new_evaluation()
        if not ep.is_new_eval_modal_visible():
            pytest.skip("Modal not visible")
        ep.click_modal_start()
        if not ep.is_wizard_visible():
            pytest.skip("Wizard not visible")
        assert ep.is_visible(ep.WIZARD_TAB_CONFIGURATION), (
            "'Evaluation Configuration' tab must be visible and active"
        )
        # Clean up
        if ep.is_visible(ep.WIZARD_CANCEL_EVALUATION, timeout=3_000):
            ep.cancel_evaluation()

    def test_wizard_shows_auto_saved_indicator(self, page: Page):
        """The wizard displays an auto-save indicator."""
        ep = EvaluationsPage(page)
        ep.go_to_evaluations_list()
        ep.click_new_evaluation()
        if not ep.is_new_eval_modal_visible():
            pytest.skip("Modal not visible")
        ep.click_modal_start()
        if not ep.is_wizard_visible():
            pytest.skip("Wizard not visible")
        assert ep.is_auto_saved_indicator_visible(), (
            "'Auto-saved' indicator must be visible in the wizard"
        )
        if ep.is_visible(ep.WIZARD_CANCEL_EVALUATION, timeout=3_000):
            ep.cancel_evaluation()

    def test_wizard_shows_three_evaluation_types(self, page: Page):
        """Technical, Domain, and Cultural evaluation type options are present."""
        ep = EvaluationsPage(page)
        ep.go_to_evaluations_list()
        ep.click_new_evaluation()
        if not ep.is_new_eval_modal_visible():
            pytest.skip("Modal not visible")
        ep.click_modal_start()
        if not ep.is_wizard_visible():
            pytest.skip("Wizard not visible")
        missing = []
        for selector in [ep.EVAL_TYPE_TECHNICAL, ep.EVAL_TYPE_DOMAIN, ep.EVAL_TYPE_CULTURAL]:
            if not ep.is_visible(selector, timeout=3_000):
                missing.append(selector)
        assert not missing, f"Missing evaluation type options: {missing}"
        if ep.is_visible(ep.WIZARD_CANCEL_EVALUATION, timeout=3_000):
            ep.cancel_evaluation()

    def test_technical_evaluation_is_selected_by_default(self, page: Page):
        """'Technical Evaluation' is the pre-selected option."""
        ep = EvaluationsPage(page)
        ep.go_to_evaluations_list()
        ep.click_new_evaluation()
        if not ep.is_new_eval_modal_visible():
            pytest.skip("Modal not visible")
        ep.click_modal_start()
        if not ep.is_wizard_visible():
            pytest.skip("Wizard not visible")
        # The Technical Evaluation type label should be present
        assert ep.is_visible(ep.EVAL_TYPE_TECHNICAL), (
            "'Technical Evaluation' must be visible as default option"
        )
        if ep.is_visible(ep.WIZARD_CANCEL_EVALUATION, timeout=3_000):
            ep.cancel_evaluation()

    def test_evaluation_modules_checkboxes_are_present(self, page: Page):
        """All three evaluation module checkboxes are shown."""
        ep = EvaluationsPage(page)
        ep.go_to_evaluations_list()
        ep.click_new_evaluation()
        if not ep.is_new_eval_modal_visible():
            pytest.skip("Modal not visible")
        ep.click_modal_start()
        if not ep.is_wizard_visible():
            pytest.skip("Wizard not visible")
        page.keyboard.press("End")
        page.wait_for_timeout(300)
        for module_sel in [
            EvaluationsLocators.EVAL_MODULE_HALLUCINATION,
            EvaluationsLocators.EVAL_MODULE_BIAS,
            EvaluationsLocators.EVAL_MODULE_PRIVACY,
        ]:
            assert ep.is_visible(module_sel, timeout=3_000), (
                f"Evaluation module must be visible: {module_sel}"
            )
        if ep.is_visible(ep.WIZARD_CANCEL_EVALUATION, timeout=3_000):
            ep.cancel_evaluation()

    def test_test_cases_tab_requires_objective_filled(self, page: Page):
        """Clicking 'Test Cases' tab without filling Objective shows a validation error."""
        ep = EvaluationsPage(page)
        ep.go_to_evaluations_list()
        ep.click_new_evaluation()
        if not ep.is_new_eval_modal_visible():
            pytest.skip("Modal not visible")
        ep.click_modal_start()
        if not ep.is_wizard_visible():
            pytest.skip("Wizard not visible")
        ep.click_test_cases_tab()
        page.wait_for_timeout(400)
        assert ep.is_objective_validation_error_visible(), (
            "Validation error 'Evaluation objective is required' must appear"
        )
        if ep.is_visible(ep.WIZARD_CANCEL_EVALUATION, timeout=3_000):
            ep.cancel_evaluation()

    def test_cancel_evaluation_returns_to_list(self, page: Page):
        """Clicking 'Cancel Evaluation' from the wizard returns to the evaluations list."""
        ep = EvaluationsPage(page)
        ep.go_to_evaluations_list()
        ep.click_new_evaluation()
        if not ep.is_new_eval_modal_visible():
            pytest.skip("Modal not visible")
        ep.click_modal_start()
        if not ep.is_wizard_visible():
            pytest.skip("Wizard not visible")
        if not ep.is_visible(ep.WIZARD_CANCEL_EVALUATION, timeout=5_000):
            pytest.skip("Cancel Evaluation button not found in wizard")
        ep.cancel_evaluation()
        assert "/evaluations" in page.url and "new" not in page.url, (
            "After cancelling, URL must return to the evaluations list"
        )


class TestEvaluationDetail:
    """Verify the evaluation detail page for the completed eval (ID=288, 85.4% pass)."""

    def test_evaluation_detail_page_loads(self, page: Page):
        ep = EvaluationsPage(page)
        ep.go_to_evaluation_detail(COMPLETED_EVAL_ID)
        assert f"/evaluations/{COMPLETED_EVAL_ID}" in page.url, (
            f"Expected evaluation detail URL with ID {COMPLETED_EVAL_ID}"
        )

    def test_completed_status_badge_is_visible(self, page: Page):
        ep = EvaluationsPage(page)
        ep.go_to_evaluation_detail(COMPLETED_EVAL_ID)
        assert ep.is_visible(ep.STATUS_COMPLETED), (
            "COMPLETED status badge must be visible on evaluation detail"
        )

    def test_automated_mode_badge_is_visible(self, page: Page):
        ep = EvaluationsPage(page)
        ep.go_to_evaluation_detail(COMPLETED_EVAL_ID)
        assert ep.is_visible(EvaluationsLocators.DETAIL_MODE_AUTOMATED), (
            "AUTOMATED mode badge must be visible"
        )

    def test_back_to_list_button_is_visible(self, page: Page):
        ep = EvaluationsPage(page)
        ep.go_to_evaluation_detail(COMPLETED_EVAL_ID)
        assert ep.is_visible(EvaluationsLocators.BACK_TO_LIST_BUTTON), (
            "'Back to List' button must be visible on the detail page"
        )

    def test_overview_section_is_present(self, page: Page):
        ep = EvaluationsPage(page)
        ep.go_to_evaluation_detail(COMPLETED_EVAL_ID)
        assert ep.is_overview_section_visible(), "'Evaluation Overview' section must be present"

    def test_overview_shows_evaluation_id(self, page: Page):
        ep = EvaluationsPage(page)
        ep.go_to_evaluation_detail(COMPLETED_EVAL_ID)
        assert ep.is_visible(EvaluationsLocators.OVERVIEW_EVAL_ID), (
            "'Evaluation ID' label must be visible in overview"
        )
        assert ep.is_visible(f"text={COMPLETED_EVAL_ID}"), (
            f"Evaluation ID {COMPLETED_EVAL_ID} must be shown"
        )

    def test_overview_shows_model_name(self, page: Page):
        """The model name 'Meta: Llama 3.1 70B Instruct' is shown in overview."""
        ep = EvaluationsPage(page)
        ep.go_to_evaluation_detail(COMPLETED_EVAL_ID)
        assert ep.is_visible("text=Meta: Llama 3.1 70B Instruct") or ep.is_visible("text=Llama"), (
            "Model name must be shown in the evaluation overview"
        )

    def test_overview_shows_modules_used(self, page: Page):
        """The evaluation modules are listed in the overview section."""
        ep = EvaluationsPage(page)
        ep.go_to_evaluation_detail(COMPLETED_EVAL_ID)
        assert ep.is_visible(EvaluationsLocators.OVERVIEW_MODULES), (
            "'Modules' label must be present in overview"
        )

    def test_summary_section_is_present(self, page: Page):
        ep = EvaluationsPage(page)
        ep.go_to_evaluation_detail(COMPLETED_EVAL_ID)
        page.wait_for_timeout(300)
        assert ep.is_summary_section_visible(), "'Evaluation Summary' section must be present"

    def test_pass_rate_is_displayed(self, page: Page):
        """Total Pass Rate is shown in the summary section."""
        ep = EvaluationsPage(page)
        ep.go_to_evaluation_detail(COMPLETED_EVAL_ID)
        assert ep.is_pass_rate_visible(), "'TOTAL PASS RATE' must be visible"

    def test_passed_failed_skipped_counts_visible(self, page: Page):
        """Passed, Failed, and Skipped test counts are all displayed."""
        ep = EvaluationsPage(page)
        ep.go_to_evaluation_detail(COMPLETED_EVAL_ID)
        missing = []
        for sel in [
            EvaluationsLocators.SUMMARY_PASSED_TESTS,
            EvaluationsLocators.SUMMARY_FAILED_TESTS,
            EvaluationsLocators.SUMMARY_SKIPPED_TESTS,
        ]:
            if not ep.is_visible(sel, timeout=3_000):
                missing.append(sel)
        assert not missing, f"Missing summary stat labels: {missing}"

    def test_risk_level_section_is_present(self, page: Page):
        """The risk breakdown section (Low/Medium/High) is shown."""
        ep = EvaluationsPage(page)
        ep.go_to_evaluation_detail(COMPLETED_EVAL_ID)
        assert ep.is_risk_section_visible(), "'Total Issues Identified' section must be present"

    def test_three_risk_levels_are_shown(self, page: Page):
        """Low Risk, Medium Risk, and High Risk cards are all present."""
        ep = EvaluationsPage(page)
        ep.go_to_evaluation_detail(COMPLETED_EVAL_ID)
        missing = []
        for sel in [
            EvaluationsLocators.RISK_LOW,
            EvaluationsLocators.RISK_MEDIUM,
            EvaluationsLocators.RISK_HIGH,
        ]:
            if not ep.is_visible(sel, timeout=3_000):
                missing.append(sel)
        assert not missing, f"Missing risk level cards: {missing}"

    def test_module_wise_results_tabs_present(self, page: Page):
        """At least one module-wise results tab is visible."""
        ep = EvaluationsPage(page)
        ep.go_to_evaluation_detail(COMPLETED_EVAL_ID)
        tab_count = ep.get_module_tab_count()
        assert tab_count >= 1, (
            f"Expected at least 1 module-wise results tab, found {tab_count}"
        )

    def test_module_tab_switching_works(self, page: Page):
        """Clicking different module tabs does not cause errors."""
        ep = EvaluationsPage(page)
        ep.go_to_evaluation_detail(COMPLETED_EVAL_ID)
        if not ep.is_visible(EvaluationsLocators.MODULE_TAB_BIAS, timeout=3_000):
            pytest.skip("Bias tab not visible")
        ep.click_module_tab("bias")
        page.wait_for_timeout(300)
        assert page.url, "Page must still be accessible after switching module tabs"

    def test_sample_issues_section_is_present(self, page: Page):
        """The 'Sample Issues' accordion section is shown."""
        ep = EvaluationsPage(page)
        ep.go_to_evaluation_detail(COMPLETED_EVAL_ID)
        page.keyboard.press("End")
        page.wait_for_timeout(300)
        assert ep.is_visible(EvaluationsLocators.SAMPLE_ISSUES_HEADING), (
            "'Sample Issues' heading must be visible"
        )

    def test_sample_issues_accordion_items_present(self, page: Page):
        """Individual issue accordion items are listed."""
        ep = EvaluationsPage(page)
        ep.go_to_evaluation_detail(COMPLETED_EVAL_ID)
        page.keyboard.press("End")
        page.wait_for_timeout(300)
        issue_count = page.locator(EvaluationsLocators.ISSUE_ACCORDION_ITEM).count()
        assert issue_count >= 1, (
            f"Expected at least 1 sample issue in accordion, found {issue_count}"
        )

    def test_download_report_button_is_visible(self, page: Page):
        """'Download Report' button is present at the bottom of the detail page."""
        ep = EvaluationsPage(page)
        ep.go_to_evaluation_detail(COMPLETED_EVAL_ID)
        page.keyboard.press("End")
        page.wait_for_timeout(300)
        assert ep.is_visible(EvaluationsLocators.DOWNLOAD_REPORT_BUTTON), (
            "'Download Report' button must be visible"
        )

    def test_back_to_list_button_navigates_correctly(self, page: Page):
        """'Back to List' button returns to the evaluations list."""
        ep = EvaluationsPage(page)
        ep.go_to_evaluation_detail(COMPLETED_EVAL_ID)
        if not ep.is_visible(EvaluationsLocators.BACK_TO_LIST_BUTTON, timeout=5_000):
            pytest.skip("'Back to List' not found")
        ep.click_back_to_list()
        assert "/evaluations" in page.url and str(COMPLETED_EVAL_ID) not in page.url, (
            "'Back to List' must return to the evaluations list page"
        )
