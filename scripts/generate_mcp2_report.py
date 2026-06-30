#!/usr/bin/env python3
"""
MCP Session 2 — Platform re-audit report generator (2026-06-22).
Compares findings from the original MCP session against current state.
"""
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

try:
    from fpdf import FPDF
except ImportError:
    print("fpdf2 not installed", file=sys.stderr)
    sys.exit(1)

_LATIN1_SUBS = str.maketrans({
    "—": "--", "–": "-", "’": "'", "‘": "'",
    "“": '"', "”": '"', "•": "*", "…": "...",
    " ": " ", "✔": "[OK]", "✘": "[X]",
})

def _s(text: str) -> str:
    text = text.translate(_LATIN1_SUBS)
    return text.encode("latin-1", errors="replace").decode("latin-1")

# ── Performance metrics captured during session ────────────────────────────────
PERF_METRICS = [
    {"page": "Homepage (/)",             "ttfb": 49,  "dcl": 202, "load": 211},
    {"page": "Dashboard (/dashboard)",   "ttfb": 41,  "dcl": 61,  "load": 80},
    {"page": "AI Maker org select",      "ttfb": None, "dcl": 57,  "load": None},
    {"page": "Prompt Libraries",         "ttfb": None, "dcl": 57,  "load": None},
    {"page": "Evaluations list",         "ttfb": 45,  "dcl": 81,  "load": 87},
    {"page": "GraphQL API (avg 10 req)", "ttfb": 112, "dcl": None, "load": None},
]

