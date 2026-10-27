# pace-v: a warm-up only after a stand, tested on blocks of many lengths, at the start and mid-route (pre-registered)

MV2 of Munim, Inc. Written with AI agents. CC BY 4.0.

This file is committed to main before any pace-v mission is flown. The job that flies them (`pace-v-v1`) waits until it is on main. It also needs rover_pilot.py 0.18.5, 0.18.6 or 0.18.7 (the pilot code is the same in all three, and in 0.18.2), `pace_u.py` as pace-u-v1 ran it (SHA-256 916fd5e8…) with `test_pace_u.py`, and `pace_t.py` as pace-t-v1 ran it (3c89c187…) with `test_pace_t.py`. It records this file's SHA-256 and the time it fetched main (`fetched.json`). The study code (`pace_v.py`, `test_pace_v.py`) will be published with the grade, byte for byte as the job ran it. No clock time is written here: the commit history and the job log show the order.

## Why

The shipped stuck check (`Pilot._stuck`) judges progress on the smoothed GPS. It calls the rover stuck about 9 s after nearly every start, though nothing holds it: the average starts from rest and lags (studies/pace-s/TRACE.md). pace-t and pace-u showed that a warm-up removes this. Both used a warm-up of 5 s or 10 s after *every* clear of the stuck history, and neither met its pre-stated rule (studies/pace-t/GRADE.md, studies/pace-u/GRADE.md). trace-u (studies/pace-u/TRACE.md, a diagnostic) found why pace-u's two warm-ups missed:

1. **Short stops restart the warm-up.** On seed 388 two GPS reports in a row were dropped, and the pilot stopped for about 1 s with no fix. That stop cleared the history, so a warm-up after every clear started again, and the blocked rover was caught 12 s late. A short stop leaves the GPS average still metres behind the rover, so it needs no warm-up.
2. **The average's lag sets a floor.** The average needs about 6-7 s of real driving to move the check's 1.5 m. Any verdict that falls in the first seconds after a block ends calls a free rover stuck. Which variant pays depends on where its verdict cycle meets the end of the block. pace-u flew a single 30 s block, and the 5 s warm-up's cycle happened to land there.

The false alarm needs an average that has caught up with a **standing** rover. pace-v flies a warm-up that comes only then: **`warmstand10`** waits 10 s at the mission's first check and after a **stand**, meaning a gap of 3 s or more between stuck checks with no recovery move in it (a stop for a lost fix or stale telemetry, or a hold at a checkpoint). After a recovery move or a short stop it judges as the check ships, and a clear never cuts short a warm-up that is already running.

pace-v also changes how a blocked rover is tested, to fix faults that pace-t's and pace-u's rules had. Every change below was decided after reading pace-u's grade and trace-u, and before any pace-v mission was flown.

- **Blocks of many lengths, at the start and mid-route.** Each seed draws its own block length between 30 and 60 s. On `blockedstart` the block starts at 0 s. On `blockedmid` it starts at a time drawn between 240 and 600 s. No variant's verdict cycle can line up with a single block length.
- **The blocked test compares each variant with the shipped check.** pace-u asked for an absolute "every eligible mission caught". pace-v asks that a warm-up miss no more blocked rovers than the shipped check does. A mission is **eligible** if no GPS outage and no stand overlapped the first 30 s of its block. It is **caught** if a recovery move came within 30 s of the block's start. Short stops (under 3 s) do *not* make a mission ineligible, so a variant that loses time to them pays for it.
- **Tolerances come from measured noise.** pace-u failed both warm-ups on a corner figure that was 0.02 m beyond a fixed 0.25 m tolerance, a tolerance it never checked against the seed-to-seed spread. pace-v flies the shipped pilot a second time on a disjoint seed set (`a0.3:B`, seeds 421-444). It sets each tolerance from the spread between the two sets, using a formula fixed here.

Prior art: as in pace-t and pace-u. Nav2's progress checker (ROS 2) fails the controller if the robot has not moved `required_movement_radius` within `movement_time_allowance`, which is the same idea as `Pilot._stuck`. Neither Nav2 nor anything we found measures how a lagging position estimate makes such a check fire falsely after a stand, or how a warm-up keyed to stands trades false alarms against late catches. pace-v is that measurement, in simulation, for an open GPS-checkpoint pilot built for the Earth Rover challenge.

## Design

