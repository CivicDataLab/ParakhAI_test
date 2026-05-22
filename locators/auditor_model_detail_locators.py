"""Selectors for the auditor model detail page (/dashboard/auditor/models/[id])."""


class AuditorModelDetailLocators:
    MODEL_TITLE = "h1, h2, [class*='model-title']"
    # Mixing `text=...` engines with commas matches the literal comma — use
    # CSS `:has-text(...)` substring matching instead. "Assigned Versions"
    # is a substring of "Your Assigned Versions", so one needle catches both.
    ASSIGNED_VERSIONS_HEADING = (
        "h1:has-text('Assigned Versions'), "
        "h2:has-text('Assigned Versions'), "
        "h3:has-text('Assigned Versions'), "
        "[class*='heading' i]:has-text('Assigned Versions')"
    )
    VERSION_ROW = "[class*='version-row'], tbody tr"
    STATUS_PENDING = "text=Pending"
    STATUS_ACCEPTED = "text=Accepted"
    ACCEPT_BUTTON = "button:has-text('Accept')"
    DECLINE_BUTTON = "button:has-text('Decline')"
    START_BUTTON = "button:has-text('Start'), a:has-text('Start Evaluation')"
    NO_ASSIGNED_VERSIONS = "text=No assigned versions"
    # Rendered when the auditor route resolves but the requested model id is
    # not in this user's assigned set. Lets tests fail-fast with a clear
    # data-dependency message instead of silently skipping on missing DOM.
    MODEL_NOT_FOUND = "text=Model not found"
