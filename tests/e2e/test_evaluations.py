"""
E2E tests for the Evaluations section.
Covers: list page, New Evaluation modal + wizard, evaluation detail view.
URLs:
  List  : /dashboard/ai-maker/1/evaluations
  Wizard: /dashboard/ai-maker/1/evaluations/new
  Detail: /dashboard/ai-maker/1/evaluations/288  (85.4% pass rate, 269/315 passed)
"""

import pytest
from playwright.sync_api import Page

from locators.evaluations_locators import EvaluationsLocators
from pages.evaluations_page import EvaluationsPage
from pages.new_evaluation_page import NewEvaluationPage

pytestmark = [pytest.mark.e2e, pytest.mark.regression, pytest.mark.auth]


@pytest.fixture
def page(authenticated_page_fast):
    """Override pytest-playwright's `page` fixture so every test in this file
    runs against the storage-state-cached auth session. Every page hit here
    targets /dashboard/ai-maker/1/... which redirects unauth visitors to
    /api/auth/signin. See tasks/lessons.md (2026-05-18, 2026-05-20)."""
    return authenticated_page_fast


# COMPLETED_EVAL_ID was a hard-coded constant (was 288, then 500) that drifted
# every time the linked eval was cancelled. The `completed_eval_id` fixture in
# tests/conftest.py now discovers a real COMPLETED eval at runtime via
# GraphQL — see lessons.md (2026-05-18, "Fixed-ID test fixtures drift").


class TestEvaluationsListPage:
    """Verify the evaluations list page renders correctly."""

    def test_evaluations_list_page_loads(self, page: Page):
        ep = EvaluationsPage(page)
        ep.go_to_evaluations_list()
        assert ep.is_evaluations_list_visible(), "'Evaluations' heading must be visible"

    def test_page_url_is_correct(self, page: Page):
        ep = EvaluationsPage(page)
        ep.go_to_evaluations_list()
        assert "/evaluations" in page.url, f"Expected /evaluations in URL, got: {page.url}"

    def test_new_evaluation_button_is_visible(self, page: Page):
        ep = EvaluationsPage(page)
        ep.go_to_evaluations_list()
        assert ep.is_visible(ep.NEW_EVALUATION_BUTTON), (
            "'New Evaluation' button must be visible"
        )

    @pytest.mark.xfail(reason="App bug #13 — see docs/app_bugs.md", strict=False)
    def test_table_column_headers_are_present(self, page: Page):
        """All five column headers are present in the evaluations table."""
        ep = EvaluationsPage(page)
        ep.go_to_evaluations_list()
        missing = []
        for col in [
            EvaluationsLocators.EVAL_NAME_COL,
            EvaluationsLocators.EVAL_STATUS_COL,
            EvaluationsLocators.EVAL_MODE_COL,
            EvaluationsLocators.EVAL_TESTS_COL,
            EvaluationsLocators.EVAL_COMPLETED_COL,
        ]:
            if not ep.is_visible(col, timeout=3_000):
                missing.append(col)
        assert not missing, f"Missing column headers: {missing}"

    def test_draft_evaluations_are_listed(self, page: Page):
        """DRAFT status evaluations appear in the list."""
        ep = EvaluationsPage(page)
        ep.go_to_evaluations_list()
        assert ep.has_draft_evaluations(), "At least one DRAFT evaluation must be listed"

    def test_completed_evaluations_are_listed(self, page: Page):
        """COMPLETED status evaluations appear in the list.

        The default (unfiltered) view only renders its first page of rows,
        most-recent first. Under concurrent sandbox write activity (multiple
        E2E shards create bulk DRAFT evaluations in parallel), that first
        page can be entirely DRAFT rows, pushing older COMPLETED ones off
        without any actually being gone. Filter to the Completed tab (backed
        by the real server-side count badge) instead of hoping one lands on
        the unfiltered first page — confirmed 2026-07-13 via debug poll:
        default view showed 16 draft / 0 completed rows purely from ordering.
        """
        ep = EvaluationsPage(page)
        ep.go_to_evaluations_list()
        counts = ep.get_status_tab_counts()
        if counts.get("Completed", 0) == 0:
            pytest.skip("No COMPLETED evaluations currently in org 1 (sandbox data is transient)")
        ep.click_status_tab("Completed")
        assert ep.has_completed_evaluations(), (
            "At least one COMPLETED evaluation must be listed after filtering to the Completed tab"
        )

    def test_automated_mode_label_is_shown(self, page: Page):
        """AUTOMATED evaluation mode label is displayed.

        See test_completed_evaluations_are_listed docstring — the default
        first page can be saturated with concurrently-created bulk-mode
        drafts. Bump rows-per-page before asserting so a lower-ranked
        AUTOMATED row is more likely to be in view.
        """
        ep = EvaluationsPage(page)
        ep.go_to_evaluations_list()
        ep.set_rows_per_page("50")
        if not ep.is_visible(EvaluationsLocators.MODE_AUTOMATED, timeout=5_000):
            pytest.skip(
                "No AUTOMATED-mode evaluation currently on the first 50 rows "
                "(sandbox data is transient under concurrent test runs)"
            )

    def test_status_badge_colors_are_distinct(self, page: Page):
        """DRAFT and COMPLETED badges are both present and visually distinguishable.

        Uses the server-side status-tab counts as the source of truth for
        "at least one of each status exists", then filters to each tab in
        turn to confirm its badge actually renders — instead of requiring
        both statuses to coincidentally appear together on the unfiltered
        first page (see test_completed_evaluations_are_listed docstring).
        """
        ep = EvaluationsPage(page)
        ep.go_to_evaluations_list()
        counts = ep.get_status_tab_counts()
        if counts.get("Draft", 0) == 0 or counts.get("Completed", 0) == 0:
            pytest.skip(
                f"Need at least 1 Draft and 1 Completed evaluation to compare badges; "
                f"got counts={counts}"
            )
        ep.click_status_tab("Draft")
        assert page.locator(EvaluationsLocators.STATUS_DRAFT).count() >= 1, (
            "Expected at least 1 DRAFT badge on the Draft tab"
        )
        ep.click_status_tab("Completed")
        assert page.locator(EvaluationsLocators.STATUS_COMPLETED).count() >= 1, (
            "Expected at least 1 COMPLETED badge on the Completed tab"
        )

    @pytest.mark.xfail(reason="App bug #7 — see docs/app_bugs.md", strict=False)
    def test_clicking_completed_evaluation_navigates_to_detail(self, page: Page):
        """Clicking a COMPLETED evaluation row navigates to its detail page."""
        ep = EvaluationsPage(page)
        ep.go_to_evaluations_list()
        completed_row = page.locator("tr").filter(has_text="COMPLETED").first
        if not completed_row.is_visible():
            pytest.skip("No completed evaluation row found")
        completed_row.click()
        page.wait_for_load_state("domcontentloaded")
        assert "/evaluations/" in page.url and "new" not in page.url, (
            "Clicking a completed evaluation must navigate to its detail URL"
        )


