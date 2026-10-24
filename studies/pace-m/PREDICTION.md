# pace-m: is the compass-bias learner too slow for a drifting compass, or are its fits too noisy? (pre-registered)

MV2 of Munim, Inc. Written with AI agents. CC BY 4.0.

This file is committed to main before any pace-m mission is flown. The job that flies them (`pace-m-v1`) waits until this file, `studies/pace-l/GRADE.md`, `studies/pace-l/runs.jsonl` and pace-l's `pace_l.py` (SHA-256 305d1ce7…) are on main with rover_pilot.py 0.16.0 or 0.16.1. It records this file's SHA-256 and the time it fetched main (`fetched.json`). The study code (`pace_m.py`, `test_pace_m.py`) will be published with the grade, byte for byte as the job ran it. No clock time is written here: the commit history and the job log show the order.

## Why

pace-l (9 of 9 predictions held) found that of the two lies it flew, wheel slip cost nothing measurable and the drifting compass cost 0.2-0.6% a mission, also on clear sky, roughly doubling the median heading error. Its grade said the compass-bias learner "hardly follows" the drift. The learner (`HeadingEstimator`) fits a line through the GPS fixes of each straight stretch of at least 10 m (`min_move_m`), takes the fitted course minus the mean compass reading as one measurement of the bias, and moves its bias 0.3 of the way to it (`gain`).

Reading pace-l's own records more closely suggests the learner is not simply too slow:
- It measures often: on drift90 a 1,450-1,580 s bayside mission had 41-59 calibrations, about one every 30 s.
- On outage90, where the compass error never changes, the bias error at the end of 24 bayside missions (bridge120) was still 4.0° RMS. A running update with gain g leaves g / (2 − g) of each measurement's variance in the bias, so measurements independent of each other would have to be off by about 9.5° each (RMS).
- With a measurement every 30 s, a 10° drift with a 120 s time constant, and measurements that noisy, a first-order model gives about the same bias error for gain 0.3 (6.6° RMS) as for 0.5 (6.5°), and more for 0.15 (7.6°). On a steady compass it gives 4.0°, 5.5° and 2.7°.

So following faster should not help, because each measurement is noisy. Less noisy measurements should help, for example ones taken over longer stretches. This is a model with assumptions (independent measurements, a fixed interval), not a result. This study measures the noise directly. For every measurement the learner uses, it records how far that measurement was from the bias that would really have cancelled the compass error at that moment (`fit_err`). It also flies learners that separate the two explanations.

Prior art: correcting a compass against GPS course over ground is standard practice (ArduPilot's in-flight compass learning, and EKF yaw estimation from GPS velocity, for example). This study proposes no new method. It measures, for this pilot on the Earth Rover Mini+'s measured telemetry, where the error of its own learner comes from and which of its two settings matters.

## Design

Every mission is flown by `pace_l.fly` as pace_l.py's `bridge120+cf0.3` (v0.16.x's pilot on a real rover: bridging GPS outages on the wheels with a 120 s reach, `--smooth-heading`), on pace_l.py's rovers. Only the learner's settings change, through `pace_m.RecordingEstimator`, a `pace_e.CountingEstimator` that decides exactly as one with the same settings and only records `fit_err`.

Variants (HeadingEstimator settings):
- `shipped`: gain 0.3, 10 m stretches (as it ships);
- `gain0.5`: gain 0.5 (follows faster);
- `gain0.15`: gain 0.15 (follows slower);
- `long20`: 20 m stretches;
- `long20-g0.5`: 20 m stretches and gain 0.5.

Profiles (pace_l.py's, cruise 0.8, pace_study's three courses): `outage90` (90 s GPS outages after a mean of 600 s of sky; a steady compass error), `drift90` (outage90 with pace_d.py's drifting compass error, SD 10°, 120 s time constant) and `lie90` (drift90 with pace-l's wheel slip). **Seeds 181-204** (none flown before). 5 × 3 × 3 × 24 = **1,080 missions**.

Before the study, `--check` flies seeds 157-159 of pace-l's outage90 and lie90 `bridge120+cf0.3` missions again as `shipped` (18 missions) and compares every field with pace-l's record.

