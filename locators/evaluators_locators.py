"""
Locators for the Evaluators management page (AI Maker role).
URL: /dashboard/ai-maker/{org_id}/auditors

UI is a card grid (not a table). Each evaluator card carries:
  - avatar
  - display name
  - optional role label
  - a "Remove" button
"""


class EvaluatorsLocators:
    # ── Page structure ─────────────────────────────────────────────────────────
    PAGE_HEADING = "text=Evaluators"
    PAGE_SUBHEADING = "text=Manage evaluators"
    ADD_EVALUATOR_BUTTON = (
        "button:has-text('Add Evaluator'), "
        "[role='button']:has-text('Add Evaluator'), "
        "a:has-text('Add Evaluator')"
    )

    # ── Card grid ──────────────────────────────────────────────────────────────
    # Anchor on the per-card Remove action: unique per card and stable across
    # the opub-ui card variants. The action is rendered as plain text + icon,
    # not always wrapped in a <button>/<a> — so use the bare `text=` engine and
    # let it find the leaf element regardless of wrapper.
    REMOVE_BUTTON = "text=Remove"
    EVALUATOR_CARD = (
        "[class*='card' i]:has(:text('Remove')), "
        "[class*='Card']:has(:text('Remove'))"
    )

    # ── Helper for data-driven evaluator assertions ────────────────────────────
    @staticmethod
    def evaluator_name_text(name: str) -> str:
        """Build a Playwright text selector for an evaluator card's display name."""
        return f"text={name}"

    @staticmethod
    def evaluator_email_text(email: str) -> str:
        """Email is not surfaced in the card view; selector exists for write-side
        tests that inspect the Add Evaluator dialog."""
        return f"text={email}"

    # ── Add Evaluator dialog (write-side regression) ──────────────────────────
    ADD_DIALOG = "[role='dialog']:has-text('Add'), [role='dialog']:has-text('Auditor')"
    ADD_DIALOG_EMAIL_INPUT = (
        "[role='dialog'] input[type='email'], "
        "[role='dialog'] input[name*='email'], "
        "[role='dialog'] input[placeholder*='email']"
    )
    ADD_DIALOG_USER_RESULT = (
        "[role='dialog'] [class*='user-result'], "
        "[role='dialog'] [class*='avatar']:near(:text('@')), "
        "[role='dialog'] [class*='search-result']"
    )
    ADD_DIALOG_SUBMIT = (
        "[role='dialog'] button:has-text('Add'), "
        "[role='dialog'] button[type='submit']"
    )
    ADD_DIALOG_CANCEL = "[role='dialog'] button:has-text('Cancel'), [role='dialog'] [aria-label='Close']"
