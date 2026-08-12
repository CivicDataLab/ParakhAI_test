"""
Responsive visual regression for authenticated routes (mobile + tablet).

Why this file exists
--------------------
The homepage is covered at three viewports, but every one of the twelve
authenticated routes in `test_visual_regression.py` is captured **only** at
desktop 1440x900. The entire logged-in application therefore has zero
responsive visual coverage — sidebar collapse, stat-card reflow, card-grid
wrapping and data-table overflow are all untested, and those are precisely
where responsive regressions live.

Route selection (the main design decision)
------------------------------------------
Deliberately NOT the full 12 routes x 2 viewports = 24 tests. That would add
~24 baselines captured against an environment currently failing a majority of
authenticated captures (bug #15), and roughly double visual-suite runtime, for
very low marginal value. Four routes were chosen for genuinely distinct
reflow behaviour:

* ``dashboard_role_selector`` — two side-by-side cards that must stack. The
  simplest, most structurally stable authenticated page (static chrome, no
  live data), so it is the one route here kept as a hard pixel assertion.
* ``ai_maker_dashboard``     — the richest reflow surface: a 4-up stat-card
  grid plus a 3-column model-card grid, both of which must collapse.
* ``evaluations_list``       — a real data table. Horizontal overflow of a
  table is the single most common responsive defect, which is also why the
  overflow check below targets these same routes.
* ``models_list``            — 3-column card grid to single column.

Explicitly excluded, with reasons:

* ``org_selector`` — `tasks/lessons.md` records a persistent ~0.5% residual
  diff on this page from a lazy-loaded placeholder widget that appears
  depending on mouse position. It is already over the 0.1% threshold at
  desktop; adding two more known-flaky baselines is negative value.
* ``new_evaluation_wizard`` — a ~35s asynchronous model dropdown makes it the
  most timing-fragile page in the suite.
* the auditor routes — ``/dashboard/auditor/assignments`` is confirmed hanging
  past 45s (app_bugs.md #24) and ``auditor_dashboard`` is currently the route
  the capture-integrity gate refuses outright.
* ``evaluation_detail_completed`` — depends on the `completed_eval_id`
  fixture, whose seeding fallback is currently intermittent.

Capture integrity
-----------------
Every capture goes through `utils.visual_guards`. Eight of twelve desktop
baselines previously encoded a 404, a stuck "Loading ..." curtain, or the
logged-out marketing homepage, because captures settled a flat 2.5s while dev
curtains run 15-30s+. New baselines here must not repeat that, so the same
`wait_for_render_settled` + `capture_integrity_problem` pair gates every save
and every compare, and `AUTH_PII_MASKS` keeps the test account's name and
initials out of the images.

Expect skips while bug #15 is active — a skip means the page never rendered,
so there was no pixel question to answer. That is the correct outcome, not
something to retry around.
"""

import pytest

# Helpers are imported from the desktop module rather than copied: duplicating
# the pixel-diff / threshold / baseline-save logic would create a second copy
# that silently drifts from the original (different threshold handling, a
# missed fix). The names are private by convention only — this is a sibling
# module inside the same `tests.visual` package.
from tests.visual.test_visual_regression import (
    _THRESHOLD,
    _authenticated_page_at_viewport,
    _capture_page_masked,
    _compare_or_save_baseline,
)
from utils.config import Config
from utils.visual_guards import (
    AUTH_PII_MASKS,
    DEFAULT_MASKS,
    capture_integrity_problem,
    wait_for_render_settled,
)

pytestmark = [
    pytest.mark.visual,
    pytest.mark.auth,
    # Each capture budgets up to 45s waiting out the auth/data curtains, plus
    # navigation and settle time. The global pytest timeout is 120s, which is
    # uncomfortably close; test_new_evaluation_smoke.py raises it for the same
    # reason.
    pytest.mark.timeout(180),
]


# (path, snapshot name) — see the module docstring for why these four.
RESPONSIVE_ROUTES = [
    ("/dashboard", "dashboard_role_selector"),
    ("/dashboard/ai-maker/1", "ai_maker_dashboard"),
    ("/dashboard/ai-maker/1/evaluations", "evaluations_list"),
    ("/dashboard/ai-maker/1/ai-models", "models_list"),
]

# (label, width, height) — matches VIEWPORTS in the desktop module.
RESPONSIVE_VIEWPORTS = [
    ("mobile", 390, 844),
    ("tablet", 768, 1024),
]

# Routes whose content is live data and therefore not stably pixel-diffable; a
# diff becomes an xfail rather than a hard failure, mirroring VISUAL-002 in the
# desktop suite.
#
# Note this diverges from the desktop module, which treats `ai_maker_dashboard`
# as a hard assertion. That page now renders a live "Recent Evaluations" table
# and live stat counters; `DEFAULT_MASKS` covers timestamps but not evaluation
# names or counts, and the suite's own `regression_write` tests create
# evaluations. Treating it as deterministic would produce exactly the flaky red
# that erodes trust in a visual suite. Flagged rather than silently differing.
_NON_DETERMINISTIC_RESPONSIVE = {
    "ai_maker_dashboard",
    "evaluations_list",
    "models_list",
}

