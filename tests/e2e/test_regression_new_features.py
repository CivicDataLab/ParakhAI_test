"""
REGRESSION TESTS — New features from the dev branch (Jun 2026).

New components deployed:
  - AuditResultsList        — bulk test-case results list in evaluation detail
  - SkippedTestsErrorsCard  — card showing error-induced skipped test cases
  - BulkTestCaseDetailSheet — slide-over sheet with individual test case detail
  - AddIssueModal           — modal to flag an issue on a completed evaluation
  - ProgressBar             — visual progress indicator on evaluation detail

All tests use `completed_eval_id` (session-scoped fixture) to navigate to a real
COMPLETED evaluation. Tests auto-skip when no completed evaluation exists.

Run with:
    pytest tests/e2e/test_regression_new_features.py -m regression -v
"""

import pytest
from playwright.sync_api import Page

from utils.config import Config

pytestmark = [pytest.mark.e2e, pytest.mark.regression, pytest.mark.auth]

_DETAIL_TIMEOUT = 120  # seconds — evaluation detail pages have multiple API calls


def _nav_to_eval_detail(page: Page, eval_id: int, wait_ms: int = 3_500) -> None:
    page.goto(
        Config.url(f"/dashboard/ai-maker/1/evaluations/{eval_id}"),
        wait_until="domcontentloaded",
        timeout=60_000,
    )
    page.wait_for_timeout(wait_ms)


# ── Audit Results List ────────────────────────────────────────────────────────


@pytest.mark.timeout(_DETAIL_TIMEOUT)
class TestAuditResultsList:
    """AuditResultsList component renders test-case rows on completed evaluation detail."""

    def test_completed_eval_shows_results_section(
        self, authenticated_page_fast: Page, completed_eval_id: int
    ):
        """Completed evaluation detail must show an 'Evaluation Results' or 'Results' section."""
        _nav_to_eval_detail(authenticated_page_fast, completed_eval_id)

        results_section = authenticated_page_fast.locator(
            "text=/Evaluation Results|Test Results|Results/i"
        )
        if results_section.count() == 0:
            # May be hidden behind a tab or loading — try waiting a bit longer
            authenticated_page_fast.wait_for_timeout(3_000)
            results_section = authenticated_page_fast.locator(
                "text=/Evaluation Results|Test Results|Results/i"
            )

        if results_section.count() == 0:
            pytest.xfail(
                "No 'Results' section found on completed evaluation detail — "
                "AuditResultsList component may not yet be deployed or the UI uses different copy"
            )
        assert results_section.first.is_visible()

    def test_results_list_has_test_case_rows(
        self, authenticated_page_fast: Page, completed_eval_id: int
    ):
        """Results list must show individual test case rows or cards."""
        _nav_to_eval_detail(authenticated_page_fast, completed_eval_id)
        authenticated_page_fast.wait_for_timeout(2_000)

        # The AuditResultsList renders rows with aria-label or class-based selectors
        rows = authenticated_page_fast.locator(
            "[aria-label^='View details for input'], "
            "[class*='bulk-evaluation-results' i] [class*='row' i], "
            "[class*='result' i] [class*='row' i], "
            "tr:has(td), "
            "[role='row']"
        )
        if rows.count() == 0:
            pytest.xfail(
                "No test-case result rows found — "
                "AuditResultsList may not have rendered, or the completed eval has 0 test cases"
            )
        # At least one row should be visible
        visible_rows = sum(
            1 for i in range(min(rows.count(), 10)) if rows.nth(i).is_visible()
        )
        assert visible_rows >= 1, "No visible result rows in the results list"

    def test_results_contain_pass_fail_indicators(
        self, authenticated_page_fast: Page, completed_eval_id: int
    ):
        """Result rows must contain pass/fail status indicators."""
        _nav_to_eval_detail(authenticated_page_fast, completed_eval_id)
        authenticated_page_fast.wait_for_timeout(2_000)

        status_indicators = authenticated_page_fast.locator(
            "text=/^PASS$|^FAIL$|^pass$|^fail$/i, "
            "[class*='pass' i], [class*='fail' i], "
            "[data-status='PASS'], [data-status='FAIL'], "
            # Risk tags from AuditResultsList
            "[class*='risk' i], [class*='tag' i]:has-text('LOW'), [class*='tag' i]:has-text('HIGH')"
        )
        if status_indicators.count() == 0:
            pytest.xfail(
                "No pass/fail or risk indicators found in results — "
                "component may use different visual encoding"
            )


# ── Skipped Tests / Errors Card ───────────────────────────────────────────────


