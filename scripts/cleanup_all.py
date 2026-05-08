#!/usr/bin/env python3
"""
Broader audit-cleanup tool that supersedes cleanup_drafts.py for routine use.

By default it cancels DRAFT audits (same as cleanup_drafts.py). With
--include-cancelled-older-than N it ALSO re-cancels CANCELLED audits older
than N days (no-op for the backend, but useful for keeping the test-run
ledger tidy for some workflows). Use --status to override status filter.

Usage:
    python scripts/cleanup_all.py                              # cancel DRAFTs in org 1
    python scripts/cleanup_all.py --org-id 5
    python scripts/cleanup_all.py --dry-run
    python scripts/cleanup_all.py --include-cancelled-older-than 7
    python scripts/cleanup_all.py --status DRAFT,RUNNING       # custom status set

Auth + GraphQL plumbing is in scripts/_api_client.py.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta, timezone

from _api_client import (
    CANCEL_MUTATION,
    EMAIL,
    LIST_AUDITS_QUERY,
    get_access_token,
    graphql,
)


def _parse_iso(s: str | None) -> datetime | None:
    """Parse an ISO-8601 timestamp; tolerate Zulu suffix and missing tz."""
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None


def _format_audit(a: dict) -> str:
    return (
        f"  - id={a['id']:<5} status={a['status']:<10} "
        f"mode={a['evaluationMode'] or '-':<10} {a['name']}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--org-id", default="1", help="Organization id (default: 1)")
    parser.add_argument(
        "--status",
        default="DRAFT",
        help="Comma-separated statuses to cancel (default: DRAFT)",
    )
    parser.add_argument(
        "--include-cancelled-older-than",
        type=int,
        default=None,
        metavar="DAYS",
        help="Also re-cancel CANCELLED audits whose createdAt is older than N days",
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

    if args.include_cancelled_older_than is not None:
        cutoff = datetime.now(timezone.utc) - timedelta(days=args.include_cancelled_older_than)
        old_cancelled = [
            a for a in audits
            if a["status"] == "CANCELLED"
            and (_parse_iso(a.get("createdAt")) or datetime.now(timezone.utc)) < cutoff
        ]
        # Avoid duplicates if --status already includes CANCELLED
        seen_ids = {a["id"] for a in targets}
        targets.extend(a for a in old_cancelled if a["id"] not in seen_ids)
        print(
            f"  + {len(old_cancelled)} CANCELLED audit(s) older than "
            f"{args.include_cancelled_older_than} days"
        )

    print(f"  total candidates: {len(targets)} (of {len(audits)} fetched)")
    if not targets:
        print("✓ Nothing to cancel.")
        return 0

    for a in targets:
        print(_format_audit(a))

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
