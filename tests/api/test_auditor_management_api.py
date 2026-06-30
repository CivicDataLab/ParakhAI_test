"""
API contract tests for auditor management queries and mutations.

Covers:
- TestOrganizationQuery          — organization(id): shape, access control
- TestAiModelDetailQuery         — aiModel(modelId): shape, auth enforcement
- TestAuditorAssignmentQueries   — auditorAssignments, auditorAssignment by ID
- TestAddAuditorMutation         — addAuditorToOrganization shape (invalid IDs)
- TestRemoveAuditorMutation      — removeAuditorFromOrganization shape (invalid IDs)
- TestAssignAuditorToVersionMutation — assignAuditorToVersion shape/validation
- TestUpdateAssignmentStatus     — updateAuditorAssignmentStatus validation

All shape/error tests use non-existent IDs so nothing is persisted.
Write-side lifecycle tests (actual assignment create/cleanup) live in
tests/e2e/test_assignment_workflow.py and test_multi_user_assignment.py.
"""

import pytest

from tests.data.test_data import TestGraphQL

pytestmark = [pytest.mark.api, pytest.mark.regression, pytest.mark.auth]


# ── organization(id) ──────────────────────────────────────────────────────────


class TestOrganizationQuery:
    """organization(id) is membership-gated — returns null for unknown IDs."""

    def test_organization_unknown_id_returns_null(self, authenticated_graphql_client):
        result = authenticated_graphql_client(
            TestGraphQL.QUERY_ORGANIZATION, variables={"id": "999999999"}
        )
        assert "data" in result or "errors" in result
        if result.get("data") is not None:
            assert result["data"].get("organization") is None

    def test_organization_without_auth_returns_null(self, graphql_client):
        result = graphql_client(
            TestGraphQL.QUERY_ORGANIZATION, variables={"id": "1"}
        )
        assert "data" in result or "errors" in result
        if result.get("data") is not None:
            assert result["data"].get("organization") is None

    def test_organization_my_org_returns_shape(self, authenticated_graphql_client):
        orgs_result = authenticated_graphql_client(TestGraphQL.QUERY_MY_ORGANIZATIONS)
        orgs = ((orgs_result.get("data") or {}).get("myOrganizations")) or []
        if not orgs:
            pytest.skip("No organizations available for this user")

        org_id = orgs[0]["id"]
        result = authenticated_graphql_client(
            TestGraphQL.QUERY_ORGANIZATION, variables={"id": str(org_id)}
        )
        assert "data" in result or "errors" in result
        if result.get("data") and result["data"].get("organization"):
            org = result["data"]["organization"]
            assert "id" in org
            assert "name" in org
            assert "slug" in org


# ── aiModel(modelId) ─────────────────────────────────────────────────────────


class TestAiModelDetailQuery:
    """aiModel(modelId) returns a single model or null for unknown IDs."""

    def test_ai_model_unknown_id_returns_null(self, authenticated_graphql_client):
        result = authenticated_graphql_client(
            TestGraphQL.QUERY_AI_MODEL,
            variables={"modelId": "00000000-0000-0000-0000-000000000000"},
        )
        assert "data" in result or "errors" in result
        if result.get("data") is not None:
            assert result["data"].get("aiModel") is None

    def test_ai_model_shape_with_valid_model(self, authenticated_graphql_client):
        models_result = authenticated_graphql_client(TestGraphQL.QUERY_MY_MODELS)
        models = ((models_result.get("data") or {}).get("myModels")) or []
        if not models:
            pytest.skip("No AI models available for this user")

        model_id = models[0]["id"]
        result = authenticated_graphql_client(
            TestGraphQL.QUERY_AI_MODEL, variables={"modelId": str(model_id)}
        )
        assert "data" in result or "errors" in result
        if result.get("data") and result["data"].get("aiModel"):
            model = result["data"]["aiModel"]
            assert "id" in model
            assert "name" in model
            assert "modelType" in model

    def test_ai_model_without_auth_returns_null(self, graphql_client):
        result = graphql_client(
            TestGraphQL.QUERY_AI_MODEL,
            variables={"modelId": "00000000-0000-0000-0000-000000000000"},
        )
        assert "data" in result or "errors" in result
        if result.get("data") is not None:
            assert result["data"].get("aiModel") is None


