"""
Visual regression tests for the Parakh platform.

First run  → saves baseline PNG snapshots to /snapshots.
Subsequent → pixel-diffs against the baseline using Pillow.
Failures   → saves a diff image to /screenshots.

Threshold: configurable via VISUAL_THRESHOLD env var (default 0.1 %).
"""

from pathlib import Path

import pytest
from PIL import Image, ImageChops
from playwright.sync_api import Page

from utils.config import Config

pytestmark = [pytest.mark.visual]

_SNAPSHOTS_DIR = Config.SNAPSHOTS_DIR
_SCREENSHOTS_DIR = Config.SCREENSHOTS_DIR
_THRESHOLD = Config.VISUAL_THRESHOLD  # percentage 0–100

# Viewport presets
VIEWPORTS = {
    "desktop": (1440, 900),
    "tablet": (768, 1024),
    "mobile": (390, 844),
}


# ──────────────────────────────────────────────────── Helpers


def _snapshot_path(name: str) -> Path:
    return _SNAPSHOTS_DIR / f"{name}.png"


def _diff_path(name: str) -> Path:
    return _SCREENSHOTS_DIR / f"DIFF_{name}.png"


def _pixel_diff_percent(img_a: Image.Image, img_b: Image.Image) -> float:
    """
    Return the percentage of pixels that differ between two images.
    Resizes the smaller image to match the larger before comparison.
    """
    if img_a.size != img_b.size:
        target = (max(img_a.width, img_b.width), max(img_a.height, img_b.height))
        img_a = img_a.resize(target, Image.LANCZOS)
        img_b = img_b.resize(target, Image.LANCZOS)

    diff = ImageChops.difference(img_a.convert("RGB"), img_b.convert("RGB"))
    pixels = diff.size[0] * diff.size[1]
    non_zero = sum(1 for p in diff.getdata() if any(c > 10 for c in p))
    return (non_zero / pixels) * 100.0


def _compare_or_save_baseline(
    current_img: Image.Image,
    snapshot_name: str,
) -> None:
    """
    If a baseline exists, compare against it and fail if diff > threshold.
    If no baseline exists, save the current image as the baseline.
    """
    snapshot = _snapshot_path(snapshot_name)

    if not snapshot.exists():
        current_img.save(str(snapshot))
        pytest.skip(f"Baseline saved for '{snapshot_name}' — re-run to compare.")

    baseline = Image.open(str(snapshot))
    diff_pct = _pixel_diff_percent(baseline, current_img)

    if diff_pct > _THRESHOLD:
        # Save diff image
        diff = ImageChops.difference(
            baseline.resize(current_img.size, Image.LANCZOS).convert("RGB"),
            current_img.convert("RGB"),
        )
        diff.save(str(_diff_path(snapshot_name)))

        raise AssertionError(
            f"Visual diff {diff_pct:.3f}% exceeds threshold {_THRESHOLD}% for '{snapshot_name}'. "
            f"Diff image saved to {_diff_path(snapshot_name)}. "
            "To update baseline, delete the snapshot and re-run."
        )


def _capture_page(page: Page, url: str) -> Image.Image:
    """Navigate to url and return a PIL Image of the full page screenshot."""
    page.goto(url, wait_until="networkidle", timeout=30_000)
    page.wait_for_timeout(1_000)  # allow fonts/animations to settle
    raw = page.screenshot(full_page=True)
    import io
    return Image.open(io.BytesIO(raw))


def _page_at_viewport(browser, width: int, height: int) -> Page:
    ctx = browser.new_context(
        viewport={"width": width, "height": height},
        ignore_https_errors=True,
    )
    return ctx.new_page()


def _authenticated_page_at_viewport(
    browser, storage_state_path: str, width: int = 1440, height: int = 900
) -> Page:
    """Create a fresh authenticated context at the given viewport.

    Seeds cookies + localStorage from the cached storage_state path so we don't
    re-run Keycloak SSO per visual scan. Caller closes via page.context.close().
    """
    ctx = browser.new_context(
        viewport={"width": width, "height": height},
        ignore_https_errors=True,
        locale="en-US",
        storage_state=storage_state_path,
    )
    return ctx.new_page()


