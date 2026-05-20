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
    # The homepage renders tabs as plain <button> elements (no role="tab"),
    # so selectors are anchored on the four known tab labels. If the labels
    # change, update FEATURE_TAB_LABELS and the OR-chain below in lockstep.
    FEATURE_TAB_LABELS = (
        "Automation-assisted Evaluation Environment",
        "Expert-led Evaluations",
        "Sector-specific Test Cases",
        "Evaluation History & Reports",
    )
    FEATURE_TABS_CONTAINER = (
        "section:has(button:has-text(\"Automation-assisted Evaluation Environment\"))"
    )
    TAB_BUTTON = (
        "button:has-text(\"Automation-assisted Evaluation Environment\"), "
        "button:has-text(\"Expert-led Evaluations\"), "
        "button:has-text(\"Sector-specific Test Cases\"), "
        "button:has-text(\"Evaluation History & Reports\")"
    )
    # Active tab is distinguished by the design-token background class
    # `bg-[#E8E4FF]` (lavender). The previous selector also included
    # `[class*='6849EE']` (violet text), but that overmatches: the homepage's
    # "Get Started" CTAs include `hover:bg-[#6849EE]` in their static class
    # list, so the substring matches even though it only activates on hover.
    # `get_active_tab_text()` was returning "Get Started" instead of the
    # active tab label. Stick to the unique lavender-background signature.
    # ARIA fallback kept in case the build adds proper a11y semantics later.
    ACTIVE_TAB = (
        "[role='tab'][aria-selected='true'], "
        "button[class*='E8E4FF']"
    )
    # Content panel sits as a sibling of the tab-button row inside the same
    # flex column wrapper. Anchor by the section, then pick the inner column
    # that contains an <img> (every tab content has an illustration).
    TAB_CONTENT = (
        "[role='tabpanel'], "
        "section:has(button:has-text(\"Automation-assisted Evaluation Environment\")) "
        "div.flex.flex-col.items-center:has(img)"
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
