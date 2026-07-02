"""
Functional matrix for the "Start an Evaluation" modal (Jul 2026 two-step design).

Read-only: none of these tests click "Start Evaluation", so no drafts are
created and no sandbox gating is required. Draft-creating flows live in
test_add_evaluation_bulk.py / test_add_evaluation_playground.py.

Step 1: model select / version select / evaluation name / method (bulk|manual)
Step 2: evaluator-type radios (Technical default) / required objective textarea
"""

import pytest
from playwright.sync_api import Page

from locators.evaluations_locators import EvaluationsLocators
from pages.new_evaluation_page import NewEvaluationPage

pytestmark = [pytest.mark.e2e, pytest.mark.regression, pytest.mark.auth]

_OBJECTIVE = "Modal functional-matrix objective"


@pytest.fixture
def page(authenticated_page_fast):
    """Override: cached session — no per-test Keycloak round-trip."""
    return authenticated_page_fast


@pytest.fixture
def open_modal(page: Page) -> NewEvaluationPage:
    """Navigate to the evaluations list and open the Start an Evaluation modal."""
    nep = NewEvaluationPage(page)
    nep.go_to_evaluations_list()
    nep.click_new_evaluation()
    assert nep.is_modal_visible(), "'Start an Evaluation' modal must open"
    return nep


# ── Smoke ─────────────────────────────────────────────────────────────────────


class TestModalSmoke:
    pytestmark = [pytest.mark.smoke]

    def test_modal_opens_on_step_1(self, open_modal: NewEvaluationPage):
        nep = open_modal
        assert nep.get_modal_step() == "1", "Modal must open on step 1"

    def test_model_dropdown_populates_with_real_models(self, open_modal: NewEvaluationPage):
        nep = open_modal
        assert nep.modal_model_dropdown_has_options(), (
            "Model dropdown must list at least one real model besides 'New AI Model'"
        )
        options = nep.get_modal_model_options()
        assert options[0][1] == "New AI Model", (
            f"First model option should be 'New AI Model'; got {options[0][1]!r}"
        )

    def test_version_dropdown_has_at_least_one_option(self, open_modal: NewEvaluationPage):
        assert open_modal.modal_version_dropdown_has_options(), (
            "Version dropdown must offer at least one version"
        )

    def test_evaluation_name_is_prefilled(self, open_modal: NewEvaluationPage):
        name = open_modal.get_modal_eval_name()
        assert name.startswith("Untitled Evaluation"), (
            f"Evaluation name must be prefilled with 'Untitled Evaluation - …'; got {name!r}"
        )


# ── Step 1 behaviour ──────────────────────────────────────────────────────────


class TestModalStep1:
    def test_bulk_and_playground_methods_selectable(self, open_modal: NewEvaluationPage):
        nep = open_modal
        nep.select_evaluation_method("bulk")
        assert nep.is_method_selected("bulk"), "Bulk radio must be checkable"
        nep.select_evaluation_method("manual")
        assert nep.is_method_selected("manual"), "Playground radio must be checkable"
        assert not nep.is_method_selected("bulk"), (
            "Selecting Playground must deselect Bulk (radio group)"
        )

    def test_changing_model_updates_version_dropdown(self, open_modal: NewEvaluationPage):
        nep = open_modal
        nep.select_model_by_index(1)
        versions_a = nep.get_modal_version_options()
        nep.select_model_by_index(2)
        versions_b = nep.get_modal_version_options()
        # Both must be non-empty; the dropdown must stay populated after a switch.
        assert versions_a and versions_b, (
            f"Version dropdown must repopulate on model change; "
            f"got {versions_a!r} then {versions_b!r}"
        )

    def test_evaluation_name_is_editable(self, open_modal: NewEvaluationPage):
        nep = open_modal
        nep.set_modal_eval_name("QA renamed evaluation")
        assert nep.get_modal_eval_name() == "QA renamed evaluation"

    def test_long_name_accepted(self, open_modal: NewEvaluationPage):
        nep = open_modal
        long_name = "QA " + "x" * 300
        nep.set_modal_eval_name(long_name)
        value = nep.get_modal_eval_name()
        assert value, "Name input must not go blank after a long-name entry"
        assert value.startswith("QA "), f"Long name mangled: {value[:40]!r}…"

    def test_special_characters_in_name_accepted(self, open_modal: NewEvaluationPage):
        nep = open_modal
        special = "QA <eval> & \"quotes\" — émojis 🚀 100%"
        nep.set_modal_eval_name(special)
        assert nep.get_modal_eval_name() == special, (
            "Special characters must round-trip through the name input"
        )

    def test_next_advances_to_step_2(self, open_modal: NewEvaluationPage):
        nep = open_modal
        nep.select_model_by_index(1)
        nep.select_evaluation_method("bulk")
        nep.click_modal_next()
        assert nep.get_modal_step() == "2", "Next must advance the dialog to step 2"
        assert nep.is_visible(EvaluationsLocators.MODAL_STEP2_HEADING), (
            "'I am evaluating as' heading must be visible on step 2"
        )

    def test_double_click_next_still_lands_on_step_2(self, open_modal: NewEvaluationPage):
        nep = open_modal
        nep.select_model_by_index(1)
        nep.select_evaluation_method("bulk")
        btn = nep.page.locator(EvaluationsLocators.MODAL_NEXT_BUTTON).first
        btn.dblclick()
        nep.page.wait_for_timeout(1_500)
        assert nep.get_modal_step() == "2", (
            "Double-clicking Next must not skip past or break step 2"
        )


