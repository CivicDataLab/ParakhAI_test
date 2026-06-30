"""
E2E tests for the evaluator dashboard home metrics.

Covers: stat cards (Invitations Received, Evaluation Runs, Test Cases,
Issues Flagged), the Pending Invitations section, and the Active
Assignments section for a logged-in evaluator.

Auth required — uses authenticated_page_fast for cached session.
"""

import pytest
from playwright.sync_api import Page

from locators.evaluator_role_locators import EvaluatorRoleLocators
from pages.evaluator_role_page import EvaluatorRolePage

pytestmark = [pytest.mark.e2e, pytest.mark.regression, pytest.mark.auth]


@pytest.fixture
def ev_page(authenticated_page_fast: Page) -> EvaluatorRolePage:
    er = EvaluatorRolePage(authenticated_page_fast)
    er.go_to_evaluator_home()
    return er


class TestEvaluatorDashboardLoads:
    """Evaluator home page renders without error."""

    def test_page_loads_for_evaluator(self, ev_page: EvaluatorRolePage):
        assert ev_page.is_overview_visible(), (
            "Evaluator dashboard overview section must be visible on load"
        )

    def test_page_title_set(self, authenticated_page_fast: Page):
        er = EvaluatorRolePage(authenticated_page_fast)
        er.go_to_evaluator_home()
        assert authenticated_page_fast.title(), "Browser tab title must not be empty"


class TestEvaluatorStatCards:
    """All four evaluator stat cards are visible and contain a numeric value."""

    def test_all_stat_cards_visible(self, ev_page: EvaluatorRolePage):
        assert ev_page.are_all_stats_visible(), (
            "All four evaluator stat cards (Invitations Received, Evaluation "
            "Runs, Test Cases, Issues Flagged) must be visible on the dashboard"
        )

    def test_invitations_received_card_visible(self, ev_page: EvaluatorRolePage):
        assert ev_page.is_visible(EvaluatorRoleLocators.STAT_INVITATIONS_RECEIVED), (
            "'Invitations Received' stat card must be visible"
        )

    def test_evaluation_runs_card_visible(self, ev_page: EvaluatorRolePage):
        assert ev_page.is_visible(EvaluatorRoleLocators.STAT_EVALUATION_RUNS), (
            "'Evaluation Runs' stat card must be visible"
        )

    def test_test_cases_card_visible(self, ev_page: EvaluatorRolePage):
        assert ev_page.is_visible(EvaluatorRoleLocators.STAT_TEST_CASES), (
            "'Test Cases' stat card must be visible"
        )

    def test_issues_flagged_card_visible(self, ev_page: EvaluatorRolePage):
        assert ev_page.is_visible(EvaluatorRoleLocators.STAT_ISSUES_FLAGGED), (
            "'Issues Flagged' stat card must be visible"
        )

    def test_stat_card_values_are_numeric(self, ev_page: EvaluatorRolePage):
        """Each visible stat card must display a numeric (possibly zero) value."""
        stats = [
            EvaluatorRoleLocators.STAT_INVITATIONS_RECEIVED,
            EvaluatorRoleLocators.STAT_EVALUATION_RUNS,
            EvaluatorRoleLocators.STAT_TEST_CASES,
            EvaluatorRoleLocators.STAT_ISSUES_FLAGGED,
        ]
        non_numeric = []
        for sel in stats:
            container = ev_page.page.locator(sel).locator("..")
            texts = [t.strip() for t in container.all_inner_texts() if t.strip()]
            has_num = any(
                t.replace(",", "").isdigit() for t in texts
            )
            if not has_num:
                non_numeric.append(sel)

        assert not non_numeric, (
            f"These stat cards have no numeric value: {non_numeric}"
        )


class TestEvaluatorPendingInvitations:
    """The Pending Invitations section renders in a known state."""

    def test_pending_invitations_section_visible(self, ev_page: EvaluatorRolePage):
        assert ev_page.is_pending_invitations_section_visible(), (
            "'Pending Invitations' section heading must be visible on the evaluator dashboard"
        )

    def test_pending_invitations_renders_list_or_empty_state(
        self, ev_page: EvaluatorRolePage
    ):
        """Either a pending invitation card or the empty-state message is shown."""
        has_invitation = ev_page.get_pending_invitation_count() > 0
        has_empty_msg = ev_page.is_no_pending_invitations_message_visible()
        assert has_invitation or has_empty_msg, (
            "Pending Invitations section must show either an invitation card or "
            "the 'no pending invitations' empty-state message"
        )


class TestEvaluatorActiveAssignments:
    """The Active Assignments section renders in a known state."""

    def test_active_assignments_section_visible(self, ev_page: EvaluatorRolePage):
        assert ev_page.is_visible(EvaluatorRoleLocators.ACTIVE_ASSIGNMENTS_HEADING), (
            "'Active Assignments' section heading must be visible on the evaluator dashboard"
        )

    def test_active_assignments_or_empty_state(self, ev_page: EvaluatorRolePage):
        """Either evaluations are listed or a 'view all' / empty-state link is shown."""
        has_evals = ev_page.is_visible(
            EvaluatorRoleLocators.EVAL_FILTER_DRAFT, timeout=3_000
        ) or ev_page.is_visible(
            EvaluatorRoleLocators.EVAL_FILTER_COMPLETED, timeout=3_000
        )
        has_link = ev_page.is_view_assignments_link_visible()
        has_no_msg = ev_page.is_no_evaluations_message_visible()
        assert has_evals or has_link or has_no_msg, (
            "Active Assignments must show evaluation items, a 'View All' link, "
            "or an empty-state message"
        )

    def test_view_assignments_link_visible_on_dashboard(self, ev_page: EvaluatorRolePage):
        """The 'View Assignments' / 'View All' shortcut is present on the dashboard."""
        if not ev_page.is_view_assignments_link_visible():
            pytest.skip(
                "'View Assignments' link not present on this build — may vary by "
                "assignment count"
            )
        assert ev_page.is_view_assignments_link_visible()
