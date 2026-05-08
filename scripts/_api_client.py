"""
Shared auth + GraphQL helpers for scripts/ tools.

All scripts in scripts/ use the same approach: drive a headless Playwright
login (using TEST_EMAIL_1 / TEST_PASSWORD_1 from .env), read the access
token from the NextAuth /api/auth/session endpoint, then call the backend
GraphQL endpoint directly via requests.

Usage:
    from _api_client import (
        get_access_token, graphql, BASE_URL, GRAPHQL_URL, EMAIL,
    )

    token = get_access_token()
    data = graphql(token, org_id="1", query=MY_QUERY, variables={...})
"""

from __future__ import annotations

import os
from pathlib import Path

import requests
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

REPO_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(REPO_ROOT / ".env")

BASE_URL = os.environ.get("BASE_URL", "https://dev.parakh.civicdataspace.in").rstrip("/")
GRAPHQL_URL = os.environ.get(
    "GRAPHQL_URL", "https://dev.api.parakh.civicdataspace.in/graphql/"
)
EMAIL = os.environ.get("TEST_EMAIL_1", "")
PASSWORD = os.environ.get("TEST_PASSWORD_1", "")


def _require_creds() -> None:
    if not EMAIL or not PASSWORD:
        raise SystemExit(
            "TEST_EMAIL_1 / TEST_PASSWORD_1 must be set in .env to run this script."
        )


def get_access_token(headless: bool = True) -> str:
    """Log in via the UI and return the Keycloak access token from NextAuth session."""
    _require_creds()
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=headless)
        context = browser.new_context()
        page = context.new_page()

        page.goto(BASE_URL, wait_until="domcontentloaded")
        page.get_by_role("button", name="LOGIN / SIGN UP").click()
        page.wait_for_url("**/openid-connect/auth*", timeout=15_000)
        page.get_by_role("textbox", name="Email").fill(EMAIL)
        page.get_by_role("textbox", name="Password").fill(PASSWORD)
        page.get_by_role("button", name="Sign In").click()
        page.wait_for_url(f"{BASE_URL}/**", timeout=20_000)
        page.reload(wait_until="domcontentloaded")

        session = page.evaluate(
            "async () => fetch('/api/auth/session').then(r => r.json())"
        )
        browser.close()

        token = session.get("access_token")
        if not token:
            raise RuntimeError(
                f"No access_token in session payload: keys={list(session)}"
            )
        return token


def graphql(token: str, org_id: str, query: str, variables: dict | None = None) -> dict:
    """POST a GraphQL operation. Raises on HTTP errors or `errors` in the response."""
    res = requests.post(
        GRAPHQL_URL,
        headers={
            "authorization": f"Bearer {token}",
            "organization": str(org_id),
            "content-type": "application/json",
        },
        json={"query": query, "variables": variables or {}},
        timeout=30,
    )
    res.raise_for_status()
    payload = res.json()
    if payload.get("errors"):
        raise RuntimeError(f"GraphQL errors: {payload['errors']}")
    return payload["data"]


# ── Reusable queries / mutations ──────────────────────────────────────────────

LIST_AUDITS_QUERY = """
query GetAudits($status: String, $limit: Int) {
  audits(status: $status, limit: $limit) {
    id
    name
    status
    evaluationMode
    createdAt
  }
}
"""

CANCEL_MUTATION = """
mutation CancelAudit($input: UpdateAuditInput!) {
  updateAudit(input: $input) {
    success
    message
    audit { id status }
  }
}
"""

REQUEST_AUDIT_MUTATION = """
mutation RequestAudit($input: RequestAuditInput!) {
  requestAudit(input: $input) {
    success
    message
    audit { id name status evaluationMode }
  }
}
"""

CREATE_BLANK_AUDIT_MUTATION = """
mutation CreateBlankAudit($input: CreateBlankAuditInput!) {
  createBlankAudit(input: $input) {
    success
    message
    audit { id name status evaluationMode }
  }
}
"""

LIST_AI_MODELS_QUERY = """
query GetAIModels($limit: Int) {
  aiModels(limit: $limit) {
    id
    name
    provider
  }
}
"""

MY_ORGS_QUERY = """
query MyOrgs {
  myOrganizations {
    id
    name
    slug
  }
}
"""


def find_org_id_by_slug(token: str, slug: str) -> str | None:
    """Resolve a slug to its numeric org id via myOrganizations. Returns None if not found.

    Notes
    -----
    `myOrganizations` is org-scoped on the backend, but actually returns the
    full set the user belongs to regardless of the `organization` header — so
    we send "1" as a placeholder and filter the result client-side.
    """
    data = graphql(token, "1", MY_ORGS_QUERY, {})
    for org in data.get("myOrganizations") or []:
        if org.get("slug") == slug:
            return str(org["id"])
    return None
