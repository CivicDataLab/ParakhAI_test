#!/usr/bin/env python3
"""
Comprehensive PDF report generator for ParakhAI test framework.

Usage:
    python scripts/generate_pdf_report.py
    python scripts/generate_pdf_report.py --json reports/full_suite_20260622.json --out reports/FULL_TEST_REPORT_2026-06-22.pdf
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent

try:
    from fpdf import FPDF
except ImportError:
    print("fpdf2 not installed. Run: pip install fpdf2", file=sys.stderr)
    sys.exit(1)

_LATIN1_SUBS = str.maketrans({
    "—": "--",   # em dash
    "–": "-",    # en dash
    "’": "'",    # right single quote
    "‘": "'",    # left single quote
    "“": '"',    # left double quote
    "”": '"',    # right double quote
    "•": "*",    # bullet
    "…": "...",  # ellipsis
    " ": " ",    # non-breaking space
    "✔": "[OK]", # heavy check mark
    "✘": "[X]",  # heavy ballot x
})

def _s(text: str) -> str:
    """Sanitise string to Latin-1 safe characters for fpdf2 core fonts."""
    text = text.translate(_LATIN1_SUBS)
    return text.encode("latin-1", errors="replace").decode("latin-1")

# ── MCP exploration findings (2026-06-22) ─────────────────────────────────────
MCP_FINDINGS = [
    {
        "id": 1,
        "severity": "LOW",
        "category": "SEO",
        "title": "Meta description typo",
        "detail": (
            "Homepage <meta name='description'> contains 'Paricipatory' (missing 't'). "
            "Should be 'Participatory'."
        ),
        "fix": "Correct the spelling in the Next.js metadata export.",
    },
    {
        "id": 2,
        "severity": "MEDIUM",
        "category": "UX",
        "title": "Unauthenticated /dashboard redirect shows no login prompt",
        "detail": (
            "Navigating to /dashboard without auth silently redirects to the homepage "
            "with no message explaining the redirect or a visible login button."
        ),
        "fix": "Add a flash message or redirect to /login?next=/dashboard.",
    },
    {
        "id": 3,
        "severity": "LOW",
        "category": "Consistency",
        "title": "Inconsistent locale prefix in URLs",
        "detail": (
            "AI Maker breadcrumb links use /en/dashboard/ai-maker (locale prefix), "
            "while Evaluator role uses /dashboard/auditor (no prefix). "
            "Sidebar nav links also omit /en/ prefix."
        ),
        "fix": "Standardise URL generation — either always include or always omit the locale prefix.",
    },
    {
        "id": 4,
        "severity": "LOW",
        "category": "Consistency",
        "title": "Org cards link to /en/ URL while landing page has no prefix",
        "detail": (
            "Org selection cards on /dashboard/ai-maker link to /en/dashboard/ai-maker/{id} "
            "while the page itself is served without the /en/ prefix."
        ),
        "fix": "Use Next.js router.push with locale option to generate consistent links.",
    },
    {
        "id": 5,
        "severity": "CRITICAL",
        "category": "Performance",
        "title": "AI Maker overview stuck on 'Loading overview...' indefinitely",
        "detail": (
            "The dashboard overview query hangs >30s on org 1 (981 audits). "
            "Root cause: N+1 per-row resolver cost on the GetAudits query fetching "
            "metrics/modules/test-counts for each evaluation row."
        ),
        "fix": "Add DataLoader batching or a summary aggregate query. "
               "Add a client-side timeout with an error state.",
    },
    {
        "id": 6,
        "severity": "CRITICAL",
        "category": "Infrastructure",
        "title": "503 errors on /ai-models and /prompt-libraries RSC prefetch",
        "detail": (
            "Next.js RSC prefetch for /dashboard/ai-maker/1/ai-models and "
            "/dashboard/ai-maker/1/prompt-libraries returns HTTP 503. "
            "Occurs under combined load of 3+ browser sessions."
        ),
        "fix": "Scale up the backend server or add connection pooling (PgBouncer). "
               "Investigate why Next.js RSC prefetch triggers 503.",
    },
    {
        "id": 7,
        "severity": "MEDIUM",
        "category": "UX",
        "title": "Breadcrumb shows 'Dashboard' instead of section name on sub-pages",
        "detail": (
            "On /evaluations, /ai-models, and /prompt-libraries pages, "
            "the last (current-page) breadcrumb crumb displays 'Dashboard' "
            "instead of 'Evaluations', 'Models', etc."
        ),
        "fix": "Pass the correct label prop to the breadcrumb component based on the route segment.",
    },
    {
        "id": 8,
        "severity": "MEDIUM",
        "category": "UX / New Feature",
        "title": "New Evaluation dialog changed from Cancel/Start to Back/Next wizard",
        "detail": (
            "The 'Start an Evaluation' modal now uses wizard-style Back/Next buttons "
            "instead of the previously tested Cancel/Start buttons. "
            "Existing test suite tests for Cancel and Start buttons which no longer exist."
        ),
        "fix": "Update test_new_evaluation_smoke.py and related tests for the new wizard UI. "
               "Also fix 'Loading models...' hang in the dialog (same N+1 issue).",
    },
    {
        "id": 9,
        "severity": "HIGH",
        "category": "UX",
        "title": "New Evaluation dialog 'Loading models...' hangs >30s",
        "detail": (
            "After clicking 'New Evaluation', the model dropdown in the dialog "
            "shows 'Loading models...' indefinitely (30s+ timeout). Back/Next buttons disabled. "
            "This blocks the most critical user flow — creating evaluations."
        ),
        "fix": "Investigate the aiModels GraphQL query performance. "
               "Add pagination to the model list or cache the first page.",
    },
    {
        "id": 10,
        "severity": "LOW",
        "category": "UX",
        "title": "Evaluation Name textbox editable on COMPLETED evaluations",
        "detail": (
            "The evaluation detail page shows the name as an editable textbox "
            "even when the status is COMPLETED. It's unclear if this is intentional "
            "or a missing read-only guard."
        ),
        "fix": "Add read-only attribute or disable the input for COMPLETED/FAILED statuses, "
               "unless renaming completed evals is a supported feature.",
    },
    {
        "id": 11,
        "severity": "LOW",
        "category": "UX",
        "title": "Evaluation detail breadcrumb lacks evaluation name/number",
        "detail": (
            "The breadcrumb on evaluation detail pages ends with the org name (e.g. 'CivicDataLab') "
            "rather than the evaluation name or ID, giving no navigation context."
        ),
        "fix": "Add evaluation name as the final breadcrumb crumb on detail pages.",
    },
    {
        "id": 12,
        "severity": "MEDIUM",
        "category": "Infrastructure",
        "title": "GraphQL request aborted (ERR_ABORTED) on New Evaluation dialog",
        "detail": (
            "Network request #2 for the model list in the New Evaluation dialog "
            "failed with net::ERR_ABORTED. Combined with the 30s hang, "
            "this indicates the request is eventually killed by the browser."
        ),
        "fix": "Implement a server-side timeout on the model list query "
               "and return an error state instead of leaving the client hanging.",
    },
    {
        "id": 13,
        "severity": "CRITICAL",
        "category": "Infrastructure",
        "title": "PostgreSQL connection pool exhausted under concurrent load",
        "detail": (
            "Console error on AI Models page: "
            "'FATAL: sorry, too many clients already' on port 5433. "
            "Occurs when 3 pytest workers + 1 MCP browser session run simultaneously. "
            "Causes multiple pages to fail to load (Models, Prompt Libraries, Overview)."
        ),
        "fix": "Deploy PgBouncer in transaction mode, or increase max_connections on the dev DB. "
               "Reduce N+1 queries to decrease connection hold time per request.",
    },
    {
        "id": 14,
        "severity": "MEDIUM",
        "category": "Security",
        "title": "/api/auth/session exposes full JWT access_token in response body",
        "detail": (
            "GET /api/auth/session returns the full Keycloak access_token (JWT) and id_token "
            "in the JSON response body. While this is a known NextAuth.js pattern for "
            "server-side token forwarding, it means anyone with the session cookie "
            "can extract the raw Keycloak JWT via a client-side fetch."
        ),
        "fix": "Consider returning only the session expiry and user info from the client-side "
               "session endpoint. Move access_token forwarding to server-side API routes only. "
               "Ensure session cookies have Secure + SameSite=Strict.",
    },
    {
        "id": 15,
        "severity": "MEDIUM",
        "category": "Security",
        "title": "Keycloak client configured with allowed-origins: ['*']",
        "detail": (
            "The JWT payload contains 'allowed-origins: [\"*\"]', meaning the Keycloak "
            "client is configured to accept tokens from any origin. "
            "This weakens CORS protection at the IdP level."
        ),
        "fix": "In Keycloak admin: set allowed-origins for the 'dataspace' client "
               "to only the known frontend domains (dev/staging/prod).",
    },
    {
        "id": 16,
        "severity": "MEDIUM",
        "category": "UX",
        "title": "Status filter tabs expanded to 9 (breaking existing tests)",
        "detail": (
            "The StatusFilterTabs component now shows 9 tabs: "
            "All | Draft | Queued | Running | In Progress | Pending Review | Completed | Failed | Cancelled. "
            "Previous tests expected only 6 tabs (All/Draft/Pending/Running/Completed/Failed). "
            "The 'Pending' tab is now split into 'Queued' and 'Pending Review'."
        ),
        "fix": "Update locators and test assertions. New locators added: "
               "STATUS_TAB_QUEUED, STATUS_TAB_IN_PROGRESS, STATUS_TAB_PENDING_REVIEW, STATUS_TAB_CANCELLED. "
               "test_nine_status_tabs_are_present added to test suite.",
    },
    {
        "id": 17,
        "severity": "LOW",
        "category": "Security",
        "title": "Session cookies are HttpOnly (positive finding)",
        "detail": (
            "Keycloak/NextAuth session cookies are not visible to JavaScript "
            "(document.cookie only shows NEXT_LOCALE=en). "
            "HttpOnly flag correctly prevents XSS-based token theft."
        ),
        "fix": "No action needed. Continue enforcing HttpOnly on all auth cookies.",
    },
    {
        "id": 18,
        "severity": "LOW",
        "category": "Accessibility",
        "title": "Mobile menu dialog missing DialogTitle",
        "detail": (
            "The hamburger menu on mobile renders as a Radix UI Dialog but lacks a DialogTitle. "
            "Console error: 'DialogContent requires a DialogTitle for screen reader users.' "
            "Screen readers cannot announce the menu purpose."
        ),
        "fix": "Add <DialogTitle> (can be visually hidden with VisuallyHidden) to the mobile menu. "
               "See: https://radix-ui.com/primitives/docs/components/dialog",
    },
    {
        "id": 19,
        "severity": "MEDIUM",
        "category": "UX",
        "title": "Mobile menu has no navigation links",
        "detail": (
            "Tapping the hamburger menu on 390px viewport opens a dialog "
            "containing only the user profile avatar button and a close button. "
            "No navigation links to Dashboard, AI Maker, or Evaluator roles are present."
        ),
        "fix": "Add primary navigation links to the mobile menu dialog. "
               "Authenticated users need access to Dashboard and Switch Roles from mobile.",
    },
    {
        "id": 20,
        "severity": "LOW",
        "category": "UX",
        "title": "404 page is bare Next.js default with no branding or navigation",
        "detail": (
            "Visiting a non-existent URL shows only '404 / This page could not be found.' "
            "with no ParakhAI logo, no back-to-home link, and no navigation."
        ),
        "fix": "Create a custom not-found.tsx page with the app layout, logo, and a "
               "'Go to Dashboard' button.",
    },
    {
        "id": 21,
        "severity": "LOW",
        "category": "UX",
        "title": "Pagination renders before data loads (race condition)",
        "detail": (
            "On the AI Models page, the pagination component shows 'Page 01 of 01' "
            "while data is still in 'Loading AI models...' state. "
            "The page count resets once data arrives."
        ),
        "fix": "Show pagination only after the data query resolves successfully.",
    },
    {
        "id": 22,
        "severity": "MEDIUM",
        "category": "UX",
        "title": "Session verification triggered on every page.goto() call",
        "detail": (
            "Every direct URL navigation causes a 'Verifying your session...' spinner "
            "before rendering. For some pages (auditor, invalid org IDs) this spinner "
            "never resolves, timing out after 30s."
        ),
        "fix": "Cache the session check result or use Next.js middleware to verify "
               "before the page renders, avoiding per-page re-verification.",
    },
]

NEW_TESTS_ADDED = [
    "locators/evaluations_locators.py — Added STATUS_TAB_QUEUED, STATUS_TAB_IN_PROGRESS, STATUS_TAB_PENDING_REVIEW, STATUS_TAB_CANCELLED",
    "tests/e2e/test_evaluations.py — test_nine_status_tabs_are_present (9-tab structure)",
    "tests/e2e/test_evaluations.py — test_queued_tab_is_present_and_clickable",
    "tests/e2e/test_evaluations.py — test_in_progress_tab_is_present_and_clickable",
    "tests/e2e/test_evaluations.py — test_pending_review_tab_filters_correctly",
    "tests/e2e/test_evaluations.py — test_cancelled_tab_is_present_and_clickable",
    "tests/e2e/test_evaluations.py — test_status_tab_count_badges_are_numeric",
    "tests/e2e/test_breadcrumb.py — test_evaluations_breadcrumb_is_not_dashboard (xfail)",
    "tests/e2e/test_breadcrumb.py — test_models_breadcrumb_is_not_dashboard (xfail)",
    "tests/e2e/test_breadcrumb.py — test_breadcrumb_home_link_navigates_to_root",
    "tests/e2e/test_breadcrumb.py — test_breadcrumb_evaluation_workspace_link_works",
    "tests/e2e/test_breadcrumb.py — test_evaluation_detail_breadcrumb_has_org_name",
    "tests/e2e/test_platform_issues.py — test_meta_description_has_no_typo",
    "tests/e2e/test_platform_issues.py — test_meta_description_mentions_ai_evaluation",
    "tests/e2e/test_platform_issues.py — test_og_title_is_present",
    "tests/e2e/test_platform_issues.py — test_404_page_shows_not_found_message",
    "tests/e2e/test_platform_issues.py — test_404_page_has_home_navigation_link (xfail)",
    "tests/e2e/test_platform_issues.py — test_404_page_has_logo_or_branding (xfail)",
    "tests/e2e/test_platform_issues.py — test_hamburger_menu_is_visible_on_mobile",
    "tests/e2e/test_platform_issues.py — test_mobile_menu_dialog_has_accessible_title (xfail)",
    "tests/e2e/test_platform_issues.py — test_mobile_menu_has_navigation_links (xfail)",
    "tests/e2e/test_platform_issues.py — test_mobile_menu_can_be_closed_with_escape",
    "tests/e2e/test_platform_issues.py — test_unauthenticated_dashboard_redirects",
    "tests/e2e/test_platform_issues.py — test_unauthenticated_redirect_shows_login_prompt (xfail)",
    "tests/e2e/test_platform_issues.py — test_session_verification_completes_within_15s",
    "tests/api/test_security.py — test_html_page_has_security_headers",
    "tests/api/test_security.py — test_session_api_returns_empty_for_unauthenticated",
    "tests/api/test_db_health.py — test_graphql_responds_under_sequential_load",
    "tests/api/test_db_health.py — test_graphql_responds_under_5_concurrent_requests",
    "tests/api/test_db_health.py — test_graphql_error_response_does_not_contain_db_connection_error",
    "tests/api/test_db_health.py — test_models_endpoint_does_not_return_503",
    "tests/api/test_db_health.py — test_prompt_libraries_endpoint_does_not_return_503",
]

SEVERITY_COLORS = {
    "CRITICAL": (220, 53, 69),
    "HIGH": (255, 133, 27),
    "MEDIUM": (255, 193, 7),
    "LOW": (40, 167, 69),
    "INFO": (108, 117, 125),
}


class PDF(FPDF):
    def cell(self, *args, **kwargs):
        # text is positional arg at index 2 (w, h, text)
        if len(args) > 2:
            args = list(args)
            args[2] = _s(str(args[2]))
            args = tuple(args)
        if "text" in kwargs:
            kwargs["text"] = _s(str(kwargs["text"]))
        if "txt" in kwargs:
            kwargs["txt"] = _s(str(kwargs["txt"]))
        return super().cell(*args, **kwargs)

    def multi_cell(self, *args, **kwargs):
        # text is positional arg at index 2 (w, h, text)
        if len(args) > 2:
            args = list(args)
            args[2] = _s(str(args[2]))
            args = tuple(args)
        if "text" in kwargs:
            kwargs["text"] = _s(str(kwargs["text"]))
        if "txt" in kwargs:
            kwargs["txt"] = _s(str(kwargs["txt"]))
        return super().multi_cell(*args, **kwargs)

    def header(self):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(80, 80, 80)
        self.cell(0, 8, "ParakhAI Platform — Full Test Report", align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(200, 200, 200)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(3)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Page {self.page_no()} — Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}", align="C")

    def section_title(self, title: str):
        self.ln(4)
        self.set_font("Helvetica", "B", 13)
        self.set_fill_color(41, 82, 163)
        self.set_text_color(255, 255, 255)
        self.cell(0, 8, f"  {title}", fill=True, new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(0, 0, 0)
        self.ln(3)

    def kv_row(self, key: str, value: str, bold_val: bool = False):
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(80, 80, 80)
        self.cell(50, 6, key + ":", new_x="RIGHT", new_y="TOP")
        self.set_font("Helvetica", "B" if bold_val else "", 9)
        self.set_text_color(0, 0, 0)
        self.multi_cell(0, 6, str(value), new_x="LMARGIN", new_y="NEXT")

    def severity_badge(self, severity: str):
        r, g, b = SEVERITY_COLORS.get(severity, (108, 117, 125))
        self.set_fill_color(r, g, b)
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 8)
        self.cell(22, 5, f" {severity} ", fill=True, new_x="RIGHT", new_y="TOP")
        self.set_text_color(0, 0, 0)


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def generate_pdf(json_path: Path, out_path: Path) -> Path:
    data = _load_json(json_path)
    summary = data.get("summary", {})
    tests = data.get("tests", [])
    created_ts = data.get("created", datetime.now(timezone.utc).timestamp())
    created_dt = datetime.fromtimestamp(created_ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    total = summary.get("total", len(tests))
    passed = summary.get("passed", 0)
    failed = summary.get("failed", 0)
    skipped = summary.get("skipped", 0)
    errors = summary.get("error", 0)
    xfailed = summary.get("xfailed", 0)
    xpassed = summary.get("xpassed", 0)
    duration = summary.get("duration", 0.0)
    pass_rate = (passed / total * 100) if total else 0.0

    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_margins(10, 15, 10)

    # ── Cover page ──────────────────────────────────────────────────────────
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(41, 82, 163)
    pdf.ln(20)
    pdf.cell(0, 12, "ParakhAI Platform", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Full Test Report", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 8, "Automated Testing + Manual MCP Exploration", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)
    pdf.set_draw_color(41, 82, 163)
    pdf.set_line_width(0.5)
    pdf.line(30, pdf.get_y(), 180, pdf.get_y())
    pdf.ln(8)

    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 10)
    info = [
        ("Date", datetime.now(timezone.utc).strftime("%Y-%m-%d")),
        ("Environment", "dev.parakh.civicdataspace.in"),
        ("Run by", "Claude Code autonomous test run"),
        ("Framework", "pytest + Playwright (Python)"),
        ("Browser", "Chromium (headless)"),
        ("Concurrency", "3 workers (xdist) + 1 MCP session"),
        ("Keycloak sessions used", "4 of 5 allowed"),
    ]
    for k, v in info:
        pdf.kv_row(k, v)

    # Overall result banner
    pdf.ln(8)
    if failed == 0 and errors == 0:
        pdf.set_fill_color(40, 167, 69)
    else:
        pdf.set_fill_color(220, 53, 69)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 14)
    status_text = "ALL TESTS PASSED" if failed == 0 and errors == 0 else f"{failed} TESTS FAILED"
    pdf.cell(0, 12, f"  {status_text}", fill=True, new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)

    # ── Executive summary ───────────────────────────────────────────────────
    pdf.section_title("1. Executive Summary")

    if total > 0:
        # Stats table
        col_w = 40
        headers = ["Total", "Passed", "Failed", "Skipped", "xFailed", "Pass Rate", "Duration"]
        values = [str(total), str(passed), str(failed), str(skipped), str(xfailed),
                  f"{pass_rate:.1f}%", f"{int(duration)}s"]
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_fill_color(230, 235, 245)
        for h in headers:
            pdf.cell(col_w / 1.5, 7, h, border=1, fill=True, align="C", new_x="RIGHT", new_y="TOP")
        pdf.ln()
        pdf.set_font("Helvetica", "", 9)
        for i, v in enumerate(values):
            if headers[i] == "Failed" and failed > 0:
                pdf.set_text_color(220, 53, 69)
            elif headers[i] == "Passed":
                pdf.set_text_color(40, 167, 69)
            else:
                pdf.set_text_color(0, 0, 0)
            pdf.cell(col_w / 1.5, 7, v, border=1, align="C", new_x="RIGHT", new_y="TOP")
        pdf.set_text_color(0, 0, 0)
        pdf.ln(10)
    else:
        pdf.set_font("Helvetica", "I", 10)
        pdf.cell(0, 8, "pytest results JSON not yet available — run in progress or not found.", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)

    # ── MCP Exploration summary ─────────────────────────────────────────────
    critical = sum(1 for f in MCP_FINDINGS if f["severity"] == "CRITICAL")
    high = sum(1 for f in MCP_FINDINGS if f["severity"] == "HIGH")
    medium = sum(1 for f in MCP_FINDINGS if f["severity"] == "MEDIUM")
    low = sum(1 for f in MCP_FINDINGS if f["severity"] == "LOW")

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 7, f"Manual Playwright MCP Exploration: {len(MCP_FINDINGS)} findings", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 6, f"  Critical: {critical}  |  High: {high}  |  Medium: {medium}  |  Low/Info: {low}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    # ── Suite breakdown ─────────────────────────────────────────────────────
    if tests:
        pdf.section_title("2. Test Suite Results by Category")
        grouped: dict[str, list] = {}
        for t in tests:
            parts = t.get("nodeid", "").split("/")
            grp = parts[1] if len(parts) >= 3 else "other"
            grouped.setdefault(grp, []).append(t)

        for grp, gtests in sorted(grouped.items()):
            gp = sum(1 for t in gtests if t.get("outcome") == "passed")
            gf = sum(1 for t in gtests if t.get("outcome") == "failed")
            gs = sum(1 for t in gtests if t.get("outcome") == "skipped")
            gx = sum(1 for t in gtests if t.get("outcome") in ("xfailed", "xpassed"))

            pdf.set_font("Helvetica", "B", 10)
            pdf.set_fill_color(245, 247, 252)
            pdf.cell(0, 7, f"  {grp.upper()} ({len(gtests)} tests)", fill=True, new_x="LMARGIN", new_y="NEXT")

            pdf.set_font("Helvetica", "", 9)
            bar_text = f"    [P] {gp} passed  [F] {gf} failed  [-] {gs} skipped  [~] {gx} xfailed"
            pdf.cell(0, 6, bar_text, new_x="LMARGIN", new_y="NEXT")

            # List failures only
            failures = [t for t in gtests if t.get("outcome") == "failed"]
            if failures:
                pdf.set_font("Helvetica", "B", 8)
                pdf.set_text_color(220, 53, 69)
                pdf.cell(0, 5, "    Failures:", new_x="LMARGIN", new_y="NEXT")
                pdf.set_font("Helvetica", "", 8)
                for t in failures[:10]:
                    name = t.get("nodeid", "").split("::")[-1]
                    pdf.cell(0, 5, f"      • {name}", new_x="LMARGIN", new_y="NEXT")
                if len(failures) > 10:
                    pdf.cell(0, 5, f"      ... and {len(failures) - 10} more", new_x="LMARGIN", new_y="NEXT")
                pdf.set_text_color(0, 0, 0)
            pdf.ln(2)

    # ── MCP Findings detail ─────────────────────────────────────────────────
    pdf.section_title(f"{'3' if tests else '2'}. MCP Browser Exploration Findings")
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 6, "Findings from manual Playwright MCP session on dev.parakh.civicdataspace.in (2026-06-22).", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    for finding in MCP_FINDINGS:
        pdf.set_fill_color(248, 249, 250)
        pdf.set_draw_color(200, 200, 200)
        y_start = pdf.get_y()

        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(10, 6, f"#{finding['id']}", new_x="RIGHT", new_y="TOP")
        pdf.severity_badge(finding["severity"])
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(20, 6, f" [{finding['category']}]", new_x="RIGHT", new_y="TOP")
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "B", 9)
        pdf.multi_cell(0, 6, f" {finding['title']}", new_x="LMARGIN", new_y="NEXT")

        pdf.set_font("Helvetica", "", 8)
        pdf.set_x(18)
        pdf.multi_cell(175, 5, finding["detail"], new_x="LMARGIN", new_y="NEXT")

        pdf.set_font("Helvetica", "I", 8)
        pdf.set_text_color(41, 82, 163)
        pdf.set_x(18)
        pdf.multi_cell(175, 5, f"Fix: {finding['fix']}", new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(0, 0, 0)
        pdf.ln(2)

    # ── New tests added ─────────────────────────────────────────────────────
    section_num = 4 if tests else 3
    pdf.section_title(f"{section_num}. New Tests Added to Framework")
    pdf.set_font("Helvetica", "", 8)
    pdf.cell(0, 6, f"{len(NEW_TESTS_ADDED)} new test cases added to cover the above findings:", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    for item in NEW_TESTS_ADDED:
        pdf.cell(5, 5, "", new_x="RIGHT", new_y="TOP")
        pdf.multi_cell(0, 5, f"• {item}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    # ── Failure details ─────────────────────────────────────────────────────
    failures_all = [t for t in tests if t.get("outcome") == "failed"]
    if failures_all:
        section_num += 1
        pdf.section_title(f"{section_num}. Failure Details (First 20)")
        for t in failures_all[:20]:
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(220, 53, 69)
            name = t.get("nodeid", "")
            pdf.multi_cell(0, 6, f"❌ {name}", new_x="LMARGIN", new_y="NEXT")
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Courier", "", 7)
            longrepr = (t.get("call") or {}).get("longrepr", "")
            if longrepr:
                # Last 600 chars of longrepr (most relevant part)
                snippet = str(longrepr)[-600:].strip()
                pdf.set_fill_color(250, 245, 245)
                pdf.multi_cell(0, 4, snippet, fill=True, new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)

    # ── Recommendations ─────────────────────────────────────────────────────
    section_num += 1
    pdf.section_title(f"{section_num}. Priority Recommendations")
    recs = [
        ("P0 — Immediate", [
            "Deploy PgBouncer or increase PostgreSQL max_connections on dev (Finding #13)",
            "Fix N+1 query on GetAudits/overview — add DataLoader batching (Finding #5, #9)",
            "Add server-side timeout on model list query; show error state in dialog (Finding #12)",
        ]),
        ("P1 — High Priority", [
            "Set Keycloak allowed-origins to specific domains, not '*' (Finding #15)",
            "Add navigation links to mobile hamburger menu (Finding #19)",
            "Fix breadcrumb label bug on sub-pages showing 'Dashboard' (Finding #7)",
            "Create a branded custom 404 page (Finding #20)",
        ]),
        ("P2 — Medium Priority", [
            "Consider not exposing raw JWT in /api/auth/session client-side (Finding #14)",
            "Add DialogTitle to mobile menu for screen reader accessibility (Finding #18)",
            "Fix 'Completed on' column header for FAILED evaluations — use 'Finished on' (Finding #8)",
            "Correct meta description typo 'Paricipatory' → 'Participatory' (Finding #1)",
            "Show explicit login prompt when redirect occurs from protected URL (Finding #2)",
            "Standardise URL locale prefix (/en/ vs no prefix) across all routes (Finding #3)",
        ]),
        ("P3 — Low Priority / Nice to Have", [
            "Make Evaluation Name read-only on COMPLETED evaluations (Finding #10)",
            "Add evaluation name to breadcrumb on detail pages (Finding #11)",
            "Hide pagination until data finishes loading (Finding #21)",
            "Add Open Graph title/image tags for social sharing",
        ]),
    ]
    for priority, items in recs:
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 7, priority, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 9)
        for item in items:
            pdf.set_x(14)
            pdf.multi_cell(0, 5, f"• {item}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(out_path))
    return out_path


def main():
    parser = argparse.ArgumentParser(description="Generate PDF test report")
    parser.add_argument(
        "--json",
        default="reports/full_suite_20260622.json",
        help="Path to pytest-json-report output",
    )
    parser.add_argument(
        "--out",
        default="reports/FULL_TEST_REPORT_2026-06-22.pdf",
        help="Output PDF path",
    )
    args = parser.parse_args()

    json_path = ROOT / args.json
    out_path = ROOT / args.out

    print(f"Reading: {json_path}")
    print(f"Writing: {out_path}")
    result = generate_pdf(json_path, out_path)
    print(f"PDF generated: {result} ({result.stat().st_size // 1024}KB)")


if __name__ == "__main__":
    main()
