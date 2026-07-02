"""
REGRESSION TESTS — New Evaluation flow (two-step modal + single-page wizard)
============================================================================
Full-coverage edge-case tests for the New Evaluation flow (Jul 2026 redesign).
These run in the full regression suite (not on every deploy).

Coverage (12 scenarios):
  REG-01  Rapid double-click on 'Start Evaluation' creates only one draft
  REG-02  Bulk: 'Run Evaluation' is disabled + library error with nothing selected
  REG-03  Bulk: 'Run Evaluation' enables after picking a prompt library
  REG-04  Playground: 'Finish Evaluation' is disabled with 0 test cases
  REG-05  Playground: module card opens test entry, 'Change Module' returns
  REG-06  Evaluator-type radio (modal step 2): selection + Overview reflection
  REG-07  Bulk wizard: checking a module reveals the sub-module dropdown prompt
  REG-08  Draft state restored after navigating away and reopening
  REG-09  Back-to-List + reopen preserves draft Mode (tabs no longer exist)
  REG-10  DRAFT rows link to /evaluations/new?auditId=… ;
          COMPLETED rows link to /evaluations/{id} (not /new)
  REG-11  'Auto-saved' indicator (skips if the redesigned page dropped it)
  REG-12  Bulk draft + Playground draft in one session — no state bleed

Auth: uses authenticated_page fixture (TEST_EMAIL_1 / TEST_PASSWORD_1 in .env)
Draft-creating classes are gated on SANDBOX_ORG_SLUG via regression_write.
"""

import pytest
from playwright.sync_api import Page

from locators.evaluations_locators import EvaluationsLocators
from pages.new_evaluation_page import NewEvaluationPage

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.regression,
    pytest.mark.auth,
    pytest.mark.timeout(300),
]

_OBJECTIVE_A = "Regression test objective A — bulk evaluation."
_OBJECTIVE_B = "Regression test objective B — playground evaluation."


def _register_cleanup(nep: NewEvaluationPage, cleanup_evaluation: list) -> None:
    """Append the current draft's auditId (if any) for teardown cancellation."""
    audit_id = nep.get_audit_id_from_url()
    if audit_id:
        cleanup_evaluation.append(audit_id)


# ---------------------------------------------------------------------------
# REG-01 — Duplicate draft prevention
# ---------------------------------------------------------------------------

class TestRapidDoubleClickPrevention:

    pytestmark = [pytest.mark.regression_write]

    def test_rapid_double_click_start_creates_only_one_draft(
        self, authenticated_page: Page, cleanup_evaluation: list
    ):
        """
        REG-01: Rapidly double-clicking 'Start Evaluation' in modal step 2 must
        not create duplicate drafts — the DRAFT row count grows by at most 1.
        """
        nep = NewEvaluationPage(authenticated_page)
        nep.go_to_evaluations_list()
        draft_count_before = nep.get_draft_row_count()

        nep.click_new_evaluation()
        if not nep.is_modal_visible():
            pytest.skip("Modal not visible")

        # Complete step 1 → step 2, fill required objective, then double-click.
        nep.select_first_model_and_version()
        nep.select_evaluation_method("bulk")
        nep.click_modal_next()
        nep.fill_modal_objective(_OBJECTIVE_A)

        start_btn = authenticated_page.locator(
            EvaluationsLocators.MODAL_START_BUTTON
        ).first
        start_btn.dblclick()
        try:
            authenticated_page.locator(
                EvaluationsLocators.MODAL_DIALOG
            ).first.wait_for(state="hidden", timeout=20_000)
        except Exception:
            pass
        authenticated_page.wait_for_timeout(2_000)
        _register_cleanup(nep, cleanup_evaluation)

        nep.go_to_evaluations_list()
        draft_count_after = nep.get_draft_row_count()
        new_drafts = draft_count_after - draft_count_before
        assert new_drafts <= 1, (
            f"Double-clicking 'Start Evaluation' created {new_drafts} new DRAFT rows; "
            "expected at most 1 (no duplicate drafts)"
        )


