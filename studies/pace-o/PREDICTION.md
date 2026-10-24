# pace-o: where does the rover stray from its course, and is it the study's planner? (pre-registered)

MV2 of Munim, Inc. Written with AI agents. CC BY 4.0.

This file is committed to main before any pace-o mission is flown. The job that flies them (`pace-o-v1`) waits until this file, rover_pilot.py 0.18.0 (with `test_lookahead_default.py`), pace-n's `pace_n.py` (SHA-256 cf3f300e…), `studies/pace-n/GRADE.md` and `studies/pace-n/runs.jsonl` are on main. It records this file's SHA-256 and the time it fetched main (`fetched.json`). The study code (`pace_o.py`, `test_pace_o.py`) will be published with the grade, byte for byte as the job ran it. No clock time is written here: the commit history and the job log show the order.

## Why

pace-n (`studies/pace-n/GRADE.md`) found that near the city-blocks course's nine right-angle path corners the rover's 95th-percentile distance from the course was only 3.3-5.7 m, against 9.0-11.1 m over the whole mission. So most of the large distances come from somewhere else. Its grade named two likely places, neither measured: the four corners that are checkpoints, and the 90 s GPS outages.

Reading the study code points at the first, and at the studies' own planner rather than at the pilot:
- The pilot plans each leg when it reports the checkpoint the leg starts from. It reports from 10 m (by the raw GPS or its own estimate, whichever is nearer), and its own estimate lags the rover by about 6 m (pace-m and pace-n: median position error 6.3-6.5 m, mostly along the track). So it plans from a point about 10-16 m before the checkpoint.
- The studies' planner (`pace_study.CoursePlanner`, `leg_points`) finds the course segment of the new leg nearest that point and goes from the point straight to that segment's end. On blocks every interior checkpoint is a right-angle corner, and the nearest segment of the new leg is the one leaving the corner. So each new leg begins with a straight line from 10-16 m before the corner to the next corner 100 m away, across the inside of the block. A line from 15 m before a right angle to 100 m beyond it runs up to about 13 m from the course.
- The OSM planner a real rover uses (`route_planner`) routes from the walkable node nearest the rover. Near a street corner that is usually the corner itself, so it would go round the corner, not across the block.

If this is right, the studies' blocks figures (times as well as distances from the course) include cutting across the inside of four corners per mission, and v0.18.0's 16 m lookahead was chosen on that course.

Prior art: none needed for the mechanism; this is an audit of the study harness. The context record (where along the course each sample was) is new to these studies.

## Design

