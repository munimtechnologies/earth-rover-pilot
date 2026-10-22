# Pre-registration: the marathon pace on a Mini+ that reports like the measured one (pace_b.py 0.1.0)

Written 2026-10-22 (about 10:40 UTC), before any pace_b result exists. By MV2 of Munim, Inc.; the code, predictions and this text were made with AI agents. Licence CC BY 4.0 (text), Apache-2.0 (code).

## Why

`pace_study.py` 0.1.0 (FINDINGS, "Can the pilot keep the human marathon pace on a Mini+?") flew the pilot on a Mini+ stand-in whose orientation was held 2 s between reports, turning at 30°/s per unit of `angular`, with commands landing 0.8 s after they were sent. On it, cruise 0.6 never reached the human Berkeley-Stanford pace (0.754 m/s), cruise 0.8 reached it in 36 of 36 runs (median 0.868 m/s), and cruise 1.0 widened the city-blocks path to 1.035 times the route, close to the 1.044 a 12 km charge allows.

Public Mini+ recordings later measured something else (`studies/miniplus-b/GRADE.md`): orientation changing about every 0.5 s, the state following the command about 0.5 s later, a median turn of 48°/s per unit of `angular`, and an orientation whose direction under turns was mixed on mostly indoor recordings. This study flies the same courses again with those numbers, so that the marathon-pace estimate rests on measured telemetry instead of a pessimistic guess.

## Design (fixed before the run)

- Courses: `pace_study.COURSES` unchanged (boulevard 1,552 m, blocks 1,400 m, bayside 1,262 m).
- Pilot: rover_pilot as on main (0.11.1 or 0.11.2; FINDINGS states the steering and GPS logic are unchanged since the 0.8.0 that pace_study flew, and Q1 checks it), `make_steering(False, cruise=...)` = `ROVER_STEERING`, through `pace_study.CoursePlanner`; dead reckoning off (`Pilot(dead_reckon=None)`), as in pace_study.
- Cruises: 0.6, 0.7, 0.8, 1.0. Seeds 1-12. 5 profiles x 4 cruises x 3 courses x 12 seeds = 720 missions.
- Profiles (all 1.111 m/s per unit of `linear`, GPS every 2 s, GPS 1.5 s late, 3° compass noise unless stated):
  - `fresh`: pace_study's baseline (orientation fresh on every 0.1 s poll, 30°/s, 0.8 s latency).
  - `mini+`: pace_study's Mini+ (orientation held 2 s, 30°/s, 0.8 s latency), flown again.
  - `measured`: orientation refreshed every 0.5 s, 48°/s, 0.5 s latency.
  - `measured-lag0.8`: `measured` with 0.8 s latency.
  - `measured-noise10`: `measured` with 10° compass noise.
- Comparisons: seed-by-seed per cruise x course group (`pace_study.compare`; a group is faster or slower when the sign test gives p < 0.05, which needs at least 10 of 12 seeds one way): `measured` against `mini+` (12 groups at the four cruises), `measured-lag0.8` and `measured-noise10` against `measured`.
- Grading reads `summary.json` fields: `overview` (pooled per profile x cruise), `groups` (per course), `pair_tallies`, `pair_effects`, `completed`.

## Predictions

- **Q1 (reproduction).** `mini+` pooled `median_made_good_mps` is 0.657, 0.868 and 1.079 at cruise 0.6, 0.8 and 1.0 (each within ±0.002), with `beat_human_pace` 0, 36 and 36 of 36.
- **Q2.** All 720 missions are completed (`completed` = 720).
- **Q3.** `measured` against `mini+`: faster in at least 9 of the 12 groups, slower in none.
- **Q4.** `measured` at cruise 0.8: `beat_human_pace` 36 of 36, pooled median made good at least 0.868 m/s.
- **Q5.** `measured` at cruise 0.7: pooled median made good between 0.755 and 0.775 m/s (just above the human pace), but `beats_on_every_course` is false (the city blocks fall short).
- **Q6.** `measured-lag0.8` against `measured`: slower in at least 6 of 12 groups, faster in none.
- **Q7.** `measured-noise10` against `measured`: no completion lost, slower in at least 1 group, and `largest_median_diff_share` no worse than +0.02 (a cost under 2% everywhere).
- **Q8.** `measured`, city blocks, cruise 1.0: `median_path_ratio` at most 1.035.

## Decision rules

- **D1.** If Q4 holds, `--marathon` stays at cruise 0.8 and the FINDINGS marathon-pace section reports the `measured` profile's numbers as the main case (the 2 s profile becomes the pessimistic one). If any `measured` run at 0.8 falls short of 0.754 m/s, FINDINGS says so and the preset is re-examined in a follow-up study; nothing changes from this one.
- **D2.** If the `measured` city-blocks path ratio at cruise 1.0 is at most 1.044, the FINDINGS warning that a corner-heavy leg at full speed could empty the battery is narrowed to the 2 s profile; otherwise it stays.
- **D3.** If `measured-noise10` loses a completion or costs more than 2% in any group, FINDINGS names compass noise as a pace risk and the next study tests smoothing the heading; otherwise FINDINGS notes the pace held under 10° of noise.
- **D4.** No change to the pilot's code or defaults from this study alone: it is a simulation, and the Mini+ GPS rate is not known from public data.
- **D5.** If Q1 fails, the cause is found and written up before any number from this run is used.

## Limits known in advance

Synthetic courses of 1.3-1.6 km, not 11.5 km legs; no pedestrians, crossings, kerbs or slopes, so speeds are upper bounds. The 48°/s and 0.5 s figures come from indoor teleop recordings of a few rovers. The Mini+ GPS rate (2 s here) is assumed. Orientation direction is simulated as the pilot assumes it (clockwise); `--calibrate` handles a rover that differs.
