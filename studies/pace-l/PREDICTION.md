# pace-l: does the 120 s reach hold up when the wheels and the compass lie? (pre-registered)

MV2 of Munim, Inc. Written with AI agents. CC BY 4.0.

This file is committed to main before any pace-l mission is flown. The job that flies them (`pace-l-v1`) waits until this file, `studies/pace-k/GRADE.md`, `studies/pace-k/runs.jsonl` and pace-k's `pace_k.py` (SHA-256 92b1642f…) are on main. It records this file's SHA-256 and the time it fetched main (`fetched.json`). The study code (`pace_l.py`, `test_pace_l.py`) will be published with the grade, byte for byte as the job ran it. No clock time is written here: the commit history and the job log show the order.

## Why

v0.16.0 lets the bridging reckoner (the real-rover default) carry the position up to 120 s after the last GPS fix, because pace-k (9 of 9 predictions held) found it faster than 30 s and 60 s on every course through 90 s outages and slower nowhere. pace-k's limit was stated in its grade and the release: in the simulator the wheels report the commanded speed exactly and never slip, so the reckoned position hardly drifted. On a real rover two things lie during an outage. The wheels' metres per RPM change with the ground (grass, gravel, kerbs), so the scale learned on earlier straight stretches is wrong for a while. And the compass error drifts, while the pilot can only correct its compass bias against GPS courses. Both errors grow with every second on the wheels alone, which is what the 120 s reach adds.

