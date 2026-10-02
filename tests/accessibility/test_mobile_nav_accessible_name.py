"""
Pending coverage for CivicDataLab/ParakhAI-frontend#442
("fix: add branded 404 page and fix mobile menu accessible name").

Only the mobile-menu accessible-name half of #442 is covered here.

The other half — the branded `app/not-found.tsx` page — is not covered by
any test in this PR, pending or otherwise: the app's `middleware.ts` treats
`'/'` as the *only* public page (`publicPages = ['/']`), so a request to any
other path, including one that matches no route at all, 307s to
`/api/auth/signin` before Next.js's router ever gets to resolve
`not-found.tsx`. Verified directly against both dev and a local build of the
PR head (`curl` to a nonexistent path returns `307` to the sign-in page,
never the 404 content). An anonymous test can't reach that page no matter
how it's written; it needs an authenticated session. See the PR body.

What's covered:
opub-ui's `Sheet.Content` (used by the mobile hamburger menu's `Sidebar`)
only renders Radix's `DialogTitle` when a `title` prop is passed. Before
#442, `Sidebar.tsx` passed none, so the dialog's auto-generated
`aria-labelledby` pointed at an id that was never in the DOM — the open
mobile menu had no accessible name (axe-core: "aria-dialog-name", impact
"serious"). #442 passes `title="Navigation menu"`, so the (visually-hidden)
`DialogTitle` renders and `aria-labelledby` resolves.

Gated on `pending_pr("ParakhAI-frontend#442")` — skips in CI until GitHub
reports #442 merged (see root `conftest.py`'s `_pending_pr_state`).
"""

import pytest
from playwright.sync_api import Page

from pages.home_page import HomePage

pytestmark = [
    pytest.mark.accessibility,
    pytest.mark.mobile,
    pytest.mark.pending_pr("ParakhAI-frontend#442"),
]

_axe_available = False
try:
    from axe_playwright_python.sync_playwright import Axe

    _axe_available = True
except ImportError:
    pass


def _require_axe():
    if not _axe_available:
        pytest.skip("axe-playwright-python not installed — run: pip install axe-playwright-python")


class TestMobileNavAccessibleName:
    def test_mobile_nav_dialog_has_accessible_name(self, mobile_page: Page):
        _require_axe()
        home = HomePage(mobile_page)
        home.go_to_home()
        home.click_hamburger()
        mobile_page.wait_for_timeout(500)

        dialog = mobile_page.locator("[role='dialog']")
        assert dialog.count() > 0, "Mobile menu did not render a role=dialog element"

        labelledby = dialog.first.get_attribute("aria-labelledby")
        assert labelledby, (
            "Dialog has no aria-labelledby at all — the #442 DialogTitle fix "
            "regressed (or never applied)."
        )

        label_text = mobile_page.evaluate(
            "(id) => { const el = document.getElementById(id); return el ? el.textContent : null; }",
            labelledby,
        )
        assert label_text == "Navigation menu", (
            f"aria-labelledby target's text was {label_text!r}, expected "
            "'Navigation menu' — either the id resolves to nothing (the "
            "pre-#442 bug: Sheet.Content rendered no DialogTitle at all) or "
            "the DialogTitle text has changed."
        )

        axe = Axe()
        results = axe.run(mobile_page).response
        violation_ids = [v["id"] for v in results.get("violations", [])]
        assert "aria-dialog-name" not in violation_ids, (
            f"axe still flags aria-dialog-name on the open mobile menu: {violation_ids}"
        )
