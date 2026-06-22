"""
Database health and connection pool tests.

MCP exploration (2026-06-22) revealed that the dev PostgreSQL instance
(port 5433) hits "FATAL: sorry, too many clients already" under concurrent
load from 3 pytest workers + 1 browser session. These tests detect that
condition via GraphQL response analysis.

Markers: api (no browser needed)
"""

import concurrent.futures

import pytest
import requests

from utils.config import Config

pytestmark = [pytest.mark.api, pytest.mark.performance]

GRAPHQL = Config.graphql_endpoint()
_LIGHT_QUERY = "{ __typename }"
_AUDIT_QUERY = (
    "query { audits(limit: 1) { data { id status } totalItemsCount } }"
)


class TestDatabaseConnectionPool:
    """GraphQL API must remain healthy under moderate concurrent load."""

    def _graphql_get(self, query: str, token: str | None = None) -> requests.Response:
        headers: dict = {"Accept": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return requests.get(
            GRAPHQL,
            params={"query": query},
            headers=headers,
            timeout=20,
        )

    def test_graphql_responds_under_sequential_load(self, graphql_client):
        """10 sequential GraphQL requests must all succeed without DB errors."""
        db_errors = []
        for i in range(10):
            try:
                body = graphql_client(_LIGHT_QUERY)
                errors = body.get("errors") or []
                for err in errors:
                    msg = str(err.get("message", "")).lower()
                    if "too many clients" in msg or "connection" in msg:
                        db_errors.append(f"Request {i+1}: {msg}")
            except Exception as exc:
                db_errors.append(f"Request {i+1} exception: {exc}")

        assert not db_errors, (
            "DB connection pool errors detected under sequential load:\n"
            + "\n".join(db_errors)
        )

    def test_graphql_responds_under_5_concurrent_requests(self, graphql_client):
        """5 concurrent GraphQL requests (light introspection) must all return 200."""
        def _fetch(_):
            try:
                resp = requests.get(
                    GRAPHQL,
                    params={"query": _LIGHT_QUERY},
                    headers={"Accept": "application/json"},
                    timeout=20,
                )
                return resp.status_code, resp.text
            except Exception as exc:
                return 0, str(exc)

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
            results = list(pool.map(_fetch, range(5)))

        failures = [
            f"Request {i+1}: status={s}, body={b[:200]}"
            for i, (s, b) in enumerate(results)
            if s != 200 or "too many clients" in b
        ]
        assert not failures, (
            "Some of 5 concurrent requests failed — likely DB connection pool exhaustion:\n"
            + "\n".join(failures)
        )

    def test_graphql_error_response_does_not_contain_db_connection_error(self, graphql_client):
        """GraphQL error messages must not expose raw PostgreSQL connection errors."""
        try:
            body = graphql_client(_AUDIT_QUERY)
        except Exception:
            pytest.skip("GraphQL endpoint unreachable")

        errors = body.get("errors") or []
        for err in errors:
            msg = str(err.get("message", ""))
            assert "too many clients" not in msg.lower(), (
                f"GraphQL response exposes DB connection pool error: '{msg}'. "
                "This reveals internal infrastructure details and indicates pool exhaustion."
            )
            assert "port 5433" not in msg, (
                f"GraphQL response exposes internal DB port: '{msg}'"
            )
            assert "127.0.0.1" not in msg, (
                f"GraphQL response exposes internal DB host: '{msg}'"
            )

    def test_models_endpoint_does_not_return_503(self):
        """The /ai-models RSC prefetch must not return 503 (server overloaded)."""
        try:
            resp = requests.get(
                Config.url("/dashboard/ai-maker/1/ai-models"),
                params={"_rsc": "test"},
                headers={
                    "Accept": "text/x-component",
                    "User-Agent": "ParakhTestFramework/1.0",
                },
                timeout=20,
                allow_redirects=False,
            )
        except requests.exceptions.ConnectionError:
            pytest.skip("Frontend unreachable")

        assert resp.status_code != 503, (
            f"AI models RSC route returned 503 Service Unavailable. "
            "Backend is likely overloaded or the DB connection pool is exhausted."
        )

    def test_prompt_libraries_endpoint_does_not_return_503(self):
        """The /prompt-libraries RSC prefetch must not return 503."""
        try:
            resp = requests.get(
                Config.url("/dashboard/ai-maker/1/prompt-libraries"),
                params={"_rsc": "test"},
                headers={
                    "Accept": "text/x-component",
                    "User-Agent": "ParakhTestFramework/1.0",
                },
                timeout=20,
                allow_redirects=False,
            )
        except requests.exceptions.ConnectionError:
            pytest.skip("Frontend unreachable")

        assert resp.status_code != 503, (
            f"Prompt libraries RSC route returned 503 Service Unavailable."
        )
