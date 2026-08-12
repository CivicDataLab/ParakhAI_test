"""
Liveness/readiness endpoint tests — ParakhAPI `dev` branch (PR #104, merged
2026-08-11 commit d9417ba, not yet cherry-picked to `main`).

Contract, from `apps/common/health.py` on `ParakhAPI` `dev`:
- `GET /health/` (liveness) — always `200 {"status": "ok"}`. Must NOT touch the
  database/cache: a dependency blip should never bounce a healthy container.
- `GET /health/ready/` (readiness) — `200 {"status": "ok", "checks": {...}}`
  when dependencies are reachable, `503 {"status": "unavailable", ...}`
  otherwise. This is what a deploy pipeline / load balancer should poll.
- Both reject non-GET with 405 and are exempt from `SECURE_SSL_REDIRECT`
  (a 301 there would read as healthy to a plain-HTTP container healthcheck,
  masking a wedged container).

As of 2026-08-11 this feature is merged to ParakhAPI `dev` but **not yet
deployed** to `dev.parakh.civicdataspace.in` (confirmed live: both paths
404). Tests assert the real contract but skip cleanly with an explicit
reason on 404 so the suite doesn't red until rollout, and start asserting
for real the moment it ships — mirrors the existing 5xx-skip convention in
test_db_health.py.

Markers: api, smoke (cheap, high-value infra checks).
"""

from urllib.parse import urlparse

import pytest

from utils.config import Config

pytestmark = [pytest.mark.api, pytest.mark.smoke]

# Health endpoints live on the backend host (same as GraphQL), not the
# frontend BASE_URL — derive it the same way Config.graphql_endpoint() does.
_BACKEND_ORIGIN = "{0.scheme}://{0.netloc}".format(urlparse(Config.graphql_endpoint()))

# Liveness must respond instantly — it does zero dependency checks by design.
_LIVENESS_BUDGET_S = 2.0


def _health_url(path: str) -> str:
    return _BACKEND_ORIGIN.rstrip("/") + "/" + path.lstrip("/")


def _skip_if_not_deployed(response) -> None:
    if response.status_code == 404:
        pytest.skip(
            "Health endpoint returned 404 — merged to ParakhAPI `dev` (PR #104) "
            "but not yet deployed to this environment. Not an app bug; revisit "
            "once the deploy ships."
        )


class TestLiveness:
    """`GET /health/` — process-alive check, must stay dependency-free."""

    def test_returns_ok(self, api_client):
        resp = api_client.get(_health_url("/health/"), timeout=10)
        _skip_if_not_deployed(resp)
        assert resp.status_code == 200, resp.text[:300]
        assert resp.json() == {"status": "ok"}

    def test_responds_fast(self, api_client):
        """No DB/cache round trip — a slow liveness response is itself a regression."""
        resp = api_client.get(_health_url("/health/"), timeout=10)
        _skip_if_not_deployed(resp)
        assert resp.elapsed.total_seconds() < _LIVENESS_BUDGET_S, (
            f"Liveness took {resp.elapsed.total_seconds():.2f}s — should be near-instant "
            "since it must not touch the database or cache."
        )

    def test_rejects_non_get(self, api_client):
        resp = api_client.post(_health_url("/health/"), timeout=10)
        _skip_if_not_deployed(resp)
        assert resp.status_code == 405

    def test_response_has_no_stack_trace_or_internal_details(self, api_client):
        """Even a healthy response must not leak framework internals."""
        resp = api_client.get(_health_url("/health/"), timeout=10)
        _skip_if_not_deployed(resp)
        body_lower = resp.text.lower()
        for leak in ("traceback", "django.db", "psycopg", "secret_key"):
            assert leak not in body_lower, f"Liveness response leaks '{leak}': {resp.text[:300]}"


class TestReadiness:
    """`GET /health/ready/` — dependency check for deploy pipelines / load balancers."""

    def test_reports_ok_with_database_check(self, api_client):
        resp = api_client.get(_health_url("/health/ready/"), timeout=10)
        _skip_if_not_deployed(resp)
        assert resp.status_code in (200, 503), resp.text[:300]
        body = resp.json()
        assert body["status"] in ("ok", "unavailable")
        assert "database" in body["checks"]
        # A live dev environment must be able to reach its own database.
        assert body["checks"]["database"] == "ok", (
            f"Readiness reports the database unreachable: {body}"
        )

    def test_rejects_non_get(self, api_client):
        resp = api_client.post(_health_url("/health/ready/"), timeout=10)
        _skip_if_not_deployed(resp)
        assert resp.status_code == 405

    def test_response_has_no_stack_trace_or_internal_details(self, api_client):
        resp = api_client.get(_health_url("/health/ready/"), timeout=10)
        _skip_if_not_deployed(resp)
        body_lower = resp.text.lower()
        for leak in ("traceback", "psycopg", "secret_key", "connection refused"):
            assert leak not in body_lower, f"Readiness response leaks '{leak}': {resp.text[:300]}"


class TestHealthEndpointsDoNotRedirect:
    """A 301 here reads as 'healthy' to a plain-HTTP container healthcheck.

    Can't flip SECURE_SSL_REDIRECT from outside the deployed app (that's
    covered on the ParakhAPI side by test_health.py::TestSslRedirectExemption)
    — this is the external half: confirm the deployed endpoint itself never
    3xx's a plain request, whatever the redirect config resolves to in prod.
    """

    @pytest.mark.parametrize("path", ["/health/", "/health/ready/"])
    def test_health_paths_do_not_redirect(self, api_client, path):
        resp = api_client.get(_health_url(path), timeout=10, allow_redirects=False)
        _skip_if_not_deployed(resp)
        assert resp.status_code not in (301, 302, 307, 308), (
            f"{path} returned a redirect ({resp.status_code}) — a container "
            "healthcheck would misread this as healthy."
        )
