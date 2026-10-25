You are a scout confirming hidden event feeds for 4 DC-area organizations. Today is in the batch file.
SPEC_SPEED.md Phase 1, step 2. Read only the files named here; they are already in the repo.

NO LIVE FETCHING. Do not use WebFetch, WebSearch or a browser on any site (RULES 12). Never fill a
gap by fetching. If discover/<slug>.json is missing, report MISSING.

For EACH source in your batch, read discover/<slug>.json. It lists "candidates": data calls the
organization's page made while rendering on GitHub, best first. Each has url, method, status,
replay_status, replay_ok (true = a plain request with no cookies got the same dated data back),
and "body" (first 4000 chars of the response).

Pick the ONE candidate that is this organization's own upcoming events list:
- The body holds 3+ events, each with a title and a full date (year present, or an ISO/epoch
  timestamp) on or after today. Count events, not date strings.
- It belongs to this org: its widget, booking system or calendar (Mindbody, Timely, Sawyer,
  Salesforce, Galaxy Digital, Keep&Share, Squarespace, Wix, Tribe, LibNet...). Not analytics, ads,
  site config, a blog list, opening hours, a product catalog, or another group.
- Prefer replay_ok true. If the best one is replay_ok false, still report it, with RESULT TOKEN.
- If the URL holds dates that look like a window (start=2026-10-24, end=..., month=10), say which
  parameter it is so the lead can replace it with {start} / {end}.

Output EXACTLY one block per source, nothing else:

ROW <n> | <name>
RESULT: FEED | TOKEN | NONE | MISSING
URL: <the candidate url, exactly as in the file, or blank>
METHOD: <GET|POST>
DATES: <which URL params are the date window, or none>
SHAPE: <where the events sit and the field names: e.g. "data.events[]: name, start_at (ISO), url, location.name">
COUNT: <n upcoming events in the body>
SAMPLES: <date title> ; <date title> ; <date title>
NOTE: <one line: why this one, or why none (e.g. "only analytics and a 2025 blog JSON")>
