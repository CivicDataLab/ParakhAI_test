"""
SEO metadata checks — canonical link and Open Graph/Twitter Card tags.

Pending coverage for CivicDataLab/ParakhAI-frontend#444, which adds these tags
to `app/layout.tsx`. Gated with `pending_pr` so it only runs once that PR
merges (see conftest.py's `_pending_pr_state`).
"""

import re

import pytest
import requests

from utils.config import Config

pytestmark = [pytest.mark.api, pytest.mark.pending_pr("ParakhAI-frontend#444")]

BASE = Config.BASE_URL.rstrip("/")


class TestSEOMetadata:
    def test_homepage_has_canonical_link(self, api_client: requests.Session):
        """The homepage must declare a canonical <link> tag (PR #444)."""
        resp = api_client.get(BASE + "/", allow_redirects=True, timeout=15)
        assert resp.status_code == 200, (
            f"Homepage returned {resp.status_code}, expected 200"
        )
        match = re.search(r'<link[^>]+rel=["\']canonical["\'][^>]*>', resp.text, re.I)
        assert match, "No <link rel=\"canonical\"> tag found on the homepage"
        href_match = re.search(r'href=["\']([^"\']+)["\']', match.group(0), re.I)
        assert href_match, f"canonical tag has no href: {match.group(0)}"
        assert href_match.group(1).startswith("http"), (
            f"canonical href is not an absolute URL: {href_match.group(1)}"
        )

    def test_homepage_has_open_graph_tags(self, api_client: requests.Session):
        """The homepage must declare og:title, og:description and og:url (PR #444)."""
        resp = api_client.get(BASE + "/", allow_redirects=True, timeout=15)
        html = resp.text
        required_og_props = ["og:title", "og:description", "og:url"]
        missing = [
            prop
            for prop in required_og_props
            if not re.search(
                rf'<meta[^>]+property=["\']{re.escape(prop)}["\']', html, re.I
            )
        ]
        assert not missing, f"Missing Open Graph meta tags: {missing}"

    def test_homepage_has_twitter_card_tag(self, api_client: requests.Session):
        """The homepage must declare a twitter:card meta tag (PR #444)."""
        resp = api_client.get(BASE + "/", allow_redirects=True, timeout=15)
        match = re.search(
            r'<meta[^>]+name=["\']twitter:card["\'][^>]*>', resp.text, re.I
        )
        assert match, "No <meta name=\"twitter:card\"> tag found on the homepage"
