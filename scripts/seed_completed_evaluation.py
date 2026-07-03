#!/usr/bin/env python3
"""
Seed one real COMPLETED bulk evaluation by driving the actual UI wizard.

Unlike scripts/seed_test_data.py (which only creates DRAFTs via
createBlankAudit), this walks the whole flow the way a human does:

    New Evaluation modal (method = Bulk, random valid model)
      -> single-page wizard
      -> check a module
      -> pick a sub-module from the combobox
      -> choose the "Select a prompt library" source
      -> select a specific prompt-library radio
      -> Run Evaluation
      -> poll QUEUED -> IN_PROGRESS -> PENDING_REVIEW
      -> submitAuditReview -> COMPLETED

This exists because a flat `updateAudit(testDatasetIds=[...])` mutation does
NOT produce a runnable audit — the sub-module and specific-library selection
steps only happen through the wizard, and skipping them yields
"No successful AuditTest objects found" / totalTests=0 (learned 03 Jul 2026).

Usage:
    python scripts/seed_completed_evaluation.py                 # seed in org 1
    python scripts/seed_completed_evaluation.py --org-id 1
    python scripts/seed_completed_evaluation.py --timeout 420   # poll budget (s)
    python scripts/seed_completed_evaluation.py --headed        # watch it run

Importable: `seed_completed_evaluation(org_id=1, poll_budget_s=360)` returns the
COMPLETED audit id (int) or None on failure/timeout. Used by the
`completed_eval_id` fixture to self-heal when the sandbox has no completed eval.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
load_dotenv(REPO_ROOT / ".env")

from playwright.sync_api import sync_playwright  # noqa: E402

try:
    # When imported as a package (e.g. from tests/conftest.py at repo root).
    from scripts._api_client import (
        BASE_URL,
        EMAIL,
        PASSWORD,
        get_access_token,
        graphql,
    )
except ModuleNotFoundError:
    # When run as a CLI from inside scripts/ (sys.path has scripts/ on it).
    from _api_client import (  # noqa: E402
        BASE_URL,
        EMAIL,
        PASSWORD,
        get_access_token,
        graphql,
    )

_AUDIT_STATUS_Q = """
query($id: ID!) {
  audit(auditId: $id) { id status progressPercentage totalTests }
}
"""
_SUBMIT_REVIEW_M = """
mutation($input: SubmitAuditReviewInput!) {
  submitAuditReview(input: $input) { success message audit { id status } }
}
"""


def _login(page) -> None:
    page.goto(BASE_URL, wait_until="domcontentloaded")
    page.get_by_role("button", name="LOGIN / SIGN UP").click()
    page.wait_for_url("**/openid-connect/auth*", timeout=20_000)
    page.get_by_role("textbox", name="Email").fill(EMAIL)
    page.get_by_role("textbox", name="Password").fill(PASSWORD)
    page.get_by_role("button", name="Sign In").click()
    page.wait_for_url(f"{BASE_URL}/**", timeout=30_000)
    page.reload(wait_until="domcontentloaded")
    page.wait_for_timeout(2_000)


def seed_completed_evaluation(
    org_id: int = 1,
    poll_budget_s: int = 360,
    headless: bool = True,
) -> int | None:
    """Drive the wizard to create a COMPLETED bulk evaluation. Returns its id."""
    from pages.new_evaluation_page import NewEvaluationPage

    if not EMAIL or not PASSWORD:
        print("TEST_EMAIL_1 / TEST_PASSWORD_1 not set — cannot seed.", file=sys.stderr)
        return None

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=headless)
        ctx = browser.new_context(viewport={"width": 1440, "height": 900})
        page = ctx.new_page()
        try:
            _login(page)
            nep = NewEvaluationPage(page, org_id=org_id)
            nep.go_to_evaluations_list()
            nep.click_new_evaluation()
            if not nep.is_modal_visible():
                print("Modal did not open.", file=sys.stderr)
                return None
            nep.start_evaluation_from_modal(
                method="bulk",
                eval_type="technical",
                objective="Seeded COMPLETED reference evaluation (automation)",
            )
            if not nep.wait_for_wizard_loaded():
                print("Wizard did not hydrate.", file=sys.stderr)
                return None
            audit_id = nep.get_audit_id_from_url()
            if not audit_id:
                print("No auditId in URL after Start.", file=sys.stderr)
                return None

            if not nep.configure_bulk_workspace_minimal(module="hallucination"):
                print(
                    "Run Evaluation never enabled — no prompt library available?",
                    file=sys.stderr,
                )
                return None
            nep.click_run_evaluation()
            page.wait_for_timeout(2_000)
        finally:
            browser.close()

    # Poll to a reviewable/terminal state via the API (faster + survives UI close).
    token = get_access_token(headless=True)
    deadline = time.monotonic() + poll_budget_s
    status = None
    while time.monotonic() < deadline:
        try:
            audit = (
                graphql(token, str(org_id), _AUDIT_STATUS_Q, {"id": audit_id}).get("audit")
                or {}
            )
        except Exception as exc:  # noqa: BLE001 — transient dev timeouts
            print(f"poll error (ignored): {exc}", file=sys.stderr)
            time.sleep(15)
            continue
        status = audit.get("status")
        print(
            f"  audit {audit_id}: {status} "
            f"({audit.get('progressPercentage')}%, {audit.get('totalTests')} tests)",
            flush=True,
        )
        if status in ("PENDING_REVIEW", "COMPLETED"):
            break
        if status == "FAILED":
            print(f"Audit {audit_id} FAILED during run.", file=sys.stderr)
            return None
        time.sleep(15)

    if status == "COMPLETED":
        return int(audit_id)
    if status == "PENDING_REVIEW":
        # Push through review to reach COMPLETED.
        res = graphql(
            token,
            str(org_id),
            _SUBMIT_REVIEW_M,
            {
                "input": {
                    "auditId": audit_id,
                    "recommendations": "Seeded reference evaluation — auto-approved.",
                }
            },
        )
        if (res.get("submitAuditReview") or {}).get("success"):
            return int(audit_id)
        print(f"submitAuditReview failed: {res}", file=sys.stderr)
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--org-id", type=int, default=1)
    parser.add_argument("--timeout", type=int, default=360, help="Poll budget (s)")
    parser.add_argument("--headed", action="store_true", help="Show the browser")
    args = parser.parse_args()

    print(f"Seeding a COMPLETED evaluation in org {args.org_id} ...", flush=True)
    audit_id = seed_completed_evaluation(
        org_id=args.org_id, poll_budget_s=args.timeout, headless=not args.headed
    )
    if audit_id:
        print(f"\nCOMPLETED evaluation seeded: id={audit_id}")
        return 0
    print("\nSeeding did not reach COMPLETED.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
