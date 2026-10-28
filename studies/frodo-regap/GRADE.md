# frodo-regap-v1: grade

Graded 2026-10-28 (~22:00 UTC) against `PREDICTION.md`, which was committed before the run (e0ca28a). MV2 of Munim, Inc.; written with AI agents. CC BY-SA 4.0 (results derive from FrodoBots-2K by FrodoBots Lab).

**Run:** frodo-regap-v1 ran in sealed compute on 2026-10-28, 19:14-19:59 UTC (45 min, peak memory 0.06 GB). `fetch_deps.py` found `PREDICTION.md` on main and confirmed that `frodo_regap.py` (0.1.0) and `test_frodo_regap.py` were byte for byte the pre-registered copies (`same_as_main: true`). The unit tests passed. It sampled 1,433 rides (60 from each of 23 parts and all 53 usable rides of part 23) and analysed 1,359, with 74 skipped for too little data and 0 errors. That is 192.6 hours of GPS, read as 243 MB over range requests, with rover_pilot 0.19.0's `GpsFilter`. All figures below come from `summary.json`.

## Check E1: passed

- Gaps per hour: 1.73, inside [1.0, 3.0]. frodo-gps-v4 had found 1.8 per hour.
- Scored first fixes: 120 (at least 60 were required). Baseline fixes: 42,547.

## Decision rules

| Rule | Stated before the run | Result | |
|---|---|---|---|
| D1: the first fix is safe to restart from | ratio of medians <= 1.5 **and** <= 5% of first fixes over 5 m | ratio 1.742 (95% CI 1.466-2.176); 6.67% over 5 m | **not met** (both parts fail) |
| D2: restarting helps on real data | >= 20 gaps driven through; restart's median below keep's; restart > 2 m worse in <= 10% | 59 gaps; 1.493 m against 2.789 m; 1.69% worse | **met** |

## Predictions: 6 of 8 held

| | Prediction | Result | |
|---|---|---|---|
| P1 | E1 passes, with 1.2-2.6 gaps per hour | passes, 1.73 per hour | held |
| P2 | median baseline miss 0.3-2.0 m | 0.736 m | held |
| P3 | the shipped average sits a median 0.8-3.0 m from the reference on ordinary fixes | 1.944 m | held |
| P4 | ratio of medians (first fix / ordinary fix) 1.0-3.0 | 1.742 | held |
| P5 | <= 10% of first fixes over 5 m | 6.67% | held |
| P6 | the wheels drove 2 m or more through at least half of the gaps a new fix ended | 49.77% | **missed** (by 0.23 points) |
| P7 | on gaps driven through, restart's median below keep's | 1.493 m against 2.789 m | held |
| P8 | D1 is met | not met | **missed** |

## What it means

- **On a real Earth Rover, the first GPS fix after a gap is worse than an ordinary fix.** It sits a median 1.28 m from where the receiver's own next 9 s put the rover, against 0.74 m for ordinary fixes, 1.74 times as far (the 95% interval, 1.47-2.18, only just reaches the 1.5 limit). 6.7% of first fixes are over 5 m off, against 0.35% of ordinary fixes, about 19 times the rate. pace-w's simulator made every first fix as good as any other, so this is a real-world cost that the simulated restart never paid.
- **Restarting still lands nearer on average.** When the wheels drove through the gap, starting the average again put the estimate a median 1.49 m from the reference, against 2.79 m for the shipped average, and it was more than 2 m worse in 1 of 59 gaps and more than 2 m better in 10. Part of this edge is the average's ordinary lag, though: on ordinary fixes alpha 0.3 already sits 1.94 m from the reference, and the reference is built from the receiver's later fixes, which favours any estimate that equals a raw fix.
- **By the rule written in advance (D1 fails), FINDINGS now says that a restart on a real rover must wait for a second fix that agrees with the first**, and any later restart study builds that in. The shipped pilot is unchanged: it keeps its average across gaps, as pace-w's rule already chose (v0.19.1).
- P6 missed by a hair: the rover was driving through 49.8% of gaps, not "at least half". It doesn't affect either rule.

## Next

frodo-regap2 (pre-registered in `studies/frodo-regap2/PREDICTION.md`) tests that rule on rides this study did not read: start the average again only from a new fix that agrees with the new fix before it. It compares this with the shipped average and the first-fix restart at the second fix after each gap, and it checks D1's failure on fresh rides.

## Limits

These are the limits listed in advance, and all of them still apply. The reference is the receiver's own next ~9 s, not surveyed truth. A constant-velocity line is wrong on turns. The rides were driven by people on Earth Rover Zero-era rovers logging GPS about once a second, while the Mini+ reports every 2 s. The wheels' distance relies on frodo_gps's RPM-to-speed factor.

## Files

`summary.json` (every figure, settings and the `fetched` record), `report.md`, `events.jsonl` (one line per first fix after a gap) and `rides.jsonl` (one line per sampled ride) are committed beside this file.
