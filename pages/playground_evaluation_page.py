"""
Page object for the playground (manual) evaluation workspace.

The playground is embedded in the New Evaluation wizard when evaluation mode
is set to Manual. After creating a DRAFT and running it, the evaluator manually
calls the model with prompts and submits issue annotations.

Entry URL: /dashboard/ai-maker/{org_id}/evaluations/new?auditId={id}
"""

from __future__ import annotations

import re

from playwright.sync_api import Page

from locators.playground_locators import PlaygroundLocators
from pages.base_page import BasePage
from utils.config import Config

CIVICDATALAB_ORG_ID = 1


class PlaygroundEvaluationPage(BasePage):
    """Interactions for the playground evaluation workspace."""

    PROMPT_INPUT = PlaygroundLocators.PROMPT_INPUT
    CALL_MODEL_BUTTON = PlaygroundLocators.CALL_MODEL_BUTTON
    MODEL_OUTPUT_PANEL = PlaygroundLocators.MODEL_OUTPUT_PANEL
    ADD_ISSUE_BUTTON = PlaygroundLocators.ADD_ISSUE_BUTTON
    ISSUE_METRIC_DROPDOWN = PlaygroundLocators.ISSUE_METRIC_DROPDOWN
    ISSUE_VERDICT_FAIL = PlaygroundLocators.ISSUE_VERDICT_FAIL
    ISSUE_VERDICT_PASS = PlaygroundLocators.ISSUE_VERDICT_PASS
    ISSUE_SEVERITY_DROPDOWN = PlaygroundLocators.ISSUE_SEVERITY_DROPDOWN
    ISSUE_REASON_TEXTAREA = PlaygroundLocators.ISSUE_REASON_TEXTAREA
    ISSUE_SUBMIT_BUTTON = PlaygroundLocators.ISSUE_SUBMIT_BUTTON
    GENERATE_REASON_BUTTON = PlaygroundLocators.GENERATE_REASON_BUTTON
    GENERATE_IDEAL_OUTPUT_BUTTON = PlaygroundLocators.GENERATE_IDEAL_OUTPUT_BUTTON
    TEST_CASE_COUNTER = PlaygroundLocators.TEST_CASE_COUNTER
    PASSED_COUNTER = PlaygroundLocators.PASSED_COUNTER
    FAILED_COUNTER = PlaygroundLocators.FAILED_COUNTER
    FINISH_EVALUATION_BUTTON = PlaygroundLocators.FINISH_EVALUATION_BUTTON
    FINISH_CONFIRM_BUTTON = PlaygroundLocators.FINISH_CONFIRM_BUTTON
    STATUS_BADGE = PlaygroundLocators.STATUS_BADGE

    def __init__(self, page: Page, org_id: int = CIVICDATALAB_ORG_ID) -> None:
        super().__init__(page)
        self.org_id = org_id

    # ── Navigation ─────────────────────────────────────────────────────────────

    def go_to_draft(self, audit_id: str) -> PlaygroundEvaluationPage:
        url = Config.url(
            f"/dashboard/ai-maker/{self.org_id}/evaluations/new?auditId={audit_id}"
        )
        self.navigate(url)
        self.wait_for_app_ready(45_000)
        return self

    # ── Model interaction ──────────────────────────────────────────────────────

    def is_prompt_input_visible(self) -> bool:
        return self.is_visible(self.PROMPT_INPUT, timeout=10_000)

    def call_model(self, prompt: str, timeout: int = 60_000) -> str:
        """Type a prompt, click Call Model, and wait for the output to appear.

        Returns the output text. Raises if output panel does not appear within timeout.
        """
        self.type_text(self.PROMPT_INPUT, prompt, clear=True)
        self.click(self.CALL_MODEL_BUTTON)
        try:
            self.page.wait_for_selector(
                PlaygroundLocators.MODEL_LOADING_INDICATOR,
                state="hidden",
                timeout=timeout,
            )
        except Exception:
            pass  # loading indicator may not appear at all for fast responses
        self.wait_for_element(self.MODEL_OUTPUT_PANEL, timeout=timeout)
        return self.get_text(self.MODEL_OUTPUT_PANEL)

    def is_model_output_visible(self) -> bool:
        return self.is_visible(self.MODEL_OUTPUT_PANEL, timeout=5_000)

    # ── Issue submission ───────────────────────────────────────────────────────

    def click_add_issue(self) -> None:
        if self.is_visible(self.ADD_ISSUE_BUTTON, timeout=3_000):
            self.click(self.ADD_ISSUE_BUTTON)

    def submit_issue(
        self,
        verdict: str = "FAILED",
        severity: str = "HIGH",
        reason: str = "Test reason for flagged issue",
    ) -> None:
        """Fill and submit the issue form.

        verdict: 'PASSED' or 'FAILED'
        severity: 'HIGH', 'MEDIUM', or 'LOW'
        """
        if verdict.upper() == "FAILED":
            if self.is_visible(self.ISSUE_VERDICT_FAIL, timeout=3_000):
                self.page.locator(self.ISSUE_VERDICT_FAIL).first.click()
        else:
            if self.is_visible(self.ISSUE_VERDICT_PASS, timeout=3_000):
                self.page.locator(self.ISSUE_VERDICT_PASS).first.click()

        sev_loc = self.page.locator(self.ISSUE_SEVERITY_DROPDOWN)
        if sev_loc.count() > 0:
            try:
                sev_loc.first.select_option(label=severity)
            except Exception:
                pass

        if self.is_visible(self.ISSUE_REASON_TEXTAREA, timeout=3_000):
            self.type_text(self.ISSUE_REASON_TEXTAREA, reason, clear=True)

        self.click(self.ISSUE_SUBMIT_BUTTON)

    # ── AI-assist ─────────────────────────────────────────────────────────────

    def is_generate_reason_button_visible(self) -> bool:
        return self.is_visible(self.GENERATE_REASON_BUTTON, timeout=3_000)

    def generate_ai_reason(self, timeout: int = 30_000) -> str:
        """Click generate reason and wait for text to populate in the reason field."""
        self.click(self.GENERATE_REASON_BUTTON)
        try:
            self.page.wait_for_selector(
                PlaygroundLocators.AI_ASSIST_LOADING, state="hidden", timeout=timeout
            )
        except Exception:
            pass
        self.wait_for_element(self.ISSUE_REASON_TEXTAREA, timeout=timeout)
        return self.get_text(self.ISSUE_REASON_TEXTAREA)

    def generate_ideal_output(self, timeout: int = 30_000) -> str:
        """Click generate ideal output and wait for result."""
        self.click(self.GENERATE_IDEAL_OUTPUT_BUTTON)
        try:
            self.page.wait_for_selector(
                PlaygroundLocators.AI_ASSIST_LOADING, state="hidden", timeout=timeout
            )
        except Exception:
            pass
        return self.get_text(self.MODEL_OUTPUT_PANEL)

    # ── Counters ───────────────────────────────────────────────────────────────

    def _extract_number(self, selector: str) -> int:
        try:
            text = self.get_text(selector)
            match = re.search(r"\d+", text or "")
            return int(match.group()) if match else 0
        except Exception:
            return 0

    def get_test_case_count(self) -> int:
        return self._extract_number(self.TEST_CASE_COUNTER)

    def get_passed_count(self) -> int:
        return self._extract_number(self.PASSED_COUNTER)

    def get_failed_count(self) -> int:
        return self._extract_number(self.FAILED_COUNTER)

    # ── Finish evaluation ──────────────────────────────────────────────────────

    def is_finish_button_enabled(self) -> bool:
        loc = self.page.locator(self.FINISH_EVALUATION_BUTTON)
        if loc.count() == 0:
            return False
        return not (
            loc.first.get_attribute("disabled") is not None
            or loc.first.get_attribute("aria-disabled") == "true"
        )

    def finish_evaluation(self) -> None:
        """Click Finish Evaluation and confirm the dialog if it appears."""
        self.click(self.FINISH_EVALUATION_BUTTON)
        if self.is_visible(self.FINISH_CONFIRM_BUTTON, timeout=3_000):
            self.click(self.FINISH_CONFIRM_BUTTON)
        self.wait_for_load("networkidle")

    # ── Status ─────────────────────────────────────────────────────────────────

    def get_status(self) -> str:
        try:
            return (self.get_text(self.STATUS_BADGE) or "").strip()
        except Exception:
            return ""
