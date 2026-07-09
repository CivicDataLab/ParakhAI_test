"""
Locators for the Evaluator role dashboard, assignments, and evaluations.
Base URL: /dashboard/auditor
"""


class EvaluatorRoleLocators:
    # ── Sidebar ────────────────────────────────────────────────────────────────
    # Drop `nav`/`li` parent gates — the sidebar wrapper is a CSS-modules
    # `<div class="Sidebar__root__xxx">`, not a semantic <nav>/<li>. The text
    # marker alone is reliable enough. See tasks/lessons.md (2026-05-18).
    SIDEBAR_HOME = "a:has-text('Home')"
    SIDEBAR_ASSIGNED_MODELS = "text=Assigned Models"
    # Use anchor selector to avoid strict-mode conflict with EVALUATIONS_PAGE_HEADING
    SIDEBAR_EVALUATIONS = "a:has-text('Evaluations')"
    SIDEBAR_SWITCH_ROLES = "text=Switch Roles"

    # ── Home dashboard ─────────────────────────────────────────────────────────
    OVERVIEW_HEADING = "text=Overview"
    # text= engine does exact/normalized match; works when labels are stable
    STAT_INVITATIONS_RECEIVED = "text=Invitations Received"
    STAT_EVALUATION_RUNS = "text=Evaluations Completed"   # renamed from "Evaluation Runs"
    STAT_TEST_CASES = "text=Test Cases Evaluated"         # renamed from "Test Cases"
    STAT_ISSUES_FLAGGED = "text=Issues Flagged"

    PENDING_INVITATIONS_HEADING = (
        "h2:has-text('Pending Invitations'), h3:has-text('Pending Invitations'), "
        ":has-text('Pending Invitations'):not(button):not(a)"
    )
    NO_PENDING_INVITATIONS = (
        ":has-text('No pending invitations'), :has-text('no pending')"
    )
    ACTIVE_ASSIGNMENTS_HEADING = (
        "h2:has-text('Active Assignments'), h3:has-text('Active Assignments'), "
        ":has-text('Active Assignments'):not(button):not(a)"
    )

    # ── Assigned Models (My Assignments) ──────────────────────────────────────
    ASSIGNMENTS_PAGE_HEADING = (
        "h1:has-text('Assignments'), h2:has-text('Assignments'), "
        ":has-text('My Assignments'):not(nav):not(a)"
    )
    # `:text()` is case-sensitive strict-substring on the text engine and
    # misses the styled tab button. `[class*='filter']` is CSS-modules
    # case-sensitive too. Drop both parent gates and use `:has-text()` on the
    # button — substring is fine because the only short-"All" button on the
    # page is the filter tab.
    FILTER_ALL = "button:has-text('All'), [role='tab']:has-text('All')"
    FILTER_PENDING = "button:has-text('Pending'), [role='tab']:has-text('Pending')"
    FILTER_ACCEPTED = "button:has-text('Accepted'), [role='tab']:has-text('Accepted')"
    FILTER_IN_PROGRESS = (
        "button:has-text('In Progress'), [role='tab']:has-text('In Progress')"
    )
    FILTER_COMPLETED = "button:has-text('Completed'), [role='tab']:has-text('Completed')"
    FILTER_DECLINED = "button:has-text('Declined'), [role='tab']:has-text('Declined')"
    NO_ASSIGNMENTS_MESSAGE = ":has-text('No assignments found'), :has-text('No assignments')"

    # ── Evaluations (Evaluator) ────────────────────────────────────────────────
    EVALUATIONS_PAGE_HEADING = "text=Evaluations"
    EVAL_FILTER_DRAFT = "text=Draft"
    EVAL_FILTER_PENDING = "text=Pending"
    EVAL_FILTER_IN_PROGRESS = "text=In Progress"
    EVAL_FILTER_RUNNING = EVAL_FILTER_IN_PROGRESS  # backward-compat alias
    EVAL_FILTER_COMPLETED = "text=Completed"
    EVAL_FILTER_FAILED = "text=Failed"
    NO_EVALUATIONS_MESSAGE = "text=No evaluations found"
    VIEW_ASSIGNMENTS_LINK = "text=View Assignments"

    # ── Pending invitation row actions (write-side regression) ────────────────
    # TODO: verify selectors via Playwright MCP — buttons live in the row of
    # the Pending Invitations table.
    PENDING_ROW = (
        "[class*='pending'] tr, "
        "[class*='invitation'] tr, "
        "tr:has(button:has-text('Accept'))"
    )
    ACCEPT_BUTTON = "button:has-text('Accept')"
    DECLINE_BUTTON = "button:has-text('Decline')"
    FILTER_TAB_ACCEPTED = "button:has-text('Accepted'), [role='tab']:has-text('Accepted')"
    FILTER_TAB_DECLINED = "button:has-text('Declined'), [role='tab']:has-text('Declined')"
    FILTER_TAB_PENDING_LIST = "button:has-text('Pending'), [role='tab']:has-text('Pending')"
