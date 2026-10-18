#!/usr/bin/env python3
"""Probe: work out how each source in sources.csv can be read.

For every source it tries, cheapest first:
  1. ical     - an iCal feed (linked .ics/webcal, Google Calendar embed,
                WordPress "The Events Calendar" ?ical=1, Squarespace
                ?format=ical, Meetup /events/ical/)
  2. api      - a JSON events API (The Events Calendar REST, Localist)
  3. jsonld   - schema.org Event data embedded in the page
  4. rss      - an events RSS/Atom feed
  5. html     - plain HTML that already shows dated listings
  6. xhr      - a JSON data call the page makes, readable without a browser
  7. browser  - the page only shows events after JavaScript runs
  8. reader   - the site blocks GitHub's servers but reads through r.jina.ai
  9. none     - nothing usable found (blocked, no dates, program page)

Writes probe_report.csv, probe_report.json and probe_samples/<slug>.txt
(the page text the decision was based on, for building scrapers later).
"""

import csv
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs, quote, urljoin, urlparse
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).parent
SAMPLES = ROOT / "probe_samples"
TODAY = datetime.now(ZoneInfo("America/New_York")).date()
TODAY_ISO = TODAY.isoformat()
TODAY_ICS = TODAY.strftime("%Y%m%d")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/129.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

MONTHS = ["january", "february", "march", "april", "may", "june", "july",
          "august", "september", "october", "november", "december"]


def _month_pattern(names):
    alts = []
    for m in names:
        alts.append(m)
        alts.append(m[:3])
        if m == "september":
            alts.append("sept")
    return r"\b(?:" + "|".join(sorted(set(alts), key=len, reverse=True)) + r")\.?\s+\d{1,2}\b"


ANY_DATE_RE = re.compile(_month_pattern(MONTHS) + r"|\b20\d\d-\d\d-\d\d\b|\b\d{1,2}/\d{1,2}/(?:20)?\d\d\b", re.I)
NEAR_MONTHS = [MONTHS[(TODAY.month - 1 + i) % 12] for i in range(3)]
NEAR_DATE_RE = re.compile(_month_pattern(NEAR_MONTHS), re.I)


def slugify(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:60]


def fetch(url, timeout=25):
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        return {"status": r.status_code, "url": r.url, "text": r.text or "",
                "ctype": r.headers.get("content-type", "")}
    except Exception as e:  # network errors, TLS, timeouts
        return {"status": 0, "url": url, "text": "", "ctype": "", "error": f"{type(e).__name__}: {e}"[:200]}


def visible_text(html):
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "noscript", "svg", "template"]):
        tag.decompose()
    text = soup.get_text("\n")
    return re.sub(r"\n\s*\n+", "\n", text).strip()


def date_stats(text):
    return len(set(m.lower() for m in ANY_DATE_RE.findall(text))), len(set(m.lower() for m in NEAR_DATE_RE.findall(text)))


def check_ics(url):
    r = fetch(url)
    body = r["text"]
    if r["status"] != 200 or "BEGIN:VCALENDAR" not in body[:2000]:
        return None
    vevents = body.count("BEGIN:VEVENT")
    starts = re.findall(r"^DTSTART[^:\n]*:(\d{8})", body, re.M)
    upcoming = sum(1 for s in starts if s >= TODAY_ICS) + len(re.findall(r"^RRULE:", body, re.M))
    return {"feed_url": url, "events": vevents, "upcoming": upcoming}


def check_json_events(url):
    r = fetch(url)
    if r["status"] != 200:
        return None
    try:
        data = json.loads(r["text"])
    except Exception:
        return None
    if isinstance(data, dict):
        for key in ("events", "upcoming"):
            events = data.get(key)
            if isinstance(events, list) and events:
                return {"feed_url": url, "events": len(events)}
    n = count_eventish(data)
    if n >= 2:
        return {"feed_url": url, "events": n}
    return None


TITLE_KEYS = {"title", "name", "summary", "event_name", "eventname", "event_title"}
DATE_KEYS = {"start", "startdate", "start_date", "starttime", "start_time", "date", "datetime",
             "datetime_start", "dtstart", "starts_at", "startsat", "start_at", "startat",
             "event_date", "eventdate", "begin", "begins", "first_date", "start_datetime", "startdatetime"}


def count_eventish(node, depth=0):
    """Count objects in a JSON tree that look like events (a title plus a start date)."""
    if depth > 12:
        return 0
    if isinstance(node, list):
        return sum(count_eventish(n, depth + 1) for n in node[:500])
    if isinstance(node, dict):
        keys = {str(k).lower() for k in node}
        hit = 1 if (keys & TITLE_KEYS and keys & DATE_KEYS) else 0
        return hit + sum(count_eventish(v, depth + 1) for v in node.values() if isinstance(v, (list, dict)))
    return 0


