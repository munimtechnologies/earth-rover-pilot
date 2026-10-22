# pace-d: grade

MV2 of Munim, Inc. Graded with AI agents against [PREDICTION.md](PREDICTION.md), which was committed to main before any mission was flown. CC BY 4.0.

**Result: 7 of 8 predictions held. Q8 missed.** The bias learner did not absorb the slow drift. There is also one finding nobody predicted: with 10° of fresh compass noise, the shipped pilot never learns its compass bias at all (below).

## The run

- Job `pace-d-v1` ran on 2026-10-22 from 20:03 to 20:21 UTC (1,107 s; peak memory 0.05 GB). `fetched.json` shows it fetched main at 20:03:12Z with rover_pilot 0.12.0. It records the SHA-256 of the PREDICTION.md it found (`4473ece3…`) and of the study code it ran: `pace_d.py` `d7f026fc…` and `test_pace_d.py` `2f126db8…`. The two files published next to this grade are those exact files.
- Tests: `test_pace_d`, `test_pace_c` and `test_smooth_heading` passed, 56 tests in total (`tests.txt`, `tests_exit` 0).
- Outputs: `summary.json`, `runs.jsonl` (one line per mission), `report.md`.

## Predictions

| | prediction | field(s) read | value | |
|---|---|---|---|---|
| Q1 | all 720 missions completed | `runs`, `completed` | 720, 720 | **held** |
| Q2 | the 288 `measured` / `measured-noise10` missions identical to pace_c.py's | `check` | compared 288, identical 288, missing 0 | **held** |
| Q3 | hardiron10 costs the shipped pilot < 1% in every group | `profile_tallies` (hardiron10, shipped) `largest_median_diff_share` | 0.0050 (0 of 6 groups slower at p < 0.05) | **held** |
| Q4 | drift10 costs the shipped pilot < 1% in every group | `profile_tallies` (drift10, shipped) `largest_median_diff_share` | 0.0055 (5 of 6 groups slower at p < 0.05, by 0.34-0.55%) | **held** |
| Q5 | hardiron20 costs less than 10° of fresh noise in each group | `profile_effect`, shipped, `median_time_diff_share` | hardiron20 0.0006 / 0.0049 / 0.0005 at 0.7 and 0.0049 / 0.0099 / 0.0006 at 0.8 (bayside / blocks / boulevard), against measured-noise10 0.0244 / 0.0280 / 0.0248 and 0.0244 / 0.0305 / 0.0255 | **held** (6 of 6) |
| Q6 | for hardiron20, blocks costs most at both cruises | same rows | 0.7: blocks 0.0049 > 0.0006, 0.0005; 0.8: blocks 0.0099 > 0.0049, 0.0006 | **held** |
| Q7 | `--smooth-heading` slower in none of the 18 lasting-error groups, and \|largest share\| ≤ 0.005 | `verdicts`, `largest` | groups slower 0 / 0 / 0; largest −0.0024 (hardiron10), −0.0021 (hardiron20), −0.0021 (drift10) | **held** |
| Q8 | drift10, shipped: group median \|heading error\| above measured's in all 6 groups and below 5° in all 6 | `heading` | 7.44-8.19° against measured's 3.54-3.95°: above in 6 of 6, below 5° in **0 of 6** | **missed** |

Notes on the ones that held:
- Q6 held on the medians, but the blocks differences behind it are not significant (sign test p = 1.0 at 0.7 and 0.77 at 0.8; 5 seeds faster and 6-7 slower). On the city blocks the hard-iron cost falls on a few seeds rather than on all of them.
- Q7: `--smooth-heading` was faster than the shipped pilot (p < 0.05) in 4 of 6 groups with hardiron10, 1 of 6 with hardiron20 and 4 of 6 with drift10, by at most 0.24%.
- No mission was lost on any profile. At cruise 0.8, every run of every profile and variant beat the human marathon pace (0.754 m/s). At 0.7, the shipped pilot beat it in only 1 of 36 runs with measured-noise10, and both variants beat it in 34 of 36 with hardiron20.

## Q8: the bias learner does not absorb the drift

