"""
GraphQL API contract tests.

These tests hit the live GraphQL endpoint via GET requests (the platform's
Strawberry setup blocks POST via CSRF protection; GET with Accept:application/json
is the supported unauthenticated path).

Covers:
- Endpoint health and basic introspection
- Unauthenticated public queries (hello, healthCheck)
- Auth-required queries return errors or empty data (not server crashes)
"""

import pytest

from tests.data.test_data import TestGraphQL

pytestmark = [pytest.mark.api]


class TestGraphQLEndpointHealth:
    """Endpoint is reachable and returns well-formed JSON responses."""

    def test_endpoint_returns_200(self, graphql_client):
        result = graphql_client(TestGraphQL.QUERY_HELLO)
        assert result is not None

    def test_hello_query_returns_expected_string(self, graphql_client):
        result = graphql_client(TestGraphQL.QUERY_HELLO)
        data = result.get("data", {})
        assert "hello" in data
        assert isinstance(data["hello"], str)
        assert len(data["hello"]) > 0

    def test_health_check_returns_ok(self, graphql_client):
        result = graphql_client(TestGraphQL.QUERY_HEALTH)
        data = result.get("data", {})
        assert "healthCheck" in data
        assert data["healthCheck"] == "OK"

    def test_valid_query_response_is_valid_graphql_shape(self, graphql_client):
        result = graphql_client(TestGraphQL.QUERY_HELLO)
        # A valid GraphQL response must have 'data' or 'errors' (or both)
        assert "data" in result or "errors" in result


class TestPublicAIModelsQuery:
    """aiModels query shape — requires org header so we verify error shape only."""

    def test_ai_models_query_returns_valid_graphql_response(self, graphql_client):
        result = graphql_client(TestGraphQL.QUERY_AI_MODELS)
        assert "data" in result or "errors" in result

    def test_ai_models_without_org_header_returns_error(self, graphql_client):
        # aiModels requires an organization header — unauthenticated access should error
        result = graphql_client(TestGraphQL.QUERY_AI_MODELS)
        errors = result.get("errors")
        data_null = result.get("data") is None or result["data"].get("aiModels") is None
        assert errors or data_null, (
            "Expected error or null data for aiModels without org header"
        )

    def test_ai_models_error_message_is_descriptive(self, graphql_client):
        result = graphql_client(TestGraphQL.QUERY_AI_MODELS)
        errors = result.get("errors", [])
        if errors:
            assert isinstance(errors[0].get("message"), str)
            assert len(errors[0]["message"]) > 0

    def test_response_contains_no_unexpected_top_level_keys(self, graphql_client):
        result = graphql_client(TestGraphQL.QUERY_HELLO)
        allowed_keys = {"data", "errors", "extensions"}
        unexpected = set(result.keys()) - allowed_keys
        assert not unexpected, f"Unexpected top-level keys in response: {unexpected}"


class TestPublicQueryStructure:
    """Introspection — verify the schema exposes the expected query fields."""

    def test_hello_field_exists_in_schema(self, graphql_client):
        result = graphql_client(
            "{ __schema { queryType { fields { name } } } }"
        )
        fields = (
            result.get("data", {})
            .get("__schema", {})
            .get("queryType", {})
            .get("fields", [])
        )
        names = [f["name"] for f in fields]
        assert "hello" in names

    def test_health_check_field_exists_in_schema(self, graphql_client):
        result = graphql_client(
            "{ __schema { queryType { fields { name } } } }"
        )
        fields = (
            result.get("data", {})
            .get("__schema", {})
            .get("queryType", {})
            .get("fields", [])
        )
        names = [f["name"] for f in fields]
        assert "healthCheck" in names

    def test_ai_models_field_exists_in_schema(self, graphql_client):
        result = graphql_client(
            "{ __schema { queryType { fields { name } } } }"
        )
        fields = (
            result.get("data", {})
            .get("__schema", {})
            .get("queryType", {})
            .get("fields", [])
        )
        names = [f["name"] for f in fields]
        assert "aiModels" in names


class TestAuthRequiredBehavior:
    """Auth-required queries and mutations fail gracefully without a token."""

    def test_my_models_without_auth_returns_error_or_empty(self, graphql_client):
        result = graphql_client(TestGraphQL.QUERY_MY_MODELS)
        has_errors = bool(result.get("errors"))
        my_models = (result.get("data") or {}).get("myModels")
        empty_list = my_models == [] if my_models is not None else False
        assert has_errors or empty_list or my_models is None, (
            f"myModels without auth returned unexpected data: {my_models}"
        )

    def test_my_audits_without_auth_returns_error_or_empty(self, graphql_client):
        result = graphql_client(TestGraphQL.QUERY_MY_AUDITS)
        has_errors = bool(result.get("errors"))
        my_audits = (result.get("data") or {}).get("myAudits")
        empty_list = my_audits == [] if my_audits is not None else False
        assert has_errors or empty_list or my_audits is None, (
            f"myAudits without auth returned unexpected data: {my_audits}"
        )

    def test_audits_without_auth_returns_error_or_empty(self, graphql_client):
        result = graphql_client(TestGraphQL.QUERY_AUDITS)
        has_errors = bool(result.get("errors"))
        audits = (result.get("data") or {}).get("audits")
        empty_list = audits == [] if audits is not None else False
        assert has_errors or empty_list or audits is None, (
            f"audits without auth returned unexpected data: {audits}"
        )

    def test_request_audit_mutation_rejected_without_auth(self, graphql_client):
        # Mutations via GET are rejected by the server (GraphQL spec: mutations require POST).
        # The platform's CSRF protection blocks unauthenticated POST, so the correct
        # observable behaviour is: the request is not fulfilled (400 or auth error).
        import requests as _requests

        from utils.config import Config

        resp = _requests.get(
            Config.graphql_endpoint(),
            params={"query": TestGraphQL.MUTATION_REQUEST_AUDIT},
            headers={"Accept": "application/json"},
            timeout=20,
        )
        # Server must refuse: either 400 (mutations not allowed on GET) or an error body
        assert resp.status_code != 200 or "errors" in resp.json(), (
            "Server must refuse an unauthenticated mutation request"
        )
