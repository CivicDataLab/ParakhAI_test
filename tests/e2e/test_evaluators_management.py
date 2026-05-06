"""
E2E tests for the Evaluators management page (AI Maker role).
Covers: page load, evaluator table, column headers, existing evaluators.
URL: /dashboard/ai-maker/1/auditors

Note: Add/Remove evaluator tests are marked xfail (write-side-effects) and require
      explicit test-data setup to run safely.
"""

import pytest
from playwright.sync_api import Page

from locators.evaluators_locators import EvaluatorsLocators
from pages.evaluators_page import EvaluatorsPage
from utils.config import Config

pytestmark = [pytest.mark.e2e, pytest.mark.regression]


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


class TestEvaluatorsTable:
    """Verify the evaluators table structure and content."""

    def test_table_is_visible(self, page: Page):
        ep = EvaluatorsPage(page)
        ep.go_to_evaluators()
        assert ep.is_table_visible(), "Evaluators table must be visible"

    def test_all_column_headers_are_present(self, page: Page):
        """All five column headers — Username, Email, Name, Joined, Actions — are shown."""
        ep = EvaluatorsPage(page)
        ep.go_to_evaluators()
        assert ep.are_column_headers_visible(), (
            "All evaluator table columns (Username, Email, Name, Joined, Actions) must be present"
        )

    def test_username_column_header_is_visible(self, page: Page):
        ep = EvaluatorsPage(page)
        ep.go_to_evaluators()
        assert ep.is_visible(EvaluatorsLocators.TABLE_HEADER_USERNAME), (
            "'Username' column header must be visible"
        )

    def test_email_column_header_is_visible(self, page: Page):
        ep = EvaluatorsPage(page)
        ep.go_to_evaluators()
        assert ep.is_visible(EvaluatorsLocators.TABLE_HEADER_EMAIL), (
            "'Email' column header must be visible"
        )

    def test_name_column_header_is_visible(self, page: Page):
        ep = EvaluatorsPage(page)
        ep.go_to_evaluators()
        assert ep.is_visible(EvaluatorsLocators.TABLE_HEADER_NAME), (
            "'Name' column header must be visible"
        )

    def test_joined_column_header_is_visible(self, page: Page):
        ep = EvaluatorsPage(page)
        ep.go_to_evaluators()
        assert ep.is_visible(EvaluatorsLocators.TABLE_HEADER_JOINED), (
            "'Joined' column header must be visible"
        )

    def test_actions_column_header_is_visible(self, page: Page):
        ep = EvaluatorsPage(page)
        ep.go_to_evaluators()
        assert ep.is_visible(EvaluatorsLocators.TABLE_HEADER_ACTIONS), (
            "'Actions' column header must be visible"
        )

    def test_evaluator_rows_are_present(self, page: Page):
        """At least one evaluator row is shown for CivicdataLab."""
        ep = EvaluatorsPage(page)
        ep.go_to_evaluators()
        count = ep.get_evaluator_row_count()
        assert count >= 1, f"Expected at least 1 evaluator row, found {count}"

    def test_at_least_two_evaluators_listed(self, page: Page):
        """The org has at least 2 evaluators in the table."""
        ep = EvaluatorsPage(page)
        ep.go_to_evaluators()
        count = ep.get_evaluator_row_count()
        assert count >= 2, (
            f"Expected at least 2 evaluators, found {count}"
        )

    def test_first_known_evaluator_is_listed(self, page: Page):
        """EVALUATOR_EMAIL_1 (if configured) appears in the evaluators table."""
        if not Config.EVALUATOR_EMAIL_1:
            pytest.skip("EVALUATOR_EMAIL_1 not configured")
        ep = EvaluatorsPage(page)
        ep.go_to_evaluators()
        selector = EvaluatorsLocators.evaluator_email_text(Config.EVALUATOR_EMAIL_1)
        assert ep.is_evaluator_present(selector), (
            f"{Config.EVALUATOR_EMAIL_1} must be listed as an evaluator"
        )

    def test_second_known_evaluator_is_listed(self, page: Page):
        """EVALUATOR_EMAIL_2 (if configured) appears in the evaluators table."""
        if not Config.EVALUATOR_EMAIL_2:
            pytest.skip("EVALUATOR_EMAIL_2 not configured")
        ep = EvaluatorsPage(page)
        ep.go_to_evaluators()
        selector = EvaluatorsLocators.evaluator_email_text(Config.EVALUATOR_EMAIL_2)
        assert ep.is_evaluator_present(selector), (
            f"{Config.EVALUATOR_EMAIL_2} must be listed as an evaluator"
        )

    def test_remove_button_present_for_each_evaluator(self, page: Page):
        """A 'Remove' action button exists for each evaluator row."""
        ep = EvaluatorsPage(page)
        ep.go_to_evaluators()
        row_count = ep.get_evaluator_row_count()
        remove_count = ep.get_remove_button_count()
        assert remove_count >= row_count, (
            f"Expected {row_count} Remove buttons (one per row), found {remove_count}"
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
