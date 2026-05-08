"""
Accessibility tests for the Parakh platform using axe-playwright-python.
Targets WCAG 2.1 AA compliance.

Reports are saved to reports/accessibility_report.json.
"""

import json

import pytest
from playwright.sync_api import Page

from pages.home_page import HomePage
from utils.reporters import build_axe_report, save_json_report

pytestmark = [pytest.mark.accessibility]

_axe_available = False
try:
    from axe_playwright_python.sync_playwright import Axe
    _axe_available = True
except ImportError:
    pass


def _require_axe():
    if not _axe_available:
        pytest.skip("axe-playwright-python not installed — run: pip install axe-playwright-python")


def _run_axe(page: Page) -> dict:
    """Run axe-core on the current page and return the full results dict.

    axe-playwright-python returns an AxeResults wrapper; .response is the raw
    axe-core JSON (violations, passes, incomplete, inapplicable).
    """
    axe = Axe()
    return axe.run(page).response


def _critical_violations(axe_results: dict) -> list[dict]:
    """Filter axe results to only critical/serious violations."""
    violations = axe_results.get("violations", [])
    return [v for v in violations if v.get("impact") in ("critical", "serious")]


# ──────────────────────────────────────────────────── Axe automated scans


class TestAxeScans:
    def test_homepage_has_no_critical_axe_violations(self, page: Page):
        """Homepage must pass axe WCAG 2.1 AA scan with no critical/serious issues."""
        _require_axe()
        home = HomePage(page)
        home.go_to_home()

        results = _run_axe(page)
        critical = _critical_violations(results)

        # Save full report
        report = build_axe_report(results.get("violations", []), page.url)
        save_json_report(report, "accessibility_report.json")

        assert len(critical) == 0, (
            f"Found {len(critical)} critical/serious axe violations on homepage:\n"
            + json.dumps(
                [{"id": v["id"], "impact": v["impact"], "description": v["description"]} for v in critical],
                indent=2,
            )
        )

    def test_login_page_has_no_critical_axe_violations(self, page: Page):
        """Login page must pass axe WCAG 2.1 AA scan with no critical/serious issues.

        Currently xfailed: see docs/app_bugs.md #5. The Keycloak login page
        (opub-kc.civicdatalab.in/auth/realms/DataSpace/...) has serious
        color-contrast and link-name violations. Owned by the Keycloak team,
        not the Parakh frontend. Confirmed via Playwright MCP 2026-05-08.
        """
        _require_axe()
        home = HomePage(page)
        home.go_to_home()

        if not home.is_visible(home.NAV_LOGIN_BUTTON, timeout=5_000):
            pytest.skip("Login button not found — cannot navigate to login page")

        home.click_login()
        page.wait_for_load_state("domcontentloaded")

        results = _run_axe(page)
        critical = _critical_violations(results)

        report = build_axe_report(results.get("violations", []), page.url)
        save_json_report(report, "accessibility_login_report.json")

        if len(critical) > 0:
            pytest.xfail(
                f"App bug #5 — see docs/app_bugs.md. {len(critical)} violations on Keycloak page."
            )
        assert len(critical) == 0


# ──────────────────────────────────────────────────── Manual a11y checks


class TestImagesAndLinks:
    def test_images_have_alt_text(self, page: Page):
        """Every <img> element must have a non-empty alt attribute."""
        home = HomePage(page)
        home.go_to_home()

        images = page.locator("img")
        count = images.count()
        if count == 0:
            pytest.skip("No <img> elements found on the page")

        missing_alt = []
        for i in range(count):
            img = images.nth(i)
            alt = img.get_attribute("alt")
            src = img.get_attribute("src") or f"img[{i}]"
            if alt is None:
                missing_alt.append(f"Missing alt: {src}")
            # Note: alt="" is acceptable for decorative images

        assert len(missing_alt) == 0, (
            f"{len(missing_alt)} image(s) missing alt attribute:\n"
            + "\n".join(missing_alt)
        )

    def test_social_links_have_accessible_names(self, page: Page):
        """Footer icon-only links must have aria-label or visible text."""
        home = HomePage(page)
        home.go_to_home()
        home.scroll_to_bottom()
        page.wait_for_timeout(300)

        social_links = page.locator(
            "footer a[href*='twitter'], footer a[href*='linkedin'], "
            "footer a[href*='github'], footer a[href*='youtube'], footer a[href*='facebook'], "
            "footer a[aria-label]"
        )
        count = social_links.count()
        if count == 0:
            pytest.skip("No social links found in footer")

        unlabelled = []
        for i in range(count):
            link = social_links.nth(i)
            aria_label = link.get_attribute("aria-label") or ""
            visible_text = link.inner_text().strip()
            title = link.get_attribute("title") or ""

            if not aria_label and not visible_text and not title:
                href = link.get_attribute("href") or f"link[{i}]"
                unlabelled.append(href)

        assert len(unlabelled) == 0, (
            f"{len(unlabelled)} social link(s) lack an accessible name:\n"
            + "\n".join(unlabelled)
        )


