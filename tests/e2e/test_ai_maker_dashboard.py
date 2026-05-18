"""
E2E tests for the CivicdataLab AI Maker dashboard home.
Covers: overview stats, sidebar navigation, org identity panel, and model cards.
URL: https://parakh.civicdataspace.in/dashboard/ai-maker/1
"""

import pytest
from playwright.sync_api import Page

from pages.ai_maker_page import AIMakerPage

pytestmark = [pytest.mark.e2e, pytest.mark.regression, pytest.mark.auth]


@pytest.fixture
def page(authenticated_page_fast):
    """Override pytest-playwright's `page` fixture — the dashboard is
    auth-walled; the cached storage state keeps each test under ~10s."""
    return authenticated_page_fast


# Direct URL for CivicdataLab AI Maker dashboard (org_id=1)
DASHBOARD_URL = "/dashboard/ai-maker/1"


class TestAIMakerDashboardLoads:
    """Verify the AI Maker dashboard home page renders correctly."""

    def test_dashboard_page_loads(self, page: Page):
        """Direct navigation to the dashboard returns a usable page."""
        ai = AIMakerPage(page)
        ai.go_to_dashboard()
        assert "dashboard" in page.url.lower(), (
            f"Expected dashboard URL, got: {page.url}"
        )

    def test_page_title_is_set(self, page: Page):
        """Browser tab title is not empty."""
        ai = AIMakerPage(page)
        ai.go_to_dashboard()
        assert page.title(), "Page title must not be empty"

    def test_civicdatalab_name_visible_in_sidebar(self, page: Page):
        """CivicdataLab identity is shown in the left panel."""
        ai = AIMakerPage(page)
        ai.go_to_dashboard()
        assert ai.is_visible("text=CivicdataLab"), (
            "CivicdataLab name must be visible in the sidebar org panel"
        )

    def test_welcome_message_is_visible(self, page: Page):
        """A personalised welcome message is shown for the logged-in user."""
        ai = AIMakerPage(page)
        ai.go_to_dashboard()
        assert ai.is_visible(ai.SWITCH_ROLES_LINK) or ai.is_visible("text=Welcome"), (
            "Welcome message or Switch Roles link must be visible"
        )


class TestOverviewStats:
    """Verify all four overview stat cards are present and non-empty."""

    def test_overview_section_is_present(self, page: Page):
        ai = AIMakerPage(page)
        ai.go_to_dashboard()
        assert ai.is_overview_visible(), "Overview section must be visible"

    def test_evaluation_runs_stat_is_visible(self, page: Page):
        ai = AIMakerPage(page)
        ai.go_to_dashboard()
        assert ai.is_stat_evaluation_runs_visible(), "Evaluation Runs stat must be visible"

    def test_test_cases_stat_is_visible(self, page: Page):
        ai = AIMakerPage(page)
        ai.go_to_dashboard()
        assert ai.is_stat_test_cases_visible(), "Test Cases stat must be visible"

    def test_models_stat_is_visible(self, page: Page):
        ai = AIMakerPage(page)
        ai.go_to_dashboard()
        assert ai.is_stat_models_visible(), "Models stat must be visible"

    def test_issues_flagged_stat_is_visible(self, page: Page):
        ai = AIMakerPage(page)
        ai.go_to_dashboard()
        assert ai.is_stat_issues_flagged_visible(), "Issues Flagged stat must be visible"

    def test_all_four_stat_cards_visible(self, page: Page):
        """All four stat cards render in a single assertion."""
        ai = AIMakerPage(page)
        ai.go_to_dashboard()
        missing = []
        if not ai.is_stat_evaluation_runs_visible():
            missing.append("Evaluation Runs")
        if not ai.is_stat_test_cases_visible():
            missing.append("Test Cases")
        if not ai.is_stat_models_visible():
            missing.append("Models")
        if not ai.is_stat_issues_flagged_visible():
            missing.append("Issues Flagged")
        assert not missing, f"Missing stat cards: {missing}"


