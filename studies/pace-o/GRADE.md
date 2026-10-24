# pace-o grade: where does the rover stray from its course, and is it the study's planner?

MV2 of Munim, Inc. Graded with AI agents. CC BY 4.0.

Predictions: `studies/pace-o/PREDICTION.md` (SHA-256 d40004e7…, on main before the job fetched it; see `fetched.json`). Job `pace-o-v1`: fetched main at 2026-10-24T14:50:17Z (rover_pilot.py 0.18.0, pace_n.py cf3f300e… as pace-n-v1 ran it, with `studies/pace-n/GRADE.md` and `runs.jsonl`), `tests_exit` 0 (56 tests: test_pace_o, test_pace_n and test_lookahead_default; `tests.txt`), then flew 576 missions in 1,071 s (peak memory 0.04 GB). Every number below is read from `summary.json` in this folder. The code is `pace_o.py` and `test_pace_o.py` as the job ran them (pace_o.py SHA-256 806b4bbc…, test_pace_o.py 8af50e53…).

**Result: 9 of 9 predictions held. Rule R2 applies: the studies' planner cut across the inside of every checkpoint corner, so the studies from pace-p on fly `pace_o`'s `keep` planner and v0.18.1 (documentation only) restates the city-blocks figures. Rule R3: neither 8 m nor 24 m qualifies, so a real rover's 16 m lookahead stays. 24 m was 3.5-3.6% faster on city blocks, but by turning before each corner: its 95th-percentile distance from the course near path corners was 1.2-1.6 m above 16 m's.**

## Predictions

| | prediction | result | |
|---|---|---|---|
| O1 | check: compared 18, identical 18, missing 0 | 18, 18, 0 | held |
| O2 | all 576 missions completed | 576 of 576 | held |
| O3 | blocks: `diag16`'s `median_behind` ≥ 3 on both profiles | 4 and 4 (outage90, drift90) | held |
| O4 | blocks `diag16`: checkpoint `p95_m` ≥ 3 m above corner and other `p95_m`, checkpoint `far_share` ≥ 0.5, both profiles | outage90: 10.54 against 3.40 and 5.38, far_share 0.95; drift90: 11.97 against 5.35 and 7.21, far_share 0.712 | held |
| O5 | blocks: `keep16`'s checkpoint `p95_m` ≥ 3 m and whole-mission `p95_offset_m` ≥ 2 m below `diag16`'s, both profiles | checkpoint 2.94 against 10.54 (−7.60) and 4.69 against 11.97 (−7.28); whole mission 3.53 against 9.11 (−5.58) and 5.73 against 9.93 (−4.20) | held |
| O6 | `keep16` against `diag16`: slower on blocks (p < 0.05, share ≥ +0.005) on both; bayside and boulevard share within ±0.005 | blocks +0.0077 (22 of 24 seeds slower) and +0.0107 (21 of 24), p < 0.0001; bayside and boulevard 0.0 on both | held |
| O7 | `keep8` against `keep16`: `groups_faster` 0 on both; slower on blocks and bayside on both | faster 0 and 0; slower on all 3 courses of both profiles | held |
| O8 | `keep24` against `keep16`: `groups_slower` 0 and `groups_lost` 0 on both | 0 / 0 and 0 / 0 | held |
| O9 | drift90: `keep24`'s `median_offset_m` above `keep16`'s on bayside and boulevard | bayside 2.14 against 1.55, boulevard 1.98 against 1.60 | held |

