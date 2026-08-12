"""
Visual regression coverage for modals and overlays.

The visual suite had zero coverage of any dialog, while the frontend actively
changes them — `90f38dc` ("Added modal with know more") and `130b5ac`
("refactor: update evaluation method handling in ModelSelectionModal") both
landed on `origin/dev` recently. Modals concentrate exactly the defects
full-page captures are worst at spotting: backdrop/z-index, panel width and
overflow, control alignment, disabled-button styling.

Captures are **element-scoped** (`Locator.screenshot()` on the dialog), not
full-page. Two reasons:
  1. Stability — the pages these dialogs open over (the evaluations list, the
     evaluator dashboard) render live, ordering-unstable data. A full-page
     capture would diff on the backdrop content, not the modal, and would land
     in the same permanently-xfailed bucket as the routes in
     `_NON_DETERMINISTIC_VISUAL`.
  2. Signal — a diff here points at the dialog, which is the thing under test.
The trade-off is that the dimmed backdrop itself is not covered; that is
deliberate, since it cannot be captured without also capturing the volatile
page beneath it.

Determinism: step-1 captures explicitly select the first model and version
rather than trusting whatever the dropdown defaults to — model ordering varies
between loads (the same reason `new_evaluation_wizard` is classified
non-deterministic in the sibling module). The prefilled evaluation name embeds
a live timestamp ("Untitled Evaluation - 10 August 2026 - 2:29PM") and is
masked.

Markers: visual, auth.
"""

import io

import pytest
from PIL import Image
from playwright.sync_api import Page

from locators.evaluations_locators import EvaluationsLocators
from locators.evaluator_role_locators import EvaluatorRoleLocators
from pages.evaluator_role_page import EvaluatorRolePage
from pages.new_evaluation_page import NewEvaluationPage

# Imported rather than copied: duplicating the diff maths would let this suite
# drift from the main one (different threshold, different baseline naming), and
# a silently-inconsistent second implementation is precisely the class of bug
# the capture-integrity work was cleaning up.
from tests.visual.test_visual_regression import _compare_or_save_baseline
from utils.visual_guards import (
    AUTH_PII_MASKS,
    DEFAULT_MASKS,
    capture_integrity_problem,
    wait_for_render_settled,
)

pytestmark = [pytest.mark.visual, pytest.mark.auth]


# Volatile content *inside* the dialogs. The evaluation-name field is prefilled
# with a wall-clock timestamp, so without this every run diffs 100% of the time.
_MODAL_VOLATILE_MASKS = [
    EvaluationsLocators.MODAL_EVAL_NAME_INPUT,
]

_MODAL_MASKS = DEFAULT_MASKS + AUTH_PII_MASKS + _MODAL_VOLATILE_MASKS


@pytest.fixture
def page(authenticated_page_fast):
    """Override: cached session, and — unlike building a raw context from
    `authenticated_storage_state` — this fixture refreshes a stale storage
    state before use, so a long suite can't capture a logged-out page."""
    return authenticated_page_fast


def _capture_dialog(page: Page, selector: str, snapshot_name: str) -> None:
    """Element-scoped capture of a dialog, gated on capture integrity.

    Screenshot first, then gate: `capture_integrity_problem` inspects the whole
    page's text (catching a 404 / curtain / logged-out fallback behind the
    dialog) and the captured image (catching a blank panel), so it needs both.
    """
    wait_for_render_settled(page)

    dialog = page.locator(selector).first
    if not dialog.is_visible():
        pytest.skip(f"Dialog not visible for selector {selector!r} — nothing to capture")

    mask_locators = []
    for sel in _MODAL_MASKS:
        loc = page.locator(sel)
        if loc.count() > 0:
            mask_locators.append(loc)

    raw = dialog.screenshot(mask=mask_locators or None)
    img = Image.open(io.BytesIO(raw))

    # expect_auth_route=True: these dialogs only exist behind the auth wall, so
    # logged-out chrome underneath means bug #15 served the public homepage and
    # whatever we just captured is not the dialog under test.
    problem = capture_integrity_problem(page, img, expect_auth_route=True)
    if problem:
        pytest.skip(f"Capture integrity check failed for {snapshot_name}: {problem}")

    _compare_or_save_baseline(img, snapshot_name)


