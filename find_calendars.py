#!/usr/bin/env python3
"""find_calendars.py: CLAUDE.md waterfall steps 0 to 3, run on GitHub (no secrets, no browser).

For every row of the current list (FEED_LIST) whose method is none (or names passed as arguments):
  - web search "<name> Washington DC events" (DuckDuckGo HTML) for candidate pages
  - fetch the row's URL (or the best search hit if it fails), the site root, and up to 4
    one-click links whose text or path says events / calendar / programs / exhibitions ...
  - on every page: JSON-LD Event count + samples, dated-string count, feed hints (.ics, webcal,
    ?ical=1, Google Calendar embeds, RSS, Eventbrite / Meetup / Luma organizer links, tribe API,
    Squarespace, Localist, LiveWhale, Trumba, Timely, Tockify), iframes, platform
  - probes: /wp-json/tribe/events/v1/events, /events/?ical=1, Squarespace <events>?format=json
Writes find/<slug>.json (everything) + find/<slug>.txt (text of the best page, 6000 chars) and
<prefix>find_log.csv. Haiku scouts read them with briefs/SCOUT_FIND.md. Cap 75s per source."""
import csv, json, re, sys, time
from pathlib import Path
from urllib.parse import urljoin, urlparse, quote_plus, unquote, parse_qs
sys.path.insert(0, ".")
from lists import current as _list
from readers.common import get
_L = _list()

