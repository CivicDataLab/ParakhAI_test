"""
Page object for the evaluator review section.

When an evaluation reaches PENDING_REVIEW status, evaluators can override
individual results and submit a final review to mark the audit COMPLETED.

URL: /dashboard/ai-maker/{org_id}/evaluations/{eval_id}
"""

from __future__ import annotations

from playwright.sync_api import Page

from locators.evaluator_review_locators import EvaluatorReviewLocators
from pages.base_page import BasePage


class EvaluatorReviewPage(BasePage):
    """Interactions for the evaluator review workflow."""

    REVIEW_SECTION = EvaluatorReviewLocators.REVIEW_SECTION
    RESULT_ROW = EvaluatorReviewLocators.RESULT_ROW
    OVERRIDE_SUCCESS_TOGGLE = EvaluatorReviewLocators.OVERRIDE_SUCCESS_TOGGLE
    OVERRIDE_RISK_DROPDOWN = EvaluatorReviewLocators.OVERRIDE_RISK_DROPDOWN
    OVERRIDE_REASON_TEXTAREA = EvaluatorReviewLocators.OVERRIDE_REASON_TEXTAREA
    SUBMIT_REVIEW_BUTTON = EvaluatorReviewLocators.SUBMIT_REVIEW_BUTTON
    SUBMIT_REVIEW_CONFIRM = EvaluatorReviewLocators.SUBMIT_REVIEW_CONFIRM
    REVIEW_SUBMITTED_BADGE = EvaluatorReviewLocators.REVIEW_SUBMITTED_BADGE

    def __init__(self, page: Page) -> None:
        super().__init__(page)

    # ── State checks ───────────────────────────────────────────────────────────

    def is_review_section_visible(self) -> bool:
        return self.is_visible(self.REVIEW_SECTION, timeout=5_000)

    def is_submit_review_button_visible(self) -> bool:
        return self.is_visible(self.SUBMIT_REVIEW_BUTTON, timeout=5_000)

    def get_result_row_count(self) -> int:
        return self.page.locator(self.RESULT_ROW).count()

    # ── Override ───────────────────────────────────────────────────────────────

    def override_result(
        self,
        row_index: int = 0,
        risk_level: str = "LOW_RISK",
        reason: str = "Evaluator override — test",
    ) -> None:
        """Override a result row's risk level and reason. row_index is 0-based."""
        rows = self.page.locator(self.RESULT_ROW)
        if rows.count() <= row_index:
            return
        row = rows.nth(row_index)

        risk_sel = row.locator(self.OVERRIDE_RISK_DROPDOWN)
        if risk_sel.count() > 0:
            try:
                risk_sel.first.select_option(
                    label=risk_level.replace("_", " ").title()
                )
            except Exception:
                pass

        reason_sel = row.locator(self.OVERRIDE_REASON_TEXTAREA)
        if reason_sel.count() > 0:
            reason_sel.first.fill(reason)

    # ── Submit ─────────────────────────────────────────────────────────────────

    def submit_review(self) -> None:
        """Click Submit Review and confirm the dialog."""
        self.click(self.SUBMIT_REVIEW_BUTTON)
        if self.is_visible(self.SUBMIT_REVIEW_CONFIRM, timeout=3_000):
            self.click(self.SUBMIT_REVIEW_CONFIRM)
        self.wait_for_load("networkidle")

    def is_review_submitted(self) -> bool:
        return self.is_visible(self.REVIEW_SUBMITTED_BADGE, timeout=10_000)