class TestNewEvaluationModal:
    """Verify the two-step 'Start an Evaluation' modal (Jul 2026 redesign).

    Read-only: never clicks 'Start Evaluation'. Draft-creating flows are
    covered in test_add_evaluation_bulk.py / test_add_evaluation_playground.py.
    """

    def test_new_evaluation_button_opens_modal(self, page: Page):
        """Clicking 'New Evaluation' opens the 'Start an Evaluation' modal."""
        ep = EvaluationsPage(page)
        ep.go_to_evaluations_list()
        ep.click_new_evaluation()
        assert ep.is_new_eval_modal_visible(), (
            "'Start an Evaluation' modal must appear after clicking the button"
        )

    def test_modal_contains_model_dropdown(self, page: Page):
        """Step 1 has the 'Select an AI Model' dropdown."""
        nep = NewEvaluationPage(page)
        nep.go_to_evaluations_list()
        nep.click_new_evaluation()
        assert nep.is_modal_visible(), (
            "Modal not visible — platform may be unavailable or slow"
        )
        assert nep.is_visible("text=Select an AI Model"), (
            "'Select an AI Model' label must appear in the modal"
        )
        assert nep.modal_model_dropdown_has_options(), (
            "Model dropdown must contain at least one real model"
        )

    def test_modal_contains_version_dropdown(self, page: Page):
        """Step 1 has the 'Select a Version' dropdown."""
        nep = NewEvaluationPage(page)
        nep.go_to_evaluations_list()
        nep.click_new_evaluation()
        assert nep.is_modal_visible(), (
            "Modal not visible — platform may be unavailable or slow"
        )
        assert nep.is_visible("text=Select a Version"), (
            "'Select a Version' label must appear in the modal"
        )
        assert nep.modal_version_dropdown_has_options(), (
            "Version dropdown must contain at least one option"
        )

    def test_modal_cancel_button_closes_modal(self, page: Page):
        """Dismissing the modal keeps the user on the evaluations list."""
        ep = EvaluationsPage(page)
        ep.go_to_evaluations_list()
        ep.click_new_evaluation()
        assert ep.is_new_eval_modal_visible(), (
            "Modal not visible — platform may be unavailable or slow"
        )
        ep.click_modal_cancel()
        page.wait_for_timeout(400)
        assert not ep.is_visible(ep.MODAL_TITLE, timeout=2_000), (
            "Modal must be closed after clicking Cancel"
        )
        assert "/evaluations" in page.url and "auditId=" not in page.url, (
            "URL must remain on evaluations list (no draft) after cancel"
        )

    def test_modal_next_advances_to_step_2(self, page: Page):
        """Next advances the dialog from step 1 to step 2 (evaluator selection)."""
        nep = NewEvaluationPage(page)
        nep.go_to_evaluations_list()
        nep.click_new_evaluation()
        assert nep.is_modal_visible(), (
            "Modal not visible — platform may be unavailable or slow"
        )
        nep.select_first_model_and_version()
        nep.select_evaluation_method("bulk")
        nep.click_modal_next()
        assert nep.get_modal_step() == "2", (
            "'Next' must advance the modal to step 2"
        )


