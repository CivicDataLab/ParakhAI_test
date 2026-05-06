"""
Locators for the Evaluators management page (AI Maker role).
URL: /dashboard/ai-maker/{org_id}/auditors
"""


class EvaluatorsLocators:
    # ── Page structure ─────────────────────────────────────────────────────────
    PAGE_HEADING = "text=Evaluators"
    PAGE_SUBHEADING = "text=Manage evaluators"
    ADD_EVALUATOR_BUTTON = "button:text('Add Evaluator'), text=Add Evaluator"

    # ── Table ──────────────────────────────────────────────────────────────────
    TABLE = "table, [class*='table'], [role='table']"
    TABLE_HEADER_USERNAME = "th:text('Username'), text=Username"
    TABLE_HEADER_EMAIL = "th:text('Email'), text=Email"
    TABLE_HEADER_NAME = "th:text('Name'), text=Name"
    TABLE_HEADER_JOINED = "th:text('Joined'), text=Joined"
    TABLE_HEADER_ACTIONS = "th:text('Actions'), text=Actions"

    TABLE_ROW = "tbody tr, [class*='row']"
    EVALUATOR_USERNAME = "td:nth-child(2), [class*='username']"
    EVALUATOR_EMAIL = "td:nth-child(3), [class*='email']"
    EVALUATOR_NAME = "td:nth-child(4), [class*='name']"
    EVALUATOR_JOINED = "td:nth-child(5), [class*='joined']"
    REMOVE_BUTTON = "text=Remove, button:text('Remove')"
    REMOVE_ICON = "[class*='delete'], [class*='trash'], svg[class*='delete']"

    # ── Helper for data-driven evaluator assertions ────────────────────────────
    @staticmethod
    def evaluator_email_text(email: str) -> str:
        """Build a Playwright text selector for an evaluator's email cell."""
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
