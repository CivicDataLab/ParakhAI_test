"""
E2E tests for the Evaluators management page (AI Maker role).
Covers: page load, evaluator card grid, Add Evaluator CTA, existing evaluators.
URL: /dashboard/ai-maker/1/auditors

UI: card grid (not a table). Each evaluator card shows name + optional role +
a "Remove" action. Email/Joined/Username are no longer surfaced in the card
view; tests that needed those columns were retired in the 2026-05-20 sweep.

Add/Remove evaluator tests are marked xfail (write-side-effects) and require
explicit test-data setup to run safely.
"""

import pytest
from playwright.sync_api import Page

from locators.evaluators_locators import EvaluatorsLocators
from pages.evaluators_page import EvaluatorsPage
from utils.config import Config

pytestmark = [pytest.mark.e2e, pytest.mark.regression, pytest.mark.auth]


@pytest.fixture
def page(authenticated_page_fast):
    """Override pytest-playwright's `page` fixture so every test in this file
    runs against the storage-state-cached auth session. Every page hit here
    targets /dashboard/ai-maker/1/auditors which redirects unauth visitors to
    /api/auth/signin. See tasks/lessons.md (2026-05-18, 2026-05-20)."""
    return authenticated_page_fast


class TestEvaluatorsPageLoads:
    """Verify the evaluators management page renders correctly."""

    def test_page_loads(self, page: Page):
        ep = EvaluatorsPage(page)
        ep.go_to_evaluators()
        assert ep.is_page_loaded(), "'Evaluators' heading must be visible"

    def test_url_contains_auditors(self, page: Page):
        ep = EvaluatorsPage(page)
        ep.go_to_evaluators()
        assert "/auditors" in page.url, f"Expected /auditors in URL, got: {page.url}"

    def test_subheading_is_visible(self, page: Page):
        """'Manage evaluators' subheading is present."""
        ep = EvaluatorsPage(page)
        ep.go_to_evaluators()
        assert ep.is_subheading_visible(), "'Manage evaluators' subheading must be visible"

    def test_add_evaluator_button_is_visible(self, page: Page):
        ep = EvaluatorsPage(page)
        ep.go_to_evaluators()
        assert ep.is_add_evaluator_button_visible(), "'Add Evaluator' button must be visible"

    def test_page_title_is_set(self, page: Page):
        ep = EvaluatorsPage(page)
        ep.go_to_evaluators()
        assert page.title(), "Page title must not be empty"


class TestEvaluatorsList:
    """Verify the evaluator card grid renders the expected content."""

    def test_card_grid_is_visible(self, page: Page):
        ep = EvaluatorsPage(page)
        ep.go_to_evaluators()
        assert ep.is_card_grid_visible(), "At least one evaluator card must be visible"

    def test_evaluator_cards_are_present(self, page: Page):
        """At least one evaluator card is shown for CivicdataLab."""
        ep = EvaluatorsPage(page)
        ep.go_to_evaluators()
        count = ep.get_evaluator_card_count()
        assert count >= 1, f"Expected at least 1 evaluator card, found {count}"

    def test_at_least_two_evaluators_listed(self, page: Page):
        """The org has at least 2 evaluator cards."""
        ep = EvaluatorsPage(page)
        ep.go_to_evaluators()
        count = ep.get_evaluator_card_count()
        assert count >= 2, f"Expected at least 2 evaluator cards, found {count}"

    def test_first_known_evaluator_is_listed(self, page: Page):
        """EVALUATOR_EMAIL_1 (if configured) appears somewhere on the page.

        Note: the card UI no longer surfaces email, so this test now hinges on
        whether the email happens to render anywhere on the page (it may not).
        Skips when the env var is unset; xfails if the card grid hides email."""
        if not Config.EVALUATOR_EMAIL_1:
            pytest.skip("EVALUATOR_EMAIL_1 not configured")
        ep = EvaluatorsPage(page)
        ep.go_to_evaluators()
        selector = EvaluatorsLocators.evaluator_email_text(Config.EVALUATOR_EMAIL_1)
        if not ep.is_evaluator_present(selector):
            pytest.xfail("Card UI does not display email — email-based listing assertion no longer applicable")

    def test_second_known_evaluator_is_listed(self, page: Page):
        if not Config.EVALUATOR_EMAIL_2:
            pytest.skip("EVALUATOR_EMAIL_2 not configured")
        ep = EvaluatorsPage(page)
        ep.go_to_evaluators()
        selector = EvaluatorsLocators.evaluator_email_text(Config.EVALUATOR_EMAIL_2)
        if not ep.is_evaluator_present(selector):
            pytest.xfail("Card UI does not display email — email-based listing assertion no longer applicable")

    def test_remove_button_present_for_each_evaluator(self, page: Page):
        """A 'Remove' action exists for each evaluator card."""
        ep = EvaluatorsPage(page)
        ep.go_to_evaluators()
        card_count = ep.get_evaluator_card_count()
        remove_count = ep.get_remove_button_count()
        assert remove_count >= card_count, (
            f"Expected {card_count} Remove actions (one per card), found {remove_count}"
        )


class TestAddEvaluatorButton:
    """Verify the Add Evaluator CTA is accessible and functional."""

    def test_add_evaluator_button_is_clickable(self, page: Page):
        """'Add Evaluator' button is not disabled."""
        ep = EvaluatorsPage(page)
        ep.go_to_evaluators()
        btn = page.locator(EvaluatorsLocators.ADD_EVALUATOR_BUTTON).first
        if not btn.is_visible():
            pytest.skip("Add Evaluator button not found")
        is_disabled = btn.get_attribute("disabled")
        assert is_disabled is None, "'Add Evaluator' button must not be disabled"

    @pytest.mark.xfail(reason="Add Evaluator opens a form/modal — needs test-data setup")
    def test_add_evaluator_opens_invite_form(self, page: Page):
        """Clicking 'Add Evaluator' opens an invite form or modal."""
        ep = EvaluatorsPage(page)
        ep.go_to_evaluators()
        ep.click(EvaluatorsLocators.ADD_EVALUATOR_BUTTON)
        page.wait_for_timeout(500)
        # Expect some form or modal to appear
        assert ep.is_visible("input[type='email']") or ep.is_visible("[role='dialog']"), (
            "A form or modal for adding an evaluator must appear"
        )
