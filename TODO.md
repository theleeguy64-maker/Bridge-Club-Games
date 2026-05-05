# Bridge Club Games — TODO

## Bugs / Fixes / Easy wins

- [ ] **Sweep weekday PM clubs to verify actual session times.** All 80 clubs tagged `(Mon PM)` / `(Wed PM)` / `(Thu PM)` / `(Fri PM)` at 14:00 carry the placeholder note `"EBU PM listing; time placeholder"`. The Tue sweep on 2026-05-04 found ~80% were actually evening RealBridge games, not afternoon. Same mislabelling almost certainly affects the other weekdays. Fetch each club's bridgewebs page, confirm/correct the time, and either update or remove (some clubs don't run that day at all). Counts: Mon 24, Wed 16, Thu 20, Fri 14.

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