GCAL_ID_RE = re.compile(r"calendar/v3/calendars/([^/?&]+)/events|/calendar/ical/([^/]+)/public|calendar/embed\?[^\"' ]*?src=([^&\"' ]+)")


def gcal_ics_from_text(text):
    out = []
    for m in GCAL_ID_RE.finditer(text):
        cal = next(g for g in m.groups() if g)
        cal = requests.utils.unquote(cal)
        out.append(f"https://calendar.google.com/calendar/ical/{quote(cal)}/public/basic.ics")
    return list(dict.fromkeys(out))[:4]


def reader_fetch(url):
    """Fallback for sites that block GitHub's servers: fetch through the r.jina.ai reader."""
    try:
        r = requests.get("https://r.jina.ai/" + url, headers={"Accept": "text/plain", "X-Return-Format": "text"},
                         timeout=60)
        return r.status_code, r.text or ""
    except Exception as e:
        return 0, f"{type(e).__name__}"


def jsonld_events(soup):
    found = []

    def walk(node):
        if isinstance(node, list):
            for n in node:
                walk(n)
        elif isinstance(node, dict):
            t = node.get("@type")
            types = t if isinstance(t, list) else [t]
            if any(isinstance(x, str) and x.endswith("Event") for x in types):
                found.append(node)
            for k in ("@graph", "itemListElement", "item", "subEvent", "event", "events"):
                if k in node:
                    walk(node[k])

    for tag in soup.find_all("script", type="application/ld+json"):
        try:
            walk(json.loads(tag.string or tag.get_text() or "null"))
        except Exception:
            continue
    upcoming = sum(1 for e in found if str(e.get("startDate", ""))[:10] >= TODAY_ISO)
    return len(found), upcoming


def ics_candidates(page_url, soup, html):
    html_lower = html.lower()
    cands = gcal_ics_from_text(html)
    for tag in soup.find_all(["a", "link"], href=True):
        href = tag["href"].strip()
        low = href.lower()
        if low.startswith("webcal:"):
            cands.append("https:" + href.split(":", 1)[1])
        elif ".ics" in low or "ical=1" in low or "format=ical" in low or low.endswith("/ical/") or "/ical?" in low:
            cands.append(urljoin(page_url, href))
    for frame in soup.find_all("iframe", src=True):
        src = frame["src"]
        if "calendar.google.com/calendar" in src:
            for cal in parse_qs(urlparse(src).query).get("src", []):
                cands.append(f"https://calendar.google.com/calendar/ical/{quote(cal)}/public/basic.ics")
    p = urlparse(page_url)
    origin = f"{p.scheme}://{p.netloc}"
    if "tribe-events" in html_lower or "the-events-calendar" in html_lower:
        cands += [origin + "/events/?ical=1", page_url.rstrip("/") + "/?ical=1"]
    if "squarespace" in html_lower:
        cands.append(page_url.split("?")[0] + "?format=ical")
    if p.netloc.endswith("meetup.com"):
        group = p.path.strip("/").split("/")[0]
        if group:
            cands.append(f"https://www.meetup.com/{group}/events/ical/")
    seen, out = set(), []
    for c in cands:
        if c not in seen:
            seen.add(c)
            out.append(c)
    return out[:8]


def platform_hints(html_lower, host):
    hints = []
    for key, label in [("tribe-events", "wp-events-calendar"), ("localist", "localist"),
                       ("trumba", "trumba"), ("squarespace", "squarespace"), ("wix.com", "wix"),
                       ("eventbrite", "eventbrite"), ("mindbodyonline", "mindbody"),
                       ("momence", "momence"), ("__next_data__", "nextjs"), ("drupal", "drupal"),
                       ("shopify", "shopify"), ("acuityscheduling", "acuity"), ("volunteerhub", "volunteerhub"),
                       ("galaxydigital", "galaxy-digital"), ("getgalaxy", "galaxy-digital")]:
        if key in html_lower:
            hints.append(label)
    if host.endswith("meetup.com"):
        hints.append("meetup")
    return hints


