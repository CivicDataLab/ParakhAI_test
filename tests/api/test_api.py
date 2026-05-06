"""
HTTP-layer API tests for the Parakh platform.
Uses the requests library — no browser required.
"""

import time

import pytest
import requests

from utils.config import Config

pytestmark = [pytest.mark.api]

BASE = Config.BASE_URL.rstrip("/")

# Security headers we expect to be present
EXPECTED_SECURITY_HEADERS = [
    "X-Content-Type-Options",
    "X-Frame-Options",
]

# Headers that are nice-to-have (soft assertions)
NICE_TO_HAVE_HEADERS = [
    "Content-Security-Policy",
    "Strict-Transport-Security",
    "Referrer-Policy",
    "Permissions-Policy",
]


class TestBasicHTTP:
    def test_homepage_returns_200(self, api_client: requests.Session):
        """GET / must return HTTP 200."""
        resp = api_client.get(BASE + "/", allow_redirects=True, timeout=15)
        assert resp.status_code == 200, (
            f"Homepage returned {resp.status_code}, expected 200"
        )

    def test_homepage_content_type_is_html(self, api_client: requests.Session):
        """Homepage response must declare text/html content type."""
        resp = api_client.get(BASE + "/", allow_redirects=True, timeout=15)
        content_type = resp.headers.get("Content-Type", "").lower()
        assert "text/html" in content_type, (
            f"Expected text/html content type, got: '{content_type}'"
        )

    def test_dashboard_returns_redirect_when_unauthenticated(
        self, api_client: requests.Session
    ):
        """
        GET /dashboard without auth should return a 3xx redirect
        (to login/SSO) or a 401/403.

        allow_redirects=False short-circuits before the session's max_redirects
        is consulted, so we receive the raw redirect response with no exception.
        """
        resp = api_client.get(BASE + "/dashboard", allow_redirects=False, timeout=15)
        assert resp.status_code in (301, 302, 303, 307, 308, 401, 403), (
            f"Expected redirect or auth error for /dashboard, got {resp.status_code}"
        )

    def test_response_time_under_3_seconds(self, api_client: requests.Session):
        """Homepage must respond within 3 seconds (wall-clock time)."""
        start = time.monotonic()
        resp = api_client.get(BASE + "/", allow_redirects=True, timeout=15)
        elapsed = time.monotonic() - start
        assert elapsed < 3.0, (
            f"Homepage took {elapsed:.2f}s — expected under 3s. "
            f"Status: {resp.status_code}"
        )


class TestStaticAssets:
    def test_robots_txt_accessible(self, api_client: requests.Session):
        """GET /robots.txt should return 200."""
        resp = api_client.get(BASE + "/robots.txt", allow_redirects=True, timeout=10)
        if resp.status_code == 404:
            pytest.xfail("/robots.txt not found — consider adding one for SEO")
        assert resp.status_code == 200, (
            f"/robots.txt returned {resp.status_code}"
        )

    def test_sitemap_accessible(self, api_client: requests.Session):
        """GET /sitemap.xml should return 200."""
        resp = api_client.get(BASE + "/sitemap.xml", allow_redirects=True, timeout=10)
        if resp.status_code == 404:
            pytest.xfail("/sitemap.xml not found — consider adding one for SEO/crawlability")
        assert resp.status_code == 200, (
            f"/sitemap.xml returned {resp.status_code}"
        )

    def test_favicon_accessible(self, api_client: requests.Session):
        """GET /favicon.ico should return 200."""
        resp = api_client.get(BASE + "/favicon.ico", allow_redirects=True, timeout=10)
        assert resp.status_code == 200, (
            f"/favicon.ico returned {resp.status_code} — "
            "ensure a favicon is served for browser tab recognition"
        )


class TestSecurityHeaders:
    def test_security_headers_present(self, api_client: requests.Session):
        """Response headers must include key security headers."""
        resp = api_client.get(BASE + "/", allow_redirects=True, timeout=15)
        missing = [h for h in EXPECTED_SECURITY_HEADERS if h not in resp.headers]
        assert len(missing) == 0, (
            f"Missing required security headers: {missing}\n"
            f"Present headers: {dict(resp.headers)}"
        )

    def test_nice_to_have_security_headers(self, api_client: requests.Session):
        """Soft check: log which recommended security headers are absent."""
        resp = api_client.get(BASE + "/", allow_redirects=True, timeout=15)
        missing = [h for h in NICE_TO_HAVE_HEADERS if h not in resp.headers]
        if missing:
            pytest.xfail(
                f"Recommended (nice-to-have) security headers missing: {missing}. "
                "Consider adding them for defence-in-depth."
            )

    def test_no_server_version_disclosure(self, api_client: requests.Session):
        """The Server header should not expose version information."""
        resp = api_client.get(BASE + "/", allow_redirects=True, timeout=15)
        server = resp.headers.get("Server", "")
        # Common version-disclosing strings
        risky = any(v in server.lower() for v in ["apache/", "nginx/", "iis/", "express/"])
        assert not risky, (
            f"Server header discloses version: '{server}'. "
            "Strip version numbers to reduce attack surface."
        )

    def test_x_content_type_options_is_nosniff(self, api_client: requests.Session):
        """X-Content-Type-Options must be set to 'nosniff'."""
        resp = api_client.get(BASE + "/", allow_redirects=True, timeout=15)
        value = resp.headers.get("X-Content-Type-Options", "").lower()
        if not value:
            pytest.skip("X-Content-Type-Options header not present")
        assert value == "nosniff", (
            f"X-Content-Type-Options should be 'nosniff', got: '{value}'"
        )


class TestHTTPS:
    def test_http_redirects_to_https(self):
        """Plain HTTP requests should redirect to HTTPS."""
        http_url = BASE.replace("https://", "http://")
        if not http_url.startswith("http://"):
            pytest.skip("BASE_URL does not start with https — skipping HTTPS redirect test")
        try:
            resp = requests.get(http_url, allow_redirects=False, timeout=10)
            assert resp.status_code in (301, 302, 307, 308), (
                f"Expected HTTP→HTTPS redirect, got {resp.status_code}"
            )
            location = resp.headers.get("Location", "")
            assert location.startswith("https://"), (
                f"Redirect location should use HTTPS, got: '{location}'"
            )
        except requests.exceptions.ConnectionError:
            pytest.skip("HTTP port not open — site may only serve HTTPS")
