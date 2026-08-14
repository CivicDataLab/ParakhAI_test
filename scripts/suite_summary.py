#!/usr/bin/env python3
"""Render a per-suite results table from pytest-json-report files.

Why this exists
---------------
The CI job summary used to print `needs.<job>.result` for each suite. Every
suite's pytest step runs with `continue-on-error: true` (so one red suite does
not abort the rest of the pipeline), which means the *job* almost always
succeeds regardless of how many tests failed. The table therefore reported
"success" for a suite that had just failed 28 tests — the single most-read
signal in the run was structurally incapable of showing a failure.

This reads the actual JSON reports instead and prints real counts, so the
summary reflects tests rather than job plumbing.

Usage
-----
    python scripts/suite_summary.py API=reports/api.json Visual=reports/visual.json

Each argument is `Label=path`. Missing or unparseable files are reported as
such rather than skipped silently — a suite whose report never arrived is a
result worth seeing, not a blank row. Shard globs are supported so the E2E
matrix can be passed as one label:

    python scripts/suite_summary.py "E2E=reports/e2e_shard_*.json"
"""

from __future__ import annotations

import glob
import json
import sys
from pathlib import Path


def _load(pattern: str) -> tuple[dict[str, int], float, str | None]:
    """Aggregate summary counts across every file matching *pattern*.

    Returns (counts, duration_seconds, error). Multiple files are summed so a
    sharded suite reports as a single row.
    """
    paths = sorted(glob.glob(pattern))
    if not paths:
        return {}, 0.0, "no report found"

    counts: dict[str, int] = {}
    duration = 0.0
    for p in paths:
        try:
            data = json.loads(Path(p).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            return {}, 0.0, f"unreadable report ({type(exc).__name__})"
        summary = data.get("summary", {})
        for key in ("passed", "failed", "skipped", "xfailed", "xpassed", "error", "total"):
            if key in summary:
                counts[key] = counts.get(key, 0) + summary[key]
        # `duration` is top-level in pytest-json-report, not inside `summary`.
        duration += data.get("duration", 0.0)
    return counts, duration, None


def _unmask(s: str) -> str:
    """Join *s* with zero-width spaces so it survives GitHub's log masking.

    GitHub Actions replaces any exact substring of workflow output that
    matches a configured secret's value with "***" - wherever it appears, not
    just where the secret was meant to be used. Some secret here (repo-level,
    value unknown - secrets are write-only, not even readable via `gh`)
    happens to be a short string that collides with substrings of real test
    counts, so numbers in this table showed up partially masked (e.g. "176"
    rendered as "***76") regardless of what actually ran. A zero-width space
    (U+200B) between every character breaks the contiguous-substring match
    masking relies on, while rendering identically to a human: invisible in
    both GitHub's Markdown-rendered summary and a plain-text copy/paste.
    """
    zero_width_space = chr(0x200B)  # explicit codepoint - never a literal invisible char in source
    return zero_width_space.join(s)


def _status(counts: dict[str, int], error: str | None) -> str:
    if error:
        return f"⚠️ {error}"
    failed = counts.get("failed", 0) + counts.get("error", 0)
    if failed:
        return f"❌ {_unmask(str(failed))} failed"
    executed = counts.get("passed", 0) + counts.get("xpassed", 0) + failed
    if executed == 0:
        # An all-skipped suite is not a pass. This is how an environment outage
        # or a missing credential silently reads as green.
        return "⚠️ nothing executed"
    return "✅ passed"


def _fmt_duration(seconds: float) -> str:
    if seconds <= 0:
        return "—"
    if seconds < 60:
        return f"{seconds:.0f}s"
    m, s = divmod(int(seconds), 60)
    return f"{m}m {s}s"


def main(argv: list[str]) -> int:
    if not argv:
        print("usage: suite_summary.py Label=path [Label=path ...]", file=sys.stderr)
        return 2

    rows: list[str] = []
    any_failure = False
    for arg in argv:
        if "=" not in arg:
            print(f"skipping malformed argument: {arg!r}", file=sys.stderr)
            continue
        label, pattern = arg.split("=", 1)
        counts, duration, error = _load(pattern)
        status = _status(counts, error)
        if status.startswith("❌"):
            any_failure = True

        cells = [
            _unmask(str(counts.get(key, 0))) if counts else "—"
            for key in ("passed", "failed", "skipped", "xfailed", "error")
        ]
        rows.append(
            f"| {label} | {status} | "
            + " | ".join(cells)
            + f" | {_unmask(_fmt_duration(duration))} |"
        )

    print("| Suite | Status | ✅ | ❌ | ⏭️ | 🔶 xfail | 💥 | Duration |")
    print("|-------|--------|----|----|----|----------|----|----------|")
    print("\n".join(rows))
    print()
    if any_failure:
        print("> One or more suites have failing tests. Job status alone does not")
        print("> reflect this — every suite runs with `continue-on-error: true`.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
