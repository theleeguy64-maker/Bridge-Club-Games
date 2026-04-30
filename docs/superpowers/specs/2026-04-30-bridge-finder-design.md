# Bridge Game Finder — Design

**Date:** 2026-04-30
**Project:** Bridge_Tournaments
**Owner:** Lee

## Purpose

A simple terminal app, launched from a Desktop `.command` file. The user enters a date; the app produces a table of UK online bridge games available on that day's afternoon or evening (12:00–23:00 UK), drawn from RealBridge and BBO. For each club it shows a 4-week rolling-median pair count, average NGS, and how to enter (cost + registration friction in one column).

Replaces the manual research-and-tabulate cycle done in chat.

## Scope

- **In:** UK clubs only. Saturday or Sunday only. PM/eve window only (≥12:00 UK).
- **Out:** worldwide clubs, face-to-face venues, weekday games, morning sessions.

## Acceptance signal (informal)

The script is working in production if Lee picks a game from its output (rather than asking in chat) on at least 4 of the next 6 weekends he wants to play. Not code-gated; informal review after ~6 weeks.

## Decisions log

| Decision | Choice | Rationale |
|---|---|---|
| Data source | Cached club list, live results lookup | UK weekend clubs are stable; only weekly results change |
| Date input | Flexible parsing (`dateparser`) pinned to UK locale | UK user; resolves `2/5/26` → 2 May |
| Empty input default | Next upcoming Sat or Sun | Empty=today fails on weekdays |
| Output | Terminal table (rich) + saved markdown file | Read on screen now, refer back later |
| Fetching | Sequential, one progress line per club, 10s timeout per fetch | Simple, never hangs |
| Club list storage | Hand-edited JSON with `last_verified` per entry | No script changes when clubs come/go; staleness visible |
| Parser strategy | Generic bridgewebs.com parser + static fallback | One parser covers most UK clubs |
| Missing data | Show `—`, explain in footer | Honest, no silent failures |
| Mode | Strict — one date → one day | One question, one answer |
| Time filter | PM/eve only (≥12:00) | Out-of-window clubs don't appear |
| Pairs metric | 4-week rolling median | Single weeks too volatile |
| NGS metric | Field average rendered as percentage (`54.0%`) | Matches EBU NGS units |
| Saturday banner | Show banner above Saturday tables | Saturday options are genuinely thin |
| Visitor / registration | Combined into one "How to enter" column | This is the actual decision driver |

## File layout

```
~/Casual_claude/Bridge_Tournaments/
├── scripts/
│   ├── check_tournaments.py          (existing, untouched)
│   └── bridge_finder.py              (new — main script)
├── clubs.json                        (new — canonical club list)
├── reports/                          (new — output markdown files; gitignored)
│   └── YYYY-MM-DD.md
└── .venv/                            (new or existing)

~/Desktop/
└── Bridge Games.command              (new — zsh launcher; named for memorability)
```

The `.command` launcher copies the structure of the existing `run_bridge_HG.command` (cd to project, activate `.venv`, run Python, drop to interactive shell). Implementation detail belongs in the build plan, not this spec.

`reports/` is added to the project's `.gitignore`. The repo is private but reports may accumulate forever and serve no value in version control.

## `clubs.json` schema

Array of objects. One per club.

```json
{
  "name": "Whitley Bay & Tynemouth",
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
}
```

| Field | Type | Notes |
|---|---|---|
| `name` | string | Display name |
| `platform` | string | `"RealBridge"` or `"BBO"` |
| `day` | string | `"Sat"`, `"Sun"`, or `"both"` |
| `time_uk` | string | `"HH:MM"` (24h). Slash-separated list permitted only when `parser == "static"` |
| `cost` | string | Cached cost string |
| `results_url` | string or null | Bridgewebs club URL. `null` for `parser: "static"` |
| `parser` | string | `"bridgewebs"` or `"static"` |
| `visitor_policy` | string | `"open"` / `"contact_first"` / `"members_only"` |
| `registration.required` | bool | Whether per-session entry needed |
| `registration.url` | string | Where to register, if required |
| `registration.deadline` | string | Human-readable deadline |
| `registration.notes` | string | Free text |
| `how_to_enter_summary` | string | Short imperative phrase rendered in the table's "How to enter" column. Author-supplied; one of: `"Open"`, `"Bank £X to club before session"`, `"Register via {host} by {time}"`, `"Contact {name} on {phone}"`, etc. |
| `last_verified` | string (ISO date) | Date the author last sanity-checked this entry. Script warns if older than 180 days |
| `notes` | string | Free text shown in report |

