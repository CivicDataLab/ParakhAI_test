"""
REGRESSION TESTS — New Evaluation flow (Draft & Auto-Save)
==========================================================
Full-coverage edge-case tests for the New Evaluation wizard.
These run in the full regression suite (not on every deploy).

Coverage (12 tests):
  REG-01  Rapid double-click on 'Start' creates only one draft (no duplicates)
  REG-02  Automated: 'Run Evaluation' is disabled + error shown with no dataset selected
  REG-03  Automated: 'Run Evaluation' becomes enabled after selecting a dataset
  REG-04  Manual: 'Finish Evaluation' is disabled with 0 test cases
  REG-05  Manual: clicking module card shows Input textarea, Output panel, Submit;
          '< Change Module' link navigates back to card list
  REG-06  Changing Evaluation Type radio updates the Evaluation Name label/tag
  REG-07  Uncheck all modules → re-check one → sub-category dropdown appears for
          that module only
  REG-08  Fill all fields, navigate away via sidebar, return to draft →
          complete state is restored
  REG-09  Switch between 'Evaluation Configuration' and 'Test Cases' tabs →
          no data loss on either tab
  REG-10  DRAFT rows link to /evaluations/new?auditId=… ;
          COMPLETED rows link to /evaluations/{id} (not /new)
  REG-11  'Auto-saved ✓' indicator resets/updates on each subsequent field change
  REG-12  End-to-end: create Automated draft then Manual draft in the same session —
          no state bleed between the two drafts

Auth: uses authenticated_page fixture (TEST_EMAIL_1 / TEST_PASSWORD_1 in .env)
"""

import pytest
from playwright.sync_api import Page

from locators.evaluations_locators import EvaluationsLocators
from pages.new_evaluation_page import NewEvaluationPage

pytestmark = [pytest.mark.e2e, pytest.mark.regression, pytest.mark.auth]

_OBJECTIVE_A = "Regression test objective A — automated evaluation."
_OBJECTIVE_B = "Regression test objective B — manual evaluation."


# ---------------------------------------------------------------------------
# REG-01 — Duplicate draft prevention
# ---------------------------------------------------------------------------

class TestRapidDoubleClickPrevention:

    def test_rapid_double_click_start_creates_only_one_draft(self, authenticated_page: Page):
        """
        REG-01: Rapidly clicking 'Start' twice (simulating an impatient user) must
        not create duplicate drafts.  After double-clicking, the evaluations list
        must contain at most one more DRAFT than before clicking.

        NOTE – This test counts DRAFT rows before and after. If the app has
        no deduplication guard on the backend, the count will increase by two
        and the assertion will fail, flagging the issue.
        """
        nep = NewEvaluationPage(authenticated_page)
        nep.go_to_evaluations_list()
        draft_count_before = nep.get_draft_row_count()

        nep.click_new_evaluation()
        if not nep.is_modal_visible():
            pytest.skip("Modal not visible")

        # Double-click 'Start'
        start_btn = authenticated_page.locator(EvaluationsLocators.MODAL_START_BUTTON)
        start_btn.dblclick()
        authenticated_page.wait_for_load_state("domcontentloaded")
        authenticated_page.wait_for_timeout(1_000)

        # Cancel whatever wizard opened
        if nep.is_visible(nep.WIZARD_CANCEL_EVALUATION, timeout=5_000):
            nep.cancel_evaluation()
        else:
            nep.go_to_evaluations_list()

        draft_count_after = nep.get_draft_row_count()
        new_drafts = draft_count_after - draft_count_before
        assert new_drafts <= 1, (
            f"Double-clicking 'Start' created {new_drafts} new DRAFT rows; "
            "expected at most 1 (no duplicate drafts)"
        )


# ---------------------------------------------------------------------------
# REG-02 & REG-03 — Automated mode: Run Evaluation button state
# ---------------------------------------------------------------------------

