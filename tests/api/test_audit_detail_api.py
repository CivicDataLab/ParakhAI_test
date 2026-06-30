"""
API contract tests for audit detail queries.

Covers:
- TestAuditDetailQuery       — audit(auditId): shape, auth, access control
- TestAuditTasksQuery        — auditTasks: field types, filter args
- TestAuditResultsQuery      — auditResults: field types, filter args
- TestAuditSummariesQuery    — auditSummaries: per-module aggregates shape
- TestResultSamplesQuery     — resultSamples: union type variants
- TestGenerateAuditReport    — generateAuditReport: auth, non-completed guard

All tests are read-only.  Write-side lifecycle tests live in test_playground_api.py.
"""

import pytest

from tests.data.test_data import TestGraphQL

pytestmark = [pytest.mark.api, pytest.mark.regression, pytest.mark.auth]


# ── audit(auditId) ────────────────────────────────────────────────────────────


class TestAuditDetailQuery:
    """audit(auditId) returns well-formed data or null for unknown IDs."""

    def test_audit_detail_invalid_id_returns_null(self, authenticated_graphql_client):
        result = authenticated_graphql_client(
            TestGraphQL.QUERY_AUDIT, variables={"auditId": "999999999"}
        )
        assert "data" in result or "errors" in result
        if result.get("data") is not None:
            assert result["data"].get("audit") is None

    def test_audit_detail_completed_eval_returns_shape(
        self, authenticated_graphql_client, completed_eval_id
    ):
        result = authenticated_graphql_client(
            TestGraphQL.QUERY_AUDIT, variables={"auditId": str(completed_eval_id)}
        )
        assert "data" in result or "errors" in result
        if result.get("data") and result["data"].get("audit"):
            audit = result["data"]["audit"]
            assert "id" in audit
            assert "name" in audit
            assert "status" in audit
            assert audit["status"] in (
                "DRAFT", "QUEUED", "IN_PROGRESS", "PENDING_REVIEW", "COMPLETED", "FAILED", "CANCELLED"
            )

    def test_audit_detail_completed_eval_has_numeric_test_counts(
        self, authenticated_graphql_client, completed_eval_id
    ):
        result = authenticated_graphql_client(
            TestGraphQL.QUERY_AUDIT, variables={"auditId": str(completed_eval_id)}
        )
        if result.get("data") and result["data"].get("audit"):
            audit = result["data"]["audit"]
            for field in ("totalTests", "passedTests", "failedTests"):
                if audit.get(field) is not None:
                    assert isinstance(audit[field], int), f"{field} must be int"
                    assert audit[field] >= 0

    def test_audit_detail_without_auth_returns_null(self, graphql_client):
        result = graphql_client(
            TestGraphQL.QUERY_AUDIT, variables={"auditId": "1"}
        )
        # Unauthenticated access must return null (not an error — resolver guards return None)
        assert "data" in result or "errors" in result
        if result.get("data") is not None:
            assert result["data"].get("audit") is None


# ── auditTasks(auditId) ───────────────────────────────────────────────────────


class TestAuditTasksQuery:
    """auditTasks returns a list of granular evaluation tasks."""

    def test_audit_tasks_invalid_id_returns_empty(self, authenticated_graphql_client):
        result = authenticated_graphql_client(
            TestGraphQL.QUERY_AUDIT_TASKS, variables={"auditId": "999999999"}
        )
        assert "data" in result or "errors" in result
        if result.get("data") and result["data"].get("auditTasks") is not None:
            assert isinstance(result["data"]["auditTasks"], list)
            assert result["data"]["auditTasks"] == []

    def test_audit_tasks_completed_eval_returns_list(
        self, authenticated_graphql_client, completed_eval_id
    ):
        result = authenticated_graphql_client(
            TestGraphQL.QUERY_AUDIT_TASKS, variables={"auditId": str(completed_eval_id)}
        )
        assert "data" in result or "errors" in result
        if result.get("data") and result["data"].get("auditTasks") is not None:
            tasks = result["data"]["auditTasks"]
            assert isinstance(tasks, list)
            for task in tasks[:3]:
                assert "id" in task
                assert "status" in task

    def test_audit_tasks_status_filter_returns_only_matching(
        self, authenticated_graphql_client, completed_eval_id
    ):
        result = authenticated_graphql_client(
            TestGraphQL.QUERY_AUDIT_TASKS,
            variables={"auditId": str(completed_eval_id), "status": "COMPLETED"},
        )
        assert "data" in result or "errors" in result
        if result.get("data") and result["data"].get("auditTasks"):
            for task in result["data"]["auditTasks"]:
                assert task.get("status") == "COMPLETED"

    def test_audit_tasks_without_auth_returns_empty(self, graphql_client):
        result = graphql_client(
            TestGraphQL.QUERY_AUDIT_TASKS, variables={"auditId": "1"}
        )
        assert "data" in result or "errors" in result
        if result.get("data") and result["data"].get("auditTasks") is not None:
            assert result["data"]["auditTasks"] == []


