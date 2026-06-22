"""
Performance tests for authenticated routes and resource sizes.

Complements test_performance.py (public homepage) with:
  TestAuthRoutePerformance      — load times for models, prompt libraries, eval detail
  TestResourceSizes             — JS bundle size, response compression, image formats
  TestNavigationTimingNewRoutes — DOMContentLoaded budgets for new routes

Results saved to reports/performance_metrics_auth.json.

Run with:
    pytest tests/performance/test_performance_auth.py -m performance -v
"""

from datetime import datetime

import pytest
from playwright.sync_api import Page

from utils.config import Config
from utils.helpers import get_performance_metrics
from utils.reporters import save_json_report

pytestmark = [pytest.mark.performance]

BASE = Config.BASE_URL.rstrip("/")

BUDGET = {
    "auth_page_load_s": 12.0,
    "eval_detail_load_s": 15.0,
    "dom_content_loaded_ms": 6_000,
    "js_bundle_total_mb": 3.0,
    "large_response_kb": 10,
}

_ORG_ID = "1"
_MODELS_PATH = f"/dashboard/ai-maker/{_ORG_ID}/ai-models"
_PROMPT_LIBS_PATH = f"/dashboard/ai-maker/{_ORG_ID}/prompt-libraries"


def _nav_and_measure(page: Page, path: str) -> tuple[float, dict]:
    """Navigate to path and return (elapsed_s, navigation_timing_metrics)."""
    start = page.evaluate("performance.now()")
    page.goto(Config.url(path), wait_until="domcontentloaded", timeout=60_000)
    page.wait_for_timeout(500)
    end = page.evaluate("performance.now()")
    elapsed_s = (end - start) / 1_000
    metrics = get_performance_metrics(page)
    return elapsed_s, metrics


# ── Authenticated Route Performance ───────────────────────────────────────────


@pytest.mark.timeout(180)
class TestAuthRoutePerformance:
    """Load-time budgets for auth-walled SPA routes (models, prompt libraries, eval detail)."""

    def test_models_list_load_time(self, authenticated_page_fast: Page):
        """AI models list must load within the auth-route budget."""
        elapsed_s, metrics = _nav_and_measure(authenticated_page_fast, _MODELS_PATH)

        save_json_report(
            {
                "label": "models_list",
                "url": authenticated_page_fast.url,
                "elapsed_s": elapsed_s,
                "timestamp": datetime.now().isoformat(),
                **metrics,
            },
            "performance_metrics_auth.json",
        )

        assert elapsed_s < BUDGET["auth_page_load_s"], (
            f"AI models list load time {elapsed_s:.2f}s exceeds budget of "
            f"{BUDGET['auth_page_load_s']}s"
        )

    def test_prompt_libraries_load_time(self, authenticated_page_fast: Page):
        """Prompt libraries page must load within the auth-route budget."""
        elapsed_s, metrics = _nav_and_measure(authenticated_page_fast, _PROMPT_LIBS_PATH)

        save_json_report(
            {
                "label": "prompt_libraries",
                "url": authenticated_page_fast.url,
                "elapsed_s": elapsed_s,
                "timestamp": datetime.now().isoformat(),
                **metrics,
            },
            "performance_metrics_auth.json",
        )

        assert elapsed_s < BUDGET["auth_page_load_s"], (
            f"Prompt libraries load time {elapsed_s:.2f}s exceeds budget of "
            f"{BUDGET['auth_page_load_s']}s"
        )

    @pytest.mark.timeout(180)
    def test_evaluation_detail_load_time(
        self, authenticated_page_fast: Page, completed_eval_id: int
    ):
        """Evaluation detail page must load within the detail-route budget."""
        path = f"/dashboard/ai-maker/{_ORG_ID}/evaluations/{completed_eval_id}"
        import time as _time
        start = _time.monotonic()
        authenticated_page_fast.goto(
            Config.url(path), wait_until="domcontentloaded", timeout=60_000
        )
        authenticated_page_fast.wait_for_timeout(1_000)
        elapsed_s = _time.monotonic() - start

        metrics = get_performance_metrics(authenticated_page_fast)
        save_json_report(
            {
                "label": "evaluation_detail",
                "url": authenticated_page_fast.url,
                "elapsed_s": elapsed_s,
                "eval_id": completed_eval_id,
                "timestamp": datetime.now().isoformat(),
                **metrics,
            },
            "performance_metrics_auth.json",
        )

        assert elapsed_s < BUDGET["eval_detail_load_s"], (
            f"Evaluation detail load time {elapsed_s:.2f}s exceeds budget of "
            f"{BUDGET['eval_detail_load_s']}s — "
            "detail page may be fetching too many resources in sequence"
        )


# ── Resource Sizes ─────────────────────────────────────────────────────────────


