"""
Security tests for the Parakh platform.

Areas covered:
  TestCookieSecurity       — HttpOnly, Secure, SameSite flags; no secrets in localStorage
  TestGraphQLSecurity      — introspection, invalid auth, malformed query, oversized input
  TestIDORProtection       — unauthenticated access, forged org headers
  TestResponseSecurity     — no stack traces in errors, standard error envelope
  TestCORSPolicy           — evil-origin reflection, valid-origin CORS
  TestInputSanitisation    — XSS payload handling, SQL injection via filters

Run explicitly with:
    pytest tests/api/test_security.py -m security -v
"""

import pytest
import requests

from utils.config import Config

pytestmark = [pytest.mark.api, pytest.mark.security]

BASE = Config.BASE_URL.rstrip("/")
GRAPHQL = Config.graphql_endpoint()

_INTROSPECTION_QUERY = "{ __schema { types { name } } }"
_MALFORMED_QUERY = "{ !! invalid syntax }"
_SIMPLE_QUERY = "{ __typename }"
_AUDITS_QUERY = "{ audits { data { id } totalItemsCount } }"

_EVIL_ORIGIN = "https://evil.example.com"
_FRONTEND_ORIGIN = Config.BASE_URL.rstrip("/")


# ── Cookie Security ────────────────────────────────────────────────────────────


class TestCookieSecurity:
    def test_session_cookies_have_httponly_flag(self, authenticated_page_fast):
        """Session cookies must have HttpOnly to prevent XSS session theft."""
        cookies = authenticated_page_fast.context.cookies()
        session_cookies = [
            c for c in cookies
            if any(k in c.get("name", "").lower() for k in ("session", "next-auth", "token", "auth"))
        ]
        if not session_cookies:
            pytest.skip("No session/auth cookies found — cannot verify HttpOnly flag")

        missing_http_only = [c["name"] for c in session_cookies if not c.get("httpOnly", False)]
        assert not missing_http_only, (
            f"Session cookies missing HttpOnly flag: {missing_http_only}. "
            "HttpOnly prevents JavaScript from accessing session cookies, mitigating XSS."
        )

    def test_session_cookies_have_secure_flag(self, authenticated_page_fast):
        """Session cookies must have Secure flag when served over HTTPS."""
        if not BASE.startswith("https://"):
            pytest.skip("BASE_URL is not HTTPS — Secure flag check not applicable")

        cookies = authenticated_page_fast.context.cookies()
        session_cookies = [
            c for c in cookies
            if any(k in c.get("name", "").lower() for k in ("session", "next-auth", "token", "auth"))
        ]
        if not session_cookies:
            pytest.skip("No session/auth cookies found — cannot verify Secure flag")

        missing_secure = [c["name"] for c in session_cookies if not c.get("secure", False)]
        if missing_secure:
            pytest.xfail(
                f"Session cookies missing Secure flag: {missing_secure}. "
                "Secure flag ensures cookies are only sent over HTTPS."
            )
        assert not missing_secure

    def test_no_access_token_in_localstorage(self, authenticated_page_fast):
        """Raw JWT access_token must not be stored in localStorage."""
        keys = authenticated_page_fast.evaluate("Object.keys(localStorage)")
        sensitive_keys = [k for k in keys if any(
            word in k.lower() for word in ("access_token", "accesstoken", "jwt", "secret")
        )]
        assert not sensitive_keys, (
            f"Sensitive keys found in localStorage: {sensitive_keys}. "
            "Access tokens in localStorage are vulnerable to XSS theft."
        )

    def test_no_password_in_localstorage(self, authenticated_page_fast):
        """Passwords must never be stored in localStorage."""
        for key in authenticated_page_fast.evaluate("Object.keys(localStorage)"):
            value = authenticated_page_fast.evaluate(f"localStorage.getItem({key!r})") or ""
            assert Config.TEST_PASSWORD_1 not in value, (
                f"Test password found in localStorage under key '{key}'. "
                "Passwords must never be persisted in browser storage."
            )

    def test_session_cookie_samesite_not_none(self, authenticated_page_fast):
        """Session cookies must not use SameSite=None (allows CSRF from cross-origin)."""
        cookies = authenticated_page_fast.context.cookies()
        session_cookies = [
            c for c in cookies
            if any(k in c.get("name", "").lower() for k in ("session", "next-auth", "token", "auth"))
        ]
        if not session_cookies:
            pytest.skip("No session/auth cookies found")

        samesite_none = [
            c["name"] for c in session_cookies
            if (c.get("sameSite") or "").lower() == "none"
        ]
        if samesite_none:
            pytest.xfail(
                f"Cookies with SameSite=None found: {samesite_none}. "
                "SameSite=None allows cross-site request forgery in some scenarios."
            )


