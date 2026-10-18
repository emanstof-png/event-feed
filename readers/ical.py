"""Method: ical. Any .ics / webcal feed (WordPress ?ical=1, Meetup /events/ical/, Google Calendar
public/basic.ics, Teamup, Squarespace ?format=ical). Expands recurring rules."""
from .common import get, event, in_window, dedupe
import icalendar, recurring_ical_events
from datetime import datetime, date

WINDOWS_TZ = {"Eastern Time (US & Canada)": "America/New_York", "Central Time (US & Canada)": "America/Chicago",
              "Mountain Time (US & Canada)": "America/Denver", "Pacific Time (US & Canada)": "America/Los_Angeles",
              "Eastern Standard Time": "America/New_York"}

def read(source, window_days=21):
    url = source.get("feed_url") or source["url"]
    if url.startswith("webcal:"):
        url = "https:" + url.split(":", 1)[1]
    raw = get(url).content
    for win, iana in WINDOWS_TZ.items():
        raw = raw.replace(win.encode(), iana.encode())
    cal = icalendar.Calendar.from_ical(raw)
    lo = date.today(); hi = lo.replace(day=lo.day)  # placeholder, replaced below
    from .common import window
    lo, hi = window(window_days)
    out = []
    for ev in recurring_ical_events.of(cal).between(lo, hi):
        start = ev.get("DTSTART").dt
        d = start.date() if isinstance(start, datetime) else start
        t = start.strftime("%H:%M") if isinstance(start, datetime) else ""
        out.append(event(d.isoformat(), str(ev.get("SUMMARY", "")), source["name"], t,
                         str(ev.get("LOCATION", "") or ""), str(ev.get("URL", "") or "")))
    return dedupe([e for e in out if in_window(e, window_days)])
