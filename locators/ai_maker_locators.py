"""
Locators for the AI Maker dashboard (home overview + sidebar navigation).
Base URL: /dashboard/ai-maker/{org_id}
"""


class AIMakerLocators:
    # ── Sidebar navigation ─────────────────────────────────────────────────────
    # Previous `[class*='sidebar']` filter was case-sensitive and missed the
    # actual PascalCase `Sidebar__...` CSS-modules class. Plain link/button
    # text match is robust against the wrapper class name.
    SIDEBAR_HOME = "a:has-text('Home'), button:has-text('Home')"
    SIDEBAR_MODELS = "a:has-text('Models'), button:has-text('Models')"
    SIDEBAR_EVALUATIONS = "a:has-text('Evaluations'), button:has-text('Evaluations')"
    SIDEBAR_PROMPT_LIBRARIES = (
        "a:has-text('Prompt Libraries'), button:has-text('Prompt Libraries')"
    )
    SIDEBAR_EVALUATORS = "a:has-text('Evaluators'), button:has-text('Evaluators')"

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
