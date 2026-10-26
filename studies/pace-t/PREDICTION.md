# pace-t: should the stuck detector wait before it judges? (pre-registered)

MV2 of Munim, Inc. Written with AI agents. CC BY 4.0.

This file is committed to main before any pace-t mission is flown. The job that flies them (`pace-t-v1`) waits until this file is on main. It also needs rover_pilot.py 0.18.5 or 0.18.4 (the pilot code is the same in both, and in 0.18.2), `pace_s.py` as pace-s-v1 ran it (SHA-256 343feeb8…) with `test_pace_s.py`, and `studies/pace-s/runs.jsonl` as pace-s-v1 wrote it (180cd541…). It records this file's SHA-256 and the time it fetched main (`fetched.json`). The study code (`pace_t.py`, `test_pace_t.py`) will be published with the grade, byte for byte as the job ran it. No clock time is written here: the commit history and the job log show the order.

## Why

`trace_s.py` (`studies/pace-s/TRACE.md`, a diagnostic, not pre-registered) traced the six outage90 boulevard seeds on which pace-s's `restart` was slower than the shipped filter. On five of them, `restart` made one extra **recovery move** (back up, turn, drive on). The pace-s simulator has no obstacles and never blocks the rover, so every one was a false alarm. The cause is in `Pilot._stuck` (rover_pilot.py 0.18.4). It judges progress on the **smoothed** GPS: the rover counts as stuck if the average moved less than 1.5 m over the last 10 s while the pilot asked for at least 0.4 × cruise. The history is cleared at a stop, while bridging a GPS gap, and at each recovery move. After a clear, the next 10 s of the average often move less than 1.5 m even though the rover drives 7-8 m. Its fixes lag about 1.5 s, the rover starts from rest, and an average that has just started from one fix still has to build up its lag. On seed 338 the extra recovery left `restart` 9.8 m short when an outage began 0.8 s after the shipped pilot had finished, and that became 94 s.

The trace also showed the same false alarm in the **shipped** pilot, seconds after every start (9.6 s in every traced mission that had one). In pace-s's record, 241 of the shipped filter's 288 missions made a recovery move, 240 of them exactly one. With GPS as quiet as recorded Earth Rovers' (quiet90, quietdrift90, quiet45), 210 of 216 did, and all six without one were on bayside. On a live rover that move backs up about 0.9 m blind and swings about 43°, on a sidewalk, every time it drives off.

The fix tested here is a **warm-up**: no stuck verdict until 10 s after the stuck history was last cleared. After that, `Pilot._stuck` works exactly as it ships, so its 10 s window starts once the average is moving with the rover. A rover that really cannot move should then be caught about 10 s later than now. pace-t measures that cost on a rover blocked for its first 30 s.

pace-t also flies pace-s's `restart` with the warm-up. pace-s's rule R2 rejected `restart`, and this re-test was prompted by that result and by the trace. It runs on fresh seeds under the same conditions, and pace-s's grade stays published as it is.

Prior art: Nav2's progress checker (ROS 2) works the same way as `Pilot._stuck`. It fails the controller if the robot's pose has not moved `required_movement_radius` within `movement_time_allowance`. Fault-detection work on autonomous robots documents the trade-off that a stricter detector delays real detections, and argues that fewer false positives can be worth a longer delay when recovery is costly (Christensen et al., *Fault Detection in Autonomous Robots Based on Fault Injection and Learning*). Lag in an exponentially smoothed position is a textbook property. A web search this run found no published measurement of how often an open GPS-checkpoint pilot's stuck detector fires falsely after a start, a stop or a filter restart, or of a warm-up's cost and benefit in such a pilot. What this study adds is that measurement, with the rule for changing a real rover's pilot written down first.

## Design

| variant | stuck check | GPS filter |
|---|---|---|
| `a0.3` | `Pilot._stuck` as it ships | `GpsFilter`, alpha 0.3, as it ships |
| `warm` | no verdict until 10 s (`WARMUP_S`) after the stuck history was last cleared, then `Pilot._stuck` as it ships | as it ships |
| `restart+warm` | as `warm` | pace-s's `restart`: the same average, started again from the fix after more than 3 s without one |

