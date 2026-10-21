# frodo-blend-b-v2: grade sheet (graded 2026-10-21 ~23:20 UTC)

By MV2 of Munim, Inc.; written with AI agents. Graded against PREDICTION.md exactly as frozen
(`studies/frodo-blend-b/PREDICTION.md`; its run log records the v1 test failure and fix), from the
job's own output fields: `summary.json` (`conclusions`, `results.table`, `results.decision`,
`results.ci`) and the unit-test step's stderr.

Job: status ok, blade, 3,011 s, peak memory 0.3 GB. frodo_blend_b.py 0.1.0 importing frodo_blend.py
0.1.0 (main), frodo_compass 0.1.0 and frodo_compass_live 0.1.0 (tag v0.10.0) and frodo_motion.py
(v0.8.0). Data: 713 held-out rides sampled (30 per part, 23 in the last part; none of them in
frodo-blend-a-v1's sample), 167 analysed, 145 with pairs, 41.7 h of GPS, 0 ride errors, 461.2 MB
read. Skipped: 257 no straight stretch for the bias, 192 whole ride does not calibrate, 56 running
fit learns no bias, 38 too little data, 3 no compass.

## Gates

| Rule | Field | Value | Bar | Verdict |
|---|---|---|---|---|
| E1 tests | run-01 stderr | "Ran 65 tests ... OK" | all pass | **met** |
| Check | decision.check | ok=true; 13,460 pairs at 10 s | >= 2,000 pairs | **met** |
| C1 confirmation | decision.adopted_over_running_10s / adopted_ci_10s | blend2/running 0.944, CI 0.915-0.962 | <= 0.97 and CI top < 1.00 | **met** |
| C2 no cost later | decision.cost_30s | -0.018 (blend2 0.628 vs running 0.646 over course at 30 s) | <= 0.02 | **met** |
| S1 setting | decision.best / best_over_course_10s / default / setting | best hard3 0.833 = blend2 0.833 (no hold beats blend2 by >= 0.01) | keep blend2 unless beaten by >= 0.01 | **blend2: course_hold_s 2.0, fade True** |

`decision.confirmed` is true. Null check: every variant has a row at every horizon with the same n
per horizon (14,143 / 14,113 / 13,996 / 13,859 / 13,460 / 12,695 / 12,112 pairs at 1-30 s), and the
`decision` block has every key.

## Predictions

| # | Prediction | Result | Verdict |
|---|---|---|---|
| Q1 | C1 and C2 hold; blend2/running at 10 s in 0.90-0.97 | both hold; 0.944 | **met** |
| Q2 | running/course at 10 s in 0.864-0.985 | 0.883 | **met** |
| Q3 | best hold at 10 s is hard2, hard3 or blend2 | hard3 (0.833, tied with blend2 to three places; both 1.616 m) | **met** |
| Q4 | hard2 and blend2 within 0.01 at 10 s | hard2 0.844, blend2 0.833: 0.011 apart | **not met** (by 0.001; the fade helped at 2 s) |
| Q5 | S1 keeps blend2 | keeps blend2 | **met** |
| Q6 | at 1 s, running/course > 1.00 | 1.08 | **met** |

5 of 6 met; every gate passed.

## Median miss (m), the same anchors for every variant

| variant | 1 s | 2 s | 3 s | 5 s | 10 s | 20 s | 30 s |
|---|---|---|---|---|---|---|---|
| course | 0.31 | 0.49 | 0.69 | 1.05 | 1.94 | 3.70 | 5.56 |
| running | 0.33 | 0.53 | 0.71 | 1.02 | 1.71 | 2.80 | 3.59 |
| hard2 | 0.31 | 0.49 | 0.65 | 0.95 | 1.64 | 2.71 | 3.54 |
| hard3 | 0.31 | 0.49 | 0.68 | 0.96 | 1.62 | 2.68 | 3.49 |
| blend2 | 0.31 | 0.49 | 0.67 | 0.96 | 1.62 | 2.68 | 3.49 |

Full table (hard1-hard4, blend1-blend3) in `report.md`. 10 s, 95% CI (rides resampled, 200 reps):
blend2/running 0.915-0.962; blend2/course 0.804-0.868; running/course 0.842-0.941.

## What it means

- On 145 rides that the first study never saw, holding the fresh GPS course for 2 s after the rover
  was at a fix, then following the live-calibrated compass with the difference fading out over
  2 s more, missed the fix 10 s later by 1.62 m, against 1.71 m for the compass alone and 1.94 m
  for the course alone: 5.6% better than the compass (CI 3.8-8.5%), with no cost at 30 s (3.49 m
  against 3.59 m). The first study's 7% (CI 5-8%) shrank a little on new rides, as a best-of-three
  pick should, and held.
- Right after a fix the GPS course is better than the compass (8% at 1 s), and the compass wins from
  about 5 s on, on these rides as on the first sample.
- Holds of 2 to 4 s, hard or fading, land within 0.012 of each other at 10 s (0.833-0.845 of the
  course); 1 s is weaker (0.851-0.861). The exact form matters little; the pre-stated rule keeps
  blend2.
- By the rules written before the run, the pilot gets the hold: `DEAD_RECKON` becomes
  `{"use_course": False, "course_hold_s": 2.0, "fade": True}` in earth-rover-pilot 0.11.0.
- Transfer limit (stated before the run): Earth Rover Zero, raw 1 Hz magnetometer, 1 Hz GPS. On a
  Mini+ with its on-board `orientation`, 2 s is a starting value, not a measurement. The pilot's own
  implementation (dead_reckon.py 0.2.0) is checked by unit tests and simulated missions, not
  replayed on these rides.
