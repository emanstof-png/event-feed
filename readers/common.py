import re, json, requests
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

TZ = ZoneInfo("America/New_York")
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36",
      "Accept-Language": "en-US,en;q=0.9"}

def today():
    return datetime.now(TZ).date()

def window(days=21):
    t = today()
    return t, t + timedelta(days=days)

def get(url, **kw):
    r = requests.get(url, headers={**UA, **kw.pop("headers", {})}, timeout=kw.pop("timeout", 30), **kw)
    r.raise_for_status()
    return r

def event(date_s, title, source, time_s="", venue="", link=""):
    return {"date": date_s, "time": time_s, "title": title.strip()[:200], "venue": venue.strip()[:120],
            "link": link, "source": source}

def in_window(ev, days=21):
    lo, hi = window(days)
    try:
        d = date.fromisoformat(ev["date"])
    except Exception:
        return False
    return lo <= d <= hi

def dedupe(events):
    seen, out = set(), []
    for e in events:
        k = (e["date"], re.sub(r"\W+", "", e["title"].lower())[:40])
        if k not in seen:
            seen.add(k); out.append(e)
    return out