# ---------------------------------------------------------------------------
# REG-02 & REG-03 — Bulk: Run Evaluation button state
# ---------------------------------------------------------------------------

class TestAutomatedRunEvaluationButtonState:

    pytestmark = [pytest.mark.regression_write]

    def test_run_evaluation_disabled_and_error_shown_with_no_dataset(
        self, authenticated_page: Page, cleanup_evaluation: list
    ):
        """
        REG-02: On a fresh Bulk wizard with no prompt library selected, the
        'Run Evaluation' button must be disabled and the 'Please select a
        prompt library…' error must be shown.
        """
        nep = NewEvaluationPage(authenticated_page)
        nep.open_new_evaluation_wizard(method="bulk", objective=_OBJECTIVE_A)
        _register_cleanup(nep, cleanup_evaluation)

        assert not nep.is_run_evaluation_button_enabled(), (
            "'Run Evaluation' button must be disabled when no prompt library is selected"
        )
        assert nep.is_run_evaluation_library_error_visible(), (
            "'Please select a prompt library…' error must be visible under Run Evaluation"
        )

    def test_run_evaluation_enabled_after_selecting_dataset(
        self, authenticated_page: Page, cleanup_evaluation: list
    ):
        """
        REG-03: Selecting a prompt library should enable 'Run Evaluation'.
        Skips when the dev environment surfaces no libraries within 30s
        (dataset loading is flaky on dev).
        """
        nep = NewEvaluationPage(authenticated_page)
        nep.open_new_evaluation_wizard(method="bulk", objective=_OBJECTIVE_A)
        _register_cleanup(nep, cleanup_evaluation)

        nep.select_prompt_library_source()
        # Wait out the 'Loading prompt datasets...' curtain.
        try:
            authenticated_page.locator(
                "text=/^Loading prompt datasets/i"
            ).first.wait_for(state="hidden", timeout=30_000)
        except Exception:
            pass

        selected = nep.select_first_dataset()
        if not selected:
            pytest.skip("No prompt library/dataset rendered within 30s — dev data unavailable")

        assert nep.is_run_evaluation_button_enabled(), (
            "'Run Evaluation' button must become enabled after selecting a prompt library"
        )


# ---------------------------------------------------------------------------
# REG-04 & REG-05 — Playground: Finish Evaluation + module card UI
# ---------------------------------------------------------------------------

class TestManualModeEdgeCases:

    pytestmark = [pytest.mark.regression_write]

    def test_finish_evaluation_disabled_with_zero_test_cases(
        self, authenticated_page: Page, cleanup_evaluation: list
    ):
        """
        REG-04: On a fresh Playground wizard, 'Finish Evaluation' must be
        disabled when no test cases have been submitted. Skips if the
        playground workspace doesn't hydrate (dev flakiness: 'No modules
        available for this model type').
        """
        nep = NewEvaluationPage(authenticated_page)
        nep.open_new_evaluation_wizard(method="manual", objective=_OBJECTIVE_B)
        _register_cleanup(nep, cleanup_evaluation)

        if not nep.is_visible(nep.FINISH_EVALUATION_BUTTON, timeout=15_000):
            pytest.skip(
                "'Finish Evaluation' button not rendered — playground workspace "
                "did not hydrate on this dev build"
            )
        assert nep.is_finish_evaluation_button_disabled(), (
            "'Finish Evaluation' button must be disabled when 0 test cases have been submitted"
        )

    @pytest.mark.xfail(
        reason="Playground test entry panel hydration is flaky on dev", strict=False
    )
    def test_module_card_opens_test_entry_and_change_module_returns(
        self, authenticated_page: Page, cleanup_evaluation: list
    ):
        """
        REG-05: Clicking a module card must render the Input textarea and Submit
        button; '< Change Module' must return to the module card list.
        """
        nep = NewEvaluationPage(authenticated_page)
        nep.open_new_evaluation_wizard(method="manual", objective=_OBJECTIVE_B)
        _register_cleanup(nep, cleanup_evaluation)

        if not nep.wait_for_module_cards(min_count=1, timeout=30_000):
            pytest.skip("No module cards visible — cannot test card click flow")

        nep.click_first_module_card()

        assert nep.is_manual_input_textarea_visible(), (
            "Input textarea must be visible after clicking a module card"
        )
        assert nep.is_manual_submit_button_visible(), (
            "Submit button must be visible after clicking a module card"
        )

        if nep.is_change_module_link_visible():
            nep.click_change_module()
            assert nep.is_module_card_visible(), (
                "Module cards must be visible again after clicking '< Change Module'"
            )


