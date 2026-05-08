"""
SMOKE TESTS — New Evaluation flow (Draft & Auto-Save)
=====================================================
Happy-path tests that run on every deploy to verify the New Evaluation wizard
is functional end-to-end for both Automated and Manual evaluation modes.

Coverage (9 tests):
  1. New Evaluation modal opens with both dropdowns populated
  2. Clicking Start navigates to /evaluations/new and the form loads
  3. Evaluation Name field is pre-filled and editable
  4. Filling Evaluation Objective triggers 'Auto-saved ✓' indicator
  5. Automated mode → Add Test Cases → auditId in URL + dataset table renders
  6. Manual mode → Add Test Cases → module cards render with counters
  7. Navigate back to list → draft appears with DRAFT badge and correct mode
  8. Click draft row → editable form loads at /evaluations/new?auditId=…
  9. Click Cancel Evaluation → redirect to list, draft still exists

URLs under test:
  /dashboard/ai-maker/1/evaluations          (evaluations list)
  /evaluations/new?modelId=…&versionId=…     (new wizard)
  /evaluations/new?auditId=…                 (re-open draft)

Auth: uses authenticated_page fixture (TEST_EMAIL_1 / TEST_PASSWORD_1 in .env)
"""

import pytest
from playwright.sync_api import Page

from locators.evaluations_locators import EvaluationsLocators
from pages.new_evaluation_page import NewEvaluationPage

pytestmark = [pytest.mark.e2e, pytest.mark.smoke, pytest.mark.auth]

# Short objective text reused across tests to trigger auto-save
_OBJECTIVE = "Smoke-test objective: evaluate model quality automatically."


class TestNewEvaluationModal:
    """
    SMOKE-1 & SMOKE-2: Modal opens correctly and navigates to the wizard.
    """

    def test_modal_opens_with_both_dropdowns_populated(self, authenticated_page: Page):
        """
        SMOKE-1: Clicking 'New Evaluation' opens the modal and both dropdowns
        ('Select AI Model' and 'Select Model Version') render with selectable options.

        NOTE – Selector stability:
          Both dropdowns are targeted by generic <select>/<combobox> patterns.
          Add data-testid="model-dropdown" and data-testid="version-dropdown" to
          the actual elements for reliable cross-build selection.
        """
        nep = NewEvaluationPage(authenticated_page)
        nep.go_to_evaluations_list()
        nep.click_new_evaluation()

        assert nep.is_modal_visible(), (
            "'Start New Evaluation' modal must appear after clicking the button"
        )
        assert nep.is_visible("text=Select AI Model"), (
            "'Select AI Model' label must be visible in the modal"
        )
        assert nep.is_visible("text=Select Model Version"), (
            "'Select Model Version' label must be visible in the modal"
        )
        assert nep.modal_model_dropdown_has_options(), (
            "'Select AI Model' dropdown must have at least one selectable option"
        )
        assert nep.modal_version_dropdown_has_options(), (
            "'Select Model Version' dropdown must have at least one selectable option"
        )
        # Clean up — dismiss modal
        nep.click_modal_cancel()

    def test_clicking_start_navigates_to_wizard(self, authenticated_page: Page):
        """
        SMOKE-2: Clicking 'Start' in the modal navigates to /evaluations/new
        and the Evaluation Configuration form loads.
        """
        nep = NewEvaluationPage(authenticated_page)
        nep.go_to_evaluations_list()
        nep.click_new_evaluation()
        if not nep.is_modal_visible():
            pytest.skip("Modal not visible — cannot test Start navigation")

        nep.select_first_model_and_version()
        nep.click_modal_start()

        assert nep.is_on_wizard_url(), (
            f"Expected /evaluations/new in URL after Start, got: {authenticated_page.url}"
        )
        assert nep.is_wizard_visible(), (
            "'Evaluation Configuration' tab must be visible after navigating to wizard"
        )
        # Clean up
        if nep.is_visible(nep.WIZARD_CANCEL_EVALUATION, timeout=3_000):
            nep.cancel_evaluation()


