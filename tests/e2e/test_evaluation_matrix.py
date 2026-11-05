"""Evaluation creation matrix: create -> run -> COMPLETED -> results -> report.

Opt-in. Each case is a REAL run (bulk ~6 min against the model), so nothing
runs unless EVAL_MATRIX is set:

    EVAL_MATRIX=pairwise SANDBOX_ORG_SLUG=1 pytest tests/e2e/test_evaluation_matrix.py   # 14 cases
    EVAL_MATRIX=all      SANDBOX_ORG_SLUG=1 pytest tests/e2e/test_evaluation_matrix.py   # 135 cases

The ParakhAPI allows 60 POST/min and 1000/hour per IP: run with one worker.
Completed audits are kept (they are the evidence); only audits that never
reach COMPLETED are cancelled by the cleanup fixture.
"""

from __future__ import annotations

import os
import time

import pytest

from locators.evaluations_locators import EvaluationsLocators
from pages.evaluation_detail_page import EvaluationDetailPage
from pages.new_evaluation_page import NewEvaluationPage
from tests.data.evaluation_matrix import Combo, combos_for
from tests.data.test_data import TestGraphQL

COMBOS = combos_for(os.getenv("EVAL_MATRIX", ""))
BUDGET_S = int(os.getenv("EVAL_MATRIX_BUDGET_S", "600"))

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.regression,
    pytest.mark.regression_write,
    pytest.mark.auth,
]

_AUDIT_Q = "query($id: ID!){ audit(auditId:$id){ id status totalTests passedTests failedTests } }"
_MODULE_WORD = {"hallucination": "hallucination", "bias": "bias", "privacy": "privacy"}


def _audit(client, audit_id: str) -> dict:
    res = client(_AUDIT_Q, variables={"id": str(audit_id)})
    return ((res.get("data") or {}).get("audit")) or {}


def _wait_status(client, audit_id: str, want: tuple[str, ...], budget_s: int) -> dict:
    deadline = time.monotonic() + budget_s
    last = None
    while time.monotonic() < deadline:
        audit = _audit(client, audit_id)
        last = audit.get("status")
        if last in want:
            return audit
        if last in ("FAILED", "CANCELLED"):
            pytest.fail(f"audit {audit_id} ended {last} while waiting for {want}")
        time.sleep(15)
    pytest.fail(f"audit {audit_id} still {last!r} after {budget_s}s (wanted {want})")


def _create_and_configure(nep: NewEvaluationPage, combo: Combo) -> str:
    nep.go_to_evaluations_list()
    nep.click_new_evaluation()
    assert nep.is_modal_visible(), "New Evaluation modal must open"
    nep.start_evaluation_from_modal(
        method=combo.method,
        eval_type=combo.evaluator,
        domain=combo.domain,
        objective=f"Matrix {combo.id}",
    )
    assert nep.wait_for_wizard_loaded(), "wizard must hydrate"
    audit_id = nep.get_audit_id_from_url()
    assert audit_id, "Start Evaluation must put auditId in the URL"
    return audit_id


def _drive_bulk(nep: NewEvaluationPage, combo: Combo) -> None:
    for module in combo.modules:
        nep.check_module(module)
    nep.page.wait_for_timeout(500)
    assert nep.select_one_submodule_in_each_module() >= 1, "a sub-module must be selectable"
    if combo.source == "library":
        nep.select_prompt_library_source()
        nep.page.wait_for_timeout(1_500)
        assert nep.select_first_prompt_library(), "a prompt library must be available"
    else:
        nep.select_own_prompts_source()
        nep.add_custom_prompt("What is the capital of India?", "New Delhi")
        nep.add_custom_prompt("Name the largest planet in the solar system.", "Jupiter")
    assert nep.is_run_evaluation_button_enabled(), "Run Evaluation must enable once configured"
    nep.click_run_evaluation()


def _drive_playground(nep: NewEvaluationPage) -> None:
    for prompt in (
        "What is the capital of India?",
        "Summarise photosynthesis in one sentence.",
        "Give two tips for staying hydrated.",
    ):
        nep.submit_playground_test_case(prompt)
    assert nep.is_finish_evaluation_button_enabled(), "Finish must enable after 3 test cases"
    nep.click_finish_evaluation()


@pytest.mark.timeout(BUDGET_S + 600)
@pytest.mark.parametrize("combo", COMBOS, ids=[c.id for c in COMBOS])
def test_create_run_complete_and_report(
    combo: Combo,
    authenticated_page_fast,
    authenticated_graphql_client,
    sandbox_org,
    cleanup_evaluation,
):
    page = authenticated_page_fast
    client = authenticated_graphql_client
    org_id = int(sandbox_org)

    nep = NewEvaluationPage(page, org_id=org_id)
    audit_id = _create_and_configure(nep, combo)
    cleanup_evaluation.append(audit_id)

    if combo.method == "bulk":
        _drive_bulk(nep, combo)
        audit = _wait_status(client, audit_id, ("PENDING_REVIEW", "COMPLETED"), BUDGET_S)
    else:
        _drive_playground(nep)
        audit = _wait_status(client, audit_id, ("PENDING_REVIEW", "COMPLETED"), BUDGET_S)

    if audit["status"] == "PENDING_REVIEW":
        res = client(
            TestGraphQL.MUTATION_SUBMIT_AUDIT_REVIEW,
            variables={"input": {"auditId": audit_id, "recommendations": f"Matrix {combo.id}: auto-approved."}},
            method="POST",
        )
        assert ((res.get("data") or {}).get("submitAuditReview") or {}).get("success"), res
        audit = _wait_status(client, audit_id, ("COMPLETED",), 120)

    cleanup_evaluation.remove(audit_id)  # completed audits are evidence: keep them
    assert audit["status"] == "COMPLETED"
    assert (audit.get("totalTests") or 0) > 0, f"completed run reported no tests: {audit}"

    detail = EvaluationDetailPage(page, org_id=org_id)
    detail.go_to_evaluation_detail(int(audit_id))
    assert detail.wait_for_detail_hydrated(), "detail page must hydrate"
    assert detail.is_summary_section_visible(), "summary section must render"
    assert detail.get_summary_stat("TOTAL PASS RATE"), "pass rate must render"
    assert detail.get_summary_stat("TOTAL TEST CASES"), "total test cases must render"
    for level in ("LOW RISK", "MEDIUM RISK", "HIGH RISK"):
        assert detail.get_summary_stat(level) != "", f"{level} count must render"
    assert detail.get_result_input_block_count() > 0, "results must list at least one input"

    assert combo.evaluator in detail.get_overview_field("Evaluator").lower()
    assert combo.domain in detail.get_overview_field("Scope").lower()
    assert combo.method in detail.get_overview_field("Mode").lower()
    if combo.method == "bulk":
        modules = detail.get_overview_field("Modules").lower()
        for m in combo.modules:
            assert _MODULE_WORD[m] in modules, f"Modules field {modules!r} must list {m}"

    with page.expect_download(timeout=60_000) as dl:
        page.locator(EvaluationsLocators.DOWNLOAD_REPORT_BUTTON).first.click()
    path = dl.value.path()
    assert path and os.path.getsize(path) > 500, "downloaded report must not be empty"