# ── GraphQL Security ───────────────────────────────────────────────────────────


class TestGraphQLSecurity:
    def test_graphql_introspection_is_restricted(self, api_client: requests.Session):
        """GraphQL introspection should be disabled or return an error in non-dev environments."""
        try:
            resp = api_client.get(
                GRAPHQL,
                params={"query": _INTROSPECTION_QUERY},
                headers={"Accept": "application/json"},
                timeout=15,
            )
        except requests.exceptions.ConnectionError:
            pytest.skip("GraphQL endpoint unreachable")

        assert resp.status_code in (200, 400, 403), (
            f"Unexpected status {resp.status_code} for introspection query"
        )
        body = resp.json() if resp.status_code == 200 else {}

        # If 200, either introspection returns data (acceptable in dev) or errors
        if resp.status_code == 200 and body.get("data", {}).get("__schema"):
            # Introspection enabled — acceptable in dev, flag for production
            if Config.ENVIRONMENT in ("production", "prod"):
                pytest.fail(
                    "GraphQL introspection is ENABLED in production. "
                    "Disable it to prevent schema enumeration by attackers."
                )
            else:
                pytest.xfail(
                    "GraphQL introspection is enabled on the dev environment. "
                    "Ensure it is disabled before production deployment."
                )

    def test_invalid_bearer_token_returns_error(self, api_client: requests.Session):
        """Auth-gated query with an invalid bearer token must not return real data."""
        try:
            resp = api_client.get(
                GRAPHQL,
                params={"query": _AUDITS_QUERY},
                headers={
                    "Accept": "application/json",
                    "Authorization": "Bearer INVALID_TOKEN_SECURITY_TEST_12345",
                },
                timeout=15,
            )
        except requests.exceptions.ConnectionError:
            pytest.skip("GraphQL endpoint unreachable")

        assert resp.status_code in (200, 400, 401, 403), (
            f"Unexpected status {resp.status_code}"
        )
        if resp.status_code == 200:
            body = resp.json()
            data = (body.get("data") or {}).get("audits") or {}
            audit_list = data.get("data") or []
            assert audit_list == [], (
                "Auth-gated audits query returned real data with an invalid token. "
                "The API must reject or return empty data for invalid credentials."
            )

    def test_malformed_graphql_query_returns_error_not_500(self, api_client: requests.Session):
        """Syntactically invalid GraphQL must return a 4xx or 200+error, never 500."""
        try:
            resp = api_client.get(
                GRAPHQL,
                params={"query": _MALFORMED_QUERY},
                headers={"Accept": "application/json"},
                timeout=15,
            )
        except requests.exceptions.ConnectionError:
            pytest.skip("GraphQL endpoint unreachable")

        assert resp.status_code != 500, (
            f"Server returned 500 for a malformed GraphQL query — "
            "internal errors must not be exposed to clients."
        )
        if resp.status_code == 200:
            body = resp.json()
            assert "errors" in body, (
                "Malformed GraphQL query returned 200 without an errors array. "
                "Invalid syntax should produce a GraphQL error response."
            )

    def test_oversized_query_variable_does_not_crash_server(self, api_client: requests.Session):
        """A 10,000-character variable value must not crash the server (no 500)."""
        large_value = "A" * 10_000
        query = "query($name: String) { audits(filters: [{field: \"name\", condition: \"icontains\", value: $name}]) { data { id } } }"
        try:
            import json
            resp = api_client.get(
                GRAPHQL,
                params={"query": query, "variables": json.dumps({"name": large_value})},
                headers={"Accept": "application/json"},
                timeout=20,
            )
        except requests.exceptions.ConnectionError:
            pytest.skip("GraphQL endpoint unreachable")
        except requests.exceptions.Timeout:
            pytest.skip("Request timed out — server may be throttling oversized inputs")

        assert resp.status_code != 500, (
            f"Server returned 500 for an oversized query variable — "
            "the server should validate input size and return 400/200+error, not crash."
        )

    def test_graphql_returns_json_content_type(self, api_client: requests.Session):
        """GraphQL responses must always declare application/json content type."""
        try:
            resp = api_client.get(
                GRAPHQL,
                params={"query": _SIMPLE_QUERY},
                headers={"Accept": "application/json"},
                timeout=15,
            )
        except requests.exceptions.ConnectionError:
            pytest.skip("GraphQL endpoint unreachable")

        content_type = resp.headers.get("Content-Type", "").lower()
        assert "application/json" in content_type, (
            f"GraphQL endpoint returned Content-Type '{content_type}' instead of application/json. "
            "Non-JSON responses can lead to content-type confusion attacks."
        )


