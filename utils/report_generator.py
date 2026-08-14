"""
Markdown report generator for the Parakh test framework.

Reads the JSON output produced by pytest-json-report and writes a human-readable
TEST_REPORT.md file to the reports/ directory.

Mirrors the report_generator.py pattern from CivicDataSpace-test, adapted for
pytest-json-report's schema and updated to be pure-stdlib (no reportlab
dependency needed for the Markdown-only version).

Usage (called automatically by the root conftest.py after every run):
    from utils.report_generator import generate_markdown_report
    generate_markdown_report(Path("reports/report.json"))
"""

import json
from datetime import UTC, datetime
from pathlib import Path

from utils.config import Config


def _status_icon(outcome: str) -> str:
    return {"passed": "✅", "failed": "❌", "skipped": "⏭️", "error": "💥"}.get(outcome, "❓")


def _duration_str(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.2f}s"
    m, s = divmod(int(seconds), 60)
    return f"{m}m {s}s"


def _test_duration(test: dict) -> float:
    """Total wall time for a test, summed across its phases.

    pytest-json-report records duration per phase (`setup`/`call`/`teardown`)
    and puts no `duration` key on the test object itself, so reading
    `test["duration"]` always fell back to 0.0 — every per-test duration in the
    report rendered as "0.00s". Setup is worth including, not just `call`: the
    authenticated fixtures do real work (SSO login, storage-state refresh), and
    attributing none of it to the test hides the slowest part of the suite.
    """
    return sum(
        test.get(phase, {}).get("duration", 0.0)
        for phase in ("setup", "call", "teardown")
    )


