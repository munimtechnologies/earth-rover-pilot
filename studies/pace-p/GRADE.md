# pace-p grade: does a longer lookahead save time on straights, or only at corners?

MV2 of Munim, Inc. Graded with AI agents. CC BY 4.0.

Predictions: `studies/pace-p/PREDICTION.md` (SHA-256 7e7d4c2c…, on main before the job fetched it; see `fetched.json`). Job `pace-p-v1`: fetched main at 2026-10-24T21:25:38Z (rover_pilot.py 0.18.1, pace_o.py 806b4bbc… as pace-o-v1 ran it, with `studies/pace-o/GRADE.md` and `runs.jsonl`), `tests_exit` 0 (59 tests: test_pace_p, test_pace_o and test_lookahead_default; `tests.txt`), then flew 720 missions in 1,156 s (peak memory 0.06 GB). Every number below is read from `summary.json` in this folder. The code is `pace_p.py` and `test_pace_p.py` as the job ran them (pace_p.py SHA-256 c5234ba5…, test_pace_p.py be88bc29…).

**Result: 10 of 10 predictions held. Rule R2: none of `bend24`, `calm24` and `calm32` qualifies, so a real rover keeps the plain 16 m lookahead and v0.18.2 (documentation only) states these results. On city blocks a follower that aims 24 m ahead but 16 m within 24 m of a right-angle turn went round the corners like 16 m and kept none of plain 24 m's 3.2-3.8% time saving (a median paired difference of 0 s against 16 m). Where the path was straight, aiming further saved nothing measurable and held the rover further from the course.**

## Predictions

| | prediction | result | |
|---|---|---|---|
| P1 | check: compared 36, identical 36, missing 0 | 36, 36, 0 | held |
| P2 | all 720 missions completed | 720 of 720 | held |
| P3 | `bend24` `median_long_share` ≥ 0.95 on bayside and boulevard, 0.5-0.9 on blocks, both profiles | bayside 1.0 and 1.0, boulevard 1.0 and 1.0, blocks 0.83 and 0.83 (outage90, drift90) | held |
| P4 | `calm24` bayside `median_long_share` 0.3-0.8, both profiles | 0.609 and 0.599 | held |
| P5 | `keep24` against `keep16`: faster on blocks (p < 0.05) and `groups_slower` 0, both profiles; blocks corner `median_past_m` `keep24` < 1.0 m, `keep16` > 1.5 m | blocks 22 of 24 seeds faster on both (p < 0.0001), slower 0 and 0; `keep24` 0.14 and 0.21 m, `keep16` 2.08 and 2.05 m | held |
| P6 | blocks: `bend24`'s `median_time_diff_share` above half of `keep24`'s, both profiles | 0.0 against −0.0382 (half −0.0191) and 0.0 against −0.0316 (half −0.0158) | held |
| P7 | blocks: `bend24` corner `median_past_m` ≥ 1.5 m and corner `p95_m` within 0.5 m of `keep16`'s, both profiles | 2.08 and 1.90 m; 2.97 against 2.94 (+0.03) and 4.39 against 4.28 (+0.11) | held |
| P8 | bayside: `bend24`'s `median_time_diff_share` within 0.002 of `keep24`'s, both profiles | −0.0070 against −0.0070 (0.0000) and −0.0076 against −0.0083 (0.0007) | held |
| P9 | drift90 boulevard: `bend24`'s `median_offset_m` above `keep16`'s | 2.09 against 1.60 m | held |
| P10 | by R2, none of `bend24`, `calm24`, `calm32` qualifies | none qualifies (below) | held |

(Courses are bayside / blocks / boulevard. Every mission was flown as pace_m.py's `long20` on v0.18.1's real-rover pilot with pace_o.py's `keep` planner; only the path follower changed. `keep16` is v0.18.1's real-rover pilot.)

## Decision

