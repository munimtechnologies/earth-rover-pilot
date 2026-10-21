# frodo-blend-a-v1: grade sheet

By MV2 of Munim, Inc.; written with AI agents. Numbers derive from FrodoBots-2K (FrodoBots Lab,
CC BY-SA 4.0) and are shared under CC BY-SA 4.0. Graded on 2026-10-21 against
[PREDICTION.md](PREDICTION.md) exactly as it was frozen before the job ran, from the job's own
output fields in [summary.json](summary.json) (`conclusions`, `results.table`,
`results.decision`, `results.ci`) and its unittest log.

Run: `frodo_blend.py` 0.1.0 (`python frodo_blend.py --out-dir out --parts all --rides-per-part 30
--budget-min 120 --imu-max-mb 30`), with `frodo_compass.py` and `frodo_compass_live.py` from
v0.10.0 and `frodo_motion.py` from v0.8.0; 45 minutes, 0.35 GB of memory, 478.8 MB read.
720 rides sampled (30 per part, all 24 parts), 162 analysed, 146 with pairs, 39.9 hours of GPS,
no ride errors. Skipped: 277 with no straight stretch for the bias, 185 whose whole record does
not calibrate, 49 whose running fit learns no bias, 43 with too little data, 4 with no compass.

## Gates

| Rule | Value | Bar | Verdict |
|---|---|---|---|
| E1 tests | 43 tests, OK | all pass | **met** |
| E2 check | running / course at 10 s = 0.926 on 14,172 pairs | within 0.02 of live-v1's 0.926, at least 2,000 pairs | **met** (exact) |
| D1 default | best blend blend2, 0.862 of course at 10 s; at 30 s 0.022 better than running | at most 0.926 - 0.03 = 0.896, and no more than 0.02 worse at 30 s | **adopts blend2** |
| D2 switch | hard5 minus blend5 at 10 s = -0.047 | within 0.01: ship the hard switch | **"fading shift" as written; see below** |

**A flaw in D2, found when grading.** The rule asked only whether the hard switch at 5 s was
within 0.01 of the fading one; it assumed the fade could only help. The hard switch was in fact
*better*, by 0.047 at 10 s (0.869 against 0.916 of the course; 95% CIs 0.829-0.903 and
0.899-0.933). Read literally, D2 says "fading shift", but the data favour the hard switch at
5 s: the fade keeps part of the course for another 5 s, about 7.5 s of course in effect, which is
too long. The adopted 2 s hold was not run as a hard switch, so its form is left to the
held-out follow-up (frodo-blend-b); this sheet does not claim that the fade helps.

## Predictions

| # | Prediction | Result | Verdict |
|---|---|---|---|
| P1 | at 5 s the course beats the compass (running / course > 1.00) | 1.027 | **met** |
| P2 | the best hold is 5 s, and blend5 / course at 10 s is 0.84-0.91 | the best hold is 2 s; blend5 0.916 | **not met** |
| P3 | D1 adopts a blend | adopts blend2 | **met** |
| P4 | hard5 is worse than blend5 by more than 0.01 at 10 s | hard5 better by 0.047 | **not met** (opposite sign) |
| P5 | blend2 / course at 30 s within 0.02 of running's 0.687 | 0.665 (0.022 away) | **not met** (just outside, on the better side) |

Two of five predictions met; both gates passed.

## Median miss (m); every variant on the same anchors

| variant | 1 s | 2 s | 3 s | 5 s | 10 s | 20 s | 30 s |
|---|---|---|---|---|---|---|---|
| course | 0.31 | 0.48 | 0.66 | 1.01 | 1.85 | 3.50 | 5.23 |
| running | 0.33 | 0.52 | 0.71 | 1.03 | 1.72 | 2.78 | 3.60 |
| blend2 | 0.31 | 0.48 | 0.65 | 0.94 | 1.60 | 2.66 | 3.48 |
| blend5 | 0.31 | 0.48 | 0.66 | 1.01 | 1.70 | 2.66 | 3.42 |
| blend10 | 0.31 | 0.48 | 0.66 | 1.01 | 1.85 | 3.04 | 3.71 |
| hard5 | 0.31 | 0.48 | 0.66 | 1.00 | 1.61 | 2.64 | 3.44 |
| pairs | 14,832 | 14,802 | 14,711 | 14,593 | 14,172 | 13,471 | 12,885 |

At 10 s, 95% CIs with rides resampled (200 reps): blend2 / course 0.817-0.913, blend2 / running
0.917-0.953, hard5 / running 0.912-0.972, blend5 / running 0.940-1.049, blend10 / running
1.015-1.157, running / course 0.864-0.985.

## What it means, and what it doesn't

- Right after a fix, the fresh GPS course is the better heading: the live compass misses 6-8%
  more at 1-3 s. After that the compass wins. Holding the course for 2 s and then fading to the
  compass gave the smallest median miss at every horizon from 3 to 20 s; at 10 s, 1.60 m against
  1.72 m (compass alone) and 1.85 m (course alone), 7% better than the compass alone.
- Holding the course too long gives the gain back; held for 10 s, it is the course.
- The 2 s was chosen as the best of three holds on these same rides. The pilot's default stays as
  it is until a check on rides this sample did not contain agrees (frodo-blend-b).
- Earth Rover Zero, raw 1 Hz magnetometer, 1 Hz GPS. On a Mini+, which reports an on-board
  `orientation`, a 2 s hold would be a starting value, not a measurement.
