"""Method: browser / stealth. Renders the page with Scrapling's stealth browser (defeats
JS-only pages, widgets, most bot blocks), reads every iframe (src and srcdoc) from the same
render, pages forward once on month grids, then hands the text to Haiku. Slowest reader.

Speed rules (SPEC_SPEED Phase 2, Oct 24):
- ONE browser session for the whole run, owned by one worker thread (Playwright's sync API is
  bound to the thread that started it). Every caller, including fetch.py's fallbacks from the
  parallel fast readers, queues here and waits at most CAP seconds.
- No network_idle. After load, wait until the text stops growing (1.5s steady, 2.5s to 12s).
- solve_cloudflare only when the first render is a challenge page; those pages get a second 45s.

render_text(source) returns the text and a small report without calling Haiku, so a job
with no API key can still prove what the browser sees (render_test.py)."""
import queue, re, threading, time
from concurrent.futures import Future, TimeoutError as FutTimeout
from .common import in_window, dedupe

CAP = 45          # seconds per source, hard
SETTLE_MS = 12000 # after load: wait for the text to stop growing, at most this long
MIN_MS = 2500     # ...but never less than this
NAV_MS = 30000    # page navigation timeout
_CHALLENGE = re.compile(r"Just a moment|Verify you are human|Checking your browser|cf-chl|Attention Required|Performing security verification|verifies you are not a bot", re.I)
_NEXT = 'a[aria-label*="next" i], button[aria-label*="next" i], a[title*="next" i], .fc-next-button, a.next'

import os
_EXE = {"executable_path": os.environ["BROWSER_EXE"]} if os.environ.get("BROWSER_EXE") else {}   # local tests only
_q, _thread, _lock = queue.Queue(), None, threading.Lock()


def _settle(page):
    """Wait until the page and its frames stop growing: text length unchanged for 1.5s, at least
    MIN_MS after load, at most SETTLE_MS. Widgets fill in after load; a date in the header is not
    proof the events arrived (Oct 24: Keep&Share, NMWA, Sixth & I read half-empty)."""
    def size():
        n = 0
        for fr in page.frames[:5]:
            try:
                n += fr.evaluate("() => document.body ? document.body.innerText.length : 0")
            except Exception:
                pass
        return n
    t0, last, stable = time.time(), -1, 0
    while (time.time() - t0) * 1000 < SETTLE_MS:
        page.wait_for_timeout(500)
        n = size()
        stable = stable + 1 if n == last else 0
        last = n
        if stable >= 3 and (time.time() - t0) * 1000 >= MIN_MS:
            return


def _html_text(html):
    """All text in the HTML, hidden tabs and collapsed lists included (innerText drops them)."""
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "lxml")
        for t in soup(["script", "style", "noscript"]):
            t.decompose()
        return soup.get_text("\n")
    except Exception:
        return re.sub(r"<[^>]+>", " ", html)


def _collect(rep, texts, seen):
    """page_action: wait for content, scroll once (lazy lists and iframes), read every loaded frame,
    click 'next' once. The main page's own HTML is read from the response afterwards."""
    def frames():
        for fr in page_ref[0].frames[1:6]:
            try:
                t = _html_text(fr.content())
                if t and len(t.strip()) > 20:
                    texts.append(t); seen.add(fr.url)
                    rep["iframes" if fr.url.startswith("http") else "srcdoc"] += 1
            except Exception:
                pass
    page_ref = [None]
    def act(page):
        page_ref[0] = page
        _settle(page)
        try:
            page.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(1500)
        except Exception:
            pass
        try:
            texts.insert(0, _html_text(page.content())); seen.add("main")
        except Exception:
            pass
        frames()
        try:
            nxt = page.locator(_NEXT).first
            if nxt.count():
                nxt.click(timeout=3000)
                _settle(page)
                rep["clicked_next"] = True
                texts.append(_html_text(page.content()))
                frames()
        except Exception:
            pass
        return page
    return act


def _render(session, source):
    rep = {"status": None, "chars": 0, "iframes": 0, "srcdoc": 0, "clicked_next": False, "error": "", "cloudflare": False}
    t0 = time.time()
    def once(cf):
        texts, seen = [], set()
        page = session.fetch(source["url"], network_idle=False, wait=0, timeout=NAV_MS, solve_cloudflare=cf,
                             page_action=_collect(rep, texts, seen))
        rep["status"] = getattr(page, "status", None)
        if "main" not in seen:
            texts.insert(0, page.get_all_text())
        # iframes that never loaded in place (lazy, cross-origin): open them directly, as before Oct 24
        for src in page.css("iframe::attr(src)").getall()[:4]:
            if src.startswith("http") and src not in seen and time.time() - t0 < CAP - 15:
                try:
                    texts.append(session.fetch(src, network_idle=False, wait=0, timeout=15000,
                                               page_action=lambda p: (_settle(p), p)[1]).get_all_text())
                    rep["iframes"] += 1
                except Exception:
                    pass
        return texts
    try:
        texts = once(False)
        if _CHALLENGE.search(" ".join(texts)[:3000]):
            rep.update(cloudflare=True, iframes=0, srcdoc=0)
            source["_challenge"] = True   # tells render_text to allow a second CAP for the solve
            texts = once(True)
    except Exception as e:
        texts = []
        rep["error"] = f"{type(e).__name__}: {e}"[:300]
    text = re.sub(r"\n\s*\n+", "\n\n", "\n\n----\n\n".join(t for t in texts if t))[:60000]
    rep["chars"] = len(text)
    return text, rep


def _worker():
    session = None
    while True:
        source, fut = _q.get()
        if not fut.set_running_or_notify_cancel():
            continue
        try:
            if session is None:
                from scrapling.fetchers import StealthySession   # inside try: a missing browser fails the source, not the thread
                session = StealthySession(headless=True, timeout=NAV_MS, network_idle=False, retries=1, **_EXE)
                session.start()
            fut.set_result(_render(session, source))
        except Exception as e:
            fut.set_exception(e)
            try:
                session.close()
            except Exception:
                pass
            session = None   # next source starts a fresh browser


def render_text(source, cap=CAP):
    """Returns (text, report). Never waits more than cap seconds."""
    global _thread
    with _lock:
        if _thread is None or not _thread.is_alive():
            _thread = threading.Thread(target=_worker, daemon=True, name="browser")
            _thread.start()
    fut = Future()
    t0 = time.time()
    _q.put((source, fut))
    # time spent queued behind other sources does not count against this source's cap
    while not fut.running() and not fut.done() and time.time() - t0 < 600:
        time.sleep(0.2)
    try:
        try:
            return fut.result(timeout=cap)
        except FutTimeout:
            if not source.get("_challenge"):
                raise
            return fut.result(timeout=cap)   # Cloudflare challenge pages only: one more CAP (Art House 7 needs ~60s)
    except FutTimeout:
        fut.cancel()
        return "", {"status": None, "chars": 0, "iframes": 0, "srcdoc": 0, "clicked_next": False,
                    "error": f"cap {cap}s", "cloudflare": False}


def read(source, window_days=21):
    from .haiku import extract_events_from_text
    text, rep = render_text(source)
    if rep["error"] and not text:
        raise RuntimeError(rep["error"])
    return dedupe([e for e in extract_events_from_text(text, source["name"], base_url=source["url"]) if in_window(e, window_days)])