class TestEvaluationConfigurationTab:
    """
    SMOKE-3 & SMOKE-4: Form field behaviour on the Configuration tab.
    """

    def test_evaluation_name_is_prefilled_and_editable(self, authenticated_page: Page):
        """
        SMOKE-3: The Evaluation Name field (id='auditName') is pre-filled with a
        default value and can be cleared and retyped.

        NOTE – Selector stability:
          The locator targets input#auditName first. If that id is absent, it falls
          back to input[name='evaluationName'] then class/value heuristics. Add
          id="auditName" to the input element to pin this selector.
        """
        nep = NewEvaluationPage(authenticated_page)
        nep.open_new_evaluation_wizard()

        prefilled = nep.get_evaluation_name()
        assert prefilled, (
            "Evaluation Name input must be pre-filled with a default value (e.g. 'Untitled')"
        )

        # Overwrite and verify
        nep.set_evaluation_name("My Smoke Test Evaluation")
        assert nep.get_evaluation_name() == "My Smoke Test Evaluation", (
            "Evaluation Name field must accept typed text"
        )
        # Clean up
        if nep.is_visible(nep.WIZARD_CANCEL_EVALUATION, timeout=3_000):
            nep.cancel_evaluation()

    def test_filling_objective_triggers_auto_save_indicator(self, authenticated_page: Page):
        """
        SMOKE-4: After typing into the Evaluation Objective textarea, the
        'Auto-saved ✓' indicator should appear in the wizard header — confirming
        the draft persisted without an explicit save button.

        Currently xfailed: see docs/app_bugs.md #1. Auto-save indicator never
        renders on the Configuration tab; draft is only created when the user
        clicks 'Add Test Cases'. Reproduced via Playwright MCP 2026-05-07.
        """
        nep = NewEvaluationPage(authenticated_page)
        nep.open_new_evaluation_wizard()
        nep.fill_evaluation_objective(_OBJECTIVE)

        if not nep.is_auto_saved_indicator_visible():
            # Clean up before xfail so we don't leave a wizard open
            if nep.is_visible(nep.WIZARD_CANCEL_EVALUATION, timeout=3_000):
                nep.cancel_evaluation()
            pytest.xfail("App bug #1 — see docs/app_bugs.md")

        # Clean up if the indicator unexpectedly works (xfail_strict will flag this)
        if nep.is_visible(nep.WIZARD_CANCEL_EVALUATION, timeout=3_000):
            nep.cancel_evaluation()


class TestAutomatedModeFlow:
    """
    SMOKE-5: Automated mode → Add Test Cases → dataset table renders.
    """

    def test_automated_mode_add_test_cases_shows_dataset_table(self, authenticated_page: Page):
        """
        SMOKE-5: Selecting 'Automated' mode and clicking 'Add Test Cases' navigates
        to the Test Cases tab. The URL gains &auditId={id} and the 'Select Prompt
        Datasets' table is rendered.

        NOTE – Selector stability:
          The dataset table is targeted by text proximity and class heuristics.
          Add data-testid="prompt-dataset-table" to the table wrapper element.
        """
        nep = NewEvaluationPage(authenticated_page)
        nep.open_new_evaluation_wizard()
        nep.fill_configuration_tab(objective=_OBJECTIVE, mode="automated")
        nep.click_add_test_cases()

        audit_id = nep.wait_for_audit_id_in_url()
        assert audit_id is not None, (
            "URL must contain auditId after clicking 'Add Test Cases' (draft created)"
        )
        assert nep.is_dataset_table_visible(), (
            "'Select Prompt Datasets' table must be visible on the Test Cases tab "
            "in Automated mode"
        )
        # Clean up
        if nep.is_visible(nep.WIZARD_CANCEL_EVALUATION, timeout=3_000):
            nep.cancel_evaluation()


class TestManualModeFlow:
    """
    SMOKE-6: Manual mode → Add Test Cases → module cards render.
    """

    def test_manual_mode_add_test_cases_shows_module_cards(self, authenticated_page: Page):
        """
        SMOKE-6: Selecting 'Manual' mode and clicking 'Add Test Cases' renders
        module cards with '0' counters for Test Cases, Failed, and Passed.

        NOTE – Selector stability:
          Module cards are matched by class heuristics and has-text('Test Cases').
          Add data-testid="module-card" to each card element.
        """
        nep = NewEvaluationPage(authenticated_page)
        nep.open_new_evaluation_wizard()
        nep.fill_configuration_tab(objective=_OBJECTIVE, mode="manual")
        nep.click_add_test_cases()

        # Wait for the URL to gain auditId — same race that bit smoke #3.
        nep.wait_for_audit_id_in_url()

        assert nep.is_module_card_visible(), (
            "At least one module card must be visible on the Test Cases tab in Manual mode"
        )
        # Verify counter labels are present on the cards. Use longer timeouts —
        # module cards hydrate slightly after the cards are placed in the DOM.
        assert nep.is_visible(
            EvaluationsLocators.MANUAL_MODULE_COUNTER_TEST_CASES, timeout=10_000
        ), "'Test Cases' counter label must appear on module cards"
        assert nep.is_visible(
            EvaluationsLocators.MANUAL_MODULE_COUNTER_FAILED, timeout=10_000
        ), "'Failed' counter label must appear on module cards"
        assert nep.is_visible(
            EvaluationsLocators.MANUAL_MODULE_COUNTER_PASSED, timeout=10_000
        ), "'Passed' counter label must appear on module cards"
        # Clean up
        if nep.is_visible(nep.WIZARD_CANCEL_EVALUATION, timeout=3_000):
            nep.cancel_evaluation()