# Allowance for sub-pixel layout rounding when comparing scrollWidth against
# innerWidth. Deliberately tiny: a real horizontal-overflow bug overshoots by
# tens or hundreds of pixels, never by one.
_OVERFLOW_TOLERANCE_PX = 2


def _capture_responsive(page, path: str):
    """Capture `path`, skipping when the render can't be trusted.

    Returns the PIL image. Skips (never fails) on an untrustworthy capture, for
    the reasons in utils/visual_guards: an invalid capture means the "did the
    pixels change?" question was never asked.
    """
    try:
        img = _capture_page_masked(
            page, Config.url(path), DEFAULT_MASKS + AUTH_PII_MASKS
        )
    except Exception as exc:  # noqa: BLE001 — mirrors the desktop suite's handling
        pytest.skip(
            f"Could not capture {path}: {exc}. "
            "Page may be unreachable for this account."
        )

    problem = capture_integrity_problem(page, img, expect_auth_route=True)
    if problem:
        pytest.skip(f"Capture integrity check failed for {path}: {problem}")
    return img


class TestResponsiveAuthenticatedVisuals:
    """Mobile (390x844) and tablet (768x1024) baselines for four auth routes.

    Snapshot names follow the existing convention
    (`auth_<name>_<viewport>_<w>x<h>`) so they sort next to their desktop
    counterparts in `snapshots/`.
    """

    @pytest.mark.parametrize(
        "viewport,width,height",
        RESPONSIVE_VIEWPORTS,
        ids=[v[0] for v in RESPONSIVE_VIEWPORTS],
    )
    @pytest.mark.parametrize(
        "path,name", RESPONSIVE_ROUTES, ids=[r[1] for r in RESPONSIVE_ROUTES]
    )
    def test_authenticated_page_responsive(
        self, browser, authenticated_storage_state, path, name, viewport, width, height
    ):
        page = _authenticated_page_at_viewport(
            browser, authenticated_storage_state, width, height
        )
        try:
            img = _capture_responsive(page, path)
            snapshot = f"auth_{name}_{viewport}_{width}x{height}"

            if name in _NON_DETERMINISTIC_RESPONSIVE:
                try:
                    _compare_or_save_baseline(img, snapshot)
                except AssertionError as exc:
                    pytest.xfail(
                        f"VISUAL-002: {name} renders live data (stat counters, "
                        f"evaluation/model lists) and is not stably pixel-diffable "
                        f"at {_THRESHOLD}%. {exc}"
                    )
            else:
                _compare_or_save_baseline(img, snapshot)
        finally:
            page.context.close()


class TestMobileLayoutIntegrity:
    """Horizontal-overflow assertions at mobile width.

    Deliberately NOT a pixel diff. A page wider than its viewport forces the
    user to scroll sideways to read content — the most common real responsive
    defect — and it is detectable deterministically from layout metrics. That
    makes this check immune to the live-data noise that forces the baselines
    above into xfail territory, so it keeps working as a hard assertion even on
    pages whose pixels can't be trusted.

    A table that scrolls inside its own container is fine and correct; only
    overflow of the document itself is a bug, which is what `documentElement`
    measures.
    """

    @pytest.mark.mobile
    @pytest.mark.parametrize(
        "path,name", RESPONSIVE_ROUTES, ids=[r[1] for r in RESPONSIVE_ROUTES]
    )
    def test_no_horizontal_overflow_at_mobile(
        self, browser, authenticated_storage_state, path, name
    ):
        page = _authenticated_page_at_viewport(
            browser, authenticated_storage_state, 390, 844
        )
        try:
            page.goto(Config.url(path), wait_until="load", timeout=30_000)
            wait_for_render_settled(page)
            page.wait_for_timeout(1_500)

            # Same integrity gate as the pixel tests — asserting layout metrics
            # on the logged-out homepage would be a meaningless green.
            import io

            from PIL import Image

            img = Image.open(io.BytesIO(page.screenshot()))
            problem = capture_integrity_problem(page, img, expect_auth_route=True)
            if problem:
                pytest.skip(f"Capture integrity check failed for {path}: {problem}")

            metrics = page.evaluate(
                """() => ({
                    scrollWidth: document.documentElement.scrollWidth,
                    innerWidth: window.innerWidth,
                })"""
            )
            overflow = metrics["scrollWidth"] - metrics["innerWidth"]
            assert overflow <= _OVERFLOW_TOLERANCE_PX, (
                f"{name} overflows horizontally at 390px: document scrollWidth "
                f"{metrics['scrollWidth']}px vs viewport {metrics['innerWidth']}px "
                f"({overflow}px too wide). The user has to scroll sideways to read "
                f"the page. A wide table should scroll inside its own container "
                f"rather than widening the document."
            )
        finally:
            page.context.close()
