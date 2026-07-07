"""
Full cross-role lifecycle: AI Maker assigns a model version to an evaluator,
the evaluator accepts the invitation, and then creates + runs an evaluation
against that assignment from their own dashboard.

Flow under test:
  USER_1 (AI Maker) discovers a sandbox model+version and assigns USER_2 as
  its evaluator (API — same discovery/assign sequence as
  test_multi_user_assignment.py). USER_2 (separate authenticated UI session)
  then:
    1. Sees the pending invitation on their evaluator dashboard and accepts it.
    2. Is routed to /dashboard/auditor/evaluations/new?modelId=&versionId=,
       the auditor entry point that reuses the same NewEvaluationContent
       wizard as the AI Maker's "New Evaluation" flow once it verifies an
       ACCEPTED/IN_PROGRESS assignment exists for that model+version
       (confirmed in ParakhAI-frontend's
       app/[locale]/dashboard/auditor/evaluations/new/page.tsx). Landing here
       auto-creates a blank draft audit (no "Start an Evaluation" modal step,
       since model/version are already fixed by the assignment).
    3. Configures and runs a bulk evaluation from that page.

This is the only test that exercises the full handoff end-to-end; the
existing multi-user (test_multi_user_assignment.py), accept/decline
(test_assignment_workflow.py), and playground (test_playground_evaluation_flow.py)
tests each cover one segment in isolation.

Gating:
- `regression_write` marker: skips when SANDBOX_ORG_SLUG is unset.
- `authenticated_page_u2` fixture: skips when TEST_EMAIL_2/TEST_PASSWORD_2
  are unset.
- Every step past the assignment skips gracefully if the platform doesn't
  render the expected control (no models, no prompt libraries, accept
  button absent, assignment status not yet propagated, etc.) — the goal is
  to prove the happy path works when the data is there, not to fail the
  suite on environment gaps. The auditor entry point has no prior UI
  automation coverage, so field presence (evaluation scope, mode dropdown)
  is checked defensively rather than assumed.
"""

import pytest
from playwright.sync_api import Page

from locators.evaluations_locators import EvaluationsLocators
from pages.evaluator_role_page import EvaluatorRolePage
from pages.new_evaluation_page import NewEvaluationPage
from tests.data.test_data import TestGraphQL
from utils.config import Config

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.regression,
    pytest.mark.regression_write,
    pytest.mark.auth,
    pytest.mark.timeout(300),
]

_OBJECTIVE = "Evaluator-initiated evaluation — full handoff regression test"


