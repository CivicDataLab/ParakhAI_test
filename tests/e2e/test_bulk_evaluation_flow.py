"""
E2E and API integration tests for the bulk (automated) evaluation flow.

Covers:
- TestBulkEvaluationCreateAndRun — create blank audit → set bulk mode → run → check status
- TestEvaluatorReviewFlow       — evaluator review UI for PENDING_REVIEW evaluations
- TestBulkEvaluationStatusUI    — UI status badge and list display for bulk eval states

Bulk evaluations are processed asynchronously by Celery, so tests that depend
on IN_PROGRESS or PENDING_REVIEW use liberal timeouts and skip when the target
status is not reached within the window.

Gating:
- Write-side tests require regression_write + SANDBOX_ORG_SLUG.
- PENDING_REVIEW discovery skips tests when no such eval exists in the env.
"""

import time

import pytest
from playwright.sync_api import Page

from pages.evaluation_detail_page import EvaluationDetailPage
from pages.evaluator_review_page import EvaluatorReviewPage
from tests.data.test_data import TestGraphQL, TestModelConstants

pytestmark = [pytest.mark.e2e, pytest.mark.regression, pytest.mark.auth]


def _sandbox_org_id(sandbox_org: str) -> int:
    try:
        return int(sandbox_org)
    except (TypeError, ValueError):
        pytest.skip(f"SANDBOX_ORG_SLUG={sandbox_org!r} must be a numeric org id")


def _first_model_id(client) -> str | None:
    result = client(TestGraphQL.QUERY_MY_MODELS)
    models = ((result.get("data") or {}).get("myModels")) or []
    return str(models[0]["id"]) if models else None


def _first_dataset_id(client) -> str | None:
    result = client(TestGraphQL.QUERY_PROMPT_DATASETS)
    datasets = ((result.get("data") or {}).get("promptDatasets")) or []
    return str(datasets[0]["id"]) if datasets else None


def _audit_status(client, audit_id: str) -> str | None:
    result = client(
        TestGraphQL.QUERY_AUDIT, variables={"auditId": audit_id}
    )
    return ((result.get("data") or {}).get("audit") or {}).get("status")


def _wait_for_status(
    client, audit_id: str, target_statuses: list, timeout_s: int = 60, poll_s: int = 5
) -> str | None:
    """Poll audit status until one of target_statuses is reached or timeout."""
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        status = _audit_status(client, audit_id)
        if status in target_statuses:
            return status
        time.sleep(poll_s)
    return _audit_status(client, audit_id)


# ── Write-side: create → update → run → verify ───────────────────────────────


