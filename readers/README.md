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

Browser rows render the Feed URL (J) when it is a URL, else the page URL (B). Since Oct 24 the
browser is one shared session for the whole run, 45s cap per source, no network-idle wait,
Cloudflare solving only on a challenge page. `common.get()` impersonates Chrome (curl_cffi) so
sites that 403 plain Python requests answer. `fetch.py` flags ALARM in the log when a source
had events last run and 0 now. To find a widget's hidden feed: run "Discover data calls"
(`discover.py`), scouts read `discover/` with `briefs/SCOUT_DISCOVER.md`.

`fetch.py` loops over Sources, dispatches on Method, writes Feed. Read its docstring for flags.

Every reader returns events with a `desc` field (raw description, up to 600 chars). `fetch.py` adds Category (Sources column C) and, with ANTHROPIC_API_KEY, a 5 to 10 word Description via `readers/haiku.py::summarize`; without the key it writes `feed_desc.csv` for the scouts in `briefs/BLURB.md`.
