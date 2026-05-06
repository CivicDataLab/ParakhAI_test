"""Selectors for the organisation selection page (/dashboard/ai-maker)."""


class OrgSelectionLocators:
    PAGE_HEADING = "h1, h2, text=Select Organization"
    ORG_CARD = "[class*='org-card'], [class*='orgCard'], a[href*='/ai-maker/']"
    NO_ORGS_MESSAGE = "text=No organizations found, text=You are not a member"
