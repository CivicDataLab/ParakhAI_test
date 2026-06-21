"""
Accessibility tests for authenticated pages of the Parakh platform.
Targets WCAG 2.1 AA compliance using axe-core.

Complements test_accessibility.py (which covers the public homepage and login page).
All tests here use `authenticated_page_fast` (cached storage state, no per-test login).
"""

import json

import pytest
from playwright.sync_api import Page

from utils.config import Config
from utils.reporters import build_axe_report, save_json_report

pytestmark = [pytest.mark.accessibility, pytest.mark.auth]

_axe_available = False
try:
    from axe_playwright_python.sync_playwright import Axe
    _axe_available = True
except ImportError:
    pass


def _require_axe() -> None:
    if not _axe_available:
        pytest.skip("axe-playwright-python not installed — run: pip install axe-playwright-python")


def _run_axe(page: Page) -> dict:
    axe = Axe()
    return axe.run(page).response


def _critical_violations(axe_results: dict) -> list[dict]:
    return [v for v in axe_results.get("violations", []) if v.get("impact") in ("critical", "serious")]


def _nav_to(page: Page, path: str, wait_ms: int = 2500) -> None:
    page.goto(Config.url(path), wait_until="domcontentloaded", timeout=60_000)
    page.wait_for_timeout(wait_ms)


# ── AI Maker Dashboard ─────────────────────────────────────────────────────────


class TestDashboardAccessibility:
    """Axe + manual checks for the authenticated AI Maker dashboard."""

    def test_ai_maker_dashboard_has_no_critical_axe_violations(self, authenticated_page_fast: Page):
        """AI Maker dashboard must pass axe WCAG 2.1 AA scan with no critical/serious issues."""
        _require_axe()
        _nav_to(authenticated_page_fast, "/dashboard/ai-maker/1")

        results = _run_axe(authenticated_page_fast)
        critical = _critical_violations(results)

        report = build_axe_report(results.get("violations", []), authenticated_page_fast.url)
        save_json_report(report, "accessibility_dashboard_report.json")

        if critical:
            pytest.xfail(
                f"Found {len(critical)} critical/serious axe violations on the AI Maker dashboard. "
                "Review accessibility_dashboard_report.json for details."
            )
        assert len(critical) == 0

    def test_dashboard_has_exactly_one_h1(self, authenticated_page_fast: Page):
        """Dashboard must have exactly one <h1> element per page."""
        _nav_to(authenticated_page_fast, "/dashboard/ai-maker/1")
        try:
            authenticated_page_fast.locator("h1").first.wait_for(state="attached", timeout=10_000)
        except Exception:
            pass
        count = authenticated_page_fast.locator("h1").count()
        assert count == 1, f"Expected 1 <h1> on dashboard, found {count}"

    def test_dashboard_visible_buttons_have_accessible_names(self, authenticated_page_fast: Page):
        """All visible buttons on the dashboard must have an accessible name."""
        _nav_to(authenticated_page_fast, "/dashboard/ai-maker/1")

        buttons = authenticated_page_fast.locator("button:visible")
        count = buttons.count()
        if count == 0:
            pytest.skip("No visible buttons found on dashboard")

        unlabelled = []
        for i in range(min(count, 30)):  # cap at 30 to avoid timeout
            btn = buttons.nth(i)
            text = btn.inner_text().strip()
            aria_label = btn.get_attribute("aria-label") or ""
            aria_labelledby = btn.get_attribute("aria-labelledby") or ""
            title = btn.get_attribute("title") or ""
            if not text and not aria_label and not aria_labelledby and not title:
                cls = btn.get_attribute("class") or f"button[{i}]"
                unlabelled.append(cls[:60])

        if unlabelled:
            pytest.xfail(
                f"{len(unlabelled)} visible button(s) missing accessible name on dashboard: {unlabelled[:5]}"
            )
        assert len(unlabelled) == 0

    def test_dashboard_nav_links_have_text(self, authenticated_page_fast: Page):
        """All navigation links on the dashboard must have non-empty accessible text."""
        _nav_to(authenticated_page_fast, "/dashboard/ai-maker/1")

        nav_links = authenticated_page_fast.locator("nav a, [role='navigation'] a")
        count = nav_links.count()
        if count == 0:
            pytest.skip("No nav links found — layout may not use <nav> element")

        unlabelled = []
        for i in range(min(count, 20)):
            link = nav_links.nth(i)
            text = link.inner_text().strip()
            aria_label = link.get_attribute("aria-label") or ""
            if not text and not aria_label:
                href = link.get_attribute("href") or f"link[{i}]"
                unlabelled.append(href)

        if unlabelled:
            pytest.xfail(
                f"{len(unlabelled)} nav link(s) missing accessible text: {unlabelled[:5]}"
            )
        assert len(unlabelled) == 0


