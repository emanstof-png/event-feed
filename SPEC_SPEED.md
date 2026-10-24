# Spec: faster, more accurate scraping (Oct 24, approved by Eric)

Goal: full scrape from ~30 min to 15 min or less on GitHub, with exact dates for as many sources as
possible. No API keys, no Sunday automation, no capture step, no Suggested scoring in this work.

Baseline (logs in repo): browser_render_log.csv 34 renders, 1699s total; 10 sources took 1375s
(Mindfulness Center 272, Repair the World 159, Soul Fire 147, Art of Living x3 140 each, Yoga District
127, Victory Comics 127, Art House 7 88, Carnegie 34). raw_fetch_log.csv: 45 plain fetches in 40s,
10 returned 403 (AU x2, JHU, AEI, Politics and Prose, Stimson, Lost City, Loyalty, Japan ICC, Reva 406).

## Phase 1: replay the data call behind each widget (do first)
1. `discover.py` + `.github/workflows/discover.yml` (no secrets). For every browser/stealth row:
   render once with Playwright/Scrapling, listen to every network response, keep JSON / ics / XML
   responses over 500 bytes whose body contains date-like strings. Save to `discover/<slug>.json`:
   request URL, method, headers needed, status, first 4000 chars of body. Per-source cap 60s.
   Commit `discover/` and `discover_log.csv` (row, name, candidates, seconds, error).
2. Haiku scouts (4 sources each, max 20 at once) read `discover/<slug>.json` and report the candidate
   URL with 3+ upcoming dated titled events, plus 3 samples, or NONE with a reason.
3. Lead agent: for each confirmed feed, add a shape to `readers/api.py`, set method xhr and J = the
   URL in the sheet AND sources_methods.csv, update K/N, run `python sync_playbook.py`, `python check.py`.
   Prove each one with a Feed test run on GitHub (`fetch.py --csv --methods xhr`).
   Feeds needing a session token that expires (Bookmanager) stay browser.

## Phase 2: safety net
- readers/browser.py: one shared browser session for the whole run; drop network_idle, wait for
  content or 5s; solve_cloudflare only when the page is a challenge; 45s hard cap per source.
  Same cap in render_test.py.
- readers/common.get(): use a browser-impersonating client (curl_cffi, shipped with Scrapling) so
  the 10 sites that 403 plain requests stop falling back to the browser. Prove with raw_fetch.yml.
- fetch.py: zero-count alarm. A source with events last run and 0 this run is flagged in run_log.

## Done when
- A full GitHub run finishes in 15 min or less.
- No source loses events vs the last run except ones flagged.
- check.py OK; sheet, sources_methods.csv and PLAYBOOK.md agree.
- Eric gets one line: N moved to feeds, N still browser, new run time.

## Risks
Hidden feeds change silently (zero-count alarm); token feeds stay browser; fewer feeds than hoped
(cap still gives ~50%); a few sites may object to replayed or impersonated requests (weekly volume, low).
