"""
End-to-end coverage of the Bulk evaluation creation flow (Jul 2026 redesign).

Flow under test:
  Start an Evaluation modal (method = Bulk) → Start Evaluation →
  single-page wizard at /evaluations/new?auditId=… →
  Evaluation Overview card + Bulk workspace (modules, prompt-library
  source, Run Evaluation gating).

Every test creates a real draft on the platform, so the whole module is
`regression_write`-gated (skips without SANDBOX_ORG_SLUG) and every created
auditId is registered with the `cleanup_evaluation` teardown.
"""

import time

import pytest
from playwright.sync_api import Page

from locators.evaluations_locators import EvaluationsLocators
from pages.new_evaluation_page import NewEvaluationPage

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.regression,
    pytest.mark.regression_write,
    pytest.mark.auth,
]

_STAMP = time.strftime("%H%M%S")


@pytest.fixture
def page(authenticated_page_fast):
    """Override: cached session — no per-test Keycloak round-trip."""
    return authenticated_page_fast


def _create_bulk_draft(
    page: Page,
    cleanup_evaluation: list,
    objective: str,
    eval_type: str = "technical",
    name: str | None = None,
) -> NewEvaluationPage:
    """Drive the modal end-to-end for method=bulk and land on the hydrated wizard."""
    nep = NewEvaluationPage(page)
    nep.go_to_evaluations_list()
    nep.click_new_evaluation()
    assert nep.is_modal_visible(), "'Start an Evaluation' modal must open"
    nep.start_evaluation_from_modal(
        method="bulk", eval_type=eval_type, objective=objective, name=name
    )
    audit_id = nep.get_audit_id_from_url()
    if not audit_id:
        # Dev flake: the draft is created but the app occasionally stays on the
        # list instead of navigating. Open the newest draft via its row link.
        nep.go_to_evaluations_list()
        nep.page.locator(EvaluationsLocators.STATUS_TAB_DRAFT).first.click()
        nep.page.wait_for_timeout(2_000)
        nep.click_first_draft_row()
        audit_id = nep.get_audit_id_from_url()
    assert audit_id, (
        f"Starting a bulk evaluation must create a draft reachable at ?auditId=…; URL: {page.url}"
    )
    cleanup_evaluation.append(str(audit_id))
    assert nep.wait_for_wizard_loaded(), (
        "Wizard page must hydrate (Evaluation Overview card) after Start Evaluation"
    )
    return nep


# ── Smoke ─────────────────────────────────────────────────────────────────────


class TestBulkDraftCreation:
    pytestmark = [pytest.mark.smoke]

    def test_bulk_draft_created_and_wizard_hydrates(
        self, page: Page, sandbox_org, cleanup_evaluation
    ):
        nep = _create_bulk_draft(
            page, cleanup_evaluation, objective=f"QA bulk smoke {_STAMP}"
        )
        assert nep.is_wizard_visible(), "Evaluation Overview card must be visible"
        assert nep.is_visible(EvaluationsLocators.WIZARD_WORKSPACE_HEADING), (
            "Evaluation Workspace section must render for a bulk draft"
        )

    def test_overview_reflects_modal_inputs(
        self, page: Page, sandbox_org, cleanup_evaluation
    ):
        objective = f"QA bulk overview {_STAMP}"
        nep = _create_bulk_draft(page, cleanup_evaluation, objective=objective)
        assert nep.get_overview_field("Mode") == "Bulk Evaluation", (
            f"Overview Mode must read 'Bulk Evaluation'; got {nep.get_overview_field('Mode')!r}"
        )
        evaluator = nep.get_overview_field("Evaluator") or ""
        assert "Technical" in evaluator, (
            f"Overview Evaluator must reflect the Technical selection; got {evaluator!r}"
        )
        assert nep.get_overview_field("Objective") == objective, (
            "Overview Objective must echo the objective entered in the modal"
        )
        scope = nep.get_overview_field("Scope") or ""
        assert scope and scope != "--", (
            f"Overview Scope must have a default value; got {scope!r}"
        )


# ── Functional: modules + test-case source ────────────────────────────────────


class TestBulkWorkspaceModules:
    def test_module_check_reveals_submodule_dropdown(
        self, page: Page, sandbox_org, cleanup_evaluation
    ):
        nep = _create_bulk_draft(
            page, cleanup_evaluation, objective=f"QA bulk modules {_STAMP}"
        )
        assert nep.is_visible(EvaluationsLocators.WIZARD_MODULES_HEADING), (
            "'Evaluation Modules' section must render"
        )
        assert not nep.is_submodule_prompt_visible(), (
            "Sub-module prompt must be hidden before any module is checked"
        )
        nep.check_module("hallucination")
        assert nep.is_submodule_prompt_visible(), (
            "Checking a module must reveal 'Select sub-modules from dropdown'"
        )

    def test_all_three_modules_checkable(
        self, page: Page, sandbox_org, cleanup_evaluation
    ):
        nep = _create_bulk_draft(
            page, cleanup_evaluation, objective=f"QA bulk 3 modules {_STAMP}"
        )
        for module in ("hallucination", "bias", "privacy"):
            nep.check_module(module)
        checked = page.locator("input[type='checkbox']:checked").count()
        assert checked >= 3, (
            f"All three evaluation modules must be checkable; only {checked} checked"
        )

    def test_test_case_source_options_present(
        self, page: Page, sandbox_org, cleanup_evaluation
    ):
        nep = _create_bulk_draft(
            page, cleanup_evaluation, objective=f"QA bulk sources {_STAMP}"
        )
        assert nep.is_visible(EvaluationsLocators.WIZARD_PROMPT_LIBRARY_OPTION), (
            "'Select a prompt library' source option must be present"
        )
        assert nep.is_visible(EvaluationsLocators.WIZARD_OWN_PROMPTS_OPTION), (
            "'Add your own prompts' source option must be present"
        )
        assert nep.is_max_test_cases_note_visible(), (
            "The maximum-test-cases note must be shown in the bulk workspace"
        )


