# Endorsed Bridge Clubs — Lee's Shortlist

Three mutually exclusive lists:

- **Endorsed** — games Lee has actually played online and rated worth returning to. Real `Played` date (verified against EBU results).
- **To be played** — meets the criteria and worth trying, but Lee hasn't played it yet (or hasn't played it to a standard worth confirming). Rendered as a separate section on the public page.
- **Discarded** — fails the criteria; lives in `clubs.json` as `status: discarded`. Not in this file.

To add: tell Claude "endorse <club>" (you've played it) or "to-try <club>" (candidate). To move between lists, say so.

`clubs_json_key` is the exact `name` value from `clubs.json` — load-bearing join key for the HTML generator. Do not edit by hand without checking the corresponding `clubs.json` entry.

`pairs_override` / `ngs_override` are optional. If both are set, the row skips the clubs.json + DB lookup and uses the literal values verbatim (e.g. for BBO games not scraped by the pipeline). The `clubs_json_key` column may be blank in that case.

## Endorsed (played & rated)

| Day | Time | Club | Platform | clubs_json_key | pairs_override | ngs_override | Played | Note |
|-----|------|------|----------|----------------|----------------|--------------|--------|------|
| Mon | 14:00 | Ascot | RealBridge | Ascot Bridge Club (Mon PM) |   |   | 2026-05-18 | Played 2026-05-18, 55.52%. |
| Mon | 19:00 | Hellesdon & Taverham | RealBridge | Hellesdon & Taverham Bridge Club (Mon Evening) |   |   | 2026-05-25 | Played 2026-05-25, 59.03%. |
| Tue | 19:00 | Chelmsford | RealBridge | Chelmsford Bridge Club (Tue Evening) |   |   | 2026-06-02 | Played 2026-06-02, 55.76%. |
| Thu | 14:10 | ACBL BBO Pairs | BBO |   | 25+ | N/A |   | Endorsed by Lee. |
| Thu | 19:00 | Noverre | RealBridge | Noverre Bridge Club (Thu Evening) |   |   | 2026-03-26 | Played 2026-03-26, 66.00%. |
| Fri | 15:00 | Exeter | RealBridge | Exeter Bridge Club (Fri PM) |   |   | 2026-02-27 | Played 2026-02-27, 56.63%. |
| Fri | 19:30 | Milton Keynes | RealBridge | Milton Keynes Bridge Club (Fri Evening) |   |   | 2026-05-22 | Played 2026-05-22, 49.63%. |
| Sun | 19:00 | Cumbria Super Sunday | RealBridge | Cumbria Super Sunday |   | 55.4 | 2026-03-29 | Played 2026-03-29, 58.86%. Field NGS 55.4 (SOpp from EBU). Hosted by Cumbria County BA. |

## To be played (candidates — not yet played)

| Day | Time | Club | Platform | clubs_json_key | pairs_override | ngs_override | Played | Note |
|-----|------|------|----------|----------------|----------------|--------------|--------|------|
| Mon | 19:00 | Chelmsford | RealBridge | Chelmsford Bridge Club (Mon Eve) |   |   |   | Not yet played (Lee plays the Tue Chelmsford). |
| Mon | 19:00 | Leighton Buzzard | RealBridge | Leighton Buzzard Bridge Club (Mon Evening) |   |   |   | Not yet played. |
| Tue | 19:30 | Ascot | RealBridge | Ascot Bridge Club (Tue Evening) |   |   |   | Not yet played (Lee plays the Mon Ascot). Strongest Tue field — NGS 57.9%. |
| Tue | 19:30 | Harpenden | RealBridge | Harpenden Bridge Club (Tue Evening) |   |   |   | Not yet played. |
| Wed | 13:55 | Oakingham | RealBridge | Oakingham Bridge Club (Wed PM) |   |   | 2025-11-12 | On trial. Played once (59.92%) but NGS ~49 that day. Fills the Wed gap. |
| Wed | 19:30 | Milton Keynes | RealBridge | Milton Keynes Bridge Club (Wed Evening) |   |   |   | Not yet played (Lee plays the Fri MK). |
| Thu | 19:15 | Allendale & Retford | RealBridge | Allendale & Retford Bridge Club (Thu Evening) |   |   |   | Not yet played. |
| Fri | 13:30 | Chelmsford | RealBridge | Chelmsford Bridge Club (Fri PM) |   |   |   | Not yet played (Lee plays the Tue Chelmsford). |
