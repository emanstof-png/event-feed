# event-feed: rules for every agent working here

You are reading the events of DC-area organizations into one Google Sheet. Read this
whole file before doing anything. It exists because the first attempt got most of
these wrong.

## Where things are

- `PLAYBOOK.md`: one row per source, the final method, feed URL or rule, and why. Mirrored in the
  Sources tab columns I (Method), J (Feed URL / rule), N (How to read). Read the row before touching a source.
- `readers/`: one module per method. `readers/README.md` maps Method to module.
- `fetch.py` (next): loops Sources, dispatches on Method, writes the Feed tab.

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

## Things that went wrong once and must not again

- Trusting the URL in the sheet as the events page. It was the homepage for 9 sources.
- Counting date strings as events.
- Reporting 54 failures as one number when they were 4 different problems.
- Searching for other groups instead of this group's own calendar.
- Running a long job silently. Say how long it will take before starting it; check back
  instead of blocking.
- Running on all 124 when asked for 20.

## Working rules

- Haiku for scouts, 4 sources per agent, in parallel. 26 agents finished in 2 minutes.
- Never invent an event. Say what you saw.
- Plain fetch from this workspace cannot reach outside sites; GitHub Actions can. The
  scouts' WebFetch can.
- The sheet is the source of truth. `sources.csv` is a snapshot for the probe.
- Commit messages end with the Claude attribution lines the session provides.
