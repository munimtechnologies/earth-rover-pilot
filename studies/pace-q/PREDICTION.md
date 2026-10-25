# pace-q: does the GPS filter's lag cost time once the GPS is as quiet as a real one? (pre-registered)

MV2 of Munim, Inc. Written with AI agents. CC BY 4.0.

This file is committed to main before any pace-q mission is flown. The job that flies them (`pace-q-v1`) waits until this file, rover_pilot.py 0.18.2 or 0.18.1 (the pilot code is the same in both; 0.18.2 only adds documentation), pace-p's `pace_p.py` (SHA-256 c5234ba5…), `studies/pace-p/GRADE.md` and `studies/pace-p/runs.jsonl` are on main. It records this file's SHA-256 and the time it fetched main (`fetched.json`). The study code (`pace_q.py`, `test_pace_q.py`) will be published with the grade, byte for byte as the job ran it. No clock time is written here: the commit history and the job log show the order.

## Why

In every pace study since pace-g the pilot's own idea of where the rover is has been a median 6.4-6.6 m from where it really is (pace-p: 6.4-6.6 m on all three courses). That number can be worked out from the pilot itself. On a real rover, whenever the GPS has a fresh fix, the pilot steers by `GpsFilter`, an exponential average with alpha 0.3 of fixes that come every 2 s. For a rover at a steady 0.889 m/s (cruise 0.8 on a Mini+), that average lags the fixes by (1 − 0.3) / 0.3 = 2.33 fixes, which is 4.7 s or 4.1 m. Each fix also shows where the rover was 1.5 s before it came (1.3 m), and on average it is read 1 s after it came (0.9 m). Together that is 6.4 m.

The average was kept for a reason. In `gps_noise_study.py` (FINDINGS-frodobots-2k.md, "Keep the smoothing"), a pilot without it (alpha 1) was slower with 14 of 21 rover × GPS-error combinations and needed up to ten times as many back-up moves. But every one of those error models had at least 1.5 m of independent noise per axis on each fix. `frodo_gps.py` later measured recorded Earth Rovers' fixes while driving straight: they scatter only 0.22 m RMS sideways about a line, about six times less (FINDINGS, "How noisy a real Earth Rover's GPS is"). The pace studies still fly the simulator's 1.5 m. With 0.22 m of jitter there is little left to smooth, so the average mostly adds its lag. At a right-angle corner that lag makes the rover turn late. It also matters after a GPS outage: the first fix after 90 s moves the average only 0.3 of the way from where the rover was before the outage, so for several fixes the pilot thinks it is tens of metres behind.

Prior art: the lag of an exponential average of a ramp, and alpha-beta trackers that remove it (Benedict and Bordner, 1962; Kalata, "The tracking index", IEEE Trans. AES 20, 1984), are textbook. Delay compensation in pure-pursuit path tracking is studied as dead-time compensation (for example arXiv:2507.06935). What this study adds is the measurement: on a simulated Earth Rover Mini+ with its measured telemetry and 90 s GPS outages, with the GPS jitter recorded Earth Rovers show and with the simulator's harsher jitter, how much the shipped filter's lag costs in time, at corners and in distance from the course, with the rule for changing the pilot written down first.

## Design

Every mission is flown by `pace_p.fly` as `keep16`: v0.18.2's real-rover pilot (`pace_m.py`'s `long20` learner on `pace_l.py`'s `bridge120+cf0.3`, `pace_o.py`'s `keep` planner, a 16 m lookahead). Only the GPS filter the pilot builds changes (`pace_q._filtering` replaces `rover_pilot.GpsFilter` while a mission is flown):