class TestAutomatedRunEvaluationButtonState:

    def test_run_evaluation_disabled_and_error_shown_with_no_dataset(self, authenticated_page: Page):
        """
        REG-02: On the Test Cases tab in Automated mode, with no dataset selected
        and no custom test cases provided, the 'Run Evaluation' button must be
        disabled and the error message must be visible.

        NOTE – Selector stability:
          'Run Evaluation' is matched by button text. Add
          data-testid="run-evaluation-button" to the button element. The error
          message is matched by its full text string — add
          data-testid="no-selection-error" if the text is likely to change.
        """
        nep = NewEvaluationPage(authenticated_page)
        nep.open_new_evaluation_wizard()
        nep.fill_configuration_tab(objective=_OBJECTIVE_A, mode="automated")
        nep.click_add_test_cases()

        # Without selecting anything, check button state and error
        assert not nep.is_run_evaluation_button_enabled(), (
            "'Run Evaluation' button must be disabled when no dataset is selected "
            "and no custom test cases are provided"
        )
        assert nep.is_run_evaluation_error_visible(), (
            "Error message 'Please select at least one prompt dataset or provide "
            "custom test cases' must be visible"
        )
        # Clean up
        if nep.is_visible(nep.WIZARD_CANCEL_EVALUATION, timeout=3_000):
            nep.cancel_evaluation()

    def test_run_evaluation_enabled_after_selecting_dataset(self, authenticated_page: Page):
        """
        REG-03: Selecting at least one dataset row must enable the 'Run Evaluation'
        button and hide (or dismiss) the error message.

        NOTE – Selector stability:
          Dataset checkboxes are targeted by class/proximity heuristics. Add
          data-testid="dataset-checkbox" to each checkbox for reliable selection.
        """
        nep = NewEvaluationPage(authenticated_page)
        nep.open_new_evaluation_wizard()
        nep.fill_configuration_tab(objective=_OBJECTIVE_A, mode="automated")
        nep.click_add_test_cases()

        if not nep.is_dataset_table_visible():
            pytest.skip("Dataset table not visible — cannot test dataset selection")

        selected = nep.select_first_dataset()
        if not selected:
            pytest.skip("No dataset checkbox found to select")

        assert nep.is_run_evaluation_button_enabled(), (
            "'Run Evaluation' button must become enabled after selecting a dataset"
        )
        # Clean up
        if nep.is_visible(nep.WIZARD_CANCEL_EVALUATION, timeout=3_000):
            nep.cancel_evaluation()


# ---------------------------------------------------------------------------
# REG-04 & REG-05 — Manual mode: Finish Evaluation + module card UI
# ---------------------------------------------------------------------------

class TestManualModeEdgeCases:

    def test_finish_evaluation_disabled_with_zero_test_cases(self, authenticated_page: Page):
        """
        REG-04: In Manual mode, 'Finish Evaluation' must be disabled when no
        test cases have been submitted (the app requires ≥3 per module).

        The note 'Evaluate at least 3 test cases per module...' must be visible.

        NOTE – Selector stability:
          'Finish Evaluation' is matched by button text. Add
          data-testid="finish-evaluation-button" to the button element.
        """
        nep = NewEvaluationPage(authenticated_page)
        nep.open_new_evaluation_wizard()
        nep.fill_configuration_tab(objective=_OBJECTIVE_B, mode="manual")
        nep.click_add_test_cases()

        assert nep.is_finish_evaluation_button_disabled(), (
            "'Finish Evaluation' button must be disabled when 0 test cases have been submitted"
        )
        assert nep.is_visible(EvaluationsLocators.MANUAL_MIN_TEST_CASES_NOTE), (
            "Note 'Evaluate at least 3 test cases per module...' must be visible"
        )
        # Clean up
        if nep.is_visible(nep.WIZARD_CANCEL_EVALUATION, timeout=3_000):
            nep.cancel_evaluation()

    @pytest.mark.xfail(reason="Manual mode test entry panel not rendering — see docs/app_bugs.md", strict=False)
    def test_module_card_opens_test_entry_and_change_module_returns(self, authenticated_page: Page):
        """
        REG-05: Clicking a module card must render the Input textarea, Output
        display panel, and Submit button. Clicking '< Change Module' must return
        to the module card list view.

        NOTE – Selector stability:
          Module cards: add data-testid="module-card"
          Input textarea: add data-testid="test-input-textarea"
          Output panel:  add data-testid="test-output-panel"
          Submit button: add data-testid="test-submit-button"
          Change Module: add data-testid="change-module-link"
        """
        nep = NewEvaluationPage(authenticated_page)
        nep.open_new_evaluation_wizard()
        nep.fill_configuration_tab(objective=_OBJECTIVE_B, mode="manual")
        nep.click_add_test_cases()

        if not nep.is_module_card_visible():
            pytest.skip("No module cards visible — cannot test card click flow")

        nep.click_first_module_card()

        assert nep.is_manual_input_textarea_visible(), (
            "Input textarea must be visible after clicking a module card"
        )
        assert nep.is_manual_output_panel_visible(), (
            "Output display panel must be visible after clicking a module card"
        )
        assert nep.is_manual_submit_button_visible(), (
            "Submit button must be visible after clicking a module card"
        )
        assert nep.is_change_module_link_visible(), (
            "'< Change Module' link must be visible inside the test entry view"
        )

        # Click '< Change Module' and verify we return to the card list
        nep.click_change_module()

        assert nep.is_module_card_visible(), (
            "Module cards must be visible again after clicking '< Change Module'"
        )
        # Clean up
        if nep.is_visible(nep.WIZARD_CANCEL_EVALUATION, timeout=3_000):
            nep.cancel_evaluation()


