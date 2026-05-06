"""Selectors for the evaluation detail page (/dashboard/ai-maker/{org}/evaluations/{id})."""


class EvaluationDetailLocators:
    # Page-level
    BACK_TO_LIST = "button:has-text('Back to List'), a:has-text('Back to List')"
    DETAIL_STATUS_COMPLETED = "text=COMPLETED"

    # Overview card
    OVERVIEW_HEADING = "text=Evaluation Overview"
    OVERVIEW_EVAL_ID = "text=Evaluation ID"

    # Summary cards
    SUMMARY_HEADING = "text=Evaluation Summary"
    SUMMARY_PASS_RATE = "text=TOTAL PASS RATE"

    # Risk level cards
    RISK_HIGH = "text=HIGH RISK"
    RISK_MEDIUM = "text=MEDIUM RISK"
    RISK_LOW = "text=LOW RISK"

    # Top-level page tabs (Overview / Test Cases / Results)
    # TODO: verify selector via Playwright MCP — opub-ui Tabs typically render
    # as role='tab'; matching by accessible name covers most variants.
    TAB_OVERVIEW = (
        "[role='tab']:has-text('Overview'), "
        "button:has-text('Overview'):not(:has-text('Module'))"
    )
    TAB_TEST_CASES = (
        "[role='tab']:has-text('Test Cases'), "
        "button:has-text('Test Cases')"
    )
    TAB_RESULTS = (
        "[role='tab']:has-text('Results'), "
        "button[role='tab']:has-text('Results')"
    )

    # Tab panel content markers (used to assert that the right panel is showing)
    TEST_CASES_PANEL = (
        "[role='tabpanel']:has(table), "
        "[class*='test-case'] table, "
        "table:has(:text('Input'))"
    )
    RESULTS_PANEL = (
        "[role='tabpanel']:has(:text('Results')), "
        "[class*='results-section'], "
        ":text('Module-wise')"
    )

    # Test cases / results table rows
    TEST_CASES_ROW = "[role='tabpanel'] tbody tr, table tbody tr"
    RESULTS_ROW = "[role='tabpanel'] tbody tr, table tbody tr"
    RESULTS_ROW_EXPAND_BUTTON = (
        "button[aria-expanded='false'], "
        "[role='button'][aria-expanded='false']"
    )

    # Module-wise results tabs (sub-tabs within the Results section)
    MODULE_TAB_HALLUCINATION = "text=Hallucination and MisInformation"
    MODULE_TAB_BIAS = "text=Bias and Fairness"

    # Sample issues
    SAMPLE_ISSUES_HEADING = "text=Sample Issues"
    ISSUE_EXPAND_TRIGGER = "button[aria-expanded], [class*='accordion'] button"

    # Report download
    DOWNLOAD_REPORT_BUTTON = (
        "button:has-text('Download Report'), a:has-text('Download Report')"
    )