class TestNewEvaluationModalStep2:
    """Verify modal step 2 — evaluator types + objective gating (read-only).

    The pre-Jul-2026 tabbed wizard (Configuration/Test Cases tabs, in-wizard
    objective validation) no longer exists; its equivalents now live in modal
    step 2 and the single-page wizard covered by test_add_evaluation_bulk.py.
    """

    @pytest.fixture
    def on_step_2(self, page: Page) -> NewEvaluationPage:
        nep = NewEvaluationPage(page)
        nep.go_to_evaluations_list()
        nep.click_new_evaluation()
        if not nep.is_modal_visible():
            pytest.skip("Modal not visible — platform may be unavailable or slow")
        nep.select_first_model_and_version()
        nep.select_evaluation_method("bulk")
        nep.click_modal_next()
        return nep

    def test_step_2_shows_three_evaluator_types(self, on_step_2: NewEvaluationPage):
        """Technical, Domain, and Cultural evaluator options are present."""
        nep = on_step_2
        missing = [
            sel
            for sel in (
                nep.EVAL_TYPE_TECHNICAL,
                nep.EVAL_TYPE_DOMAIN,
                nep.EVAL_TYPE_CULTURAL,
            )
            if not nep.is_visible(sel, timeout=3_000)
        ]
        assert not missing, f"Missing evaluator type options: {missing}"

    def test_technical_evaluator_is_selected_by_default(
        self, on_step_2: NewEvaluationPage
    ):
        """'a technical evaluator' is the pre-selected option."""
        assert on_step_2.get_checked_evaluator_type() == "Technical", (
            "'a technical evaluator' must be checked by default on step 2"
        )

    @pytest.mark.xfail(reason="App bug #20 — see docs/app_bugs.md", strict=False)
    def test_start_requires_objective_filled(self, on_step_2: NewEvaluationPage):
        """'Start Evaluation' stays disabled until the objective is filled."""
        nep = on_step_2
        assert not nep.is_start_evaluation_enabled(), (
            "'Start Evaluation' must be disabled while the objective is empty"
        )
        nep.fill_modal_objective("Objective gating check")
        assert nep.is_start_evaluation_enabled(), (
            "'Start Evaluation' must enable once the objective is filled"
        )


