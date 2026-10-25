#!/usr/bin/env python3
"""discover.py (SPEC_SPEED Phase 1, step 1). No secrets.

For every browser/stealth row in sources_methods.csv (or names passed as arguments), render the
page once with Playwright, listen to every network response (main page and iframes), and keep
JSON / ics / XML / JSONP responses over 500 bytes whose body contains date-like strings.
Each kept call is then replayed with a plain GET/POST (no cookies) to see if it works on its own.

Writes discover/<slug>.json (candidates, best first: url, method, headers, post_data, status,
date_count, replay_status, replay_ok, first 4000 chars of body) and discover_log.csv.
Haiku scouts read those files with briefs/SCOUT_DISCOVER.md. Cap: 60s per source."""
import asyncio, csv, json, re, sys, time
from pathlib import Path
from lists import current as _list
_L = _list()   # FEED_LIST=elite reads elite_methods.csv, writes elite_<log>.csv; sample files are per source either way

OUT = Path("discover"); OUT.mkdir(exist_ok=True)
CAP = 60
DATE_RE = re.compile(r"20\d\d-\d\d-\d\d|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.? \d{1,2},? 20\d\d|\b\d{1,2}/\d{1,2}/20\d\d|\b1[7-9]\d{8}\b")
SKIP_HOST = re.compile(r"google-analytics|googletagmanager|doubleclick|facebook|hotjar|segment|sentry|newrelic|clarity\.ms|fonts\.|recaptcha|hcaptcha|stripe|intercom|cookie|consent|onetrust|tiktok|pinterest|linkedin|twitter|cloudflareinsights|datadog")
KEEP_HDR = {"accept", "content-type", "x-requested-with", "referer", "origin", "authorization", "x-csrf-token", "x-api-key"}

def slug(n): return re.sub(r"[^a-z0-9]+", "-", n.lower()).strip("-")[:60]

def is_data(ct, body):
    ct = (ct or "").lower()
    b = body.lstrip()[:20]
    return ("json" in ct or "calendar" in ct or "xml" in ct or "javascript" in ct and b[:1] in "[{(" or
            b.startswith(("{", "[", "BEGIN:VCALENDAR", "<?xml")))

async def discover(browser, r):
    url = r["feed_url"] if r["feed_url"].startswith("http") else r["url"]
    cands, seen, err = [], set(), ""
    ctx = await browser.new_context(user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36",
                                    locale="en-US", viewport={"width": 1366, "height": 900})
    page = await ctx.new_page()

    async def on_resp(resp):
        try:
            req = resp.request
            u = resp.url
            if u in seen or SKIP_HOST.search(u) or req.resource_type in ("image", "font", "stylesheet", "media"):
                return
            seen.add(u)
            ct = resp.headers.get("content-type", "")
            body = (await resp.body()).decode("utf-8", "replace")
            if len(body) < 500 or not is_data(ct, body):
                return
            n = len(DATE_RE.findall(body))
            if n < 3:
                return
            hdrs = {k: v for k, v in (await req.all_headers()).items() if k.lower() in KEEP_HDR}
            cands.append({"url": u, "method": req.method, "headers": hdrs, "post_data": req.post_data,
                          "status": resp.status, "content_type": ct, "bytes": len(body), "date_count": n,
                          "body": body[:4000]})
        except Exception:
            pass

    page.on("response", lambda resp: asyncio.ensure_future(on_resp(resp)))
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        for _ in range(3):                          # let widgets load; scroll to trigger lazy calendars
            await page.wait_for_timeout(3000)
            await page.mouse.wheel(0, 2500)
        try:
            await page.wait_for_load_state("networkidle", timeout=8000)
        except Exception:
            pass
    except Exception as e:
        err = f"{type(e).__name__}: {e}"[:200]
    await asyncio.sleep(1)
    await ctx.close()
    return url, cands, err

def replay(c):
    """Plain request with only the kept headers, no cookies: does the call work on its own?"""
    import requests
    h = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36", **c["headers"]}
    try:
        if c["method"] == "POST":
            rr = requests.post(c["url"], data=c["post_data"], headers=h, timeout=20)
        else:
            rr = requests.get(c["url"], headers=h, timeout=20)
        c["replay_status"] = rr.status_code
        c["replay_ok"] = rr.status_code == 200 and len(DATE_RE.findall(rr.text)) >= 3
    except Exception as e:
        c["replay_status"], c["replay_ok"] = f"{type(e).__name__}", False

async def main():
    from playwright.async_api import async_playwright
    names = set(sys.argv[1:])
    rows = list(csv.DictReader(open(_L["csv"], newline="", encoding="utf-8")))
    targets = [r for r in rows if (r["name"] in names) if names] or [r for r in rows if r["method"] in ("browser", "stealth")]
    print(f"{len(targets)} sources, cap {CAP}s each", flush=True)
    log = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
        for r in targets:
            t0 = time.time()
            try:
                url, cands, err = await asyncio.wait_for(discover(browser, r), CAP)
            except asyncio.TimeoutError:
                url, cands, err = r["url"], [], f"cap {CAP}s"
            cands.sort(key=lambda c: -c["date_count"])
            cands = cands[:8]
            for c in cands:
                replay(c)
            secs = round(time.time() - t0, 1)
            (OUT / f"{slug(r['name'])}.json").write_text(json.dumps(
                {"row": r["row"], "name": r["name"], "page": url, "discovered": time.strftime("%Y-%m-%d %H:%MZ", time.gmtime()),
                 "error": err, "candidates": cands}, indent=1), encoding="utf-8")
            line = [r["row"], r["name"], url, len(cands), sum(1 for c in cands if c.get("replay_ok")), secs, err]
            log.append(line); print(line, flush=True)
        await browser.close()
    with open(_L["prefix"] + "discover_log.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["row", "name", "page", "candidates", "replay_ok", "seconds", "error"]); w.writerows(log)
    print("DONE", len(log), "sources,", sum(1 for l in log if l[3]), "with candidates,", sum(1 for l in log if l[4]), "replayable")

if __name__ == "__main__":
    asyncio.run(main())
