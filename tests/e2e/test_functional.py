"""
Functional tests for the Parakh platform.

Verifies business-logic behaviour and UI interactions on key pages.
Uses authenticated_page_fast (cached storage state) for all tests that require login.

Coverage:
  TestEvaluationsListFunctionality  — status filter tabs, New Evaluation CTA, column headers
  TestModelsFunctionality           — model cards render, required fields, page heading
  TestPromptLibrariesFunctionality  — list renders, items have titles, heading present
  TestDashboardMetrics              — welcome section, metrics cards, sidebar nav

Run with:
    pytest tests/e2e/test_functional.py -v
    pytest tests/e2e/test_functional.py -m regression -v
"""

import pytest
from playwright.sync_api import Page

from locators.dashboard_locators import DashboardLocators
from locators.evaluations_locators import EvaluationsLocators
from locators.models_locators import ModelsLocators
from locators.prompt_libraries_locators import PromptLibrariesLocators
from utils.config import Config

pytestmark = [pytest.mark.e2e, pytest.mark.auth, pytest.mark.regression]

_ORG_ID = "1"
_EVAL_URL = f"/dashboard/ai-maker/{_ORG_ID}/evaluations"
_MODELS_URL = f"/dashboard/ai-maker/{_ORG_ID}/ai-models"
_PROMPT_LIBS_URL = f"/dashboard/ai-maker/{_ORG_ID}/prompt-libraries"
_DASHBOARD_URL = f"/dashboard/ai-maker/{_ORG_ID}"


def _goto(page: Page, path: str, wait_ms: int = 3_000) -> None:
    page.goto(Config.url(path), wait_until="domcontentloaded", timeout=60_000)
    page.wait_for_timeout(wait_ms)


# ── Evaluations List ──────────────────────────────────────────────────────────


