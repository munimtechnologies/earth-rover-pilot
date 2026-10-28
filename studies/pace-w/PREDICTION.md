# pace-w: should the GPS average start again after a gap, now that the stuck check has a warm-up? (pre-registered)

MV2 of Munim, Inc. Written with AI agents. CC BY 4.0.

This file is committed to main before any pace-w mission is flown. The job that flies them (`pace-w-v1`) waits until this file is on main. It also needs rover_pilot.py 0.19.0, `pace_v.py` as pace-v-v1 ran it (SHA-256 79ad43ed…) with `test_pace_v.py`, and `test_stuck_warmup_default.py`. It records this file's SHA-256 and the time it fetched main (`fetched.json`). The study code (`pace_w.py`, `test_pace_w.py`) will be published with the grade, byte for byte as the job ran it. No clock time is written here: the commit history and the job log show the order.

## Why

`GpsFilter`, as it ships, keeps its exponential average through a GPS outage and blends the first fix after it with the average from before it. After 90 s without fixes the pilot's idea of where it is jumps about 57 m back along the course, and it takes about 19 s to come within 10 m of the rover again (studies/pace-r/TRACE.md). pace-s flew `restart`, which starts the average again from the fix after more than 3 s without a valid reading. It removed the jump (the median of each mission's largest position error fell from 55-63 m to 10-12 m) but was slower on 6 of 24 outage90 boulevard seeds, so it failed its rule (studies/pace-s/GRADE.md). trace-s found why: a freshly restarted average lags the rover for about 10 s, and the stuck check, which judges on that average, called a moving rover stuck (studies/pace-s/TRACE.md).

pace-t and pace-u then flew `restart` together with a 10 s warm-up for the stuck check. Against the warm-up alone it was never slower and never lost a mission. It was faster on bayside and blocks on every profile (a median 2-20 s a mission), tied on boulevard, and kept the median largest error at 9.95-11.50 m against 35-63 m (studies/pace-u/GRADE.md). Their rule R3 could only adopt it on top of an adopted warm-up, and neither study adopted one. pace-v did (studies/pace-v/GRADE.md): v0.19.0 gives a real rover's stuck check a 10 s warm-up after every clear of its history (`warm10`). pace-w asks the R3 question again, as a confirmation on fresh seeds. It compares against v0.19.0's real-rover pilot, takes its tolerances from the measured seed-to-seed spread as pace-v did, and adds rovers blocked at the start and mid-route, which pace-u's single 30 s block did not cover.

Prior art: restarting a filter or tracker after a gap in measurements (track re-initiation, rather than coasting through the gap) is standard practice in tracking. Nav2's progress checker (ROS 2) is the same idea as `Pilot._stuck`. We found nothing that measures how re-initialising the position estimate interacts with a progress check that judges on that estimate, or what that costs or gains an open GPS-checkpoint pilot built for the Earth Rover challenge. pace-s, pace-t and pace-u measured it, in simulation, and pace-w is the confirmatory run that decides it.

## Design

