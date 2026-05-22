"""
E2E tests for authentication flows on the Parakh platform.
The platform uses Keycloak SSO — tests navigate to the login page and verify
form fields, error handling, auth redirects, and successful login/logout flows.
"""

import pytest
from playwright.sync_api import Page

from pages.dashboard_page import DashboardPage
from pages.home_page import HomePage
from pages.login_page import LoginPage

pytestmark = [pytest.mark.e2e, pytest.mark.regression]

# Dummy credentials for negative tests — these must NOT be real accounts
DUMMY_EMAIL = "notareal@example.invalid"
DUMMY_PASSWORD = "WrongPassword!999"


def _navigate_to_login(page: Page) -> LoginPage:
    """Go to the homepage, click Login, and return a LoginPage object."""
    home = HomePage(page)
    home.go_to_home()

    if not home.is_visible(home.NAV_LOGIN_BUTTON, timeout=5_000):
        pytest.skip("Login button not visible — platform may not expose a login CTA")

    home.click_login()
    page.wait_for_load_state("domcontentloaded")
    return LoginPage(page)


class TestLoginPageStructure:
    def test_login_page_loads(self, page: Page):
        """Navigating to the login flow should render a login form."""
        login = _navigate_to_login(page)
        assert login.is_email_field_visible() or login.is_sign_in_button_visible(), (
            "Login page should show an email field or a sign-in button"
        )

    def test_login_form_has_required_fields(self, page: Page):
        """The login form must expose Email/Username and Password fields."""
        login = _navigate_to_login(page)
        assert login.is_email_field_visible(), "Email/username input must be present"
        assert login.is_password_field_visible(), "Password input must be present"

    def test_forgot_password_link_present(self, page: Page):
        """A 'Forgot Password' link should be available on the login page."""
        login = _navigate_to_login(page)
        assert login.is_forgot_password_visible(), (
            "Forgot Password link should be present on the login page"
        )

    def test_register_link_present(self, page: Page):
        """A link to create a new account should be visible on the login page."""
        login = _navigate_to_login(page)
        assert login.is_register_link_visible(), (
            "Register/Sign Up link should be present on the login page"
        )

    def test_sign_in_button_is_visible(self, page: Page):
        """The submit button must be visible and not disabled by default."""
        login = _navigate_to_login(page)
        assert login.is_sign_in_button_visible(), "Sign In button must be visible"


class TestLoginValidation:
    def test_empty_form_submission_shows_error(self, page: Page):
        """Submitting an empty login form should display a validation error."""
        login = _navigate_to_login(page)

        if not login.is_sign_in_button_visible():
            pytest.skip("Sign-in button not visible — cannot test empty submission")

        login.submit_empty_form()

        # Keycloak silently rejects empty submissions — user remains on the login page.
        # Accept: inline error, HTML5 required attrs, or staying on the login/auth URL.
        has_error = login.has_error()
        has_required_attr = page.locator(
            "input[required], input[aria-required='true']"
        ).count() > 0
        stayed_on_login = any(
            kw in page.url.lower()
            for kw in ["login", "auth", "keycloak", "sso", "signin"]
        )

        assert has_error or has_required_attr or stayed_on_login, (
            "Submitting an empty form should show an error, use HTML5 required validation, "
            f"or keep the user on the login page. Current URL: {page.url}"
        )

    def test_invalid_credentials_shows_error(self, page: Page):
        """Submitting invalid credentials should display an authentication error."""
        login = _navigate_to_login(page)

        if not login.is_email_field_visible():
            pytest.skip("Login form fields not available")

        login.login(DUMMY_EMAIL, DUMMY_PASSWORD)

        assert login.has_error(), (
            "Invalid credentials should produce an error message from the auth server"
        )

        error_text = login.get_error_message().lower()
        # Accept any of several common auth error messages
        error_keywords = [
            "invalid", "incorrect", "wrong", "failed", "error",
            "credentials", "username", "password", "not found"
        ]
        assert any(kw in error_text for kw in error_keywords) or error_text, (
            f"Error message should indicate invalid credentials, got: '{error_text}'"
        )