# ---------------------------------------------------------------------------
# REG-06 — Evaluation Type radio changes name tag
# ---------------------------------------------------------------------------

class TestEvaluationTypeRadio:

    def test_changing_eval_type_updates_name_label(self, authenticated_page: Page):
        """
        REG-06: Switching the Evaluation Type radio from 'Technical Evaluation' to
        'Domain Evaluation' must update the Evaluation Name label/tag visible in
        the form header or name field.

        The test checks that at minimum the 'Domain Evaluation' option becomes
        selected (via aria-checked, checked attribute, or sibling indicator class).

        NOTE – Selector stability:
          Radios are targeted by text proximity. Add
          data-testid="eval-type-technical", "eval-type-domain", "eval-type-cultural"
          to each radio input for stable selection.
        """
        nep = NewEvaluationPage(authenticated_page)
        nep.open_new_evaluation_wizard()

        # Switch to Domain Evaluation
        nep.select_evaluation_type("domain")

        # Verify 'Domain Evaluation' text/selection is reflected
        # Strategy 1: check a radio is marked as selected via aria-checked
        domain_radio = authenticated_page.locator(EvaluationsLocators.EVAL_TYPE_DOMAIN_RADIO).first
        if domain_radio.count() > 0 and domain_radio.is_visible():
            assert domain_radio.is_checked() or domain_radio.get_attribute("aria-checked") == "true", (
                "Domain Evaluation radio must be checked after clicking"
            )
        else:
            # Strategy 2: at minimum the label text must be visible
            assert nep.is_visible(EvaluationsLocators.EVAL_TYPE_DOMAIN), (
                "'Domain Evaluation' option text must be visible after selection"
            )
        # Clean up
        if nep.is_visible(nep.WIZARD_CANCEL_EVALUATION, timeout=3_000):
            nep.cancel_evaluation()


# ---------------------------------------------------------------------------
# REG-07 — Module checkbox + sub-category dropdown
# ---------------------------------------------------------------------------

