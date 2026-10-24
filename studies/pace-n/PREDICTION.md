# pace-n: how far ahead should the rover aim along its path? (pre-registered)

MV2 of Munim, Inc. Written with AI agents. CC BY 4.0.

This file is committed to main before any pace-n mission is flown. The job that flies them (`pace-n-v1`) waits until this file, `studies/pace-m/GRADE.md`, `studies/pace-m/runs.jsonl`, `test_learner_default.py` and pace-m's `pace_m.py` (SHA-256 7167780f…) are on main with rover_pilot.py 0.17.0. It records this file's SHA-256 and the time it fetched main (`fetched.json`). The study code (`pace_n.py`, `test_pace_n.py`) will be published with the grade, byte for byte as the job ran it. No clock time is written here: the commit history and the job log show the order.

## Why

With a planner (`--osm` or `--fetch-osm` on a real rover, `CoursePlanner` in every study since pace-b) the pilot follows its planned path by pure pursuit (`PathFollower`): it aims at the point 8 m ahead of its place on the path. The 8 m was never tested.

pace-m's own records point at it:
- On the blocks course, the only one with right-angle corners, the rover's true distance from the course had a 95th percentile of 10.6-11.0 m (outage90 and drift90, shipped and long20 learners), against 3.6-6.1 m on bayside and 5.7-7.7 m on boulevard. Its median there was only 1.3-2.1 m. So the large distances come from a small part of each mission.
- The pilot's idea of where it is was off by a median 6.3-6.5 m on every course, also where its distance from the course stayed small. So most of that error is along the track, not across it. A likely reason: the smoothed GPS (`GpsFilter`, alpha 0.3 on a fix every 2 s, each fix 1.5 s late) lags the rover. A first-order estimate gives about 7 s, or 6 m at 0.89 m/s.
- If so, the lookahead the rover really has is about 8 − 6 = 2 m. It starts turning only as it reaches a corner, and runs past it before the turn takes hold.

Aiming further ahead should start the turn earlier. Aiming nearer should run further past. A longer lookahead also holds the rover further to one side for the same heading error (lookahead × tan(error); FINDINGS measured 3.6-3.9 m for an unlearned −25° at 8 m), and it reacts more slowly to the GPS's noise, so it should steer less hard.

Prior art: the lookahead trade-off of pure pursuit is textbook (Coulter, "Implementation of the Pure Pursuit Path Tracking Algorithm", CMU-RI-TR-92-01, 1992), and speed-adaptive lookaheads are common. Compensating GPS latency is standard in vehicle navigation. This study proposes no new method. It measures, for this pilot on the Earth Rover Mini+'s measured telemetry, what the untested 8 m costs at corners and in time. It also introduces a corner record (`past_m`: how far the rover gets beyond each corner along the course into it), which earlier studies did not have.

## Design

