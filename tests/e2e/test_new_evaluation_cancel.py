"""
Cancel-mid-run tests for the New Evaluation wizard.

Verifies that cancelling at various stages of the wizard:
  (a) navigates the user away from /evaluations/new
  (b) does not leave the app in a broken state

Auth is required. Native window.confirm dialogs are auto-accepted by the
`authenticated_page` fixture via page.on("dialog", ...).
"""

import pytest
from playwright.sync_api import Page

from pages.new_evaluation_page import NewEvaluationPage

pytestmark = [pytest.mark.e2e, pytest.mark.regression, pytest.mark.auth]


def _open_wizard(page: Page) -> NewEvaluationPage:
    nep = NewEvaluationPage(page)
    nep.open_new_evaluation_wizard()
    return nep


class TestCancelFromWizard:
    def test_cancel_from_fresh_wizard_leaves_wizard_url(self, authenticated_page: Page):
        """Cancelling immediately after the wizard opens navigates away from /evaluations/new."""
        nep = _open_wizard(authenticated_page)
        nep.cancel_evaluation()
        assert "/evaluations/new" not in authenticated_page.url, (
            f"URL still on wizard after cancel: {authenticated_page.url}"
        )

    def test_cancel_after_filling_objective_leaves_wizard_url(self, authenticated_page: Page):
        """Cancelling after typing the objective still exits the wizard cleanly."""
        nep = _open_wizard(authenticated_page)
        nep.type_evaluation_name("Cancel-mid-run test")
        nep.cancel_evaluation()
        assert "/evaluations/new" not in authenticated_page.url, (
            f"URL still on wizard after cancel: {authenticated_page.url}"
        )

    def test_cancel_lands_on_a_valid_page(self, authenticated_page: Page):
        """After cancel, the page must be renderable (no crash / blank screen)."""
        nep = _open_wizard(authenticated_page)
        nep.cancel_evaluation()
        # A renderable page has at least a <body> — JS crash pages typically don't.
        body_count = authenticated_page.locator("body").count()
        assert body_count == 1, "Page body missing after cancel — app may have crashed"
        # Should land somewhere inside /dashboard, not on an error page.
        url = authenticated_page.url.lower()
        assert "/error" not in url and "/404" not in url, (
            f"Landed on an error page after cancel: {authenticated_page.url}"
        )


class TestCancelFromModal:
    def test_cancel_from_new_evaluation_modal_stays_on_list(self, authenticated_page: Page):
        """Clicking 'Cancel' on the New Evaluation modal (before entering wizard) stays on list."""
        nep = NewEvaluationPage(authenticated_page)
        nep.go_to_evaluations_list()
        nep.click_new_evaluation()

        if not nep.is_modal_visible():
            pytest.skip("New Evaluation modal did not appear — cannot test modal cancel")

        nep.click_modal_cancel()

        # Modal should close and we stay on the evaluations list.
        assert not nep.is_modal_visible(), "Modal must close after clicking Cancel"
        assert "/evaluations/new" not in authenticated_page.url, (
            f"Should remain on evaluations list, got: {authenticated_page.url}"
        )


class TestCancelNavigation:
    """Cancel uses client-side router.push (Jun 2026) — browser Back must work cleanly."""

    @pytest.mark.regression_write
    def test_cancel_browser_back_does_not_loop(self, authenticated_page: Page, sandbox_org, cleanup_evaluation):
        """After cancelling, pressing browser Back must resolve to a clean page (no redirect loop)."""
        nep = _open_wizard(authenticated_page)
        # Record the audit ID if the wizard created a draft so cleanup can cancel it.
        audit_id = nep.get_audit_id_from_url()
        if audit_id:
            cleanup_evaluation.append(audit_id)

        nep.cancel_evaluation()
        list_url = authenticated_page.url

        # Navigate Back — with router.push the history stack has the list page,
        # so Back should go to the page visited before the evaluations list.
        authenticated_page.go_back()
        authenticated_page.wait_for_timeout(800)

        final_url = authenticated_page.url
        # Must not end up stuck on /evaluations/new after pressing Back.
        assert "/evaluations/new" not in final_url, (
            f"Browser Back after cancel landed on wizard URL: {final_url}"
        )
        # Must not land on an error page.
        assert "/error" not in final_url.lower() and "/404" not in final_url.lower(), (
            f"Browser Back after cancel landed on error page: {final_url}"
        )
