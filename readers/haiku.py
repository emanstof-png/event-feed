"""Shared: turn messy page/feed text into dated events with Claude Haiku.
Needs ANTHROPIC_API_KEY. Returns [] without it (so feeds still work)."""
import os, json, re
from .common import event, today

PROMPT = """Today is {today} (America/New_York). Below is text from the events page or feed of "{name}".
Extract every UPCOMING event (on or after today) that has a specific date. Ignore navigation, past events,
and items without a date. If a year is missing, assume the next occurrence on or after today.
Return ONLY a JSON array, each item: {{"date":"YYYY-MM-DD","time":"HH:MM" or "","title":"...","venue":"...","link":"absolute URL or ''"}}.
Base URL for relative links: {base}

TEXT:
{text}"""

def extract_events_from_text(text, name, base_url=""):
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key or not text.strip():
        return []
    import anthropic
    client = anthropic.Anthropic(api_key=key)
    msg = client.messages.create(model="claude-haiku-4-5", max_tokens=4000,
        messages=[{"role": "user", "content": PROMPT.format(today=today().isoformat(), name=name, base=base_url, text=text[:60000])}])
    raw = msg.content[0].text
    m = re.search(r"\[.*\]", raw, re.S)
    if not m: return []
    try: items = json.loads(m.group(0))
    except Exception: return []
    out = []
    for it in items:
        if re.match(r"^\d{4}-\d{2}-\d{2}$", str(it.get("date", ""))) and it.get("title"):
            out.append(event(it["date"], it["title"], name, it.get("time", "") or "", it.get("venue", "") or "", it.get("link", "") or ""))
    return out