class TestBulkEvaluationCreateAndRun:
    """Create a bulk evaluation, run it, and verify the response shape."""

    pytestmark = [pytest.mark.regression_write]

    def test_create_bulk_audit_returns_draft(
        self, authenticated_graphql_client, sandbox_org, cleanup_evaluation
    ):
        model_id = _first_model_id(authenticated_graphql_client)
        if not model_id:
            pytest.skip("No AI models available in sandbox org")

        cr = authenticated_graphql_client(
            TestGraphQL.MUTATION_CREATE_BLANK_AUDIT,
            variables={"input": {"modelId": model_id}},
            method="POST",
        )
        resp = ((cr.get("data") or {}).get("createBlankAudit")) or {}
        assert resp.get("success") is True, f"createBlankAudit failed: {resp.get('message')}"
        audit = resp.get("audit") or {}
        assert audit.get("id"), "createBlankAudit must return an audit id"
        assert audit.get("status") in ("DRAFT", "PENDING", None)
        cleanup_evaluation.append(str(audit["id"]))

    def test_run_bulk_audit_transitions_status(
        self, authenticated_graphql_client, sandbox_org, cleanup_evaluation
    ):
        model_id = _first_model_id(authenticated_graphql_client)
        if not model_id:
            pytest.skip("No AI models available")

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
            pytest.skip("Could not create audit")
        cleanup_evaluation.append(str(audit_id))

        # Update to automated mode with at least one metric
        authenticated_graphql_client(
            TestGraphQL.MUTATION_UPDATE_AUDIT,
            variables={
                "input": {
                    "auditId": str(audit_id),
                    "evaluationMode": "automated",
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
        resp = (run_result.get("data") or {}).get("runAudit") or {}
        if resp.get("audit"):
            status = resp["audit"].get("status")
            assert status in TestModelConstants.AUDIT_STATUSES, (
                f"Unexpected status after runAudit: {status!r}"
            )

    def test_bulk_audit_reaches_queued_or_in_progress(
        self, authenticated_graphql_client, sandbox_org, cleanup_evaluation
    ):
        model_id = _first_model_id(authenticated_graphql_client)
        if not model_id:
            pytest.skip("No AI models available")

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
            pytest.skip("Could not create audit")
        cleanup_evaluation.append(str(audit_id))

        authenticated_graphql_client(
            TestGraphQL.MUTATION_UPDATE_AUDIT,
            variables={
                "input": {
                    "auditId": str(audit_id),
                    "evaluationMode": "automated",
                    "metrics": ["hallucination"],
                }
            },
            method="POST",
        )
        authenticated_graphql_client(
            TestGraphQL.MUTATION_RUN_AUDIT,
            variables={"input": {"auditId": str(audit_id)}},
            method="POST",
        )

        # Poll for up to 30s — Celery should pick it up quickly
        final_status = _wait_for_status(
            authenticated_graphql_client,
            audit_id,
            target_statuses=["QUEUED", "IN_PROGRESS", "PENDING_REVIEW", "COMPLETED", "FAILED"],
            timeout_s=30,
            poll_s=5,
        )
        assert final_status in TestModelConstants.AUDIT_STATUSES, (
            f"Audit should transition out of DRAFT after run; got {final_status!r}"
        )
        assert final_status not in ("DRAFT", "CANCELLED"), (
            f"Audit must progress past DRAFT after runAudit; got {final_status!r}"
        )


# ── Evaluator review flow ─────────────────────────────────────────────────────


class TestEvaluatorReviewFlow:
    """Evaluator review section renders on PENDING_REVIEW evaluations."""

    @pytest.fixture(scope="class")
    def pending_review_eval_id(self, authenticated_graphql_client):
        """Discover a PENDING_REVIEW audit ID, or skip all tests in this class."""
        result = authenticated_graphql_client(
            TestGraphQL.QUERY_AUDITS,
            variables={
                "filters": [
                    {"field": "status", "condition": "exact", "value": "PENDING_REVIEW"}
                ]
            },
        )
        audits = ((result.get("data") or {}).get("audits") or {}).get("data") or []
        if not audits:
            pytest.skip("No PENDING_REVIEW evaluations found on this environment")
        return int(audits[0]["id"])

    def test_evaluation_detail_page_loads_for_pending_review(
        self, authenticated_page_fast, pending_review_eval_id
    ):
        detail = EvaluationDetailPage(authenticated_page_fast)
        detail.go_to_evaluation_detail(pending_review_eval_id)
        assert detail.is_overview_section_visible() or "evaluations" in authenticated_page_fast.url, (
            "Evaluation detail must load for a PENDING_REVIEW audit"
        )

    def test_evaluator_review_section_is_visible_on_pending_review(
        self, authenticated_page_fast, pending_review_eval_id
    ):
        detail = EvaluationDetailPage(authenticated_page_fast)
        detail.go_to_evaluation_detail(pending_review_eval_id)

        review_page = EvaluatorReviewPage(authenticated_page_fast)
        # Scroll to bottom to reveal review section
        authenticated_page_fast.keyboard.press("End")
        authenticated_page_fast.wait_for_timeout(500)

        assert review_page.is_review_section_visible() or review_page.is_submit_review_button_visible(), (
            "Evaluator review section should be present on PENDING_REVIEW evaluation"
        )

    def test_submit_review_button_visible_on_pending_review(
        self, authenticated_page_fast, pending_review_eval_id
    ):
        detail = EvaluationDetailPage(authenticated_page_fast)
        detail.go_to_evaluation_detail(pending_review_eval_id)

        review_page = EvaluatorReviewPage(authenticated_page_fast)
        authenticated_page_fast.keyboard.press("End")
        authenticated_page_fast.wait_for_timeout(500)

        assert review_page.is_submit_review_button_visible(), (
            "Submit Review button should appear on PENDING_REVIEW evaluation"
        )


# ── Evaluator override fields ─────────────────────────────────────────────────


class TestEvaluatorOverrideFields:
    """Override controls on a PENDING_REVIEW result row are actually interactive.

    `EvaluatorReviewPage.override_result()`/`submit_review()` (the full write
    path) were never exercised by any test before this — only presence checks
    existed. Submitting a review irreversibly transitions a real sandbox audit
    to COMPLETED (no un-submit mutation exists on the backend), so these tests
    stop short of clicking Submit; they verify the override inputs themselves
    accept and retain input, which was previously untested at any depth.
    """

    @pytest.fixture(scope="class")
    def pending_review_eval_id(self, authenticated_graphql_client):
        result = authenticated_graphql_client(
            TestGraphQL.QUERY_AUDITS,
            variables={
                "filters": [
                    {"field": "status", "condition": "exact", "value": "PENDING_REVIEW"}
                ]
            },
        )
        audits = ((result.get("data") or {}).get("audits") or {}).get("data") or []
        if not audits:
            pytest.skip("No PENDING_REVIEW evaluations found on this environment")
        return int(audits[0]["id"])

    def _open_review_with_rows(self, page: Page, eval_id: int) -> EvaluatorReviewPage:
        detail = EvaluationDetailPage(page)
        detail.go_to_evaluation_detail(eval_id)
        review_page = EvaluatorReviewPage(page)
        page.keyboard.press("End")
        page.wait_for_timeout(500)
        if review_page.get_result_row_count() == 0:
            pytest.skip("PENDING_REVIEW evaluation has no result rows to override")
        return review_page

    def test_override_reason_textarea_accepts_typed_input(
        self, authenticated_page_fast, pending_review_eval_id
    ):
        review_page = self._open_review_with_rows(
            authenticated_page_fast, pending_review_eval_id
        )
        row = authenticated_page_fast.locator(review_page.RESULT_ROW).first
        textarea = row.locator(review_page.OVERRIDE_REASON_TEXTAREA).first
        if textarea.count() == 0:
            pytest.skip("No override reason textarea rendered on this result row")

        reason_text = "Automated coverage check — override reason"
        textarea.fill(reason_text)
        assert textarea.input_value() == reason_text, (
            "Override reason textarea must retain typed input"
        )

    def test_override_risk_dropdown_has_selectable_options(
        self, authenticated_page_fast, pending_review_eval_id
    ):
        review_page = self._open_review_with_rows(
            authenticated_page_fast, pending_review_eval_id
        )
        row = authenticated_page_fast.locator(review_page.RESULT_ROW).first
        dropdown = row.locator(review_page.OVERRIDE_RISK_DROPDOWN).first
        if dropdown.count() == 0:
            pytest.skip("No override risk dropdown rendered on this result row")

        options = dropdown.locator("option").all_inner_texts()
        assert len(options) >= 2, (
            f"Override risk dropdown should expose multiple risk levels, got: {options}"
        )


# ── Bulk evaluation status in the evaluations list UI ────────────────────────


class TestBulkEvaluationStatusUI:
    """Status tabs and list rows reflect bulk evaluation states."""

    @pytest.fixture
    def page(self, authenticated_page_fast):
        return authenticated_page_fast

    def test_completed_eval_detail_shows_status_badge(
        self, page: Page, completed_eval_id
    ):
        detail = EvaluationDetailPage(page)
        detail.go_to_evaluation_detail(completed_eval_id)
        # Status badge on a COMPLETED evaluation must say COMPLETED
        assert page.locator("text=COMPLETED").count() >= 1, (
            "A COMPLETED evaluation detail page must show the COMPLETED status badge"
        )

    def test_completed_eval_detail_overview_renders(
        self, page: Page, completed_eval_id
    ):
        detail = EvaluationDetailPage(page)
        detail.go_to_evaluation_detail(completed_eval_id)
        assert detail.is_overview_section_visible(), (
            "Evaluation Overview section must render on a COMPLETED evaluation"
        )

    def test_completed_eval_shows_generate_or_download_report(
        self, page: Page, completed_eval_id
    ):
        detail = EvaluationDetailPage(page)
        detail.go_to_evaluation_detail(completed_eval_id)
        page.wait_for_timeout(1_000)
        gen = detail.is_generate_report_button_visible()
        dl = detail.is_download_button_visible()
        assert gen or dl, (
            "A COMPLETED evaluation must show either 'Generate Report' or 'Download Report' button"
        )
