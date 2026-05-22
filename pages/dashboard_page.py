"""
Page Object Model for the Parakh dashboard (authenticated area).

Selectors live in locators/dashboard_locators.py.
"""

from playwright.sync_api import Page

from locators.dashboard_locators import DashboardLocators
from pages.base_page import BasePage
from utils.config import Config


class DashboardPage(BasePage):
    # Re-export locators as class attributes for caller convenience.
    USER_MENU = DashboardLocators.USER_MENU
    DASHBOARD_HEADING = DashboardLocators.DASHBOARD_HEADING
    NAV_LINKS = DashboardLocators.NAV_LINKS
    SIGN_OUT_BUTTON = DashboardLocators.SIGN_OUT_BUTTON
    BREADCRUMB = DashboardLocators.BREADCRUMB
    LOGIN_REDIRECT_INDICATOR = DashboardLocators.LOGIN_REDIRECT_INDICATOR

    def __init__(self, page: Page) -> None:
        super().__init__(page)

    # ── Navigation ────────────────────────────────────────────────────────────

    def go_to_dashboard(self) -> "DashboardPage":
        self.navigate(Config.url("dashboard"))
        self.wait_for_load("domcontentloaded")
        self.wait_for_app_ready()
        return self

    # ── State checks ──────────────────────────────────────────────────────────

    def is_authenticated(self) -> bool:
        """Return True if the user menu is visible (logged in)."""
        if self.is_visible(self.LOGIN_REDIRECT_INDICATOR, timeout=4_000):
            return False
        return self.is_visible(self.USER_MENU, timeout=4_000)

    def was_redirected_to_login(self) -> bool:
        return self.is_visible(self.LOGIN_REDIRECT_INDICATOR, timeout=5_000)

    def get_page_title(self) -> str:
        return self.title

    def get_heading_text(self) -> str:
        if self.is_visible(self.DASHBOARD_HEADING, timeout=3_000):
            return self.get_text(self.DASHBOARD_HEADING)
        return ""

    def sign_out(self) -> None:
        # Sign-out lives inside a dropdown — open the user menu first.
        if self.is_visible(self.USER_MENU):
            self.click(self.USER_MENU)
            self.page.wait_for_timeout(500)
        if self.is_visible(self.SIGN_OUT_BUTTON):
            self.click(self.SIGN_OUT_BUTTON)
