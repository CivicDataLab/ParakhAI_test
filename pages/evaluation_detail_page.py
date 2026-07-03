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
    GENERATE_REPORT_BUTTON = EvaluationDetailLocators.GENERATE_REPORT_BUTTON
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
        self.wait_for_detail_hydrated()
        return self

    def wait_for_detail_hydrated(self, timeout_s: int = 90) -> bool:
        """Wait for the detail page to hydrate (dev takes ~20s, worse under load).

        Polls for the 'Evaluation Overview' heading — a positive condition.
        (Polling for the absence of 'Loading evaluation…' is unreliable: there
        is a brief pre-hydration window where neither the curtain text nor the
        content is in the DOM yet.) Non-fatal on timeout so callers can still
        make their own assertions.
        """
        for _ in range(timeout_s // 2):
            if self.page.locator(self.OVERVIEW_HEADING).count() > 0:
                return True
            self.page.wait_for_timeout(2_000)
        return False

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

    def is_generate_report_button_visible(self) -> bool:
        return self.is_visible(self.GENERATE_REPORT_BUTTON, timeout=5_000)

    def click_generate_report(self) -> None:
        self.click(self.GENERATE_REPORT_BUTTON)
        self.wait_for_load("networkidle")

    def is_download_button_visible(self) -> bool:
        return self.is_visible(self.DOWNLOAD_REPORT_BUTTON)

    def expand_first_issue(self) -> None:
        triggers = self.page.locator(self.ISSUE_EXPAND_TRIGGER)
        if triggers.count() > 0:
            triggers.first.click()

    # ── Redesigned single-page layout (Jul 2026) ──────────────────────────────

    NAME_INPUT = EvaluationDetailLocators.NAME_INPUT
    RECOMMENDATIONS_HEADING = EvaluationDetailLocators.RECOMMENDATIONS_HEADING
    RESULTS_HEADING = EvaluationDetailLocators.RESULTS_HEADING
    RESULTS_SORT_SELECT = EvaluationDetailLocators.RESULTS_SORT_SELECT
    RESULT_INPUT_BLOCK = EvaluationDetailLocators.RESULT_INPUT_BLOCK

    def has_tabs(self) -> bool:
        """True when any [role='tab'] renders — the redesign has none."""
        return self.page.locator("[role='tab']").count() > 0

    def is_name_input_visible(self) -> bool:
        return self.is_visible(self.NAME_INPUT, timeout=5_000)

    def get_eval_name(self) -> str:
        return self.page.locator(self.NAME_INPUT).first.input_value()

    def is_results_section_visible(self) -> bool:
        return self.is_visible(self.RESULTS_HEADING, timeout=5_000)

    def is_recommendations_visible(self) -> bool:
        return self.is_visible(self.RECOMMENDATIONS_HEADING, timeout=3_000)

    def get_overview_field(self, label: str) -> str:
        """Parse an Overview line of the form 'Label : value' (exact key match)."""
        body = self.page.locator("body").inner_text()
        for line in body.splitlines():
            key, sep, value = line.partition(":")
            if sep and key.strip().lower() == label.lower():
                return value.strip()
        return ""

    def get_summary_stat(self, label: str) -> str:
        """Return the value rendered directly below a summary-card label.

        The summary/risk cards render as 'LABEL\\n<value>' in innerText,
        e.g. 'TOTAL PASS RATE\\n100.00%' or 'HIGH RISK\\n0'.
        """
        import re

        body = self.page.locator("body").inner_text()
        m = re.search(
            re.escape(label) + r"\s*:?\s*\n\s*([\d.,]+\s*%?|\d+)", body, re.IGNORECASE
        )
        return m.group(1).strip() if m else ""

    def get_results_sort_options(self) -> list[str]:
        sel = self.page.locator(self.RESULTS_SORT_SELECT).first
        if not sel.count():
            return []
        if sel.evaluate("el => el.tagName") != "SELECT":
            return []
        return sel.locator("option").all_inner_texts()

    def select_results_sort(self, label: str) -> bool:
        """Select a sort option by visible label. Returns False when no select."""
        sel = self.page.locator(self.RESULTS_SORT_SELECT).first
        if not sel.count() or sel.evaluate("el => el.tagName") != "SELECT":
            return False
        sel.select_option(label=label)
        self.page.wait_for_timeout(1_000)
        return True

    def get_result_input_block_count(self) -> int:
        return self.page.locator(self.RESULT_INPUT_BLOCK).count()

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
        # The page renders mobile + desktop variants of both the <a> and the
        # <button> form — strict-mode click on `BasePage.click()` fails with
        # "resolved to 2 elements". Matches the .first pattern used in
        # `pages/evaluations_page.py:click_back_to_list`.
        self.page.locator(self.BACK_TO_LIST).first.click()
        self.wait_for_load("domcontentloaded")
