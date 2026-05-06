"""
Locators for the AI Models list page and individual model detail page.
List URL  : /dashboard/ai-maker/{org_id}/ai-models
Detail URL: /dashboard/ai-maker/{org_id}/ai-models/{model_id}
"""


class ModelsLocators:
    # ── Models list ────────────────────────────────────────────────────────────
    PAGE_HEADING = "text=AI Models"
    SEARCH_INPUT = "input[placeholder*='Search'], input[placeholder*='name']"
    ADD_FILTERS_BUTTON = "text=Add Filters"
    MODEL_CARD = "a[href*='/ai-models/'], [class*='card'] a"
    MODEL_CARD_TITLE = "[class*='card'] a, [class*='title'] a"
    MODEL_TYPE_BADGE = "text=Text Generation"

    # Model card metadata
    MODEL_DATE = "[class*='date'], [class*='Date']"
    MODEL_TEST_CASES = "text=test cases"
    MODEL_EVALUATIONS = "text=evaluations"

    # Known model names
    MODEL_SARVAM = "text=SarvamaI: Sarvam-M"
    MODEL_LLAMA = "text=Meta: Llama 3.1 70B Instruct"
    MODEL_GPT5 = "text=OpenAI: GPT-5 Mini"
    MODEL_QWEN = "text=Alibaba Cloud: Qwen3 235B"
    MODEL_GEMMA = "text=Google: Gemma 3 27B"
    MODEL_MISTRAL = "text=MistralAI: Mistral 7B Instruct"

    # ── Model detail ────────────────────────────────────────────────────────────
    DETAIL_MODEL_TITLE = "h1, h2, [class*='title']:not([class*='card'])"
    ABOUT_HEADING = "text=About"
    ABOUT_DESCRIPTION = "p, [class*='description'], [class*='about']"
    VERSIONS_HEADING = "text=Versions"

    # Version row
    VERSION_ROW = "[class*='version'], tr, [class*='row']"
    VERSION_LABEL = "text=Version"
    PRIMARY_BADGE = "text=Primary"
    START_EVALUATION_LINK = "text=Start Evaluation"
    INVITE_AUDITORS_LINK = "text=Invite Auditors"
    DATE_UPDATED_COL = "text=DATE UPDATED, th:text('DATE UPDATED')"
    CAPABILITIES_COL = "text=CAPABILITIES, th:text('CAPABILITIES')"
    LIFECYCLE_STAGE_COL = "text=LIFECYCLE STAGE, th:text('LIFECYCLE STAGE')"

    # Past evaluations table
    PAST_EVALUATIONS_HEADING = "text=Past Evaluations"
    PAST_EVAL_TABLE = "table, [class*='table'], [role='table']"
    PAST_EVAL_ROW = "tr[class*='row'], tbody tr"
    PAST_EVAL_NAME_COL = "text=Evaluation Name, th:text('Evaluation Name')"
    PAST_EVAL_TIME_COL = "text=Evaluation Time, th:text('Evaluation Time')"
    PAST_EVAL_ID_COL = "text=Evaluation ID, th:text('Evaluation ID')"
    PAST_EVAL_TYPE_COL = "text=Type, th:text('Type')"
    PAGINATION = "[class*='pagination'], [class*='Pagination']"
    ROWS_PER_PAGE = "text=Rows:"
