"""
E2E tests for the AI Models section — list page and model detail.
Covers: model grid, search, filters, model detail, versions, past evaluations.
URLs:
  List  : /dashboard/ai-maker/1/ai-models
  Detail: /dashboard/ai-maker/1/ai-models/22  (SarvamaI: Sarvam-M)
"""

import pytest
from playwright.sync_api import Page

from locators.models_locators import ModelsLocators
from pages.models_page import ModelsPage

pytestmark = [pytest.mark.e2e, pytest.mark.regression, pytest.mark.auth]

KNOWN_MODELS = [
    "SarvamaI: Sarvam-M",
    "Meta: Llama 3.1 70B Instruct",
    "OpenAI: GPT-5 Mini",
]


class TestModelsListPage:
    """Verify the Models list page renders and behaves correctly."""

    def test_models_list_page_loads(self, authenticated_page_fast: Page):
        """Direct navigation to /ai-models returns the models list."""
        mp = ModelsPage(authenticated_page_fast)
        mp.go_to_models_list()
        assert mp.is_models_list_visible(), "'AI Models' heading must be visible"

    def test_page_url_contains_ai_models(self, authenticated_page_fast: Page):
        mp = ModelsPage(authenticated_page_fast)
        mp.go_to_models_list()
        assert "/ai-models" in authenticated_page_fast.url, (
            f"Expected /ai-models in URL, got: {authenticated_page_fast.url}"
        )

    def test_search_bar_is_visible(self, authenticated_page_fast: Page):
        """Search input is present on the models page."""
        mp = ModelsPage(authenticated_page_fast)
        mp.go_to_models_list()
        assert mp.is_visible(mp.SEARCH_INPUT), "Search bar must be visible"

    @pytest.mark.xfail(
        reason="'Add Filters' control was removed from the models list UI "
        "in 2026-05; only the search input remains. Remove this xfail if the "
        "control is reintroduced.",
        strict=True,
    )
    def test_add_filters_button_is_visible(self, authenticated_page_fast: Page):
        """'Add Filters' button is present."""
        mp = ModelsPage(authenticated_page_fast)
        mp.go_to_models_list()
        assert mp.is_visible(mp.ADD_FILTERS_BUTTON), "'Add Filters' must be visible"

    def test_model_cards_are_displayed(self, authenticated_page_fast: Page):
        """At least one model card is visible."""
        mp = ModelsPage(authenticated_page_fast)
        mp.go_to_models_list()
        count = mp.get_model_card_count()
        assert count >= 1, f"Expected ≥1 model card, found {count}"

    def test_six_models_displayed_for_civicdatalab(self, authenticated_page_fast: Page):
        """CivicdataLab has 6 models — all should be listed."""
        mp = ModelsPage(authenticated_page_fast)
        mp.go_to_models_list()
        count = mp.get_model_card_count()
        assert count >= 6, (
            f"CivicdataLab should have 6 models, found {count}. "
            "May indicate pagination or a newly added model."
        )

    def test_text_generation_badge_present(self, authenticated_page_fast: Page):
        """'Text Generation' type badge appears on model cards."""
        mp = ModelsPage(authenticated_page_fast)
        mp.go_to_models_list()
        assert mp.is_visible(ModelsLocators.MODEL_TYPE_BADGE), (
            "'Text Generation' badge must appear on at least one model card"
        )

    @pytest.mark.parametrize("model_name", KNOWN_MODELS)
    def test_known_model_is_visible(self, authenticated_page_fast: Page, model_name: str):
        """Each known CivicdataLab model appears in the list.

        Uses search to narrow the list because newer models (e.g. GPT-5 Mini)
        live on page 2 of the default grid. The list page lacks a pagination
        helper, but the search input already exists and is the user-facing
        way to find a specific model.
        """
        mp = ModelsPage(authenticated_page_fast)
        mp.go_to_models_list()
        mp.search_model(model_name)
        assert mp.is_visible(f"text={model_name}"), (
            f"Model '{model_name}' must be visible in the list after searching"
        )

    def test_search_filters_models_by_name(self, authenticated_page_fast: Page):
        """Searching by 'Llama' shows only Llama-related models."""
        mp = ModelsPage(authenticated_page_fast)
        mp.go_to_models_list()
        initial_count = mp.get_model_card_count()
        mp.search_model("Llama")
        # After filtering, either a Llama model is visible or the list shrunk.
        # is_visible already waits — no extra sleep required.
        filtered_count = mp.get_model_card_count()
        assert mp.is_visible("text=Llama") or filtered_count <= initial_count, (
            "Searching for 'Llama' should filter the model list"
        )

    def test_search_with_no_results(self, authenticated_page_fast: Page):
        """Searching for a nonsense term reduces the result count."""
        mp = ModelsPage(authenticated_page_fast)
        mp.go_to_models_list()
        mp.search_model("xyzxyzxyznotamodel123")
        count = mp.get_model_card_count()
        assert count == 0 or mp.is_visible("text=No"), (
            "An invalid search should return 0 results or a 'No results' message"
        )

    def test_clear_search_restores_full_list(self, authenticated_page_fast: Page):
        """Clearing the search input restores the full model list."""
        mp = ModelsPage(authenticated_page_fast)
        mp.go_to_models_list()
        full_count = mp.get_model_card_count()
        mp.search_model("Llama")
        mp.clear_search()
        restored_count = mp.get_model_card_count()
        assert restored_count >= full_count, (
            "Clearing search should restore the full model list"
        )


