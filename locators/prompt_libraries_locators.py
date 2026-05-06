"""
Locators for the Prompt Libraries page.
URL: /dashboard/ai-maker/{org_id}/prompt-libraries
"""


class PromptLibrariesLocators:
    # ── Page structure ─────────────────────────────────────────────────────────
    PAGE_HEADING = "text=Prompt Libraries"
    SEARCH_INPUT = "input[placeholder*='Search'], input[placeholder*='name']"
    ADD_FILTERS_BUTTON = "text=Add Filters"

    # ── Library cards ──────────────────────────────────────────────────────────
    LIBRARY_CARD = "[class*='card'], [class*='Card']"
    LIBRARY_CARD_TITLE = "[class*='card'] [class*='title'], [class*='card'] a, [class*='card'] h3"
    LIBRARY_DATE = "[class*='date'], [class*='Date']"
    LIBRARY_DESCRIPTION = "[class*='description'], [class*='card'] p"

    # Category badges
    CATEGORY_BADGE = "[class*='badge'], [class*='tag'], [class*='chip']"
    CATEGORY_AGRICULTURE = "text=Agriculture"
    CATEGORY_HEALTHCARE = "text=Healthcare"
    CATEGORY_GENERAL = "text=General"

    # Known library names
    LIBRARY_KCC_ENGLISH = "text=KCC English Queries"
    LIBRARY_PARIKSHA = "text=Microsoft: PARIKSHA"
    LIBRARY_PUBLIC_INTEREST_ENGLISH = "text=Public Interest English"
    LIBRARY_PUBLIC_INTEREST_HINDI = "text=Public Interest Hindi"
    LIBRARY_KCC_HINDI = "text=KCC: Hindi Queries"
    LIBRARY_KISAN_CALL = "text=Kisan Call Centre"
