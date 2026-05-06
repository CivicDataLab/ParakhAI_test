"""
Locators for the Evaluator role dashboard, assignments, and evaluations.
Base URL: /dashboard/auditor
"""


class EvaluatorRoleLocators:
    # ── Sidebar ────────────────────────────────────────────────────────────────
    SIDEBAR_HOME = "nav a:text('Home'), li a:text('Home')"
    SIDEBAR_ASSIGNED_MODELS = "text=Assigned Models"
    SIDEBAR_EVALUATIONS = "text=Evaluations"
    SIDEBAR_SWITCH_ROLES = "text=Switch Roles"

    # ── Home dashboard ─────────────────────────────────────────────────────────
    OVERVIEW_HEADING = "text=Overview"
    STAT_INVITATIONS_RECEIVED = "text=Invitations Received"
    STAT_EVALUATION_RUNS = "text=Evaluation Runs"
    STAT_TEST_CASES = "text=Test Cases"
    STAT_ISSUES_FLAGGED = "text=Issues Flagged"

    PENDING_INVITATIONS_HEADING = "text=Pending Invitations"
    NO_PENDING_INVITATIONS = "text=No pending invitations"
    ACTIVE_ASSIGNMENTS_HEADING = "text=Active Assignments"

    # ── Assigned Models (My Assignments) ──────────────────────────────────────
    ASSIGNMENTS_PAGE_HEADING = "text=My Assignments"
    FILTER_ALL = "button:text('All'), [class*='filter']:text('All')"
    FILTER_PENDING = "text=Pending"
    FILTER_ACCEPTED = "text=Accepted"
    FILTER_IN_PROGRESS = "text=In Progress"
    FILTER_COMPLETED = "text=Completed"
    FILTER_DECLINED = "text=Declined"
    NO_ASSIGNMENTS_MESSAGE = "text=No assignments found"

    # ── Evaluations (Evaluator) ────────────────────────────────────────────────
    EVALUATIONS_PAGE_HEADING = "text=Evaluations"
    EVAL_FILTER_DRAFT = "text=Draft"
    EVAL_FILTER_PENDING = "text=Pending"
    EVAL_FILTER_RUNNING = "text=Running"
    EVAL_FILTER_COMPLETED = "text=Completed"
    EVAL_FILTER_FAILED = "text=Failed"
    NO_EVALUATIONS_MESSAGE = "text=No evaluations found"
    VIEW_ASSIGNMENTS_LINK = "text=View Assignments"