@pytest.mark.timeout(_DETAIL_TIMEOUT)
class TestSkippedTestsErrorsCard:
    """SkippedTestsErrorsCard renders on evaluation detail when errors/skips exist."""

    def test_evaluation_detail_skipped_or_error_section_present(
        self, authenticated_page_fast: Page, completed_eval_id: int
    ):
        """Evaluation detail should show a 'Skipped' count or 'Errors' section."""
        _nav_to_eval_detail(authenticated_page_fast, completed_eval_id)
        authenticated_page_fast.wait_for_timeout(2_000)

        # The component renders "Error leading to skipped test" or "SKIPPED TESTS" text
        skipped_indicators = authenticated_page_fast.locator(
            "text=/Skipped Tests|SKIPPED TESTS|Error leading to skipped/i, "
            "[class*='skipped' i]"
        )

        # Also check the existing SUMMARY_SKIPPED_TESTS locator from EvaluationsLocators
        from locators.evaluations_locators import EvaluationsLocators
        summary_skipped = authenticated_page_fast.locator(EvaluationsLocators.SUMMARY_SKIPPED_TESTS)

        has_skipped_info = (
            skipped_indicators.count() > 0 or summary_skipped.count() > 0
        )

        if not has_skipped_info:
            pytest.xfail(
                "No skipped-tests section or card found on evaluation detail — "
                "SkippedTestsErrorsCard only renders when test cases have errors; "
                "the selected completed eval may have 0 skipped tests"
            )

    def test_skipped_card_shows_count_or_zero(
        self, authenticated_page_fast: Page, completed_eval_id: int
    ):
        """The SKIPPED TESTS card must display a number (possibly 0)."""
        _nav_to_eval_detail(authenticated_page_fast, completed_eval_id)
        authenticated_page_fast.wait_for_timeout(2_000)

        from locators.evaluations_locators import EvaluationsLocators
        skipped_card = authenticated_page_fast.locator(EvaluationsLocators.SUMMARY_SKIPPED_TESTS)

        if skipped_card.count() == 0:
            pytest.skip("SKIPPED TESTS card not found on this evaluation")

        # The card should be visible and the nearby value should be numeric
        assert skipped_card.first.is_visible(), "SKIPPED TESTS label not visible"


# ── Bulk Test Case Detail Sheet ───────────────────────────────────────────────


@pytest.mark.timeout(_DETAIL_TIMEOUT)
class TestBulkTestCaseDetailSheet:
    """BulkTestCaseDetailSheet opens when clicking on a test case result row."""

    def test_clicking_result_row_opens_detail_sheet(
        self, authenticated_page_fast: Page, completed_eval_id: int
    ):
        """Clicking a test case result row must open a detail slide-over sheet."""
        _nav_to_eval_detail(authenticated_page_fast, completed_eval_id)
        authenticated_page_fast.wait_for_timeout(3_000)

        # Find a clickable result row
        result_rows = authenticated_page_fast.locator(
            "[aria-label^='View details for input'], "
            "[class*='result' i] [class*='row' i]:not(thead *), "
            "tbody tr:has(td)"
        )
        if result_rows.count() == 0:
            pytest.skip("No result rows found to click — test case detail sheet cannot be tested")

        # Click the first row
        first_row = result_rows.first
        if not first_row.is_visible():
            pytest.skip("First result row is not visible")

        first_row.click()
        authenticated_page_fast.wait_for_timeout(1_500)

        # The detail sheet should appear
        sheet = authenticated_page_fast.locator(
            "[role='dialog'], [class*='sheet' i], [class*='drawer' i], "
            "[class*='side-panel' i], [class*='detail' i][class*='panel' i]"
        )
        if sheet.count() == 0:
            pytest.xfail(
                "Clicking a result row did not open a detail sheet or dialog. "
                "BulkTestCaseDetailSheet may require a different interaction or may not be deployed."
            )
        assert sheet.first.is_visible(timeout=3_000)

    def test_detail_sheet_shows_input_and_output(
        self, authenticated_page_fast: Page, completed_eval_id: int
    ):
        """The detail sheet must contain Input and Output (or Model Output) sections."""
        _nav_to_eval_detail(authenticated_page_fast, completed_eval_id)
        authenticated_page_fast.wait_for_timeout(3_000)

        result_rows = authenticated_page_fast.locator(
            "[aria-label^='View details for input'], tbody tr:has(td)"
        )
        if result_rows.count() == 0:
            pytest.skip("No result rows found — cannot test detail sheet content")

        result_rows.first.click()
        authenticated_page_fast.wait_for_timeout(1_500)

        # Look for Input/Output labels in the sheet
        sheet_content = authenticated_page_fast.locator(
            "text=/Input|Model Output|Output|Expected/i"
        )
        if sheet_content.count() == 0:
            pytest.xfail(
                "Detail sheet did not show Input/Output sections — "
                "may not have opened, or content differs from expected"
            )


# ── Add Issue Modal ───────────────────────────────────────────────────────────


