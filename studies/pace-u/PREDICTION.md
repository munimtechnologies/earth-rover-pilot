# pace-u: the stuck detector's warm-up again, 5 s or 10 s, with a fair stuck test (pre-registered)

MV2 of Munim, Inc. Written with AI agents. CC BY 4.0.

This file is committed to main before any pace-u mission is flown. The job that flies them (`pace-u-v1`) waits until it is on main. It also needs rover_pilot.py 0.18.6 or 0.18.5 (the pilot code is the same in both, and in 0.18.2), `pace_t.py` as pace-t-v1 ran it (SHA-256 3c89c187…) with `test_pace_t.py`, `pace_s.py` as pace-s-v1 ran it (343feeb8…) with `test_pace_s.py`, and `studies/pace-s/runs.jsonl` (180cd541…). It records this file's SHA-256 and the time it fetched main (`fetched.json`). The study code (`pace_u.py`, `test_pace_u.py`) will be published with the grade, byte for byte as the job ran it. No clock time is written here: the commit history and the job log show the order.

## Why

pace-t (`studies/pace-t/GRADE.md`, 8 of 10 predictions held) flew a **warm-up** for `Pilot._stuck`: no stuck verdict until 10 s after the stuck history was last cleared. It removed the false recovery move that the shipped check makes about 9 s after every start. That move fired in 22-23 of 24 missions per course with quiet GPS, and in no warm-up mission. The warm-up was faster than the shipped check on all 9 quiet courses and slower on none. On a rover blocked for its first 30 s it made its first recovery move at 19.1-21.1 s instead of 9.1-11.1 s.

The warm-up still failed pace-t's rule R2. R2 asked for a recovery move before 30 s in every blocked mission, and the warm-up made one in 22 of 24 per course. The two misses were the same two seeds on every course. On seed 352 even the shipped check gave no verdict. In both, the rover stood still for 88.5 s with no fix: a GPS outage began while it was blocked, before the dead reckoner could bridge it, and the block was over when the fixes came back. Those missions took exactly as long with the warm-up as without it. A rover with no GPS fix stands still and cannot make a recovery move, and does not need one. pace-t did not record when the outages began, so that cause is inferred.

pace-u flies the warm-up again on **fresh seeds**. It records each mission's first outage start (`first_outage_s`, from the same windows the simulated rover draws). For the blocked test, it counts only missions whose GPS stayed up until the block was over. This change was prompted by pace-t's result and is stated here before any pace-u mission is flown. pace-t's grade stays published as it is. pace-u also flies a **5 s warm-up**, which would catch a really stuck rover about 5 s sooner. A fake pilot that never moves is first called stuck at 9.25 s with no warm-up, 14.25 s with 5 s and 19.25 s with 10 s (`test_pace_u`). It also flies pace-s's GPS restart with each warm-up. Unless it qualifies under R3, a real rover keeps the average across gaps.

Prior art: as in pace-t. Nav2's progress checker (ROS 2) fails the controller if the robot's pose has not moved `required_movement_radius` within `movement_time_allowance`, which is the same idea as `Pilot._stuck`. Fault-detection work on robots documents that a stricter detector delays real detections. A web search before pace-t found no published measurement of how often an open GPS-checkpoint pilot's stuck detector fires falsely after a start, a stop or a filter restart, or of what a warm-up costs and gains. pace-u adds a replication on fresh seeds, a second warm-up length, and a blocked test that separates "not caught" from "no GPS to judge by".

## Design

