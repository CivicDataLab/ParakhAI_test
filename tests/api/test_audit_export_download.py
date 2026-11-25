"""
Contract tests for the evaluation data export REST endpoint.

ParakhAI-Backend#147 adds `GET /api/audits/<audit_id>/export/download/`, a
streamed ZIP of the full evaluation data (overview + per-result JSON),
alongside the existing PDF report download. Both views share one
authentication/access-check base class (`_AuditSummaryView`), so the new
route's auth contract is identical to the pre-existing report endpoint:

- No `Authorization` header -> 401 `{"detail": "Authentication required."}`
  (checked before the audit/summary lookup, so this holds for any audit id).
- Non-GET verbs -> 405 (plain `django.views.View`, only `get` is defined).

This environment has no test credentials, so only the unauthenticated and
method-not-allowed contract can be executed here; the 403 (wrong org) / 404
(no summary yet) / 200 (success) branches need `TEST_EMAIL_1` and are not
covered by this file. See the PR body for what a human run should check.

Marked `api` + `regression` (not `smoke`): ParakhAI-Backend's prod deploy
gate (`deploy-parakh-api.yml`) runs ParakhAI_test's `run-smoke.yml` with
`marker_expr: "api and smoke"` against the *prod* backend, which is still
pre-#147 code (the route doesn't exist there yet - confirmed 404 on
api.parakh.civicdataspace.in). Carrying `smoke` would fail that gate on the
very next prod deploy of an unrelated change. Once #147 reaches
ParakhAI-Backend `main`, `smoke` can be added so this also covers prod.
"""

from urllib.parse import urlparse

import pytest

from utils.config import Config

pytestmark = [pytest.mark.api, pytest.mark.regression]

# The export endpoint lives on the backend host, same as GraphQL -- derive it
# the same way test_health_endpoints.py does, rather than assuming BASE_URL.
_BACKEND_ORIGIN = "{0.scheme}://{0.netloc}".format(urlparse(Config.graphql_endpoint()))


def _export_url(audit_id) -> str:
    return _BACKEND_ORIGIN.rstrip("/") + f"/api/audits/{audit_id}/export/download/"


class TestAuditExportDownloadAuth:
    """Unauthenticated access to the export endpoint is refused, not leaked."""

    def test_no_auth_header_returns_401(self, api_client):
        resp = api_client.get(_export_url(1), timeout=15)
        assert resp.status_code == 401, (
            f"expected 401 for an unauthenticated export download, got "
            f"{resp.status_code}: {resp.text[:300]}"
        )
        body = resp.json()
        assert body.get("detail") == "Authentication required."

    def test_no_auth_header_returns_401_for_any_audit_id(self, api_client):
        # The auth check in _AuditSummaryView.get() runs before the audit
        # lookup, so a nonexistent id must still 401, not 404 -- an id-based
        # branch here would mean the auth check moved after the lookup.
        resp = api_client.get(_export_url(999999999), timeout=15)
        assert resp.status_code == 401, (
            f"expected 401 regardless of audit id when unauthenticated, got "
            f"{resp.status_code}: {resp.text[:300]}"
        )

    def test_post_not_allowed(self, api_client):
        resp = api_client.post(_export_url(1), timeout=15)
        assert resp.status_code == 405, (
            f"expected 405 for POST (view defines only get()), got "
            f"{resp.status_code}: {resp.text[:300]}"
        )
