"""Method: rss. Events RSS/Atom feed. Dates often live in the title or description, so
Haiku fills in dates for items that lack one (see readers/haiku.py)."""
import feedparser
from .common import event, in_window, dedupe
from .haiku import extract_events_from_text

def read(source, window_days=21):
    url = source.get("feed_url") or source["url"]
    feed = feedparser.parse(url)
    text = "\n\n".join(f"{e.get('title','')}\n{e.get('published','')}\n{e.get('summary','')}\n{e.get('link','')}"
                       for e in feed.entries[:80])
    evs = extract_events_from_text(text, source["name"])
    return dedupe([e for e in evs if in_window(e, window_days)])
