# event-feed: rules for every agent working here

You are reading the events of DC-area organizations into one Google Sheet. Read this
whole file before doing anything. It exists because the first attempt got most of
these wrong.

## Where things are

- `SPEC_SPEED.md`: the approved speed/accuracy plan (Oct 24), executed Oct 24; results at its end.
- `discover.py` + "Discover data calls" workflow: renders browser rows once and saves every JSON/ics/XML
  call the widget makes to `discover/<slug>.json`, replayed without cookies. Scouts read them with
  `briefs/SCOUT_DISCOVER.md`. To try a candidate feed before it goes in the sheet: add it to
  `prove_sources.csv`, run "Feed test" with sources=prove_sources.csv, out=_prove, read `run_log_prove.csv`.
  J for a replayed call is `URL#{json options}` (post, multipart, headers, filter, exclude, token_page);
  see `readers/api.py::parse_feed`.
- Elite list (Oct 24): `elite_methods.csv` = the Elite Sources tab (same columns + O Programs, P Access),
  `ELITE_PLAYBOOK.md`, `elite_feed.csv` = what goes in the Elite Feed tab. Same code: set FEED_LIST=elite
  (`lists.py`), or pick list=elite on any workflow. New groups: add rows with method none + status
  UNTESTED, run "Find calendars" (`find_calendars.py`) and "Discover data calls", scouts use
  `briefs/SCOUT_FIND.md`, prove feeds via `prove_sources.csv`. Loading a feed tab (no secrets, nothing through chat): in the Composio workbench,
  GOOGLEDRIVE_UPLOAD_FROM_URL (account googledrive_suddle-drib) pulls the committed csv from
  raw.githubusercontent.com, proxy_execute downloads it, GOOGLESHEETS_BATCH_UPDATE writes the tab, a
  setDataValidation BOOLEAN makes column A tick boxes, then trash the temp Drive file. (IMPORTDATA needs a
  browser click Eric never saw; do not use it.) First done Oct 25: 673 events.
- `RULES.md`: twelve operating rules. Read it second. `python check.py` enforces the mechanical ones
  and CI runs it on every push; run it before every commit.
- `sources_methods.csv`: snapshot of the Sources tab (B, I, J, K, L, M, N). `PLAYBOOK.md` is
  generated from it by `python sync_playbook.py`; never edit PLAYBOOK by hand. Read a source's
  row before touching the source.
- `feed_test.csv` + `run_log.csv`: the latest "Feed test (no secrets)" run on GitHub (ical/api/xhr/
  recurring only, no Haiku, no browser). Oct 18 03:35Z: 674 events, 34 of 44 sources live.
  Re-run from the Actions tab, or `gh api -X POST repos/emanstof-png/event-feed/actions/workflows/feedtest.yml/dispatches -f ref=main`.
- `debug/<slug>.json`: first 4000 chars of any API response no known shape matched. Add the shape to `readers/api.py`.
- `briefs/`: the three Haiku scout prompts (verify a source, judge a browser render, write blurbs).
  `briefs/README.md` says which to use when. Do not rewrite them in chat; read them from here.
- `render_test.py` + "Browser render test" workflow: renders every browser row with the stealth
  browser and commits the page text to `browser_samples/` (29 min for 34 rows). Scouts read those
  files with `briefs/SCOUT_RENDER.md`. Oct 18: 20 of 34 showed real listings.
- `readers/`: one module per method. `readers/README.md` maps Method to module.
- `fetch.py`: loops Sources, dispatches on Method, writes the Feed tab. `--csv` runs with no Google
  key: reads `sources_methods.csv`, writes `feed_test.csv` + `run_log.csv`. `--dry-run` writes
  `Feed_test` + `Run_log` (one line per source: status, count, seconds, error, 3 samples).
  Run it from the Actions tab ("Weekly fetch" > Run workflow); it needs the two repo secrets
  `GOOGLE_SERVICE_ACCOUNT_JSON` and `ANTHROPIC_API_KEY`.

