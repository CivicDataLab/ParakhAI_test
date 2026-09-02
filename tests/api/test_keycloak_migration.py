"""
Keycloak migration regression coverage — ParakhAI side.

Every CivicDataLab product moved off `opub-kc.civicdatalab.in`, which served
each realm under an `/auth` path prefix, onto `auth.civicdatalab.in`, which
serves from the domain root. Two distinct things changed: the host AND the
disappearance of the `/auth` segment.

Two failures this guards, both of which happened in production:

1. ParakhAI's sign-in must hand users to the NEW issuer. A stale issuer mints
   tokens the CivicDataSpace backend rejects.

2. ParakhAI's backend does not verify Keycloak tokens itself. Its
   `DataSpaceAuthMiddleware` forwards the user's bearer token to the
   CivicDataSpace backend (`/api/auth/keycloak/login/`) via `dataspace_sdk`
   and adopts the user it returns. When CivicDataSpace moved to the new
   Keycloak and ParakhAI had not, every such call failed with
   `DataSpaceAuthError: Invalid or expired token` — ParakhAI broke because a
   *different application's* identity provider moved. Separately, the SDK
   hardcoded `/auth` into its Keycloak URLs and could not reach a root-path
   Keycloak at all (fixed in dataspace-sdk 0.5.5).

Why this file does NOT assert on a GraphQL query
------------------------------------------------
The obvious test — call `{ myAssignments { id } }` authenticated and check it
succeeds — is worthless here. Verified against dev: the SAME query
unauthenticated returns the SAME body, `{"data": {"myAssignments": []}}`.
`DataSpaceAuthMiddleware` swallows a rejected/expired token and silently sets
`request.user = AnonymousUser()`, returning HTTP 200 with empty data and no
error. `audits` and `auditorAssignments` behave identically. So no GraphQL
response distinguishes "authenticated" from "silently anonymous", and any
assertion built on one would pass even with authentication completely broken.

Instead, test 2 exercises the cross-application handoff directly: take a real
Keycloak token and present it to the CivicDataSpace endpoint the middleware
actually calls. That returns 401 when the issuers disagree, which is exactly
the regression, with no ambiguity.

Markers: api, regression (+ auth for the test needing a real login).
"""

import os
from urllib.parse import unquote

import pytest
import requests

from utils.config import Config

pytestmark = [pytest.mark.api, pytest.mark.regression]

KEYCLOAK_BASE = "https://auth.civicdatalab.in"
KEYCLOAK_REALM = "DataSpace"
EXPECTED_ISSUER = f"{KEYCLOAK_BASE}/realms/{KEYCLOAK_REALM}"
AUTH_ENDPOINT = f"{EXPECTED_ISSUER}/protocol/openid-connect/auth"
EXPECTED_CLIENT_ID = "dataspace"

# The endpoint DataSpaceAuthMiddleware calls through dataspace_sdk.
CDS_BASE = os.getenv("CDS_URL", "https://dev.civicdataspace.in").rstrip("/")
CDS_API_BASE = CDS_BASE.replace("://dev.", "://dev.api.", 1)
CDS_KEYCLOAK_LOGIN = f"{CDS_API_BASE}/api/auth/keycloak/login/"

# Dev nginx 403s non-browser User-Agents.
BROWSER_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
TIMEOUT = 30


def _browser_session() -> requests.Session:
    s = requests.Session()
    s.headers["User-Agent"] = BROWSER_UA
    return s