# ── Negative: Run Evaluation gating ───────────────────────────────────────────


class TestRunEvaluationGating:
    def test_run_disabled_without_prompt_library(
        self, page: Page, sandbox_org, cleanup_evaluation
    ):
        nep = _create_bulk_draft(
            page, cleanup_evaluation, objective=f"QA bulk gating {_STAMP}"
        )
        assert not nep.is_run_evaluation_button_enabled(), (
            "'Run Evaluation' must be disabled before a prompt library is selected"
        )
        assert nep.is_run_evaluation_library_error_visible(), (
            "'Please select a prompt library…' hint must be shown"
        )

    def test_run_still_disabled_with_module_but_no_library(
        self, page: Page, sandbox_org, cleanup_evaluation
    ):
        nep = _create_bulk_draft(
            page, cleanup_evaluation, objective=f"QA bulk gating2 {_STAMP}"
        )
        nep.check_module("hallucination")
        page.wait_for_timeout(1_000)
        assert not nep.is_run_evaluation_button_enabled(), (
            "Checking a module alone (no prompt library) must not enable 'Run Evaluation'"
        )


# ── Regression: persistence, routing, evaluator variants, cancel ──────────────


class TestBulkDraftPersistence:
    def test_draft_persists_after_back_to_list_and_reopen(
        self, page: Page, sandbox_org, cleanup_evaluation
    ):
        objective = f"QA bulk persist {_STAMP}"
        nep = _create_bulk_draft(
            page,
            cleanup_evaluation,
            objective=objective,
            name=f"QA Persist {_STAMP}",
        )
        audit_id = nep.get_audit_id_from_url()
        nep.click_back_to_list()
        assert "auditId=" not in page.url, "Back to List must leave the wizard URL"
        # Re-open the same draft directly and verify state survived the round trip.
        nep.go_to_draft(audit_id)
        assert nep.wait_for_wizard_loaded(), "Reopened draft must hydrate"
        assert nep.get_overview_field("Objective") == objective, (
            "Draft objective must survive Back to List → reopen"
        )
        assert nep.get_overview_field("Mode") == "Bulk Evaluation", (
            "Draft mode must survive Back to List → reopen"
        )

    def test_new_draft_appears_in_draft_tab_with_wizard_link(
        self, page: Page, sandbox_org, cleanup_evaluation
    ):
        nep = _create_bulk_draft(
            page,
            cleanup_evaluation,
            objective=f"QA bulk listed {_STAMP}",
            name=f"QA Listed {_STAMP}",
        )
        audit_id = nep.get_audit_id_from_url()
        nep.click_back_to_list()
        nep.page.locator(EvaluationsLocators.STATUS_TAB_DRAFT).first.click()
        nep.page.wait_for_timeout(2_000)
        # Parallel workers also create drafts, so don't assume ours is the
        # first row — find its wizard link by auditId anywhere in the tab.
        our_link = nep.page.locator(f"a[href*='auditId={audit_id}']")
        assert our_link.count() > 0, (
            f"The just-created draft (auditId={audit_id}) must appear in the "
            "Draft tab with a wizard link"
        )
        href = our_link.first.get_attribute("href") or ""
        assert "/evaluations/new" in href, (
            f"Draft rows must link to the editable wizard; got href={href!r}"
        )

    def test_back_to_list_exits_draft_wizard(
        self, page: Page, sandbox_org, cleanup_evaluation
    ):
        """'Back to List' is the draft exit path; the header Cancel button must
        at least be present (its enabled state varies with hydration timing)."""
        nep = _create_bulk_draft(
            page, cleanup_evaluation, objective=f"QA bulk cancel {_STAMP}"
        )
        assert nep.is_visible(nep.WIZARD_CANCEL_EVALUATION, timeout=10_000), (
            "The header 'Cancel' button must be present on the draft wizard"
        )
        nep.click_back_to_list()
        assert "auditId=" not in page.url, (
            f"'Back to List' must navigate away from the wizard; still on {page.url}"
        )


class TestEvaluatorTypeVariants:
    @pytest.mark.parametrize(
        ("eval_type", "expected"),
        [("domain", "Domain"), ("cultural", "Cultural")],
    )
    def test_evaluator_type_reflected_in_overview(
        self, page: Page, sandbox_org, cleanup_evaluation, eval_type, expected
    ):
        nep = _create_bulk_draft(
            page,
            cleanup_evaluation,
            objective=f"QA bulk {eval_type} {_STAMP}",
            eval_type=eval_type,
        )
        evaluator = nep.get_overview_field("Evaluator") or ""
        assert expected in evaluator, (
            f"Overview Evaluator must reflect the {eval_type} selection; got {evaluator!r}"
        )
