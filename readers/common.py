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
    """GET that looks like Chrome down to the TLS handshake (curl_cffi impersonation), so sites
    that 403 plain Python requests answer normally (SPEC_SPEED Phase 2). Falls back to requests
    if curl_cffi is missing. Retries twice on 429/5xx with a short backoff."""
    import time
    timeout = kw.pop("timeout", 30)
    extra = kw.pop("headers", {})
    try:
        from curl_cffi import requests as creq
        # no User-Agent override: the impersonated browser sends its own, matching its TLS fingerprint
        do = lambda: creq.get(url, headers={"Accept-Language": UA["Accept-Language"], **extra},
                              impersonate="chrome", timeout=timeout, **kw)
    except ImportError:
        do = None
    plain = lambda: requests.get(url, headers={**UA, **extra}, timeout=timeout, **kw)
    for attempt in range(3):
        r = do() if do else plain()
        if do and r.status_code in (401, 403, 406):   # some sites refuse the impersonation; Oct 24: Ann Kite
            r2 = plain()
            if r2.status_code < 400:
                return r2
        if r.status_code in (429, 500, 502, 503, 504) and attempt < 2:
            time.sleep(4 * (attempt + 1))
            continue
        r.raise_for_status()
        return r
    r.raise_for_status()
    return r

def request(url, method="GET", data=None, multipart=None, headers=None, timeout=30):
    """POST / multipart replay of a widget's data call (SPEC_SPEED Phase 1). GET goes through get()."""
    headers = headers or {}
    if isinstance(data, str):   # a captured form string: send it as a form (sets the form Content-Type)
        from urllib.parse import parse_qsl
        data = dict(parse_qsl(data, keep_blank_values=True))
    if method == "GET" and not multipart:
        return get(url, headers=headers, timeout=timeout)
    if multipart is not None:   # requests builds the boundary; curl_cffi's multipart API differs
        r = requests.post(url, files={k: (None, v) for k, v in multipart.items()}, headers={**UA, **headers}, timeout=timeout)
    else:
        try:
            from curl_cffi import requests as creq
            r = creq.post(url, data=data, headers={"Accept-Language": UA["Accept-Language"], **headers}, impersonate="chrome", timeout=timeout)
            if r.status_code in (401, 403, 406):
                raise ImportError
        except ImportError:
            r = requests.post(url, data=data, headers={**UA, **headers}, timeout=timeout)
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
