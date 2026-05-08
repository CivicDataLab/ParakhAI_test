#!/usr/bin/env python3
"""
Hard-reset the sandbox organization back to a clean state.

This is the destructive cleanup tool. It cancels EVERY audit in the
sandbox org regardless of status (DRAFT, RUNNING, COMPLETED, CANCELLED is
left alone). Use this between regression-write runs that exercise mutations.

The org is identified by SANDBOX_ORG_SLUG from .env (set the same value the
test framework's `sandbox_org` fixture expects). The script refuses to run
if SANDBOX_ORG_SLUG is unset, so it cannot accidentally fire against
production.

Confirmation: by default a y/N prompt is shown listing the targeted org and
the audit count. Skip the prompt with --yes for non-interactive use (CI).

TODO: also remove non-owner evaluator assignments via
remove_auditor_from_organization. Skipped today — needs owner-tracking
logic to know which evaluators to keep.

Usage:
    python scripts/sandbox_reset.py                    # interactive
    python scripts/sandbox_reset.py --yes              # CI / non-interactive
    python scripts/sandbox_reset.py --dry-run          # show plan only

Auth + GraphQL plumbing is in scripts/_api_client.py.
"""

from __future__ import annotations

import argparse
import os
import sys

from _api_client import (
    CANCEL_MUTATION,
    EMAIL,
    LIST_AUDITS_QUERY,
    find_org_id_by_slug,
    get_access_token,
    graphql,
)

# Statuses we'll cancel. CANCELLED is excluded — already in the terminal
# "cleaned" state, calling updateAudit on it is a no-op but burns API quota.
RESET_STATUSES = {"DRAFT", "PENDING", "RUNNING", "COMPLETED", "FAILED"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--yes", action="store_true", help="Skip confirmation prompt")
    parser.add_argument("--dry-run", action="store_true", help="List targets, don't cancel")
    parser.add_argument("--limit", type=int, default=1000, help="Max audits to fetch (default: 1000)")
    parser.add_argument("--headed", action="store_true", help="Show the login browser window")
    args = parser.parse_args()

    slug = os.environ.get("SANDBOX_ORG_SLUG", "").strip()
    if not slug:
        print(
            "✗ SANDBOX_ORG_SLUG is unset. Set it in .env to the slug of an org "
            "that is safe to wipe (NOT a production org). Aborting.",
            file=sys.stderr,
        )
        return 2

    print(f"→ Logging in as {EMAIL} ...", flush=True)
    token = get_access_token(headless=not args.headed)

    print(f"→ Resolving sandbox slug '{slug}' to org id ...", flush=True)
    org_id = find_org_id_by_slug(token, slug)
    if not org_id:
        print(f"✗ No organization with slug '{slug}' is visible to {EMAIL}.", file=sys.stderr)
        return 1
    print(f"  → org id = {org_id}")

    print(f"→ Fetching audits for org {org_id} (limit={args.limit}) ...", flush=True)
    data = graphql(token, org_id, LIST_AUDITS_QUERY, {"status": None, "limit": args.limit})
    audits = data["audits"]
    targets = [a for a in audits if a["status"] in RESET_STATUSES]

    by_status: dict[str, int] = {}
    for a in targets:
        by_status[a["status"]] = by_status.get(a["status"], 0) + 1

    print(f"  total audits: {len(audits)}; targets: {len(targets)} {by_status or {}}")
    if not targets:
        print("✓ Sandbox already clean.")
        return 0

    if not args.dry_run and not args.yes:
        print(f"\nThis will CANCEL {len(targets)} audit(s) in org '{slug}' (id={org_id}).")
        ans = input("Type 'yes' to proceed: ").strip().lower()
        if ans != "yes":
            print("aborted.")
            return 1

    if args.dry_run:
        for a in targets[:20]:
            print(f"  - id={a['id']:<5} status={a['status']:<10} {a['name']}")
        if len(targets) > 20:
            print(f"  ... and {len(targets) - 20} more")
        print("\n(dry-run) no changes made.")
        return 0

    print(f"\n→ Cancelling {len(targets)} audit(s) ...", flush=True)
    failed = []
    for a in targets:
        try:
            res = graphql(
                token,
                org_id,
                CANCEL_MUTATION,
                {"input": {"auditId": a["id"], "status": "CANCELLED"}},
            )
            ok = res["updateAudit"]["success"]
            print(f"  {'✓' if ok else '✗'} id={a['id']} ({a['status']:<10}) → {res['updateAudit']['message']}")
            if not ok:
                failed.append(a["id"])
        except Exception as e:
            print(f"  ✗ id={a['id']} → {e}")
            failed.append(a["id"])

    if failed:
        print(f"\n{len(failed)} failed: {failed}")
        return 1
    print(f"\n✓ Cancelled {len(targets)} audit(s). Sandbox '{slug}' is reset.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
