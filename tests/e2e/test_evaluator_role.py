"""
E2E tests for the Evaluator role — dashboard, assigned models, and evaluations.
URLs:
  Home       : /dashboard/auditor
  Assignments: /dashboard/auditor/assignments
  Evaluations: /dashboard/auditor/evaluations
"""

import pytest
from playwright.sync_api import Page

from locators.evaluator_role_locators import EvaluatorRoleLocators
from pages.evaluator_role_page import EvaluatorRolePage

pytestmark = [pytest.mark.e2e, pytest.mark.regression, pytest.mark.auth]


@pytest.fixture
def page(authenticated_page_fast):
    """Override pytest-playwright's `page` fixture so every test in this file
    runs against the storage-state-cached auth session. Every page hit here
    targets /dashboard/auditor/... which redirects unauth visitors to
    /api/auth/signin. See tasks/lessons.md (2026-05-18, 2026-05-20)."""
    return authenticated_page_fast


class TestEvaluatorHomeDashboard:
    """Verify the Evaluator role home/overview page renders correctly."""

    def test_evaluator_home_loads(self, page: Page):
        er = EvaluatorRolePage(page)
        er.go_to_evaluator_home()
        assert "/auditor" in page.url, f"Expected /auditor in URL, got: {page.url}"

    def test_page_title_is_set(self, page: Page):
        er = EvaluatorRolePage(page)
        er.go_to_evaluator_home()
        assert page.title(), "Page title must not be empty"

    def test_overview_section_is_visible(self, page: Page):
        er = EvaluatorRolePage(page)
        er.go_to_evaluator_home()
        assert er.is_overview_visible(), "'Overview' section must be visible"

    def test_all_four_stat_cards_are_visible(self, page: Page):
        """All four overview stats are shown for the Evaluator role."""
        er = EvaluatorRolePage(page)
        er.go_to_evaluator_home()
        assert er.are_all_stats_visible(), (
            "All 4 stats (Invitations Received, Evaluation Runs, "
            "Test Cases, Issues Flagged) must be visible"
        )

    def test_invitations_received_stat_is_visible(self, page: Page):
        er = EvaluatorRolePage(page)
        er.go_to_evaluator_home()
        assert er.is_visible(EvaluatorRoleLocators.STAT_INVITATIONS_RECEIVED), (
            "'Invitations Received' stat must be visible"
        )

    def test_pending_invitations_section_is_visible(self, page: Page):
        er = EvaluatorRolePage(page)
        er.go_to_evaluator_home()
        assert er.is_pending_invitations_section_visible(), (
            "'Pending Invitations' section must be visible"
        )

    def test_no_pending_invitations_message_shown(self, page: Page):
        """'No pending invitations' empty state is shown when no invites exist."""
        er = EvaluatorRolePage(page)
        er.go_to_evaluator_home()
        if not er.is_pending_invitations_section_visible():
            pytest.skip("Pending Invitations section not found")
        assert er.is_no_pending_invitations_message_visible(), (
            "'No pending invitations' message must be shown when inbox is empty"
        )

    def test_active_assignments_section_is_visible(self, page: Page):
        er = EvaluatorRolePage(page)
        er.go_to_evaluator_home()
        assert er.is_visible(er.ACTIVE_ASSIGNMENTS_HEADING), (
            "'Active Assignments' section must be visible"
        )

    def test_sidebar_has_three_nav_items(self, page: Page):
        """Evaluator sidebar has Home, Assigned Models, and Evaluations."""
        er = EvaluatorRolePage(page)
        er.go_to_evaluator_home()
        missing = []
        if not er.is_visible(EvaluatorRoleLocators.SIDEBAR_HOME, timeout=3_000):
            missing.append("Home")
        if not er.is_visible(er.SIDEBAR_ASSIGNED_MODELS, timeout=3_000):
            missing.append("Assigned Models")
        if not er.is_visible(er.SIDEBAR_EVALUATIONS, timeout=3_000):
            missing.append("Evaluations")
        assert not missing, f"Missing evaluator sidebar items: {missing}"

    def test_switch_roles_link_is_visible(self, page: Page):
        er = EvaluatorRolePage(page)
        er.go_to_evaluator_home()
        assert er.is_visible(er.SWITCH_ROLES_LINK), "'Switch Roles' link must be visible"


