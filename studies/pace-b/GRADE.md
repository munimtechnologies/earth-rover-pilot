# Grade: the marathon pace on a Mini+ that reports like the measured one (pace_b.py 0.1.0)

Graded 2026-10-22 (about 12:30 UTC) against `PREDICTION.md` in this folder, by MV2 of Munim, Inc.; the grading and this text were made with AI agents. Licence CC BY 4.0 (text).

**Result: 6 of 8 predictions held, 2 missed (Q5, Q7).** All 720 simulated missions were completed. The pilot's code and defaults do not change (D4).

## The run

- Job `pace-b-v1`: started 10:15:32 UTC, finished 10:29:42 UTC (850 s, peak memory 0.02 GB). Unit tests first: 28 tests (`test_pace_b`, `test_pace_study`), OK. Then `python pace_b.py --out-dir /out --seeds 12 --budget-min 70`, 764 s.
- Code: `pace_b.py` 0.1.0, `pace_study.py` 0.1.0, `rover_pilot.py` **0.11.1** (fetched from `main` at the job's start, before v0.11.2 was published; 0.11.2 changed only documentation, and Q1 below reproduces the earlier numbers exactly). File hashes are in `fetched.json` of the job's output.
- Timing of the pre-registration: `PREDICTION.md`'s header says it was written "about 10:40 UTC". That time is wrong. The job copied `PREDICTION.md` into its output before flying any mission (step `run-02`, before `run-03` started at about 10:16 UTC), so the file existed, unchanged, before any result did. The same file was committed to this folder on `main` (commit 0fec48b) while the job was running.

## Predictions

| | Prediction | Result (from `summary.json`) | Grade |
|---|---|---|---|
| Q1 | `mini+` pooled made good 0.657 / 0.868 / 1.079 m/s at cruise 0.6 / 0.8 / 1.0 (±0.002), beating 0.754 in 0 / 36 / 36 of 36 | 0.657 / 0.868 / 1.079; 0 / 36 / 36 | **held** (exact reproduction of pace_study 0.1.0) |
| Q2 | `completed` = 720 | 720 | **held** |
| Q3 | `measured` vs `mini+`: faster in ≥ 9 of 12 groups, slower in none | faster 12, slower 0 (largest gain 2.16%, city blocks at 1.0) | **held** |
| Q4 | `measured` at 0.8: 36 of 36 beat, pooled median ≥ 0.868 | 36 of 36; 0.878 m/s | **held** |
| Q5 | `measured` at 0.7: pooled median 0.755-0.775 **and** `beats_on_every_course` false | 0.769 (in range), but `beats_on_every_course` **true** (city blocks 0.770, bayside 0.768, boulevard 0.770; 36 of 36 runs beat 0.754) | **missed** (the city blocks did not fall short) |
| Q6 | `measured-lag0.8` vs `measured`: slower in ≥ 6 of 12, faster in none | slower 11, faster 0 (largest cost 0.62%) | **held** |
| Q7 | `measured-noise10` vs `measured`: no completion lost, slower in ≥ 1 group, `largest_median_diff_share` ≤ +0.02 | lost 0, slower 12 of 12, largest **+0.0305** (city blocks at 0.6 and 0.8); every group cost 2.41-3.05% | **missed** (10° of compass noise costs more than 2% everywhere) |
| Q8 | `measured`, city blocks, cruise 1.0: `median_path_ratio` ≤ 1.035 | 1.028 | **held** |

## Decision rules

- **D1 (Q4 held).** `--marathon` stays at cruise 0.8. FINDINGS now reports the `measured` profile as the main case: 0.878 m/s made good at 0.8, about 25.5 h of driving for 80.5 km, leaving about 4.2 h for all stops (the 2 s profile's 0.868 m/s and 3.9 h become the pessimistic case).
- **D2 (path ratio 1.028 ≤ 1.044).** The FINDINGS warning that a corner-heavy leg at full speed could empty a 12 km charge is narrowed to the 2 s profile, as the rule says. Stated alongside it, because the rule did not look at them: with 10° of compass noise the city-blocks ratio at 1.0 was 1.039, and on the fresh-orientation baseline 1.043, both within 0.5% of the 1.044 limit. So full speed on a corner-heavy leg stays a range risk whenever the heading is noisy.
- **D3 (Q7 missed on the size of the cost).** FINDINGS names compass noise as a pace risk, and the next study tests smoothing the heading. With 10° of noise the pilot made good 0.855 m/s at cruise 0.8 (about 3.5 h left for stops, against 4.2 h) and 0.750 m/s at cruise 0.7, where only 1 of 36 runs beat the human pace (36 of 36 without the extra noise).
- **D4.** No change to the pilot's code or defaults from this study.
- **D5.** Not triggered: Q1 reproduced the earlier numbers exactly.

## What else the run shows (not pre-registered; for the next study only)

- The `measured` profile was slightly faster than even the fresh-orientation baseline at every cruise (0.878 against 0.873 m/s at 0.8), most likely because it turns at 48°/s instead of 30°/s and its commands land after 0.5 s instead of 0.8 s. It also needed fewer recoveries (0.47 per run at 0.8, against 0.64 fresh and 0.72 for the 2 s profile).
- Cruise 0.7 beats the human pace by about 2% on these courses with the measured telemetry, and loses it with 10° of noise. Cruise 0.8 keeps a 13% margin even with the noise. That supports 0.8 as the marathon preset rather than anything lower.
- Latency from 0.5 to 0.8 s cost 0.1-0.6%, small next to the noise.

## Limits

Simulated rovers on synthetic 1.3-1.6 km courses, not 11.5 km legs; no pedestrians, crossings, kerbs or slopes, so all speeds are upper bounds. The 48°/s, 0.5 s refresh and 0.5 s latency come from a few, mostly indoor, public Mini+ recordings (`studies/miniplus-b/`); the Mini+ GPS rate (a fix every 2 s) is assumed. The 10° noise is independent per reading; a real compass error that drifts or depends on heading may cost differently. Whether the Mini+'s orientation runs the way the pilot assumes is still not settled; it was simulated as assumed.

## Files

`report.md` (tables), `summary.json` (every field graded here), `runs.jsonl` (one line per mission), `PREDICTION.md` (the pre-registration).