def probe_static(src):
    url = src["url"]
    rec = {**src, "method": "", "feed_url": "", "http_status": "", "final_url": "",
           "static_text_len": 0, "static_date_hits": 0, "static_near_hits": 0,
           "rendered_date_hits": "", "rendered_near_hits": "", "ics_events": "", "ics_upcoming": "",
           "jsonld_events": 0, "jsonld_upcoming": 0, "platform": "", "notes": ""}
    notes = []
    r = fetch(url)
    rec["http_status"] = r["status"]
    rec["final_url"] = r["url"]
    if r.get("error"):
        notes.append(r["error"])
    html = r["text"]
    html_lower = html.lower()
    soup = BeautifulSoup(html, "lxml") if html else BeautifulSoup("", "lxml")
    host = urlparse(r["url"]).netloc
    rec["platform"] = ",".join(platform_hints(html_lower, host))

    # 1. iCal
    best = None
    for cand in ics_candidates(r["url"], soup, html):
        res = check_ics(cand)
        if res and (best is None or res["upcoming"] > best["upcoming"]):
            best = res
    if best:
        rec["ics_events"], rec["ics_upcoming"] = best["events"], best["upcoming"]
        is_meetup = "meetup.com/" in best["feed_url"]
        is_calendar_service = any(k in best["feed_url"] for k in ("calendar.google.com", "teamup.com"))
        if best["events"] >= 2 or is_meetup or (is_calendar_service and best["events"] >= 1):
            rec["method"], rec["feed_url"] = "ical", best["feed_url"]
        else:
            notes.append("only a single-event calendar link, not a feed")

    # 2. JSON API
    if not rec["method"]:
        p = urlparse(r["url"])
        origin = f"{p.scheme}://{p.netloc}"
        api_cands = []
        if "tribe-events" in html_lower or "the-events-calendar" in html_lower:
            api_cands.append(origin + "/wp-json/tribe/events/v1/events?per_page=20")
        if "localist" in html_lower:
            api_cands.append(origin + "/api/2/events?pp=20")
        if "squarespace" in html_lower:
            api_cands.append(r["url"].split("?")[0] + "?format=json")
        for cand in api_cands:
            res = check_json_events(cand)
            if res:
                rec["method"], rec["feed_url"] = "api", res["feed_url"]
                notes.append(f"api returned {res['events']} events")
                break

    # 3. JSON-LD
    n_ld, up_ld = jsonld_events(soup) if html else (0, 0)
    rec["jsonld_events"], rec["jsonld_upcoming"] = n_ld, up_ld
    if not rec["method"] and n_ld > 0:
        rec["method"] = "jsonld"

    # 4. Events RSS
    if not rec["method"]:
        for tag in soup.find_all("link", rel="alternate", href=True):
            t = (tag.get("type") or "").lower()
            href = urljoin(r["url"], tag["href"])
            if ("rss" in t or "atom" in t) and ("event" in href.lower() or "calendar" in href.lower()):
                fr = fetch(href)
                if fr["status"] == 200 and ("<rss" in fr["text"][:500] or "<feed" in fr["text"][:500]):
                    rec["method"], rec["feed_url"] = "rss", href
                    break

    # 5. Plain HTML
    text = visible_text(html) if html else ""
    rec["static_text_len"] = len(text)
    rec["static_date_hits"], rec["static_near_hits"] = date_stats(text)
    if not rec["method"] and (rec["static_near_hits"] >= 2 or rec["static_date_hits"] >= 4):
        rec["method"] = "html"

    if "enable javascript" in text.lower() or len(text) < 400:
        notes.append("looks like a JavaScript shell")
    if r["status"] in (401, 403, 429, 503):
        notes.append(f"blocked or rate-limited ({r['status']})")

    rec["notes"] = "; ".join(notes)
    rec["_text"] = text
    return rec


