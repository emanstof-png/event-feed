"""Method: api / xhr. A JSON endpoint that returns events. Known shapes handled directly;
anything else is flattened and handed to Haiku."""
import json, re
from datetime import datetime, timedelta
from .common import get, event, in_window, dedupe, window
from .haiku import extract_events_from_text

def _tribe(data, name):   # WordPress Events Calendar /wp-json/tribe/events/v1/events
    return [event(e["start_date"][:10], e["title"], name, e["start_date"][11:16],
                  (e.get("venue") or {}).get("venue", "") if isinstance(e.get("venue"), dict) else "",
                  e.get("url", "")) for e in data.get("events", [])]

def _localist(data, name):  # /api/2/events
    out = []
    for w in data.get("events", []):
        e = w.get("event", w)
        for inst in e.get("event_instances", [{}]):
            i = inst.get("event_instance", inst)
            s = i.get("start", "")
            out.append(event(s[:10], e.get("title", ""), name, s[11:16], e.get("location_name", ""), e.get("localist_url", "")))
    return out

def _connectjew(data, name):
    return [event((e.get("start_time") or e.get("date") or "")[:10], e.get("title") or e.get("name", ""), name,
                  (e.get("start_time") or "")[11:16], e.get("location", "") or "", e.get("url", "") or "")
            for e in data.get("events", [])]

def _dcpolicy(data, name):
    return [event((e.get("date") or e.get("start") or "")[:10], e.get("title", ""), e.get("org") or name,
                  e.get("time", "") or "", e.get("location", "") or "", e.get("url", "") or "")
            for e in data.get("events", [])]

SHAPES = [("tribe/events", _tribe), ("/api/2/events", _localist), ("connectjew.org", _connectjew), ("dcpolicyevents", _dcpolicy)]

def read(source, window_days=21):
    url = source.get("feed_url") or source["url"]
    lo, hi = window(window_days)
    url = url.replace("{start}", lo.isoformat()).replace("{end}", hi.isoformat())
    data = get(url).json()
    for key, fn in SHAPES:
        if key in url:
            try:
                evs = fn(data, source["name"])
                if evs:
                    return dedupe([e for e in evs if in_window(e, window_days)])
            except Exception:
                pass
    text = json.dumps(data)[:60000]
    return dedupe([e for e in extract_events_from_text(text, source["name"]) if in_window(e, window_days)])
