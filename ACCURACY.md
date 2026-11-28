# Accuracy test, weekend Nov 27-29 2026 (run Nov 27 evening)

Three layers. Rerun each weekend: `python accuracy_check.py START END "<scout tsv glob>"`, a blind re-read of a sample
with a stronger model on the SAME page versions the scouts read, then `python accuracy_compare.py "<scout glob>" "<blind glob>" <sources>`.

## Layer 1: capture (all 170 sources with a method, accuracy_capture.csv)
- 131 OK, 9 BLOCKED (403/404/timeouts: AEI, Loyalty, AU CAS, Goethe, Art House 7, Pozez, AJC, SOME, MoCA before fix),
  5 TRUNCATED (old 40k/60k caps: Songbyrd, Comedy Loft, DC Reads, Volunteer Arlington, People's Book), 7 STALE.
- 19 flagged as possible miss/undercount (saved page mentions weekend dates more than we extracted). Layer 2 resolved the sampled ones.

## Layer 2: blind re-read, 27 sources (19 flagged + 8 random OK), Sonnet vs Haiku scouts
- Scout rows in sample: 88. Correct: 75 (85%). Wrong: 13, all read from a stale Nov 22 render (12 Art of Living, 1 WGIT). Removed from the Sheet.
- Real misses: 1 (Merry Pin "Small Business Saturday", added). Catch rate on the groups' own events: 75 of 76 (99%).
- WGIT DC: its calendar page is a citywide CitySpark listing (75 items on Fri alone); scouts took 0 of them. Counted separately:
  it is a mass-market aggregator, not WGIT's own events. Decision needed: keep WGIT as a source or drop it.
- Not counted as errors (policy differences between readers): date-range exhibitions repeated per day (NGA, UMD), year-round
  forms (Rock Creek), multi-day comedy runs per day (DC Improv), closure notices (Sixth & I, AU), out-of-area items (Repair the World).
- Field accuracy on matched rows: titles and dates agree; times agree except 1 blank time (Sur La Table Croissant, 9:00 AM).

## Layer 3: human spot check
- "Accuracy Check" tab, 20 sources, filled by Eric against the live sites. Pending.

## Fixes made from this test
- Extraction waits for every fetch job; STALE flag added; CLAUDE.md lesson.
- Page caps raised (40k -> 150k raw, 120k reader). Yoga District (68) and Hill Center (8) recovered in the Nov 27 recheck.