- `a0.3`: `GpsFilter` as it ships (alpha 0.3);
- `a0.6`: `GpsFilter` with alpha 0.6 (a ramp lag of 0.67 fixes, 1.2 m);
- `raw`: `GpsFilter` with alpha 1, so each new fix is taken as it comes;
- `track`: `pace_q.TrackingGpsFilter`, an alpha-beta filter with alpha 0.3 and beta 0.053 (alpha² / (2 − alpha), Benedict and Bordner's pairing). Each accepted fix is compared with the estimate carried forward at the tracked velocity. The estimate moves alpha of the way to the fix and the velocity beta / dt of the difference, so at a steady speed it settles on the fixes with no lag. After more than 3 s without a valid reading it starts again from the fix with no velocity, because a velocity can't be carried across an outage. It drops bad readings exactly as `GpsFilter` does, and with beta 0 and no restart it is `GpsFilter` (a test checks this reading by reading).

All four keep `GpsFilter`'s checks for jumps and stale fixes. Nothing else in the pilot changes: checkpoint reports still also use the last raw fix, and the compass-bias learner and the wheels' reckoner still get the raw fixes.

Profiles (cruise 0.8, pace_study's three courses: bayside, blocks, boulevard):
- `outage90`: `pace_l.py`'s outage90 (90 s GPS outages after a mean of 600 s of sky, a steady compass error, the simulator's 1.5 m of GPS noise per axis). This is the stress test.
- `quiet90`: outage90 with 0.22 m of GPS noise per axis (frodo_gps.py's measured sideways scatter).
- `quietdrift90`: `pace_l.py`'s drift90 (a compass error that drifts, SD 10°, 120 s time constant) with 0.22 m.

The noise is drawn from the same generator in the same order, so on a seed the fixes differ between profiles only in size. **Seeds 277-300** (none flown before). 4 × 3 × 3 × 24 = **864 missions**.

Before the study, `--check` flies seeds 253-255 of pace-p's outage90 and drift90 `keep16` missions again as `a0.3` (18 missions) and compares every field with pace-p's record.

Output fields: `verdicts` compare each variant with `a0.3`, paired by seed per course. "Faster" or "slower" means a paired sign test with p < 0.05 (`groups_faster`, `groups_slower`). `groups_lost` counts courses where the variant completed fewer missions. `pair_effect` gives each course's `median_time_diff_share` (negative is faster). `profile_verdicts` and `profile_effect` compare each variant on quiet90 with itself on outage90, and on quietdrift90 with itself on quiet90. `position` gives `median_position_err_m`, the median over missions of each mission's median distance between the pilot's position and the rover's true one while driving forward. `corner` is pace-n's corner record (`p95_m`, and `median_past_m`, how far past each path corner the rover got, where below 0 means it turned before the corner). `offset` gives `median_offset_m` and `p95_offset_m` for the whole mission. `gps` gives recovery moves and `track`'s restarts.

## Predictions

Each is graded from those output fields.

- **P1.** The check: compared 18, identical 18, missing 0.
- **P2.** All 864 missions are completed.
- **P3 (the lag).** On quiet90, `median_position_err_m` is between 5.8 and 7.0 m for `a0.3` on every course, below 3.0 m for `raw` and for `track` on every course, and for `a0.6` strictly between `raw`'s and `a0.3`'s on every course.
- **P4 (the question).** On quiet90 and on quietdrift90, `raw` is faster than `a0.3` (p < 0.05) on blocks, and its blocks corner `median_past_m` is lower than `a0.3`'s.
- **P5.** On quiet90 and on quietdrift90, `raw`'s `groups_slower` against `a0.3` is 0.
- **P6.** Turning earlier is not cutting the corner: on quiet90 and on quietdrift90, `raw`'s blocks corner `p95_m` is at most 0.25 m above `a0.3`'s.
- **P7 (the stress test).** On outage90, `raw`'s `p95_offset_m` is above `a0.3`'s on bayside and on boulevard.
- **P8.** Under the stress-test noise, tracking smooths what `raw` doesn't: on outage90, `track`'s `median_position_err_m` is below `raw`'s on every course.
- **P9.** Quieter fixes alone barely change the shipped pilot: `a0.3` on quiet90 against itself on outage90 has `median_time_diff_share` within ±0.01 on every course.
- **P10.** By rule R2 below, at least one of `a0.6`, `raw` and `track` qualifies.

Why these:
- P3 is the arithmetic above. With 0.22 m of jitter the noise adds almost nothing to `a0.3`'s 6.4 m. `raw` keeps only the fix's age: 1.5 s plus a median 1 s since it came, about 2.2 m at 0.889 m/s. `a0.6` adds 1.2 m to that (about 3.4 m). `track` settles on the fixes like `raw`, apart from about 20-30 s after each restart.
- P4: with the 16 m lookahead measured from a position about 6.4 m behind, `a0.3` aims about 10 m ahead of the true rover; `raw` about 14 m. pace-n and pace-o found that aiming further ahead was faster on blocks and turned earlier at its right angles. pace-n's 8 m lookahead ran a median 4.3 m past each corner, 16 m 1.7-2.2 m. `raw` also stops trusting the stale average after each outage at once.
- P5 and P6: on bayside and boulevard there are no right angles to gain at, and with 0.22 m of jitter there is little noise to lose to. A true lookahead of about 14 m is still shorter than the 24 m one (about 17.6 m true) that pace-o and pace-p found cutting corners. This is the prediction most likely to miss.
- P7: unsmoothed 1.5 m jitter moves the point the pilot steers from by about 1.5 m every 2 s, which turns into heading changes of about 5° at a 16 m lookahead. That is what made alpha 1 slower in gps_noise_study.py. Blocks is left out because its p95 offset is set mostly at the corners, where `raw`'s smaller lag may help.
- P8: with alpha 0.3 and beta 0.053 the tracker keeps about half of the noise's standard deviation (a steady-state variance ratio of about 0.24), and, like `raw`, it has no ramp lag.
- P9: the shipped filter already damps 1.5 m of noise to about 0.6 m, so its error is mostly lag on both profiles.
- P10: if P4-P6 hold for `raw`, it passes R2's quiet-profile conditions. On outage90 `raw` or `track` must stay within 1% in the median on every course, and `track` should.

## Decision rules

- **R1.** If the check finds any difference, nothing from this study is published as a finding, and nothing changes until the difference is explained.
- **R2 (the GPS filter on a real rover).** `a0.6`, `raw` or `track` qualifies if, against `a0.3`:
  - on quiet90 and on quietdrift90: `groups_slower` 0 and `groups_lost` 0; its blocks corner `p95_m` is at most 0.25 m above `a0.3`'s; its blocks corner `median_past_m` is at least 0 m (it does not turn before the corner); its `p95_offset_m` is at most 0.5 m above `a0.3`'s on every course; and `groups_faster` is at least 1 on one of the two profiles;
  - on outage90: `groups_lost` 0, and `median_time_diff_share` at most +0.01 on every course.

  If more than one qualifies, the choice goes to the one with more `groups_faster` summed over quiet90 and quietdrift90. If that ties, it goes to the lower sum of `median_time_diff_share` over those six groups, and then to the first in the order `a0.6`, `raw`, `track` (the least new code). If one qualifies, v0.19.0 makes the command line give a real rover's GPS filter that variant's settings (and, for `track`, adds `TrackingGpsFilter` to rover_pilot.py). The simulator and the class defaults are unchanged. Otherwise a real rover keeps alpha 0.3, and the results are documented in v0.18.3 (documentation only).
- **R3.** Whatever the outcome, the grade and the outputs are published in studies/pace-q/ with the code. P2-P10 decide nothing beyond what R1 and R2 read from the fields.

Why R2 differs from pace-p's rule:
- The corner condition is `median_past_m` ≥ 0 m, not 1.0 m. There it caught a longer lookahead that turned before the corners. Here the lag makes the shipped pilot run about 2 m past each corner, and a truer position should cut that overshoot; turning before the corner (below 0) still fails. The `p95_m` and `p95_offset_m` limits are unchanged and still catch cutting across the inside.
- outage90 is only a floor. It is about six times noisier than recorded Earth Rovers' fixes, so a variant only has to not lose a mission and not be more than 1% slower there. It does not have to win.

## Limits

- Simulated rovers only (pace_l.py's measured Mini+ profile), so speeds are upper bounds on what a sidewalk allows.
- quiet90's 0.22 m is the sideways scatter of recorded Earth Rover Zero fixes (2024) over 10 s of straight driving, drawn here as independent noise per fix. The slow wander measured on standing rovers (1.5 m in 60 s) and steady offsets are not modelled, and no exponential average with a time constant of a few seconds would remove them. The Mini+'s receiver may differ.
- The fixes' 1.5 s delay is the simulator's, from FrodoBots-2K; no variant here predicts the rover forward to the present.
- Three idealised courses, with corners of only 90° or under 25°, and no sidewalk width, so "distance from the course" stands in for "off the sidewalk".
- alpha 0.6, beta 0.053 and the 3 s restart are choices made here, before any mission is flown.
- None of this has been measured on a live Mini+.
