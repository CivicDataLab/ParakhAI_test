#!/usr/bin/env python3
"""
Cancel all DRAFT audits visible to TEST_USER_1 in a given organization.

The ParakhAI backend has no deleteAudit mutation; "cleanup" here means
calling updateAudit(status: "CANCELLED") on every audit currently in
status DRAFT, which removes them from the active drafts list.

Usage:
    python scripts/cleanup_drafts.py                 # org 1, dry-run off
    python scripts/cleanup_drafts.py --dry-run       # list, don't cancel
    python scripts/cleanup_drafts.py --org-id 5
    python scripts/cleanup_drafts.py --status DRAFT,CANCELLED  # also re-cancel

Auth: drives the same Playwright UI login the test framework uses
(TEST_EMAIL_1 / TEST_PASSWORD_1 from .env), then reads the access token
from /api/auth/session and calls GraphQL directly.
"""

from __future__ import annotations

import argparse
import os
import sys
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
EMAIL = os.environ["TEST_EMAIL_1"]
PASSWORD = os.environ["TEST_PASSWORD_1"]

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


def get_access_token(headless: bool = True) -> str:
    """Log in via the UI and return the Keycloak access token from the NextAuth session."""
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
        page.reload(wait_until="domcontentloaded")  # platform quirk — see CLAUDE.md

        session = page.evaluate(
            "async () => fetch('/api/auth/session').then(r => r.json())"
        )
        browser.close()

        token = session.get("access_token")
        if not token:
            raise RuntimeError(f"No access_token in session payload: keys={list(session)}")
        return token


def graphql(token: str, org_id: str, query: str, variables: dict) -> dict:
    res = requests.post(
        GRAPHQL_URL,
        headers={
            "authorization": f"Bearer {token}",
            "organization": str(org_id),
            "content-type": "application/json",
        },
        json={"query": query, "variables": variables},
        timeout=30,
    )
    res.raise_for_status()
    payload = res.json()
    if payload.get("errors"):
        raise RuntimeError(f"GraphQL errors: {payload['errors']}")
    return payload["data"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--org-id", default="1", help="Organization id (default: 1 = CivicDataLab)")
    parser.add_argument(
        "--status",
        default="DRAFT",
        help="Comma-separated statuses to cancel (default: DRAFT)",
    )
    parser.add_argument("--dry-run", action="store_true", help="List matches, don't cancel")
    parser.add_argument("--limit", type=int, default=500, help="Max audits to fetch (default: 500)")
    parser.add_argument("--headed", action="store_true", help="Show the login browser window")
    args = parser.parse_args()

    statuses = {s.strip().upper() for s in args.status.split(",") if s.strip()}

    print(f"→ Logging in as {EMAIL} ...", flush=True)
    token = get_access_token(headless=not args.headed)

    print(f"→ Fetching audits for org {args.org_id} (limit={args.limit}) ...", flush=True)
    data = graphql(
        token, args.org_id, LIST_AUDITS_QUERY, {"status": None, "limit": args.limit}
    )
    audits = data["audits"]
    targets = [a for a in audits if a["status"] in statuses]

    print(f"  fetched {len(audits)} audits, {len(targets)} match {sorted(statuses)}")
    if not targets:
        print("✓ Nothing to cancel.")
        return 0

    for a in targets:
        print(f"  - id={a['id']:<5} status={a['status']:<10} mode={a['evaluationMode'] or '-':<10} {a['name']}")

    if args.dry_run:
        print("\n(dry-run) no changes made.")
        return 0

    print(f"\n→ Cancelling {len(targets)} audit(s) ...", flush=True)
    failed = []
    for a in targets:
        try:
            res = graphql(
                token,
                args.org_id,
                CANCEL_MUTATION,
                {"input": {"auditId": a["id"], "status": "CANCELLED"}},
            )
            ok = res["updateAudit"]["success"]
            print(f"  {'✓' if ok else '✗'} id={a['id']} → {res['updateAudit']['message']}")
            if not ok:
                failed.append(a["id"])
        except Exception as e:
            print(f"  ✗ id={a['id']} → {e}")
            failed.append(a["id"])

    if failed:
        print(f"\n{len(failed)} failed: {failed}")
        return 1
    print(f"\n✓ Cancelled {len(targets)} audit(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
