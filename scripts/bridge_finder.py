#!/usr/bin/env python3
"""
Bridge Game Finder — terminal app that prints UK online bridge games
for a given day's afternoon/evening (12:00–23:00 UK).

Spec: docs/superpowers/specs/2026-04-30-bridge-finder-design.md
"""

import json
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from statistics import median
from urllib.parse import urlparse, parse_qs
from zoneinfo import ZoneInfo

import dateparser
import requests
from bs4 import BeautifulSoup
from rich.console import Console
from rich.table import Table

import bridge_db

PROJECT_DIR = Path(__file__).resolve().parent.parent
CLUBS_FILE = PROJECT_DIR / "clubs.json"
REPORTS_DIR = PROJECT_DIR / "reports"
UK_TZ = ZoneInfo("Europe/London")
HTTP_TIMEOUT = 10
HTTP_USER_AGENT = "BridgeFinder/0.1 (lee personal use)"

STALE_DAYS = 180
MEDIAN_WEEKS = 4
LOOKBACK_WEEKS = 5
MIN_RANKED_ROWS = 3
DRIFT_LO = 0.5
DRIFT_HI = 1.5

console = Console()


_NEXT_DAY_RE = {
    "sat": "saturday", "saturday": "saturday",
    "sun": "sunday",   "sunday": "sunday",
    "mon": "monday",   "monday": "monday",
    "tue": "tuesday",  "tuesday": "tuesday",
    "wed": "wednesday","wednesday": "wednesday",
    "thu": "thursday", "thursday": "thursday",
    "fri": "friday",   "friday": "friday",
}


def _preprocess(raw: str) -> str:
    """Expand 'next sat' → 'saturday' so dateparser resolves it correctly."""
    lower = raw.lower().strip()
    if lower.startswith("next "):
        rest = lower[5:].strip()
        if rest in _NEXT_DAY_RE:
            return _NEXT_DAY_RE[rest]
    return raw


def prompt_date():
    """Prompt for a date, parse with UK locale, return a date or exit."""
    settings = {"DATE_ORDER": "DMY", "PREFER_DATES_FROM": "future"}
    for _attempt in range(3):
        raw = input('Date of game (e.g. "next sat", "2 May", or blank)? ').strip()
        if not raw:
            return next_weekend_day()
        parsed = dateparser.parse(_preprocess(raw), settings=settings)
        if parsed:
            return parsed.date()
        console.print(f"[red]Couldn't parse '{raw}'. Try '2 May' or 'next sat'.[/red]")
    console.print("[red]Giving up after 3 attempts.[/red]")
    sys.exit(1)


def next_weekend_day():
    """Today if today is Sat/Sun, else next Saturday."""
    today = datetime.now(UK_TZ).date()
    if today.weekday() in (5, 6):
        return today
    days_to_sat = (5 - today.weekday()) % 7
    return today + timedelta(days=days_to_sat or 7)


def weekday_label(d):
    return d.strftime("%A")


_DAY_CODES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def day_code(d):
    return _DAY_CODES[d.weekday()]