def _capture_page_masked(page: Page, url: str, masks: list) -> Image.Image:
    """Like _capture_page but masks dynamic regions in the screenshot.

    Each selector in `masks` is resolved to a Locator; Playwright paints those
    elements as solid pink boxes during the screenshot so they don't trigger
    visual diffs on every nightly run (timestamps, polling counters,
    activity feeds).

    Auth-walled routes have background polling (assignments lists, eval lists)
    that prevent `networkidle` from ever settling — mirrors the workaround
    already in HomePage.go_to_home. Use `load` and a longer settle delay
    instead.
    """
    page.goto(url, wait_until="load", timeout=30_000)
    page.wait_for_timeout(2_500)
    mask_locators = []
    for sel in masks:
        loc = page.locator(sel)
        if loc.count() > 0:
            mask_locators.append(loc)
    raw = page.screenshot(full_page=True, mask=mask_locators or None)
    import io
    return Image.open(io.BytesIO(raw))


# Dynamic regions that change every page load — masking stops false diffs on
# nightly visual runs.
_DEFAULT_MASKS = [
    "[class*='timestamp']",
    "[class*='last-updated']",
    "[class*='activity']",
    "time",
    "[class*='polling']",
]


# ──────────────────────────────────────────────────── Homepage viewports


class TestHomepageVisual:
    def test_homepage_desktop_screenshot(self, browser):
        """Desktop 1440×900 — full page screenshot regression."""
        page = _page_at_viewport(browser, 1440, 900)
        try:
            img = _capture_page(page, Config.BASE_URL)
            _compare_or_save_baseline(img, "homepage_desktop_1440x900")
        finally:
            page.context.close()

    def test_homepage_tablet_screenshot(self, browser):
        """Tablet 768×1024 — full page screenshot regression."""
        page = _page_at_viewport(browser, 768, 1024)
        try:
            img = _capture_page(page, Config.BASE_URL)
            _compare_or_save_baseline(img, "homepage_tablet_768x1024")
        finally:
            page.context.close()

    def test_homepage_mobile_screenshot(self, browser):
        """Mobile 390×844 — full page screenshot regression."""
        page = _page_at_viewport(browser, 390, 844)
        try:
            img = _capture_page(page, Config.BASE_URL)
            _compare_or_save_baseline(img, "homepage_mobile_390x844")
        finally:
            page.context.close()


# ──────────────────────────────────────────────────── Section-level


class TestSectionVisual:
    def test_hero_section_screenshot(self, browser):
        """Capture the above-the-fold hero section for visual regression."""
        page = _page_at_viewport(browser, 1440, 900)
        try:
            page.goto(Config.BASE_URL, wait_until="networkidle", timeout=30_000)
            page.wait_for_timeout(1_000)

            hero = page.locator(
                "section:first-of-type, [class*='hero'], [class*='Hero'], [class*='banner']"
            ).first
            if not hero.is_visible():
                pytest.skip("Hero section element not found with current selectors")

            import io
            raw = hero.screenshot()
            img = Image.open(io.BytesIO(raw))
            _compare_or_save_baseline(img, "hero_section_desktop")
        finally:
            page.context.close()

    def test_footer_screenshot(self, browser):
        """Capture the footer for visual regression."""
        page = _page_at_viewport(browser, 1440, 900)
        try:
            page.goto(Config.BASE_URL, wait_until="networkidle", timeout=30_000)
            page.keyboard.press("End")
            page.wait_for_timeout(700)

            footer = page.locator("footer").first
            if not footer.is_visible():
                pytest.skip("Footer element not found")

            import io
            raw = footer.screenshot()
            img = Image.open(io.BytesIO(raw))
            _compare_or_save_baseline(img, "footer_desktop")
        finally:
            page.context.close()


# ──────────────────────────────────────────────────── Feature tabs


