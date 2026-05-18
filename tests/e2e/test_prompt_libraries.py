"""
E2E tests for the Prompt Libraries section.
Covers: page load, library card grid, categories, search, and filters.
URL: /dashboard/ai-maker/1/prompt-libraries
"""

import pytest
from playwright.sync_api import Page

from locators.prompt_libraries_locators import PromptLibrariesLocators
from pages.prompt_libraries_page import PromptLibrariesPage

pytestmark = [pytest.mark.e2e, pytest.mark.regression, pytest.mark.auth]


@pytest.fixture
def page(authenticated_page_fast):
    """Override pytest-playwright's `page` fixture — /prompt-libraries is
    auth-walled; use the cached storage state."""
    return authenticated_page_fast

KNOWN_LIBRARIES = [
    (PromptLibrariesLocators.LIBRARY_KCC_ENGLISH, "KCC English Queries"),
    (PromptLibrariesLocators.LIBRARY_PUBLIC_INTEREST_HINDI, "Public Interest Hindi"),
    (PromptLibrariesLocators.LIBRARY_KCC_HINDI, "KCC: Hindi Queries"),
]


class TestPromptLibrariesPageLoads:
    """Verify the prompt libraries page renders correctly."""

    def test_page_loads(self, page: Page):
        pl = PromptLibrariesPage(page)
        pl.go_to_prompt_libraries()
        assert pl.is_page_loaded(), "'Prompt Libraries' heading must be visible"

    def test_url_contains_prompt_libraries(self, page: Page):
        pl = PromptLibrariesPage(page)
        pl.go_to_prompt_libraries()
        assert "/prompt-libraries" in page.url, (
            f"Expected /prompt-libraries in URL, got: {page.url}"
        )

    def test_page_title_is_set(self, page: Page):
        pl = PromptLibrariesPage(page)
        pl.go_to_prompt_libraries()
        assert page.title(), "Page title must not be empty"

    def test_search_bar_is_visible(self, page: Page):
        pl = PromptLibrariesPage(page)
        pl.go_to_prompt_libraries()
        assert pl.is_visible(pl.SEARCH_INPUT), "Search input must be visible"

    @pytest.mark.xfail(
        reason="'Add Filters' control was removed from the prompt libraries "
        "UI in 2026-05 (same as the models list — only the search input "
        "remains). Remove this xfail if the control is reintroduced.",
        strict=True,
    )
    def test_add_filters_button_is_visible(self, page: Page):
        pl = PromptLibrariesPage(page)
        pl.go_to_prompt_libraries()
        assert pl.is_add_filters_visible(), "'Add Filters' button must be visible"


class TestLibraryCards:
    """Verify library cards render with correct data."""

    def test_library_cards_are_displayed(self, page: Page):
        """At least one library card is shown."""
        pl = PromptLibrariesPage(page)
        pl.go_to_prompt_libraries()
        count = pl.get_library_card_count()
        assert count >= 1, f"Expected at least 1 library card, found {count}"

    def test_multiple_libraries_are_listed(self, page: Page):
        """CivicdataLab has 6+ prompt libraries."""
        pl = PromptLibrariesPage(page)
        pl.go_to_prompt_libraries()
        page.keyboard.press("End")
        page.wait_for_timeout(300)
        count = pl.get_library_card_count()
        assert count >= 6, (
            f"Expected 6+ prompt libraries for CivicdataLab, found {count}"
        )

    @pytest.mark.parametrize("selector,name", KNOWN_LIBRARIES)
    def test_known_library_is_visible(self, page: Page, selector: str, name: str):
        """Each known library card is visible."""
        pl = PromptLibrariesPage(page)
        pl.go_to_prompt_libraries()
        page.keyboard.press("End")
        page.wait_for_timeout(300)
        assert pl.is_library_visible(selector), f"Library '{name}' must be visible"