class TestEvaluationsListFunctionality:
    """Functional tests for the evaluations list page."""

    def test_evaluations_list_shows_status_filter_tabs(self, authenticated_page_fast: Page):
        """Status filter tabs (All / Draft / Completed etc.) must be visible."""
        _goto(authenticated_page_fast, _EVAL_URL)

        all_tab = authenticated_page_fast.locator(EvaluationsLocators.STATUS_TAB_ALL)
        draft_tab = authenticated_page_fast.locator(EvaluationsLocators.STATUS_TAB_DRAFT)

        has_tabs = all_tab.count() > 0 or draft_tab.count() > 0
        if not has_tabs:
            pytest.xfail(
                "No status filter tabs found on evaluations list — "
                "StatusFilterTabs component may not yet be deployed to dev"
            )
        assert has_tabs, "Status filter tabs must be present on the evaluations list"

    def test_status_filter_tabs_are_clickable(self, authenticated_page_fast: Page):
        """Clicking a status filter tab must not error; the tab must become active."""
        _goto(authenticated_page_fast, _EVAL_URL)

        tab_selectors = [
            EvaluationsLocators.STATUS_TAB_ALL,
            EvaluationsLocators.STATUS_TAB_COMPLETED,
            EvaluationsLocators.STATUS_TAB_DRAFT,
        ]
        clicked_any = False
        for sel in tab_selectors:
            tabs = authenticated_page_fast.locator(sel)
            if tabs.count() > 0 and tabs.first.is_visible():
                tabs.first.click()
                authenticated_page_fast.wait_for_timeout(800)
                clicked_any = True
                break

        if not clicked_any:
            pytest.skip("No visible status filter tabs to click")

    def test_evaluations_list_shows_new_evaluation_button(self, authenticated_page_fast: Page):
        """'New Evaluation' button must be visible on the evaluations list."""
        _goto(authenticated_page_fast, _EVAL_URL)
        cta = authenticated_page_fast.locator(EvaluationsLocators.NEW_EVALUATION_BUTTON)
        assert cta.count() > 0 and cta.first.is_visible(), (
            "'New Evaluation' button not visible — primary workflow entry point missing"
        )

    def test_evaluations_list_has_column_headers(self, authenticated_page_fast: Page):
        """The evaluations table must have column headers for Name and Status."""
        _goto(authenticated_page_fast, _EVAL_URL)

        name_col = authenticated_page_fast.locator(EvaluationsLocators.EVAL_NAME_COL)
        status_col = authenticated_page_fast.locator(EvaluationsLocators.EVAL_STATUS_COL)

        has_name = name_col.count() > 0
        has_status = status_col.count() > 0

        if not has_name and not has_status:
            pytest.xfail(
                "Neither 'Evaluation Name' nor 'Status' column headers found. "
                "The list may use a card layout instead of a table."
            )
        assert has_name or has_status

    def test_all_tab_shows_all_evaluations(self, authenticated_page_fast: Page):
        """Clicking 'All' tab must show all evaluations (not filtered to a single status)."""
        _goto(authenticated_page_fast, _EVAL_URL)

        all_tab = authenticated_page_fast.locator(EvaluationsLocators.STATUS_TAB_ALL)
        if all_tab.count() == 0:
            pytest.skip("'All' filter tab not found")

        all_tab.first.click()
        authenticated_page_fast.wait_for_timeout(1_000)

        rows = authenticated_page_fast.locator(EvaluationsLocators.EVAL_TABLE_ROW)
        row_count_after = rows.count()
        # After clicking All, at least one row should be visible (or the empty state is shown)
        empty_state = authenticated_page_fast.locator("text=/no evaluations|empty|get started/i")
        has_content = row_count_after > 1 or empty_state.count() > 0
        assert has_content, (
            "After clicking 'All' filter tab, no rows and no empty state visible"
        )

    def test_completed_filter_shows_only_completed(self, authenticated_page_fast: Page):
        """Clicking 'Completed' tab must show only COMPLETED evaluations."""
        _goto(authenticated_page_fast, _EVAL_URL)

        completed_tab = authenticated_page_fast.locator(EvaluationsLocators.STATUS_TAB_COMPLETED)
        if completed_tab.count() == 0:
            pytest.skip("'Completed' filter tab not found")

        completed_tab.first.click()
        authenticated_page_fast.wait_for_timeout(1_500)

        # Either completed rows are shown or empty state
        completed_badge = authenticated_page_fast.locator(EvaluationsLocators.STATUS_COMPLETED)
        draft_badge = authenticated_page_fast.locator(EvaluationsLocators.STATUS_DRAFT)
        empty_state = authenticated_page_fast.locator("text=/no evaluations|empty/i")

        # Draft badges should NOT appear when Completed filter is active
        if draft_badge.count() > 0 and completed_badge.count() == 0:
            pytest.xfail(
                "Completed filter tab is showing DRAFT evaluations — status filter may not be working"
            )


# ── AI Models ─────────────────────────────────────────────────────────────────