def probe_browser(recs):
    """Render pages the static pass could not classify. Along the way, look for
    calendar feeds that only appear after JavaScript runs and for JSON data calls
    that carry the events, which are cheaper to read than the rendered page."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        for rec in recs:
            rec["notes"] = (rec["notes"] + "; playwright missing").strip("; ")
        return
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        ctx = browser.new_context(user_agent=HEADERS["User-Agent"], locale="en-US")
        for rec in recs:
            page = ctx.new_page()
            responses = []
            page.on("response", lambda resp: responses.append(resp))
            try:
                try:
                    page.goto(rec["url"], wait_until="networkidle", timeout=45000)
                except Exception:
                    page.goto(rec["url"], wait_until="load", timeout=45000)
                    page.wait_for_timeout(4000)
                text = page.inner_text("body")
                html = page.content()
            except Exception as e:
                rec["notes"] = (rec["notes"] + f"; browser error {type(e).__name__}").strip("; ")
                page.close()
                continue

            # JSON data calls made by the page
            best_xhr = None
            for resp in responses:
                try:
                    if resp.request.method != "GET" or "json" not in (resp.headers.get("content-type") or ""):
                        continue
                    body = resp.text()
                    if len(body) > 3_000_000:
                        continue
                    n = count_eventish(json.loads(body))
                    if n >= 2 and (best_xhr is None or n > best_xhr[1]):
                        best_xhr = (resp.url, n, body[:8000])
                except Exception:
                    continue
            page.close()

            d, n = date_stats(text)
            rec["rendered_date_hits"], rec["rendered_near_hits"] = d, n
            soup = BeautifulSoup(html, "lxml")
            n_ld, up_ld = jsonld_events(soup)
            if n_ld and not rec["jsonld_events"]:
                rec["jsonld_events"], rec["jsonld_upcoming"] = n_ld, up_ld

            # a) calendar feed that only shows up after rendering
            for cand in ics_candidates(rec["url"], soup, html) + gcal_ics_from_text(
                    " ".join(r.url for r in responses)):
                res = check_ics(cand)
                if res and (res["events"] >= 2 or ("calendar.google.com" in cand and res["events"] >= 1)):
                    rec["method"], rec["feed_url"] = "ical", cand
                    rec["ics_events"], rec["ics_upcoming"] = res["events"], res["upcoming"]
                    break
            if rec["method"]:
                rec["_text"] = text
                continue

            # b) JSON data call that also works without a browser
            if best_xhr:
                replay = check_json_events(best_xhr[0])
                if replay:
                    rec["method"], rec["feed_url"] = "xhr", best_xhr[0]
                    rec["notes"] = (rec["notes"] + f"; json feed with {best_xhr[1]} events").strip("; ")
                    rec["_text"] = best_xhr[2]
                    continue
                rec["notes"] = (rec["notes"] + f"; json feed needs the browser: {best_xhr[0][:150]}").strip("; ")

            # c) dates visible in the rendered page
            if n >= 2 or d >= 4 or n_ld or best_xhr:
                rec["method"] = "browser"
                rec["_text"] = text
        browser.close()


def probe_reader(recs):
    """Sites that block GitHub's servers: try the r.jina.ai reader instead."""
    for rec in recs:
        status, text = reader_fetch(rec["url"])
        d, n = date_stats(text)
        if status == 200 and (n >= 2 or d >= 4):
            rec["method"], rec["feed_url"] = "reader", "https://r.jina.ai/" + rec["url"]
            rec["_text"] = text
            rec["notes"] = (rec["notes"] + f"; reader found {d} dates").strip("; ")
        else:
            rec["notes"] = (rec["notes"] + f"; reader {status}, {d} dates").strip("; ")
        time.sleep(4)


def main():
    with open(ROOT / "sources.csv", newline="", encoding="utf-8") as f:
        sources = [row for row in csv.DictReader(f) if row.get("url")]
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=8) as ex:
        recs = list(ex.map(probe_static, sources))
    print(f"static pass: {len(recs)} sources in {time.time() - t0:.0f}s", flush=True)

    todo = [r for r in recs if not r["method"]]
    t1 = time.time()
    probe_browser(todo)
    print(f"browser pass: {len(todo)} sources in {time.time() - t1:.0f}s", flush=True)

    blocked = [r for r in recs if not r["method"] and (
        r["http_status"] in (0, 202, 403, 406, 429, 503) or "JavaScript shell" in r["notes"])]
    t2 = time.time()
    probe_reader(blocked)
    print(f"reader pass: {len(blocked)} sources in {time.time() - t2:.0f}s", flush=True)

    for r in recs:
        if not r["method"]:
            r["method"] = "none"

    SAMPLES.mkdir(exist_ok=True)
    for old in SAMPLES.glob("*.txt"):
        old.unlink()
    for r in recs:
        (SAMPLES / f"{slugify(r['name'])}.txt").write_text(
            f"{r['name']}\n{r['url']}\nmethod: {r['method']}\n\n{r.pop('_text', '')[:8000]}", encoding="utf-8")

    fields = ["name", "url", "category", "priority", "method", "feed_url", "http_status", "final_url",
              "static_text_len", "static_date_hits", "static_near_hits", "rendered_date_hits",
              "rendered_near_hits", "ics_events", "ics_upcoming", "jsonld_events", "jsonld_upcoming",
              "platform", "notes"]
    with open(ROOT / "probe_report.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(recs)
    (ROOT / "probe_report.json").write_text(
        json.dumps({"run_at": datetime.now(ZoneInfo("America/New_York")).isoformat(),
                    "sources": [{k: r.get(k) for k in fields} for r in recs]}, indent=1),
        encoding="utf-8")

    counts = {}
    for r in recs:
        counts[r["method"]] = counts.get(r["method"], 0) + 1
    print("methods:", json.dumps(counts, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