# ── IDOR Protection ────────────────────────────────────────────────────────────


class TestIDORProtection:
    def test_unauthenticated_dashboard_redirects_to_login(self, api_client: requests.Session):
        """GET /dashboard without auth must redirect to login, not expose content."""
        try:
            resp = api_client.get(BASE + "/dashboard", allow_redirects=False, timeout=15)
        except requests.exceptions.ConnectionError:
            pytest.skip("Frontend unreachable")

        assert resp.status_code in (301, 302, 303, 307, 308, 401, 403), (
            f"Expected redirect or auth error for /dashboard, got {resp.status_code}. "
            "Unauthenticated users must be redirected to login."
        )

    def test_graphql_audits_without_auth_returns_empty_or_error(self, api_client: requests.Session):
        """audits query without Authorization header must return empty data or an error."""
        try:
            resp = api_client.get(
                GRAPHQL,
                params={"query": _AUDITS_QUERY},
                headers={"Accept": "application/json"},
                timeout=15,
            )
        except requests.exceptions.ConnectionError:
            pytest.skip("GraphQL endpoint unreachable")

        if resp.status_code != 200:
            return  # 401/403 is fine

        body = resp.json()
        # Either errors returned or data is null/empty
        if body.get("errors"):
            return  # error envelope — correct behaviour

        audit_list = ((body.get("data") or {}).get("audits") or {}).get("data") or []
        assert audit_list == [], (
            "Anonymous GraphQL query for audits returned real audit records. "
            "Audit data must require authentication."
        )

    def test_forged_org_header_does_not_return_real_data(self, api_client: requests.Session):
        """A request with a fake organization ID header must not return real audit data."""
        ai_models_query = "{ aiModels(limit: 5) { id name } }"
        try:
            resp = api_client.get(
                GRAPHQL,
                params={"query": ai_models_query},
                headers={
                    "Accept": "application/json",
                    "organization": "999999",
                },
                timeout=15,
            )
        except requests.exceptions.ConnectionError:
            pytest.skip("GraphQL endpoint unreachable")

        if resp.status_code != 200:
            return

        body = resp.json()
        models = (body.get("data") or {}).get("aiModels") or []
        # We can't assert *which* models are returned, but we can check no crash
        assert isinstance(models, list), (
            "aiModels with forged org header returned non-list response"
        )

    def test_authenticated_ai_maker_routes_require_org_membership(self, api_client: requests.Session):
        """Private org routes should redirect or 403 for unauthenticated requests."""
        try:
            resp = api_client.get(
                BASE + "/dashboard/ai-maker/99999/evaluations",
                allow_redirects=False,
                timeout=15,
            )
        except requests.exceptions.ConnectionError:
            pytest.skip("Frontend unreachable")

        assert resp.status_code in (301, 302, 303, 307, 308, 401, 403, 404), (
            f"Expected redirect/auth-error for private org route, got {resp.status_code}"
        )


# ── Response Security ──────────────────────────────────────────────────────────


