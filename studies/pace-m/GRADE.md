# pace-m grade: is the compass-bias learner too slow for a drifting compass, or are its fits too noisy?

MV2 of Munim, Inc. Graded with AI agents. CC BY 4.0.

Predictions: `studies/pace-m/PREDICTION.md` (SHA-256 bd84033d…, on main before the job fetched it; see `fetched.json`). Job `pace-m-v1`: fetched main at 2026-10-24T01:54:23Z (rover_pilot.py 0.16.1, pace_l.py 305d1ce7… as pace-l-v1 ran it, with `studies/pace-l/GRADE.md` and `runs.jsonl`), `tests_exit` 0 (32 tests: test_pace_m and test_pace_l), then flew 1,080 missions in 1,943 s (peak memory 0.07 GB). Every number below is read from `summary.json` in this folder. The code is `pace_m.py` and `test_pace_m.py` as the job ran them (pace_m.py SHA-256 7167780f…, test_pace_m.py bfd97ec3…).

**Result: 8 of 9 predictions held (M8 missed). Rule R2 applies: `long20` (20 m stretches, gain 0.3) qualifies with the most `groups_faster`, so v0.17.0 gives a real rover's compass-bias learner 20 m stretches. The gain it qualifies on is small (at most 0.22% a mission), and on a drifting compass it steered less true, not more; both are stated with the release.**

## Predictions

| | prediction | result | |
|---|---|---|---|
| M1 | check: compared 18, identical 18, missing 0 | 18, 18, 0 | held |
| M2 | all 1,080 missions completed | 1,080 of 1,080 | held |
| M3 | `shipped`'s `fit` `rms_deg` on outage90 between 6 and 14 on every course | 9.20 / 9.12 / 9.27 | held |
| M4 | `long20`'s `median_fits` and `rms_deg` below `shipped`'s on every profile and course (9 of 9 each) | fits 18.5 / 18.5 / 31.5 vs 52 / 51 / 74 (outage90), 15.5 / 15.5 / 26.5 vs 47.5 / 47 / 66 (drift90), 15 / 15 / 26.5 vs 47.5 / 49.5 / 64 (lie90); rms 4.07 / 4.04 / 4.00 vs 9.20 / 9.12 / 9.27, 5.56 / 5.56 / 5.50 vs 9.71 / 9.79 / 9.71, 5.65 / 5.71 / 5.53 vs 9.54 / 9.94 / 9.66 | held (9 of 9 each) |
| M5 | `gain0.5` against `shipped`: `groups_faster` 0 on drift90 and lie90 | 0 and 0 (and `groups_slower` 2 on each) | held |
| M6 | outage90 heading `median_abs_deg`: `gain0.15` < `shipped` < `gain0.5` on every course | 2.36 < 2.94 < 4.08, 2.31 < 3.08 < 4.00, 2.09 < 2.88 < 3.75 | held |
| M7 | drift90: `gain0.15`'s `median_abs_deg` above `shipped`'s on ≥ 2 of 3 courses | 6.37 > 5.44, 6.62 > 5.95, 5.88 > 5.55 (3 of 3) | held |
| M8 | drift90: `long20-g0.5`'s `median_abs_deg` below `shipped`'s on every course | 6.64 vs 5.44, 6.46 vs 5.95, 6.13 vs 5.55: above on all 3 | **missed** |
| M9 | `profile_verdicts`: `groups_faster` 0 for every variant on drift90 and lie90 | 0 in all 10 | held |

(Courses are bayside / blocks / boulevard. `shipped` = gain 0.3 and 10 m stretches, as v0.16.1 ships; every mission was flown as pace_l.py's `bridge120+cf0.3`, v0.16.x's real-rover pilot.)

## Decision

- **R1 does not stop anything:** the check found no difference (18 of 18 identical).
- **R2 applies.** A variant qualifies with `groups_slower` 0 and `groups_lost` 0 against `shipped` on all three profiles and `groups_faster` ≥ 1 on drift90 or lie90:
  - `gain0.5`: slower on 3 / 2 / 2 courses (outage90 / drift90 / lie90). Does not qualify.
  - `gain0.15`: slower 0 and lost 0 everywhere, but faster only on outage90 (2), none on drift90 or lie90. Does not qualify.
  - `long20`: slower 0 and lost 0 everywhere; faster on outage90 2, drift90 1, lie90 0. **Qualifies, 3 in total.**
  - `long20-g0.5`: slower 0 and lost 0 everywhere; faster on outage90 1, drift90 1, lie90 0. Qualifies, 2 in total.
  - So `long20` has the most `groups_faster` and no tie-break is needed. v0.17.0 gives a real rover's compass-bias learner `min_move_m` 20 (gain stays 0.3), at the command-line layer only. The simulator's defaults and the HeadingEstimator and Pilot classes are unchanged.
