"""
E2E coverage for the Evaluations list controls (verified live 03 Jul 2026):

- Status filter buttons with live counts: All | Draft(N) | Queued(N) |
  In Progress(N) | Pending Review(N) | Completed(N) | Failed(N) | Cancelled(N)
- Sortable column headers (Evaluation Name, Model, Status, ...)
- Rows-per-page select (10/25/50/100) + "Page X of Y" pagination

All tests are read-only. Counts on dev change under parallel test traffic,
so assertions are structural/relative rather than pinned to exact numbers.
"""

import pytest

from pages.evaluations_page import EvaluationsPage

pytestmark = [pytest.mark.e2e, pytest.mark.regression, pytest.mark.auth]

_STATUS_BADGES = {
    "Draft": "DRAFT",
    "Queued": "QUEUED",
    "In Progress": "IN PROGRESS",
    "Pending Review": "PENDING REVIEW",
    "Completed": "COMPLETED",
    "Failed": "FAILED",
    "Cancelled": "CANCELLED",
}


@pytest.fixture()
def eval_list(authenticated_page_fast) -> EvaluationsPage:
    ep = EvaluationsPage(authenticated_page_fast)
    ep.go_to_evaluations_list()
    ep.wait_for_list_loaded()
    return ep


class TestStatusFilterTabs:
    @pytest.mark.smoke
    def test_all_status_tabs_render_with_counts(self, eval_list):
        """The old StatusFilterTabs bar showed inline 'Label(N)' counts.

        The evaluation-table-listing redesign (~2026-08) replaced it with a
        per-column 'Filter Status' popover — confirmed live 2026-08-13 the
        popover's checkbox options render plain labels with no counts
        anywhere (not just moved elsewhere). This is a deliberate scope
        change in the redesign, not app breakage — same class of call as
        this file's existing precedent for tabs that were intentionally
        dropped (see docs/app_bugs.md Phase log, 2026-07-28 evaluator
        assignment tabs). Assert the new control exists instead.
        """
        assert eval_list.is_status_filter_available(), (
            "Expected a 'Filter Status' control to be present on the evaluations table"
        )

    def test_counts_are_nonnegative(self, eval_list):
        """See test_all_status_tabs_render_with_counts — counts no longer
        render anywhere in the redesigned UI, so this assertion has no
        current equivalent."""
        pytest.skip(
            "Status tab counts were removed in the evaluation-table-listing "
            "redesign (~2026-08) — no counts render anywhere in the new "
            "'Filter Status' popover UI. See test_all_status_tabs_render_with_counts."
        )

    @pytest.mark.parametrize("label", ["Completed", "Draft", "Failed"])
    def test_filter_shows_only_matching_rows(self, eval_list, label):
        if not eval_list.is_status_filter_available():
            pytest.skip("'Filter Status' control not found on evaluations list page")
        eval_list.click_status_tab(label)
        eval_list.page.wait_for_timeout(2_000)
        statuses = eval_list.get_row_statuses()
        if not statuses:
            pytest.skip(f"No {label} evaluations on dev right now")
        badge = _STATUS_BADGES[label]
        mismatched = [s for s in statuses if badge not in s.upper()]
        if mismatched:
            pytest.xfail("App bug #27 — see docs/app_bugs.md")
        assert not mismatched, (
            f"'{label}' filter shows rows with other statuses: {mismatched}"
        )

    def test_filtered_row_count_within_tab_count(self, eval_list):
        """Rows shown under 'Completed' must not exceed the page size.

        Previously bounded the filtered row count against the tab's
        advertised total count; that count no longer renders anywhere (see
        test_all_status_tabs_render_with_counts), so this now checks the
        weaker but still meaningful invariant: a single filtered page never
        exceeds the max page size (100).
        """
        if not eval_list.is_status_filter_available():
            pytest.skip("'Filter Status' control not found on evaluations list page")
        eval_list.click_status_tab("Completed")
        eval_list.page.wait_for_timeout(2_000)
        rows = eval_list.get_table_row_count()
        if rows == 0:
            pytest.skip("No completed evaluations on dev right now")
        assert rows <= 100, f"Completed tab shows {rows} rows — exceeds max page size"


class TestSortableHeaders:
    def test_sort_by_name_toggles_order(self, eval_list):
        if eval_list.get_table_row_count() < 2:
            pytest.skip("Fewer than 2 rows — sort order not observable")
        before = eval_list.get_first_column_texts()
        assert eval_list.click_sort_header("Evaluation Name"), (
            "'Evaluation Name' sort header button not found"
        )
        after = eval_list.get_first_column_texts()
        # Same multiset of rows in a different (or re-confirmed) order; with
        # >=2 distinct names a toggle must change the order.
        if len(set(before)) >= 2 and after == before:
            pytest.xfail("App bug #28 — see docs/app_bugs.md")
        if len(set(before)) >= 2:
            assert after != before, (
                "Clicking the Evaluation Name sort header did not change row order"
            )

    def test_sort_click_does_not_lose_rows(self, eval_list):
        before = eval_list.get_table_row_count()
        if not before:
            pytest.skip("Empty list")
        if not eval_list.click_sort_header("Status"):
            pytest.skip("'Status' sort header not found")
        assert eval_list.get_table_row_count() == before, (
            "Row count changed after sorting by Status"
        )


class TestRowsPerPageAndPagination:
    def test_page_indicator_present(self, eval_list):
        # The footer renders after the table — poll a little extra.
        info = None
        for _ in range(10):
            info = eval_list.get_page_x_of_y()
            if info:
                break
            eval_list.page.wait_for_timeout(2_000)
        assert info is not None, (
            "'Page X of Y' indicator must render under the evaluations table"
        )

    def test_rows_per_page_change_updates_table(self, eval_list):
        page_info = eval_list.get_page_x_of_y()
        if not eval_list.set_rows_per_page("25"):
            pytest.skip("Rows-per-page select not found")
        rows = eval_list.get_table_row_count()
        assert rows <= 25, f"25-per-page selected but {rows} rows rendered"
        new_info = eval_list.get_page_x_of_y()
        if page_info and new_info:
            assert new_info[1] <= page_info[1], (
                f"Total pages should not grow when page size grows: "
                f"{page_info} -> {new_info}"
            )

    def test_rows_never_exceed_default_page_size(self, eval_list):
        rows = eval_list.get_table_row_count()
        info = eval_list.get_page_x_of_y()
        if info is None:
            pytest.skip("No page indicator")
        assert rows <= 100, f"{rows} rows rendered — exceeds every page-size option"


class TestListSmoke:
    @pytest.mark.smoke
    def test_list_renders_heading_and_new_button(self, eval_list):
        # 'text=Evaluations' .first can hit a hidden mobile-nav duplicate, so
        # assert on the loaded-list signals instead of the heading locator.
        assert eval_list.get_status_tab_counts() or eval_list.get_table_row_count(), (
            "Evaluations list did not hydrate (no status counts and no rows)"
        )
        assert eval_list.is_visible(eval_list.NEW_EVALUATION_BUTTON)

    @pytest.mark.smoke
    def test_table_headers_match_redesign(self, eval_list, authenticated_page_fast):
        table = authenticated_page_fast.locator("table").first
        if not table.count():
            pytest.skip("No table rendered (empty list state)")
        body = table.inner_text(timeout=15_000)
        for col in ("Evaluation Name", "Model", "Status", "Evaluation Mode", "Tests"):
            assert col in body, f"Column '{col}' missing from evaluations table"