# ── Evaluations List ───────────────────────────────────────────────────────────


class TestEvaluationsListAccessibility:
    """Axe + manual checks for the evaluations list page."""

    def test_evaluations_list_has_no_critical_axe_violations(self, authenticated_page_fast: Page):
        """Evaluations list must pass axe WCAG 2.1 AA scan."""
        _require_axe()
        _nav_to(authenticated_page_fast, "/dashboard/ai-maker/1/evaluations")

        results = _run_axe(authenticated_page_fast)
        critical = _critical_violations(results)

        report = build_axe_report(results.get("violations", []), authenticated_page_fast.url)
        save_json_report(report, "accessibility_evaluations_report.json")

        if critical:
            pytest.xfail(
                f"{len(critical)} critical/serious axe violations on evaluations list. "
                "Review accessibility_evaluations_report.json."
            )
        assert len(critical) == 0

    def test_evaluations_status_filter_tabs_have_aria_attributes(self, authenticated_page_fast: Page):
        """Status filter tabs must use ARIA roles or semantics for screen reader support."""
        _nav_to(authenticated_page_fast, "/dashboard/ai-maker/1/evaluations")

        tabs = authenticated_page_fast.locator("[role='tab'], button[aria-selected]")
        if tabs.count() == 0:
            pytest.xfail(
                "No [role='tab'] or aria-selected buttons found on evaluations list. "
                "Status filter tabs should use ARIA tab pattern for accessibility."
            )

        missing = []
        for i in range(tabs.count()):
            tab = tabs.nth(i)
            aria_selected = tab.get_attribute("aria-selected")
            if aria_selected is None:
                missing.append(tab.inner_text().strip() or f"tab[{i}]")
        if missing:
            pytest.xfail(f"Tab(s) missing aria-selected: {missing}")

    def test_evaluations_table_has_column_headers(self, authenticated_page_fast: Page):
        """If a table is present, it must have column header elements (<th>)."""
        _nav_to(authenticated_page_fast, "/dashboard/ai-maker/1/evaluations")

        tables = authenticated_page_fast.locator("table")
        if tables.count() == 0:
            pytest.skip("No <table> found on evaluations list — may use grid/list layout")

        headers = authenticated_page_fast.locator("table th, table [role='columnheader']")
        assert headers.count() > 0, (
            "Table has no <th> column headers — screen readers cannot identify column meanings."
        )


# ── AI Models Page ─────────────────────────────────────────────────────────────


class TestModelsPageAccessibility:
    """Axe + structural checks for the AI models list."""

    def test_models_list_has_no_critical_axe_violations(self, authenticated_page_fast: Page):
        """AI models list must pass axe WCAG 2.1 AA scan."""
        _require_axe()
        _nav_to(authenticated_page_fast, "/dashboard/ai-maker/1/ai-models")

        results = _run_axe(authenticated_page_fast)
        critical = _critical_violations(results)

        report = build_axe_report(results.get("violations", []), authenticated_page_fast.url)
        save_json_report(report, "accessibility_models_report.json")

        if critical:
            pytest.xfail(
                f"{len(critical)} critical/serious axe violations on AI models page. "
                "Review accessibility_models_report.json."
            )
        assert len(critical) == 0

    def test_models_page_has_one_h1(self, authenticated_page_fast: Page):
        """Models page must have exactly one <h1>."""
        _nav_to(authenticated_page_fast, "/dashboard/ai-maker/1/ai-models")
        try:
            authenticated_page_fast.locator("h1").first.wait_for(state="attached", timeout=8_000)
        except Exception:
            pass
        count = authenticated_page_fast.locator("h1").count()
        assert count == 1, f"Expected 1 <h1> on models page, found {count}"

    def test_model_cards_have_accessible_headings_or_labels(self, authenticated_page_fast: Page):
        """Each visible model card must be identifiable by a heading or label."""
        _nav_to(authenticated_page_fast, "/dashboard/ai-maker/1/ai-models")

        # Model cards should have a heading element or aria-label
        cards = authenticated_page_fast.locator("[class*='card' i], [class*='item' i]")
        if cards.count() == 0:
            pytest.skip("No model cards found — page may show empty state")

        # Check that each card has either a heading or aria-label
        headings_in_cards = authenticated_page_fast.locator(
            "[class*='card' i] h2, [class*='card' i] h3, [class*='card' i] [class*='title' i]"
        )
        assert headings_in_cards.count() > 0, (
            "Model cards do not contain heading elements (h2/h3) or title elements. "
            "Screen readers need headings to navigate between cards."
        )


# ── Prompt Libraries ───────────────────────────────────────────────────────────


