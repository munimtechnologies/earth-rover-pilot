# pace-g grade: dead reckoning and `--smooth-heading` together

MV2 of Munim, Inc. Written with AI agents. CC BY 4.0.

**4 of 9 predictions held. Rule R1 failed: v0.13.0's real-rover defaults are slower than `--smooth-heading` alone on a clean GPS.** By R2 the defaults stay as they are until the next pre-registered study (pace-h) decides whether dead reckoning stays on by default.

Job `pace-g-v1` (MV2-Compete, 2026-10-23 09:32-10:22 UTC, 0.07 GB peak) fetched main at 09:32:09Z with rover_pilot.py 0.13.0 and `studies/pace-g/PREDICTION.md` (SHA-256 `04f76705…`) already on it (`fetched.json`). Its tests passed (63 of 63, `tests.txt`), and `pace_g.py` (SHA-256 `ce4e7990…`) and `test_pace_g.py` (`e3d6134b…`) are published here byte for byte as the job ran them. Every number below is read from `summary.json`; `report.md` has the same tables.

## Predictions

| | prediction | result | held? |
|---|---|---|---|
| G1 | check: 36 compared, 36 identical, 0 missing | 36, 36, 0 | **yes** |
| G2 | all 1,728 missions completed | 1,728 of 1,728 | **yes** |
| G3 | dr+cf0.3 vs dr: `groups_slower` 0 and `groups_lost` 0 on every profile; `groups_faster` 3 on noise6, noise8, dropout0.3-noise8 | slower 2 on noise6 and 2 on noise8; faster 0, 1 and 3 | no |
| G4 | dr+cf0.3 vs cf0.3: `groups_slower` 0 and `groups_lost` 0 on every profile; `groups_faster` 3 on both dropout profiles with share ≤ −0.03 on every course | slower 3 of 3 on measured, noise6, noise8 and wheels0.85; faster 1 of 3 on each dropout profile | no |
| G5 | measured, every course: dr+cf0.3 `median_position_err_m` ≤ 2.5, cf0.3 ≥ 4.0 | dr+cf0.3 2.62, 2.61, 2.60; cf0.3 6.46, 6.37, 6.56 | no (by 0.10-0.12 m) |
| G6 | measured: `never_trusted` 0 and `median_trusted_at_s` ≤ 120 for dr and dr+cf0.3; noise8: dr's ≥ 2× dr+cf0.3's | measured dr 110, 81, 82 s and dr+cf0.3 94, 91, 90 s, never 0; noise8 dr null (never trusted in 23, 24, 23 of 24), dr+cf0.3 85, 74, 75 s | **yes** |
| G7 | wheels0.85: dr+cf0.3 `median_abs_scale_error` ≤ 0.05 on every course | 0.062 (bayside), 0.031 (blocks), 0.052 (boulevard) | no |
| G8 | cf0.3 vs plain: `groups_slower` 0 and `groups_lost` 0 on every profile | slower 0, lost 0 everywhere; faster on 15 of 18 courses | **yes** |
| G9 | dr+cf0.3 pooled `median_made_good_mps` ≥ 0.86 and `beat_human_pace` 72 on every profile | 0.826-0.834 on every profile; 72 of 72 beat the human pace everywhere | no |

## Decision rules

- **R1 fails.** (a) holds (36 of 36 identical). (b) fails: with dead reckoning on, the smoother was slower on noise6 bayside (+1.7%, 21 of 24 seeds slower) and boulevard (+0.9%, 21 of 24), and on noise8 bayside (+4.9%, 24 of 24) and boulevard (+4.6%, 24 of 24). (c) fails: with the smoother on, dead reckoning was slower on all three courses of measured (bayside +7.0%, blocks +1.5%, boulevard +6.9%; 24 of 24 seeds slower on each), noise6 (+6.9%, +1.6%, +6.6%), noise8 (+6.6%, +1.0%, +6.3%) and wheels0.85 (as measured). No course was lost by either.
- **R2 applies.** README and FINDINGS will name those profiles and courses. The next study is pre-registered before any default changes: pace-h (`studies/pace-h/PREDICTION.md`) asks whether dead reckoning should stay on by default, and tests the smoother with dead reckoning on through a dead-reckoning mode that is only used through GPS gaps.
- **R3.** Position error on measured, median over missions of each mission's median: dr+cf0.3 2.62 / 2.61 / 2.60 m (bayside / blocks / boulevard), dr 2.65 / 2.66 / 2.63, cf0.3 6.46 / 6.37 / 6.56, plain 6.46 / 6.37 / 6.55. Dead reckoning's first trust on noise8: dr never (23, 24 and 23 of 24 missions never trusted), dr+cf0.3 at 85 / 74 / 75 s.
- **R4.** The check found no difference, so these results stand as findings.
- **R5.** This grade, the outputs and the code are in `studies/pace-g/` and at the top level; README and FINDINGS follow in the next documentation release.

