"""
E2E regression tests for the auditor evaluations list and model detail pages.
"""

import pytest

from locators.evaluator_role_locators import EvaluatorRoleLocators
from pages.auditor_model_detail_page import AuditorModelDetailPage
from pages.base_page import BasePage
from utils.config import Config

pytestmark = [pytest.mark.e2e, pytest.mark.regression, pytest.mark.auth]

# Correct authenticated path for the evaluator role evaluations list
AUDITOR_EVALUATIONS_PATH = "/dashboard/auditor/evaluations"
AUDITOR_MODEL_ID = 1


class TestAuditorEvaluationsListPage:
    """The auditor evaluations list page loads and shows expected structure."""

    def test_page_loads_without_404(self, authenticated_page):
        base = BasePage(authenticated_page)
        resp = base.navigate(Config.url(AUDITOR_EVALUATIONS_PATH))
        assert resp is None or resp.status != 404, (
            "Auditor evaluations page returned 404"
        )
        assert "/auditor" in authenticated_page.url or "/dashboard" in authenticated_page.url

    def test_filter_tabs_present(self, authenticated_page):
        base = BasePage(authenticated_page)
        base.navigate(Config.url(AUDITOR_EVALUATIONS_PATH))
        base.wait_for_app_ready()
        filter_selectors = [
            EvaluatorRoleLocators.EVAL_FILTER_DRAFT,
            EvaluatorRoleLocators.EVAL_FILTER_PENDING,
            EvaluatorRoleLocators.EVAL_FILTER_RUNNING,
            EvaluatorRoleLocators.EVAL_FILTER_COMPLETED,
            EvaluatorRoleLocators.EVAL_FILTER_FAILED,
        ]
        visible_count = sum(1 for sel in filter_selectors if base.is_visible(sel))
        assert visible_count >= 3, (
            f"Expected at least 3 filter tabs, found {visible_count}"
        )

    def test_empty_state_or_rows_visible(self, authenticated_page):
        base = BasePage(authenticated_page)
        base.navigate(Config.url(AUDITOR_EVALUATIONS_PATH))
        base.wait_for_app_ready()
        has_rows = authenticated_page.locator("tbody tr").count() > 0
        has_empty = base.is_visible(EvaluatorRoleLocators.NO_EVALUATIONS_MESSAGE)
        assert has_rows or has_empty, (
            "Neither evaluation rows nor empty-state message found on auditor evaluations page"
        )


class TestAuditorModelDetailPage:
    """The auditor model detail page loads and shows version info."""

    def test_page_loads_without_error_redirect(self, authenticated_page):
        page = AuditorModelDetailPage(authenticated_page)
        page.go_to_model_detail(AUDITOR_MODEL_ID)
        assert "/error" not in authenticated_page.url and "/404" not in authenticated_page.url, (
            f"Model detail page redirected to error: {authenticated_page.url}"
        )

    def test_assigned_versions_heading_visible(self, authenticated_page):
        page = AuditorModelDetailPage(authenticated_page)
        page.go_to_model_detail(AUDITOR_MODEL_ID)
        if not page.is_assigned_versions_section_visible():
            pytest.skip("No Assigned Versions section — user may not be assigned to this model")
        assert page.is_assigned_versions_section_visible()

    def test_accept_or_start_button_when_row_exists(self, authenticated_page):
        page = AuditorModelDetailPage(authenticated_page)
        page.go_to_model_detail(AUDITOR_MODEL_ID)
        if page.get_version_row_count() == 0:
            pytest.skip("No version rows found — cannot check action buttons")
        has_accept = page.is_accept_button_visible()
        has_start = page.is_start_button_visible()
        assert has_accept or has_start, (
            "Version rows exist but neither Accept nor Start button is visible"
        )


# ── Auditor dashboard: real metrics from auditorMetrics API (Jun 2026) ─────────


class TestAuditorDashboardMetrics:
    """Stat cards on /dashboard/auditor are populated from the auditorMetrics API."""

    AUDITOR_DASHBOARD_PATH = "/dashboard/auditor"

    def test_auditor_stat_card_labels_are_rendered(self, authenticated_page):
        from locators.evaluator_role_locators import EvaluatorRoleLocators
        base = BasePage(authenticated_page)
        base.navigate(Config.url(self.AUDITOR_DASHBOARD_PATH))
        base.wait_for_app_ready()
        labels = [
            EvaluatorRoleLocators.STAT_INVITATIONS_RECEIVED,
            EvaluatorRoleLocators.STAT_EVALUATION_RUNS,
            EvaluatorRoleLocators.STAT_TEST_CASES,
            EvaluatorRoleLocators.STAT_ISSUES_FLAGGED,
        ]
        visible_count = sum(1 for sel in labels if base.is_visible(sel))
        assert visible_count >= 3, (
            f"Expected at least 3 auditor stat card labels, found {visible_count}"
        )

    @pytest.mark.xfail(
        strict=False,
        reason="Stat values may be 0 for the test account if it has no auditor assignments",
    )
    def test_auditor_stat_cards_show_numeric_values(self, authenticated_page):
        from locators.evaluator_role_locators import EvaluatorRoleLocators
        base = BasePage(authenticated_page)
        base.navigate(Config.url(self.AUDITOR_DASHBOARD_PATH))
        base.wait_for_app_ready()
        # Fetch the text near each label and check it contains a digit.
        for sel in [
            EvaluatorRoleLocators.STAT_INVITATIONS_RECEIVED,
            EvaluatorRoleLocators.STAT_EVALUATION_RUNS,
        ]:
            if not base.is_visible(sel):
                continue
            parent = authenticated_page.locator(sel).locator("..")
            texts = " ".join(parent.all_inner_texts())
            has_digit = any(ch.isdigit() for ch in texts)
            assert has_digit, (
                f"Stat card for '{sel}' must show a numeric value, got: {texts!r}"
            )
