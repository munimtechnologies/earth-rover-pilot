# pace-s: should the GPS average start again after a gap? (pre-registered)

MV2 of Munim, Inc. Written with AI agents. CC BY 4.0.

This file is committed to main before any pace-s mission is flown. The job that flies them (`pace-s-v1`) waits until this file is on main, along with rover_pilot.py 0.18.4 or 0.18.3 (the pilot code is the same in both, and in 0.18.2), `pace_q.py` as pace-q-v1 ran it (SHA-256 e65c9b56…) with `test_pace_q.py`, and `studies/pace-r/runs.jsonl` as pace-r-v1 wrote it (486ce42e…). It records this file's SHA-256 and the time it fetched main (`fetched.json`). The study code (`pace_s.py`, `test_pace_s.py`) will be published with the grade, byte for byte as the job ran it. No clock time is written here: the commit history and the job log show the order.

## Why

`trace_r.py` (`studies/pace-r/TRACE.md`, a diagnostic, not pre-registered) flew pace-r's outage90 boulevard mission on seed 313 again and logged it once a second. It found the cause of the shipped pilot's 63.7 m position error. It was not a bad fix. `GpsFilter` keeps its exponential average (alpha 0.3) through a GPS outage, and the first fix after the outage is averaged with the average from before it. The dead reckoner had carried the pilot's estimate to within 7.2 m of the rover through 90 s without fixes. Then the first new fix moved it to 0.3 × the fix + 0.7 × the 90-second-old average, 56.6 m back along the course. It took about 19 s, at 30% of the way per fix, to come back within 10 m. The same happened after all three of that mission's outages (peaks 64.3, 63.0 and 52.7 m). The jump check does not catch it, because the jump it allows grows with the time since the last fix: 3 m/s × about 92 s + 10 m is about 290 m. The rover stayed on the boulevard only because the error lay along a straight course.

`pace_r.py`'s record shows the same thing across the board. 65 of the shipped pilot's 72 outage90 missions had a largest position error over 20 m (most between 57 and 65 m), and 65 of 72 on quietdrift90 too. Every mission with none stayed at or under 17.6 m. pace-q's alpha-beta tracker starts again from the fix after a gap, and none of its 72 outage90 missions in pace-r went over 11.8 m.

The same code path is in rover_pilot.py 0.18.4: `GpsFilter.update` and `Pilot._position`. With the command line's `dead_reckon_gaps`, `Pilot._position` uses the smoothed GPS as soon as a fix is fresh again. A real rover running v0.18.x would therefore jump back by about 70% of the distance it drove through any GPS gap longer than 3 s. This study asks whether the plain fix, starting the average again from the first fix after a gap, removes the jump and costs nothing else.

Prior art: restarting or reinitialising a recursive filter after a measurement gap is standard tracking practice (track initiation after coasting; Bar-Shalom, Li and Kirubarajan, *Estimation with Applications to Tracking and Navigation*, 2001). What this study adds is the measurement of the fault and of the fix in an open GPS-checkpoint pilot built for the Earth Rover challenge, with the rule for changing a real rover's pilot written down first.

## Design

| variant | GPS filter |
|---|---|
| `a0.3` | `GpsFilter`, alpha 0.3, as it ships |
| `restart` | the same average, started again from the fix after more than 3 s (`GpsFilter.max_age_s`) without a valid reading. This is pace-q's `TrackingGpsFilter` with beta 0: its velocity stays 0, so it is `GpsFilter` except for the restart (tests check both) |

Every mission is flown by `pace_s.fly` as `pace_q.fly` flies it: v0.18.2's real-rover pilot (`pace_p.py`'s `keep16`: `pace_m.py`'s `long20` learner on `pace_l.py`'s `bridge120+cf0.3`, `pace_o.py`'s `keep` planner, a 16 m lookahead), with only the GPS filter changed. A test checks that `a0.3` flies exactly as `pace_q.fly`'s `a0.3`. `restart` also restarts after the simulator's short GPS dropouts (more than 3 s without a fix), not only after outages, and the `gps` record counts every restart.

Profiles: pace-q's outage90 (90 s GPS outages after a mean of 600 s of sky, a steady compass error, the simulator's 1.5 m of GPS noise per axis), quiet90 (the same with 0.22 m), quietdrift90 (pace_l.py's drift90 with 0.22 m), and **quiet45** (pace_l.py's outage45, 45 s outages after a mean of 300 s of sky, with 0.22 m). Cruise 0.8, pace_study's three courses. **Seeds 325-348** (none flown before). 4 × 2 × 3 × 24 = **576 missions**.

Before the study, `--check` flies seeds 311-313 of pace-r's outage90 and quiet90 `a0.3-16` missions again as `a0.3` (18 missions, including the traced boulevard mission on seed 313) and compares every field with pace-r's record.

