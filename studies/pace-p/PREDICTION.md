# pace-p: does a longer lookahead save time on straights, or only at corners? (pre-registered)

MV2 of Munim, Inc. Written with AI agents. CC BY 4.0.

This file is committed to main before any pace-p mission is flown. The job that flies them (`pace-p-v1`) waits until this file, rover_pilot.py 0.18.1 or 0.18.0 (the pilot code is the same in both; 0.18.1 only adds documentation), pace-o's `pace_o.py` (SHA-256 806b4bbc…), `studies/pace-o/GRADE.md` and `studies/pace-o/runs.jsonl` are on main. It records this file's SHA-256 and the time it fetched main (`fetched.json`). The study code (`pace_p.py`, `test_pace_p.py`) will be published with the grade, byte for byte as the job ran it. No clock time is written here: the commit history and the job log show the order.

## Why

pace-o (`studies/pace-o/GRADE.md`) flew v0.18.0's real-rover pilot with the studies' planner going round each checkpoint corner. A 24 m lookahead was 3.5-3.6% faster than the shipped 16 m on the city-blocks course and 0.6-0.7% faster on bayside, slower nowhere. But it turned before each corner (median 0.17 m past it, against 2.3 m with 16 m), its 95th-percentile distance from the course near path corners was 1.2-1.6 m higher, and its whole-mission 95th percentile was up to 1.3 m higher, so by the pre-stated rule 16 m stayed. Its grade called corner cutting the likely source of the time, not tested.

The pilot's speed is `cruise × cos(heading error)` (at least a quarter of cruise). At a right-angle corner a longer lookahead swings the aim point round the corner earlier, so the heading error stays smaller and the rover slows less, which is the same thing as cutting the corner. On a straight a longer lookahead only changes how gently the rover closes a sideways offset, for example after a GPS outage. If nearly all of 24 m's time comes from corners, no lookahead rule can buy it without cutting them; if a real share comes from straights, a follower that aims far on straights and 16 m near turns could keep it.

Prior art: pure pursuit with a lookahead that changes along the way is well known. Adaptive Pure Pursuit scales the lookahead with speed, and Nav2's Regulated Pure Pursuit (Macenski et al., "Regulated pure pursuit for robot path tracking", Autonomous Robots 47, 2023, https://arxiv.org/abs/2305.20026) slows the robot on high curvature, which also shortens its speed-scaled lookahead; its authors note it still short-cuts sharp turns, though less. Lookaheads chosen from upcoming curvature appear in the vehicle literature. What these studies add is the measurement: on a simulated Mini+ with measured telemetry, 90 s GPS outages and a steady or drifting compass error, how much of a longer lookahead's time saving comes from straights and how much from corners, with corner overshoot and distance from the course measured alongside, and the rule for changing the pilot written down first.

## Design

Every mission is flown by `pace_m.fly` as pace-m's `long20` (v0.18.1's pilot on a real rover: `pace_l.py`'s `bridge120+cf0.3` with the compass-bias learner on 20 m stretches), on `pace_o`'s `keep` planner, which pace-o's rule R2 made the studies' planner from pace-p on. Only the path follower changes.

`pace_p.BendFollower` is `rover_pilot.PathFollower` (points every 2 m) with one change: it aims at the long lookahead while the path from the rover's place to that point stays within `turn_deg` of the heading at the rover's place (`turn_ahead`: the largest change of segment heading over those segments), and at `short_m` otherwise. It counts its targets and how many were long (the **aim** record).

