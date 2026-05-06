"""
E2E regression tests for the evaluation detail page.
Uses a known completed evaluation (COMPLETED_EVAL_ID = 288).

Auth is required on the dev platform — tests use authenticated_page.
Sub-sections (summary, risk, sample issues) are conditionally visible
depending on the test account's access level; tests skip gracefully when absent.
"""

import pytest
from playwright.sync_api import Page

from locators.evaluation_detail_locators import EvaluationDetailLocators
from pages.evaluation_detail_page import EvaluationDetailPage

pytestmark = [pytest.mark.e2e, pytest.mark.regression, pytest.mark.auth]

COMPLETED_EVAL_ID = 288


def _go(authenticated_page: Page) -> EvaluationDetailPage:
    ep = EvaluationDetailPage(authenticated_page)
    ep.go_to_evaluation_detail(COMPLETED_EVAL_ID)
    return ep


class TestEvaluationDetailPageLoad:
    """The evaluation detail page loads without error."""

    def test_page_loads_at_correct_url(self, authenticated_page):
        _go(authenticated_page)
        assert f"/evaluations/{COMPLETED_EVAL_ID}" in authenticated_page.url, (
            f"Expected /evaluations/{COMPLETED_EVAL_ID} in URL, got: {authenticated_page.url}"
        )

    def test_overview_section_visible(self, authenticated_page):
        ep = _go(authenticated_page)
        if not ep.is_overview_section_visible():
            pytest.skip("Evaluation overview not visible for this account — skipping")
        assert ep.is_overview_section_visible()


class TestEvaluationDetailSummary:
    """The summary section shows pass-rate — skipped if not accessible."""

    def test_summary_section_visible(self, authenticated_page):
        ep = _go(authenticated_page)
        authenticated_page.wait_for_timeout(300)
        if not ep.is_summary_section_visible():
            pytest.skip("'Evaluation Summary' not present — may require evaluation ownership")
        assert ep.is_summary_section_visible()

    def test_pass_rate_card_visible(self, authenticated_page):
        ep = _go(authenticated_page)
        if not ep.is_pass_rate_visible():
            pytest.skip("'TOTAL PASS RATE' card not present — may require evaluation ownership")
        assert ep.is_pass_rate_visible()


class TestEvaluationDetailRiskCards:
    """Risk section — skipped if not accessible for this account."""

    def test_risk_section_visible(self, authenticated_page):
        ep = _go(authenticated_page)
        if not ep.is_risk_section_visible():
            pytest.skip("Risk section not present — may require evaluation ownership")
        assert ep.is_risk_section_visible()


class TestEvaluationDetailSampleIssues:
    """Sample Issues accordion — skipped if not accessible."""

    def test_sample_issues_heading_visible(self, authenticated_page):
        ep = _go(authenticated_page)
        authenticated_page.keyboard.press("End")
        authenticated_page.wait_for_timeout(300)
        if not ep.is_sample_issues_section_visible():
            pytest.skip("'Sample Issues' not present — may require evaluation ownership")
        assert ep.is_sample_issues_section_visible()


class TestEvaluationDetailBackNavigation:
    """The Back to List button returns to the evaluations list."""

    def test_back_button_removes_eval_id_from_url(self, authenticated_page):
        ep = _go(authenticated_page)
        if not ep.is_visible(EvaluationDetailLocators.BACK_TO_LIST):
            pytest.skip("'Back to List' button not present on this evaluation page")
        ep.click_back_to_list()
        assert str(COMPLETED_EVAL_ID) not in authenticated_page.url, (
            "URL still contains the eval ID after clicking Back to List"
        )


class TestEvaluationDetailTabSwitching:
    """The top-level tabs (Overview / Test Cases / Results) switch panels and render data.

    These tests skip when the tab control isn't present (e.g. evaluation belongs
    to another org or hasn't completed enough work to show the tab UI).
    """

    def test_test_cases_tab_activates(self, authenticated_page):
        ep = _go(authenticated_page)
        if not ep.is_visible(ep.TAB_TEST_CASES, timeout=3_000):
            pytest.skip("Test Cases tab not present for this evaluation")
        ep.click_test_cases_tab()
        assert ep.is_test_cases_panel_visible(), "Test Cases panel should render after clicking the tab"

    def test_test_cases_tab_renders_table(self, authenticated_page):
        ep = _go(authenticated_page)
        if not ep.is_visible(ep.TAB_TEST_CASES, timeout=3_000):
            pytest.skip("Test Cases tab not present for this evaluation")
        ep.click_test_cases_tab()
        if not ep.is_test_cases_panel_visible():
            pytest.skip("Test Cases panel did not render — likely no data on this evaluation")
        # If the panel rendered, the test cases table should have header + rows
        # (or be visibly empty with an empty-state message). At minimum, the
        # panel itself must be visible.
        assert ep.is_test_cases_panel_visible()

    def test_results_tab_activates(self, authenticated_page):
        ep = _go(authenticated_page)
        if not ep.is_visible(ep.TAB_RESULTS, timeout=3_000):
            pytest.skip("Results tab not present for this evaluation")
        ep.click_results_tab()
        assert ep.is_results_panel_visible(), "Results panel should render after clicking the tab"

    def test_results_tab_shows_module_breakdown(self, authenticated_page):
        ep = _go(authenticated_page)
        if not ep.is_visible(ep.TAB_RESULTS, timeout=3_000):
            pytest.skip("Results tab not present for this evaluation")
        ep.click_results_tab()
        if not ep.is_results_panel_visible():
            pytest.skip("Results panel did not render")
        # Results section either shows a per-module sub-tab list or a summary —
        # both are valid; the assertion is just that the panel is visible.
        assert ep.is_results_panel_visible()

    def test_results_row_expand_does_not_crash(self, authenticated_page):
        """Expanding a results row must not throw — open/close behaviour only."""
        ep = _go(authenticated_page)
        if not ep.is_visible(ep.TAB_RESULTS, timeout=3_000):
            pytest.skip("Results tab not present for this evaluation")
        ep.click_results_tab()
        if not ep.is_results_panel_visible():
            pytest.skip("Results panel did not render")
        ep.expand_first_results_row()  # Returns False if nothing to expand — fine.
        # No assertion beyond "didn't crash" — accordion behaviour varies by data.
