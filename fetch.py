#!/usr/bin/env python3
"""fetch.py: the weekly job.

Reads the Sources tab, dispatches each row on its Method column to readers/<method>.py,
and writes every upcoming event (next 21 days) to the Feed tab, oldest first.

    python fetch.py                 # real run: writes Feed, updates Sources G (Last run) and L (count)
    python fetch.py --dry-run       # writes Feed_test and Run_log instead; Sources untouched
    python fetch.py --only "Baila"  # only sources whose name contains this (case-insensitive)
    python fetch.py --methods ical,api,recurring   # only these methods (fast smoke test)
    python fetch.py --limit 20      # first N eligible rows

Env (GitHub Actions secrets):
    GOOGLE_SERVICE_ACCOUNT_JSON   the service-account key JSON, as one string
    ANTHROPIC_API_KEY             for the Haiku readers (html, rss, browser, unknown api shapes)
    SHEET_ID                      optional, defaults to the Event Calendars sheet

Every source gets a line in Run_log (or Sources col K/L on a real run): status, count, seconds,
error. One source failing never stops the run. A per-source timeout keeps the browser readers
from eating the whole job.
"""
import argparse, json, os, sys, time, traceback, importlib
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutTimeout
from datetime import datetime

from readers.common import TZ, dedupe
from lists import current as _list
L = _list()   # FEED_LIST=elite runs the Elite Sources tab into Elite Feed with this same code

SHEET_ID = os.environ.get("SHEET_ID", "1vDMP4n3bOBGGvwZ9PerbctPr4uGhiRvxu1cPv_QROYg")
WINDOW_DAYS = 21
PER_SOURCE_TIMEOUT = {"browser": 90, "stealth": 90}   # seconds; browser render itself is capped at 45s (readers/browser.CAP), the rest is Haiku; everything else 150 (room for a fallback)
DEFAULT_TIMEOUT = 150
FALLBACK_TO_BROWSER = {"html", "jsonld", "api", "xhr", "rss"}   # on error or 0 events, render with the stealth browser

# Sources tab columns (0-based)
COL = dict(name=0, url=1, category=2, has_feed=3, paused=4, status_old=5, last_run=6,
           priority=7, method=8, feed_url=9, status=10, verified=11, notes=12, how=13)

# Method in sheet -> readers module
MODULE = {"ical": "ical", "api": "api", "xhr": "api", "rss": "rss", "html": "html",
          "jsonld": "html", "reader": "html", "browser": "browser", "stealth": "browser",
          "recurring": "recurring"}

FEED_HEADER = ["Pick", "Date", "Time", "Title", "Venue", "Source", "Link", "Category", "Description"]
LOG_HEADER = ["Source", "Method", "Status", "Events", "Seconds", "Error", "Sample", "Run at"]


# ---------- sheet access ----------

def open_sheet():
    import gspread
    from google.oauth2.service_account import Credentials
    raw = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not raw:
        sys.exit("GOOGLE_SERVICE_ACCOUNT_JSON is not set")
    creds = Credentials.from_service_account_info(
        json.loads(raw), scopes=["https://www.googleapis.com/auth/spreadsheets"])
    return gspread.authorize(creds).open_by_key(SHEET_ID)


def load_sources(sh):
    rows = sh.worksheet(L["sources"]).get_all_values()
    out = []
    for i, r in enumerate(rows[1:], start=2):          # sheet row numbers
        r = r + [""] * (14 - len(r))
        if not r[COL["name"]].strip():
            continue
        out.append({
            "row": i,
            "name": r[COL["name"]].strip(),
            "url": r[COL["url"]].strip(),
            "category": r[COL["category"]].strip(),
            "paused": r[COL["paused"]].strip().upper() == "TRUE",
            "method": r[COL["method"]].strip().lower(),
            "feed_url": r[COL["feed_url"]].strip(),
        })
    return out


def load_sources_csv(path=None):
    path = path or L["csv"]
    """Snapshot of Sources columns A, B, E, I, J for runs without a Google key."""
    import csv
    out = []
    with open(path, newline="", encoding="utf-8") as f:
        for i, r in enumerate(csv.DictReader(f), start=2):
            out.append({"row": i, "name": r["name"].strip(), "url": r["url"].strip(), "category": r.get("category", ""),
                        "paused": (r.get("paused") or "").strip().upper() == "TRUE",
                        "method": r["method"].strip().lower(), "feed_url": (r.get("feed_url") or "").strip()})
    return out


def worksheet(sh, title, rows=2000, cols=10):
    try:
        return sh.worksheet(title)
    except Exception:
        return sh.add_worksheet(title=title, rows=rows, cols=cols)


def write_table(ws, header, rows):
    ws.clear()
    ws.update(range_name="A1", values=[header] + rows, value_input_option="USER_ENTERED")
    try:
        ws.freeze(rows=1)
    except Exception:
        pass


