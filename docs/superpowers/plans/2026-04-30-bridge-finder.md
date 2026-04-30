# Bridge Game Finder Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a terminal app that asks for a date and prints a table of UK online bridge games (Sat/Sun afternoons or evenings on RealBridge/BBO), with last-month pair counts and average NGS pulled live from bridgewebs.com. Launched from a Desktop `.command` file. Saves a markdown report.

**Architecture:** Single Python script (`scripts/bridge_finder.py`) reads a hand-edited `clubs.json`, fetches recent results for `parser: "bridgewebs"` clubs, returns baseline values for `parser: "static"` clubs, renders a `rich` table, writes a markdown report to `reports/`. Strict scope (one date → one weekend day, PM/eve only). No automated tests — manual smoke tests after build.

**Tech Stack:** Python 3.10+, `dateparser`, `requests`, `beautifulsoup4`, `rich`. Existing `.venv` at `/Users/leeguy/Casual_claude/Bridge_Tournaments/.venv`.

**Spec:** `docs/superpowers/specs/2026-04-30-bridge-finder-design.md`

---

## File Structure

| File | Responsibility |
|---|---|
| `clubs.json` | Canonical 7-entry club list (hand-edited) |
| `scripts/bridge_finder.py` | The entire script — date prompt, filter, fetch, parse, render, write |
| `reports/` (gitignored) | Output directory for `YYYY-MM-DD.md` reports |
| `~/Desktop/Bridge Games.command` | zsh launcher |
| `docs/superpowers/specs/2026-04-30-bridge-finder-design.md` | Spec (already written) |

The script is small enough (~400 lines estimated) that splitting it into modules would add ceremony without payoff. Keep it as one file with clearly-sectioned helpers.

---

## Task 1: Set up dependencies and seed `clubs.json`

**Files:**
- Modify: `/Users/leeguy/Casual_claude/Bridge_Tournaments/.venv/` (install packages)
- Create: `/Users/leeguy/Casual_claude/Bridge_Tournaments/clubs.json`

- [ ] **Step 1: Install dependencies into the existing venv**

Run:
```bash
cd /Users/leeguy/Casual_claude/Bridge_Tournaments
source .venv/bin/activate
pip install dateparser requests beautifulsoup4 rich
pip freeze | grep -E '(dateparser|requests|beautifulsoup4|rich)'
```

Expected output (versions may differ):
```
beautifulsoup4==4.12.3
dateparser==1.2.0
requests==2.32.3
rich==13.7.1
```

- [ ] **Step 2: Create `clubs.json` with the 7 seed entries**

Create file `/Users/leeguy/Casual_claude/Bridge_Tournaments/clubs.json` with exactly this content:

```json
[
  {
    "name": "Whitley Bay & Tynemouth (afternoon)",
    "platform": "RealBridge",
    "day": "Sat",
    "time_uk": "13:00",
    "cost": "£3 visitors",
    "results_url": "https://www.bridgewebs.com/wbatbc/",
    "parser": "bridgewebs",
    "visitor_policy": "contact_first",
    "registration": {
      "required": true,
      "url": "https://www.bridgewebs.com/wbatbc/",
      "deadline": "Before session",
      "notes": "Pay £3 by bank transfer"
    },
    "how_to_enter_summary": "Bank £3 to club before session",
    "last_verified": "2026-04-30",
    "notes": ""
  },
  {
    "name": "Whitley Bay & Tynemouth (evening)",
    "platform": "RealBridge",
    "day": "Sat",
    "time_uk": "19:00",
    "cost": "£3 visitors",
    "results_url": "https://www.bridgewebs.com/wbatbc/",
    "parser": "bridgewebs",
    "visitor_policy": "contact_first",
    "registration": {
      "required": true,
      "url": "https://www.bridgewebs.com/wbatbc/",
      "deadline": "Before session",
      "notes": "Pay £3 by bank transfer"
    },
    "how_to_enter_summary": "Bank £3 to club before session",
    "last_verified": "2026-04-30",
    "notes": ""
  },
  {
    "name": "Hunstanton Sunday Pairs",
    "platform": "RealBridge",
    "day": "Sun",
    "time_uk": "19:00",
    "cost": "£1.50 m / £2 v",
    "results_url": "https://www.bridgewebs.com/hunstanton/",
    "parser": "bridgewebs",
    "visitor_policy": "contact_first",
    "registration": {
      "required": true,
      "url": "https://www.bridgewebs.com/hunstanton/",
      "deadline": "First-visit registration",
      "notes": "Visitors register on first visit"
    },
    "how_to_enter_summary": "First visit: register; £2 visitors",
    "last_verified": "2026-04-30",
    "notes": "22 boards, prompt 7pm start"
  },
  {
    "name": "EBU Super Sunday Special",
    "platform": "RealBridge",
    "day": "Sun",
    "time_uk": "19:00",
    "cost": "£2.50",
    "results_url": "https://www.bridgewebs.com/cumbria/",
    "parser": "bridgewebs",
    "visitor_policy": "open",
    "registration": {
      "required": true,
      "url": "https://www.bridgewebs.com/cgi-bin/bwoq/bw.cgi?club=cumbria&pid=display_page70",
      "deadline": "By 17:00 same day",
      "notes": "Per-session entry; contact Ken Johnston 07712 162 816 if late"
    },
    "how_to_enter_summary": "Register at Cumbria CBA by 17:00; £2.50",
    "last_verified": "2026-04-30",
    "notes": "20-board MP pairs, Black Points"
  },
  {
    "name": "Friendly Online BC",
    "platform": "BBO",
    "day": "Sun",
    "time_uk": "19:15",
    "cost": "~$2 BB$",
    "results_url": "https://www.bridgewebs.com/friendlyonline/",
    "parser": "bridgewebs",
    "visitor_policy": "open",
    "registration": {
      "required": false,
      "url": "",
      "deadline": "",
      "notes": ""
    },
    "how_to_enter_summary": "Open, ~$2 BB$",
    "last_verified": "2026-04-30",
    "notes": "Run by Oliver Cowan on BBO"
  },
  {
    "name": "EBU Daily BBO",
    "platform": "BBO",
    "day": "both",
    "time_uk": "14:00 / 15:30 / 19:30 / 21:00",
    "cost": "~£1.80",
    "results_url": null,
    "parser": "static",
    "visitor_policy": "open",
    "registration": {
      "required": false,
      "url": "",
      "deadline": "",
      "notes": ""
    },
    "how_to_enter_summary": "Open, ~£1.80",
    "baseline_pairs": "20+",
    "baseline_ngs_label": "Mixed, NGS-rated",
    "last_verified": "2026-04-30",
    "notes": "Platform pool, NGS-rated"
  },
  {
    "name": "Dragon Pairs / Oliver Cowan",
    "platform": "BBO",
    "day": "Sat",
    "time_uk": "13:00",
    "cost": "~£13 (BB$16)",
    "results_url": null,
    "parser": "static",
    "visitor_policy": "open",
    "registration": {
      "required": true,
      "url": "https://www.bridgewebs.com/olivercowan/",
      "deadline": "Periodic only",
      "notes": "WBU Green Point Swiss Pairs; only runs occasionally"
    },
    "how_to_enter_summary": "Periodic only; check Oliver Cowan calendar",
    "baseline_pairs": "30–60",
    "baseline_ngs_label": "WBU Green Point — strong field",
    "last_verified": "2026-04-30",
    "notes": "Not weekly — periodic Green Point days"
  }
]
```

- [ ] **Step 3: Verify JSON parses**

Run:
```bash
python3 -c "import json; print(len(json.load(open('clubs.json'))), 'clubs')"
```

Expected output: `7 clubs`

- [ ] **Step 4: Commit**

```bash
git add clubs.json
git commit -m "$(cat <<'EOF'
data: seed clubs.json with 7 UK weekend bridge clubs

Whitley Bay & Tynemouth (Sat afternoon + evening), Hunstanton
(Sun), EBU Super Sunday Special (Sun), Friendly Online BC (Sun),
EBU Daily BBO (both, static), Dragon Pairs (Sat, static).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: Sample bridgewebs to pin CSS selectors

This task answers the build-time question raised in spec review: "What's the exact CSS class for the result table and NGS header?"

**Files:**
- Create (temporary, throwaway): `/tmp/bw_sample.html`

- [ ] **Step 1: Fetch a sample bridgewebs result index and result page**

Run:
```bash
curl -s -A "BridgeFinder/0.1 (lee personal use)" \
  'https://www.bridgewebs.com/cgi-bin/bwor/bw.cgi?club=hunstanton&pid=display_past' \
  > /tmp/bw_index.html

