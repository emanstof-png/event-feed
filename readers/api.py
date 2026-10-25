"""Method: api / xhr. A JSON endpoint that returns events. Known shapes handled directly;
anything else is flattened and handed to Haiku."""
import json, re
from datetime import datetime, timedelta
from .common import get, request, event, in_window, dedupe, window
from .haiku import extract_events_from_text

def _tribe(data, name):   # WordPress Events Calendar /wp-json/tribe/events/v1/events
    return [event(e["start_date"][:10], e["title"], name, e["start_date"][11:16],
                  (e.get("venue") or {}).get("venue", "") if isinstance(e.get("venue"), dict) else "",
                  e.get("url", ""), desc=e.get("excerpt") or e.get("description", "")) for e in data.get("events", [])]

def _localist(data, name):  # /api/2/events
    out = []
    for w in data.get("events", []):
        e = w.get("event", w)
        for inst in e.get("event_instances", [{}]):
            i = inst.get("event_instance", inst)
            s = i.get("start", "")
            out.append(event(s[:10], e.get("title", ""), name, s[11:16], e.get("location_name", ""), e.get("localist_url", ""), desc=e.get("description_text", "")))
    return out

def _connectjew(data, name):
    return [event((e.get("start_time") or e.get("date") or "")[:10], e.get("title") or e.get("name", ""), name,
                  (e.get("start_time") or "")[11:16], e.get("location", "") or "", e.get("url", "") or "")
            for e in data.get("events", [])]

def _dcpolicy(data, name):
    return [event((e.get("date") or e.get("start") or "")[:10], e.get("title", ""), e.get("org") or name,
                  e.get("time", "") or "", e.get("location", "") or "", e.get("url", "") or "")
            for e in data.get("events", [])]

def _livewhale(data, name):  # events.georgetown.edu/live/json/events/...
    items = data if isinstance(data, list) else data.get("data") or data.get("events") or data.get("items") or []
    out = []
    for e in items:
        s = e.get("date_iso") or e.get("date_utc") or e.get("date", "")
        d = s[:10] if s and s[4:5] == "-" else ""
        if not d:
            try:
                d = datetime.strptime(s[:30], "%A, %B %d, %Y").date().isoformat()
            except Exception:
                pass
        import html as _h
        out.append(event(d, _h.unescape(e.get("title", "")), name, s[11:16] if s[4:5] == "-" else "",
                         e.get("location", "") or "", e.get("url", "") or "", desc=e.get("summary") or e.get("description", "")))
    return [e for e in out if e["date"]]

def _keepandshare(data, name):   # keepandshare.com calendar18 fns_asynch_api.php action=getrange
    evs = (data.get("data") or {}).get("repeatidToEvent") or {}
    return [event(e.get("startdate", ""), e.get("request", ""), name, e.get("starttime", ""), "", "", desc=e.get("notecontent", ""))
            for e in evs.values() if e.get("deleteflag") in ("0", 0, None)]

def _handsonconnect(data, name):  # Galaxy/HandsOn volunteer portals: /search/getOpportunitiesCalendar
    out = []
    for day in data.get("items", []):
        for o in day.get("occurrences", []):
            s = o.get("startDateTimeISO") or day.get("dayDate", "")
            out.append(event(s[:10], o.get("opportunityName", ""), name, s[11:16], o.get("locationCity", "") or "",
                             o.get("opportunityLink", ""), desc=o.get("description", "")))
    return out

def _eaton(data, name):  # eatonworkshop.com/api/events/list/{year}/{month}
    out = []
    for day in data.get("items", []):
        for e in day.get("items", []):
            v = re.sub(r"^\[\w+\]-", "", e.get("venue", "") or "").replace("-", " ").title()
            loc = " ".join(e.get("locations") or [])   # "washington-dc" or "hong-kong": J filters on it
            out.append(event(day.get("date", "")[:10], e.get("name", ""), name, "", f"{v}, {loc.replace('-', ' ').title()}".strip(", "),
                             "https://www.eatonworkshop.com" + (e.get("pageUrl") or ""), desc=e.get("time", "")))
    return out

def _libnet(data, name):  # Communico/LibNet: /eeventcaldata?req={...}
    return [event((e.get("raw_start_time") or "")[:10], e.get("title", ""), name, (e.get("raw_start_time") or "")[11:16],
                  e.get("location", "") or "", e.get("url", "") or "", desc=e.get("long_description") or e.get("description", ""))
            for e in (data if isinstance(data, list) else [])]

