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
    """GET with a browser-like UA; retries twice on 429/5xx with a short backoff."""
    import time
    headers = {**UA, **kw.pop("headers", {})}
    timeout = kw.pop("timeout", 30)
    for attempt in range(3):
        r = requests.get(url, headers=headers, timeout=timeout, **kw)
        if r.status_code in (429, 500, 502, 503, 504) and attempt < 2:
            time.sleep(4 * (attempt + 1))
            continue
        r.raise_for_status()
        return r
    r.raise_for_status()
    return r

def event(date_s, title, source, time_s="", venue="", link="", desc=""):
    return {"date": date_s, "time": time_s, "title": title.strip()[:200], "venue": venue.strip()[:120],
            "link": link, "source": source, "desc": clean_text(desc)[:600]}

def clean_text(x):
    import html as _h
    x = re.sub(r"<[^>]+>", " ", str(x or ""))
    return re.sub(r"\s+", " ", _h.unescape(x)).strip()

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
