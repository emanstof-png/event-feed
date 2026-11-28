You are rechecking DC-area groups whose calendar gave NO events for a weekend. Decide WHY, from saved files only.
Never WebFetch, WebSearch or browse (RULES 12). Never invent a URL, date or event.

For each group in your task line you get: list, row, name, method, and the saved files for it:
- raw_samples/<slug>.txt or browser_samples/<slug>.txt: page text GitHub saved (line 1 name, line 2 URL, line 3 fetch status)
- find/<slug>.json: links and probes the "Find calendars" job saved (calendar-looking links, feeds, search hits)
- discover/<slug>.json: JSON/ics/XML data calls the page made, replayed
Also read the group's row in sources_methods.csv (list main) or elite_methods.csv (list elite): columns url, method, feed_url, status, notes.

VERDICTS (pick one):
- OK-EMPTY: the file is the group's real calendar, it loaded, it shows upcoming dated events, and none fall in the window. Give the next event date and title as evidence.
- WRONG-PAGE: the page is a homepage, about page, past-events page, single event, or a listing of other things. Give the better URL ONLY if it appears in the files (a link in page text, find json, or discover json).
- PARTIAL: the calendar loaded but shows only part (first N cards, one month, "load more", a teaser box). Say what is cut off and any URL/param in the files that shows more (?page=2, list view, ?ical=1, an API call in discover).
- NOT-LOADED: page is a JS shell, "loading", cookie wall, empty, or render timed out. Say if discover/find shows a data call or feed that would work.
- BLOCKED: 403, 404, 5xx, Cloudflare, login wall. Quote the status line.
- FEED-DEAD: an ical/api/xhr feed returned 0 or an error. Say what the files show (stale feed, moved, server error) and any alternative.

MISSED EVENTS: if while reading you see an event dated 2026-11-28 or 2026-11-29 in any file for this group, list it.

OUTPUT: write a TSV to the path in your task line, header first:
list<TAB>row<TAB>name<TAB>verdict<TAB>evidence<TAB>fix_url<TAB>fix_method<TAB>missed_events
- evidence: one line, what you saw (quote briefly).
- fix_url: a URL copied exactly from the files, or blank.
- fix_method: html / browser / stealth / ical / api / xhr (with the call) / none, or blank if unchanged.
- missed_events: "YYYY-MM-DD HH:MM Title" separated by " ; ", or blank.
Then reply exactly: done <rows>
