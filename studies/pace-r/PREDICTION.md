# pace-r: is a truer GPS position worth anything once the rover really aims as far ahead? (pre-registered)

MV2 of Munim, Inc. Written with AI agents. CC BY 4.0.

This file is committed to main before any pace-r mission is flown. The job that flies them (`pace-r-v1`) waits until this file, rover_pilot.py 0.18.3 or 0.18.2 (the pilot code is the same in both; 0.18.3 only adds documentation), `pace_q.py` as pace-q-v1 ran it (SHA-256 e65c9b56…) with `test_pace_q.py` and `studies/pace-q/GRADE.md`, and `pace_p.py` (c5234ba5…) with `studies/pace-p/runs.jsonl` are on main. It records this file's SHA-256 and the time it fetched main (`fetched.json`). The study code (`pace_r.py`, `test_pace_r.py`) will be published with the grade, byte for byte as the job ran it. No clock time is written here: the commit history and the job log show the order.

## Why

pace-q (`studies/pace-q/GRADE.md`) found that with GPS as quiet as recorded Earth Rovers' (0.22 m per axis), filters without the shipped exponential average's lag were 3.1-4.4% faster on the city-blocks course and slower on no course, but every one turned before blocks' corners, so none passed its rule. The path follower's lookahead is measured from where the pilot thinks it is. With the shipped filter (alpha 0.3) that is a median 6.31-6.41 m behind the rover on quiet90, so the 16 m lookahead really aims about 16 − 6.4 = 9.6 m ahead of it. With pace-q's `TrackingGpsFilter` (alpha 0.3, beta 0.053, 2.17-2.34 m behind) it aims about 13.8 m ahead. pace-p found that a longer real aim saves time on blocks by turning before the corners (24 m: 3.2-3.8% faster, a median 0.1-0.2 m past each corner instead of 2.1 m). So pace-q's saving may be partly or entirely the longer real aim, and partly or not at all a truer position.

This study separates the two by flying each filter at both real aims:

| variant | filter | lookahead | real aim (16 or 12 or 20 m minus the measured lag) |
|---|---|---|---|
| `a0.3-16` | `GpsFilter`, alpha 0.3 (as it ships) | 16 m (as it ships) | about 9.6 m |
| `track-12` | `TrackingGpsFilter` | 12 m | about 9.8 m, as the shipped pilot |
| `a0.3-20` | `GpsFilter`, alpha 0.3 | 20 m | about 13.6 m, as the tracker at 16 m |
| `track-16` | `TrackingGpsFilter` | 16 m | about 13.8 m (pace-q's `track`) |

`track-12` against `a0.3-16` asks what a truer position is worth when the rover aims as far ahead as the shipped pilot does. `track-16` against `a0.3-20` asks the same at the longer aim. `a0.3-20` against `a0.3-16` is the aim alone. `PathFollower` rounds lookahead / 2 m half to even, so every lookahead here is a whole number of its 2 m steps (13 m would be flown as 12 m). The real-aim figures are worked out from pace-q's measured position errors, not measured here.

Prior art: pure pursuit's lookahead trade-off (Coulter, CMU-RI-TR-92-01, 1992), alpha-beta tracking (Benedict and Bordner, 1962; Kalata, IEEE Trans. AES 20, 1984), and delay compensation in path tracking are textbook. What this study adds is the separation on a simulated Earth Rover Mini+ with its measured telemetry and 90 s GPS outages. It asks how much of a lag-free filter's time saving is a truer position and how much is the longer real aim that the lookahead's reference point gives it for free, with the rule for changing the pilot written down first.

## Design

Every mission is flown by `pace_q.fly`, which flies `pace_p.py`'s `keep16`: v0.18.2's real-rover pilot (`pace_m.py`'s `long20` learner on `pace_l.py`'s `bridge120+cf0.3`, `pace_o.py`'s `keep` planner). It uses pace-q's `a0.3` or `track` filter, and `pace_r.fly` sets the path follower's lookahead around it (`pace_o._aiming`; the outer setting is the one the follower gets, which a test checks). With 16 m, `a0.3-16` and `track-16` fly exactly as pace-q's `a0.3` and `track`; tests check this, and `--check-q` checks it on pace-q's record. Nothing else in the pilot changes.

Profiles: pace-q's outage90 (90 s GPS outages after a mean of 600 s of sky, a steady compass error, the simulator's 1.5 m of GPS noise per axis), quiet90 (the same with 0.22 m) and quietdrift90 (pace_l.py's drift90 with 0.22 m). Cruise 0.8, pace_study's three courses (bayside, blocks, boulevard). **Seeds 301-324** (none flown before). 4 × 3 × 3 × 24 = **864 missions**.

Before the study, `--check` flies seeds 253-255 of pace-p's outage90 and drift90 `keep16` missions again as `a0.3-16` (18 missions) and compares every field with pace-p's record. If `studies/pace-q/runs.jsonl` is on main when the job fetches it (`fetched.json`: `pace_q_runs_on_main`), `--check-q` also flies seeds 277-279 of pace-q's quiet90 `a0.3` and `track` missions again as `a0.3-16` and `track-16` (18 missions) and compares them with pace-q's record.

Output fields are pace-q's: `verdicts` per pair (`a0.3-16` against each other variant, `track-16` against `a0.3-20`, `track-16` against `track-12`), paired by seed per course. "Faster" or "slower" means a paired sign test with p < 0.05 (`groups_faster`, `groups_slower`), `groups_lost` counts courses where the variant completed fewer missions, and `pair_effect` gives each course's `median_time_diff_share` (negative is faster). `position`, `corner` (`p95_m`, `median_past_m`: how far past each path corner the rover got, below 0 meaning it turned before it), `offset` (`p95_offset_m`) and `gps` are as in pace-q.

## Predictions

Each is graded from those output fields.

- **P1.** The check: compared 18, identical 18, missing 0. If `--check-q` was flown, the same for it.
- **P2.** All 864 missions are completed.
- **P3 (the lookahead leaves the lag alone).** On quiet90, `median_position_err_m` is between 5.8 and 7.0 m for `a0.3-16` and for `a0.3-20` on every course, and below 3.0 m for `track-12` and for `track-16` on every course.
- **P4 (the aim alone).** On quiet90 and on quietdrift90, `a0.3-20` is faster than `a0.3-16` on blocks (p < 0.05) with a `median_time_diff_share` between −0.030 and −0.005, and its blocks corner `median_past_m` is lower than `a0.3-16`'s.
- **P5.** On quiet90 and on quietdrift90, `track-12`'s blocks corner `median_past_m` is above `track-16`'s and below `a0.3-16`'s.
- **P6 (the question).** On quiet90 and on quietdrift90, `track-12` is faster than `a0.3-16` on blocks (p < 0.05) with a `median_time_diff_share` between −0.035 and −0.005.
- **P7.** On quiet90 and on quietdrift90, `track-16` is faster than `a0.3-20` on blocks (p < 0.05).
- **P8.** On quiet90 and on quietdrift90, `track-12`'s `groups_slower` against `a0.3-16` is 0.
- **P9 (the stress test).** On outage90, `track-12` against `a0.3-16` has `groups_lost` 0 and a `median_time_diff_share` of at most +0.01 on every course.
- **P10.** By rule R2 below, `track-12` does not qualify.

Why these:
- P3: the lookahead changes where the pilot aims, not how its filter follows the fixes.
- P4: pace-n and pace-p found lookaheads of 8, 16 and 24 m about 3.5% apart on blocks with each step of 8 m; 16 to 20 m is half a step. P7 and P6 then ask what the tracker adds at each real aim. pace-q's `track` saved 3.7-4.1% with quiet GPS at a real aim of about 13.8 m. That is as much as pace-p's shipped filter saved with a 24 m lookahead (3.2-3.8%), whose real aim was longer (about 17.6 m), although pace-p used the noisier profiles. So the tracker probably adds something beyond the aim (P6, P7), but less than its whole pace-q saving (P6's upper bound).
- P5: a shorter lookahead turns later, and a truer position turns sooner than a lagging one, so `track-12`'s turn should lie between the other two.
- P8 and P9: pace-q's `track` was slower on no course with either noise, and at 12 m the tracker's remaining noise (about half of the 1.5 m) turns into at most about 4° of aim jitter.
- P10: pure pursuit from a true position cuts the inside of a right angle. The shipped pilot overshoots by 2.1 m only because its position lags behind the turn. A truer position should turn sooner even at a matched real aim, so `track-12`'s blocks corner `median_past_m` probably falls below 0 on at least one quiet profile. This is the prediction most likely to miss.

## Decision rules

- **R1.** If the check (or `--check-q`, when flown) finds any difference, nothing from this study is published as a finding, and nothing changes until the difference is explained.
- **R2 (the GPS filter and lookahead on a real rover).** Only `track-12` is a candidate; `a0.3-20` is a lookahead change of the kind pace-p already ruled on, and `track-16` failed pace-q's rule. `track-12` qualifies if, against `a0.3-16`:
  - on quiet90 and on quietdrift90: `groups_slower` 0 and `groups_lost` 0; its blocks corner `p95_m` is at most 0.25 m above `a0.3-16`'s; its blocks corner `median_past_m` is at least 0 m; its `p95_offset_m` is at most 0.5 m above `a0.3-16`'s on every course; and `groups_faster` is at least 1 on one of the two profiles;
  - on outage90: `groups_lost` 0, and `median_time_diff_share` at most +0.01 on every course.

  These are pace-q's conditions, unchanged. If `track-12` qualifies, v0.19.0 makes the command line give a real rover's pilot `TrackingGpsFilter` (alpha 0.3, beta 0.053, starting again after more than 3 s without a fix) and a 12 m path lookahead. The simulator and the class defaults are unchanged. Otherwise a real rover keeps the shipped filter and 16 m, and the results are documented in v0.18.4 (documentation only).
- **R3.** Whatever the outcome, the grade and the outputs are published in studies/pace-r/ with the code. P2-P10 decide nothing beyond what R1 and R2 read from the fields.

## Limits

- Simulated rovers only (pace_l.py's measured Mini+ profile), so speeds are upper bounds on what a sidewalk allows.
- The real-aim matching uses pace-q's median position errors; the lag varies along a mission (it is larger right after an outage and during turns), so the match holds only at the median.
- quiet90's 0.22 m is drawn as independent noise per fix. The slow wander of real fixes, steady offsets and multipath jumps are not modelled, and the Mini+'s receiver may differ from the Zero's. Nothing here predicts a fix forward over its 1.5 s delay.
- Three idealised courses, with corners of only 90° or under 25°, and no sidewalk width, so "distance from the course" stands in for "off the sidewalk".
- The lookaheads (12 and 20 m) were chosen before any mission was flown, from pace-q's published position errors.
- None of this has been measured on a live Mini+.