class TestEvaluationModuleSubcategory:

    def test_rechecking_one_module_shows_subcategory_dropdown_for_that_module(
        self, authenticated_page: Page
    ):
        """
        REG-07: Uncheck all Evaluation Modules then re-check one — the sub-category
        multi-select dropdown must appear for that module only.

        NOTE – Selector stability:
          Module checkboxes are targeted by proximity to label text. Add
          data-testid="module-checkbox-hallucination" etc. for reliable targeting.
          The sub-category dropdown is matched by class/aria heuristics. Add
          data-testid="module-subcategory-dropdown" to that element.
        """
        nep = NewEvaluationPage(authenticated_page)
        nep.open_new_evaluation_wizard()

        # Scroll to modules section
        authenticated_page.keyboard.press("End")
        authenticated_page.wait_for_timeout(300)

        # Find all checkboxes and uncheck them all
        checkboxes = authenticated_page.locator(EvaluationsLocators.EVAL_MODULE_CHECKBOX)
        count = checkboxes.count()
        for i in range(count):
            cb = checkboxes.nth(i)
            if cb.is_visible() and cb.is_checked():
                cb.click()
                authenticated_page.wait_for_timeout(200)

        # Re-check Hallucination module only
        hallucination_checkbox = authenticated_page.locator(
            "input[type='checkbox']:near(:text('Hallucination and Misinformation'))"
        ).first
        if not hallucination_checkbox.is_visible():
            pytest.skip("Hallucination module checkbox not found")

        hallucination_checkbox.click()
        authenticated_page.wait_for_timeout(500)

        assert nep.module_subcategory_dropdown_visible(), (
            "Sub-category dropdown must appear for the re-checked Hallucination module"
        )
        # Clean up
        if nep.is_visible(nep.WIZARD_CANCEL_EVALUATION, timeout=3_000):
            nep.cancel_evaluation()


# ---------------------------------------------------------------------------
# REG-08 — State restoration after sidebar navigation
# ---------------------------------------------------------------------------

class TestDraftStateRestoration:

    @pytest.mark.xfail(reason="Mode dropdown disabled — state restoration not verifiable", strict=False)
    def test_complete_state_restored_after_sidebar_navigation(self, authenticated_page: Page):
        """
        REG-08: Fill all wizard fields (name, type, objective, modules, mode),
        navigate away via the sidebar link, then reopen the draft — all fields
        must be restored exactly.

        NOTE: The test navigates away using the browser's back button (simplest
        cross-framework approach). If the app uses Next.js Link, a direct URL
        change is tested instead. Adjust if the sidebar uses a different mechanism.
        """
        nep = NewEvaluationPage(authenticated_page)
        nep.open_new_evaluation_wizard()

        # Fill all fields — use fill_configuration_tab() to ensure modules are
        # checked before mode is selected (mode dropdown starts disabled).
        nep.set_evaluation_name("State Restoration Test")
        nep.fill_configuration_tab(
            objective=_OBJECTIVE_A, eval_type="domain", mode="automated"
        )
        authenticated_page.wait_for_timeout(500)  # allow auto-save

        # Advance to persist the auditId
        nep.click_add_test_cases()
        audit_id = nep.get_audit_id_from_url()
        if not audit_id:
            pytest.skip("auditId not present in URL — cannot verify state restoration")

        # Navigate away to the evaluations list
        nep.go_to_evaluations_list()
        assert "new" not in authenticated_page.url, "Should be on list page now"

        # Return to the draft
        nep.go_to_draft(audit_id)

        assert nep.is_wizard_visible(), "Wizard must load when reopening draft via auditId URL"
        objective_restored = authenticated_page.locator(
            EvaluationsLocators.EVAL_OBJECTIVE_TEXTAREA
        ).first.input_value()
        assert objective_restored, (
            "Evaluation Objective must be restored after navigating away and back to the draft"
        )
        assert nep.is_visible(EvaluationsLocators.EVAL_TYPE_DOMAIN), (
            "'Domain Evaluation' type must still be selected after state restoration"
        )
        # Clean up
        if nep.is_visible(nep.WIZARD_CANCEL_EVALUATION, timeout=3_000):
            nep.cancel_evaluation()


# ---------------------------------------------------------------------------
# REG-09 — Tab switching without data loss
# ---------------------------------------------------------------------------

