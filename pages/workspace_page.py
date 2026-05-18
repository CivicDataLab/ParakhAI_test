"""
Page object for the Evaluation Workspace entry point (role selection + org selection).
"""

from playwright.sync_api import Page

from locators.workspace_locators import WorkspaceLocators
from pages.base_page import BasePage
from utils.config import Config


class WorkspacePage(BasePage):
    """Handles the role selection and organisation selection screens."""

    # Expose locators as class attributes
    AI_MAKER_CARD = WorkspaceLocators.AI_MAKER_CARD
    EVALUATOR_CARD = WorkspaceLocators.EVALUATOR_CARD
    ORG_CIVICDATALAB_CARD = WorkspaceLocators.ORG_CIVICDATALAB_CARD
    NAV_EVALUATION_WORKSPACE = WorkspaceLocators.NAV_EVALUATION_WORKSPACE
    BREADCRUMB_EVALUATION_WORKSPACE = WorkspaceLocators.BREADCRUMB_EVALUATION_WORKSPACE
    FOOTER = WorkspaceLocators.FOOTER

    def __init__(self, page: Page) -> None:
        super().__init__(page)

    # ── Navigation ─────────────────────────────────────────────────────────────

    def go_to_workspace(self) -> "WorkspacePage":
        """Navigate to the role-selection dashboard page."""
        self.navigate(Config.url("/dashboard"))
        self.wait_for_app_ready()
        return self

    # ── Role selection ─────────────────────────────────────────────────────────

    def is_role_selection_visible(self) -> bool:
        return self.is_visible(self.AI_MAKER_CARD) or self.is_visible(self.EVALUATOR_CARD)

    def select_ai_maker(self) -> None:
        """Click the AI Maker role card and wait for the org list to populate."""
        self.click(self.AI_MAKER_CARD)
        self.wait_for_app_ready()
        try:
            self.page.locator(
                f"{WorkspaceLocators.ORG_CARD}, text=No organizations"
            ).first.wait_for(state="visible", timeout=10_000)
        except Exception:  # noqa: BLE001
            pass

    def select_evaluator(self) -> None:
        """Click the Evaluator role card and wait for the auditor URL."""
        self.click(self.EVALUATOR_CARD)
        # Role-switch is an SPA navigation — content updates first, URL follows.
        # Without the explicit URL wait, page.url assertions race the router.
        try:
            self.page.wait_for_url("**/auditor", timeout=5_000)
        except Exception:  # noqa: BLE001
            pass
        self.wait_for_app_ready()

    # ── Org selection ──────────────────────────────────────────────────────────

    def is_org_selection_visible(self) -> bool:
        return self.is_visible(WorkspaceLocators.ORG_SELECTION_HEADING)

    def select_civicdatalab(self) -> None:
        """Select the CivicdataLab organisation and wait for AI Maker URL."""
        self.click(self.ORG_CIVICDATALAB_CARD)
        try:
            self.page.wait_for_url("**/ai-maker/**", timeout=5_000)
        except Exception:  # noqa: BLE001
            pass
        self.wait_for_app_ready()

    def get_org_card_count(self) -> int:
        return self.page.locator(WorkspaceLocators.ORG_CARD).count()

    # ── Global nav helpers ─────────────────────────────────────────────────────

    def click_evaluation_workspace_nav(self) -> None:
        self.click(self.NAV_EVALUATION_WORKSPACE)
        self.wait_for_app_ready()

    def is_parakh_logo_visible(self) -> bool:
        return self.is_visible(WorkspaceLocators.PARAKH_LOGO)

    def is_footer_visible(self) -> bool:
        return self.is_visible(self.FOOTER)
