"""
Smoke coverage for small standalone pages discovered in the 03 Jul 2026
route sweep that had no tests:

- /resources          — placeholder page ("Under construction"), must not 404
- /dashboard          — role-selection page (AI Maker / Evaluator cards)
"""

import pytest

from utils.config import Config

pytestmark = [pytest.mark.e2e, pytest.mark.smoke]


class TestResourcesPage:
    def test_resources_page_renders_placeholder(self, page):
        resp = page.goto(Config.url("/resources"), wait_until="domcontentloaded")
        assert resp is None or resp.status < 400, (
            f"/resources returned HTTP {resp.status}"
        )
        page.wait_for_timeout(2_000)
        body = page.locator("body").inner_text()
        assert "Under construction" in body or len(body.strip()) > 0, (
            "/resources rendered an empty page"
        )
        assert "Application error" not in body, "/resources crashed client-side"


class TestRoleSelectionPage:
    pytestmark = [pytest.mark.auth]

    def test_role_cards_render(self, authenticated_page_fast):
        authenticated_page_fast.goto(
            Config.url("/dashboard"), wait_until="domcontentloaded"
        )
        authenticated_page_fast.wait_for_timeout(3_000)
        body = authenticated_page_fast.locator("body").inner_text()
        assert "Select Your Role" in body, "Role selection heading missing"
        assert "AI Maker" in body and "Evaluator" in body, (
            "Both role cards (AI Maker / Evaluator) must render"
        )

    def test_ai_maker_card_navigates(self, authenticated_page_fast):
        authenticated_page_fast.goto(
            Config.url("/dashboard"), wait_until="domcontentloaded"
        )
        authenticated_page_fast.wait_for_timeout(3_000)
        authenticated_page_fast.locator("text=AI Maker").first.click()
        authenticated_page_fast.wait_for_url(
            "**/dashboard/ai-maker**", timeout=45_000, wait_until="commit"
        )
        assert "/dashboard/ai-maker" in authenticated_page_fast.url

    def test_evaluator_card_navigates(self, authenticated_page_fast):
        authenticated_page_fast.goto(
            Config.url("/dashboard"), wait_until="domcontentloaded"
        )
        authenticated_page_fast.wait_for_timeout(3_000)
        authenticated_page_fast.locator("text=Evaluator").first.click()
        authenticated_page_fast.wait_for_url(
            "**/dashboard/auditor**", timeout=45_000, wait_until="commit"
        )
        assert "/dashboard/auditor" in authenticated_page_fast.url
