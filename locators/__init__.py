# Locators package — each module holds raw selector strings for one page/section.
# Keep selectors here; keep browser actions in pages/.
from locators.ai_maker_locators import AIMakerLocators
from locators.dashboard_locators import DashboardLocators
from locators.evaluations_locators import EvaluationsLocators
from locators.evaluator_role_locators import EvaluatorRoleLocators
from locators.evaluators_locators import EvaluatorsLocators
from locators.home_locators import HomeLocators
from locators.login_locators import LoginLocators
from locators.models_locators import ModelsLocators
from locators.prompt_libraries_locators import PromptLibrariesLocators
from locators.workspace_locators import WorkspaceLocators

__all__ = [
    "HomeLocators",
    "LoginLocators",
    "DashboardLocators",
    "WorkspaceLocators",
    "AIMakerLocators",
    "ModelsLocators",
    "EvaluationsLocators",
    "PromptLibrariesLocators",
    "EvaluatorsLocators",
    "EvaluatorRoleLocators",
]