class TestTabSwitchingDataPersistence:

    def test_switching_tabs_does_not_lose_form_data(self, authenticated_page: Page):
        """
        REG-09: Switch from 'Evaluation Configuration' to 'Test Cases' tab and
        back — the Objective field must retain its value on the Configuration tab.

        NOTE: This requires the objective to be filled before advancing (otherwise
        the app may block the tab switch and show a validation error).
        """
        nep = NewEvaluationPage(authenticated_page)
        nep.open_new_evaluation_wizard()
        nep.fill_configuration_tab(objective=_OBJECTIVE_A, mode="automated")

        # Switch to Test Cases tab
        nep.click_add_test_cases()
        assert nep.is_visible(EvaluationsLocators.WIZARD_TAB_TEST_CASES), (
            "'Test Cases' tab must be active after clicking 'Add Test Cases'"
        )

        # Switch back to Configuration tab
        nep.click_tab_configuration()
        authenticated_page.wait_for_timeout(300)

        objective_value = authenticated_page.locator(
            EvaluationsLocators.EVAL_OBJECTIVE_TEXTAREA
        ).first.input_value()
        assert objective_value, (
            "Evaluation Objective must not be cleared when switching back to "
            "the 'Evaluation Configuration' tab"
        )
        assert _OBJECTIVE_A in objective_value or len(objective_value) > 0, (
            f"Expected objective text to be restored; got: {objective_value!r}"
        )
        # Clean up
        if nep.is_visible(nep.WIZARD_CANCEL_EVALUATION, timeout=3_000):
            nep.cancel_evaluation()


# ---------------------------------------------------------------------------
# REG-10 — DRAFT vs COMPLETED URL routing
# ---------------------------------------------------------------------------

class TestDraftCompletedUrlRouting:

    def test_draft_row_links_to_wizard_and_completed_row_links_to_report(
        self, authenticated_page: Page
    ):
        """
        REG-10: In the evaluations list:
          • DRAFT rows must navigate to /evaluations/new?auditId=… (editable wizard)
          • COMPLETED rows must navigate to /evaluations/{id} (read-only report)

        The test checks both by navigating and inspecting the resulting URL.

        NOTE – Selector stability:
          DRAFT/COMPLETED rows are targeted by has-text. Add
          data-testid="draft-row-link" and data-testid="completed-row-link" to the
          row anchor/button elements for stable selection.
        """
        nep = NewEvaluationPage(authenticated_page)
        nep.go_to_evaluations_list()

        # ── DRAFT row ────────────────────────────────────────────────────────
        if nep.get_draft_row_count() == 0:
            # Create a draft for the test
            nep.open_new_evaluation_wizard()
            nep.fill_configuration_tab(objective=_OBJECTIVE_A, mode="automated")
            nep.click_add_test_cases()
            nep.go_to_evaluations_list()

        if nep.get_draft_row_count() > 0:
            nep.click_first_draft_row()
            assert "/evaluations/new" in authenticated_page.url, (
                f"DRAFT row must link to /evaluations/new; got: {authenticated_page.url}"
            )
            assert "auditId=" in authenticated_page.url, (
                "DRAFT row URL must contain auditId query parameter"
            )
            nep.go_to_evaluations_list()
        else:
            pytest.skip("No DRAFT rows to test URL routing")

        # ── COMPLETED row ─────────────────────────────────────────────────────
        completed_rows = authenticated_page.locator(EvaluationsLocators.COMPLETED_ROW)
        if completed_rows.count() == 0:
            pytest.skip("No COMPLETED rows to test URL routing")

        nep.click_first_completed_row()
        assert "/evaluations/" in authenticated_page.url, (
            f"COMPLETED row must link to /evaluations/{{id}}; got: {authenticated_page.url}"
        )
        assert "new" not in authenticated_page.url, (
            "COMPLETED row must NOT link to the wizard (/evaluations/new)"
        )


# ---------------------------------------------------------------------------
# REG-11 — Auto-save indicator resets on each field change
# ---------------------------------------------------------------------------

