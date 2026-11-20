"""
"Add Prompt Dataset" (ParakhAI-frontend#484): the button opens a confirm
dialog; "Yes, continue" opens the org's CivicDataSpace dataset listing in a new
tab (prompt libraries are created there as PROMPT datasets); "No" closes it.
"""

import re
from urllib.parse import unquote

import pytest
from playwright.sync_api import Page

from pages.prompt_libraries_page import PromptLibrariesPage

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.regression,
    pytest.mark.auth,
    pytest.mark.pending_pr("ParakhAI-frontend#484"),
]


@pytest.fixture
def pl(authenticated_page_fast: Page) -> PromptLibrariesPage:
    return PromptLibrariesPage(authenticated_page_fast).go_to_prompt_libraries()


def test_cancel_closes_dialog_without_redirect(pl: PromptLibrariesPage):
    pages_before = len(pl.page.context.pages)
    pl.open_add_library_dialog()
    pl.cancel_redirect()
    assert pl.is_redirect_dialog_closed(), "'No' must close the redirect dialog"
    assert len(pl.page.context.pages) == pages_before, "'No' must not open a new tab"
    assert "/prompt-libraries" in pl.page.url


def test_continue_opens_org_dataset_page_on_cds(pl: PromptLibrariesPage):
    pl.open_add_library_dialog()
    cds_tab = pl.continue_redirect()
    cds_tab.wait_for_load_state("domcontentloaded")
    # Signed-out CDS bounces through /login?callbackUrl=..., so match the decoded URL.
    url = unquote(cds_tab.url)
    cds_tab.close()
    assert "civicdataspace.in" in url, f"Expected a CivicDataSpace URL, got {url}"
    assert re.search(r"/dashboard/organization/[^/?#]+/dataset(?:[/?#]|$)", url), (
        f"Expected the org's CDS dataset listing, got {url}"
    )
