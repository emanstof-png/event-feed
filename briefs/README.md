# briefs: the prompts Haiku scouts run on

Each file is handed to one Haiku subagent (4 sources or 40 rows per agent, at most 20 agents at
once). Replace TODAY with the sheet-header date. Outputs are fixed-format so the lead agent can
parse them without reading prose.

| Brief | Used for | Input | Output |
| --- | --- | --- | --- |
| `SCOUT_VERIFY.md` | re-test a source's recorded method by fetching its feed or page | 4 lines from the Sources tab (row, name, URL, method, feed, status) | one `ROW` block per source |
| `SCOUT_RENDER.md` | judge a stealth-browser render saved by `render_test.py` | 4 files from `browser_samples/` | one `FILE` block per file |
| `SCOUT_DISCOVER.md` | pick the hidden event feed from a `discover.py` capture | 4 files from `discover/` | one `ROW` block per source |
| `SCOUT_FIND.md` | pick a new source's calendar from `find_calendars.py` + `discover.py` output | 4 rows' `find/` + `discover/` files | one `ROW` block per source |
| `BLURB.md` | write a 5 to 10 word description per event | 40 lines of `feed_desc.csv` | `n<TAB>blurb` lines in a file |

Run order for a manual feed: CLAUDE.md, "The manual run, step by step".
