# pace-e: what the compass-bias learner does under noise (pre-registered)

MV2 of Munim, Inc. Written with AI agents. CC BY 4.0.

This file is committed to main before any pace-e mission is flown. The job that flies them (`pace-e-v1`) waits until this file is on main, and records its SHA-256 and the time it fetched main (`fetched.json`). The study code (`pace_e.py`, `test_pace_e.py`) will be published with the grade, byte for byte as the job ran it; the job records its SHA-256 too. No clock time is written here: the commit history and the job log show the order.

## Why

pace_d.py (studies/pace-d/GRADE.md) found something it had not predicted. With 10° of fresh compass noise, the shipped pilot (rover_pilot 0.12.0) never learned its compass bias: in all 72 such missions it steered with the whole −25° error the simulator gives it. With `--smooth-heading` it learned the bias. Under a slow drift (10°, 120 s), the learner took out almost none of the drift (Q8 missed).

The bias learner (`HeadingEstimator`) fits a line through the GPS fixes of each straight stretch and compares its course with the mean compass reading. Two of its gates sit close to 10° of noise:
- **straight-stretch test**: a stretch counts only while the low-passed `angular` command stays within ±0.1 (`max_angular`). At the steering gain of 1/60 per degree, 0.1 is 6° of heading error, so 10° of noise on each reading pushes the command past it every few readings. A stretch must last about 10 s and 5 GPS fixes to be fitted.
- **compass-spread test**: a fitted stretch is used only if the mean resultant length of its compass readings is at least 0.985 (`max_spread`). For Gaussian noise of standard deviation σ, that length is about e^(−σ²/2): 0.9986 at 3°, 0.9945 at 6°, 0.9903 at 8°, 0.9849 at 10°, 0.9783 at 12°.

Our expectation is that the straight-stretch test is the one that stops it. With 10° of noise, the low-passed command should go past ±0.1 on a large share of ticks, and a stretch needs about 100 ticks in a row within it. So few fits ever reach the spread test.

## Design

Every profile is pace_b.py's `measured` Mini+: orientation every 0.5 s, 48°/s per unit of `angular`, 0.5 s latency, GPS every 2 s (1.5 s behind the wheels), a constant −25° compass error to learn. The rover is pace_d.py's `DistortedRover`, which flies exactly as `MeasuredRover` when undistorted.

| profile | compass |
|---|---|
| measured | 3° of noise per reading |
| noise6, noise8 | 6°, 8° |
| measured-noise10 | 10° |
| noise12 | 12° |
| drift10 | 3°, plus pace_d.py's drift (SD 10°, time constant 120 s) |

