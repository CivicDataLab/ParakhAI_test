"""
E2E tests for the organisation selection page (/dashboard/ai-maker).
"""

import pytest

from pages.ai_maker_page import AIMakerPage
from pages.org_selection_page import OrgSelectionPage

pytestmark = [pytest.mark.e2e, pytest.mark.smoke, pytest.mark.regression, pytest.mark.auth]

CIVICDATALAB_ORG_NAME = "CivicdataLab"


class TestOrgSelectionPageLoad:
    """The org selection page loads and shows expected content."""

    def test_page_loads_at_expected_url(self, authenticated_page):
        page = OrgSelectionPage(authenticated_page)
        page.go_to_org_selection()
        url = authenticated_page.url
        assert "/ai-maker" in url or "/dashboard" in url, (
            f"Unexpected URL after navigating to org selection: {url}"
        )

    def test_org_card_or_redirect_visible(self, authenticated_page):
        page = OrgSelectionPage(authenticated_page)
        page.go_to_org_selection()
        has_cards = page.get_org_card_count() > 0
        has_heading = page.is_page_loaded()
        assert has_cards or has_heading, "Neither org cards nor page heading found"

    def test_civicdatalab_org_visible(self, authenticated_page):
        page = OrgSelectionPage(authenticated_page)
        page.go_to_org_selection()
        if not page.is_org_visible(CIVICDATALAB_ORG_NAME):
            pytest.skip(f"'{CIVICDATALAB_ORG_NAME}' org not present for this test account")
        assert page.is_org_visible(CIVICDATALAB_ORG_NAME)


class TestOrgSelectionNavigation:
    """Clicking an org card navigates to the correct AI Maker URL."""

    def test_clicking_org_navigates_to_ai_maker(self, authenticated_page):
        page = OrgSelectionPage(authenticated_page)
        page.go_to_org_selection()
        if page.get_org_card_count() == 0:
            pytest.skip("No org cards present — cannot test navigation")
        page.select_org_by_index(0)
        assert "/ai-maker/" in authenticated_page.url, (
            f"Expected /ai-maker/ in URL after org selection, got: {authenticated_page.url}"
        )

    def test_org_selection_lands_on_overview(self, authenticated_page):
        page = OrgSelectionPage(authenticated_page)
        page.go_to_org_selection()
        if page.get_org_card_count() == 0:
            pytest.skip("No org cards present — cannot test navigation")
        page.select_org_by_index(0)
        ai_maker = AIMakerPage(authenticated_page)
        assert ai_maker.is_overview_visible(), (
            "AIMaker overview heading not visible after org selection"
        )