class TestSignInIssuer:
    """ParakhAI must hand sign-in to the migrated Keycloak."""

    def test_signin_redirects_to_migrated_issuer(self):
        """/api/auth/signin/keycloak must 302 to the new issuer, not opub-kc."""
        base = Config.BASE_URL.rstrip("/")
        session = _browser_session()

        csrf = session.get(f"{base}/api/auth/csrf", timeout=TIMEOUT)
        assert csrf.status_code == 200, (
            f"CSRF endpoint {base}/api/auth/csrf returned {csrf.status_code}: "
            f"{csrf.text[:300]}"
        )
        token = csrf.json().get("csrfToken")
        assert token, f"No csrfToken in {csrf.text[:300]}"

        resp = session.post(
            f"{base}/api/auth/signin/keycloak",
            data={"csrfToken": token, "callbackUrl": base},
            allow_redirects=False,
            timeout=TIMEOUT,
        )
        assert resp.status_code == 302, (
            f"Expected 302 to Keycloak from {base}/api/auth/signin/keycloak, "
            f"got {resp.status_code}: {resp.text[:300]}"
        )

        location = resp.headers.get("Location", "")
        assert AUTH_ENDPOINT in location, (
            f"Sign-in did not hand off to the migrated authorization endpoint "
            f"{AUTH_ENDPOINT}. Location: {location!r}"
        )
        assert f"client_id={EXPECTED_CLIENT_ID}" in location, (
            f"Expected client_id={EXPECTED_CLIENT_ID}. Location: {location!r}"
        )
        assert f"{base}/api/auth/callback/keycloak" in unquote(location), (
            f"Expected redirect_uri back to {base}/api/auth/callback/keycloak. "
            f"Location: {location!r}"
        )

    def test_signin_does_not_use_decommissioned_keycloak(self):
        """The old host and its /auth path must not appear in the hand-off."""
        base = Config.BASE_URL.rstrip("/")
        session = _browser_session()

        csrf = session.get(f"{base}/api/auth/csrf", timeout=TIMEOUT)
        token = csrf.json().get("csrfToken")
        resp = session.post(
            f"{base}/api/auth/signin/keycloak",
            data={"csrfToken": token, "callbackUrl": base},
            allow_redirects=False,
            timeout=TIMEOUT,
        )
        location = resp.headers.get("Location", "")

        assert "opub-kc" not in location, (
            "Sign-in still points at the decommissioned Keycloak host "
            f"(opub-kc). Location: {location!r}"
        )
        assert "/auth/realms/" not in location, (
            "Sign-in uses the pre-migration /auth/realms/ path; Keycloak now "
            f"serves realms from the domain root. Location: {location!r}"
        )


class TestCrossApplicationTokenHandoff:
    """
    The ParakhAI -> CivicDataSpace token exchange that DataSpaceAuthMiddleware
    depends on. This is the path that broke in production (ParakhAI-Backend#107).
    """

    pytestmark = [pytest.mark.api, pytest.mark.regression, pytest.mark.auth]

    def test_parakh_token_is_accepted_by_civicdataspace(self, authenticated_page):
        """
        A token minted for a logged-in ParakhAI user must be accepted by the
        CivicDataSpace backend endpoint the middleware forwards it to.

        A 401 here is the exact production regression: the two applications
        trusting different issuers. Asserted directly rather than through a
        GraphQL response, because the middleware degrades to AnonymousUser
        silently and every GraphQL query returns 200 with empty data either
        way (see module docstring).
        """
        session_blob = authenticated_page.evaluate(
            "async () => await (await fetch('/api/auth/session')).json()"
        )
        access_token = (session_blob or {}).get("access_token")
        if not access_token:
            pytest.skip(
                "No access_token on the NextAuth session — login did not "
                "complete, so there is no token to exchange."
            )

        resp = _browser_session().post(
            CDS_KEYCLOAK_LOGIN,
            json={"token": access_token},
            timeout=TIMEOUT,
        )

        assert resp.status_code != 401, (
            f"CivicDataSpace rejected a live ParakhAI token at "
            f"{CDS_KEYCLOAK_LOGIN} (401). This is the cross-application issuer "
            "mismatch from ParakhAI-Backend#107: ParakhAI's "
            "DataSpaceAuthMiddleware forwards user tokens here, so every "
            "authenticated ParakhAI request degrades to anonymous when this "
            f"fails. Body: {resp.text[:300]}"
        )
        assert resp.status_code == 200, (
            f"Token exchange at {CDS_KEYCLOAK_LOGIN} returned "
            f"{resp.status_code}: {resp.text[:300]}"
        )

        body = resp.json()
        assert body.get("access"), (
            "Token exchange succeeded but returned no 'access' token, so "
            f"DataSpaceAuthMiddleware could not adopt a user. Body: {resp.text[:300]}"
        )
