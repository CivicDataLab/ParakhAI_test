"""Responsive check: the Start-an-Evaluation modal at phone and tablet widths.

Read-only (never clicks Start Evaluation), so no drafts are created.
"""

import pytest

from pages.new_evaluation_page import NewEvaluationPage

pytestmark = [pytest.mark.e2e, pytest.mark.mobile, pytest.mark.smoke, pytest.mark.auth]


@pytest.mark.parametrize("size", [(390, 844), (768, 1024)], ids=["phone", "tablet"])
def test_new_evaluation_modal_fits_viewport(authenticated_page_fast, sandbox_org, size):
    page = authenticated_page_fast
    page.set_viewport_size({"width": size[0], "height": size[1]})
    nep = NewEvaluationPage(page, org_id=int(sandbox_org))
    nep.go_to_evaluations_list()
    nep.click_new_evaluation()
    assert nep.is_modal_visible(), "New Evaluation modal must open"
    overflow = page.evaluate("document.documentElement.scrollWidth - window.innerWidth")
    assert overflow <= 1, f"page scrolls horizontally by {overflow}px at {size}"
    box = page.get_by_role("dialog").first.bounding_box()
    assert box and box["x"] >= -1 and box["x"] + box["width"] <= size[0] + 1, f"modal overflows viewport: {box}"
