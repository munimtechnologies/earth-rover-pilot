# Pre-registration: smoothing the heading on a Mini+ with a noisy compass (pace_c.py 0.1.0)

Written 2026-10-22 between about 12:40 and 13:00 UTC, before any pace_c result exists; the job copies this file into its output before it flies a mission. By MV2 of Munim, Inc.; the code, predictions and this text were made with AI agents. Licence CC BY 4.0 (text), Apache-2.0 (code).

## Why

`pace_b.py` 0.1.0 (`studies/pace-b/GRADE.md`) flew the pilot on a simulated Mini+ that reports like the public recordings (orientation every 0.5 s, 48°/s per unit of `angular`, 0.5 s latency). 10° of compass noise instead of 3° made every one of 12 cruise × course groups slower, by 2.4-3.1%, and took cruise 0.7 below the human marathon pace (0.750 against 0.754 m/s). Its rule D3 said the next study tests smoothing the heading.

Smoothing should help because the pilot slows by the cosine of its heading error and steers on every reading, so noise costs speed and wiggles the path. It may also hurt: a plain average lags behind real turns, and the pilot steers on the lagging heading. Turning the average by the commanded turn before each update (a complementary filter) should remove most of that lag if the turn rate is right.

## Design (fixed before the run)

- Courses: `pace_study.COURSES` (boulevard 1,552 m, blocks 1,400 m, bayside 1,262 m). Seeds 1-12. Cruise 0.7 and 0.8.
- Pilot: rover_pilot as on main (0.11.2; no change to steering or GPS handling since 0.8.0), `make_steering(False, cruise=...)` = `ROVER_STEERING`, through `pace_study.CoursePlanner`, dead reckoning off; the rover is `pace_b.MeasuredRover`.
- Profiles (from `pace_b.py`): `measured` (3° compass noise) and `measured-noise10` (10°).
- Variants, each a wrapper around the simulated rover (`HeadingSmoother`; the pilot's code is unchanged). On each new orientation report the estimate moves `gain` of the way towards the report, the short way across north, and is held until the next report:
  - `shipped`: no wrapper.
  - `ema0.5`, `ema0.3`: gain 0.5 or 0.3, no turn prediction.
  - `cf0.3`: gain 0.3, the estimate first turned by the angular commanded since the last report at 48°/s per unit, each command landing 0.5 s after it is sent (the profile's true values).
  - `cf0.3-yaw30`: the same, assuming 30°/s (a wrong rate).
- 2 profiles × 5 variants × 2 cruises × 3 courses × 12 seeds = 720 missions.
- Comparisons: each variant against `shipped` on the same profile, seed by seed per cruise × course group (`pace_study.summarise` `verdicts`; faster or slower when the sign test gives p < 0.05, which needs at least 10 of 12 seeds one way). 6 groups per profile and variant.
- Grading reads `summary.json`: `overview` (pooled per profile × variant × cruise, with `beats_on_every_course`), `verdicts`, `largest` (largest median time difference as a share of the shipped median), `variant_effect`, `completed`.

## Predictions

- **Q1 (reproduction).** `shipped` pooled `median_made_good_mps` equals pace_b's: `measured` 0.769 at 0.7 and 0.878 at 0.8; `measured-noise10` 0.750 and 0.855 (each within ±0.001).
- **Q2.** All 720 missions are completed.
- **Q3.** `measured-noise10`, `cf0.3` against `shipped`: faster in at least 5 of 6 groups, slower in none.
- **Q4.** `measured-noise10`, `cf0.3` at cruise 0.8: pooled median made good at least 0.867 m/s (at least half of the 0.855 to 0.878 gap won back).
- **Q5.** `measured`, `cf0.3` against `shipped`: no completion lost, and `largest_median_diff_share` at most +0.01 (smoothing costs under 1% on the cleaner compass).
- **Q6.** `measured-noise10`, `cf0.3-yaw30` against `shipped`: faster in at least 4 of 6 groups.
- **Q7.** `measured-noise10` at cruise 0.8: `ema0.3`'s pooled median made good is below `cf0.3`'s.
- **Q8.** `measured-noise10`, `cf0.3` at cruise 0.7: `beats_on_every_course` is true.

## Decision rules

- **D1.** If Q3 and Q5 hold, a later release adds the complementary filter to the pilot as an opt-in option, off by default, with its own tests; it would take the turn rate from `--calibrate` (`yaw_dps_at_full`). The default changes only after the compass noise of a real Mini+ is measured.
- **D2.** If `cf0.3` is faster in fewer than 3 of the 6 `measured-noise10` groups, FINDINGS records that smoothing the heading did not win back the noise cost, and nothing is added to the pilot.
- **D3.** If `cf0.3` loses a completion or costs more than 1% in any `measured` group, nothing is added, not even as an option, whatever D1 says.
- **D4.** If Q6 fails, any option added under D1 requires a calibrated turn rate and has no built-in default rate.
- **D5.** If Q1 fails, the cause is found and written up before any number from this run is used.

## Limits known in advance

Simulated rovers on synthetic 1.3-1.6 km courses; no pedestrians, crossings, kerbs or slopes, so speeds are upper bounds. The noise is independent from report to report; a real compass error that drifts, or depends on heading or nearby steel, would not average away like this. The 48°/s and 0.5 s values come from a few, mostly indoor, public recordings, and the Mini+ GPS rate (a fix every 2 s) is assumed. Orientation runs the way the pilot assumes in the simulator; on a rover where it runs the other way `--calibrate` is needed anyway, and a filter that predicts turns would need the same convention.
