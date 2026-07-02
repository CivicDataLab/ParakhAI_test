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

Auth + GraphQL plumbing is in scripts/_api_client.py.
"""

from __future__ import annotations

import argparse
import sys

from _api_client import (
    CANCEL_MUTATION,
    EMAIL,
    LIST_AUDITS_QUERY,
    get_access_token,
    graphql,
)


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
    # The API caps limit at 100 — page through with offset until args.limit
    # audits are fetched or the list is exhausted.
    audits: list = []
    offset = 0
    while len(audits) < args.limit:
        page_size = min(100, args.limit - len(audits))
        data = graphql(
            token,
            args.org_id,
            LIST_AUDITS_QUERY,
            {"limit": page_size, "offset": offset},
        )
        payload = data.get("audits") or {}
        page = payload.get("data") or []
        audits.extend(page)
        offset += len(page)
        total = payload.get("totalItemsCount") or 0
        if not page or offset >= total:
            break
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
