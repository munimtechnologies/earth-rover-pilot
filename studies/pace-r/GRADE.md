# pace-r grade: is a truer GPS position worth anything once the rover really aims as far ahead?

MV2 of Munim, Inc. Graded with AI agents. CC BY 4.0.

Predictions: `studies/pace-r/PREDICTION.md` (SHA-256 907629a7…, on main before the job fetched it; see `fetched.json`). Job `pace-r-v1`: fetched main at 2026-10-25T05:28:04Z (rover_pilot.py 0.18.2, pace_q.py e65c9b56… as pace-q-v1 ran it with `studies/pace-q/GRADE.md` and `runs.jsonl`, pace_p.py c5234ba5… with `studies/pace-p/runs.jsonl`), `tests_exit` 0 (36 tests: test_pace_r and test_pace_q; `tests.txt`), then flew 864 missions in 1,924 s (peak memory 0.04 GB). Every number below is read from `summary.json` in this folder. The code is `pace_r.py` and `test_pace_r.py` as the job ran them (pace_r.py SHA-256 50067f5c…, test_pace_r.py c236b43d…).

**Result: 10 of 10 predictions held. Rule R2: `track-12` does not qualify, so a real rover keeps the shipped GPS filter (alpha 0.3) and the 16 m lookahead, and v0.18.4 (documentation only) states these results. pace-q's saving was about half a truer position and half the longer real aim. When the alpha-beta tracker aims as far ahead of the rover as the shipped pilot does (`track-12`), it is still 1.6-1.75% faster on city blocks with quiet GPS (22-23 of 24 seeds), and on these measures it holds the rover closer to the course. But it still turns about 1 m before each right-angle corner, as P10 predicted, and the rule requires at least 0 m.**

## Predictions

| | prediction | result | |
|---|---|---|---|
| P1 | check: compared 18, identical 18, missing 0; the same for `--check-q` if flown | `check` 18, 18, 0; `check_q` (flown: `pace_q_runs_on_main` true) 18, 18, 0 | held |
| P2 | all 864 missions completed | 864 of 864 | held |
| P3 | quiet90 `median_position_err_m`: `a0.3-16` and `a0.3-20` 5.8-7.0 m on every course; `track-12` and `track-16` below 3.0 m | `a0.3-16` 6.40 / 6.31 / 6.39; `a0.3-20` 6.40 / 6.30 / 6.39; `track-12` 2.25 / 2.38 / 2.18; `track-16` 2.25 / 2.37 / 2.17 | held |
| P4 | quiet90 and quietdrift90: `a0.3-20` faster than `a0.3-16` on blocks (p < 0.05), share between −0.030 and −0.005, and a lower blocks corner `median_past_m` | 24 of 24 seeds faster on both (−32 and −26 s; −0.0200 and −0.0160); past 1.07 against 1.99 m and 0.99 against 2.20 m | held |
| P5 | quiet90 and quietdrift90: `track-12`'s blocks corner `median_past_m` above `track-16`'s and below `a0.3-16`'s | −1.08 between −2.02 and 1.99; −0.83 between −1.83 and 2.20 | held |
| P6 | quiet90 and quietdrift90: `track-12` faster than `a0.3-16` on blocks (p < 0.05), share between −0.035 and −0.005 | 22 faster / 2 slower (−28 s, −0.0175) and 23 / 0 (−26 s, −0.0160); p < 0.0001 both | held |
| P7 | quiet90 and quietdrift90: `track-16` faster than `a0.3-20` on blocks (p < 0.05) | 23 / 1 (−27 s, −0.0175) and 23 / 1 (−28 s, −0.0178) | held |
| P8 | quiet90 and quietdrift90: `track-12` `groups_slower` against `a0.3-16` is 0 | 0 and 0 | held |
| P9 | outage90: `track-12` against `a0.3-16` `groups_lost` 0 and share at most +0.01 on every course | lost 0; −0.0040 / −0.0137 / +0.0011 | held |
| P10 | by R2, `track-12` does not qualify | does not qualify (below) | held |

