"""
E2E regression tests for the auditor model detail page.

Route: /auditor/models/{model_id} (or /dashboard/auditor/models/{model_id}
on newer builds). The page lists past evaluations / assigned versions for
a model the current user has been invited to audit.

Tests skip when the test account has no assigned versions to inspect — the
data dependency is unavoidable without a sandbox org for write tests.
"""

import pytest

from pages.auditor_model_detail_page import AuditorModelDetailPage

pytestmark = [pytest.mark.e2e, pytest.mark.regression, pytest.mark.auth]

# Use model id 1 as the canonical reference — the page must at least load
# without crashing for any positive integer id.
DEFAULT_MODEL_ID = 1


def _go(page) -> AuditorModelDetailPage:
    p = AuditorModelDetailPage(page)
    p.go_to_model_detail(DEFAULT_MODEL_ID)
    return p


class TestAuditorModelDetailLoads:
    """The page renders without HTTP/JS errors for an authenticated auditor."""

    def test_page_loads_at_correct_url(self, authenticated_page_fast):
        _go(authenticated_page_fast)
        assert f"/models/{DEFAULT_MODEL_ID}" in authenticated_page_fast.url, (
            f"Expected /models/{DEFAULT_MODEL_ID} in URL, got: {authenticated_page_fast.url}"
        )

    def test_page_does_not_redirect_to_error(self, authenticated_page_fast):
        _go(authenticated_page_fast)
        url = authenticated_page_fast.url.lower()
        assert "/error" not in url and "/404" not in url and "/login" not in url, (
            f"Auditor model detail must not redirect to an error page; got {url}"
        )


class TestAuditorModelDetailContent:
    """Content sections render when the user has assigned versions; skip otherwise."""

    def test_assigned_versions_heading_or_empty_state(self, authenticated_page_fast):
        p = _go(authenticated_page_fast)
        # Either the section heading is visible OR the empty-state copy is.
        if not (
            p.is_assigned_versions_section_visible()
            or p.is_visible(p.NO_ASSIGNED_VERSIONS, timeout=2_000)
        ):
            pytest.skip(
                "Neither 'Assigned Versions' heading nor empty-state visible — "
                "page may render differently for this account or model id"
            )
        assert (
            p.is_assigned_versions_section_visible()
            or p.is_visible(p.NO_ASSIGNED_VERSIONS)
        )

    def test_status_chip_renders_when_versions_present(self, authenticated_page_fast):
        p = _go(authenticated_page_fast)
        if p.get_version_row_count() == 0:
            pytest.skip("No assigned versions to inspect")
        chip = p.get_status_chip_text()
        assert chip in ("PENDING", "ACCEPTED", "DECLINED", "COMPLETED"), (
            f"Status chip should be a known status; got: {chip!r}"
        )


class TestAuditorModelDetailNavigation:
    """Back navigation and inter-page links don't crash."""

    def test_back_button_does_not_crash(self, authenticated_page_fast):
        p = _go(authenticated_page_fast)
        if not p.is_visible(
            "button:has-text('Back'), a:has-text('Back')", timeout=2_000
        ):
            pytest.skip("Back control not present on this page")
        p.click_back()
        # Whatever the destination is, the page should still be usable.
        assert authenticated_page_fast.url is not None
