# pace-e: grade

MV2 of Munim, Inc. Written with AI agents. CC BY 4.0.

The predictions (`PREDICTION.md`) were committed to main before any mission was flown. The job `pace-e-v1` fetched main at 2026-10-22T22:17:15Z with that file on it (SHA-256 `2eb9e69a…`, `fetched.json`), ran `test_pace_e`, `test_pace_d` and `test_smooth_heading` (56 tests, OK, `tests.txt`), then flew the study in 25 minutes. `pace_e.py` (SHA-256 `910bcf6a…`) and `test_pace_e.py` (`c86169db…`) are published here byte for byte as the job ran them. rover_pilot 0.12.0. Every number below is read from `summary.json`.

**8 of 9 predictions held. Q7 missed.**

## Predictions

**Q1. All 1,080 missions are completed. Held.** `completed` = 1080 of `runs` = 1080.

**Q2. The check against pace_d.py's runs. Held.** `check`: compared 216, identical 216, missing 0, different [].

**Q3. The finding, counted. Held.**
- (measured-noise10, shipped) `median_calibrations`: bayside 0.0, blocks 0.0, boulevard 0.0. `zero_calibration_missions`: 11, 12, 12 of 12 (needed at least 10).
- (measured-noise10, cf0.3) `median_calibrations`: 13.0, 12.0, 18.0 (needed at least 1).

**Q4. More noise, fewer calibrations. Held.** Shipped pilot, `median_calibrations` along measured → noise6 → noise8 → measured-noise10 → noise12:
- bayside 23.5, 0.0, 0.0, 0.0, 0.0
- blocks 24.0, 0.5, 0.0, 0.0, 0.0
- boulevard 33.0, 1.0, 0.0, 0.0, 0.0

It never rises, and it is at least 1 on measured.

**Q5. The straight-stretch test is what stops it. Held.**
- (measured-noise10, shipped) `spread_checked_per_mission`: 0.08, 0.0, 0.0 (needed below 1.0).
- (measured-noise10, spread0.95) `median_calibrations`: 0.0, 0.0, 0.0.

**Q6. Loosening the straight-stretch test brings the learning back. Held.**
- (measured-noise10, straight0.3) `median_calibrations`: 13.5, 12.5, 19.5.
- (measured-noise10, both) `median_calibrations`: 52.5, 52.0, 63.5. `median_abs_bias_error_deg`: 2.66, 3.58, 2.83 (needed below 10).

**Q7. No harm, and little time at stake. Missed.**
- `both` against shipped, `verdicts` `groups_slower`: measured 2, noise6 1, noise8 1, measured-noise10 0, noise12 0, drift10 3. That is 7 of 18 groups, where the prediction was none. The largest slowdown is 0.43% (drift10, blocks, `median_time_diff_share` 0.0043).
- The second part held: on measured-noise10, `both`'s `largest_median_diff_share` is −0.0054 (|value| < 0.01).

**Q8. The unlearned bias shows as an offset from the path. Held.**
- (measured-noise10, shipped) `median_offset_m`: blocks 3.88, boulevard 3.71 (needed 2.5-5.0). Bayside is 3.69. The geometric estimate was 8 × tan 25° = 3.73 m.
- (measured, shipped): bayside 0.64, blocks 1.31, boulevard 1.9 (needed below 2.0).
- (measured-noise10, both): 0.83, 1.36, 1.69, each below shipped's 3.69, 3.88, 3.71.

**Q9. Under the drift, more fits help. Held.** `heading` `median_abs_deg`, drift10: `both` 5.53, 5.87, 5.5 against shipped 8.16, 8.0, 7.44.

## Decision rules

- **E1: no loosened learner qualifies.** For each candidate, in the order the rule gives:
  - `straight0.3`: (a) holds (on measured-noise10 `median_calibrations` 13.5, 12.5, 19.5; `median_offset_m` 0.72, 1.71, 1.77 against shipped's 3.69, 3.88, 3.71). (c) holds (on measured, 0.69, 1.34, 1.79 against 0.64, 1.31, 1.9: at most 0.05 m above). **(b) fails**: it is slower than shipped in 5 of 18 groups (measured 2, noise6 1, drift10 2), by at most 0.28%.
  - `spread0.95`: **(a) fails**: `median_calibrations` 0 on every course of measured-noise10. In fact it flew every one of its 216 missions in the same time as shipped (0 faster, 0 slower in all 18 groups), because the shipped pilot's spread test never turned a fit down (`spread_rejected_share` 0.0 wherever a fit reached it).
  - `both`: **(b) fails**: slower in 7 of 18 groups.
- **E2 applies: the pilot is unchanged.** README and FINDINGS now say that with about 6° of compass noise or more, the shipped pilot does not learn its compass bias. Q3's cf0.3 part held, so they name `--smooth-heading` as the way to get the bias learned.
- **E3 does not apply.** Q5 held: fits hardly ever reach the spread test (`spread_checked_per_mission` 0.08 or less).
- **E4 does not apply.** The check found 216 of 216 identical.
- **E5:** the grade, outputs and code are in `studies/pace-e/` and at the top level, and the results are in FINDINGS-frodobots-2k.md and the README.

## What else the outputs show (not predicted)

- **Learning stops by 6° of noise, not 10°.** With 6° the shipped pilot calibrated in a median of 0-1 times per mission (`zero_calibration_missions` 8, 6, 5 of 12). It steered 24.3-24.9° off (`heading` medians) and drove 3.63-3.83 m from its course, about as far as with 10° or 12° of noise. With 3° it learned the bias (23.5-33 calibrations; 3.5-4.0° heading error). So the edge lies somewhere between 3° and 6°, and how noisy a real Mini+ compass is has not been measured.
- **`--smooth-heading` fixes it best.** With cf0.3, the heading error was the lowest of the five variants on every course at every level of fresh noise (3-12°): 4.25-5.37° at 10° of noise against 7.8-9.0° for the loosened learners and 25° for shipped. It was faster than shipped in 15 of 18 groups and slower in none. Its offset from the course stayed between 0.64 and 2.24 m (median) on every profile.
- **Once the straight-stretch test is loosened, the spread test takes over.** With `straight0.3`, the spread test turned down 71-75% of the fits that reached it at 10° of noise and 86-89% at 12°. Loosening it too (`both`) used them all. More fits did not mean a better heading: `both` was off by 7.8-8.0° at 10° of noise, against 4.3-5.4° for cf0.3, which used only 12-17 fits per mission. Under the drift the three were close (5.4-6.0°).
- Every mission in every group beat the human marathon pace (0.754 m/s). The slowest group median was 0.845 m/s (noise12, shipped).

## Limits

Simulated rovers only, so speeds and offsets are upper bounds on what a real sidewalk allows. The noise is Gaussian and independent from one reading to the next. The −25° compass error, the drift and the noise levels are the simulator's, not measurements of a real Mini+. The offset is to the nearest segment of the course, which understates it on corners.