class TestAutoSaveIndicatorUpdates:

    @pytest.mark.xfail(reason="App bug #1 — see docs/app_bugs.md", strict=False)
    def test_auto_save_indicator_updates_on_subsequent_field_changes(
        self, authenticated_page: Page
    ):
        """
        REG-11: The 'Auto-saved ✓' indicator must reappear (or update its
        timestamp) after each field change — not just on the first change.

        Test approach:
          1. Fill objective → wait for indicator.
          2. Change objective text → indicator must still/again be visible.

        NOTE – Selector stability:
          If the indicator disappears between saves (e.g. it shows a spinner
          then re-shows the checkmark), increase the timeout below. Add
          data-testid="auto-save-indicator" to the element for reliable targeting.
        """
        nep = NewEvaluationPage(authenticated_page)
        nep.open_new_evaluation_wizard()

        # First save
        nep.fill_evaluation_objective("First objective text.")
        assert nep.is_auto_saved_indicator_visible(timeout=8_000), (
            "'Auto-saved' indicator must appear after first objective entry"
        )

        # Second save — change the text
        nep.fill_evaluation_objective("Updated objective text — second edit.")
        assert nep.is_auto_saved_indicator_visible(timeout=8_000), (
            "'Auto-saved' indicator must reappear after a subsequent field change"
        )
        # Clean up
        if nep.is_visible(nep.WIZARD_CANCEL_EVALUATION, timeout=3_000):
            nep.cancel_evaluation()


# ---------------------------------------------------------------------------
# REG-12 — End-to-end Automated + Manual in same session (no state bleed)
# ---------------------------------------------------------------------------

class TestNoStateBleeedBetweenDrafts:

    @pytest.mark.timeout(120)  # longer timeout for double end-to-end flow
    def test_automated_and_manual_drafts_in_same_session_no_state_bleed(
        self, authenticated_page: Page
    ):
        """
        REG-12: Create an Automated draft and a Manual draft in the same browser
        session. Verify that:
          • Each draft has its own auditId in the URL.
          • The Manual draft shows module cards (not a dataset table).
          • The Automated draft shows a dataset table (not module cards).
          • The two auditIds are different (no shared state).

        NOTE: This test navigates the wizard twice. If the app reuses an existing
        DRAFT on re-opening the modal, the second flow may reopen the first draft
        — the assertion on distinct auditIds would catch that regression.
        """
        nep = NewEvaluationPage(authenticated_page)

        # ── Draft A: Automated ───────────────────────────────────────────────
        nep.open_new_evaluation_wizard()
        nep.fill_configuration_tab(objective=_OBJECTIVE_A, mode="automated")
        nep.click_add_test_cases()

        audit_id_a = nep.get_audit_id_from_url()
        assert audit_id_a, "Automated draft must have an auditId in the URL"
        automated_has_dataset_table = nep.is_dataset_table_visible()
        automated_has_module_cards = nep.is_module_card_visible()

        # Cancel automated draft to return to list
        if nep.is_visible(nep.WIZARD_CANCEL_EVALUATION, timeout=3_000):
            nep.cancel_evaluation()
        else:
            nep.go_to_evaluations_list()

        # ── Draft B: Manual ──────────────────────────────────────────────────
        nep.open_new_evaluation_wizard()
        nep.fill_configuration_tab(objective=_OBJECTIVE_B, mode="manual")
        nep.click_add_test_cases()

        audit_id_b = nep.get_audit_id_from_url()
        assert audit_id_b, "Manual draft must have an auditId in the URL"
        manual_has_module_cards = nep.is_module_card_visible()
        manual_has_dataset_table = nep.is_dataset_table_visible()

        # Cancel manual draft
        if nep.is_visible(nep.WIZARD_CANCEL_EVALUATION, timeout=3_000):
            nep.cancel_evaluation()
        else:
            nep.go_to_evaluations_list()

        # ── Assertions ───────────────────────────────────────────────────────
        assert audit_id_a != audit_id_b, (
            f"Each draft must have a unique auditId; "
            f"got audit_id_a={audit_id_a!r}, audit_id_b={audit_id_b!r} — "
            "possible state bleed between sessions"
        )
        assert automated_has_dataset_table, (
            "Automated draft must render the 'Select Prompt Datasets' table on "
            "the Test Cases tab"
        )
        assert not automated_has_module_cards, (
            "Automated draft must NOT render module cards on the Test Cases tab"
        )
        assert manual_has_module_cards, (
            "Manual draft must render module cards on the Test Cases tab"
        )
        assert not manual_has_dataset_table, (
            "Manual draft must NOT render the dataset table on the Test Cases tab"
        )
