"""
Pending coverage for CivicDataLab/ParakhAI-frontend#443
("fix(a11y): label evaluator select and notes textarea in invitation dialog").

Open `dev` PR, no coverage yet (test-sync §9 sweep, 2026-10-08). Gated with
`pending_pr` — skipped in CI until GitHub reports #443 merged.

PR #443 head: db9cc7e89c43f437c18e7e7b565a486ab60fd598 (as of 2026-10-08).
If review drags on, re-check the head hasn't moved before this merges.

What changed: in the "Invite Evaluator" dialog (AuditorInvitation.tsx,
opened from an AI model's version row via "Invite Evaluators"), the
"Select Evaluator" <select> and the "Notes (optional)" <textarea> each had
a <label> rendered visually above them but with no `htmlFor`/`id` link, so
screen readers announced both controls with no name. #443 adds the
`htmlFor`/`id` pair to both.

Proof approach: Playwright's `get_by_label()` resolves a control through
the real accessible-name algorithm (the same one assistive tech uses) --
it does NOT just look for nearby text. Before the fix, with no
`htmlFor`/`id`, `get_by_label("Select Evaluator")` and
`get_by_label("Notes (optional)")` resolve to zero elements even though
the label text is visibly right above the control. After the fix, each
resolves to exactly one element. That is a genuine behaviour assertion,
not a cosmetically-flipped expected value.

UNVERIFIED — not executed, no credentials in this cloud sandbox. The
invitation dialog is behind the AI Maker dashboard (Keycloak login via
`authenticated_page_fast`), which this environment cannot reach, and it also
requires a model that has at least one version with available evaluators
to invite -- a data precondition that also needs a real login to check.
A human with TEST_EMAIL_1/TEST_PASSWORD_1 must run this locally:

    pytest tests/accessibility/test_auditor_invitation_a11y.py -v --tb=short -rs

Red/green proof to perform, since #443 isn't on dev yet:
  1. Run against dev now -> expect FAIL: `get_by_label(...)` finds 0
     elements for both the evaluator select and the notes textarea (old
     markup has no htmlFor/id).
  2. `gh pr checkout 443` (frontend repo) and serve locally against the dev
     API per SKILL.md section 6's local-serve recipe (note: the local-serve
     stub-auth caveat means the header nav won't render, so reaching this
     page may need to go directly to the model detail URL rather than via
     nav click) -> expect PASS: both resolve to exactly one element.
  3. Restore pointing at dev, confirm the gate (`pending_pr
     ParakhAI-frontend#443: not merged yet` skip reason).
"""

import pytest
from playwright.sync_api import Page

from pages.models_page import ModelsPage

pytestmark = [
    pytest.mark.accessibility,
    pytest.mark.auth,
    pytest.mark.pending_pr("ParakhAI-frontend#443"),
    pytest.mark.timeout(120),
]


@pytest.fixture
def invite_dialog_page(authenticated_page_fast: Page) -> Page:
    """Navigate to a model detail page and open the 'Invite Evaluator' dialog.

    Skips (does not fail) when there's no model, no version, or no
    available evaluators to invite — those are dev-data gaps, not what
    this test is checking.
    """
    mp = ModelsPage(authenticated_page_fast)
    mp.go_to_model_detail()
    if not mp.is_invite_auditors_visible():
        pytest.skip("No 'Invite Evaluators' link visible on dev — no model version to test")
    if not mp.click_invite_auditors():
        pytest.skip("'Invite Evaluator' dialog did not open")
    return authenticated_page_fast


class TestInvitationDialogAccessibleLabels:
    """Select Evaluator and Notes must each resolve through their <label>."""

    def test_evaluator_select_has_accessible_label(self, invite_dialog_page: Page):
        if not invite_dialog_page.locator("select").first.is_visible():
            pytest.skip(
                "Evaluator <select> not rendered — likely 'no evaluators available' "
                "state (loading list, or none invitable) rather than #443's target markup"
            )
        matches = invite_dialog_page.get_by_label("Select Evaluator")
        assert matches.count() == 1, (
            "'Select Evaluator' must resolve to exactly one control via its "
            f"accessible label, found {matches.count()} (PR #443 adds the "
            "missing htmlFor/id pair)"
        )

    def test_notes_textarea_has_accessible_label(self, invite_dialog_page: Page):
        matches = invite_dialog_page.get_by_label("Notes (optional)")
        assert matches.count() == 1, (
            "'Notes (optional)' must resolve to exactly one control via its "
            f"accessible label, found {matches.count()} (PR #443 adds the "
            "missing htmlFor/id pair)"
        )
