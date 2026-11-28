"""Capture check (layer 1 of the accuracy test, Nov 27). No network, no model.

For every source on every list, read the page GitHub saved (raw_samples/ or browser_samples/), and flag:
  BLOCKED    status 4xx/5xx/None or 0 chars
  STALE      the saved page was fetched/rendered before the run date (a job had not finished; Nov 27 lesson)
  TRUNCATED  saved text hit a length cap (40000 / 60000 / 150000), so later events may be missing
  POSSIBLE MISS  the saved page mentions window dates but the weekend feed has fewer rows for that source
Structured feeds (ical/api/xhr/recurring) have no saved page; their row count comes from the feed test.

  python accuracy_check.py 2026-11-27 2026-11-29 [scout tsv globs...]   -> accuracy_capture.csv + a summary
"""
import csv, os, re, sys
from datetime import date, timedelta
from collections import Counter

start, end = (date.fromisoformat(a) for a in sys.argv[1:3])
days = [start + timedelta(n) for n in range((end - start).days + 1)]
CAPS = {40000, 60000, 150000}
MON = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

def slug(n):
    return re.sub(r"[^a-z0-9]+", "-", n.lower()).strip("-")[:60]

def day_patterns(d):
    m, mm = MON[d.month - 1], MON[d.month - 1][:3]
    return [rf"\b{m}\s+{d.day}\b", rf"\b{mm}\.?\s+{d.day}\b", rf"\b{d.day}\s+{mm}", rf"\b{d.month}/{d.day}\b",
            rf"{d.isoformat()}", rf"\b{d.month:02d}/{d.day:02d}\b"]

PATS = {d: re.compile("|".join(day_patterns(d)), re.I) for d in days}

feed = Counter()
for f in ("weekend_feed.csv", "weekend_feed_elite.csv"):
    if os.path.exists(f):
        for r in csv.DictReader(open(f, encoding="utf-8")):
            feed[r["Source"]] += 1

# extracted rows before the "already started" filter: scout TSVs passed after the dates (Date Time Title Venue Link Source File)
import glob
ext = Counter()
for pat in sys.argv[3:]:
    for f in glob.glob(pat):
        for row in csv.reader(open(f, encoding="utf-8"), delimiter="\t"):
            if len(row) >= 6 and re.match(r"\d{4}-\d\d-\d\d", row[0]):
                ext[row[5]] += 1
for k, v in ext.items():
    feed[k] = max(feed[k], v)

out = []
for lst, f in (("main", "sources_methods.csv"), ("elite", "elite_methods.csv"), ("nightlife", "nightlife_methods.csv")):
    for r in csv.DictReader(open(f, encoding="utf-8")):
        if r["method"] == "none" or (r.get("paused") or "").strip().upper() == "TRUE":
            continue
        s = slug(r["name"])
        paths = [p for p in (f"browser_samples/{s}.txt", f"raw_samples/{s}.txt") if os.path.exists(p)]
        path = max(paths, key=os.path.getmtime) if paths else ""
        status = chars = ""
        hits = 0
        flags = []
        if path:
            text = open(path, encoding="utf-8", errors="replace").read()
            head = text.split("\n", 3)
            meta = head[2] if len(head) > 2 else ""
            m1 = re.search(r"status=(\S+)", meta); m2 = re.search(r"chars=(\d+)", meta)
            status = m1[1] if m1 else ""; chars = int(m2[1]) if m2 else 0
            body = head[3] if len(head) > 3 else ""
            hits = sum(1 for d in days for _ in PATS[d].finditer(body))
            if status in ("None", "") or (status.isdigit() and int(status) >= 400) or chars == 0:
                flags.append("BLOCKED")
            m3 = re.search(r"(?:fetched|rendered) (\d{4}-\d\d-\d\d)", meta)
            if m3 and m3[1] < (sys.argv[1] if len(sys.argv) > 1 else m3[1]):
                flags.append("STALE")
            if chars in CAPS:
                flags.append("TRUNCATED")
        elif r["method"] in ("html", "jsonld", "rss", "browser", "stealth"):
            flags.append("NO SAVED PAGE")
        n = feed.get(r["name"], 0)
        if path and "BLOCKED" not in flags and hits > 0 and n == 0:
            flags.append("POSSIBLE MISS")
        elif path and hits >= 4 and n < hits / 3:
            flags.append("POSSIBLE UNDERCOUNT")
        out.append([lst, r["row"], r["name"], r["method"], path, status, chars, hits, n, " ".join(flags) or "OK"])

with open("accuracy_capture.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["list", "row", "name", "method", "saved_file", "status", "chars", "window_date_mentions", "feed_rows", "flags"])
    w.writerows(out)
c = Counter(f for row in out for f in row[-1].split(" ") if f)
print(len(out), "sources checked;", dict(c))
