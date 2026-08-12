"""Capture-integrity guards for visual regression tests.

Why this exists
---------------
`_compare_or_save_baseline` treats whatever is on screen as truth: if no
baseline exists it saves the capture verbatim. That is only safe if the capture
is actually the page we asked for — and against the shared dev environment it
frequently is not. Three documented failure modes all render a *plausible-looking*
page that is not the one under test:

* bug #13 / #14 — the route hangs on a "Loading …" curtain that never resolves.
* bug #15 — a deep-link to an auth route intermittently renders the **public
  marketing homepage** (~17-25% of loads) while the session is still valid.
* a wrong/stale route simply 404s (this is how `/evaluation/288` came to have a
  404 saved as the "completed evaluation detail" baseline).

A baseline captured during any of those bakes the defect in permanently, and the
resulting test is worse than no test: `auth_ai_maker_dashboard` had a stuck
"Loading overview..." saved as its baseline under a *hard* pixel-diff assertion,
so it passed only while the app stayed broken and would have gone red the day the
product was fixed.

skip vs fail
------------
These guards **skip** rather than fail, in both the save and the compare path.
The reasoning is deliberate:

A visual regression test answers exactly one question — "did the pixels change?"
— and it can only answer that from a valid capture. A 404, a stuck curtain or a
homepage fallback means the question was never asked, so the honest result is
*no signal*, which is a skip. Failing would assert a pixel regression that was
never observed; passing (today's behaviour) silently certifies a page nobody
looked at.

Skips are visible: pytest tallies them and `reports/TEST_REPORT.md` lists them
with the reason string, so a route that stops rendering surfaces as a growing
skip count rather than a green tick.

"But a stuck curtain IS a regression" — agreed, and it is already owned by
suites better suited to it: the e2e and accessibility suites assert on page
content and track these exact states as bugs #13/#14 with explicit xfails.
Detecting "the page failed to load" via a full-page pixel diff would duplicate
that concern with a far noisier signal.
"""

from __future__ import annotations

import re
import time

from PIL import Image
from playwright.sync_api import Page

# Next.js' built-in not-found page, plus the bare status line some routes emit.
_NOT_FOUND_MARKERS = (
    "this page could not be found",
    "404: this page could not be found",
)

# Loading curtains are matched with a trailing ellipsis rather than a bare
# "Loading" so legitimate copy (a column header, a tooltip) can't trip the
# guard. Covers both ASCII "..." and the unicode "…" the app uses in places.
# Real examples: "Loading overview...", "Loading evaluations…",
# "Loading AI models...", "Verifying your session...".
_CURTAIN_RE = re.compile(
    # "Loading overview...", "Loading your assignments...", "Loading evaluations…"
    r"(Loading[^\n]{0,40}?(\.\.\.|…))"
    # A bare, standalone "Loading" line — the org-selector spinner renders exactly
    # this with no ellipsis, and slipped past an ellipsis-only pattern into a
    # saved baseline. Anchored to a whole line so prose ("Downloading report",
    # "Reload the page") still can't trip it.
    r"|(^[ \t]*Loading[ \t]*$)"
    r"|(Verifying your session)",
    re.I | re.M,
)

# Copy that only exists on the public marketing homepage. If any of these show
# up while we are sitting on a /dashboard route, we caught bug #15's fallback.
_HOMEPAGE_ONLY_MARKERS = (
    "build ai that's trustworthy from day one",
    "automation-assisted evaluation environment",
    "expert-led evaluations",
    "sector-specific test cases",
)

# Logged-out chrome. A far more reliable tell than the hero copy: the marketing
# nav renders LOGIN/SIGN UP, which the authenticated shell never does. Four of
# the twelve auth baselines turned out to be pixel-identical to the logged-out
# homepage, so this is the single highest-value check in this module.
_LOGGED_OUT_MARKERS = (
    "sign up",
    "login",
    # An expired/absent session bounces the route to the NextAuth provider
    # picker, which renders only this string — confirmed live 2026-08-12.
    "sign in with keycloak",
)

# A capture this uniform is a blank/white screen, not a rendered page. Set
# deliberately high: several real pages (empty states, the role selector) are
# mostly flat background, and a false "blank" verdict would suppress a valid
# baseline. 99.8% single-colour is well past anything that renders content.
_UNIFORM_RATIO = 0.998


def _body_text(page: Page) -> str:
    """Visible body text, or "" if the page is in a state that can't yield it."""
    try:
        return page.locator("body").inner_text(timeout=5_000)
    except Exception:  # noqa: BLE001 — a page we can't read is handled by callers
        return ""


def _is_near_uniform(img: Image.Image) -> bool:
    """True when almost every pixel is the same shade — i.e. a blank capture."""
    histogram = img.convert("L").histogram()
    total = sum(histogram)
    if total == 0:
        return True
    return (max(histogram) / total) >= _UNIFORM_RATIO


