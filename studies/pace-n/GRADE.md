# pace-n grade: how far ahead should the rover aim along its path?

MV2 of Munim, Inc. Graded with AI agents. CC BY 4.0.

Predictions: `studies/pace-n/PREDICTION.md` (SHA-256 6d1378a9…, on main before the job fetched it; see `fetched.json`). Job `pace-n-v1`: fetched main at 2026-10-24T07:52:42Z (rover_pilot.py 0.17.0, pace_m.py 7167780f… as pace-m-v1 ran it, with `studies/pace-m/GRADE.md` and `runs.jsonl`), `tests_exit` 0 (47 tests: test_pace_n, test_pace_m and test_learner_default), then flew 576 missions in 1,184 s (peak memory 0.07 GB). Every number below is read from `summary.json` in this folder. The code is `pace_n.py` and `test_pace_n.py` as the job ran them (pace_n.py SHA-256 cf3f300e…, test_pace_n.py 3356dc26…).

**Result: 8 of 9 predictions held (N5 missed). Rule R2 applies: only `look16` (a 16 m lookahead) qualifies, so v0.18.0 gives a real rover's path follower a 16 m lookahead. `look12` missed R2 by 0.03 m on one course (drift90 bayside 95th-percentile distance from the course 0.53 m above 8 m's, where the rule allows 0.5 m).**

## Predictions

| | prediction | result | |
|---|---|---|---|
| N1 | check: compared 18, identical 18, missing 0 | 18, 18, 0 | held |
| N2 | all 576 missions completed | 576 of 576 | held |
| N3 | `look8`'s blocks `median_past_m` above +2 m on both profiles | 4.27 (outage90), 4.25 (drift90) | held |
| N4 | blocks `median_past_m` ordered look4 > look8 > look12 > look16 on both profiles | 5.67 > 4.27 > 2.96 > 1.73 (outage90); 5.46 > 4.25 > 3.16 > 2.20 (drift90) | held |
| N5 | blocks corner `p95_m`: `look12` and `look16` each ≥ 2 m below `look8`, `look4` above, both profiles | look8 4.86 / 5.68 (outage90 / drift90); look12 3.90 / 5.07 (0.96 and 0.61 m below); look16 3.34 / 5.18 (1.52 and 0.50 m below); look4 6.19 / 7.09 (above) | **missed** (lower, but not by 2 m) |
| N6 | `look4` against `look8`: `groups_slower` ≥ 2 on each profile | 3 and 3 | held |
| N7 | `look12` and `look16` against `look8`: slower 0, lost 0 on both profiles, faster on blocks on both | slower 0, lost 0 in all 4; blocks faster in all 4 (p ≤ 0.0001) | held |
| N8 | drift90: `look16`'s `median_offset_m` above `look8`'s on boulevard and bayside, by more than on outage90 | bayside 1.83 vs 1.42 (+0.41; outage90 −0.16), boulevard 2.54 vs 2.35 (+0.19; outage90 −0.13) | held |
| N9 | `median_mean_abs_angular` ordered look4 > look8 > look12 > look16 in 6 of 6 profile × course groups | 6 of 6 (e.g. outage90 blocks 0.0934 > 0.0593 > 0.0473 > 0.0432) | held |