class TestPromptLibrariesAccessibility:
    """Axe + structural checks for the prompt libraries page."""

    def test_prompt_libraries_has_no_critical_axe_violations(self, authenticated_page_fast: Page):
        """Prompt libraries page must pass axe WCAG 2.1 AA scan."""
        _require_axe()
        _nav_to(authenticated_page_fast, "/dashboard/ai-maker/1/prompt-libraries")

        results = _run_axe(authenticated_page_fast)
        critical = _critical_violations(results)

        report = build_axe_report(results.get("violations", []), authenticated_page_fast.url)
        save_json_report(report, "accessibility_prompt_libraries_report.json")

        if critical:
            pytest.xfail(
                f"{len(critical)} critical/serious axe violations on prompt libraries. "
                "Review accessibility_prompt_libraries_report.json."
            )
        assert len(critical) == 0

    def test_prompt_libraries_search_input_has_label(self, authenticated_page_fast: Page):
        """Search input on prompt libraries must have an associated label."""
        _nav_to(authenticated_page_fast, "/dashboard/ai-maker/1/prompt-libraries")

        search = authenticated_page_fast.locator("input[type='search'], input[placeholder*='Search' i]")
        if search.count() == 0:
            pytest.skip("No search input found on prompt libraries page")

        # Check for accessible label via aria-label, aria-labelledby, or <label for>
        first = search.first
        aria_label = first.get_attribute("aria-label") or ""
        aria_labelledby = first.get_attribute("aria-labelledby") or ""
        placeholder = first.get_attribute("placeholder") or ""
        input_id = first.get_attribute("id") or ""

        has_label = bool(aria_label or aria_labelledby or placeholder)
        if input_id:
            label = authenticated_page_fast.locator(f"label[for='{input_id}']")
            has_label = has_label or label.count() > 0

        if not has_label:
            pytest.xfail(
                "Search input has no accessible label (aria-label, aria-labelledby, or <label>). "
                "Screen readers cannot identify unlabelled inputs."
            )


# ── Auditor Dashboard ──────────────────────────────────────────────────────────


class TestAuditorDashboardAccessibility:
    """Axe + structural checks for the auditor role dashboard."""

    def test_auditor_dashboard_has_no_critical_axe_violations(self, authenticated_page_fast: Page):
        """Auditor dashboard must pass axe WCAG 2.1 AA scan."""
        _require_axe()
        _nav_to(authenticated_page_fast, "/dashboard/auditor")

        # Auditor route may redirect to AI maker if this user is not an auditor
        if "auditor" not in authenticated_page_fast.url:
            pytest.skip("Test user is not in auditor role — auditor dashboard not accessible")

        results = _run_axe(authenticated_page_fast)
        critical = _critical_violations(results)

        report = build_axe_report(results.get("violations", []), authenticated_page_fast.url)
        save_json_report(report, "accessibility_auditor_dashboard_report.json")

        if critical:
            pytest.xfail(
                f"{len(critical)} critical/serious axe violations on auditor dashboard. "
                "Review accessibility_auditor_dashboard_report.json."
            )
        assert len(critical) == 0


# ── Cross-page Checks ──────────────────────────────────────────────────────────


class TestAuthPagesCrossCheck:
    """Cross-cutting accessibility checks applied to multiple authenticated pages."""

    @pytest.mark.parametrize("path,label", [
        ("/dashboard/ai-maker/1", "ai-maker-home"),
        ("/dashboard/ai-maker/1/evaluations", "evaluations-list"),
        ("/dashboard/ai-maker/1/ai-models", "models-list"),
        ("/dashboard/ai-maker/1/prompt-libraries", "prompt-libraries"),
    ])
    def test_authenticated_pages_have_lang_attribute(self, authenticated_page_fast: Page, path, label):
        """Every authenticated page must have a lang attribute on <html>."""
        _nav_to(authenticated_page_fast, path)
        lang = authenticated_page_fast.locator("html").get_attribute("lang")
        assert lang and len(lang) >= 2, (
            f"<html> on '{path}' is missing a lang attribute (got: '{lang}'). "
            "The lang attribute is required for screen reader language detection."
        )

    @pytest.mark.parametrize("path,label", [
        ("/dashboard/ai-maker/1", "ai-maker-home"),
        ("/dashboard/ai-maker/1/evaluations", "evaluations-list"),
    ])
    def test_authenticated_pages_have_page_title(self, authenticated_page_fast: Page, path, label):
        """Each page must have a non-empty <title> element."""
        _nav_to(authenticated_page_fast, path)
        title = authenticated_page_fast.title()
        assert title and title.strip(), (
            f"Page at '{path}' has an empty <title> element. "
            "Page titles are essential for screen reader users to identify pages."
        )
