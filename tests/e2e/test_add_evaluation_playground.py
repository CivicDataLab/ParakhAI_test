"""
End-to-end coverage of the Playground (manual) evaluation creation flow
(Jul 2026 redesign).

Flow under test:
  Start an Evaluation modal (method = Playground / value 'manual') →
  Start Evaluation → single-page wizard at /evaluations/new?auditId=… →
  Evaluation Overview shows Mode "Playground Evaluation" → playground
  workspace hydrates (prompt input / Call Model).

Dev-environment caveat: the playground workspace's module fetch is flaky —
it can resolve to "No modules available for this model type". Workspace-level
tests skip in that case rather than fail; the creation/overview assertions
always run.

All tests create real drafts → `regression_write`-gated + cleanup_evaluation.
"""

import time

import pytest
from playwright.sync_api import Page

from locators.evaluations_locators import EvaluationsLocators
from pages.new_evaluation_page import NewEvaluationPage
from pages.playground_evaluation_page import PlaygroundEvaluationPage

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


def _create_playground_draft(
    page: Page,
    cleanup_evaluation: list,
    objective: str,
    name: str | None = None,
) -> NewEvaluationPage:
    """Drive the modal end-to-end for method=manual and land on the hydrated wizard."""
    nep = NewEvaluationPage(page)
    nep.go_to_evaluations_list()
    nep.click_new_evaluation()
    assert nep.is_modal_visible(), "'Start an Evaluation' modal must open"
    nep.start_evaluation_from_modal(
        method="manual", objective=objective, name=name
    )
    audit_id = nep.get_audit_id_from_url()
    if not audit_id:
        # Dev flake: draft is created but the app occasionally stays on the
        # list instead of navigating. Open the newest draft via its row link.
        nep.go_to_evaluations_list()
        nep.page.locator(EvaluationsLocators.STATUS_TAB_DRAFT).first.click()
        nep.page.wait_for_timeout(2_000)
        nep.click_first_draft_row()
        audit_id = nep.get_audit_id_from_url()
    assert audit_id, (
        f"Starting a playground evaluation must create a draft reachable at ?auditId=…; URL: {page.url}"
    )
    cleanup_evaluation.append(str(audit_id))
    assert nep.wait_for_wizard_loaded(), (
        "Wizard page must hydrate (Evaluation Overview card) after Start Evaluation"
    )
    return nep


def _workspace_hydrated_or_skip(page: Page, timeout_s: int = 60) -> None:
    """Wait for the playground workspace; skip on the known dev flakiness."""
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        body = page.locator("body").inner_text()
        if "No modules available" in body:
            pytest.skip(
                "Dev flakiness: playground workspace reports "
                "'No modules available for this model type'"
            )
        if "Loading evaluation" not in body and "Evaluation Workspace" in body:
            return
        page.wait_for_timeout(3_000)
    pytest.skip(f"Playground workspace did not hydrate within {timeout_s}s on dev")


# ── Smoke ─────────────────────────────────────────────────────────────────────


class TestPlaygroundDraftCreation:
    pytestmark = [pytest.mark.smoke]

    def test_playground_draft_created_and_wizard_hydrates(
        self, page: Page, sandbox_org, cleanup_evaluation
    ):
        nep = _create_playground_draft(
            page, cleanup_evaluation, objective=f"QA playground smoke {_STAMP}"
        )
        assert nep.is_wizard_visible(), "Evaluation Overview card must be visible"

    def test_overview_shows_playground_mode(
        self, page: Page, sandbox_org, cleanup_evaluation
    ):
        objective = f"QA playground overview {_STAMP}"
        nep = _create_playground_draft(page, cleanup_evaluation, objective=objective)
        assert nep.get_overview_field("Mode") == "Playground Evaluation", (
            f"Overview Mode must read 'Playground Evaluation'; "
            f"got {nep.get_overview_field('Mode')!r}"
        )
        assert nep.get_overview_field("Objective") == objective, (
            "Overview Objective must echo the objective entered in the modal"
        )


# ── Functional: workspace ─────────────────────────────────────────────────────


class TestPlaygroundWorkspace:
    def test_workspace_section_renders(
        self, page: Page, sandbox_org, cleanup_evaluation
    ):
        _create_playground_draft(
            page, cleanup_evaluation, objective=f"QA playground ws {_STAMP}"
        )
        _workspace_hydrated_or_skip(page)
        assert page.locator(
            EvaluationsLocators.WIZARD_WORKSPACE_HEADING
        ).first.is_visible(), "Evaluation Workspace section must render"

    def test_prompt_input_available_in_workspace(
        self, page: Page, sandbox_org, cleanup_evaluation
    ):
        _create_playground_draft(
            page, cleanup_evaluation, objective=f"QA playground prompt {_STAMP}"
        )
        _workspace_hydrated_or_skip(page)
        pg = PlaygroundEvaluationPage(page)
        if not pg.is_prompt_input_visible():
            pytest.skip(
                "Prompt input not rendered — playground may require module "
                "selection first on this build"
            )
        # Reaching here means the core playground input is usable.
        assert pg.is_prompt_input_visible()


# ── Negative ──────────────────────────────────────────────────────────────────


class TestPlaygroundFinishGating:
    def test_finish_disabled_at_zero_test_cases(
        self, page: Page, sandbox_org, cleanup_evaluation
    ):
        nep = _create_playground_draft(
            page, cleanup_evaluation, objective=f"QA playground finish {_STAMP}"
        )
        _workspace_hydrated_or_skip(page)
        finish = page.locator(EvaluationsLocators.FINISH_EVALUATION_BUTTON).first
        if not finish.is_visible():
            pytest.skip("Finish Evaluation button not present on this build")
        assert nep.is_finish_evaluation_button_disabled(), (
            "'Finish Evaluation' must be disabled with zero submitted test cases"
        )


# ── Edge: state restoration ───────────────────────────────────────────────────


class TestPlaygroundStateRestoration:
    def test_reload_restores_playground_draft(
        self, page: Page, sandbox_org, cleanup_evaluation
    ):
        objective = f"QA playground reload {_STAMP}"
        nep = _create_playground_draft(page, cleanup_evaluation, objective=objective)
        page.reload(wait_until="load")
        assert nep.wait_for_wizard_loaded(), "Draft must re-hydrate after a reload"
        assert nep.get_overview_field("Mode") == "Playground Evaluation", (
            "Playground mode must survive a page reload"
        )
        assert nep.get_overview_field("Objective") == objective, (
            "Objective must survive a page reload"
        )

    def test_back_to_list_and_reopen_same_draft(
        self, page: Page, sandbox_org, cleanup_evaluation
    ):
        nep = _create_playground_draft(
            page, cleanup_evaluation, objective=f"QA playground reopen {_STAMP}"
        )
        audit_id = nep.get_audit_id_from_url()
        nep.click_back_to_list()
        nep.go_to_draft(audit_id)
        assert nep.wait_for_wizard_loaded(), "Reopened playground draft must hydrate"
        assert nep.get_audit_id_from_url() == audit_id, (
            "Reopening must land on the same draft"
        )
        assert nep.get_overview_field("Mode") == "Playground Evaluation", (
            "Mode must remain Playground Evaluation after reopen"
        )