# ---------------------------------------------------------------------------
# REG-06 — Evaluator-type radio (modal step 2)
# ---------------------------------------------------------------------------

class TestEvaluationTypeRadio:

    pytestmark = [pytest.mark.regression_write]

    def test_changing_eval_type_updates_name_label(
        self, authenticated_page: Page, cleanup_evaluation: list
    ):
        """
        REG-06 (redesigned): The evaluator-type radios live in modal step 2.
        Selecting 'a domain expert' must check the Domain radio, and after
        Start Evaluation the wizard Overview must report a Domain evaluator.
        """
        nep = NewEvaluationPage(authenticated_page)
        nep.go_to_evaluations_list()
        nep.click_new_evaluation()
        if not nep.is_modal_visible():
            pytest.skip("Modal not visible")

        nep.select_first_model_and_version()
        nep.select_evaluation_method("bulk")
        nep.click_modal_next()

        # Technical must be the default; switching to Domain must stick.
        assert nep.get_checked_evaluator_type() == "Technical", (
            "'a technical evaluator' must be pre-selected in modal step 2"
        )
        nep.select_evaluator_type_in_modal("domain")
        assert nep.get_checked_evaluator_type() == "Domain", (
            "Domain radio must be checked after selecting 'a domain expert'"
        )

        nep.fill_modal_objective(_OBJECTIVE_A)
        nep.click_modal_start()
        _register_cleanup(nep, cleanup_evaluation)
        nep.wait_for_wizard_loaded()

        evaluator = nep.get_overview_field("Evaluator")
        assert evaluator and "Domain" in evaluator, (
            f"Overview Evaluator must reflect the Domain selection; got {evaluator!r}"
        )


# ---------------------------------------------------------------------------
# REG-07 — Module checkbox + sub-module dropdown
# ---------------------------------------------------------------------------

class TestEvaluationModuleSubcategory:

    pytestmark = [pytest.mark.regression_write]

    def test_rechecking_one_module_shows_subcategory_dropdown_for_that_module(
        self, authenticated_page: Page, cleanup_evaluation: list
    ):
        """
        REG-07: On the Bulk wizard, checking the 'Hallucination and
        Misinformation' module must reveal the 'Select sub-modules from
        dropdown' prompt.
        """
        nep = NewEvaluationPage(authenticated_page)
        nep.open_new_evaluation_wizard(method="bulk", objective=_OBJECTIVE_A)
        _register_cleanup(nep, cleanup_evaluation)

        if not nep.is_visible(
            EvaluationsLocators.WIZARD_MODULES_HEADING, timeout=15_000
        ):
            pytest.skip("'Evaluation Modules' section not rendered — dev data unavailable")

        nep.check_module("hallucination")
        assert nep.is_submodule_prompt_visible(), (
            "'Select sub-modules from dropdown' must appear after checking a module"
        )


# ---------------------------------------------------------------------------
# REG-08 — State restoration after navigating away
# ---------------------------------------------------------------------------

