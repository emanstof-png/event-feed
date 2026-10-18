"""Method: browser / stealth. Renders the page with Scrapling's stealth browser (defeats
JS-only pages, widgets, most bot blocks), reads iframes, pages forward on month grids,
then hands the text to Haiku. Slowest reader; use only when the sheet says so."""
from .common import event, in_window, dedupe
from .haiku import extract_events_from_text

def read(source, window_days=21):
    from scrapling.fetchers import StealthySession
    texts = []
    with StealthySession(headless=True, solve_cloudflare=True, network_idle=True, timeout=60000) as s:
        page = s.fetch(source["url"])
        texts.append(page.get_all_text())
        # iframes with real src
        for src in page.css("iframe::attr(src)").getall()[:4]:
            if src.startswith("http"):
                try: texts.append(s.fetch(src).get_all_text())
                except Exception: pass
        # month grids: click "next" once to cover the window
        try:
            nxt = page.css('a[aria-label*="next" i], button[aria-label*="next" i], a[title*="next" i], .fc-next-button, a.next')
            if nxt and hasattr(page, "click"):
                page.click(nxt[0]); texts.append(page.get_all_text())
        except Exception:
            pass
    text = "\n\n----\n\n".join(t for t in texts if t)[:60000]
    return dedupe([e for e in extract_events_from_text(text, source["name"], base_url=source["url"]) if in_window(e, window_days)])
