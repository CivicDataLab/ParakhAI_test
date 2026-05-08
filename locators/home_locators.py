"""
Selectors for the Parakh homepage.

Keeping selectors in a dedicated module makes it easy to update them without
touching page-action logic, and allows multiple page objects to share the same
element references.
"""


class HomeLocators:
    # ── Navigation bar ────────────────────────────────────────────────────────
    LOGO = "a[href='/']"
    NAV_LOGIN_BUTTON = (
        "a:has-text('LOGIN'), "
        "a:has-text('SIGN UP'), "
        "button:has-text('Login'), "
        "a:has-text('Sign In')"
    )
    NAV_EVALUATION_WORKSPACE = (
        "a[href*='evaluation'], "
        "a:has-text('Evaluation Workspace')"
    )
    HAMBURGER_MENU = (
        "button[aria-label*='menu'], "
        "button[aria-label*='Menu'], "
        "button.hamburger, "
        "[data-testid='mobile-menu-button']"
    )
    MOBILE_NAV_ITEMS = "nav a, [role='navigation'] a"

    # ── Hero section ──────────────────────────────────────────────────────────
    # Include h2 as fallback — some builds promote h2 as the visual hero heading.
    # `>> nth=0` keeps strict-mode safe when the page renders multiple top-level
    # headings (e.g. hero + section header both as h1/h2).
    HERO_HEADING = (
        "h1, "
        "h2, "
        "[class*='hero'] h1, "
        "[class*='hero'] h2, "
        "[class*='Hero'] h1, "
        "[class*='Hero'] h2"
        " >> nth=0"
    )
    # Broad CTA selector — covers common label variations across builds
    GET_STARTED_BUTTON = (
        "a:has-text('Get Started'), "
        "button:has-text('Get Started'), "
        "a:has-text('Get started'), "
        "a:has-text('Explore'), "
        "a:has-text('Try now'), "
        "a:has-text('Learn more'), "
        "[class*='cta'], "
        "[class*='CTA']"
    )
    HERO_SECTION = (
        "section:first-of-type, "
        "[class*='hero'], "
        "[class*='Hero'], "
        "[class*='banner'], "
        "[class*='Banner']"
    )

    # ── Feature tabs ──────────────────────────────────────────────────────────
    FEATURE_TABS_CONTAINER = "[role='tablist'], [class*='tab'], [class*='Tab']"
    TAB_BUTTON = "[role='tab'], button[class*='tab'], button[class*='Tab']"
    ACTIVE_TAB = (
        "[role='tab'][aria-selected='true'], "
        "[class*='tab'][class*='active'], "
        "[class*='Tab'][class*='Active']"
    )
    TAB_CONTENT = (
        "[role='tabpanel'], "
        "[class*='tab-content'], "
        "[class*='TabContent'], "
        "[class*='tabPanel']"
    )

    # ── Footer ────────────────────────────────────────────────────────────────
    FOOTER = "footer"
    SOCIAL_LINKS = (
        "footer a[aria-label], "
        "footer a[href*='twitter'], "
        "footer a[href*='linkedin'], "
        "footer a[href*='github'], "
        "footer a[href*='youtube'], "
        "footer a[href*='facebook']"
    )
    CIVICDATALAB_LINK = "footer a[href*='civicdatalab']"