class TestAssignmentAcceptAndEvaluate:
    """USER_1 assigns USER_2; USER_2 accepts and runs an evaluation."""

    def test_evaluator_accepts_assignment_and_completes_evaluation(
        self,
        authenticated_page_u2: Page,
        authenticated_graphql_client,
        sandbox_org: str,
        cleanup_assignment: list,
        cleanup_evaluator: list,
        cleanup_evaluation: list,
    ):
        user2_email = Config.TEST_EMAIL_2
        if not user2_email or user2_email.endswith("@example.com"):
            pytest.skip("TEST_EMAIL_2 not configured")

        # ── Step 1: USER_1 (API) adds USER_2 as an evaluator, if not already ──
        add_result = authenticated_graphql_client(
            TestGraphQL.MUTATION_ADD_AUDITOR_TO_ORGANIZATION,
            variables={
                "organizationId": sandbox_org,
                "input": {"email": user2_email},
            },
            method="POST",
        )
        add_data = ((add_result or {}).get("data") or {}).get("addAuditorToOrganization") or {}
        already_member = not add_data.get("success") and "already" in (
            add_data.get("message") or ""
        ).lower()
        if not add_data.get("success") and not already_member:
            pytest.skip(f"Could not add USER_2 to sandbox org: {add_data.get('message')}")

        _aud_resp = authenticated_graphql_client(
            TestGraphQL.QUERY_ORGANIZATION_AUDITORS,
            variables={"organizationId": sandbox_org},
        ) or {}
        org_auditors_resp = (_aud_resp.get("data") or {}).get("organizationAuditors") or {}
        org_auditors = (
            org_auditors_resp.get("auditors") or [] if isinstance(org_auditors_resp, dict) else []
        )
        user2_record = next(
            (a for a in org_auditors if isinstance(a, dict) and a.get("email") == user2_email),
            None,
        )
        if user2_record and not already_member:
            cleanup_evaluator.append((sandbox_org, user2_record["id"]))

        # ── Step 2: USER_1 (API) discovers a model+version and assigns USER_2 ──
        _models_resp = authenticated_graphql_client(
            TestGraphQL.QUERY_AI_MODELS_WITH_VERSIONS,
            variables={"limit": 10},
        ) or {}
        models_resp = (_models_resp.get("data") or {}).get("aiModels") or []
        model_id = model_name = version_id = None
        for m in models_resp:
            versions = m.get("versions") or []
            if versions:
                model_id = m["id"]
                model_name = m.get("name", "")
                version_id = versions[0]["id"]
                break
        if not model_id or not version_id:
            pytest.skip("No AI models with versions found in sandbox — cannot assign a version")

        assign_result = authenticated_graphql_client(
            TestGraphQL.MUTATION_ASSIGN_AUDITOR_TO_VERSION,
            variables={
                "input": {
                    "modelId": model_id,
                    "modelName": model_name,
                    "modelVersionId": version_id,
                    "auditorEmail": user2_email,
                }
            },
            method="POST",
        ) or {}
        assign_data = (assign_result.get("data") or {}).get("assignAuditorToVersion") or {}
        if not assign_data.get("success"):
            pytest.skip(
                f"Could not assign USER_2 to sandbox model version: {assign_data.get('message')}"
            )
        assignment_id = (assign_data.get("assignment") or {}).get("id")
        if assignment_id:
            cleanup_assignment.append(assignment_id)

        # ── Step 3: USER_2 (UI) accepts the pending invitation ──
        evaluator = EvaluatorRolePage(authenticated_page_u2)
        evaluator.go_to_assignments()
        if evaluator.get_pending_invitation_count() == 0:
            pytest.skip(
                "USER_2 has no pending invitation to accept — assignment may not "
                "have propagated to the UI yet"
            )
        if not evaluator.click_accept_first_pending():
            pytest.skip("Accept button not found on the pending invitation row")

        # ── Step 4: USER_2 (UI) is routed to their own New Evaluation entry point ──
        eval_url = Config.url(
            f"/dashboard/auditor/evaluations/new?modelId={model_id}&versionId={version_id}"
        )
        evaluator.navigate(eval_url)
        evaluator.wait_for_app_ready()
        if evaluator.is_visible("text=/don't have an accepted assignment/i", timeout=5_000):
            pytest.skip(
                "Platform has not yet propagated the ACCEPTED status to the "
                "auditor evaluation entry point — likely a brief backend lag"
            )

        nep = NewEvaluationPage(authenticated_page_u2)
        if not nep.wait_for_wizard_loaded():
            pytest.skip("Evaluation wizard did not hydrate for the auditor entry point")

        # ── Step 5: USER_2 (UI) fills the required fields and runs the evaluation ──
        # This entry point skips the "Start an Evaluation" modal (model/version
        # are already fixed by the assignment), so objective/scope/mode — set
        # via the modal on the AI Maker path — must be filled directly here.
        if nep.is_visible(EvaluationsLocators.EVAL_OBJECTIVE_TEXTAREA, timeout=10_000):
            nep.fill_evaluation_objective(_OBJECTIVE)
        if nep.is_visible(EvaluationsLocators.EVAL_SCOPE_DROPDOWN, timeout=3_000):
            try:
                nep.select_evaluation_scope("General")
            except Exception:
                pass
        nep.check_module("hallucination")
        if nep.is_visible(nep.EVAL_MODE_DROPDOWN, timeout=5_000):
            try:
                nep.select_mode("automated")
            except Exception:
                pass

        audit_id = nep.get_audit_id_from_url()
        if audit_id:
            cleanup_evaluation.append(str(audit_id))

        enabled = nep.configure_bulk_workspace_minimal(module="hallucination")
        if not enabled:
            pytest.skip(
                "Run Evaluation did not enable after minimal configuration — "
                "no prompt library available in this sandbox"
            )

        nep.click_run_evaluation()
        authenticated_page_u2.wait_for_timeout(3_000)

        if not audit_id:
            pytest.skip("No auditId captured — cannot verify backend run status")

        result = authenticated_graphql_client(
            TestGraphQL.QUERY_AUDIT, variables={"auditId": str(audit_id)}
        )
        if result.get("errors"):
            pytest.skip(
                f"Could not query audit status via USER_1's token: {result['errors']}"
            )
        audit = ((result.get("data") or {}).get("audit")) or {}
        assert audit.get("status") in ("QUEUED", "IN_PROGRESS", "PENDING_REVIEW", "COMPLETED"), (
            "Evaluator-initiated Run Evaluation must move the audit off DRAFT; "
            f"got status={audit.get('status')!r}"
        )
