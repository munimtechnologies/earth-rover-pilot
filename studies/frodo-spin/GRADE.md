# frodo-spin-v1: grade

Graded 2026-10-29 against `PREDICTION.md`, which was committed before the run (155ed3b). By MV2 of Munim, Inc.; the grading and write-up are made with AI agents. Text CC BY 4.0; the figures derive from FrodoBots-2K (FrodoBots Lab, CC BY-SA 4.0) and are shared under CC BY-SA 4.0.

**Result: check E1 failed, so nothing is decided.** In-place turns from rest to rest are rarer in the recorded rides than the plan assumed: 720 sampled rides gave 59 turns on 49 rides, short of the 100 turns on 40 rides E1 asked for. D1 (gyroscope units) and D2 (short pulses) are therefore not decided, and FINDINGS keeps its gyroscope-based turn rate. For the record, all 6 testable predictions came out inside their ranges, and P3 was not testable.

## The run

- Job `frodo-spin-v1`, sealed container, 2026-10-29 14:21-14:38 UTC (16 min, peak memory 0.09 GB). `fetch_deps.py` found `PREDICTION.md` on main and confirmed that `frodo_spin.py` 0.1.0 and `test_frodo_spin.py` were byte for byte the pre-registered copies (`same_as_main: true`), with frodo_motion 0.2.0 (v0.8.0) and frodo_compass / frodo_compass_live 0.1.0 (main). The unit tests passed.
- 30 rides per part from all 24 parts: 720 sampled, 256 MB read over range requests. 667 had no in-place turn from rest, 4 had a compass that failed calibration, 49 were analysed, 0 errors.

## Check E1: failed

| Stated before the run | Result | |
|---|---|---|
| at least 100 turns | 59 | **no** |
| from at least 40 rides | 49 | yes |
| at least 85% of turns of 10° or more went the commanded way | 100% | yes |
| g positive | 29.53 | yes |

## Predictions (reported; E1 failed, so they decide nothing)

| | Prediction | Result | |
|---|---|---|---|
| P1 | g between 20 and 36 deg/s per unit | 29.53 (95% CI 24.31-35.13, rides resampled) | inside |
| P2 | c between -15 and +15 deg | -2.77 | inside |
| P3 | 2-3 s holds with \|angular\| >= 0.8 (at least 10) turn a median 35-85° | only 2 such turns | not testable |
| P4 | gyro gain / g between 0.75 and 1.33 | 35.08 / 29.53 = 1.188 (32 turns) | inside |
| P5 | at least 90% of turns of 10° or more went the commanded way | 100% | inside |
| P6 | median rate per unit lower for 0.3-1 s holds than for 2-3 s holds | 12.55 against 23.11 deg/s | inside |
| P7 | upper end of g's 95% interval below 48 deg/s per unit | 35.13 | inside |

## What it shows, short of a decision

- **The compass agrees with the gyroscope's turn rate.** Measured from the calibrated compass before and after each turn, without the gyroscope, an in-place turn on the recorded Earth Rover Zeros fits turn = 29.5 deg/s × |angular| × seconds − 2.8°. The gyroscope's own reading over the same turns is 1.19 times that. Both match the 28-30 deg/s per unit that FINDINGS has used since v0.7.0. With 59 turns this supports that figure but, under E1, does not settle it.
- **Short holds turn much less per second.** Holds of 0.3-1 s turned a median 3.6° (12.6 deg/s per unit) and 1-2 s 10.8° (10.7 deg/s per unit), against 39.6° (23.1) for 2-3 s and 88.8° (36.3) for 3-5 s. With so few turns per bin, and the compass's error of about 10° per reading on each side, this is suggestive only; D2 needed 10 turns in the 2-3 s bin and had 9.
- **What a 2.5 s held turn does.** By the fit, one RoboColosseum observation's held command turns a Zero about 71° at angular 1 and 34° at 0.5. The GeNIE baseline's notes report about 45° per answered turn on a Mini+, which would fit angular of about 0.65 on a Zero, or a Mini+ that turns faster per unit. At `--max-angular 0.3`, the setting colosseum-hold-confirm supports in a 60 deg/s simulator, the fit gives about 19° per 2.5 s hold on a Zero, against 45° in the simulator.

## What comes next

A larger sample under the same code and the same pre-registered predictions and rules: `frodo-spin-v2` reads up to 200 rides per part (about 4,000; written down in `PLAN-v2.md` before it runs). It will re-read the 720 rides v1 read where they fall in its sample, so it is a bigger sample, not an independent replication, and v1's numbers above were seen before it was planned. That is stated in the plan.

## Limits

As stated in advance: the rides are human-driven Earth Rover Zero-era rides, not SDK or bridge commands, and the Mini+ may turn at a different rate. One compass sample on each side of a turn, with no tilt or soft-iron correction. Turns over about 300° would be misread, so holds are capped at 5 s.

## Files

`summary.json`, `report.md`, `events.jsonl` and `rides.jsonl` (one line per sampled ride) are committed beside this file.
