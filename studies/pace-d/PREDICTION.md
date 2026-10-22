# pace-d: compass errors that last, and `--smooth-heading` (pre-registered)

MV2 of Munim, Inc. Written with AI agents. CC BY 4.0.

This file is committed to main before any pace-d mission is flown. The job that flies them (`pace-d-v1`) waits until this file is on main, and records its SHA-256 and the time it fetched main (`fetched.json`). The study code (`pace_d.py`, `test_pace_d.py`) will be published with the grade, byte for byte as the job ran it; the job records its SHA-256 too. No clock time is written here: the commit history and the job log show the order.

## Why

`pace_c.py` (studies/pace-c/GRADE.md, 8 of 8 predictions held) drew the compass noise afresh for every orientation report. With 10° of that noise, rover_pilot 0.12.0's `--smooth-heading` (a complementary filter, `HeadingSmoother` with gain 0.3, 48°/s per unit of `angular`, 0.5 s latency) won back about 83% of what the noise cost. A real compass is also wrong in ways that last. A magnet near it that nobody corrected for (hard iron) bends every reading by an amount that depends on the heading. The error can also wander slowly. The pilot learns one compass bias from the GPS course on straight stretches (`HeadingEstimator`). Before `--smooth-heading` can be on by default, we need to know whether it still helps, or hurts, with errors like these, and how much of them the bias learner absorbs.

## Design

Every profile is pace_b.py's `measured` Mini+: orientation every 0.5 s, 48°/s per unit of `angular`, 0.5 s latency, GPS every 2 s (1.5 s behind the wheels), a constant −25° compass error the pilot has to learn, and 3° of noise per report.

| profile | compass error on top of `measured` |
|---|---|
| measured | none (pace_b.py's, flown again) |
| measured-noise10 | 10° of noise per report instead of 3° (pace_b.py's, flown again) |
| hardiron10 | 10° × sin(heading + phase), the phase drawn per seed |
| hardiron20 | 20° × sin(heading + phase) |
| drift10 | Ornstein-Uhlenbeck drift: SD 10°, time constant 120 s, stepped every 1 s |

The phase and the drift come from a random generator of their own, so every profile's GPS and noise draws are the same as `measured` for the same seed.

Variants: `shipped` (the pilot as it ships) and `cf0.3` (`--smooth-heading`, the pilot's own `HeadingSmoother` with `SMOOTH_HEADING`). Cruises 0.7 and 0.8. pace_study's three courses (boulevard, blocks, bayside; 1.3-1.6 km). Seeds 1-12. 5 × 2 × 2 × 3 × 12 = **720 missions**.

Comparisons are paired by seed in each cruise × course group (6 groups per profile and variant):
- **cost** of a profile = its median time difference against `measured`, flown by the same variant, as a share of `measured`'s median time;
- **cf0.3 against shipped** on the same profile, as in pace_c.py; "faster" / "slower" = a paired sign test with p < 0.05;
- **heading error** = the heading the pilot steers by minus where the simulated rover really points, sampled every tick while it drives forward; per mission its median |error|; per group the median over missions.

Outputs: `summary.json` (`profile_effect`, `profile_tallies`, `variant_effect`, `verdicts`, `largest`, `heading`, `check`), `runs.jsonl`, `report.md`.

## Predictions

Each is graded from those output fields.

- **Q1.** All 720 missions are completed.
- **Q2.** The check: every `measured` and `measured-noise10` mission (288, both variants) gives exactly the fields pace_c.py recorded for it in studies/pace-c/runs.jsonl (`check.identical` = 288, `missing` = 0).
- **Q3.** hardiron10 costs the shipped pilot less than 1% in every group: `profile_tallies` (hardiron10, shipped) `largest_median_diff_share` has |value| < 0.010.
- **Q4.** drift10 costs the shipped pilot less than 1% in every group (the same field, |value| < 0.010).
- **Q5.** A lasting 20° error costs less than 10° of fresh noise: in each of the 6 groups, the shipped pilot's hardiron20 share is below its measured-noise10 share.
- **Q6.** Blocks (right-angle corners, where the hard-iron error jumps at each turn) is where hard iron costs most: for (hardiron20, shipped), the blocks share is the largest of the three courses at both cruises.
- **Q7.** `--smooth-heading` does no harm with lasting errors: cf0.3 is slower than shipped (p < 0.05) in none of the 18 groups of hardiron10, hardiron20 and drift10, and its `largest_median_diff_share` against shipped has |value| ≤ 0.005 on each of those three profiles.
- **Q8.** The bias learner absorbs most of the drift: for (drift10, shipped), the group median |heading error| is above `measured`'s in all 6 groups, and below 5° in all 6 (a 10° SD drift left alone would have a median |error| of about 6.7°).

Why these: a heading error that lasts makes the pilot crab along the path rather than weave, and a crab costs little speed, while fresh noise makes it weave on every report (pace_b.py: 2.4-3.1% for 10°). The bias learner refits every 10-20 s on straight stretches. Hard iron changes the error only when the heading changes, so blocks' 90° corners are where it changes most. The filter only smooths the 3° of fresh noise and turns its estimate by the command, so it should behave as it did on `measured` in pace_c.py (0 of 6 groups slower).

## Decision rules

- **D1.** If Q7 holds, lasting errors are no reason to keep `--smooth-heading` off; it stays off by default only because no real Mini+'s compass noise has been measured, and README and FINDINGS say so. If cf0.3 is slower in any group, README and FINDINGS name the case, and turning it on by default also needs that kind of error measured on a real rover.
- **D2.** If any (hardiron20, shipped) group costs 2% or more, the next study tests a bias learned per heading sector (8 sectors of 45°). Otherwise no per-sector learner is built.
- **D3.** If Q4 fails, the next study tests the bias learner's gain (0.3 against 0.5) under drift.
- **D4.** If Q2 fails, nothing from this study is published as a finding until the difference is explained.
- **D5.** Whatever the outcome, the grade and the outputs are published in studies/pace-d/ with the code, and the results go into FINDINGS-frodobots-2k.md and the README in a documentation release.

Limits: simulated rovers only, so the speeds are upper bounds; the hard-iron model is the once-per-turn term alone (no twice-per-turn soft-iron term); the drift's size and time constant are guesses, not measurements.