(Courses are bayside / blocks / boulevard. Every mission was flown as pace_m.py's `long20` on v0.18.0's real-rover pilot; only the study's planner and the path follower's lookahead changed. `diag16` is pace-n's `look16`.)

## Decision

- **R1 does not stop anything:** the check found no difference (18 of 18 identical).
- **R2 applies.** `keep16`'s blocks checkpoint `p95_m` is below `diag16`'s on both profiles (2.94 against 10.54, 4.69 against 11.97). So the studies from pace-p on fly with `pace_o`'s `keep` planner, and v0.18.1 (documentation only) states in the README and FINDINGS that the city-blocks figures of the pace studies up to `pace_n.py` include cutting across the inside of its four checkpoint corners, with `keep16`'s figures next to them. The pilot is not changed by R2.
- **R3: neither qualifies, so 16 m stays.** A variant qualifies if, against `keep16` on both profiles, it has `groups_slower` 0 and `groups_lost` 0, its blocks corner `p95_m` (pace-n's corner record) is not above `keep16`'s, its `p95_offset_m` is at most 0.5 m above `keep16`'s on every course, and `groups_faster` ≥ 1 on some profile:
  - `keep8`: slower on 3 of 3 courses on both profiles. Does not qualify.
  - `keep24`: slower 0, lost 0, faster 3 + 2; but its blocks corner `p95_m` is 4.80 against 3.23 (outage90) and 5.81 against 4.63 (drift90), and its `p95_offset_m` is more than 0.5 m above `keep16`'s on four of six courses (outage90 +0.23 / +0.80 / +0.63 m, drift90 +1.28 / +1.10 / +0.48 m on bayside / blocks / boulevard). **Does not qualify.**
- R4: this grade, the outputs and the code are published here.

## Going round each checkpoint corner, against cutting across it (`keep16` against `diag16`)

| | outage90 (steady compass) | drift90 (drifting compass) |
|---|---|---|
| blocks: 95th-percentile distance from the course, whole mission | 9.11 → 3.53 m | 9.93 → 5.73 m |
| blocks: same, from 20 m before to 60 m after a checkpoint | 10.54 → 2.94 m | 11.97 → 4.69 m |
| blocks: same, near the 9 path corners | 3.40 → 3.23 m | 5.35 → 4.63 m |
| blocks: median of each mission's largest distance | 10.94 → 7.66 m | 13.40 → 10.35 m |
| boulevard: 95th percentile, whole mission | 5.51 → 2.54 m | 8.82 → 7.15 m |
| bayside: 95th percentile, whole mission | 2.82 → 2.93 m | 5.45 → 5.37 m |
| blocks: mission time (median paired difference) | +12 s (+0.77%) | +17 s (+1.07%) |
| bayside, boulevard: mission time | 0 s | 0 s |
| made good, three courses pooled (m/s) | 0.883 → 0.883 | 0.877 → 0.876 |

## Each lookahead against 16 m, corners kept (paired by seed, same profile)

| variant | outage90 | drift90 |
|---|---|---|
| keep8 | slower on all 3: +10 / +97 / +6 s (+0.70 / +6.16 / +0.34%) | slower on all 3: +11 / +87 / +6 s (+0.76 / +5.44 / +0.34%) |
| keep24 | faster on all 3: −9 / −57 / −1 s (−0.63 / −3.62 / −0.06%) | faster on 2: −10 / −56 s (−0.69 / −3.50%); boulevard 0 s (p 0.55) |

(bayside / blocks / boulevard.) Pooled made good, outage90 / drift90: keep8 0.853 / 0.853; keep16 0.883 / 0.876; keep24 0.888 / 0.882. Every variant completed every mission, every mission beat the human marathon pace (0.754 m/s), and no checkpoint report was refused.

## Findings

1. **The studies' planner cut across the inside of every checkpoint corner (O3, O4).** The pilot plans each leg when it reports the checkpoint the leg starts from, from its own estimate of where it is, which lags the rover (median 6.4-6.6 m off). On blocks all four interior checkpoints were planned from before the corner, and the studies' `CoursePlanner` then drew the new leg straight from there to the far end of the first segment, 100 m away. From 20 m before to 60 m after each checkpoint the rover's 95th-percentile distance from the course was 10.5-12.0 m, against 3.4-5.4 m near the path corners, and those 80 m stretches held 71-95% of all samples more than 8 m off.
2. **Going round the corner removes it, and costs about 1% on blocks (O5, O6).** With `keep` the blocks checkpoint stretches look like the path corners (2.9-4.7 m), the whole-mission 95th percentile falls from 9.1-9.9 m to 3.5-5.7 m, and blocks missions take 12-17 s longer (0.8-1.1%, 21-22 of 24 seeds), the extra distance round four corners. Boulevard's checkpoints are its bends, so its distances fell too (95th percentile 5.5 → 2.5 m with a steady compass), with no change in time. So the blocks times of the pace studies up to `pace_n.py` were flattered by about 1%, and their blocks distances from the course (and boulevard's) mostly measured the planner, not the pilot. That answers pace-n's open question (its N5 miss): the large blocks figure came from the checkpoint corners, not the outages.
3. **With the corners kept, 16 m beats 8 m by more on blocks (O7).** 8 m was 5.4-6.2% slower than 16 m on blocks, against 3.6-3.9% in pace-n with the corners cut, and 0.3-0.8% slower on the gentle courses. A likely reason, not tested: going round them adds four more right-angle turns per mission, and 8 m runs a median 4.3-4.5 m past each corner against 2.3 m with 16 m.
4. **24 m is faster still, by cutting corners (O8, O9, R3).** 24 m was 3.5-3.6% faster than 16 m on blocks and 0.6-0.7% on bayside, slower nowhere. But it turned before each corner (median 0.17 m past it, against 2.3 m with 16 m), its 95th-percentile distance near path corners rose 1.2-1.6 m, its whole-mission 95th percentile rose up to 1.3 m, and its path was shorter than the course itself (0.993 of the route with a steady compass). On a real sidewalk that is time saved by leaving it, which is what R3's distance limits were written to catch. Its median distance from the course was higher on the gentle courses with a drifting compass (O9) and also with a steady one (0.88 against 0.53 m on bayside), so the curve-cutting and not only the drift is behind it.
5. **What did not change.** The pilot's own position error (median 6.4-6.6 m), heading error and calibrations were the same with both planners; only where the path went changed.

## Limits

Simulated rovers only (pace_l.py's measured Mini+ profile), so speeds are upper bounds on what a sidewalk allows. `keep` is closer to the OpenStreetMap planner at a checkpoint corner but is not it: on a real map the nearest node can also be behind the rover or on another street, and real corners come at every angle. The size of the effect is measured here only for v0.18.0's real-rover pilot; the earlier studies' blocks figures likely include a similar share, not measured. Sidewalk width is not modelled, so "distance from the course" stands in for "off the sidewalk". The 20 m / 60 m window and the 8 m "far" mark were fixed before any mission was flown. The reason in finding 3 is likely, not tested. None of this has been measured on a live Mini+.
