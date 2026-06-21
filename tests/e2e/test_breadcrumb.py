"""
Breadcrumb navigation consistency tests.

MCP exploration (2026-06-22) found that the deepest breadcrumb crumb shows
"Dashboard" on sub-pages (Models, Evaluations) instead of the section name.
These tests document the expected behaviour and will fail until the app is fixed.
"""

import pytest
from playwright.sync_api import Page

from pages.evaluations_page import EvaluationsPage
from utils.config import Config

pytestmark = [pytest.mark.e2e, pytest.mark.auth, pytest.mark.regression]


def _get_last_breadcrumb_text(page: Page) -> str:
    """Return text of the last (current-page) breadcrumb item."""
    crumbs = page.locator("nav[aria-label='breadcrumb'] li, [aria-label='breadcrumb'] li")
    count = crumbs.count()
    if count == 0:
        crumbs = page.locator("ol li, nav li")
        count = crumbs.count()
    if count == 0:
        return ""
    return (crumbs.nth(count - 1).text_content() or "").strip()


class TestBreadcrumbLabels:
    """The deepest breadcrumb crumb must reflect the current section, not 'Dashboard'."""

    def test_evaluations_breadcrumb_is_not_dashboard(self, authenticated_page_fast: Page):
        page = authenticated_page_fast
        ep = EvaluationsPage(page)
        ep.go_to_evaluations_list()
        page.wait_for_timeout(1500)
        last = _get_last_breadcrumb_text(page)
        assert "Dashboard" not in last or "Evaluation" in last, (
            f"Evaluations page breadcrumb should say 'Evaluations', not 'Dashboard'. Got: '{last}'"
        )

    def test_models_breadcrumb_is_not_dashboard(self, authenticated_page_fast: Page):
        page = authenticated_page_fast
        page.goto(Config.url("/dashboard/ai-maker/1/ai-models"))
        page.wait_for_timeout(2000)
        last = _get_last_breadcrumb_text(page)
        assert "Dashboard" not in last or "Model" in last, (
            f"Models page breadcrumb should say 'Models', not 'Dashboard'. Got: '{last}'"
        )

    def test_breadcrumb_home_link_navigates_to_root(self, authenticated_page_fast: Page):
        page = authenticated_page_fast
        ep = EvaluationsPage(page)
        ep.go_to_evaluations_list()
        page.wait_for_timeout(1000)
        home_link = page.locator("nav[aria-label='breadcrumb'] a:has-text('Home'), [aria-label='breadcrumb'] a:has-text('Home')").first
        if home_link.count() == 0:
            pytest.skip("Home breadcrumb link not found")
        home_link.click()
        page.wait_for_load_state("domcontentloaded")
        assert page.url.rstrip("/") in (Config.BASE_URL.rstrip("/"), Config.BASE_URL.rstrip("/") + "/en"), (
            f"Home breadcrumb link must navigate to root, got: {page.url}"
        )

    def test_breadcrumb_evaluation_workspace_link_works(self, authenticated_page_fast: Page):
        page = authenticated_page_fast
        ep = EvaluationsPage(page)
        ep.go_to_evaluations_list()
        page.wait_for_timeout(1000)
        ws_link = page.locator("a:has-text('Evaluation Workspace')").first
        if ws_link.count() == 0:
            pytest.skip("'Evaluation Workspace' breadcrumb not found")
        ws_link.click()
        page.wait_for_load_state("domcontentloaded")
        assert "/dashboard" in page.url, (
            f"'Evaluation Workspace' breadcrumb must navigate to /dashboard, got: {page.url}"
        )

    def test_evaluation_detail_breadcrumb_has_org_name(self, authenticated_page_fast: Page, completed_eval_id: int):
        page = authenticated_page_fast
        page.goto(Config.url(f"/dashboard/ai-maker/1/evaluations/{completed_eval_id}"))
        page.wait_for_timeout(3000)
        crumb_text = page.locator("nav[aria-label='breadcrumb'], [aria-label='breadcrumb']").text_content() or ""
        assert "CivicDataLab" in crumb_text or "AI Maker" in crumb_text, (
            "Evaluation detail breadcrumb must include the org or role context. "
            f"Got: '{crumb_text[:200]}'"
        )
