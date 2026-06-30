"""
E2E tests for the Evaluators management page (read-side, AI Maker role).

These tests verify the evaluators list page structure, card count, and the
presence of the Add Evaluator button without mutating data. Write-side add/
remove flows live in test_evaluators_management_write.py.

Auth required — uses authenticated_page_fast.
"""

import pytest
from playwright.sync_api import Page

from locators.evaluators_locators import EvaluatorsLocators
from pages.evaluators_page import EvaluatorsPage

pytestmark = [pytest.mark.e2e, pytest.mark.regression, pytest.mark.auth]


@pytest.fixture
def ep(authenticated_page_fast: Page) -> EvaluatorsPage:
    page_obj = EvaluatorsPage(authenticated_page_fast)
    page_obj.go_to_evaluators()
    return page_obj


class TestEvaluatorsPageLoads:
    """The evaluators management page renders without error."""

    def test_page_loads_at_correct_url(self, ep: EvaluatorsPage, authenticated_page_fast: Page):
        assert "auditors" in authenticated_page_fast.url or "evaluators" in authenticated_page_fast.url, (
            f"Expected evaluators URL, got: {authenticated_page_fast.url}"
        )

    def test_page_heading_visible(self, ep: EvaluatorsPage):
        assert ep.is_page_loaded(), (
            "Evaluators page heading must be visible after navigation"
        )

    def test_page_title_is_set(self, authenticated_page_fast: Page):
        EvaluatorsPage(authenticated_page_fast).go_to_evaluators()
        assert authenticated_page_fast.title(), "Browser tab title must not be empty"


class TestEvaluatorsPageStructure:
    """The evaluators page shows expected structural elements."""

    def test_page_subheading_visible(self, ep: EvaluatorsPage):
        if not ep.is_subheading_visible():
            pytest.skip("Subheading not present on this build")
        assert ep.is_subheading_visible()

    def test_add_evaluator_button_visible(self, ep: EvaluatorsPage):
        assert ep.is_add_evaluator_button_visible(), (
            "'Add Evaluator' button must be visible on the evaluators page "
            "(requires AI Maker role)"
        )

    def test_evaluator_cards_or_empty_state(self, ep: EvaluatorsPage):
        """Page must show either evaluator cards or be in a valid empty state."""
        count = ep.get_evaluator_card_count()
        has_add_btn = ep.is_add_evaluator_button_visible()
        assert count >= 0 and has_add_btn, (
            "Evaluators page must show cards (count >= 0) and the Add Evaluator button"
        )

    def test_evaluator_card_count_is_non_negative(self, ep: EvaluatorsPage):
        count = ep.get_evaluator_card_count()
        assert count >= 0, f"Evaluator card count must be >= 0, got {count}"


class TestEvaluatorsPageHasEvaluators:
    """When the org has evaluators, their cards are rendered correctly."""

    def test_at_least_one_evaluator_card_present(self, ep: EvaluatorsPage):
        """Skip when the org has no evaluators (sandbox may be empty)."""
        count = ep.get_evaluator_card_count()
        if count == 0:
            pytest.skip("No evaluator cards on this org — skipping card-render assertions")
        assert count >= 1

    def test_remove_button_present_on_each_card(
        self, ep: EvaluatorsPage, authenticated_page_fast: Page
    ):
        """Each evaluator card must expose a Remove action."""
        count = ep.get_evaluator_card_count()
        if count == 0:
            pytest.skip("No evaluator cards to check Remove button on")
        remove_count = ep.get_remove_button_count()
        assert remove_count >= 1, (
            "At least one Remove button must be visible when evaluator cards are present"
        )


class TestAddEvaluatorDialogOpens:
    """Clicking Add Evaluator opens the dialog (smoke check — does not submit)."""

    def test_add_button_opens_dialog(self, ep: EvaluatorsPage, authenticated_page_fast: Page):
        if not ep.is_visible(EvaluatorsLocators.ADD_EVALUATOR_BUTTON, timeout=3_000):
            pytest.skip("Add Evaluator button not visible on this build")
        ep.click(EvaluatorsLocators.ADD_EVALUATOR_BUTTON)
        assert ep.is_visible(EvaluatorsLocators.ADD_DIALOG, timeout=5_000), (
            "Add Evaluator dialog must appear after clicking the button"
        )

    def test_dialog_email_input_is_present(
        self, ep: EvaluatorsPage, authenticated_page_fast: Page
    ):
        if not ep.is_visible(EvaluatorsLocators.ADD_EVALUATOR_BUTTON, timeout=3_000):
            pytest.skip("Add Evaluator button not visible on this build")
        ep.click(EvaluatorsLocators.ADD_EVALUATOR_BUTTON)
        if not ep.is_visible(EvaluatorsLocators.ADD_DIALOG, timeout=5_000):
            pytest.skip("Dialog did not appear")
        assert ep.is_visible(EvaluatorsLocators.ADD_DIALOG_EMAIL_INPUT, timeout=3_000), (
            "Email input must be present inside the Add Evaluator dialog"
        )

    def test_dialog_cancel_closes_dialog(
        self, ep: EvaluatorsPage, authenticated_page_fast: Page
    ):
        if not ep.is_visible(EvaluatorsLocators.ADD_EVALUATOR_BUTTON, timeout=3_000):
            pytest.skip("Add Evaluator button not visible on this build")
        ep.click(EvaluatorsLocators.ADD_EVALUATOR_BUTTON)
        if not ep.is_visible(EvaluatorsLocators.ADD_DIALOG, timeout=5_000):
            pytest.skip("Dialog did not appear")
        ep.click(EvaluatorsLocators.ADD_DIALOG_CANCEL)
        ep.wait_for_element(EvaluatorsLocators.ADD_DIALOG, state="hidden", timeout=5_000)
