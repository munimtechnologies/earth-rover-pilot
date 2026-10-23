# pace-h grade: should dead reckoning stay on by default?

MV2 of Munim, Inc. Written with AI agents. CC BY 4.0.

**9 of 10 predictions held. Rules R1 and R2 failed, so rule R3 applies: the next release (v0.14.0) turns dead reckoning off by default on a real rover.** `--dead-reckon` turns it back on. Without it the pilot stops when the GPS drops out. Bridging GPS gaps only (`bridge+cf0.3`) was the fastest pilot on every profile, pooled over the courses. But it was slower than v0.13.0's pilot on one course with GPS gaps and compass noise, and R1 needed it to be slower nowhere. v0.14.0 therefore offers it only as an option. A new pre-registered study (pace-i) will decide whether it becomes the default.

Job `pace-h-v1` (MV2-Compete, 2026-10-23 11:45-13:26 UTC, 0.07 GB peak) fetched main at 11:45:23Z. Main already had rover_pilot.py 0.13.0, `studies/pace-g/GRADE.md` and `studies/pace-h/PREDICTION.md` (SHA-256 `c98c96cb…`) (`fetched.json`). Its tests passed (31 of 31, `tests.txt`). `pace_h.py` (SHA-256 `db0306b3…`) and `test_pace_h.py` (`a6cc0c84…`) are published here byte for byte as the job ran them. Every number below is read from `summary.json`; `report.md` has the same tables. "Share" is the median paired time difference over the reference's median time: + is slower.

## Predictions

| | prediction | result | held? |
|---|---|---|---|
| H1 | check: 36 compared, 36 identical, 0 missing | 36, 36, 0 | **yes** |
| H2 | all 1,440 missions completed | 1,440 of 1,440 | **yes** |
| H3 | dr+cf0.3 vs cf0.3 slower on all 3 courses of measured | slower 3 of 3: bayside +6.68%, blocks +1.24%, boulevard +6.47% (24 of 24 seeds slower on each) | **yes** |
| H4 | bridge+cf0.3 vs cf0.3: `groups_slower` 0 and `groups_lost` 0 on every profile; \|share\| ≤ 0.005 on every course of measured and noise8 | slower 0, lost 0 on all four profiles; shares 0.0000, 0.0000, −0.0006 (measured) and −0.0014, 0.0000, 0.0000 (noise8) | **yes** |
| H5 | bridge+cf0.3 vs cf0.3 faster on all 3 courses of both dropout profiles, share ≤ −0.03 on each | faster 3 of 3 on each (24 of 24 seeds on every course); shares −0.049, −0.054, −0.048 (dropout0.3) and −0.051, −0.054, −0.050 (dropout0.3-noise8) | **yes** |
| H6 | bridge+cf0.3 vs dr+cf0.3: `groups_slower` 0 and `groups_lost` 0 on every profile; `groups_faster` ≥ 2 on measured and noise8 | faster 3 of 3 on measured and on noise8, lost 0 everywhere, but **slower on blocks of dropout0.3-noise8** (+1.26%, 21 of 24 seeds slower, p = 0.0003) | no |
| H7 | bridge+cf0.3 pooled `median_made_good_mps` ≥ 0.87 on measured and noise8, ≥ 0.85 on both dropout profiles; `beat_human_pace` 72 on all four | 0.879, 0.877, 0.869, 0.867; 72 of 72 on all four | **yes** |
| H8 | dr+cf0.3+kb vs cf0.3 still slower on bayside and boulevard of measured, share ≥ +0.03 on both | slower on both: +6.82% and +6.96% (24 of 24 seeds) | **yes** |
| H9 | drg0.3+cf0.3 vs dr+cf0.3 faster on ≥ 2 of 3 courses of measured | faster on 3 of 3: −4.43%, −2.65%, −4.07% (24 of 24 seeds) | **yes** |
| H10 | measured, every course: dr+cf0.3's `median_mean_abs_angular` above cf0.3's and bridge+cf0.3's within 10% of cf0.3's; dr+cf0.3's `median_breaks` ≥ 3× cf0.3's and bridge+cf0.3's ≤ 1.1× | angular: dr+cf0.3 0.223 / 0.224 / 0.209 against cf0.3 0.046 / 0.059 / 0.044 (3.8-4.8×); bridge+cf0.3 0.4-1.1% above cf0.3. Breaks: dr+cf0.3 477 / 505.5 / 588 against 97.5 / 129.5 / 98 (3.9-6.0×); bridge+cf0.3 0.98-1.01× | **yes** |

Courses are listed as bayside / blocks / boulevard.

## Decision rules

