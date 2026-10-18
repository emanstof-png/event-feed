# Playbook: how every source is read

One row per source. Method names the module in `readers/`. Feed URL is that module's input. This table is mirrored in the Sources tab (columns I, J, N) and generated from the same data.

| # | Source | Method | Reader | Feed URL / rule | How we know |
|---|---|---|---|---|---|
| 2 | GatherDC | ical | `readers/ical.py` | `https://gatherdc.org/?post_type=tribe_events&ical=1&eventDisplay=list` | WordPress Events Calendar; ?ical=1 feed, 33 upcoming. Page also fine. |
| 3 | EntryPointDC (Edlavitch DCJCC) | ical | `readers/ical.py` | `https://www.edcjcc.org/events/?ical=1` | WordPress ?ical=1 feed, 31 upcoming. |
| 4 | Moishe House DC (Columbia Heights) | html | `readers/html.py` |  | 3 dated on house page; 'Load More' hides others. Haiku reads page text. |
| 5 | ConnectJew | api | `readers/api.py` | `https://connectjew.org/api/v1/events?sort_by=date_asc&limit=50` | Page says 'No events found' but its own API returns 20 events. Read the API. |
| 6 | Sixth & I | stealth | `readers/browser.py` |  | Blocks plain requests (403). Stealth browser reads it: 13 upcoming. Server-rendered once loaded. |
| 7 | 2239 (Washington Hebrew Congregation) | stealth | `readers/browser.py` |  | Blocks plain requests. Main WHC calendar has 24; none tagged 2239 this month. Read whole calendar, filter titles for 2239/Metro Minyan. |
| 8 | Reva (Adas Israel) | stealth | `readers/browser.py` |  | Blocks plain requests (406). Stealth reads ~15 dated gatherings on /reva. |
| 9 | Chabad Young Professionals DC | browser | `readers/browser.py` |  | yjpdc.org lists events as '10.21' with no year; ticket buttons have no URLs until drop. Browser + Haiku with year inference; verify. |
| 10 | Next Gen (Jewish Federation of Greater Washington) | ical | `readers/ical.py` | `https://www.shalomdc.org/all-events/?ical=1` | WordPress ?ical=1, 33 upcoming (whole Federation calendar). Also community calendar page. |
| 11 | Repair the World | none | `(skipped)` |  | Volunteer list has no DC entries. Confirmed empty Oct 17. |
| 12 | Bhakti Yoga DC | recurring | `readers/recurring.py` | `weekly; thu; 18:45; Bhakti Yoga DC; Satsang` | No dated list; WellnessLiving widget empty. Satsang every Thursday 6:45pm. Elevate Kirtan 2nd Sat monthly from Jan 2027 (add a second rule then). |
| 13 | Ecstatic Dance DC | recurring | `readers/recurring.py` | `weekly; thu; 20:45; Edgewood Arts Center; Ecstatic Dance DC` | No dated list anywhere. Weekly Thursday 8:45-10:30pm. |
| 14 | Eaton Wellness | browser | `readers/browser.py` | `https://www.eatonworkshop.com/en-us/events-calendar/` | Calendar page is JS; Eventbrite organizer eventbrite.com/o/eaton-dc-17606335636 shows no cards. Browser the calendar page; if still empty, mark empty. |
| 15 | Soul Fire Experiences / Ecstatic Dance Arlington | browser | `readers/browser.py` |  | Ticket page is one event, JS-only (theticketing.co). Browser reads the page; monthly Saturday afternoons. |
| 16 | The Dance with Ann Kite | html | `readers/html.py` |  | tickets.annkite.com/events/annkitecom/1994688/select-date lists Fridays with dates. Haiku reads. |
| 17 | Sun & Moon Yoga Studio | html | `readers/html.py` |  | /workshops is server-rendered, 9 dated. Haiku reads. |
| 18 | Flow Yoga Center | html | `readers/html.py` |  | /cathedral (Yoga at the Cathedral series) lists 10 dated. /schedule has none. Haiku reads. |
| 19 | Kadampa Meditation Center DC | html | `readers/html.py` |  | /calendar is server-rendered (Wix), 12 dated. Haiku reads. |
| 20 | Yoga District | browser | `readers/browser.py` |  | Only 2 dated on homepage; rest in Mindbody/HealCode widget (/workshops). Browser + Haiku. |
| 21 | National Museum of Women in the Arts | browser | `readers/browser.py` |  | /whats-on/calendar/ is JS-rendered. Browser + Haiku. Per-event ICS at nmwa.org/feed/export-event/?id=N if needed. |
| 22 | Authentic Relating DC | ical | `readers/ical.py` | `https://www.meetup.com/authentic-relating-dc/events/ical/` | Meetup iCal, 4-7 upcoming. |
| 23 | Interfusion Festival | none | `(skipped)` |  | One festival Jan 14-18 2027; sessions on sched.com. Not a calendar. Add the festival by hand if wanted. |
| 24 | Awarehouse | browser | `readers/browser.py` | `https://www.awarehousedc.com/schedule` | /events shows only past; booking calendar /schedule is Mariana Tek, JS-only. Browser + Haiku. |
| 25 | DC Contact Improv | recurring | `readers/recurring.py` | `weekly; sun; 14:00-17:00; Dance Place; Sunday Jam (1st Sunday = Underscore)` | Weekly Sunday 2-5pm at Dance Place; plus dated studio jams on /other/events (html fallback). |
| 26 | ONIMA Breathwork | browser | `readers/browser.py` | `https://calendly.com/onimabreathwork` | Sessions booked via Calendly, client-rendered. Browser + Haiku; if empty, mark empty. |
| 27 | Blueberry Gardens Healing Center | browser | `readers/browser.py` | `https://www.blueberrygardens.org/calendar.php` | Google Calendar embed on /calendar.php. Browser once to read the calendar ID from the iframe src, then switch to ical with calendar.google.com/calendar/ical/<id>/public/basic.ics. |
| 28 | Art of Living DC Center (events) | browser | `readers/browser.py` |  | members.us.artofliving.org is a JS shell ('Loading...'). Browser + Haiku. |
| 29 | Insight Meditation Community of Washington (IMCW) | browser | `readers/browser.py` | `https://imcw.org/events/` | Page JS-rendered via eventagent.ai; browser pass found 17 dates. Browser + Haiku. |
| 30 | The Center for Mindful Living | recurring | `readers/recurring.py` | `weekly; sat; 10:30; Center for Mindful Living; In-Person Living Dharma Circle` | Weekly sits, no dated list. Sat 10:30 in-person circle is the social one; other sits are online. |
| 31 | The Mindfulness Center | none | `(skipped)` |  | Zoom classes only, booking via Mindbody studioid=8687. Not in-person social. Drop or mark empty. |
| 32 | Satchidananda Ashram-Yogaville | ical | `readers/ical.py` | `https://www.yogaville.org/all-events/?ical=1` | WordPress ?ical=1, 9+ upcoming; programs calendar has 29 dated. |
| 33 | Georgetown University (university-wide) | api | `readers/api.py` | `https://events.georgetown.edu/live/json/events/` | LiveWhale. Try /live/json/events/ (all groups) or /live/ical/events; browser fallback found 6 dates. |
| 34 | Georgetown School of Foreign Service | api | `readers/api.py` | `https://events.georgetown.edu/live/json/events/group/School%20of%20Foreign%20Service` | LiveWhale JSON by group name; browser fallback. |
| 35 | Georgetown Institute of Politics and Public Service | none | `(skipped)` |  | No upcoming list exists; only a past archive. Google Calendar subscribe link on politics.georgetown.edu (cid=...) could become an ical row once the ID is read in a browser. |
| 36 | Georgetown Department of Government | none | `(skipped)` |  | Dept pages stale; points to guevents.georgetown.edu. Covered by the university-wide row. |
| 37 | George Washington University (university-wide) | api | `readers/api.py` | `https://calendar.gwu.edu/api/2/events?days=21&pp=100` | Localist. /api/2/events is anonymous and documented. The 1.ics feed is truncated and stale; do not use. |
| 38 | GW Elliott School of International Affairs | api | `readers/api.py` | `https://calendar.gwu.edu/elliott/api/2/events?days=21&pp=100` | Localist sub-calendar; iCal calendar.gwu.edu/elliott/calendar/1.ics also exists. |
| 39 | American University (university-wide) | stealth | `readers/browser.py` |  | Blocks plain requests (403). Stealth reads it; server-rendered list. Per-event .ics only. |
| 40 | American University College of Arts and Sciences | stealth | `readers/browser.py` |  | Blocks plain requests. Stealth reads 10 dated. |
| 41 | University of Maryland, College Park | api | `readers/api.py` | `https://calendar.umd.edu/api/2/events?days=21&pp=100` | Localist. API anonymous. HTML category pages are JS-paged; API is better. |
| 42 | Johns Hopkins Bloomberg Center DC | stealth | `readers/browser.py` |  | Blocks plain requests (403). Stealth reads 16 dated plus Load More. |
| 43 | Japan Information & Culture Center (Embassy of Japan) | stealth | `readers/browser.py` |  | Blocks plain requests. Stealth reads it; only 1 upcoming right now. |
| 44 | Goethe-Institut Washington | human | `(Eric's Chrome)` |  | Blocks even the stealth browser (403). Eric's Chrome on Sunday, or skip. 1 upcoming via scout. |
| 45 | Alliance Francaise of Washington DC | html | `readers/html.py` |  | Server-rendered, 3 dated; tickets on Eventbrite. Haiku reads. |
| 46 | Italian Cultural Institute of Washington | html | `readers/html.py` |  | Server-rendered, 4 listed. Haiku reads. |
| 47 | Austrian Cultural Forum Washington | api | `readers/api.py` | `https://www.acfdc.org/events?format=json` | Squarespace collection JSON, 4 upcoming. |
| 48 | Mexican Cultural Institute | none | `(skipped)` |  | Calendar widget says '0 Events loaded'; blog stale. 1 item (Oct 31) only on Instagram. Mark thin/empty; revisit. |
| 49 | La Maison Francaise (Embassy of France) | ical | `readers/ical.py` | `https://media.franceintheus.org/events/?ical=1` | WordPress ?ical=1, 16 upcoming. |
| 50 | SPAIN arts & culture (Washington) | rss | `readers/rss.py` | `https://www.spainculture.us/city/washington-dc/feed/` | RSS feed; html page also readable (4 dated). |
| 51 | Korean Cultural Center Washington | none | `(skipped)` |  | Site, board, and own Eventbrite all end in 2025. Confirmed empty Oct 17. |
| 52 | Embassy of the Czech Republic (cultural events) | html | `readers/html.py` |  | Server-rendered, 10 dated. RSS at mzv.gov.cz/washington/en/rss.html is site-wide. Haiku reads. |
| 53 | Socrates Cafe Rockville | ical | `readers/ical.py` | `https://www.meetup.com/socrates-cafe-rockville/events/ical/` | Meetup iCal, confirmed valid, 10 upcoming. |
| 54 | Practical Philosophy Club (Washington DC) | ical | `readers/ical.py` | `https://www.meetup.com/practical-philosophy-club-washington-dc/events/ical/` | Meetup iCal, 19 upcoming; weekly Wed 7:30 Tryst. |
| 55 | Effective Altruism DC | ical | `readers/ical.py` | `https://api.luma.com/ics/get?entity=calendar&id=cal-GTJhC5OzDHfqInR` | Luma calendar ICS. Had only past events Oct 17; keep, it fills when they post. |
| 56 | LessWrong community events | none | `(skipped)` |  | DC group has 0 upcoming; site is a global map. Drop. |
| 57 | Interintellect | xhr | `readers/api.py` | `https://interintellect.com/api/salon/public/all?grouped=true&direction=newer&isFirstLoad=true&includeSeries=true&tabType=all&limit=100` | Hidden JSON API returns 119 salons (mostly online). Haiku filters to in-person DC. |
| 58 | Braver Angels DC Alliance | ical | `readers/ical.py` | `https://calendar.google.com/calendar/ical/c_699a2b8c681edb1f3cf7e85d3b9717529b4ccef15a8769cfca3a3f7023579fbb%40group.calendar.google.com/public/basic.ics` | Google Calendar behind the site; public ICS, 8 upcoming. |
| 59 | Profs and Pints (Washington DC) | ical | `readers/ical.py` | `https://www.meetup.com/Profs-and-Pints-Meetup/events/ical/` | Org page has no dates; its Meetup has 13. Also inffuse JSON feed exists (500 events, all cities). |
| 60 | Hill Center DC | html | `readers/html.py` |  | iCal feed is STALE (May 2026). Read the HTML calendar page: 31 items. Haiku reads. |
| 61 | Brookings Institution | html | `readers/html.py` |  | Server-rendered table, 9 upcoming. Haiku reads. Many online; Haiku notes format. |
| 62 | CSIS | html | `readers/html.py` |  | Server-rendered, 6 upcoming. Haiku reads. |
| 63 | Carnegie Endowment for International Peace | html | `readers/html.py` |  | Server-rendered, 6 upcoming, not DC-filtered. Haiku reads and drops non-DC. |
| 64 | Atlantic Council | html | `readers/html.py` |  | 4 on first load, Load More for rest. Haiku reads first page. |
| 65 | Stimson Center | html | `readers/html.py` |  | Server-rendered, 8 upcoming. Haiku reads. |
| 66 | New America | html | `readers/html.py` |  | Server-rendered, 10 upcoming, mostly online. Haiku reads. |
| 67 | CNAS | html | `readers/html.py` |  | Server-rendered; only 2 upcoming exist. Haiku reads. |
| 68 | Cato Institute | html | `readers/html.py` |  | Server-rendered, 19 upcoming. Haiku reads. |
| 69 | American Enterprise Institute | stealth | `readers/browser.py` |  | Blocks plain requests (403). Stealth reads 9 upcoming. |
| 70 | Hudson Institute | html | `readers/html.py` |  | Server-rendered, 10 upcoming. Haiku reads; drop invite-only. |
| 71 | DC Policy Events (aggregator) | api | `readers/api.py` | `https://dcpolicyevents.com/api/events` | JSON feed confirmed, 113 events across 119 think tanks. Overlaps the individual think-tank rows; de-dupe handles it. |
| 72 | Politics and Prose | stealth | `readers/browser.py` |  | Blocks plain requests (403). Stealth reads ~23 upcoming in October. |
| 73 | Lost City Books | stealth | `readers/browser.py` |  | Blocks plain requests (403). Stealth reads 7+ upcoming. |
| 74 | Kramers | browser | `readers/browser.py` |  | JS-only; Bookmanager API needs a session token the page sets. Browser + Haiku. |
| 75 | East City Bookshop | browser | `readers/browser.py` |  | Same Bookmanager gate as Kramers. Browser + Haiku. |
| 76 | People's Book (Takoma Park) | api | `readers/api.py` | `https://peoplesbooktakoma.com/wp-json/tribe/events/v1/events?per_page=50&start_date={start}` | WordPress Events API live; first page returned past events, so pass start_date. '/donotuse/' paths are odd; verify output. |
| 77 | Loyalty Bookstores (book clubs) | html | `readers/html.py` |  | Server-rendered, 20+ club meetings. Haiku reads; years not printed, infer. |
| 78 | Solid State Books: Reading the City | html | `readers/html.py` |  | /events is server-rendered, 14 upcoming. Haiku reads. |
| 79 | Folger Shakespeare Library | xhr | `readers/api.py` | `https://www.folger.edu/admin/wp-admin/admin-ajax.php?action=basethemeCalendarRequest&start={start}T00:00:00Z&end={end}T23:59:59Z` | Hidden admin-ajax JSON, 33 events; titles are HTML snippets, Haiku cleans. |
| 80 | The Writer's Center (Bethesda) | stealth | `readers/browser.py` |  | Rate-limits plain requests (429). Stealth reads 17 dated. |
| 81 | DC Public Library: DC Reads | browser | `readers/browser.py` | `https://dclibrary.libnet.info/events` | RSS has no per-item dates. libnet events page is JS; browser + Haiku. Low priority. |
| 82 | DC Central Kitchen | html | `readers/html.py` | `https://dccentralkitchen.org/register` | Gleaning table on /register has dates; regular shifts have no dates (daily 9am, weekday 6-8pm). Haiku reads table; add a recurring rule for shifts if wanted. |
| 83 | Food & Friends | xhr | `readers/api.py` | `https://foodandfriends.org/volunteer/volunteer-with-us/jdata/` | Hidden JSON (40 items) found by the browser pass. Haiku reads. |
| 84 | Martha's Table | browser | `readers/browser.py` |  | Galaxy Digital; shifts visible without login (Eric verified) but only after JS. Browser + Haiku; page forward one month. |
| 85 | SOME (So Others Might Eat) | browser | `readers/browser.py` | `https://some.volunteerportal.org/` | Portal errors on plain fetch. Browser; if shifts need login, mark empty. 2 org events on some.org/get-involved/events/. |
| 86 | Volunteer Arlington | html | `readers/html.py` |  | Galaxy Digital but the calendar page rendered 8 dates to plain fetch. Haiku reads; browser fallback. |
| 87 | Volunteer Alexandria | browser | `readers/browser.py` | `https://www.volunteeralexandria.org/calendar` | Shift calendar is JS; partner-events page is galas. Browser + Haiku on /calendar. |
| 88 | Rock Creek Conservancy | browser | `readers/browser.py` |  | Timely widget; its API call only works from inside the page. Browser + Haiku. |
| 89 | Casey Trees | ical | `readers/ical.py` | `https://caseytrees.org/events/?ical=1` | WordPress ?ical=1, confirmed, 5 future. |
| 90 | Anacostia Watershed Society | api | `readers/api.py` | `https://www.anacostiaws.org/wp-json/tribe/events/v1/events?per_page=50` | WordPress Events API, confirmed. |
| 91 | Capital Area Food Bank | browser | `readers/browser.py` | `https://volunteer.capitalareafoodbank.org/calendar` | Galaxy Digital; every fetch view shows 0 and 'All Opportunities' is a dead link. Browser; if still 0, mark empty. |
| 92 | HacDC | ical | `readers/ical.py` | `https://www.meetup.com/hac-dc/events/ical/` | Meetup iCal confirmed, 25 upcoming. |
| 93 | Nova Labs | rss | `readers/rss.py` | `https://portal.nova-labs.org/events/RSS` | RSS confirmed, ~170 in 3 weeks. Haiku parses dates from titles/descriptions. |
| 94 | Data Science DC | ical | `readers/ical.py` | `https://www.meetup.com/data-science-dc/events/ical/` | Meetup iCal; 0 upcoming right now. Keep, fills when they post. |
| 95 | Data Community DC | none | `(skipped)` |  | Hub page; its groups are separate rows or Luma luma.com/DC2 (undated). Drop or add Luma ICS if one exists. |
| 96 | DC Tech Meetup | none | `(skipped)` |  | Paused until 2027. Confirmed empty. |
| 97 | DC Python | ical | `readers/ical.py` | `https://www.meetup.com/dcpython/events/ical/` | Meetup iCal, 1-3 upcoming (online). |
| 98 | PSW Science | ical | `readers/ical.py` | `https://ics.teamup.com/feed/ks1p86psgyu3z6msb4/10769005.ics` | Teamup iCal, 28 upcoming. |
| 99 | National Capital Astronomers | html | `readers/html.py` |  | Homepage lists 5 dated. Haiku reads. |
| 100 | Northern Virginia Astronomy Club (NOVAC) | stealth | `readers/browser.py` |  | Blocks plain requests (403). Stealth reads 7 dates; events page itself is mostly undated outreach. |
| 101 | Carnegie Science | html | `readers/html.py` |  | Server-rendered; 1 DC item, rest Pasadena. Haiku reads and keeps DC only. |
| 102 | Labyrinth Games & Puzzles | xhr | `readers/api.py` | `https://www.labyrinthdc.com/?format=json` | Squarespace JSON found 5 items; calendar page lists only event types. Browser fallback. |
| 103 | Game Kastle (College Park) | ical | `readers/ical.py` | `https://calendar.google.com/calendar/ical/800f6bde859b0593ad025d88a9aee4e33487a4840eeb918ee6b0ee1034bc8279%40group.calendar.google.com/public/basic.ics` | Google Calendar behind the embed; public ICS, 305 upcoming. |
| 104 | Victory Comics | browser | `readers/browser.py` | `https://victorycomics.com/event-schedule` | Two srcdoc iframes (no URL to fetch). Browser + Haiku; page forward. |
| 105 | Games & Comics Pair O' Dice (Fairfax) | ical | `readers/ical.py` | `https://calendar.google.com/calendar/ical/c_i992fmeebehi4bi15lbke0acvg%40group.calendar.google.com/public/basic.ics` | Google Calendar behind the page; public ICS, 35 upcoming. |
| 106 | Fantom Comics | html | `readers/html.py` | `https://ma.to/venue/fantomcomics` | Own site says 'No events found' and blocks robots; third-party venue listing has 4. Haiku reads that. |
| 107 | Break My Game | recurring | `readers/recurring.py` | `monthly; 2 sun; 15:00-18:00; Manassas VA; Break My Game playtest` | No dated list. Manassas 2nd Sunday 3-6pm; DC at Labyrinth quarterly (unscheduled). |
| 108 | Arlington Chess Club | browser | `readers/browser.py` | `https://www.arlingtonchessclub.com/Schedule.html` | Schedule.html errors on plain fetch. Browser; else recurring Friday club night. |
| 109 | Beer & Board Games | ical | `readers/ical.py` | `https://www.meetup.com/beerbogglers/events/ical/` | Meetup iCal confirmed, 10 upcoming. |
| 110 | The DC Area Board Game Club | ical | `readers/ical.py` | `https://www.meetup.com/dc-area-board-games/events/ical/` | Meetup iCal; 0 upcoming now. Keep, fills when they post. |
| 111 | The Board Room (Arlington) | none | `(skipped)` |  | Domain redirects to Goodwood Brewing, Louisville KY. Delete this row. |
| 112 | DC Rawhides | html | `readers/html.py` |  | Server-rendered, 15 dated. Haiku reads. |
| 113 | Hollywood Ballroom | browser | `readers/browser.py` | `https://www.keepandshare.com/calendar18/embed_calendar.php?i=2582549` | Keep&Share month grid; no feed. Browser the embed directly, page forward one month, Haiku reads. |
| 114 | Salsa Vida (DMV aggregator) | jsonld | `readers/html.py` |  | schema.org Event JSON-LD on page, 24 upcoming. html reader uses it. |
| 115 | Baila DC (socials) | recurring | `readers/recurring.py` | `monthly; 1,3 thu; 19:00; La Cosecha 1280 4th St NE; Baila Thursdays Salsa Social` | 1st and 3rd Thursdays; tickettailor.com/all-tickets/bailadc confirms dates (html fallback). |
| 116 | Baila DC (classes) | none | `(skipped)` |  | Weekly class series, not social events. Drop. |
| 117 | Dance Jam Productions | html | `readers/html.py` |  | Server-rendered, 5 multi-day weekends. Haiku reads. |
| 118 | Carpe Diem Arts | browser | `readers/browser.py` | `https://carpediemarts.org/event-calendar` | Google Calendar embed on /event-calendar. Browser once to read the ID, then switch to ical. |
| 119 | District Clay Center (One Shot classes) | recurring | `readers/recurring.py` | `weekly; fri,sat,sun; 17:30; District Clay Center; One Shot wheel class` | Fri/Sat/Sun 5:30pm, no dated list readable (Canvas). |
| 120 | Merry Pin | browser | `readers/browser.py` |  | Weebly/editmysite JS; browser pass found 16 dates. Browser + Haiku. |
| 121 | Art House 7 | browser | `readers/browser.py` | `https://arthouseseven.com/workshops/` | Dates in hisawyer widgets. Browser + Haiku. |
| 122 | Sur La Table (Pentagon Row) | html | `readers/html.py` |  | Server-rendered, 10 classes; identical to Alexandria list, de-dupe handles it. Haiku reads. |
| 123 | Sur La Table (Alexandria) | html | `readers/html.py` |  | Server-rendered, 10 classes. Haiku reads. |
| 124 | WGIT DC | none | `(skipped)` |  | Calendar behind sign-in. Confirmed unusable. |
| 125 | DC Social Guide | xhr | `readers/api.py` | `https://discovery.evvnt.com/api/publisher/6609/home_page_events?hitsPerPage=50&multipleEventInstances=true&page=0&publisher_id=6609` | evvnt JSON feed, 32 events. Haiku reads. |
| 126 | Art of Living DC Center (meetups) | browser | `readers/browser.py` |  | Same JS shell as events page. Browser + Haiku. |
| 127 | Art of Living DC Center (courses) | browser | `readers/browser.py` |  | Same JS shell as events page. Browser + Haiku. |