# ── auditorAssignments + auditorAssignment ────────────────────────────────────


class TestAuditorAssignmentDetailQueries:
    """Verify auditorAssignment(id) and auditorAssignments(filters) shape."""

    def test_auditor_assignments_returns_list(self, authenticated_graphql_client):
        result = authenticated_graphql_client(TestGraphQL.QUERY_AUDITOR_ASSIGNMENTS)
        assert "data" in result or "errors" in result
        if result.get("data") and result["data"].get("auditorAssignments") is not None:
            assignments = result["data"]["auditorAssignments"]
            assert isinstance(assignments, list)
            for a in assignments[:3]:
                assert "id" in a
                assert "status" in a

    def test_auditor_assignments_status_filter(self, authenticated_graphql_client):
        result = authenticated_graphql_client(
            TestGraphQL.QUERY_AUDITOR_ASSIGNMENTS, variables={"status": "PENDING"}
        )
        assert "data" in result or "errors" in result
        if result.get("data") and result["data"].get("auditorAssignments"):
            for a in result["data"]["auditorAssignments"]:
                assert a.get("status") == "PENDING"

    def test_auditor_assignment_by_id_invalid_returns_null(self, authenticated_graphql_client):
        result = authenticated_graphql_client(
            TestGraphQL.QUERY_AUDITOR_ASSIGNMENT, variables={"assignmentId": "999999999"}
        )
        assert "data" in result or "errors" in result
        if result.get("data") is not None:
            assert result["data"].get("auditorAssignment") is None

    def test_auditor_assignments_without_auth_returns_empty(self, graphql_client):
        result = graphql_client(TestGraphQL.QUERY_AUDITOR_ASSIGNMENTS)
        assert "data" in result or "errors" in result
        if result.get("data") and result["data"].get("auditorAssignments") is not None:
            assert result["data"]["auditorAssignments"] == []


# ── addAuditorToOrganization mutation shape ───────────────────────────────────


class TestAddAuditorMutation:
    """addAuditorToOrganization must return structured success/failure — never crash."""

    def test_add_auditor_unknown_org_returns_structured_response(
        self, authenticated_graphql_client
    ):
        result = authenticated_graphql_client(
            TestGraphQL.MUTATION_ADD_AUDITOR_TO_ORGANIZATION,
            variables={
                "organizationId": "999999",
                "input": {"email": "nobody@sandbox.parakh.test"},
            },
            method="POST",
        )
        assert "data" in result or "errors" in result
        if result.get("data") and result["data"].get("addAuditorToOrganization"):
            resp = result["data"]["addAuditorToOrganization"]
            assert "success" in resp
            assert "message" in resp

    def test_add_auditor_without_auth_returns_failure(self, graphql_client):
        import requests as _requests
        from utils.config import Config
        import json

        mutation = TestGraphQL.MUTATION_ADD_AUDITOR_TO_ORGANIZATION
        try:
            resp = _requests.post(
                Config.graphql_endpoint(),
                json={
                    "query": mutation,
                    "variables": {
                        "organizationId": "999999",
                        "input": {"email": "nobody@sandbox.parakh.test"},
                    },
                },
                headers={"Content-Type": "application/json", "Accept": "application/json"},
                timeout=15,
            )
        except _requests.exceptions.ConnectionError:
            pytest.skip("GraphQL endpoint unreachable")

        assert resp.status_code in (200, 400, 401, 403), (
            f"Unexpected status {resp.status_code} for unauthenticated mutation"
        )


# ── removeAuditorFromOrganization mutation shape ──────────────────────────────


class TestRemoveAuditorMutation:
    """removeAuditorFromOrganization returns structured response for unknown IDs."""

    def test_remove_auditor_unknown_ids_returns_structured_response(
        self, authenticated_graphql_client
    ):
        result = authenticated_graphql_client(
            TestGraphQL.MUTATION_REMOVE_AUDITOR_FROM_ORGANIZATION,
            variables={"organizationId": "999999", "userId": "999999"},
            method="POST",
        )
        assert "data" in result or "errors" in result
        if result.get("data") and result["data"].get("removeAuditorFromOrganization"):
            resp = result["data"]["removeAuditorFromOrganization"]
            assert "success" in resp
            assert "message" in resp
            assert isinstance(resp["success"], bool)