Every mission is flown by `pace_m.fly` as pace-m's `long20`: v0.17.0's pilot on a real rover (`pace_l.py`'s `bridge120+cf0.3`, which bridges GPS outages on the wheels with a 120 s reach and uses `--smooth-heading`, plus the compass-bias learner with 20 m stretches). Only the path follower's lookahead changes, through `pace_n._aiming`, which gives every `PathFollower` the Pilot builds the variant's `lookahead_m`. The path is densified every 2 m, so the lookaheads are 2, 4, 6 and 8 path points.

Variants:
- `look8`: 8 m (as it ships);
- `look4`: 4 m;
- `look12`: 12 m;
- `look16`: 16 m.

Profiles (pace_l.py's, cruise 0.8, pace_study's three courses): `outage90` (90 s GPS outages after a mean of 600 s of sky; a steady compass error) and `drift90` (outage90 with pace_d.py's drifting compass error, SD 10°, 120 s time constant). **Seeds 205-228** (none flown before). 4 × 2 × 3 × 24 = **576 missions**.

The corner record: every 1 s while the rover drives forward, `pace_n._watching` reads its true position (it only reads). A path corner is an interior course point that is not a checkpoint, where the course turns by at least 45°. Blocks has 9 of them, and boulevard and bayside have none. For each sample within 20 m of a path corner it records the true distance from the course. For each corner it records `past_m`: the furthest the rover got beyond the corner, measured along the course into it. Above 0 means it ran past the corner. 0 means it turned onto the next leg at the corner. Below 0 means it turned before the corner without reaching the next leg within 20 m.

Before the study, `--check` flies seeds 181-183 of pace-m's outage90 and drift90 `long20` missions again as `look8` (18 missions) and compares every field with pace-m's record.

Output fields: `verdicts` compare each variant with `look8` on the same profile, paired by seed per course. "Faster" or "slower" means a paired sign test with p < 0.05 (`groups_faster`, `groups_slower`), and `groups_lost` counts courses where `look8` completed more missions. `corner` gives, for blocks per profile and variant, `p95_m` (the median over missions of each mission's 95th-percentile distance from the course near corners) and `median_past_m` (the median over missions of each mission's median `past_m` over its corners). `offset` gives `median_offset_m` and `p95_offset_m` for the whole mission. `steer` gives `median_mean_abs_angular`, the median over missions of each mission's mean |angular| while driving forward. `offset_max` gives each group's largest distance from the course and its refused checkpoint reports.

## Predictions

Each is graded from those output fields.

- **N1.** The check: compared 18, identical 18, missing 0.
- **N2.** All 576 missions are completed.
- **N3.** The shipped lookahead runs past corners: `look8`'s blocks `median_past_m` is above +2 m on both profiles.
- **N4.** The further ahead it aims, the earlier it turns: on blocks, `median_past_m` is ordered look4 > look8 > look12 > look16 on both profiles.
- **N5.** Aiming further ahead keeps it nearer the course at corners, and aiming nearer keeps it further: on blocks, `look12`'s and `look16`'s corner `p95_m` are each at least 2 m below `look8`'s, and `look4`'s is above `look8`'s, on both profiles.
- **N6.** A 4 m lookahead is slower: `look4` against `look8` has `groups_slower` at least 2 (of 3 courses) on each profile.
- **N7.** Longer lookaheads cost no time and save it at corners: `look12` and `look16` against `look8` have `groups_slower` 0 and `groups_lost` 0 on both profiles, and each is faster (p < 0.05) on blocks on both profiles.
- **N8.** With a drifting compass, a longer lookahead holds the rover further from the course on straights and gentle curves: on drift90, `look16`'s `median_offset_m` is above `look8`'s on boulevard and on bayside, and on each of those two courses that increase is larger on drift90 than on outage90.
- **N9.** The further ahead it aims, the less hard it steers: `median_mean_abs_angular` is ordered look4 > look8 > look12 > look16 on every profile and course (6 of 6).

Why these:
- N3: with about 6 m of along-track lag, an 8 m lookahead starts the turn about 2 m before the corner. The turn needs several seconds at 0.89 m/s, and the command lands 0.8 s late. The rover should end up several metres past the corner; +2 m leaves room for a smaller lag than estimated.
- N4 and N5: the same picture with lookaheads of about −2, 2, 6 and 10 m. At 12 m and 16 m it should turn early enough to round the corner on the inside. A chord cut from 10 m before to 10 m after a right angle is at most about 5 m from the course, and pure pursuit cuts less than a chord. The order of `look12` and `look16` in `p95_m` is not predicted: one may round the corner more tightly, the other cut it more.
- N6: at 4 m the rover is aiming at a point about 2 m behind where it really is. It weaves on the GPS's noise, about twice as much in angle as at 8 m, and it overshoots every corner.
- N7: blocks has 9 path corners in 1,400 m. Turning early takes the inside line, with less slowing for the heading error (linear = cruise × cos(error)). Elsewhere the courses are straight or gently curved, so a longer lookahead should change little there. This is the prediction most likely to miss on bayside, where a 16 m lookahead cuts each curve by about 0.5 m.
- N8: pace-m's drift90 median heading error was 6.3-6.9° (long20). 16 × tan 6.5° ≈ 1.8 m against 0.9 m at 8 m; on outage90 (1.6-1.7°) the same change is about 0.2 m. A longer lookahead also returns more slowly to the path after a disturbance, on both profiles. That part should not depend on the drift, so the drift90-minus-outage90 difference isolates the lookahead × heading-error term.
- N9: the angle to the aim point moves by about (lateral noise) / lookahead, and corner turns are gentler with a longer lookahead.

## Decision rules

- **R1.** If the check finds any difference, nothing from this study is published as a finding, and no default changes until the difference is explained.
- **R2.** A variant qualifies if all of these hold against `look8` on both profiles: `groups_slower` 0 and `groups_lost` 0; its blocks corner `p95_m` is not above `look8`'s; its `p95_offset_m` is at most 0.5 m above `look8`'s on every course; and either `groups_faster` is at least 1 on some profile, or its blocks corner `p95_m` is at least 1 m below `look8`'s on both profiles.
  - If any variant qualifies, v0.18.0 gives a real rover's path follower the lookahead of the qualifying variant with the lowest mean of blocks corner `p95_m` over the two profiles. Ties go to the most `groups_faster` summed over both profiles, then to the shorter lookahead.
  - The change is made at the command-line layer, for a real rover only: the command line sets the lookahead the Pilot gives its PathFollower. The simulator's defaults and the defaults of the PathFollower and Pilot classes are unchanged.
- **R3.** If no variant qualifies, the lookahead stays at 8 m, and v0.17.1 only adds pace-n's results to the README and FINDINGS.
- **R4.** Whatever the outcome, the grade and the outputs are published in studies/pace-n/ with the code. N2-N9 decide nothing beyond what R1-R3 read from the fields.

Limits:
- Simulated rovers only (pace_l.py's measured Mini+ profile), so speeds are upper bounds on what a sidewalk allows.
- The courses are three idealised shapes. A real OSM path has corners of every angle, and sidewalk width is not modelled, so "distance from the course" stands in for "off the sidewalk".
- The lookahead matters only with a planner (`--osm`/`--fetch-osm`). Without one the pilot heads straight for each checkpoint.
- The lag explanation is a likely reason, not tested here. A study that compensates the lag directly would test it.
- None of this has been measured on a live Mini+.