(Courses are bayside / blocks / boulevard. Every mission was flown by `pace_q.py` as `pace_p.py`'s `keep16`, v0.18.2's real-rover pilot; only the GPS filter and the path follower's lookahead changed. `a0.3-16` is the pilot as it ships.)

## Decision

- **R1 does not stop anything:** both checks found no difference (18 of 18 identical against pace-p's record, 18 of 18 against pace-q's).
- **R2: `track-12` does not qualify, so a real rover keeps alpha 0.3 and 16 m.** It qualifies if, against `a0.3-16` on quiet90 and on quietdrift90, it has `groups_slower` 0 and `groups_lost` 0, its blocks corner `p95_m` is at most 0.25 m above `a0.3-16`'s, its blocks corner `median_past_m` is at least 0 m, its `p95_offset_m` is at most 0.5 m above `a0.3-16`'s on every course, and `groups_faster` ≥ 1 on one profile; and on outage90 `groups_lost` 0 and `median_time_diff_share` at most +0.01 on every course.
  - Met: slower 0 and 0; lost 0 and 0; faster 3 and 2; blocks corner `p95_m` 2.27 against 2.71 m and 3.67 against 4.29 m (below the shipped pilot's); `p95_offset_m` 1.35 / 2.33 / 0.96 against 2.32 / 3.15 / 1.04 m and 5.12 / 4.88 / 4.78 against 6.26 / 5.44 / 6.26 m (below on every course); outage90 lost 0, shares −0.40 / −1.37 / +0.11%.
  - **Not met:** blocks corner `median_past_m` −1.08 m (quiet90) and −0.83 m (quietdrift90). It turned before the corners.
  - So v0.18.4 changes no code: the README, FINDINGS and a note above `PATH_LOOKAHEAD_M` state these results.
- R3: this grade, the outputs and the code are published here.

## What each change is worth on city blocks (paired by seed, same profile)

| blocks: median paired time difference | outage90 (1.5 m noise) | quiet90 (0.22 m) | quietdrift90 (0.22 m, drifting compass) |
|---|---|---|---|
| the aim alone: `a0.3-20` against `a0.3-16` | −26 s (−1.62%) | −32 s (−2.00%) | −26 s (−1.60%) |
| the aim alone, with the tracker: `track-16` against `track-12` | −29 s (−1.87%) | −29 s (−1.88%) | −28 s (−1.78%) |
| a truer position at the shipped real aim: `track-12` against `a0.3-16` | −22 s (−1.37%) | −28 s (−1.75%) | −26 s (−1.60%) |
| a truer position at the longer real aim: `track-16` against `a0.3-20` | −23 s (−1.49%) | −27 s (−1.75%) | −28 s (−1.78%) |
| both (pace-q's `track`): `track-16` against `a0.3-16` | −57 s (−3.56%) | −63 s (−3.93%) | −62 s (−3.82%) |

Every row was faster by the sign test on blocks on every profile (22-24 of 24 seeds). The two halves add up to about the whole: on quiet90 2.00 + 1.75 = 3.75% against 3.93% for both together.

| other courses: bayside / boulevard | outage90 | quiet90 | quietdrift90 |
|---|---|---|---|
| `track-12` against `a0.3-16` | −6 / +2 s (−0.40 / +0.11%); boulevard slower (13 of 24 seeds) | −9 / −2 s (−0.60 / −0.11%) | −8 / 0 s (−0.53 / 0%) |
| `a0.3-20` against `a0.3-16` | −4 / 0 s (−0.27 / 0%) | −4 / 0 s (−0.27 / 0%) | −2 / 0 s (−0.13 / 0%) |
| `track-16` against `a0.3-20` | −4 / +1 s (−0.27 / +0.06%); boulevard slower (12 of 24) | −6 / 0 s (−0.40 / 0%) | −10 / 0 s (−0.67 / 0%) |

| blocks, near path corners: median m past / p95 m | outage90 | quiet90 | quietdrift90 |
|---|---|---|---|
| `a0.3-16` (as shipped) | 2.12 / 2.95 | 1.99 / 2.71 | 2.20 / 4.29 |
| `a0.3-20` | 1.15 / 3.06 | 1.07 / 3.26 | 0.99 / 4.69 |
| `track-12` | −0.99 / 3.08 | −1.08 / 2.27 | −0.83 / 3.67 |
| `track-16` | −1.94 / 3.88 | −2.02 / 3.65 | −1.83 / 4.37 |

| 95th-percentile m from the course while driving forward, bayside / blocks / boulevard | outage90 | quiet90 | quietdrift90 |
|---|---|---|---|
| `a0.3-16` | 3.99 / 3.38 / 3.86 | 2.32 / 3.15 / 1.04 | 6.26 / 5.44 / 6.26 |
| `a0.3-20` | 4.00 / 3.85 / 3.79 | 2.59 / 3.55 / 1.23 | 6.28 / 6.26 / 6.96 |
| `track-12` | 3.63 / 3.58 / 3.52 | 1.35 / 2.33 / 0.96 | 5.12 / 4.88 / 4.78 |
| `track-16` | 3.38 / 3.75 / 4.18 | 1.81 / 3.30 / 1.18 | 5.56 / 5.54 / 5.63 |

Pooled made good, outage90 / quiet90 / quietdrift90: `a0.3-16` 0.873 / 0.873 / 0.857; `track-12` 0.879 / 0.880 / 0.873; `a0.3-20` 0.883 / 0.883 / 0.874; `track-16` 0.883 / 0.885 / 0.877 m/s. Every mission was completed, no checkpoint report was refused, and all 864 beat the human marathon pace (0.754 m/s).

## Findings

1. **pace-q's saving was about half a truer position and half the longer real aim (P4, P6, P7).** On city blocks, aiming 4 m further ahead from the same lagging position (`a0.3-20`) saved 1.6-2.0%. Flying the tracker at the shipped pilot's real aim (`track-12`) saved 1.4-1.75%, and at the longer aim (`track-16` against `a0.3-20`) 1.5-1.8%. The two together (pace-q's `track`) saved 3.6-3.9%, close to the sum. On bayside the truer position saved 0.3-0.7% at either aim. On boulevard, the straightest course, nothing saved more than 2 s, and with the simulator's 1.5 m noise the tracker was 1-2 s slower there (13 of 24 seeds at 12 m, 12 of 24 at 16 m against `a0.3-20`).
2. **A truer position turns early even at the shipped pilot's real aim (P5, P10).** The shipped pilot goes a median 2.0-2.2 m past each right-angle corner because its position lags behind the turn. Aiming 4 m further ahead from the lagging position cut that to 1.0-1.2 m past. The tracker at a matched real aim turned 0.8-1.1 m before the corner, as pure pursuit from a true position does. A 12 m lookahead turns later than 16 m, so it sits between the two. The arithmetic of matching the aims (lookahead minus measured lag) held: the lookahead did not change how far behind the filter was (P3).
3. **By these measures `track-12` held the rover closer to the course than the shipped pilot, and the rule still keeps the shipped pilot.** With quiet GPS its blocks corner 95th percentile was 0.44-0.62 m lower and its 95th-percentile distance from the course was lower on every course (by 0.08-1.48 m). The median of each mission's largest distance from the course fell from 7.3-7.4 m to 5.3 m on quiet90. It failed only the condition that it go at least 0 m past each corner. That condition was written so that a truer position could not save time by cutting corners. It has now been the only failing condition for two candidates: pace-q's `a0.6`, at −0.22 m, and `track-12`, at −0.83 to −1.08 m. The rule binds as written. The simulator has no sidewalk width or corner geometry, so it cannot say whether turning 1 m early leaves a real sidewalk more often than going 2 m past the corner does. Any new rule must be argued and pre-registered for a new study on fresh seeds. It cannot be applied to this one.
4. **One mission no prediction or rule reads.** On outage90 boulevard, seed 313, something in the mission threw every filter's position estimate far off. The shipped filter's largest position error was 63.7 m, yet its rover stayed within 7.7 m of the course; with `track-16` the error and the distance both stayed under 8.2 m. With `track-12` the pilot's estimate was up to 32.3 m off, and the rover followed it, up to 32.7 m from the course (95th percentile 23.4 m). It still completed the mission at 0.877 m/s. No other tracker mission with a steady compass error (outage90 and quiet90: 431 more across pace-q and pace-r) went further than 11.6 m from the course. With a drifting compass (quietdrift90) every variant, the shipped pilot included, had missions 21-28 m off, so that profile cannot tell the filters apart here. The cause was not diagnosed. Before a tracker is proposed for a real rover again, this mission should be flown with a trace and explained.

## Limits

Simulated rovers only (pace_l.py's measured Mini+ profile), so speeds are upper bounds on what a sidewalk allows. The real-aim matching uses pace-q's median position errors; the lag varies along a mission (larger after an outage and in turns), and `track-12`'s matched aim (about 9.8 m) is about 0.2 m longer than the shipped pilot's (about 9.6 m). quiet90's 0.22 m is drawn as independent noise per fix. The slow wander measured on standing Earth Rovers (1.5 m in 60 s), steady offsets and multipath jumps are not modelled; a tracker that follows the fixes more closely may also follow their wander. Nothing here predicts a fix forward over its 1.5 s delay. Three idealised courses with corners of only 90° or under 25° and no sidewalk width, so "distance from the course" stands in for "off the sidewalk". The lookaheads (12 and 20 m) were fixed before any mission was flown. None of this has been measured on a live Mini+.
