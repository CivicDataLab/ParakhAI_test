"""
Page object for the organisation selection page.
URL: /dashboard/ai-maker
"""

from playwright.sync_api import Page

from locators.org_selection_locators import OrgSelectionLocators
from pages.base_page import BasePage
from utils.config import Config


class OrgSelectionPage(BasePage):
    """Org selection landing page — list of orgs the user belongs to."""

    PAGE_HEADING = OrgSelectionLocators.PAGE_HEADING
    ORG_CARD = OrgSelectionLocators.ORG_CARD
    NO_ORGS_MESSAGE = OrgSelectionLocators.NO_ORGS_MESSAGE

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.org_selection_url = Config.url("/dashboard/ai-maker")

    # ── Navigation ─────────────────────────────────────────────────────────────

    def go_to_org_selection(self) -> "OrgSelectionPage":
        self.navigate(self.org_selection_url)
        self.wait_for_load("domcontentloaded")
        return self

    # ── State checks ───────────────────────────────────────────────────────────

    def is_page_loaded(self) -> bool:
        return self.is_visible(self.PAGE_HEADING)

    def get_org_card_count(self) -> int:
        return self.page.locator(self.ORG_CARD).count()

    def is_org_visible(self, name: str) -> bool:
        return self.is_visible(f"text={name}")

    def get_all_org_names(self) -> list[str]:
        cards = self.page.locator(self.ORG_CARD)
        return [cards.nth(i).inner_text().strip() for i in range(cards.count())]

    # ── Actions ────────────────────────────────────────────────────────────────

    def select_org_by_name(self, name: str) -> None:
        self.click(f"text={name}")
        self.wait_for_load("domcontentloaded")

    def select_org_by_index(self, index: int) -> str:
        """Click the org card at *index* and return its name."""
        card = self.page.locator(self.ORG_CARD).nth(index)
        name = card.inner_text().strip()
        card.click()
        self.wait_for_load("domcontentloaded")
        return name