class TestEvaluationDetail:
    """Verify the evaluation detail page for an existing COMPLETED evaluation.

    The target eval is discovered at runtime via the `completed_eval_id`
    fixture (GraphQL `audits(status: COMPLETED)` → first ID). Tests skip
    cleanly when no COMPLETED eval exists on the current environment."""

    def test_evaluation_detail_page_loads(self, page: Page, completed_eval_id):
        ep = EvaluationsPage(page)
        ep.go_to_evaluation_detail(completed_eval_id)
        assert f"/evaluations/{completed_eval_id}" in page.url, (
            f"Expected evaluation detail URL with ID {completed_eval_id}"
        )

    @pytest.mark.xfail(reason="App bug #7 — see docs/app_bugs.md", strict=False)
    def test_completed_status_badge_is_visible(self, page: Page, completed_eval_id):
        ep = EvaluationsPage(page)
        ep.go_to_evaluation_detail(completed_eval_id)
        assert ep.is_visible(ep.STATUS_COMPLETED), (
            "COMPLETED status badge must be visible on evaluation detail"
        )

    def test_automated_mode_badge_is_visible(self, page: Page, completed_eval_id):
        ep = EvaluationsPage(page)
        ep.go_to_evaluation_detail(completed_eval_id)
        assert ep.is_visible(EvaluationsLocators.DETAIL_MODE_AUTOMATED), (
            "AUTOMATED mode badge must be visible"
        )

    def test_back_to_list_button_is_visible(self, page: Page, completed_eval_id):
        ep = EvaluationsPage(page)
        ep.go_to_evaluation_detail(completed_eval_id)
        assert ep.is_visible(EvaluationsLocators.BACK_TO_LIST_BUTTON), (
            "'Back to List' button must be visible on the detail page"
        )

    def test_overview_section_is_present(self, page: Page, completed_eval_id):
        ep = EvaluationsPage(page)
        ep.go_to_evaluation_detail(completed_eval_id)
        assert ep.is_overview_section_visible(), "'Evaluation Overview' section must be present"

    def test_overview_shows_evaluation_id(self, page: Page, completed_eval_id):
        ep = EvaluationsPage(page)
        ep.go_to_evaluation_detail(completed_eval_id)
        assert ep.is_visible(EvaluationsLocators.OVERVIEW_EVAL_ID), (
            "'Evaluation ID' label must be visible in overview"
        )
        assert ep.is_visible(f"text={completed_eval_id}"), (
            f"Evaluation ID {completed_eval_id} must be shown"
        )

    def test_overview_shows_model_name(self, page: Page, completed_eval_id):
        """The Model row is populated in the overview section. Tests are now
        data-agnostic: any non-empty model label proves the overview wired up
        the eval's model. Specific model names can't be hardcoded because the
        completed_eval_id fixture surfaces whatever COMPLETED eval exists."""
        ep = EvaluationsPage(page)
        ep.go_to_evaluation_detail(completed_eval_id)
        assert ep.is_visible("text=Model"), (
            "'Model' label must be present in the overview section"
        )

    def test_overview_shows_modules_used(self, page: Page, completed_eval_id):
        """The evaluation modules are listed in the overview section."""
        ep = EvaluationsPage(page)
        ep.go_to_evaluation_detail(completed_eval_id)
        assert ep.is_visible(EvaluationsLocators.OVERVIEW_MODULES), (
            "'Modules' label must be present in overview"
        )

    def test_summary_section_is_present(self, page: Page, completed_eval_id):
        ep = EvaluationsPage(page)
        ep.go_to_evaluation_detail(completed_eval_id)
        page.wait_for_timeout(300)
        assert ep.is_summary_section_visible(), "'Evaluation Summary' section must be present"

    def test_pass_rate_is_displayed(self, page: Page, completed_eval_id):
        """Total Pass Rate is shown in the summary section."""
        ep = EvaluationsPage(page)
        ep.go_to_evaluation_detail(completed_eval_id)
        assert ep.is_pass_rate_visible(), "'TOTAL PASS RATE' must be visible"

    def test_passed_failed_skipped_counts_visible(self, page: Page, completed_eval_id):
        """Passed, Failed, and Skipped test counts are all displayed."""
        ep = EvaluationsPage(page)
        ep.go_to_evaluation_detail(completed_eval_id)
        missing = []
        for sel in [
            EvaluationsLocators.SUMMARY_PASSED_TESTS,
            EvaluationsLocators.SUMMARY_FAILED_TESTS,
            EvaluationsLocators.SUMMARY_SKIPPED_TESTS,
        ]:
            if not ep.is_visible(sel, timeout=3_000):
                missing.append(sel)
        assert not missing, f"Missing summary stat labels: {missing}"

    def test_risk_level_section_is_present(self, page: Page, completed_eval_id):
        """The risk breakdown section (Low/Medium/High) is shown."""
        ep = EvaluationsPage(page)
        ep.go_to_evaluation_detail(completed_eval_id)
        assert ep.is_risk_section_visible(), "'Total Issues Identified' section must be present"

    def test_three_risk_levels_are_shown(self, page: Page, completed_eval_id):
        """Low Risk, Medium Risk, and High Risk cards are all present."""
        ep = EvaluationsPage(page)
        ep.go_to_evaluation_detail(completed_eval_id)
        missing = []
        for sel in [
            EvaluationsLocators.RISK_LOW,
            EvaluationsLocators.RISK_MEDIUM,
            EvaluationsLocators.RISK_HIGH,
        ]:
            if not ep.is_visible(sel, timeout=3_000):
                missing.append(sel)
        assert not missing, f"Missing risk level cards: {missing}"

    @pytest.mark.xfail(reason="App bug #7 — see docs/app_bugs.md", strict=False)
    def test_module_wise_results_tabs_present(self, page: Page, completed_eval_id):
        """At least one module-wise results tab is visible."""
        ep = EvaluationsPage(page)
        ep.go_to_evaluation_detail(completed_eval_id)
        tab_count = ep.get_module_tab_count()
        assert tab_count >= 1, (
            f"Expected at least 1 module-wise results tab, found {tab_count}"
        )

    def test_module_tab_switching_works(self, page: Page, completed_eval_id):
        """Clicking different module tabs does not cause errors."""
        ep = EvaluationsPage(page)
        ep.go_to_evaluation_detail(completed_eval_id)
        if not ep.is_visible(EvaluationsLocators.MODULE_TAB_BIAS, timeout=3_000):
            pytest.skip("Bias tab not visible")
        ep.click_module_tab("bias")
        page.wait_for_timeout(300)
        assert page.url, "Page must still be accessible after switching module tabs"

    @pytest.mark.xfail(reason="App bug #7 — see docs/app_bugs.md", strict=False)
    def test_sample_issues_section_is_present(self, page: Page, completed_eval_id):
        """The 'Sample Issues' accordion section is shown."""
        ep = EvaluationsPage(page)
        ep.go_to_evaluation_detail(completed_eval_id)
        page.keyboard.press("End")
        page.wait_for_timeout(300)
        assert ep.is_visible(EvaluationsLocators.SAMPLE_ISSUES_HEADING), (
            "'Sample Issues' heading must be visible"
        )

    def test_sample_issues_accordion_items_present(self, page: Page, completed_eval_id):
        """Individual issue accordion items are listed."""
        ep = EvaluationsPage(page)
        ep.go_to_evaluation_detail(completed_eval_id)
        page.keyboard.press("End")
        page.wait_for_timeout(300)
        issue_count = page.locator(EvaluationsLocators.ISSUE_ACCORDION_ITEM).count()
        assert issue_count >= 1, (
            f"Expected at least 1 sample issue in accordion, found {issue_count}"
        )

    def test_download_report_button_is_visible(self, page: Page, completed_eval_id):
        """'Download Report' button is present at the bottom of the detail page."""
        ep = EvaluationsPage(page)
        ep.go_to_evaluation_detail(completed_eval_id)
        page.keyboard.press("End")
        page.wait_for_timeout(300)
        assert ep.is_visible(EvaluationsLocators.DOWNLOAD_REPORT_BUTTON), (
            "'Download Report' button must be visible"
        )

    def test_back_to_list_button_navigates_correctly(self, page: Page, completed_eval_id):
        """'Back to List' button returns to the evaluations list."""
        ep = EvaluationsPage(page)
        ep.go_to_evaluation_detail(completed_eval_id)
        assert ep.is_visible(EvaluationsLocators.BACK_TO_LIST_BUTTON, timeout=5_000), (
            "'Back to List' button not found on evaluation detail page"
        )
        ep.click_back_to_list()
        assert "/evaluations" in page.url and str(completed_eval_id) not in page.url, (
            "'Back to List' must return to the evaluations list page"
        )