## What the study found that was not predicted

**1. On a clean GPS, dead reckoning makes the pilot slower, not faster.** With the smoother on, missions took 1.5-7.0% longer with dead reckoning than without (measured: pooled 0.826 against 0.878 m/s). Without the smoother it was the same: dr against plain was +6.6%, +1.5% and +6.6% on measured. The pilot drove a longer path (median path ratio 1.026 against 1.004) and drove more slowly while it drove: in seed 37 on bayside it covered 1,293.8 m in 1,522.5 s of driving (0.850 m/s) with dead reckoning and 1,264.6 m in 1,426.4 s (0.887 m/s) without. It did not drive further from the course: its median distance from the course on measured was 0.74 / 1.15 / 1.31 m against cf0.3's 0.69 / 1.25 / 1.77 m. It weaves along the course.

**2. Dead reckoning starves the compass-bias learner.** The learner only measures the compass bias on straight stretches (the commanded turn, low-passed, below 0.1 for at least 5 GPS fixes and 10 m). On measured, straight stretches were cut off by a turn a median 482-586 times per mission with dr+cf0.3 against 98-126 times with cf0.3, so it fitted 2.8-3.0 stretches per mission against 61-84, and ended with a median bias error of 4.3-5.0° against 2.5-3.1°. Without the smoother it was worse: 1 fit, 7-17° of bias error.

**3. A position that knows better where it is can still steer worse.** Dead reckoning's position was 2.6 m from the truth against 6.4 m for the GPS filter, yet the pilot was slower with it. The likely reason, not yet tested: the GPS filter's error is mostly a steady lag along the course (its average of fixes 1.5 s late and 2 s apart), which barely changes the direction to steer. Dead reckoning instead starts again from every fix (gain 1), so its position jumps by the fix's noise (1.5 m) every 2 s and drifts sideways between fixes by the heading's error. Each jump turns the pilot. In general this is a known effect: position jumps from GPS corrections upset path followers, and the usual cure is to fuse GPS and odometry smoothly rather than reset to each fix (for example Fixposition's field guide on position jumps, https://www.fixposition.com/blogs/field-guide/position-jumps-after-gnss-outage, and the "locally consistent" odometry frame of Gonzalez et al., CMU 2006). What this study adds is the size of the cost on this rover's measured telemetry and its knock-on on the compass-bias learner. That is weaving (finding 1), and weaving breaks the learner's straight stretches (finding 2), which leaves more heading error for dead reckoning to carry. pace-h tests both parts: a known compass bias (the learner's part) and dead reckoning used only through GPS gaps or moved 0.3 of the way to each fix (the jumps' part).

**4. Through GPS gaps dead reckoning pays, as designed.** With 30% of fixes missing, the pilot without dead reckoning stood still 5.9% of the time and with it 0.5%. On blocks that made dr+cf0.3 6.2% faster than cf0.3 (24 of 24 seeds). On bayside and boulevard the weaving cost cancelled the saving (−0.5% and +0.2%, not significant).

**5. On noise8, dead reckoning without the smoother never starts.** Its straight-stretch test (every compass reading within 15° of the first for about 20 s) failed in 70 of 72 missions, so dr flew almost exactly as plain did (median difference 0.0 s on every course; 2 of 72 missions differed). The smoother let it start at 74-85 s (G6). On noise8, then, "dr+cf0.3 against dr" is really dead reckoning against none, and its slowdown on bayside and boulevard is finding 1 again. That is why G3 missed, not a cost of the smoother.

**6. The wheel size changed nothing.** Every wheels0.85 summary row equals measured's: the reckoner learns metres per RPM only from GPS distance over wheel turns, so a different wheel gives a different RPM count and the same metres. G7 missed because the scale error after 2-3 stretches with 1.5 m GPS noise is 3-6% on any wheel, not because of the wheel. The `wheels0.85` profile tested nothing.

**7. pace-f's result held on fresh seeds and through GPS gaps (G8).** The smoother alone was never slower than the pilot without it, on any of the 18 profile × course groups, and faster in 15.

## Limits

Simulated rovers only (pace_d.py's `DistortedRover` with pace_f.py's measured Mini+ settings), so speeds and errors are bounds on what a real sidewalk allows. GPS noise and dropouts are independent from fix to fix. The wheels report the commanded speed exactly. None of this has been measured on a live Mini+. Finding 3's mechanism is a hypothesis until pace-h is graded.
