"""
Page object for the New Evaluation wizard — Draft & Auto-Save flow.

Covers:
  • "New Evaluation" modal (model + version dropdowns → Start)
  • Evaluation Configuration tab (name, type, objective, modules, mode)
  • Test Cases tab — Automated mode (dataset selection, paste/upload, Run Evaluation)
  • Test Cases tab — Manual mode   (module cards, test entry, Change Module, Finish)
  • Auto-save indicator
  • Cancel Evaluation
  • Draft row navigation from the list

Entry URL : /dashboard/ai-maker/{org_id}/evaluations  (click New Evaluation)
Wizard URL: /evaluations/new?modelId=…&versionId=…
            /evaluations/new?auditId=…  (re-open a draft)
"""

from __future__ import annotations

import re

from playwright.sync_api import Page

from locators.evaluations_locators import EvaluationsLocators
from pages.base_page import BasePage
from utils.config import Config

CIVICDATALAB_ORG_ID = 1


class NewEvaluationPage(BasePage):
    """
    Interactions for the New Evaluation wizard and its Draft/Auto-Save behaviour.

    Instantiate with the authenticated Playwright Page object:
        page = NewEvaluationPage(authenticated_page)
    """

    # ── Locator aliases (for readable test assertions) ─────────────────────────
    NEW_EVALUATION_BUTTON = EvaluationsLocators.NEW_EVALUATION_BUTTON
    MODAL_TITLE = EvaluationsLocators.MODAL_TITLE
    MODAL_START_BUTTON = EvaluationsLocators.MODAL_START_BUTTON
    MODAL_CANCEL_BUTTON = EvaluationsLocators.MODAL_CANCEL_BUTTON
    WIZARD_TAB_CONFIGURATION = EvaluationsLocators.WIZARD_TAB_CONFIGURATION
    WIZARD_TAB_TEST_CASES = EvaluationsLocators.WIZARD_TAB_TEST_CASES
    WIZARD_EVAL_NAME_INPUT = EvaluationsLocators.WIZARD_EVAL_NAME_INPUT
    WIZARD_CANCEL_EVALUATION = EvaluationsLocators.WIZARD_CANCEL_EVALUATION
    WIZARD_AUTO_SAVED = EvaluationsLocators.WIZARD_AUTO_SAVED
    EVAL_TYPE_TECHNICAL = EvaluationsLocators.EVAL_TYPE_TECHNICAL
    EVAL_TYPE_DOMAIN = EvaluationsLocators.EVAL_TYPE_DOMAIN
    EVAL_TYPE_CULTURAL = EvaluationsLocators.EVAL_TYPE_CULTURAL
    EVAL_MODE_DROPDOWN = EvaluationsLocators.EVAL_MODE_DROPDOWN
    EVAL_OBJECTIVE_TEXTAREA = EvaluationsLocators.EVAL_OBJECTIVE_TEXTAREA
    ADD_TEST_CASES_BUTTON = EvaluationsLocators.ADD_TEST_CASES_BUTTON
    RUN_EVALUATION_BUTTON = EvaluationsLocators.RUN_EVALUATION_BUTTON
    RUN_EVALUATION_NO_SELECTION_ERROR = EvaluationsLocators.RUN_EVALUATION_NO_SELECTION_ERROR
    FINISH_EVALUATION_BUTTON = EvaluationsLocators.FINISH_EVALUATION_BUTTON
    MANUAL_MIN_TEST_CASES_NOTE = EvaluationsLocators.MANUAL_MIN_TEST_CASES_NOTE
    STATUS_DRAFT = EvaluationsLocators.STATUS_DRAFT

    def __init__(self, page: Page, org_id: int = CIVICDATALAB_ORG_ID) -> None:
        super().__init__(page)
        self.org_id = org_id
        self.list_url = Config.url(f"/dashboard/ai-maker/{org_id}/evaluations")

    # ── Navigation ─────────────────────────────────────────────────────────────

    def go_to_evaluations_list(self) -> NewEvaluationPage:
        """Navigate to the evaluations list page."""
        self.navigate(self.list_url)
        self.wait_for_load("domcontentloaded")
        # The dashboard shows a 'Verifying your session...' curtain on every
        # cold protected-route load before rendering content. On a cold
        # deep-link load this can take well over 5s; reloading restarts the
        # check, so we wait it out rather than refresh (see
        # base_page.wait_for_app_ready for the full rationale).
        self.wait_for_app_ready(60_000)
        # Give the evaluations table data time to load before callers inspect rows.
        try:
            self.page.wait_for_selector(
                EvaluationsLocators.EVAL_TABLE_ROW, timeout=30_000
            )
        except Exception:
            pass
        return self

    def go_to_draft(self, audit_id: int | str) -> NewEvaluationPage:
        """Directly navigate to a known draft by its auditId query param."""
        self.navigate(Config.url(f"/evaluations/new?auditId={audit_id}"))
        self.wait_for_load("domcontentloaded")
        return self

    # ── Modal ─────────────────────────────────────────────────────────────────

    def click_new_evaluation(self) -> NewEvaluationPage:
        """Click the 'New Evaluation' button and wait for the modal to be ready.

        The modal title paints immediately, but the model/version dropdowns are
        gated behind a 'Loading models...' curtain that can take ~20s to resolve
        on dev. Callers assert on the dropdown labels straight after, so wait the
        curtain out here rather than racing it with a short fixed sleep.
        """
        loc = self.page.locator(self.NEW_EVALUATION_BUTTON).first
        loc.wait_for(state="visible", timeout=self.timeout)
        loc.click()
        # Wait for the 'Loading models...' curtain inside the modal to clear.
        # Until it does, no model/version is selected and the Start button stays
        # aria-disabled, so use a generous budget (dev can take 30s+ under load).
        try:
            self.page.locator("text=/^Loading models/i").first.wait_for(
                state="hidden", timeout=60_000
            )
        except Exception:
            pass  # absent or already gone — let the caller's assertion surface it
        return self

    def is_modal_visible(self) -> bool:
        """Return True if the 'Start New Evaluation' modal is open."""
        return self.is_visible(self.MODAL_TITLE)

    def modal_model_dropdown_has_options(self) -> bool:
        """
        Return True if the 'Select AI Model' dropdown contains at least one option.

        Handles both native <select> and custom combobox patterns.
        NOTE: If only placeholder text renders, add data-testid="model-option" to
        each option element so this selector can target them directly.
        """
        # Try native <select> first
        native = self.page.locator("select").first
        if native.is_visible():
            return native.locator("option").count() > 1  # >1 excludes placeholder
        # Fallback: custom combobox — open it and count list items
        combo = self.page.locator(
            "[aria-label*='AI Model'], [aria-label*='model'], "
            "[class*='model'] [role='combobox']"
        ).first
        if combo.is_visible():
            combo.click()
            self.page.wait_for_timeout(300)
            count = self.page.locator("[role='option'], [role='listbox'] li").count()
            # Close without selecting
            self.page.keyboard.press("Escape")
            return count > 0
        # Last resort: check for visible option text
        return self.is_visible(EvaluationsLocators.MODAL_MODEL_OPTION, timeout=3_000)

    def modal_version_dropdown_has_options(self) -> bool:
        """
        Return True if the 'Select Model Version' dropdown contains at least one
        selectable version.

        Unlike the model dropdown, a model may expose a single version (e.g.
        '1.0 (Latest)') — so the threshold here is >= 1 real option, not > 1.
        The version <select> has no placeholder <option>, so every option is a
        real, selectable version. Target it by accessible name to avoid relying
        on the positional index of <select> elements on the page.
        """
        version_select = self.page.get_by_role(
            "combobox", name="Select Model Version"
        ).first
        if version_select.is_visible():
            return version_select.locator("option").count() >= 1
        # Fallback: the second native <select> in the modal is the version one.
        selects = self.page.locator("select")
        if selects.count() >= 2 and selects.nth(1).is_visible():
            return selects.nth(1).locator("option").count() >= 1
        return self.is_visible(EvaluationsLocators.MODAL_VERSION_OPTION, timeout=3_000)

    def select_first_model_and_version(self) -> None:
        """
        Select the first available option in both model and version dropdowns.

        The modal renders three <select> elements:
          index 0 — rows-per-page selector (10 / 25 / 50 / 100) — skip this one
          index 1 — AI Model dropdown
          index 2 — Model Version dropdown

        Works for native <select> elements.  If the dropdowns are custom comboboxes
        (React-Select / Radix), add data-testid="model-dropdown" /
        data-testid="version-dropdown" and update this method to use those selectors.
        """
        selects = self.page.locator("select")
        n = selects.count()
        # Start at index 1 to skip the rows-per-page selector at index 0
        for i in range(1, min(n, 3)):
            sel = selects.nth(i)
            if not sel.is_visible():
                continue
            opts = sel.locator("option")
            if opts.count() > 0:
                val = opts.first.get_attribute("value")
                if val:
                    sel.select_option(value=val)
                    self.page.wait_for_timeout(300)

    def click_modal_start(self) -> NewEvaluationPage:
        """Click 'Start' in the modal and wait for the wizard page to render."""
        # Use .first to avoid strict mode — the modal may render an enabled
        # "Start New Evaluation" button alongside a disabled "Start" button.
        # Target the *enabled* Start button: it renders aria-disabled until a
        # model + version are selected (which only happens once the modal's
        # model list has loaded). Waiting for the enabled one avoids a 30s
        # auto-wait spent clicking a button that is still disabled.
        enabled_start = self.page.locator(
            "button:has-text('Start'):not([aria-disabled='true']):not([disabled])"
        ).first
        try:
            enabled_start.wait_for(state="visible", timeout=self.timeout)
            loc = enabled_start
        except Exception:
            loc = self.page.locator(self.MODAL_START_BUTTON).first
            loc.wait_for(state="visible", timeout=self.timeout)
        loc.click()
        # Wait for the SPA URL change to /evaluations/new
        try:
            self.page.wait_for_url("**/evaluations/new**", timeout=self.timeout)
        except Exception:
            self.page.wait_for_timeout(2_000)
        # The wizard mounts client-side from this navigation and renders without
        # a refresh. Do NOT reload here: a reload cold-loads the wizard URL,
        # which re-triggers the ~20s 'Verifying your session...' curtain for no
        # benefit. Wait for the Configuration tab to confirm the wizard mounted.
        try:
            self.page.locator(self.WIZARD_TAB_CONFIGURATION).first.wait_for(
                state="visible", timeout=self.timeout
            )
        except Exception:
            pass  # let the caller's assertion surface the real failure
        return self

    def click_modal_cancel(self) -> None:
        """Click 'Cancel' in the modal."""
        loc = self.page.locator(self.MODAL_CANCEL_BUTTON).first
        loc.wait_for(state="visible", timeout=self.timeout)
        loc.click()

    # ── Wizard — general ──────────────────────────────────────────────────────

    def is_wizard_visible(self) -> bool:
        """Return True if the Evaluation Configuration tab is visible (wizard is open)."""
        return self.is_visible(self.WIZARD_TAB_CONFIGURATION)

    def is_on_wizard_url(self, timeout: int = 10_000) -> bool:
        """
        Return True if the current URL is the wizard URL (/evaluations/new).

        Waits up to `timeout` ms for the SPA route to settle so callers don't
        race the navigation that follows clicking 'Start' in the modal.
        """
        try:
            self.page.wait_for_url("**/evaluations/new**", timeout=timeout)
            return True
        except Exception:
            return "/evaluations/new" in self.page.url

    def wait_for_audit_id_in_url(self, timeout: int = 15_000) -> str | None:
        """
        Wait for the URL to gain an `auditId` query param (i.e. the draft has
        been persisted) and return that id. Returns None on timeout.

        Use this after clicking 'Add Test Cases' in the wizard, instead of
        reading `page.url` immediately — the URL update is async and races
        the click. See app_bugs.md #1 for related auto-save behaviour.
        """
        try:
            self.page.wait_for_url(lambda u: "auditId=" in u, timeout=timeout)
        except Exception:
            return None
        return self.get_audit_id_from_url()

    def get_audit_id_from_url(self) -> str | None:
        """
        Extract the auditId query param from the current URL.
        Returns None if not present.
        """
        match = re.search(r"[?&]auditId=([^&]+)", self.page.url)
        return match.group(1) if match else None

    def is_auto_saved_indicator_visible(self, timeout: int = 8_000) -> bool:
        """
        Return True if the 'Auto-saved ✓' indicator is visible in the header.

        NOTE: Add data-testid="auto-save-indicator" to the indicator element for
        stable selection — the current text-based selector may match false positives
        if "Auto-saved" appears elsewhere on the page.
        """
        return self.is_visible(self.WIZARD_AUTO_SAVED, timeout=timeout)

    def cancel_evaluation(self) -> None:
        """Click 'Cancel Evaluation ✕' and wait to return to the list."""
        loc = self.page.locator(self.WIZARD_CANCEL_EVALUATION).first
        loc.wait_for(state="visible", timeout=self.timeout)
        loc.click()
        # The app may show a confirmation modal before navigating away.
        # Try the most common confirm/yes button patterns within 3 s.
        for confirm_sel in (
            "button:has-text('Confirm')",
            "button:has-text('Yes')",
            "button:has-text('OK')",
            # Some apps label the final destructive button "Cancel Evaluation" again
            # inside the dialog.
            "[role='dialog'] button:has-text('Cancel')",
        ):
            if self.is_visible(confirm_sel, timeout=2_000):
                self.page.locator(confirm_sel).first.click()
                break
        # SPA navigation — domcontentloaded fires immediately after route change.
        # Wait for the URL to no longer contain '/evaluations/new'.
        try:
            self.page.wait_for_function(
                "() => !window.location.pathname.includes('/evaluations/new')",
                timeout=self.timeout,
            )
        except Exception:
            self.wait_for_load("domcontentloaded")
        self.page.wait_for_timeout(1_000)

    def click_tab_configuration(self) -> None:
        """Switch to the 'Evaluation Configuration' tab."""
        self.click(self.WIZARD_TAB_CONFIGURATION)
        self.page.wait_for_timeout(300)

    def click_tab_test_cases(self) -> None:
        """Switch to the 'Test Cases' tab."""
        self.click(self.WIZARD_TAB_TEST_CASES)
        self.page.wait_for_timeout(300)

    # ── Wizard — Evaluation Configuration tab ─────────────────────────────────

    def get_evaluation_name(self) -> str:
        """Return the current value of the Evaluation Name input.

        Waits for the input to attach + become visible before reading. Without
        this, callers race the SPA hydration and get an empty string.
        """
        loc = self.page.locator(self.WIZARD_EVAL_NAME_INPUT).first
        loc.wait_for(state="visible", timeout=self.timeout)
        return loc.input_value()

    def set_evaluation_name(self, name: str) -> None:
        """
        Clear and type a new evaluation name.

        NOTE: The spec states id="auditName" — the locator already targets that.
        If the field is read-only by default (pre-filled by the server), the app
        may need a click-to-edit interaction; adjust if needed.
        """
        self.type_text(self.WIZARD_EVAL_NAME_INPUT, name)

    def type_evaluation_name(self, name: str) -> None:
        self.set_evaluation_name(name)

    def select_evaluation_type(self, eval_type: str) -> None:
        """
        Select an evaluation type by clicking its radio/label.

        Args:
            eval_type: "technical" | "domain" | "cultural"
        """
        selector_map = {
            "technical": self.EVAL_TYPE_TECHNICAL,
            "domain": self.EVAL_TYPE_DOMAIN,
            "cultural": self.EVAL_TYPE_CULTURAL,
        }
        sel = selector_map.get(eval_type.lower(), self.EVAL_TYPE_TECHNICAL)
        # Use .first to avoid strict mode violation — the label text may appear
        # twice: once as the radio label and once as the selected-type tag badge.
        loc = self.page.locator(sel).first
        loc.wait_for(state="visible", timeout=self.timeout)
        loc.click()
        self.page.wait_for_timeout(300)

    def fill_evaluation_objective(self, objective: str) -> None:
        """Fill the Evaluation Objective textarea."""
        self.type_text(self.EVAL_OBJECTIVE_TEXTAREA, objective)

    def check_module(self, module: str) -> None:
        """
        Ensure an evaluation module checkbox is checked.

        This method is idempotent — it only clicks if the checkbox is currently
        unchecked, so calling it on an already-checked module is a no-op.

        Args:
            module: "hallucination" | "bias" | "privacy"

        NOTE: The checkboxes are currently targeted by proximity to label text.
        Add data-testid="module-checkbox-hallucination" etc. for stable selection.
        """
        label_map = {
            "hallucination": EvaluationsLocators.EVAL_MODULE_HALLUCINATION,
            "bias": EvaluationsLocators.EVAL_MODULE_BIAS,
            "privacy": EvaluationsLocators.EVAL_MODULE_PRIVACY,
        }
        label_sel = label_map.get(module.lower())
        if not label_sel:
            raise ValueError(f"Unknown module: {module!r}")
        label_text = label_sel.split("=", 1)[1].split(" >>")[0]  # strip nth= suffix
        # Locate the checkbox near the module label
        checkbox = self.page.locator(
            f"input[type='checkbox']:near(:text('{label_text}'))"
        )
        if checkbox.count() > 0:
            cb = checkbox.first
            # Only click if NOT already checked — avoids toggling a pre-checked box
            if not cb.is_checked():
                cb.click()
                self.page.wait_for_timeout(300)
        else:
            # Fallback: the label itself may act as a toggle (custom checkbox)
            self.click(label_sel)

    def uncheck_module(self, module: str) -> None:
        """Uncheck an evaluation module checkbox (same logic as check_module)."""
        self.check_module(module)  # toggle — callers must know current state

    def module_subcategory_dropdown_visible(self) -> bool:
        """Return True if a sub-category dropdown is visible (module is checked)."""
        return self.is_visible(EvaluationsLocators.EVAL_MODULE_SUBCATEGORY_DROPDOWN, timeout=3_000)

    def select_evaluation_scope(self, scope: str = "General") -> None:
        """
        Select the Evaluation Scope. Required — without it, the wizard's
        'Add Test Cases' click does NOT persist a draft (no auditId in URL).
        Confirmed via Playwright MCP 2026-05-07.

        Args:
            scope: "Healthcare" | "Agriculture" | "General" (default: "General")
        """
        sel = self.page.locator(EvaluationsLocators.EVAL_SCOPE_DROPDOWN)
        sel.wait_for(state="visible", timeout=self.timeout)
        sel.select_option(label=scope)
        self.page.wait_for_timeout(300)

    def select_mode(self, mode: str) -> None:
        """
        Select the Mode of Evaluation.

        Args:
            mode: "automated" | "manual"

        NOTE: The Mode dropdown (<select name="modeOfEvaluation">) is rendered as
        disabled until at least one Evaluation Module checkbox is checked.  Always
        call check_module() (or use fill_configuration_tab() which does it
        automatically) before calling this method.
        """
        # Mode of Evaluation is a native <select> — use select_option() directly.
        label = "Automated" if mode.lower() == "automated" else "Manual"
        sel = self.page.locator(self.EVAL_MODE_DROPDOWN)
        sel.wait_for(state="visible", timeout=self.timeout)
        # Wait up to 10 s for the dropdown to become enabled.
        # It starts disabled and only becomes enabled after at least one module
        # checkbox is checked. If modules haven't been checked yet this will
        # time-out and select_option will surface the real error.
        try:
            self.page.wait_for_function(
                "() => { const el = document.querySelector('select[name=\"modeOfEvaluation\"]');"
                " return el ? !el.disabled : false; }",
                timeout=10_000,
            )
        except Exception:
            pass  # let select_option surface the real failure
        sel.select_option(label=label)
        self.page.wait_for_timeout(300)

    def click_add_test_cases(self) -> None:
        """
        Click 'Add Test Cases' to advance to the Test Cases tab.
        After clicking, the URL should gain &auditId=... if a draft is created.
        """
        self.click(self.ADD_TEST_CASES_BUTTON)
        # SPA route change — wait for auditId to appear in the URL (= draft
        # persisted server-side). If auditId was already present (re-opening a
        # draft), fall through.
        try:
            self.page.wait_for_url("**auditId=**", timeout=self.timeout)
        except Exception:
            self.page.wait_for_timeout(3_000)
        # Persisting the draft triggers a re-fetch gated behind a
        # 'Loading evaluation details...' curtain that can take ~30-60s on dev,
        # during which the page stays on the Configuration tab; once it clears
        # the app auto-advances to the Test Cases tab. Wait it out — do NOT
        # reload (a reload cold-loads the wizard URL and re-triggers the ~20s
        # 'Verifying your session...' curtain, and bounces back to Configuration).
        try:
            self.page.locator("text=/^Loading evaluation details/i").first.wait_for(
                state="hidden", timeout=60_000
            )
        except Exception:
            pass  # absent or already gone
        # Confirm we actually landed on the Test Cases tab by waiting for its
        # real content: the manual module-selection cards (specific class, no
        # false-match on the Configuration tab) or the automated dataset table.
        try:
            self.page.locator(
                "[class*='moduleselectioncard'], "
                ":text('Select Prompt Datasets')"
            ).first.wait_for(state="visible", timeout=20_000)
        except Exception:
            pass  # let the caller's wait_for_* assertion surface the real failure

    # ── Wizard — Test Cases tab (Automated) ────────────────────────────────────

    def is_dataset_table_visible(self) -> bool:
        """Return True if the 'Select Prompt Datasets' table is rendered."""
        return self.is_visible(EvaluationsLocators.AUTOMATED_DATASET_TABLE, timeout=5_000)

    def wait_for_dataset_table(self, timeout: int = 15_000) -> bool:
        """
        Wait for the 'Select Prompt Datasets' table to attach + become visible
        on the Test Cases tab (Automated mode). Returns True on success, False
        on timeout. Use this instead of `is_dataset_table_visible()` directly
        after `click_add_test_cases()` — the table renders after the SPA
        post-reload hydration completes.
        """
        try:
            self.page.locator(
                EvaluationsLocators.AUTOMATED_DATASET_TABLE
            ).first.wait_for(state="visible", timeout=timeout)
            return True
        except Exception:
            return False

    def select_first_dataset(self) -> bool:
        """
        Click the first dataset row checkbox.  Returns True if a checkbox was found.

        NOTE: Add data-testid="dataset-checkbox" to dataset checkboxes for stable
        selection; class/proximity selectors may break across UI rebuilds.
        """
        checkbox_loc = self.page.locator(EvaluationsLocators.AUTOMATED_DATASET_CHECKBOX).first
        if checkbox_loc.is_visible():
            checkbox_loc.click()
            self.page.wait_for_timeout(300)
            return True
        return False

    def is_run_evaluation_button_enabled(self) -> bool:
        """Return True if the 'Run Evaluation' button is enabled (not disabled)."""
        btn = self.page.locator(self.RUN_EVALUATION_BUTTON).first
        return btn.is_visible() and btn.is_enabled()

    def is_run_evaluation_error_visible(self) -> bool:
        """Return True if the 'no dataset selected' error message is shown."""
        return self.is_visible(self.RUN_EVALUATION_NO_SELECTION_ERROR, timeout=3_000)

    def click_run_evaluation(self) -> None:
        """Click 'Run Evaluation' (only if enabled)."""
        self.click(self.RUN_EVALUATION_BUTTON)

    # ── Wizard — Test Cases tab (Manual) ──────────────────────────────────────

    def get_module_card_count(self) -> int:
        """Return the number of module cards rendered in the Manual test tab."""
        return self.page.locator(EvaluationsLocators.MANUAL_MODULE_CARD).count()

    def is_module_card_visible(self) -> bool:
        """Return True if at least one module card is visible."""
        return self.is_visible(EvaluationsLocators.MANUAL_MODULE_CARD, timeout=5_000)

    def wait_for_module_cards(self, min_count: int = 1, timeout: int = 15_000) -> bool:
        """
        Wait for at least `min_count` module cards to render on the Test Cases
        tab (Manual mode). Returns True on success, False on timeout. Use this
        instead of `is_module_card_visible()` directly after
        `click_add_test_cases()` — module cards hydrate after the SPA settle.

        Counts the specific module-selection card class only. The broad
        `MANUAL_MODULE_CARD` fallback chain must NOT be used here: its
        `div:has(:text('Hallucination...')):has(:text('Test Cases'))` clause
        also matches the Configuration tab (module checkbox label + 'Test Cases'
        tab button), which would report a false positive while the Test Cases
        tab is still behind the 'Loading evaluation details...' curtain.
        """
        card_selector = "[class*='moduleselectioncard']"
        try:
            self.page.wait_for_function(
                f'() => document.querySelectorAll("{card_selector}").length'
                f" >= {min_count}",
                timeout=timeout,
            )
            return True
        except Exception:
            return self.page.locator(card_selector).count() >= min_count

    def click_first_module_card(self) -> None:
        """
        Click the first module card to enter the test entry view.

        NOTE: Add data-testid="module-card" to each card element so the first
        card can be targeted without relying on class-name fragility.
        """
        card = self.page.locator(EvaluationsLocators.MANUAL_MODULE_CARD).first
        card.wait_for(state="visible", timeout=self.timeout)
        card.click()
        self.page.wait_for_timeout(500)

    def is_manual_input_textarea_visible(self) -> bool:
        """Return True if the Input textarea in the test entry panel is visible."""
        return self.is_visible(EvaluationsLocators.MANUAL_INPUT_TEXTAREA, timeout=5_000)

    def is_manual_output_panel_visible(self) -> bool:
        """Return True if the Output display panel is visible."""
        return self.is_visible(EvaluationsLocators.MANUAL_OUTPUT_PANEL, timeout=5_000)

    def is_manual_submit_button_visible(self) -> bool:
        """Return True if the Submit button in the test entry panel is visible."""
        return self.is_visible(EvaluationsLocators.MANUAL_SUBMIT_BUTTON, timeout=5_000)

    def is_change_module_link_visible(self) -> bool:
        """Return True if the '< Change Module' navigation link is visible."""
        return self.is_visible(EvaluationsLocators.MANUAL_CHANGE_MODULE_LINK, timeout=5_000)

    def click_change_module(self) -> None:
        """Click '< Change Module' to return to the module card list."""
        self.click(EvaluationsLocators.MANUAL_CHANGE_MODULE_LINK)
        self.page.wait_for_timeout(400)

    def is_finish_evaluation_button_enabled(self) -> bool:
        """Return True if the 'Finish Evaluation' button is enabled."""
        btn = self.page.locator(self.FINISH_EVALUATION_BUTTON).first
        return btn.is_visible() and btn.is_enabled()

    def is_finish_evaluation_button_disabled(self) -> bool:
        """Return True if 'Finish Evaluation' is disabled (not enough test cases)."""
        btn = self.page.locator(self.FINISH_EVALUATION_BUTTON).first
        if not btn.is_visible():
            return True  # invisible == effectively unavailable
        return btn.is_disabled()

    # ── Draft list helpers ─────────────────────────────────────────────────────

    def get_draft_row_count(self) -> int:
        """Return the number of DRAFT rows in the evaluations list."""
        return self.page.locator(EvaluationsLocators.DRAFT_ROW).count()

    def click_first_draft_row(self) -> None:
        """Click the first DRAFT row in the evaluations list."""
        row = self.page.locator(EvaluationsLocators.DRAFT_ROW).first
        row.wait_for(state="visible", timeout=self.timeout)
        row.click()
        self.wait_for_load("domcontentloaded")

    def click_first_completed_row(self) -> None:
        """Click the first COMPLETED row in the evaluations list."""
        row = self.page.locator(EvaluationsLocators.COMPLETED_ROW).first
        row.wait_for(state="visible", timeout=self.timeout)
        row.click()
        self.wait_for_load("domcontentloaded")

    def draft_row_href_contains_new(self) -> bool:
        """
        Return True if the first DRAFT row's anchor href contains '/evaluations/new'.

        Validates that DRAFT rows link to the editable wizard, not the read-only
        report view.

        NOTE: If the row is a <tr> with a click handler rather than an <a>, this
        check will evaluate the URL *after* navigation instead. Add
        data-testid="draft-row-link" wrapping the <tr> in an <a> for reliability.
        """
        row = self.page.locator(EvaluationsLocators.DRAFT_ROW).first
        # Wait for the row to attach so get_attribute returns its real value
        # rather than None from a not-yet-rendered element.
        row.wait_for(state="visible", timeout=self.timeout)
        href = row.get_attribute("href")
        if href is not None:
            return "/evaluations/new" in href
        # Fallback: navigate and check URL
        row.click()
        self.wait_for_load("domcontentloaded")
        result = "/evaluations/new" in self.page.url
        self.page.go_back()
        self.wait_for_load("domcontentloaded")
        return result

    def completed_row_href_excludes_new(self) -> bool:
        """
        Return True if the first COMPLETED row links to /evaluations/{id} (not /new).

        NOTE: Same stabilisation note as draft_row_href_contains_new.
        """
        row = self.page.locator(EvaluationsLocators.COMPLETED_ROW).first
        row.wait_for(state="visible", timeout=self.timeout)
        href = row.get_attribute("href")
        if href is not None:
            return "/evaluations/" in href and "new" not in href
        # Fallback: navigate and check URL
        row.click()
        self.wait_for_load("domcontentloaded")
        result = "/evaluations/" in self.page.url and "new" not in self.page.url
        self.page.go_back()
        self.wait_for_load("domcontentloaded")
        return result

    # ── Composite helpers (multi-step) ─────────────────────────────────────────

    def open_new_evaluation_wizard(self) -> NewEvaluationPage:
        """
        Full flow: navigate to list → click New Evaluation → Start.

        Skips the test if the modal or wizard is not reachable.
        Returns self for fluent chaining.
        """
        self.go_to_evaluations_list()
        self.click_new_evaluation()
        assert self.is_modal_visible(), (
            "'Start New Evaluation' modal did not appear — platform may be unavailable or slow"
        )
        self.select_first_model_and_version()
        self.click_modal_start()
        assert self.is_wizard_visible(), (
            "Evaluation wizard did not load after clicking Start"
        )
        return self

    def fill_configuration_tab(
        self,
        objective: str,
        eval_type: str = "technical",
        mode: str = "automated",
        modules: list | None = None,
        scope: str = "General",
    ) -> NewEvaluationPage:
        """
        Fill all required fields on the Evaluation Configuration tab.

        Args:
            objective: The evaluation objective text.
            eval_type: "technical" | "domain" | "cultural"
            mode:      "automated" | "manual"
            modules:   List of module names to check before selecting mode.
                       Defaults to ["hallucination"] because the Mode dropdown
                       is disabled until at least one module is checked.
            scope:     "Healthcare" | "Agriculture" | "General" (default).
                       Required — without it the wizard does NOT create a draft.

        Returns self for fluent chaining.
        """
        if modules is None:
            modules = ["hallucination"]

        self.select_evaluation_type(eval_type)
        # The Scope dropdown, module checkboxes, and (enabled) Mode dropdown all
        # render together only after the wizard's 'Loading modules...' fetch
        # resolves — which can take ~30s+ on dev. Wait it out once here so the
        # field interactions below don't each race the same curtain with their
        # own timeout (the cause of intermittent 'select[name=auditScope]'
        # timeouts when the suite runs back-to-back).
        try:
            self.page.locator("text=/^Loading modules/i").first.wait_for(
                state="hidden", timeout=45_000
            )
        except Exception:
            pass  # absent or already gone — field waits below will surface issues
        self.select_evaluation_scope(scope)
        self.fill_evaluation_objective(objective)
        # Check modules BEFORE selecting mode — mode dropdown starts disabled
        # and only becomes enabled after at least one module checkbox is checked.
        for module in modules:
            self.check_module(module)
            self.page.wait_for_timeout(300)
        self.select_mode(mode)
        self.page.wait_for_timeout(300)
        return self