def checkboxes(sh, sheet_id, n):
    """Turn column A rows 2..n+1 into real checkboxes."""
    try:
        sh.batch_update({"requests": [{"setDataValidation": {
            "range": {"sheetId": sheet_id, "startRowIndex": 1, "endRowIndex": n + 1,
                      "startColumnIndex": 0, "endColumnIndex": 1},
            "rule": {"condition": {"type": "BOOLEAN"}, "showCustomUi": True}}}]})
    except Exception as e:
        print("checkbox formatting failed:", e, flush=True)


# ---------- running one source ----------

def run_source(src):
    """Returns (events, status, error). Never raises."""
    m = src["method"]
    if src["paused"]:
        return [], "PAUSED", ""
    if m in ("", "none", "human"):
        return [], "SKIPPED", f"method={m or 'blank'}"
    mod_name = MODULE.get(m)
    if not mod_name:
        return [], "SKIPPED", f"unknown method '{m}'"
    if src["feed_url"].startswith("https://r.jina.ai/"):
        src = {**src, "url": src["feed_url"]}
    if m in ("browser", "stealth") and src["feed_url"].startswith("http"):
        src = {**src, "url": src["feed_url"]}   # J holds the widget/embed URL to render
    try:
        mod = importlib.import_module(f"readers.{mod_name}")
        evs = mod.read(src, WINDOW_DAYS) or []
        evs = dedupe(evs)
        if not evs and m in FALLBACK_TO_BROWSER:
            evs, status, err = _browser_fallback(src, "0 events")
            if evs:
                return evs, status, err
        if m == "recurring":
            status = "RECURRING"
        elif len(evs) >= 3:
            status = "LIVE"
        elif evs:
            status = "LIVE but thin"
        else:
            status = "EMPTY"
        return evs, status, ""
    except Exception as e:
        err = f"{type(e).__name__}: {e}"[:300]
        if m in FALLBACK_TO_BROWSER:
            evs, status, err2 = _browser_fallback(src, err)
            if evs:
                return evs, status, err2
        return [], "ERROR", err


def _browser_fallback(src, why):
    """html/api/xhr/rss got nothing: render the page URL with the stealth browser instead."""
    try:
        mod = importlib.import_module("readers.browser")
        evs = dedupe(mod.read({**src, "feed_url": ""}, WINDOW_DAYS) or [])
    except Exception as e:
        return [], "ERROR", f"{why}; browser fallback: {type(e).__name__}: {e}"[:300]
    if len(evs) >= 3:
        return evs, "LIVE", f"via browser fallback ({why})"
    if evs:
        return evs, "LIVE but thin", f"via browser fallback ({why})"
    return [], "EMPTY", f"{why}; browser fallback also 0"


def previous_counts(sh=None):
    """{source name: (events, run at)} from the last run, for the zero-count alarm: Run_log tab on
    a sheet run, else the committed run_log.csv."""
    rows = []
    try:
        if sh is not None:
            rows = sh.worksheet(L["run_log"]).get_all_values()[1:]
        else:
            import csv
            rows = list(csv.reader(open(f"run_log{L['out']}.csv", newline="", encoding="utf-8")))[1:]
    except Exception:
        return {}
    out = {}
    for r in rows:
        try:
            if int(r[3]) > 0:
                out[r[0]] = (int(r[3]), r[7] if len(r) > 7 else "")
        except Exception:
            pass
    return out


def run_with_timeout(src):
    t0 = time.time()
    limit = PER_SOURCE_TIMEOUT.get(src["method"], DEFAULT_TIMEOUT)
    ex = ThreadPoolExecutor(max_workers=1)   # no `with`: its exit would wait for a hung reader, defeating the timeout
    fut = ex.submit(run_source, src)
    try:
        evs, status, err = fut.result(timeout=limit)
    except FutTimeout:
        evs, status, err = [], "ERROR", f"timeout after {limit}s"
    finally:
        ex.shutdown(wait=False)
    return evs, status, err, round(time.time() - t0, 1)


