"""
Page object for the Prompt Libraries page.
URL: /dashboard/ai-maker/{org_id}/prompt-libraries
"""

from playwright.sync_api import Page

from locators.prompt_libraries_locators import PromptLibrariesLocators
from pages.base_page import BasePage
from utils.config import Config

CIVICDATALAB_ORG_ID = 1


class PromptLibrariesPage(BasePage):
    """Prompt Libraries list page interactions."""

    PAGE_HEADING = PromptLibrariesLocators.PAGE_HEADING
    SEARCH_INPUT = PromptLibrariesLocators.SEARCH_INPUT
    ADD_FILTERS_BUTTON = PromptLibrariesLocators.ADD_FILTERS_BUTTON
    LIBRARY_CARD = PromptLibrariesLocators.LIBRARY_CARD
    CATEGORY_AGRICULTURE = PromptLibrariesLocators.CATEGORY_AGRICULTURE
    CATEGORY_HEALTHCARE = PromptLibrariesLocators.CATEGORY_HEALTHCARE
    CATEGORY_GENERAL = PromptLibrariesLocators.CATEGORY_GENERAL

    def __init__(self, page: Page, org_id: int = CIVICDATALAB_ORG_ID) -> None:
        super().__init__(page)
        self.org_id = org_id
        self.url = Config.url(f"/dashboard/ai-maker/{org_id}/prompt-libraries")

    def go_to_prompt_libraries(self) -> "PromptLibrariesPage":
        self.navigate(self.url)
        self.wait_for_app_ready()
        self.skip_if_redirected_to_home("/prompt-libraries")
        return self

    def is_page_loaded(self) -> bool:
        return self.is_visible(self.PAGE_HEADING)

    def get_library_card_count(self) -> int:
        return self.page.locator(self.LIBRARY_CARD).count()

    def search_library(self, query: str) -> None:
        self.type_text(self.SEARCH_INPUT, query)
        self.page.wait_for_timeout(500)

    def clear_search(self) -> None:
        self.type_text(self.SEARCH_INPUT, "")
        self.page.wait_for_timeout(500)

    def is_category_badge_visible(self, category: str) -> bool:
        selector_map = {
            "agriculture": self.CATEGORY_AGRICULTURE,
            "healthcare": self.CATEGORY_HEALTHCARE,
            "general": self.CATEGORY_GENERAL,
        }
        sel = selector_map.get(category.lower())
        return self.is_visible(sel) if sel else False

    def get_agriculture_card_count(self) -> int:
        return self.page.locator(self.CATEGORY_AGRICULTURE).count()

    def get_healthcare_card_count(self) -> int:
        return self.page.locator(self.CATEGORY_HEALTHCARE).count()

    def is_library_visible(self, library_selector: str) -> bool:
        return self.is_visible(library_selector)

    def is_add_filters_visible(self) -> bool:
        return self.is_visible(self.ADD_FILTERS_BUTTON)
