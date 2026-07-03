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

    # ── Redesigned single-page layout (Jul 2026 frontend restructure) ─────────
    # The detail page no longer has Test Cases / Results tabs: everything
    # renders on one page (header → overview → recommendations → summary →
    # risk counters → "Evaluation Results" list with a sort dropdown).
    NAME_INPUT = "input[name='evaluationName']"
    RECOMMENDATIONS_HEADING = "text=Evaluator's Recommendations"
    RESULTS_HEADING = "text=Evaluation Results"
    RESULTS_SORT_SELECT = (
        "select[name='audit-results-sort'], "
        "input[name='audit-results-sort'], "
        "select:has(option:has-text('No. of Issues'))"
    )
    SUMMARY_TOTAL_TESTS = "text=TOTAL TEST CASES"
    SUMMARY_PASSED = "text=PASSED TESTS"
    SUMMARY_FAILED = "text=FAILED TESTS"
    SUMMARY_SKIPPED = "text=SKIPPED TESTS"
    TOTAL_ISSUES_HEADING = "text=Total Issues Identified"
    RESULT_INPUT_BLOCK = "text=/^Input \\d+$/"

    # Top-level page tabs (Overview / Test Cases / Results)
    # DEPRECATED (Jul 2026): the redesigned detail page has no tabs at all —
    # kept only so old references fail visibly instead of silently matching.
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

    # Report download — two-step flow (changed upstream Jun 2026):
    # user must click "Generate Report" first; "Download Report" appears after generation.
    GENERATE_REPORT_BUTTON = (
        "button:has-text('Generate Report'), "
        "a:has-text('Generate Report')"
    )
    DOWNLOAD_REPORT_BUTTON = (
        "button:has-text('Download Report'), "
        "a:has-text('Download Report')"
    )
