# pace-q grade: does the GPS filter's lag cost time once the GPS is as quiet as a real one?

MV2 of Munim, Inc. Graded with AI agents. CC BY 4.0.

Predictions: `studies/pace-q/PREDICTION.md` (SHA-256 d6e6bbdb…, on main before the job fetched it; see `fetched.json`). Job `pace-q-v1`: fetched main at 2026-10-25T01:02:38Z (rover_pilot.py 0.18.2, pace_p.py c5234ba5… as pace-p-v1 ran it, with `studies/pace-p/GRADE.md` and `runs.jsonl`), `tests_exit` 0 (53 tests: test_pace_q, test_pace_p and test_lookahead_default; `tests.txt`), then flew 864 missions in 1,678 s (peak memory 0.04 GB). Every number below is read from `summary.json` in this folder. The code is `pace_q.py` and `test_pace_q.py` as the job ran them (pace_q.py SHA-256 e65c9b56…, test_pace_q.py 323d8cf1…).

**Result: 7 of 10 predictions held. Rule R2: none of `a0.6`, `raw` and `track` qualifies, so a real rover keeps the shipped GPS filter (alpha 0.3) and v0.18.3 (documentation only) states these results. The arithmetic held: the shipped average leaves the pilot a median 6.3-6.4 m behind the rover, and filters without its lag cut that to 2.1-3.4 m. With GPS as quiet as recorded Earth Rovers', every such filter was faster on every course where the result was significant (3.1-4.4% on city blocks) and slower on none. But every one turned before the corners, which R2 does not allow. Because the 16 m lookahead is measured from where the pilot thinks it is, a truer position also means aiming further ahead in reality, so this study cannot separate the two. pace-r is designed to.**

## Predictions

| | prediction | result | |
|---|---|---|---|
| P1 | check: compared 18, identical 18, missing 0 | 18, 18, 0 | held |
| P2 | all 864 missions completed | 864 of 864 | held |
| P3 | quiet90 `median_position_err_m`: `a0.3` 5.8-7.0 m on every course; `raw` and `track` below 3.0 m; `a0.6` strictly between | `a0.3` 6.39 / 6.31 / 6.41; `raw` 2.05 / 2.11 / 2.13; `track` 2.23 / 2.34 / 2.17; `a0.6` 3.32 / 3.33 / 3.37 | held |
| P4 | quiet90 and quietdrift90: `raw` faster than `a0.3` on blocks (p < 0.05), with a lower blocks corner `median_past_m` | 24 of 24 seeds faster on both (−69 and −67 s, −4.37% and −4.21%); past −0.84 against 2.07 m and −1.07 against 2.10 m | held |
| P5 | quiet90 and quietdrift90: `raw` `groups_slower` 0 | 0 and 0 | held |
| P6 | quiet90 and quietdrift90: `raw` blocks corner `p95_m` at most 0.25 m above `a0.3`'s | quiet90 3.60 against 3.17 (+0.43); quietdrift90 4.53 against 4.58 (−0.05) | **missed** (quiet90) |
| P7 | outage90: `raw` `p95_offset_m` above `a0.3`'s on bayside and boulevard | 7.99 against 3.75 m; 8.61 against 3.58 m | held |
| P8 | outage90: `track` `median_position_err_m` below `raw`'s on every course | bayside 2.55 against 2.77, blocks 2.87 against 2.80, boulevard 2.52 against 2.84 | **missed** (blocks, by 0.07 m) |
| P9 | `a0.3` on quiet90 against outage90: `median_time_diff_share` within ±0.01 on every course | 0.0 / 0.0 / 0.0 | held |
| P10 | by R2, at least one of `a0.6`, `raw`, `track` qualifies | none qualifies (below) | **missed** |

