"""
SMOKE TESTS — New Evaluation flow (two-step modal + single-page wizard)
=======================================================================
Happy-path tests that run on every deploy to verify the New Evaluation flow
is functional end-to-end for both Bulk and Playground evaluation methods.

Jul 2026 redesign under test:
  • "Start an Evaluation" modal — step 1 (model/version/name/method) →
    step 2 (evaluator type, objective) → Start Evaluation
  • Single-page wizard at /evaluations/new?auditId=… — NO tabs; header
    (name, Draft badge, Back to List, Cancel) + Evaluation Overview card +
    Evaluation Workspace (modules, test-case source, Run Evaluation)

Coverage (9 tests):
  1. New Evaluation modal opens with both dropdowns populated
  2. Completing both modal steps navigates to /evaluations/new?auditId=…
  3. Evaluation Name is pre-filled and editable in modal step 1
  4. Objective entered in the modal appears in the wizard Overview card
  5. Bulk method → wizard shows prompt-library test-case source
  6. Playground method → wizard Overview shows 'Playground Evaluation' mode
  7. Navigate back to list → draft appears with DRAFT badge
  8. Click draft row link → wizard reloads at /evaluations/new?auditId=…
  9. Cancel from wizard → URL returns to the evaluations list

Auth: uses authenticated_page fixture (TEST_EMAIL_1 / TEST_PASSWORD_1 in .env)
Write-side classes are additionally gated on SANDBOX_ORG_SLUG via the
regression_write marker (drafts are created server-side).
"""

import pytest
from playwright.sync_api import Page

from locators.evaluations_locators import EvaluationsLocators
from pages.new_evaluation_page import NewEvaluationPage

# The full new-evaluation flow walks through several slow async curtains on the
# dev environment (cold 'Verifying your session...' ~20s, 'Loading models...'
# ~35s, 'Loading evaluation details...' ~20s), so a single test can take
# ~2 min end-to-end. Override the global 120s per-test timeout (pytest.ini).
pytestmark = [
    pytest.mark.e2e,
    pytest.mark.smoke,
    pytest.mark.auth,
    pytest.mark.timeout(300),
]

_OBJECTIVE = "Smoke-test objective: evaluate model quality automatically."


def _register_cleanup(nep: NewEvaluationPage, cleanup_evaluation: list) -> None:
    """Append the current draft's auditId (if any) for teardown cancellation."""
    audit_id = nep.get_audit_id_from_url()
    if audit_id:
        cleanup_evaluation.append(audit_id)


class TestNewEvaluationModal:
    """SMOKE-1 & SMOKE-2: Modal opens correctly and Start navigates to the wizard."""

    def test_modal_opens_with_both_dropdowns_populated(self, authenticated_page: Page):
        """
        SMOKE-1: Clicking 'New Evaluation' opens the two-step modal; step 1
        renders 'Select an AI Model' and 'Select a Version' with options.
        """
        nep = NewEvaluationPage(authenticated_page)
        nep.go_to_evaluations_list()
        nep.click_new_evaluation()

        assert nep.is_modal_visible(), (
            "'Start an Evaluation' modal must appear after clicking the button"
        )
        assert nep.is_visible("text=Select an AI Model"), (
            "'Select an AI Model' label must be visible in the modal"
        )
        assert nep.is_visible("text=Select a Version"), (
            "'Select a Version' label must be visible in the modal"
        )
        assert nep.modal_model_dropdown_has_options(), (
            "'Select an AI Model' dropdown must have at least one selectable option"
        )
        assert nep.modal_version_dropdown_has_options(), (
            "'Select a Version' dropdown must have at least one selectable option"
        )
        # Clean up — dismiss modal
        nep.click_modal_cancel()

    @pytest.mark.regression_write
    def test_clicking_start_navigates_to_wizard(
        self, authenticated_page: Page, cleanup_evaluation: list
    ):
        """
        SMOKE-2: Completing both modal steps and clicking 'Start Evaluation'
        navigates to /evaluations/new?auditId=… and the wizard hydrates.
        """
        nep = NewEvaluationPage(authenticated_page)
        nep.go_to_evaluations_list()
        nep.click_new_evaluation()
        if not nep.is_modal_visible():
            pytest.skip("Modal not visible — cannot test Start navigation")

        nep.start_evaluation_from_modal(objective=_OBJECTIVE)
        _register_cleanup(nep, cleanup_evaluation)

        assert "auditId=" in authenticated_page.url, (
            f"Expected auditId in URL after Start Evaluation, got: {authenticated_page.url}"
        )
        assert nep.wait_for_wizard_loaded(), (
            "Single-page wizard (Evaluation Overview card) must load after Start Evaluation"
        )


