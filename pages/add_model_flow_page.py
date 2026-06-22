"""Page object for the Add Model cross-platform flow (ParakhAI → CivicDataSpace)."""

from locators.add_model_flow_locators import AddModelFlowLocators
from pages.base_page import BasePage
from utils.config import Config


class AddModelFlowPage(BasePage):
    def go_to_parakh_models(self, org_id: int = 1) -> None:
        self.navigate(Config.url(f"/dashboard/ai-maker/{org_id}/ai-models"))
        self.page.wait_for_load_state("domcontentloaded")

    def click_add_new_model(self) -> None:
        btn = self.page.locator(AddModelFlowLocators.ADD_NEW_MODEL_BUTTON)
        btn.first.click()
        self.page.wait_for_timeout(1000)

    def get_redirect_dialog(self):
        return self.page.locator(AddModelFlowLocators.REDIRECT_DIALOG)

    def confirm_redirect(self) -> None:
        self.page.locator(AddModelFlowLocators.REDIRECT_CONFIRM_BTN).first.click()

    def cancel_redirect(self) -> None:
        self.page.locator(AddModelFlowLocators.REDIRECT_CANCEL_BTN).first.click()

    def go_to_cds_ai_models(self) -> None:
        self.navigate(Config.cds_url("/en/manage/ai-models"))
        self.page.wait_for_load_state("domcontentloaded")

    def go_to_cds_new_model_editor(self) -> None:
        self.navigate(Config.cds_url("/en/manage/ai-models/new"))
        self.page.wait_for_load_state("domcontentloaded")
        self.page.wait_for_timeout(2000)

    def navigate_wizard_step(self, step: int) -> None:
        self.navigate(Config.cds_url(f"/en/manage/ai-models/new?step={step}"))
        self.page.wait_for_load_state("domcontentloaded")

    def inject_console_error_collector(self) -> None:
        self.page.evaluate("""() => {
            window._consoleErrors = [];
            const orig = console.error;
            console.error = function(...args) {
                window._consoleErrors.push(args.join(' '));
                orig.apply(console, args);
            };
        }""")

    def get_console_errors(self) -> list:
        return self.page.evaluate("""() => {
            if (!window._consoleErrors) return [];
            return window._consoleErrors;
        }""")
