#!/usr/bin/env python3
"""build_weekend.py START END [scout_tsv ...]: one feed per list for a short window (e.g. this weekend).
Merges the structured feeds (feed_test.csv, feed_test_elite.csv) with Haiku-scout lines (SCOUT_EXTRACT
format), keeps START..END, dedupes on date + title (an org's own row beats an aggregator's), and writes
weekend_feed.csv (main list) and weekend_feed_elite.csv (Elite list). A source in both lists goes to both."""
import csv, html, re, sys

start, end, tsvs = sys.argv[1], sys.argv[2], sys.argv[3:]
lists = {"main": list(csv.DictReader(open("sources_methods.csv"))), "elite": list(csv.DictReader(open("elite_methods.csv"))),
         "nightlife": list(csv.DictReader(open("nightlife_methods.csv")))}   # Nov 27: nightlife sources feed the main tab
meta = {}
for key, rows in lists.items():
    for r in rows:
        m = meta.setdefault(r["name"], {"lists": set(), "category": r["category"], "url": r["url"]})
        m["lists"].add("main" if key == "nightlife" else key)

def match(src):
    if src in meta:
        return src
    s = src.lower()[:20]
    hits = [n for n in meta if n.lower().startswith(s)]
    return hits[0] if hits else src

rows = []
desc = {}
for f in ("feed_desc.csv", "feed_desc_elite.csv", "feed_desc_nightlife.csv"):
    try:
        for r in csv.DictReader(open(f)):
            desc[(r.get("title"), r.get("source"))] = r.get("desc", "")
    except FileNotFoundError:
        pass
for f in ("feed_test.csv", "feed_test_elite.csv", "feed_test_nightlife.csv"):
    try:
        fr = list(csv.DictReader(open(f)))
    except FileNotFoundError:
        continue
    for r in fr:
        rows.append(dict(Date=r["Date"], Time=r["Time"], Title=r["Title"], Venue=r["Venue"], Source=r["Source"],
                         Link=r["Link"], raw=desc.get((r["Title"], r["Source"]), "")))
for f in tsvs:
    for line in open(f, encoding="utf-8"):
        p = line.rstrip("\n").split("\t")
        if len(p) < 6 or p[0] == "NONE" or not re.match(r"20\d\d-\d\d-\d\d$", p[0]):
            continue
        src = match(p[5].strip())
        rows.append(dict(Date=p[0], Time=p[1], Title=p[2], Venue=p[3], Source=src,
                         Link=p[4] if p[4].startswith("http") else meta.get(src, {}).get("url", ""), raw=""))
rows = [r for r in rows if start <= r["Date"] <= end]

agg = {n for n, m in meta.items() if m["category"] in ("Discovery",) or "aggregator" in n.lower()}
key = lambda r: (r["Date"], (r["Time"] or "")[:5], re.sub(r"\W+", "", html.unescape(r["Title"]).lower())[:40])   # Nov 27: time too, so a 7pm and 9:30pm show both stay
ART = re.compile(r"art|galler|exhibit|opening|first friday|museum|reception|underground", re.I)
NOW = sys.argv[0] and __import__("os").environ.get("NOT_BEFORE", "")   # e.g. "2026-11-14 18:00": drop what already ended

def keep(r):
    if r["Source"] == "Dupont Circle Art Walk" and not ART.search(r["Title"] + " " + r["Venue"]):
        return False   # the BID calendar is the whole neighborhood; keep the art
    if r["Time"] and not re.match(r"\d\d:\d\d", r["Time"]):
        return False   # scraped junk ("Time unclear", nav text)
    if re.search(r"\b(no classes|office closed|closed for|break \(|holiday hours)", r["Title"], re.I):
        return False   # closures, not events
    if NOW and r["Time"] and f"{r['Date']} {r['Time']}" < NOW:
        return False
    return True

def dedupe(rs):   # Nov 27: two orgs' own rows both stay (two Sur La Table stores); an aggregator copy of an org's row goes
    best = {}
    for r in rs:
        k = key(r)
        if r["Source"] in agg:
            best.setdefault(k + ("*agg",), r)
        else:
            best[k + (r["Source"],)] = r
    own = {k[:-1] for k in best if k[-1] != "*agg"}
    return [r for k, r in best.items() if k[-1] != "*agg" or k[:-1] not in own]

def blurb(r):
    t = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html.unescape(r["raw"] or ""))).strip()
    w = t.split()
    if len(w) >= 4:
        return " ".join(w[:12]).rstrip(",.;:") + ("..." if len(w) > 12 else "")
    return f"{meta.get(r['Source'], {}).get('category', 'Event')} at {r['Source']}"

for lst, out in (("main", "weekend_feed.csv"), ("elite", "weekend_feed_elite.csv")):
    sel = sorted(dedupe([r for r in rows if keep(r) and lst in meta.get(r["Source"], {"lists": {"main"}})["lists"]]),
                 key=lambda r: (r["Date"], r["Time"] or "99:99", r["Source"]))
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Pick", "Date", "Time", "Title", "Venue", "Source", "Link", "Category", "Description"])
        for r in sel:
            w.writerow([False, r["Date"], r["Time"], html.unescape(r["Title"]), html.unescape(r["Venue"]), r["Source"],
                        r["Link"] or meta.get(r["Source"], {}).get("url", ""), meta.get(r["Source"], {}).get("category", ""), blurb(r)])
    print(out, len(sel), "events from", len({r["Source"] for r in sel}), "groups")