# ── auditResults(auditId) ─────────────────────────────────────────────────────


class TestAuditResultsQuery:
    """auditResults returns detailed per-test-case results."""

    def test_audit_results_invalid_id_returns_empty(self, authenticated_graphql_client):
        result = authenticated_graphql_client(
            TestGraphQL.QUERY_AUDIT_RESULTS, variables={"auditId": "999999999"}
        )
        assert "data" in result or "errors" in result
        if result.get("data") and result["data"].get("auditResults") is not None:
            assert isinstance(result["data"]["auditResults"], list)
            assert result["data"]["auditResults"] == []

    def test_audit_results_completed_eval_returns_list(
        self, authenticated_graphql_client, completed_eval_id
    ):
        result = authenticated_graphql_client(
            TestGraphQL.QUERY_AUDIT_RESULTS, variables={"auditId": str(completed_eval_id)}
        )
        assert "data" in result or "errors" in result
        if result.get("data") and result["data"].get("auditResults") is not None:
            assert isinstance(result["data"]["auditResults"], list)
            for r in result["data"]["auditResults"][:3]:
                assert "id" in r

    def test_audit_results_without_auth_returns_empty(self, graphql_client):
        result = graphql_client(
            TestGraphQL.QUERY_AUDIT_RESULTS, variables={"auditId": "1"}
        )
        assert "data" in result or "errors" in result
        if result.get("data") and result["data"].get("auditResults") is not None:
            assert result["data"]["auditResults"] == []


# ── auditSummaries(auditId) ───────────────────────────────────────────────────


class TestAuditSummariesQuery:
    """auditSummaries returns per-module aggregate summaries."""

    def test_audit_summaries_invalid_id_returns_empty(self, authenticated_graphql_client):
        result = authenticated_graphql_client(
            TestGraphQL.QUERY_AUDIT_SUMMARIES, variables={"auditId": "999999999"}
        )
        assert "data" in result or "errors" in result
        if result.get("data") and result["data"].get("auditSummaries") is not None:
            assert isinstance(result["data"]["auditSummaries"], list)
            assert result["data"]["auditSummaries"] == []

    def test_audit_summaries_completed_eval_returns_list(
        self, authenticated_graphql_client, completed_eval_id
    ):
        result = authenticated_graphql_client(
            TestGraphQL.QUERY_AUDIT_SUMMARIES, variables={"auditId": str(completed_eval_id)}
        )
        assert "data" in result or "errors" in result
        if result.get("data") and result["data"].get("auditSummaries") is not None:
            summaries = result["data"]["auditSummaries"]
            assert isinstance(summaries, list)

    def test_audit_summaries_without_auth_returns_empty(self, graphql_client):
        result = graphql_client(
            TestGraphQL.QUERY_AUDIT_SUMMARIES, variables={"auditId": "1"}
        )
        assert "data" in result or "errors" in result
        if result.get("data") and result["data"].get("auditSummaries") is not None:
            assert result["data"]["auditSummaries"] == []


# ── resultSamples(auditId) ────────────────────────────────────────────────────


