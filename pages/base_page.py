"""
Base page object — all other page objects inherit from this class.
Provides common browser interactions with built-in waits and error handling.
"""

from pathlib import Path

from playwright.sync_api import Locator, Page, Response, expect

from utils.config import Config
from utils.helpers import take_screenshot


class BasePage:
    """Thin wrapper around a Playwright Page with reusable action helpers."""

    def __init__(self, page: Page) -> None:
        self.page = page
        self.base_url = Config.BASE_URL
        self.timeout = Config.TIMEOUT

    # ----------------------------------------------------------------- Navigation

    def navigate(self, url: str) -> Response | None:
        """Navigate to an absolute URL and wait for the page to load.

        Uses wait_until="load" (all resources including JS bundles fetched)
        rather than "domcontentloaded" so that React/Next.js apps have time
        to hydrate before tests start querying elements.

        Returns the Response object so callers can inspect the HTTP status code.
        """
        return self.page.goto(url, wait_until="load", timeout=self.timeout)

    def navigate_to_path(self, path: str = "") -> None:
        """Navigate to a path relative to BASE_URL."""
        self.navigate(Config.url(path))

    def wait_for_load(self, state: str = "networkidle") -> None:
        """Wait for the page to reach a given load state."""
        self.page.wait_for_load_state(state, timeout=self.timeout)

    def reload(self) -> None:
        self.page.reload(wait_until="domcontentloaded", timeout=self.timeout)

    # ----------------------------------------------------------------- Locators

    def find_element(self, selector: str) -> Locator:
        """Return a Locator for *selector*."""
        return self.page.locator(selector)

    def find_elements(self, selector: str) -> Locator:
        """Return a Locator matching all elements for *selector*."""
        return self.page.locator(selector)

    # ----------------------------------------------------------------- Actions

    def click(self, selector: str, timeout: int | None = None) -> None:
        """Wait for *selector* to be visible then click it."""
        loc = self.page.locator(selector)
        loc.wait_for(state="visible", timeout=timeout or self.timeout)
        loc.click()

    def type_text(self, selector: str, text: str, clear: bool = True) -> None:
        """Focus the field identified by *selector* and type *text*."""
        loc = self.page.locator(selector)
        loc.wait_for(state="visible", timeout=self.timeout)
        if clear:
            loc.clear()
        loc.fill(text)

    def get_text(self, selector: str) -> str:
        """Return the trimmed inner text of *selector*."""
        return self.page.locator(selector).inner_text().strip()

    def get_attribute(self, selector: str, attribute: str) -> str | None:
        return self.page.locator(selector).get_attribute(attribute)

    # ---------------------------------------------------------------- Visibility

    def is_visible(self, selector: str, timeout: int = 5_000) -> bool:
        """Return True if at least one element matching selector is visible within timeout ms."""
        try:
            self.page.locator(selector).first.wait_for(state="visible", timeout=timeout)
            return True
        except Exception:  # noqa: BLE001
            return False

    def is_hidden(self, selector: str) -> bool:
        return self.page.locator(selector).is_hidden()

    # ------------------------------------------------------------------ Waits

    def wait_for_element(
        self,
        selector: str,
        state: str = "visible",
        timeout: int | None = None,
    ) -> Locator:
        loc = self.page.locator(selector)
        loc.wait_for(state=state, timeout=timeout or self.timeout)
        return loc

    def wait_for_url(self, url_pattern: str, timeout: int | None = None) -> None:
        self.page.wait_for_url(url_pattern, timeout=timeout or self.timeout)

    # ----------------------------------------------------------------- Scroll

    def scroll_to_element(self, selector: str) -> None:
        self.page.locator(selector).scroll_into_view_if_needed()

    def scroll_to_bottom(self) -> None:
        self.page.keyboard.press("End")

    # --------------------------------------------------------------- Screenshot

    def take_screenshot(self, name: str) -> Path:
        return take_screenshot(self.page, name)

    # ------------------------------------------------------------ Assertions

    def assert_title_contains(self, text: str) -> None:
        expect(self.page).to_have_title(text)

    def assert_url_contains(self, fragment: str) -> None:
        expect(self.page).to_have_url(f"*{fragment}*")

    def assert_visible(self, selector: str) -> None:
        expect(self.page.locator(selector)).to_be_visible()

    def assert_text_equals(self, selector: str, text: str) -> None:
        expect(self.page.locator(selector)).to_have_text(text)

    def assert_text_contains(self, selector: str, text: str) -> None:
        expect(self.page.locator(selector)).to_contain_text(text)

    # ----------------------------------------------- Modal / dialog helpers

    def confirm_modal(self, accept: bool = True, role: str = "dialog") -> None:
        """Find an open dialog and click its primary CTA (accept) or cancel (decline).

        The platform uses opub-ui Dialog (role='dialog'). Buttons inside follow
        a common naming pattern: primary action is "Confirm"/"Add"/"Submit"/
        "Create"/"Run"/"Yes"; secondary is "Cancel"/"Close"/"No".
        """
        dialog = self.page.locator(f"[role='{role}']").first
        dialog.wait_for(state="visible", timeout=self.timeout)
        if accept:
            primary = dialog.locator(
                "button:has-text('Confirm'), button:has-text('Add'), "
                "button:has-text('Submit'), button:has-text('Create'), "
                "button:has-text('Run'), button:has-text('Yes'), "
                "button:has-text('Save')"
            ).first
            primary.click()
        else:
            secondary = dialog.locator(
                "button:has-text('Cancel'), button:has-text('Close'), "
                "button:has-text('No'), [aria-label='Close']"
            ).first
            secondary.click()

    def wait_for_toast(self, text_fragment: str = "", timeout: int = 5_000) -> str:
        """Wait for a toast/notification and return its text.

        Covers both the opub-ui toast and the custom inline toast used for
        assignment actions. Pass `text_fragment` to filter to a specific
        message; otherwise returns the first toast's text.
        """
        toast_selector = (
            "[role='status'], [role='alert'], "
            "[class*='toast'], [class*='Toast'], [class*='notification'], "
            ".fixed.bottom-4.right-4, .fixed.bottom-4"
        )
        loc = self.page.locator(toast_selector)
        if text_fragment:
            loc = loc.filter(has_text=text_fragment)
        loc = loc.first
        loc.wait_for(state="visible", timeout=timeout)
        return loc.inner_text().strip()

    def assert_in_url(self, fragment: str, timeout: int = 5_000) -> None:
        """Assert that *fragment* appears anywhere in the current URL."""
        self.page.wait_for_function(
            f"() => window.location.href.includes({fragment!r})",
            timeout=timeout,
        )

    def select_combobox(self, trigger_selector: str, value: str) -> None:
        """Open an opub-ui Combobox and pick *value* from its options.

        Pattern: click the trigger to open, then click the option whose text
        matches *value*. Used by the new-evaluation wizard for org/scope/
        modules/metrics selection.
        """
        self.click(trigger_selector)
        option = self.page.locator(
            f"[role='option']:has-text('{value}'), li:has-text('{value}')"
        ).first
        option.wait_for(state="visible", timeout=self.timeout)
        option.click()

    # ------------------------------------------------------------------- Misc

    @property
    def current_url(self) -> str:
        return self.page.url

    @property
    def title(self) -> str:
        return self.page.title()