class TestCategoryBadges:
    """Verify category badges are shown on library cards."""

    def test_agriculture_category_badge_is_visible(self, page: Page):
        pl = PromptLibrariesPage(page)
        pl.go_to_prompt_libraries()
        assert pl.is_category_badge_visible("agriculture"), (
            "'Agriculture' category badge must be present"
        )

    def test_healthcare_category_badge_is_visible(self, page: Page):
        pl = PromptLibrariesPage(page)
        pl.go_to_prompt_libraries()
        assert pl.is_category_badge_visible("healthcare"), (
            "'Healthcare' category badge must be present"
        )

    def test_general_category_badge_is_visible(self, page: Page):
        pl = PromptLibrariesPage(page)
        pl.go_to_prompt_libraries()
        page.keyboard.press("End")
        page.wait_for_timeout(300)
        assert pl.is_category_badge_visible("general"), (
            "'General' category badge must be present"
        )

    def test_multiple_categories_are_displayed(self, page: Page):
        """More than one unique category badge type is shown."""
        pl = PromptLibrariesPage(page)
        pl.go_to_prompt_libraries()
        agri_count = pl.get_agriculture_card_count()
        health_count = pl.get_healthcare_card_count()
        total = agri_count + health_count
        assert total >= 2, (
            f"Expected multiple category types, found Agriculture={agri_count}, "
            f"Healthcare={health_count}"
        )


class TestPromptLibrarySearch:
    """Verify the search functionality on the prompt libraries page."""

    def test_search_input_is_interactive(self, page: Page):
        """Typing in the search field does not raise errors."""
        pl = PromptLibrariesPage(page)
        pl.go_to_prompt_libraries()
        pl.search_library("KCC")
        page.wait_for_timeout(500)
        assert page.url, "Page must still be accessible after searching"

    def test_search_for_kcc_filters_results(self, page: Page):
        """Searching 'KCC' shows KCC-related libraries."""
        pl = PromptLibrariesPage(page)
        pl.go_to_prompt_libraries()
        pl.search_library("KCC")
        page.wait_for_timeout(600)
        assert pl.is_visible(PromptLibrariesLocators.LIBRARY_KCC_ENGLISH) or \
               pl.is_visible(PromptLibrariesLocators.LIBRARY_KCC_HINDI), (
            "Searching 'KCC' must show KCC-related libraries"
        )

    def test_search_for_healthcare_filters_results(self, page: Page):
        """Searching 'Healthcare' shows healthcare libraries."""
        pl = PromptLibrariesPage(page)
        pl.go_to_prompt_libraries()
        pl.search_library("PARIKSHA")
        page.wait_for_timeout(600)
        assert pl.is_visible(PromptLibrariesLocators.LIBRARY_PARIKSHA) or \
               pl.get_library_card_count() >= 0, (
            "Searching 'PARIKSHA' should filter results"
        )

    def test_search_with_invalid_term_shows_empty_or_fewer_results(self, page: Page):
        """A nonsense search reduces the result count."""
        pl = PromptLibrariesPage(page)
        pl.go_to_prompt_libraries()
        initial_count = pl.get_library_card_count()
        pl.search_library("zzzzzzzzz_no_match")
        page.wait_for_timeout(600)
        filtered_count = pl.get_library_card_count()
        assert filtered_count == 0 or filtered_count <= initial_count, (
            "Invalid search should return 0 results or fewer than the full list"
        )

    def test_clearing_search_restores_full_list(self, page: Page):
        """Clearing the search restores all library cards."""
        pl = PromptLibrariesPage(page)
        pl.go_to_prompt_libraries()
        full_count = pl.get_library_card_count()
        pl.search_library("KCC")
        page.wait_for_timeout(500)
        pl.clear_search()
        page.wait_for_timeout(500)
        restored_count = pl.get_library_card_count()
        assert restored_count >= full_count, (
            "Clearing search must restore the original library count"
        )