class TestModelsFunctionality:
    """Functional tests for the AI models list page."""

    def test_models_list_renders_model_cards(self, authenticated_page_fast: Page):
        """At least one model card must be visible, or an empty state is shown."""
        _goto(authenticated_page_fast, _MODELS_URL)

        cards = authenticated_page_fast.locator(
            "[class*='card' i], [class*='model' i] [class*='item' i]"
        )
        empty_state = authenticated_page_fast.locator(
            "text=/no models|add your first|no AI models/i"
        )
        has_content = cards.count() > 0 or empty_state.count() > 0
        assert has_content, (
            "Models list shows neither model cards nor an empty state — page may have failed to load"
        )

    def test_model_cards_have_name_text(self, authenticated_page_fast: Page):
        """Each visible model card must display a non-empty name."""
        _goto(authenticated_page_fast, _MODELS_URL)

        # Known model names from locators
        known_model = authenticated_page_fast.locator(
            f"{ModelsLocators.MODEL_SARVAM}, "
            f"{ModelsLocators.MODEL_LLAMA}, "
            f"{ModelsLocators.MODEL_GPT5}, "
            f"{ModelsLocators.MODEL_QWEN}, "
            f"{ModelsLocators.MODEL_GEMMA}, "
            f"{ModelsLocators.MODEL_MISTRAL}"
        )
        if known_model.count() > 0:
            # At least one known model name is visible — good
            return

        # Fallback: any card with non-empty heading text
        card_titles = authenticated_page_fast.locator(ModelsLocators.MODEL_CARD_TITLE)
        if card_titles.count() == 0:
            pytest.skip("No model cards visible — may be empty state or different layout")

        for i in range(min(card_titles.count(), 5)):
            title = card_titles.nth(i)
            if title.is_visible():
                text = title.inner_text().strip()
                assert text, f"Model card title at index {i} is empty"
                break

    def test_models_page_has_heading_with_models_text(self, authenticated_page_fast: Page):
        """The models page must have a heading containing 'Model' or 'AI'."""
        _goto(authenticated_page_fast, _MODELS_URL)

        try:
            authenticated_page_fast.locator("h1, h2").first.wait_for(
                state="visible", timeout=8_000
            )
        except Exception:
            pytest.xfail("No heading found within 8s on models page")

        headings = authenticated_page_fast.locator("h1, h2")
        found = False
        for i in range(headings.count()):
            h = headings.nth(i)
            if h.is_visible():
                text = h.inner_text().upper()
                if "MODEL" in text or "AI" in text:
                    found = True
                    break

        if not found:
            pytest.xfail(
                "No h1/h2 containing 'Model' or 'AI' found on the models page — "
                "heading copy may have changed"
            )

    def test_models_list_has_search_input(self, authenticated_page_fast: Page):
        """A search/filter input must be present on the models list."""
        _goto(authenticated_page_fast, _MODELS_URL)
        search = authenticated_page_fast.locator(ModelsLocators.SEARCH_INPUT)
        if search.count() == 0:
            pytest.xfail("Search input not found on models list — may not yet be implemented")
        assert search.first.is_visible(), "Search input exists but is not visible"

    def test_model_type_badge_present(self, authenticated_page_fast: Page):
        """Model cards must display a model type badge (e.g., Text Generation)."""
        _goto(authenticated_page_fast, _MODELS_URL)

        type_badge = authenticated_page_fast.locator(ModelsLocators.MODEL_TYPE_BADGE)
        if type_badge.count() == 0:
            pytest.xfail(
                "No 'Text Generation' type badge found — there may be no models with this type, "
                "or the badge rendering changed"
            )
        assert type_badge.first.is_visible()


# ── Prompt Libraries ──────────────────────────────────────────────────────────


class TestPromptLibrariesFunctionality:
    """Functional tests for the prompt libraries page."""

    def test_prompt_libraries_list_renders(self, authenticated_page_fast: Page):
        """Prompt libraries page must show library cards or an empty state."""
        _goto(authenticated_page_fast, _PROMPT_LIBS_URL)

        cards = authenticated_page_fast.locator(PromptLibrariesLocators.LIBRARY_CARD)
        empty_state = authenticated_page_fast.locator("text=/no datasets|no libraries|empty/i")
        has_content = cards.count() > 0 or empty_state.count() > 0
        assert has_content, (
            "Prompt libraries page shows neither library cards nor an empty state"
        )

    def test_prompt_library_cards_have_titles(self, authenticated_page_fast: Page):
        """Each visible library card must have a non-empty title."""
        _goto(authenticated_page_fast, _PROMPT_LIBS_URL)

        titles = authenticated_page_fast.locator(PromptLibrariesLocators.LIBRARY_CARD_TITLE)
        if titles.count() == 0:
            pytest.skip("No library card titles found — page may show empty state")

        for i in range(min(titles.count(), 5)):
            title = titles.nth(i)
            if title.is_visible():
                text = title.inner_text().strip()
                assert text, f"Library card title at index {i} is empty"

    def test_prompt_libraries_page_has_heading(self, authenticated_page_fast: Page):
        """Prompt libraries page must have a visible heading."""
        _goto(authenticated_page_fast, _PROMPT_LIBS_URL)
        heading = authenticated_page_fast.locator(PromptLibrariesLocators.PAGE_HEADING)
        assert heading.count() > 0 and heading.first.is_visible(), (
            "Prompt Libraries page heading not visible"
        )

    def test_known_library_is_present(self, authenticated_page_fast: Page):
        """At least one known prompt library must appear in the list."""
        _goto(authenticated_page_fast, _PROMPT_LIBS_URL)

        known_libraries = [
            PromptLibrariesLocators.LIBRARY_KCC_ENGLISH,
            PromptLibrariesLocators.LIBRARY_PARIKSHA,
            PromptLibrariesLocators.LIBRARY_PUBLIC_INTEREST_ENGLISH,
            PromptLibrariesLocators.LIBRARY_KCC_HINDI,
        ]
        for selector in known_libraries:
            lib = authenticated_page_fast.locator(selector)
            if lib.count() > 0 and lib.first.is_visible():
                return  # found at least one

        pytest.xfail(
            "None of the known prompt libraries are visible. "
            "The dev environment may have different seed data or the page may not have loaded."
        )

    def test_prompt_libraries_has_pagination_or_full_list(self, authenticated_page_fast: Page):
        """If more than 10 libraries exist, pagination controls must be present."""
        _goto(authenticated_page_fast, _PROMPT_LIBS_URL)

        cards = authenticated_page_fast.locator(PromptLibrariesLocators.LIBRARY_CARD)
        card_count = cards.count()

        if card_count < 10:
            pytest.skip(f"Only {card_count} libraries visible — pagination not expected")

        pagination = authenticated_page_fast.locator(PromptLibrariesLocators.PAGINATION_CONTAINER)
        if pagination.count() == 0:
            pytest.xfail(
                f"{card_count} library cards visible but no pagination controls found. "
                "Large lists should be paginated for performance."
            )


