# frodo-spin-v2: grade

Graded 2026-10-29 against `PREDICTION.md` (155ed3b, committed before v1 ran) and `PLAN-v2.md` (committed before v2 ran). By MV2 of Munim, Inc.; the grading and write-up are made with AI agents. Text CC BY 4.0; the figures derive from FrodoBots-2K (FrodoBots Lab, CC BY-SA 4.0) and are shared under CC BY-SA 4.0.

**Result: check E1 passed and all 7 predictions held, so both rules decide.** On 297 in-place turns from rest to rest (235 rides), a recorded Earth Rover turned 23.4 deg/s per unit of `angular` held (95% CI 20.5-26.6), measured from the calibrated compass alone. **D1:** the gyroscope agrees (0.978 times that), so it reads degrees per second. **D2:** short pulses cost turn: holds of 0.3-1 s turned at 5.1 deg/s per unit, under half the 18.0 of 2-3 s holds. So a steering mode built for RoboColosseum's held commands should hold a turn for the whole observation, not pulse it.

## The run

- Job `frodo-spin-v2`, sealed container, 2026-10-29 19:32-20:50 UTC (77 min, peak memory 0.1 GB). `fetch_deps_v2.py` found `PLAN-v2.md` on main and confirmed that `frodo_spin.py` 0.1.0 and `test_frodo_spin.py` were byte for byte the files v1 ran (`same_as_v1: true`, sha256 194b3bca... and 7fbc1bb0...). The unit tests passed.
- Up to 200 rides per part from all 24 parts: 4,171 sampled, 422 MB read over range requests. 3,890 had no in-place turn from rest, 30 had a compass that failed calibration, 1 had no compass, 250 were analysed, 0 errors.

## Check E1: passed

| Stated before v1 | Result | |
|---|---|---|
| at least 100 turns | 297 | yes |
| from at least 40 rides | 235 | yes |
| at least 85% of turns of 10° or more went the commanded way | 100% | yes |
| g positive | 23.41 | yes |

## Predictions

| | Prediction | Result | |
|---|---|---|---|
| P1 | g between 20 and 36 deg/s per unit | 23.41 (95% CI 20.46-26.64, rides resampled) | held |
| P2 | c between -15 and +15 deg | -3.13 | held |
| P3 | 2-3 s holds with \|angular\| >= 0.8 (at least 10) turn a median 35-85° | 36.1° on 12 turns | held, by 1.1° |
| P4 | gyro gain / g between 0.75 and 1.33 | 22.9 / 23.41 = 0.978 (157 turns) | held |
| P5 | at least 90% of turns of 10° or more went the commanded way | 100% | held |
| P6 | median rate per unit lower for 0.3-1 s holds than for 2-3 s holds | 5.12 against 18.01 deg/s | held |
| P7 | upper end of g's 95% interval below 48 deg/s per unit | 26.64 | held |

## Decisions

- **D1 (gyroscope units): holds.** The gyroscope's x axis reads degrees per second. By the rule, FINDINGS keeps its gyroscope-based method. What this run adds is a number for one kind of turn: from rest to rest in place, including spin-up and coasting, the rover averages about 23 deg/s per unit, and the gyroscope over the same turns says the same. FINDINGS' 28-30 deg/s per unit is close to the rate on longer holds (3-5 s: 26.9 deg/s per unit by the bins) and is not contradicted; the next documentation release should state both.
- **D2 (short pulses): holds.** The rate per unit rises with hold time: 5.1 (0.3-1 s), 11.5 (1-2 s), 18.0 (2-3 s) and 26.9 deg/s (3-5 s). A held-command steering mode should keep a turn for the whole 2-3 s observation rather than send a short pulse. earth-rover-pilot's existing behaviour under the bridge already does this, because the bridge holds whatever command it samples.

## What it changes

- **The README's RoboColosseum note uses v1's figure.** v0.19.2's "Running under RoboColosseum" section says a 2.5 s hold at `--max-angular 0.3` turns a Zero about 19°, from v1's fit (29.5 deg/s per unit on 59 turns). By v2's fit (23.41 × 0.3 × 2.5 − 3.13) it is about **14°**; at 0.5 about 26° and at full angular about 55°. The next documentation release corrects this.
- **It raises a fair question about that recommendation.** `--max-angular 0.3` was chosen in a simulator that turns 60°/s at full angular, where one 2.5 s hold at 0.3 turns 45°. On a rover turning 23 deg/s per unit, the same cap allows only about 14-18° per observation, so a large heading error takes many observations to remove, while a higher cap may no longer overshoot. `studies/colosseum-rate` (pre-registered beside this grade, before any flight) flies the same bridge simulation at 23.4 and 48 deg/s per unit to test that.

## Honest limits

- **Not blind and not independent of v1.** v2 re-read many of v1's rides; its predictions were set before v1, not before v2, and v1's numbers were seen when v2 was planned (all stated in `PLAN-v2.md`).
- **v1 read high.** v1's 59 turns gave g = 29.5 (CI 24.3-35.1); v2's 297 give 23.4 (CI 20.5-26.6). The intervals overlap only between 24.3 and 26.6. v1's sample was too small, which is what E1 was for.
- As stated in advance: human-driven rides on mostly Earth Rover Zero-era hardware, not SDK or bridge commands; the Mini+ may turn at a different rate. One compass sample on each side of a turn, with no tilt or soft-iron correction; turns over about 300° would be misread, so holds are capped at 5 s. P3 held on 12 turns by a 1.1° margin.

## Files

`v2/summary.json`, `v2/report.md`, `v2/events.jsonl` and `v2/rides.jsonl` (one line per sampled ride) are committed beside this file.

## Reproduce

```
python fetch_deps_v2.py
python -m unittest -v test_frodo_spin
python frodo_spin.py --out-dir out-spin2 --parts all --rides-per-part 200 --budget-min 220
```
