# pace-g: dead reckoning and `--smooth-heading` together (pre-registered)

MV2 of Munim, Inc. Written with AI agents. CC BY 4.0.

This file is committed to main before any pace-g mission is flown. The job that flies them (`pace-g-v1`) waits until this file and rover_pilot.py 0.13.0 are on main, and records this file's SHA-256 and the time it fetched main (`fetched.json`). The study code (`pace_g.py`, `test_pace_g.py`) will be published with the grade, byte for byte as the job ran it; the job records its SHA-256 too. No clock time is written here: the commit history and the job log show the order.

## Why

Since v0.13.0 the command line turns on two things for a real rover: dead reckoning (`dead_reckon.DeadReckoner` with `DEAD_RECKON`: from each GPS fix the position is carried by the wheels along the pilot's heading; on since v0.10.0, from `dead_reckon_study.py`) and `--smooth-heading` (`HeadingSmoother` with `SMOOTH_HEADING`; from `pace_c.py` to `pace_f.py`). They were never flown together. Every pace study flew the pilot without dead reckoning, and `dead_reckon_study.py` flew it without the smoother and on a different rover model.

They interact. The smoothed compass feeds dead reckoning twice: as the direction the position is carried in, and as the test of whether a stretch of about 20 s was straight enough (every compass reading within 15° of the first) to learn the wheel size on. The reckoner gives no position until two such stretches agree with the 95 mm wheel prior. With 8° of compass noise, two raw readings often differ by more than 15°, so without the smoother the reckoner may be trusted late or never.

## Design

Every profile is pace_f.py's `measured` Mini+ (orientation every 0.5 s, 48°/s per unit of `angular`, 0.5 s latency, GPS every 2 s and 1.5 s late with 1.5 m noise and 5% of fixes missing, 3° of compass noise, a constant −25° compass error to learn), now also reporting its wheels' RPM as the simulator's `--dead-reckon` does (95 mm wheels). The rover is pace_d.py's `DistortedRover`.

| profile | change |
|---|---|
| measured | none |
| noise6, noise8 | 6° or 8° of compass noise |
| dropout0.3 | 30% of GPS fixes missing |
| dropout0.3-noise8 | 30% missing and 8° of compass noise |
| wheels0.85 | the wheels drive 0.85 of what the 95 mm prior says per RPM; the reckoner must learn it |

Variants: `dr+cf0.3` (dead reckoning with `DEAD_RECKON` and `--smooth-heading` with `SMOOTH_HEADING`: v0.13.0 on a real rover), `dr` (dead reckoning only: v0.12.x on a real rover), `cf0.3` (`--smooth-heading` only: pace_f.py's cf0.3), `plain` (neither: pace_f.py's shipped). Cruise 0.8 (`--marathon`). pace_study's three courses (boulevard, blocks, bayside; 1.3-1.6 km). **Seeds 37-60**, none flown by an earlier study. 6 × 4 × 3 × 24 = **1,728 missions**.

Every mission records what `pace_f.py` records (time, made good, the learner's counts, the heading error, the distance from the course), and also: once a second while driving forward, how far the pilot's position (`Pilot.pos`) is from the rover's true position (`position_err`); and, with dead reckoning, when it was first trusted (`trusted_at_s`), the straight stretches it learned on and turned down, the seconds driven on the wheels alone through a GPS gap (`bridged_s`), and the learned metres per RPM over the rover's own (`learned_scale`, 1 is right).

Before the study, `--check` flies seeds 13-15 of pace_f.py's `measured` and `noise6` missions again as `plain` and `cf0.3` (with the wheels now reported) and compares every field with studies/pace-f/runs.jsonl: 36 missions.

Outputs: `summary.json` (`completed`, `check`, `overview`, `verdicts`, `pair_effect`, `position`, `reckoner`, `learner`, `offset`, `heading`), `runs.jsonl`, `report.md`. `verdicts` compares pairs paired by seed per course: dr+cf0.3 against dr, dr+cf0.3 against cf0.3, dr against plain, cf0.3 against plain. "Slower" or "faster" means a paired sign test with p < 0.05 (`groups_slower`, `groups_faster`); `groups_lost` counts courses where the variant compared against completed more missions. `position` rows give the median over completed missions of each mission's median position error (`median_position_err_m`). `reckoner` rows give `never_trusted` and `median_trusted_at_s` (a median with never-trusted missions counted last; null if that median is "never") and `median_abs_scale_error` (|`learned_scale` − 1|).

## Predictions

Each is graded from those output fields.

- **G1.** The check: `check` compared 36, identical 36, missing 0.
- **G2.** All 1,728 missions are completed (`completed` = `runs`).
- **G3.** The smoother does no harm with dead reckoning on. dr+cf0.3 against dr: `groups_slower` 0 and `groups_lost` 0 on every profile, and `groups_faster` 3 on noise6, noise8 and dropout0.3-noise8.
- **G4.** Dead reckoning does no harm with the smoother on, and pays through GPS gaps. dr+cf0.3 against cf0.3: `groups_slower` 0 and `groups_lost` 0 on every profile; on dropout0.3 and dropout0.3-noise8, `groups_faster` 3, with `median_time_diff_share` at most −0.03 on every course.
- **G5.** Dead reckoning knows better where the rover is. On measured, on every course, dr+cf0.3's `median_position_err_m` is at most 2.5 m and cf0.3's is at least 4.0 m.
- **G6.** The smoother lets dead reckoning start. On measured, `never_trusted` is 0 and `median_trusted_at_s` at most 120 for dr and dr+cf0.3 on every course. On noise8, on every course, dr's `median_trusted_at_s` is at least twice dr+cf0.3's (a null for dr counts as satisfying this if dr+cf0.3's is not null).
- **G7.** The wheel size is learned with both on. On wheels0.85, dr+cf0.3's `median_abs_scale_error` is at most 0.05 on every course.
- **G8.** pace-f's result holds on new seeds and with GPS gaps. cf0.3 against plain: `groups_slower` 0 and `groups_lost` 0 on every profile.
- **G9.** The real-rover pilot keeps the marathon pace. On every profile, dr+cf0.3's pooled `median_made_good_mps` is at least 0.86 and `beat_human_pace` is 72 (every mission above the 0.754 m/s human Berkeley-Stanford pace).

Why these:
- G4, G5: in `dead_reckon_study.py`'s Mini+ stand-in the 0.9.3 pilot's position was 4.79 m off late in a mission and dead reckoning's 1.79 m; missions took 0.97 of the time, and 0.93 with GPS dropouts. Without dead reckoning the position is an average of fixes that are 1.5 s late and 2 s apart (`GpsFilter`, alpha 0.3), which on a straight lags by roughly (2.3 fixes × 2 s + 1.5 s + 1 s) × 0.89 m/s ≈ 6 m. Here the pilot already makes good about 0.878 of an ideal 0.889 m/s (pace-f), so there is little left to gain on a clean GPS. With 30% of fixes missing, a fix is lost for more than 3 s whenever two in a row are missing (`GpsFilter.max_age_s`), and the pilot without dead reckoning stops until the next one: by a rough count about 6% of the time.
- G6: the reckoner's straight-stretch test compares every compass reading in about 20 s (about 40 refreshes) with the first. With 3° of noise a 15° difference is rare. With 8°, two readings differ by more than 15° about 18% of the time, so a 20 s stretch rarely passes. The smoother cuts the noise to roughly 3.4° (0.3 gain).
- G7: one stretch of about 18 m measured by two fixes with 1.5 m noise each gives the wheel size to about 12%; pooled over a mission's stretches, a few percent.

## Decision rules

- **R1.** v0.13.0's real-rover defaults (dead reckoning and `--smooth-heading` both on) stay as they are, and README and FINDINGS say they have now been flown together, if all of these hold: (a) the check found 36 of 36 identical; (b) dr+cf0.3 has `groups_lost` 0 and `groups_slower` 0 against dr on every profile; (c) dr+cf0.3 has `groups_lost` 0 and `groups_slower` 0 against cf0.3 on every profile.
- **R2.** If (b) fails, README and FINDINGS name each profile and course where the smoother lost or was slower with dead reckoning on, and the next study, pre-registered, tests the smoother's settings with dead reckoning on before any default changes. If (c) fails, they name each profile and course where dead reckoning lost or was slower with the smoother on, and the next study asks whether dead reckoning should stay on by default; no default changes without it.
- **R3.** Whatever the outcome, README and FINDINGS give each variant's position error on measured, and dead reckoning's trust times with and without the smoother on noise8.
- **R4.** If the check finds any difference, nothing from this study is published as a finding until the difference is explained.
- **R5.** Whatever the outcome, the grade and the outputs are published in studies/pace-g/ with the code, and the results go into FINDINGS-frodobots-2k.md and the README.

Limits: simulated rovers only, so speeds and position errors are bounds on what a real sidewalk allows. The simulated wheels report the commanded speed exactly (no slip beyond a fixed scale, no bumps), so dead reckoning is at its best here. GPS noise is independent from fix to fix, and missing fixes are independent too; real GPS errors drift and real dropouts come in runs (`dead_reckon_study.py` tried both). The compass noise is Gaussian and independent from reading to reading. None of these has been measured on a live Mini+.
