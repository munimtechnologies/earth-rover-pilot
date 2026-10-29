# frodo-regap2-v1: grade

Graded 2026-10-29 against `PREDICTION.md`, which was committed before the run (7cd1eb7). MV2 of Munim, Inc.; written with AI agents. CC BY-SA 4.0 (results derive from FrodoBots-2K by FrodoBots Lab).

**Run:** frodo-regap2-v1 ran in sealed compute on 2026-10-29, 13:52-14:47 UTC (55 min, peak memory 0.06 GB). `fetch_deps.py` confirmed that `frodo_regap2.py` (0.1.0) and `test_frodo_regap2.py` were byte for byte the pre-registered copies on main (`same_as_main: true`), with rover_pilot 0.19.0 from v0.19.0, frodo_motion 0.2.0 from v0.8.0 and `studies/frodo-regap/frodo_regap.py` 0.1.0 from main. The unit tests passed. Leaving out the 60 rides per part that frodo-regap-v1 read, it sampled 1,758 rides (up to 80 per part; none were left in part 23) and analysed 1,669, with 89 skipped for too little data and 0 errors: 243.8 hours of GPS, read as 250 MB over range requests. All figures below come from `summary.json`.

## Check E1: passed

- Gaps per hour: 1.81, inside [1.0, 3.0] (frodo-regap-v1: 1.73).
- Scored second fixes: 215 (at least 60 were required). Baseline fixes: 54,697.

## Decision rules

| Rule | Stated before the run | Result | |
|---|---|---|---|
| D1 again | fails if the ratio of medians (first / ordinary fix) > 1.5 **or** > 5% of first fixes over 5 m | ratio 2.029 (95% CI 1.752-2.335); 9.42% over 5 m | **fails again** (both parts) |
| D3: confirm is safe | at the second fix, confirm > 5 m off in <= 5% of scored gaps, **and** no more often than restart | 7.91% (restart 9.77%) | **not met** |
| D4: confirm helps | >= 20 gaps driven through; confirm's median below keep's; confirm > 2 m worse than keep in <= 10% | 97 gaps; 1.349 m against 2.786 m; 0% worse | **met** |

## Predictions: 6 of 8 held

| | Prediction | Result | |
|---|---|---|---|
| P1 | E1 passes, with 1.2-2.6 gaps per hour | passes, 1.81 per hour | held |
| P2 | D1 fails again | fails: ratio 2.03, 9.4% over 5 m | held |
| P3 | the second fix agrees with the first in 70-97% of gaps with a second fix | 96.81% of 313 | held |
| P4 | where both are scored, the second fix's median miss is below the first's | 1.378 m against 1.488 m (184 gaps) | held |
| P5 | D3 is met | 7.91% over 5 m, above 5% | **missed** |
| P6 | D4 is met | met | held |
| P7 | confirm restarts a median of at most 2.0 s after the first fix | 0.8 s (90th percentile 6.7 s; within 10 s in 91%) | held |
| P8 | of first fixes over 5 m off that have a second fix, confirm refuses at least half at the second fix | 6 of 18 (33%) | **missed** |

## What it means

- **The first fix after a gap is bad again, and worse than frodo-regap-v1 measured.** On rides that study did not read, it sat a median 1.47 m from the reference against 0.72 m for ordinary fixes (2.03 times; v1 1.74), and 9.4% of first fixes were over 5 m off against 0.27% of ordinary fixes (v1 6.7% against 0.35%). Two independent samples now agree that a real Earth Rover's first fix after a gap of more than 3 s is about twice as far off as an ordinary one, with a tail roughly 20-35 times as heavy.
- **Waiting for a second agreeing fix helps on average but doesn't remove the tail.** At the second fix, confirm sat a median 1.31 m from the reference, against 1.55 m for restart and 2.02 m for the shipped average. But it was still over 5 m off in 7.9% of gaps (restart 9.8%, the shipped average 13.0%). The 2 m + 1.5 m/s agreement test refused only 6 of the 18 first fixes that were over 5 m off: a bad fix is usually followed by a second one that is wrong the same way, so two fixes agreeing does not make them right.
- **By the rule written in advance (D3 not met), a real rover keeps the GPS average across gaps and the restart line is closed.** pace-x, the simulated trial confirm would have earned, is not run. The shipped pilot is unchanged (v0.19.1, the choice pace-w's rule already made).
- One honest caution about that closure: the shipped average's own tail at the second fix (13.0% over 5 m) was worse than confirm's, so "keep" is not safe either by D3's bar. D3 asked whether confirm is safe in absolute terms, not whether it beats keep, and the reference favours any estimate equal to a raw fix (see Limits). The study does not show that keeping the average is better after a gap, only that neither restart rule met the safety bar set in advance.

## Limits

These are the limits listed in advance, and all of them still apply. The reference is the receiver's own next ~9 s, not surveyed truth; it favours any estimate equal to a raw fix, and at the second fix confirm usually is that fix, so D4 partly measures the average's ordinary lag. A constant-velocity line is wrong on turns and speed changes. The rides were driven by people on Earth Rover Zero-era rovers logging GPS about once a second; a Mini+ reports every 2 s, which doubles the time confirm waits. The agreement thresholds were set from earlier measurements, not tuned on this data.

## Files

`summary.json` (every figure, settings and the `fetched` record), `report.md`, `events.jsonl` (one line per gap) and `rides.jsonl` (one line per sampled ride) are committed beside this file.

Reproduce: `python fetch_deps.py && python -m unittest -v test_frodo_regap2 && python frodo_regap2.py --out-dir out --parts all --rides-per-part 80 --skip-first 60 --budget-min 150` in `studies/frodo-regap2/`.