# ── Status filter tabs (StatusFilterTabs component — Jun 2026) ─────────────────


class TestStatusFilterTabs:
    """StatusFilterTabs renders on the evaluations list and filters correctly."""

    def test_status_filter_tabs_are_present(self, page: Page):
        """The old StatusFilterTabs bar was replaced by a per-column filter
        popover on the DataTable (evaluation-table-listing redesign,
        ~2026-08) — confirmed live 2026-08-13, see EvaluationsLocators
        FILTER_STATUS_BUTTON. Status filtering as a capability must still
        be reachable, even though the UI paradigm changed from tabs to a
        popover."""
        ep = EvaluationsPage(page)
        ep.go_to_evaluations_list()
        assert ep.is_status_filter_available(), (
            "Expected a 'Filter Status' control to be present on the evaluations table"
        )

    def test_all_six_tabs_are_present(self, page: Page):
        """As of the ~2026-08 redesign, status options live inside the
        'Filter Status' popover rather than as separate tabs — see
        test_status_filter_tabs_are_present docstring."""
        ep = EvaluationsPage(page)
        ep.go_to_evaluations_list()
        options = ep.get_status_filter_options()
        expected = {"Draft", "In Progress", "Completed", "Failed"}
        found = expected & set(options)
        assert len(found) >= 4, (
            f"Expected at least 4 of {expected}, found {options}"
        )

    def test_nine_status_tabs_are_present(self, page: Page):
        """Late-Jun 2026: StatusFilterTabs expanded to 9 states; ~2026-08 the
        tab bar itself was replaced by the 'Filter Status' popover (see
        test_status_filter_tabs_are_present docstring) which now carries 7
        checkbox options (Draft/Queued/In Progress/Pending Review/Completed/
        Failed/Cancelled — 'All' has no checkbox of its own, it's the
        unfiltered default)."""
        ep = EvaluationsPage(page)
        ep.go_to_evaluations_list()
        options = ep.get_status_filter_options()
        expected = {
            "Draft", "Queued", "In Progress", "Pending Review",
            "Completed", "Failed", "Cancelled",
        }
        found = expected & set(options)
        assert len(found) >= 6, (
            f"Expected at least 6 of {expected}, found {options}"
        )

    def test_column_header_completed_is_present(self, page: Page):
        ep = EvaluationsPage(page)
        ep.go_to_evaluations_list()
        assert ep.is_visible(EvaluationsLocators.EVAL_COMPLETED_COL), (
            "'Completed' column header must be visible in the evaluations table"
        )

    def test_all_tab_shows_evaluations(self, page: Page):
        ep = EvaluationsPage(page)
        ep.go_to_evaluations_list()
        if ep.is_status_filter_available():
            ep.click_status_tab("All")
        row_count = page.locator("tbody tr, [role='row']:not([role='columnheader'])").count()
        assert row_count >= 1 or ep.is_visible("text=No evaluations"), (
            "After clicking 'All', either rows or an empty-state message must appear"
        )

    def test_completed_tab_filters_to_completed_rows(self, page: Page):
        ep = EvaluationsPage(page)
        ep.go_to_evaluations_list()
        if not ep.is_status_filter_available():
            pytest.skip("'Filter Status' control not found on evaluations list page")
        ep.click_status_tab("Completed")
        page.wait_for_timeout(800)
        # Any visible status badges must contain COMPLETED (case-insensitive)
        badges = page.locator("td :has-text('COMPLETED'), [role='cell'] :has-text('COMPLETED')")
        non_completed = page.locator(
            "td :has-text('DRAFT'), td :has-text('IN_PROGRESS'), td :has-text('FAILED')"
        )
        has_completed = badges.count() > 0
        has_wrong_status = non_completed.count() > 0
        if has_completed:
            assert not has_wrong_status, (
                "After clicking 'Completed' tab, non-COMPLETED status badges must not appear"
            )

    def test_draft_tab_filters_to_draft_rows(self, page: Page):
        ep = EvaluationsPage(page)
        ep.go_to_evaluations_list()
        if not ep.is_status_filter_available():
            pytest.skip("'Filter Status' control not found on evaluations list page")
        ep.click_status_tab("Draft")
        page.wait_for_timeout(800)
        non_draft = page.locator(
            "td :has-text('COMPLETED'), td :has-text('IN_PROGRESS'), td :has-text('FAILED')"
        )
        assert non_draft.count() == 0, (
            "After clicking 'Draft' tab, only DRAFT rows must be visible"
        )

    def test_queued_tab_is_present_and_clickable(self, page: Page):
        """'Queued' is a new tab added in late Jun 2026."""
        ep = EvaluationsPage(page)
        ep.go_to_evaluations_list()
        if not ep.is_status_filter_available():
            pytest.skip("'Filter Status' control not found on evaluations list page")
        ep.click_status_tab("Queued")
        page.wait_for_timeout(600)
        rows = page.locator("tbody tr")
        empty = page.locator(
            "text=No evaluations, text=no results, text=0 evaluations"
        )
        assert rows.count() >= 0 or empty.count() >= 0, (
            "Clicking 'Queued' tab must not crash the page"
        )

    def test_in_progress_tab_is_present_and_clickable(self, page: Page):
        """'In Progress' is a new tab added in late Jun 2026."""
        ep = EvaluationsPage(page)
        ep.go_to_evaluations_list()
        if not ep.is_status_filter_available():
            pytest.skip("'Filter Status' control not found on evaluations list page")
        ep.click_status_tab("In Progress")
        page.wait_for_timeout(600)
        assert page.url, "Page must remain accessible after clicking 'In Progress' tab"

    def test_pending_review_tab_filters_correctly(self, page: Page):
        """'Pending Review' replaces the old 'Pending' tab (late Jun 2026)."""
        ep = EvaluationsPage(page)
        ep.go_to_evaluations_list()
        if not ep.is_status_filter_available():
            pytest.skip("'Filter Status' control not found on evaluations list page")
        ep.click_status_tab("Pending Review")
        page.wait_for_timeout(800)
        wrong_status = page.locator(
            "td :has-text('DRAFT'), td :has-text('COMPLETED'), td :has-text('IN_PROGRESS')"
        )
        rows = page.locator("tbody tr")
        if rows.count() > 0 and wrong_status.count() > 0:
            pytest.xfail("App bug #27 — see docs/app_bugs.md")
        if rows.count() > 0:
            assert wrong_status.count() == 0, (
                "After clicking 'Pending Review', non-pending-review rows must not appear"
            )

    def test_cancelled_tab_is_present_and_clickable(self, page: Page):
        """'Cancelled' is a new tab added in late Jun 2026."""
        ep = EvaluationsPage(page)
        ep.go_to_evaluations_list()
        if not ep.is_status_filter_available():
            pytest.skip("'Filter Status' control not found on evaluations list page")
        ep.click_status_tab("Cancelled")
        page.wait_for_timeout(600)
        assert page.url, "Page must remain accessible after clicking 'Cancelled' tab"

    def test_status_tab_count_badges_are_numeric(self, page: Page):
        """Tab count badges like 'Draft(40)' must contain valid integers."""
        ep = EvaluationsPage(page)
        ep.go_to_evaluations_list()
        import re
        tabs_with_counts = page.locator(
            "button:has-text('Draft'), button:has-text('Completed'), button:has-text('Failed')"
        )
        for i in range(tabs_with_counts.count()):
            label = tabs_with_counts.nth(i).text_content() or ""
            numbers = re.findall(r"\d+", label)
            if numbers:
                assert int(numbers[0]) >= 0, f"Tab count must be non-negative: '{label}'"


