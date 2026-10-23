# pace-j: does bridging GPS outages still pay when the GPS wanders first? (pre-registered)

MV2 of Munim, Inc. Written with AI agents. CC BY 4.0.

This file is committed to main before any pace-j mission is flown. The job that flies them (`pace-j-v1`) waits until this file, `studies/pace-i/GRADE.md`, `studies/pace-i/runs.jsonl` and pace-i's `pace_i.py` (SHA-256 d4dc9304…) are on main. It records this file's SHA-256 and the time it fetched main (`fetched.json`). The study code (`pace_j.py`, `test_pace_j.py`) will be published with the grade, byte for byte as the job ran it. No clock time is written here: the commit history and the job log show the order.

## Why

pace-i (`studies/pace-i/GRADE.md`, 7 of 9 predictions held) made bridging GPS outages on the wheels the real-rover default for the next release: through simulated outages of 15 s and 45 s it was 6.3-7.2% faster than v0.14.0's pilot on every course and slower nowhere. But pace-i's outages were clean. The fixes kept their usual noise until the GPS cut out and again as soon as it came back. pace-i's own limits say what is missing: a real GPS often wanders off by metres before it drops out, under trees or beside tall buildings, and again while it recovers. Bridging starts from the last fix before the outage. If that fix has already wandered, the wheels carry the error through the outage. A pilot that stops instead (v0.14.0's) only waits.

Prior art: rejecting GNSS fixes that disagree with odometry is standard in state estimators (for example the Mahalanobis rejection thresholds of ROS robot_localization). This study does not add a gate. It asks a narrower question first: on this rover's measured telemetry and this pilot, does the new default keep its lead when the fixes wander before and after each outage, and what does the wandering cost each pilot?

## Design

Profiles: pace-i's measured Mini+ (pace_h.py's `measured`) with pace-i's outages:
- `outage15`, `outage45`: pace-i's profiles exactly (15 s outages after a mean of 150 s of sky; 45 s after 300 s);
- `wander15`, `wander45`: the same outages, with every one wrapped in wandering fixes. For the 20 s before an outage each fix is moved steadily further off, from 0 to 8 m, in a direction drawn for that outage; through the outage there is no fix; for the 20 s after it the fixes come back from 8 m to 0. The directions come from a generator of their own seeded from the seed, so the rover's own draws and the outages are the same as on the matching outage profile. A drift of 0.4 m/s passes the GPS filter's jump test. The simulated server judges checkpoint reports by the reported fix; a real server also sees only the rover's own GPS.

Variants (pace-i's): `cf0.3` (v0.14.0 on a real rover), `bridge+cf0.3` (the next release's real-rover default), `dr+cf0.3` (v0.13.0). Every mission is flown by pace_i.py's own `fly`, on a rover that adds the wandering. Cruise 0.8, pace_study's three courses, **seeds 109-132** (none flown before). 4 × 3 × 3 × 24 = **864 missions**. Every mission records pace_i.py's fields plus `wander.wandered` (GPS reports moved).

Before the study, `--check` flies seeds 85-87 of pace-i's outage15 `cf0.3` and `bridge+cf0.3` missions again (18 missions) and compares every field with pace-i's record.

Output fields: `verdicts` compare variants on the same profile (pace_i.py's pairs: `bridge+cf0.3` and `dr+cf0.3` against `cf0.3`), paired by seed per course. `profile_verdicts` compare each variant on a wander profile against itself on the matching outage profile, paired by seed per course. "Faster" or "slower" means a paired sign test with p < 0.05 (`groups_faster`, `groups_slower`); `groups_lost` counts courses where the first completed more missions; `median_time_diff_share` is the median paired difference over the first's median time. `overview` gives each profile and variant's pooled `median_made_good_mps` and `beat_human_pace`; `offset` gives the 95th-percentile distance from the course (`p95_offset_m`) and `position` the pilot's 95th-percentile position error (`p95_position_err_m`) per course.

## Predictions

Each is graded from those output fields.

- **J1.** The check: compared 18, identical 18, missing 0.
- **J2.** All 864 missions are completed.
- **J3.** Bridging keeps its lead: on wander15 and on wander45, `bridge+cf0.3` against `cf0.3` has `groups_faster` 3, `groups_slower` 0 and `groups_lost` 0.
- **J4.** Wandering costs bridging a little: in `profile_verdicts`, `bridge+cf0.3` on wander15 against outage15 has `groups_slower` ≥ 2, and every course's `median_time_diff_share` is between 0 and +0.03.
- **J5.** It costs v0.14.0's pilot too: `cf0.3` on wander15 against outage15 has `groups_slower` ≥ 2.
- **J6.** The cost is smaller when outages are rarer: for `bridge+cf0.3`, the pooled `median_made_good_mps` falls by less from outage45 to wander45 than from outage15 to wander15 (strictly).
- **J7.** The rover is held off its course: for `bridge+cf0.3` on bayside, `p95_offset_m` on wander15 is at least 1.5 m above outage15's.
- **J8.** The pilot knows less well where it is: for `bridge+cf0.3`, `p95_position_err_m` on wander15 is at least 1.5 m above outage15's on every course.
- **J9.** Marathon pace: `bridge+cf0.3`'s `beat_human_pace` is 72 on wander15 and at least 66 on wander45.

Why these:
- J3: wandering moves the position every pilot steers by, before and after each outage, alike. Bridging carries the wandered position through the outage, but steering toward a course 8 m to one side for 15-30 s costs a few seconds, while stopping costs the whole outage (pace-i: 119-148 s a mission with 15 s outages, 214-255 s with 45 s).
- J4, J5: the pilot steers so that the wandered position stays on the course, so the rover drifts sideways at up to 0.4 m/s while driving about 0.88 m/s. With a random direction that lengthens the path by roughly 4% during the 40 s of each 165 s cycle, about 1% in all.
- J6: on outage45 the cycle is 345 s, so the wandering takes about half the share of the time.
- J7: on bayside (pace-i's bridging p95 2.95 m on outage15) about a third of the driving time has the rover held up to 8 m to one side by the sideways part of the drift.
- J8: the pilot's position already lags the truth by a median of about 6.4 m (pace-i); an 8 m drift in any direction adds to it for about a third of the time.
- J9: bridging made good 0.870 m/s with 15 s outages and beat the human pace (0.754) in all 72 missions; with 45 s outages, 69 of 72.

## Decision rules

- **R1.** If J1 is not failed and `bridge+cf0.3` against `cf0.3` has `groups_slower` 0 and `groups_lost` 0 on both wander profiles, the bridging default stands, and README and FINDINGS report what wandering costs each pilot.
- **R2.** Otherwise the README says on which courses wandering fixes made bridging slower than v0.14.0's pilot, and the next study, pre-registered, tests gating: steering by the wheels instead of a fresh fix that disagrees with them by more than a set distance. The defaults stay as they are until that study is graded.
- **R3.** If the check finds any difference, nothing from this study is published as a finding until the difference is explained.
- **R4.** Whatever the outcome, the grade and the outputs are published in studies/pace-j/ with the code. J4-J9 decide nothing.

Limits: simulated rovers only, so speeds are bounds on what a real sidewalk allows. The wandering is one simple shape (a straight-line drift out to 8 m and back over 20 s each way, in a random direction); real multipath errors can jump, oscillate or last longer. The simulated wheels report the commanded speed exactly. None of this has been measured on a live Mini+.
