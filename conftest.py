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