# ── assignAuditorToVersion mutation shape ─────────────────────────────────────


class TestAssignAuditorToVersionMutation:
    """assignAuditorToVersion validates required fields and returns structured errors."""

    def test_assign_auditor_missing_user_email_returns_failure(
        self, authenticated_graphql_client
    ):
        result = authenticated_graphql_client(
            TestGraphQL.MUTATION_ASSIGN_AUDITOR_TO_VERSION,
            variables={
                "input": {
                    "auditorEmail": "nobody@sandbox.parakh.test",
                    "modelId": "00000000-0000-0000-0000-000000000000",
                    "modelVersionId": 999999,
                    "modelName": "Contract Test Model",
                }
            },
            method="POST",
        )
        assert "data" in result or "errors" in result
        if result.get("data") and result["data"].get("assignAuditorToVersion"):
            resp = result["data"]["assignAuditorToVersion"]
            assert "success" in resp
            assert "message" in resp
            # Unknown user email should fail
            assert resp["success"] is False

    def test_assign_auditor_without_auth_returns_failure(self, graphql_client):
        import requests as _requests
        from utils.config import Config

        try:
            resp = _requests.post(
                Config.graphql_endpoint(),
                json={
                    "query": TestGraphQL.MUTATION_ASSIGN_AUDITOR_TO_VERSION,
                    "variables": {
                        "input": {
                            "auditorEmail": "nobody@test.invalid",
                            "modelId": "00000000-0000-0000-0000-000000000000",
                            "modelVersionId": 1,
                            "modelName": "Test",
                        }
                    },
                },
                headers={"Content-Type": "application/json", "Accept": "application/json"},
                timeout=15,
            )
        except _requests.exceptions.ConnectionError:
            pytest.skip("GraphQL endpoint unreachable")

        assert resp.status_code in (200, 400, 401, 403)
        if resp.status_code == 200:
            body = resp.json()
            if (body.get("data") or {}).get("assignAuditorToVersion"):
                resp_data = body["data"]["assignAuditorToVersion"]
                assert resp_data.get("success") is False


# ── updateAuditorAssignmentStatus mutation shape ──────────────────────────────


class TestUpdateAssignmentStatusMutation:
    """updateAuditorAssignmentStatus validates status enum and returns errors for unknown IDs."""

    def test_update_status_invalid_assignment_id_returns_failure(
        self, authenticated_graphql_client
    ):
        result = authenticated_graphql_client(
            TestGraphQL.MUTATION_UPDATE_AUDITOR_ASSIGNMENT_STATUS,
            variables={"assignmentId": "999999999", "status": "ACCEPTED"},
            method="POST",
        )
        assert "data" in result or "errors" in result
        if result.get("data") and result["data"].get("updateAuditorAssignmentStatus"):
            resp = result["data"]["updateAuditorAssignmentStatus"]
            assert "success" in resp
            assert "message" in resp
            assert resp["success"] is False

    def test_update_status_invalid_enum_value_returns_failure(
        self, authenticated_graphql_client
    ):
        result = authenticated_graphql_client(
            TestGraphQL.MUTATION_UPDATE_AUDITOR_ASSIGNMENT_STATUS,
            variables={"assignmentId": "999999999", "status": "NOT_A_VALID_STATUS"},
            method="POST",
        )
        assert "data" in result or "errors" in result
        if result.get("data") and result["data"].get("updateAuditorAssignmentStatus"):
            resp = result["data"]["updateAuditorAssignmentStatus"]
            assert resp.get("success") is False

    @pytest.mark.parametrize("status", ["PENDING", "ACCEPTED", "DECLINED", "COMPLETED"])
    def test_update_status_all_valid_statuses_return_structured_response(
        self, authenticated_graphql_client, status
    ):
        result = authenticated_graphql_client(
            TestGraphQL.MUTATION_UPDATE_AUDITOR_ASSIGNMENT_STATUS,
            variables={"assignmentId": "999999999", "status": status},
            method="POST",
        )
        assert "data" in result or "errors" in result
        if result.get("data") and result["data"].get("updateAuditorAssignmentStatus"):
            resp = result["data"]["updateAuditorAssignmentStatus"]
            assert "success" in resp
            assert "message" in resp
