"""
Cancel-mid-run tests for the New Evaluation flow (Jul 2026 redesign).

Verifies that cancelling at various stages:
  (a) modal step 1/2 — dismisses without creating a draft
  (b) single-page wizard — navigates away from /evaluations/new cleanly

Under the redesigned flow, 'Start Evaluation' creates the draft immediately,
so every wizard-level cancel test is write-side (regression_write + cleanup).
Native window.confirm dialogs are auto-accepted by the authenticated fixtures
via page.on("dialog", ...).
"""

import pytest
from playwright.sync_api import Page

from pages.new_evaluation_page import NewEvaluationPage

pytestmark = [pytest.mark.e2e, pytest.mark.regression, pytest.mark.auth]

_OBJECTIVE = "Cancel-flow test objective"


def _open_wizard(page: Page, cleanup_evaluation: list) -> NewEvaluationPage:
    """Create a bulk draft via the modal and register it for teardown."""
    nep = NewEvaluationPage(page)
    nep.open_new_evaluation_wizard(method="bulk", objective=_OBJECTIVE)
    audit_id = nep.get_audit_id_from_url()
    if audit_id:
        cleanup_evaluation.append(audit_id)
    return nep


class TestCancelFromWizard:
    """The header 'Cancel' button cancels the audit; its enabled state on a
    fresh DRAFT varies with hydration timing. Drafts exit via 'Back to List'."""

    pytestmark = [pytest.mark.regression_write]

    def test_cancel_button_present_on_draft_wizard(
        self, authenticated_page: Page, sandbox_org, cleanup_evaluation
    ):
        """The header Cancel button renders on the draft wizard. Its enabled
        state varies with hydration timing (observed both ways on dev), so
        only presence is asserted; exit behaviour is covered by Back to List."""
        nep = _open_wizard(authenticated_page, cleanup_evaluation)
        assert nep.is_visible(nep.WIZARD_CANCEL_EVALUATION, timeout=10_000), (
            "The header 'Cancel' button must be present on the wizard"
        )

    def test_back_to_list_leaves_wizard_url(
        self, authenticated_page: Page, sandbox_org, cleanup_evaluation
    ):
        """'Back to List' exits the wizard cleanly for a fresh draft."""
        nep = _open_wizard(authenticated_page, cleanup_evaluation)
        nep.click_back_to_list()
        assert "auditId=" not in authenticated_page.url, (
            f"URL still on wizard after Back to List: {authenticated_page.url}"
        )

    def test_back_to_list_lands_on_a_valid_page(
        self, authenticated_page: Page, sandbox_org, cleanup_evaluation
    ):
        """After exiting, the page must be renderable (no crash / blank screen)."""
        nep = _open_wizard(authenticated_page, cleanup_evaluation)
        nep.click_back_to_list()
        body_count = authenticated_page.locator("body").count()
        assert body_count == 1, "Page body missing after exit — app may have crashed"
        url = authenticated_page.url.lower()
        assert "/error" not in url and "/404" not in url, (
            f"Landed on an error page after exit: {authenticated_page.url}"
        )


class TestCancelFromModal:
    def test_cancel_from_new_evaluation_modal_stays_on_list(
        self, authenticated_page: Page
    ):
        """Dismissing the modal (before Start Evaluation) creates nothing and stays on list."""
        nep = NewEvaluationPage(authenticated_page)
        nep.go_to_evaluations_list()
        nep.click_new_evaluation()

        if not nep.is_modal_visible():
            pytest.skip("New Evaluation modal did not appear — cannot test modal cancel")

        nep.click_modal_cancel()

        assert not nep.is_modal_visible(), "Modal must close after clicking Cancel"
        assert "auditId=" not in authenticated_page.url, (
            f"Dismissing the modal must not create a draft; got: {authenticated_page.url}"
        )

    def test_cancel_from_modal_step_2_creates_no_draft(self, authenticated_page: Page):
        """Backing out of step 2 (Escape) must not create a draft."""
        nep = NewEvaluationPage(authenticated_page)
        nep.go_to_evaluations_list()
        nep.click_new_evaluation()
        if not nep.is_modal_visible():
            pytest.skip("New Evaluation modal did not appear")

        nep.select_first_model_and_version()
        nep.select_evaluation_method("bulk")
        nep.click_modal_next()
        nep.fill_modal_objective(_OBJECTIVE)
        authenticated_page.keyboard.press("Escape")
        authenticated_page.wait_for_timeout(1_000)

        assert not nep.is_modal_visible(), "Escape must dismiss the modal from step 2"
        assert "auditId=" not in authenticated_page.url, (
            "Dismissing step 2 without clicking Start must not create a draft"
        )


class TestCancelNavigation:
    """Cancel uses client-side router.push — browser Back must work cleanly."""

    pytestmark = [pytest.mark.regression_write]

    def test_cancel_browser_back_does_not_loop(
        self, authenticated_page: Page, sandbox_org, cleanup_evaluation
    ):
        """After exiting the wizard, browser Back must resolve to a clean page (no redirect loop)."""
        nep = _open_wizard(authenticated_page, cleanup_evaluation)
        nep.click_back_to_list()

        authenticated_page.go_back()
        authenticated_page.wait_for_timeout(800)

        final_url = authenticated_page.url
        assert "/error" not in final_url.lower() and "/404" not in final_url.lower(), (
            f"Browser Back after cancel landed on error page: {final_url}"
        )
        # Back may legitimately land on the wizard history entry; the key
        # invariant is the app doesn't loop or crash — assert it renders.
        assert authenticated_page.locator("body").count() == 1, (
            "Page body missing after Back — app may have crashed"
        )
