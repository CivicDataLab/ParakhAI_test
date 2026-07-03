"""
Page object for the New Evaluation flow (Jul 2026 redesign).

Covers:
  • "Start an Evaluation" modal — two steps:
      step 1: model + version selects, evaluation name, method (bulk/manual)
      step 2: evaluator-type radios, objective textarea → Start Evaluation
  • Single-page wizard at /evaluations/new?auditId=… (NO tabs any more):
      header (editable name, Draft badge, Back to List, Cancel)
      Evaluation Overview card (Eval ID / Scope / Mode / Evaluator / Objective)
      Evaluation Workspace — Bulk: module checkboxes + prompt-library source
                             + Run Evaluation; Playground: prompt workspace
  • Draft row navigation from the list (anchor inside the first cell)

Entry URL : /dashboard/ai-maker/{org_id}/evaluations  (click New Evaluation)
Wizard URL: /evaluations/new?auditId=…
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
        self.navigate(
            Config.url(
                f"/dashboard/ai-maker/{self.org_id}/evaluations/new?auditId={audit_id}"
            )
        )
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
        """Return True if the 'Start an Evaluation' modal is open."""
        return self.is_visible(self.MODAL_TITLE)

    def get_modal_step(self) -> str | None:
        """Return the current modal step ('1' or '2'), or None if no modal is open.

        The data-start-evaluation-step attribute is only set on step 2 on some
        builds, so fall back to content detection: step 2 shows the
        'I am evaluating as' heading, step 1 shows the model select.
        """
        try:
            dlg = self.page.locator(EvaluationsLocators.MODAL_DIALOG).first
            step = dlg.get_attribute("data-start-evaluation-step", timeout=2_000)
            if step:
                return step
        except Exception:
            pass
        if not self.is_visible(self.MODAL_TITLE, timeout=2_000):
            return None
        if self.is_visible(EvaluationsLocators.MODAL_STEP2_HEADING, timeout=1_000):
            return "2"
        return "1"

    def modal_model_dropdown_has_options(self) -> bool:
        """Return True if the model dropdown has at least one real model option."""
        model_select = self.page.locator(EvaluationsLocators.MODAL_MODEL_DROPDOWN)
        if model_select.is_visible():
            return model_select.locator("option").count() > 1
        return False

    def modal_version_dropdown_has_options(self) -> bool:
        """Return True if the version dropdown has at least one option."""
        version_select = self.page.locator(EvaluationsLocators.MODAL_VERSION_DROPDOWN)
        if version_select.is_visible():
            return version_select.locator("option").count() >= 1
        return False

    def get_modal_model_options(self) -> list[tuple[str, str]]:
        """Return [(value, text), ...] for every model option."""
        opts = self.page.locator(
            f"{EvaluationsLocators.MODAL_MODEL_DROPDOWN} option"
        ).all()
        return [(o.get_attribute("value") or "", o.inner_text().strip()) for o in opts]

    def get_modal_version_options(self) -> list[str]:
        """Return the visible text of every version option."""
        opts = self.page.locator(
            f"{EvaluationsLocators.MODAL_VERSION_DROPDOWN} option"
        ).all()
        return [o.inner_text().strip() for o in opts]

    def select_model_by_index(self, index: int = 1) -> None:
        """Select a model by option index (index 0 is 'New AI Model'; real models from 1)."""
        model_select = self.page.locator(EvaluationsLocators.MODAL_MODEL_DROPDOWN)
        model_select.wait_for(state="visible", timeout=self.timeout)
        opts = model_select.locator("option")
        if opts.count() > index:
            val = opts.nth(index).get_attribute("value")
            if val:
                model_select.select_option(value=val)
                self.page.wait_for_timeout(500)

    # Excluded from random selection: 'New AI Model' is the ghost placeholder
    # created by the CDS-002 "Add New AI Model" bug (empty metadata, no working
    # access method); 'xAI: Grok 4.1 Fast' is deprecated on the platform.
    EXCLUDED_MODEL_NAMES = {"New AI Model", "xAI: Grok 4.1 Fast"}

    def select_random_valid_model_and_version(self) -> str:
        """Select a random model, excluding 'New AI Model' and deprecated 'xAI: Grok 4.1 Fast'.

        Returns the selected model's display text (useful for logging/assertions).
        Falls back to index 1 if every option is excluded or the list is empty.
        """
        import random

        options = self.get_modal_model_options()
        valid = [
            i for i, (_, text) in enumerate(options)
            if text.strip() not in self.EXCLUDED_MODEL_NAMES
        ]
        if not valid:
            self.select_model_by_index(1)
            return options[1][1] if len(options) > 1 else ""
        idx = random.choice(valid)
        self.select_model_by_index(idx)
        return options[idx][1]

    def select_first_model_and_version(self) -> None:
        """Select a random valid model (skips 'New AI Model' and deprecated 'xAI: Grok 4.1 Fast')."""
        self.select_random_valid_model_and_version()

    def get_modal_eval_name(self) -> str:
        """Return the current value of the evaluation-name input in the modal."""
        loc = self.page.locator(EvaluationsLocators.MODAL_EVAL_NAME_INPUT)
        loc.wait_for(state="visible", timeout=self.timeout)
        return loc.input_value()

    def set_modal_eval_name(self, name: str) -> None:
        """Replace the evaluation name in the modal's step-1 input."""
        loc = self.page.locator(EvaluationsLocators.MODAL_EVAL_NAME_INPUT)
        loc.wait_for(state="visible", timeout=self.timeout)
        loc.fill(name)

    def select_evaluation_method(self, method: str = "bulk") -> None:
        """Select the evaluation-method radio in step 1: 'bulk' or 'manual' (Playground)."""
        self.page.locator(
            f"input[name='evaluationMethod'][value='{method}']"
        ).click()

    def is_method_selected(self, method: str) -> bool:
        """Return True if the given evaluation-method radio is checked."""
        return self.page.locator(
            f"input[name='evaluationMethod'][value='{method}']"
        ).is_checked()

    def click_modal_next(self) -> NewEvaluationPage:
        """Click 'Next' in step 1 of the modal to advance to step 2."""
        loc = self.page.locator(EvaluationsLocators.MODAL_NEXT_BUTTON).first
        loc.wait_for(state="visible", timeout=self.timeout)
        loc.click()
        try:
            self.page.locator(EvaluationsLocators.MODAL_STEP2_HEADING).first.wait_for(
                state="visible", timeout=15_000
            )
        except Exception:
            pass
        return self

    def click_modal_back(self) -> NewEvaluationPage:
        """Click 'Back' inside the modal (step 2 → step 1, or step 1 → close)."""
        loc = self.page.locator(EvaluationsLocators.MODAL_BACK_BUTTON).first
        loc.wait_for(state="visible", timeout=self.timeout)
        loc.click()
        self.page.wait_for_timeout(500)
        return self

    def select_evaluator_type_in_modal(self, eval_type: str = "technical") -> None:
        """Select the evaluator-type radio in step 2 (technical/domain/cultural)."""
        value_map = {
            "technical": EvaluationsLocators.MODAL_EVALUATOR_TECHNICAL,
            "domain": EvaluationsLocators.MODAL_EVALUATOR_DOMAIN,
            "cultural": EvaluationsLocators.MODAL_EVALUATOR_CULTURAL,
        }
        sel = value_map.get(eval_type.lower(), value_map["technical"])
        self.page.locator(sel).first.check()

    def get_checked_evaluator_type(self) -> str | None:
        """Return the value (Technical/Domain/Cultural) of the checked step-2 radio."""
        radios = self.page.locator(EvaluationsLocators.MODAL_EVALUATOR_TYPE_RADIO).all()
        for r in radios:
            if r.is_checked():
                return r.get_attribute("value")
        return None

    def fill_modal_objective(self, objective: str) -> None:
        """Fill the required objective textarea in modal step 2.

        Uses real keyboard events — the Start button's enable-validation only
        fires on keystrokes (verified live 2026-07-02: fill()/blur never
        enables it, press_sequentially does). Clearing likewise needs
        select-all + Backspace key events.
        """
        ta = self.page.locator(EvaluationsLocators.MODAL_OBJECTIVE_TEXTAREA).first
        ta.wait_for(state="visible", timeout=self.timeout)
        ta.click()
        self.page.keyboard.press("ControlOrMeta+a")
        self.page.keyboard.press("Backspace")
        if objective:
            ta.press_sequentially(objective, delay=5)
        self.page.wait_for_timeout(300)

    def get_modal_objective(self) -> str:
        """Return the current objective textarea value in modal step 2."""
        ta = self.page.locator(EvaluationsLocators.MODAL_OBJECTIVE_TEXTAREA).first
        ta.wait_for(state="visible", timeout=self.timeout)
        return ta.input_value()

    def is_start_evaluation_enabled(self, settle_ms: int = 2_000) -> bool:
        """Return True if the 'Start Evaluation' button in step 2 is enabled.

        The button uses aria-disabled (Radix) as well as the disabled attribute.
        The enabled state updates asynchronously after typing in the objective,
        so poll briefly (settle_ms) before reporting disabled.
        """
        btn = self.page.locator(self.MODAL_START_BUTTON).first

        def _enabled() -> bool:
            if not btn.is_visible():
                return False
            if btn.get_attribute("aria-disabled") == "true":
                return False
            return btn.is_enabled()

        polls = max(1, settle_ms // 250)
        for _ in range(polls):
            if _enabled():
                return True
            self.page.wait_for_timeout(250)
        return _enabled()

    def click_modal_start(self) -> NewEvaluationPage:
        """Click 'Start Evaluation' in step 2 and wait for the wizard navigation.

        The Radix dialog overlay keeps intercepting pointer events until the
        dialog fully closes, so wait for hidden BEFORE any further clicks.
        """
        loc = self.page.locator(self.MODAL_START_BUTTON).first
        loc.wait_for(state="visible", timeout=self.timeout)
        loc.click()
        try:
            self.page.locator(EvaluationsLocators.MODAL_DIALOG).first.wait_for(
                state="hidden", timeout=20_000
            )
        except Exception:
            pass
        try:
            self.page.wait_for_url("**auditId=**", timeout=self.timeout)
        except Exception:
            self.page.wait_for_timeout(2_000)
        return self

    def start_evaluation_from_modal(
        self,
        model_index: int | None = None,
        method: str = "bulk",
        eval_type: str = "technical",
        objective: str = "Automated test evaluation objective",
        name: str | None = None,
    ) -> NewEvaluationPage:
        """Complete both modal steps and land on the single-page wizard.

        Precondition: the modal is already open (call click_new_evaluation()).

        `model_index`: pass an explicit dropdown index to pin a specific model
        (e.g. for a test asserting on a particular model's name). Leave as
        None (default) to pick a random valid model, excluding the 'New AI
        Model' placeholder and deprecated 'xAI: Grok 4.1 Fast'.
        """
        if model_index is None:
            self.select_random_valid_model_and_version()
        else:
            self.select_model_by_index(model_index)
        if name is not None:
            self.set_modal_eval_name(name)
        self.select_evaluation_method(method)
        self.click_modal_next()
        self.select_evaluator_type_in_modal(eval_type)
        self.fill_modal_objective(objective)
        self.click_modal_start()
        return self

    def click_modal_cancel(self) -> None:
        """Dismiss the modal via its close control, falling back to Escape."""
        try:
            loc = self.page.locator(self.MODAL_CANCEL_BUTTON).first
            loc.wait_for(state="visible", timeout=10_000)
            loc.click()
            self.page.locator(self.MODAL_TITLE).first.wait_for(
                state="hidden", timeout=8_000
            )
        except Exception:
            pass
        if self.is_visible(self.MODAL_TITLE, timeout=1_000):
            self.page.keyboard.press("Escape")
            try:
                self.page.locator(self.MODAL_TITLE).first.wait_for(
                    state="hidden", timeout=8_000
                )
            except Exception:
                pass

    # ── Wizard — general (single-page layout) ─────────────────────────────────

    def wait_for_wizard_loaded(self, timeout: int = 90_000) -> bool:
        """Wait until the single-page wizard has fully hydrated.

        The wizard shows a 'Loading evaluation details...' curtain for ~20s on
        dev, and content can flash empty in between. Poll until the curtain is
        gone AND the Evaluation Overview card is rendered. Returns True on
        success, False on timeout (callers assert).
        """
        deadline_polls = max(1, timeout // 3_000)
        for _ in range(deadline_polls):
            try:
                body = self.page.locator("body").inner_text()
            except Exception:
                body = ""
            if (
                "Loading evaluation details" not in body
                and "Evaluation Overview" in body
            ):
                return True
            self.page.wait_for_timeout(3_000)
        return False

    def is_wizard_visible(self) -> bool:
        """Return True if the single-page wizard is open (Evaluation Overview card rendered)."""
        return self.is_visible(EvaluationsLocators.WIZARD_OVERVIEW_HEADING, timeout=5_000)

    def get_overview_field(self, label: str) -> str | None:
        """Read a field from the Evaluation Overview card by its label.

        The card renders lines like 'Scope : Healthcare' / 'Mode : Bulk
        Evaluation'. Returns the value part, or None if the label is absent.
        """
        try:
            body = self.page.locator("body").inner_text()
        except Exception:
            return None
        for line in body.split("\n"):
            line = line.strip()
            key, sep, value = line.partition(":")
            # Exact label match (not prefix) so 'Mode' doesn't hit 'Modules : --'.
            if sep and key.strip().lower() == label.lower():
                return value.strip()
        return None

    def click_back_to_list(self) -> None:
        """Click 'Back to List' in the wizard header and wait for the list page."""
        self.click(EvaluationsLocators.WIZARD_BACK_TO_LIST)
        try:
            self.page.wait_for_function(
                "() => !window.location.search.includes('auditId=')",
                timeout=self.timeout,
            )
        except Exception:
            self.wait_for_load("domcontentloaded")
        self.page.wait_for_timeout(1_000)

    # ── Wizard — Bulk workspace (test-case source) ────────────────────────────

    def select_prompt_library_source(self) -> None:
        """Choose the 'Select a prompt library' test-case source."""
        self.page.locator(
            EvaluationsLocators.WIZARD_PROMPT_LIBRARY_OPTION
        ).first.click()
        self.page.wait_for_timeout(500)

    def select_own_prompts_source(self) -> None:
        """Choose the 'Add your own prompts' test-case source."""
        self.page.locator(
            EvaluationsLocators.WIZARD_OWN_PROMPTS_OPTION
        ).first.click()
        self.page.wait_for_timeout(500)

    def is_max_test_cases_note_visible(self) -> bool:
        """Return True if the 'Maximum test cases…' note is rendered."""
        return self.is_visible(
            EvaluationsLocators.WIZARD_MAX_TEST_CASES_NOTE, timeout=3_000
        )

    def is_submodule_prompt_visible(self) -> bool:
        """Return True if 'Select sub-modules from dropdown' is shown (module checked)."""
        return self.is_visible(EvaluationsLocators.WIZARD_SUBMODULE_PROMPT, timeout=3_000)

    def select_submodules(self, count: int = 1) -> int:
        """Open the sub-module combobox and select up to `count` options.

        Required before Run Evaluation can be enabled — checking a top-level
        module alone is not enough. Returns the number of options actually
        selected (0 if the combobox never appeared, e.g. no module checked yet).
        """
        trigger = self.page.locator(EvaluationsLocators.WIZARD_SUBMODULE_COMBOBOX_TRIGGER).first
        if not trigger.count():
            return 0
        trigger.click(timeout=10_000)
        self.page.wait_for_timeout(800)
        options = self.page.locator(EvaluationsLocators.WIZARD_SUBMODULE_OPTION)
        n = min(options.count(), count)
        for i in range(n):
            options.nth(i).click()
            self.page.wait_for_timeout(300)
        self.page.keyboard.press("Escape")
        self.page.wait_for_timeout(300)
        return n

    def select_first_prompt_library(self) -> bool:
        """Click the first prompt-library row's radio input (not its title link).

        Must be called after `select_prompt_library_source()`. Returns False if
        no library rows are available (e.g. still loading, or none exist).
        """
        radio = self.page.locator(EvaluationsLocators.WIZARD_PROMPT_LIBRARY_RADIO).first
        if not radio.count():
            return False
        radio.click(timeout=10_000)
        self.page.wait_for_timeout(1_000)
        return True

    def configure_bulk_workspace_minimal(self, module: str = "hallucination") -> bool:
        """Configure the minimum required to enable Run Evaluation: check a
        module, pick a sub-module, choose the prompt-library source, and
        select the first available library. Returns True if Run Evaluation
        ends up enabled.
        """
        self.check_module(module)
        self.page.wait_for_timeout(500)
        self.select_submodules(count=1)
        self.select_prompt_library_source()
        self.page.wait_for_timeout(1_500)
        self.select_first_prompt_library()
        return self.is_run_evaluation_button_enabled()

    def is_run_evaluation_library_error_visible(self) -> bool:
        """Return True if 'Please select a prompt library…' error is shown."""
        return self.is_visible(
            EvaluationsLocators.RUN_EVALUATION_LIBRARY_ERROR, timeout=3_000
        )

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

    def is_cancel_evaluation_enabled(self) -> bool:
        """Return True if the wizard header 'Cancel' button is enabled.

        On the redesigned page the Cancel button (styles_cancelAuditButton)
        cancels a RUNNING audit — it is aria-disabled for a fresh DRAFT.
        Use click_back_to_list() to leave a draft.
        """
        btn = self.page.locator(self.WIZARD_CANCEL_EVALUATION).first
        if not btn.is_visible():
            return False
        if btn.get_attribute("aria-disabled") == "true":
            return False
        return btn.is_enabled()

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
        """Open the first DRAFT evaluation from the list.

        The navigable element is the <a> inside the first cell — clicking the
        <tr> body does NOT navigate (confirmed live 2026-07-02).
        """
        link = self.page.locator(EvaluationsLocators.DRAFT_ROW_LINK).first
        link.wait_for(state="visible", timeout=self.timeout)
        link.click()
        try:
            self.page.wait_for_url("**auditId=**", timeout=self.timeout)
        except Exception:
            self.wait_for_load("domcontentloaded")

    def click_first_completed_row(self) -> None:
        """Open the first COMPLETED evaluation from the list (via its name anchor)."""
        link = self.page.locator(EvaluationsLocators.COMPLETED_ROW_LINK).first
        link.wait_for(state="visible", timeout=self.timeout)
        link.click()
        self.wait_for_load("domcontentloaded")

    def get_first_draft_href(self) -> str | None:
        """Return the href of the first DRAFT row's name anchor (or None)."""
        link = self.page.locator(EvaluationsLocators.DRAFT_ROW_LINK).first
        try:
            link.wait_for(state="visible", timeout=self.timeout)
            return link.get_attribute("href")
        except Exception:
            return None

    def get_first_completed_href(self) -> str | None:
        """Return the href of the first COMPLETED row's name anchor (or None)."""
        link = self.page.locator(EvaluationsLocators.COMPLETED_ROW_LINK).first
        try:
            link.wait_for(state="visible", timeout=self.timeout)
            return link.get_attribute("href")
        except Exception:
            return None

    def draft_row_href_contains_new(self) -> bool:
        """Return True if the first DRAFT row's anchor links to /evaluations/new?auditId=…"""
        href = self.get_first_draft_href()
        return href is not None and "/evaluations/new" in href and "auditId=" in href

    def completed_row_href_excludes_new(self) -> bool:
        """Return True if the first COMPLETED row's anchor links to /evaluations/{id} (not /new)."""
        href = self.get_first_completed_href()
        return href is not None and "/evaluations/" in href and "/new" not in href

    # ── Composite helpers (multi-step) ─────────────────────────────────────────

    def open_new_evaluation_wizard(
        self,
        method: str = "bulk",
        eval_type: str = "technical",
        objective: str = "Automated test evaluation objective",
    ) -> NewEvaluationPage:
        """Full flow: list → New Evaluation → both modal steps → hydrated wizard.

        After 'Start Evaluation' the platform navigates to
        /evaluations/new?auditId={id}; the page hydrates behind a
        'Loading evaluation details...' curtain (~20s on dev).
        """
        self.go_to_evaluations_list()
        self.click_new_evaluation()
        assert self.is_modal_visible(), (
            "'Start an Evaluation' modal did not appear — platform may be unavailable or slow"
        )
        self.start_evaluation_from_modal(
            method=method, eval_type=eval_type, objective=objective
        )
        self.wait_for_wizard_loaded()
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
