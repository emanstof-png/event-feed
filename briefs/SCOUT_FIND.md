You are a scout choosing where 4 DC-area organizations publish their OWN upcoming events.
Today is in the batch line. First read CLAUDE.md in this repo (the waterfall, the proof standard).

NO LIVE FETCHING. Do not use WebFetch, WebSearch or a browser (RULES 12). Read only these files,
which GitHub fetched for you:
- find/<slug>.json      seed URL, search hits, every page fetched (status, title, date_strings,
                        jsonld events + samples, feed hints, iframes, event links, platform), probes
                        (tribe API, ?ical=1)
- find/<slug>.txt       text of the best page found
- discover/<slug>.json  data calls the page made when rendered in a browser (may be missing)
If a needed file is missing, say MISSING in NOTE and still pick the best candidate.

For EACH organization pick, in this order of preference (cheapest that works, CLAUDE.md waterfall):
1. ical: a .ics / webcal / ?ical=1 / Google Calendar embed (src= value -> 
   https://calendar.google.com/calendar/ical/<src>/public/basic.ics). A probe with events > 0 counts.
2. api: /wp-json/tribe/events/v1/events (probe events > 0), Localist /api/2/events, LiveWhale /live/json.
3. xhr: a discover/ candidate that is this org's event list with replay_ok true.
4. rss: a feed hint that is an events feed (not a blog).
5. jsonld: a page with 3+ JSON-LD events -> method jsonld, URL = that page.
6. html: a page whose text (find/<slug>.txt) lists 3+ upcoming events with dates -> URL = that page.
7. browser: an events page exists but is a JavaScript shell, 403, or widget -> URL = that page.
8. none: no public calendar (members-only, venue-hire page, directory). Say why in NOTE.
Also note an Eventbrite / Meetup / Luma organizer link if one is present: report it in ALT.

Rules: the org's OWN calendar, never another group's. Count events, not date strings. A page of
past exhibitions or an archive is not a calendar. Never invent an event or a URL: every URL you
report must appear in the files.

Output EXACTLY one block per organization, nothing else:

ROW <n> | <name>
METHOD: <ical|api|xhr|rss|jsonld|html|browser|none>
URL: <the page that lists events (column B)>
FEED: <feed / API URL for ical, api, xhr, rss; browser: widget URL if different from URL; else blank>
ALT: <Eventbrite/Meetup/Luma organizer URL or blank>
COUNT: <upcoming events you can see, or ?>
SAMPLES: <date title> ; <date title> ; <date title>   (blank if none visible)
NOTE: <one line: which file, what you saw, why this method; for none, why>
