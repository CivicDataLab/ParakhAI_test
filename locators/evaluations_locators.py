"""
Locators for the Evaluations list, New Evaluation wizard, and Evaluation detail.
List URL  : /dashboard/ai-maker/{org_id}/evaluations
Wizard URL: /dashboard/ai-maker/{org_id}/evaluations/new
Detail URL: /dashboard/ai-maker/{org_id}/evaluations/{eval_id}
"""


class EvaluationsLocators:
    # ── Evaluations list ───────────────────────────────────────────────────────
    PAGE_HEADING = "text=Evaluations"
    NEW_EVALUATION_BUTTON = "button:has-text('New Evaluation'), a:has-text('New Evaluation')"
    EVAL_TABLE_ROW = "tr, [class*='row']"
    EVAL_NAME_COL = "th:text('Evaluation Name'), :text('Evaluation Name')"
    EVAL_STATUS_COL = "th:text('Status'), :text('Status')"
    EVAL_MODE_COL = "th:text('Evaluation Mode'), :text('Evaluation Mode')"
    EVAL_TESTS_COL = "th:text('Tests'), :text('Tests')"
    EVAL_COMPLETED_COL = "th:text('Completed'), :text('Completed')"

    # Status badges and mode labels live inside the evaluations table — scope
    # the selectors to table cells so they don't match unrelated text elsewhere
    # on the page (e.g. the Mode dropdown options literally contain "Automated"
    # / "Manual"; the Cancel modal contains "Cancel Evaluation"). Prefer
    # data-testid when frontend adds them.
    STATUS_DRAFT = (
        "[data-testid='status-draft'], "
        "td :has-text('DRAFT'), "
        "[role='cell'] :has-text('DRAFT')"
    )
    STATUS_COMPLETED = (
        "[data-testid='status-completed'], "
        "td :has-text('COMPLETED'), "
        "[role='cell'] :has-text('COMPLETED')"
    )
    MODE_AUTOMATED = (
        "[data-testid='mode-automated'], "
        "td :has-text('AUTOMATED'), "
        "[role='cell'] :has-text('AUTOMATED')"
    )
    MODE_MANUAL = (
        "[data-testid='mode-manual'], "
        "td :has-text('MANUAL'), "
        "[role='cell'] :has-text('MANUAL')"
    )

    # ── New Evaluation modal ───────────────────────────────────────────────────
    MODAL_TITLE = "[role='dialog']:has-text('Start New Evaluation'), [class*='modal']:has-text('Start New Evaluation'), [class*='Modal']:has-text('Start New Evaluation')"
    MODAL_MODEL_DROPDOWN = "select, [class*='select'], [role='combobox']"
    MODAL_VERSION_DROPDOWN = "select, [class*='select'], [role='combobox']"
    MODAL_START_BUTTON = "button:has-text('Start')"
    MODAL_CANCEL_BUTTON = "button:has-text('Cancel')"

    # Modal dropdown option lists — at least one <option> or listbox item must be present
    # NOTE: If dropdowns are custom (React-Select / Radix), add data-testid="model-option"
    #       and data-testid="version-option" to option elements for stable selection.
    MODAL_MODEL_OPTION = "option, [role='option'], [class*='option']"
    MODAL_VERSION_OPTION = "option, [role='option'], [class*='option']"

    # ── New Evaluation wizard ──────────────────────────────────────────────────
    # Scope tab selectors to <button> / [role='tab'] so they don't collide with
    # the same text appearing in module-card counters ("0 Test Cases").
    WIZARD_TAB_CONFIGURATION = (
        "[data-testid='tab-configuration'], "
        "[role='tab']:has-text('Evaluation Configuration'), "
        "button:has-text('Evaluation Configuration')"
    )
    WIZARD_TAB_TEST_CASES = (
        "[data-testid='tab-test-cases'], "
        "[role='tab']:has-text('Test Cases'), "
        "button:has-text('Test Cases'):not(:has-text('0 '))"
    )
    # NOTE: The name input uses id="auditName" per spec — prefer that; class fallback kept.
    WIZARD_EVAL_NAME_INPUT = "input#auditName, input[name='evaluationName'], input[value*='Untitled'], input[class*='name']"
    WIZARD_CANCEL_EVALUATION = "text=Cancel Evaluation"
    # NOTE: Add data-testid="auto-save-indicator" to the header indicator for stability.
    WIZARD_AUTO_SAVED = "text=Auto-saved"

    # Evaluation type radio options
    EVAL_TYPE_TECHNICAL = "text=Technical Evaluation"
    EVAL_TYPE_DOMAIN = "text=Domain Evaluation"
    EVAL_TYPE_CULTURAL = "text=Cultural Evaluation"
    EVAL_TYPE_TECHNICAL_RADIO = "input[type='radio']:near(:text('Technical Evaluation'))"
    EVAL_TYPE_DOMAIN_RADIO = "input[type='radio']:near(:text('Domain Evaluation'))"
    EVAL_TYPE_CULTURAL_RADIO = "input[type='radio']:near(:text('Cultural Evaluation'))"

    # Evaluation objective
    EVAL_OBJECTIVE_TEXTAREA = "textarea, [class*='objective']"
    EVAL_OBJECTIVE_ERROR = "text=Evaluation objective is required"

    # Evaluation modules (checkboxes + labels). The label text appears twice on
    # the page (title + description), so `>> nth=0` targets the title row.
    EVAL_MODULE_HALLUCINATION = "text=Hallucination and Misinformation >> nth=0"
    EVAL_MODULE_BIAS = "text=Bias and Fairness >> nth=0"
    EVAL_MODULE_PRIVACY = "text=Privacy and Safety >> nth=0"
    EVAL_MODULE_CHECKBOX = "input[type='checkbox']"
    # Sub-category multi-select dropdown that appears when a module is checked
    # NOTE: Add data-testid="module-subcategory-dropdown" for stable selection.
    EVAL_MODULE_SUBCATEGORY_DROPDOWN = (
        "[class*='subcategory'], [class*='sub-category'], "
        "[aria-label*='subcategory'], [aria-label*='sub-category'], "
        "select:near(input[type='checkbox']:checked)"
    )

    # Evaluation Scope is a native <select name="auditScope"> with options
    # 'Healthcare', 'Agriculture', 'General'. The dropdown is required — without
    # selecting a scope, clicking 'Add Test Cases' does not assign an auditId,
    # so no draft is persisted. Confirmed via Playwright MCP 2026-05-07.
    EVAL_SCOPE_DROPDOWN = "select[name='auditScope']"

    # Mode of evaluation
    # NOTE: The dropdown placeholder text is "Click to select from dropdown"; the
    #       selector below covers both native <select> and custom combobox patterns.
    # Mode of Evaluation is a native <select name="modeOfEvaluation">
    EVAL_MODE_DROPDOWN = "select[name='modeOfEvaluation']"
    EVAL_MODE_OPTION_AUTOMATED = "text=Automated"
    EVAL_MODE_OPTION_MANUAL = "text=Manual"
    ADD_TEST_CASES_BUTTON = "button:has-text('Add Test Cases')"

    # ── Test Cases tab — Automated mode ───────────────────────────────────────
    # Dataset selection table
    # NOTE: Add data-testid="prompt-dataset-table" to the table for stable selection.
    AUTOMATED_DATASET_TABLE = (
        ":text('Select Prompt Datasets'), "
        "[class*='dataset'], "
        "table:near(:text('Select Prompt Datasets'))"
    )
    AUTOMATED_DATASET_ROW = (
        "[class*='dataset'] tr, "
        "table:near(:text('Select Prompt Datasets')) tr, "
        "tr:has(input[type='checkbox'])"
    )
    AUTOMATED_DATASET_CHECKBOX = (
        "[class*='dataset'] input[type='checkbox'], "
        "table:near(:text('Select Prompt Datasets')) input[type='checkbox']"
    )
    # Custom test cases section
    AUTOMATED_PASTE_TEXT_TAB = "text=Paste Text"
    AUTOMATED_UPLOAD_FILE_TAB = "text=Upload File"
    AUTOMATED_PASTE_TEXTAREA = (
        "textarea[placeholder*='paste'], "
        "textarea[placeholder*='Paste'], "
        "[class*='paste'] textarea, "
        "textarea:near(:text('Paste Text'))"
    )
    # Run Evaluation CTA
    RUN_EVALUATION_BUTTON = "button:has-text('Run Evaluation')"
    # Error shown when nothing is selected
    RUN_EVALUATION_NO_SELECTION_ERROR = (
        "text=Please select at least one prompt dataset or provide custom test cases"
    )

    # ── Test Cases tab — Manual mode ──────────────────────────────────────────
    # Module cards showing Test Cases / Failed / Passed counters
    # NOTE: Add data-testid="module-card" to each card for stable selection.
    MANUAL_MODULE_CARD = (
        "[class*='module-card'], "
        "[class*='moduleCard'], "
        "[class*='ModuleCard'], "
        "[class*='module'] [class*='card'], "
        "[class*='Module'] [class*='Card'], "
        "[class*='card']:has-text('Test Cases'), "
        "[class*='Card']:has-text('Test Cases'), "
        "article:has-text('Test Cases'), "
        # Broadest fallback: any div that contains a module name AND 'Test Cases'
        # (the module cards are the only elements with both on the Test Cases tab)
        "div:has(:text('Hallucination and Misinformation')):has(:text('Test Cases')), "
        "div:has(:text('Bias and Fairness')):has(:text('Test Cases')), "
        "div:has(:text('Privacy and Safety')):has(:text('Test Cases'))"
    )
    # Counter labels live inside the module-card containers. A plain
    # `text=Failed` matches unrelated content (toasts, tab headers) and races
    # the SPA hydration. Each selector below tries in priority order:
    #   1. data-testid (preferred — frontend can add these later)
    #   2. counter scoped to a module-card container with the module title
    #   3. last-resort scoped text= so we still find something on a render lag
    # Counter labels render as e.g. "0 Test Cases" / "0 Failed" / "0 Passed".
    # Use :has-text (substring) not :text-is (exact) — the leading number is
    # part of the same text node. Use case-insensitive class match (`i` flag)
    # so we hit both camelCase (`moduleCard`) and kebab-case (`module-card`).
    MANUAL_MODULE_COUNTER_TEST_CASES = (
        "[data-testid='counter-test-cases'], "
        "[class*='module' i][class*='card' i] :has-text('Test Cases'), "
        "[class*='card' i] :has-text('Test Cases')"
    )
    MANUAL_MODULE_COUNTER_FAILED = (
        "[data-testid='counter-failed'], "
        "[class*='module' i][class*='card' i] :has-text('Failed'), "
        "[class*='card' i] :has-text('Failed')"
    )
    MANUAL_MODULE_COUNTER_PASSED = (
        "[data-testid='counter-passed'], "
        "[class*='module' i][class*='card' i] :has-text('Passed'), "
        "[class*='card' i] :has-text('Passed')"
    )
    # Test entry panel (shown after clicking a module card)
    MANUAL_INPUT_TEXTAREA = (
        "textarea[placeholder*='nput'], "
        "textarea[aria-label*='nput'], "
        "[class*='input-area'] textarea, "
        "[class*='inputArea'] textarea"
    )
    MANUAL_OUTPUT_PANEL = (
        "[class*='output'], "
        "[class*='Output'], "
        "[aria-label*='output'], "
        "[aria-label*='Output']"
    )
    MANUAL_SUBMIT_BUTTON = (
        "button:has-text('Submit'), "
        "button[type='submit']:near(textarea)"
    )
    MANUAL_CHANGE_MODULE_LINK = (
        "a:has-text('Change Module'), "
        "button:has-text('Change Module')"
    )
    FINISH_EVALUATION_BUTTON = "button:has-text('Finish Evaluation')"
    MANUAL_MIN_TEST_CASES_NOTE = (
        "text=Evaluate at least 3 test cases per module to complete the evaluation"
    )

    # ── Draft row navigation ───────────────────────────────────────────────────
    # A DRAFT row's clickable area should navigate to /evaluations/new?auditId=...
    # NOTE: Add data-testid="draft-row-link" to draft rows for stable selection.
    DRAFT_ROW = "tr:has-text('DRAFT'), [class*='row']:has-text('DRAFT')"
    COMPLETED_ROW = "tr:has-text('COMPLETED'), [class*='row']:has-text('COMPLETED')"

    # ── Evaluation detail ──────────────────────────────────────────────────────
    DETAIL_EVAL_NAME = "[class*='eval-name'], [class*='title'], h1, h2"
    DETAIL_STATUS_COMPLETED = "text=COMPLETED"
    DETAIL_MODE_AUTOMATED = "text=AUTOMATED"
    BACK_TO_LIST_BUTTON = "button:has-text('Back to List'), a:has-text('Back to List')"

    # Overview card
    OVERVIEW_HEADING = "text=Evaluation Overview"
    OVERVIEW_EVAL_ID = "text=Evaluation ID"
    OVERVIEW_CREATED = "text=Created"
    OVERVIEW_COMPLETED = "text=Completed"
    OVERVIEW_DURATION = "text=Duration"
    OVERVIEW_EVAL_TYPE = "text=Evaluation Type"
    OVERVIEW_MODULES = "text=Modules"

    # Summary cards
    SUMMARY_HEADING = "text=Evaluation Summary"
    SUMMARY_PASS_RATE = "text=TOTAL PASS RATE"
    SUMMARY_PASSED_TESTS = "text=PASSED TESTS"
    SUMMARY_FAILED_TESTS = "text=FAILED TESTS"
    SUMMARY_SKIPPED_TESTS = "text=SKIPPED TESTS"

    # Risk level cards
    RISK_TOTAL_ISSUES = "text=Total Issues Identified"
    RISK_LOW = "text=LOW RISK"
    RISK_MEDIUM = "text=MEDIUM RISK"
    RISK_HIGH = "text=HIGH RISK"

    # Module-wise results tabs
    MODULE_TAB_HALLUCINATION = "text=Hallucination and MisInformation"
    MODULE_TAB_BIAS = "text=Bias and Fairness"
    MODULE_TAB_PRIVACY = "text=Privacy and Safety"

    # Sample issues accordion
    SAMPLE_ISSUES_HEADING = "text=Sample Issues"
    ISSUE_ACCORDION_ITEM = "text=Issue"
    ISSUE_EXPAND_BUTTON = "button[aria-expanded], [class*='accordion'] button"

    # Report download
    DOWNLOAD_REPORT_BUTTON = "button:has-text('Download Report'), a:has-text('Download Report')"