def _bookmanager(data, name):  # api.bookmanager.com/customer/event/v2/list (multipart)
    out = []
    for e in data.get("rows", []):
        d = str(e.get("date", ""))
        out.append(event(f"{d[:4]}-{d[4:6]}-{d[6:8]}" if len(d) == 8 else "", e.get("title", ""), name,
                         "" if e.get("all_day") else (e.get("start_time") or "")[:5], e.get("location_text", "") or "", "",
                         desc=e.get("description", "")))
    return out

def _stec(data, name):  # Stachethemes Event Calendar: wp-admin/admin-ajax.php action=stec_public_ajax_action
    return [event((e.get("start_date") or "")[:10], e.get("title", ""), name, (e.get("start_date") or "")[11:16],
                  ((e.get("location") or {}).get("title", "") if isinstance(e.get("location"), dict) else ""),
                  e.get("permalink", "") or "", desc=e.get("description_short") or e.get("description", ""))
            for e in (data if isinstance(data, list) else [])]

SHAPES = [("keepandshare.com", _keepandshare), ("getOpportunitiesCalendar", _handsonconnect),
          ("eatonworkshop.com/api/events", _eaton), ("libnet.info/eeventcaldata", _libnet),
          ("bookmanager.com/customer/event", _bookmanager), ("stec_public_ajax_action", _stec),
          ("tribe/events", _tribe), ("/api/2/events", _localist), ("connectjew.org", _connectjew),
          ("dcpolicyevents", _dcpolicy), ("/live/json/", _livewhale)]

def _fill(x, lo, hi, month=None):
    if not isinstance(x, str):
        return x
    x = (x.replace("{start}", lo.isoformat()).replace("{end}", hi.isoformat())
          .replace("{start8}", lo.strftime("%Y%m%d")).replace("{end8}", hi.strftime("%Y%m%d"))
          .replace("{days}", str((hi - lo).days)))
    if month:
        x = x.replace("{year}", str(month[0])).replace("{month}", str(month[1]))
    return x

def parse_feed(feed):
    """J may carry request options after '#' as JSON (SPEC_SPEED Phase 1, replayed widget calls):
    https://host/path#{"post": "a=1&from={start}", "headers": {...}, "filter": "regex"}
    keys: post (form string), multipart (dict), headers (dict), filter (regex kept on title+venue).
    Placeholders: {start} {end} (ISO), {start8} {end8} (YYYYMMDD), {days}, {year} {month}
    (a {month} URL is fetched once per month the window touches)."""
    if "#{" in feed:
        url, opts = feed.split("#", 1)
        return url, json.loads(opts)
    return feed, {}

def read(source, window_days=21):
    url, opts = parse_feed(source.get("feed_url") or source["url"])
    lo, hi = window(window_days)
    months = [(lo.year, lo.month)]
    if "{month}" in url and (hi.year, hi.month) != months[0]:
        months.append((hi.year, hi.month))
    datas = []
    for m in months:
        u = _fill(url, lo, hi, m)
        if opts.get("post") is not None or opts.get("multipart") is not None:
            mp = {k: _fill(v, lo, hi, m) for k, v in opts["multipart"].items()} if opts.get("multipart") else None
            r = request(u, "POST", data=_fill(opts.get("post"), lo, hi, m), multipart=mp, headers=opts.get("headers"))
        else:
            r = get(u, headers=opts.get("headers") or {})
        datas.append(r.json())
    keep = re.compile(opts["filter"], re.I) if opts.get("filter") else None
    for key, fn in SHAPES:
        if key in url or key in str(opts.get("post", "")):
            try:
                evs = [e for d in datas for e in fn(d, source["name"])]
                if keep:
                    evs = [e for e in evs if keep.search(e["title"] + " " + e["venue"])]
                if evs:
                    return dedupe([e for e in evs if in_window(e, window_days)])
            except Exception:
                pass
    data = datas[0]
    text = json.dumps(data)[:60000]
    _debug_dump(source["name"], text)
    return dedupe([e for e in extract_events_from_text(text, source["name"]) if in_window(e, window_days)])


def _debug_dump(name, text):
    """No known shape matched: keep the first 4000 chars so the shape can be added."""
    try:
        import os, re
        os.makedirs("debug", exist_ok=True)
        slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:60]
        open(f"debug/{slug}.json", "w", encoding="utf-8").write(text[:4000])
    except Exception:
        pass
