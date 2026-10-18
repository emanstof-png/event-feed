# RULES: how this project is run

Ten rules. Each one exists because its absence cost us a session. `check.py` enforces the ones a
script can; CI runs it on every push. The rest are on whoever is working.

1. **The sheet is the truth; the repo mirrors it.** Sources tab columns B, I, J, K, L, M, N are
   the record. `sources_methods.csv` is a snapshot of them and `PLAYBOOK.md` is generated from
   the snapshot by `python sync_playbook.py`. Never edit PLAYBOOK.md by hand. *(checked)*

2. **A method change touches every mirror in the same commit.** Changing I (Method) means J
   (Feed), K (Status), N (How to read), the CSV snapshot and PLAYBOOK all change with it. Tonight
   N was left stale on 34 rows; that is the bug this rule prevents. *(checked: N must name the
   reader module and say whether it reads B or J)*

3. **Browser rows render J when J is a URL, else B.** The widget or embed URL lives in J; the
   org's page lives in B. `fetch.py` does this; N must say which. *(checked)*

4. **Record the cheapest method that worked, not the strongest one.** html before stealth, feed
   before html. `fetch.py` falls back to the browser on its own when the cheap one fails.

5. **UNTESTED is not EMPTY.** A feed the scouts could not reach (calendar.google.com,
   robots-disallowed routes, 5xx) is UNTESTED until GitHub Actions has tried it. EMPTY requires
   a note saying what was checked. *(checked: status vocabulary and EMPTY notes)*

6. **Proof is 3 dated, titled events with samples.** Counts without samples are not proof; dates
   without years are not proof. Scouts run on the prompts in `briefs/` and report in their fixed
   block format; a brief that only exists in a chat is lost when the chat is compacted.

7. **Say how long before starting; check back, never block.** Any job over a minute gets an
   expected duration up front and a scheduled check, not a silent wait. 20 subagents at once,
   no more.

8. **Do what was asked, to the number asked.** "Top 20" is 20. "This org's calendar" is not a
   search for other orgs.

9. **Secrets live only in GitHub Actions secrets.** Never in the repo, the sheet, or a doc.
   *(checked: a grep for key-shaped strings)*

10. **Every session ends with a handoff in the Specs doc** (numbers, built / not built,
    confidence, next steps in order) and a green `python check.py`. Then it is safe to compact.

Added Oct 18, 2:55am, after Eric found 166 empty links in the first feed:

11. **Every feed row is clickable.** Link is the event's own URL, else the first link in its
    description, else the organization's calendar page. Never blank. *(checked on the last
    committed feed)*

## Commands

    python check.py                       # before every commit
    python sync_playbook.py               # after any change to sources_methods.csv
    python sync_playbook.py --from-sheet  # with the Google key: refresh the snapshot from the live sheet first
    python check.py --sheet               # with the Google key: snapshot vs live sheet drift
