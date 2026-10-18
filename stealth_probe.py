#!/usr/bin/env python3
"""Experiment: can Scrapling's stealth browser read the sites that block
GitHub's servers? Runs only on sources the Probe saw as blocked (403/406/429).
Writes stealth_report.json and stealth_samples/<slug>.txt."""

import json
import sys
import time
from pathlib import Path

from probe import date_stats, slugify

ROOT = Path(__file__).parent
OUT = ROOT / "stealth_samples"


def page_text(page):
    for attr in ("get_all_text", "markdown"):
        fn = getattr(page, attr, None)
        if callable(fn):
            try:
                t = fn()
                if t:
                    return str(t), attr
            except Exception:
                pass
    body = getattr(page, "body", None) or getattr(page, "html_content", "")
    if isinstance(body, bytes):
        body = body.decode("utf-8", "replace")
    from probe import visible_text
    return visible_text(str(body)), "body"


def main():
    report = json.loads((ROOT / "probe_report.json").read_text())["sources"]
    targets = [s for s in report if s["http_status"] in (403, 406, 429)]
    print(f"{len(targets)} blocked sources", flush=True)

    from scrapling.fetchers import StealthySession

    results = []
    OUT.mkdir(exist_ok=True)
    with StealthySession(headless=True, solve_cloudflare=True, network_idle=True, timeout=45000) as session:
        for s in targets:
            t0 = time.time()
            rec = {"name": s["name"], "url": s["url"], "probe_method": s["method"]}
            try:
                page = session.fetch(s["url"])
                text, how = page_text(page)
                d, n = date_stats(text)
                rec.update(status=getattr(page, "status", None), text_len=len(text), date_hits=d,
                           near_hits=n, text_via=how, works=(n >= 2 or d >= 4))
                (OUT / f"{slugify(s['name'])}.txt").write_text(
                    f"{s['name']}\n{s['url']}\n\n{text[:8000]}", encoding="utf-8")
            except Exception as e:
                rec.update(error=f"{type(e).__name__}: {e}"[:300], works=False)
            rec["seconds"] = round(time.time() - t0, 1)
            print(json.dumps(rec), flush=True)
            results.append(rec)

    (ROOT / "stealth_report.json").write_text(json.dumps(results, indent=1), encoding="utf-8")
    print("works:", sum(r["works"] for r in results), "of", len(results))
    return 0


if __name__ == "__main__":
    sys.exit(main())
