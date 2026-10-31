"""
Accessibility of the mobile navigation sheet (hamburger menu, 390px).

`test_accessibility.py::test_buttons_have_accessible_names` only inspects the
page with the menu *closed*, so nothing in the open sheet was being checked.
Measured on dev 2026-10-31 with the sheet open: axe `aria-dialog-name`
(serious) and `button-name` (critical).
"""

import pytest
from playwright.sync_api import Page

from pages.home_page import HomePage

pytestmark = [pytest.mark.accessibility, pytest.mark.mobile]


class TestMobileMenuSheet:
    @pytest.mark.xfail(
        strict=True,
        reason="App bug #38: mobile menu sheet (role=dialog) has no accessible name — see docs/app_bugs.md",
    )
    def test_dialog_has_accessible_name(self, mobile_page: Page):
        """The open mobile menu is announced with a name (WCAG 4.1.2, axe `aria-dialog-name`)."""
        home = HomePage(mobile_page).go_to_home()
        home.open_mobile_menu_and_wait()

        name = home.get_mobile_menu_dialog_name()
        assert name, (
            "The mobile menu <div role=dialog> has neither aria-label nor a resolvable "
            "aria-labelledby, so screen readers announce an unnamed dialog."
        )