With the drift, the heading the shipped pilot steered by was off by a group median of 7.4-8.2° (RMS 11.0-12.5°). On the `measured` profile it was 3.5-4.0° (RMS 6.5-7.3°). That is more than the 6.7° a 10° drift would give if nothing corrected it at all, because the drift adds to the error the pilot already has. Going by the RMS figures, almost none of the drift was taken out: √(12² − 7²) ≈ 10°, the drift's whole size. With `--smooth-heading` it was 5.4-6.1°. The pilot learns its bias again from every straight stretch it fits, at gain 0.3, so if it fitted one every 10-20 s it should have followed a drift with a 120 s time constant. Either it fits far less often than that, or each fit is too noisy. The pre-registered predictions don't separate the two; the next study does (below).

The cost in time stayed small all the same (Q4: at most 0.55%). An error that lasts makes the rover crab along its path, and crabbing costs little time.

## Not predicted: with 10° of noise the shipped pilot never learns its compass bias

Every simulated rover has a compass error of −25° that the pilot must learn from the GPS course on straight stretches (`HeadingEstimator`). In every one of the 72 measured-noise10 missions flown by the shipped pilot, the heading it steered by was off by about −25° on average: group medians of \|error\| were 24.96-25.03°, and per-mission means were −24.66 to −25.27° (the 12 boulevard missions at cruise 0.8). So the bias was never learned, or only in the last moments of a mission. On the same missions with `--smooth-heading`, the error was 4.3-5.4°. With 3° of noise, the shipped pilot's mean error per mission was within a few degrees of 0.

This was not pre-registered. It comes from the `heading_err` field the study added, and it was found while grading. Two gates in `HeadingEstimator` could cause it. Reading the code, both sit close to 10° of noise:
- **The straight-stretch test.** A stretch counts only while the low-passed `angular` command stays within ±0.1. At the steering gain of 1/60 per degree, that is about 6° of heading error. With 10° of noise on each reading, the command jumps past 0.1 every few readings. That could keep every stretch from lasting the ~10 s and 5 GPS fixes a fit needs.
- **The compass-spread test.** A fitted stretch is used only if its compass readings agree (mean resultant length ≥ 0.985). For Gaussian noise with standard deviation σ, that length is about e^(−σ²/2). At 10° that is 0.9849, just under the threshold.

What follows is inferred, not measured. With the 8 m lookahead of the path follower, a heading error of 25° that never goes away would hold the rover about 8 × tan 25° ≈ 3.7 m to one side of its path. That costs little time (measured-noise10 lost 2.4-3.1%, most of it to weaving) but would matter on a real sidewalk. On a real rover, dead reckoning (on by default) would also carry the position along the wrong heading. Part of what `--smooth-heading` gains with noise (pace_c.py: 2.1-2.5%) may come from letting the bias be learned at all, not only from the smoothing.

## Decision rules

- **D1** (Q7 held): lasting errors of these kinds are no reason to keep `--smooth-heading` off. It stays off by default only because no real Mini+ compass has been measured. README and FINDINGS say so, and they add the unlearned-bias finding above.
- **D2**: the largest (hardiron20, shipped) cost was 0.99%, below 2%, so no per-sector bias learner is built.
- **D3**: Q4 held, so the learner's gain is not studied as a fix for drift. Q8's miss is followed up by counting the fits instead (next study).
- **D4**: Q2 held (288 of 288 identical), so the findings stand.
- **D5**: the grade, the outputs and the code are published here, and the results go into FINDINGS-frodobots-2k.md and the README in documentation release v0.12.1.

## Next

`pace_e.py` (pre-registered in studies/pace-e/PREDICTION.md before it runs) counts what the bias learner does in every mission: stretches broken off, fits reaching the spread test, fits it turns down, and calibrations. It also measures how far the simulated rover really drives from its path. It flies the shipped pilot, `--smooth-heading`, the spread test loosened to 0.95, the straight-stretch test loosened to ±0.3, and both loosened together. The profiles are 3°, 6°, 8°, 10° and 12° of noise, plus the drift.

Limits: simulated rovers only, so the speeds are upper bounds. The hard-iron model has only the once-per-turn term, and the drift's size and time constant are guesses, not measurements.
