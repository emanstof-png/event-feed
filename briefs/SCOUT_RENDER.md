You are checking whether a headless browser render of an events page shows real upcoming events. Today is the date in the sheet header.
Read each file listed in your batch file (they are under browser_samples/). Line 1 is the org, line 2 the URL,
line 3 the render report, then the page text. Do NOT fetch the web; judge only the text in the file.

For each file, count UPCOMING events (date on/after TODAY, within ~5 weeks) that have a title. If the page prints month/day
without a year, infer the year from today's date (today) and say "year inferred". Count events, not date strings.

Output EXACTLY one block per file, nothing else:

FILE <basename>
ORG <name>
RESULT: EVENTS | SHELL | PAST_ONLY | RULE_ONLY | ERROR
COUNT: <n upcoming with titles>
SAMPLES: <date title> ; <date title> ; <date title>
WHAT_THE_PAGE_IS: <one line: real listing / loading shell / login wall / only a weekly schedule / 404 etc.>
NEXT: <one line: 'browser works' | 'needs click X / scroll / month-forward' | 'recurring rule: weekly; day; HH:MM; venue; title' | 'dead'>
