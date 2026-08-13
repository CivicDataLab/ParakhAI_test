"""
Page object for the Evaluations list, New Evaluation wizard, and Evaluation detail.
List URL  : /dashboard/ai-maker/{org_id}/evaluations
Wizard URL: /dashboard/ai-maker/{org_id}/evaluations/new
Detail URL: /dashboard/ai-maker/{org_id}/evaluations/{eval_id}
"""

from playwright.sync_api import Page

from locators.evaluations_locators import EvaluationsLocators
from pages.base_page import BasePage
from utils.config import Config

CIVICDATALAB_ORG_ID = 1
# A known-COMPLETED eval used by several tests to assert Summary/Risk/Modules
# sections. This drifts over time as old evals are cancelled or new ones run.
# Last verified: 2026-05-18 — ID 500 (Anthropic Claude 3.5 Haiku, COMPLETED).
SAMPLE_COMPLETED_EVAL_ID = 500


class EvaluationsPage(BasePage):
    """Evaluations list, wizard, and detail interactions."""

    # Expose locators
    PAGE_HEADING = EvaluationsLocators.PAGE_HEADING
    NEW_EVALUATION_BUTTON = EvaluationsLocators.NEW_EVALUATION_BUTTON
    STATUS_DRAFT = EvaluationsLocators.STATUS_DRAFT
    STATUS_COMPLETED = EvaluationsLocators.STATUS_COMPLETED
    MODAL_TITLE = EvaluationsLocators.MODAL_TITLE
    MODAL_START_BUTTON = EvaluationsLocators.MODAL_START_BUTTON
    MODAL_CANCEL_BUTTON = EvaluationsLocators.MODAL_CANCEL_BUTTON
    WIZARD_TAB_CONFIGURATION = EvaluationsLocators.WIZARD_TAB_CONFIGURATION
    WIZARD_TAB_TEST_CASES = EvaluationsLocators.WIZARD_TAB_TEST_CASES
    WIZARD_CANCEL_EVALUATION = EvaluationsLocators.WIZARD_CANCEL_EVALUATION
    EVAL_TYPE_TECHNICAL = EvaluationsLocators.EVAL_TYPE_TECHNICAL
    EVAL_TYPE_DOMAIN = EvaluationsLocators.EVAL_TYPE_DOMAIN
    EVAL_TYPE_CULTURAL = EvaluationsLocators.EVAL_TYPE_CULTURAL
    EVAL_OBJECTIVE_TEXTAREA = EvaluationsLocators.EVAL_OBJECTIVE_TEXTAREA
    EVAL_OBJECTIVE_ERROR = EvaluationsLocators.EVAL_OBJECTIVE_ERROR
    DOWNLOAD_REPORT_BUTTON = EvaluationsLocators.DOWNLOAD_REPORT_BUTTON

    def __init__(self, page: Page, org_id: int = CIVICDATALAB_ORG_ID) -> None:
        super().__init__(page)
        self.org_id = org_id
        self.list_url = Config.url(f"/dashboard/ai-maker/{org_id}/evaluations")

    # ── Navigation ─────────────────────────────────────────────────────────────

    def go_to_evaluations_list(self) -> "EvaluationsPage":
        self.navigate(self.list_url)
        self.wait_for_app_ready()
        return self

    def go_to_evaluation_detail(self, eval_id: int = SAMPLE_COMPLETED_EVAL_ID) -> "EvaluationsPage":
        self.navigate(Config.url(f"/dashboard/ai-maker/{self.org_id}/evaluations/{eval_id}"))
        self.wait_for_app_ready()
        return self

    # ── Evaluations list ───────────────────────────────────────────────────────

    def is_evaluations_list_visible(self) -> bool:
        return self.is_visible(self.PAGE_HEADING)

    def click_status_tab(self, status: str) -> None:
        """Filter the evaluations table to a single status.

        The old StatusFilterTabs bar was replaced by a per-column filter
        popover on the DataTable in the evaluation-table-listing redesign
        (~2026-08) — confirmed live 2026-08-13. Opens the 'Filter Status'
        popover, checks the matching option, and clicks Apply. 'All' clears
        any active filter instead (there's no 'All' checkbox anymore).
        """
        self.page.locator(EvaluationsLocators.FILTER_STATUS_BUTTON).click()
        self.page.locator(EvaluationsLocators.FILTER_DIALOG).first.wait_for(
            state="visible", timeout=5_000
        )
        if status == "All":
            clear_btn = self.page.locator(EvaluationsLocators.FILTER_CLEAR_BUTTON).first
            if clear_btn.is_visible() and clear_btn.get_attribute("aria-disabled") != "true":
                clear_btn.click()
            else:
                self.page.keyboard.press("Escape")
            self.page.wait_for_timeout(500)
            return
        self.page.locator(
            f"{EvaluationsLocators.FILTER_DIALOG} label:has-text('{status}')"
        ).first.click()
        self.page.locator(EvaluationsLocators.FILTER_APPLY_BUTTON).click()
        self.page.wait_for_timeout(800)

    def get_status_filter_options(self) -> list[str]:
        """Open the 'Filter Status' popover and return the available status labels."""
        self.page.locator(EvaluationsLocators.FILTER_STATUS_BUTTON).click()
        self.page.locator(EvaluationsLocators.FILTER_DIALOG).first.wait_for(
            state="visible", timeout=5_000
        )
        labels = self.page.locator(f"{EvaluationsLocators.FILTER_DIALOG} label").all_inner_texts()
        self.page.keyboard.press("Escape")
        self.page.wait_for_timeout(200)
        return labels

    def is_status_filter_available(self) -> bool:
        """Return True if the 'Filter Status' column-filter control is present."""
        return self.is_visible(EvaluationsLocators.FILTER_STATUS_BUTTON)

    def is_pagination_visible(self) -> bool:
        return self.is_visible(EvaluationsLocators.PAGINATION_CONTAINER)

    # ── List controls (status counts / sort / rows-per-page — Jul 2026) ───────

    _STATUS_TAB_LABELS = (
        "All",
        "Draft",
        "Queued",
        "In Progress",
        "Pending Review",
        "Completed",
        "Failed",
        "Cancelled",
    )

    def wait_for_list_loaded(self, timeout_s: int = 90) -> bool:
        """Wait until the hydrated list renders (positive condition).

        Polling for the absence of 'Loading evaluations…' is unreliable —
        there is a pre-hydration window where neither the curtain nor the
        content is in the DOM. Instead wait for a status-count button
        ('Draft(N)') or a table row to appear.
        """
        import re as _re

        for _ in range(timeout_s // 2):
            body = self.page.locator("body").inner_text()
            if _re.search(r"\w\(\d+\)", body) or self.get_table_row_count() > 0:
                return True
            self.page.wait_for_timeout(2_000)
        return False

    def get_status_tab_counts(self) -> dict[str, int]:
        """Parse the status filter buttons into {'Draft': 1, 'Completed': 5, ...}.

        The 'All' tab renders without a count; tabs with counts render as
        'Label(N)'. Longer labels are matched first so 'Pending Review' isn't
        consumed by a hypothetical 'Pending'.
        """
        import re

        counts: dict[str, int] = {}
        body = self.page.locator("body").inner_text()
        for label in self._STATUS_TAB_LABELS:
            if label == "All":
                continue
            m = re.search(re.escape(label) + r"\s*\((\d+)\)", body)
            if m:
                counts[label] = int(m.group(1))
        return counts

    def get_table_row_count(self) -> int:
        return self.page.locator(EvaluationsLocators.TABLE_BODY_ROW).count()

    def get_first_column_texts(self) -> list[str]:
        return [
            t.strip()
            for t in self.page.locator(
                f"{EvaluationsLocators.TABLE_BODY_ROW} td:first-child"
            ).all_inner_texts()
        ]

    def get_row_statuses(self) -> list[str]:
        """Uppercase status badge text per visible row (4th column)."""
        cells = self.page.locator(
            f"{EvaluationsLocators.TABLE_BODY_ROW} td:nth-child(4)"
        ).all_inner_texts()
        return [c.strip() for c in cells]

    def click_sort_header(self, header: str = "Evaluation Name") -> bool:
        loc = self.page.locator(f"th button:has-text('{header}')").first
        if not loc.count():
            return False
        loc.click()
        self.page.wait_for_timeout(1_500)
        return True

    def set_rows_per_page(self, value: str) -> bool:
        sel = self.page.locator(EvaluationsLocators.ROWS_PER_PAGE_SELECT).first
        if not sel.count():
            return False
        sel.select_option(value)
        self.page.wait_for_timeout(1_500)
        return True

    def get_page_x_of_y(self) -> tuple[int, int] | None:
        import re

        # Parse from body text — the indicator may be split across elements.
        m = re.search(r"Page\s+0?(\d+)\s+of\s+0?(\d+)", self.page.locator("body").inner_text())
        return (int(m.group(1)), int(m.group(2))) if m else None

    def get_evaluation_row_count(self) -> int:
        return self.page.locator(EvaluationsLocators.EVAL_TABLE_ROW).count()

    def has_draft_evaluations(self) -> bool:
        return self.page.locator(self.STATUS_DRAFT).count() > 0

    def has_completed_evaluations(self) -> bool:
        return self.page.locator(self.STATUS_COMPLETED).count() > 0

    def click_evaluation_row(self, row_index: int = 0) -> None:
        rows = self.page.locator(EvaluationsLocators.EVAL_TABLE_ROW)
        rows.nth(row_index).click()
        self.wait_for_app_ready()

    def click_new_evaluation(self) -> None:
        loc = self.page.locator(self.NEW_EVALUATION_BUTTON).first
        loc.wait_for(state="visible", timeout=self.timeout)
        loc.click()
        self.page.wait_for_timeout(500)

    # ── New Evaluation modal ───────────────────────────────────────────────────

    def is_new_eval_modal_visible(self) -> bool:
        return self.is_visible(self.MODAL_TITLE)

    def click_modal_start(self) -> None:
        self.click(self.MODAL_START_BUTTON)
        self.wait_for_app_ready()

    def click_modal_cancel(self) -> None:
        self.click(self.MODAL_CANCEL_BUTTON)

    # ── Wizard ─────────────────────────────────────────────────────────────────

    def is_wizard_visible(self) -> bool:
        return self.is_visible(self.WIZARD_TAB_CONFIGURATION)

    def is_auto_saved_indicator_visible(self) -> bool:
        return self.is_visible(EvaluationsLocators.WIZARD_AUTO_SAVED)

    def select_evaluation_type(self, eval_type: str) -> None:
        """Select Technical, Domain, or Cultural evaluation type."""
        selector_map = {
            "technical": self.EVAL_TYPE_TECHNICAL,
            "domain": self.EVAL_TYPE_DOMAIN,
            "cultural": self.EVAL_TYPE_CULTURAL,
        }
        sel = selector_map.get(eval_type.lower(), self.EVAL_TYPE_TECHNICAL)
        self.click(sel)

    def fill_evaluation_objective(self, objective: str) -> None:
        self.type_text(self.EVAL_OBJECTIVE_TEXTAREA, objective)

    def click_test_cases_tab(self) -> None:
        self.click(self.WIZARD_TAB_TEST_CASES)

    def is_objective_validation_error_visible(self) -> bool:
        return self.is_visible(self.EVAL_OBJECTIVE_ERROR)

    def cancel_evaluation(self) -> None:
        self.click(self.WIZARD_CANCEL_EVALUATION)
        self.wait_for_app_ready()

    # ── Evaluation detail ──────────────────────────────────────────────────────

    def is_overview_section_visible(self) -> bool:
        return self.is_visible(EvaluationsLocators.OVERVIEW_HEADING)

    def is_summary_section_visible(self) -> bool:
        return self.is_visible(EvaluationsLocators.SUMMARY_HEADING)

    def is_pass_rate_visible(self) -> bool:
        return self.is_visible(EvaluationsLocators.SUMMARY_PASS_RATE)

    def is_risk_section_visible(self) -> bool:
        return self.is_visible(EvaluationsLocators.RISK_TOTAL_ISSUES)

    def get_module_tab_count(self) -> int:
        tabs = [
            EvaluationsLocators.MODULE_TAB_HALLUCINATION,
            EvaluationsLocators.MODULE_TAB_BIAS,
            EvaluationsLocators.MODULE_TAB_PRIVACY,
        ]
        return sum(1 for t in tabs if self.is_visible(t))

    def click_module_tab(self, tab_name: str) -> None:
        tab_map = {
            "hallucination": EvaluationsLocators.MODULE_TAB_HALLUCINATION,
            "bias": EvaluationsLocators.MODULE_TAB_BIAS,
            "privacy": EvaluationsLocators.MODULE_TAB_PRIVACY,
        }
        sel = tab_map.get(tab_name.lower())
        if sel:
            self.click(sel)

    def is_download_report_visible(self) -> bool:
        return self.is_visible(self.DOWNLOAD_REPORT_BUTTON)

    def click_back_to_list(self) -> None:
        # The page renders mobile + desktop variants for both the <a> and the
        # <button> form — strict-mode click fails on 4 matches. Use .first.
        self.page.locator(EvaluationsLocators.BACK_TO_LIST_BUTTON).first.click()
        self.wait_for_app_ready()
