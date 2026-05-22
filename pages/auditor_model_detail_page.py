"""
Page object for the auditor model detail page.
URL: /dashboard/auditor/models/{model_id}
"""


from locators.auditor_model_detail_locators import AuditorModelDetailLocators
from pages.base_page import BasePage
from utils.config import Config


class AuditorModelDetailPage(BasePage):
    """Auditor model detail — assigned versions and audit actions."""

    MODEL_TITLE = AuditorModelDetailLocators.MODEL_TITLE
    ASSIGNED_VERSIONS_HEADING = AuditorModelDetailLocators.ASSIGNED_VERSIONS_HEADING
    VERSION_ROW = AuditorModelDetailLocators.VERSION_ROW
    STATUS_PENDING = AuditorModelDetailLocators.STATUS_PENDING
    STATUS_ACCEPTED = AuditorModelDetailLocators.STATUS_ACCEPTED
    ACCEPT_BUTTON = AuditorModelDetailLocators.ACCEPT_BUTTON
    DECLINE_BUTTON = AuditorModelDetailLocators.DECLINE_BUTTON
    START_BUTTON = AuditorModelDetailLocators.START_BUTTON
    NO_ASSIGNED_VERSIONS = AuditorModelDetailLocators.NO_ASSIGNED_VERSIONS
    MODEL_NOT_FOUND = AuditorModelDetailLocators.MODEL_NOT_FOUND

    # ── Navigation ─────────────────────────────────────────────────────────────

    def go_to_model_detail(self, model_id: int) -> "AuditorModelDetailPage":
        url = Config.url(f"/dashboard/auditor/models/{model_id}")
        self.navigate(url)
        self.wait_for_app_ready()
        self.skip_if_redirected_to_home(f"/auditor/models/{model_id}")
        return self

    # ── State checks ───────────────────────────────────────────────────────────

    def is_page_loaded(self) -> bool:
        return self.is_visible(self.MODEL_TITLE)

    def is_model_not_found(self) -> bool:
        return self.is_visible(self.MODEL_NOT_FOUND, timeout=2_000)

    def is_assigned_versions_section_visible(self) -> bool:
        return self.is_visible(self.ASSIGNED_VERSIONS_HEADING)

    def get_version_row_count(self) -> int:
        return self.page.locator(self.VERSION_ROW).count()

    def has_pending_versions(self) -> bool:
        return self.is_visible(self.STATUS_PENDING)

    def is_accept_button_visible(self) -> bool:
        return self.is_visible(self.ACCEPT_BUTTON)

    def is_start_button_visible(self) -> bool:
        return self.is_visible(self.START_BUTTON)

    # ── Actions ────────────────────────────────────────────────────────────────

    def click_accept(self) -> None:
        self.click(self.ACCEPT_BUTTON)

    def click_decline(self) -> None:
        self.click(self.DECLINE_BUTTON)

    def click_start(self) -> None:
        self.click(self.START_BUTTON)
        self.wait_for_app_ready()

    def get_status_chip_text(self) -> str:
        """Return the status chip text on the first version row, if visible."""
        for status in ("Pending", "Accepted", "Declined", "Completed"):
            sel = f"text={status}"
            if self.is_visible(sel, timeout=1_000):
                return status.upper()
        return ""

    def click_back(self) -> None:
        self.click("button:has-text('Back'), a:has-text('Back')")
        self.wait_for_app_ready()
