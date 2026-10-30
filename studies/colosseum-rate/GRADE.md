# colosseum-rate: grade

Graded 2026-10-30 against `PLAN.md` (committed before any flight). By MV2 of Munim, Inc.; the grading and write-up are made with AI agents. Text CC BY 4.0.

**Result: 7 of 8 predictions held, and the decision is R1: `--max-angular 0.3` stays the recommendation under RoboColosseum's 2-3 s cadence.** In 960 simulated flights on fresh seeds 49-72, every stale-telemetry arm completed every trial at both turn rates, 23.4°/s per unit (recorded Earth Rovers, `studies/frodo-spin/GRADE-v2.md`) and 48°/s (what the pilot assumes for a Mini+). 0.3 scored 1.138 times the live time, within the rule's 0.10 of the best (0.7 at 1.112). The miss was S4: the unchanged pilot did **not** fail at 48°/s, though it came within 0.07 of the limit on 30 m trials. At the recorded rovers' rate the unchanged pilot passed easily (S3), so the cap matters most on a rover that turns faster.

## The run

- Job `colosseum-rate-v1`, sealed container, 2026-10-30 00:38-00:41 UTC (flights 67 s). `fetch_deps.py` found `PLAN.md` on main (sha256 f079ac87...), confirmed `colosseum_rate.py` was byte for byte the file on main, and confirmed that `studies/colosseum-hold/colosseum_hold.py` was the file both earlier studies flew (`same_as_hold_v1: true`, sha256 1d54b068...). rover_pilot.py 0.19.2 (sha256 8d60538e...). The unit tests passed.
- 2 rates × 5 arms × 2 distances × 2 noise levels × 24 seeds = 960 flights, 300 s trials, hold 2-3 s.

## Median time as a multiple of `live` at the same rate

| Rate | Arm | 30 m, 0.22 m | 80 m, 0.22 m | 30 m, 1.5 m | 80 m, 1.5 m | passes |
|---|---|---|---|---|---|---|
| 23.4 | stale (unchanged) | 1.117 | 1.039 | 1.198 | 1.052 | yes |
| 23.4 | stale-m30 | 1.208 | 1.078 | 1.256 | 1.101 | yes |
| 23.4 | stale-m50 | 1.174 | 1.045 | 1.181 | 1.073 | yes |
| 23.4 | stale-m70 | 1.135 | 1.041 | 1.197 | 1.049 | yes |
| 48 | stale (unchanged) | 1.429 | 1.163 | 1.384 | 1.164 | yes |
| 48 | stale-m30 | 1.269 | 1.100 | 1.288 | 1.115 | yes |
| 48 | stale-m50 | 1.276 | 1.091 | 1.263 | 1.089 | yes |
| 48 | stale-m70 | 1.282 | 1.112 | 1.276 | 1.095 | yes |

All 40 cells completed and were accepted 24 of 24, with no timeouts and no crashes. Live median times were 54.0-55.5 s (30 m) and 158.6-160.6 s (80 m) at 23.4°/s, and 51.5-54.0 s and 157.6-158.6 s at 48°/s.

**Scores** (summed median time over the 4 cells ÷ live's, averaged over both rates): unchanged 1.149, 0.3 1.138, 0.5 1.112, 0.7 1.112. Fastest passing arm: the unchanged pilot at 23.4, 0.5 at 48.

## Predictions

| | Prediction | Result | |
|---|---|---|---|
| S1 | `stale-m30` passes at 48 | 24/24 in every cell, at most 1.288 × live | held |
| S2 | `stale-m30` passes at 23.4 | 24/24 in every cell, at most 1.256 × live | held |
| S3 | the unchanged pilot passes at 23.4 | 24/24 in every cell, at most 1.198 × live | held |
| S4 | the unchanged pilot fails at 48 | it passed: 24/24 everywhere, worst cell 1.429 × live (limit 1.5) | **missed** |
| S5 | at 23.4, `stale-m30`'s summed median time is higher than `stale-m50`'s | 482.6 s against 467.0 s | held |
| S6 | the decision is R1 | R1 (0.3's score 1.138 is 0.026 above the best, 1.112) | held |
| S7 | no flight crashes | 0 in all 40 cells | held |
| S8 | `live` is slower at 23.4 than at 48 in all 4 cells | 55.5 vs 54.0, 160.6 vs 158.6, 54.0 vs 51.5, 158.6 vs 157.6 s | held, narrowly |

## Decision: R1

0.3 passes at both rates and its score is less than 0.10 above the best, so by the rule the README keeps recommending `--max-angular 0.3` under a 2-3 s cadence with telemetry refreshed only at observations, and adds that it also passed at 23.4 and 48°/s per unit. As the plan requires, S3 is reported too: at the recorded Earth Rovers' turn rate the unchanged pilot completed every trial at 1.04-1.20 times the live time.

## What it says

- **The cap is insurance, not a cost-free win.** At 23.4°/s the cap of 0.3 was the slowest of the four arms (1.08-1.26 × live) and the unchanged pilot the fastest (1.04-1.20). 0.3 also needed a median 0.5-1 recovery move a trial at 23.4, where the other arms needed none: at that rate one held command at 0.3 turns only about 14°, so large heading errors take several observations to remove.
- **At 48°/s the unchanged pilot is near the edge.** Its 30 m trials took 1.38-1.43 × live, against the pass limit of 1.5, and in the 60°/s simulator of `colosseum-hold` it failed (1.64-1.84). Every cap kept 30 m trials at 1.26-1.29. A real Mini+'s rate is not yet measured, so 0.3 is the choice that passed at every rate tried (23.4, 48 and 60).
- **0.5 and 0.7 did slightly better overall** (score 1.112 against 1.138) and passed at both rates, but the margin is inside what the rule set in advance as too small to change the recommendation, and neither has been confirmed on a second seed set.

## Honest limits

As stated in the plan: the 2-3 s cadence comes from the GeNIE baseline's notes (frodobots-org/colosseum-policy-server #8), not the bridge's code, which publishes no licence. The simulator turns at a constant rate per unit after a 0.8 s latency; recorded rovers turn less per second on short holds (frodo-spin-v2, D2). 23.4 comes from human-driven, mostly Earth Rover Zero-era rides; 48 is an assumed Mini+ figure. Simulation only; no pilot code changed. S8 held by margins of 1.0-2.5 s. A real RoboColosseum trial is the only real test.

## Files

`summary.json`, `runs.jsonl` (one line per flight) and `fetched.json` (the files flown and their hashes) are committed beside this file.

## Reproduce

```
python fetch_deps.py
python -m unittest -v test_colosseum_rate
python colosseum_rate.py --out-dir out --seeds 24 --first-seed 49
```