(Courses are bayside / blocks / boulevard. Every mission was flown as pace_m.py's `long20`, v0.17.0's real-rover pilot; only the path follower's lookahead changed.)

## Decision

- **R1 does not stop anything:** the check found no difference (18 of 18 identical).
- **R2 applies.** A variant qualifies if, against `look8` on both profiles, it has `groups_slower` 0 and `groups_lost` 0, its blocks corner `p95_m` is not above `look8`'s, its `p95_offset_m` is at most 0.5 m above `look8`'s on every course, and it is faster somewhere or ≥ 1 m lower in corner `p95_m` on both profiles:
  - `look4`: slower on 3 of 3 courses on both profiles. Does not qualify.
  - `look12`: slower 0, lost 0, faster 3 + 3, corner p95 3.90 ≤ 4.86 and 5.07 ≤ 5.68; but `p95_offset_m` on drift90 bayside is 7.87 against 7.34 (+0.53 m). **Does not qualify.** (Its other five courses: +0.43, −0.80, −0.59, −0.18, −2.59 m.)
  - `look16`: slower 0, lost 0, faster 3 + 3; corner p95 3.34 ≤ 4.86 and 5.18 ≤ 5.68; `p95_offset_m` against `look8`: outage90 −0.33 / −2.10 / −0.60 m, drift90 +0.48 / −0.66 / −1.73 m (bayside / blocks / boulevard), all within +0.5 m. **Qualifies.**
  - Only `look16` qualifies, so no tie-break is needed. v0.18.0 gives a real rover's path follower a 16 m lookahead, at the command-line layer only (the command line sets the lookahead the Pilot gives its PathFollower). The simulator's defaults and the defaults of the PathFollower and Pilot classes stay 8 m.
- R3 does not apply. R4: this grade, the outputs and the code are published here.

## Each lookahead against 8 m (paired by seed, same profile)

Median paired difference a mission (share of the time) and seeds faster/slower of 24; every course below had p < 0.05:

| variant | outage90 (steady compass) | drift90 (drifting compass) |
|---|---|---|
| look4 | slower on all 3: +54 / +110 / +55 s (+3.7 / +6.7 / +3.1%) | slower on all 3: +54 / +114 / +64 s (+3.7 / +6.9 / +3.6%) |
| look12 | faster on all 3: −13 / −32 / −2 s (−0.89 / −1.96 / −0.11%) | faster on all 3: −8 / −26 / −2 s (−0.55 / −1.58 / −0.11%) |
| look16 | faster on all 3: −18 / −59 / −6 s (−1.23 / −3.61 / −0.34%); 23/0, 23/1, 18/1 | faster on all 3: −10 / −64 / −5 s (−0.68 / −3.88 / −0.28%); 21/1, 23/1, 16/5 |

Pooled made good (m/s), outage90 / drift90: look8 0.863 / 0.859; look4 0.815 / 0.805; look12 0.873 / 0.867; look16 0.879 / 0.869. Missions beating the human marathon pace (0.754 m/s), of 72: look8 71 / 69; look4 69 / 66; look12 72 / 70; look16 72 / 70. Every variant completed every mission, and no checkpoint report was refused.

## Findings

1. **The shipped 8 m lookahead runs past corners, and aiming further ahead turns earlier, in order.** On blocks (9 right-angle path corners) the rover with 8 m got a median 4.3 m beyond each corner along the course into it, on both profiles (N3). With 4, 12 and 16 m that was 5.5-5.7, 3.0-3.2 and 1.7-2.2 m (N4). This is what a position that lags the rover along its track predicts, but it is not a test of the lag: the turn itself also takes seconds (the steering reaches full turn rate only at a 60° error).
2. **Aiming further ahead was faster on every course, mostly at corners.** 16 m saved 3.6-3.9% a mission on blocks (59-64 s), 0.7-1.2% on bayside and about 0.3% on boulevard, slower on no course of either profile (N7). 4 m was 3.1-6.9% slower everywhere (N6), and its heading error was 2.4-5.4 times larger (median 4.1-17.8° against 1.7-7.4° at 8 m): at 4 m the rover aims at a point barely ahead of where it really is, and weaves.
3. **Near corners the gain in distance was real but smaller than predicted (N5 missed).** The rover's 95th-percentile distance from the course within 20 m of a path corner was already only 4.9-5.7 m with 8 m, and 16 m brought it to 3.3-5.2 m (0.5-1.5 m lower, not 2 m). So the blocks course's large whole-mission 95th percentile (10.7-11.1 m with 8 m, 9.0-10.0 m with 16 m) mostly comes from somewhere other than the path corners. A likely place, not measured here: the four corners that are checkpoints, which the corner record leaves out by design (the rover reports a checkpoint from 10 m and turns for the next one early), and the 90 s GPS outages.
4. **The worst case improved most.** The median of each mission's largest distance from the course on blocks fell from 17.8 m to 12.8 m (outage90) and from 15.9 m to 13.7 m (drift90), and the largest of all from 33.1 to 25.2 m and 46.0 to 34.4 m.
5. **With a drifting compass, a longer lookahead holds the rover a little further to one side** (N8): on drift90 16 m's median distance from the course was 0.41 m higher on bayside and 0.19 m higher on boulevard, while on a steady compass it was 0.13-0.16 m lower. That is the lookahead × tan(heading error) term (16 × tan 6.5° ≈ 1.8 m against 0.9 m at 8 m). It is the cost that kept `look12` out of R2 on one course and that `look16` stayed just inside (+0.48 m).
6. **The further ahead, the gentler the steering** (N9): mean |angular| fell in order on all 6 profile × course groups, by 25-33% from 8 m to 16 m.

## Limits

Simulated rovers only (pace_l.py's measured Mini+ profile), so speeds are upper bounds on what a sidewalk allows. The courses are three idealised shapes; a real OpenStreetMap path has corners of every angle and curves between buildings, and sidewalk width is not modelled, so "distance from the course" stands in for "off the sidewalk". Cutting inside a corner on a real sidewalk can mean leaving it. The lookahead matters only with a planner (`--osm` or `--fetch-osm`); without one the pilot heads straight for each checkpoint. 16 m was the longest lookahead tested, so a longer one may do better still or start to cost on curves; this study cannot say. The lag explanation in finding 1 and the place named in finding 3 are likely, not tested. None of this has been measured on a live Mini+.
