# pace-f: should `--smooth-heading` be on by default? (pre-registered)

MV2 of Munim, Inc. Written with AI agents. CC BY 4.0.

This file is committed to main before any pace-f mission is flown. The job that flies them (`pace-f-v1`) waits until this file is on main, and records its SHA-256 and the time it fetched main (`fetched.json`). The study code (`pace_f.py`, `test_pace_f.py`) will be published with the grade, byte for byte as the job ran it; the job records its SHA-256 too. No clock time is written here: the commit history and the job log show the order.

## Why

`--smooth-heading` (rover_pilot's `HeadingSmoother`: each new compass reading moves the heading only 0.3 of the way from the last estimate, after turning that estimate by the commanded `angular` at an assumed 48°/s per unit and 0.5 s lag) was slower than the shipped pilot in none of the groups `pace_c.py`, `pace_d.py` and `pace_e.py` compared. `pace_e.py` (studies/pace-e/GRADE.md) found that without it the pilot stops learning its compass bias once the compass noise reaches 6°: it then steers with the whole −25° simulated error and drives about 3.7 m to one side of its course. `--smooth-heading` stays off by default only because no real Mini+ compass has been measured.

Before it becomes the default, it should be tried where it could hurt. It assumes how fast the rover turns and how late commands land, and a real rover may differ. Every earlier study also flew the same 12 seeds. So this study flies new seeds against rovers it doesn't expect.

## Design

Every profile is pace_b.py's `measured` Mini+ (orientation every 0.5 s, 48°/s per unit of `angular`, 0.5 s latency, GPS every 2 s, 3° of compass noise, a constant −25° compass error to learn), with one or two things changed. The rover is pace_d.py's `DistortedRover`, which flies exactly as `MeasuredRover` when undistorted.

| profile | change |
|---|---|
| measured | none |
| noise4, noise5, noise6 | 4°, 5°, 6° of compass noise |
| yaw32, yaw64 | the rover turns 32°/s or 64°/s per unit of `angular` (the smoother still assumes 48) |
| lag1.0 | commands land after 1.0 s (the smoother still assumes 0.5) |
| yaw32-noise8, yaw64-noise8 | the turn rate changed as above, and 8° of compass noise |
| bias60 | a −60° compass error to learn instead of −25° |
| bias60-noise8 | −60°, and 8° of compass noise |

Variants: `shipped` (rover_pilot as it ships) and `cf0.3` (`--smooth-heading`, `SMOOTH_HEADING`). Cruise 0.8 (the `--marathon` cruise). pace_study's three courses (boulevard, blocks, bayside; 1.3-1.6 km). **Seeds 13-36**, none flown by an earlier study. 11 × 2 × 3 × 24 = **1,584 missions**.

Every mission records what `pace_e.py` records: the learner's counts (`calibrations`, `fits`, `breaks`, spread tests, `bias_error_deg`), the heading error, and the distance from the course once a second while driving forward. `pace_f.py` flies them with the same code path as `pace_e.py`. Before the study, `--check` flies seeds 1-3 of `pace_e.py`'s `measured` and `noise6` missions again, both variants, and compares every field with studies/pace-e/runs.jsonl: 36 missions.

Outputs: `summary.json` (`completed`, `check`, `overview`, `verdicts`, `variant_effect`, `learner`, `offset`, `offset_diff`, `heading`), `runs.jsonl`, `report.md`. Comparisons with the shipped pilot are paired by seed per course; "slower" or "faster" means a paired sign test with p < 0.05 (`verdicts` `groups_slower`, `groups_faster`). `groups_lost` counts courses where the shipped pilot completed more missions. `offset_diff` gives cf0.3's `median_offset_m` minus shipped's per profile and course. `learner`, `offset` and `heading` rows are medians over the completed missions of each profile, variant and course.

## Predictions

Each is graded from those output fields.

- **Q1.** The check: `check` compared 36, identical 36, missing 0.
- **Q2.** Every mission is completed on every profile but bias60-noise8 (`overview` `completed` = `runs`, both variants). On bias60-noise8, cf0.3 completes all 72.
- **Q3.** Where the shipped learner stops. Shipped `median_calibrations` on every course: at least 3 on noise4, at least 1 on noise5, at most 1 on noise6. On noise4, shipped `median_abs_bias_error_deg` is below 10 on every course.
- **Q4.** pace-e's noise6 result holds on new seeds. On noise6, cf0.3 has `groups_faster` 3; its `median_offset_m` is below 2.5 m on every course, and shipped's is above 3.0 m on every course.
- **Q5.** The wrong turn rate or lag does no harm with 3° of noise. On yaw32, yaw64 and lag1.0, cf0.3 has `groups_slower` 0 and `groups_lost` 0, and `offset_diff` `diff_m` is at most 0.2 on every course.
- **Q6.** With 8° of noise, smoothing still wins at the wrong turn rate. On yaw32-noise8 and yaw64-noise8, cf0.3 has `groups_faster` 3 and `groups_slower` 0, and `offset_diff` `diff_m` is below 0 on every course.
- **Q7.** A larger compass error is learned. On bias60, shipped `median_calibrations` is at least 10 and `median_abs_bias_error_deg` below 10 on every course; cf0.3 has `groups_slower` 0.
- **Q8.** A larger error left unlearned shows. On bias60-noise8, on every course, shipped either completed fewer than 24 missions or its `heading` `median_abs_deg` is above 40. cf0.3's `median_offset_m` is below 2.5 m on every course.
- **Q9.** cf0.3 steers closer to the true heading: its `heading` `median_abs_deg` is below shipped's on every course of measured, noise4, noise5, noise6, yaw64, yaw32-noise8, yaw64-noise8, bias60 and bias60-noise8. (No prediction for yaw32 and lag1.0, where it assumes a turn faster or sooner than the rover's.)

