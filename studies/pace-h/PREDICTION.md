# pace-h: should dead reckoning stay on by default? (pre-registered)

MV2 of Munim, Inc. Written with AI agents. CC BY 4.0.

This file is committed to main before any pace-h mission is flown. The job that flies them (`pace-h-v1`) waits until this file, `studies/pace-g/GRADE.md` and pace-g's `pace_g.py` are on main, and records this file's SHA-256 and the time it fetched main (`fetched.json`). The study code (`pace_h.py`, `test_pace_h.py`) will be published with the grade, byte for byte as the job ran it. No clock time is written here: the commit history and the job log show the order.

## Why

pace-g (`studies/pace-g/GRADE.md`, 4 of 9 predictions held) found that v0.13.0's real-rover pilot, which uses dead reckoning and `--smooth-heading`, is 1.5-7.0% slower on a clean GPS than `--smooth-heading` alone, on every course of every profile without GPS gaps. Through GPS gaps dead reckoning saves the pilot from stopping (5.9% of the time stopped without it, 0.5% with it). Its rule R2 asks this study whether dead reckoning should stay on by default.

pace-g's explanation, not yet tested: the reckoner starts again from every fix (gain 1), so the position it gives jumps by the fix's noise every 2 s and drifts sideways between fixes by the heading's error. The pilot turns at each jump and weaves, the compass-bias learner's straight stretches break about 5 times as often, and it fits 3 stretches a mission instead of 60-84, leaving more heading error.

Prior art: that GPS corrections which make the position jump upset a path follower is known in general, and the usual cure is a smooth fusion of GPS and odometry (a Kalman filter, or a weighted blend) with the controller tracking the continuous odometry frame (for example Fixposition's field guide, https://www.fixposition.com/blogs/field-guide/position-jumps-after-gnss-outage, and ROS robot_localization's odom/map setup). drg0.3+cf0.3 is the simplest such blend; bridge+cf0.3 is a different choice, to use dead reckoning only where the GPS is missing. What is tested here is which of them, if any, keeps the human marathon pace on this rover's measured telemetry.

## Design

Profiles (pace_g.py's, the measured Mini+ reporting its wheels' RPM): `measured`, `noise8` (8° of compass noise), `dropout0.3` (30% of GPS fixes missing), `dropout0.3-noise8`.

Variants:

| variant | what it is |
|---|---|
| dr+cf0.3 | v0.13.0 on a real rover: dead reckoning (`DEAD_RECKON`) and `--smooth-heading` |
| cf0.3 | `--smooth-heading` only |
| bridge+cf0.3 | dead reckoning steered by only while the GPS has no fresh fix (`BridgePilot`: `GpsFilter.has_fix` false); otherwise the GPS filter's position, as cf0.3 steers |
| drg0.3+cf0.3 | dead reckoning moved 0.3 of the way to each fix (`gain` 0.3) instead of starting again from it |
| dr+cf0.3+kb | dr+cf0.3 with the compass-bias learner starting at the bias that cancels the rover's compass error (later fits still move it by the learner's gain 0.3) |

Cruise 0.8 (`--marathon`), pace_study's three courses (boulevard, blocks, bayside), **seeds 61-84**, none flown by an earlier study. 4 × 5 × 3 × 24 = **1,440 missions**. Every mission records pace_g.py's fields and also `steer.mean_abs_angular`, the mean |angular| applied while driving forward.

Before the study, if `studies/pace-g/runs.jsonl` is on main, `--check` flies seeds 37-39 of pace-g's measured and dropout0.3 missions with dr+cf0.3 and cf0.3 again (36 missions) and compares every field with pace-g's record.

`verdicts` compare pairs paired by seed per course, b against a: (cf0.3 → dr+cf0.3), (cf0.3 → bridge+cf0.3), (dr+cf0.3 → bridge+cf0.3), (dr+cf0.3 → drg0.3+cf0.3), (cf0.3 → drg0.3+cf0.3), (cf0.3 → dr+cf0.3+kb), (dr+cf0.3 → dr+cf0.3+kb). "Faster" or "slower" means a paired sign test with p < 0.05 (`groups_faster`, `groups_slower`); `groups_lost` counts courses where a completed more missions. `median_time_diff_share` is the median paired difference over a's median time. `steer` rows give `median_mean_abs_angular`; `learner` rows give `median_breaks`.

## Predictions

Each is graded from those output fields.

