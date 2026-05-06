"""
Page object for the evaluation detail page.
URL: /dashboard/ai-maker/{org_id}/evaluations/{eval_id}
"""

from playwright.sync_api import Page

from locators.evaluation_detail_locators import EvaluationDetailLocators
from pages.base_page import BasePage
from utils.config import Config

CIVICDATALAB_ORG_ID = 1


class EvaluationDetailPage(BasePage):
    """Evaluation detail — overview, summary, risk cards, module tabs, sample issues."""

    BACK_TO_LIST = EvaluationDetailLocators.BACK_TO_LIST
    OVERVIEW_HEADING = EvaluationDetailLocators.OVERVIEW_HEADING
    SUMMARY_HEADING = EvaluationDetailLocators.SUMMARY_HEADING
    SUMMARY_PASS_RATE = EvaluationDetailLocators.SUMMARY_PASS_RATE
    RISK_HIGH = EvaluationDetailLocators.RISK_HIGH
    RISK_MEDIUM = EvaluationDetailLocators.RISK_MEDIUM
    RISK_LOW = EvaluationDetailLocators.RISK_LOW
    MODULE_TAB_HALLUCINATION = EvaluationDetailLocators.MODULE_TAB_HALLUCINATION
    MODULE_TAB_BIAS = EvaluationDetailLocators.MODULE_TAB_BIAS
    SAMPLE_ISSUES_HEADING = EvaluationDetailLocators.SAMPLE_ISSUES_HEADING
    ISSUE_EXPAND_TRIGGER = EvaluationDetailLocators.ISSUE_EXPAND_TRIGGER
    DOWNLOAD_REPORT_BUTTON = EvaluationDetailLocators.DOWNLOAD_REPORT_BUTTON
    TAB_OVERVIEW = EvaluationDetailLocators.TAB_OVERVIEW
    TAB_TEST_CASES = EvaluationDetailLocators.TAB_TEST_CASES
    TAB_RESULTS = EvaluationDetailLocators.TAB_RESULTS
    TEST_CASES_PANEL = EvaluationDetailLocators.TEST_CASES_PANEL
    RESULTS_PANEL = EvaluationDetailLocators.RESULTS_PANEL
    TEST_CASES_ROW = EvaluationDetailLocators.TEST_CASES_ROW
    RESULTS_ROW = EvaluationDetailLocators.RESULTS_ROW
    RESULTS_ROW_EXPAND_BUTTON = EvaluationDetailLocators.RESULTS_ROW_EXPAND_BUTTON

    def __init__(self, page: Page, org_id: int = CIVICDATALAB_ORG_ID) -> None:
        super().__init__(page)
        self.org_id = org_id

    # ── Navigation ─────────────────────────────────────────────────────────────

    def go_to_evaluation_detail(self, eval_id: int) -> "EvaluationDetailPage":
        url = Config.url(f"/dashboard/ai-maker/{self.org_id}/evaluations/{eval_id}")
        self.navigate(url)
        self.wait_for_load("domcontentloaded")
        return self

    # ── State checks ───────────────────────────────────────────────────────────

    def is_overview_section_visible(self) -> bool:
        return self.is_visible(self.OVERVIEW_HEADING)

    def is_summary_section_visible(self) -> bool:
        return self.is_visible(self.SUMMARY_HEADING)

    def is_pass_rate_visible(self) -> bool:
        return self.is_visible(self.SUMMARY_PASS_RATE)

    def is_risk_section_visible(self) -> bool:
        # Check "Total Issues Identified" heading (matches existing EvaluationsPage pattern)
        return self.is_visible("text=Total Issues Identified")

    def is_sample_issues_section_visible(self) -> bool:
        return self.is_visible(self.SAMPLE_ISSUES_HEADING)

    def is_download_button_visible(self) -> bool:
        return self.is_visible(self.DOWNLOAD_REPORT_BUTTON)

    def expand_first_issue(self) -> None:
        triggers = self.page.locator(self.ISSUE_EXPAND_TRIGGER)
        if triggers.count() > 0:
            triggers.first.click()

    # ── Tab switching ──────────────────────────────────────────────────────────

    def click_overview_tab(self) -> None:
        if self.is_visible(self.TAB_OVERVIEW, timeout=2_000):
            self.click(self.TAB_OVERVIEW)

    def click_test_cases_tab(self) -> None:
        self.click(self.TAB_TEST_CASES)

    def click_results_tab(self) -> None:
        self.click(self.TAB_RESULTS)

    def is_test_cases_panel_visible(self) -> bool:
        return self.is_visible(self.TEST_CASES_PANEL, timeout=5_000)

    def is_results_panel_visible(self) -> bool:
        return self.is_visible(self.RESULTS_PANEL, timeout=5_000)

    def get_test_cases_row_count(self) -> int:
        return self.page.locator(self.TEST_CASES_ROW).count()

    def get_results_row_count(self) -> int:
        return self.page.locator(self.RESULTS_ROW).count()

    def expand_first_results_row(self) -> bool:
        """Click the first expand-trigger inside the results panel.

        Returns True if a trigger was clicked, False if none was visible.
        """
        triggers = self.page.locator(self.RESULTS_ROW_EXPAND_BUTTON)
        if triggers.count() == 0:
            return False
        triggers.first.click()
        return True

    # ── Actions ────────────────────────────────────────────────────────────────

    def click_module_tab(self, tab_selector: str) -> None:
        self.click(tab_selector)

    def click_back_to_list(self) -> None:
        self.click(self.BACK_TO_LIST)
        self.wait_for_load("domcontentloaded")