| variant | stuck check | GPS filter |
|---|---|---|
| `a0.3` | `Pilot._stuck` as it ships | `GpsFilter`, alpha 0.3, as it ships |
| `warm5` | no verdict until 5 s after the stuck history was last cleared, then `Pilot._stuck` as it ships | as it ships |
| `warm10` | the same with 10 s (pace-t's `warm`) | as it ships |
| `restart+warm5` | as `warm5` | pace-s's `restart`: the same average, started again from the fix after more than 3 s without one |
| `restart+warm10` | as `warm10` | as `restart+warm5` (pace-t's `restart+warm`) |

Every mission is flown by `pace_u.fly` as `pace_t.fly` flies it (v0.18.2's real-rover pilot, `pace_p.py`'s `keep16`), with `pace_t._warming` for the warm-up. A test checks that `a0.3`, `warm10` and `restart+warm10` fly exactly as `pace_t.fly`'s `a0.3`, `warm` and `restart+warm`. Profiles are pace-t's: outage90 (90 s GPS outages after a mean of 600 s of sky, the simulator's 1.5 m of GPS noise), quiet90 (0.22 m), quietdrift90 (0.22 m and a drifting compass), quiet45 (45 s outages after a mean of 300 s, 0.22 m) and blocked30 (quiet90 with a rover that cannot move, but can turn, for its first 30 s). Cruise 0.8, pace_study's three courses. **Seeds 373-396** (none flown before). 5 × 5 × 3 × 24 = **1800 missions**.

Two checks run before the study. `--check` flies pace-s's outage90 and quiet90 `a0.3` missions on seeds 325-327 again (18 missions) and compares every field with pace-s's record. `--check-t` flies 11 of pace-t's missions again: both blocked30 seeds without a recovery move, the late recovery moves on quietdrift90 blocks, and quiet90 boulevard seed 349. It compares each one's time and recovery-move times with pace-t's record.

Output fields: `stuck` per (profile, variant, course), over the completed missions: `with_recovery`, `recoveries`, `early` (missions whose first recovery move came before 30 s), `late` (recovery moves at or after 30 s), `eligible` (missions whose first GPS outage began at or after 30 s, the end of blocked30's block), `early_eligible` (eligible missions whose first recovery move came before 30 s), `median_first_s` and `latest_first_s`. `verdicts` for the pairs (`a0.3`, `warm5`), (`a0.3`, `warm10`), (`warm10`, `warm5`), (`warm5`, `restart+warm5`) and (`warm10`, `restart+warm10`), paired by seed per course, as in pace-t. "Faster" or "slower" means a paired sign test with p < 0.05 (`groups_faster`, `groups_slower`), and `groups_lost` counts courses where the variant completed fewer missions. `pair_effect` gives each course's `median_time_diff_share`. `worst` (`median_max_m`, `over_snap`), `corner` (`p95_m`, `median_past_m`) and `offset` (`p95_offset_m`) are as in pace-t.

## Predictions

Each is graded from those output fields.

- **P1.** The checks: against pace-s, 18 compared, 18 identical, 0 missing; against pace-t, 11 compared, 11 identical.
- **P2.** All 1800 missions are completed.
- **P3 (the false alarm, as shipped).** For `a0.3` on quiet90, quietdrift90 and quiet45, `early` is at least 20 of 24 on every course.
- **P4 (10 s removes it).** For `warm10` and `restart+warm10`, `early` is 0 on every course of outage90, quiet90, quietdrift90 and quiet45.
- **P5 (5 s removes it too).** For `warm5` and `restart+warm5`, `early` is at most 2 of 24 on every course of the same four profiles.
- **P6 (no new late moves).** For `warm5` and `warm10`, `late` is at most `a0.3`'s `late` + 1 on every course of the same four profiles.
- **P7 (a stuck rover is caught).** On blocked30, for every variant and course, `eligible` is at least 20 and `early_eligible` equals `eligible`.
- **P8 (how soon).** On blocked30, `median_first_s` is at most 11.5 s for `a0.3`, between 13.5 and 16.5 s for `warm5` and `restart+warm5`, and between 18.5 and 21.5 s for `warm10` and `restart+warm10`, on every course.
- **P9 (the time).** `warm5` and `warm10` are each faster than `a0.3` (p < 0.05) on every course of quiet90, quietdrift90 and quiet45 (`groups_faster` 3 on each).
- **P10 (never slower).** Against `a0.3`, `warm5`'s and `warm10`'s `groups_slower` and `groups_lost` are 0 on every profile, and so are `warm5`'s against `warm10`.
- **P11 (the restart).** `restart+warm5` against `warm5` and `restart+warm10` against `warm10`: `groups_slower` and `groups_lost` 0 on every profile, and both restart variants' `median_max_m` at most 15 m on every course of outage90, quiet90, quietdrift90 and quiet45.

Why these:
- P3, P4: pace-t gave 22-23 of 24 for `a0.3` and 0 for both 10 s variants. On fresh seeds, a GPS outage in the first 10 s can take a mission out of `early`, as on seed 352.
- P5: with 5 s, the stuck window starts at about 5 s, once the rover has been driving for a few seconds. The simulated average then moves several metres in the 9 s the window needs. trace-s measured about 1.3 m in the first 8-9 s after a start, so the false alarm needs most of its lag to come in those first 5 s. This is the prediction most exposed. Two per course leaves room for a slow start.
- P6: a warm-up only delays a verdict, so it should not add verdicts later on. A different moment can still meet or miss an outage, and pace-t's quietdrift90 blocks had 3 late moves with the warm-up against 4 as shipped, so +1 is allowed.
- P7: a blocked rover with GPS is called stuck about 9, 14 or 19 s after the start, all before 30 s. An exponential clear spell of mean 600 s ends before 30 s in about 5% of missions (about 1.2 of 24), so 20 eligible per course leaves room.
- P8: pace-t's blocked30 first moves were 9.1-11.1 s and 19.1-21.1 s. The 5 s warm-up should come 5 s earlier than 10 s. The medians include missions whose first move came late because the GPS went out during the block.
- P9, P10: pace-t's `warm` was faster than `a0.3` on all 9 quiet courses (blocks with a median difference of 0 s, but 10-11 seeds faster and none slower) and slower nowhere. A recovery move costs about 5-7 s. A 5 s warm-up should save the same at the start and catch a blocked rover about 5 s sooner. P10's `warm5` against `warm10` is the prediction most exposed to timing luck, where a few seconds' shift meets or misses an outage at a checkpoint.
- P11: pace-t's `restart+warm` was slower than `warm` nowhere and kept `median_max_m` at 9.9-12.1 m. With 5 s the restart has a shorter warm-up after each outage, when the average starts again from one fix, which is where trace-s found its false alarms.

## Decision rules

- **R1.** If either check finds any difference, nothing from this study is published as a finding, and nothing changes until the difference is explained.
- **R2 (the warm-up on a real rover).** A warm-up W (`warm5` or `warm10`) qualifies if all of these hold:
  - against `a0.3`, on every profile: `groups_slower` 0 and `groups_lost` 0;
  - its `early` is at most 2 of 24 on every course of outage90, quiet90, quietdrift90 and quiet45;
  - on blocked30, on every course: `eligible` is at least 20 and `early_eligible` equals `eligible`;
  - its `p95_offset_m` is at most 0.5 m above `a0.3`'s on every course;
  - its blocks corner `median_past_m` is at least 0 m and its blocks corner `p95_m` at most 0.25 m above `a0.3`'s, on every profile.

  If both qualify and `warm5` against `warm10` has `groups_slower` 0 and `groups_lost` 0 on every profile, a real rover gets **5 s**. Otherwise, if `warm10` qualifies, it gets **10 s**, and if only `warm5` qualifies, **5 s**. In either case v0.19.0 adds a `stuck_warmup_s` setting to `Pilot`. Its default, 0, keeps today's verdicts, so the simulator and every earlier study fly as before. The command line gives a real rover's pilot the chosen value, and a test checks that `Pilot(stuck_warmup_s=W)`'s verdicts match `pace_t._warming`'s. If neither qualifies, a real rover keeps today's stuck check and the results are documented only.
- **R3 (the restart, with the chosen warm-up).** Only if R2 chose a warm-up W: `restart+W` qualifies if, against W, on every profile: `groups_slower` 0 and `groups_lost` 0. Its blocks corner `median_past_m` must be at least 0 m and its blocks corner `p95_m` at most 0.25 m above W's. Its `p95_offset_m` must be at most 0.5 m above W's on every course, and its `median_max_m` below W's on every course of outage90, quiet90, quietdrift90 and quiet45. These are pace-s's R2 conditions, unchanged. If it qualifies, v0.19.0 also adds pace-s's `restart_s` setting to `GpsFilter` (default None; a real rover's pilot gets 3.0). Otherwise a real rover keeps the average across gaps.
- **R4.** Whatever the outcome, the grade and the outputs are published in studies/pace-u/ with the code. P2-P11 decide nothing beyond what R1-R3 read from the fields.

## Limits

- Simulated rovers only (pace_l.py's measured Mini+ profile), so speeds are upper bounds on what a sidewalk allows.
- The only time anything stops the rover is blocked30's first 30 s. A rover stuck mid-route, right after a checkpoint stop or right after an outage, is where a warm-up delays the catch, and that is not flown. How often a real Mini+ gets stuck is not measured.
- R2's blocked condition is looser than pace-t's: it leaves out missions whose GPS went out while the rover was blocked. That was decided after seeing pace-t's two such missions, on which the warm-up lost no time, and pace-t's stricter grade stands.
- Only 5 s and 10 s warm-ups are tried. The outages are idealised, and the three courses have corners of only 90° or under 25° and no sidewalk width.
- None of this has been measured on a live Mini+.