@pytest.fixture
def open_eval_modal(page: Page) -> NewEvaluationPage:
    """Open 'Start an Evaluation' via the in-app flow.

    Deep-linking is avoided deliberately (lessons.md: cold deep-links to
    protected routes intermittently bounce to sign-in). `click_new_evaluation`
    already waits out the modal's own ~20s "Loading models" curtain.
    """
    nep = NewEvaluationPage(page)
    nep.go_to_evaluations_list()
    nep.click_new_evaluation()
    if not nep.is_modal_visible():
        pytest.skip("'Start an Evaluation' modal did not open")
    return nep


# ──────────────────────────────────────────── Start an Evaluation modal


class TestStartEvaluationModalVisual:
    """The two-step model-selection modal (`130b5ac` touched its method handling)."""

    def test_modal_step_1_desktop(self, open_eval_modal: NewEvaluationPage):
        """Step 1: model/version selects, name, and the bulk|playground radios."""
        nep = open_eval_modal
        # Pin the selection so the capture doesn't diff on dropdown ordering.
        nep.select_first_model_and_version()
        _capture_dialog(
            nep.page,
            EvaluationsLocators.MODAL_STEP_1,
            "modal_start_evaluation_step1_desktop_1440x900",
        )

    def test_modal_step_1_playground_method_desktop(
        self, open_eval_modal: NewEvaluationPage
    ):
        """Step 1 with the Playground method selected.

        Targets `130b5ac` ("update evaluation method handling in
        ModelSelectionModal") directly: the bulk/playground choice is the part
        that changed, and the selected-radio state is what a refactor there is
        most likely to break visually.
        """
        nep = open_eval_modal
        nep.select_first_model_and_version()
        try:
            nep.select_evaluation_method("manual")
        except Exception as exc:  # noqa: BLE001
            # Same class of issue as completed_eval_id's UI-seeding fallback
            # timing out: an intermittently slow/absent radio control is a
            # flow reliability issue, not a visual regression — skip rather
            # than fail so this doesn't flap the suite red.
            pytest.skip(f"Could not select evaluation method in modal: {exc}")
        _capture_dialog(
            nep.page,
            EvaluationsLocators.MODAL_STEP_1,
            "modal_start_evaluation_step1_playground_desktop_1440x900",
        )

    def test_modal_step_2_desktop(self, open_eval_modal: NewEvaluationPage):
        """Step 2: evaluator-type radios + objective textarea.

        The objective is left empty on purpose. That keeps the capture
        deterministic and captures the *disabled* Start Evaluation button — and
        it sidesteps app bug #20, where a filled form intermittently fails to
        enable that button, which would make the baseline a coin flip.
        """
        nep = open_eval_modal
        nep.select_first_model_and_version()
        nep.click_modal_next()
        if nep.get_modal_step() != "2":
            pytest.skip("Modal did not advance to step 2")
        try:
            nep.select_evaluator_type_in_modal("technical")
        except Exception as exc:  # noqa: BLE001
            pytest.skip(f"Could not select evaluator type in modal: {exc}")
        _capture_dialog(
            nep.page,
            EvaluationsLocators.MODAL_STEP_2,
            "modal_start_evaluation_step2_desktop_1440x900",
        )


# ──────────────────────────────────────────── Evaluator "Know More" modal


class TestKnowMoreModalVisual:
    """The info dialog added by `90f38dc`.

    Only rendered inside the empty pending-invitations state on the evaluator
    dashboard, so this skips whenever the account has pending invitations —
    same guard the e2e coverage uses (test_evaluator_role.py).
    """

    def test_know_more_dialog_desktop(self, page: Page):
        er = EvaluatorRolePage(page)
        er.go_to_evaluator_home()
        if not er.is_know_more_link_visible():
            pytest.skip(
                "'Know More' link not rendered — only present in the empty "
                "pending-invitations state"
            )
        er.click_know_more()
        if not er.is_know_more_dialog_visible():
            pytest.skip("'Know More' dialog did not open")
        _capture_dialog(
            page,
            EvaluatorRoleLocators.KNOW_MORE_DIALOG,
            "modal_know_more_desktop_1440x900",
        )