class TestSidebarNavigation:
    """Verify sidebar navigation items are present and route correctly."""

    def test_all_sidebar_items_present(self, page: Page):
        """All five sidebar links are visible."""
        ai = AIMakerPage(page)
        ai.go_to_dashboard()
        assert ai.is_sidebar_nav_complete(), (
            "All sidebar items (Home, Models, Evaluations, Prompt Libraries, Evaluators) "
            "must be visible"
        )

    def test_sidebar_home_link_is_visible(self, page: Page):
        ai = AIMakerPage(page)
        ai.go_to_dashboard()
        assert ai.is_visible(ai.SIDEBAR_HOME), "Sidebar Home link must be visible"

    def test_sidebar_models_link_navigates(self, page: Page):
        """Clicking Models in the sidebar routes to the models list."""
        ai = AIMakerPage(page)
        ai.go_to_dashboard()
        if not ai.is_visible(ai.SIDEBAR_MODELS, timeout=5_000):
            pytest.skip("Models sidebar link not found")
        ai.go_to_models()
        assert "/ai-models" in page.url, (
            f"Expected /ai-models in URL after clicking Models, got: {page.url}"
        )

    def test_sidebar_evaluations_link_navigates(self, page: Page):
        """Clicking Evaluations in the sidebar routes to the evaluations list."""
        ai = AIMakerPage(page)
        ai.go_to_dashboard()
        if not ai.is_visible(ai.SIDEBAR_EVALUATIONS, timeout=5_000):
            pytest.skip("Evaluations sidebar link not found")
        ai.go_to_evaluations()
        assert "/evaluations" in page.url, (
            f"Expected /evaluations in URL, got: {page.url}"
        )

    def test_sidebar_prompt_libraries_link_navigates(self, page: Page):
        """Clicking Prompt Libraries routes to the prompt libraries page."""
        ai = AIMakerPage(page)
        ai.go_to_dashboard()
        if not ai.is_visible(ai.SIDEBAR_PROMPT_LIBRARIES, timeout=5_000):
            pytest.skip("Prompt Libraries link not found")
        ai.go_to_prompt_libraries()
        assert "/prompt-libraries" in page.url, (
            f"Expected /prompt-libraries in URL, got: {page.url}"
        )

    def test_sidebar_evaluators_link_navigates(self, page: Page):
        """Clicking Evaluators routes to the evaluators management page."""
        ai = AIMakerPage(page)
        ai.go_to_dashboard()
        if not ai.is_visible(ai.SIDEBAR_EVALUATORS, timeout=5_000):
            pytest.skip("Evaluators link not found")
        ai.go_to_evaluators()
        assert "/auditors" in page.url, (
            f"Expected /auditors in URL, got: {page.url}"
        )

    def test_switch_roles_link_is_visible(self, page: Page):
        ai = AIMakerPage(page)
        ai.go_to_dashboard()
        assert ai.is_visible(ai.SWITCH_ROLES_LINK), "'Switch Roles' link must be visible"

    def test_switch_roles_navigates_to_workspace(self, page: Page):
        """Switch Roles returns the user to the /dashboard role-selection page."""
        ai = AIMakerPage(page)
        ai.go_to_dashboard()
        if not ai.is_visible(ai.SWITCH_ROLES_LINK, timeout=5_000):
            pytest.skip("Switch Roles link not found")
        ai.click_switch_roles()
        assert page.url.rstrip("/").endswith("/dashboard"), (
            f"Switch Roles should return to /dashboard, got: {page.url}"
        )


class TestModelCardsonHome:
    """Verify model cards render correctly on the AI Maker home."""

    def test_add_new_model_button_is_visible(self, page: Page):
        ai = AIMakerPage(page)
        ai.go_to_dashboard()
        # Scroll down to Models section
        page.keyboard.press("End")
        page.wait_for_timeout(300)
        assert ai.is_add_new_model_visible(), "'Add A New Model' button must be visible"

    def test_model_cards_are_rendered(self, page: Page):
        """At least one model card is shown on the home screen."""
        ai = AIMakerPage(page)
        ai.go_to_dashboard()
        page.keyboard.press("End")
        page.wait_for_timeout(300)
        count = ai.get_model_card_count()
        assert count >= 1, f"Expected at least 1 model card on home, found {count}"

    def test_text_generation_badge_is_present(self, page: Page):
        """Model type badge 'Text Generation' appears on at least one card."""
        ai = AIMakerPage(page)
        ai.go_to_dashboard()
        page.keyboard.press("End")
        page.wait_for_timeout(300)
        assert ai.is_visible("text=Text Generation"), (
            "'Text Generation' badge must appear on model cards"
        )