def wait_for_render_settled(page: Page, timeout_ms: int = 45_000) -> None:
    """Block until no loading curtain is on screen (or the budget runs out).

    `_capture_page_masked` previously settled for 2.5s after `load`. Against dev
    that is far too short: lessons.md records the session curtain at ~15-20s on a
    cold deep-link and route data curtains at 30s+. Screenshotting at 2.5s
    therefore captured a curtain most of the time — which is the mechanism behind
    the poisoned baselines this module exists to prevent. The integrity gate
    alone would just convert that into a permanent skip; waiting properly is what
    lets a good baseline actually be produced.

    Returns on timeout rather than raising: the caller's integrity check is the
    thing that decides what a still-curtained page means.
    """
    deadline = time.monotonic() + (timeout_ms / 1000)
    while time.monotonic() < deadline:
        text = _body_text(page)
        # An empty body means the SPA hasn't mounted yet, not that it's settled
        # — returning here would reintroduce the mid-curtain capture this
        # function exists to prevent.
        if text.strip() and not _CURTAIN_RE.search(text):
            return
        page.wait_for_timeout(1_000)


def capture_integrity_problem(
    page: Page,
    img: Image.Image,
    *,
    expect_auth_route: bool = False,
) -> str | None:
    """Return a reason string when a capture must not be trusted, else None.

    `expect_auth_route` enables the homepage-fallback check, which is only
    meaningful for auth-walled routes — the homepage tests legitimately capture
    that exact content.
    """
    text = _body_text(page)
    lowered = text.lower()

    for marker in _NOT_FOUND_MARKERS:
        if marker in lowered:
            return (
                f"page rendered a 404 ('{marker}') — the route is wrong or the "
                "resource no longer exists, so this capture is not the page "
                "under test"
            )

    curtain = _CURTAIN_RE.search(text)
    if curtain:
        return (
            f"page still showing a loading curtain ({curtain.group(0).strip()!r}) "
            "— see app_bugs.md #13/#14; capturing now would bake the stuck "
            f"state into the baseline. Body began: {text[:120]!r}"
        )

    if expect_auth_route:
        for marker in _LOGGED_OUT_MARKERS:
            if marker in lowered:
                return (
                    f"auth route is rendering logged-out chrome (matched {marker!r}) "
                    "— the session did not apply, or app_bugs.md #15's deep-link "
                    "fallback served the public homepage"
                )
        for marker in _HOMEPAGE_ONLY_MARKERS:
            if marker in lowered:
                return (
                    "auth route rendered the public marketing homepage "
                    f"(matched {marker!r}) — app_bugs.md #15 deep-link fallback"
                )

    if _is_near_uniform(img):
        return "capture is a blank/near-uniform image — nothing rendered"

    return None


# ── Screenshot masks ─────────────────────────────────────────────────────────
# Shared with every visual test module so a new suite cannot silently omit the
# identity masks and start committing the test account's name to baselines.

# Dynamic regions that change every page load — masking stops false diffs on
# nightly visual runs.
DEFAULT_MASKS = [
    "[class*='timestamp']",
    "[class*='last-updated']",
    "[class*='activity']",
    "time",
    "[class*='polling']",
]

# Personal data rendered by the logged-in shell. Masked on every authenticated
# capture for two reasons:
#   1. Privacy — these baselines embed the real test account's full name
#      ("Welcome, <first> <last>") and avatar initials. `snapshots/` is
#      gitignored so they never reach git history, but CI both caches the
#      directory and uploads it as a 30-day build artifact
#      (.github/workflows/ci.yml), so the images are retrievable by anyone with
#      repo access.
#   2. Portability — an unmasked name pins every baseline to one account, so
#      re-running the suite as TEST_USER_2 would diff on the sidebar alone.
# Deliberately NOT matching initials literally: locators/workspace_locators.py
# pins `text=MSM` while this account renders "SM", confirming initials vary per
# account. Anchored `^Welcome,` is used rather than
# AIMakerLocators.WELCOME_MESSAGE's bare `text=Welcome`, which would also match
# body copy containing the word. `_capture_page_masked` drops zero-count
# selectors, so listing extras is free.
# Verified against the live DOM 2026-08-12:
#   <div class="text-center …">            ← masked (the whole identity block)
#     <div class="… rounded-full …"><span>SM</span></div>   ← initials, NO avatar class
#     <p class="welcome-text">Welcome,&nbsp;<span>Saqib Manan</span></p>
#     <a class="switch-roles-link">Switch Roles</a>
#   </div>
# The sidebar initials circle is a bare Tailwind div, so `[class*='avatar' i]`
# (which matches only the 2 header avatars) does not cover it. Masking the
# parent block catches the circle and the name together. That also masks the
# "Switch Roles" link — an accepted trade: a small, static control loses pixel
# coverage so no capture carries identity.
AUTH_PII_MASKS = [
    "[class*='avatar' i]",  # header avatar circle(s) rendering initials
    ".welcome-text >> xpath=..",  # sidebar identity block (circle + name)
    "text=/^Welcome,/ >> xpath=..",  # fallback if .welcome-text is renamed
    "button[aria-label='Open profile']",  # per locators/dashboard_locators.py
]
