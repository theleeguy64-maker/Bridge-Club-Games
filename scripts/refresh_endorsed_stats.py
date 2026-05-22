"""Scrape latest 4 same-weekday results for each endorsed club and upsert to DB.

Scoped refresh used by CI before regenerating docs/index.html so the published
page always has fresh pairs/NGS.

Reads ENDORSED.md (for clubs_json_key + Day), joins to clubs.json for results_url,
then for each club fetches up to LOOKBACK_WEEKS of past same-weekday sessions
and records them in data/bridge_results.db.
"""

import json
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bridge_db
from bridge_finder import (
    slug_from_url, fetch, index_url, parse_index,
    result_url, parse_result_page,
)
from generate_endorsed_html import parse_endorsed_md, normalize

PROJECT_DIR = Path(__file__).resolve().parent.parent
ENDORSED_MD = PROJECT_DIR / "ENDORSED.md"
CLUBS_JSON = PROJECT_DIR / "clubs.json"

LOOKBACK_WEEKS = 4
DAY_NAME_TO_PY_WEEKDAY = {
    "Mon": 0, "Tue": 1, "Wed": 2, "Thu": 3, "Fri": 4, "Sat": 5, "Sun": 6,
}


def candidate_dates(weekday_int, weeks=LOOKBACK_WEEKS):
    """Return the last `weeks` dates for the given weekday (most recent first)."""
    today = date.today()
    offset = (today.weekday() - weekday_int) % 7
    most_recent = today - timedelta(days=offset)
    return [most_recent - timedelta(weeks=w) for w in range(weeks)]


def refresh_club(conn, name, slug, results_url, target_dates, day_label):
    """Fetch index, then for each target_date find the matching event and upsert."""
    try:
        index_html = fetch(index_url(slug))
    except Exception as e:
        print(f"  WARN {name}: index fetch failed: {e}", file=sys.stderr)
        return 0

    events = parse_index(index_html)  # list of (date, label, event_id)
    if not events:
        print(f"  WARN {name}: no events in index", file=sys.stderr)
        return 0

    target_set = {d.isoformat() for d in target_dates}
    matched = [(d, label, eid) for d, label, eid in events if d.isoformat() in target_set]

    # Also upsert the club row so the FK is satisfied
    bridge_db.upsert_club(conn, slug, name, day_label, "", results_url, "RealBridge")

    n = 0
    for d, label, eid in matched:
        try:
            result_html = fetch(result_url(slug, eid))
            pairs, ngs = parse_result_page(result_html)
            bridge_db.record_session(conn, slug, d.isoformat(), eid, pairs, ngs)
            n += 1
        except Exception as e:
            print(f"  WARN {name} {d}: result fetch failed: {e}", file=sys.stderr)
    conn.commit()
    return n


def main():
    endorsed = parse_endorsed_md(ENDORSED_MD)
    clubs = json.load(open(CLUBS_JSON, encoding="utf-8"))
    by_name = {normalize(c["name"]): c for c in clubs}

    conn = bridge_db.connect()
    bridge_db.init_db(conn)
    total = 0
    try:
        for row in endorsed:
            key = normalize(row["clubs_json_key"])
            club = by_name.get(key)
            if not club:
                continue
            url = club.get("results_url", "")
            if not url:
                continue
            slug = slug_from_url(url)
            if not slug:
                continue
            day_label = row["Day"]
            weekday_int = DAY_NAME_TO_PY_WEEKDAY[day_label]
            dates = candidate_dates(weekday_int)
            print(f"Refreshing {row['Club']} ({day_label}) — slug={slug}")
            n = refresh_club(conn, club["name"], slug, url, dates, day_label)
            print(f"  upserted {n} sessions")
            total += n
    finally:
        conn.close()
    print(f"\nDone — {total} session upserts across {len(endorsed)} endorsed clubs.")


if __name__ == "__main__":
    main()
