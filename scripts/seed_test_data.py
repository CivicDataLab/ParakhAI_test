#!/usr/bin/env python3
"""
Seed N draft audits in a given organization, for repeatable demo or
test-fixture state.

Uses the `createBlankAudit` mutation — equivalent to clicking "New Evaluation"
in the UI but stopping before any configuration is done. The resulting audit
appears in the evaluations list with status DRAFT.

Usage:
    python scripts/seed_test_data.py                   # 5 drafts in org 1
    python scripts/seed_test_data.py --count 10
    python scripts/seed_test_data.py --org-id 5
    python scripts/seed_test_data.py --model-id 129    # pin to a known model
    python scripts/seed_test_data.py --name-prefix "Demo eval"
    python scripts/seed_test_data.py --dry-run         # show plan, don't create

If --model-id is not given, the first AI model returned by `aiModels()` for
the organization is used.

Auth + GraphQL plumbing is in scripts/_api_client.py.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime

from _api_client import (
    CREATE_BLANK_AUDIT_MUTATION,
    EMAIL,
    LIST_AI_MODELS_QUERY,
    get_access_token,
    graphql,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=5, help="Number of drafts to create (default: 5)")
    parser.add_argument("--org-id", default="1", help="Organization id (default: 1)")
    parser.add_argument("--model-id", default=None, help="AI model id (default: first aiModel returned)")
    parser.add_argument(
        "--name-prefix",
        default="Seeded eval",
        help="Audit name prefix; full name is '<prefix> N (<timestamp>)' (default: 'Seeded eval')",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print the plan, don't create")
    parser.add_argument("--headed", action="store_true", help="Show the login browser window")
    args = parser.parse_args()

    if args.count < 1:
        print("--count must be ≥ 1", file=sys.stderr)
        return 2

    print(f"→ Logging in as {EMAIL} ...", flush=True)
    token = get_access_token(headless=not args.headed)

    model_id = args.model_id
    if not model_id:
        print(f"→ Looking up first AI model for org {args.org_id} ...", flush=True)
        data = graphql(token, args.org_id, LIST_AI_MODELS_QUERY, {"limit": 1})
        models = data.get("aiModels") or []
        if not models:
            print(f"✗ No AI models found in org {args.org_id}. Pass --model-id explicitly.")
            return 1
        model_id = models[0]["id"]
        print(f"  using model: {models[0]['name']} (id={model_id})")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    plan = [
        {"name": f"{args.name_prefix} {i + 1} ({timestamp})"}
        for i in range(args.count)
    ]

    print(f"\n→ Plan: create {args.count} draft(s) in org {args.org_id} with model {model_id}")
    for p in plan:
        print(f"  - {p['name']}")

    if args.dry_run:
        print("\n(dry-run) no changes made.")
        return 0

    print(f"\n→ Creating {args.count} draft(s) ...", flush=True)
    failed = []
    for p in plan:
        try:
            res = graphql(
                token,
                args.org_id,
                CREATE_BLANK_AUDIT_MUTATION,
                {"input": {"modelId": str(model_id), "name": p["name"]}},
            )
            payload = res["createBlankAudit"]
            if payload["success"]:
                aid = payload["audit"]["id"]
                print(f"  ✓ id={aid}  {p['name']}")
            else:
                print(f"  ✗ {p['name']} → {payload['message']}")
                failed.append(p["name"])
        except Exception as e:
            print(f"  ✗ {p['name']} → {e}")
            failed.append(p["name"])

    if failed:
        print(f"\n{len(failed)} failed: {failed}")
        return 1
    print(f"\n✓ Created {args.count} draft(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