| variant | stuck check | seeds |
|---|---|---|
| `a0.3` | `Pilot._stuck` as it ships | 397-420 |
| `warm10` | no verdict until 10 s after every clear of the stuck history (pace-u's `warm10`, pace-t's `warm`) | 397-420 |
| `warmstand10` | no verdict until 10 s after the first check or after a stand (a gap of ≥ 3 s between checks with no recovery move); other clears leave a running warm-up as it is and start none | 397-420 |
| `a0.3:B` | as `a0.3`, flown only to measure the seed-to-seed spread | 421-444 |

The GPS filter is as it ships (alpha 0.3) in every variant. Every mission is flown by `pace_v.fly` as `pace_u.fly` flies it: v0.18.2's real-rover pilot and `pace_p.py`'s `keep16`. A test checks that `a0.3` and `warm10` fly exactly as `pace_u.fly`'s. Profiles: outage90, quiet90, quietdrift90 and quiet45 as in pace-u; `blockedstart` and `blockedmid` are quiet90 with the block above. The rover can turn but cannot move inside a block, and its wheels still report the commanded speed. Blocks are drawn from a generator of their own (`block_window`), so the rover's other draws are unchanged. A test checks that a 0-30 s block flies exactly as pace-u's `blocked30`. Cruise 0.8, pace_study's three courses. 6 profiles × 4 variants × 3 courses × 24 seeds = **1728 missions**.

Before the study, `--check-u` flies 8 of pace-u's missions again and compares each one's time and recovery-move times with pace-u's record (`studies/pace-u/runs-<profile>.jsonl`). Three of them are `blocked30` missions flown through pace-v's own block: seed 388's late catch, and two catches that came 2 s late after a dropped first report.

