"""
Accessibility checks that run against the *hydrated* public homepage.

Why this file exists
--------------------
The homepage mounts its nav, hero, feature tabs and footer with
`next/dynamic({ ssr: false })`. `HomePage.go_to_home()` returns at the `load`
event, when the page is still a skeleton: no <h1>, no footer links, no tabs.
`test_accessibility.py::test_homepage_has_no_critical_axe_violations` therefore
scans that skeleton and passes, while the page a user actually sees has serious
axe violations (measured on dev, 2026-10-31: `color-contrast` x1 and
`link-name` x4). Every test below calls `wait_until_hydrated()` first.

Known defects are asserted as the *correct* behaviour under strict xfail and
are logged in docs/app_bugs.md; the suite goes red when one is fixed (XPASS).
"""

import json

import pytest
from playwright.sync_api import Page

from pages.home_page import HomePage

pytestmark = [pytest.mark.accessibility]

try:
    from axe_playwright_python.sync_playwright import Axe
except ImportError:  # pragma: no cover - requirements.txt installs it
    Axe = None

_WCAG_AA_TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]


def _serious_violations(page: Page) -> list[dict]:
    """Run axe (WCAG 2.0/2.1 A+AA rules) and return critical/serious violations."""
    if Axe is None:
        pytest.skip("axe-playwright-python not installed — run: pip install axe-playwright-python")
    options = {"runOnly": {"type": "tag", "values": _WCAG_AA_TAGS}, "resultTypes": ["violations"]}
    results = Axe().run(page, options=options).response
    return [v for v in results.get("violations", []) if v.get("impact") in ("critical", "serious")]


def _summarise(violations: list[dict]) -> str:
    return json.dumps(
        [
            {
                "id": v["id"],
                "impact": v["impact"],
                "nodes": [n["target"] for n in v["nodes"][:5]],
            }
            for v in violations
        ],
        indent=2,
    )


class TestHydratedHomepageAxe:
    # Rules that have their own dedicated test (or ledger row) and are therefore
    # excluded here so one known defect cannot mask a different new one:
    #   link-name       -> docs/app_bugs.md #9 (footer social icons)
    #   color-contrast  -> docs/app_bugs.md #31 (active feature tab)
    _TRACKED_ELSEWHERE = {"link-name", "color-contrast"}

    def test_no_untracked_serious_axe_violations(self, page: Page):
        """The fully rendered homepage has no critical/serious WCAG 2.1 AA axe
        violations beyond the two defects tracked in the ledger."""
        HomePage(page).go_to_home().wait_until_hydrated()

        unexpected = [
            v for v in _serious_violations(page) if v["id"] not in self._TRACKED_ELSEWHERE
        ]
        assert not unexpected, (
            f"{len(unexpected)} new critical/serious axe violation(s) on the hydrated "
            f"homepage:\n{_summarise(unexpected)}"
        )

    @pytest.mark.xfail(
        strict=True,
        reason="App bug #31: active feature tab text #6849EE on #E8E4FF is 4.49:1 (< 4.5:1) — see docs/app_bugs.md",
    )
    def test_color_contrast_meets_aa(self, page: Page):
        """Every rendered homepage text node meets the 4.5:1 AA contrast ratio (WCAG 1.4.3)."""
        HomePage(page).go_to_home().wait_until_hydrated()

        contrast = [v for v in _serious_violations(page) if v["id"] == "color-contrast"]
        assert not contrast, (
            "Insufficient colour contrast on the hydrated homepage:\n"
            + "\n".join(
                f"  {n['target']}: {n['any'][0]['message']}"
                for v in contrast
                for n in v["nodes"]
            )
        )


class TestHydratedHomepageFeatureTabs:
    @pytest.mark.xfail(
        strict=True,
        reason="App bug #32: feature tabs are plain <button>s whose selected state is colour-only — see docs/app_bugs.md",
    )
    def test_selected_tab_is_exposed_to_assistive_tech(self, page: Page):
        """Selecting a feature tab exposes exactly that tab as selected (WCAG 4.1.2, 1.4.1).

        The sibling `test_feature_tabs_have_aria_states` skips on this page
        because there is no [role='tab']; this one asserts against the real
        markup (buttons) so it cannot skip its way to green.
        """
        home = HomePage(page).go_to_home().wait_until_hydrated()

        for label in home.get_all_tab_names():
            home.click_feature_tab(label)
            flags = home.get_tab_selected_flags()
            selected = [name for name, is_selected in flags.items() if is_selected]
            assert selected == [label], (
                f"After selecting the '{label}' tab, tabs exposed as selected via "
                f"aria-selected/aria-pressed/aria-current: {selected or 'none'} "
                f"(expected only '{label}')."
            )


class TestHydratedHomepageLanguage:
    @pytest.mark.xfail(
        strict=True,
        reason="App bug #33: Hindi/Odia/Assamese words in the hero sub-heading carry no lang attribute — see docs/app_bugs.md",
    )
    def test_non_english_passages_declare_their_language(self, page: Page):
        """Text in another script is marked up with its own lang (WCAG 3.1.2, GIGW 3.0)."""
        home = HomePage(page).go_to_home().wait_until_hydrated()

        untagged = home.get_non_latin_text_without_own_language()
        assert not untagged, (
            "Indic-script text rendered under the page language (en) with no lang attribute "
            f"of its own: {untagged}"
        )


@pytest.fixture
def narrow_page(browser) -> Page:
    """320 CSS px wide viewport — the WCAG 1.4.10 Reflow reference width."""
    from utils.config import Config

    context = browser.new_context(
        viewport={"width": 320, "height": 640}, ignore_https_errors=True, locale="en-US"
    )
    context.set_default_timeout(Config.TIMEOUT)
    yield context.new_page()
    context.close()


class TestHydratedHomepageReflow:
    def test_no_horizontal_scroll_at_320px(self, narrow_page: Page):
        """At 320px the whole hydrated homepage fits the viewport width (WCAG 1.4.10)."""
        home = HomePage(narrow_page).go_to_home().wait_until_hydrated()

        overflow = home.get_horizontal_overflow()
        assert overflow["scrollWidth"] <= overflow["clientWidth"], (
            f"Homepage scrolls horizontally at 320px: scrollWidth={overflow['scrollWidth']} > "
            f"clientWidth={overflow['clientWidth']}; elements past the right edge: "
            f"{overflow['offenders']}"
        )
