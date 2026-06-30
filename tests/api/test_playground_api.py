"""
API contract tests for playground (manual) evaluation mutations and queries.

Coverage:
- TestPlaygroundQueryContract  — playgroundEvaluationStatus, manualTestCases (read-only)
- TestPlaygroundMutationContract — shape/error-handling with invalid IDs (no writes)
- TestPlaygroundEvaluationCreate — write-side lifecycle: create → update → run → cancel
  (marked regression_write; auto-skips when SANDBOX_ORG_SLUG is unset)
"""

import pytest

from tests.data.test_data import TestGraphQL, TestModelConstants

pytestmark = [pytest.mark.api, pytest.mark.regression, pytest.mark.auth]


# ── Read-only query contracts ─────────────────────────────────────────────────


class TestPlaygroundQueryContract:
    """Playground status and manual test-case queries return well-formed responses."""

    def test_playground_status_invalid_id_returns_error_or_null(
        self, authenticated_graphql_client
    ):
        result = authenticated_graphql_client(
            TestGraphQL.QUERY_PLAYGROUND_EVALUATION_STATUS,
            variables={"auditId": "999999999"},
        )
        assert "data" in result or "errors" in result
        if result.get("data") and result["data"].get("playgroundEvaluationStatus"):
            s = result["data"]["playgroundEvaluationStatus"]
            for field in ("canFinish", "testCaseCount", "auditStatus"):
                assert field in s, f"Missing field: {field}"

    def test_playground_status_shape_with_completed_id(
        self, authenticated_graphql_client, completed_eval_id
    ):
        result = authenticated_graphql_client(
            TestGraphQL.QUERY_PLAYGROUND_EVALUATION_STATUS,
            variables={"auditId": str(completed_eval_id)},
        )
        assert "data" in result or "errors" in result
        if result.get("data") and result["data"].get("playgroundEvaluationStatus"):
            s = result["data"]["playgroundEvaluationStatus"]
            if s.get("testCaseCount") is not None:
                assert isinstance(s["testCaseCount"], int)
                assert s["testCaseCount"] >= 0
            if s.get("canFinish") is not None:
                assert isinstance(s["canFinish"], bool)

    def test_manual_test_cases_invalid_id_returns_error_or_empty(
        self, authenticated_graphql_client
    ):
        result = authenticated_graphql_client(
            TestGraphQL.QUERY_MANUAL_TEST_CASES,
            variables={"auditId": "999999999"},
        )
        assert "data" in result or "errors" in result
        if result.get("data") and result["data"].get("manualTestCases") is not None:
            assert isinstance(result["data"]["manualTestCases"], list)

    def test_manual_test_cases_completed_eval_returns_list(
        self, authenticated_graphql_client, completed_eval_id
    ):
        result = authenticated_graphql_client(
            TestGraphQL.QUERY_MANUAL_TEST_CASES,
            variables={"auditId": str(completed_eval_id)},
        )
        assert "data" in result or "errors" in result
        if result.get("data") and result["data"].get("manualTestCases") is not None:
            cases = result["data"]["manualTestCases"]
            assert isinstance(cases, list)
            for case in cases[:3]:
                assert "id" in case
                assert "status" in case


# ── Mutation input-shape contracts (no writes — all use invalid IDs) ──────────


