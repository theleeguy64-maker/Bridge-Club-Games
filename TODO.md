# Bridge Club Games — TODO

## Bugs / Fixes / Easy wins

- [ ] **Finish the placeholder-time sweep — findings verified 2026-07-21, NOT yet written to `clubs.json`.** Only 7 active clubs ever carried an unpinned time (the item below badly overstates it). All 7 were verified live; the edits were interrupted before being applied. Apply these:
  - **Faringdon (Mon)** — 19:00 → **19:15**. Homepage: "Duplicate play every Monday at 7.15pm on RealBridge". Live sessions replaced by online. Confirms RealBridge. 24–29 pairs.
  - **Farnham (Mon)** — 19:00 → **19:30**. Calendar: "RealBridge Club Session / RealBridge Online" Mon 19:30. Also runs a **Wed 19:30** RealBridge session — not in `clubs.json`, consider adding. 22–27 pairs.
  - **Truro (Wed)** — 19:00 → **18:30**. Homepage: "Wednesday Evenings at 6.30pm", online-only RealBridge, £1.50/session. ⚠️ Truro's page also lists *other* clubs' games ("Devon online RealBridge - Wed 7:15") in a links panel — do NOT read those as Truro's. Pairs 8–15, so likely fails the ≥14 bar; check before keeping.
  - **Hadley Wood (Fri)** — 19:00 → **19:30**, but **venue is "Live at HWA Centre" = face-to-face**. Their *Tue* 19:30 session is the RealBridge one (already correctly listed separately). Recommend **discard** the Fri entry: F2F, and 8–15 pairs.
  - **Fulbourn (Fri)** — 19:00 → **19:15** ("Friday Online Pairs" 7.15). Their Tue/Thu sessions are explicitly "Face to Face". Pairs 6–13 → fails ≥14; recommend **discard** on pairs.
  - **Stretford (Fri)** — **no Friday session exists.** Calendar shows Sun 13:00 + Tue 13:15 "The Club" (F2F), Fri 13:15 Supervised Play (F2F). The RealBridge session is hosted by *Adam Wiseberg Bridge*, not Stretford. Recommend **discard**.
  - **Leighton Buzzard (Mon)** — **unresolved.** Best games of the seven (25–32 pairs, NGS 55–56%), confirmed RealBridge from event titles, but no start time published anywhere on bridgewebs (shared Mon–Fri virtual club with MK and Regis). Leave 19:00 flagged as placeholder, or ask the club.
  - Method note: session start times come from the **`display_past` / calendar table** (day, date, event, venue, time). Do **not** scrape times off result pages — those are results-*publication* timestamps (~22:00) and are meaningless as start times. Scratchpad scripts used: `sweep_times.py`, `sweep_calendar.py`.

- [ ] **Sweep weekday PM clubs to verify actual session times.** *(Largely superseded — see above. Counts below are stale: of 92 entries, 56 are already discarded and only 1 active club sits at the 14:00 placeholder, Ascot, already marked verified.)* All 80 clubs tagged `(Mon PM)` / `(Wed PM)` / `(Thu PM)` / `(Fri PM)` at 14:00 carry the placeholder note `"EBU PM listing; time placeholder"`. The Tue sweep on 2026-05-04 found ~80% were actually evening RealBridge games, not afternoon. Same mislabelling almost certainly affects the other weekdays. Fetch each club's bridgewebs page, confirm/correct the time, and either update or remove (some clubs don't run that day at all). Counts: Mon 24, Wed 16, Thu 20, Fri 14.

## Enhancements (deferred from spec)

- [ ] Live-update table during fetch (vs scrolling progress lines)
- [ ] Same-day result caching
- [ ] EBU Daily NGS pulled live from EBU site (currently `None` for static rows)
- [ ] Concurrency lock against double-click
- [ ] SIGINT (Ctrl-C) graceful handling
- [ ] Atomic writes for reports
- [ ] NGS spread/sigma alongside mean
- [ ] Versioned reports for repeated same-day runs
- [ ] Dependency bootstrap on first run
- [ ] Worldwide clubs (Saturday is genuinely thin worldwide)
- [ ] Sat+Sun combined report
- [ ] Auto-add new clubs by re-scanning EBU PDF
