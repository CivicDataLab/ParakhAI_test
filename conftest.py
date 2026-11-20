"""
Root-level conftest.py — session-wide hooks that run outside the test
collection tree.

Why a root conftest in addition to tests/conftest.py?
  - pytest_sessionstart / pytest_sessionfinish hooks placed here run even
    when only a subset of the test suite is collected, making them reliable
    for session-level logging and report generation.
  - Keeps tests/conftest.py focused on fixtures.
"""

import logging

import pytest

from utils.config import Config
from utils.report_generator import generate_markdown_report

logger = logging.getLogger(__name__)


def pytest_sessionstart(session: pytest.Session) -> None:
    """Log a config summary at the start of every test run."""
    summary = Config.summary()
    logger.info("=" * 60)
    logger.info("Parakh Test Framework — session starting")
    for key, value in summary.items():
        logger.info("  %-22s %s", key, value)
    logger.info("=" * 60)


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """
    After the run completes, generate a Markdown summary report from the
    JSON report produced by pytest-json-report.

    The Markdown file is written to reports/TEST_REPORT.md.
    This mirrors the pattern in CivicDataSpace-test and gives a human-readable
    artefact that CI can upload alongside the HTML report.
    """
    json_path = Config.JSON_REPORT_FILE
    if json_path.exists():
        try:
            md_path = generate_markdown_report(json_path)
            logger.info("Markdown report written to %s", md_path)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not generate Markdown report: %s", exc)
    else:
        logger.debug("JSON report not found at %s — skipping Markdown generation", json_path)


# --- pending_pr: tests written for an open product PR run only once it merges ---
import functools as _functools
import os
import json as _json
import urllib.request as _urlreq


@_functools.lru_cache(maxsize=None)
def _pending_pr_state(ref):
    """Return None if `ref` ("Repo#N" or "owner/Repo#N") is merged, else a skip reason."""
    repo, num = ref.split("#")
    if "/" not in repo:
        repo = f"CivicDataLab/{repo}"
    req = _urlreq.Request(f"https://api.github.com/repos/{repo}/pulls/{num}",
                          headers={"Accept": "application/vnd.github+json"})
    token = os.getenv("GH_PR_TOKEN") or os.getenv("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with _urlreq.urlopen(req, timeout=10) as resp:
            pr = _json.load(resp)
        if not pr.get("merged_at"):
            return f"pending_pr {ref}: not merged yet"
        # Merged isn't deployed: dev and main drift apart, and a PR merged to main
        # never reaches dev until a back-merge. Open the gate only once the merge
        # commit is on the branch that deploys the environment under test.
        branch = "dev" if "://dev." in Config.BASE_URL else "main"
        req.full_url = f"https://api.github.com/repos/{repo}/compare/{branch}...{pr['merge_commit_sha']}"
        with _urlreq.urlopen(req, timeout=10) as resp:
            status = _json.load(resp).get("status")
    except Exception as e:  # 404 on a private repo without GH_PR_TOKEN lands here too
        return f"pending_pr {ref}: could not read PR state ({e})"
    return None if status in ("behind", "identical") else f"pending_pr {ref}: merged, not on {branch} yet"


def pytest_collection_modifyitems(config, items):
    for item in items:
        marker = item.get_closest_marker("pending_pr")
        if marker:
            reason = _pending_pr_state(marker.args[0])
            if reason:
                item.add_marker(pytest.mark.skip(reason=reason))
