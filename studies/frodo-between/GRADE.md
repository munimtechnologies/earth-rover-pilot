# frodo-between-v1: grade

Graded 2026-10-22 (~04:00 UTC) against `PREDICTION.md`, which was written before the run. MV2 of Munim, Inc.; graded with AI agents. CC BY-SA 4.0 (results derive from FrodoBots-2K).

Run: `frodo_between.py` 0.1.0 on the compute runner, 2026-10-22 02:11-03:04 UTC (51 minutes, 461 MB read over range requests, peak memory 0.38 GB). Unit tests first: 69 of 69 passed (`test_frodo_compass`, `test_frodo_compass_live`, `test_frodo_blend_b`, `test_frodo_between`). Rides: 713 sampled, 167 scored (41.7 hours of GPS), 145 with pairs; the same held-out rides and anchors as `frodo_blend_b.py`. Full tables: `report.md`, `summary.json`.

## Check E1: passed

13,460 pairs at 10 s. `interp`/`course` = 0.883 and `b2_interp`/`interp` = 0.944, the same as frodo-blend-b-v2's `running`/`course` and `blend2`/`running` (needed within 0.002). The decision rules below apply.

## Median miss of the next GPS fix (m), same anchors for every variant

| variant | 1 s | 5 s | 10 s | 30 s |
|---|---|---|---|---|
| course | 0.31 | 1.05 | 1.94 | 5.56 |
| interp (looks up to ~1 s ahead) | 0.33 | 1.02 | 1.71 | 3.59 |
| last (what a live pilot reads) | 0.33 | 1.02 | 1.72 | 3.60 |
| gyro05 | 0.33 | 1.03 | 1.73 | 3.60 |
| gyro1 | 0.34 | 1.04 | 1.74 | 3.60 |
| cmd20 | 0.33 | 1.02 | 1.72 | 3.60 |
| b2_interp (v0.11.0 hold) | 0.31 | 0.96 | 1.62 | 3.49 |
| b2_last | 0.31 | 0.96 | 1.62 | 3.50 |
| pairs | 14,143 | 13,859 | 13,460 | 12,112 |

## Decisions

- **D1 (reported):** `last`/`interp` = 1.006 at 10 s (95% CI 0.998-1.010) and 1.004 at 30 s. The look-ahead in the earlier compass studies was worth well under 1%. A live pilot's compass misses the fix 10 s later by 0.888x the last GPS course (CI 0.847-0.943) and 0.648x at 30 s.
- **D2: nothing is built.** Over `last` at 10 s: `gyro05` 1.001 (CI 0.996-1.008), `gyro1` 1.010 (CI 1.000-1.016), `cmd20` 0.998 (CI 0.994-1.003). The bar was at most 0.98 with the interval's top below 1; none came close. Cost at 30 s was 0.001 or less for each, so that rule did not decide anything.
- **D3: the course hold stays.** `b2_last`/`last` at 10 s = 0.943 (CI 0.920-0.963), within the rule (at most 0.97, top below 1). 0.11.0's `course_hold_s` 2.0 with `fade` stands for a live pilot.

## Predictions: 7 of 8 held

| | Prediction | Result | |
|---|---|---|---|
| P1 | E1 passes with exactly 13,460 pairs at 10 s | 13,460 pairs; 0.883 and 0.944 | held |
| P2 | `last`/`interp` at 10 s in 1.00-1.05 | 1.006 | held |
| P3 | `gyro05`/`last` at 10 s <= 1.00 | 1.001 | **missed** (by 0.001; CI 0.996-1.008) |
| P4 | `gyro1`/`last` > `gyro05`/`last` at 10 s | 1.010 > 1.001 | held |
| P5 | `cmd20`/`last` at 10 s in 0.98-1.01 | 0.998 | held |
| P6 | D3 met | 0.943, CI top 0.963 | held |
| P7 | D2 builds nothing | nothing passed | held |
| P8 | `last`/`interp` at 30 s <= 1.03 | 1.004 | held |

## What it means

- Every compass figure in FINDINGS-frodobots-2k.md was measured with a heading interpolated between 1 Hz reads. Re-scored with only past reads, the figures move by at most 0.01 m at 10 s and 30 s. The conclusions stand for a pilot driving live.
- Turning the held read by the gyroscope or by the command between reads gains nothing on these rides; the full gyroscope turn is slightly worse, as it was for the wheels along the GPS course (`frodo_odometry.py`). A possible reason, not tested here: the rover turns at most about 30 deg/s (at full `angular`), so the heading change inside a 1 s gap is mostly small next to the live compass's median heading error of about 12 deg (`frodo_compass_live.py`).
- The pilot needs no change: it already uses the latest reading it has.

## Limits

- Earth Rover Zero, raw 1 Hz magnetometer and 1 Hz gyroscope. The Mini+ telemetry holds `orientation` up to about 2 s between reports, a longer gap; `pace_study.py` looked at that only in simulation.
- The bias every variant uses was learned from interpolated headings, on straight stretches where `last` and `interp` nearly agree.
- The gyroscope's units are inferred (deg/s), not documented. `cmd20` assumes 20 deg/s per unit and a 0.5 s delay.
- The reference is the next GPS fix, not surveyed truth. Human-driven rides that calibrate and have straight stretches (the smoother ones).
