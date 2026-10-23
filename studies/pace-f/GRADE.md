# pace-f: grade

MV2 of Munim, Inc. Written with AI agents. CC BY 4.0.

The predictions (studies/pace-f/PREDICTION.md) were committed to main before any mission was flown. The job `pace-f-v1` waited until they were on main, fetched main at 2026-10-23T00:36:25Z and recorded the SHA-256 of every file it used (`fetched.json`: PREDICTION.md `2635b06c…`, pace_e.py `910bcf6a…`, rover_pilot.py 0.12.1 `e30b384e…`, pace_f.py `c4708d27…`, test_pace_f.py `568d8fb2…`). `pace_f.py` and `test_pace_f.py` in this commit are the files the job ran, byte for byte. Its tests passed first (50 tests, `tests.txt`, `tests_exit` 0); then it flew 1,584 missions in 1,627 s on 1 GB (peak 0.06 GB). Every figure below is read from `summary.json` (and the same numbers in `report.md`).

**Result: 9 of 9 predictions held. Decision rule F1 holds: `--smooth-heading` becomes the default in v0.13.0.**

## Predictions

| | prediction | result | graded |
|---|---|---|---|
| Q1 | `check` compared 36, identical 36, missing 0 | compared 36, identical 36, missing 0 | **held** |
| Q2 | every mission completed on every profile but bias60-noise8 (both variants); on bias60-noise8 cf0.3 completes all 72 | `completed` 1,584 of `runs` 1,584; every `overview` row 72/72, including bias60-noise8 cf0.3 (and shipped) | **held** |
| Q3 | shipped `median_calibrations` ≥ 3 on noise4, ≥ 1 on noise5, ≤ 1 on noise6, every course; noise4 shipped `median_abs_bias_error_deg` < 10 | noise4 9.0 / 8.0 / 11.5 (bayside / blocks / boulevard); noise5 2.0 / 2.0 / 3.0; noise6 0.0 / 0.0 / 0.0; noise4 bias error 2.87 / 3.46 / 4.11 | **held** |
| Q4 | noise6: cf0.3 `groups_faster` 3; cf0.3 `median_offset_m` < 2.5 and shipped > 3.0 on every course | `groups_faster` 3; cf0.3 0.71 / 1.25 / 1.85 m; shipped 3.70 / 3.85 / 3.64 m | **held** |
| Q5 | yaw32, yaw64, lag1.0: cf0.3 `groups_slower` 0, `groups_lost` 0, `offset_diff` ≤ 0.2 m on every course | slower 0 and lost 0 on all three; `diff_m` yaw32 0.06 / 0.07 / −0.15, yaw64 0.00 / −0.10 / −0.02, lag1.0 0.04 / −0.24 / −0.10 | **held** |
| Q6 | yaw32-noise8, yaw64-noise8: cf0.3 `groups_faster` 3, `groups_slower` 0, `offset_diff` < 0 on every course | faster 3, slower 0 on both; `diff_m` yaw32-noise8 −2.92 / −2.37 / −1.93, yaw64-noise8 −2.97 / −2.57 / −1.81 | **held** |
| Q7 | bias60: shipped `median_calibrations` ≥ 10 and `median_abs_bias_error_deg` < 10 on every course; cf0.3 `groups_slower` 0 | calibrations 24.0 / 23.5 / 32.5; bias error 2.71 / 2.52 / 3.29; slower 0 | **held** |
| Q8 | bias60-noise8, every course: shipped completed < 24 or `heading` `median_abs_deg` > 40; cf0.3 `median_offset_m` < 2.5 | shipped completed 24 on each course, heading error 59.75 / 59.64 / 59.70°; cf0.3 offset 0.75 / 1.31 / 1.90 m | **held** |
| Q9 | cf0.3 `heading` `median_abs_deg` below shipped's on every course of the nine named profiles | below on all 27 (e.g. measured 2.97 / 3.01 / 3.04 against 3.75 / 3.65 / 3.71; yaw64 3.19 / 2.85 / 2.96 against 3.71 / 3.83 / 3.71; bias60 2.92 / 3.21 / 2.84 against 3.86 / 4.03 / 3.75) | **held** |

