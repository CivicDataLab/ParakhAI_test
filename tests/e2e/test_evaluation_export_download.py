"""
E2E tests for the evaluation data export (ZIP) entry in the Download menu.

ParakhAI-frontend#488 replaced the detail page's standalone "Generate Report" /
"Download Report" buttons with one "Download" button that opens a menu with two
items: "Report (PDF)" (or "Generate report (PDF)" before one exists) and
"Evaluation data (ZIP)". The ZIP item calls the backend export endpoint added in
ParakhAI-Backend#147 (GET /api/audits/<id>/export/download/, already covered
unauthenticated in ParakhAI_test#36).

UNVERIFIED — not executed, no credentials in this environment. These tests need
TEST_EMAIL_1 / TEST_PASSWORD_1 (the `authenticated_page_fast` / `completed_eval_id`
fixtures), which this environment does not have. A human should run:

    pytest tests/e2e/test_evaluation_export_download.py -q -rfExXs

against dev, and confirm both pass. To prove it can fail (red), point
DOWNLOAD_MENU_ITEM_EXPORT at non-existent text (e.g. append "XXX") and rerun —
it must fail at the `is_download_menu_item_export_visible()` assertion, not with
a collection/fixture error.

Tests skip cleanly when no COMPLETED evaluation exists on the environment
(same `completed_eval_id` fixture as tests/e2e/test_report_download.py).
"""

import re

import pytest
from playwright.sync_api import Page

from pages.evaluation_detail_page import EvaluationDetailPage

pytestmark = [pytest.mark.e2e, pytest.mark.regression, pytest.mark.auth]


@pytest.fixture
def page(authenticated_page_fast):
    """Override: use cached session to avoid per-test Keycloak round-trips."""
    return authenticated_page_fast


class TestDownloadMenu:
    """The Download button opens a menu with the report and export items."""

    def test_download_menu_has_report_and_export_items(
        self, page: Page, completed_eval_id
    ):
        detail = EvaluationDetailPage(page)
        detail.go_to_evaluation_detail(completed_eval_id)
        page.wait_for_timeout(1_000)

        if not detail.is_download_menu_trigger_visible():
            pytest.skip(
                "Download menu trigger not visible — evaluation may not be in a "
                "state that shows download actions (e.g. still pending review)"
            )

        detail.open_download_menu()
        assert detail.is_download_menu_item_report_visible(), (
            "Download menu must list a report item ('Report (PDF)' or "
            "'Generate report (PDF)')"
        )
        assert detail.is_download_menu_item_export_visible(), (
            "Download menu must list 'Evaluation data (ZIP)'"
        )

    def test_download_export_item_requests_export_endpoint(
        self, page: Page, completed_eval_id
    ):
        """Clicking 'Evaluation data (ZIP)' must call the export endpoint for
        *this* evaluation — not just render a menu item that does nothing.

        This is the assertion that would actually have caught a regression:
        a menu item with the right label but a missing/broken onAction handler
        would pass a visibility check but never fire this request.
        """
        detail = EvaluationDetailPage(page)
        detail.go_to_evaluation_detail(completed_eval_id)
        page.wait_for_timeout(1_000)

        if not detail.is_download_menu_trigger_visible():
            pytest.skip(
                "Download menu trigger not visible — evaluation may not be in a "
                "state that shows download actions"
            )

        detail.open_download_menu()
        if not detail.is_download_menu_item_export_visible():
            pytest.skip("'Evaluation data (ZIP)' item not visible on this build")

        export_url_re = re.compile(
            rf"/api/audits/{completed_eval_id}/export/download/?(\?.*)?$"
        )
        with page.expect_request(export_url_re, timeout=15_000) as req_info:
            detail.click_download_menu_item_export()

        request = req_info.value
        assert request.method == "GET", (
            f"Export download must be a GET, got {request.method}"
        )
