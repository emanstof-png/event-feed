You are a scout verifying how 4 DC-area organizations publish their events. Today is the date in the sheet header.
First read CLAUDE.md in this repo (the waterfall and proof standard). Then read your batch file.

For EACH of the 4 rows, re-test what is recorded, in this order, stopping when you have proof:
1. If a Feed/rule is a URL, WebFetch it. Count UPCOMING events (date on/after TODAY, within ~5 weeks) that have a title.
2. If Method is recurring, WebFetch the URL and confirm the rule text (day/time) still appears on the page.
3. If no feed, WebFetch the URL. Count upcoming dated events with titles.
4. If fewer than 3: try the waterfall steps 1, 3 and 4 from CLAUDE.md for THIS org only (its own feed guesses, one click away, its platform's public API). Never search for other groups, never go to Eventbrite/Meetup/Facebook unless the org's own page links there.
5. If a URL is a Google Calendar embed, report the src= calendar id and the /calendar/ical/<id>/public/basic.ics URL, and test it.

Rules: count events, not date strings. Years matter. Never invent an event. If WebFetch is blocked (403, Cloudflare, "Just a moment", empty JS shell), say so exactly; that is a real finding.

Output EXACTLY one block per row, nothing else:

ROW <n> | <name>
RESULT: VERIFIED | CORRECTION | NEEDS BROWSER | EMPTY | BLOCKED
METHOD: <ical|api|xhr|rss|html|jsonld|browser|stealth|recurring|none>  (what the sheet SHOULD say)
FEED: <exact feed/API URL or rule, or blank>
COUNT: <n upcoming>
SAMPLES: <date title> ; <date title> ; <date title>
NOTE: <one line: what you fetched, what you saw, why this method>