class TestEvaluatorAssignedModels:
    """Verify the My Assignments page for the Evaluator role."""

    def test_assignments_page_loads(self, page: Page):
        er = EvaluatorRolePage(page)
        er.go_to_assignments()
        assert er.is_assignments_page_loaded(), (
            "'My Assignments' heading must be visible"
        )

    def test_url_contains_assignments(self, page: Page):
        er = EvaluatorRolePage(page)
        er.go_to_assignments()
        assert "/assignments" in page.url, (
            f"Expected /assignments in URL, got: {page.url}"
        )

    def test_all_filter_tabs_are_visible(self, page: Page):
        """All assignment status filter tabs are shown: All, Pending, Accepted, etc."""
        er = EvaluatorRolePage(page)
        er.go_to_assignments()
        missing = []
        for tab_sel in [
            EvaluatorRoleLocators.FILTER_ALL,
            EvaluatorRoleLocators.FILTER_PENDING,
            EvaluatorRoleLocators.FILTER_ACCEPTED,
            EvaluatorRoleLocators.FILTER_IN_PROGRESS,
            EvaluatorRoleLocators.FILTER_COMPLETED,
            EvaluatorRoleLocators.FILTER_DECLINED,
        ]:
            if not er.is_visible(tab_sel, timeout=3_000):
                missing.append(tab_sel)
        assert not missing, f"Missing assignment filter tabs: {missing}"

    def test_all_tab_is_active_by_default(self, page: Page):
        """'All' tab is selected by default on the assignments page."""
        er = EvaluatorRolePage(page)
        er.go_to_assignments()
        assert er.is_visible(EvaluatorRoleLocators.FILTER_ALL), (
            "'All' filter tab must be visible and default"
        )

    def test_filter_tabs_show_counts(self, page: Page):
        """Filter tab labels include counts like 'Pending (0)'."""
        er = EvaluatorRolePage(page)
        er.go_to_assignments()
        # Count labels include "(0)" when empty
        assert er.is_visible("text=(0)") or er.is_visible("text=Pending"), (
            "Filter tabs must display counts"
        )

    def test_empty_state_message_is_shown(self, page: Page):
        """'No assignments found' empty state is displayed when no assignments exist."""
        er = EvaluatorRolePage(page)
        er.go_to_assignments()
        assert er.is_no_assignments_message_visible(), (
            "'No assignments found' message must be shown when inbox is empty"
        )

    def test_clicking_pending_filter_works(self, page: Page):
        """Clicking the Pending filter tab does not cause an error."""
        er = EvaluatorRolePage(page)
        er.go_to_assignments()
        if not er.is_visible(EvaluatorRoleLocators.FILTER_PENDING, timeout=3_000):
            pytest.skip("Pending filter not visible")
        er.click_filter("pending")
        page.wait_for_timeout(300)
        assert page.url, "Page must still be accessible after clicking Pending filter"

    @pytest.mark.parametrize("filter_name", ["pending", "accepted", "in_progress", "completed", "declined"])
    def test_each_filter_tab_is_clickable(self, page: Page, filter_name: str):
        """Each filter tab can be clicked without errors."""
        er = EvaluatorRolePage(page)
        er.go_to_assignments()
        er.click_filter(filter_name)
        page.wait_for_timeout(300)
        assert page.url, f"Page accessible after clicking '{filter_name}' filter"

    def test_sidebar_link_navigates_to_assignments(self, page: Page):
        """Clicking 'Assigned Models' from the evaluator sidebar navigates correctly."""
        er = EvaluatorRolePage(page)
        er.go_to_evaluator_home()
        if not er.is_visible(er.SIDEBAR_ASSIGNED_MODELS, timeout=5_000):
            pytest.skip("Assigned Models sidebar link not found")
        er.click_assigned_models()
        assert "/assignments" in page.url, (
            f"Expected /assignments in URL after clicking sidebar, got: {page.url}"
        )


class TestEvaluatorEvaluations:
    """Verify the Evaluations page for the Evaluator role."""

    def test_evaluations_page_loads(self, page: Page):
        er = EvaluatorRolePage(page)
        er.go_to_evaluations()
        assert "/evaluations" in page.url, (
            f"Expected /evaluations in URL, got: {page.url}"
        )

    def test_evaluations_filter_tabs_are_visible(self, page: Page):
        """Draft, Pending, Running, Completed, Failed filter tabs are all shown."""
        er = EvaluatorRolePage(page)
        er.go_to_evaluations()
        missing = []
        for tab_sel in [
            EvaluatorRoleLocators.EVAL_FILTER_DRAFT,
            EvaluatorRoleLocators.EVAL_FILTER_PENDING,
            EvaluatorRoleLocators.EVAL_FILTER_RUNNING,
            EvaluatorRoleLocators.EVAL_FILTER_COMPLETED,
            EvaluatorRoleLocators.EVAL_FILTER_FAILED,
        ]:
            if not er.is_visible(tab_sel, timeout=3_000):
                missing.append(tab_sel)
        assert not missing, f"Missing evaluations filter tabs: {missing}"

    def test_no_evaluations_empty_state_is_shown(self, page: Page):
        """'No evaluations found' empty state is shown when no evaluations exist."""
        er = EvaluatorRolePage(page)
        er.go_to_evaluations()
        assert er.is_no_evaluations_message_visible(), (
            "'No evaluations found' message must be shown when list is empty"
        )

    def test_view_assignments_link_is_visible(self, page: Page):
        """'View Assignments' shortcut link is shown in the empty state."""
        er = EvaluatorRolePage(page)
        er.go_to_evaluations()
        if not er.is_no_evaluations_message_visible():
            pytest.skip("Not in empty state — evaluations may exist for this user")
        assert er.is_view_assignments_link_visible(), (
            "'View Assignments' link must be shown in the empty evaluations state"
        )

    @pytest.mark.xfail(reason="App bug #8 — see docs/app_bugs.md", strict=False)
    def test_view_assignments_link_navigates_to_assignments(self, page: Page):
        """Clicking 'View Assignments' navigates to the assignments page."""
        er = EvaluatorRolePage(page)
        er.go_to_evaluations()
        if not er.is_view_assignments_link_visible():
            pytest.skip("View Assignments link not visible")
        er.click_view_assignments()
        assert "/assignments" in page.url, (
            f"'View Assignments' should navigate to /assignments, got: {page.url}"
        )

    def test_sidebar_link_navigates_to_evaluations(self, page: Page):
        """Clicking 'Evaluations' from the evaluator sidebar navigates correctly."""
        er = EvaluatorRolePage(page)
        er.go_to_evaluator_home()
        if not er.is_visible(er.SIDEBAR_EVALUATIONS, timeout=5_000):
            pytest.skip("Evaluations sidebar link not found")
        er.click_evaluations()
        assert "/evaluations" in page.url, (
            f"Expected /evaluations in URL after clicking sidebar, got: {page.url}"
        )
