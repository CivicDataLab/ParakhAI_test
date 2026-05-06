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
        self.wait_for_load("domcontentloaded")
        return self

    def go_to_assignments(self) -> "EvaluatorRolePage":
        self.navigate(self.assignments_url)
        self.wait_for_load("domcontentloaded")
        return self

    def go_to_evaluations(self) -> "EvaluatorRolePage":
        self.navigate(self.evaluations_url)
        self.wait_for_load("domcontentloaded")
        return self

    def click_assigned_models(self) -> None:
        self.click(self.SIDEBAR_ASSIGNED_MODELS)
        self.wait_for_load("domcontentloaded")

    def click_evaluations(self) -> None:
        self.click(self.SIDEBAR_EVALUATIONS)
        self.wait_for_load("domcontentloaded")

    def click_switch_roles(self) -> None:
        self.click(self.SWITCH_ROLES_LINK)
        self.wait_for_load("domcontentloaded")

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
        self.wait_for_load("domcontentloaded")