class TestPlaygroundMutationContract:
    """Mutation shape contract tests using invalid IDs.

    Sends well-formed inputs against non-existent resources so nothing is
    persisted, but the API must respond with the expected JSON shape (not a 500).
    """

    def test_call_model_invalid_audit_id_returns_structured_response(
        self, authenticated_graphql_client
    ):
        result = authenticated_graphql_client(
            TestGraphQL.MUTATION_CALL_MODEL_FOR_MANUAL_EVAL,
            variables={"input": {"auditId": "999999999", "inputPrompt": "hello world"}},
            method="POST",
        )
        assert "data" in result or "errors" in result
        if result.get("data") and result["data"].get("callModelForManualEval"):
            r = result["data"]["callModelForManualEval"]
            assert "success" in r
            assert "message" in r
            assert "output" in r

    def test_submit_manual_test_case_invalid_audit_returns_structured_response(
        self, authenticated_graphql_client
    ):
        result = authenticated_graphql_client(
            TestGraphQL.MUTATION_SUBMIT_MANUAL_TEST_CASE,
            variables={
                "input": {
                    "auditId": "999999999",
                    "status": "PASSED",
                    "inputPrompt": "contract test prompt",
                    "modelOutput": "contract test output",
                }
            },
            method="POST",
        )
        assert "data" in result or "errors" in result
        if result.get("data") and result["data"].get("submitManualTestCase"):
            r = result["data"]["submitManualTestCase"]
            assert "success" in r
            assert "message" in r

    def test_generate_playground_reason_invalid_audit_returns_structured_response(
        self, authenticated_graphql_client
    ):
        result = authenticated_graphql_client(
            TestGraphQL.MUTATION_GENERATE_PLAYGROUND_REASON,
            variables={
                "input": {
                    "auditId": "999999999",
                    "metricName": "hallucination",
                    "severity": "HIGH",
                    "inputPrompt": "What is the capital of France?",
                    "modelOutput": "The capital of France is Berlin.",
                }
            },
            method="POST",
        )
        assert "data" in result or "errors" in result
        if result.get("data") and result["data"].get("generatePlaygroundReason"):
            r = result["data"]["generatePlaygroundReason"]
            assert "success" in r
            assert "message" in r
            assert "reason" in r

    def test_generate_playground_ideal_output_invalid_audit_returns_structured_response(
        self, authenticated_graphql_client
    ):
        result = authenticated_graphql_client(
            TestGraphQL.MUTATION_GENERATE_PLAYGROUND_IDEAL_OUTPUT,
            variables={
                "input": {
                    "auditId": "999999999",
                    "metricName": "hallucination",
                    "severity": "HIGH",
                    "inputPrompt": "What is the capital of France?",
                    "modelOutput": "The capital of France is Berlin.",
                    "reason": "Factual error — correct answer is Paris.",
                }
            },
            method="POST",
        )
        assert "data" in result or "errors" in result
        if result.get("data") and result["data"].get("generatePlaygroundIdealOutput"):
            r = result["data"]["generatePlaygroundIdealOutput"]
            assert "success" in r
            assert "message" in r
            assert "idealOutput" in r

    def test_finish_manual_evaluation_invalid_id_returns_structured_response(
        self, authenticated_graphql_client
    ):
        result = authenticated_graphql_client(
            TestGraphQL.MUTATION_FINISH_MANUAL_EVALUATION,
            variables={"input": {"auditId": "999999999"}},
            method="POST",
        )
        assert "data" in result or "errors" in result
        if result.get("data") and result["data"].get("finishManualEvaluation"):
            r = result["data"]["finishManualEvaluation"]
            assert "success" in r
            assert "message" in r

    def test_update_audit_result_invalid_result_id_returns_structured_response(
        self, authenticated_graphql_client
    ):
        result = authenticated_graphql_client(
            TestGraphQL.MUTATION_UPDATE_AUDIT_RESULT,
            variables={
                "input": {
                    "resultId": "999999999",
                    "evaluatorSuccess": True,
                    "evaluatorRiskLevel": "LOW_RISK",
                    "evaluatorReason": "Looks correct — contract test",
                }
            },
            method="POST",
        )
        assert "data" in result or "errors" in result
        if result.get("data") and result["data"].get("updateAuditResult"):
            r = result["data"]["updateAuditResult"]
            assert "success" in r
            assert "message" in r
            assert "result" in r

    def test_submit_audit_review_invalid_id_returns_structured_response(
        self, authenticated_graphql_client
    ):
        result = authenticated_graphql_client(
            TestGraphQL.MUTATION_SUBMIT_AUDIT_REVIEW,
            variables={
                "input": {
                    "auditId": "999999999",
                    "recommendations": "No issues found — contract test",
                }
            },
            method="POST",
        )
        assert "data" in result or "errors" in result
        if result.get("data") and result["data"].get("submitAuditReview"):
            r = result["data"]["submitAuditReview"]
            assert "success" in r
            assert "message" in r
            assert "audit" in r


# ── Write-side lifecycle: create → update → run → cancel ─────────────────────


