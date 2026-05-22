"""
Multi-user assignment tests — requires two authenticated sessions simultaneously.

Gating:
- `regression_write` marker: skips when SANDBOX_ORG_SLUG is unset (no writes
  against real org data).
- `authenticated_page_u2` fixture: skips when TEST_EMAIL_2 / TEST_PASSWORD_2
  are not configured.

Flow under test:
  USER_1 (AI Maker) uses the GraphQL API to add USER_2 as an evaluator and
  assign them to a model version. USER_2's evaluator dashboard (second browser
  session, simultaneously open) must then show the pending invitation.

This exercises the full cross-user state sync: write via USER_1's token →
read via USER_2's authenticated UI session.
"""

import pytest
from playwright.sync_api import Page

from pages.evaluator_role_page import EvaluatorRolePage
from tests.data.test_data import TestGraphQL, TestSandbox
from utils.config import Config

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.regression,
    pytest.mark.regression_write,
    pytest.mark.auth,
]


class TestCrossUserAssignment:
    """USER_1 assigns a model to USER_2; USER_2 sees the invitation."""

    def test_user2_sees_pending_invitation_after_assignment(
        self,
        authenticated_page: Page,
        authenticated_page_u2: Page,
        authenticated_graphql_client,
        sandbox_org: str,
        cleanup_assignment: list,
        cleanup_evaluator: list,
    ):
        """
        USER_1 adds USER_2 to the sandbox org as an evaluator (API), then
        assigns USER_2 to the first available model version (API). USER_2's
        evaluator dashboard must show at least one pending invitation.
        """
        user2_email = Config.TEST_EMAIL_2
        if not user2_email or user2_email.endswith("@example.com"):
            pytest.skip("TEST_EMAIL_2 not configured")

        # Step 1 — Add USER_2 to the org as an evaluator
        add_result = authenticated_graphql_client(
            TestGraphQL.MUTATION_ADD_AUDITOR_TO_ORGANIZATION,
            variables={
                "organizationId": sandbox_org,
                "input": {"email": user2_email},
            },
            method="POST",
        )
        add_data = add_result.get("data", {}).get("addAuditorToOrganization", {})
        if not add_data.get("success"):
            pytest.skip(
                f"Could not add USER_2 to sandbox org: {add_data.get('message')}"
            )

        # Register USER_2 for evaluator-removal cleanup (org_id, user_id).
        # user_id is not returned by the mutation — look it up from org auditors.
        org_auditors = authenticated_graphql_client(
            TestGraphQL.QUERY_ORGANIZATION_AUDITORS,
            variables={"organizationId": sandbox_org},
        ).get("data", {}).get("organizationAuditors") or []
        user2_record = next(
            (a for a in org_auditors if a.get("email") == user2_email), None
        )
        if user2_record:
            cleanup_evaluator.append((sandbox_org, user2_record["id"]))

        # Step 2 — Assign USER_2 to the first available sandbox model version
        sandbox_model_id = getattr(TestSandbox, "MODEL_ID", None)
        sandbox_version_id = getattr(TestSandbox, "MODEL_VERSION_ID", None)
        if not sandbox_model_id or not sandbox_version_id:
            pytest.skip(
                "SANDBOX_MODEL_ID / SANDBOX_MODEL_VERSION_ID not configured — "
                "cannot create a version assignment"
            )

        assign_result = authenticated_graphql_client(
            TestGraphQL.MUTATION_ASSIGN_AUDITOR_TO_VERSION,
            variables={
                "input": {
                    "modelId": sandbox_model_id,
                    "modelVersionId": sandbox_version_id,
                    "auditorEmail": user2_email,
                }
            },
            method="POST",
        )
        assign_data = assign_result.get("data", {}).get("assignAuditorToVersion", {})
        if not assign_data.get("success"):
            pytest.skip(
                f"Could not assign USER_2 to sandbox model version: "
                f"{assign_data.get('message')}"
            )
        assignment_id = assign_data.get("assignment", {}).get("id")
        if assignment_id:
            cleanup_assignment.append(assignment_id)

        # Step 3 — USER_2 checks their evaluator dashboard for the pending invitation
        evaluator = EvaluatorRolePage(authenticated_page_u2)
        evaluator.go_to_assignments()
        pending_count = evaluator.get_pending_invitation_count()
        assert pending_count > 0, (
            "USER_2's evaluator dashboard must show at least one pending invitation "
            f"after USER_1 created the assignment (found {pending_count})"
        )

    def test_two_sessions_do_not_interfere(
        self,
        authenticated_page: Page,
        authenticated_page_u2: Page,
        sandbox_org: str,
    ):
        """
        USER_1 and USER_2 can both be authenticated simultaneously without
        either session being invalidated or redirected to login.
        """
        from pages.ai_maker_dashboard_page import AIMakerDashboardPage

        dash_u1 = AIMakerDashboardPage(authenticated_page)
        dash_u1.go_to_dashboard()
        assert "login" not in authenticated_page.url.lower(), (
            "USER_1 session must remain authenticated while USER_2 is also logged in"
        )

        evaluator_u2 = EvaluatorRolePage(authenticated_page_u2)
        evaluator_u2.go_to_evaluator_home()
        assert "login" not in authenticated_page_u2.url.lower(), (
            "USER_2 session must remain authenticated while USER_1 is also logged in"
        )