Output fields:
- `stuck` per (profile, variant, course), over the completed missions: `early` (missions whose first recovery move came before 30 s), `late`, `stands`, `median_first_s`.
- `block` per blocked (profile, variant, course): `eligible`, `caught`, `missed` (eligible but not caught), `caught_any`, `median_catch_s` (seconds after the block's start, over eligible catches), `post` (recovery moves that began within 10 s after the block ended, when the rover was free again) and `post_missions`.
- `verdicts` for the pairs (`a0.3`, `warm10`), (`a0.3`, `warmstand10`) and (`warm10`, `warmstand10`), paired by seed per course. "Faster" or "slower" means a paired sign test with p < 0.05 (`groups_faster`, `groups_slower`), and `groups_lost` counts courses where the variant completed fewer missions.
- `tolerance`: `corner_spread_m` is the largest |`a0.3` − `a0.3:B`| in blocks corner `p95_m` over the six profiles. `offset_spread_m` is the largest such difference in `p95_offset_m` over every profile and course. `corner_tol_m` is `corner_spread_m` rounded up to a multiple of 0.05 m, and never below 0.25 m. `offset_tol_m` is the same for the offset, never below 0.5 m.
- `corner` (`p95_m`, `median_past_m`) and `offset` (`p95_offset_m`), as in pace-u.

## Predictions

Each is graded from those output fields.

- **P1.** The check against pace-u: 8 compared, 8 identical.
- **P2.** All 1728 missions are completed.
- **P3 (the false alarm, as shipped).** For `a0.3` on quiet90, quietdrift90 and quiet45, `early` is at least 20 of 24 on every course.
- **P4 (both warm-ups remove it).** On every course of outage90, quiet90, quietdrift90 and quiet45, `early` is 0 for `warm10` and at most 1 of 24 for `warmstand10`.
- **P5 (a rover blocked at the start).** On `blockedstart`, for every variant and course: `eligible` is at least 20. `missed` is 0 for `a0.3` and `warmstand10`, and at most 2 for `warm10`.
- **P6 (how soon, at the start).** On `blockedstart`, `median_catch_s` is at most 11.5 s for `a0.3`, and between 18.5 and 21.5 s for `warm10` and `warmstand10`, on every course.
- **P7 (a rover blocked mid-route).** On `blockedmid`, for every variant and course: `eligible` is at least 12 and `median_catch_s` is between 12 and 26 s. `missed` is at most 1 for `a0.3` and `warmstand10`.
- **P8 (moves after the block).** On `blockedstart`, summed over the three courses, `warm10`'s `post` is lower than `a0.3`'s, and `warmstand10`'s `post` is at least `warm10`'s.
- **P9 (the time).** `warm10` and `warmstand10` are each faster than `a0.3` (p < 0.05) on every course of quiet90, quietdrift90 and quiet45 (`groups_faster` 3 on each).
- **P10 (never slower without a block).** Against `a0.3`, `warm10`'s and `warmstand10`'s `groups_slower` and `groups_lost` are 0 on outage90, quiet90, quietdrift90 and quiet45.
- **P11 (pace-u's corner tolerance was inside the noise).** `corner_spread_m` is above 0.25 m, and `offset_spread_m` is at most 0.5 m.

Why these:
- P3, P4, P9, P10: pace-u gave 22-24 of 24 for `a0.3`, 0 for `warm10`, and `warm10` faster on all 9 quiet courses and slower on none of the four profiles. `warmstand10` is the same as `warm10` from the start until its first clear, so the start should look the same. P4 allows `warmstand10` one early move per course, for a short stop during the first seconds that restarts the history with no new warm-up.
- P5, P6: a blocked rover with GPS is first called stuck at 9.1 s as shipped and 19.1 s with a 10 s warm-up, or 2 s later if the first report was dropped (pace-u). `warmstand10` keeps its warm-up through a short stop, so seed-388-like stops should cost it nothing. `warm10` restarts its warm-up and can miss; such double drops come about once in 40 missions in the first 20 s. An outage starts in a block's first 30 s in about 5% of missions.
- P7: mid-route the history is not cleared when the block begins. After the rover stops, the average still has to close its lag of about 6 m, and the check then needs a window with less than 1.5 m of movement. A rough calculation puts the first verdict about 18-20 s after the block starts, for every variant. Holds at checkpoints, bridged gaps and outages make some missions ineligible or late. The 240-600 s start sits within the span when outages are drawn, so `eligible` may fall well below 24. This is the most uncertain prediction.
- P8: after a block ends, the average needs about 6-7 s of driving before the check stops calling the rover stuck. The shipped check repeats every 15.1 s while blocked (9.1 s plus the 6 s recovery move), `warm10` every 25.1 s, and `warmstand10` every 15.1 s after its first catch. With block lengths spread over 30-60 s, the share of block ends that land inside that 6-7 s window should scale with 1 / cycle.
- P11: pace-u's warm-ups and `a0.3` differed by 0.27 m on one profile's corner `p95_m`, a 95th percentile of about 216 corner passes. On a disjoint seed set the shipped pilot should move that much too.

## Decision rules

- **R1.** If the check finds any difference, nothing from this study is published as a finding, and nothing changes until the difference is explained.
- **R2 (a warm-up on a real rover).** A warm-up W (`warm10` or `warmstand10`) qualifies if all of these hold:
  - against `a0.3`, on every one of the six profiles: `groups_slower` 0 and `groups_lost` 0;
  - its `early` is at most 2 of 24 on every course of outage90, quiet90, quietdrift90 and quiet45;
  - on every course of `blockedstart` and `blockedmid`: its `eligible` is at least 12 and its `missed` is at most `a0.3`'s `missed` on that course;
  - its `p95_offset_m` is at most `a0.3`'s + `offset_tol_m` on every profile and course;
  - on every profile, its blocks corner `median_past_m` is at least 0 m and its blocks corner `p95_m` is at most `a0.3`'s + `corner_tol_m`.

  If `corner_tol_m` or `offset_tol_m` is missing, nothing qualifies. If both qualify, a real rover gets `warmstand10`, unless `warmstand10` against `warm10` has `groups_slower` or `groups_lost` above 0 on any profile, in which case it gets `warm10`. If only one qualifies, it gets that one. v0.19.0 then adds `stuck_warmup_s` (default 0) to `Pilot`, and for `warmstand10` also `stuck_stand_s` (default None, a warm-up after every clear; with a number, a warm-up only at the first check and after a stand at least that long with no recovery move). The defaults keep today's verdicts, so the simulator and every earlier study fly as before. The command line gives a real rover's pilot the chosen values, and a test checks that `Pilot`'s verdicts match `pace_v._warming`'s. If neither qualifies, a real rover keeps today's stuck check and the results are documented only.
- **R3.** Whatever the outcome, the grade and the outputs are published in studies/pace-v/ with the code. P2-P11 decide nothing beyond what R1 and R2 read from the fields.

## Limits

- Simulated rovers only (`pace_l.py`'s measured Mini+ profile), so speeds are upper bounds on what a sidewalk allows.
- A block is a rover that can turn but not move, with its wheels still turning. A real snag can be different (a wheel caught, a kerb that lets it rock), and how often a real Mini+ gets stuck is not measured.
- The 3 s stand threshold, the 10 s warm-up, the 30 s catch window and the 10 s post-block window were chosen from trace-u's timings and are not tuned here. Only one warm-up length is flown.
- The rule changes listed under "Why" were made after seeing pace-t's and pace-u's results. Those grades stand as published.
- The outages are idealised, and the three courses have corners of only 90° or under 25° and no sidewalk width.
- None of this has been measured on a live Mini+.