def generate_markdown_report(json_path: Path) -> Path:
    """
    Read *json_path* (pytest-json-report output) and write a Markdown report.

    Returns the Path of the generated Markdown file.
    """
    with json_path.open(encoding="utf-8") as fh:
        data = json.load(fh)

    summary = data.get("summary", {})
    tests = data.get("tests", [])
    created_ts = data.get("created", datetime.now(UTC).timestamp())
    created_dt = datetime.fromtimestamp(created_ts, tz=UTC).strftime("%Y-%m-%d %H:%M UTC")

    total = summary.get("total", len(tests))
    passed = summary.get("passed", 0)
    failed = summary.get("failed", 0)
    skipped = summary.get("skipped", 0)
    errors = summary.get("error", 0)
    # xfail/xpass are their own outcomes in pytest-json-report. Without them the
    # rows below silently fail to add up to `total` on any suite using xfail —
    # which is most of them (see docs/app_bugs.md).
    xfailed = summary.get("xfailed", 0)
    xpassed = summary.get("xpassed", 0)
    # `duration` is a TOP-LEVEL key in pytest-json-report, not a summary key.
    # Reading it from `summary` silently returned the 0.0 default on every run,
    # so every report claimed "0.00s" regardless of actual runtime.
    duration = data.get("duration", summary.get("duration", 0.0))

    # Pass rate over *executed* tests only. Counting skips in the denominator
    # made a run that skipped almost everything look like a catastrophic failure
    # (0 passed / 1 skipped rendered as "0.0%"), which is exactly backwards —
    # a skip is the absence of a result, not a failed one.
    executed = passed + failed + errors + xpassed
    pass_rate = f"{(passed + xpassed) / executed * 100:.1f}%" if executed else "n/a"

    # A run where nothing executed is NOT a pass. The old check was
    # `failed == 0 and errors == 0`, so an all-skipped run — including one where
    # every test was skipped because the environment was down — reported
    # "✅ PASSED". That is the same vacuous-green failure mode this framework
    # keeps hitting elsewhere; report it honestly instead.
    if failed or errors:
        overall = "❌ FAILED"
    elif executed == 0:
        overall = "⚠️ NO TESTS EXECUTED" + (f" ({skipped} skipped)" if skipped else "")
    else:
        overall = "✅ PASSED"

    lines: list[str] = []

    # ── Header ────────────────────────────────────────────────────────────────
    lines += [
        "# Parakh Test Framework — Test Report",
        "",
        f"**Generated:** {created_dt}  ",
        f"**Environment:** `{Config.ENVIRONMENT}` — {Config.BASE_URL}  ",
        f"**Browser:** `{Config.BROWSER}`  ",
        f"**Overall result:** {overall}",
        "",
    ]

    # ── Summary table ─────────────────────────────────────────────────────────
    lines += [
        "## Summary",
        "",
        "| Metric | Value |",
        "| ------ | ----- |",
        f"| Total tests | {total} |",
        f"| Passed | {passed} ✅ |",
        f"| Failed | {failed} ❌ |",
        f"| Skipped | {skipped} ⏭️ |",
        f"| xfailed | {xfailed} 🔶 |",
        f"| xpassed | {xpassed} 🔷 |",
        f"| Errors | {errors} 💥 |",
        f"| Pass rate | {pass_rate} |",
        f"| Duration | {_duration_str(duration)} |",
        "",
    ]

    # ── Results by test type (marker) ─────────────────────────────────────────
    # Group tests by the first path segment after tests/ (e2e, api, etc.)
    grouped: dict[str, list[dict]] = {}
    for t in tests:
        node_id: str = t.get("nodeid", "")
        # e.g.  tests/e2e/test_auth.py::TestClass::test_foo  →  e2e
        parts = node_id.split("/")
        group = parts[1] if len(parts) >= 3 else "other"
        grouped.setdefault(group, []).append(t)

    lines += ["## Results by Suite", ""]
    for group, group_tests in sorted(grouped.items()):
        g_passed = sum(1 for t in group_tests if t.get("outcome") == "passed")
        g_failed = sum(1 for t in group_tests if t.get("outcome") == "failed")
        g_skipped = sum(1 for t in group_tests if t.get("outcome") == "skipped")
        # Included so the per-suite counts reconcile with the suite total; without
        # it an xfail-heavy suite shows e.g. "21 tests — 13/0/3" and looks like 5
        # results went missing.
        g_xfailed = sum(1 for t in group_tests if t.get("outcome") == "xfailed")
        g_xpassed = sum(1 for t in group_tests if t.get("outcome") == "xpassed")
        lines += [
            f"### {group.upper()} ({len(group_tests)} tests — "
            f"✅ {g_passed} / ❌ {g_failed} / ⏭️ {g_skipped}"
            f" / 🔶 {g_xfailed} / 🔷 {g_xpassed})",
            "",
            "| Test | Result | Duration |",
            "| ---- | ------ | -------- |",
        ]
        for t in group_tests:
            outcome = t.get("outcome", "unknown")
            icon = _status_icon(outcome)
            name = t.get("nodeid", "").split("::")[-1]
            dur = _duration_str(_test_duration(t))
            lines.append(f"| `{name}` | {icon} {outcome} | {dur} |")
        lines.append("")

    # ── Failures detail ───────────────────────────────────────────────────────
    failures = [t for t in tests if t.get("outcome") in ("failed", "error")]
    if failures:
        lines += ["## Failure Details", ""]
        for t in failures:
            outcome = t.get("outcome", "failed")
            lines += [
                f"### {_status_icon(outcome)} `{t.get('nodeid', '')}`",
                "",
            ]
            call = t.get("call", {})
            longrepr = call.get("longrepr", "")
            if longrepr:
                lines += ["```", str(longrepr)[:2000], "```", ""]

            # Screenshot attached via user_properties
            for prop in t.get("user_properties", []):
                if isinstance(prop, dict) and "screenshot" in prop:
                    lines += [f"**Screenshot:** `{prop['screenshot']}`", ""]
                elif isinstance(prop, (list, tuple)) and len(prop) == 2 and prop[0] == "screenshot":
                    lines += [f"**Screenshot:** `{prop[1]}`", ""]

    # ── Footer ────────────────────────────────────────────────────────────────
    lines += [
        "---",
        "",
        "_Generated by the Parakh Test Framework report generator._",
    ]

    # ── Write file ────────────────────────────────────────────────────────────
    Config.ensure_dirs()
    out_path = Config.REPORTS_DIR / "TEST_REPORT.md"
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path
