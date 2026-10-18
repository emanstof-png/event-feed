"""Method: recurring. The org publishes a rule, not dates. The rule lives in the sheet's
Feed URL column as text, e.g.:
  weekly; thu; 20:45; Edgewood Arts Center
  monthly; 1,3 thu; 19:00; La Cosecha           (1st and 3rd Thursdays)
  monthly; 2 sat; 18:30; venue                  (2nd Saturday)
  weekly; sun; 14:00-17:00; Dance Place
"""
from datetime import timedelta
from .common import event, window

DAYS = {"mon":0,"tue":1,"wed":2,"thu":3,"fri":4,"sat":5,"sun":6}

def read(source, window_days=21):
    rule = (source.get("feed_url") or source.get("rule") or "").strip()
    if not rule: return []
    parts = [p.strip() for p in rule.split(";")]
    kind, days_s, time_s = parts[0].lower(), parts[1].lower(), parts[2] if len(parts) > 2 else ""
    venue = parts[3] if len(parts) > 3 else ""
    title = parts[4] if len(parts) > 4 else f"{source['name']} (regular)"
    lo, hi = window(window_days)
    out = []
    if kind.startswith("weekly"):
        for d in days_s.replace(",", " ").split():
            wd = DAYS[d[:3]]
            cur = lo + timedelta((wd - lo.weekday()) % 7)
            while cur <= hi:
                out.append(event(cur.isoformat(), title, source["name"], time_s.split("-")[0], venue, source["url"])); cur += timedelta(7)
    elif kind.startswith("monthly"):
        ords, wd = days_s.rsplit(" ", 1); wd = DAYS[wd[:3]]
        ords = [int(x) for x in ords.replace(",", " ").split()]
        cur = lo
        while cur <= hi:
            if cur.weekday() == wd and ((cur.day - 1) // 7 + 1) in ords:
                out.append(event(cur.isoformat(), title, source["name"], time_s.split("-")[0], venue, source["url"]))
            cur += timedelta(1)
    return out
