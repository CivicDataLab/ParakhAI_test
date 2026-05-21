"""
Page object for the Evaluator role — dashboard, assigned models, evaluations.
Base URL: /dashboard/auditor
"""

from playwright.sync_api import Page

from locators.evaluator_role_locators import EvaluatorRoleLocators
from pages.base_page import BasePage
from utils.config import Config


class EvaluatorRolePage(BasePage):
    """Evaluator role dashboard, assignments, and evaluations pages."""

    # Sidebar
    SIDEBAR_ASSIGNED_MODELS = EvaluatorRoleLocators.SIDEBAR_ASSIGNED_MODELS
    SIDEBAR_EVALUATIONS = EvaluatorRoleLocators.SIDEBAR_EVALUATIONS
    SWITCH_ROLES_LINK = EvaluatorRoleLocators.SIDEBAR_SWITCH_ROLES

    # Home
    OVERVIEW_HEADING = EvaluatorRoleLocators.OVERVIEW_HEADING
    PENDING_INVITATIONS_HEADING = EvaluatorRoleLocators.PENDING_INVITATIONS_HEADING
    NO_PENDING_INVITATIONS = EvaluatorRoleLocators.NO_PENDING_INVITATIONS
    ACTIVE_ASSIGNMENTS_HEADING = EvaluatorRoleLocators.ACTIVE_ASSIGNMENTS_HEADING

    # Assignments
    ASSIGNMENTS_PAGE_HEADING = EvaluatorRoleLocators.ASSIGNMENTS_PAGE_HEADING
    NO_ASSIGNMENTS_MESSAGE = EvaluatorRoleLocators.NO_ASSIGNMENTS_MESSAGE

    # Evaluations
    NO_EVALUATIONS_MESSAGE = EvaluatorRoleLocators.NO_EVALUATIONS_MESSAGE
    VIEW_ASSIGNMENTS_LINK = EvaluatorRoleLocators.VIEW_ASSIGNMENTS_LINK

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.home_url = Config.url("/dashboard/auditor")
        self.assignments_url = Config.url("/dashboard/auditor/assignments")
        self.evaluations_url = Config.url("/dashboard/auditor/evaluations")

    # ── Navigation ─────────────────────────────────────────────────────────────

    def go_to_evaluator_home(self) -> "EvaluatorRolePage":
        self.navigate(self.home_url)
        self.wait_for_app_ready()
        self.skip_if_redirected_to_home("/auditor")
        return self

    def go_to_assignments(self) -> "EvaluatorRolePage":
        self.navigate(self.assignments_url)
        self.wait_for_app_ready()
        self.skip_if_redirected_to_home("/auditor/assignments")
        return self

    def go_to_evaluations(self) -> "EvaluatorRolePage":
        self.navigate(self.evaluations_url)
        self.wait_for_app_ready()
        self.skip_if_redirected_to_home("/auditor/evaluations")
        return self

    def click_assigned_models(self) -> None:
        self.click(self.SIDEBAR_ASSIGNED_MODELS)
        self.wait_for_app_ready()

    def click_evaluations(self) -> None:
        self.click(self.SIDEBAR_EVALUATIONS)
        self.wait_for_app_ready()

    def click_switch_roles(self) -> None:
        self.click(self.SWITCH_ROLES_LINK)
        self.wait_for_app_ready()

    # ── Home dashboard ─────────────────────────────────────────────────────────

    def is_overview_visible(self) -> bool:
        return self.is_visible(self.OVERVIEW_HEADING)

    def are_all_stats_visible(self) -> bool:
        return all([
            self.is_visible(EvaluatorRoleLocators.STAT_INVITATIONS_RECEIVED),
            self.is_visible(EvaluatorRoleLocators.STAT_EVALUATION_RUNS),
            self.is_visible(EvaluatorRoleLocators.STAT_TEST_CASES),
            self.is_visible(EvaluatorRoleLocators.STAT_ISSUES_FLAGGED),
        ])

    def is_pending_invitations_section_visible(self) -> bool:
        return self.is_visible(self.PENDING_INVITATIONS_HEADING)

    def is_no_pending_invitations_message_visible(self) -> bool:
        return self.is_visible(self.NO_PENDING_INVITATIONS)

    # ── Assignments ────────────────────────────────────────────────────────────

    def is_assignments_page_loaded(self) -> bool:
        return self.is_visible(self.ASSIGNMENTS_PAGE_HEADING)

    def click_filter(self, filter_name: str) -> None:
        filter_map = {
            "all": EvaluatorRoleLocators.FILTER_ALL,
            "pending": EvaluatorRoleLocators.FILTER_PENDING,
            "accepted": EvaluatorRoleLocators.FILTER_ACCEPTED,
            "in_progress": EvaluatorRoleLocators.FILTER_IN_PROGRESS,
            "completed": EvaluatorRoleLocators.FILTER_COMPLETED,
            "declined": EvaluatorRoleLocators.FILTER_DECLINED,
        }
        sel = filter_map.get(filter_name.lower())
        if sel:
            self.click(sel)

    def is_no_assignments_message_visible(self) -> bool:
        return self.is_visible(self.NO_ASSIGNMENTS_MESSAGE)

    # ── Evaluations ────────────────────────────────────────────────────────────

    def is_no_evaluations_message_visible(self) -> bool:
        return self.is_visible(self.NO_EVALUATIONS_MESSAGE)

    def is_view_assignments_link_visible(self) -> bool:
        return self.is_visible(self.VIEW_ASSIGNMENTS_LINK)

    def click_view_assignments(self) -> None:
        self.click(self.VIEW_ASSIGNMENTS_LINK)
        self.wait_for_app_ready()

    # ── Pending invitation actions (write-side) ────────────────────────────────

    def get_pending_invitation_count(self) -> int:
        """Count rows in the Pending Invitations section."""
        return self.page.locator(EvaluatorRoleLocators.PENDING_ROW).count()

    def click_accept_first_pending(self) -> bool:
        """Click the first pending invitation's Accept button.

        Returns True if a button was clicked, False if no pending row exists.
        """
        rows = self.page.locator(EvaluatorRoleLocators.PENDING_ROW)
        if rows.count() == 0:
            return False
        accept = rows.first.locator(EvaluatorRoleLocators.ACCEPT_BUTTON)
        if accept.count() == 0:
            return False
        accept.first.click()
        self.page.wait_for_timeout(800)
        return True

    def click_decline_first_pending(self) -> bool:
        """Click the first pending invitation's Decline button. See click_accept."""
        rows = self.page.locator(EvaluatorRoleLocators.PENDING_ROW)
        if rows.count() == 0:
            return False
        decline = rows.first.locator(EvaluatorRoleLocators.DECLINE_BUTTON)
        if decline.count() == 0:
            return False
        decline.first.click()
        self.page.wait_for_timeout(800)
        return True

    def open_filter_tab(self, name: str) -> bool:
        """Open the named filter tab on the assignments list. Returns True on click."""
        sel_map = {
            "pending": EvaluatorRoleLocators.FILTER_TAB_PENDING_LIST,
            "accepted": EvaluatorRoleLocators.FILTER_TAB_ACCEPTED,
            "declined": EvaluatorRoleLocators.FILTER_TAB_DECLINED,
        }
        sel = sel_map.get(name.lower())
        if not sel or not self.is_visible(sel, timeout=2_000):
            return False
        self.click(sel)
        self.page.wait_for_timeout(400)
        return True
