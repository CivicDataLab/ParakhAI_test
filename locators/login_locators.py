"""
Selectors for the Keycloak SSO login page.

The platform redirects to a Keycloak-hosted login form, so selectors use
multiple fallback options to handle slight variations between KC versions.
"""


class LoginLocators:
    # ── Form fields ───────────────────────────────────────────────────────────
    EMAIL_INPUT = (
        "input[name='username'], "
        "input[type='email'], "
        "input[id='username']"
    )
    PASSWORD_INPUT = (
        "input[name='password'], "
        "input[type='password'], "
        "input[id='password']"
    )

    # ── Buttons / links ───────────────────────────────────────────────────────
    SIGN_IN_BUTTON = (
        "input[type='submit'], "
        "button[type='submit'], "
        "button:has-text('Sign In'), "
        "button:has-text('Log In'), "
        "button:has-text('Login')"
    )
    FORGOT_PASSWORD_LINK = (
        "a:has-text('Forgot Password'), "
        "a:has-text('Forgot password'), "
        "a[href*='forgot']"
    )
    REGISTER_LINK = (
        "a:has-text('Register'), "
        "a:has-text('Sign up'), "
        "a:has-text('Create account'), "
        "a[href*='register'], "
        "a[href*='registration']"
    )

    # ── Feedback / errors ─────────────────────────────────────────────────────
    ERROR_MESSAGE = (
        "[class*='error'], "
        "[class*='alert'], "
        "#kc-feedback-text, "
        ".pf-c-alert__title, "
        "[role='alert']"
    )

    # ── Form container ────────────────────────────────────────────────────────
    FORM = "form#kc-form-login, form[action*='login'], form"

    # ── Provider selection page (intermediate SSO step) ───────────────────────
    KEYCLOAK_PROVIDER_BUTTON = (
        "button:has-text('Sign in with Keycloak'), "
        "a:has-text('Sign in with Keycloak'), "
        "[class*='provider']:has-text('Keycloak'), "
        "[class*='social']:has-text('Keycloak')"
    )
