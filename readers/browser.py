"""Method: browser / stealth. Renders the page with Scrapling's stealth browser (defeats
JS-only pages, widgets, most bot blocks), reads iframes (src and srcdoc), pages forward on
month grids, then hands the text to Haiku. Slowest reader; use only when the sheet says so.

render_text(source) returns the text and a small report without calling Haiku, so a job
with no API key can still prove what the browser sees (render_test.py)."""
import re
from .common import event, in_window, dedupe
from .haiku import extract_events_from_text


def _html_text(html):
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "lxml")
        for t in soup(["script", "style", "noscript"]):
            t.decompose()
        return re.sub(r"\n{3,}", "\n\n", soup.get_text("\n"))
    except Exception:
        return re.sub(r"<[^>]+>", " ", html)


def render_text(source, timeout_ms=60000):
    """Returns (text, report). report: status, chars, iframes, srcdoc, clicked_next, error."""
    from scrapling.fetchers import StealthySession
    rep = {"status": None, "chars": 0, "iframes": 0, "srcdoc": 0, "clicked_next": False, "error": ""}
    texts = []
    try:
        with StealthySession(headless=True, solve_cloudflare=True, network_idle=True, timeout=timeout_ms) as s:
            page = s.fetch(source["url"])
            rep["status"] = getattr(page, "status", None)
            texts.append(page.get_all_text())
            for src in page.css("iframe::attr(src)").getall()[:4]:
                if src.startswith("http"):
                    try:
                        texts.append(s.fetch(src).get_all_text()); rep["iframes"] += 1
                    except Exception:
                        pass
            for doc in page.css("iframe::attr(srcdoc)").getall()[:4]:
                if doc and len(doc) > 50:
                    texts.append(_html_text(doc)); rep["srcdoc"] += 1
            try:
                nxt = page.css('a[aria-label*="next" i], button[aria-label*="next" i], a[title*="next" i], .fc-next-button, a.next')
                if nxt and hasattr(page, "click"):
                    page.click(nxt[0]); texts.append(page.get_all_text()); rep["clicked_next"] = True
            except Exception:
                pass
    except Exception as e:
        rep["error"] = f"{type(e).__name__}: {e}"[:300]
    text = "\n\n----\n\n".join(t for t in texts if t)[:60000]
    rep["chars"] = len(text)
    return text, rep


def read(source, window_days=21):
    text, rep = render_text(source)
    if rep["error"] and not text:
        raise RuntimeError(rep["error"])
    return dedupe([e for e in extract_events_from_text(text, source["name"], base_url=source["url"]) if in_window(e, window_days)])
