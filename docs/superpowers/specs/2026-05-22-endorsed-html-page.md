# Spec: Endorsed Shortlist — Distributable HTML Page

**Date:** 2026-05-22
**Status:** Draft (lee accept — product + dev lenses applied 2026-05-22)

## Goal
A single self-contained HTML file showing Lee's endorsed bridge clubs. Distributable — Lee emails / AirDrops / messages it to a friend, they double-click, it opens in any browser. No server, no install, no login.

## Non-goals
- No security, auth, or access control (shareable-with-known-friends by design — see Privacy below).
- No personal play history in the distributable output (the `Played` column stays in `ENDORSED.md` for Lee's own use but is not rendered into `endorsed.html`).
- No live data fetch — snapshot at generation time.
- No interactivity beyond clicking a link.
- No mobile-specific styling beyond basic responsive layout.

## Privacy
The file is distributed to known friends, not posted publicly. The `Played` column from `ENDORSED.md` (Lee's personal play history) is **excluded** from the rendered output to avoid leaking routine/location patterns even if the file is forwarded.

## Source
- `ENDORSED.md` — the shortlist (8 clubs currently).
- `clubs.json` — for `results_url` per club (the bridgewebs page; doubles as "where to go").
- `data/bridge_results.db` — for 4-week rolling pairs + NGS averages.

## Schema change: add `clubs_json_key` to ENDORSED.md

`ENDORSED.md` short names ("Ascot", "Chelmsford") do NOT match `clubs.json` suffixed names ("Ascot Bridge Club (Mon PM)") — naive name-equality fails 7/8 rows. To fix the join unambiguously:

Add a **`clubs_json_key`** column to `ENDORSED.md`. Value is the exact `name` string from `clubs.json` for the intended entry. This is the load-bearing join key — generator looks up `clubs.json` by `name == clubs_json_key`, then reads `results_url` from that entry.

**Startup validation (hard-fail, exit non-zero):**
- Every `clubs_json_key` in `ENDORSED.md` MUST match exactly one entry in `clubs.json` (case-sensitive, NBSP-normalized). If any row's key matches zero or >1 entries, the generator exits non-zero and lists offenders to stderr.
- `clubs.json` MUST have no duplicate `name` values (case-insensitive, NBSP-normalized). Generator exits non-zero on first duplicate detected.
- Empty `clubs_json_key` cell is also a hard-fail (added to the required-field gate below).

New `ENDORSED.md` columns: **Day | Time | Club | Platform | clubs_json_key | Played | Note**

(URL is NOT stored in `ENDORSED.md` — it's looked up at render time from `clubs.json`.)

The existing 8 rows must be backfilled with `clubs_json_key` before the generator can run.

## DB join: (slug, weekday) composite key

`clubs.json` has no `slug` field — slugs only exist in the DB, derived from the bridgewebs URL at upsert time. Clubs that share a bridgewebs URL (e.g. Chelmsford Mon/Tue/Fri all hit `bridgewebs.com/chelmsford/`) share a single slug, so slug-alone joins collide.

**Timezone & date contract.** `session_date` is stored as a date-only ISO string in UK local (no time component). The weekday for the join MUST come from the `ENDORSED.md` `Day` column — it is NEVER derived from `session_date` (that would re-introduce TZ drift via SQLite's UTC-based `'now'`).

**Weekday encoding.** SQLite `strftime('%w', ...)` returns a **TEXT** value with **Sunday=0** convention. Python `datetime.weekday()` uses **Monday=0**. The generator MUST remap and bind as a string:

```python
DAY_TO_SQLITE_WEEKDAY = {
    "Sun": "0", "Mon": "1", "Tue": "2", "Wed": "3",
    "Thu": "4", "Fri": "5", "Sat": "6",
}
weekday = DAY_TO_SQLITE_WEEKDAY[row["Day"]]  # str, not int
cursor.execute(SQL, (slug, weekday))         # binding an int returns 0 rows silently
```

The generator MUST use a composite `(slug, weekday)` key:

```sql
SELECT pairs, ngs FROM sessions
WHERE club_slug = ?
  AND strftime('%w', session_date) = ?   -- bind as TEXT, Sun=0..Sat=6
  AND session_date >= date('now', '-28 days')
ORDER BY session_date DESC
```

The slug is derived from the `clubs.json` entry's `results_url`. The generator MUST `from bridge_finder import slug_from_url` rather than re-implementing the rule (avoids drift if the canonical function changes).

## 4wk rolling-window query (new capability)

No existing query in `bridge_db.py` returns a 4wk rolling window. `latest_per_club` returns only MAX(session_date); `median_pairs_4w` lives in `bridge_finder.py` and reads live-fetched data, not the DB. The generator MUST add a new function `rolling_4w(slug, weekday)` to `bridge_db.py` (per project convention — DB queries live in the DB module, never inline in callers) returning the rows for the SQL above.

**Mean calculation:** filter `None` values out of the result before averaging (`pairs` / `ngs` columns are nullable; `statistics.mean([None, ...])` raises). The `(partial)` tag (see below) counts **non-NULL sessions** within the 4-week window, not the total row count.

## Render schema (HTML output)

Each row in the rendered HTML: **Day | Time | Club | Platform | 4wk pairs | 4wk NGS | Note**

(`Played` excluded for privacy; `clubs_json_key` is internal-only; `URL` is rendered as a hyperlink on the Club name, not a separate column — see Output below.)

## Output
- One file: `reports/dist/endorsed.html`. Lives under `reports/` (already gitignored, matches existing generated-artifact convention). No new top-level dir.
- Atomic write: generator writes to `<output>.tmp` then `os.replace()` to the final path. Avoids friend opening a truncated file if the generator is killed mid-write.
- All file I/O uses `encoding="utf-8"` (matches `bridge_finder.py` / `generate_verified.py` convention).
- All dynamic cell content (club names, notes, hrefs) is passed through `html.escape()` before templating. Five real club names contain `&` (Whitley Bay & Tynemouth, Hellesdon & Taverham, Allendale & Retford, Blewbury & Wantage, Lymington & West Wight) — un-escaped, these mangle the output.
- Self-contained: inline CSS, no external assets, no JS required.
- Dark theme, readable on phone + desktop.
- Each row renders the columns above; the Club name is the hyperlink to its bridgewebs page (no separate URL column — keeps table width tight on phone).
- Per-row staleness badge: if `MAX(session_date)` for a row's `(slug, weekday)` is >28 days old (matches the rolling-window cut-off — one threshold, not two), render a small visible badge ("stale", coloured) next to the 4wk columns. No behaviour change for the friend; just an honest signal.
- Header: "Lee's endorsed UK online bridge clubs" + **generation timestamp** in ISO-8601 UK-local `YYYY-MM-DD HH:MM` with "(UK time)" suffix — answers "when was this file built".
- Footer: "Data as of `YYYY-MM-DD` — newest session across all 8 rows" — uses `MAX(session_date)` across the rendered rows, NOT the generation time. Answers "how fresh is the data" (different question from the header — conflating them hides staleness).

## Empty / partial / missing data behaviour

- **Missing `results_url`** in clubs.json for a row → render the club name as plain text (no hyperlink) AND emit a stderr warning naming the row. Friend sees the row; Lee sees what to fix.
- **DB returns 0 sessions** in the 4wk window for `(slug, weekday)` → render "—" in the pairs/NGS cells AND stderr warn.
- **DB returns 1–3 sessions** (partial coverage, less than the 4 expected) → render the mean as normal, but append an inline `(partial)` tag in the cell. Honest signal, no row dropped.

In all cases the row is rendered — never silently dropped. The friend always sees the full 8-row table.

## Correctness criterion (build-time gates) & exit codes

The generator MUST enforce these gates. Exit codes are distinct so callers (cron, CI, future wrappers) can distinguish clean vs degraded vs broken runs:

- **Exit 0:** clean run, no warnings.
- **Exit 1:** hard-fail — any gate below tripped, or any startup validation tripped. No output file written.
- **Exit 2:** soft-fail — file written successfully, but at least one stderr warning emitted (e.g. missing URL, missing DB stats, partial coverage). Output is still distributable but degraded.

Gates (all exit 1):

1. **Row-count gate:** rendered HTML row count == `ENDORSED.md` row count. Any silent drop = exit 1.
2. **Required-field gate:** every rendered row has non-empty `Day`, `Time`, `Club`, `Platform`, `clubs_json_key`. Any blank in these columns = exit 1.
3. **clubs_json_key validation gate** (see Schema change section): every key matches exactly one `clubs.json` entry; no duplicates in `clubs.json`. Exit 1 with offender list.

Missing URL / missing DB stats / partial coverage do NOT trip the gates — they have their own fallback render rules above AND trigger exit 2.

## Generator
- New script: `scripts/generate_endorsed_html.py`.
- Reads `ENDORSED.md`, joins to `clubs.json` by `clubs_json_key` for `results_url`, calls `bridge_db.rolling_4w(slug, weekday)` for 4wk averages (see queries above).
- Writes `endorsed.html` (atomic — see Output).
- Re-run manually; no automation.

**ENDORSED.md parser:** split on `|`, skip the header row and the `|---|` alignment separator row, `.strip()` each cell, normalize NBSP (`\xa0`) to regular space. No third-party markdown library.

**Build-step task:** create `reports/dist/` if missing. `reports/` is already gitignored — no new `.gitignore` entry needed.

## Concurrency

`bridge_db.py` MUST enable WAL mode + `busy_timeout=5000` once at connection setup. Applies to both `bridge_finder.py` (writer) and the new generator (reader), so the generator can read a consistent snapshot while `bridge_finder.py` writes without `SQLITE_BUSY` errors. Standard SQLite hygiene; one-line PRAGMA change in the DB module.

## Scope decisions (resolved)

- **Endorsed-only**, no verified-but-not-endorsed section. Matches "endorsed shortlist" framing — the 41-verified list is a different product, not a fold-out of this one.
- **Branding / extra styling:** none beyond dark + readable for v1.

## Open questions

None remaining — see Scope decisions above. Spec is implementable.
