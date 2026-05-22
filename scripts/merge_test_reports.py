"""
Merge multiple pytest-json-report shard files into a combined JSON + Markdown summary.

Usage:
    python scripts/merge_test_reports.py shard1.json shard2.json shard3.json \
        --output reports/e2e_combined.json \
        --markdown reports/e2e_summary.md
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def load(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        print(f"Warning: shard report not found: {path}", file=sys.stderr)
        return {}
    return json.loads(p.read_text())


def merge(shards: list[dict]) -> dict:
    combined: dict = {
        "created": None,
        "duration": 0.0,
        "exitcode": 0,
        "root": "",
        "environment": {},
        "summary": {
            "passed": 0,
            "failed": 0,
            "error": 0,
            "skipped": 0,
            "xfailed": 0,
            "xpassed": 0,
            "warnings": 0,
            "total": 0,
        },
        "collectors": [],
        "tests": [],
    }

    for shard in shards:
        if not shard:
            continue
        combined["duration"] += shard.get("duration", 0.0)
        if combined["created"] is None:
            combined["created"] = shard.get("created")
        if not combined["root"]:
            combined["root"] = shard.get("root", "")
        if not combined["environment"]:
            combined["environment"] = shard.get("environment", {})

        s = shard.get("summary", {})
        for key in ("passed", "failed", "error", "skipped", "xfailed", "xpassed", "warnings", "total"):
            combined["summary"][key] += s.get(key, 0)

        combined["tests"].extend(shard.get("tests", []))
        combined["collectors"].extend(shard.get("collectors", []))

        # escalate exitcode (0=OK, 1=tests failed, 2=interrupted, 3=internal error)
        combined["exitcode"] = max(combined["exitcode"], shard.get("exitcode", 0))

    return combined


def to_markdown(summary: dict, duration: float) -> str:
    s = summary
    total = s.get("total", 0)
    passed = s.get("passed", 0)
    failed = s.get("failed", 0)
    skipped = s.get("skipped", 0)
    xfailed = s.get("xfailed", 0)
    xpassed = s.get("xpassed", 0)
    errors = s.get("error", 0)

    status = "PASS" if failed == 0 and errors == 0 else "FAIL"
    icon = "✅" if status == "PASS" else "❌"

    lines = [
        f"## E2E Test Results {icon}",
        "",
        f"| Metric | Count |",
        f"|--------|-------|",
        f"| Total  | {total} |",
        f"| Passed | {passed} |",
        f"| Failed | {failed} |",
        f"| Skipped | {skipped} |",
        f"| xFailed (expected) | {xfailed} |",
        f"| xPassed (unexpected) | {xpassed} |",
        f"| Errors | {errors} |",
        f"| Duration | {duration:.1f}s (wall: ~{duration/3:.0f}s across 3 shards) |",
        "",
    ]

    if failed > 0 or errors > 0:
        lines.append("### Failed / Errored Tests")
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Merge pytest-json-report shard files")
    parser.add_argument("shards", nargs="+", help="Shard JSON report paths")
    parser.add_argument("--output", default="reports/e2e_combined.json", help="Combined JSON output path")
    parser.add_argument("--markdown", default="reports/e2e_summary.md", help="Markdown summary output path")
    args = parser.parse_args()

    shards = [load(s) for s in args.shards]
    combined = merge(shards)

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(combined, indent=2))
    print(f"Combined report: {out} ({combined['summary']['total']} tests)")

    md = Path(args.markdown)
    md.parent.mkdir(parents=True, exist_ok=True)
    md.write_text(to_markdown(combined["summary"], combined["duration"]))
    print(f"Markdown summary: {md}")


if __name__ == "__main__":
    main()