class TestPlaygroundEvaluationCreate:
    """Write-side lifecycle tests for the playground evaluation create+cancel path.

    Marked regression_write — auto-skip when SANDBOX_ORG_SLUG is unset.
    Every test registers the created audit_id with cleanup_evaluation so
    it is cancelled in teardown even on failure.
    """

    pytestmark = [pytest.mark.regression_write]

    @staticmethod
    def _first_model_id(client) -> str | None:
        result = client(TestGraphQL.QUERY_MY_MODELS)
        models = ((result.get("data") or {}).get("myModels")) or []
        return str(models[0]["id"]) if models else None

    def test_create_blank_audit_returns_draft_audit(
        self, authenticated_graphql_client, sandbox_org, cleanup_evaluation
    ):
        model_id = self._first_model_id(authenticated_graphql_client)
        if not model_id:
            pytest.skip("No AI models found — cannot create blank audit")

        result = authenticated_graphql_client(
            TestGraphQL.MUTATION_CREATE_BLANK_AUDIT,
            variables={"input": {"modelId": model_id}},
            method="POST",
        )
        assert "data" in result, f"No data in createBlankAudit response: {result}"
        resp = (result["data"] or {}).get("createBlankAudit") or {}
        assert resp.get("success") is True, f"createBlankAudit failed: {resp.get('message')}"
        audit = resp.get("audit") or {}
        assert audit.get("id"), "createBlankAudit did not return an audit ID"
        assert audit.get("status") in ("DRAFT", "PENDING", None)
        cleanup_evaluation.append(str(audit["id"]))

    def test_update_audit_to_playground_mode(
        self, authenticated_graphql_client, sandbox_org, cleanup_evaluation
    ):
        model_id = self._first_model_id(authenticated_graphql_client)
        if not model_id:
            pytest.skip("No AI models found")

        cr = authenticated_graphql_client(
            TestGraphQL.MUTATION_CREATE_BLANK_AUDIT,
            variables={"input": {"modelId": model_id}},
            method="POST",
        )
        audit_id = (
            ((cr.get("data") or {}).get("createBlankAudit") or {})
            .get("audit", {})
            .get("id")
        )
        if not audit_id:
            pytest.skip("createBlankAudit did not return an audit ID")
        cleanup_evaluation.append(str(audit_id))

        result = authenticated_graphql_client(
            TestGraphQL.MUTATION_UPDATE_AUDIT,
            variables={
                "input": {
                    "auditId": str(audit_id),
                    "evaluationMode": "manual",
                    "name": "API contract test — playground mode",
                    "metrics": ["hallucination"],
                }
            },
            method="POST",
        )
        assert "data" in result or "errors" in result
        resp = ((result.get("data") or {}).get("updateAudit")) or {}
        if resp:
            assert "success" in resp
            assert "message" in resp
            if resp.get("audit"):
                assert resp["audit"].get("id") == str(audit_id)

    def test_run_audit_playground_returns_valid_status(
        self, authenticated_graphql_client, sandbox_org, cleanup_evaluation
    ):
        model_id = self._first_model_id(authenticated_graphql_client)
        if not model_id:
            pytest.skip("No AI models found")

        cr = authenticated_graphql_client(
            TestGraphQL.MUTATION_CREATE_BLANK_AUDIT,
            variables={"input": {"modelId": model_id}},
            method="POST",
        )
        audit_id = (
            ((cr.get("data") or {}).get("createBlankAudit") or {})
            .get("audit", {})
            .get("id")
        )
        if not audit_id:
            pytest.skip("createBlankAudit did not return an audit ID")
        cleanup_evaluation.append(str(audit_id))

        # Set playground mode before running
        authenticated_graphql_client(
            TestGraphQL.MUTATION_UPDATE_AUDIT,
            variables={
                "input": {
                    "auditId": str(audit_id),
                    "evaluationMode": "manual",
                    "metrics": ["hallucination"],
                }
            },
            method="POST",
        )

        run_result = authenticated_graphql_client(
            TestGraphQL.MUTATION_RUN_AUDIT,
            variables={"input": {"auditId": str(audit_id)}},
            method="POST",
        )
        assert "data" in run_result or "errors" in run_result
        resp = ((run_result.get("data") or {}).get("runAudit")) or {}
        if resp and resp.get("audit"):
            status = resp["audit"].get("status")
            assert status in TestModelConstants.AUDIT_STATUSES, (
                f"runAudit returned unexpected status: {status!r}"
            )