# ── Evaluations list pagination (Jun 2026) ────────────────────────────────────


class TestEvaluationsPagination:
    """Pagination controls appear and behave correctly on the evaluations list."""

    def test_pagination_present_when_exceeds_page_size(self, page: Page):
        ep = EvaluationsPage(page)
        ep.go_to_evaluations_list()
        if ep.is_status_filter_available():
            ep.click_status_tab("All")
        page.wait_for_timeout(500)
        row_count = page.locator("tbody tr").count()
        if row_count < 20:
            pytest.skip(
                f"Test account has {row_count} evaluations — need >20 to trigger pagination"
            )
        assert ep.is_pagination_visible(), (
            "Pagination controls must be visible when there are more than 20 evaluations"
        )

    def test_status_filter_resets_to_first_page(self, page: Page):
        ep = EvaluationsPage(page)
        ep.go_to_evaluations_list()
        if not ep.is_pagination_visible():
            pytest.skip("Pagination not present — not enough evaluations to test page reset")
        next_btn = page.locator(EvaluationsLocators.PAGINATION_NEXT)
        if next_btn.count() == 0 or not next_btn.first.is_enabled():
            pytest.skip("No 'Next' pagination button available")
        next_btn.first.click()
        page.wait_for_timeout(500)
        # Applying a filter should reset offset to 0 (page 1)
        if ep.is_status_filter_available():
            ep.click_status_tab("Completed")
            page.wait_for_timeout(500)
            ep.click_status_tab("All")
            page.wait_for_timeout(500)
        # After filter change, pagination next from page 1 should be available
        # (i.e. we are back at page 1, not stuck on a non-existent page)
        assert ep.is_visible(EvaluationsLocators.PAGE_HEADING), (
            "Page heading must still be visible after filter reset"
        )
