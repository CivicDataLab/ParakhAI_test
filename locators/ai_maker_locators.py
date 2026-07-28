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
    # Cards now render as `.metric-card > .metric-card-label + .metric-card-value`
    # (confirmed via live DOM dump 2026-07-13). Labels were renamed at some point:
    # "Evaluation Runs" -> "Evaluations Completed", "Test Cases" -> "Test Cases
    # Evaluated", "Models" -> "Models Added". Anchor on `.metric-card-label` with
    # `:has-text` (substring, tolerates the exact wording drifting again) scoped to
    # the `.metric-card` container so a card can be found + its value read in one
    # locator, without colliding with sidebar links or other page text that happens
    # to share a word (e.g. "Models").
    OVERVIEW_HEADING = "text=Overview"
    STAT_EVALUATION_RUNS = ".metric-card:has(.metric-card-label:has-text('Evaluations Completed'))"
    STAT_TEST_CASES = ".metric-card:has(.metric-card-label:has-text('Test Cases'))"
    STAT_MODELS = ".metric-card:has(.metric-card-label:has-text('Models Added'))"
    STAT_ISSUES_FLAGGED = ".metric-card:has(.metric-card-label:has-text('Issues Flagged'))"
    STAT_CARD = "[class*='stat'], [class*='card'], [class*='Card']"
    STAT_CARD_VALUE = ".metric-card-value"

    # ── Org selection page: Add Organisation button (Jun 2026) ───────────────
    ADD_ORGANISATION_BUTTON = (
        "button:has-text('Add Organisation'), a:has-text('Add Organisation')"
    )
    # AlertDialog opened by Add Organisation / Add A New Model / Edit model buttons.
    # The dialog title and "Yes, continue" CTA are stable text anchors.
    EXTERNAL_REDIRECT_DIALOG = (
        "[role='alertdialog'], [role='dialog'], [class*='AlertDialog'], [class*='alertdialog']"
    )
    EXTERNAL_REDIRECT_CONFIRM = "button:has-text('Yes, continue')"

    # ── Models section on home ─────────────────────────────────────────────────
    MODELS_SECTION_HEADING = "text=Models"
    # Playwright's `text=` engine treats commas as literal text; the original
    # `"text=Add A New Model, button:text('Add A New Model')"` searched for
    # that whole joined string and matched 0 elements.
    ADD_NEW_MODEL_BUTTON = "button:has-text('Add A New Model'), a:has-text('Add A New Model')"
    MODEL_CARD = "[class*='card'], [class*='Card']"
    MODEL_TYPE_BADGE = "text=Text Generation"