Static-parser entries also include:
```json
"baseline_pairs": "20+",
"baseline_ngs_label": "Mixed, NGS-rated"
```

(Static entries do **not** include `verified_visitor_cost` — that field is bridgewebs-only.)

## Seed data (7 clubs)

Newbury is **not** included — it's a Saturday morning club outside the PM/eve window. Documented here only for context. (Removed from `clubs.json` entirely; was previously included only to be filtered out, which was wrong factoring.)

| Club | Day | Time | Platform | Parser | How to enter (summary) |
|---|---|---|---|---|---|
| Whitley Bay & Tynemouth (afternoon) | Sat | 13:00 | RealBridge | bridgewebs | Bank £3 to club before session |
| Whitley Bay & Tynemouth (evening) | Sat | 19:00 | RealBridge | bridgewebs | Bank £3 to club before session |
| Hunstanton Sunday Pairs | Sun | 19:00 | RealBridge | bridgewebs | First visit: register; £2 visitors |
| EBU Super Sunday Special | Sun | 19:00 | RealBridge | bridgewebs | Register at Cumbria CBA by 17:00; £2.50 |
| Friendly Online BC | Sun | 19:15 | BBO | bridgewebs | Open, ~$2 BB$ |
| EBU Daily BBO | both | 14:00 / 15:30 / 19:30 / 21:00 | BBO | static | Open, ~£1.80 |
| Dragon Pairs / Oliver Cowan | Sat | 13:00 | BBO | static | Periodic only; check Oliver Cowan calendar |

## Date input

Single prompt:

```
Date of game (e.g. "next sat", "2 May", or blank)?
```

Parsed with `dateparser.parse(input, settings={'DATE_ORDER': 'DMY', 'PREFER_DATES_FROM': 'future'})`. Accepts `2026-05-02`, `2/5/26`, `2 May`, `Sat 2 May`, `next Saturday`, `tomorrow`, bare `sat`/`sun`. UK locale pinned so `2/5/26` reliably means 2 May.

**Empty input** → next upcoming Saturday or Sunday (whichever is sooner). If today is Saturday or Sunday, empty → today.

After parsing, echo `→ Saturday 2 May 2026` for awareness, then proceed.

**Failures:**
- Unparseable: print error, re-prompt, max 3 attempts then `sys.exit(1)`.
- Parsed date is not Sat/Sun: print `Script only handles Saturday or Sunday games — parsed {weekday}`, exit 1.

## bridgewebs parser

**Inputs:** club's `results_url`, target date, `time_uk`.

**Output:**
```python
{
    "median_pairs_4w": int | None,    # rolling median of last 4 same-weekday sessions including target
    "latest_pairs": int | None,       # most recent session's pair count, for drift canary
    "ngs_avg": float | None,          # percentage e.g. 54.0
    "session_date": str,              # ISO date actually used
    "session_url": str | None,
    "fallback_used": bool,
    "fallback_weeks_back": int,       # 0 if target date hit; 1+ if walked back
    "drift_warning": bool,            # True if latest_pairs differs from median by >50%
    "error": str | None
}
```

**Algorithm:**

1. **Find results index.** Pattern: `https://www.bridgewebs.com/cgi-bin/bwor/bw.cgi?club={slug}&pid=display_past`, where `{slug}` is parsed from `results_url`. The cgi-bin shard prefix (`bwor` / `bwos` / `bwoq` / `bwx`) is interchangeable in practice; use `bwor` and let the server resolve.

2. **Find the target session.** Locate entries matching the target date. If multiple sessions on that day, pick by case-insensitive substring match on `time_uk` (e.g. `"19:00"` or `"7pm"` against the session label).

3. **Date fallback.** If target date isn't in the index OR session has no published result yet:
   - Walk backwards through same-weekday sessions, week by week, up to 4 weeks.
   - First with a published result wins. Set `fallback_used = True`, `fallback_weeks_back = N`, `session_date` to the older date.
   - If 4 weeks back yields nothing → `error: "No recent sessions found"`.

