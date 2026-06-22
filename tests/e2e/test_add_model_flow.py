"""
Tests for the Add Model cross-platform flow (ParakhAI → CivicDataSpace).

Issues covered:
  VALID-001  Step 1→2 wizard skips required field validation
  CDS-001    JS SyntaxError (appendChild) on every editor page load
  CDS-002    Ghost model created before any form input
  CDS-003    "All Changes Saved" indicator shows with empty required fields
  CDS-004    ?tab=registered URL param from ParakhAI redirect silently ignored
  CDS-005    Quill bullet format not registered — console error + button fails
  SEC-004    API key field missing autocomplete="off"

TestAddModelRedirect covers the ParakhAI side of the flow.
TestCDSAddModelEditor covers CivicDataSpace-specific issues.

Tests auto-skip when CDS_URL is unreachable (CivicDataSpace not running).
Both platforms share Keycloak, so TEST_EMAIL_1/TEST_PASSWORD_1 applies to both.
"""

import pytest
import requests as _requests
from playwright.sync_api import Page

from locators.add_model_flow_locators import AddModelFlowLocators
from pages.add_model_flow_page import AddModelFlowPage
from utils.config import Config

pytestmark = [pytest.mark.e2e, pytest.mark.auth, pytest.mark.regression]

CDS_BASE = Config.CDS_URL


def _cds_reachable() -> bool:
    try:
        r = _requests.get(CDS_BASE, timeout=8, allow_redirects=True)
        return r.status_code < 500
    except Exception:
        return False


def skip_if_cds_unreachable() -> None:
    if not _cds_reachable():
        pytest.skip(f"CivicDataSpace ({CDS_BASE}) unreachable — skipping CDS tests")


class TestAddModelRedirect:
    """Tests for the ParakhAI side of the Add Model cross-platform redirect."""

    def test_add_new_model_button_visible_on_models_page(self, authenticated_page_fast: Page):
        flow = AddModelFlowPage(authenticated_page_fast)
        flow.go_to_parakh_models()
        authenticated_page_fast.wait_for_timeout(2000)
        btn = authenticated_page_fast.locator(AddModelFlowLocators.ADD_NEW_MODEL_BUTTON)
        assert btn.count() > 0, "Add A New Model button must be present on the AI Models page"

    def test_add_model_button_opens_redirect_dialog(self, authenticated_page_fast: Page):
        flow = AddModelFlowPage(authenticated_page_fast)
        flow.go_to_parakh_models()
        authenticated_page_fast.wait_for_timeout(2000)
        btn = authenticated_page_fast.locator(AddModelFlowLocators.ADD_NEW_MODEL_BUTTON)
        if btn.count() == 0:
            pytest.skip("Add New Model button not found — platform may have changed")
        btn.first.click()
        authenticated_page_fast.wait_for_timeout(1500)
        dialog = authenticated_page_fast.locator(AddModelFlowLocators.REDIRECT_DIALOG)
        assert dialog.count() > 0, (
            "Clicking 'Add A New Model' must open a redirect confirmation dialog before "
            "navigating away. If it navigates immediately, ghost model creation (CDS-002) "
            "may occur without user intent."
        )

    @pytest.mark.xfail(reason="CDS-004: redirect URL includes ?tab=registered which CivicDataSpace silently ignores — known bug")
    def test_cds004_redirect_url_has_no_invalid_tab_param(self, authenticated_page_fast: Page):
        """CDS-004: The redirect to CivicDataSpace should not include ?tab=registered.

        CivicDataSpace AI Models page has no 'registered' tab — the param is silently
        ignored. Expected fix: remove or correctly map the param on the ParakhAI side.
        """
        flow = AddModelFlowPage(authenticated_page_fast)
        flow.go_to_parakh_models()
        authenticated_page_fast.wait_for_timeout(2000)
        btn = authenticated_page_fast.locator(AddModelFlowLocators.ADD_NEW_MODEL_BUTTON)
        if btn.count() == 0:
            pytest.skip("Add New Model button not found")
        btn.first.click()
        authenticated_page_fast.wait_for_timeout(1500)
        confirm = authenticated_page_fast.locator(AddModelFlowLocators.REDIRECT_CONFIRM_BTN)
        if confirm.count() == 0:
            pytest.skip("Redirect confirm button not found")
        with authenticated_page_fast.expect_popup() as popup_info:
            confirm.first.click()
        popup = popup_info.value
        popup.wait_for_load_state("domcontentloaded")
        url = popup.url
        popup.close()
        assert "tab=registered" not in url, (
            f"CDS-004: Redirect URL contains '?tab=registered' which CivicDataSpace silently "
            f"ignores (no such tab exists). URL: {url}"
        )