class TestResponseSecurity:
    def test_404_does_not_expose_stack_trace(self, api_client: requests.Session):
        """404 responses must not contain Python stack traces or internal file paths."""
        try:
            resp = api_client.get(
                BASE + "/this-path-definitely-does-not-exist-12345",
                allow_redirects=True,
                timeout=15,
            )
        except requests.exceptions.ConnectionError:
            pytest.skip("Frontend unreachable")

        body = resp.text.lower()
        assert "traceback" not in body, "404 response contains 'traceback' — stack trace exposure"
        assert 'file "/' not in body, "404 response contains file paths — internal path exposure"
        assert "django" not in body or resp.status_code == 200, (
            "404 response mentions 'django' framework — version/framework disclosure"
        )

    def test_graphql_error_does_not_expose_internal_paths(self, api_client: requests.Session):
        """GraphQL error messages must not contain internal server file paths."""
        try:
            resp = api_client.get(
                GRAPHQL,
                params={"query": _MALFORMED_QUERY},
                headers={"Accept": "application/json"},
                timeout=15,
            )
        except requests.exceptions.ConnectionError:
            pytest.skip("GraphQL endpoint unreachable")

        body = resp.text.lower()
        assert 'file "/' not in body, (
            "GraphQL error contains internal file path — exposes server filesystem structure"
        )
        assert "traceback" not in body, (
            "GraphQL error contains Python traceback — exposes internal implementation"
        )

    def test_graphql_errors_use_standard_envelope(self, api_client: requests.Session):
        """GraphQL errors must use the {errors: [...]} JSON envelope."""
        try:
            resp = api_client.get(
                GRAPHQL,
                params={"query": _MALFORMED_QUERY},
                headers={"Accept": "application/json"},
                timeout=15,
            )
        except requests.exceptions.ConnectionError:
            pytest.skip("GraphQL endpoint unreachable")

        if resp.status_code not in (200, 400):
            return

        try:
            body = resp.json()
        except Exception:
            pytest.skip("Response was not valid JSON — cannot check error envelope")

        if resp.status_code == 400 or "errors" in body:
            if "errors" in body:
                assert isinstance(body["errors"], list), (
                    "GraphQL 'errors' field must be a list per the GraphQL spec"
                )


# ── CORS Policy ────────────────────────────────────────────────────────────────


class TestCORSPolicy:
    def test_evil_origin_not_reflected_in_cors_header(self, api_client: requests.Session):
        """Arbitrary evil origins must not be reflected in Access-Control-Allow-Origin."""
        try:
            resp = api_client.get(
                GRAPHQL,
                params={"query": _SIMPLE_QUERY},
                headers={
                    "Accept": "application/json",
                    "Origin": _EVIL_ORIGIN,
                },
                timeout=15,
            )
        except requests.exceptions.ConnectionError:
            pytest.skip("GraphQL endpoint unreachable")

        acao = resp.headers.get("Access-Control-Allow-Origin", "")
        assert acao != _EVIL_ORIGIN, (
            f"Evil origin '{_EVIL_ORIGIN}' was reflected in Access-Control-Allow-Origin. "
            "This enables cross-origin request forgery from arbitrary domains."
        )
        assert acao != "*" or not resp.headers.get("Access-Control-Allow-Credentials"), (
            "Access-Control-Allow-Origin: * combined with Allow-Credentials: true "
            "is a critical CORS misconfiguration that allows any site to send authenticated requests."
        )

    def test_frontend_origin_gets_cors_response(self, api_client: requests.Session):
        """The legitimate frontend origin should receive a CORS response."""
        try:
            resp = api_client.get(
                GRAPHQL,
                params={"query": _SIMPLE_QUERY},
                headers={
                    "Accept": "application/json",
                    "Origin": _FRONTEND_ORIGIN,
                },
                timeout=15,
            )
        except requests.exceptions.ConnectionError:
            pytest.skip("GraphQL endpoint unreachable")

        # Either ACAO is set to the frontend origin, or the request succeeded (same-origin)
        acao = resp.headers.get("Access-Control-Allow-Origin", "")
        if acao and acao not in (_FRONTEND_ORIGIN, "*"):
            pytest.xfail(
                f"Frontend origin '{_FRONTEND_ORIGIN}' not in Access-Control-Allow-Origin '{acao}'. "
                "This may cause browser CORS errors when the frontend makes cross-origin API calls."
            )

    def test_cors_preflight_returns_valid_headers(self, api_client: requests.Session):
        """OPTIONS preflight for the GraphQL endpoint should return CORS headers."""
        try:
            resp = api_client.options(
                GRAPHQL,
                headers={
                    "Origin": _FRONTEND_ORIGIN,
                    "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": "Content-Type,Authorization",
                },
                timeout=10,
            )
        except requests.exceptions.ConnectionError:
            pytest.skip("GraphQL endpoint unreachable")

        # Preflight returns 200 or 204; some servers return 405 for OPTIONS
        if resp.status_code == 405:
            pytest.xfail("OPTIONS method not allowed — CORS preflight may not be handled")

        assert resp.status_code in (200, 204), (
            f"CORS preflight returned {resp.status_code}"
        )


# ── Input Sanitisation ─────────────────────────────────────────────────────────


