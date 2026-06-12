"""
Page object for the AI Maker dashboard home.
URL: /dashboard/ai-maker/{org_id}
"""

from playwright.sync_api import Page

from locators.ai_maker_locators import AIMakerLocators
from pages.base_page import BasePage
from utils.config import Config

# CivicdataLab org ID on the platform
CIVICDATALAB_ORG_ID = 1


class AIMakerPage(BasePage):
    """AI Maker dashboard — overview stats and sidebar navigation."""

    # Expose locators
    SIDEBAR_HOME = AIMakerLocators.SIDEBAR_HOME
    SIDEBAR_MODELS = AIMakerLocators.SIDEBAR_MODELS
    SIDEBAR_EVALUATIONS = AIMakerLocators.SIDEBAR_EVALUATIONS
    SIDEBAR_PROMPT_LIBRARIES = AIMakerLocators.SIDEBAR_PROMPT_LIBRARIES
    SIDEBAR_EVALUATORS = AIMakerLocators.SIDEBAR_EVALUATORS
    OVERVIEW_HEADING = AIMakerLocators.OVERVIEW_HEADING
    STAT_EVALUATION_RUNS = AIMakerLocators.STAT_EVALUATION_RUNS
    STAT_TEST_CASES = AIMakerLocators.STAT_TEST_CASES
    STAT_MODELS = AIMakerLocators.STAT_MODELS
    STAT_ISSUES_FLAGGED = AIMakerLocators.STAT_ISSUES_FLAGGED
    SWITCH_ROLES_LINK = AIMakerLocators.SWITCH_ROLES_LINK
    ADD_NEW_MODEL_BUTTON = AIMakerLocators.ADD_NEW_MODEL_BUTTON
    ADD_ORGANISATION_BUTTON = AIMakerLocators.ADD_ORGANISATION_BUTTON
    EXTERNAL_REDIRECT_DIALOG = AIMakerLocators.EXTERNAL_REDIRECT_DIALOG
    EXTERNAL_REDIRECT_CONFIRM = AIMakerLocators.EXTERNAL_REDIRECT_CONFIRM

    def __init__(self, page: Page, org_id: int = CIVICDATALAB_ORG_ID) -> None:
        super().__init__(page)
        self.org_id = org_id
        self.dashboard_url = Config.url(f"/dashboard/ai-maker/{org_id}")

    # ── Navigation ─────────────────────────────────────────────────────────────

    def go_to_dashboard(self) -> "AIMakerPage":
        self.navigate(self.dashboard_url)
        self.wait_for_app_ready()
        return self

    def go_to_models(self) -> None:
        self.click(self.SIDEBAR_MODELS)
        self.wait_for_app_ready()

    def go_to_evaluations(self) -> None:
        self.click(self.SIDEBAR_EVALUATIONS)
        self.wait_for_app_ready()

    def go_to_prompt_libraries(self) -> None:
        self.click(self.SIDEBAR_PROMPT_LIBRARIES)
        self.wait_for_app_ready()

    def go_to_evaluators(self) -> None:
        self.click(self.SIDEBAR_EVALUATORS)
        self.wait_for_app_ready()

    def click_switch_roles(self) -> None:
        self.click(self.SWITCH_ROLES_LINK)
        self.wait_for_app_ready()

    # ── Overview stats ─────────────────────────────────────────────────────────

    def is_overview_visible(self) -> bool:
        return self.is_visible(self.OVERVIEW_HEADING)

    def is_stat_evaluation_runs_visible(self) -> bool:
        return self.is_visible(self.STAT_EVALUATION_RUNS)

    def is_stat_test_cases_visible(self) -> bool:
        return self.is_visible(self.STAT_TEST_CASES)

    def is_stat_models_visible(self) -> bool:
        return self.is_visible(self.STAT_MODELS)

    def is_stat_issues_flagged_visible(self) -> bool:
        return self.is_visible(self.STAT_ISSUES_FLAGGED)

    def get_stat_value(self, stat_label_selector: str) -> str:
        """Return the numeric text of a stat card adjacent to the given label."""
        container = self.page.locator(stat_label_selector).locator("..")
        # The number is usually in a sibling/child element
        texts = container.all_inner_texts()
        for t in texts:
            stripped = t.strip()
            if stripped.isdigit() or stripped.replace(",", "").isdigit():
                return stripped
        return ""

    # ── Sidebar ────────────────────────────────────────────────────────────────

    def is_sidebar_nav_complete(self) -> bool:
        """Return True if all five sidebar nav items are present."""
        return all([
            self.is_visible(self.SIDEBAR_HOME),
            self.is_visible(self.SIDEBAR_MODELS),
            self.is_visible(self.SIDEBAR_EVALUATIONS),
            self.is_visible(self.SIDEBAR_PROMPT_LIBRARIES),
            self.is_visible(self.SIDEBAR_EVALUATORS),
        ])

    # ── Models section on home ─────────────────────────────────────────────────

    def get_model_card_count(self) -> int:
        return self.page.locator(AIMakerLocators.MODEL_CARD).count()

    def is_add_new_model_visible(self) -> bool:
        return self.is_visible(self.ADD_NEW_MODEL_BUTTON)