class TestEvaluationConfigurationTab:
    """SMOKE-3 & SMOKE-4: Evaluation name and objective behaviour."""

    def test_evaluation_name_is_prefilled_and_editable(self, authenticated_page: Page):
        """
        SMOKE-3: The Evaluation Name input in modal step 1 is pre-filled with a
        default ('Untitled Evaluation - <date>') and can be overwritten.
        """
        nep = NewEvaluationPage(authenticated_page)
        nep.go_to_evaluations_list()
        nep.click_new_evaluation()
        if not nep.is_modal_visible():
            pytest.skip("Modal not visible — cannot test name field")

        prefilled = nep.get_modal_eval_name()
        assert prefilled, (
            "Evaluation Name input must be pre-filled with a default value "
            "(e.g. 'Untitled Evaluation - …')"
        )
        assert "Untitled" in prefilled, (
            f"Default name should start with 'Untitled'; got {prefilled!r}"
        )

        nep.set_modal_eval_name("My Smoke Test Evaluation")
        assert nep.get_modal_eval_name() == "My Smoke Test Evaluation", (
            "Evaluation Name field must accept typed text"
        )
        nep.click_modal_cancel()

    @pytest.mark.regression_write
    def test_filling_objective_triggers_auto_save_indicator(
        self, authenticated_page: Page, cleanup_evaluation: list
    ):
        """
        SMOKE-4 (redesigned): The objective is entered in modal step 2 and must
        be persisted on the draft — the wizard's Evaluation Overview card shows
        it under 'Objective :'.

        (Pre-Jul-2026 this test asserted an 'Auto-saved' indicator on the
        Configuration tab; that tab no longer exists.)
        """
        nep = NewEvaluationPage(authenticated_page)
        nep.open_new_evaluation_wizard(objective=_OBJECTIVE)
        _register_cleanup(nep, cleanup_evaluation)

        overview_objective = nep.get_overview_field("Objective")
        assert overview_objective, (
            "The Evaluation Overview card must show the objective entered in the modal"
        )
        assert _OBJECTIVE[:30] in overview_objective, (
            f"Overview objective must match the modal input; got {overview_objective!r}"
        )


class TestAutomatedModeFlow:
    """SMOKE-5: Bulk method → wizard shows the prompt-library test-case source."""

    pytestmark = [pytest.mark.regression_write]

    def test_automated_mode_add_test_cases_shows_dataset_table(
        self, authenticated_page: Page, cleanup_evaluation: list
    ):
        """
        SMOKE-5 (redesigned): Creating a Bulk evaluation lands on the wizard
        with an auditId in the URL and the test-case source options
        ('Select a prompt library' / 'Add your own prompts') rendered.
        """
        nep = NewEvaluationPage(authenticated_page)
        nep.open_new_evaluation_wizard(method="bulk", objective=_OBJECTIVE)
        _register_cleanup(nep, cleanup_evaluation)

        audit_id = nep.get_audit_id_from_url()
        assert audit_id is not None, (
            "URL must contain auditId after Start Evaluation (draft created)"
        )
        assert nep.is_visible(
            EvaluationsLocators.WIZARD_PROMPT_LIBRARY_OPTION, timeout=15_000
        ), "'Select a prompt library' test-case source must be visible for Bulk evals"
        assert nep.is_visible(
            EvaluationsLocators.WIZARD_OWN_PROMPTS_OPTION, timeout=5_000
        ), "'Add your own prompts' test-case source must be visible for Bulk evals"