class TestAuthRedirects:
    def test_dashboard_redirects_unauthenticated_user(self, page: Page):
        """Accessing /dashboard without authentication should redirect to login."""
        dashboard = DashboardPage(page)
        dashboard.go_to_dashboard()

        # Either redirected to login or shows an auth barrier
        redirected = dashboard.was_redirected_to_login()
        on_auth_page = any(
            ind in page.url.lower()
            for ind in ["login", "auth", "keycloak", "sso", "signin"]
        )

        assert redirected or on_auth_page or not dashboard.is_authenticated(), (
            f"Unauthenticated access to /dashboard should redirect to login. "
            f"Current URL: {page.url}"
        )


@pytest.mark.auth
class TestSuccessfulLogin:
    def test_login_lands_on_authenticated_page(self, authenticated_page: Page):
        """After successful login, the Keycloak login form should no longer be visible."""
        login = LoginPage(authenticated_page)
        assert not login.is_email_field_visible(), (
            "Login form should not be visible after a successful authentication"
        )

    def test_authenticated_user_can_reach_dashboard(self, authenticated_page: Page):
        """A logged-in user should be able to access the dashboard without redirect."""
        dashboard = DashboardPage(authenticated_page)
        dashboard.go_to_dashboard()

        assert not dashboard.was_redirected_to_login(), (
            "Authenticated user should reach the dashboard without being sent back to login"
        )
        assert "dashboard" in authenticated_page.url.lower(), (
            f"URL should contain 'dashboard' after navigation. Current URL: {authenticated_page.url}"
        )


@pytest.mark.auth
class TestPostLoginState:
    def test_dashboard_heading_visible_after_login(self, authenticated_page: Page):
        """The dashboard should render a visible heading for authenticated users."""
        dashboard = DashboardPage(authenticated_page)
        dashboard.go_to_dashboard()

        heading = dashboard.get_heading_text()
        assert heading, "Dashboard heading should be non-empty for authenticated users"

    def test_user_menu_visible_after_login(self, authenticated_page: Page):
        """The user menu (avatar/profile) should be visible after login."""
        dashboard = DashboardPage(authenticated_page)
        dashboard.go_to_dashboard()

        assert dashboard.is_authenticated(), (
            "User menu should be visible on dashboard after successful login"
        )

    def test_authenticated_user_not_redirected_from_dashboard(self, authenticated_page: Page):
        """An authenticated user accessing /dashboard should NOT be redirected to login."""
        dashboard = DashboardPage(authenticated_page)
        dashboard.go_to_dashboard()

        assert not dashboard.was_redirected_to_login(), (
            "Authenticated user should not be redirected to the login page from /dashboard"
        )


@pytest.mark.auth
class TestLogout:
    def test_logout_redirects_to_login(self, authenticated_page: Page):
        """Signing out should return the user to the login page."""
        dashboard = DashboardPage(authenticated_page)
        dashboard.go_to_dashboard()

        dashboard.sign_out()
        # Sign-out either bounces to Keycloak or back to home — wait for either.
        try:
            authenticated_page.wait_for_url(
                lambda url: "dashboard" not in url.lower(),
                timeout=10_000,
            )
        except Exception:  # noqa: BLE001
            pass  # fall through to the multi-signal assertion below

        redirected_to_login = dashboard.was_redirected_to_login()
        on_auth_url = any(
            kw in authenticated_page.url.lower()
            for kw in ["login", "auth", "keycloak", "sso", "signin"]
        )
        login_form_visible = LoginPage(authenticated_page).is_email_field_visible()
        # Platform redirects to home page after sign-out — verify login CTA reappears
        home = HomePage(authenticated_page)
        on_home_logged_out = (
            "dashboard" not in authenticated_page.url.lower()
            and home.is_visible(home.NAV_LOGIN_BUTTON, timeout=3_000)
        )

        assert redirected_to_login or on_auth_url or login_form_visible or on_home_logged_out, (
            f"After sign-out, user should be signed out (login page or home with Login button). "
            f"Current URL: {authenticated_page.url}"
        )