(Courses are bayside / blocks / boulevard. Every mission was flown by `pace_p.py` as `keep16`, v0.18.2's real-rover pilot; only the GPS filter changed. `a0.3` is the filter as it ships.)

## Decision

- **R1 does not stop anything:** the check found no difference (18 of 18 identical).
- **R2: none qualifies, so a real rover keeps alpha 0.3.** A variant qualifies if, against `a0.3` on quiet90 and on quietdrift90, it has `groups_slower` 0 and `groups_lost` 0, its blocks corner `p95_m` is at most 0.25 m above `a0.3`'s, its blocks corner `median_past_m` is at least 0 m, its `p95_offset_m` is at most 0.5 m above `a0.3`'s on every course and `groups_faster` ≥ 1 on one profile; and on outage90 `groups_lost` 0 and `median_time_diff_share` at most +0.01 on every course.
  - `a0.6`: slower 0 and 0, lost 0, faster 3 and 3; corner `p95_m` 3.04 against 3.17 and 4.35 against 4.58 m; `p95_offset_m` at most +0.02 m on any course; outage90 lost 0, −0.28 / −3.08 / 0.00%. But blocks corner `median_past_m` −0.22 and −0.37 m: it turned before the corners. **Does not qualify** (this condition only).
  - `raw`: slower 0, lost 0, faster 3 and 3; outage90 lost 0, +0.49 / −2.95 / +0.57%. But corner `p95_m` +0.43 m on quiet90, and `median_past_m` −0.84 and −1.07 m. **Does not qualify.**
  - `track`: slower 0, lost 0, faster 3 and 2; outage90 lost 0, −0.83 / −4.21 / 0.00%. But corner `p95_m` 3.74 against 3.17 (+0.57) and 5.04 against 4.58 m (+0.46), and `median_past_m` −2.09 and −2.06 m. **Does not qualify.**
  - So v0.18.3 changes no code: the README, FINDINGS and a note above `GpsFilter` state these results.
- R3: this grade, the outputs and the code are published here.

## Each filter against the shipped one (paired by seed, same profile)

| variant | outage90 (1.5 m noise) | quiet90 (0.22 m) | quietdrift90 (0.22 m, drifting compass) |
|---|---|---|---|
| a0.6 | −4 / −49 / 0 s (−0.28 / −3.08 / 0%) | −14 / −51 / −6 s (−0.98 / −3.23 / −0.34%) | −12 / −50 / −8 s (−0.83 / −3.14 / −0.45%) |
| raw | +7 / −47 / +10 s (+0.49 / −2.95 / +0.57%); slower on 2 | −16 / −69 / −6 s (−1.11 / −4.37 / −0.34%) | −15 / −67 / −8 s (−1.03 / −4.21 / −0.45%) |
| track | −12 / −67 / 0 s (−0.83 / −4.21 / 0%) | −13 / −65 / 0 s (−0.91 / −4.11 / 0%) | −12 / −59 / 0 s (−0.83 / −3.71 / 0%) |

(Median paired differences, bayside / blocks / boulevard. Each was faster by the sign test on every course except `raw` on outage90 bayside and boulevard, where it was slower, and `a0.6` and `track` on outage90 boulevard and `track` on quietdrift90 boulevard, where it was neither. A course can count as faster with a median of 0 s, as `track`'s quiet90 boulevard did with 10 seeds faster, 0 slower and 14 tied.)

| blocks, near path corners | outage90 past / p95 (m) | quiet90 | quietdrift90 |
|---|---|---|---|
| a0.3 | 2.16 / 4.34 | 2.07 / 3.17 | 2.10 / 4.58 |
| a0.6 | −0.07 / 3.60 | −0.22 / 3.04 | −0.37 / 4.35 |
| raw | −0.89 / 8.08 | −0.84 / 3.60 | −1.07 / 4.53 |
| track | −1.79 / 4.05 | −2.09 / 3.74 | −2.06 / 5.04 |

| 95th-percentile distance from the course, whole mission (m) | outage90 | quiet90 | quietdrift90 |
|---|---|---|---|
| a0.3 | 3.75 / 4.34 / 3.58 | 2.17 / 3.31 / 0.86 | 6.79 / 6.78 / 7.51 |
| a0.6 | 3.99 / 4.01 / 4.48 | 1.36 / 2.65 / 0.88 | 5.72 / 5.76 / 7.12 |
| raw | 7.99 / 9.47 / 8.61 | 1.43 / 3.10 / 0.90 | 5.40 / 5.51 / 5.86 |
| track | 3.50 / 3.59 / 3.17 | 1.82 / 3.34 / 1.09 | 5.50 / 6.13 / 6.43 |

Pooled made good, outage90 / quiet90 / quietdrift90: `a0.3` 0.880 / 0.882 / 0.873; `a0.6` 0.886 / 0.889 / 0.885; `raw` 0.875 / 0.890 / 0.885; `track` 0.888 / 0.886 / 0.881 m/s. Every mission was completed and no checkpoint report was refused; 71-72 of each 72 missions beat the human marathon pace (0.754 m/s).

## Findings

1. **The lag is the shipped filter's, as the arithmetic said (P3, P9).** With alpha 0.3 the pilot's position was a median 6.31-6.44 m from the rover's true one on every course and profile, and making the GPS noise seven times smaller changed that by under 0.1 m and the mission times by a median 0 s. Without the average (`raw`) only the fix's own age is left: 2.05-2.13 m with quiet GPS, against about 2.2 m predicted from a 1.5 s delay plus a median 1 s before the fix is read. alpha 0.6 sits between (3.3-3.4 m), and the tracker settles on the fixes like `raw` (2.2-2.3 m).
2. **A truer position was faster on every course where the difference was significant, but it also turned before the corners (P4, P5, R2).** With quiet GPS, every lag-free filter was 3.1-4.4% faster on city blocks (50-69 s a mission, 24 of 24 seeds) and 0.8-1.1% faster on bayside, and slower on no course. Each went round blocks' right angles earlier: a median 0.2-2.1 m before each corner, against 2.1 m past it with the shipped filter. The 16 m lookahead is measured from where the pilot thinks it is, so with alpha 0.3 the pilot really aims about 9.6 m ahead of the rover, and with the tracker about 13.8 m. pace-p found that aiming further ahead on blocks saves time by turning early. So this study cannot tell how much of the saving is a truer position and how much is a longer real aim. pace-r flies the tracker with a 12 m lookahead (a real aim of about 9.8 m, the shipped pilot's) and the shipped filter with 20 m (about 13.6 m, the tracker's at 16 m) to separate them.
3. **Under the simulator's 1.5 m noise, raw fixes cost what `gps_noise_study.py` said, and the tracker does not (P7, P8).** On outage90, `raw` held the rover more than twice as far from the course at the 95th percentile (7.99-9.47 m against 3.58-4.34 m; largest 38-45 m), with heading errors three times larger (RMS 10.0-14.1° against 4.2-4.4°), and was slower on bayside and boulevard. With the same noise the tracker's 95th percentile was below the shipped filter's on every course (3.17-3.59 m), it steered no harder (mean |angular| 0.027-0.041 against 0.027-0.042), and it was 4.2% faster on blocks. Its median position error was below `raw`'s on two courses and 0.07 m above it on blocks (P8's miss), but its 95th percentile was lower on all three (4.79-5.62 m against 6.21-6.77 m).
4. **Where the shipped filter lost time on gentle courses.** With quiet GPS `a0.6` and `raw` made a median 0 recovery moves (backing up when the target is behind) against the shipped filter's 1, and the largest distance from the course in a mission fell from 7.3-7.4 m to 5.6-6.3 m. The tracker, which restarts after each outage, kept a median of 1 recovery and still saved 0.9% on bayside. Which part of the bayside saving comes from fewer recovery moves was not tested.
5. **How the decision rule decided.** `a0.6` met every condition but one. It turned a median 0.22 and 0.37 m before blocks' corners, and the rule required at least 0 m. The rule was written so that a truer position could cut the shipped pilot's 2 m overshoot without turning early. A condition set exactly at the target value fails a variant that turns within half a metre of it. The rule binds as written. pace-r changes the question instead of the threshold: it matches the real aim, so a lag-free filter that turns where the shipped one does can show what a truer position is worth by itself.

## Limits

Simulated rovers only (pace_l.py's measured Mini+ profile), so speeds are upper bounds on what a sidewalk allows. quiet90's 0.22 m is drawn as independent noise per fix. The slow wander measured on standing Earth Rovers (1.5 m in 60 s), steady offsets and multipath jumps are not modelled, and the Mini+'s receiver may differ from the Zero's. Nothing here predicts a fix forward over its 1.5 s delay. The courses are idealised, with corners of only 90° or under 25°, and sidewalk width is not modelled, so "distance from the course" stands in for "off the sidewalk". alpha 0.6, beta 0.053 and the 3 s restart were fixed before any mission was flown. Finding 2's real-aim figures are worked out from the measured position errors, not measured. None of this has been measured on a live Mini+.