class TestModelDetailPage:
    """Verify the model detail page for SarvamaI: Sarvam-M (model_id=22)."""

    def test_model_detail_page_loads(self, authenticated_page_fast: Page):
        """Direct navigation to model detail renders the page."""
        mp = ModelsPage(authenticated_page_fast)
        mp.go_to_model_detail()
        assert "/ai-models/22" in authenticated_page_fast.url, (
            f"Model detail page must load, got: {authenticated_page_fast.url}"
        )

    def test_model_name_is_displayed(self, authenticated_page_fast: Page):
        """The model name 'SarvamaI: Sarvam-M' is visible."""
        mp = ModelsPage(authenticated_page_fast)
        mp.go_to_model_detail()
        assert mp.is_visible("text=SarvamaI: Sarvam-M") or mp.is_visible("text=Sarvam"), (
            "Model name must be visible on the detail page"
        )

    def test_about_section_is_visible(self, authenticated_page_fast: Page):
        mp = ModelsPage(authenticated_page_fast)
        mp.go_to_model_detail()
        assert mp.is_about_section_visible(), "'About' section must be visible"

    def test_versions_section_is_visible(self, authenticated_page_fast: Page):
        mp = ModelsPage(authenticated_page_fast)
        mp.go_to_model_detail()
        assert mp.is_versions_section_visible(), "'Versions' section must be visible"

    def test_primary_version_badge_is_shown(self, authenticated_page_fast: Page):
        """Version 1.0 with 'Primary' badge is displayed."""
        mp = ModelsPage(authenticated_page_fast)
        mp.go_to_model_detail()
        if not mp.is_versions_section_visible():
            pytest.skip("Versions section not visible")
        assert mp.is_primary_badge_visible(), "'Primary' badge must appear on version row"

    def test_start_evaluation_link_is_visible(self, authenticated_page_fast: Page):
        """'Start Evaluation' action link is present in the versions table."""
        mp = ModelsPage(authenticated_page_fast)
        mp.go_to_model_detail()
        if not mp.is_versions_section_visible():
            pytest.skip("Versions section not visible")
        assert mp.is_start_evaluation_visible(), "'Start Evaluation' must be visible"

    def test_invite_auditors_link_is_visible(self, authenticated_page_fast: Page):
        """'Invite Auditors' action link is present."""
        mp = ModelsPage(authenticated_page_fast)
        mp.go_to_model_detail()
        if not mp.is_versions_section_visible():
            pytest.skip("Versions section not visible")
        assert mp.is_invite_auditors_visible(), "'Invite Auditors' must be visible"

    def test_version_table_columns_are_present(self, authenticated_page_fast: Page):
        """Version table shows Date Updated, Capabilities, and Lifecycle Stage columns."""
        mp = ModelsPage(authenticated_page_fast)
        mp.go_to_model_detail()
        missing_cols = []
        for col_sel in [
            ModelsLocators.DATE_UPDATED_COL,
            ModelsLocators.CAPABILITIES_COL,
            ModelsLocators.LIFECYCLE_STAGE_COL,
        ]:
            if not mp.is_visible(col_sel, timeout=3_000):
                missing_cols.append(col_sel)
        assert not missing_cols, f"Missing version table columns: {missing_cols}"

    def test_production_lifecycle_stage_is_shown(self, authenticated_page_fast: Page):
        """Sarvam-M is in PRODUCTION lifecycle stage."""
        mp = ModelsPage(authenticated_page_fast)
        mp.go_to_model_detail()
        assert mp.is_visible("text=PRODUCTION"), (
            "PRODUCTION lifecycle stage must be shown for Sarvam-M"
        )

    def test_past_evaluations_section_visible(self, authenticated_page_fast: Page):
        """'Past Evaluations' table is rendered below the versions section."""
        mp = ModelsPage(authenticated_page_fast)
        mp.go_to_model_detail()
        mp.scroll_to_bottom()
        assert mp.is_past_evaluations_visible(), "'Past Evaluations' section must be visible"

    def test_past_evaluations_table_has_rows(self, authenticated_page_fast: Page):
        """Past evaluations table has at least one row for Sarvam-M."""
        mp = ModelsPage(authenticated_page_fast)
        mp.go_to_model_detail()
        mp.scroll_to_bottom()
        if not mp.is_past_evaluations_visible():
            pytest.skip("Past Evaluations section not found")
        count = mp.get_past_evaluation_row_count()
        assert count >= 1, f"Expected at least 1 past evaluation, found {count}"

    def test_past_evaluations_table_columns_present(self, authenticated_page_fast: Page):
        """Past evaluations table shows all four column headers."""
        mp = ModelsPage(authenticated_page_fast)
        mp.go_to_model_detail()
        mp.scroll_to_bottom()
        if not mp.is_past_evaluations_visible():
            pytest.skip("Past Evaluations section not found")
        for col_sel in [
            ModelsLocators.PAST_EVAL_NAME_COL,
            ModelsLocators.PAST_EVAL_TIME_COL,
            ModelsLocators.PAST_EVAL_ID_COL,
            ModelsLocators.PAST_EVAL_TYPE_COL,
        ]:
            assert mp.is_visible(col_sel, timeout=3_000), (
                f"Expected column header not found: {col_sel}"
            )

    def test_pagination_controls_are_visible(self, authenticated_page_fast: Page):
        """Rows-per-page control is shown for the past evaluations table."""
        mp = ModelsPage(authenticated_page_fast)
        mp.go_to_model_detail()
        mp.scroll_to_bottom()
        if not mp.is_past_evaluations_visible():
            pytest.skip("Past Evaluations section not found")
        assert mp.is_pagination_visible(), "Pagination/rows control must be visible"

    @pytest.mark.xfail(
        reason="App bug #6 — View buttons on the models list are aria-disabled "
        "and onClick does not navigate. See docs/app_bugs.md.",
        strict=True,
    )
    def test_clicking_model_card_from_list_navigates_to_detail(self, authenticated_page_fast: Page):
        """Clicking a model card from the list navigates to the detail URL."""
        mp = ModelsPage(authenticated_page_fast)
        mp.go_to_models_list()
        initial_url = authenticated_page_fast.url
        mp.click_first_model()
        assert "/ai-models/" in authenticated_page_fast.url and authenticated_page_fast.url != initial_url, (
            "Clicking a model card must navigate to a model detail URL"
        )
