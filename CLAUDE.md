# Bridge Club Games

**You are working in the Bridge Club Games project.** Always be aware of this context — the user should not need to tell you which project this is.

## Project Overview

Terminal app that finds UK online bridge games for a given date. Reads a curated `clubs.json` of UK clubs running RealBridge or BBO sessions, fetches recent results live from bridgewebs.com, renders a Rich table to the terminal, and saves a markdown report.

Launched from `~/Desktop/Bridge Games.command` (zsh) or directly via `python3 scripts/bridge_finder.py`.

Separate from the **Bridge Tournaments** project (`~/Casual_claude/Bridge_Tournaments/`), which tracks face-to-face tournaments and festivals.

## Optimization

**Project Weight:** Light
**Message Threshold:** 25 messages
**Default Model:** Haiku

**Feature Defaults:**
- Web Search: OFF (use Firecrawl for specific URLs)
- Advanced Thinking: OFF (enable only for tricky parser bugs)
- MCP Servers: Firecrawl ON (used for bridgewebs scraping during dev), Firebase OFF, Context7 OFF

## Key Files

| File | Purpose |
|------|---------|
| `scripts/bridge_finder.py` | The whole script — date prompt, fetch, render, write |
| `scripts/launcher_template.sh` | Backup of the Desktop `.command` launcher |
| `clubs.json` | Canonical list of ~103 UK weekday + weekend bridge clubs |
| `reports/` | Generated markdown reports per date (gitignored) |
| `docs/superpowers/specs/2026-04-30-bridge-finder-design.md` | The design spec |
| `docs/superpowers/plans/2026-04-30-bridge-finder.md` | The implementation plan (7 tasks) |

## Architecture summary

- **Cached club list, live result lookup.** Clubs are hand-curated in `clubs.json`; only weekly results are fetched.
- **Two parsers:** `bridgewebs` (live HTTP fetch) and `static` (baseline values from clubs.json — used for EBU Daily BBO and Dragon Pairs).
- **4-week rolling median** for pair count; **drift canary** (>50% deviation) flags suspect data.
- **bridgewebs serves ISO-8859-1** — decode `response.content` explicitly.
- **HTTP timeout 10s, custom User-Agent, no retries.**
- **Time filter:** PM/eve only (≥12:00).

## Running

```bash
source .venv/bin/activate
echo "next sat" | python3 scripts/bridge_finder.py
```

Or double-click `~/Desktop/Bridge Games.command`.

## Conventions

- Keep `clubs.json` under hand-edit control. The implementation plan documents how to add or refresh entries.
- `last_verified` field on each club — script warns if older than 180 days.
- All file I/O uses UTF-8.
- Commit messages match the existing project style — short summary line, blank line, body, `Co-Authored-By` footer.
- Push to GitHub: `theleeguy64-maker/Bridge-Club-Games` (private).