Every mission is flown by `pace_m.fly` as pace-m's `long20`: v0.18.0's pilot on a real rover (`pace_l.py`'s `bridge120+cf0.3` with the compass-bias learner on 20 m stretches). Only the planner and the path follower's lookahead change.

Planners:
- `diag`: the studies' `CoursePlanner`, unchanged (`pace_o.LegPlanner` with keep off returns exactly its path).
- `keep`: `pace_o.keep_points`. As `leg_points`, except that the segment leading into the leg counts too: if the rover is nearest to it (it has not yet reached the point the leg starts from), the path goes through that point first. Everywhere else the path is `leg_points`' own.

Both count `behind`: the plans made while the rover was nearest the segment leading into the leg (where the two planners differ).

Variants:
- `diag16`: `diag`, 16 m (v0.18.0's real-rover pilot as the studies fly it; pace-n's `look16`);
- `keep16`: `keep`, 16 m;
- `keep8`: `keep`, 8 m;
- `keep24`: `keep`, 24 m.

Profiles (pace_l.py's, cruise 0.8, pace_study's three courses): `outage90` (90 s GPS outages after a mean of 600 s of sky; a steady compass error) and `drift90` (outage90 with pace_d.py's drifting compass error, SD 10°, 120 s time constant). **Seeds 229-252** (none flown before). 4 × 2 × 3 × 24 = **576 missions**.

The context record: every 1 s while the rover drives forward, its true position is read (only read), with whether the GPS is in an outage. Each sample is placed by its position along the course (the nearest point of the course): **checkpoint** if from 20 m before to 60 m after an interior checkpoint (not the last); else **corner** if within 20 m of a path corner (pace-n's: an interior point, not a checkpoint, where the course turns by at least 45°); else **other**. Separately it is **outage** or **fix**. For each context the record gives the samples' distance from the course (`median_m`, `p95_m`, `max_m`) and `far`, how many were more than 8 m from it. Blocks has 4 interior checkpoints (all right-angle corners) and 9 path corners; bayside and boulevard have 3 interior checkpoints each and no path corners.

Before the study, `--check` flies seeds 205-207 of pace-n's outage90 and drift90 `look16` missions again as `diag16` (18 missions) and compares every field with pace-n's record.

Output fields: `verdicts` compare, paired by seed per course, `keep16` with `diag16`, and `keep8` and `keep24` with `keep16`. "Faster" or "slower" means a paired sign test with p < 0.05 (`groups_faster`, `groups_slower`); `groups_lost` counts courses where the variant compared with completed fewer missions; `pair_effect` gives each course's `median_time_diff_share`. `context` gives per profile, variant, course and context `p95_m` (the median over missions with a sample there of each mission's 95th percentile), `far` and `far_share` (that context's far samples as a share of the group's far samples). `planner` gives `median_behind`. `offset` gives `median_offset_m` and `p95_offset_m` for the whole mission, and `corner` pace-n's corner record.

## Predictions

Each is graded from those output fields.

- **O1.** The check: compared 18, identical 18, missing 0.
- **O2.** All 576 missions are completed.
- **O3.** The studies' planner plans from behind the corner: on blocks, `diag16`'s `median_behind` is at least 3 on both profiles.
- **O4.** The far samples are at the checkpoints: on blocks, `diag16`'s checkpoint `p95_m` is at least 3 m above both its corner `p95_m` and its other `p95_m`, and its checkpoint `far_share` is at least 0.5, on both profiles.
- **O5.** Keeping the corner removes them: on blocks, `keep16`'s checkpoint `p95_m` is at least 3 m below `diag16`'s, and its whole-mission `p95_offset_m` at least 2 m below `diag16`'s, on both profiles.
- **O6.** Keeping the corner costs time on blocks only: `keep16` against `diag16` is slower (p < 0.05) on blocks on both profiles with `median_time_diff_share` at least +0.005, and on bayside and boulevard its `median_time_diff_share` is between −0.005 and +0.005 on both profiles.
- **O7.** With the corner kept, 16 m still beats 8 m: `keep8` against `keep16` has `groups_faster` 0 on both profiles, and is slower (p < 0.05) on blocks and on bayside on both profiles.
- **O8.** 24 m costs no time: `keep24` against `keep16` has `groups_slower` 0 and `groups_lost` 0 on both profiles.
- **O9.** With a drifting compass a longer lookahead holds the rover further to one side: on drift90, `keep24`'s `median_offset_m` is above `keep16`'s on bayside and on boulevard.

Why these:
- O3: the leg is planned at the report, from the pilot's estimate, which is behind the rover and so before the corner. An outage over a checkpoint can delay the report until the rover is past it (reports need a fix), so 3 of 4, not 4.
- O4 and O5: the diagonal begins about 10-16 m inside the corner and closes over 100 m, so for the first 60 m after the checkpoint the rover is several metres off; near path corners pace-n measured 3.3-5.2 m at 16 m. With `keep` a checkpoint corner should look like a path corner.
- O6: going round the corner instead of across it adds roughly 5-10 m per checkpoint corner, 4 per mission on blocks: about 1-3% of a 1,600 s mission. On bayside and boulevard the checkpoints are on gentle bends, so the two planners' paths differ by little.
- O7: pace-n's 16 m gain was 3.6-3.9% on blocks and 0.7-1.2% on bayside. Bayside has no checkpoint corners, so that part does not depend on the planner; on blocks the nine path corners remain. How much of the blocks gain survives is not predicted.
- O8: pace-n's gain grew from 8 to 12 to 16 m with no course slower. A 24 m lookahead cuts bayside's curves a little more (shorter) and turns earlier at corners. This is the prediction most likely to miss: past some lookahead, cutting curves and corners should start to cost.
- O9: pace-n's N8 (lookahead × tan(heading error)): 24 × tan 6.5° ≈ 2.7 m against 1.8 m at 16 m.

## Decision rules

- **R1.** If the check finds any difference, nothing from this study is published as a finding, and nothing changes until the difference is explained.
- **R2 (the studies' planner).** If `keep16`'s blocks checkpoint `p95_m` is below `diag16`'s on both profiles, the studies from pace-p on fly with `pace_o`'s `keep` planner, and v0.18.1 (documentation only) states in the README and FINDINGS that the blocks course's figures in pace-b through pace-n include cutting across the inside of its four checkpoint corners, giving `keep16`'s blocks figures next to them. Otherwise the studies' planner stays and only the results are documented. The pilot itself is not changed by R2.
- **R3 (the lookahead), only if R2 applies.** `keep8` or `keep24` qualifies if, against `keep16` on both profiles: `groups_slower` 0 and `groups_lost` 0; its blocks corner `p95_m` (pace-n's corner record) is not above `keep16`'s; its `p95_offset_m` is at most 0.5 m above `keep16`'s on every course; and `groups_faster` is at least 1 on some profile. If one qualifies, v0.19.0 gives a real rover's path follower its lookahead (`PATH_LOOKAHEAD_M`, at the command-line layer only); if both, the one with more `groups_faster` summed over both profiles, then the shorter. Otherwise 16 m stays.
- **R4.** Whatever the outcome, the grade and the outputs are published in studies/pace-o/ with the code. O2-O9 decide nothing beyond what R1-R3 read from the fields.

Limits:
- Simulated rovers only (pace_l.py's measured Mini+ profile), so speeds are upper bounds on what a sidewalk allows.
- The courses are three idealised shapes, and sidewalk width is not modelled, so "distance from the course" stands in for "off the sidewalk".
- `keep` is closer to the OSM planner at a checkpoint corner, but it is not the OSM planner: on a real map the nearest node can also be behind the rover or on another street.
- The 20 m / 60 m window and the 8 m "far" mark are choices made here, before any mission is flown; other windows would split the samples differently.
- None of this has been measured on a live Mini+.