| variant | change |
|---|---|
| shipped | none |
| cf0.3 | `--smooth-heading` (the pilot's own `HeadingSmoother`, `SMOOTH_HEADING`) |
| spread0.95 | `max_spread` 0.95 |
| straight0.3 | `max_angular` 0.3 |
| both | `max_spread` 0.95 and `max_angular` 0.3 |

Cruise 0.8 (the `--marathon` cruise). pace_study's three courses (boulevard, blocks, bayside; 1.3-1.6 km). Seeds 1-12. 6 × 5 × 3 × 12 = **1,080 missions**.

In every mission a counting subclass of `HeadingEstimator` (it decides exactly as the plain one) records: `calibrations`; `breaks`, the straight stretches cut off by a turn or by slowing down; `fits`, the stretches long enough to fit; `spread_checked`, the fits that reached the spread test; `spread_rejected`, those it turned down; the median spread of the checked fits; and `bias_error_deg`, the learned bias plus the compass error at the end of the mission (0 = fully cancelled). Once a second of simulated time while driving forward, it also records `offset`: how far the simulated rover really is from the course (its nearest segment). The heading error is recorded as in pace_d.py.

Outputs: `summary.json` (`learner`, `offset`, `heading`, `verdicts`, `largest`, `variant_effect`, `profile_tallies`, `check`), `runs.jsonl`, `report.md`. Comparisons with the shipped pilot are paired by seed per course; "slower" or "faster" means a paired sign test with p < 0.05. Per course, the `learner` and `offset` rows give the median over the completed missions.

## Predictions

Each is graded from those output fields.

- **Q1.** All 1,080 missions are completed (`completed`).
- **Q2.** The check: the 216 shipped and cf0.3 missions on measured, measured-noise10 and drift10 give exactly the fields pace_d.py recorded for them in studies/pace-d/runs.jsonl (`check.identical` = 216, `missing` = 0).
- **Q3.** The finding, counted. (measured-noise10, shipped): `median_calibrations` is 0 on every course, and `zero_calibration_missions` is at least 10 of 12 on every course. (measured-noise10, cf0.3): `median_calibrations` is at least 1 on every course.
- **Q4.** More noise, fewer calibrations. For the shipped pilot on each course, `median_calibrations` never rises along measured → noise6 → noise8 → measured-noise10 → noise12, and it is at least 1 on measured.
- **Q5.** The straight-stretch test is what stops it. (measured-noise10, shipped): `spread_checked_per_mission` is below 1.0 on every course. (measured-noise10, spread0.95): `median_calibrations` is 0 on every course.
- **Q6.** Loosening the straight-stretch test brings the learning back. (measured-noise10, straight0.3) and (measured-noise10, both): `median_calibrations` is at least 1 on every course. For both, `median_abs_bias_error_deg` is below 10 on every course.
- **Q7.** No harm, and little time at stake. `both` is slower than the shipped pilot in none of the 18 profile × course groups (`verdicts` `groups_slower` 0 on each of the 6 profiles). On measured-noise10, its `largest_median_diff_share` against shipped has \|value\| < 0.01.
- **Q8.** The unlearned bias shows as an offset from the path. (measured-noise10, shipped): `median_offset_m` is between 2.5 and 5.0 m on boulevard and on blocks. (measured, shipped): below 2.0 m on every course. (measured-noise10, both): below (measured-noise10, shipped)'s on every course.
- **Q9.** Under the drift, more fits help. (drift10, both): the `heading` row's `median_abs_deg` is below (drift10, shipped)'s on every course.

Why these:
- Q3-Q5 follow from the gates above.
- In Q6, one accepted fit is enough to learn most of the bias, because the first fit sets it outright.
- Q7: pace_d.py showed that an error that lasts makes the rover crab rather than weave, and crabbing costs little time.
- Q8: with the path follower's 8 m lookahead, a lasting 25° error balances when the rover is 8 × tan 25° ≈ 3.7 m to one side of its path.
- No prediction is made for noise6, noise8 or noise12 beyond Q4. They show where learning stops.

## Decision rules

- **E1.** A loosened learner becomes the default in the next release only if all of these hold: (a) on measured-noise10 its `median_calibrations` is at least 1 and its `median_offset_m` is below shipped's on every course; (b) it is slower than shipped in none of the 18 groups; (c) on measured, its `median_offset_m` is at most 0.2 m above shipped's on every course. Take the first that qualifies, in this order: straight0.3, spread0.95, both. The release must fly that variant's pace-e missions exactly with the new default (a whole-mission equality test, as v0.12.0 did for `--smooth-heading`).
- **E2.** If none qualifies, the pilot is unchanged. README and FINDINGS say that with about 10° of compass noise or more the shipped pilot does not learn its compass bias, and name `--smooth-heading` as the way to get it learned if Q3's cf0.3 part held.
- **E3.** If Q5 fails because fits do reach the spread test (`spread_checked_per_mission` ≥ 1.0) and are turned down there, the spread test is named as a cause in README and FINDINGS.
- **E4.** If Q2 fails, nothing from this study is published as a finding until the difference is explained.
- **E5.** Whatever the outcome, the grade and the outputs are published in studies/pace-e/ with the code, and the results go into FINDINGS-frodobots-2k.md and the README.

Limits: simulated rovers only, so speeds and offsets are upper bounds on what a real sidewalk allows. The noise is Gaussian and independent from one reading to the next, and how noisy a real Mini+ compass is has not been measured. The offset is measured to the nearest segment of the course, which on corners understates how far the rover is from the leg it is driving.