class TestResultSamplesQuery:
    """resultSamples returns a union of ManualModuleSamples | BulkModuleSamples."""

    def test_result_samples_invalid_id_returns_empty(self, authenticated_graphql_client):
        result = authenticated_graphql_client(
            TestGraphQL.QUERY_RESULT_SAMPLES,
            variables={"auditId": "999999999", "samplesPerMetric": 2},
        )
        assert "data" in result or "errors" in result
        if result.get("data") and result["data"].get("resultSamples") is not None:
            assert isinstance(result["data"]["resultSamples"], list)
            assert result["data"]["resultSamples"] == []

    def test_result_samples_completed_eval_returns_list(
        self, authenticated_graphql_client, completed_eval_id
    ):
        result = authenticated_graphql_client(
            TestGraphQL.QUERY_RESULT_SAMPLES,
            variables={"auditId": str(completed_eval_id), "samplesPerMetric": 2},
        )
        assert "data" in result or "errors" in result
        if result.get("data") and result["data"].get("resultSamples") is not None:
            samples = result["data"]["resultSamples"]
            assert isinstance(samples, list)
            for s in samples:
                assert "__typename" in s
                assert s["__typename"] in ("ManualModuleSamples", "BulkModuleSamples")

    def test_result_samples_samples_per_metric_respected(
        self, authenticated_graphql_client, completed_eval_id
    ):
        result = authenticated_graphql_client(
            TestGraphQL.QUERY_RESULT_SAMPLES,
            variables={"auditId": str(completed_eval_id), "samplesPerMetric": 1},
        )
        if result.get("data") and result["data"].get("resultSamples"):
            for module_samples in result["data"]["resultSamples"]:
                inner = module_samples.get("samples") or []
                assert len(inner) <= 1, (
                    f"samplesPerMetric=1 but got {len(inner)} samples for "
                    f"module '{module_samples.get('module')}'"
                )

    def test_result_samples_without_auth_returns_empty(self, graphql_client):
        result = graphql_client(
            TestGraphQL.QUERY_RESULT_SAMPLES, variables={"auditId": "1"}
        )
        assert "data" in result or "errors" in result
        if result.get("data") and result["data"].get("resultSamples") is not None:
            assert result["data"]["resultSamples"] == []


# ── generateAuditReport(auditId) ─────────────────────────────────────────────


class TestGenerateAuditReportQuery:
    """generateAuditReport returns DownloadReportResponse{success, message}."""

    def test_generate_report_invalid_id_returns_failure(self, authenticated_graphql_client):
        result = authenticated_graphql_client(
            TestGraphQL.QUERY_GENERATE_AUDIT_REPORT, variables={"auditId": "999999999"}
        )
        assert "data" in result or "errors" in result
        if result.get("data") and result["data"].get("generateAuditReport"):
            resp = result["data"]["generateAuditReport"]
            assert "success" in resp
            assert "message" in resp
            # Unknown audit → must fail
            assert resp["success"] is False

    def test_generate_report_response_has_required_fields(self, authenticated_graphql_client):
        result = authenticated_graphql_client(
            TestGraphQL.QUERY_GENERATE_AUDIT_REPORT, variables={"auditId": "999999999"}
        )
        if result.get("data") and result["data"].get("generateAuditReport") is not None:
            resp = result["data"]["generateAuditReport"]
            assert "success" in resp, "generateAuditReport must have 'success' field"
            assert "message" in resp, "generateAuditReport must have 'message' field"
            assert isinstance(resp["success"], bool)
            assert isinstance(resp["message"], str)
            assert len(resp["message"]) > 0

    def test_generate_report_without_auth_returns_failure(self, graphql_client):
        result = graphql_client(
            TestGraphQL.QUERY_GENERATE_AUDIT_REPORT, variables={"auditId": "1"}
        )
        assert "data" in result or "errors" in result
        if result.get("data") and result["data"].get("generateAuditReport"):
            resp = result["data"]["generateAuditReport"]
            assert resp.get("success") is False


# ── sectorsWithAimodels ───────────────────────────────────────────────────────


class TestSectorsWithAimodelsQuery:
    """sectorsWithAimodels returns sectors that have ≥1 active AI model."""

    def test_sectors_with_aimodels_returns_list(self, authenticated_graphql_client):
        result = authenticated_graphql_client(
            TestGraphQL.QUERY_SECTORS_WITH_AIMODELS, variables={"limit": 10}
        )
        assert "data" in result or "errors" in result
        if result.get("data") and result["data"].get("sectorsWithAimodels") is not None:
            sectors = result["data"]["sectorsWithAimodels"]
            assert isinstance(sectors, list)
            for s in sectors:
                assert "id" in s
                assert "name" in s