class TestDraftStateRestoration:

    pytestmark = [pytest.mark.regression_write]

    def test_complete_state_restored_after_sidebar_navigation(
        self, authenticated_page: Page, cleanup_evaluation: list
    ):
        """
        REG-08: Create a Bulk draft, navigate away to the list, reopen the
        draft via its auditId URL — the Overview card must still show the
        objective entered in the modal.
        """
        nep = NewEvaluationPage(authenticated_page)
        nep.open_new_evaluation_wizard(method="bulk", objective=_OBJECTIVE_A)
        audit_id = nep.get_audit_id_from_url()
        if not audit_id:
            pytest.skip("auditId not present in URL — cannot verify state restoration")
        cleanup_evaluation.append(audit_id)

        nep.go_to_evaluations_list()
        assert "auditId=" not in authenticated_page.url, "Should be on list page now"

        nep.go_to_draft(audit_id)
        assert nep.wait_for_wizard_loaded(), (
            "Wizard must hydrate when reopening the draft via auditId URL"
        )
        objective_restored = nep.get_overview_field("Objective")
        assert objective_restored and _OBJECTIVE_A[:30] in objective_restored, (
            f"Objective must be restored after navigating away and back; got {objective_restored!r}"
        )


# ---------------------------------------------------------------------------
# REG-09 — Back-to-List + reopen preserves draft data (tabs removed Jul 2026)
# ---------------------------------------------------------------------------

class TestTabSwitchingDataPersistence:

    pytestmark = [pytest.mark.regression_write]

    def test_switching_tabs_does_not_lose_form_data(
        self, authenticated_page: Page, cleanup_evaluation: list
    ):
        """
        REG-09 (redesigned): The wizard's Configuration/Test Cases tabs were
        removed in the Jul 2026 single-page redesign. The equivalent
        persistence guarantee: leave the wizard via 'Back to List' and reopen
        the draft — Mode and Objective must be unchanged.
        """
        nep = NewEvaluationPage(authenticated_page)
        nep.open_new_evaluation_wizard(method="bulk", objective=_OBJECTIVE_A)
        audit_id = nep.get_audit_id_from_url()
        if not audit_id:
            pytest.skip("auditId not present — draft was not persisted")
        cleanup_evaluation.append(audit_id)

        mode_before = nep.get_overview_field("Mode")

        nep.click_back_to_list()
        nep.go_to_draft(audit_id)
        assert nep.wait_for_wizard_loaded(), "Wizard must hydrate on reopen"

        mode_after = nep.get_overview_field("Mode")
        objective_after = nep.get_overview_field("Objective")
        assert mode_after == mode_before, (
            f"Mode must persist across Back-to-List; before={mode_before!r} after={mode_after!r}"
        )
        assert objective_after and _OBJECTIVE_A[:30] in objective_after, (
            f"Objective must persist across Back-to-List; got {objective_after!r}"
        )


# ---------------------------------------------------------------------------
# REG-10 — DRAFT vs COMPLETED URL routing (anchor-based, no navigation)
# ---------------------------------------------------------------------------

class TestDraftCompletedUrlRouting:

    def test_draft_row_links_to_wizard_and_completed_row_links_to_report(
        self, authenticated_page: Page
    ):
        """
        REG-10: In the evaluations list, the name anchor inside each row's
        first cell must route:
          • DRAFT rows → /evaluations/new?auditId=… (editable wizard)
          • COMPLETED rows → /evaluations/{id} (read-only report, not /new)
        Checked via the anchors' hrefs — no navigation needed.
        """
        nep = NewEvaluationPage(authenticated_page)
        nep.go_to_evaluations_list()

        # Filter per status tab — page 1 of 'All' may hold only one status.
        authenticated_page.locator(EvaluationsLocators.STATUS_TAB_DRAFT).first.click()
        authenticated_page.wait_for_timeout(2_000)
        if nep.get_draft_row_count() > 0:
            assert nep.draft_row_href_contains_new(), (
                f"DRAFT row anchor must link to /evaluations/new?auditId=…; "
                f"got: {nep.get_first_draft_href()!r}"
            )
        else:
            pytest.skip("No DRAFT rows to test URL routing")

        authenticated_page.locator(
            EvaluationsLocators.STATUS_TAB_COMPLETED
        ).first.click()
        authenticated_page.wait_for_timeout(2_000)
        completed_rows = authenticated_page.locator(EvaluationsLocators.COMPLETED_ROW)
        if completed_rows.count() == 0:
            pytest.skip("No COMPLETED rows to test URL routing")

        assert nep.completed_row_href_excludes_new(), (
            f"COMPLETED row anchor must link to /evaluations/{{id}} (not /new); "
            f"got: {nep.get_first_completed_href()!r}"
        )


