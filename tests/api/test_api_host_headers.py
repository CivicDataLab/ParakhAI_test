"""
Response-header hygiene of the GraphQL API host (`dev.api.parakh...`).

`test_security.py` checks the *frontend* host (SEC-003 `Server` header is fixed
there). The API host sits behind a different nginx, so the same checks have to
be repeated against it.
"""

import pytest
import requests

from utils.config import Config

pytestmark = [pytest.mark.api, pytest.mark.security]

GRAPHQL = Config.graphql_endpoint()

# Headers where two different values in one response make browsers drop or
# pick a value unpredictably.
_SINGLE_VALUE_HEADERS = ("X-Frame-Options", "Referrer-Policy", "X-Content-Type-Options")


def _get_graphql(api_client: requests.Session) -> requests.Response:
    try:
        resp = api_client.get(
            GRAPHQL,
            params={"query": "{ __typename }"},
            headers={"Accept": "application/json"},
            timeout=15,
        )
    except requests.exceptions.ConnectionError:
        pytest.skip("GraphQL endpoint unreachable")
    assert resp.status_code == 200, f"GraphQL endpoint returned {resp.status_code}"
    return resp


class TestApiHostHeaders:
    @pytest.mark.xfail(
        strict=True,
        reason="App bug #36: API host Server header discloses 'nginx/1.24.0 (Ubuntu)' — see docs/app_bugs.md",
    )
    def test_server_header_does_not_disclose_version(self, api_client: requests.Session):
        """The API host's Server header carries no nginx version or OS string."""
        server = _get_graphql(api_client).headers.get("Server", "")
        assert "/" not in server and "ubuntu" not in server.lower(), (
            f"API host Server header discloses software details: '{server}'. "
            "Set 'server_tokens off;' in the API host's nginx config."
        )

    @pytest.mark.xfail(
        strict=True,
        reason="App bug #37: API host sends conflicting duplicate X-Frame-Options / Referrer-Policy headers — see docs/app_bugs.md",
    )
    def test_security_headers_are_not_duplicated_with_conflicting_values(
        self, api_client: requests.Session
    ):
        """Each of X-Frame-Options / Referrer-Policy / X-Content-Type-Options is sent
        with one consistent value (two layers each adding their own copy conflict)."""
        resp = _get_graphql(api_client)

        conflicts = {}
        for name in _SINGLE_VALUE_HEADERS:
            values = [v.strip() for v in resp.raw.headers.getlist(name)]
            if len(set(values)) > 1:
                conflicts[name] = values
        assert not conflicts, f"Conflicting duplicate response headers on {GRAPHQL}: {conflicts}"
