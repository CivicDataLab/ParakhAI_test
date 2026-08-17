"""Locators for the evaluator review section on a PENDING_REVIEW evaluation.

This section renders on the evaluation detail page when status is PENDING_REVIEW.
URL: /dashboard/ai-maker/{org_id}/evaluations/{eval_id}
"""


class EvaluatorReviewLocators:
    # ── Review section container ───────────────────────────────────────────────
    # The Jul 2026 single-page redesign dropped the "Evaluator Review" heading
    # in favour of plain prose ("This evaluation has AI generated observations
    # pending review by the evaluator." / "Ready to submit? ...") — confirmed
    # live against a real PENDING_REVIEW audit 2026-08-17. Keep the older
    # class/aria fallbacks in case a future redesign reintroduces a labelled
    # container, but the text fallbacks are what actually matches today.
    REVIEW_SECTION = (
        "[class*='review' i]:not(button), "
        "[aria-label*='review' i], "
        ":has-text('Evaluator Review'), "
        ":has-text('pending review by the evaluator'), "
        ":has-text('Ready to submit')"
    )

    # ── Results table rows ─────────────────────────────────────────────────────
    RESULT_ROW = "tbody tr, [class*='result' i] [class*='row' i]"
    RESULT_METRIC_CELL = "td:nth-child(1), [class*='metric' i]"
    RESULT_SCORE_CELL = "td:nth-child(2), [class*='score' i]"
    RESULT_RISK_CELL = "td:nth-child(3), [class*='risk' i]"

    # ── Evaluator override fields ──────────────────────────────────────────────
    OVERRIDE_SUCCESS_TOGGLE = (
        "input[type='checkbox'][name*='success' i], "
        "button[role='switch'][aria-label*='success' i], "
        "[class*='override' i] input[type='checkbox']"
    )
    OVERRIDE_RISK_DROPDOWN = (
        "select[name*='risk' i], "
        "[aria-label*='risk level' i], "
        "[class*='override' i] select"
    )
    OVERRIDE_REASON_TEXTAREA = (
        "textarea[name*='reason' i], "
        "textarea[placeholder*='reason' i], "
        "[class*='override' i] textarea"
    )

    # ── Submit review ──────────────────────────────────────────────────────────
    # The redesigned review panel's primary action is a bare "Submit" button
    # (confirmed live 2026-08-17 against a real PENDING_REVIEW audit — the
    # panel copy is "Ready to submit? ... " followed by a button literally
    # labelled "Submit", not "Submit Review"). Keep the older, more specific
    # labels as fallbacks in case they're reintroduced.
    SUBMIT_REVIEW_BUTTON = (
        "button:has-text('Submit Review'), "
        "button:has-text('Complete Review'), "
        "button:has-text('Finalize Review'), "
        "button:has-text('Submit')"
    )
    SUBMIT_REVIEW_CONFIRM = (
        "[role='dialog'] button:has-text('Submit'), "
        "[role='dialog'] button:has-text('Confirm'), "
        "[role='alertdialog'] button:has-text('Submit')"
    )

    # ── Post-submit states ─────────────────────────────────────────────────────
    REVIEW_SUBMITTED_BADGE = (
        "text=COMPLETED, "
        "[class*='status' i]:has-text('COMPLETED')"
    )
