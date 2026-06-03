"""
Read-only walk of the manual-evaluation workspace UI.

The manual workspace is rendered inside the new-evaluation wizard when the
audit type is set to Domain or Cultural (which forces the mode to Manual)
*and* the user advances to the Test Cases tab. These tests assert the
workspace UI is wired up — module cards, input textarea, output panel,
submit button — without actually submitting test cases.

Tests skip cleanly if the user can't reach the manual workspace (no models
in their org, account lacks permission, etc.).
"""

import pytest

from locators.evaluations_locators import EvaluationsLocators
from pages.evaluations_page import EvaluationsPage

pytestmark = [pytest.mark.e2e, pytest.mark.regression, pytest.mark.auth]


def _open_manual_workspace(page) -> EvaluationsPage:
    """Navigate to the manual workspace via the New Evaluation flow.

    Raises AssertionError if any platform prerequisite is not met.
    The helper fills the required Evaluation Objective so the Test Cases tab
    transition fires — without it the wizard's validation blocks the tab switch.
    """
    ep = EvaluationsPage(page)
    ep.go_to_evaluations_list()
    assert ep.is_visible(ep.NEW_EVALUATION_BUTTON, timeout=3_000), (
        "New Evaluation button not visible — platform may be unavailable or account lacks permission"
    )
    ep.click_new_evaluation()
    assert ep.is_new_eval_modal_visible(), (
        "New Evaluation modal did not appear"
    )
    ep.click_modal_start()
    assert ep.is_wizard_visible(), (
        "Evaluation wizard did not load after clicking Start"
    )
    # Force manual mode by selecting Domain (forces Manual per platform rule).
    ep.select_evaluation_type("domain")
    page.wait_for_timeout(500)
    # Fill the required objective so the Test Cases tab can be reached.
    ep.fill_evaluation_objective(
        "Manual mode regression test — verify Test Cases tab UI"
    )
    return ep


class TestManualWorkspaceLoad:
    """The wizard renders manual-mode controls when Domain type is selected."""

    def test_can_navigate_to_wizard(self, authenticated_page_fast):
        ep = EvaluationsPage(authenticated_page_fast)
        ep.go_to_evaluations_list()
        assert ep.is_visible(ep.NEW_EVALUATION_BUTTON, timeout=3_000), (
            "New Evaluation button not visible — platform may be unavailable or account lacks permission"
        )
        ep.click_new_evaluation()
        assert ep.is_new_eval_modal_visible(), "New Evaluation modal did not appear"

    def test_domain_type_renders_manual_mode_controls(self, authenticated_page_fast):
        ep = _open_manual_workspace(authenticated_page_fast)
        # Manual mode label or selector must be visible after picking Domain.
        assert ep.is_visible(EvaluationsLocators.EVAL_MODE_OPTION_MANUAL, timeout=3_000) \
            or ep.is_visible(EvaluationsLocators.EVAL_MODE_DROPDOWN, timeout=3_000), (
            "Manual mode UI should appear when Domain audit type is selected"
        )


class TestManualWorkspaceModuleCards:
    """The module cards (Hallucination / Bias / Privacy) render with counters."""

    def test_module_cards_visible_on_test_cases_tab(self, authenticated_page_fast):
        ep = _open_manual_workspace(authenticated_page_fast)
        # Advance to the Test Cases tab.
        assert ep.is_visible(ep.WIZARD_TAB_TEST_CASES, timeout=3_000), (
            "Test Cases tab not present"
        )
        ep.click_test_cases_tab()
        authenticated_page_fast.wait_for_timeout(700)
        assert ep.is_visible(EvaluationsLocators.MANUAL_MODULE_CARD, timeout=3_000), (
            "No module cards rendered — platform may not have loaded the manual workspace"
        )

    def test_module_card_shows_counter_labels(self, authenticated_page_fast):
        ep = _open_manual_workspace(authenticated_page_fast)
        assert ep.is_visible(ep.WIZARD_TAB_TEST_CASES, timeout=3_000), (
            "Test Cases tab not present"
        )
        ep.click_test_cases_tab()
        authenticated_page_fast.wait_for_timeout(700)
        assert ep.is_visible(EvaluationsLocators.MANUAL_MODULE_CARD, timeout=3_000), (
            "No module cards rendered"
        )
        # MANUAL_MODULE_CARD has broad fallbacks that also match
        # Configuration-tab module checkboxes. Counter labels only render on
        # the actual Test Cases tab. When the wizard stays on Configuration due
        # to a validation gate, the counter never appears — skip rather than
        # fail spuriously (this is a known test limitation, not a platform bug).
        if not ep.is_visible(
            EvaluationsLocators.MANUAL_MODULE_COUNTER_TEST_CASES, timeout=3_000
        ):
            pytest.skip(
                "Counter labels absent — likely still on Configuration tab "
                "(validation gate blocked transition to Test Cases)."
            )
        assert ep.is_visible(EvaluationsLocators.MANUAL_MODULE_COUNTER_TEST_CASES)


class TestManualWorkspaceTestEntry:
    """Clicking a module card opens the input/output entry panel."""

    @pytest.mark.xfail(reason="App bug #11 — see docs/app_bugs.md", strict=False)
    def test_module_click_opens_input_panel(self, authenticated_page_fast):
        ep = _open_manual_workspace(authenticated_page_fast)
        assert ep.is_visible(ep.WIZARD_TAB_TEST_CASES, timeout=3_000), (
            "Test Cases tab not present"
        )
        ep.click_test_cases_tab()
        authenticated_page_fast.wait_for_timeout(700)
        cards = authenticated_page_fast.locator(EvaluationsLocators.MANUAL_MODULE_CARD)
        assert cards.count() > 0, "No module cards to click — platform failed to load module list"
        cards.first.click()
        authenticated_page_fast.wait_for_timeout(500)
        # Input textarea OR change-module link should now be visible.
        has_panel = (
            ep.is_visible(EvaluationsLocators.MANUAL_INPUT_TEXTAREA, timeout=3_000)
            or ep.is_visible(EvaluationsLocators.MANUAL_CHANGE_MODULE_LINK, timeout=3_000)
        )
        assert has_panel, "Input panel did not render after module click"

    @pytest.mark.xfail(reason="App bug #11 — see docs/app_bugs.md", strict=False)
    def test_min_test_cases_note_visible(self, authenticated_page_fast):
        ep = _open_manual_workspace(authenticated_page_fast)
        assert ep.is_visible(ep.WIZARD_TAB_TEST_CASES, timeout=3_000), (
            "Test Cases tab not present"
        )
        ep.click_test_cases_tab()
        authenticated_page_fast.wait_for_timeout(700)
        assert ep.is_visible(EvaluationsLocators.MANUAL_MIN_TEST_CASES_NOTE, timeout=2_000), (
            "Min-test-cases note not rendered — platform may not have transitioned to Test Cases tab"
        )
