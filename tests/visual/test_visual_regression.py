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
    @pytest.mark.parametrize(
        "tab_index,tab_label",
        [
            (0, "tab_0_automation"),
            (1, "tab_1_expert"),
            (2, "tab_2_sector"),
            (3, "tab_3_history"),
        ],
    )
    def test_feature_tabs_screenshot(self, browser, tab_index: int, tab_label: str):
        """Visual regression for each feature tab's content area."""
        page = _page_at_viewport(browser, 1440, 900)
        try:
            page.goto(Config.BASE_URL, wait_until="networkidle", timeout=30_000)
            page.wait_for_timeout(1_000)

            tabs = page.locator("[role='tab'], button[class*='tab'], button[class*='Tab']")
            if tabs.count() <= tab_index:
                pytest.skip(
                    f"Tab index {tab_index} not available — only {tabs.count()} tabs found"
                )

            tabs.nth(tab_index).click()
            page.wait_for_timeout(600)

            content = page.locator(
                "[role='tabpanel'], [class*='tab-content'], [class*='TabContent']"
            ).first
            if not content.is_visible():
                pytest.skip("Tab content panel not found after clicking")

            import io
            raw = content.screenshot()
            img = Image.open(io.BytesIO(raw))
            _compare_or_save_baseline(img, f"feature_{tab_label}")
        finally:
            page.context.close()