Every mission is flown by `pace_t.fly` as `pace_s.fly` flies it: v0.18.2's real-rover pilot (`pace_p.py`'s `keep16`), with only the stuck check and the GPS filter changed. The warm-up wraps `Pilot._stuck`. With a warm-up of 0 its verdicts are `Pilot._stuck`'s own, and a test checks that `a0.3` flies exactly as `pace_s.fly`'s `a0.3`. Each mission's record adds `stuck`: the warm-up and the time of every recovery move.

Profiles: pace-s's outage90 (90 s GPS outages after a mean of 600 s of sky, a steady compass error, the simulator's 1.5 m of GPS noise per axis), quiet90 (the same with 0.22 m), quietdrift90 (a drifting compass with 0.22 m), quiet45 (45 s outages after a mean of 300 s, with 0.22 m), and **blocked30**: quiet90 with a rover that cannot move (it can still turn) for its first 30 s (`SimRover`'s `blocked_until_s`). Cruise 0.8, pace_study's three courses. **Seeds 349-372** (none flown before). 5 × 3 × 3 × 24 = **1080 missions**.

Before the study, `--check` flies seeds 325-327 of pace-s's outage90 and quiet90 `a0.3` missions again (18 missions, including the traced seed 327) and compares every field with pace-s's record.

Output fields: `stuck` per (profile, variant, course), over the completed missions: `with_recovery` (missions that made at least one recovery move), `recoveries`, `early` (missions whose first recovery move came before 30 s), `median_first_s`, `latest_first_s`. `verdicts` for `warm` against `a0.3` and for `restart+warm` against `warm`, paired by seed per course, as in pace-s. "Faster" or "slower" means a paired sign test with p < 0.05 (`groups_faster`, `groups_slower`), and `groups_lost` counts courses where the variant completed fewer missions. `pair_effect` gives each course's `median_time_diff_share` (negative is faster, ties included). `worst` (`median_max_m`, `over_snap`: a largest position error over 20 m), `position`, `corner` (`p95_m`, `median_past_m`) and `offset` (`p95_offset_m`) are as in pace-s.

## Predictions

Each is graded from those output fields.

- **P1.** The check: compared 18, identical 18, missing 0.
- **P2.** All 1080 missions are completed.
- **P3 (the false alarm, as shipped).** For `a0.3` on quiet90, quietdrift90 and quiet45, on every course, `with_recovery` is at least 20 of 24 and `early` is at least 20 of 24.
- **P4 (the warm-up removes it).** For `warm` on outage90, quiet90, quietdrift90 and quiet45, `with_recovery` is at most 2 of 24 on every course.
- **P5 (and the restart's).** For `restart+warm` on the same four profiles, `with_recovery` is at most 2 of 24 on every course.
- **P6 (a stuck rover is still caught).** On blocked30, for every variant and course, `early` is 24 of 24: every mission makes a recovery move before 30 s.
- **P7 (the time).** `warm` is faster than `a0.3` (p < 0.05) on every course of quiet90, quietdrift90 and quiet45, with a `median_time_diff_share` between −0.01 and 0.
- **P8.** `warm`'s `groups_slower` and `groups_lost` are 0 on every profile.
- **P9 (the restart, with the warm-up).** `restart+warm`'s `groups_slower` and `groups_lost` against `warm` are 0 on every profile.
- **P10 (the restart's estimate).** For `restart+warm`, `median_max_m` is at most 15 m on every course of outage90, quiet90, quietdrift90 and quiet45, and `over_snap` is at most 2 of 24 on every course of outage90, quiet90 and quiet45.

Why these:
- P3: pace-s's seeds 325-348 gave 210 of 216 on these profiles, with the lowest course at 22 of 24. Every false alarm traced came at 9.6 s.
- P4-P5: after a clear, the warm-up waits 10 s and `Pilot._stuck` then needs 9 s of its window. By then the rover has driven at cruise for over 10 s, and the average, lagging about 1.5 s of delay plus (1 − 0.3) / 0.3 fixes, moves about as fast as the rover: 7-8 m per window against the 1.5 m threshold. Two per course leaves room for a corner or a slow approach falling inside a window.
- P6: a blocked rover turns toward the course, then is told to drive at cruise while its average does not move. As shipped it is called stuck about 9-10 s after the start, and with the warm-up about 19-20 s after.
- P7: one recovery move takes 6 s (2 s reversing at −0.4, 1.5 s turning at ±0.6, 2.5 s at 0.5) and gains about 0.5 m where cruising gains about 5.3 m: about 5-7 s, or 0.3-0.4% of a 1750-1900 s mission. Where an outage later stops both variants at the same checkpoint until the same moment, the saving vanishes and the pair ties. That can make the median difference 0, so 0 is allowed. Ties do not count in the sign test. On outage90, 1.5 m of noise often moves the average more than 1.5 m by itself (31 of pace-s's 72 shipped missions had a recovery), so no speed-up is predicted there.
- P8: the warm-up only removes verdicts in the first 10 s after a clear. Where the rover is really blocked (blocked30), it delays the first move by about 10 s but can save the later false ones. This is the prediction most exposed to timing luck: a few seconds' shift can meet or miss an outage at a checkpoint (`studies/pace-s/TRACE.md`, seed 338).
- P9: trace-s found the restart's boulevard cost in its extra false recovery moves, and the warm-up removes those. Seed 337's 2 s (one GPS period, with no extra recovery) is not explained, and P9 is the prediction most likely to miss.
- P10: pace-s's `restart` kept `median_max_m` at 9.9-12.5 m. Its `over_snap` was 1-4 only on quietdrift90, where the drifting compass, not the filter, throws the estimate off.

## Decision rules

- **R1.** If the check finds any difference, nothing from this study is published as a finding, and nothing changes until the difference is explained.
- **R2 (the warm-up on a real rover).** `warm` qualifies if, against `a0.3`, on every profile: `groups_slower` 0 and `groups_lost` 0. On blocked30 its `early` must be 24 of 24 on every course. Its `p95_offset_m` must be at most 0.5 m above `a0.3`'s on every course, and its blocks corner `median_past_m` at least 0 m with its blocks corner `p95_m` at most 0.25 m above `a0.3`'s. If it qualifies, v0.19.0 adds a `stuck_warmup_s` setting to `Pilot`. Its default, 0, keeps today's verdicts, so the simulator and every earlier study fly as before. The command line gives a real rover's pilot `stuck_warmup_s` = 10.0, and a test checks that `Pilot(stuck_warmup_s=10.0)`'s verdicts match `pace_t._warming`'s. Otherwise a real rover keeps today's stuck check, and the results are documented in v0.18.6 (documentation only).
- **R3 (the restart, tested again).** `restart+warm` qualifies only if `warm` qualifies under R2 and, against `warm`, on every profile: `groups_slower` 0 and `groups_lost` 0. Its blocks corner `median_past_m` must be at least 0 m and its blocks corner `p95_m` at most 0.25 m above `warm`'s. Its `p95_offset_m` must be at most 0.5 m above `warm`'s on every course, and its `median_max_m` below `warm`'s on every course of outage90, quiet90, quietdrift90 and quiet45. These are pace-s's R2 conditions, unchanged, measured against the warm-up. If it qualifies, v0.19.0 also adds pace-s's `restart_s` setting to `GpsFilter` (default None; a real rover's pilot gets 3.0) with the test pace-s's R2 described. Otherwise a real rover keeps the average across gaps.
- **R4.** Whatever the outcome, the grade and the outputs are published in studies/pace-t/ with the code. P2-P10 decide nothing beyond what R1-R3 read from the fields.

## Limits

- Simulated rovers only (pace_l.py's measured Mini+ profile), so speeds are upper bounds on what a sidewalk allows.
- Nothing in these courses really stops the rover except blocked30's 30 s at the start. How often a real Mini+ gets stuck mid-route (a kerb, a bush, a wheel in a gap), and what catching it 10 s later costs there, is not measured. A rover stuck against an obstacle while its wheels spin is the case the warm-up makes slower.
- The 10 s warm-up was chosen before any pace-t mission was flown, from the trace's arithmetic (the average needs about 5 fixes to build up its lag). Shorter or longer warm-ups are not tested.
- The outages are idealised as in pace-s, and three idealised courses have corners of only 90° or under 25°, and no sidewalk width.
- None of this has been measured on a live Mini+.
