"""
Page object for the AI Models list and model detail pages.
List URL  : /dashboard/ai-maker/{org_id}/ai-models
Detail URL: /dashboard/ai-maker/{org_id}/ai-models/{model_id}
"""

from playwright.sync_api import Page

from locators.models_locators import ModelsLocators
from pages.base_page import BasePage
from utils.config import Config

CIVICDATALAB_ORG_ID = 1
SARVAM_MODEL_ID = 22


class ModelsPage(BasePage):
    """Models list and model detail page interactions."""

    # Expose locators
    PAGE_HEADING = ModelsLocators.PAGE_HEADING
    SEARCH_INPUT = ModelsLocators.SEARCH_INPUT
    ADD_FILTERS_BUTTON = ModelsLocators.ADD_FILTERS_BUTTON
    MODEL_CARD = ModelsLocators.MODEL_CARD
    START_EVALUATION_LINK = ModelsLocators.START_EVALUATION_LINK
    INVITE_AUDITORS_LINK = ModelsLocators.INVITE_AUDITORS_LINK
    PAST_EVALUATIONS_HEADING = ModelsLocators.PAST_EVALUATIONS_HEADING
    DOWNLOAD_REPORT_BUTTON = ModelsLocators.PAGINATION

    def __init__(self, page: Page, org_id: int = CIVICDATALAB_ORG_ID) -> None:
        super().__init__(page)
        self.org_id = org_id
        self.list_url = Config.url(f"/dashboard/ai-maker/{org_id}/ai-models")

    # ── Navigation ─────────────────────────────────────────────────────────────

    def go_to_models_list(self) -> "ModelsPage":
        self.navigate(self.list_url)
        self.wait_for_load("domcontentloaded")
        return self

    def go_to_model_detail(self, model_id: int = SARVAM_MODEL_ID) -> "ModelsPage":
        self.navigate(Config.url(f"/dashboard/ai-maker/{self.org_id}/ai-models/{model_id}"))
        self.wait_for_load("domcontentloaded")
        return self

    # ── Models list ────────────────────────────────────────────────────────────

    def is_models_list_visible(self) -> bool:
        return self.is_visible(self.PAGE_HEADING)

    def get_model_card_count(self) -> int:
        return self.page.locator(self.MODEL_CARD).count()

    def search_model(self, query: str) -> None:
        self.type_text(self.SEARCH_INPUT, query)
        self.page.wait_for_timeout(500)  # debounce

    def clear_search(self) -> None:
        self.type_text(self.SEARCH_INPUT, "")
        self.page.wait_for_timeout(500)

    def is_model_visible(self, model_name_selector: str) -> bool:
        return self.is_visible(model_name_selector)

    def click_model(self, model_name_selector: str) -> None:
        self.click(model_name_selector)
        self.wait_for_load("domcontentloaded")

    def click_first_model(self) -> None:
        self.page.locator(self.MODEL_CARD).first.click()
        self.wait_for_load("domcontentloaded")

    # ── Model detail ────────────────────────────────────────────────────────────

    def is_about_section_visible(self) -> bool:
        return self.is_visible(ModelsLocators.ABOUT_HEADING)

    def is_versions_section_visible(self) -> bool:
        return self.is_visible(ModelsLocators.VERSIONS_HEADING)

    def is_primary_badge_visible(self) -> bool:
        return self.is_visible(ModelsLocators.PRIMARY_BADGE)

    def is_start_evaluation_visible(self) -> bool:
        return self.is_visible(self.START_EVALUATION_LINK)

    def is_invite_auditors_visible(self) -> bool:
        return self.is_visible(self.INVITE_AUDITORS_LINK)

    def is_past_evaluations_visible(self) -> bool:
        return self.is_visible(self.PAST_EVALUATIONS_HEADING)

    def get_past_evaluation_row_count(self) -> int:
        return self.page.locator(ModelsLocators.PAST_EVAL_ROW).count()

    def is_pagination_visible(self) -> bool:
        return self.is_visible(ModelsLocators.ROWS_PER_PAGE)

    def click_start_evaluation(self) -> None:
        self.click(self.START_EVALUATION_LINK)
        self.wait_for_load("domcontentloaded")

    def get_model_title(self) -> str:
        return self.get_text(ModelsLocators.DETAIL_MODEL_TITLE)