# ---------- main ----------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="write Feed_test + Run_log, leave Feed and Sources alone")
    ap.add_argument("--only", default="", help="substring of source name")
    ap.add_argument("--methods", default="", help="comma list of methods to run")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--workers", type=int, default=4, help="parallel sources (browser rows run 1 at a time)")
    ap.add_argument("--csv", action="store_true",
                    help="no Google key: read sources from sources_methods.csv, write feed_test.csv + run_log.csv")
    ap.add_argument("--sources-csv", default=None, help="with --csv: read sources from this file")
    ap.add_argument("--out", default=L["out"], help="with --csv: write feed_test<out>.csv and run_log<out>.csv (e.g. _prove)")
    args = ap.parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("WARNING: ANTHROPIC_API_KEY not set; html/rss/browser readers will return nothing", flush=True)

    if args.csv:
        sh, sources = None, load_sources_csv(args.sources_csv)
    else:
        sh = open_sheet()
        sources = load_sources(sh)
    if args.only:
        sources = [s for s in sources if args.only.lower() in s["name"].lower()]
    if args.methods:
        want = {m.strip().lower() for m in args.methods.split(",")}
        sources = [s for s in sources if s["method"] in want]
    if args.limit:
        sources = sources[: args.limit]
    print(f"{len(sources)} sources, dry_run={args.dry_run}", flush=True)

    run_at = datetime.now(TZ).strftime("%Y-%m-%d %H:%M")
    fast = [s for s in sources if s["method"] not in ("browser", "stealth")]
    slow = [s for s in sources if s["method"] in ("browser", "stealth")]

    results = {}

    def handle(src):
        evs, status, err, secs = run_with_timeout(src)
        results[src["row"]] = (src, evs, status, err, secs)
        sample = "; ".join(f"{e['date']} {e['title'][:40]}" for e in evs[:3])
        print(f"[{status:14}] {src['name'][:45]:45} {src['method']:9} n={len(evs):3} {secs:6.1f}s {err} | {sample}", flush=True)

    # fast readers in parallel, browser readers one at a time (one Chromium each is plenty)
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as ex:
        list(ex.map(handle, fast))
    for s in slow:
        handle(s)

    # ---- Feed rows: oldest first, then time, then source
    all_events = []
    for src, evs, status, err, secs in results.values():
        for e in evs:
            all_events.append(e)
    all_events.sort(key=lambda e: (e["date"], e["time"] or "99:99", e["source"]))
    if args.csv:   # keep the raw text so Haiku scouts can write blurbs without an API key
        import csv as _csv
        with open(f"feed_desc{args.out}.csv", "w", newline="", encoding="utf-8") as f:
            w = _csv.writer(f); w.writerow(["n", "title", "source", "desc"])
            w.writerows([k + 2, e["title"], e["source"], e.get("desc", "")] for k, e in enumerate(all_events))
    from readers.haiku import summarize
    summarize(all_events)
    cat = {src["name"]: src.get("category", "") for src, *_ in results.values()}
    urls = {src["name"]: src["url"] for src, *_ in results.values()}
    for e in all_events:                       # RULES: a feed row is always clickable
        if not (e.get("link") or "").startswith("http"):
            e["link"] = urls.get(e["source"], "")
    feed_rows = [[False, e["date"], e["time"], e["title"], e["venue"], e["source"], e["link"], cat.get(e["source"], ""), e.get("desc", "")]
                 for e in all_events]

    prev = previous_counts(sh)
    alarms = []
    log_rows = []
    for row in sorted(results):
        src, evs, status, err, secs = results[row]
        was = prev.get(src["name"])
        if not evs and was and status not in ("PAUSED", "SKIPPED"):   # SPEC_SPEED: zero-count alarm
            err = f"ALARM: 0 events, had {was[0]} on {was[1]}" + (f"; {err}" if err else "")
            results[row] = (src, evs, status, err, secs)
            alarms.append(src["name"])
        sample = "; ".join(f"{e['date']} {e['title'][:40]}" for e in evs[:3])
        log_rows.append([src["name"], src["method"], status, len(evs), secs, err, sample, run_at])

    counts = {}
    for _, _, status, _, _ in results.values():
        counts[status] = counts.get(status, 0) + 1
    print("\nSUMMARY", json.dumps(counts), f"events={len(feed_rows)}", flush=True)
    if alarms:
        print(f"ALARM: {len(alarms)} source(s) had events last run and 0 now: " + "; ".join(alarms), flush=True)

    if args.csv:
        import csv
        with open(f"feed_test{args.out}.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f); w.writerow(FEED_HEADER); w.writerows(feed_rows)
        with open(f"run_log{args.out}.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f); w.writerow(LOG_HEADER); w.writerows(log_rows)
        print(f"wrote feed_test{args.out}.csv and run_log{args.out}.csv", flush=True)
        return 0

    if args.dry_run:
        write_table(worksheet(sh, L["feed_test"]), FEED_HEADER, feed_rows)
        write_table(worksheet(sh, L["run_log"]), LOG_HEADER, log_rows)
        print("wrote Feed_test and Run_log", flush=True)
        return 0

    # real run: Feed tab, plus Last run (G), Status (K), Events verified (L) on Sources
    feed_ws = worksheet(sh, L["feed"])
    write_table(feed_ws, FEED_HEADER, feed_rows)
    if feed_rows:
        checkboxes(sh, feed_ws.id, len(feed_rows))
    src_ws = sh.worksheet(L["sources"])
    updates = []
    for row in sorted(results):
        src, evs, status, err, secs = results[row]
        if status in ("PAUSED", "SKIPPED"):
            continue
        reason = f"{status} ({err})" if err else status
        updates.append({"range": f"G{row}", "values": [[run_at]]})
        updates.append({"range": f"K{row}:L{row}", "values": [[reason, len(evs) if src["method"] != "recurring" else "recurring"]]})
    if updates:
        src_ws.batch_update(updates, value_input_option="USER_ENTERED")
    write_table(worksheet(sh, L["run_log"]), LOG_HEADER, log_rows)
    print(f"wrote {L['feed']}, {L['sources']} G/K/L, {L['run_log']}", flush=True)
    return 0


if __name__ == "__main__":
    rc = main() or 0
    sys.stdout.flush(); sys.stderr.flush()
    os._exit(rc)   # a reader that hung past its timeout must not hold the job open (Oct 24)