Output fields: `verdicts` compare each variant with `shipped` on the same profile, paired by seed per course. "Faster" or "slower" means a paired sign test with p < 0.05 (`groups_faster`, `groups_slower`), and `groups_lost` counts courses where `shipped` completed more missions. `profile_verdicts` compare each variant on drift90 and lie90 with itself on outage90. `heading` gives, per profile, variant and course, `median_abs_deg`: the median over missions of each mission's median |heading error| while driving forward. `fit` gives `rms_deg`: the median over missions of each mission's RMS measurement error, and `median_fits`: measurements per mission.

## Predictions

Each is graded from those output fields.

- **M1.** The check: compared 18, identical 18, missing 0.
- **M2.** All 1,080 missions are completed.
- **M3.** Each measurement is noisy: `shipped`'s `fit` `rms_deg` on outage90 is between 6 and 14 on every course.
- **M4.** Longer stretches measure less often and less noisily: `long20`'s `median_fits` and its `rms_deg` are both below `shipped`'s on every profile and course (9 of 9 each).
- **M5.** Following faster alone does not pay on a drifting compass: `gain0.5` against `shipped` has `groups_faster` 0 on drift90 and on lie90.
- **M6.** On a steady compass, a slower learner steers truer and a faster one less true: on outage90, `heading` `median_abs_deg` is lower for `gain0.15` than for `shipped`, and lower for `shipped` than for `gain0.5`, on every course.
- **M7.** On a drifting compass the slower learner steers less true: on drift90, `gain0.15`'s `median_abs_deg` is above `shipped`'s on at least 2 of 3 courses.
- **M8.** Less noisy measurements followed faster steer truest on a drifting compass: on drift90, `long20-g0.5`'s `median_abs_deg` is below `shipped`'s on every course.
- **M9.** No learner removes the drift's cost: in `profile_verdicts`, `groups_faster` is 0 for every variant on drift90 and lie90.

Why these:
- M3 is the model's 9.5° with room either way. If the GPS errors of successive stretches are correlated, the white-noise formula overstates the noise; if the compass smoother adds error on the stretches, it understates it.
- M4: a 20 m stretch takes the place of at least two 10 m ones, and a stretch of 10-20 m between turns gives none. With the GPS error mostly independent from fix to fix, a course fitted over twice the length is about 2-3 times less wrong. A GPS error that wanders slowly would shrink that gain but not reverse it.
- M5, M6, M7: the first-order model above. A heading error of ~1-1.5° more or less was worth about 0.1-0.3% a mission in pace-l, so time verdicts may not reach p < 0.05 with 24 seeds. The heading predictions carry the mechanism, and the time verdicts carry the decision.
- M8: the model with a measurement about 3° off every ~60 s gives about 4.8° RMS for gain 0.5, against 6.6° for the shipped learner.
- M9: the drift also turns the compass between measurements, and nothing here can see that until the next straight stretch.

## Decision rules

- **R1.** If the check finds any difference, nothing from this study is published as a finding, and no default changes until the difference is explained.
- **R2.** A variant qualifies if, against `shipped`, it has `groups_slower` 0 and `groups_lost` 0 on all three profiles, and `groups_faster` at least 1 on drift90 or lie90. If any qualify, v0.17.0 gives a real rover's compass-bias learner the settings of the qualifying variant with the most `groups_faster` summed over the three profiles. Ties go to the lower mean over courses of lie90's heading `median_abs_deg`, then to the order listed above. The change is made at the command-line layer, for a real rover only. The simulator's defaults and the HeadingEstimator and Pilot classes are unchanged.
- **R3.** If none qualifies, the learner stays as it is, and v0.16.2 only adds pace-m's results to the README and FINDINGS.
- **R4.** Whatever the outcome, the grade and the outputs are published in studies/pace-m/ with the code. M2-M9 decide nothing beyond what R1-R3 read from the verdicts.

Limits: simulated rovers only (pace_l.py's measured Mini+ profile), so speeds are upper bounds on what a sidewalk allows. The drift is pace-d's model, and the GPS error is the simulator's. The learner's gates other than gain and stretch length (the straightness and compass-spread tests) are not varied. The first-order model behind M5-M8 assumes independent measurements at a fixed interval, and `fit_err` is there to test that. None of this has been measured on a live Mini+.