OUT = Path("find"); OUT.mkdir(exist_ok=True)
CAP = 75
DATE_RE = re.compile(r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.? \d{1,2}(?:,? 20\d\d)?\b|\b20\d\d-\d\d-\d\d\b|\b\d{1,2}/\d{1,2}/20\d\d\b")
EVENTISH = re.compile(r"event|calendar|whats-?on|what's on|programs?\b|exhibition|upcoming|schedule|happenings|gatherings|salon|series|tickets", re.I)
HINT = re.compile(r"\.ics\b|webcal:|ical=1|format=ical|calendar\.google\.com/calendar/(?:embed|ical|u/\d/embed)|eventbrite\.[a-z.]+/o/|meetup\.com/[^/\s\"']+|lu\.ma/|luma\.com/|/wp-json/tribe|tockify\.com|time\.ly|timely\.fun|localist|/live/json|trumba\.com|/feed/?$|rss|atom|eventbrite\.[a-z.]+/e/", re.I)
SKIP = re.compile(r"facebook|instagram|linkedin|twitter|x\.com|yelp|tripadvisor|wikipedia|youtube|tiktok|pinterest|glassdoor|indeed|mapquest|google\.com/maps", re.I)

def slug(n): return re.sub(r"[^a-z0-9]+", "-", n.lower()).strip("-")[:60]

def search(q):
    try:
        r = get("https://html.duckduckgo.com/html/?q=" + quote_plus(q), timeout=15)
        out = []
        for href in re.findall(r'class="result__a"[^>]*href="([^"]+)"', r.text):
            if "uddg=" in href:
                href = unquote(parse_qs(urlparse(href).query).get("uddg", [href])[0])
            if href.startswith("http") and not SKIP.search(href) and href not in out:
                out.append(href)
        return out[:6], ""
    except Exception as e:
        return [], f"{type(e).__name__}: {e}"[:120]

def soup_of(html):
    from bs4 import BeautifulSoup
    return BeautifulSoup(html, "lxml")

def jsonld_events(soup):
    evs = []
    for tag in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(tag.string or "")
        except Exception:
            continue
        stack = data if isinstance(data, list) else [data]
        while stack:
            d = stack.pop()
            if isinstance(d, dict):
                t = d.get("@type")
                if (t == "Event" or (isinstance(t, list) and "Event" in t) or (isinstance(t, str) and t.endswith("Event"))):
                    evs.append({"name": d.get("name"), "start": d.get("startDate"), "url": d.get("url")})
                stack += [v for v in d.values() if isinstance(v, (dict, list))]
            elif isinstance(d, list):
                stack += d
    return evs

def examine(url, deadline):
    rec = {"url": url, "status": None, "final_url": "", "title": "", "dates": 0, "jsonld": 0, "jsonld_samples": [],
           "hints": [], "iframes": [], "event_links": [], "platform": "", "error": "", "text": ""}
    if time.time() > deadline:
        rec["error"] = "cap"; return rec
    try:
        r = get(url, timeout=20)
        rec["status"], rec["final_url"] = r.status_code, str(r.url)
        html = r.text
    except Exception as e:
        rec["error"] = f"{type(e).__name__}: {e}"[:160]; return rec
    s = soup_of(html)
    rec["title"] = (s.title.string or "").strip()[:120] if s.title else ""
    gen = s.find("meta", attrs={"name": "generator"})
    low = html.lower()
    rec["platform"] = " ".join(p for p, k in [("wordpress", "wp-content"), ("squarespace", "squarespace"), ("wix", "wix.com"),
                      ("tribe-events", "tribe-events"), ("drupal", "drupal"), ("hubspot", "hubspot"), ("webflow", "webflow"),
                      ("growthzone", "growthzone"), ("chambermaster", "chambermaster"), ("eventbrite", "eventbrite"),
                      ("blackbaud", "blackbaud"), ("salesforce", "force.com"), ("localist", "localist"), ("trumba", "trumba"),
                      ("tockify", "tockify"), ("timely", "time.ly"), ("wild apricot", "wildapricot"), ("shulcloud", "shulcloud"),
                      ("clubessential", "clubessential"), ("jonas", "jonasclub"), ("cvent", "cvent")] if k in low)
    if gen and gen.get("content"):
        rec["platform"] += f" [{gen['content'][:40]}]"
    for t in s(["script", "style", "noscript"]):
        if t.get("type") != "application/ld+json":
            t.decompose()
    ev = jsonld_events(soup_of(html))
    rec["jsonld"], rec["jsonld_samples"] = len(ev), ev[:5]
    text = re.sub(r"\n\s*\n+", "\n", s.get_text("\n"))
    rec["dates"], rec["text"] = len(DATE_RE.findall(text)), text[:6000]
    base = rec["final_url"] or url
    seen = set()
    for tag in s.find_all(["a", "link", "iframe"]):
        href = tag.get("href") or tag.get("src") or ""
        if not href or href.startswith(("mailto:", "tel:", "javascript:", "#")):
            continue
        full = urljoin(base, href)
        if full in seen:
            continue
        seen.add(full)
        if tag.name == "iframe":
            rec["iframes"].append(full)
        if HINT.search(full) or (tag.name == "link" and "alternate" in (tag.get("rel") or [])):
            rec["hints"].append(full)
        label = (tag.get_text(" ") or "").strip()[:60]
        if tag.name == "a" and (EVENTISH.search(label) or EVENTISH.search(urlparse(full).path)) and not SKIP.search(full):
            rec["event_links"].append({"text": label, "url": full})
    rec["hints"], rec["iframes"], rec["event_links"] = rec["hints"][:25], rec["iframes"][:8], rec["event_links"][:25]
    return rec

def probes(root, deadline):
    out = []
    for path in ["/wp-json/tribe/events/v1/events?per_page=10", "/events/?ical=1", "/?ical=1"]:
        if time.time() > deadline:
            break
        u = root.rstrip("/") + path
        try:
            r = get(u, timeout=15)
            body = r.text
            n = body.count("BEGIN:VEVENT") if "ical" in path else len(re.findall(r'"start_date"', body))
            out.append({"url": u, "status": r.status_code, "events": n, "head": body[:300]})
        except Exception as e:
            out.append({"url": u, "status": f"{type(e).__name__}"[:40], "events": 0})
    return out

def same_site(a, b):
    ha, hb = urlparse(a).netloc.lower().removeprefix("www."), urlparse(b).netloc.lower().removeprefix("www.")
    return ha == hb or ha.endswith("." + hb) or hb.endswith("." + ha) or ha.split(".")[-2:] == hb.split(".")[-2:]

def main():
    names = set(sys.argv[1:])
    rows = list(csv.DictReader(open(_L["csv"], newline="", encoding="utf-8")))
    targets = [r for r in rows if r["name"] in names] if names else [r for r in rows if r["method"] == "none"]
    print(f"{len(targets)} sources, cap {CAP}s each", flush=True)
    log = []
    for r in targets:
        t0 = time.time(); deadline = t0 + CAP
        hits, serr = search(f'"{r["name"].split(" (")[0]}" Washington DC events')
        pages = [examine(r["url"], deadline)]
        start = pages[0]
        if (start["error"] or (start["status"] or 0) >= 400) and hits:
            pages.append(examine(hits[0], deadline)); start = pages[-1]
        base = start["final_url"] or start["url"]
        root = f"{urlparse(base).scheme}://{urlparse(base).netloc}/"
        if root.rstrip("/") != base.rstrip("/"):
            pages.append(examine(root, deadline))
        follow = []
        for p in pages:
            for l in p["event_links"]:
                if same_site(l["url"], base) and l["url"] not in follow and l["url"] not in [x["url"] for x in pages]:
                    follow.append(l["url"])
        for u in follow[:4]:
            pages.append(examine(u, deadline))
        pr = probes(root, deadline)
        best = max(pages, key=lambda p: (p["jsonld"] * 5 + p["dates"]) if not p["error"] else -1)
        doc = {"row": r["row"], "name": r["name"], "seed_url": r["url"], "programs": r.get("programs", ""),
               "access": r.get("access", ""), "found": time.strftime("%Y-%m-%d %H:%MZ", time.gmtime()),
               "search_hits": hits, "search_error": serr, "probes": pr,
               "pages": [{k: v for k, v in p.items() if k != "text"} for p in pages], "best_page": best["url"]}
        (OUT / f"{slug(r['name'])}.json").write_text(json.dumps(doc, indent=1), encoding="utf-8")
        (OUT / f"{slug(r['name'])}.txt").write_text(f"{r['name']}\nbest page: {best['url']} (status {best['status']}, {best['dates']} date strings, {best['jsonld']} JSON-LD events)\nfetched {doc['found']}\n\n{best['text']}", encoding="utf-8")
        line = [r["row"], r["name"], best["url"], best["status"], best["dates"], best["jsonld"],
                sum(len(p["hints"]) for p in pages), max((x.get("events", 0) for x in pr), default=0), len(hits),
                round(time.time() - t0, 1), (start["error"] or serr)[:80]]
        log.append(line); print(line, flush=True)
    with open(_L["prefix"] + "find_log.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["row", "name", "best_page", "status", "date_strings", "jsonld_events", "feed_hints", "probe_events", "search_hits", "seconds", "error"]); w.writerows(log)
    print("DONE", len(log))

if __name__ == "__main__":
    main()
