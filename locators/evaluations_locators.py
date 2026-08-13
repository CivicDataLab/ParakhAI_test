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

    # ── Status filter tabs (StatusFilterTabs component — Jun 2026) ───────────
    # As of late Jun 2026 the component renders 9 tabs:
    #   All | Draft | Queued | Running | In Progress | Pending Review | Completed | Failed | Cancelled
    # Use :has-text for substring match so count badges ("Draft(40)") still match.
    STATUS_TAB_ALL = "button:has-text('All'), [role='tab']:has-text('All')"
    STATUS_TAB_DRAFT = "button:has-text('Draft'), [role='tab']:has-text('Draft')"
    # "Pending" is now split into "Queued" and "Pending Review" — keep old selector
    # as a broad fallback and add the specific new ones.
    STATUS_TAB_PENDING = "button:has-text('Pending'), [role='tab']:has-text('Pending')"
    STATUS_TAB_QUEUED = "button:has-text('Queued'), [role='tab']:has-text('Queued')"
    STATUS_TAB_IN_PROGRESS = "button:has-text('In Progress'), [role='tab']:has-text('In Progress')"
    STATUS_TAB_PENDING_REVIEW = "button:has-text('Pending Review'), [role='tab']:has-text('Pending Review')"
    STATUS_TAB_RUNNING = "button:has-text('Running'), [role='tab']:has-text('Running')"
    STATUS_TAB_COMPLETED = "button:has-text('Completed'), [role='tab']:has-text('Completed')"
    STATUS_TAB_FAILED = "button:has-text('Failed'), [role='tab']:has-text('Failed')"
    STATUS_TAB_CANCELLED = "button:has-text('Cancelled'), [role='tab']:has-text('Cancelled')"

    # ── List table controls (verified live 03 Jul 2026) ──────────────────────
    # Column headers are sort buttons (accessible text includes
    # "Sorted in descending order"). Rows-per-page is a select next to "Rows:".
    SORT_HEADER_NAME = "th button:has-text('Evaluation Name')"
    SORT_HEADER_STATUS = "th button:has-text('Status')"
    ROWS_PER_PAGE_SELECT = "select:has(option:text-is('25')):has(option:text-is('50'))"
    TABLE_BODY_ROW = "table tbody tr"
    PAGE_X_OF_Y = "text=/Page \\d+ of \\d+/"

    # ── Pagination controls (Jun 2026) ────────────────────────────────────────
    PAGINATION_NEXT = (
        "button:has-text('Next'), [aria-label='Go to next page'], [class*='pagination'] button:last-child"
    )
    PAGINATION_CONTAINER = "[class*='pagination'], [class*='Pagination'], [aria-label*='pagination']"

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
    # Two-step Radix dialog. The dialog element carries
    # data-start-evaluation-step="1" / "2" so the current step can be asserted.
    MODAL_TITLE = "[role='dialog']:has-text('Start an Evaluation')"
    MODAL_DIALOG = "[role='dialog'][data-start-evaluation-step]"
    MODAL_STEP_1 = "[role='dialog'][data-start-evaluation-step='1']"
    MODAL_STEP_2 = "[role='dialog'][data-start-evaluation-step='2']"
    MODAL_MODEL_DROPDOWN = "select[name='modelSelect']"
    MODAL_VERSION_DROPDOWN = "select[name='versionSelect']"
    MODAL_EVAL_NAME_INPUT = "input[name='evaluationName']"
    # Playground radio's DOM value drifted to 'playground' (was 'manual');
    # confirmed via origin/dev source 2026-08-13. Bulk unchanged.
    MODAL_EVAL_METHOD_BULK = "input[name='evaluationMethod'][value='bulk']"
    MODAL_EVAL_METHOD_PLAYGROUND = "input[name='evaluationMethod'][value='playground']"
    MODAL_NEXT_BUTTON = "[role='dialog'] button:has-text('Next')"
    MODAL_BACK_BUTTON = "[role='dialog'] button:has-text('Back')"
    MODAL_START_BUTTON = "[role='dialog'] button:has-text('Start Evaluation')"
    MODAL_CANCEL_BUTTON = (
        "[role='dialog'] button[aria-label='Close dialog'], "
        "[role='dialog'] button:has-text('Cancel')"
    )
    MODAL_LOADING_MODELS = "[role='dialog'] :text('Loading models')"

    # Step-2 evaluator-type radios. DOM `value`s are the backend enum
    # (TECHNICAL_AUDIT / DOMAIN_AUDIT / CULTURAL_AUDIT), not the display
    # label — confirmed via live DOM dump 2026-08-13 (previously plain
    # 'Technical' / 'Domain' / 'Cultural', now drifted to the _AUDIT suffix
    # form). TECHNICAL_AUDIT is checked by default. See
    # NewEvaluationPage.get_checked_evaluator_type() for the reverse mapping
    # back to the human-readable label tests assert against.
    MODAL_EVALUATOR_TYPE_RADIO = "input[name='evaluatorType']"
    MODAL_EVALUATOR_TECHNICAL = "input[name='evaluatorType'][value='TECHNICAL_AUDIT']"
    MODAL_EVALUATOR_DOMAIN = "input[name='evaluatorType'][value='DOMAIN_AUDIT']"
    MODAL_EVALUATOR_CULTURAL = "input[name='evaluatorType'][value='CULTURAL_AUDIT']"
    # Step-2 objective textarea — required; Start Evaluation stays disabled
    # while it is empty.
    MODAL_OBJECTIVE_TEXTAREA = "[role='dialog'] textarea"
    MODAL_STEP2_HEADING = "[role='dialog'] :text('I am evaluating as')"

    # Modal dropdown option lists — at least one <option> or listbox item must be present
    # NOTE: If dropdowns are custom (React-Select / Radix), add data-testid="model-option"
    #       and data-testid="version-option" to option elements for stable selection.
    MODAL_MODEL_OPTION = "option, [role='option'], [class*='option']"
    MODAL_VERSION_OPTION = "option, [role='option'], [class*='option']"

    # ── New Evaluation wizard (single-page layout, Jul 2026 redesign) ─────────
    # The wizard at /evaluations/new?auditId=… is now ONE page — there are no
    # Configuration / Test Cases tabs any more ([role='tab'] count is 0).
    # Layout: header (name, Draft badge, Back to List, Cancel) → Evaluation
    # Overview card → Evaluation Workspace (modules + test-case source + Run).
    WIZARD_LOADING_CURTAIN = "text=Loading evaluation details"
    WIZARD_OVERVIEW_HEADING = "text=Evaluation Overview"
    WIZARD_WORKSPACE_HEADING = "text=Evaluation Workspace"
    WIZARD_MODULES_HEADING = "text=Evaluation Modules"
    WIZARD_DRAFT_BADGE = ":text('Draft')"
    WIZARD_BACK_TO_LIST = "button:has-text('Back to List'), a:has-text('Back to List')"
    # Test-case source options (Bulk workspace)
    WIZARD_PROMPT_LIBRARY_OPTION = "text=Select a prompt library"
    WIZARD_OWN_PROMPTS_OPTION = "text=Add your own prompts"
    WIZARD_PREMADE_LIBRARIES_LABEL = "text=Select from pre-made prompt libraries"
    WIZARD_MAX_TEST_CASES_NOTE = "text=Maximum test cases for your current selection"
    WIZARD_SUBMODULE_PROMPT = "text=Select sub-modules from dropdown"
    # The sub-module picker is a cmdk-style combobox: a trigger button (labelled
    # "open combobox"/"close combobox" depending on state) that reveals a list
    # of [role='option']/[cmdk-item] entries (e.g. "Hallucination", "Misinformation").
    WIZARD_SUBMODULE_COMBOBOX_TRIGGER = "text=open combobox"
    WIZARD_SUBMODULE_OPTION = "[role='option'], [cmdk-item]"
    # Each prompt-library row renders a radio input as the real selection
    # target — the dataset title is a plain <a> that navigates to CivicDataSpace
    # in a new tab, NOT a selection control. Always click the radio, not the link.
    WIZARD_PROMPT_LIBRARY_RADIO = "input[type='radio'][name='promptLibrary']"
    # Error under the Run Evaluation button when no prompt library is selected
    RUN_EVALUATION_LIBRARY_ERROR = "text=Please select a prompt library"

    # DEPRECATED (pre-Jul-2026 tabbed wizard) — kept so old imports don't break;
    # do not assert on these, the tabs no longer exist.
    WIZARD_TAB_CONFIGURATION = (
        "[data-testid='tab-configuration'], "
        "[role='tab']:has-text('Evaluation Configuration'), "
        "button:has-text('Evaluation Configuration')"
    )
    WIZARD_TAB_TEST_CASES = (
        "[data-testid='tab-test-cases'], "
        "[role='tab']:has-text('Test Cases'), "
        "button[class*='auditConfigTab']:has-text('Test Cases')"
    )
    # NOTE: The name input uses id="auditName" per spec — prefer that; class fallback kept.
    WIZARD_EVAL_NAME_INPUT = "input#auditName, input[name='evaluationName'], input[value*='Untitled'], input[class*='name']"
    # The wizard header action is labelled just 'Cancel' (alongside 'Back to
    # List') as of Jun 2026 — older builds said 'Cancel Evaluation'. The plain
    # 'Cancel' button is listed last so the more specific labels win when present.
    WIZARD_CANCEL_EVALUATION = (
        "button:has-text('Cancel Evaluation'), "
        "a:has-text('Cancel Evaluation'), "
        "button:has-text('Discard'), "
        "button:has-text('Cancel')"
    )
    # NOTE: Add data-testid="auto-save-indicator" to the header indicator for stability.
    WIZARD_AUTO_SAVED = "text=Auto-saved"

    # Evaluation type radio options
    EVAL_TYPE_TECHNICAL = "label:has-text('a technical evaluator'), :text('a technical evaluator')"
    EVAL_TYPE_DOMAIN = "label:has-text('a domain expert'), :text('a domain expert')"
    EVAL_TYPE_CULTURAL = "label:has-text('a cultural expert'), :text('a cultural expert')"
    EVAL_TYPE_TECHNICAL_RADIO = "input[type='radio']:near(:text('a technical evaluator'))"
    EVAL_TYPE_DOMAIN_RADIO = "input[type='radio']:near(:text('a domain expert'))"
    EVAL_TYPE_CULTURAL_RADIO = "input[type='radio']:near(:text('a cultural expert'))"

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
        # Real class as of Jun 2026: <button class="styles_moduleselectioncard__…">.
        # Kept first so wait_for_module_cards (which uses split(',')[0] in a
        # querySelectorAll) targets an element that actually exists.
        "[class*='moduleselectioncard'], "
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
    # The clickable element is the <a> INSIDE the first cell (evaluation name),
    # NOT the <tr> itself — clicking the row body does not navigate. The anchor
    # href is /en/dashboard/ai-maker/{org}/evaluations/new?auditId={id} for
    # drafts and /evaluations/{id} for completed evals. Confirmed live 2026-07-02.
    DRAFT_ROW = "tr:has-text('DRAFT'), [class*='row']:has-text('DRAFT')"
    COMPLETED_ROW = "tr:has-text('COMPLETED'), [class*='row']:has-text('COMPLETED')"
    DRAFT_ROW_LINK = "tr:has-text('DRAFT') td:first-child a"
    COMPLETED_ROW_LINK = "tr:has-text('COMPLETED') td:first-child a"

    # ── Evaluation detail ──────────────────────────────────────────────────────
    DETAIL_EVAL_NAME = "[class*='eval-name'], [class*='title'], h1, h2"
    DETAIL_STATUS_COMPLETED = "text=COMPLETED"
    # Live UI shows "Bulk Evaluation" for the mode badge, not "AUTOMATED"
    # (confirmed 2026-07-28) — keep the old value as a fallback. A bare
    # `:has-text(...)` with no element in front of it is invalid CSS and
    # throws when Playwright parses it; `is_visible()` (base_page.py)
    # swallows *all* exceptions and reports "not visible", silently masking
    # the parse error as a missing element — same failure shape as the
    # text=/regex/,css comma bug fixed in test_functional.py. Per this repo's
    # own selector convention (CLAUDE.md "Selector conventions"), fallbacks
    # must be comma-separated valid CSS, each with an explicit tag/wildcard.
    DETAIL_MODE_AUTOMATED = (
        "span:has-text('Bulk Evaluation'), div:has-text('Bulk Evaluation'), "
        "span:has-text('AUTOMATED'), div:has-text('AUTOMATED')"
    )
    BACK_TO_LIST_BUTTON = "button:has-text('Back to List'), a:has-text('Back to List')"

    # Overview card
    OVERVIEW_HEADING = "text=Evaluation Overview"
    # Live label is "Eval ID :" not "Evaluation ID" (confirmed 2026-07-28) —
    # keep the old value as a fallback. Same bare-`:has-text()`-throws issue
    # as DETAIL_MODE_AUTOMATED above; fixed the same way.
    OVERVIEW_EVAL_ID = (
        "span:has-text('Eval ID'), div:has-text('Eval ID'), "
        "span:has-text('Evaluation ID'), div:has-text('Evaluation ID')"
    )
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

    # Module-wise results tabs. Module names also appear in the data display
    # panel, so a plain `text=` match resolves to 2 elements and trips strict
    # mode — scope to role=tab.
    MODULE_TAB_HALLUCINATION = "[role='tab']:has-text('Hallucination and MisInformation')"
    MODULE_TAB_BIAS = "[role='tab']:has-text('Bias and Fairness')"
    MODULE_TAB_PRIVACY = "[role='tab']:has-text('Privacy and Safety')"

    # Sample issues accordion
    SAMPLE_ISSUES_HEADING = "text=Sample Issues"
    ISSUE_ACCORDION_ITEM = "text=Issue"
    ISSUE_EXPAND_BUTTON = "button[aria-expanded], [class*='accordion'] button"

    # Report download
    DOWNLOAD_REPORT_BUTTON = "button:has-text('Download Report'), a:has-text('Download Report')"