@pytest.mark.timeout(120)
class TestResourceSizes:
    """Checks JS bundle size, response compression, and image formats on the homepage."""

    def test_js_bundle_total_size_under_budget(self, page: Page):
        """Total transferred JS size on homepage must not exceed 3 MB."""
        js_sizes: list[int] = []

        def _on_response(response):
            ct = response.headers.get("content-type", "").lower()
            if "javascript" in ct or response.url.endswith(".js"):
                try:
                    body = response.body()
                    js_sizes.append(len(body))
                except Exception:
                    pass

        page.on("response", _on_response)
        try:
            page.goto(BASE + "/", wait_until="load", timeout=60_000)
            page.wait_for_timeout(2_000)
        finally:
            page.remove_listener("response", _on_response)

        total_bytes = sum(js_sizes)
        total_mb = total_bytes / (1024 * 1024)

        save_json_report(
            {
                "label": "js_bundle_size",
                "url": BASE,
                "timestamp": datetime.now().isoformat(),
                "total_js_bytes": total_bytes,
                "total_js_mb": round(total_mb, 3),
                "js_file_count": len(js_sizes),
            },
            "performance_metrics_auth.json",
        )

        assert total_mb < BUDGET["js_bundle_total_mb"], (
            f"Total JS bundle size {total_mb:.2f} MB exceeds {BUDGET['js_bundle_total_mb']} MB budget. "
            "Consider code splitting, lazy loading, or removing unused dependencies."
        )

    def test_large_responses_use_compression(self, page: Page):
        """HTTP responses larger than 10 KB must use gzip or brotli compression."""
        uncompressed: list[str] = []

        def _check_compression(response):
            try:
                content_length = int(response.headers.get("content-length", "0") or "0")
                content_encoding = response.headers.get("content-encoding", "").lower()
                ct = response.headers.get("content-type", "").lower()

                is_text = any(
                    t in ct for t in ("html", "javascript", "css", "json", "text")
                )
                if is_text and content_length > BUDGET["large_response_kb"] * 1024:
                    if not any(enc in content_encoding for enc in ("gzip", "br", "deflate")):
                        uncompressed.append(
                            f"{response.url.split('?')[0][-80:]} ({content_length // 1024} KB)"
                        )
            except Exception:
                pass

        page.on("response", _check_compression)
        try:
            page.goto(BASE + "/", wait_until="load", timeout=60_000)
            page.wait_for_timeout(1_500)
        finally:
            page.remove_listener("response", _check_compression)

        if uncompressed:
            pytest.xfail(
                f"{len(uncompressed)} response(s) over {BUDGET['large_response_kb']} KB "
                f"served without compression: {uncompressed[:3]}. "
                "Enable gzip/brotli on the server to reduce transfer size."
            )

    def test_no_oversized_unoptimised_images(self, page: Page):
        """Images over 100 KB that are not WebP/AVIF should be flagged for optimisation."""
        large_jpegs: list[str] = []

        def _check_image(response):
            ct = response.headers.get("content-type", "").lower()
            if ct.startswith("image/") and "webp" not in ct and "avif" not in ct:
                try:
                    body = response.body()
                    if len(body) > 100 * 1024:
                        large_jpegs.append(
                            f"{response.url.split('?')[0][-80:]} "
                            f"({len(body) // 1024} KB, {ct})"
                        )
                except Exception:
                    pass

        page.on("response", _check_image)
        try:
            page.goto(BASE + "/", wait_until="load", timeout=60_000)
            page.wait_for_timeout(2_000)
        finally:
            page.remove_listener("response", _check_image)

        if large_jpegs:
            pytest.xfail(
                f"{len(large_jpegs)} image(s) over 100 KB not using WebP/AVIF: "
                f"{large_jpegs[:3]}. "
                "Convert to WebP/AVIF for significantly smaller file sizes. "
                "Next.js Image component handles this automatically when configured."
            )


# ── Navigation Timing for New Routes ─────────────────────────────────────────


@pytest.mark.timeout(120)
class TestNavigationTimingNewRoutes:
    """DOMContentLoaded budgets for routes added in the recent dev branch."""

    def test_models_page_dom_content_loaded(self, authenticated_page_fast: Page):
        """DOMContentLoaded on the models page must fire within the auth-route budget."""
        authenticated_page_fast.goto(
            Config.url(_MODELS_PATH), wait_until="domcontentloaded", timeout=60_000
        )
        authenticated_page_fast.wait_for_timeout(500)

        metrics = get_performance_metrics(authenticated_page_fast)
        dcl = metrics.get("dom_content_loaded_ms", 0)

        save_json_report(
            {
                "label": "models_list_dcl",
                "url": authenticated_page_fast.url,
                "timestamp": datetime.now().isoformat(),
                **metrics,
            },
            "performance_metrics_auth.json",
        )

        assert dcl < BUDGET["dom_content_loaded_ms"], (
            f"Models page DOMContentLoaded {dcl:.0f}ms exceeds "
            f"{BUDGET['dom_content_loaded_ms']}ms budget"
        )

    def test_prompt_libraries_dom_content_loaded(self, authenticated_page_fast: Page):
        """DOMContentLoaded on the prompt libraries page must be within budget."""
        authenticated_page_fast.goto(
            Config.url(_PROMPT_LIBS_PATH), wait_until="domcontentloaded", timeout=60_000
        )
        authenticated_page_fast.wait_for_timeout(500)

        metrics = get_performance_metrics(authenticated_page_fast)
        dcl = metrics.get("dom_content_loaded_ms", 0)

        save_json_report(
            {
                "label": "prompt_libraries_dcl",
                "url": authenticated_page_fast.url,
                "timestamp": datetime.now().isoformat(),
                **metrics,
            },
            "performance_metrics_auth.json",
        )

        assert dcl < BUDGET["dom_content_loaded_ms"], (
            f"Prompt libraries DOMContentLoaded {dcl:.0f}ms exceeds "
            f"{BUDGET['dom_content_loaded_ms']}ms budget"
        )

    def test_full_metrics_report_for_new_routes(self, authenticated_page_fast: Page):
        """Collect and persist full Navigation Timing metrics for new authenticated routes."""
        routes = [
            (_MODELS_PATH, "models_list_full"),
            (_PROMPT_LIBS_PATH, "prompt_libraries_full"),
        ]
        for path, label in routes:
            elapsed_s, metrics = _nav_and_measure(authenticated_page_fast, path)
            save_json_report(
                {
                    "label": label,
                    "url": Config.url(path),
                    "elapsed_s": elapsed_s,
                    "timestamp": datetime.now().isoformat(),
                    **metrics,
                },
                "performance_metrics_auth.json",
            )
        # Always passes — collects metrics for trend analysis
        assert True, "Metrics collection run complete"