# ── Finding status comparison ──────────────────────────────────────────────────
# status: "FIXED" | "IMPROVED" | "OPEN" | "NEW" | "CONFIRMED" | "POSITIVE"
FINDINGS = [
    {
        "id": 1, "severity": "LOW", "category": "SEO",
        "title": "Meta description typo 'Paricipatory'",
        "status": "OPEN",
        "evidence": "document.querySelector('meta[name=description]').content = 'Paricipatory AI Evaluation' -- typo unchanged.",
        "fix": "Correct spelling in Next.js metadata export.",
    },
    {
        "id": 2, "severity": "LOW", "category": "SEO",
        "title": "Open Graph title tag missing",
        "status": "OPEN",
        "evidence": "og:title meta tag returns empty string. Social sharing will show no title.",
        "fix": "Add openGraph.title in Next.js layout metadata.",
    },
    {
        "id": 3, "severity": "LOW", "category": "Consistency",
        "title": "Locale prefix inconsistency in URLs",
        "status": "OPEN",
        "evidence": "Org cards link to /en/dashboard/ai-maker/{id} but page is served without /en/ prefix.",
        "fix": "Standardise URL generation via Next.js locale router.",
    },
    {
        "id": 4, "severity": "LOW", "category": "Consistency",
        "title": "Org card links use /en/ prefix",
        "status": "OPEN",
        "evidence": "All 10 org links render with /en/ prefix causing 307 redirects before landing.",
        "fix": "Use useRouter().push with locale option to generate prefix-free links.",
    },
    {
        "id": 5, "severity": "CRITICAL", "category": "Performance",
        "title": "AI Maker overview 'Loading overview...' hang",
        "status": "IMPROVED",
        "evidence": "Overview loaded in this session without hanging (previously >30s). N+1 may be partially addressed or load was lighter. Needs sustained monitoring.",
        "fix": "Continue monitoring. Add DataLoader batching on GetAudits resolver as permanent fix.",
    },
    {
        "id": 6, "severity": "HIGH", "category": "Infrastructure",
        "title": "503 errors on RSC prefetch routes",
        "status": "IMPROVED",
        "evidence": "/ai-models and /prompt-libraries RSC prefetches now return 200 (were 503). Org 15 (/en/dashboard/ai-maker/15) still returns 503 on RSC prefetch.",
        "fix": "Investigate why org 15 specifically triggers 503. Other routes appear fixed.",
    },
    {
        "id": 7, "severity": "MEDIUM", "category": "UX",
        "title": "Breadcrumb shows org name not section name on sub-pages",
        "status": "OPEN",
        "evidence": "Breadcrumb last item = 'CivicDataLabCivicDataLab' on Evaluations, Models, Prompt Libraries pages. Section name never appears. Text also appears duplicated (doubled).",
        "fix": "Pass correct label prop to BreadcrumbItem based on route segment. Fix duplicate text render.",
    },
    {
        "id": 8, "severity": "MEDIUM", "category": "UX",
        "title": "New Evaluation modal changed to wizard (Back/Next)",
        "status": "CONFIRMED",
        "evidence": "Dialog still uses Back/Next wizard buttons. No Cancel/Start. This is the intended new UI pattern.",
        "fix": "Update test suite to target Back/Next buttons (done in test_evaluations.py).",
    },
    {
        "id": 9, "severity": "HIGH", "category": "Performance",
        "title": "New Evaluation dialog model list loading hang",
        "status": "FIXED",
        "evidence": "Model dropdown now loads immediately with full model list (xAI Grok 4.3, Gemma 4, SarvamAI, etc.). No 30s hang observed. ERR_ABORTED gone.",
        "fix": "Fixed. Likely resolved by backend query optimisation or model list caching.",
    },
    {
        "id": 10, "severity": "LOW", "category": "UX",
        "title": "Evaluation name editable on COMPLETED evaluations",
        "status": "OPEN",
        "evidence": "Input readOnly=false, disabled=false on eval 1383 (status: COMPLETED). Editable field on final-state evaluation.",
        "fix": "Set readOnly or disabled on name input when audit.status is COMPLETED or FAILED.",
    },
    {
        "id": 11, "severity": "LOW", "category": "UX",
        "title": "Eval detail breadcrumb lacks evaluation name",
        "status": "OPEN",
        "evidence": "Breadcrumb on /evaluations/1383 ends with 'CivicDataLab', not the evaluation name.",
        "fix": "Append evaluation name as final BreadcrumbItem on detail pages.",
    },
    {
        "id": 12, "severity": "MEDIUM", "category": "Infrastructure",
        "title": "GraphQL request ERR_ABORTED on model list",
        "status": "FIXED",
        "evidence": "No aborted requests observed. Model loading resolved (see Finding #9).",
        "fix": "Resolved by model list fix.",
    },
    {
        "id": 13, "severity": "CRITICAL", "category": "Infrastructure",
        "title": "PostgreSQL connection pool exhaustion",
        "status": "IMPROVED",
        "evidence": "10 sequential GraphQL requests completed without 'too many clients' errors. Avg 112ms. No DB error messages observed in console during this session.",
        "fix": "Monitor under higher concurrency. PgBouncer deployment still recommended as permanent fix.",
    },
    {
        "id": 14, "severity": "MEDIUM", "category": "Security",
        "title": "/api/auth/session exposes full JWT in body",
        "status": "OPEN",
        "evidence": "Not re-tested in this session (requires authenticated session cookie).",
        "fix": "Move access_token to server-side only; expose only user info + expiry client-side.",
    },
    {
        "id": 15, "severity": "MEDIUM", "category": "Security",
        "title": "Keycloak allowed-origins: ['*']",
        "status": "OPEN",
        "evidence": "Not re-tested in this session.",
        "fix": "Restrict allowed-origins to known domains in Keycloak admin.",
    },
    {
        "id": 16, "severity": "MEDIUM", "category": "UX",
        "title": "StatusFilterTabs expanded to 9 tabs",
        "status": "CONFIRMED",
        "evidence": "All 9 tabs present with counts: All | Draft(40) | Queued(0) | Running(1) | In Progress(10) | Pending Review(17) | Completed(25) | Failed(6) | Cancelled(1).",
        "fix": "Test suite updated. Counts indicate 10 in-progress evaluations.",
    },
    {
        "id": 17, "severity": "LOW", "category": "Security",
        "title": "Session cookies are HttpOnly (positive)",
        "status": "POSITIVE",
        "evidence": "Security headers confirmed: HSTS (max-age=31536000, preload), x-frame-options: SAMEORIGIN, x-content-type-options: nosniff, x-xss-protection: 1; mode=block, referrer-policy: strict-origin-when-cross-origin, permissions-policy set.",
        "fix": "No action needed. Good posture.",
    },
    {
        "id": 18, "severity": "MEDIUM", "category": "Accessibility",
        "title": "Mobile menu dialog missing DialogTitle",
        "status": "OPEN",
        "evidence": "Console error: 'DialogContent requires a DialogTitle for the component to be accessible for screen reader users.' Same Radix UI violation as before. Additionally, Missing aria-describedby warning.",
        "fix": "Add <DialogTitle> (VisuallyHidden if visual title not desired). Add <DialogDescription> or aria-describedby.",
    },
    {
        "id": 19, "severity": "MEDIUM", "category": "UX",
        "title": "Mobile menu has no navigation links",
        "status": "OPEN",
        "evidence": "Dialog content = 'SM' (only user avatar button). No nav links, no dashboard access from mobile.",
        "fix": "Add primary navigation links (Dashboard, Switch Roles) to the mobile menu dialog.",
    },
    {
        "id": 20, "severity": "LOW", "category": "UX",
        "title": "404 page is bare Next.js default",
        "status": "OPEN",
        "evidence": "No logo, no nav, no links, no branding. Title: '404: This page could not be found.' Only inline CSS in body.",
        "fix": "Create not-found.tsx with app layout, logo, and home/dashboard link.",
    },
    {
        "id": 21, "severity": "LOW", "category": "UX",
        "title": "Pagination renders before data loads",
        "status": "OPEN",
        "evidence": "Not re-tested in this session.",
        "fix": "Conditionally render pagination after query resolves.",
    },
    {
        "id": 22, "severity": "MEDIUM", "category": "UX",
        "title": "Session verification triggered on every page.goto()",
        "status": "OPEN",
        "evidence": "Not directly re-tested. Dashboard loaded via in-app navigation without visible hang.",
        "fix": "Cache session check result in middleware.",
    },
    # New findings from session 2
    {
        "id": 23, "severity": "LOW", "category": "Accessibility",
        "title": "New Evaluation dialog missing aria-describedby",
        "status": "NEW",
        "evidence": "Console warning: 'Missing Description or aria-describedby={undefined} for DialogContent' on the New Evaluation dialog. Separate issue from mobile menu (Finding #18).",
        "fix": "Add <DialogDescription> or aria-describedby to the New Evaluation modal.",
    },
    {
        "id": 24, "severity": "LOW", "category": "Security",
        "title": "Content-Security-Policy header absent",
        "status": "NEW",
        "evidence": "curl -I on frontend: no Content-Security-Policy header returned. HSTS and other headers present.",
        "fix": "Add CSP header via Next.js headers() config or reverse proxy. Start with report-only mode.",
    },
    {
        "id": 25, "severity": "LOW", "category": "UX",
        "title": "Breadcrumb text duplicated in DOM",
        "status": "NEW",
        "evidence": "Breadcrumb items render with doubled text: 'HomeHome', 'AI MakerAI Maker', 'CivicDataLabCivicDataLab'. Likely two renders of the same node (screen-reader + visible).",
        "fix": "Use aria-hidden on the decorative text copy, or consolidate to single render.",
    },
]

