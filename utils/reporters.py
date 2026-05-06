"""
Custom reporting helpers for the Parakh test framework.
Saves structured JSON reports and prints human-readable summaries.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from utils.config import Config


def save_json_report(data: Any, filename: str) -> Path:
    """
    Serialize *data* as pretty-printed JSON and write it to reports/<filename>.

    Returns the Path of the saved file.
    """
    Config.ensure_dirs()
    output_path = Config.REPORTS_DIR / filename
    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, default=str)
    print(f"[reporter] Saved report → {output_path}")
    return output_path


def generate_summary(results: list[dict]) -> None:
    """
    Print a pass/fail/skip summary table to stdout.

    Each dict in *results* should have at minimum:
        {
            "name": str,
            "status": "passed" | "failed" | "skipped",
            "duration_s": float,          # optional
            "message": str,               # optional, shown on failure
        }
    """
    passed = [r for r in results if r.get("status") == "passed"]
    failed = [r for r in results if r.get("status") == "failed"]
    skipped = [r for r in results if r.get("status") == "skipped"]

    total = len(results)
    print("\n" + "=" * 60)
    print(f"  TEST SUMMARY  —  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print(f"  Total   : {total}")
    print(f"  Passed  : {len(passed)}")
    print(f"  Failed  : {len(failed)}")
    print(f"  Skipped : {len(skipped)}")
    print("-" * 60)

    if failed:
        print("  FAILURES:")
        for r in failed:
            name = r.get("name", "unknown")
            msg = r.get("message", "")
            print(f"    ✗  {name}")
            if msg:
                print(f"       {msg}")

    if skipped:
        print("  SKIPPED:")
        for r in skipped:
            print(f"    ○  {r.get('name', 'unknown')}")

    print("=" * 60 + "\n")


def append_to_json_report(filepath: Path, new_entry: dict) -> None:
    """
    Load an existing JSON array from *filepath*, append *new_entry*, and save.
    Creates the file if it does not exist.
    """
    Config.ensure_dirs()
    if filepath.exists():
        with open(filepath, encoding="utf-8") as fh:
            try:
                data = json.load(fh)
                if not isinstance(data, list):
                    data = [data]
            except json.JSONDecodeError:
                data = []
    else:
        data = []

    data.append(new_entry)
    with open(filepath, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, default=str)


def build_axe_report(violations: list[dict], page_url: str) -> dict:
    """
    Structure axe violation data into a report-friendly dict.
    """
    return {
        "timestamp": datetime.now().isoformat(),
        "page_url": page_url,
        "total_violations": len(violations),
        "critical": [v for v in violations if v.get("impact") == "critical"],
        "serious": [v for v in violations if v.get("impact") == "serious"],
        "moderate": [v for v in violations if v.get("impact") == "moderate"],
        "minor": [v for v in violations if v.get("impact") == "minor"],
        "all_violations": violations,
    }
