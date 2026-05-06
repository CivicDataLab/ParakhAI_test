"""
Reusable utility functions for the Parakh test framework.
"""

import time
from datetime import datetime
from pathlib import Path

from playwright.sync_api import ConsoleMessage, Page

from utils.config import Config

# ─────────────────────────────────────────────────────────────── Screenshots


def take_screenshot(page: Page, name: str) -> Path:
    """
    Save a PNG screenshot to the screenshots directory.

    Returns the Path of the saved file.
    """
    Config.ensure_dirs()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = name.replace(" ", "_").replace("/", "_")
    filename = Config.SCREENSHOTS_DIR / f"{timestamp}_{safe_name}.png"
    page.screenshot(path=str(filename), full_page=True)
    return filename


# ──────────────────────────────────────────────────────────────── Network


def wait_for_network_idle(page: Page, timeout: int = 10_000) -> None:
    """Wait until there are no in-flight network requests."""
    page.wait_for_load_state("networkidle", timeout=timeout)


# ─────────────────────────────────────────────────────────────── Console


def assert_no_console_errors(page: Page) -> list[str]:
    """
    Collect and return browser console errors.
    Caller decides whether to assert on the returned list.
    """
    errors: list[str] = []

    def _capture(msg: ConsoleMessage) -> None:
        if msg.type == "error":
            errors.append(msg.text)

    page.on("console", _capture)
    return errors


# ─────────────────────────────────────────────────────────── Accessibility


def _hex_to_rgb(hex_color: str) -> tuple[float, float, float]:
    """Convert a hex color string (#rrggbb or rrggbb) to an (R, G, B) tuple."""
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 3:
        hex_color = "".join(c * 2 for c in hex_color)
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    return r, g, b


def _relative_luminance(r: float, g: float, b: float) -> float:
    """Compute relative luminance per WCAG 2.1 formula."""

    def _linearise(c: float) -> float:
        c /= 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    return 0.2126 * _linearise(r) + 0.7152 * _linearise(g) + 0.0722 * _linearise(b)


def calculate_contrast_ratio(hex1: str, hex2: str) -> float:
    """
    Return the WCAG 2.1 contrast ratio between two hex colours.

    WCAG AA requires >= 4.5 for normal text, >= 3.0 for large text.
    """
    l1 = _relative_luminance(*_hex_to_rgb(hex1))
    l2 = _relative_luminance(*_hex_to_rgb(hex2))
    lighter, darker = max(l1, l2), min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


# ─────────────────────────────────────────────────────────── Performance


def measure_load_time(page: Page, url: str) -> float:
    """
    Navigate to a URL and return the total load time in seconds.
    Uses the Navigation Timing API.
    """
    page.goto(url, wait_until="load")
    timing = page.evaluate(
        """() => {
            const t = performance.timing;
            return t.loadEventEnd - t.navigationStart;
        }"""
    )
    return timing / 1000.0  # convert ms → s


def get_performance_metrics(page: Page) -> dict:
    """
    Return a dict of key performance metrics from the Navigation Timing API.
    """
    metrics = page.evaluate(
        """() => {
            const t = performance.timing;
            const nav = performance.getEntriesByType('navigation')[0] || {};
            return {
                dns_lookup_ms: t.domainLookupEnd - t.domainLookupStart,
                tcp_connect_ms: t.connectEnd - t.connectStart,
                ttfb_ms: t.responseStart - t.requestStart,
                dom_content_loaded_ms: t.domContentLoadedEventEnd - t.navigationStart,
                page_load_ms: t.loadEventEnd - t.navigationStart,
                dom_interactive_ms: t.domInteractive - t.navigationStart,
                transfer_size_bytes: nav.transferSize || 0,
                encoded_body_size_bytes: nav.encodedBodySize || 0,
            };
        }"""
    )
    return metrics


# ──────────────────────────────────────────────────────────── Misc


def retry(fn, retries: int = 3, delay: float = 1.0):
    """Simple retry wrapper for flaky operations."""
    last_exc = None
    for _attempt in range(retries):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            time.sleep(delay)
    raise last_exc  # type: ignore[misc]
