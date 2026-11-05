"""
Content checks for crawler-facing static endpoints.

`test_api.py::test_sitemap_accessible` only asserts HTTP 200 and so passes when
`/sitemap.xml` is answered with the homepage HTML shell (a "soft 404"). These
tests assert what the response actually *is*.
"""

import xml.etree.ElementTree as ET

import pytest
import requests

from utils.config import Config

pytestmark = [pytest.mark.api, pytest.mark.regression]

BASE = Config.BASE_URL.rstrip("/")
_SITEMAP_ROOTS = {"urlset", "sitemapindex"}


class TestSitemap:
    @pytest.mark.xfail(
        strict=True,
        reason="App bug #35: /sitemap.xml answers 200 with the HTML app shell instead of a sitemap or a 404 — see docs/app_bugs.md",
    )
    def test_sitemap_is_xml_or_not_found(self, api_client: requests.Session):
        """/sitemap.xml is either a real sitemap document or a 404 — never a 200 HTML page."""
        try:
            resp = api_client.get(BASE + "/sitemap.xml", timeout=15, allow_redirects=False)
        except requests.exceptions.ConnectionError:
            pytest.skip("Frontend unreachable")

        if resp.status_code == 404:
            return  # no sitemap published: an honest 404 is acceptable
        assert resp.status_code == 200, f"/sitemap.xml returned {resp.status_code}"

        content_type = resp.headers.get("content-type", "")
        assert "xml" in content_type.lower(), (
            f"/sitemap.xml returned 200 with Content-Type '{content_type}' "
            f"(body starts: {resp.text[:60]!r}) — crawlers expect XML or a 404."
        )
        root = ET.fromstring(resp.content)  # raises ParseError on HTML
        assert root.tag.rsplit("}", 1)[-1] in _SITEMAP_ROOTS, (
            f"/sitemap.xml root element is <{root.tag}>, expected <urlset> or <sitemapindex>"
        )
