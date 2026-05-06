"""
Selectors for the Parakh dashboard (authenticated area).
"""


class DashboardLocators:
    # ── Authenticated-state indicators ────────────────────────────────────────
    USER_MENU = (
        "button[aria-label='Open profile'], "
        "button[aria-haspopup='dialog'], "
        "[data-testid='user-menu'], "
        "[aria-label*='account']"
    )
    DASHBOARD_HEADING = (
        "h1, h2, "
        "[class*='dashboard-title'], "
        "[class*='DashboardTitle']"
    )
    NAV_LINKS = "nav a, [role='navigation'] a"
    SIGN_OUT_BUTTON = (
        "button:has-text('Log Out'), "
        "button:has-text('Sign out'), "
        "button:has-text('Sign Out'), "
        "a:has-text('Log Out'), "
        "a:has-text('Logout'), "
        "[role='menuitem']:has-text('Log Out')"
    )
    BREADCRUMB = "[aria-label='breadcrumb'], [class*='breadcrumb']"

    # ── Auth-guard / redirect indicators ─────────────────────────────────────
    LOGIN_REDIRECT_INDICATOR = (
        "input[name='username'], "
        "input[type='email'], "
        "[class*='login'], "
        "#kc-form-login"
    )