Why these:
- Q3: in pace-e the shipped pilot calibrated 23.5-33 times a mission with 3° of noise and 0-1 times with 6°. The straight-stretch test (low-passed `angular` within ±0.1, about 6° of heading error) should break off stretches more often as the noise grows; we expect the edge near 5°.
- Q5: pace_c.py's `cf0.3-yaw30` (assuming 30°/s on a 48°/s rover) changed almost nothing. Here the smoother also over-predicts turns (48 assumed, 32 real), which pace-c did not try. Each new reading takes out 0.3 of any error, so an error made in a turn should be gone a few seconds after it.
- Q7, Q8: a constant error is learned from the first accepted fit when the noise is low. With 8° the shipped pilot rarely fits, and by the 8 m lookahead a 60° error left unlearned would put the rover 8 × tan 60° ≈ 14 m to one side of its path, close to the 15 m within which a checkpoint counts as reached.

## Decision rules

- **F1.** `--smooth-heading` becomes the default in the next release (v0.13.0, with a `--no-smooth-heading` to turn it off) only if all of these hold on these seeds: (a) the check found 36 of 36 identical; (b) cf0.3 has `groups_lost` 0 on every profile; (c) cf0.3 has `groups_slower` 0 on every profile (33 groups); (d) `offset_diff` `diff_m` is at most 0.2 on every profile and course. The release must fly pace-f's cf0.3 missions exactly with the new default on a short course (a whole-mission equality test, as v0.12.0 did for `--smooth-heading`).
- **F2.** If F1 fails, the default is unchanged, and README and FINDINGS name each profile where cf0.3 lost a group, was slower, or drove more than 0.2 m further from the course.
- **F3.** README and FINDINGS state the highest of 3°, 4°, 5° and 6° of noise at which the shipped pilot's `median_calibrations` is at least 1 on every course (3° is pace-e's `measured`).
- **F4.** If the check finds any difference, nothing from this study is published as a finding until the difference is explained.
- **F5.** Whatever the outcome, the grade and the outputs are published in studies/pace-f/ with the code, and the results go into FINDINGS-frodobots-2k.md and the README.

Limits: simulated rovers only, so speeds and offsets are upper bounds on what a real sidewalk allows. The noise is Gaussian and independent from one reading to the next. The turn rates, lag and compass errors tried are guesses at how a real Mini+ might differ; none has been measured on a live rover. The offset is measured to the nearest segment of the course, which understates it on corners.