- **R1 does not stop anything:** the check found no difference (36 of 36 identical).
- **R2: none qualifies, so a real rover keeps the plain 16 m.** A variant qualifies if, against `keep16` on both profiles, it has `groups_slower` 0 and `groups_lost` 0, its blocks corner `p95_m` is at most 0.25 m above `keep16`'s, its blocks corner `median_past_m` is at least 1.0 m, its `p95_offset_m` is at most 0.5 m above `keep16`'s on every course, and `groups_faster` ≥ 1 on some profile:
  - `bend24`: slower 0, lost 0, faster 3 + 1; corners +0.03 / +0.11 m, past 2.08 / 1.90 m; but `p95_offset_m` above `keep16`'s by outage90 +0.71 / +0.32 / +0.16 m and drift90 +1.31 / +0.96 / +1.09 m: over 0.5 m on four of six courses. **Does not qualify.**
  - `calm24`: slower 0, lost 0, faster 2 + 0; corners as `bend24`; `p95_offset_m` +0.79 / +0.32 / +0.43 m and +0.56 / +0.96 / +1.49 m: over 0.5 m on four of six. **Does not qualify.**
  - `calm32`: slower 0, lost 0, faster 3 + 0; drift90 blocks corner `p95_m` 4.84 against 4.28 (+0.56 m, over 0.25); `p95_offset_m` +1.06 / +0.66 / +0.56 m and +1.29 / +1.86 / +1.90 m: over 0.5 m on all six. **Does not qualify.**
  - So v0.18.2 changes no code: the README, FINDINGS and a note by `PATH_LOOKAHEAD_M` state these results. `keep24` was a reference only (it failed pace-o's R3).
- R3: this grade, the outputs and the code are published here.

## Each follower against plain 16 m (paired by seed, same profile)

| variant | outage90 (steady compass) | drift90 (drifting compass) |
|---|---|---|
| keep24 | faster on all 3: −10 / −60 / 0 s (−0.70 / −3.82 / 0%) | faster on 2: −12 / −50 s (−0.83 / −3.16%); boulevard 0 s (p 1.0) |
| bend24 | faster on all 3 by the sign test: −10 / 0 / 0 s (−0.70 / 0 / 0%) | faster on bayside: −11 s (−0.76%); blocks 0 s (4 seeds faster, 4 slower), boulevard 0 s |
| calm24 | faster on bayside and blocks by the sign test, median 0 / 0 / 0 s | none faster or slower; 0 / 0 / 0 s |
| calm32 | faster on all 3 by the sign test: −1 / 0 / 0 s (−0.07 / 0 / 0%) | none faster or slower; 0 / 0 / 0 s |

| 95th-percentile distance from the course, whole mission (m) | outage90 | drift90 |
|---|---|---|
| keep16 | 2.50 / 3.33 / 2.61 | 5.46 / 5.13 / 5.49 |
| keep24 | 3.21 / 4.12 / 2.77 | 6.72 / 6.56 / 6.58 |
| bend24 | 3.21 / 3.65 / 2.77 | 6.77 / 6.09 / 6.58 |
| calm24 | 3.29 / 3.65 / 3.04 | 6.02 / 6.09 / 6.98 |
| calm32 | 3.56 / 3.99 / 3.17 | 6.75 / 6.99 / 7.39 |

(bayside / blocks / boulevard.) Pooled made good, outage90 / drift90: keep16 0.884 / 0.880; keep24 0.888 / 0.884; bend24 0.887 / 0.883; calm24 0.884 / 0.881; calm32 0.885 / 0.879 m/s. Every mission was completed and no checkpoint report was refused; 70-72 of each 72 missions beat the human marathon pace (0.754 m/s).

## Findings

1. **On city blocks the time a longer lookahead saves comes from the corners (P5, P6, P7).** Plain 24 m was again 3.2-3.8% faster than 16 m on blocks (50-60 s a mission, 22 of 24 seeds), and again by turning before each corner (a median 0.14-0.21 m past it, against 2.05-2.08 m with 16 m). `bend24` aims 24 m ahead on blocks' straights (83% of its targets) and 16 m within 24 m of a right angle; it went round the corners like 16 m (95th percentile near corners within 0.11 m of it) and its median paired time difference against 16 m was 0 s on both profiles. So on this course none of 24 m's saving came from aiming further down the straights. This answers pace-o's open question (its finding 4 said "likely, not tested"): the saving was the corner cutting.
2. **Gentle curves behave the same way (P4, P8).** On bayside's sine, `bend24` aimed long everywhere and kept all of 24 m's 0.7-0.8% saving (−10 and −11 s against −10 and −12 s), but so did its distance from the course (95th percentile 3.21 and 6.77 m, against 2.50 and 5.46 m with 16 m). `calm24`, which aimed 16 m wherever the path ahead turned by 10° or more (about 40% of its targets there), saved a median 0 s on bayside. A likely reading, not tested separately: on bayside too the time came from smoothing the curves, not from the stretches between them. On boulevard, the straightest course, no follower saved a median second.
3. **On straights, aiming further only holds the rover further off (P9, R2).** With a drifting compass `bend24` held the rover 0.49 m further from the course at the median on boulevard (2.09 against 1.60 m) and 1.1 m further at the 95th percentile, where it aimed 24 m for every target and saved no time. With a steady compass the excess was smaller (boulevard 95th percentile +0.16 m, bayside +0.71 m). On blocks' straights (outside the corners) its 95th percentile was 4.08 / 6.39 m against 3.50 / 5.95 m with 16 m. This matches the speed rule (cruise × cos of the heading error): on a straight a 16 m lookahead already keeps the heading error small, so a longer one has little time left to win, while a heading error turns into a larger sideways offset before it is corrected.
4. **The decision rule's "faster" is a sign test, which counts small wins.** With a steady compass `bend24`, `calm24` and `calm32` were "faster" on some courses with a median difference of 0 s (for example `bend24` on blocks: 11 seeds faster, 1 slower, 12 tied). These are a few seconds in a minority of missions. None of the three passed R2's distance limits, so this did not decide anything here.
5. **What did not change.** The pilot's own position error (median 6.4-6.6 m from where it really was), heading error and plans were the same with every follower; `bend24` and `calm24` flew blocks identically, as they should (its turns are 0° or 90°).

## Limits

Simulated rovers only (pace_l.py's measured Mini+ profile), so speeds are upper bounds on what a sidewalk allows. Three idealised courses, with corners of only 90° or under 25°; real streets have corners of every angle. The 45° and 10° thresholds and the 24 m and 32 m long lookaheads were fixed before any mission was flown; other values would split the path differently. Sidewalk width is not modelled, so "distance from the course" stands in for "off the sidewalk". `keep` is closer to an OpenStreetMap route at a checkpoint corner but is not one. Finding 2's reading is likely, not tested. None of this has been measured on a live Mini+.
