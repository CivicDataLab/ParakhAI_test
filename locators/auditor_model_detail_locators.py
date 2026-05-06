"""Selectors for the auditor model detail page (/auditor/models/[id])."""


class AuditorModelDetailLocators:
    MODEL_TITLE = "h1, h2, [class*='model-title']"
    ASSIGNED_VERSIONS_HEADING = "text=Your Assigned Versions, text=Assigned Versions"
    VERSION_ROW = "[class*='version-row'], tbody tr"
    STATUS_PENDING = "text=Pending"
    STATUS_ACCEPTED = "text=Accepted"
    ACCEPT_BUTTON = "button:has-text('Accept')"
    DECLINE_BUTTON = "button:has-text('Decline')"
    START_BUTTON = "button:has-text('Start'), a:has-text('Start Evaluation')"
    NO_ASSIGNED_VERSIONS = "text=No assigned versions"