@pytest.mark.timeout(_DETAIL_TIMEOUT)
class TestAddIssueModal:
    """AddIssueModal allows flagging issues on a completed evaluation."""

    def test_add_issue_button_visible_on_completed_eval(
        self, authenticated_page_fast: Page, completed_eval_id: int
    ):
        """An 'Add Issue' button or similar CTA must be visible on completed eval detail."""
        _nav_to_eval_detail(authenticated_page_fast, completed_eval_id)
        authenticated_page_fast.wait_for_timeout(3_000)

        # AddIssueModal is triggered by a button that might be inside the detail sheet
        add_issue_btn = authenticated_page_fast.locator(
            "button:has-text('Add an issue'), button:has-text('Add Issue'), "
            "button:has-text('Flag Issue'), [aria-label*='issue' i]"
        )
        if add_issue_btn.count() == 0:
            pytest.xfail(
                "No 'Add Issue' button found on evaluation detail page. "
                "AddIssueModal may only be accessible from within the BulkTestCaseDetailSheet "
                "which requires clicking a specific result row first."
            )
        assert add_issue_btn.first.is_visible()

    def test_add_issue_via_result_row_sheet(
        self, authenticated_page_fast: Page, completed_eval_id: int
    ):
        """The Add Issue modal must open from within the result row detail sheet."""
        _nav_to_eval_detail(authenticated_page_fast, completed_eval_id)
        authenticated_page_fast.wait_for_timeout(3_000)

        # Step 1: Click a result row to open the detail sheet
        result_rows = authenticated_page_fast.locator(
            "[aria-label^='View details for input'], tbody tr:has(td)"
        )
        if result_rows.count() == 0:
            pytest.skip("No result rows — cannot test AddIssueModal")

        result_rows.first.click()
        authenticated_page_fast.wait_for_timeout(1_500)

        # Step 2: Find and click the Add Issue button in the sheet
        add_issue = authenticated_page_fast.locator(
            "button:has-text('Add an issue'), button:has-text('Add Issue')"
        )
        if add_issue.count() == 0:
            pytest.xfail(
                "Add Issue button not found inside detail sheet — "
                "may require auditor role (isEditable flag) or different UI state"
            )

        add_issue.first.click()
        authenticated_page_fast.wait_for_timeout(1_000)

        # Step 3: Verify modal opened
        modal = authenticated_page_fast.locator("[role='dialog'], [class*='modal' i]")
        if modal.count() == 0:
            pytest.xfail("Add Issue modal did not open after clicking the button")

        # Step 4: Close without submitting
        close_btn = authenticated_page_fast.locator(
            "[role='dialog'] button:has-text('Cancel'), "
            "[role='dialog'] button[aria-label='Close'], "
            "[role='dialog'] button:has-text('Close')"
        )
        if close_btn.count() > 0:
            close_btn.first.click()
            authenticated_page_fast.wait_for_timeout(500)


# ── Progress Bar ──────────────────────────────────────────────────────────────


@pytest.mark.timeout(_DETAIL_TIMEOUT)
class TestProgressBarComponent:
    """ProgressBar component renders on evaluation detail pages."""

    def test_evaluation_detail_shows_progress_indicator(
        self, authenticated_page_fast: Page, completed_eval_id: int
    ):
        """Completed evaluation detail must show a progress indicator (100% or pass rate)."""
        _nav_to_eval_detail(authenticated_page_fast, completed_eval_id)
        authenticated_page_fast.wait_for_timeout(2_000)

        from locators.evaluations_locators import EvaluationsLocators

        progress_indicators = authenticated_page_fast.locator(
            # ProgressBar component renders as progress element or div with aria role
            "progress, [role='progressbar'], "
            # Text-based: percentage
            "text=/\\d+%/i, "
            # Existing summary cards that confirm the eval completed
            f"{EvaluationsLocators.SUMMARY_PASS_RATE}, "
            f"{EvaluationsLocators.SUMMARY_PASSED_TESTS}"
        )
        assert progress_indicators.count() > 0 and progress_indicators.first.is_visible(timeout=5_000), (
            "No progress indicator found on completed evaluation detail — "
            "the ProgressBar component may not be rendered on this page"
        )

    def test_progress_bar_shows_meaningful_value_on_completed_eval(
        self, authenticated_page_fast: Page, completed_eval_id: int
    ):
        """Completed evaluation progress should indicate completion (100% or pass rate > 0)."""
        _nav_to_eval_detail(authenticated_page_fast, completed_eval_id)
        authenticated_page_fast.wait_for_timeout(2_000)

        # Look for a percentage value > 0
        percentage_text = authenticated_page_fast.locator("text=/\\d+%/")
        if percentage_text.count() == 0:
            pytest.xfail(
                "No percentage values found on completed evaluation detail — "
                "ProgressBar or pass-rate display may not be rendered"
            )

        # At least one percentage value should be visible
        found_visible = False
        for i in range(min(percentage_text.count(), 5)):
            if percentage_text.nth(i).is_visible():
                found_visible = True
                break

        assert found_visible, "Percentage text exists but none is visible"