# Find the most recent result link in the index
grep -oE 'href="[^"]*display_rank[^"]*"' /tmp/bw_index.html | head -5
```

Expected: 5+ lines of `href="..."` URLs, each containing `display_rank` and an `event=` parameter.

- [ ] **Step 2: Fetch one result page**

Pick the first event URL from step 1 (it'll look like `/cgi-bin/bwor/bw.cgi?club=hunstanton&pid=display_rank&event=...`). Fetch it:

```bash
curl -s -A "BridgeFinder/0.1 (lee personal use)" \
  'https://www.bridgewebs.com/cgi-bin/bwor/bw.cgi?club=hunstanton&pid=display_rank&event=<EVENT_ID_FROM_STEP_1>' \
  -o /tmp/bw_result.html
wc -l /tmp/bw_result.html
```

Expected: `~500-2000 lines`.

- [ ] **Step 3: Identify the result table CSS structure**

Run:
```bash
grep -oE 'class="[a-z_0-9]+"' /tmp/bw_result.html | sort -u | head -30
```

Look for classes that look like ranking-table cells (typical bridgewebs uses `bwbox_*` classes). The likely candidate for the ranking table itself is `bwbox_data_text` or a `<table>` with class like `bwsep_table`. **Read the file in a browser or `less /tmp/bw_result.html` and find the table that lists pairs by rank** — note its class attribute.

Record the findings as constants for the script. You'll need:
- The CSS class or selector that uniquely identifies the **ranking table** (the one with one row per pair)
- The text pattern or selector for the **NGS event-average header** (often a `<font>` or `<td>` containing the literal text `"Average NGS"` or `"NGS"` followed by a percentage)

Write what you find into a file as a reference for Task 4:

```bash
cat > /tmp/bw_selectors.txt <<'EOF'
RANKING_TABLE_SELECTOR: <FILL IN — e.g. "table.bwsep_table" or specific class>
NGS_HEADER_PATTERN: <FILL IN — regex like r"NGS\s*Average[^0-9]*([0-9.]+)">
PAIR_ROW_SELECTOR: <FILL IN — e.g. "tr" inside the ranking table, excluding header rows>
NOTES: <any other observations about the page structure>
EOF
```

- [ ] **Step 4: Verify selectors against a second page**

Repeat steps 1–2 with `club=wbatbc` (Whitley Bay) instead of `hunstanton`. Confirm the same selectors find the ranking table and NGS info on a different club's page. If they don't, refine the selectors to be more general.

- [ ] **Step 5: Clean up temp files**

```bash
rm -f /tmp/bw_index.html /tmp/bw_result.html
# Keep /tmp/bw_selectors.txt for Task 4
```

No commit at this task — the output is a notes file used in Task 4.

---

## Task 3: Script skeleton — date prompt, filter, banner

**Files:**
- Create: `/Users/leeguy/Casual_claude/Bridge_Tournaments/scripts/bridge_finder.py`

This task gets the script running end-to-end with **no live fetching yet** — every row will use static-parser logic so we can verify the table renders.

- [ ] **Step 1: Write the script skeleton**

Create `scripts/bridge_finder.py`:

```python
#!/usr/bin/env python3
"""
Bridge Game Finder — terminal app that prints UK online bridge games
for a given Saturday or Sunday afternoon/evening.

Spec: docs/superpowers/specs/2026-04-30-bridge-finder-design.md
"""

import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import dateparser
from rich.console import Console
from rich.table import Table

PROJECT_DIR = Path(__file__).resolve().parent.parent
CLUBS_FILE = PROJECT_DIR / "clubs.json"
REPORTS_DIR = PROJECT_DIR / "reports"
UK_TZ = ZoneInfo("Europe/London")
HTTP_TIMEOUT = 10
HTTP_USER_AGENT = "BridgeFinder/0.1 (lee personal use)"

console = Console()


def prompt_date():
    """Prompt for a date, parse with UK locale, return a date or exit."""
    settings = {"DATE_ORDER": "DMY", "PREFER_DATES_FROM": "future"}
    for _attempt in range(3):
        raw = input('Date of game (e.g. "next sat", "2 May", or blank)? ').strip()
        if not raw:
            return next_weekend_day()
        parsed = dateparser.parse(raw, settings=settings)
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


def is_weekend(d):
    return d.weekday() in (5, 6)


def day_code(d):
    return "Sat" if d.weekday() == 5 else "Sun" if d.weekday() == 6 else None


