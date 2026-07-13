"""
Locators for the Evaluation Workspace entry point and shared navigation.
URL: /dashboard
"""


class WorkspaceLocators:
    # ── Role selection page ────────────────────────────────────────────────────
    ROLE_SELECTION_HEADING = "h2, h3, [class*='heading'], [class*='title']"
    # Role cards render a heading span (e.g. "Evaluator") AND a body-copy span
    # (e.g. "For expert as evaluator") inside the same <a>. Plain `text=Evaluator`
    # substring-matches BOTH spans independently (case-insensitive: "evaluator" in
    # the body copy too) -> Locator strict-mode violation on click(). Scope to the
    # single containing <a> instead (2026-07-13).
    AI_MAKER_CARD = "a:has-text('AI Maker')"
    EVALUATOR_CARD = "a:has-text('Evaluator')"
    ROLE_CARD = "[class*='card'], [class*='Card'], [class*='role']"

    # ── Global nav ─────────────────────────────────────────────────────────────
    NAV_EVALUATION_WORKSPACE = "text=Evaluation Workspace"
    NAV_USER_AVATAR = "[class*='avatar'], [class*='Avatar'], text=MSM"
    PARAKH_LOGO = "text=ParakhAI, img[alt*='Parakh'], a[href='/']"

    # ── Breadcrumb ─────────────────────────────────────────────────────────────
    BREADCRUMB = "nav[aria-label*='breadcrumb'], [class*='breadcrumb'], [class*='Breadcrumb']"
    BREADCRUMB_HOME = "a:text('Home')"
    BREADCRUMB_EVALUATION_WORKSPACE = "text=Evaluation Workspace"

    # ── Org selection (AI Maker → Select Organisation) ─────────────────────────
    ORG_SELECTION_HEADING = "text=Select Organization"
    ORG_CIVICDATALAB_CARD = "text=CivicdataLab"
    # Each org card is a link into that org's AI Maker dashboard. Anchoring
    # on the href is more stable than guessing at the wrapper class name.
    ORG_CARD = "a[href*='/dashboard/ai-maker/']"

    # ── Sidebar (shared) ───────────────────────────────────────────────────────
    SIDEBAR_HOME = "nav a:text('Home'), [class*='sidebar'] a:text('Home')"
    SIDEBAR_SWITCH_ROLES = "text=Switch Roles"

    # ── Footer ─────────────────────────────────────────────────────────────────
    FOOTER = "footer, [class*='footer'], [class*='Footer']"
    FOOTER_MADE_BY = "text=made by"
