#!/usr/bin/env python3
"""Verify: pull real events from each feed / widget API the Probe found, and
test known calendar-widget endpoints for the sources still marked none.
Prints a JSON report: per source, how many upcoming events with titles came back."""

import json, re, sys, time
from datetime import datetime, timedelta
from urllib.parse import quote, urlparse
import requests
from probe import fetch, HEADERS, TODAY_ICS, count_eventish, reader_fetch, date_stats

TODAY = datetime.now()
IN3W = TODAY + timedelta(days=21)

def ics_events(url):
    r = fetch(url)
    r["text"] = r.get("text") or ""
    if r["status"] != 200 or "BEGIN:VEVENT" not in r["text"]: return None
    body = r["text"]
    out = []
    for block in body.split("BEGIN:VEVENT")[1:]:
        m = re.search(r"^DTSTART[^:\n]*:(\d{8})", block, re.M)
        t = re.search(r"^SUMMARY[^:\n]*:(.*)$", block, re.M)
        if m and t:
            out.append((m.group(1), t.group(1).strip()[:60]))
    up = [e for e in out if e[0] >= TODAY_ICS]
    return {"total": len(out), "upcoming": len(up), "sample": up[:3]}

def json_events(url, extra_headers=None):
    try:
        r = requests.get(url, headers={**HEADERS, **(extra_headers or {})}, timeout=30)
        data = r.json()
    except Exception as e:
        return {"error": f"{type(e).__name__}", "status": getattr(locals().get('r'), 'status_code', None), "head": (getattr(locals().get('r'), 'text', '') or '')[:200]}
    n = count_eventish(data)
    txt = json.dumps(data)[:600]
    return {"status": r.status_code, "eventish": n, "head": txt}