def load_clubs():
    """Load and return clubs.json as a list of dicts, or exit with error."""
    if not CLUBS_FILE.exists():
        console.print(f"[red]clubs.json missing at {CLUBS_FILE}[/red]")
        sys.exit(1)
    try:
        return json.loads(CLUBS_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        console.print(f"[red]clubs.json malformed: {e}[/red]")
        sys.exit(1)


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
    """Return True if last_verified > 180 days ago."""
    try:
        lv = datetime.strptime(club["last_verified"], "%Y-%m-%d").date()
    except (KeyError, ValueError):
        return False
    return (date.today() - lv).days > 180


def main():
    console.print("[bold]Bridge Game Finder[/bold]\n")
    target = prompt_date()
    console.print(f"→ {weekday_label(target)} {target.strftime('%-d %B %Y')}\n")

    if not is_weekend(target):
        console.print(
            f"[red]Script only handles Saturday or Sunday games — parsed {weekday_label(target)}[/red]"
        )
        sys.exit(1)

    clubs = load_clubs()
    matched = filter_clubs(clubs, day_code(target))
    rows = expand_multi_time(matched)
    rows.sort(key=lambda r: r[1])  # sort by time string

    if not rows:
        console.print("No clubs match this day in the PM/eve window.")
        sys.exit(0)

    if target.weekday() == 5:
        console.print("[yellow]Note: Saturday options are limited — Sunday has more variety.[/yellow]\n")

    # For now, render with placeholders — Task 4 fills in fetched data.
    table = Table(show_header=True, header_style="bold")
    table.add_column("UK time")
    table.add_column("Club")
    table.add_column("Platform")
    table.add_column("Pairs (4w median)")
    table.add_column("Avg NGS")
    table.add_column("How to enter")

    for club, time_str in rows:
        if club["parser"] == "static":
            pairs_cell = club.get("baseline_pairs", "—")
            ngs_cell = club.get("baseline_ngs_label", "—")
        else:
            pairs_cell = "—"
            ngs_cell = "—"
        table.add_row(
            time_str,
            club["name"],
            club["platform"],
            pairs_cell,
            ngs_cell,
            club["how_to_enter_summary"],
        )
    console.print(table)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Smoke-test the skeleton**

Run from the project root with the venv active:
```bash
cd /Users/leeguy/Casual_claude/Bridge_Tournaments
source .venv/bin/activate
echo "next sat" | python3 scripts/bridge_finder.py
```

Expected:
- Banner `Bridge Game Finder`
- Echo line `→ Saturday <date>`
- Yellow Saturday warning line
- A table with 4 rows (Whitley Bay afternoon, Whitley Bay evening, Dragon Pairs at 13:00, EBU Daily BBO at 14:00, 15:30, 19:30, 21:00 — total 7 rows when EBU's 4 slots expand)
- Whitley Bay rows show `—` for pairs and NGS (live fetch not implemented yet)
- EBU Daily BBO rows show `20+` and `Mixed, NGS-rated` (static)

- [ ] **Step 3: Smoke-test the Sunday path**

```bash
echo "next sun" | python3 scripts/bridge_finder.py
```

Expected: no Saturday warning; table includes Hunstanton, SSS, FOBC, and EBU dailies.

- [ ] **Step 4: Smoke-test the weekday rejection**

```bash
echo "next mon" | python3 scripts/bridge_finder.py
```

Expected: red error `Script only handles Saturday or Sunday games — parsed Monday`, exit code 1.
Verify exit code:
```bash
echo "next mon" | python3 scripts/bridge_finder.py; echo "exit=$?"
```

Expected: `exit=1`.

- [ ] **Step 5: Smoke-test the empty-input default**

```bash
echo "" | python3 scripts/bridge_finder.py
```

Expected: parsed date = today if today is Sat/Sun, else next Saturday. No errors.

- [ ] **Step 6: Commit**

```bash
git add scripts/bridge_finder.py
git commit -m "$(cat <<'EOF'
feat: bridge finder skeleton — date prompt, filter, table

Renders table with placeholders for live fetches. Static rows
already populated. Saturday banner. UK locale dateparser. Empty
input defaults to next upcoming Sat/Sun. Weekday rejection.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: Bridgewebs parser — fetch, parse, 4-week median

**Files:**
- Modify: `/Users/leeguy/Casual_claude/Bridge_Tournaments/scripts/bridge_finder.py`

This adds the live fetch for `parser: "bridgewebs"` clubs. Use the CSS selectors you recorded in `/tmp/bw_selectors.txt` from Task 2.

- [ ] **Step 1: Add the parser helpers near the top of `bridge_finder.py`**

Insert these functions after the existing helpers (after `stale_warning`):

```python
import re
from urllib.parse import urlparse, parse_qs, urljoin
from statistics import median

import requests
from bs4 import BeautifulSoup


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
    most recent first. Date is a date object, label is the session label string,
    event_id is the value of the event= URL param."""
    html = html_bytes.decode("iso-8859-1")
    soup = BeautifulSoup(html, "html.parser")
    entries = []
    for a in soup.find_all("a", href=re.compile(r"display_rank")):
        href = a.get("href", "")
        qs = parse_qs(urlparse(href).query)
        event_id = qs.get("event", [None])[0]
        if not event_id:
            continue
        # Bridgewebs typical pattern: event_id starts with YYYYMMDD
        m = re.match(r"^(\d{8})", event_id)
        if not m:
            continue
        try:
            d = datetime.strptime(m.group(1), "%Y%m%d").date()
        except ValueError:
            continue
        label = a.get_text(strip=True)
        entries.append((d, label, event_id))
    # de-dup and sort newest first
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

    # Pair count: find the ranking table. Bridgewebs renders ranks in a table where
    # each pair has a row. The most reliable signal is rows with a numeric rank
    # in the first cell. Fall back to counting <tr> in the largest <table>.
    pair_count = None
    for table in soup.find_all("table"):
        rows_with_rank = 0
        for tr in table.find_all("tr"):
            cells = tr.find_all(["td", "th"])
            if not cells:
                continue
            first_text = cells[0].get_text(strip=True)
            # Match plain integers (rank) or "1=" (tied) or "1." patterns
            if re.match(r"^\d+[=.]?$", first_text):
                rows_with_rank += 1
        if rows_with_rank > (pair_count or 0):
            pair_count = rows_with_rank
    if pair_count == 0:
        pair_count = None

    # NGS: look for "NGS" near a percentage in the page text
    ngs_avg = None
    text = soup.get_text(" ", strip=True)
    m = re.search(r"NGS[^0-9%]{0,40}(\d{1,3}(?:\.\d+)?)\s*%", text, re.IGNORECASE)
    if m:
        try:
            ngs_avg = float(m.group(1))
        except ValueError:
            pass

    return pair_count, ngs_avg


def fetch_bridgewebs(club, target_date, time_uk):
    """Fetch results for a bridgewebs club. Return a dict per spec.
    Walks back up to 4 same-weekday sessions including target_date."""
    out = {
        "median_pairs_4w": None,
        "latest_pairs": None,
        "ngs_avg": None,
        "session_date": None,
        "session_url": None,
        "fallback_used": False,
        "fallback_weeks_back": 0,
        "drift_warning": False,
        "error": None,
    }
    slug = slug_from_url(club["results_url"])
    if not slug:
        out["error"] = "Bad results_url"
        return out
    try:
        index_html = fetch(index_url(slug))
        entries = parse_index(index_html)
    except Exception as e:
        out["error"] = "Network error"
        return out

    # Filter to same weekday only.
    target_weekday = target_date.weekday()
    same_weekday = [e for e in entries if e[0].weekday() == target_weekday]

    # Substring match by time_uk if multiple sessions on a single date — keep one per date.
    # Group by date, prefer the entry whose label contains time_uk substrings.
    time_substrs = [time_uk]  # could be e.g. "13:00" — also try "1pm"
    if ":" in time_uk:
        h = int(time_uk.split(":")[0])
        time_substrs.append(f"{h % 12 or 12}pm" if h >= 12 else f"{h}am")
    by_date = {}
    for d, label, eid in same_weekday:
        existing = by_date.get(d)
        score = sum(s.lower() in label.lower() for s in time_substrs)
        if existing is None or score > existing[0]:
            by_date[d] = (score, label, eid)
    candidates = sorted(
        ((d, eid) for d, (_, _, eid) in by_date.items()),
        key=lambda x: x[0],
        reverse=True,
    )

    # Find target_date or walk back up to 4 weeks
    selected = None
    weeks_back = 0
    for d, eid in candidates:
        if d > target_date:
            continue
        # 4-week window from target backwards (inclusive)
        days_diff = (target_date - d).days
        if days_diff > 28:
            break
        if d == target_date:
            selected = (d, eid, 0)
            break
        weeks_back += 1
        if weeks_back > 4:
            break
        selected = (d, eid, weeks_back)
        break

    if not selected:
        out["error"] = "No recent sessions found"
        return out

    sel_date, sel_eid, sel_wb = selected
    out["fallback_used"] = sel_wb > 0
    out["fallback_weeks_back"] = sel_wb
    out["session_date"] = sel_date.isoformat()
    out["session_url"] = result_url(slug, sel_eid)

    # Collect last 4 same-weekday sessions ending at the selected date (inclusive)
    pair_counts = []
    ngs_values = []
    for d, eid in candidates:
        if d > sel_date:
            continue
        if (sel_date - d).days > 21:  # 4 sessions = today + 3 weeks back
            break
        try:
            page = fetch(result_url(slug, eid))
            pc, ngs = parse_result_page(page)
        except Exception:
            continue
        if pc is not None:
            pair_counts.append(pc)
        if ngs is not None:
            ngs_values.append(ngs)
        if len(pair_counts) >= 4:
            break

    if pair_counts:
        out["latest_pairs"] = pair_counts[0]
        out["median_pairs_4w"] = int(median(pair_counts))
        if out["median_pairs_4w"] > 0:
            ratio = out["latest_pairs"] / out["median_pairs_4w"]
            if ratio < 0.5 or ratio > 1.5:
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
        "fallback_used": False,
        "fallback_weeks_back": 0,
        "drift_warning": False,
        "error": None,
    }
```

- [ ] **Step 2: Update `main()` to fetch per-club**

Replace the current `main()` rendering loop. The new loop fetches each unique club once (caching the result for any expanded multi-time slot), prints progress, and uses the result in the table.

Replace the body of `main()` (everything from `if not rows:` onward) with:

```python
    if not rows:
        console.print("No clubs match this day in the PM/eve window.")
        sys.exit(0)

    if target.weekday() == 5:
        console.print("[yellow]Note: Saturday options are limited — Sunday has more variety.[/yellow]\n")

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
            data = fetch_bridgewebs(club, target, club["time_uk"])
            fetched[club["name"]] = data
            if data["error"]:
                console.print(f"[red]— ({data['error']})[/red]")
                footnotes.append(
                    f"**{club['name']}** — {data['error']}. Data unavailable for this run; the club may still be running — check their site."
                )
            else:
                console.print(f"[green]✓[/green] {data['median_pairs_4w']} pairs (4w median)")
                if data["fallback_used"]:
                    weeks = data["fallback_weeks_back"]
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
        data = fetched[club["name"]]
        if club["parser"] == "static":
            pairs_cell = str(data["median_pairs_4w"])
            ngs_cell = club.get("baseline_ngs_label", "—")
        else:
            mp = data["median_pairs_4w"]
            pairs_cell = "—" if mp is None else (f"{mp} ⚠" if data["drift_warning"] else str(mp))
            ngs_cell = "—" if data["ngs_avg"] is None else f"{data['ngs_avg']:.1f}%"
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
```

- [ ] **Step 3: Live smoke-test against Hunstanton (Sunday)**

```bash
cd /Users/leeguy/Casual_claude/Bridge_Tournaments
source .venv/bin/activate
echo "next sun" | python3 scripts/bridge_finder.py
```

Expected:
- Progress lines like `Fetching Hunstanton Sunday Pairs... ✓ 14 pairs (4w median)` (number may vary)
- Table populated with real numbers for bridgewebs rows
- EBU dailies still show `20+` (static)
- No Python tracebacks

If a network error happens for any club, the script should print `— (Network error)` for that row and continue. Re-run if transient.

- [ ] **Step 4: Live smoke-test against Whitley Bay (Saturday)**

```bash
echo "next sat" | python3 scripts/bridge_finder.py
```

Expected: real numbers for Whitley Bay rows, Saturday warning shown.

- [ ] **Step 5: Smoke-test the no-result fallback**

Use a far-future date:
```bash
python3 -c "
import sys; sys.argv = []
from scripts.bridge_finder import main
" 2>/dev/null  # this won't work — instead just type the date manually
echo "1 January 2030" | python3 scripts/bridge_finder.py
```

Expected: every bridgewebs row either shows `—` with a `No recent sessions found` footnote, OR shows the most recent session it could find with a `showing N weeks ago` footnote. (Fallback walks 4 weeks max — beyond that, it gives up.)

- [ ] **Step 6: Commit**

```bash
git add scripts/bridge_finder.py
git commit -m "$(cat <<'EOF'
feat: live bridgewebs fetching with 4-week median + drift canary

Per-club fetch (not per row), 10s timeout, ISO-8859-1 decoding,
4-week rolling median pair count, NGS as percentage, drift warning
when latest pair count diverges >50% from median, footnotes for
fallbacks/errors/stale entries.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: Markdown report writer

**Files:**
- Modify: `/Users/leeguy/Casual_claude/Bridge_Tournaments/scripts/bridge_finder.py`

- [ ] **Step 1: Add the report-writer function**

Add this function near the bottom of `bridge_finder.py`, just above `def main()`:

```python
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
        data = fetched[club["name"]]
        if club["parser"] == "static":
            pairs_cell = str(data["median_pairs_4w"])
            ngs_cell = club.get("baseline_ngs_label", "—")
        else:
            mp = data["median_pairs_4w"]
            pairs_cell = "—" if mp is None else (f"{mp} ⚠" if data["drift_warning"] else str(mp))
            ngs_cell = "—" if data["ngs_avg"] is None else f"{data['ngs_avg']:.1f}%"
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
```

- [ ] **Step 2: Call the report writer at the end of `main()`**

Add after the table rendering and footnote-printing block in `main()`:

```python
    out_path = write_report(target, rows, fetched, footnotes)
    console.print(f"\nReport saved to {out_path}")
```

- [ ] **Step 3: Smoke-test report generation**

```bash
echo "next sun" | python3 scripts/bridge_finder.py
ls -la reports/
cat reports/$(ls reports/ | head -1)
```

Expected:
- `reports/` directory created
- A markdown file named `YYYY-MM-DD.md` exists
- File contents are well-formed markdown with the same table as on screen
- Header timestamp shows correct timezone (`BST` or `GMT`)

- [ ] **Step 4: Verify `reports/` is gitignored**

```bash
git status
```

Expected: `reports/` does NOT appear in untracked files (it's in `.gitignore`).

- [ ] **Step 5: Commit**

```bash
git add scripts/bridge_finder.py
git commit -m "$(cat <<'EOF'
feat: write markdown report to reports/

UTF-8 output, Europe/London timestamp with correct BST/GMT label,
mkdir -p semantics, same table + footnotes as terminal.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 6: Desktop launcher

**Files:**
- Create: `~/Desktop/Bridge Games.command`

- [ ] **Step 1: Create the launcher**

```bash
cat > "$HOME/Desktop/Bridge Games.command" <<'EOF'
#!/bin/zsh

# ----------------------------------------
# Bridge Game Finder launcher
# ----------------------------------------

PROJECT_DIR="$HOME/Casual_claude/Bridge_Tournaments"

cd "$PROJECT_DIR" || { echo "Could not cd to $PROJECT_DIR"; exec zsh -i; }

[[ -f "$HOME/.zshrc" ]] && source "$HOME/.zshrc"
[[ -f ".venv/bin/activate" ]] && source ".venv/bin/activate"

python3 scripts/bridge_finder.py

echo ""
echo "=== Done. Press Ctrl-D or type 'exit' to close. ==="
exec zsh -i
EOF

chmod +x "$HOME/Desktop/Bridge Games.command"
```

- [ ] **Step 2: Verify the launcher is executable**

```bash
ls -la "$HOME/Desktop/Bridge Games.command"
```

Expected: permissions include `x` (e.g. `-rwxr-xr-x`).

- [ ] **Step 3: Test the launcher end-to-end**

Double-click `Bridge Games.command` in Finder (or run `open "$HOME/Desktop/Bridge Games.command"`).

Expected:
- Terminal opens
- The script runs interactively, prompts for date
- After completing, terminal stays open with shell prompt
- Type `exit` to close

- [ ] **Step 4: Commit (the launcher itself isn't in the repo, but capture the change in `scripts/`)**

The launcher lives on Desktop, not in the repo. No commit needed.

If you want to keep a copy in the repo for reference:

```bash
cp "$HOME/Desktop/Bridge Games.command" scripts/launcher_template.sh
git add scripts/launcher_template.sh
git commit -m "$(cat <<'EOF'
chore: keep launcher template in repo for reference

The actual launcher lives on Desktop. This is a backup so the
script can be regenerated if Desktop file is lost.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 7: Final smoke-test pass

This task runs all the spec's manual smoke tests as a final acceptance check.

- [ ] **Step 1: Test 1 — next Sat**

```bash
echo "next sat" | python3 scripts/bridge_finder.py
```

Expected:
- Saturday banner shown
- Whitley Bay (afternoon + evening) rows present with real pair count + NGS
- Dragon Pairs row present with `30–60` baseline_pairs
- EBU Daily BBO rows for 14:00, 15:30, 19:30, 21:00
- Report saved

- [ ] **Step 2: Test 2 — next Sun**

```bash
echo "next sun" | python3 scripts/bridge_finder.py
```

Expected:
- No Saturday banner
- Hunstanton, SSS, FOBC rows with real fetched data
- EBU Daily BBO rows
- Report saved

- [ ] **Step 3: Test 3 — weekday rejection**

```bash
echo "next mon" | python3 scripts/bridge_finder.py; echo "exit=$?"
```

Expected: `exit=1`, red error message.

- [ ] **Step 4: Test 4 — garbage input then valid input**

```bash
printf "asdfqwerty\n2 May 2026\n" | python3 scripts/bridge_finder.py
```

Expected: re-prompt after the garbage line, accept the second line, run.

- [ ] **Step 5: Test 5 — far-future date (no results)**

```bash
echo "1 January 2030" | python3 scripts/bridge_finder.py
```

Expected: bridgewebs rows show `—`, footnotes explain "No recent sessions found" or fallback.

- [ ] **Step 6: Test 6 — empty input on a weekday**

If today is a weekday:
```bash
echo "" | python3 scripts/bridge_finder.py
```

Expected: parsed date is the next Saturday (or Sunday if Sunday is sooner).

- [ ] **Step 7: Test 7 — stale entry warning**

Edit `clubs.json`, change one club's `last_verified` to `"2025-01-01"`, run the script:
```bash
python3 -c "
import json
d = json.load(open('clubs.json'))
d[0]['last_verified'] = '2025-01-01'
json.dump(d, open('clubs.json','w'), indent=2)
"
echo "next sat" | python3 scripts/bridge_finder.py
```

Expected: footnote `Whitley Bay & Tynemouth (afternoon) — entry last verified 2025-01-01 (>180 days ago); URLs may have changed.`

Restore:
```bash
python3 -c "
import json
d = json.load(open('clubs.json'))
d[0]['last_verified'] = '2026-04-30'
json.dump(d, open('clubs.json','w'), indent=2)
"
```

Verify clean:
```bash
git diff clubs.json
```

Expected: no diff (you restored the date).

- [ ] **Step 8: Lee fresh — final commit and update task tracking**

If anything was committed during smoke tests, the commit log will show it. Final commit catches anything outstanding:

```bash
git status
# Only expected uncommitted item: launcher_template.sh from Task 6 step 4 (if you did it)
```

---

## Self-review summary

**Spec coverage check:**
- ✅ Date prompt with UK locale (`PREFER_DATES_FROM=future`, `DATE_ORDER=DMY`) — Task 3
- ✅ Empty input → next Sat/Sun — Task 3
- ✅ Sat/Sun-only with weekday rejection (exit 1) — Task 3
- ✅ Saturday banner — Task 3
- ✅ `clubs.json` schema with `last_verified`, `how_to_enter_summary` — Task 1
- ✅ Time filter ≥12:00 — Task 3
- ✅ Multi-time expansion only for `parser: "static"` — Task 3
- ✅ Live bridgewebs fetch with 10s timeout, custom UA, no retries — Task 4
- ✅ ISO-8859-1 decoding — Task 4
- ✅ 4-week rolling median pair count — Task 4
- ✅ Drift canary >50% — Task 4
- ✅ Date fallback up to 4 weeks back — Task 4
- ✅ NGS as percentage with one decimal — Task 4 (display in Task 4 main loop)
- ✅ Static parser baseline values — Task 4
- ✅ Per-unique-club fetch (not per row) — Task 4
- ✅ Combined "How to enter" column — Task 3 (table) + Task 1 (data)
- ✅ Markdown report with Europe/London timestamp — Task 5
- ✅ `reports/` auto-create + UTF-8 — Task 5
- ✅ `reports/` gitignored — already done in spec triage commit
- ✅ Launcher named `Bridge Games.command` — Task 6
- ✅ Stale entry warning >180 days — Task 3 helper, Task 4 footnote
- ✅ All smoke tests in spec — Task 7

**Type consistency check:**
- `fetch_bridgewebs` and `fetch_static` return dicts with the same keys ✅
- `expand_multi_time` returns `[(club_dict, time_str)]` consistent across Tasks 3, 4, 5 ✅
- `slug_from_url`, `index_url`, `result_url` chain consistent ✅

**Placeholder scan:**
- The `<EVENT_ID_FROM_STEP_1>` in Task 2 step 2 is a literal placeholder for the human running the task to fill in from step 1's output. That's intentional, not a plan failure.
- The `/tmp/bw_selectors.txt` file in Task 2 has `<FILL IN>` markers — those are also intentional, the human fills them in by inspecting the page. **However**, Task 4's parser doesn't actually use those selectors — it uses heuristics (regex on numeric ranks, regex on `NGS .. %` text) that don't depend on specific class names. The selectors file is a safety net in case the heuristics fail; Task 4 doesn't reference it directly. This is fine — Task 2 produces diagnostic notes, Task 4 builds against the heuristics. If Task 4's heuristics fail in practice, the engineer reaches for `/tmp/bw_selectors.txt`.

No other placeholders.