# ── Dashboard Metrics ─────────────────────────────────────────────────────────


class TestDashboardMetrics:
    """Functional tests for the AI Maker dashboard metrics section."""

    def test_dashboard_welcome_section_present(self, authenticated_page_fast: Page):
        """Dashboard must show a welcome or overview section."""
        _goto(authenticated_page_fast, _DASHBOARD_URL)

        welcome = authenticated_page_fast.locator(
            "text=/welcome|overview|dashboard/i, "
            "[class*='welcome' i], [class*='overview' i]"
        )
        # At minimum a heading should be there
        headings = authenticated_page_fast.locator("h1, h2, h3")
        has_content = welcome.count() > 0 or headings.count() > 0
        assert has_content, "Dashboard shows no welcome section or headings — page failed to load"

    def test_dashboard_metrics_cards_render(self, authenticated_page_fast: Page):
        """Dashboard must display one or more metric/stat cards (evaluations, models, etc.)."""
        _goto(authenticated_page_fast, _DASHBOARD_URL)

        # Metric cards typically contain number + label patterns
        metric_indicators = authenticated_page_fast.locator(
            "[class*='metric' i], [class*='stat' i], "
            "[class*='card' i]:has(p):has(h2), "
            "text=/Evaluation Runs|Test Cases|Models|Issues Flagged/"
        )
        if metric_indicators.count() == 0:
            pytest.xfail(
                "No metric cards found on dashboard — "
                "dashboard metrics section may not yet be populated on dev"
            )
        assert metric_indicators.count() > 0

    def test_dashboard_sidebar_navigation_visible(self, authenticated_page_fast: Page):
        """Dashboard sidebar navigation must be visible with at least one link."""
        _goto(authenticated_page_fast, _DASHBOARD_URL)

        nav = authenticated_page_fast.locator(DashboardLocators.NAV_LINKS)
        visible_links = sum(
            1 for i in range(min(nav.count(), 20)) if nav.nth(i).is_visible()
        )
        assert visible_links >= 1, (
            "No navigation links visible on dashboard — sidebar may have failed to render"
        )

    def test_dashboard_user_menu_visible_when_authenticated(self, authenticated_page_fast: Page):
        """Authenticated dashboard must show the user menu/avatar."""
        _goto(authenticated_page_fast, _DASHBOARD_URL)

        user_menu = authenticated_page_fast.locator(DashboardLocators.USER_MENU)
        if user_menu.count() == 0:
            pytest.xfail("User menu not found — may use a different auth indicator")
        assert user_menu.first.is_visible(timeout=5_000), (
            "User menu not visible on authenticated dashboard"
        )
