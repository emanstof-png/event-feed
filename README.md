# event-feed

Weekly pipeline that turns ~125 public DC-area calendars into one chronological
feed in the **Event Calendars** Google Sheet, plus a short curated **Suggested**
list. You tick events there and accept them into Google Calendar.

## What's here so far

| File | What it does |
| --- | --- |
| `sources.csv` | Snapshot of the sheet's Sources tab, used by the Probe. The sheet stays the source of truth. |
| `probe.py` | Visits every source once and records how it can be read: `ical`, `api`, `jsonld`, `rss`, `html`, `xhr`, `browser`, `reader`, or `none`. |
| `.github/workflows/probe.yml` | Runs the Probe on GitHub whenever `probe.py` or `sources.csv` changes, then commits the results. |
| `probe_report.csv` / `.json` | Probe results, one row per source. |
| `probe_samples/` | The page text each decision was based on, used to build scrapers. |
| `CLAUDE.md` | Rules every agent follows here: the per-source waterfall, proof standard, columns. |
| `PLAYBOOK.md` | One row per source: final method, feed URL or rule, and how we know. Mirrored in the sheet. |
| `readers/` | One module per method (ical, api, rss, html, browser, recurring, haiku). |

## Coming next

- `fetch.py`: weekly run that reads each source by its Method, keeps the next three weeks, de-dupes, and writes the Feed tab.
- Suggested scoring with Claude Haiku against the screening rules in the architecture doc.
- `weekly.yml`: the Sunday-morning schedule.
- Apps Script for the sheet: the Accept menu that adds ticked events to Google Calendar and the Itinerary tab.

Secrets (Google access, Anthropic API key) live in GitHub Actions secrets, never in this repo.
