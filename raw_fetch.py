#!/usr/bin/env python3
"""Raw fetch (no API key). For every html / jsonld / rss row in sources_methods.csv, fetch the
page (B) or feed (J for rss) with a plain request and save what a reader would see to
raw_samples/<slug>.txt: schema.org Event JSON-LD lines first (exact), then the visible text
(or the feed items). One line per source goes to raw_fetch_log.csv. Haiku scouts read the
files with briefs/SCOUT_EXTRACT.md, standing in for readers/haiku.py until the key exists.
Browser and stealth rows are rendered by render_test.py instead."""
import csv, re, sys, time
from pathlib import Path
from lists import current as _list
_L = _list()   # FEED_LIST=elite reads elite_methods.csv, writes elite_<log>.csv; sample files are per source either way
sys.path.insert(0, ".")
import feedparser
from readers.common import get
from readers.html import visible_text, jsonld_events

OUT = Path("raw_samples"); OUT.mkdir(exist_ok=True)
METHODS = {"html", "jsonld", "rss"}

def slug(n): return re.sub(r"[^a-z0-9]+", "-", n.lower()).strip("-")[:60]

rows = list(csv.DictReader(open(_L["csv"], newline="", encoding="utf-8")))
targets = [r for r in rows if r["method"] in METHODS and not r.get("paused")]
print(f"{len(targets)} sources", flush=True)
log = []
for r in targets:
    t0 = time.time(); status, err, body = "", "", ""
    try:
        if r["method"] == "rss":
            url = r["feed_url"] or r["url"]
            feed = feedparser.parse(get(url).content)
            status = f"{len(feed.entries)} items"
            body = "\n\n".join(f"{e.get('title','')}\n{e.get('published','')}\n{e.get('summary','')[:800]}\n{e.get('link','')}"
                               for e in feed.entries[:80])
        else:
            url = r["url"]
            resp = get(url); status = str(resp.status_code)
            text, soup = visible_text(resp.text)
            ld = jsonld_events(soup, r["name"])
            ld_lines = "\n".join(f"JSONLD\t{e.get('date','')}\t{e.get('time','')}\t{e.get('title','')}\t{e.get('venue','')}\t{e.get('link','')}" for e in ld)
            body = (ld_lines + "\n\n" if ld_lines else "") + text[:40000]
    except Exception as e:
        url = r["feed_url"] if r["method"] == "rss" else r["url"]
        err = f"{type(e).__name__}: {e}"[:200]
    secs = round(time.time() - t0, 1)
    (OUT / f"{slug(r['name'])}.txt").write_text(
        f"{r['name']}\n{url}\nfetched {time.strftime('%Y-%m-%d %H:%MZ', time.gmtime())}  status={status} chars={len(body)} error={err}\n\n{body}",
        encoding="utf-8")
    line = [r["row"], r["name"], r["method"], url, status, len(body), secs, err]
    log.append(line); print(line, flush=True)
with open(_L["prefix"] + "raw_fetch_log.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["row", "name", "method", "url", "status", "chars", "seconds", "error"]); w.writerows(log)
print("DONE", len(log))