4. **Collect last 4 same-weekday sessions** (target session + 3 prior weeks). Each that has a published result contributes a pair count. Compute `median_pairs_4w` from whatever count we have (1, 2, 3 or 4 values). `latest_pairs = pairs in the most recent of those`.

5. **Drift canary.** If `latest_pairs / median_pairs_4w` is outside `[0.5, 1.5]`, set `drift_warning = True` (e.g. parser miscounted or club had unusual session).

6. **Pair count parsing.** Locate the result page's ranking table (CSS selector pinned during build by sampling a real page — see Open implementation questions below). Count rows.

7. **NGS extraction.**
   - Look for a page-header NGS event average → use that.
   - Else if the result table has an NGS column → arithmetic mean across rated rows.
   - Else `ngs_avg = None`.
   - NGS is treated as a percentage throughout (EBU convention).

**Encoding.** bridgewebs.com serves `iso-8859-1`. Use `response.content` and decode explicitly: `response.content.decode("iso-8859-1")`. Don't use `response.text` blindly.

**HTTP config (universal across all fetches):**
- `timeout=10` seconds per request
- `User-Agent: BridgeFinder/0.1 (lee personal use)`
- No retries — fail fast

**Failure modes:** any exception or non-2xx → `error` set, all data fields `None`. Network error vs SSL vs HTTP 4xx/5xx all surface as one `"Network error"` string.

## static parser

For `parser: "static"` entries, no live fetch. Returns:

```python
{
    "median_pairs_4w": club["baseline_pairs"],   # e.g. "20+" — string in this case
    "latest_pairs": None,
    "ngs_avg": None,                              # render uses baseline_ngs_label instead
    "session_date": None,
    "session_url": None,
    "fallback_used": False,
    "fallback_weeks_back": 0,
    "drift_warning": False,
    "error": None
}
```

In the rendered table, the NGS column shows `baseline_ngs_label` for static rows.

## Script flow

