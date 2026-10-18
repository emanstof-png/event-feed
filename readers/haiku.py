"""Shared: turn messy page/feed text into dated events with Claude Haiku.
Needs ANTHROPIC_API_KEY. Returns [] without it (so feeds still work)."""
import os, json, re
from .common import event, today

PROMPT = """Today is {today} (America/New_York). Below is text from the events page or feed of "{name}".
Extract every UPCOMING event (on or after today) that has a specific date. Ignore navigation, past events,
and items without a date. If a year is missing, assume the next occurrence on or after today.
Return ONLY a JSON array, each item: {{"date":"YYYY-MM-DD","time":"HH:MM" or "","title":"...","venue":"...","link":"absolute URL or ''","desc":"5 to 10 words saying what it is"}}.
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
            out.append(event(it["date"], it["title"], name, it.get("time", "") or "", it.get("venue", "") or "", it.get("link", "") or "", desc=it.get("desc", "") or ""))
    return out


def summarize(events, batch=40):
    """Give each event a 5-10 word 'desc' from its raw description. Needs ANTHROPIC_API_KEY;
    without it, trims the raw text to 80 chars."""
    key = os.environ.get("ANTHROPIC_API_KEY")
    todo = [e for e in events if e.get("desc") and len(e["desc"].split()) > 12]
    if not key:
        for e in events:
            e["desc"] = (e.get("desc") or "")[:80]
        return events
    import anthropic
    client = anthropic.Anthropic()
    for i in range(0, len(todo), batch):
        chunk = todo[i:i + batch]
        lines = "\n".join(f'{k}. {e["title"]} :: {e["desc"][:400]}' for k, e in enumerate(chunk))
        try:
            msg = client.messages.create(model=MODEL, max_tokens=4000, messages=[{"role": "user", "content":
                "For each numbered event, write a 5 to 10 word plain description of what it is (no dates, no org name). "
                "Return ONLY a JSON object mapping the number to the description.\n\n" + lines}])
            txt = msg.content[0].text
            m = re.search(r"\{.*\}", txt, re.S)
            d = json.loads(m.group(0)) if m else {}
            for k, e in enumerate(chunk):
                v = d.get(str(k))
                if v:
                    e["desc"] = str(v)[:120]
        except Exception:
            pass
    for e in events:
        e["desc"] = (e.get("desc") or "")[:120]
    return events