def load_clubs():
    """Load and return clubs.json as a list of dicts, or exit with error.

    Entries marked ``"status": "discarded"`` are filtered out here — they
    failed the eligibility criteria (wrong time, F2F, cancelled, or sub-14
    fields) and should never surface in the finder. The record is kept in
    clubs.json (with a ``discard_reason``) so it isn't re-investigated later.
    """
    if not CLUBS_FILE.exists():
        console.print(f"[red]clubs.json missing at {CLUBS_FILE}[/red]")
        sys.exit(1)
    try:
        clubs = json.loads(CLUBS_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        console.print(f"[red]clubs.json malformed: {e}[/red]")
        sys.exit(1)
    return [c for c in clubs if c.get("status") != "discarded"]


def earliest_time(time_uk_str):
    """For 'HH:MM' or 'HH:MM / HH:MM / ...' return the earliest as a string."""
    return time_uk_str.split("/")[0].strip()


def filter_clubs(clubs, target_day_code):
    """Filter to clubs running on target_day with earliest time >= 12:00."""
    out = []
    for c in clubs:
        if c["day"] != target_day_code and c["day"] != "both":
            continue
        if earliest_time(c["time_uk"]) < "12:00":
            continue
        out.append(c)
    return out


def expand_multi_time(clubs):
    """For static-parser clubs with slash-separated times, emit one row per slot.
    Returns list of (club_dict, time_str) tuples."""
    rows = []
    for c in clubs:
        if c["parser"] == "static" and "/" in c["time_uk"]:
            for t in [p.strip() for p in c["time_uk"].split("/")]:
                rows.append((c, t))
        else:
            rows.append((c, c["time_uk"]))
    return rows


def stale_warning(club):
    try:
        lv = datetime.strptime(club["last_verified"], "%Y-%m-%d").date()
    except (KeyError, ValueError):
        return False
    return (date.today() - lv).days > STALE_DAYS


def fetch(url):
    """GET with our UA and timeout. Returns response.content (bytes) or raises."""
    return requests.get(
        url,
        headers={"User-Agent": HTTP_USER_AGENT},
        timeout=HTTP_TIMEOUT,
    ).content


def slug_from_url(results_url):
    """Extract bridgewebs slug from e.g. https://www.bridgewebs.com/wbatbc/ → 'wbatbc'."""
    path = urlparse(results_url).path.strip("/")
    return path.split("/")[0] if path else None


def index_url(slug):
    return f"https://www.bridgewebs.com/cgi-bin/bwor/bw.cgi?club={slug}&pid=display_past"


def parse_index(html_bytes):
    """Parse the past-results index. Return list of (date, label, event_id) tuples,
    most recent first.

    Bridgewebs renders results via onClick="eventLink('YYYYMMDD_N','','')" on <td>
    elements rather than <a href>. We extract both patterns.
    """
    html = html_bytes.decode("iso-8859-1")
    soup = BeautifulSoup(html, "html.parser")
    entries = []

    # Pattern 1: <a href="...display_rank&event=..."> links
    for a in soup.find_all("a", href=re.compile(r"display_rank")):
        href = a.get("href", "")
        qs = parse_qs(urlparse(href).query)
        event_id = qs.get("event", [None])[0]
        if not event_id:
            continue
        m = re.match(r"^(\d{8})", event_id)
        if not m:
            continue
        try:
            d = datetime.strptime(m.group(1), "%Y%m%d").date()
        except ValueError:
            continue
        label = a.get_text(strip=True)
        entries.append((d, label, event_id))

    # Pattern 2: onClick="eventLink ('YYYYMMDD_N','','')" on any element
    for tag in soup.find_all(onclick=re.compile(r"eventLink")):
        onclick = tag.get("onclick", "")
        m = re.search(r"eventLink\s*\(\s*'(\d{8}[^']*)'", onclick)
        if not m:
            continue
        event_id = m.group(1)
        date_m = re.match(r"^(\d{8})", event_id)
        if not date_m:
            continue
        try:
            d = datetime.strptime(date_m.group(1), "%Y%m%d").date()
        except ValueError:
            continue
        label = tag.get_text(strip=True)
        entries.append((d, label, event_id))

    seen = set()
    out = []
    for e in entries:
        if e[2] in seen:
            continue
        seen.add(e[2])
        out.append(e)
    out.sort(reverse=True)
    return out


def result_url(slug, event_id):
    return f"https://www.bridgewebs.com/cgi-bin/bwor/bw.cgi?club={slug}&pid=display_rank&event={event_id}"


def parse_result_page(html_bytes):
    """Parse a single result page. Return (pair_count, ngs_avg) — either may be None."""
    html = html_bytes.decode("iso-8859-1")
    soup = BeautifulSoup(html, "html.parser")

    pair_count = None
    for table in soup.find_all("table"):
        rows_with_rank = 0
        for tr in table.find_all("tr"):
            cells = tr.find_all(["td", "th"])
            if not cells:
                continue
            first_text = cells[0].get_text(strip=True)
            if re.match(r"^\d+[=.]?$", first_text):
                rows_with_rank += 1
        if rows_with_rank > (pair_count or 0):
            pair_count = rows_with_rank
    # Require at least 3 ranked rows to avoid false positives from generic pages
    if pair_count is not None and pair_count < MIN_RANKED_ROWS:
        pair_count = None

    ngs_avg = None
    text = soup.get_text(" ", strip=True)
    m = re.search(r"NGS[^0-9%]{0,40}(\d{1,3}(?:\.\d+)?)\s*%", text, re.IGNORECASE)
    if m:
        try:
            ngs_avg = float(m.group(1))
        except ValueError:
            pass

    return pair_count, ngs_avg


def candidate_dates_for_weekday(target_date, n=LOOKBACK_WEEKS):
    """Return up to n dates on the same weekday as target_date, starting from
    the most recent occurrence at or before target_date, going back weekly."""
    # Find the most recent occurrence of target_date's weekday at or before target_date
    start = target_date
    while start.weekday() != target_date.weekday():
        start -= timedelta(days=1)
    return [start - timedelta(weeks=i) for i in range(n)]


def fetch_bridgewebs(club, target_date, time_uk, db_conn=None):
    """Fetch results for a bridgewebs club.

    Strategy: Bridgewebs display_past only returns the last 3 sessions, so we
    skip the index and directly construct event IDs (YYYYMMDD_1) for the target
    weekday going back up to 5 weeks. We try N=1 first; if no result, try N=2.
    """
    out = {
        "median_pairs_4w": None,
        "latest_pairs": None,
        "ngs_avg": None,
        "session_date": None,
        "session_url": None,
        "fallback_weeks_back": 0,
        "drift_warning": False,
        "error": None,
    }
    slug = slug_from_url(club["results_url"])
    if not slug:
        out["error"] = "Bad results_url"
        return out

    dates = candidate_dates_for_weekday(target_date)

    def try_fetch(d):
        """Try _1 then _2 suffix for a date. Return (event_id, pc, ngs) or None."""
        for suffix in ("_1", "_2"):
            eid = d.strftime("%Y%m%d") + suffix
            try:
                page = fetch(result_url(slug, eid))
                pc, ngs = parse_result_page(page)
                if pc is not None:
                    if db_conn is not None:
                        bridge_db.record_session(db_conn, slug, d.isoformat(), eid, pc, ngs)
                    return eid, pc, ngs
            except Exception:
                pass
        return None

    selected = None
    weeks_back = 0
    for i, d in enumerate(dates):
        result = try_fetch(d)
        if result:
            selected = (d, *result)
            weeks_back = i
            break

    if selected is None:
        out["error"] = "No recent sessions found"
        return out

    selected_date, selected_eid, selected_pc, selected_ngs = selected
    out["fallback_weeks_back"] = weeks_back
    out["session_date"] = selected_date.isoformat()
    out["session_url"] = result_url(slug, selected_eid)

    pair_counts = [selected_pc]
    ngs_values = [selected_ngs] if selected_ngs is not None else []
    for d in dates:
        if d >= selected_date:
            continue
        if (selected_date - d).days > (MEDIAN_WEEKS - 1) * 7:
            break
        result = try_fetch(d)
        if result:
            _, pc, ngs = result
            pair_counts.append(pc)
            if ngs is not None:
                ngs_values.append(ngs)
        if len(pair_counts) >= MEDIAN_WEEKS:
            break

    out["latest_pairs"] = pair_counts[0]
    out["median_pairs_4w"] = int(median(pair_counts))
    if out["median_pairs_4w"] > 0:
        ratio = out["latest_pairs"] / out["median_pairs_4w"]
        if ratio < DRIFT_LO or ratio > DRIFT_HI:
            out["drift_warning"] = True
    if ngs_values:
        out["ngs_avg"] = sum(ngs_values) / len(ngs_values)

    return out


def fetch_static(club):
    """Return a result dict for a static-parser club using baseline values."""
    return {
        "median_pairs_4w": club.get("baseline_pairs", "—"),
        "latest_pairs": None,
        "ngs_avg": None,
        "session_date": None,
        "session_url": None,
        "fallback_weeks_back": 0,
        "drift_warning": False,
        "error": None,
    }


def format_cells(club, data):
    """Return (pairs_cell, ngs_cell) strings for a row."""
    if club["parser"] == "static":
        return str(data["median_pairs_4w"]), club.get("baseline_ngs_label", "—")
    mp = data["median_pairs_4w"]
    pairs_cell = "—" if mp is None else (f"{mp} ⚠" if data["drift_warning"] else str(mp))
    ngs_cell = "—" if data["ngs_avg"] is None else f"{data['ngs_avg']:.1f}%"
    return pairs_cell, ngs_cell


def write_report(target, rows, fetched, footnotes):
    """Write the markdown report to reports/{date}.md."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = REPORTS_DIR / f"{target.isoformat()}.md"
    now = datetime.now(UK_TZ)
    tz_label = now.strftime("%Z")  # BST or GMT depending on date
    lines = [
        f"# Bridge games — {target.strftime('%A %-d %B %Y')}",
        "",
        f"Generated {now.strftime('%Y-%m-%d %H:%M')} {tz_label}.",
        "",
    ]
    if target.weekday() == 5:
        lines.append("> Saturday options are limited — Sunday has more variety.")
        lines.append("")
    lines.append("| UK time | Club | Platform | Pairs (4w median) | Avg NGS | How to enter |")
    lines.append("|---|---|---|---|---|---|")
    for club, time_str in rows:
        pairs_cell, ngs_cell = format_cells(club, fetched[club["name"]])
        lines.append(
            f"| {time_str} | {club['name']} | {club['platform']} | {pairs_cell} | {ngs_cell} | {club['how_to_enter_summary']} |"
        )
    if footnotes:
        lines.append("")
        lines.append("## Notes")
        lines.append("")
        for note in footnotes:
            lines.append(f"- {note}")
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out_path


def main():
    console.print("[bold]Bridge Game Finder[/bold]\n")
    target = prompt_date()
    console.print(f"→ {weekday_label(target)} {target.strftime('%-d %B %Y')}\n")

    clubs = load_clubs()
    matched = filter_clubs(clubs, day_code(target))
    rows = expand_multi_time(matched)
    rows.sort(key=lambda r: r[1])  # sort by time string

    if not rows:
        console.print("No clubs match this day in the PM/eve window.")
        sys.exit(0)

    if target.weekday() == 5:
        console.print("[yellow]Note: Saturday options are limited — Sunday has more variety.[/yellow]\n")

    # Open DB and register clubs
    db_conn = bridge_db.connect()
    bridge_db.init_db(db_conn)
    for club, _ in rows:
        if club["parser"] != "bridgewebs":
            continue
        slug = slug_from_url(club["results_url"])
        if slug:
            bridge_db.upsert_club(
                db_conn, slug, club["name"], club["day"], club["time_uk"],
                club["results_url"], club["platform"],
            )
    db_conn.commit()

    # Fetch per unique club (not per row — multi-time entries share data)
    fetched = {}
    footnotes = []
    for club, _ in rows:
        if club["name"] in fetched:
            continue
        console.print(f"  Fetching {club['name']}... ", end="")
        if club["parser"] == "static":
            fetched[club["name"]] = fetch_static(club)
            console.print("[dim]static[/dim]")
        else:
            data = fetch_bridgewebs(club, target, club["time_uk"], db_conn=db_conn)
            db_conn.commit()
            fetched[club["name"]] = data
            if data["error"]:
                console.print(f"[red]— ({data['error']})[/red]")
                footnotes.append(
                    f"**{club['name']}** — {data['error']}. Data unavailable for this run; the club may still be running — check their site."
                )
            else:
                console.print(f"[green]✓[/green] {data['median_pairs_4w']} pairs (4w median)")
                weeks = data["fallback_weeks_back"]
                if weeks > 0:
                    weeks_label = "1 week" if weeks == 1 else f"{weeks} weeks"
                    footnotes.append(
                        f"**{club['name']}** — showing {weeks_label} ago ({data['session_date']}); {target.isoformat()} not yet published."
                    )
                if data["drift_warning"]:
                    footnotes.append(
                        f"**{club['name']}** — last week's pairs differ sharply from the 4-week median; data may be unreliable."
                    )

        if stale_warning(club):
            footnotes.append(
                f"**{club['name']}** — entry last verified {club.get('last_verified', '?')} (>180 days ago); URLs may have changed."
            )

    console.print()

    # Build the table
    table = Table(show_header=True, header_style="bold")
    table.add_column("UK time")
    table.add_column("Club")
    table.add_column("Platform")
    table.add_column("Pairs (4w median)")
    table.add_column("Avg NGS")
    table.add_column("How to enter")

    for club, time_str in rows:
        pairs_cell, ngs_cell = format_cells(club, fetched[club["name"]])
        table.add_row(
            time_str,
            club["name"],
            club["platform"],
            pairs_cell,
            ngs_cell,
            club["how_to_enter_summary"],
        )
    console.print(table)

    if footnotes:
        console.print("\n[bold]Notes:[/bold]")
        for note in footnotes:
            console.print(f"  {note}")

    out_path = write_report(target, rows, fetched, footnotes)
    console.print(f"\nReport saved to {out_path}")


if __name__ == "__main__":
    main()
