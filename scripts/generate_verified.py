#!/usr/bin/env python3
"""Regenerate VERIFIED.md from clubs.json.

Verified = club entry exists in clubs.json AND its time is not marked
as a placeholder (notes do not contain 'placeholder').
"""
import json
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent
CLUBS = ROOT / "clubs.json"
OUT = ROOT / "VERIFIED.md"

DAY_ORDER = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun", "both"]


def main() -> None:
    clubs = json.loads(CLUBS.read_text(encoding="utf-8"))
    verified = [c for c in clubs if "placeholder" not in (c.get("notes") or "").lower()]

    by_day: dict[str, list[dict]] = defaultdict(list)
    for c in verified:
        by_day[c["day"]].append(c)

    lines: list[str] = []
    lines.append("# Verified Bridge Clubs")
    lines.append("")
    lines.append(
        f"Auto-generated from `clubs.json`. {len(verified)} of {len(clubs)} clubs have "
        f"day/time verified against bridgewebs (no placeholder notes)."
    )
    lines.append("")
    lines.append("Regenerate: `python3 scripts/generate_verified.py`")
    lines.append("")

    for day in DAY_ORDER:
        entries = sorted(by_day.get(day, []), key=lambda c: (c["time_uk"], c["name"]))
        if not entries:
            continue
        lines.append(f"## {day} ({len(entries)})")
        lines.append("")
        lines.append("| Time | Club | Platform | Cost | Last verified |")
        lines.append("|------|------|----------|------|---------------|")
        for c in entries:
            lines.append(
                f"| {c['time_uk']} | {c['name']} | {c['platform']} | "
                f"{c.get('cost', '')} | {c.get('last_verified', '')} |"
            )
        lines.append("")

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT} ({len(verified)} verified entries)")


if __name__ == "__main__":
    main()
