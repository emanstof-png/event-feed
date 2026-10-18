"""Method: html / jsonld. Server-rendered page with dated listings. Reads schema.org Event
JSON-LD first (exact), then hands the visible text to Haiku."""
import json, re
from bs4 import BeautifulSoup
from .common import get, event, in_window, dedupe
from .haiku import extract_events_from_text

def jsonld_events(soup, name):
    out = []
    def walk(n):
        if isinstance(n, list):
            for x in n: walk(x)
        elif isinstance(n, dict):
            t = n.get("@type"); t = t if isinstance(t, list) else [t]
            if any(isinstance(x, str) and x.endswith("Event") for x in t) and n.get("startDate"):
                s = str(n["startDate"]); loc = n.get("location"); loc = loc.get("name", "") if isinstance(loc, dict) else (loc or "")
                out.append(event(s[:10], str(n.get("name", "")), name, s[11:16] if "T" in s else "", str(loc), str(n.get("url", ""))))
            for k in ("@graph", "itemListElement", "item", "subEvent"):
                if k in n: walk(n[k])
    for tag in soup.find_all("script", type="application/ld+json"):
        try: walk(json.loads(tag.string or ""))
        except Exception: pass
    return out

def visible_text(html):
    soup = BeautifulSoup(html, "lxml")
    for t in soup(["script", "style", "noscript", "svg"]): t.decompose()
    return re.sub(r"\n\s*\n+", "\n", soup.get_text("\n")).strip(), soup

def read(source, window_days=21):
    html = get(source["url"]).text
    text, soup = visible_text(html)
    evs = jsonld_events(soup, source["name"])
    if len([e for e in evs if in_window(e, window_days)]) >= 3:
        return dedupe([e for e in evs if in_window(e, window_days)])
    evs += extract_events_from_text(text[:40000], source["name"], base_url=source["url"])
    return dedupe([e for e in evs if in_window(e, window_days)])
