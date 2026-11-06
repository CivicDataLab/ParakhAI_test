"""
Pending coverage for CivicDataLab/ParakhAI-frontend#441
("fix: sort AI model and evaluation domain dropdowns alphabetically").

Open `dev` PR, no coverage yet (test-sync §9 sweep, 2026-10-08). Gated with
`pending_pr` — skipped in CI until GitHub reports #441 merged.

PR #441 head: acbf053512e5a2bfa7a87136d2105f74eb5e95c9 (as of 2026-10-08).
If review drags on, re-check the head hasn't moved before this merges.

What changed: the "Select AI Model" dropdown (New Evaluation modal, step 1)
and the "Evaluation Domain" dropdown (step 2) used to render options in
whatever order the API returned them. #441 sorts both by visible label with
`localeCompare`.

UNVERIFIED — not executed, no credentials in this cloud sandbox. Both
dropdowns live behind the AI Maker dashboard (Keycloak login via
`authenticated_page`), which this environment cannot reach. A human with
TEST_EMAIL_1/TEST_PASSWORD_1 must run this locally to get the real
red/green proof:

    pytest tests/e2e/test_new_evaluation_dropdown_sort.py -v --tb=short

Red/green proof to perform, since #441 isn't on dev yet:
  1. Run against dev now -> expect FAIL (old code serves API order, which
     is not guaranteed alphabetical -- fails whenever the live model/domain
     list isn't already sorted; see the note on test_model_dropdown's skip
     condition below for the one case this can't show anything).
  2. `gh pr checkout 441` (frontend repo) and serve locally against the dev
     API per SKILL.md section 6's local-serve recipe, point HOME_URL_DEV at
     the local port -> expect PASS.
  3. Restore pointing at dev, confirm the test is correctly gated
     (`pending_pr ParakhAI-frontend#441: not merged yet` skip reason).
"""

import pytest
from playwright.sync_api import Page

from pages.new_evaluation_page import NewEvaluationPage

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.auth,
    pytest.mark.pending_pr("ParakhAI-frontend#441"),
    pytest.mark.timeout(180),
]


class TestDropdownsSortedAlphabetically:
    """Both dropdowns must render options sorted by visible label, not API order."""

    def test_model_dropdown_options_sorted_alphabetically(self, authenticated_page: Page):
        """
        'Select an AI Model' options (modal step 1) must be in ascending,
        case-insensitive alphabetical order by label.

        This only has teeth when the live model list has 2+ distinct labels
        whose case-sensitive ('<') and case-insensitive order differ, or
        whose API order isn't already alphabetical -- otherwise an
        unsorted-but-coincidentally-alphabetical API response would pass
        either way. Skip rather than pass vacuously when there's too little
        data to distinguish the two.
        """
        nep = NewEvaluationPage(authenticated_page)
        nep.go_to_evaluations_list()
        nep.click_new_evaluation()

        if not nep.is_modal_visible():
            pytest.skip("New Evaluation modal did not open — cannot reach the dropdown")

        options = nep.get_modal_model_options()
        labels = [text for (_value, text) in options if text.strip()]

        if len(labels) < 2:
            nep.click_modal_cancel()
            pytest.skip(
                f"Only {len(labels)} model option(s) on dev — not enough data to "
                "distinguish sorted from unsorted"
            )

        expected = sorted(labels, key=lambda s: (s.casefold(), s))
        nep.click_modal_cancel()

        assert labels == expected, (
            "'Select an AI Model' options are not sorted alphabetically by "
            f"label: got {labels!r}, expected {expected!r} (PR #441)"
        )

    def test_evaluation_domain_dropdown_options_sorted_alphabetically(
        self, authenticated_page: Page
    ):
        """
        'Evaluation Domain' options (modal step 2) must be sorted the same
        way. The dropdown only renders for models that have a domain with
        non-empty backend audit-domain options -- try a few models before
        concluding none qualify, rather than skipping on the first miss.
        """
        nep = NewEvaluationPage(authenticated_page)
        nep.go_to_evaluations_list()
        nep.click_new_evaluation()

        if not nep.is_modal_visible():
            pytest.skip("New Evaluation modal did not open — cannot reach the dropdown")

        options = nep.get_modal_model_options()
        valid_indices = [
            i
            for i, (_value, text) in enumerate(options)
            if text.strip() and text.strip() not in nep.EXCLUDED_MODEL_NAMES
        ]
        if not valid_indices:
            nep.click_modal_cancel()
            pytest.skip("No usable model options on dev — cannot select a model")

        domain_labels: list[str] | None = None
        for idx in valid_indices[:5]:
            nep.select_model_by_index(idx)
            nep.click_modal_next()
            if nep.is_modal_evaluation_domain_dropdown_visible():
                domain_labels = nep.get_modal_evaluation_domain_options()
                break
            nep.click_modal_back()

        if domain_labels is None:
            nep.click_modal_cancel()
            pytest.skip(
                "No model among the first candidates renders an 'Evaluation "
                "Domain' dropdown on dev — cannot exercise PR #441's domain-sort change"
            )

        if len(domain_labels) < 2:
            nep.click_modal_cancel()
            pytest.skip(
                f"Only {len(domain_labels)} domain option(s) on dev — not enough "
                "data to distinguish sorted from unsorted"
            )

        expected = sorted(domain_labels, key=lambda s: (s.casefold(), s))
        nep.click_modal_cancel()

        assert domain_labels == expected, (
            "'Evaluation Domain' options are not sorted alphabetically by "
            f"label: got {domain_labels!r}, expected {expected!r} (PR #441)"
        )