- R3 does not apply. R4: this grade, the outputs and the code are published here.

## What each learner did against the shipped one (paired by seed, same profile)

Courses with p < 0.05, the median paired difference and seeds faster/slower of 24:

| variant | outage90 (steady compass) | drift90 (drifting compass) | lie90 (drift and slip) |
|---|---|---|---|
| gain0.5 | slower on all 3: +2 / +3 / +4 s (+0.14 / +0.18 / +0.22%) | slower on bayside (+1 s, 2/12) and boulevard (+4 s, 2/16) | slower on blocks (+2 s, 3/13) and boulevard (+4 s, 1/16) |
| gain0.15 | faster on bayside (0 s median, 10/0) and boulevard (−2 s, −0.11%, 15/0) | none (median 0 s on every course) | none |
| long20 | faster on bayside (0 s median, 10/1) and boulevard (−4 s, −0.22%, 20/1) | faster on blocks (−1 s, −0.06%, 12/3) | none (median 0 s on every course) |
| long20-g0.5 | faster on boulevard (−3 s, −0.17%, 18/1) | faster on blocks (−2 s, −0.12%, 15/3) | none |

Pooled made good (m/s), outage90 / drift90 / lie90: shipped 0.866 / 0.863 / 0.862; gain0.5 0.863 / 0.861 / 0.860; gain0.15 0.866 / 0.863 / 0.863; long20 0.867 / 0.861 / 0.861; long20-g0.5 0.866 / 0.862 / 0.864. Every learner completed every mission. Against outage90, the drift still cost every learner time: slower on 2-3 courses each, by up to +0.55% (M9).

## Findings

1. **Each 10 m fit is about 9° off, as pace-l's records implied.** The RMS error of each measurement the shipped learner used, against the bias that would really have cancelled the compass error at that moment, was 9.1-9.3° on a steady compass and 9.5-9.9° on a drifting one (M3). pace-l's end-of-mission bias errors had implied about 9.5° if measurements were independent. So the learner's error on a steady compass comes from the noise of each fit, not from forgetting too slowly.
2. **20 m stretches give fits about 2.3 times less wrong, but a third as many.** On a steady compass the measurement error fell from 9.1-9.3° to 4.0-4.1° (2.3 times; independent fix errors alone would give about 2.8 for twice the length). The learner calibrated 18.5-31.5 times a mission instead of 51-74: a third as often, not half, because a straight stretch between turns of 10-20 m gives no fit at all. Its bias at the end of a mission was off by a median 0.9-1.4° against 2.4-3.4°, and its median heading error was 1.6-1.7° against 2.9-3.1°.
3. **On a drifting compass, fewer fits followed the drift worse, whatever the gain.** With the drift, long20's median heading error was 6.3-6.9° against the shipped learner's 5.4-6.0°, and long20-g0.5's 6.1-6.6° (M8 missed: the first-order model had a measurement every ~60 s about 3° off; the drift itself moved the truth during and between stretches, so the 20 m measurements were 5.3-5.6° off, not 3°). Following faster alone (gain 0.5) also steered no truer on the drift (5.6-6.1°) and was slower on 2-3 courses on every profile (M5); following slower (gain 0.15) steered truest on a steady compass (2.1-2.4°) and less true on the drift (5.9-6.6°, M6, M7).
4. **Steering less true did not make long20 slower.** On drift90 long20 was faster on one course and slower on none, although its median heading error was about 1° higher. It steered 1.9-4.2% less hard than the shipped learner on every course of every profile (mean |angular| 0.0415-0.0607 against 0.0433-0.0623). A likely reason, not tested here: with a third as many bias updates, the heading it steers by jumps less often. This is the fifth study in this series in which a truer estimate and a faster pilot did not go together.
5. **No learner setting removes the drift's cost** (M9): against a steady compass every variant was still slower on 2-3 courses with the drift, by up to 0.55% a mission. The drift turns the compass between straight stretches, and a learner fed only by straight-stretch GPS fits cannot see that until the next one.

## Limits

Simulated rovers only (pace_l.py's measured Mini+ profile), so speeds are upper bounds on what a sidewalk allows. The time differences that decide R2 are small: at most 4 s (0.22%) a mission on any course, and none on lie90. Whether a real Mini+'s compass error holds steady (where 20 m stretches clearly help the heading) or drifts like pace-d's model (where they steer about 1° less true) has not been measured. The drift is pace-d's model and the GPS error is the simulator's. The learner's other gates (straightness, compass spread) were not varied. The first-order model behind M5-M8 assumed independent measurements at a fixed interval; it was right about the gain and wrong about long stretches on a drifting compass. Finding 4's reason is a likely one, not a tested one. None of this has been measured on a live Mini+.