- **H1.** If the check runs: compared 36, identical 36, missing 0. If `studies/pace-g/runs.jsonl` is not on main, H1 is graded "not tested".
- **H2.** All 1,440 missions are completed.
- **H3.** pace-g's cost replicates on fresh seeds: dr+cf0.3 against cf0.3 is slower (`groups_slower`) on all 3 courses of measured.
- **H4.** On a clean GPS, bridging costs nothing: bridge+cf0.3 against cf0.3 has `groups_slower` 0 and `groups_lost` 0 on every profile, and on measured and noise8 `|median_time_diff_share|` ≤ 0.005 on every course.
- **H5.** Bridging keeps the gap saving: bridge+cf0.3 against cf0.3 is faster on all 3 courses of dropout0.3 and of dropout0.3-noise8, with `median_time_diff_share` ≤ −0.03 on every one of those courses.
- **H6.** Bridging beats v0.13.0: bridge+cf0.3 against dr+cf0.3 has `groups_slower` 0 and `groups_lost` 0 on every profile, and `groups_faster` ≥ 2 on measured and on noise8.
- **H7.** Bridging keeps the marathon pace: bridge+cf0.3's pooled `median_made_good_mps` is ≥ 0.87 on measured and noise8 and ≥ 0.85 on both dropout profiles, and `beat_human_pace` is 72 on all four.
- **H8.** Most of the cost is the jumps, not the learner: dr+cf0.3+kb against cf0.3 is still slower on bayside and boulevard of measured, with `median_time_diff_share` ≥ +0.03 on both.
- **H9.** A gentler reckoner weaves less: drg0.3+cf0.3 against dr+cf0.3 is faster on at least 2 of the 3 courses of measured.
- **H10.** The weaving is measurable: on measured, on every course, dr+cf0.3's `median_mean_abs_angular` is above cf0.3's, and bridge+cf0.3's is within 10% of cf0.3's; dr+cf0.3's `median_breaks` is at least 3 times cf0.3's, and bridge+cf0.3's at most 1.1 times cf0.3's.

Why these:
- H3: pace-g measured 24 of 24 seeds slower on every measured course (+7.0%, +1.5%, +6.9%).
- H4, H10 (bridge): with a fresh fix bridge+cf0.3 steers exactly as cf0.3 does (the reckoner only reads), so its missions can differ only after the first second it bridges a gap, which on measured happened for a median of 1.1-2.0 s per mission in pace-g.
- H5, H7: in pace-g, cf0.3 stood still 5.9% of the time on dropout0.3 and dr+cf0.3 0.5%. With the GPS filter's position between gaps, the learner works as it does for cf0.3, so dead reckoning through a gap follows a well-learned heading. 0.821 m/s (cf0.3 on dropout0.3) without most of the 5.4 points of stopping is about 0.86-0.87.
- H8: in pace-g, dr (bias error 7-17° at the end) and dr+cf0.3 (4-5°) cost about the same (6.6% and 7.0% on bayside), so the size of the bias error does not seem to drive the cost.
- H9: with gain 0.3 each fix's noise moves the position by 0.3 of it, not all of it.

## Decision rules

- **R1.** If H1 is not failed and bridge+cf0.3 has `groups_slower` 0 and `groups_lost` 0 against both cf0.3 and dr+cf0.3 on every profile, and is faster than cf0.3 on at least 2 courses of each dropout profile: the next release (v0.14.0) makes bridging the real-rover dead-reckoning mode (dead reckoning steered by only while the GPS has no fresh fix), with a flag to restore v0.13.0's. The release is assembled and must fly pace-h's bridge+cf0.3 missions exactly (a sample of them), as v0.12.0 did pace-c's.
- **R2.** If R1's conditions fail for bridge+cf0.3 but hold for drg0.3+cf0.3, the release uses gain 0.3 for the reckoner instead, on the same terms. If both hold, bridging is chosen: on a clean GPS it is the pilot pace-f and pace-g already tested.
- **R3.** If neither holds and H3 holds, the next release turns dead reckoning off by default on a real rover (`--dead-reckon` turns it on), and README says that the pilot then stops through GPS gaps.
- **R4.** If the check finds any difference, nothing from this study is published as a finding until the difference is explained.
- **R5.** Whatever the outcome, the grade and the outputs are published in studies/pace-h/ with the code, and the results go into FINDINGS-frodobots-2k.md and the README. H8-H10 decide nothing; they test pace-g's explanation.

Limits: simulated rovers only, so speeds are bounds on what a real sidewalk allows. GPS noise and dropouts are independent from fix to fix; real GPS errors drift and real dropouts come in runs. The simulated wheels report the commanded speed exactly. None of this has been measured on a live Mini+.