# ── Step 2 behaviour + step navigation ────────────────────────────────────────


class TestModalStep2:
    @pytest.fixture
    def on_step_2(self, open_modal: NewEvaluationPage) -> NewEvaluationPage:
        nep = open_modal
        nep.select_model_by_index(1)
        nep.select_evaluation_method("bulk")
        nep.click_modal_next()
        return nep

    def test_technical_evaluator_checked_by_default(self, on_step_2: NewEvaluationPage):
        assert on_step_2.get_checked_evaluator_type() == "Technical", (
            "'a technical evaluator' must be the default evaluator type"
        )

    def test_all_three_evaluator_types_selectable(self, on_step_2: NewEvaluationPage):
        nep = on_step_2
        for eval_type, value in (
            ("domain", "Domain"),
            ("cultural", "Cultural"),
            ("technical", "Technical"),
        ):
            nep.select_evaluator_type_in_modal(eval_type)
            assert nep.get_checked_evaluator_type() == value, (
                f"Selecting {eval_type} radio must check the {value} option"
            )

    def test_back_returns_to_step_1_preserving_selections(self, on_step_2: NewEvaluationPage):
        nep = on_step_2
        nep.click_modal_back()
        assert nep.get_modal_step() == "1", "Back must return the dialog to step 1"
        assert nep.is_method_selected("bulk"), (
            "Step-1 method selection must survive a Back navigation"
        )

    def test_objective_retained_after_back_and_next(self, on_step_2: NewEvaluationPage):
        nep = on_step_2
        nep.fill_modal_objective(_OBJECTIVE)
        nep.click_modal_back()
        nep.click_modal_next()
        assert nep.get_modal_objective() == _OBJECTIVE, (
            "Objective text must be retained across Back → Next"
        )


# ── Negative: Start Evaluation gating ─────────────────────────────────────────


class TestStartEvaluationValidation:
    @pytest.fixture
    def on_step_2(self, open_modal: NewEvaluationPage) -> NewEvaluationPage:
        nep = open_modal
        nep.select_model_by_index(1)
        nep.select_evaluation_method("bulk")
        nep.click_modal_next()
        return nep

    def test_start_disabled_with_empty_objective(self, on_step_2: NewEvaluationPage):
        assert not on_step_2.is_start_evaluation_enabled(), (
            "'Start Evaluation' must be disabled while the objective is empty"
        )

    def test_start_disabled_with_whitespace_objective(self, on_step_2: NewEvaluationPage):
        nep = on_step_2
        nep.fill_modal_objective("   \n\t  ")
        assert not nep.is_start_evaluation_enabled(), (
            "A whitespace-only objective must not enable 'Start Evaluation'"
        )

    @pytest.mark.xfail(
        strict=False,
        reason=(
            "PLATFORM BUG (intermittent, dev): 'Start Evaluation' sometimes "
            "never enables despite a valid form — verified live 2026-07-02 "
            "~16:55 IST: identical keystroke input enabled the button in one "
            "session and not the next. Server-side validation state suspected."
        ),
    )
    def test_start_enables_with_objective_and_disables_when_cleared(
        self, on_step_2: NewEvaluationPage
    ):
        nep = on_step_2
        nep.select_evaluator_type_in_modal("technical")
        nep.fill_modal_objective(_OBJECTIVE)
        assert nep.is_start_evaluation_enabled(settle_ms=5_000), (
            "'Start Evaluation' must enable once an objective is entered"
        )
        nep.fill_modal_objective("")
        assert not nep.is_start_evaluation_enabled(), (
            "Clearing the objective must disable 'Start Evaluation' again"
        )


# ── Dismissal: no draft side-effects ──────────────────────────────────────────


class TestModalDismissal:
    def test_escape_closes_modal_without_navigation(self, open_modal: NewEvaluationPage):
        nep = open_modal
        nep.page.keyboard.press("Escape")
        nep.page.wait_for_timeout(1_000)
        assert not nep.is_visible(EvaluationsLocators.MODAL_DIALOG, timeout=2_000), (
            "Escape must close the modal"
        )
        assert "auditId=" not in nep.page.url, (
            "Dismissing the modal must not create/navigate to a draft"
        )

    def test_close_button_dismisses_modal(self, open_modal: NewEvaluationPage):
        nep = open_modal
        nep.click_modal_cancel()
        assert not nep.is_visible(EvaluationsLocators.MODAL_DIALOG, timeout=2_000), (
            "The close/cancel control must dismiss the modal"
        )
        assert "auditId=" not in nep.page.url, (
            "Dismissing the modal must not create/navigate to a draft"
        )

    def test_dismiss_and_reopen_shows_fresh_step_1(self, open_modal: NewEvaluationPage):
        nep = open_modal
        nep.select_model_by_index(1)
        nep.select_evaluation_method("manual")
        nep.click_modal_next()
        nep.page.keyboard.press("Escape")
        nep.page.wait_for_timeout(1_000)
        nep.click_new_evaluation()
        assert nep.is_modal_visible(), "Modal must reopen after dismissal"
        assert nep.get_modal_step() == "1", (
            "A reopened modal must start again from step 1"
        )
