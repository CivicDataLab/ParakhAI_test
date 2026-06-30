"""Locators for the playground (manual) evaluation workspace.

This UI renders inside the New Evaluation wizard when evaluation mode is
set to Manual and the user has advanced to the Test Cases tab.
URL: /dashboard/ai-maker/{org_id}/evaluations/new?auditId={id}
"""


class PlaygroundLocators:
    # ── Prompt input & model call ──────────────────────────────────────────────
    PROMPT_INPUT = (
        "textarea[placeholder*='prompt' i], "
        "textarea[placeholder*='input' i], "
        "textarea[aria-label*='prompt' i], "
        "[class*='prompt' i] textarea"
    )
    CALL_MODEL_BUTTON = (
        "button:has-text('Call Model'), "
        "button:has-text('Get Response'), "
        "button:has-text('Submit Prompt')"
    )
    MODEL_OUTPUT_PANEL = (
        "[class*='output' i]:not(button), "
        "[aria-label*='output' i], "
        "[class*='response' i]:not(button)"
    )
    MODEL_LOADING_INDICATOR = (
        "[class*='loading' i]:not([aria-hidden='true']), "
        "[class*='spinner' i], "
        "button:has-text('Generating')"
    )

    # ── Issue submission panel ─────────────────────────────────────────────────
    # The "Add Issue" / "Submit" panel renders after a model response
    ADD_ISSUE_BUTTON = (
        "button:has-text('Add Issue'), "
        "button:has-text('Flag Issue'), "
        "button:has-text('Submit Issue')"
    )
    ISSUE_METRIC_DROPDOWN = (
        "select[name*='metric' i], "
        "[aria-label*='metric' i], "
        "[class*='metric' i] select, "
        "[class*='metric' i] [role='combobox']"
    )
    ISSUE_VERDICT_PASS = (
        "input[type='radio'][value*='PASS' i], "
        "button:has-text('Pass'), "
        "label:has-text('Pass') input"
    )
    ISSUE_VERDICT_FAIL = (
        "input[type='radio'][value*='FAIL' i], "
        "button:has-text('Fail'), "
        "label:has-text('Fail') input"
    )
    ISSUE_SEVERITY_DROPDOWN = (
        "select[name*='severity' i], "
        "[aria-label*='severity' i], "
        "[class*='severity' i] select, "
        "[class*='severity' i] [role='combobox']"
    )
    ISSUE_REASON_TEXTAREA = (
        "textarea[name*='reason' i], "
        "textarea[placeholder*='reason' i], "
        "[class*='reason' i] textarea"
    )
    ISSUE_SUBMIT_BUTTON = (
        "button:has-text('Submit'), "
        "button[type='submit']:near(textarea)"
    )

    # ── AI-assist buttons ──────────────────────────────────────────────────────
    GENERATE_REASON_BUTTON = (
        "button:has-text('Generate Reason'), "
        "button:has-text('Generate with AI'), "
        "button:has-text('AI Reason')"
    )
    GENERATE_IDEAL_OUTPUT_BUTTON = (
        "button:has-text('Generate Ideal Output'), "
        "button:has-text('Ideal Output')"
    )
    AI_ASSIST_LOADING = (
        "[class*='loading' i] :near(button:has-text('Generate')), "
        "button:has-text('Generating'):disabled"
    )

    # ── Test case counters (shown in module card / progress bar) ───────────────
    TEST_CASE_COUNTER = (
        "[data-testid='test-case-count'], "
        "[class*='counter' i]:has-text('Test Cases'), "
        ":has-text('Test Cases'):not(button)"
    )
    PASSED_COUNTER = (
        "[data-testid='passed-count'], "
        "[class*='counter' i]:has-text('Passed'), "
        ":has-text('Passed'):not(button)"
    )
    FAILED_COUNTER = (
        "[data-testid='failed-count'], "
        "[class*='counter' i]:has-text('Failed'), "
        ":has-text('Failed'):not(button)"
    )

    # ── Finish evaluation ──────────────────────────────────────────────────────
    FINISH_EVALUATION_BUTTON = "button:has-text('Finish Evaluation')"
    FINISH_CONFIRM_BUTTON = (
        "[role='dialog'] button:has-text('Confirm'), "
        "[role='dialog'] button:has-text('Finish'), "
        "[role='alertdialog'] button:has-text('Confirm')"
    )

    # ── Status badge ───────────────────────────────────────────────────────────
    STATUS_BADGE = (
        "[data-testid='audit-status'], "
        "[class*='status' i] [class*='badge' i], "
        "[class*='statusBadge' i]"
    )
    STATUS_PENDING_REVIEW = "text=PENDING_REVIEW, text=Pending Review"
    STATUS_IN_PROGRESS = "text=IN_PROGRESS, text=In Progress"
    STATUS_DRAFT = "text=DRAFT"
