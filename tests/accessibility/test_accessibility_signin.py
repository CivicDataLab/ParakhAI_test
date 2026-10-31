"""
Accessibility of NextAuth's provider-selection page (`/api/auth/signin`).

Every anonymous visit to a protected route (`/dashboard`, `/resources`, any
unknown URL — see app bug #18) is redirected here, so it is the first screen
many users see. It is rendered by NextAuth's built-in template, not by the
Parakh React app.
"""

import pytest
from playwright.sync_api import Page

from pages.login_page import LoginPage

pytestmark = [pytest.mark.accessibility]


class TestProviderSigninPage:
    @pytest.mark.xfail(
        strict=True,
        reason="App bug #34: NextAuth sign-in page provider logo <img> has no alt attribute — see docs/app_bugs.md",
    )
    def test_provider_logo_has_alt_attribute(self, page: Page):
        """The provider logo image carries an alt attribute — alt="" is fine since the
        button text already names the provider (WCAG 1.1.1, axe `image-alt`, critical)."""
        login = LoginPage(page)
        login.go_to_provider_signin()

        alts = login.get_provider_logo_alt_values()
        assert alts, "Expected the sign-in page to render at least one provider logo image"
        missing = [i for i, alt in enumerate(alts) if alt is None]
        assert not missing, (
            f"{len(missing)} of {len(alts)} provider logo image(s) on {page.url} have no "
            "alt attribute (screen readers announce the image file name instead)."
        )