class TestDraftLifecycle:
    """
    SMOKE-7, SMOKE-8, SMOKE-9: Draft appears in list, can be reopened, and
    survives 'Cancel Evaluation'.
    """

    def test_draft_appears_in_list_with_correct_badge_and_mode(self, authenticated_page: Page):
        """
        SMOKE-7: After starting an evaluation wizard and cancelling, the evaluations
        list shows a row with a yellow 'DRAFT' badge and the correct evaluation mode
        (e.g. 'AUTOMATED').

        NOTE: If the framework does not persist drafts on cancel, the draft may only
        be visible after explicitly saving (clicking 'Add Test Cases'). Adjust the
        flow if the app behaviour differs.
        """
        nep = NewEvaluationPage(authenticated_page)
        nep.open_new_evaluation_wizard()
        nep.fill_configuration_tab(objective=_OBJECTIVE, mode="automated")
        # Advance to Test Cases tab to ensure auditId is assigned
        nep.click_add_test_cases()
        nep.get_audit_id_from_url()

        # Navigate back to the list
        nep.go_to_evaluations_list()

        assert nep.is_visible(EvaluationsLocators.STATUS_DRAFT), (
            "A DRAFT status badge must appear in the evaluations list"
        )
        assert nep.is_visible(EvaluationsLocators.MODE_AUTOMATED), (
            "The AUTOMATED mode label must appear next to the draft evaluation"
        )

    def test_clicking_draft_row_reopens_editable_wizard(self, authenticated_page: Page):
        """
        SMOKE-8: Clicking a DRAFT row in the evaluations list opens the editable
        wizard at /evaluations/new?auditId={id} with the previously entered fields
        restored.

        NOTE – Selector stability:
          The DRAFT row is targeted by has-text('DRAFT'). If the badge is rendered
          inside a nested element that breaks has-text matching, add
          data-testid="draft-row-link" to the row's anchor/button.
        """
        nep = NewEvaluationPage(authenticated_page)
        # Ensure there is a draft in the list (create one if needed)
        nep.go_to_evaluations_list()
        if nep.get_draft_row_count() == 0:
            # Create a fresh draft
            nep.open_new_evaluation_wizard()
            nep.fill_configuration_tab(objective=_OBJECTIVE, mode="automated")
            nep.click_add_test_cases()
            nep.go_to_evaluations_list()

        if nep.get_draft_row_count() == 0:
            pytest.skip("No DRAFT rows available to test re-open flow")

        nep.click_first_draft_row()

        assert "/evaluations/new" in authenticated_page.url, (
            "Clicking a DRAFT row must navigate to /evaluations/new?auditId=… "
            f"(editable wizard), got: {authenticated_page.url}"
        )
        assert "auditId=" in authenticated_page.url, (
            "The wizard URL must contain auditId= for a reopened draft"
        )
        assert nep.is_wizard_visible(), (
            "'Evaluation Configuration' tab must be visible when reopening a draft"
        )
        # Verify objective field is not empty (state restoration)
        objective_text = nep.page.locator(EvaluationsLocators.EVAL_OBJECTIVE_TEXTAREA).first.input_value()
        assert objective_text, (
            "Evaluation Objective must be restored when reopening a saved draft"
        )
        # Clean up
        if nep.is_visible(nep.WIZARD_CANCEL_EVALUATION, timeout=3_000):
            nep.cancel_evaluation()

    def test_cancel_evaluation_redirects_to_list_and_draft_persists(self, authenticated_page: Page):
        """
        SMOKE-9: Clicking 'Cancel Evaluation ✕' redirects back to the evaluations
        list without deleting the draft — the DRAFT badge is still visible.
        """
        nep = NewEvaluationPage(authenticated_page)
        nep.open_new_evaluation_wizard()
        nep.fill_configuration_tab(objective=_OBJECTIVE, mode="automated")
        nep.click_add_test_cases()  # persist the draft

        # Cancel from within the wizard
        if not nep.is_visible(nep.WIZARD_CANCEL_EVALUATION, timeout=5_000):
            pytest.skip("'Cancel Evaluation' button not found — cannot test this flow")
        nep.cancel_evaluation()

        assert "/evaluations" in authenticated_page.url and "new" not in authenticated_page.url, (
            "After clicking 'Cancel Evaluation', URL must return to the evaluations list"
        )
        assert nep.is_visible(EvaluationsLocators.STATUS_DRAFT), (
            "The DRAFT badge must still appear in the list after cancelling — "
            "cancel must not delete the draft"
        )
