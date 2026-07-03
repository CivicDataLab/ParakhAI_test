"""
E2E coverage for the redesigned evaluation detail page (Jul 2026 frontend
restructure — "Bulletproof React" refactor, single-page layout).

Verified live on dev 03 Jul 2026 (eval 1598):
- Header: editable input[name='evaluationName'], status badge, mode badge,
  Back to List, Download Report.
- Cards: Evaluation Overview ("Label : value" lines), Evaluator's
  Recommendations, Evaluation Summary (TOTAL PASS RATE / TOTAL TEST CASES /
  PASSED / FAILED / SKIPPED), Total Issues Identified (LOW/MEDIUM/HIGH RISK).
- Evaluation Results: flat "Input N" blocks with an audit-results-sort select
  (No. of Issues - High to Low / Low to High). No tabs anywhere.

All tests are read-only against a discovered COMPLETED evaluation.
"""

import re

import pytest

from pages.evaluation_detail_page import EvaluationDetailPage

pytestmark = [pytest.mark.e2e, pytest.mark.regression, pytest.mark.auth]


@pytest.fixture()
def detail_page(authenticated_page_fast, completed_eval_id) -> EvaluationDetailPage:
    ep = EvaluationDetailPage(authenticated_page_fast)
    # go_to_evaluation_detail waits for hydration (positive-condition poll).
    ep.go_to_evaluation_detail(completed_eval_id)
    return ep


class TestDetailHeaderSmoke:
    """Header chrome of the redesigned page."""

    @pytest.mark.smoke
    def test_header_renders_name_input_and_back_button(self, detail_page):
        assert detail_page.is_name_input_visible(), (
            "input[name='evaluationName'] must render in the detail header"
        )
        assert detail_page.is_visible(detail_page.BACK_TO_LIST), (
            "'Back to List' must render in the detail header"
        )

    @pytest.mark.smoke
    def test_name_input_is_prefilled(self, detail_page):
        assert detail_page.get_eval_name().strip(), (
            "Evaluation name input must be prefilled with the evaluation's name"
        )

    def test_completed_badge_visible(self, detail_page, authenticated_page_fast):
        assert authenticated_page_fast.locator("text=COMPLETED").count() > 0, (
            "COMPLETED status badge must render for a completed evaluation"
        )


class TestDetailOverviewCard:
    """'Evaluation Overview' card fields ('Label : value' lines)."""

    @pytest.mark.smoke
    def test_overview_card_visible(self, detail_page):
        assert detail_page.is_overview_section_visible()

    def test_eval_id_matches_url(self, detail_page, completed_eval_id):
        val = detail_page.get_overview_field("Eval ID")
        assert val == str(completed_eval_id), (
            f"Overview 'Eval ID' should be {completed_eval_id}, got {val!r}"
        )

    def test_mode_field_is_valid(self, detail_page):
        mode = detail_page.get_overview_field("Mode")
        assert mode in ("Bulk Evaluation", "Playground Evaluation"), (
            f"Overview 'Mode' must be a known evaluation mode, got {mode!r}"
        )

    def test_created_on_field_present(self, detail_page):
        created = detail_page.get_overview_field("Created on")
        assert created, "Overview must show a 'Created on' timestamp"

    def test_evaluator_and_objective_present(self, detail_page):
        assert detail_page.get_overview_field("Evaluator"), (
            "Overview must show the Evaluator type"
        )
        assert detail_page.get_overview_field("Objective"), (
            "Overview must show the Objective"
        )


class TestDetailSummaryConsistency:
    """Numeric integrity of the Evaluation Summary + risk counters."""

    @staticmethod
    def _num(text: str) -> int | None:
        m = re.search(r"\d+", text or "")
        return int(m.group()) if m else None

    def test_summary_counts_add_up(self, detail_page):
        total = self._num(detail_page.get_summary_stat("TOTAL TEST CASES"))
        passed = self._num(detail_page.get_summary_stat("PASSED TESTS"))
        failed = self._num(detail_page.get_summary_stat("FAILED TESTS"))
        skipped = self._num(detail_page.get_summary_stat("SKIPPED TESTS"))
        if None in (total, passed, failed, skipped):
            pytest.skip(
                f"Summary cards not all numeric (total={total}, passed={passed}, "
                f"failed={failed}, skipped={skipped}) — layout may differ for this eval"
            )
        assert passed + failed + skipped == total, (
            f"PASSED({passed}) + FAILED({failed}) + SKIPPED({skipped}) != TOTAL({total})"
        )

    def test_pass_rate_matches_counts(self, detail_page):
        rate_text = detail_page.get_summary_stat("TOTAL PASS RATE")
        total = self._num(detail_page.get_summary_stat("TOTAL TEST CASES"))
        passed = self._num(detail_page.get_summary_stat("PASSED TESTS"))
        m = re.search(r"([\d.]+)\s*%", rate_text or "")
        if not m or not total:
            pytest.skip(f"Pass rate not parseable (rate={rate_text!r}, total={total})")
        shown = float(m.group(1))
        expected = passed / total * 100
        assert abs(shown - expected) < 1.0, (
            f"Pass rate card shows {shown}% but {passed}/{total} = {expected:.2f}%"
        )

    def test_risk_counters_are_nonnegative_ints(self, detail_page):
        for label in ("LOW RISK", "MEDIUM RISK", "HIGH RISK"):
            val = self._num(detail_page.get_summary_stat(label))
            if val is None:
                pytest.skip(f"Risk counter {label!r} not found — layout variant")
            assert val >= 0


class TestDetailResultsSection:
    """The flat 'Evaluation Results' list with its sort control."""

    @pytest.mark.smoke
    def test_results_section_visible(self, detail_page):
        assert detail_page.is_results_section_visible(), (
            "'Evaluation Results' section must render on a completed evaluation"
        )

    def test_result_input_blocks_render(self, detail_page):
        count = detail_page.get_result_input_block_count()
        assert count > 0, (
            "At least one 'Input N' result block must render for a completed "
            "evaluation with test cases"
        )

    def test_sort_select_has_both_orders(self, detail_page):
        options = detail_page.get_results_sort_options()
        if not options:
            pytest.skip("audit-results-sort select not rendered as <select>")
        joined = " | ".join(options)
        assert "High to Low" in joined and "Low to High" in joined, (
            f"Sort select must offer both orders, got: {options}"
        )

    def test_switching_sort_order_does_not_break_results(self, detail_page):
        before = detail_page.get_result_input_block_count()
        if not detail_page.select_results_sort("No. of Issues - Low to High"):
            pytest.skip("audit-results-sort select not rendered as <select>")
        after = detail_page.get_result_input_block_count()
        assert after == before, (
            f"Result count changed after re-sorting: {before} -> {after}"
        )


class TestDetailNavigation:
    def test_back_to_list_returns_to_evaluations(
        self, authenticated_page_fast, completed_eval_id
    ):
        """'Back to List' is history-based (router.back) — it no-ops on a
        deep-linked detail page with no history, so build history first
        (list → detail → back). The deep-link no-op is noted as a UX quirk."""
        from utils.config import Config

        ep = EvaluationDetailPage(authenticated_page_fast)
        authenticated_page_fast.goto(
            Config.url("/dashboard/ai-maker/1/evaluations"),
            wait_until="domcontentloaded",
        )
        ep.go_to_evaluation_detail(completed_eval_id)
        ep.click_back_to_list()
        authenticated_page_fast.wait_for_timeout(3_000)
        assert f"/evaluations/{completed_eval_id}" not in authenticated_page_fast.url, (
            "Back to List did not leave the detail page (history was present)"
        )