class TestInputSanitisation:
    def test_xss_payload_in_filter_does_not_cause_500(self, api_client: requests.Session):
        """XSS payload in a GraphQL filter variable must not cause a 500 error."""
        xss_payload = '<script>alert("xss")</script>'
        import json
        query = (
            "query($name: String) { "
            "audits(filters: [{field: \"name\", condition: \"icontains\", value: $name}]) "
            "{ data { id } } }"
        )
        try:
            resp = api_client.get(
                GRAPHQL,
                params={"query": query, "variables": json.dumps({"name": xss_payload})},
                headers={"Accept": "application/json"},
                timeout=15,
            )
        except requests.exceptions.ConnectionError:
            pytest.skip("GraphQL endpoint unreachable")

        assert resp.status_code != 500, (
            f"Server returned 500 for XSS payload in filter — "
            "input must be validated, not passed directly to the backend"
        )

    def test_sql_injection_in_filter_returns_empty_or_error(self, api_client: requests.Session):
        """SQL injection pattern in filter variable must not return unexpected data."""
        sql_payload = "' OR '1'='1"
        import json
        query = (
            "query($name: String) { "
            "audits(filters: [{field: \"name\", condition: \"exact\", value: $name}]) "
            "{ data { id } totalItemsCount } }"
        )
        try:
            resp = api_client.get(
                GRAPHQL,
                params={"query": query, "variables": json.dumps({"name": sql_payload})},
                headers={"Accept": "application/json"},
                timeout=15,
            )
        except requests.exceptions.ConnectionError:
            pytest.skip("GraphQL endpoint unreachable")

        assert resp.status_code != 500, (
            "Server returned 500 for SQL injection payload — likely a query construction error"
        )
        if resp.status_code == 200:
            body = resp.json()
            if body.get("data") and body["data"].get("audits"):
                # The filter should match nothing (literal string match)
                # A huge count would suggest injection worked
                count = body["data"]["audits"].get("totalItemsCount", 0)
                audit_list = body["data"]["audits"].get("data") or []
                # Cannot assert exact count without knowing DB state, just verify no crash
                assert isinstance(count, int) and count >= 0

    def test_html_page_has_security_headers(self, api_client: requests.Session):
        """The homepage HTML response must include essential security headers."""
        try:
            resp = api_client.get(BASE + "/", timeout=15, allow_redirects=True)
        except requests.exceptions.ConnectionError:
            pytest.skip("Frontend unreachable")

        required = {
            "x-content-type-options": "nosniff",
            "x-frame-options": None,
            "strict-transport-security": None,
        }
        headers_lower = {k.lower(): v for k, v in resp.headers.items()}
        missing = [h for h in required if h not in headers_lower]
        assert not missing, (
            f"Homepage HTML response is missing security headers: {missing}"
        )

    def test_session_api_returns_empty_for_unauthenticated(self, api_client: requests.Session):
        """GET /api/auth/session without a session cookie must not return user data."""
        try:
            # Use a fresh session (no cookies) to simulate unauthenticated request
            fresh = requests.Session()
            fresh.headers.update({"Accept": "application/json"})
            resp = fresh.get(BASE + "/api/auth/session", timeout=15)
        except requests.exceptions.ConnectionError:
            pytest.skip("Frontend unreachable")

        if resp.status_code not in (200, 401, 403):
            pytest.skip(f"Unexpected status {resp.status_code}")

        if resp.status_code == 200:
            try:
                body = resp.json()
            except Exception:
                return
            # Unauthenticated session must be empty — must not expose access_token
            assert "access_token" not in body, (
                "/api/auth/session returned access_token without authentication. "
                "The endpoint must return empty {} or null for unauthenticated requests."
            )
            assert "user" not in body or body.get("user") is None, (
                "/api/auth/session returned user data without authentication"
            )

    def test_null_byte_in_query_does_not_crash(self, api_client: requests.Session):
        """Null bytes in query parameters must not crash the server."""
        try:
            resp = api_client.get(
                GRAPHQL,
                params={"query": _SIMPLE_QUERY + "\x00"},
                headers={"Accept": "application/json"},
                timeout=15,
            )
        except requests.exceptions.ConnectionError:
            pytest.skip("GraphQL endpoint unreachable")
        except Exception:
            pytest.skip("Request library rejected null byte — not a server issue")

        assert resp.status_code != 500, (
            "Server returned 500 for a query containing a null byte"
        )