tests = {
 # bookstores on Bookmanager (Kramers, East City, Politics & Prose?, Lost City?)
 "Kramers": ("json", "https://api.bookmanager.com/customer/event/v2/list?_cb=1562584"),
 "East City Bookshop": ("json", "https://api.bookmanager.com/customer/event/v2/list?_cb=9900977"),
 # Bhakti Yoga via WellnessLiving
 "Bhakti Yoga DC": ("json", "https://www.wellnessliving.com/Wl/Event/EventList.json?.id-region=1&dl_start=2026-10-18&dl_end=2026-11-30&id_flag=1&is_backend=0&is_tab_all=1&k_business=145144"),
 # Mindbody widget
 "The Mindfulness Center": ("json", "https://widgets.mindbodyonline.com/widgets/schedules/68577199f8a.json?mobile=false&version=1"),
 # Rock Creek via Timely
 "Rock Creek Conservancy": ("json", "https://events.timely.fun/api/calendars/54713121/events?timezone=America/New_York&view=tile&start_date_utc=1792220400&per_page=50"),
 # Hollywood Ballroom keepandshare
 "Hollywood Ballroom": ("json", "https://www.keepandshare.com/calendar18/fns_asynch_api.php?r=getrange0.0716661"),
 # Georgetown IPPS livewhale json
 "Georgetown Institute of Politics and Public Service": ("json", "https://events.georgetown.edu/live/json/events/group/Institute%20of%20Politics%20and%20Public%20Service/max/20"),
 # Ann Kite / AU / Rock Creek 'events?cee=no' endpoints are squarespace-ish mpc; try Ann Kite ical
 "The Dance with Ann Kite": ("ics", "https://www.annkite.com/letgo?format=ical"),
 "Sun & Moon Yoga Studio": ("json", "https://www.sunandmoonstudio.com/?format=json"),
 "The Center for Mindful Living": ("json", "https://living-mindfully.org/?format=json"),
 "Solid State Books: Reading the City": ("json", "https://www.solidstatebooksdc.com/ssb-read-the-city-book-club?format=json"),
 "Data Community DC": ("json", "https://www.dc2.org/?format=json"),
 "DC Central Kitchen": ("ics", "https://dccentralkitchen.org/events/?ical=1"),
 "DC Central Kitchen api": ("json", "https://dccentralkitchen.org/wp-json/tribe/events/v1/events?per_page=20"),
 "Martha's Table": ("json", "https://volunteer.marthastable.org/api/v1/needs?per_page=20"),
 "Volunteer Alexandria": ("json", "https://www.volunteeralexandria.org/api/v1/needs?per_page=20"),
 "Capital Area Food Bank": ("json", "https://volunteer.capitalareafoodbank.org/api/v1/needs?per_page=20"),
 "Braver Angels DC Alliance": ("ics", "https://calendar.google.com/calendar/ical/c_699a2b8c681edb1f3cf7e85d3b9717529b4ccef15a8769cfca3a3f7023579fbb%40group.calendar.google.com/public/basic.ics"),
 "Game Kastle (College Park)": ("ics", "https://calendar.google.com/calendar/ical/800f6bde859b0593ad025d88a9aee4e33487a4840eeb918ee6b0ee1034bc8279%40group.calendar.google.com/public/basic.ics"),
 "Games & Comics Pair O' Dice (Fairfax)": ("ics", "https://calendar.google.com/calendar/ical/c_i992fmeebehi4bi15lbke0acvg%40group.calendar.google.com/public/basic.ics"),
 "Casey Trees": ("ics", "https://caseytrees.org/events/?ical=1"),
 "People's Book (Takoma Park)": ("ics", "https://peoplesbooktakoma.com/donotuse/?ical=1"),
 "Nova Labs": ("raw", "https://portal.nova-labs.org/events/RSS"),
 "Labyrinth Games & Puzzles": ("json", "https://www.labyrinthdc.com/events/calendar/?format=json"),
 "Interintellect": ("json", "https://interintellect.com/api/salon/public/all?grouped=true&direction=newer&isFirstLoad=true&includeSeries=true&tabType=all&limit=27"),
 "Food & Friends": ("json", "https://foodandfriends.org/volunteer/volunteer-with-us/jdata/"),
 "DC Rawhides": ("ics", "https://dcrawhides.com/event-calendar/?ical=1"),
 "DC Rawhides api": ("json", "https://dcrawhides.com/wp-json/tribe/events/v1/events?per_page=20"),
 "Ecstatic Dance DC": ("raw", "https://ecstaticdance.org/dance/ecstatic-dance-dc/"),
 "Fantom Comics": ("raw", "https://stores.comichub.com/fantom_comics/Events/All"),
 "Victory Comics": ("raw", "https://victorycomics.com/event-schedule"),
 "Break My Game": ("raw", "https://www.breakmygame.com/event-calendar"),
 "Eaton Wellness": ("json", "https://ev.hotelchamp.io//production/events"),
 "Baila DC (classes)": ("raw", "https://bailadc.com/classes"),
 "District Clay Center": ("raw", "https://www.districtclaycenter.com/events-calendar.html"),
 "WGIT DC": ("raw", "https://wgitdc.com/events/"),
 "Carpe Diem Arts": ("raw", "https://carpediemarts.org/events"),
 "Art of Living DC Center": ("raw", "https://dc.artofliving.org/events"),
 "Blueberry Gardens": ("raw", "https://www.blueberrygardens.org/classes"),
 "ONIMA Breathwork": ("raw", "https://onimabreathwork.com/events/"),
 "Chabad YP": ("raw", "https://www.jewishwashington.com/templates/articlecco_cdo/aid/5903412"),
 "LessWrong": ("json", "https://www.lesswrong.com/graphql?query=%7Bposts(input:%7Bterms:%7Bview:%22events%22,limit:30%7D%7D)%7Bresults%7Btitle%20startTime%20location%7D%7D%7D"),
 "Repair the World": ("raw", "https://werepair.org/events/"),
 "Goethe": ("raw", "https://www.goethe.de/ins/us/en/sta/wsh/ver.cfm"),
}

import traceback
report = {}
for name, (kind, url) in tests.items():
    t0 = time.time()
    try:
        if kind == "ics": res = ics_events(url)
        elif kind == "json": res = json_events(url)
        else:
            r = fetch(url); d, n = date_stats(r["text"])
            res = {"status": r["status"], "len": len(r["text"]), "dates": d, "near": n, "iframes": re.findall(r'<iframe[^>]+src="([^"]+)"', r["text"])[:3]}
    except BaseException as e:
        res = {"error": f"{type(e).__name__}: {e}"[:120], "tb": traceback.format_exc()[-300:]}
    res["url"] = url; res["sec"] = round(time.time()-t0,1)
    report[name] = res
    print(name, json.dumps(res)[:400], flush=True)
json.dump(report, open("verify_report.json","w"), indent=1)
print("DONE", len(report))