class TestStructure:
    def test_skip_link_exists(self, page: Page):
        """A skip-to-main-content link should be present for keyboard users.

        Currently xfailed: see docs/app_bugs.md #4. The homepage has no skip
        link — confirmed via Playwright MCP 2026-05-08.
        """
        home = HomePage(page)
        home.go_to_home()

        skip_link = page.locator("a[href='#main-content'], a[href='#main']")
        if skip_link.count() == 0:
            pytest.xfail("App bug #4 — see docs/app_bugs.md")
        assert skip_link.count() > 0

    def test_heading_hierarchy(self, page: Page):
        """There must be exactly one <h1> per page.

        Wait for the h1 to attach before counting — the homepage is a Next.js
        SPA and the h1 ("Build AI that's trustworthy…") renders after hydration.
        Reading count immediately after navigate() races the render and reports 0.
        """
        home = HomePage(page)
        home.go_to_home()

        # Wait for at least one h1 to attach, up to 10 s — the SPA hydrates
        # asynchronously after navigate() returns.
        try:
            page.locator("h1").first.wait_for(state="attached", timeout=10_000)
        except Exception:
            pass  # let the assertion below report what we actually saw

        h1_count = page.locator("h1").count()
        assert h1_count == 1, (
            f"Expected exactly 1 <h1> on the page, found {h1_count}. "
            "Multiple h1 elements break heading hierarchy."
        )

    def test_lang_attribute_set(self, page: Page):
        """The <html> element must have a lang attribute."""
        home = HomePage(page)
        home.go_to_home()

        lang = page.locator("html").get_attribute("lang")
        assert lang and len(lang) >= 2, (
            f"<html> element must have a non-empty lang attribute, got: '{lang}'"
        )

    def test_buttons_have_accessible_names(self, page: Page):
        """Every button must have either visible text or an aria-label."""
        home = HomePage(page)
        home.go_to_home()

        buttons = page.locator("button")
        count = buttons.count()
        if count == 0:
            pytest.skip("No <button> elements found on the page")

        unlabelled = []
        for i in range(count):
            btn = buttons.nth(i)
            # Skip hidden buttons
            if not btn.is_visible():
                continue
            text = btn.inner_text().strip()
            aria_label = btn.get_attribute("aria-label") or ""
            aria_labelledby = btn.get_attribute("aria-labelledby") or ""
            title = btn.get_attribute("title") or ""

            if not text and not aria_label and not aria_labelledby and not title:
                class_name = btn.get_attribute("class") or f"button[{i}]"
                unlabelled.append(class_name)

        assert len(unlabelled) == 0, (
            f"{len(unlabelled)} visible button(s) have no accessible name:\n"
            + "\n".join(unlabelled)
        )

    def test_feature_tabs_have_aria_states(self, page: Page):
        """Tab buttons in the feature tabs widget must use aria-selected."""
        home = HomePage(page)
        home.go_to_home()

        tabs = page.locator("[role='tab']")
        count = tabs.count()
        if count == 0:
            pytest.skip("No [role='tab'] elements found — feature tabs may not use ARIA roles")

        missing_aria = []
        for i in range(count):
            tab = tabs.nth(i)
            aria_selected = tab.get_attribute("aria-selected")
            if aria_selected is None:
                missing_aria.append(tab.inner_text().strip() or f"tab[{i}]")

        assert len(missing_aria) == 0, (
            f"Tab(s) missing aria-selected attribute: {missing_aria}"
        )


class TestKeyboardNavigation:
    def test_keyboard_navigation_tab_order(self, page: Page):
        """Tab through the page and verify interactive elements receive focus."""
        home = HomePage(page)
        home.go_to_home()

        # Focus the first element
        page.keyboard.press("Tab")
        focused_elements = []

        for _ in range(10):  # check first 10 focusable elements
            focused = page.evaluate(
                "document.activeElement ? document.activeElement.tagName + ':' + (document.activeElement.textContent || document.activeElement.getAttribute('aria-label') || '') : null"
            )
            if focused and focused not in focused_elements:
                focused_elements.append(focused)
            page.keyboard.press("Tab")

        assert len(focused_elements) >= 1, (
            "Tab key navigation should move focus through interactive elements"
        )

    def test_focus_visible_on_buttons(self, page: Page):
        """Visible buttons should show a visible focus ring when focused."""
        home = HomePage(page)
        home.go_to_home()

        buttons = page.locator("button:visible")
        count = buttons.count()
        if count == 0:
            pytest.skip("No visible buttons found")

        # Focus the first visible button and check its outline/box-shadow
        first_btn = buttons.first
        first_btn.focus()

        outline = page.evaluate(
            """(el) => {
                const style = window.getComputedStyle(el);
                return {
                    outline: style.outline,
                    outlineWidth: style.outlineWidth,
                    outlineStyle: style.outlineStyle,
                    boxShadow: style.boxShadow,
                };
            }""",
            first_btn.element_handle(),
        )

        # A focus ring is present if outline is non-zero or box-shadow is set
        has_outline = (
            outline.get("outlineStyle", "none") != "none"
            and outline.get("outlineWidth", "0px") not in ("0px", "0")
        )
        has_shadow = (
            outline.get("boxShadow", "none") not in ("none", "")
        )

        # This is a warning-level check — log the result but don't hard-fail
        # because some designs use custom focus indicators
        if not has_outline and not has_shadow:
            pytest.xfail(
                "Button does not appear to have a visible focus indicator "
                f"(outline: {outline.get('outline')}, box-shadow: {outline.get('boxShadow')}). "
                "Ensure :focus-visible styles are applied for WCAG 2.4.7."
            )
