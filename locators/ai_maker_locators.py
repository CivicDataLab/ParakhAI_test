"""
Locators for the AI Maker dashboard (home overview + sidebar navigation).
Base URL: /dashboard/ai-maker/{org_id}
"""


class AIMakerLocators:
    # ── Sidebar navigation ─────────────────────────────────────────────────────
    SIDEBAR_HOME = "nav a:text('Home'), [class*='sidebar'] a:text('Home'), li a:text('Home')"
    SIDEBAR_MODELS = "nav a:text('Models'), [class*='sidebar'] a:text('Models'), li a:text('Models')"
    SIDEBAR_EVALUATIONS = (
        "nav a:text('Evaluations'), "
        "[class*='sidebar'] a:text('Evaluations'), "
        "li a:text('Evaluations')"
    )
    SIDEBAR_PROMPT_LIBRARIES = (
        "nav a:text('Prompt Libraries'), "
        "[class*='sidebar'] a:text('Prompt Libraries')"
    )
    SIDEBAR_EVALUATORS = (
        "nav a:text('Evaluators'), "
        "[class*='sidebar'] a:text('Evaluators')"
    )

    # ── Org identity (left panel) ──────────────────────────────────────────────
    ORG_LOGO = "img[alt*='CivicData'], img[alt*='civic'], [class*='logo']"
    ORG_NAME = "text=CivicdataLab"
    WELCOME_MESSAGE = "text=Welcome"
    SWITCH_ROLES_LINK = "text=Switch Roles"

    # ── Overview stat cards ────────────────────────────────────────────────────
    OVERVIEW_HEADING = "text=Overview"
    STAT_EVALUATION_RUNS = "text=Evaluation Runs"
    STAT_TEST_CASES = "text=Test Cases"
    STAT_MODELS = "text=Models"
    STAT_ISSUES_FLAGGED = "text=Issues Flagged"
    STAT_CARD = "[class*='stat'], [class*='card'], [class*='Card']"

    # ── Models section on home ─────────────────────────────────────────────────
    MODELS_SECTION_HEADING = "text=Models"
    ADD_NEW_MODEL_BUTTON = "text=Add A New Model, button:text('Add A New Model')"
    MODEL_CARD = "[class*='card'], [class*='Card']"
    MODEL_TYPE_BADGE = "text=Text Generation"
