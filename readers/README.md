# readers

One module per method. The sheet's **Method** column names the module; **Feed URL** is its input.

| Method in sheet | Module | Input (Feed URL column) | Needs Haiku? | Needs browser? |
| --- | --- | --- | --- | --- |
| ical | `readers/ical.py` | the .ics / webcal URL | no | no |
| api, xhr | `readers/api.py` | the JSON URL (may contain `{start}` `{end}`) | only for unknown shapes | no |
| rss | `readers/rss.py` | the RSS URL | yes (dates) | no |
| html, jsonld | `readers/html.py` | (uses URL column) | yes, unless JSON-LD is present | no |
| browser, stealth | `readers/browser.py` | J if it is a URL, else B | yes | yes |
| recurring | `readers/recurring.py` | the rule text, see module docstring | no | no |
| reader | `readers/html.py` with `https://r.jina.ai/` prefix in Feed URL | yes | no |
| none | skipped; row Status explains why | | |

Browser rows render the Feed URL (J) when it is a URL, else the page URL (B).

`fetch.py` loops over Sources, dispatches on Method, writes Feed. Read its docstring for flags.

Every reader returns events with a `desc` field (raw description, up to 600 chars). `fetch.py` adds Category (Sources column C) and, with ANTHROPIC_API_KEY, a 5 to 10 word Description via `readers/haiku.py::summarize`; without the key it writes `feed_desc.csv` for the scouts in `briefs/BLURB.md`.