| variant | GPS average | stuck check | seeds |
|---|---|---|---|
| `warm10` | `GpsFilter` as it ships (alpha 0.3) | v0.19.0's real-rover check: no verdict until 10 s after every clear of its history | 445-468 |
| `restart+warm10` | the same average, started again from the fix after more than 3 s (`GpsFilter`'s max_age_s) without a valid reading: `pace_q.py`'s `TrackingGpsFilter` with beta 0, which is pace-s's `restart` and pace-u's `restart+warm10` | as `warm10` | 445-468 |
| `warm10:B` | as `warm10`, flown only to measure the seed-to-seed spread | as `warm10` | 469-492 |

The warm-up is flown by `pace_v.py`'s `_warming`. `test_stuck_warmup_default.py` (v0.19.0) shows that it flies exactly as `Pilot.stuck_warmup_s = 10` on four of pace-v's recorded missions. Every mission is flown by `pace_w.fly` as `pace_v.fly` flies it: v0.18.2's real-rover pilot and `pace_p.py`'s `keep16`. A test checks that `warm10` flies exactly as `pace_v.fly`'s `warm10` and `restart+warm10` as `pace_u.fly`'s. Profiles are pace-v's six: outage90, quiet90, quietdrift90 and quiet45, plus `blockedstart` and `blockedmid` (quiet90 with a block of 30-60 s drawn per seed by `pace_v.block_window`, at the start or starting 240-600 s in). Every profile except quiet45 has 90 s outages; quiet45's are 45 s. Cruise is 0.8, on pace_study's three courses. 6 profiles × 3 variants × 3 courses × 24 seeds = **1296 missions**.

Before the study, `--check` flies 7 recorded missions again. Four are pace-v `warm10` missions (time and recovery-move times): outage90 boulevard 397, quiet90 blocks 397, blockedstart boulevard 397 and blockedmid boulevard 415. Three are pace-s `restart` missions without a warm-up (time, recovery moves and filter restarts): outage90 boulevard 338 (trace-s's 94 s loss) and 339, and quiet90 boulevard 338.

Output fields (as in pace-v, unless noted):
- `worst` per (profile, variant, course): `median_max_m` (the median over missions of the largest distance between where the pilot thinks it is and where it is) and `over_snap` (missions whose largest error is over 20 m).
- `stuck`: `early` (missions whose first recovery move came before 30 s).
- `block` per blocked (profile, variant, course): `eligible`, `missed`, `median_catch_s`.
- `gps`: `median_restarts` for `restart+warm10`.
- `verdicts` for the pair (`warm10`, `restart+warm10`), paired by seed per course. "Faster" or "slower" means a paired sign test with p < 0.05 (`groups_faster`, `groups_slower`); `groups_lost` counts courses where `restart+warm10` completed fewer missions.
- `tolerance`: `corner_spread_m` is the largest |`warm10` − `warm10:B`| in blocks corner `p95_m` over the six profiles, and `offset_spread_m` is the largest such difference in `p95_offset_m` over every profile and course. `corner_tol_m` is `corner_spread_m` rounded up to a multiple of 0.05 m and never below 0.25 m. `offset_tol_m` is the same for the offset, never below 0.5 m (pace-v's formula).
- `corner` (`p95_m`, `median_past_m`) and `offset` (`p95_offset_m`).

## Predictions

Each is graded from those output fields.

- **P1.** The check: 7 compared, 7 identical.
- **P2.** All 1296 missions are completed.
- **P3 (the jump, as v0.19.0 ships).** For `warm10`, on every course of the five 90 s profiles, `median_max_m` is at least 45 m and `over_snap` is at least 15 of 24. On every quiet45 course `median_max_m` is between 25 and 45 m.
- **P4 (restart removes it).** For `restart+warm10`, `median_max_m` is at most 15 m on every course of all six profiles. `over_snap` is at most 4 of 24 on every quietdrift90 course and at most 1 on every course of the other five profiles.
- **P5 (no false alarm at the start).** `early` is 0 for both `warm10` and `restart+warm10` on every course of outage90, quiet90, quietdrift90 and quiet45.
- **P6 (faster).** Against `warm10`, `restart+warm10`'s `groups_faster` is at least 2 on every one of the six profiles.
- **P7 (never slower).** Against `warm10`, `restart+warm10`'s `groups_slower` and `groups_lost` are 0 on every one of the six profiles.
- **P8 (blocked rovers).** On every course of `blockedstart` and `blockedmid`, `restart+warm10`'s `eligible` is at least 12, its `missed` is at most `warm10`'s, and its `median_catch_s` is within 1.0 s of `warm10`'s.
- **P9 (how often it restarts).** `restart+warm10`'s `median_restarts` is between 3 and 9 on every course of every profile.
- **P10 (corners and the course).** On every profile, `restart+warm10`'s blocks corner `p95_m` is at most `warm10`'s + `corner_tol_m`. On every profile and course, its `p95_offset_m` is at most `warm10`'s + `offset_tol_m`.
- **P11 (the spread).** `corner_spread_m` and `offset_spread_m` are each between 0.25 and 2.0 m.

Why these:
- P3, P4, P9: in pace-u, `warm10`'s `median_max_m` was 55.2-63.3 m with `over_snap` 18-20 on the 90 s profiles, and 35.2-36.5 m with `over_snap` 24 on quiet45. `restart+warm10` had 9.95-11.50 m, with `over_snap` 0 everywhere except quietdrift90 (2-3, from the drifting compass while bridging), and a median of 4-8 restarts.
- P5: pace-v's `warm10` and pace-u's `restart+warm10` had no early move on these profiles. A restart comes only after a gap of more than 3 s, and such a gap already clears the stuck history (the pilot stops or bridges), so the warm-up covers the restarted average's first seconds.
- P6, P7: in pace-u, `restart+warm10` against `warm10` was faster on bayside and blocks on every profile, including blocked30, and was slower on no course. On boulevard it tied (median 0 s). quietdrift90 boulevard was slower on 6 seeds and faster on 3 (p 0.51), so P7 is the prediction most at risk.
- P8: a block stops the rover but not the fixes, so the filter does not restart because of it. Mid-route, both averages have long caught up with the rover by the time a block begins, so both should catch it at the same time. An outage inside the first 30 s of a block makes a mission ineligible for both variants alike.
- P10: in pace-u, `restart+warm10`'s blocks corner `p95_m` was lower than `warm10`'s on every profile, and its `p95_offset_m` was at most 0.07 m above.
- P11: pace-v measured 0.94 m (corner) and 1.40 m (offset) between two seed sets of the shipped pilot. `warm10` should spread about as much.

## Decision rules

- **R1.** If the check finds any difference, nothing from this study is published as a finding, and nothing changes until the difference is explained.
- **R2 (restart on a real rover).** `restart+warm10` qualifies if all of these hold:
  - against `warm10`, on every one of the six profiles: `groups_slower` 0 and `groups_lost` 0;
  - its `early` is at most 2 of 24 on every course of outage90, quiet90, quietdrift90 and quiet45;
  - on every course of `blockedstart` and `blockedmid`: its `eligible` is at least 12 and its `missed` is at most `warm10`'s;
  - its `p95_offset_m` is at most `warm10`'s + `offset_tol_m` on every profile and course;
  - on every profile, its blocks corner `median_past_m` is at least 0 m and its blocks corner `p95_m` is at most `warm10`'s + `corner_tol_m`;
  - its `median_max_m` is below `warm10`'s on every course of the five 90 s profiles.

  If `corner_tol_m` or `offset_tol_m` is missing, it does not qualify. If it qualifies, v0.20.0 adds a restart option to `GpsFilter` (default off, so the simulator and every earlier study fly as before). The command line turns it on for a real rover, and a test checks that a Pilot built that way flies exactly as `pace_w.py`'s `restart+warm10` on recorded missions. If it does not qualify, a real rover keeps the GPS average across gaps, and the results are documented only.
- **R3.** Whatever the outcome, the grade and the outputs are published in studies/pace-w/ with the code. P2-P11 decide nothing beyond what R1 and R2 read from the fields.

## Limits

- Simulated rovers only (`pace_l.py`'s measured Mini+ profile), so speeds are upper bounds on what a sidewalk allows.
- The outages are idealised: the fixes stop and start cleanly. On a real Mini+ the first fixes after an outage can be poor, and a restart that starts from one bad fix would carry its error until the average settles. The filter's jump check still drops a fix that is far off, but how often a real first fix is poor is not measured here.
- A block is a rover that can turn but not move, with its wheels still turning. How often a real Mini+ gets stuck is not measured.
- The 3 s gap that triggers a restart is `GpsFilter`'s existing max_age_s and is not tuned here.
- R2 was written after reading pace-s's, pace-t's and pace-u's results for this same variant. Those grades stand as published, and pace-w flies fresh seeds.
- None of this has been measured on a live Mini+.
