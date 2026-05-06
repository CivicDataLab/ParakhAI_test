"""
Page Object Model for the Parakh / Keycloak login page.
The platform uses Keycloak SSO, so the login form may be on an external domain.

Selectors live in locators/login_locators.py.
"""

from playwright.sync_api import Page

from locators.login_locators import LoginLocators
from pages.base_page import BasePage


class LoginPage(BasePage):
    # Re-export locators as class attributes for caller convenience.
    EMAIL_INPUT = LoginLocators.EMAIL_INPUT
    PASSWORD_INPUT = LoginLocators.PASSWORD_INPUT
    SIGN_IN_BUTTON = LoginLocators.SIGN_IN_BUTTON
    FORGOT_PASSWORD_LINK = LoginLocators.FORGOT_PASSWORD_LINK
    REGISTER_LINK = LoginLocators.REGISTER_LINK
    ERROR_MESSAGE = LoginLocators.ERROR_MESSAGE
    FORM = LoginLocators.FORM
    KEYCLOAK_PROVIDER_BUTTON = LoginLocators.KEYCLOAK_PROVIDER_BUTTON

    def __init__(self, page: Page) -> None:
        super().__init__(page)

    # ── Actions ───────────────────────────────────────────────────────────────

    def enter_email(self, email: str) -> None:
        self.type_text(self.EMAIL_INPUT, email)

    def enter_password(self, password: str) -> None:
        self.type_text(self.PASSWORD_INPUT, password)

    def click_sign_in(self) -> None:
        self.click(self.SIGN_IN_BUTTON)

    def click_forgot_password(self) -> None:
        self.click(self.FORGOT_PASSWORD_LINK)

    def click_register(self) -> None:
        self.click(self.REGISTER_LINK)

    def click_provider_if_present(self, timeout: int = 3_000) -> bool:
        """Click the 'Sign in with Keycloak' provider button if the intermediate
        provider-selection page is shown. Returns True if clicked.

        The platform sometimes routes through a provider-selection page before
        the Keycloak form. When skipped, the email field appears directly.
        """
        if self.is_visible(self.KEYCLOAK_PROVIDER_BUTTON, timeout=timeout):
            self.click(self.KEYCLOAK_PROVIDER_BUTTON)
            self.page.wait_for_load_state("domcontentloaded")
            return True
        return False

    def login(self, email: str, password: str) -> None:
        """Fill credentials and submit the login form."""
        self.enter_email(email)
        self.enter_password(password)
        self.click_sign_in()

    def submit_empty_form(self) -> None:
        """Click submit without entering any data (negative test helper)."""
        self.click(self.SIGN_IN_BUTTON)

    # ── State checks ──────────────────────────────────────────────────────────

    def is_sign_in_button_visible(self) -> bool:
        return self.is_visible(self.SIGN_IN_BUTTON)

    def is_email_field_visible(self) -> bool:
        return self.is_visible(self.EMAIL_INPUT)

    def is_password_field_visible(self) -> bool:
        return self.is_visible(self.PASSWORD_INPUT)

    def is_forgot_password_visible(self) -> bool:
        return self.is_visible(self.FORGOT_PASSWORD_LINK)

    def is_register_link_visible(self) -> bool:
        return self.is_visible(self.REGISTER_LINK)

    def get_error_message(self) -> str:
        try:
            loc = self.page.locator(self.ERROR_MESSAGE).first
            loc.wait_for(state="visible", timeout=5_000)
            return loc.inner_text().strip()
        except Exception:  # noqa: BLE001
            return ""

    def has_error(self) -> bool:
        try:
            loc = self.page.locator(self.ERROR_MESSAGE).first
            loc.wait_for(state="visible", timeout=5_000)
            return True
        except Exception:  # noqa: BLE001
            return False
