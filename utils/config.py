"""
Environment configuration loader for the Parakh test framework.
Supports development, staging, and production environments via .env or shell vars.

Priority (highest → lowest):
  1. Shell / CI environment variables
  2. .env file at the project root (loaded with override=False)
  3. Hardcoded defaults below
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root — shell vars take priority (override=False)
_root = Path(__file__).resolve().parent.parent
load_dotenv(_root / ".env", override=False)


class Config:
    """Central config object — read once at import time, referenced everywhere."""

    # ── URLs ──────────────────────────────────────────────────────────────────
    BASE_URL: str = os.getenv("BASE_URL", "https://dev.parakh.civicdataspace.in")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development").lower()
    # Keycloak SSO base URL (may differ from the app URL)
    KEYCLOAK_URL: str = os.getenv("KEYCLOAK_URL", "")
    # GraphQL API endpoint (defaults to BASE_URL/graphql if not set)
    GRAPHQL_URL: str = os.getenv("GRAPHQL_URL", "")

    # ── Browser ───────────────────────────────────────────────────────────────
    BROWSER: str = os.getenv("BROWSER", "chromium").lower()
    HEADLESS: bool = os.getenv("HEADLESS", "true").lower() in ("true", "1", "yes")
    SLOW_MO: int = int(os.getenv("SLOW_MO", "0"))
    TIMEOUT: int = int(os.getenv("TIMEOUT", "30000"))  # ms

    # ── Viewport ──────────────────────────────────────────────────────────────
    VIEWPORT_WIDTH: int = int(os.getenv("VIEWPORT_WIDTH", "1440"))
    VIEWPORT_HEIGHT: int = int(os.getenv("VIEWPORT_HEIGHT", "900"))

    # ── Auth — primary test account ───────────────────────────────────────────
    TEST_EMAIL: str = os.getenv("TEST_EMAIL", os.getenv("TEST_EMAIL_1", "test@example.com"))
    TEST_PASSWORD: str = os.getenv("TEST_PASSWORD", os.getenv("TEST_PASSWORD_1", "testpassword123"))

    # ── Auth — multi-user slots (for parallel test runs) ──────────────────────
    # Each runner picks a slot via TEST_USER_INDEX so tests don't share state.
    TEST_EMAIL_1: str = os.getenv("TEST_EMAIL_1", os.getenv("TEST_EMAIL", "test@example.com"))
    TEST_PASSWORD_1: str = os.getenv("TEST_PASSWORD_1", os.getenv("TEST_PASSWORD", "testpassword123"))
    TEST_EMAIL_2: str = os.getenv("TEST_EMAIL_2", "test2@example.com")
    TEST_PASSWORD_2: str = os.getenv("TEST_PASSWORD_2", "testpassword2")
    TEST_USER_INDEX: int = int(os.getenv("TEST_USER_INDEX", "1"))  # 1 or 2

    # ── Sandbox org for write-side regression tests ───────────────────────────
    # When set, write-marked regression tests are allowed to mutate this org.
    # When unset, those tests skip (so production data is never accidentally
    # touched). The slug is the URL-path segment after /dashboard/ai-maker/.
    SANDBOX_ORG_SLUG: str = os.getenv("SANDBOX_ORG_SLUG", "")

    # ── Known evaluator emails (deployment-specific) ──────────────────────────
    # Some E2E tests assert specific evaluator accounts appear on the Evaluators
    # management page. Leave unset to auto-skip those data-driven assertions.
    EVALUATOR_EMAIL_1: str = os.getenv("EVALUATOR_EMAIL_1", "")
    EVALUATOR_EMAIL_2: str = os.getenv("EVALUATOR_EMAIL_2", "")

    # ── Retries ───────────────────────────────────────────────────────────────
    RETRY_COUNT: int = int(os.getenv("RETRY_COUNT", "2"))
    RETRY_DELAY: float = float(os.getenv("RETRY_DELAY", "2.0"))

    # ── Reports ───────────────────────────────────────────────────────────────
    SCREENSHOT_ON_FAILURE: bool = os.getenv(
        "SCREENSHOT_ON_FAILURE", "true"
    ).lower() in ("true", "1", "yes")
    SCREENSHOTS_DIR: Path = _root / "screenshots"
    SNAPSHOTS_DIR: Path = _root / "snapshots"
    REPORTS_DIR: Path = _root / "reports"
    JSON_REPORT_FILE: Path = _root / "reports" / "report.json"

    # ── Visual regression ─────────────────────────────────────────────────────
    VISUAL_THRESHOLD: float = float(os.getenv("VISUAL_THRESHOLD", "0.1"))

    # ── Derived helpers ───────────────────────────────────────────────────────

    @classmethod
    def url(cls, path: str = "") -> str:
        """Return an absolute URL for *path* relative to BASE_URL."""
        return cls.BASE_URL.rstrip("/") + "/" + path.lstrip("/")

    @classmethod
    def graphql_endpoint(cls) -> str:
        """GraphQL API endpoint — uses GRAPHQL_URL if set, else prepends 'api.'.

        Convention: parakh.civicdataspace.in → api.parakh.civicdataspace.in.
        Note: this *prepends* the api segment instead of replacing the first
        subdomain, otherwise parakh.civicdataspace.in collapses to
        api.civicdataspace.in (which does not exist).
        """
        if cls.GRAPHQL_URL:
            return cls.GRAPHQL_URL
        base = cls.BASE_URL.rstrip("/")
        if "://" in base:
            scheme, host = base.split("://", 1)
            if not host.startswith("api."):
                host = "api." + host
            return f"{scheme}://{host}/graphql"
        return base + "/graphql"

    @classmethod
    def active_test_user(cls) -> dict:
        """Return the credential dict for the currently configured user slot."""
        if cls.TEST_USER_INDEX == 2:
            return {"email": cls.TEST_EMAIL_2, "password": cls.TEST_PASSWORD_2}
        return {"email": cls.TEST_EMAIL_1, "password": cls.TEST_PASSWORD_1}

    @classmethod
    def ensure_dirs(cls) -> None:
        """Create all output directories if they do not already exist."""
        for d in (cls.SCREENSHOTS_DIR, cls.SNAPSHOTS_DIR, cls.REPORTS_DIR):
            d.mkdir(parents=True, exist_ok=True)

    @classmethod
    def summary(cls) -> dict:
        """Return a human-readable config snapshot (no secrets)."""
        return {
            "base_url": cls.BASE_URL,
            "environment": cls.ENVIRONMENT,
            "browser": cls.BROWSER,
            "headless": cls.HEADLESS,
            "viewport": f"{cls.VIEWPORT_WIDTH}x{cls.VIEWPORT_HEIGHT}",
            "timeout_ms": cls.TIMEOUT,
            "visual_threshold": cls.VISUAL_THRESHOLD,
            "test_user_index": cls.TEST_USER_INDEX,
            "retry_count": cls.RETRY_COUNT,
            "sandbox_org_slug": cls.SANDBOX_ORG_SLUG or "(unset — write tests will skip)",
        }


# Ensure output directories exist as soon as config is imported.
Config.ensure_dirs()