Variants:
- `keep16`: a plain 16 m (v0.18.1's real-rover pilot; flown by `pace_o.fly` itself);
- `keep24`: a plain 24 m (as pace-o flew it; a reference, it cannot qualify below);
- `bend24`: 24 m, 16 m when the path ahead turns by 45° or more (pace-n's corner threshold);
- `calm24`: 24 m, 16 m when it turns by 10° or more;
- `calm32`: 32 m, 16 m when it turns by 10° or more.

On these courses only blocks has turns of 45° or more (its right angles). Bayside's points, 20 m apart on a 15 m sine, turn by up to 15° each, and boulevard's bends (about 20°) are its checkpoints, so each leg's path ends at one and turns by about 20° at most, where it starts by going round the previous one. So `bend24` should aim long almost everywhere on bayside and boulevard and differ from `keep24` mainly on blocks, while `calm24` and `calm32` also go short on bayside's curves.

Profiles (pace_l.py's, cruise 0.8, pace_study's three courses): `outage90` (90 s GPS outages after a mean of 600 s of sky; a steady compass error) and `drift90` (outage90 with pace_d.py's drifting compass error, SD 10°, 120 s time constant). **Seeds 253-276** (none flown before). 5 × 2 × 3 × 24 = **720 missions**.

Before the study, `--check` flies seeds 229-231 of pace-o's outage90 and drift90 `keep16` and `keep24` missions again (36 missions) and compares every field with pace-o's record.

Output fields: `verdicts` compare, paired by seed per course, each variant with `keep16`. "Faster" or "slower" means a paired sign test with p < 0.05 (`groups_faster`, `groups_slower`); `groups_lost` counts courses where the variant completed fewer missions; `pair_effect` gives each course's `median_time_diff_share` (negative is faster). `aim` gives per profile, variant and course `median_long_share`, the median over missions of the share of targets that were long. `corner` is pace-n's corner record (`p95_m`, `median_past_m`: how far past each path corner the rover got, below 0 meaning it turned before it). `offset` gives `median_offset_m` and `p95_offset_m` for the whole mission. `context` and `planner` are pace-o's.

## Predictions

Each is graded from those output fields.

- **P1.** The check: compared 36, identical 36, missing 0.
- **P2.** All 720 missions are completed.
- **P3.** The aim record does what it was built to: `bend24`'s `median_long_share` is at least 0.95 on bayside and on boulevard, and between 0.5 and 0.9 on blocks, on both profiles.
- **P4.** `calm24` goes short on bayside's curves: its bayside `median_long_share` is between 0.3 and 0.8 on both profiles.
- **P5.** pace-o's 24 m result comes back on new seeds: `keep24` against `keep16` is faster (p < 0.05) on blocks on both profiles with `groups_slower` 0 on both, and on blocks `keep24`'s corner `median_past_m` is below 1.0 m while `keep16`'s is above 1.5 m, on both profiles.
- **P6 (the question).** The corners carry most of 24 m's blocks time: on blocks, `bend24`'s `median_time_diff_share` against `keep16` is above half of `keep24`'s (`keep24`'s is negative, so `bend24` keeps less than half of its saving), on both profiles.
- **P7.** `bend24` goes round corners like 16 m: on blocks its corner `median_past_m` is at least 1.5 m and its corner `p95_m` within 0.5 m of `keep16`'s, on both profiles.
- **P8.** Where it aims long, `bend24` flies like 24 m: its bayside `median_time_diff_share` against `keep16` is within 0.002 of `keep24`'s, on both profiles.
- **P9.** Aiming long on a straight holds the rover further to one side with a drifting compass: on drift90, `bend24`'s boulevard `median_offset_m` is above `keep16`'s.
- **P10.** By rule R2 below, none of `bend24`, `calm24` and `calm32` qualifies.

Why these:
- P3 and P4 follow from the course shapes above. On blocks, each 100 m side ends in a right angle, so `bend24` aims short for the last 24 m before each corner (about a quarter of the distance), and the rover spends longer there because it slows to turn. The ranges are wide because each leg starts at the pilot's own estimate, a few metres off the course, which adds a kink of unknown size. For `calm24` on bayside, working the 10° threshold through the sine gives long on about 58% of the distance.
- P5: the same pilot and planner as pace-o on 24 new seeds.
- P6: with the speed rule above, a straight costs time only through the heading error while closing a sideways offset, which is small at a 16 m lookahead already. This is the prediction most likely to miss: aiming long on straights may also steady the heading after each outage.
- P7: within 24 m of a corner `bend24` aims as `keep16` does; it only enters that stretch from a slightly different place.
- P8: on bayside `bend24` aims long for at least 95% of its targets (P3).
- P9: pace-o's O9 (24 m: 1.98 against 1.60 m on boulevard with drift90); a longer lookahead turns a heading error into a larger sideways offset before the rover corrects it.
- P10: on boulevard, which these variants fly long, pace-o's `keep24` was 0.63 m above `keep16` in `p95_offset_m` on outage90 and 0.48 m on drift90; on bayside with drift90, 1.28 m. Going short on curves (`calm`) should remove much of bayside's excess but not boulevard's.

## Decision rules

- **R1.** If the check finds any difference, nothing from this study is published as a finding, and nothing changes until the difference is explained.
- **R2 (the path follower).** `bend24`, `calm24` or `calm32` qualifies if, against `keep16` on both profiles: `groups_slower` 0 and `groups_lost` 0; its blocks corner `p95_m` is at most 0.25 m above `keep16`'s; its blocks corner `median_past_m` is at least 1.0 m (it does not turn before corners); its `p95_offset_m` is at most 0.5 m above `keep16`'s on every course; and `groups_faster` is at least 1 on some profile. If more than one qualifies: the one with more `groups_faster` summed over both profiles, then the shorter long lookahead, then the larger `turn_deg`. If one qualifies, v0.19.0 adds the BendFollower to rover_pilot.py and the command line gives a real rover's path follower that variant's settings, with 16 m (`PATH_LOOKAHEAD_M`) as its short lookahead; the simulator and the class defaults are unchanged. Otherwise a real rover keeps the plain 16 m lookahead and the results are documented (v0.18.2, documentation only). `keep24` is a reference only: it failed pace-o's rule R3 and cannot qualify here.
- **R3.** Whatever the outcome, the grade and the outputs are published in studies/pace-p/ with the code. P2-P10 decide nothing beyond what R1 and R2 read from the fields.

Limits:
- Simulated rovers only (pace_l.py's measured Mini+ profile), so speeds are upper bounds on what a sidewalk allows.
- The courses are three idealised shapes with corners of only 90° or under 25°, and sidewalk width is not modelled, so "distance from the course" stands in for "off the sidewalk".
- The 45° and 10° thresholds and the 24 m and 32 m long lookaheads are choices made here, before any mission is flown; other values would split the path differently.
- `keep` is closer to the OpenStreetMap planner at a checkpoint corner but is not it.
- None of this has been measured on a live Mini+.