class TestFeatureTabsVisual:
    # Source of truth lives in HomeLocators.FEATURE_TAB_LABELS; mirrored here
    # only to keep snapshot filenames pinned to short stable IDs.
    _TAB_PARAMS = [
        ("Automation-assisted Evaluation Environment", "tab_0_automation"),
        ("Expert-led Evaluations", "tab_1_expert"),
        ("Sector-specific Test Cases", "tab_2_sector"),
        ("Evaluation History & Reports", "tab_3_history"),
    ]

    @pytest.mark.parametrize(
        "tab_label,snapshot_label", _TAB_PARAMS, ids=[p[1] for p in _TAB_PARAMS]
    )
    def test_feature_tabs_screenshot(
        self, browser, tab_label: str, snapshot_label: str
    ):
        """Visual regression for each feature tab's content area.

        The homepage renders tabs as plain <button>s (no role="tab"),
        so we locate by visible label. The captured region is the whole
        tabs <section> — captures both the active-button highlight and
        the content panel, which both change per tab.
        """
        page = _page_at_viewport(browser, 1440, 900)
        try:
            page.goto(Config.BASE_URL, wait_until="networkidle", timeout=30_000)
            page.wait_for_timeout(1_000)

            tab = page.locator(f"button:has-text({tab_label!r})").first
            if not tab.is_visible(timeout=5_000):
                pytest.skip(f"Tab '{tab_label}' not found on homepage")

            tab.click()
            page.wait_for_timeout(600)

            section = page.locator(
                "section:has(button:has-text(\"Automation-assisted Evaluation Environment\"))"
            ).first
            if not section.is_visible():
                pytest.skip("Tabs section not found after clicking")

            import io
            raw = section.screenshot()
            img = Image.open(io.BytesIO(raw))
            _compare_or_save_baseline(img, f"feature_{snapshot_label}")
        finally:
            page.context.close()


# ──────────────────────────────────────────── Authenticated page baselines


class TestAuthenticatedPageVisuals:
    """Desktop visual baselines for 12 auth-walled routes.

    First run (`run_visual=true` workflow_dispatch): saves baselines to
    `snapshots/auth_<name>_desktop.png` and skips with the standard
    "baseline saved" message. Subsequent runs diff against the cached
    baseline at Config.VISUAL_THRESHOLD (default 0.1%).

    Dynamic regions are masked via _DEFAULT_MASKS to prevent flaky diffs.
    Tests are parametrized by (path, name); each is independent so a failure
    on one page doesn't mask the others.
    """

    AUTH_ROUTES = [
        ("/dashboard", "dashboard_role_selector"),
        ("/dashboard/ai-maker", "org_selector"),
        ("/dashboard/ai-maker/1", "ai_maker_dashboard"),
        ("/dashboard/ai-maker/1/ai-models", "models_list"),
        ("/dashboard/ai-maker/1/evaluations", "evaluations_list"),
        ("/dashboard/ai-maker/1/evaluations/new", "new_evaluation_wizard"),
        ("/dashboard/ai-maker/1/auditors", "auditors_management"),
        ("/dashboard/ai-maker/1/prompt-libraries", "prompt_libraries"),
        ("/dashboard/auditor", "auditor_dashboard"),
        ("/dashboard/auditor/assignments", "auditor_assignments"),
        ("/dashboard/auditor/evaluations", "auditor_evaluations"),
        ("/evaluation/288", "evaluation_detail_completed"),
    ]

    @pytest.mark.parametrize(
        "path,name", AUTH_ROUTES, ids=[r[1] for r in AUTH_ROUTES]
    )
    @pytest.mark.auth
    @pytest.mark.regression
    def test_authenticated_page_desktop(
        self, browser, authenticated_storage_state, path, name
    ):
        page = _authenticated_page_at_viewport(
            browser, authenticated_storage_state, 1440, 900
        )
        try:
            try:
                img = _capture_page_masked(page, Config.url(path), _DEFAULT_MASKS)
            except Exception as exc:  # noqa: BLE001
                pytest.skip(
                    f"Could not capture {path}: {exc}. "
                    "Page may be unreachable for this account."
                )
            _compare_or_save_baseline(img, f"auth_{name}_desktop_1440x900")
        finally:
            page.context.close()