Output fields: `worst` per (profile, variant, course): over the completed missions, `median_max_m` (the median of each mission's largest position error), `largest_m`, and `over_snap` (missions whose largest position error is over 20 m). Also, as in pace-r: `verdicts` for `restart` against `a0.3`, paired by seed per course. "Faster" or "slower" means a paired sign test with p < 0.05 (`groups_faster`, `groups_slower`), `groups_lost` counts courses where `restart` completed fewer missions, and `pair_effect` gives each course's `median_time_diff_share` (negative is faster). `position` (`median_position_err_m`), `corner` (`p95_m`, `median_past_m`: how far past each path corner the rover got, below 0 meaning it turned before it), `offset` (`p95_offset_m`) and `gps` (`median_restarts`) are also as in pace-r.

## Predictions

Each is graded from those output fields.

- **P1.** The check: compared 18, identical 18, missing 0.
- **P2.** All 576 missions are completed.
- **P3 (the jump, as shipped).** For `a0.3`, on outage90, quiet90 and quietdrift90, `median_max_m` is at least 40 m and `over_snap` is at least 18 of 24, on every course.
- **P4 (shorter outages, shorter jumps).** For `a0.3` on quiet45, `median_max_m` is between 20 and 40 m on every course.
- **P5 (the fix).** For `restart`, `median_max_m` is at most 15 m and `over_snap` at most 2 of 24, on every profile and course.
- **P6 (the lag is otherwise the same).** On every profile and course, `restart`'s `median_position_err_m` is no more than 0.1 m above `a0.3`'s and no more than 1.0 m below it.
- **P7.** `restart`'s `groups_slower` is 0 on every profile.
- **P8.** `restart`'s `groups_lost` is 0 on every profile.
- **P9 (corners).** On every profile, `restart`'s blocks corner `median_past_m` is at least 0 m and within 0.5 m of `a0.3`'s.
- **P10 (the time question).** On outage90 and on quiet90, `restart` is faster than `a0.3` on blocks (p < 0.05), with a `median_time_diff_share` between −0.03 and 0.

Why these:
- P3: the jump is about 0.7 × (the distance driven through the outage plus the average's lag before it): 0.7 × (90 s × about 0.88 m/s + about 6 m), about 60 m, wherever a mission meets an outage on a long enough stretch. pace-r's seeds 301-324 gave 65 of 72 such missions on two of these profiles. P4: half as long an outage gives about 0.7 × (45 × 0.88 + 6), about 32 m, and less where a corner falls inside the outage.
- P5: without the jump, the largest errors left are the average's lag when an outage starts (about 10.4 m before the reckoner takes over after 3 s) and the reckoner's drift through 90 s. The shipped missions that had no jump peaked at 9.7-17.6 m.
- P6: between gaps `restart` is the shipped average. Right after each gap, including the short dropouts, it starts from a fix that is only about 1.3 m old instead of an average about 6 m behind. That can only make the median slightly smaller.
- P7-P9: on a straight course the jump lies along the course and costs nothing, and between gaps the two filters are the same.
- P10: where an outage ends after a corner the rover turned on the reckoner, the shipped pilot's estimate jumps back to before the corner, and its aim from there points off the new leg until the average catches up. This is the prediction most likely to miss: the cost may be too small, too rare or too mixed to show on 24 seeds, or not there at all.

## Decision rules

- **R1.** If the check finds any difference, nothing from this study is published as a finding, and nothing changes until the difference is explained.
- **R2 (the GPS filter on a real rover).** `restart` qualifies if, against `a0.3`, on every profile: `groups_slower` 0 and `groups_lost` 0; its blocks corner `median_past_m` is at least 0 m and its blocks corner `p95_m` at most 0.25 m above `a0.3`'s; its `p95_offset_m` is at most 0.5 m above `a0.3`'s on every course; and its `median_max_m` is below `a0.3`'s on every course of outage90, quiet90, quietdrift90 and quiet45.

  Unlike pace-q's and pace-r's rules, R2 asks for no time saving. Those studies tried speed changes. This one fixes an estimation fault, a position estimate that throws away 90 s of dead reckoning, and the rule asks only that the fix removes it and costs nothing that is measured. The corner conditions are pace-q's, unchanged.

  If `restart` qualifies, v0.19.0 adds a `restart_s` setting to `GpsFilter`. Its default, None, keeps the average across gaps, so the simulator and every earlier study fly as before. The command line gives a real rover's pilot `restart_s` = 3.0, and a test checks that `GpsFilter(restart_s=3.0)` matches `TrackingGpsFilter(alpha=0.3, beta=0.0)` fix for fix. Otherwise a real rover keeps the shipped filter, and the results are documented in v0.18.5 (documentation only).
- **R3.** Whatever the outcome, the grade and the outputs are published in studies/pace-s/ with the code. P2-P10 decide nothing beyond what R1 and R2 read from the fields.

## Limits

- Simulated rovers only (pace_l.py's measured Mini+ profile), so speeds are upper bounds on what a sidewalk allows.
- The outages are idealised: the GPS gives no fix at all for exactly 45 or 90 s, and its fixes come back with the same noise as before. Real receivers often come back from an urban canyon with a few poor fixes first. A restart then adopts one poor fix, which the average would have damped. 0.22 m and 1.5 m of independent noise per fix bracket that, but a 10 m multipath fix right after an outage is not modelled.
- `restart` starts from the raw fix. Starting the average from the reckoner's estimate and blending the fix in is another possible fix, and is not tested here.
- Three idealised courses, with corners of only 90° or under 25°, and no sidewalk width.
- The 20 m threshold in `over_snap` and the 3 s restart time were chosen before any pace-s mission was flown, from pace-r's published record and `GpsFilter.max_age_s`.
- None of this has been measured on a live Mini+.