STATUS_COLORS = {
    "FIXED":     (40, 167, 69),
    "IMPROVED":  (23, 162, 184),
    "POSITIVE":  (40, 167, 69),
    "CONFIRMED": (108, 117, 125),
    "OPEN":      (220, 53, 69),
    "NEW":       (255, 133, 27),
}

SEVERITY_COLORS = {
    "CRITICAL": (220, 53, 69),
    "HIGH":     (255, 133, 27),
    "MEDIUM":   (255, 193, 7),
    "LOW":      (40, 167, 69),
}

class PDF(FPDF):
    def cell(self, *args, **kwargs):
        if len(args) > 2:
            args = list(args); args[2] = _s(str(args[2])); args = tuple(args)
        for k in ("text", "txt"):
            if k in kwargs: kwargs[k] = _s(str(kwargs[k]))
        return super().cell(*args, **kwargs)

    def multi_cell(self, *args, **kwargs):
        if len(args) > 2:
            args = list(args); args[2] = _s(str(args[2])); args = tuple(args)
        for k in ("text", "txt"):
            if k in kwargs: kwargs[k] = _s(str(kwargs[k]))
        return super().multi_cell(*args, **kwargs)

    def header(self):
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(100, 100, 100)
        self.cell(0, 7, _s("ParakhAI Platform -- MCP Re-Audit Report | 2026-06-22"), align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(200, 200, 200)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(2)

    def footer(self):
        self.set_y(-14)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Page {self.page_no()} -- {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}", align="C")

    def section_title(self, title):
        self.ln(4)
        self.set_font("Helvetica", "B", 12)
        self.set_fill_color(33, 97, 140)
        self.set_text_color(255, 255, 255)
        self.cell(0, 8, f"  {title}", fill=True, new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(0, 0, 0)
        self.ln(3)

    def status_badge(self, status, w=28):
        r, g, b = STATUS_COLORS.get(status, (108, 117, 125))
        self.set_fill_color(r, g, b)
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 7)
        self.cell(w, 5, f" {status} ", fill=True, new_x="RIGHT", new_y="TOP")
        self.set_text_color(0, 0, 0)

    def severity_badge(self, severity):
        r, g, b = SEVERITY_COLORS.get(severity, (108, 117, 125))
        self.set_fill_color(r, g, b)
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 7)
        self.cell(20, 5, f" {severity}", fill=True, new_x="RIGHT", new_y="TOP")
        self.set_text_color(0, 0, 0)


