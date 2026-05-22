"""Generate distributable HTML of Lee's endorsed bridge clubs.

Spec: docs/superpowers/specs/2026-05-22-endorsed-html-page.md

Reads ENDORSED.md + clubs.json + DB. Writes reports/dist/endorsed.html.

Exit codes:
  0  clean run
  1  hard-fail (gate tripped, validation failed; no output written)
  2  soft-fail (output written, but stderr warnings emitted)
"""

import html
import json
import os
import statistics
import sys
from datetime import datetime, date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bridge_db
from bridge_finder import slug_from_url

PROJECT_DIR = Path(__file__).resolve().parent.parent
ENDORSED_MD = PROJECT_DIR / "ENDORSED.md"
CLUBS_JSON = PROJECT_DIR / "clubs.json"
OUTPUT_PATH = PROJECT_DIR / "docs" / "index.html"

DAY_TO_SQLITE_WEEKDAY = {
    "Sun": "0", "Mon": "1", "Tue": "2", "Wed": "3",
    "Thu": "4", "Fri": "5", "Sat": "6",
}

EXIT_OK = 0
EXIT_HARD_FAIL = 1
EXIT_SOFT_FAIL = 2

_warnings = []


def warn(msg):
    print(f"WARN: {msg}", file=sys.stderr)
    _warnings.append(msg)


def die(msg):
    print(f"FATAL: {msg}", file=sys.stderr)
    sys.exit(EXIT_HARD_FAIL)


def normalize(s):
    return (s or "").replace("\xa0", " ").strip()


def parse_endorsed_md(path):
    """Parse the ENDORSED.md table. Returns list of dicts."""
    rows = []
    with open(path, encoding="utf-8") as f:
        lines = f.readlines()
    header = None
    for line in lines:
        line = line.rstrip("\n")
        if not line.startswith("|"):
            continue
        cells = [normalize(c) for c in line.strip("|").split("|")]
        if header is None:
            header = cells
            continue
        if all(set(c) <= set("-: ") for c in cells):  # separator row
            continue
        rows.append(dict(zip(header, cells)))
    return rows


