# Grade: smoothing the heading on a Mini+ with a noisy compass (pace_c.py 0.1.0)

Graded 2026-10-22 (about 13:50 UTC) against `PREDICTION.md` in this folder, by MV2 of Munim, Inc.; the grading and this text were made with AI agents. Licence CC BY 4.0 (text).

**Result: all 8 predictions held.** All 720 simulated missions were completed. Under rule D1, a later release adds the complementary filter (`cf0.3`) to the pilot as an option that is off by default.

## The run

- Job `pace-c-v1`: started 12:31:32 UTC and finished 12:50:37 UTC (1,145 s, peak memory 0.02 GB). Unit tests ran first: 43 tests (`test_pace_c`, `test_pace_b`, `test_pace_study`), all OK. Then `python pace_c.py --out-dir /out --seeds 12 --budget-min 70` ran for 926 s.
- Code: `pace_c.py` 0.1.0, `pace_b.py` 0.1.0, `pace_study.py` 0.1.0 and `rover_pilot.py` 0.11.2, fetched from `main` when the job started. File hashes are in `fetched.json`.
- When the pre-registration was written: `PREDICTION.md`'s header says "between about 12:40 and 13:00 UTC". That is wrong, the same mistake as in pace-b. The job copied `PREDICTION.md` into its output in step `run-02`, about 12:31:34 UTC, before step `run-03` flew any mission. So the file existed, unchanged, before any result did. The job log is the record of that order.

## Predictions

| | Prediction | Result (from `summary.json`) | Grade |
|---|---|---|---|
| Q1 | `shipped` pooled made good: `measured` 0.769 at 0.7 and 0.878 at 0.8; `measured-noise10` 0.750 and 0.855 (each ±0.001) | 0.769 / 0.878; 0.750 / 0.855 | **held** (exact reproduction of pace_b) |
| Q2 | `completed` = 720 | 720 | **held** |
| Q3 | `measured-noise10`, `cf0.3` vs `shipped`: faster in ≥ 5 of 6 groups, slower in none | faster 6, slower 0 (each group 12 of 12 seeds faster, p = 0.0005) | **held** |
| Q4 | `measured-noise10`, `cf0.3` at 0.8: pooled median ≥ 0.867 m/s | 0.874 | **held** (83% of the 0.855 to 0.878 gap won back) |
| Q5 | `measured`, `cf0.3` vs `shipped`: no completion lost, `largest_median_diff_share` ≤ +0.01 | lost 0; largest −0.0027 (no group slower; faster in 3 of 6) | **held** |
| Q6 | `measured-noise10`, `cf0.3-yaw30` vs `shipped`: faster in ≥ 4 of 6 groups | faster 6, slower 0 | **held** |
| Q7 | `measured-noise10` at 0.8: `ema0.3` pooled median below `cf0.3`'s | 0.865 < 0.874 | **held** |
| Q8 | `measured-noise10`, `cf0.3` at 0.7: `beats_on_every_course` true | true (36 of 36 runs beat 0.754 m/s, against 1 of 36 for `shipped`) | **held** |

## Decision rules

- **D1 (Q3 and Q5 held).** A later release adds the complementary filter to the pilot as an opt-in option with its own tests, off by default. It takes the turn rate from `--calibrate` (`yaw_dps_at_full`) when a calibration is given. The default changes only after the compass noise of a real Mini+ has been measured.
- **D2.** Not triggered: `cf0.3` was faster in 6 of 6 `measured-noise10` groups.
- **D3.** Not triggered: on the `measured` profile `cf0.3` lost no completion and was slower in no group. Its largest median difference was a 0.27% gain.
- **D4.** Not triggered: Q6 held. With a wrong rate (30°/s for a rover that turns at 48°/s), the filter still won back almost all of the noise cost. So the option may keep a built-in default rate, the 48°/s measured on public Mini+ recordings, for use when no calibration is given.
- **D5.** Not triggered: Q1 reproduced pace_b's numbers exactly.

## What the numbers mean for the marathon

| 80.5 km on a Mini+ with 10° compass noise | cruise 0.7 | cruise 0.8 |
|---|---|---|
| shipped pilot, made good | 0.750 m/s, 29.8 h of driving, **0.2 h slower than the human 29 h 38 min even with no stops** | 0.855 m/s, 26.1 h, about 3.5 h left for stops |
| with `cf0.3`, made good | 0.768 m/s, 29.1 h, about 0.5 h left | 0.874 m/s, 25.6 h, about 4.1 h left |
| with no extra noise (3°), shipped | 0.769 m/s, 0.6 h left | 0.878 m/s, 4.2 h left |

- The filter cut the time on each 1.3-1.6 km course by 32-46 s (2.1-2.5%). Ten degrees of noise had cost 2.4-3.1% in pace_b, so most of that cost came back. Efficiency (made good / ideal) at 0.8 rose from 0.962 to 0.984, against 0.988 with the cleaner compass.

## What else the run shows (not pre-registered)

- **A plain average lags, and the lag costs time.** With the cleaner 3° compass, `ema0.3` was slower than the shipped pilot in all 6 groups (0.45-0.81%) and `ema0.5` in 3 of 6. Turning the estimate by the commanded angular (`cf0.3`) removed that cost: it was 0.1-0.3% faster in 3 of 6 groups and slower in none.
- **With noise, the plain averages help about half as much.** `ema0.5` and `ema0.3` were faster in all 6 noisy groups, by 0.8-1.3%, against 2.1-2.5% for `cf0.3`. At cruise 0.7 they beat the human pace in 31 and 35 of 36 runs.
- **The exact turn rate matters little.** With the wrong rate, `cf0.3-yaw30` was within 0.001 m/s of `cf0.3` everywhere (0.873 against 0.874 at 0.8, noisy). On the clean compass it was neither faster nor slower in any group.
- Paths straightened too: the city-blocks path ratio at 0.8 with noise fell from 1.016 to 1.009.

## Limits

These are simulated rovers on synthetic 1.3-1.6 km courses, with no pedestrians, crossings, kerbs or slopes, so all speeds are upper bounds. The compass noise is independent from report to report, which is the case a filter handles best. A real compass error that drifts, or that depends on heading or on nearby steel, will not average away like this, and no filter on one compass can remove a slowly changing bias. The 10° noise level is an assumption: a real Mini+'s compass noise has not been measured. The 48°/s, 0.5 s refresh and 0.5 s latency come from a few, mostly indoor, public recordings, and the Mini+ GPS rate (a fix every 2 s) is assumed. Orientation was simulated running the way the pilot assumes. A filter that predicts turns depends on that convention, which `--calibrate` measures on a real rover.

## Files

`report.md` (tables), `summary.json` (every field graded here), `runs.jsonl` (one line per mission), `fetched.json` (hashes of the code fetched), `PREDICTION.md` (the pre-registration, already on `main`).