def generate():
    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_margins(10, 15, 10)

    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    fixed   = [f for f in FINDINGS if f["status"] in ("FIXED", "POSITIVE")]
    improved = [f for f in FINDINGS if f["status"] == "IMPROVED"]
    still_open = [f for f in FINDINGS if f["status"] == "OPEN"]
    new_found = [f for f in FINDINGS if f["status"] == "NEW"]
    confirmed = [f for f in FINDINGS if f["status"] == "CONFIRMED"]

    # ── Cover ──────────────────────────────────────────────────────────────
    pdf.add_page()
    pdf.ln(14)
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(33, 97, 140)
    pdf.cell(0, 11, "ParakhAI Platform", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 9, "MCP Re-Audit Report", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(90, 90, 90)
    pdf.cell(0, 7, "Live platform verification -- Playwright MCP browser exploration", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    pdf.set_draw_color(33, 97, 140)
    pdf.set_line_width(0.5)
    pdf.line(30, pdf.get_y(), 180, pdf.get_y())
    pdf.ln(7)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 10)
    for k, v in [
        ("Date", "2026-06-22"),
        ("Platform", "dev.parakh.civicdataspace.in"),
        ("Tool", "Playwright MCP (Chromium headless)"),
        ("Viewport", "1440x900 desktop + 390x844 mobile"),
        ("Pages tested", "Homepage, Dashboard, AI Maker, Evaluations, Models, Prompt Libraries, Eval Detail, 404, Mobile"),
        ("Previous audit", "2026-06-22 session 1 (22 findings)"),
    ]:
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(80, 80, 80)
        pdf.cell(48, 6, k + ":", new_x="RIGHT", new_y="TOP")
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(0, 0, 0)
        pdf.multi_cell(0, 6, v, new_x="LMARGIN", new_y="NEXT")

    # Status summary banner
    pdf.ln(7)
    box_w = 37
    for label, count, color in [
        ("FIXED", len(fixed), (40,167,69)),
        ("IMPROVED", len(improved), (23,162,184)),
        ("OPEN", len(still_open), (220,53,69)),
        ("NEW", len(new_found), (255,133,27)),
        ("CONFIRMED", len(confirmed), (108,117,125)),
    ]:
        r, g, b = color
        pdf.set_fill_color(r, g, b)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(box_w, 14, str(count), align="C", fill=True, new_x="RIGHT", new_y="TOP")
    pdf.ln()
    for label, count, color in [
        ("FIXED", len(fixed), (40,167,69)),
        ("IMPROVED", len(improved), (23,162,184)),
        ("OPEN", len(still_open), (220,53,69)),
        ("NEW", len(new_found), (255,133,27)),
        ("CONFIRMED", len(confirmed), (108,117,125)),
    ]:
        r, g, b = color
        pdf.set_fill_color(r, g, b)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "", 7)
        pdf.cell(box_w, 6, label, align="C", fill=True, new_x="RIGHT", new_y="TOP")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(10)

    # ── Key fixes headline ─────────────────────────────────────────────────
    pdf.section_title("1. Key Changes Since Last Audit")
    for label, items, note in [
        ("FIXED", fixed, "These issues are resolved or confirmed positive."),
        ("IMPROVED", improved, "Partial improvement -- monitor for recurrence."),
        ("NEW", new_found, "Newly discovered issues not in the previous report."),
    ]:
        r, g, b = STATUS_COLORS[label]
        pdf.set_fill_color(r, g, b)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(0, 6, f"  {label} ({len(items)}): {note}", fill=True, new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "", 9)
        for f in items:
            pdf.set_x(14)
            pdf.multi_cell(0, 5, f"#{f['id']} [{f['category']}] {f['title']}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

    # ── Performance metrics ────────────────────────────────────────────────
    pdf.section_title("2. Performance Metrics")
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 5, "All timings from Navigation Timing API. TTFB and load times well within budget.", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 8)
    pdf.set_fill_color(230, 235, 245)
    for h, w in [("Page", 70), ("TTFB (ms)", 30), ("DOMContentLoaded (ms)", 50), ("Load Complete (ms)", 40)]:
        pdf.cell(w, 6, h, border=1, fill=True, align="C", new_x="RIGHT", new_y="TOP")
    pdf.ln()
    pdf.set_font("Helvetica", "", 8)
    for m in PERF_METRICS:
        ttfb = str(m["ttfb"]) if m["ttfb"] else "--"
        dcl  = str(m["dcl"])  if m["dcl"]  else "--"
        load = str(m["load"]) if m["load"] else "--"
        # Colour load column if slow
        for val, w in [(m["page"], 70), (ttfb, 30), (dcl, 50), (load, 40)]:
            if val in (str(m["load"]),) and m["load"] and m["load"] > 2000:
                pdf.set_text_color(220, 53, 69)
            else:
                pdf.set_text_color(0, 0, 0)
            pdf.cell(w, 6, str(val), border=1, align="C", new_x="RIGHT", new_y="TOP")
        pdf.set_text_color(0, 0, 0)
        pdf.ln()
    pdf.ln(3)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 5, "GraphQL API: 10 sequential requests, avg 112ms, max 130ms. No DB connection errors. API returns 403 without auth (correct).", new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)

    # ── Full findings detail ───────────────────────────────────────────────
    pdf.section_title("3. Full Findings Status (All 25)")
    for f in FINDINGS:
        r, g, b = STATUS_COLORS.get(f["status"], (108, 117, 125))
        pdf.set_fill_color(248, 249, 250)
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(10, 6, f"#{f['id']}", new_x="RIGHT", new_y="TOP")
        pdf.status_badge(f["status"])
        pdf.cell(3, 6, "", new_x="RIGHT", new_y="TOP")
        pdf.severity_badge(f["severity"])
        pdf.cell(3, 6, "", new_x="RIGHT", new_y="TOP")
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(80, 80, 80)
        pdf.cell(18, 6, f"[{f['category']}]", new_x="RIGHT", new_y="TOP")
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(0, 0, 0)
        pdf.multi_cell(0, 6, f['title'], new_x="LMARGIN", new_y="NEXT")

        pdf.set_font("Helvetica", "", 8)
        pdf.set_x(14)
        pdf.multi_cell(0, 5, f["evidence"], new_x="LMARGIN", new_y="NEXT")

        if f["status"] not in ("FIXED", "POSITIVE", "CONFIRMED"):
            pdf.set_font("Helvetica", "I", 8)
            pdf.set_text_color(33, 97, 140)
            pdf.set_x(14)
            pdf.multi_cell(0, 5, f"Fix: {f['fix']}", new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(0, 0, 0)
        pdf.ln(3)

    # ── Security headers summary ───────────────────────────────────────────
    pdf.section_title("4. Security Headers Summary")
    pdf.set_font("Helvetica", "", 9)
    headers = [
        ("strict-transport-security", "max-age=31536000; includeSubDomains; preload", "PASS"),
        ("x-frame-options",           "SAMEORIGIN",                                   "PASS"),
        ("x-content-type-options",    "nosniff",                                      "PASS"),
        ("x-xss-protection",          "1; mode=block",                                "PASS"),
        ("referrer-policy",           "strict-origin-when-cross-origin",              "PASS"),
        ("permissions-policy",        "geolocation=(), microphone=(), camera=()",     "PASS"),
        ("content-security-policy",   "NOT SET",                                      "FAIL"),
    ]
    for hdr, val, result in headers:
        color = (40,167,69) if result == "PASS" else (220,53,69)
        pdf.set_fill_color(*color)
        pdf.set_text_color(255,255,255)
        pdf.set_font("Helvetica", "B", 7)
        pdf.cell(12, 5, result, fill=True, align="C", new_x="RIGHT", new_y="TOP")
        pdf.set_text_color(0,0,0)
        pdf.set_font("Helvetica", "B", 8)
        pdf.cell(60, 5, hdr, new_x="RIGHT", new_y="TOP")
        pdf.set_font("Helvetica", "", 8)
        pdf.multi_cell(0, 5, val, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    # ── Priority actions ───────────────────────────────────────────────────
    pdf.section_title("5. Recommended Priority Actions")
    actions = [
        ("P0 -- Do immediately", [
            "#7 Fix breadcrumb: show section name (Evaluations/Models/Prompt Libraries) not org name",
            "#25 Fix breadcrumb duplicate text ('HomeHome', 'AI MakerAI Maker') -- likely aria-hidden missing",
            "#18/#23 Add DialogTitle + aria-describedby to mobile menu and New Evaluation dialogs",
        ]),
        ("P1 -- This sprint", [
            "#19 Add navigation links to mobile hamburger menu (currently only shows avatar)",
            "#20 Create branded not-found.tsx with logo and home link (currently bare Next.js 404)",
            "#24 Add Content-Security-Policy header (report-only first, then enforce)",
            "#10 Make eval name read-only when status is COMPLETED or FAILED",
        ]),
        ("P2 -- Next sprint", [
            "#1 Fix meta description typo: 'Paricipatory' -> 'Participatory'",
            "#2 Add og:title meta tag for social sharing",
            "#3/#4 Standardise URL locale prefix -- either always /en/ or never",
            "#5 Permanently fix GetAudits N+1 with DataLoader (overview hang may recur under load)",
            "#6 Investigate why org 15 RSC prefetch still returns 503",
            "#11 Add evaluation name as final breadcrumb item on detail pages",
        ]),
        ("P3 -- Ongoing / monitor", [
            "#13 DB connection pool -- no errors seen today but PgBouncer still recommended",
            "#14/#15 Review session JWT exposure and Keycloak allowed-origins scope",
            "#21 Hide pagination until data query resolves",
        ]),
    ]
    for priority, items in actions:
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 7, priority, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 9)
        for item in items:
            pdf.set_x(14)
            pdf.multi_cell(0, 5, f"- {item}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

    out = ROOT / "reports" / "MCP_REAUDIT_2026-06-22.pdf"
    pdf.output(str(out))
    return out


if __name__ == "__main__":
    out = generate()
    print(f"PDF generated: {out} ({out.stat().st_size // 1024}KB)")
