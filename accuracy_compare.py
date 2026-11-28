"""Blind re-read comparison (layer 2 of the accuracy test, Nov 27).

Compares the events the weekend scouts extracted (A) with an independent re-read of the same saved pages by a
stronger model that never saw A (B). Per source: matched, only-in-A (possible wrong row), only-in-B (possible miss),
time disagreements. Rows match on date + the first 24 letters of the title.

  python accuracy_compare.py "<A tsv glob>" "<B tsv glob>" [sources...]   -> accuracy_blind.csv + summary
"""
import csv, glob, re, sys
from collections import defaultdict

def load(pat):
    out = defaultdict(list)
    for f in glob.glob(pat):
        for r in csv.reader(open(f, encoding="utf-8"), delimiter="\t"):
            if len(r) >= 6 and re.match(r"\d{4}-\d\d-\d\d", r[0]):
                out[r[5].strip()].append((r[0], (r[1] or "")[:5], r[2].strip()))
    return out

def key(e):
    return (e[0], re.sub(r"[^a-z0-9]", "", e[2].lower())[:24])

A, B = load(sys.argv[1]), load(sys.argv[2])
sources = sys.argv[3:] or sorted(B)
rows, tot = [], defaultdict(int)
for s in sources:
    a, b = A.get(s, []), B.get(s, [])
    ka = {}
    for e in a: ka.setdefault(key(e), []).append(e)
    kb = {}
    for e in b: kb.setdefault(key(e), []).append(e)
    match = [k for k in kb if k in ka]
    only_a = [e for k, v in ka.items() if k not in kb for e in v]
    only_b = [e for k, v in kb.items() if k not in ka for e in v]
    time_diff = [k for k in match if {e[1] for e in ka[k]} != {e[1] for e in kb[k]}]
    n_match = sum(min(len(ka[k]), len(kb[k])) for k in match)
    rows.append([s, len(a), len(b), n_match, len(only_a), len(only_b), len(time_diff),
                 " ; ".join(f"{e[0]} {e[1]} {e[2]}" for e in only_b)[:500],
                 " ; ".join(f"{e[0]} {e[1]} {e[2]}" for e in only_a)[:500]])
    for k, v in (("A", len(a)), ("B", len(b)), ("match", n_match), ("onlyA", len(only_a)), ("onlyB", len(only_b)), ("time", len(time_diff))):
        tot[k] += v
with open("accuracy_blind.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["source", "scout_rows", "blind_rows", "matched", "only_scout", "only_blind", "time_disagree", "only_blind_events", "only_scout_events"])
    w.writerows(rows)
print(dict(tot))
