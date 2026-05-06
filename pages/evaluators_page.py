"""
Page object for the Evaluators management page (AI Maker role).
URL: /dashboard/ai-maker/{org_id}/auditors
"""

from playwright.sync_api import Page

from locators.evaluators_locators import EvaluatorsLocators
from pages.base_page import BasePage
from utils.config import Config

CIVICDATALAB_ORG_ID = 1


class EvaluatorsPage(BasePage):
    """Evaluators management page — list, add, and remove evaluators."""

    PAGE_HEADING = EvaluatorsLocators.PAGE_HEADING
    PAGE_SUBHEADING = EvaluatorsLocators.PAGE_SUBHEADING
    ADD_EVALUATOR_BUTTON = EvaluatorsLocators.ADD_EVALUATOR_BUTTON
    TABLE = EvaluatorsLocators.TABLE
    TABLE_ROW = EvaluatorsLocators.TABLE_ROW
    REMOVE_BUTTON = EvaluatorsLocators.REMOVE_BUTTON

    def __init__(self, page: Page, org_id: int = CIVICDATALAB_ORG_ID) -> None:
        super().__init__(page)
        self.org_id = org_id
        self.url = Config.url(f"/dashboard/ai-maker/{org_id}/auditors")

    def go_to_evaluators(self) -> "EvaluatorsPage":
        self.navigate(self.url)
        self.wait_for_load("domcontentloaded")
        return self

    def is_page_loaded(self) -> bool:
        return self.is_visible(self.PAGE_HEADING)

    def is_subheading_visible(self) -> bool:
        return self.is_visible(self.PAGE_SUBHEADING)

    def is_table_visible(self) -> bool:
        return self.is_visible(self.TABLE)

    def get_evaluator_row_count(self) -> int:
        return self.page.locator(self.TABLE_ROW).count()

    def is_add_evaluator_button_visible(self) -> bool:
        return self.is_visible(self.ADD_EVALUATOR_BUTTON)

    def is_evaluator_present(self, evaluator_selector: str) -> bool:
        return self.is_visible(evaluator_selector)

    def are_column_headers_visible(self) -> bool:
        return all([
            self.is_visible(EvaluatorsLocators.TABLE_HEADER_USERNAME),
            self.is_visible(EvaluatorsLocators.TABLE_HEADER_EMAIL),
            self.is_visible(EvaluatorsLocators.TABLE_HEADER_NAME),
            self.is_visible(EvaluatorsLocators.TABLE_HEADER_JOINED),
            self.is_visible(EvaluatorsLocators.TABLE_HEADER_ACTIONS),
        ])

    def get_remove_button_count(self) -> int:
        return self.page.locator(self.REMOVE_BUTTON).count()