1. Print banner: `Bridge Game Finder`
2. Prompt for date.
3. Parse with `dateparser` (UK settings). Re-prompt up to 3 times. Empty → next Sat/Sun.
4. Echo: `→ Saturday 2 May 2026`
5. If not Sat/Sun: error, exit 1.
6. Load `clubs.json`. Filter:
   - `day` matches the parsed date's weekday OR `day == "both"`
   - Earliest of the entry's `time_uk` slots is `>= "12:00"`
   - Warn (don't fail) for any club with `last_verified` more than 180 days ago.
7. Expand multi-time entries: for each `parser: "static"` entry with slash-separated `time_uk` (e.g. `"14:00 / 15:30 / 19:30 / 21:00"`), emit one row per slot. (Multi-time only allowed for static parser — bridgewebs entries must have a single `time_uk`.)
8. Sort all expanded rows by `time_uk` ascending.
9. For each unique club (one fetch per club, not per slot), in order:
   - Print `  Fetching {name}... ` (no newline)
   - Run the appropriate parser
   - Print result on the same line: `✓ N pairs (median 4w)` / `— ({error})` / `static`
10. Build the table.
11. **Saturday banner:** if the parsed weekday is Saturday, print `Note: Saturday options are limited — Sunday has more variety.` above the table.
12. Render to terminal with `rich`.
13. Ensure `~/Casual_claude/Bridge_Tournaments/reports/` exists (`mkdir -p` semantics). Write markdown report there as `{date}.md`. All file I/O uses `encoding="utf-8"`.
14. Print: `Report saved to {path}`.
15. Exit 0.

## Output — terminal table

Columns:

1. **UK time** — `time_uk` (one row per slot for multi-time static entries)
2. **Club** — `name`
3. **Platform** — `RealBridge` or `BBO`
4. **Pairs (4w median)** — int, or `20+` for static, or `—` if unknown. Drift warning shown as `9 ⚠` (warning glyph).
5. **Avg NGS** — `54.0%` (one decimal, percent sign), or `—`, or `baseline_ngs_label` for static
6. **How to enter** — short imperative from `how_to_enter_summary` (e.g. `Bank £3 to club before session`, `Register at Cumbria CBA by 17:00`, `Open`)

Below the table — combined footnote section, one entry per affected club (chronological by club appearance), each containing all relevant caveats:

- If `fallback_used`: `{Club} — showing N week(s) ago ({date}); {requested_date} not yet published.`
- If `error`: `{Club} — {error}. Data unavailable for this run; the club may still be running — check their site.`
- If `drift_warning`: `{Club} — last week's pairs differ sharply from the 4-week median; data may be unreliable.`
- If `last_verified` >180 days ago: `{Club} — entry last verified {date} (>180 days ago); URLs may have changed.`

## Output — markdown report

Same table in GitHub-flavoured markdown. Same footnotes. Header:

```markdown
# Bridge games — Saturday 2 May 2026

Generated {ISO timestamp in Europe/London with correct BST/GMT label}.
```

Timestamp uses `zoneinfo.ZoneInfo("Europe/London")`; the timezone abbreviation (`BST` or `GMT`) is read from `datetime.tzname()` so it's always correct.

Filename: `~/Casual_claude/Bridge_Tournaments/reports/{date}.md`. Re-running the same date overwrites without warning. (Reports are regenerable; a versioning scheme is deferred to v2.)

## Dependencies

- `dateparser`
- `requests`
- `beautifulsoup4`
- `rich`

Manual install into the project's `.venv` documented in the build plan. No bootstrap from the script (deferred to v2).

## Error handling summary

| Failure | User sees |
|---|---|
| Unparseable date input | Re-prompt (max 3) |
| Date not Sat/Sun | Error, exit 1 |
| `clubs.json` missing or malformed | Error with path, exit 1 |
| Empty filter result (no clubs match the day/time) | Empty table with message: `No clubs match this day in the PM/eve window.` |
| Network error fetching club | Row shows `—`, footnote `{Club} — Network error. Data unavailable.` |
| Bridgewebs page structure changed | Row shows `—`, footnote `{Club} — Couldn't parse results page.` |
| No recent sessions in 4 weeks | Row shows `—`, footnote `{Club} — No recent sessions found.` |
| Stale `last_verified` (>180 days) | Row renders normally, footnote `{Club} — entry last verified {date}; check URLs.` |

The script never crashes silently; it always renders a table.

## Open implementation questions (resolved during build, not in spec)

These were caught in spec review but defer to the implementer to pin via real-page sampling:

1. **Bridgewebs CSS selectors.** The exact CSS class for the result page's ranking table and the NGS-event-average header. Implementer samples one Whitley Bay result page during initial build, pins selectors in code constants, and notes them in a code comment.

2. **`how_to_enter_summary` per club.** The seed data above gives starting strings; implementer may refine after seeing real result/registration pages.

## Testing

Manual smoke tests after build:
1. Run with next Sat → expect Whitley Bay (afternoon + evening) + EBU dailies. Saturday banner shown.
2. Run with next Sun → expect Hunstanton, SSS, FOBC, EBU dailies. No Saturday banner.
3. Run with weekday → expect "Sat/Sun only" error, exit 1.
4. Run with garbage input → expect re-prompt.
5. Run with date 4+ weeks in the future → expect rows with `—` and "No recent sessions found" footnotes.
6. Run with empty input on a weekday → expect parsed date = next upcoming Sat or Sun.
7. Edit one club's `last_verified` to 2025-01-01 → expect stale-entry footnote.

No automated tests planned. The script is small, failures are visible in rendered output, and data sources are external.

## Future enhancements (not in scope for v1)

- Live-update table during fetch (vs scrolling progress lines).
- Same-day result caching (avoid redundant fetches if user runs script multiple times).
- EBU Daily NGS pulled from EBU site instead of `None` for static rows.
- Concurrency lock against double-click.
- SIGINT (Ctrl-C) handling — emit partial report.
- Atomic write for reports.
- NGS spread / sigma alongside mean.
- Versioned reports (e.g. `2026-05-02-103045.md` for repeated runs same day).
- Dependency bootstrap on first run.
- Worldwide clubs (Saturday is genuinely thin worldwide, per chat research).
- Sat+Sun combined report.
- Weekday games.
- Auto-add new clubs by scanning EBU's RealBridge club list PDF.
