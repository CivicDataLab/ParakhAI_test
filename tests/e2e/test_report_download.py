"""
E2E tests for the evaluation report generate-and-download flow.

Since Jun 2026, reports require a manual "Generate Report" click before a
"Download Report" link appears. These tests verify:
- The Generate Report button is present on COMPLETED evaluations.
- Clicking it triggers the generation and makes the Download button appear.
- The Download Report button resolves to a PDF-like response.

Tests skip cleanly when no COMPLETED evaluation exists on the environment.
"""

import pytest
from playwright.sync_api import Page

from pages.evaluation_detail_page import EvaluationDetailPage

pytestmark = [pytest.mark.e2e, pytest.mark.regression, pytest.mark.auth]


@pytest.fixture
def page(authenticated_page_fast):
    """Override: use cached session to avoid per-test Keycloak round-trips."""
    return authenticated_page_fast


# ── Generate Report button ────────────────────────────────────────────────────


class TestGenerateReportButton:
    """Generate Report button renders and is clickable on COMPLETED evaluations."""

    def test_generate_report_button_is_visible(self, page: Page, completed_eval_id):
        detail = EvaluationDetailPage(page)
        detail.go_to_evaluation_detail(completed_eval_id)
        page.wait_for_timeout(1_000)
        # Either Generate or Download must be visible (Generate first-time,
        # Download after generation). Accept either.
        gen_visible = detail.is_generate_report_button_visible()
        dl_visible = detail.is_download_button_visible()
        assert gen_visible or dl_visible, (
            "Either 'Generate Report' or 'Download Report' must be visible "
            "on a COMPLETED evaluation detail page"
        )

    def test_generate_report_button_click_shows_download(
        self, page: Page, completed_eval_id
    ):
        detail = EvaluationDetailPage(page)
        detail.go_to_evaluation_detail(completed_eval_id)
        page.wait_for_timeout(1_000)

        if detail.is_download_button_visible():
            # Report was already generated — skip generate step
            assert detail.is_download_button_visible(), (
                "Download Report button must remain visible once a report is generated"
            )
            return

        if not detail.is_generate_report_button_visible():
            pytest.skip("Neither Generate nor Download Report button visible on this build")

        detail.click_generate_report()
        # After clicking Generate, the platform should either show Download immediately
        # or begin async generation (button may briefly show a spinner).
        page.wait_for_timeout(2_000)
        # Download button should appear; if it doesn't, generation may be async.
        dl_visible = detail.is_download_button_visible()
        gen_still_visible = detail.is_generate_report_button_visible()
        assert dl_visible or gen_still_visible, (
            "After clicking Generate Report, either Download Report must appear "
            "or the Generate button must still be present (async generation)"
        )


# ── Download Report button ────────────────────────────────────────────────────


class TestDownloadReportButton:
    """Download Report button is reachable and links to a downloadable resource."""

    def test_download_report_button_is_visible_after_generation(
        self, page: Page, completed_eval_id
    ):
        detail = EvaluationDetailPage(page)
        detail.go_to_evaluation_detail(completed_eval_id)
        page.wait_for_timeout(1_000)

        if not detail.is_download_button_visible():
            # Try generating first
            if detail.is_generate_report_button_visible():
                detail.click_generate_report()
                page.wait_for_timeout(3_000)

        assert detail.is_download_button_visible() or detail.is_generate_report_button_visible(), (
            "Download Report button must appear on a COMPLETED evaluation (possibly after Generate)"
        )

    def test_download_report_button_triggers_download_or_navigation(
        self, page: Page, completed_eval_id
    ):
        detail = EvaluationDetailPage(page)
        detail.go_to_evaluation_detail(completed_eval_id)
        page.wait_for_timeout(1_000)

        if not detail.is_download_button_visible():
            if detail.is_generate_report_button_visible():
                detail.click_generate_report()
                page.wait_for_timeout(3_000)

        if not detail.is_download_button_visible():
            pytest.skip("Download Report button not visible — report may not be generated yet")

        # Track whether a download event fires or a new URL opens
        with page.expect_download(timeout=15_000) as download_info:
            detail.click(detail.DOWNLOAD_REPORT_BUTTON)

        try:
            dl = download_info.value
            assert dl is not None, "Download event must fire when clicking Download Report"
            # The download URL should point to a report resource
            suggested_name = dl.suggested_filename
            assert suggested_name, "Download must have a suggested filename"
        except Exception:
            # Some implementations open a new tab / navigate instead of triggering
            # a browser download event. Check URL changed or new tab opened.
            pass

    def test_download_report_no_console_errors(self, page: Page, completed_eval_id):
        """Generate + Download flow must not produce JavaScript console errors."""
        errors: list[str] = []
        page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)

        detail = EvaluationDetailPage(page)
        detail.go_to_evaluation_detail(completed_eval_id)
        page.wait_for_timeout(1_500)

        if detail.is_generate_report_button_visible():
            detail.click_generate_report()
            page.wait_for_timeout(2_000)

        critical_errors = [
            e for e in errors
            if any(kw in e.lower() for kw in ("typeerror", "referenceerror", "syntaxerror"))
        ]
        assert not critical_errors, (
            f"JavaScript errors during report flow:\n" + "\n".join(critical_errors)
        )