class TestCDSAddModelEditor:
    """CivicDataSpace Add Model editor issues found during 2026-06-22 MCP exploration."""

    @pytest.fixture(autouse=True)
    def check_cds_reachable(self):
        skip_if_cds_unreachable()

    def test_cds001_no_js_syntax_error_on_editor_page_load(self, page: Page):
        """CDS-001: The model editor must not throw a JS SyntaxError on load.

        MCP found: SyntaxError: Failed to execute 'appendChild' on 'Node':
        missing ) after argument list — fires on every editor page load.
        """
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(Config.cds_url("/en/manage/ai-models"), wait_until="domcontentloaded", timeout=20000)
        page.wait_for_timeout(3000)
        syntax_errors = [e for e in errors if "SyntaxError" in e or "appendChild" in e]
        assert not syntax_errors, (
            "CDS-001: JS SyntaxError(s) on editor page load:\n" + "\n".join(syntax_errors)
        )

    @pytest.mark.xfail(reason="CDS-001: JS SyntaxError 'appendChild missing )' fires on every load — known bug")
    def test_cds001_editor_has_no_console_errors_on_load(self, page: Page):
        """CDS-001: Editor page should load without any JS console errors."""
        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        page.goto(Config.cds_url("/en/manage/ai-models"), wait_until="domcontentloaded", timeout=20000)
        page.wait_for_timeout(3000)
        assert not console_errors, f"Console errors on CDS editor load: {console_errors}"

    @pytest.mark.xfail(reason="CDS-004: ?tab=registered param silently ignored on CivicDataSpace AI Models — known bug")
    def test_cds004_registered_tab_param_is_handled(self, page: Page):
        """CDS-004: Navigating to /ai-models?tab=registered must show a 'Registered' tab.

        The ParakhAI redirect appends ?tab=registered but CivicDataSpace has no such tab.
        """
        page.goto(
            Config.cds_url("/en/manage/ai-models?tab=registered"),
            wait_until="domcontentloaded",
            timeout=20000,
        )
        page.wait_for_timeout(2000)
        assert not page.url.endswith("404"), "CDS AI Models page returned 404"
        tab_area = page.locator("[role='tablist'], [role='tab']")
        if tab_area.count() == 0:
            pytest.skip("No tab elements found — page structure may have changed")
        tab_texts = tab_area.all_text_contents()
        assert any("registered" in t.lower() for t in tab_texts), (
            f"CDS-004: ?tab=registered is silently ignored — no 'Registered' tab found. "
            f"Tab texts: {tab_texts}"
        )

    @pytest.mark.xfail(reason="CDS-002: Ghost model created before form input — known bug")
    def test_cds002_add_model_does_not_create_db_record_before_form(self, page: Page):
        """CDS-002: Clicking 'Add New AI Model' must not create a DB record before form submit.

        MCP found that clicking the button immediately creates a draft in the database
        (visible in the list) before the user has filled in any fields.
        """
        page.goto(Config.cds_url("/en/manage/ai-models"), wait_until="domcontentloaded", timeout=20000)
        page.wait_for_timeout(2000)
        count_locator = page.locator(
            "[data-testid='model-count'], .model-count, .total-count"
        )
        initial_count = count_locator.first.text_content() if count_locator.count() > 0 else None
        add_btn = page.locator(AddModelFlowLocators.CDS_ADD_MODEL_BTN)
        if add_btn.count() == 0:
            pytest.skip("CDS 'Add New AI Model' button not found — page may require auth")
        add_btn.first.click()
        page.wait_for_timeout(1500)
        page.goto(Config.cds_url("/en/manage/ai-models"), wait_until="domcontentloaded", timeout=20000)
        page.wait_for_timeout(1500)
        new_count = count_locator.first.text_content() if count_locator.count() > 0 else None
        assert initial_count == new_count, (
            f"CDS-002: Model count changed from '{initial_count}' to '{new_count}' immediately "
            "after clicking 'Add New AI Model' without submitting any form data. Ghost model "
            "was created before user input."
        )

    @pytest.mark.xfail(reason="CDS-003: 'All Changes Saved' shows with empty required fields — known bug")
    def test_cds003_autosave_indicator_not_shown_with_empty_fields(self, page: Page):
        """CDS-003: 'All Changes Saved' must not appear when required metadata fields are empty.

        MCP found the autosave indicator fires on draft record existence, not field
        completeness — misleads users into thinking the model is ready to publish.
        """
        page.goto(Config.cds_url("/en/manage/ai-models/new"), wait_until="domcontentloaded", timeout=25000)
        page.wait_for_timeout(3000)
        autosave = page.locator(AddModelFlowLocators.CDS_AUTOSAVE_INDICATOR)
        if autosave.count() == 0:
            pytest.skip("Autosave indicator not found — check locator or page requires auth")
        page.wait_for_timeout(2000)
        title_input = page.locator(AddModelFlowLocators.CDS_STEP1_TITLE_INPUT)
        title_value = title_input.first.input_value() if title_input.count() > 0 else ""
        if title_value.strip():
            pytest.skip("Model editor has pre-filled title — cannot test empty-field autosave")
        assert not autosave.first.is_visible(), (
            "CDS-003: 'All Changes Saved' indicator is visible even though all required "
            "metadata fields are empty. Misleads users about form completeness."
        )

    @pytest.mark.xfail(reason="VALID-001: Step 1→2 wizard navigation skips required field validation — known bug")
    def test_valid001_wizard_step1_to_step2_requires_title(self, page: Page):
        """VALID-001: Advancing from Step 1 to Step 2 must validate that Title is not empty.

        MCP found that clicking Next with an empty Title successfully advances to Step 2
        with no validation error shown.
        """
        page.goto(Config.cds_url("/en/manage/ai-models/new"), wait_until="domcontentloaded", timeout=25000)
        page.wait_for_timeout(3000)
        title_input = page.locator(AddModelFlowLocators.CDS_STEP1_TITLE_INPUT)
        if title_input.count() == 0:
            pytest.skip("Title input not found — page may require auth")
        if title_input.first.input_value().strip():
            title_input.first.fill("")
        next_btn = page.locator(AddModelFlowLocators.CDS_NEXT_BTN)
        if next_btn.count() == 0:
            pytest.skip("Next/Save & Continue button not found")
        next_btn.first.click()
        page.wait_for_timeout(1500)
        error_visible = page.locator(
            "[aria-invalid='true'], .field-error, [role='alert']:has-text('required'), "
            ".error-message, input:invalid"
        ).count() > 0
        still_on_step1 = "step=2" not in page.url and page.locator(
            "text=Step 2, [data-step='2'].active"
        ).count() == 0
        assert error_visible or still_on_step1, (
            "VALID-001: Clicking 'Next' with empty Title advanced to Step 2 with no validation "
            "error. Required field validation must block step progression."
        )

    @pytest.mark.xfail(reason="CDS-005: Quill bullet format not registered — console error on init")
    def test_cds005_quill_bullet_no_console_error(self, page: Page):
        """CDS-005: Quill editor must not log 'Cannot register bullet' on init.

        MCP found: Cannot register "bullet" specified in "formats" config — fires on init.
        """
        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        page.goto(Config.cds_url("/en/manage/ai-models/new"), wait_until="domcontentloaded", timeout=25000)
        page.wait_for_timeout(3000)
        quill_errors = [e for e in console_errors if "bullet" in e.lower() and "register" in e.lower()]
        assert not quill_errors, f"CDS-005: Quill bullet registration error: {quill_errors}"

    @pytest.mark.xfail(reason="CDS-005: Quill bullet button silently fails — known bug")
    def test_cds005_quill_bullet_button_activates(self, page: Page):
        """CDS-005: Clicking the Quill bullet list button must apply bullet formatting."""
        page.goto(Config.cds_url("/en/manage/ai-models/new"), wait_until="domcontentloaded", timeout=25000)
        page.wait_for_timeout(3000)
        bullet_btn = page.locator(AddModelFlowLocators.CDS_QUILL_BULLET_BTN)
        if bullet_btn.count() == 0:
            pytest.skip("Quill bullet button not found — editor may not be on this page")
        bullet_btn.first.click()
        page.wait_for_timeout(500)
        active_class = bullet_btn.first.get_attribute("class") or ""
        assert "ql-active" in active_class, (
            "CDS-005: Quill bullet button did not activate after click — the bullet format "
            "is not registered so the click has no effect."
        )

    @pytest.mark.xfail(reason="SEC-004: API key field has autocomplete='on' — known bug")
    def test_sec004_api_key_field_has_autocomplete_off(self, page: Page):
        """SEC-004: The API key input in 'Add New Access Method' dialog must have autocomplete='off'.

        MCP found autocomplete='on' (or no attribute) — allows browsers to store API keys.
        """
        page.goto(Config.cds_url("/en/manage/ai-models/new"), wait_until="domcontentloaded", timeout=25000)
        page.wait_for_timeout(3000)
        add_access_btn = page.locator(AddModelFlowLocators.CDS_ADD_ACCESS_METHOD_BTN)
        if add_access_btn.count() == 0:
            pytest.skip("Add Access Method button not found — may require Step 2 to be completed first")
        add_access_btn.first.click()
        page.wait_for_timeout(1000)
        api_key_input = page.locator(AddModelFlowLocators.CDS_API_KEY_INPUT)
        if api_key_input.count() == 0:
            pytest.skip("API key input not found in Add Access Method dialog")
        autocomplete = api_key_input.first.get_attribute("autocomplete") or "on"
        assert autocomplete in ("off", "new-password"), (
            f"SEC-004: API key field has autocomplete='{autocomplete}'. "
            "Must be 'off' or 'new-password' to prevent browsers from storing API keys."
        )
