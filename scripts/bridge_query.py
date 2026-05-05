#!/usr/bin/env python3
"""Print qualifying clubs from the DB.

Usage:
  python3 scripts/bridge_query.py            # all days
  python3 scripts/bridge_query.py Tue        # one day
  python3 scripts/bridge_query.py Tue all    # show excluded too
"""

import sys

from rich.console import Console
from rich.table import Table

import bridge_db

console = Console()


def main():
    day = sys.argv[1] if len(sys.argv) > 1 else None
    show_all = len(sys.argv) > 2 and sys.argv[2] == "all"

    conn = bridge_db.connect()
    bridge_db.init_db(conn)
    rows = bridge_db.latest_per_club(conn, day=day)

    if not rows:
        console.print("[yellow]No data — run bridge_finder.py first.[/yellow]")
        return

    enriched = []
    for r in rows:
        status = bridge_db.classify(r["pairs"], r["ngs"])
        enriched.append({**r, "status": status})

    if not show_all:
        enriched = [r for r in enriched if r["status"] == "include"]

    enriched.sort(key=lambda r: ((r["pairs"] or 0) * -1, r["name"]))

    table = Table(show_header=True, header_style="bold")
    table.add_column("Day")
    table.add_column("Time")
    table.add_column("Club")
    table.add_column("Pairs", justify="right")
    table.add_column("NGS", justify="right")
    table.add_column("Last session")
    table.add_column("Status")

    status_style = {
        "include": "green",
        "exclude_pairs": "yellow",
        "exclude_ngs": "yellow",
        "exclude_both": "red",
        "no_data": "dim",
    }

    for r in enriched:
        pairs = "—" if r["pairs"] is None else str(r["pairs"])
        ngs = "—" if r["ngs"] is None else f"{r['ngs']:.1f}%"
        sess = r["session_date"] or "—"
        style = status_style.get(r["status"], "")
        table.add_row(
            r["day"], r["time_uk"], r["name"], pairs, ngs, sess,
            f"[{style}]{r['status']}[/{style}]" if style else r["status"],
        )

    console.print(table)
    console.print(
        f"\n[dim]Filter: pairs ≥ {bridge_db.PAIRS_THRESHOLD}, "
        f"NGS > {bridge_db.NGS_THRESHOLD}%[/dim]"
    )
    if not show_all:
        console.print("[dim]Showing 'include' only. Add 'all' as 2nd arg to see excluded.[/dim]")


if __name__ == "__main__":
    main()
