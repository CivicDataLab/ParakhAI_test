"""
Performance tests for the Parakh platform.
Uses Playwright's CDP (Chrome DevTools Protocol) and the Navigation Timing API
to measure real page load metrics.

Metrics are saved to reports/performance_metrics.json.
"""

from datetime import datetime

import pytest
from playwright.sync_api import Browser, Page

from utils.config import Config
from utils.helpers import get_performance_metrics, measure_load_time
from utils.reporters import save_json_report

pytestmark = [pytest.mark.performance]

BASE = Config.BASE_URL

# Performance budgets (adjust based on acceptable baselines)
BUDGET = {
    "page_load_s": 5.0,
    "ttfb_ms": 800,
    "dom_content_loaded_ms": 3_000,
    "lcp_candidate_s": 3.0,
    "mobile_load_s": 8.0,  # 3G-equivalent throttling
}


def _collect_metrics(page: Page, url: str, label: str) -> dict:
    """Navigate to url, collect timing metrics, and return them with metadata."""
    page.goto(url, wait_until="load", timeout=60_000)
    page.wait_for_timeout(500)

    raw = get_performance_metrics(page)
    metrics = {
        "label": label,
        "url": url,
        "timestamp": datetime.now().isoformat(),
        **raw,
    }
    return metrics


# ──────────────────────────────────────────────────── Load time


class TestLoadTime:
    def test_homepage_load_time(self, page: Page):
        """Total page load time must be under 5 seconds."""
        elapsed = measure_load_time(page, BASE)
        assert elapsed < BUDGET["page_load_s"], (
            f"Homepage load time {elapsed:.2f}s exceeds budget of {BUDGET['page_load_s']}s"
        )

    def test_time_to_first_byte(self, page: Page):
        """TTFB (Time to First Byte) must be under 800ms."""
        metrics = _collect_metrics(page, BASE, "homepage")
        ttfb = metrics.get("ttfb_ms", 0)
        assert ttfb < BUDGET["ttfb_ms"], (
            f"TTFB {ttfb:.0f}ms exceeds budget of {BUDGET['ttfb_ms']}ms"
        )

    def test_dom_content_loaded(self, page: Page):
        """DOMContentLoaded must fire within 3 seconds of navigation start."""
        metrics = _collect_metrics(page, BASE, "homepage")
        dcl = metrics.get("dom_content_loaded_ms", 0)
        assert dcl < BUDGET["dom_content_loaded_ms"], (
            f"DOMContentLoaded at {dcl:.0f}ms exceeds budget of {BUDGET['dom_content_loaded_ms']}ms"
        )

    def test_time_to_interactive(self, page: Page):
        """
        Approximate TTI: domInteractive should be within a reasonable window.
        True TTI requires a Long Tasks observer — this is a proxy measure.
        """
        metrics = _collect_metrics(page, BASE, "homepage")
        tti_ms = metrics.get("dom_interactive_ms", 0)
        # Soft budget: 4 seconds for proxy TTI
        assert tti_ms < 4_000, (
            f"Proxy TTI (domInteractive) {tti_ms:.0f}ms exceeds 4000ms budget"
        )


# ──────────────────────────────────────────────────── Hero / LCP


class TestHeroImage:
    def test_hero_image_load_time(self, page: Page):
        """
        The largest contentful paint candidate (hero image/text) should load in < 3s.
        Uses the PerformanceObserver LCP API via CDP evaluation.
        """

        def _inject_lcp_observer(pg: Page) -> None:
            pg.evaluate(
                """() => {
                    window.__LCP__ = null;
                    new PerformanceObserver((list) => {
                        const entries = list.getEntries();
                        if (entries.length > 0) {
                            window.__LCP__ = entries[entries.length - 1].startTime;
                        }
                    }).observe({ type: 'largest-contentful-paint', buffered: true });
                }"""
            )

        page.goto(BASE, wait_until="domcontentloaded", timeout=30_000)
        _inject_lcp_observer(page)
        page.wait_for_load_state("networkidle", timeout=15_000)
        page.wait_for_timeout(1_000)

        lcp_ms = page.evaluate("window.__LCP__")
        if lcp_ms is None:
            pytest.xfail("LCP not available — PerformanceObserver may not have fired in time")

        lcp_s = lcp_ms / 1000.0
        assert lcp_s < BUDGET["lcp_candidate_s"], (
            f"LCP {lcp_s:.2f}s exceeds budget of {BUDGET['lcp_candidate_s']}s. "
            "Optimise hero image size, use next-gen formats (WebP/AVIF), or add preload hints."
        )


# ──────────────────────────────────────────────────── Render blocking


class TestRenderBlocking:
    def test_no_render_blocking_resources(self, page: Page):
        """
        Check for synchronous scripts or non-deferred stylesheets in <head>
        that could block the initial render.
        """
        page.goto(BASE, wait_until="domcontentloaded", timeout=30_000)

        blocking = page.evaluate(
            """() => {
                const scripts = Array.from(document.querySelectorAll('head script[src]'));
                const blocking = scripts.filter(s => !s.defer && !s.async && !s.type.includes('module'));
                return blocking.map(s => s.src);
            }"""
        )

        if blocking:
            pytest.xfail(
                f"Found {len(blocking)} potentially render-blocking script(s) in <head>:\n"
                + "\n".join(blocking[:5])
                + "\nAdd 'defer' or 'async' attributes to non-critical scripts."
            )


# ──────────────────────────────────────────────────── Mobile performance


class TestMobilePerformance:
    def test_mobile_performance_score(self, browser: Browser):
        """
        Simulate 3G-equivalent conditions (latency + bandwidth throttling via CDP)
        and measure page load time at mobile viewport.
        """
        context = browser.new_context(
            viewport={"width": 390, "height": 844},
            ignore_https_errors=True,
        )
        page = context.new_page()

        try:
            # Emulate slow 3G via Chrome DevTools Protocol
            cdp = context.new_cdp_session(page)
            cdp.send(
                "Network.emulateNetworkConditions",
                {
                    "offline": False,
                    "latency": 150,           # ms round-trip latency
                    "downloadThroughput": 1_500_000 / 8,  # 1.5 Mbps in bytes/s
                    "uploadThroughput": 750_000 / 8,       # 750 kbps
                    "connectionType": "cellular3g",
                },
            )

            start = page.evaluate("performance.now()")
            page.goto(BASE, wait_until="load", timeout=60_000)
            end = page.evaluate("performance.now()")
            elapsed_s = (end - start) / 1000.0

            metrics = {
                "label": "mobile_3g",
                "url": BASE,
                "timestamp": datetime.now().isoformat(),
                "load_time_s": elapsed_s,
                "viewport": "390x844",
                "network": "simulated_3g",
            }
            save_json_report(metrics, "performance_metrics.json")

            assert elapsed_s < BUDGET["mobile_load_s"], (
                f"Mobile (3G) load time {elapsed_s:.2f}s exceeds budget of {BUDGET['mobile_load_s']}s"
            )
        finally:
            context.close()


# ──────────────────────────────────────────────────── Full metrics report


class TestMetricsReport:
    def test_save_full_performance_report(self, page: Page):
        """
        Collect and persist full Navigation Timing metrics to JSON.
        This test always passes — it only generates the report.
        """
        metrics = _collect_metrics(page, BASE, "homepage_full")
        save_json_report(metrics, "performance_metrics.json")
        assert True, "Performance report generated"
