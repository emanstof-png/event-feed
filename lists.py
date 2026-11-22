"""Which source list a script works on. Same code, same readers, same rules for every list;
only the file and tab names differ. Pick with the FEED_LIST environment variable
(main by default; the GitHub workflows take it as the "list" input)."""
import os

LISTS = {
    "main":  dict(csv="sources_methods.csv", sources="Sources", feed="Feed", feed_test="Feed_test",
                  run_log="Run_log", playbook="PLAYBOOK.md", prefix="", out=""),
    "elite": dict(csv="elite_methods.csv", sources="Elite Sources", feed="Elite Feed", feed_test="Elite Feed_test",
                  run_log="Elite Run_log", playbook="ELITE_PLAYBOOK.md", prefix="elite_", out="_elite"),
    # Nov 21: candidates from the nightlife source search (briefs/SCOUT_NIGHT.md); git only, no sheet tab yet
    "nightlife": dict(csv="nightlife_methods.csv", sources="Nightlife Sources", feed="Nightlife Feed",
                  feed_test="Nightlife Feed_test", run_log="Nightlife Run_log", playbook="NIGHTLIFE_PLAYBOOK.md",
                  prefix="nightlife_", out="_nightlife"),
}

def name():
    n = os.environ.get("FEED_LIST", "main").strip() or "main"
    if n not in LISTS:
        raise SystemExit(f"FEED_LIST={n!r}; choose one of {sorted(LISTS)}")
    return n

def current():
    return LISTS[name()]