## The goal, in one sentence

For each organization in the Sources tab, find WHERE THAT ORGANIZATION PUBLISHES ITS
OWN UPCOMING EVENTS, read the events from there, and prove it with real samples.

Not "find similar events." Not "find other groups." That one organization's own calendar,
wherever it keeps it: its site, its booking widget, its Meetup, its Eventbrite organizer
page, its Luma, its ticketing page. Eventbrite counts only when it is that org's page.

## The waterfall: do these in order, stop at the first that yields 3+ dated events

### 0. Read what is already known
Check `PLAYBOOK.md` or the Sources tab (columns I, J, N) for this source first.
If a working URL, feed, or method is recorded, start there. Do not re-discover what
is already written down.

### 1. Official feed (cheapest, most reliable)
Look for: `.ics`, `webcal://`, `?ical=1` (WordPress Events Calendar), `?format=ical` or
`?format=json` (Squarespace), `/events/ical/` (Meetup), `/wp-json/tribe/events/v1/events`
(WordPress), `/api/2/events` (Localist), `/live/json/events/group_id/N` (LiveWhale),
`calendar.google.com/calendar/ical/<id>/public/basic.ics` (any Google Calendar embed:
take the `src=` value from the embed URL), RSS links in the page head.
A feed with only past events is NOT a working feed (Hill Center's iCal is stale).

### 2. The page itself
Fetch it. Are there 3+ upcoming events with dates AND titles? Count events, not date
strings. "47 dates" on a page can be next year's book-club schedule.

### 3. One click away
If the page has no events, follow links whose text or path says: events, calendar,
upcoming, schedule, classes, workshops, what's on, programs, meetups, tickets, register.
Up to 2 levels deep, same site or its booking subdomain (members.*, tickets.*, portal.*).
Nine of our corrected URLs were one click from the original. A person would have clicked.

### 4. The data call behind a widget
If the page is a JavaScript shell or a calendar widget, the data comes from an API call.
Known platforms and whether a public route exists:

| Platform | Public route | Action |
| --- | --- | --- |
| Localist (calendar.gwu.edu, calendar.umd.edu) | `/api/2/events?days=21&pp=100` | call it |
| LiveWhale (events.georgetown.edu) | `/live/json/events/group_id/N` | call it |
| Google Calendar embed | `/calendar/ical/<src>/public/basic.ics` | call it |
| Squarespace | `<collection>?format=json` | call it |
| WordPress Events Calendar | `/wp-json/tribe/events/v1/events` | call it |
| Galaxy Digital (volunteer.*) | none | browser |
| Keep&Share | none | browser |
| Bookmanager (bookstores) | needs session token | browser |
| Mindbody / HealCode | none | browser |
| WellnessLiving | none | browser |
| Wix Events | needs API key | browser |
| Timely, evvnt, inffuse, eventagent | the call the browser makes, replayable | capture then call |

### 5. Headless browser (Scrapling stealth)
Renders JavaScript, defeats most bot blocks (13 of 16 blocked sites read fine). Use for
anything in the "browser" rows above, for srcdoc iframes, and for month-grid calendars
(page forward to cover 3 weeks). Also read iframes by fetching each iframe's own `src`.

### 6. Recurring rule
Some groups never publish dates, only a rule: "every Thursday 8:45pm", "1st and 3rd
Thursdays". Record the rule. The fetch script generates the dates. This is a valid
outcome, not a failure.

### 7. Human browser (last resort)
Only Cloudflare "Just a moment" pages that beat the stealth browser. Record it as
NEEDS HUMAN. Eric's Chrome reads these on Sunday.

## What counts as proof

- 3 or more upcoming events, each with a date and a title, read from the page or feed.
- Today's date is in the sheet header; "upcoming" means on or after today.
- Years matter. A page showing "10.21" with no year is not proof.
- Write 3 sample events into your report. A count without samples is not proof.
- A feed row is proof only when every column is filled: Date, Time (or blank for all-day), Title,
  Venue, Link (http), Source, Category, Description. The first feed went out with 166 empty links
  because this list stopped at "date and title".

## What to record (Sources tab columns)

| Column | Meaning |
| --- | --- |
| B URL | the URL that actually lists events (replace the original if a better one was found) |
| I Method | ical / api / jsonld / rss / html / xhr / browser / stealth / reader / recurring / none |
| J Feed URL | the exact feed or API call, if one exists |
| K Status | LIVE / LIVE but thin / RECURRING / NEEDS BROWSER / NEEDS HUMAN / EMPTY, plus the reason |
| L Events verified | the count, or "recurring" |
| M Notes | what you checked, what you saw, what failed, with dates |

EMPTY is allowed only after steps 1 to 5 and must say what was checked. "No dates found"
is never a complete note.

## What the Oct 17 re-verification found (32 Haiku scouts, every row)

- 61 LIVE (3+ dated events read), 6 LIVE but thin, 7 RECURRING, 11 EMPTY (confirmed), 35 NEEDS
  BROWSER, 6 UNTESTED (feed exists but the scouts' fetcher is blocked from it).
- Proven from GitHub on Oct 18: every Google Calendar .ics works (Game Kastle 75, Pair O' Dice 51,
  Carpe Diem 24, Georgetown IPPS 12, Blueberry 4); LiveWhale JSON works with `data[]`; Localist,
  Tribe, Meetup, Luma, Teamup all work. Still 403 from GitHub: sixthandi.org, whctemple.org,
  events.timely.fun (browser fallback handles these in the weekly job).
- The scouts' WebFetch honors robots.txt and cannot reach calendar.google.com at all. So a
  Google Calendar .ics, a robots-disallowed admin-ajax or ?format=json route, or an API that
  returned a server error is UNTESTED, not broken. Test those from GitHub Actions (`fetch.py`).
- 12 sources recorded as "stealth" read fine with a plain fetch (AEI, Politics & Prose, Lost City,
  JHU, AU, Writer's Center...). Blocks come and go; record the cheapest method that worked and let
  `fetch.py`'s browser fallback handle the bad days.
- Six sheet URLs were still the wrong page (Bhakti, Awarehouse, Loyalty, Folger, Volunteer
  Alexandria, Break My Game). Now fixed. Check column B before anything else.
- Pages that print "Oct 18" with no year are common (Moishe House, Flow Yoga, Sur La Table, Alliance
  Francaise). Haiku infers the year from the weekday; the proof standard still wants a year, so
  these stay "LIVE" only once the fetch run shows correct dates.
- The 35 NEEDS BROWSER rows are mostly five platforms: Galaxy Digital (4 volunteer sites),
  Bookmanager (2 bookstores), Mindbody (3 studios), Art of Living's Salesforce app (3 rows),
  Keep&Share / Square Online / Sawyer / Calendly / Mariana Tek (1 each). One browser reader that
  works on each platform unlocks the group.

## Operating plan until the Google key exists (decided Oct 18, 1:50am)

Manual mode. Eric says "run the feed"; the agent dispatches the GitHub job, pastes the resulting
CSV into the Feed tab (Composio Sheets, as the Sources tab was filled), Eric ticks rows and says
"capture"; the agent copies ticked rows to Itinerary and Google Calendar. The Anthropic key on
GitHub is the one setup step that matters: without it the feed is the 34 structured sources only.
Nothing gets automated for Sunday until one manual run has been looked at by Eric.

The manual run, step by step (first done Oct 18, 2:50am; 673 events with category and blurb):
1. Dispatch: `gh api -X POST repos/emanstof-png/event-feed/actions/workflows/feedtest.yml/dispatches -f ref=main`
   (about 1 minute; writes feed_test.csv, feed_desc.csv, run_log.csv to the repo).
2. Blurbs: split feed_desc.csv into 40-row batches; one Haiku scout per batch with `briefs/BLURB.md`
   (5 to 10 words, writes `n<TAB>blurb` to a file, replies "done N"); cat the outputs into
   feed_blurbs.tsv and commit it. 17 scouts, under a minute.
3. Paste: in the Composio workbench, curl feed_test.csv and feed_blurbs.tsv from
   raw.githubusercontent.com, build the rows, one GOOGLESHEETS_BATCH_UPDATE to Feed!A1 with
   header Pick, Date, Time, Title, Venue, Source, Link, Category, Description. Never paste rows
   through the chat; 673 rows is 140k characters.
4. Tell Eric the count and the date range. He ticks; "capture" moves ticked rows to Itinerary.

## Things that went wrong once and must not again

- Trusting the URL in the sheet as the events page. It was the homepage for 9 sources.
- Counting date strings as events.
- Reporting 54 failures as one number when they were 4 different problems.
- Searching for other groups instead of this group's own calendar.
- Running a long job silently. Say how long it will take before starting it; check back
  instead of blocking.
- Running on all 124 when asked for 20.
- Launching more than 20 subagents at once: the harness caps concurrency at 20 and the rest fail.
  Send 20, wait, send the rest.
- Reporting "built" and "proven" as one number. Say both: what exists, and what has produced
  real events on GitHub. Eric reads "a third proven" as "two thirds broken" unless the
  distinction is explicit.
- Quoting a duration without saying who spends it. "15 minutes" of GitHub rendering costs no
  tokens; say so, or it reads as 15 minutes of Fable.
- A browser render job with no per-source cap: 34 sources ran past 28 minutes. Cap each source.
  (Fixed Oct 24: readers/browser.py is one shared session, 45s cap, no network-idle wait.)
- Speeding the browser by waiting for "the first date on the page": half the widgets had not loaded
  yet (Oct 24, 10 sources lost events). Compare a new render against the old one per source before
  calling a speed-up done. The wait is now "text stopped growing", full HTML, lazy iframes opened.
- A timeout that never fires: ThreadPoolExecutor's `with` waits for the hung thread. fetch.py now
  shuts the executor down without waiting and exits with os._exit.
- Announcing the feed without reading it. 166 of 673 rows had no link; Eric found it, not the
  agent. Why it slipped: the proof standard covered sources (date + title), not feed rows; check.py
  checked the source table, not the output; the ical reader was written against feeds the scouts
  could not open (Google Calendar), so its URL handling was never exercised; and the lead agent
  reported the row count instead of opening rows. Fixes: rule 11, check_feed() in check.py, the
  feed-row proof line above, and the pre-announce check below.

## Working rules

- Haiku for scouts, 4 sources per agent, in parallel. 26 agents finished in 2 minutes.
- Haiku scouts in chat stand in for the API key when testing: a GitHub job renders or fetches and
  commits raw text; scouts read the committed files and extract events. No key, same proof.
- Fable designs and writes; Haiku repeats. Anything done more than four times goes to Haiku.
- Answers to Eric: short, numbers first, built and proven stated separately.
- Before telling Eric an output is ready: run `python check.py` on it, then read 5 rows chosen at
  random as he would (click the link, read the blurb). A count is not a look.
- Never invent an event. Say what you saw.
- Plain fetch from this workspace cannot reach outside sites; GitHub Actions can.
- NO LIVE FETCHING FROM CHAT. Never WebFetch, WebSearch or browse an organization's site, from
  the lead agent or any scout: each new domain stops Eric with a permission prompt (Oct 24, again
  after he had said no). All fetching runs on GitHub (feedtest.yml, rawfetch.yml, render.yml),
  which commits the text; agents read the committed files only. Missing file = dispatch the job.
- The sheet is the source of truth. `sources_methods.csv` is its snapshot; `sources.csv` is the
  older probe snapshot (names and URLs only).
- Before committing: `python check.py` must print OK. After changing a method anywhere, change
  J, K, N, the CSV and run `python sync_playbook.py` in the same commit (RULES.md 1 to 3).
- Commit messages end with the Claude attribution lines the session provides.