- **R1 fails.** H1 did not fail. bridge+cf0.3 against cf0.3 was slower nowhere and lost nothing, and it was faster on 3 of 3 courses of each dropout profile. Against dr+cf0.3 it lost nothing. But it was slower on one course: blocks on dropout0.3-noise8 (+1.26%, 21 of 24 seeds). It was also behind on blocks on dropout0.3 (+0.43%, 15 of 24 seeds), though not significantly (p = 0.078). R1 required slower 0 against both pilots on every profile.
- **R2 fails.** drg0.3+cf0.3 against cf0.3 was slower on bayside and boulevard of measured (+2.09%, +2.16%) and of noise8 (+1.79%, +2.18%), 24 of 24 seeds each.
- **R3 applies** (H3 held). v0.14.0 turns dead reckoning off by default on a real rover; `--dead-reckon` turns it on, and README says that the pilot then stops through GPS gaps. In this study, with 30% of fixes missing, the pilot without dead reckoning stood still 5.8% of the time; with v0.13.0's dead reckoning it stood still 0.5%, and with bridging 0.4-0.5%. On a clean GPS the change gains back what pace-g measured: cf0.3 made good 0.878 m/s on measured against 0.828 for v0.13.0's pilot.
- **R4.** The check found no difference (36 of 36 identical), so these results stand as findings.
- **R5.** This grade, the outputs and the code are in `studies/pace-h/` and at the top level. README and FINDINGS get pace-g's and pace-h's results in v0.14.0.

Not covered by any rule, and so stated here before the release: v0.14.0 also adds bridging as an option (`--dead-reckon-gaps`: dead reckoning steered by only while the GPS has no fresh fix), off by default. Its test must fly pace-h's `bridge+cf0.3` missions exactly. Whether it becomes the default is left to pace-i, a new pre-registered study on fresh seeds, with GPS outages that come in runs as real ones do.

## What the study found that was not predicted

**1. The cost is the jumps, not the learner (pace-g's explanation holds).** v0.13.0's pilot weaves: on measured it applied a mean |angular| of 0.21-0.22 while driving forward, against 0.044-0.059 without dead reckoning. Knowing the compass bias from the start made no difference to that. dr+cf0.3+kb ended with 2.0-2.3° of bias error against 3.5-4.3° for dr+cf0.3. Yet it steered just as hard (0.22-0.23), broke as many straight stretches (483-595) and was faster than dr+cf0.3 on no course. It was slightly slower on 5 of 12 (+0.35% to +0.91%). Moving the reckoner only 0.3 of the way to each fix roughly halved both the steering (0.12-0.13) and the cost (+2.1-2.2% against cf0.3 on bayside and boulevard instead of +6.5-6.7%). Bridging steers exactly as cf0.3 does while the GPS is fresh, and it weaved no more than cf0.3.

**2. At corners a fresher position helps, even on a clean GPS.** Blocks is the course of right-angle corners. There dead reckoning cost only +1.24% where it cost +6.5-6.7% on the other two courses. The gentler reckoner was *faster* than cf0.3 on blocks (−1.37% on measured, −1.33% on noise8; 24 of 24 seeds each). On blocks the rover's distance from the course reached 10.2 m (95th percentile) with cf0.3 and with bridging, against 7.3 m with v0.13.0's dead reckoning and 7.7 m with the gentler one. The GPS filter's position is a smoothed average of fixes that arrive 1.5 s late, and it ran a median 6.4-6.6 m from the truth, against 2.6 m for dead reckoning. A likely reason, not yet tested: a pilot steering by that lagging position turns late and overshoots corners. This is probably why bridging lost to v0.13.0's pilot on blocks with GPS gaps: there, v0.13.0's position was the fresher one. Turning late at corners is a known effect of lagging position estimates in path followers. What is measured here is its size on this rover's telemetry.

**3. Through GPS gaps, bridging keeps v0.13.0's saving without its cost.** With 30% of fixes missing, bridging made good 0.869 m/s (0.867 with 8° of compass noise). Without dead reckoning the pilot made 0.822 (0.820), and with v0.13.0's 0.832 (0.835). It stood still 0.4-0.5% of the time, like v0.13.0's pilot, against 5.8% without dead reckoning. Its compass-bias learner worked as cf0.3's does: 38-56 calibrations a mission on dropout0.3, against 36-52.5 for cf0.3 and 2 for v0.13.0's pilot.

**4. With 8° of compass noise, v0.13.0's pilot hardly learned its compass bias.** It made one calibration a mission and ended 10.8-16.9° off on noise8 (15.7-18.1° on dropout0.3-noise8). Without dead reckoning, and with bridging, it made 23.5-33.5 calibrations and ended 2.1-3.4° off. The weaving from finding 1 breaks the learner's straight stretches.

## Limits

Simulated rovers only (pace_d.py's `DistortedRover` with pace_g.py's measured Mini+ settings), so speeds are bounds on what a real sidewalk allows. GPS noise and dropouts are independent from fix to fix; real GPS errors drift and real dropouts come in runs, which pace-i tests. The simulated wheels report the commanded speed exactly. The mechanism in finding 2 is a hypothesis. None of this has been measured on a live Mini+.