def load_clubs(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def validate_clubs_unique(clubs):
    seen = {}
    for c in clubs:
        key = normalize(c["name"]).casefold()
        if key in seen:
            die(f"duplicate club name in clubs.json: {c['name']!r} (also {seen[key]!r})")
        seen[key] = c["name"]


def validate_clubs_json_keys(endorsed, clubs):
    """A row may opt out of the clubs.json join by leaving clubs_json_key blank
    AND supplying both pairs_override and ngs_override. Rows with a key must
    match exactly one clubs.json entry."""
    by_name = {normalize(c["name"]): c for c in clubs}
    offenders = []
    for row in endorsed:
        key = normalize(row.get("clubs_json_key", ""))
        if not key:
            if normalize(row.get("pairs_override", "")) and normalize(row.get("ngs_override", "")):
                continue  # override-only row, no clubs.json lookup needed
            offenders.append(f"{row.get('Club','?')} ({row.get('Day','?')}): empty clubs_json_key (and no pairs_override + ngs_override)")
        elif key not in by_name:
            offenders.append(f"{row.get('Club','?')} ({row.get('Day','?')}): no clubs.json match for {key!r}")
    if offenders:
        for o in offenders:
            print(f"FATAL: {o}", file=sys.stderr)
        sys.exit(EXIT_HARD_FAIL)


def required_fields_gate(endorsed):
    """clubs_json_key may be blank only if both overrides are provided."""
    required = ["Day", "Time", "Club", "Platform"]
    offenders = []
    for row in endorsed:
        for f in required:
            if not normalize(row.get(f, "")):
                offenders.append(f"{row.get('Club','?')}: missing {f}")
        if not normalize(row.get("clubs_json_key", "")):
            if not (normalize(row.get("pairs_override", "")) and normalize(row.get("ngs_override", ""))):
                offenders.append(f"{row.get('Club','?')}: missing clubs_json_key and no overrides")
    if offenders:
        for o in offenders:
            print(f"FATAL: {o}", file=sys.stderr)
        sys.exit(EXIT_HARD_FAIL)


def mean_or_none(values):
    clean = [v for v in values if v is not None]
    if not clean:
        return None
    return statistics.mean(clean)


def build_rows(endorsed, clubs, conn):
    by_name = {normalize(c["name"]): c for c in clubs}
    out = []
    today = date.today()
    for row in endorsed:
        key = normalize(row.get("clubs_json_key", ""))
        pairs_override = normalize(row.get("pairs_override", ""))
        ngs_override = normalize(row.get("ngs_override", ""))

        # Override-only row (no clubs.json join, no DB lookup, no warnings)
        if not key and pairs_override and ngs_override:
            out.append({
                "Day": row["Day"], "Time": row["Time"], "Club": row["Club"],
                "Platform": row["Platform"], "Note": row.get("Note", ""),
                "url": "",
                "pairs_mean": pairs_override, "ngs_mean": ngs_override,
                "partial": False, "stale": False, "max_date": None,
            })
            continue

        club = by_name[key]
        url = club.get("results_url", "")
        if not url:
            warn(f"{row['Club']} ({row['Day']}): no results_url in clubs.json")
        slug = slug_from_url(url) if url else None
        weekday = DAY_TO_SQLITE_WEEKDAY[row["Day"]]
        sessions = bridge_db.rolling_4w(conn, slug, weekday) if slug else []

        pairs_vals = [s[1] for s in sessions]
        ngs_vals = [s[2] for s in sessions]
        non_null_pairs = [v for v in pairs_vals if v is not None]
        non_null_ngs = [v for v in ngs_vals if v is not None]

        pairs_mean = mean_or_none(pairs_vals)
        ngs_mean = mean_or_none(ngs_vals)
        # Per-cell override wins over computed value
        if pairs_override:
            pairs_mean = pairs_override
        if ngs_override:
            ngs_mean = ngs_override
        partial = 0 < len(non_null_pairs) < 4 or 0 < len(non_null_ngs) < 4

        max_date = max((s[0] for s in sessions), default=None)
        stale = False
        if max_date:
            try:
                d = datetime.strptime(max_date, "%Y-%m-%d").date()
                stale = (today - d).days > 28
            except ValueError:
                pass

        if not sessions and not (pairs_override and ngs_override):
            warn(f"{row['Club']} ({row['Day']}): no DB sessions in 4wk window")

        out.append({
            "Day": row["Day"],
            "Time": row["Time"],
            "Club": row["Club"],
            "Platform": row["Platform"],
            "Note": row.get("Note", ""),
            "url": url,
            "pairs_mean": pairs_mean,
            "ngs_mean": ngs_mean,
            "partial": partial,
            "stale": stale,
            "max_date": max_date,
        })
    return out


def fmt_num(v, partial):
    if v is None:
        return "—"
    if isinstance(v, str):  # literal override from ENDORSED.md
        return html.escape(v)
    s = f"{v:.1f}"
    if partial:
        s += ' <span class="partial">(partial)</span>'
    return s


def render_html(rows, endorsed_count):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    max_dates = [r["max_date"] for r in rows if r["max_date"]]
    data_as_of = max(max_dates) if max_dates else "—"

    trs = []
    for r in rows:
        club_cell = html.escape(r["Club"])
        if r["url"]:
            club_cell = f'<a href="{html.escape(r["url"], quote=True)}">{html.escape(r["Club"])}</a>'
        stale_badge = ' <span class="stale">stale</span>' if r["stale"] else ""
        trs.append(
            f'<tr>'
            f'<td>{html.escape(r["Day"])}</td>'
            f'<td>{html.escape(r["Time"])}</td>'
            f'<td>{club_cell}</td>'
            f'<td class="num">{fmt_num(r["pairs_mean"], r["partial"])}{stale_badge}</td>'
            f'<td class="num">{fmt_num(r["ngs_mean"], r["partial"])}</td>'
            f'<td>{html.escape(r["Note"])}</td>'
            f'</tr>'
        )
    body_rows = "\n".join(trs)

    if len(rows) != endorsed_count:
        die(f"row-count gate: rendered {len(rows)} != ENDORSED.md {endorsed_count}")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>RealBridge Bridge Club Games</title>
<style>
  :root {{ color-scheme: dark; }}
  body {{
    background: #0e1217; color: #e6e6e6;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
    margin: 0; padding: 1.5rem; line-height: 1.5;
  }}
  h1 {{ font-size: 1.4rem; margin: 0 0 0.25rem; }}
  .ts {{ color: #8a96a3; font-size: 0.85rem; margin-bottom: 1rem; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 0.95rem; }}
  th, td {{ padding: 0.5rem 0.6rem; text-align: left; border-bottom: 1px solid #232a33; vertical-align: top; }}
  th {{ background: #161c24; color: #b8c2cc; font-weight: 600; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.05em; }}
  td.num {{ text-align: right; font-variant-numeric: tabular-nums; }}
  a {{ color: #6cb4ff; text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}
  .stale {{ display: inline-block; background: #5a2a2a; color: #ffb4b4; font-size: 0.7rem; padding: 0.05rem 0.4rem; border-radius: 0.25rem; margin-left: 0.4rem; }}
  .partial {{ color: #b8b86c; font-size: 0.8rem; }}
  footer {{ color: #8a96a3; font-size: 0.85rem; margin-top: 1rem; }}
  @media (max-width: 600px) {{
    body {{ padding: 0.75rem; }}
    th, td {{ padding: 0.4rem 0.35rem; font-size: 0.85rem; }}
    th {{ font-size: 0.7rem; }}
  }}
</style>
</head>
<body>
<h1>RealBridge Bridge Club Games</h1>
<div class="ts">Generated {now} (UK time)</div>
<table>
  <thead>
    <tr><th>Day</th><th>Time</th><th>Club</th><th>4wk pairs</th><th>4wk NGS</th><th>Note</th></tr>
  </thead>
  <tbody>
{body_rows}
  </tbody>
</table>
<footer>
Data as of {html.escape(data_as_of)} — newest session across all rows. Pairs/NGS from bridgewebs.com rolling 4-week window.<br>
<span class="partial">(partial)</span> = fewer than 4 same-weekday sessions in the last 28 days, so the average is based on less data than usual.
</footer>
</body>
</html>
"""


def atomic_write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(content)
    os.replace(tmp, path)


def main():
    endorsed = parse_endorsed_md(ENDORSED_MD)
    if not endorsed:
        die("no rows parsed from ENDORSED.md")

    clubs = load_clubs(CLUBS_JSON)
    validate_clubs_unique(clubs)
    validate_clubs_json_keys(endorsed, clubs)
    required_fields_gate(endorsed)

    conn = bridge_db.connect()
    try:
        rows = build_rows(endorsed, clubs, conn)
    finally:
        conn.close()

    html_out = render_html(rows, endorsed_count=len(endorsed))
    atomic_write(OUTPUT_PATH, html_out)

    print(f"Wrote {OUTPUT_PATH.relative_to(PROJECT_DIR)} ({len(rows)} rows, {len(_warnings)} warnings)")
    sys.exit(EXIT_SOFT_FAIL if _warnings else EXIT_OK)


if __name__ == "__main__":
    main()
