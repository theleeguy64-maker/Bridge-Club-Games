# Spec: Endorsed Shortlist — Distributable HTML Page

**Date:** 2026-05-22
**Status:** Draft (lee accept — product lens applied 2026-05-22)

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

Add a **`clubs_json_key`** column to `ENDORSED.md`. Value is the exact `name` string from `clubs.json` for the intended entry. This is the load-bearing join key — generator looks up `clubs.json` by `name == clubs_json_key`, then reads `results_url` from that entry. (Alternative considered: fuzzy match + day-of-week tiebreak. Rejected — adds parser complexity and silent-failure surface; explicit key is one line of data per row and impossible to misread.)

New `ENDORSED.md` columns: **Day | Time | Club | Platform | clubs_json_key | Played | Note**

(URL is NOT stored in `ENDORSED.md` — it's looked up at render time from `clubs.json`.)

The existing 8 rows must be backfilled with `clubs_json_key` before the generator can run.

## DB join: (slug, weekday) composite key

`clubs.json` has no `slug` field — slugs only exist in the DB, derived from the bridgewebs URL at upsert time. Clubs that share a bridgewebs URL (e.g. Chelmsford Mon/Tue/Fri all hit `bridgewebs.com/chelmsford/`) share a single slug, so slug-alone joins collide.

The generator MUST use a composite `(slug, weekday)` key:

```sql
SELECT pairs, ngs FROM sessions
WHERE club_slug = ?
  AND strftime('%w', session_date) = ?   -- 0=Sun, 1=Mon, ..., 6=Sat
  AND session_date >= date('now', '-28 days')
ORDER BY session_date DESC
```

The slug is derived from the `clubs.json` entry's `results_url` (same derivation rule as `bridge_finder.py`).

## 4wk rolling-window query (new capability)

No existing query in `bridge_db.py` returns a 4wk rolling window. `latest_per_club` returns only MAX(session_date); `median_pairs_4w` lives in `bridge_finder.py` and reads live-fetched data, not the DB. The generator MUST introduce the SQL above as a new query — either inline in `scripts/generate_endorsed_html.py` or added to `bridge_db.py` as `rolling_4w(slug, weekday)`. Decision deferred to implementation, but new code is required either way.

Output: mean of `pairs` and `ngs` across the returned rows. Render conventions for sparse data — see "Empty / partial data" below.

## Render schema (HTML output)

Each row in the rendered HTML: **Day | Time | Club | Platform | 4wk pairs | 4wk NGS | Note**

(`Played` excluded for privacy; `clubs_json_key` is internal-only; `URL` is rendered as a hyperlink on the Club name, not a separate column — see Output below.)

## Output
- One file: `dist/endorsed.html` (new `dist/` directory, gitignored — explicit "distributable artifact" location, keeps repo clean and avoids accidentally committing personal data).
- Self-contained: inline CSS, no external assets, no JS required.
- Dark theme, readable on phone + desktop.
- Each row renders the columns above; the Club name is the hyperlink to its bridgewebs page (no separate URL column — keeps table width tight on phone).
- Per-row staleness badge: if the underlying DB stats for a row are >30 days old, render a small visible badge ("stale", coloured) next to the 4wk columns. No behaviour change for the friend; just an honest signal.
- Header: "Lee's endorsed UK online bridge clubs" + generation timestamp.
- Footer: "Snapshot generated YYYY-MM-DD from bridgewebs results."

## Empty / partial / missing data behaviour

- **Missing `results_url`** in clubs.json for a row → render the club name as plain text (no hyperlink) AND emit a stderr warning naming the row. Friend sees the row; Lee sees what to fix.
- **DB returns 0 sessions** in the 4wk window for `(slug, weekday)` → render "—" in the pairs/NGS cells AND stderr warn.
- **DB returns 1–3 sessions** (partial coverage, less than the 4 expected) → render the mean as normal, but append an inline `(partial)` tag in the cell. Honest signal, no row dropped.

In all cases the row is rendered — never silently dropped. The friend always sees the full 8-row table.

## Correctness criterion (build-time gates)

The generator MUST enforce both gates and exit non-zero if either fails. Catches silent join misses (the R3/R4 class of bug) at build time rather than after distribution.

1. **Row-count gate:** rendered HTML row count == `ENDORSED.md` row count. Any silent drop = exit 1.
2. **Required-field gate:** every rendered row has non-empty `Day`, `Time`, `Club`, `Platform`. Any blank in these columns = exit 1.

Missing URL / missing DB stats do NOT trip these gates — they have their own fallback render rules above.

## Generator
- New script: `scripts/generate_endorsed_html.py`.
- Reads `ENDORSED.md`, joins to `clubs.json` by `clubs_json_key` for `results_url`, joins to DB by `(slug, weekday)` for 4wk averages (see queries above).
- Writes `endorsed.html`.
- Re-run manually; no automation.

## Scope decisions (resolved)

- **Endorsed-only**, no verified-but-not-endorsed section. Matches "endorsed shortlist" framing — the 41-verified list is a different product, not a fold-out of this one.
- **Branding / extra styling:** none beyond dark + readable for v1.

## Open questions

None remaining — see Scope decisions above. Spec is implementable.
