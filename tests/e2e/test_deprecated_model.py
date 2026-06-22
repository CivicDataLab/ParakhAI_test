"""
Deprecated model version controls — Jun 2026.

Covers the isDeprecatedLifecycle() guard added to the model detail page:
- "Start Evaluation" button is disabled for DEPRECATED/DEPRECETED/DEPRECIATED versions.
- Clicking it shows a toast "Sorry this model version is deprecated".

All tests auto-skip gracefully when no deprecated version exists in the test account.
"""

import pytest
from playwright.sync_api import Page

from locators.models_locators import ModelsLocators
from pages.models_page import ModelsPage

pytestmark = [pytest.mark.e2e, pytest.mark.auth]

# Known model ID used for navigation — model detail page is the test surface.
MODEL_ID = ModelsPage.__init__.__defaults__  # uses SARVAM_MODEL_ID default from ModelsPage


def _go_to_model_detail(page: Page) -> ModelsPage:
    mp = ModelsPage(page)
    mp.go_to_model_detail()
    return mp


class TestStartEvaluationButton:
    """Start Evaluation button is present for active versions."""

    @pytest.mark.smoke
    def test_start_evaluation_button_present_for_active_version(
        self, authenticated_page_fast: Page
    ):
        mp = _go_to_model_detail(authenticated_page_fast)
        if not mp.is_versions_section_visible():
            pytest.skip("No versions section found on model detail page")
        assert mp.is_start_evaluation_visible(), (
            "'Start Evaluation' button must be present on the model detail page"
        )


class TestDeprecatedVersionControls:
    """Start Evaluation is disabled for deprecated lifecycle stages."""

    def test_deprecated_version_shows_disabled_start_button(
        self, authenticated_page_fast: Page
    ):
        mp = _go_to_model_detail(authenticated_page_fast)
        disabled_btn = authenticated_page_fast.locator(
            ModelsLocators.START_EVALUATION_BUTTON_DISABLED
        )
        if disabled_btn.count() == 0:
            pytest.skip(
                "No deprecated model version found in test account — "
                "seed a version with lifecycle DEPRECATED to enable this test"
            )
        assert disabled_btn.first.is_visible(), (
            "Disabled 'Start Evaluation' button must be visible for deprecated version"
        )

    def test_deprecated_version_start_button_shows_toast_on_click(
        self, authenticated_page_fast: Page
    ):
        mp = _go_to_model_detail(authenticated_page_fast)
        disabled_btn = authenticated_page_fast.locator(
            ModelsLocators.START_EVALUATION_BUTTON_DISABLED
        )
        if disabled_btn.count() == 0:
            pytest.skip(
                "No deprecated model version found in test account — "
                "seed a version with lifecycle DEPRECATED to enable this test"
            )
        disabled_btn.first.click(force=True)
        authenticated_page_fast.wait_for_timeout(800)
        toast = authenticated_page_fast.locator(ModelsLocators.DEPRECATED_TOAST)
        assert toast.count() > 0, (
            "Expected a toast notification when clicking disabled 'Start Evaluation' "
            "on a deprecated version"
        )
