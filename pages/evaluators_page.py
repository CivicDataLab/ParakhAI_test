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
    """Evaluators management page — list, add, and remove evaluators.

    The page renders evaluators as a card grid (one card per evaluator). Tests
    anchor on the per-card "Remove" action, which is unique per card.
    """

    PAGE_HEADING = EvaluatorsLocators.PAGE_HEADING
    PAGE_SUBHEADING = EvaluatorsLocators.PAGE_SUBHEADING
    ADD_EVALUATOR_BUTTON = EvaluatorsLocators.ADD_EVALUATOR_BUTTON
    EVALUATOR_CARD = EvaluatorsLocators.EVALUATOR_CARD
    REMOVE_BUTTON = EvaluatorsLocators.REMOVE_BUTTON

    def __init__(self, page: Page, org_id: int = CIVICDATALAB_ORG_ID) -> None:
        super().__init__(page)
        self.org_id = org_id
        self.url = Config.url(f"/dashboard/ai-maker/{org_id}/auditors")

    def go_to_evaluators(self) -> "EvaluatorsPage":
        self.navigate(self.url)
        self.wait_for_load("domcontentloaded")
        self.wait_for_app_ready()
        self.skip_if_redirected_to_home(f"/dashboard/ai-maker/{self.org_id}/auditors")
        return self

    def is_page_loaded(self) -> bool:
        return self.is_visible(self.PAGE_HEADING)

    def is_subheading_visible(self) -> bool:
        return self.is_visible(self.PAGE_SUBHEADING)

    def is_card_grid_visible(self) -> bool:
        """True when at least one evaluator card is rendered. Uses the BasePage
        is_visible helper which wraps wait_for(state="visible", timeout=…) so
        the data-spinner curtain doesn't race us to zero."""
        return self.is_visible(self.REMOVE_BUTTON)

    def get_evaluator_card_count(self) -> int:
        """Count of evaluator cards (one Remove action per card).

        `Locator.count()` is synchronous — it returns whatever is on the page
        right now. The data-spinner curtain on this route can race a fresh
        navigation to zero. Wait for the first Remove action to become visible
        (BasePage helper wraps wait_for) before counting; if it never appears,
        callers see 0 and surface the real-bug assertion."""
        if not self.is_visible(self.REMOVE_BUTTON):
            return 0
        return self.page.locator(self.REMOVE_BUTTON).count()

    def is_add_evaluator_button_visible(self) -> bool:
        return self.is_visible(self.ADD_EVALUATOR_BUTTON)

    def is_evaluator_present(self, evaluator_selector: str) -> bool:
        return self.is_visible(evaluator_selector)

    def get_remove_button_count(self) -> int:
        return self.get_evaluator_card_count()