## Decision rules

- **F1 holds.** (a) The check found 36 of 36 missions identical. (b) cf0.3 `groups_lost` is 0 on all 11 profiles. (c) cf0.3 `groups_slower` is 0 in all 33 profile × course groups. (d) The largest `offset_diff` `diff_m` is 0.07 m (yaw32, blocks), within 0.2 m on every profile and course. So the next release, v0.13.0, turns `--smooth-heading` on by default and adds `--no-smooth-heading`. How: the pilot's real-rover defaults (dead reckoning, the real-rover steering, the left-turning `angular`) are applied by the command line on a real rover and not in the simulator, so earlier studies stay reproducible; `--smooth-heading` follows the same pattern (on for a real rover, off in the simulator unless asked for), and the `Pilot` class keeps `smooth_heading=None`, which is what every study's `shipped` variant flies. The release must fly pace-f's cf0.3 missions exactly with the smoother the command line now builds, on a short course.
- **F2** does not apply (F1 holds).
- **F3.** The highest of 3°, 4°, 5° and 6° of compass noise at which the shipped pilot's `median_calibrations` is at least 1 on every course is **5°** (2.0 / 2.0 / 3.0; at 6° it is 0 on every course).
- **F4** does not apply: the check found no difference.
- **F5.** This grade, the outputs and the code are published in studies/pace-f/; v0.13.0 puts the results in FINDINGS-frodobots-2k.md and the README.

## Not predicted, worth knowing

- **The learner fades before it stops.** With 3° of noise the shipped pilot calibrated 23.5-33 times a mission; with 4°, 8-11.5; with 5°, 2-3, and 2-3 of each course's 24 missions never calibrated; with 6°, 0, and 17-20 of 24 never did. `--smooth-heading` calibrated 40-79 times a mission on every one of those profiles.
- **Late commands also starve the learner.** With commands landing after 1.0 s instead of 0.5 s, the shipped pilot calibrated 11-14.5 times a mission instead of 23.5-33; `--smooth-heading` 56-75.5. Its heading error was lower there too (2.80 / 3.02 / 3.11° against 3.58 / 4.50 / 4.00°), and with the rover turning at 32°/s instead of the assumed 48 (3.00 / 2.74 / 2.75° against 3.44 / 3.61 / 3.51°). Neither had a prediction.
- **A large compass error left unlearned is costly, not fatal.** On bias60-noise8 the shipped pilot never calibrated in 68 of 72 missions and steered about 60° off. It still reached every checkpoint (the 15 m tolerance absorbed its 12.8-13.1 m median offset), but at 0.577 m/s made good, a path 1.51 times the route and no mission beating the human marathon pace (0.754 m/s). `--smooth-heading` learned the error in every mission (bias within 2.9-3.5°, medians), made good 0.869 m/s and beat the pace in all 72, taking 30-37% less time (median paired difference per course).
- **The cost of compass noise to the shipped pilot grows with the noise; with smoothing it barely does.** Made good at cruise 0.8 (courses pooled), shipped: 0.878 (3°), 0.876 (4°), 0.873 (5°), 0.871 (6°) m/s; `--smooth-heading`: 0.879, 0.878, 0.878, 0.878.

## Limits

Simulated rovers only, so speeds and offsets are upper bounds on what a real sidewalk allows. The noise is Gaussian and independent from one reading to the next. The turn rates, lag and compass errors tried are guesses at how a real Mini+ might differ; none has been measured on a live rover. Every pace study, this one included, flew the pilot without dead reckoning, which a real rover uses by default; the smoothed heading also feeds dead reckoning there, and that combination has not been studied yet. The offset is to the nearest segment of the course, which understates it on corners.