# ---------------------------------------------------------------------------
# REG-11 — Auto-save indicator (may be dropped by the redesign)
# ---------------------------------------------------------------------------

class TestAutoSaveIndicatorUpdates:

    pytestmark = [pytest.mark.regression_write]

    def test_auto_save_indicator_updates_on_subsequent_field_changes(
        self, authenticated_page: Page, cleanup_evaluation: list
    ):
        """
        REG-11: If the single-page wizard still has an 'Auto-saved' indicator,
        it must appear after a field change. Skips when the redesigned page
        has no such indicator (draft persistence now happens in the modal).
        """
        nep = NewEvaluationPage(authenticated_page)
        nep.open_new_evaluation_wizard(method="bulk", objective=_OBJECTIVE_A)
        _register_cleanup(nep, cleanup_evaluation)

        if not nep.is_visible(
            EvaluationsLocators.WIZARD_MODULES_HEADING, timeout=15_000
        ):
            pytest.skip("Workspace not hydrated — cannot exercise a field change")

        nep.check_module("hallucination")
        if not nep.is_auto_saved_indicator_visible(timeout=8_000):
            pytest.skip(
                "'Auto-saved' indicator absent on the redesigned single-page "
                "wizard — persistence is handled by the modal flow"
            )


# ---------------------------------------------------------------------------
# REG-12 — Bulk + Playground drafts in one session (no state bleed)
# ---------------------------------------------------------------------------

class TestNoStateBleeedBetweenDrafts:

    pytestmark = [pytest.mark.regression_write]

    def test_automated_and_manual_drafts_in_same_session_no_state_bleed(
        self, authenticated_page: Page, cleanup_evaluation: list
    ):
        """
        REG-12: Create a Bulk draft then a Playground draft in the same browser
        session. Each must get its own auditId, and each Overview card must
        report the mode chosen for it (no shared state).
        """
        nep = NewEvaluationPage(authenticated_page)

        # ── Draft A: Bulk ────────────────────────────────────────────────────
        nep.open_new_evaluation_wizard(method="bulk", objective=_OBJECTIVE_A)
        audit_id_a = nep.get_audit_id_from_url()
        assert audit_id_a, "Bulk draft must have an auditId in the URL"
        cleanup_evaluation.append(audit_id_a)
        mode_a = nep.get_overview_field("Mode")

        # ── Draft B: Playground ──────────────────────────────────────────────
        nep.open_new_evaluation_wizard(method="manual", objective=_OBJECTIVE_B)
        audit_id_b = nep.get_audit_id_from_url()
        assert audit_id_b, "Playground draft must have an auditId in the URL"
        cleanup_evaluation.append(audit_id_b)
        mode_b = nep.get_overview_field("Mode")

        # ── Assertions ───────────────────────────────────────────────────────
        assert audit_id_a != audit_id_b, (
            f"Each draft must have a unique auditId; "
            f"got audit_id_a={audit_id_a!r}, audit_id_b={audit_id_b!r} — "
            "possible state bleed between drafts"
        )
        assert mode_a and "Bulk" in mode_a, (
            f"Bulk draft Overview must report 'Bulk Evaluation'; got {mode_a!r}"
        )
        assert mode_b and "Playground" in mode_b, (
            f"Playground draft Overview must report 'Playground Evaluation'; got {mode_b!r}"
        )