Prior art: wheel slip and terrain-dependent odometry scale are well known, which is why navigation filters cap dead-reckoning time (PX4's EKF2, for example). This study does not propose a method. It checks whether the cap v0.16.0 chose for this pilot still pays when the wheels and compass err in these two simple ways.

## Design

Rover (`pace_l.SlipRover`, a `pace_j.WanderRover` that drives exactly as before):
- **slip**: the wheels report a factor times their true RPM. Each spell's factor is drawn uniformly from [0.85, 1.15]; spells last 120 s on average (exponential), from a generator of their own seeded by the mission seed. With no slip the rover reports exactly what a WanderRover does.
- **drift**: pace_d.py's drifting compass error (Ornstein-Uhlenbeck, SD 10°, 120 s time constant), as in pace-d's `drift10`.

Profiles (pace_k.py's measured Mini+, cruise 0.8, pace_study's three courses):
- `outage45`, `outage90`: pace_k.py's profiles exactly (45 s outages after a mean of 300 s of sky; 90 s after 600 s);
- `lie45`: outage45 with slip and drift;
- `slip90`, `drift90`, `lie90`: outage90 with slip, with drift, with both.

Variants: pace_k.py's three, unchanged: the bridging pilot with the reckoner's reach at 30 s (`bridge+cf0.3`), 60 s (`bridge60+cf0.3`) or 120 s (`bridge120+cf0.3`, v0.16.0 on a real rover). Every mission is flown by pace_j.py's own `fly`. **Seeds 157-180** (none flown before). 6 × 3 × 3 × 24 = **1,296 missions**.

Before the study, `--check` flies seeds 133-135 of pace-k's outage45 and outage90 missions for `bridge+cf0.3` and `bridge120+cf0.3` again (36 missions) through pace_l.py's own rover (with no slip) and compares every field with pace-k's record.

Output fields: `verdicts` compare reaches on the same profile, paired by seed per course: 60 s against 30 s, 120 s against 30 s, 120 s against 60 s. "Faster" or "slower" means a paired sign test with p < 0.05 (`groups_faster`, `groups_slower`); `groups_lost` counts courses where the first completed more missions. `profile_verdicts` and `profile_effect` compare each variant on a lying profile against itself on the honest one (lie45 against outage45; slip90, drift90 and lie90 against outage90), same seeds and outages; `median_time_diff_share` is the median paired difference over the honest profile's median time. `overview` gives `beat_human_pace` per profile and variant; `position` gives `p95_position_err_m` per course.

## Predictions

Each is graded from those output fields.

- **L1.** The check: compared 36, identical 36, missing 0.
- **L2.** All 1,296 missions are completed.
- **L3.** The 120 s reach still beats 60 s when the wheels and compass lie: on slip90, drift90 and lie90, `bridge120+cf0.3` against `bridge60+cf0.3` has `groups_faster` at least 2, `groups_slower` 0 and `groups_lost` 0.
- **L4.** And 60 s still beats 30 s through lying 45 s outages: on lie45, `bridge60+cf0.3` against `bridge+cf0.3` has `groups_faster` 3, `groups_slower` 0, `groups_lost` 0.
- **L5.** The lies never help: in `profile_verdicts`, `groups_faster` is 0 for every variant on every lying profile.
- **L6.** They cost little: on lie90 against outage90, `bridge120+cf0.3`'s `median_time_diff_share` is below +0.05 on every course.
- **L7.** They cost the long reach more: on lie90 against outage90, `bridge120+cf0.3`'s `median_time_diff_share` is larger than `bridge+cf0.3`'s on at least 2 of 3 courses.
- **L8.** The pilot knows less well where it is: `bridge120+cf0.3`'s `p95_position_err_m` on lie90 is above its own on outage90, and above `bridge60+cf0.3`'s on lie90, on every course.
- **L9.** Marathon pace: `bridge120+cf0.3`'s `beat_human_pace` is at least 66 of 72 on slip90, drift90 and lie90.

Why these:
- L3: in pace-k a 120 s reach saved 36-59 s a mission over 60 s on outage90, by not standing still for the last ~30 s of each outage (about 2-3 outages a mission). A 90 s outage at the rover's ~0.63 m/s is ~57 m on the wheels; a scale off by up to 15% puts it up to ~8.5 m off along the route, and 10° of compass drift up to ~10 m across it, within the checkpoints' 15 m tolerance, and the pilot never reports a checkpoint without a fix. The detour to recover should cost a few seconds an outage, less than the standing still it replaces.
- L4: a 45 s outage gives the lies only 15 s more on the wheels at 60 s than at 30 s, against ~15 s less standing still per outage.
- L5, L6: slip only matters while the wheels steer (outages); the drift also moves the compass on clear sky, where the pilot's bias learner follows it against GPS courses, as in pace-d.
- L7: with a 30 s reach the pilot stands still through most of a 90 s outage, and standing still costs nothing when the wheels or compass lie.
- L8: `position` is sampled only while driving, and with 60 s the pilot stands still for the last ~30 s of each 90 s outage, when the reckoned position would be furthest off.
- L9: pace-k's bridge120 beat the human pace (0.754 m/s) in 72 of 72 outage90 missions at a median 0.864 m/s, 15% above it.

## Decision rules

- **R1.** If L1 is not failed and `bridge120+cf0.3` against `bridge60+cf0.3` has `groups_slower` 0 and `groups_lost` 0 on all six profiles, the 120 s reach stays. The next release (v0.16.1) only adds pace-l's results to the README and FINDINGS.
- **R2.** If R1 does not apply but `bridge60+cf0.3` against `bridge+cf0.3` has `groups_slower` 0 and `groups_lost` 0 on all six profiles, v0.16.1 sets the real-rover default's reach to 60 s.
- **R3.** If neither applies, v0.16.1 sets it back to 30 s, and the README says on which profiles and courses a longer reach was slower or lost missions.
- **R4.** If the check finds any difference, nothing from this study is published as a finding until the difference is explained.
- **R5.** Whatever the outcome, the grade and the outputs are published in studies/pace-l/ with the code. L2-L9 decide nothing beyond what R1-R3 read from the verdicts.

Limits: simulated rovers only, so speeds are bounds on what a real sidewalk allows. The slip is one simple model (a scale that changes in spells; no wheel spinning in place, no one-sided slip turning the rover: the reckoner steers by the compass, not by the wheels' difference, so one-sided slip would show up as the rover turning, which the compass sees). The drift is pace-d's model. Outages are clean cut-outs of fixed length. None of this has been measured on a live Mini+.