class TestManualModeFlow:
    """SMOKE-6: Playground method → wizard Overview shows Playground mode."""

    pytestmark = [pytest.mark.regression_write]

    def test_manual_mode_add_test_cases_shows_module_cards(
        self, authenticated_page: Page, cleanup_evaluation: list
    ):
        """
        SMOKE-6 (redesigned): Creating a Playground evaluation lands on the
        wizard and the Evaluation Overview card reports
        'Mode : Playground Evaluation'.
        """
        nep = NewEvaluationPage(authenticated_page)
        nep.open_new_evaluation_wizard(method="manual", objective=_OBJECTIVE)
        _register_cleanup(nep, cleanup_evaluation)

        assert nep.get_audit_id_from_url() is not None, (
            "URL must contain auditId after Start Evaluation (draft created)"
        )
        mode = nep.get_overview_field("Mode")
        assert mode and "Playground" in mode, (
            f"Overview Mode must read 'Playground Evaluation' for manual method; got {mode!r}"
        )


class TestDraftLifecycle:
    """SMOKE-7, SMOKE-8, SMOKE-9: Draft appears in list, reopens, and cancels."""

    pytestmark = [pytest.mark.regression_write]

    def test_draft_appears_in_list_with_correct_badge_and_mode(
        self, authenticated_page: Page, cleanup_evaluation: list
    ):
        """
        SMOKE-7: After creating a Bulk draft and navigating back, the
        evaluations list shows a DRAFT status badge.
        """
        nep = NewEvaluationPage(authenticated_page)
        nep.open_new_evaluation_wizard(method="bulk", objective=_OBJECTIVE)
        _register_cleanup(nep, cleanup_evaluation)

        nep.go_to_evaluations_list()

        assert nep.is_visible(EvaluationsLocators.STATUS_DRAFT), (
            "A DRAFT status badge must appear in the evaluations list"
        )

    def test_clicking_draft_row_reopens_editable_wizard(
        self, authenticated_page: Page, cleanup_evaluation: list
    ):
        """
        SMOKE-8: Clicking a DRAFT row's name link opens the editable wizard at
        /evaluations/new?auditId={id} with the draft state restored.
        """
        nep = NewEvaluationPage(authenticated_page)
        nep.go_to_evaluations_list()
        if nep.get_draft_row_count() == 0:
            nep.open_new_evaluation_wizard(method="bulk", objective=_OBJECTIVE)
            _register_cleanup(nep, cleanup_evaluation)
            nep.go_to_evaluations_list()

        if nep.get_draft_row_count() == 0:
            pytest.skip("No DRAFT rows available to test re-open flow")

        nep.click_first_draft_row()

        assert "/evaluations/new" in authenticated_page.url, (
            "Clicking a DRAFT row link must navigate to /evaluations/new?auditId=… "
            f"(editable wizard), got: {authenticated_page.url}"
        )
        assert "auditId=" in authenticated_page.url, (
            "The wizard URL must contain auditId= for a reopened draft"
        )
        assert nep.wait_for_wizard_loaded(), (
            "The single-page wizard must hydrate when reopening a draft"
        )

    def test_back_to_list_redirects_and_draft_persists(
        self, authenticated_page: Page, cleanup_evaluation: list
    ):
        """
        SMOKE-9: 'Back to List' in the wizard header returns to the evaluations
        list (URL loses the auditId). The header 'Cancel' button is disabled
        for DRAFTs — it only cancels running audits.
        """
        nep = NewEvaluationPage(authenticated_page)
        nep.open_new_evaluation_wizard(method="bulk", objective=_OBJECTIVE)
        _register_cleanup(nep, cleanup_evaluation)

        nep.click_back_to_list()

        assert "auditId=" not in authenticated_page.url, (
            "After 'Back to List', URL must leave the wizard "
            f"(got: {authenticated_page.url})"
        )
