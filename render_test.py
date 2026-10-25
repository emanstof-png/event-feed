#!/usr/bin/env python3
"""Browser render test (no API key). For every browser/stealth row in sources_methods.csv,
plus any names passed as arguments, render the page with the stealth browser and save the
text to browser_samples/<slug>.txt plus one line per source in browser_render_log.csv.
Haiku scouts then read the text files to prove (or disprove) that events are visible."""
import csv, re, sys, time, os
from pathlib import Path
from lists import current as _list
_L = _list()   # FEED_LIST=elite reads elite_methods.csv, writes elite_<log>.csv; sample files are per source either way
sys.path.insert(0, ".")
from readers.browser import render_text

OUT = Path("browser_samples"); OUT.mkdir(exist_ok=True)
EXTRA = set(sys.argv[1:]) or (set() if _L["prefix"] else {"Sixth & I", "2239 (Washington Hebrew Congregation)", "Rock Creek Conservancy", "Interintellect"})

def slug(n): return re.sub(r"[^a-z0-9]+", "-", n.lower()).strip("-")[:60]

rows = list(csv.DictReader(open(_L["csv"], newline="", encoding="utf-8")))
targets = [r for r in rows if r["method"] in ("browser", "stealth") or r["name"] in EXTRA]
print(f"{len(targets)} sources", flush=True)
log = []
for r in targets:
    url = r["feed_url"] if (r["method"] in ("browser", "stealth") and r["feed_url"].startswith("http")) else r["url"]
    t0 = time.time()
    text, rep = render_text({"name": r["name"], "url": url, "feed_url": r["feed_url"]})
    secs = round(time.time() - t0, 1)
    dates = len(re.findall(r"\b(?:Oct|Nov|Dec|October|November|December)\.? \d{1,2}\b|\b(?:1[0-2]|0?[1-9])/\d{1,2}(?:/\d{2,4})?\b|\b20\d{2}-\d{2}-\d{2}\b", text))
    (OUT / f"{slug(r['name'])}.txt").write_text(f"{r['name']}\n{url}\nrendered {time.strftime('%Y-%m-%d %H:%MZ', time.gmtime())}  status={rep['status']} chars={rep['chars']} iframes={rep['iframes']} srcdoc={rep['srcdoc']} next={rep['clicked_next']} error={rep['error']}\n\n{text}", encoding="utf-8")
    line = [r["row"], r["name"], url, rep["status"], rep["chars"], rep["iframes"], rep["srcdoc"], rep["clicked_next"], dates, secs, rep["error"]]
    log.append(line); print(line, flush=True)
with open(_L["prefix"] + "browser_render_log.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["row", "name", "url", "status", "chars", "iframes", "srcdoc", "clicked_next", "date_strings", "seconds", "error"]); w.writerows(log)
print("DONE", len(log))
