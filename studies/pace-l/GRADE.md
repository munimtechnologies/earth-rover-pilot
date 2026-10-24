# pace-l grade: does the 120 s reach hold up when the wheels and the compass lie?

MV2 of Munim, Inc. Graded with AI agents. CC BY 4.0.

Predictions: `studies/pace-l/PREDICTION.md` (SHA-256 37b2544e…, on main before the job fetched it; see `fetched.json`). Job `pace-l-v1`: fetched main at 2026-10-23T23:22:13Z (rover_pilot.py 0.16.0, pace_k.py 92b1642f… as pace-k-v1 ran it, with `studies/pace-k/GRADE.md` and `runs.jsonl`), `tests_exit` 0 (27 tests: test_pace_l and test_pace_k), then flew 1,296 missions in 2,394 s (peak memory 0.07 GB). Every number below is read from `summary.json` in this folder. The code is `pace_l.py` and `test_pace_l.py` as the job ran them (pace_l.py SHA-256 305d1ce7…, test_pace_l.py 2348ed23…).

**Result: 9 of 9 predictions held. Rule R1 applies: the 120 s reach stays; v0.16.1 only adds pace-l's results to the README and FINDINGS.**

## Predictions

| | prediction | result | |
|---|---|---|---|
| L1 | check: compared 36, identical 36, missing 0 | 36, 36, 0 | held |
| L2 | all 1,296 missions completed | 1,296 of 1,296 | held |
| L3 | slip90, drift90, lie90: bridge120 against bridge60 faster ≥ 2, slower 0, lost 0 | 3 / 0 / 0 on each | held |
| L4 | lie45: bridge60 against bridge faster 3, slower 0, lost 0 | 3 / 0 / 0 | held |
| L5 | `profile_verdicts`: `groups_faster` 0 for every variant on every lying profile | 0 in all 12 | held |
| L6 | lie90 against outage90, bridge120's `median_time_diff_share` below +0.05 on every course | +0.0048, +0.0049, +0.0028 | held |
| L7 | lie90 against outage90, bridge120's share above bridge's on ≥ 2 of 3 courses | 0.0048 > 0.0032, 0.0049 > 0.0029, 0.0028 > 0.0021 (3 of 3) | held |
| L8 | bridge120's p95 position error on lie90 above its own on outage90 and above bridge60's on lie90, every course | bayside 8.89 / 8.63 / 8.73, blocks 8.77 / 8.52 / 8.59, boulevard 9.28 / 8.77 / 8.85 m | held (by 0.16-0.51 m) |
| L9 | bridge120 `beat_human_pace` ≥ 66 of 72 on slip90, drift90, lie90 | 72, 72, 72 | held |

(bridge = `bridge+cf0.3`, reach 30 s, v0.15.0's real-rover default; bridge60 = `bridge60+cf0.3`; bridge120 = `bridge120+cf0.3`, v0.16.0's real-rover default. Shares are bayside / blocks / boulevard.)

## Decision

- **R1 applies.** L1 held, and bridge120 against bridge60 has `groups_slower` 0 and `groups_lost` 0 on all six profiles (outage45, lie45, outage90, slip90, drift90, lie90). So the 120 s reach stays, and v0.16.1 only adds pace-l's results to the README and FINDINGS.
- R2 and R3 do not need to be read. (bridge60 against bridge also has `groups_slower` 0 and `groups_lost` 0 on all six.)
- R4 does not apply: the check found no difference (36 of 36 identical).

## What a longer reach did when the wheels and compass lie (paired by seed, same outages)

Median paired time difference per course (bayside / blocks / boulevard) and seeds faster of 24:

| profile | 60 s against 30 s | 120 s against 30 s | 120 s against 60 s |
|---|---|---|---|
| outage45 | −57 / −76 / −85 s (−3.7 / −4.5 / −4.5%), 23/22/24 | same as 60 s | identical missions |
| lie45 | −54 / −66 / −82 s (−3.5 / −3.9 / −4.3%), 23/22/24 | same as 60 s | identical missions |
| outage90 | −48 / −53 / −61 s (−3.1 / −3.1 / −3.2%), 20/20/21 | −71 / −108 / −124 s (−4.6 / −6.2 / −6.5%) | −30 / −45 / −49 s (−2.0 / −2.7 / −2.6%), 19/19/21 |
| slip90 | −48 / −48 / −61 s (−3.1 / −2.8 / −3.2%), 20/20/21 | −71 / −105 / −124 s (−4.6 / −6.1 / −6.5%) | −32 / −48 / −50 s (−2.1 / −2.9 / −2.7%), 19/19/21 |
| drift90 | −37 / −54 / −62 s (−2.4 / −3.1 / −3.2%), 19/17/21 | −76 / −113 / −119 s (−4.9 / −6.5 / −6.2%) | −36 / −45 / −48 s (−2.4 / −2.7 / −2.6%), 18/17/21 |
| lie90 | −37 / −50 / −62 s (−2.4 / −2.9 / −3.2%), 20/18/21 | −74 / −112 / −119 s (−4.7 / −6.5 / −6.2%) | −32 / −45 / −48 s (−2.1 / −2.7 / −2.6%), 18/18/21 |

Single seeds slower: 1 of 24 on blocks in drift90 (60 and 120 against 30 s), outage90 and slip90 (120 against 60 s); none elsewhere. Pooled made good (m/s), 30 / 60 / 120 s: outage45 0.825 / 0.862 / 0.862; lie45 0.822 / 0.858 / 0.858; outage90 0.809 / 0.836 / 0.868; slip90 0.809 / 0.836 / 0.866; drift90 0.807 / 0.831 / 0.860; lie90 0.807 / 0.831 / 0.861. Missions beating the human marathon pace (0.754 m/s), of 72: on the 90 s profiles 56-57 at 30 s, 69-70 at 60 s and 72 at 120 s; on the 45 s profiles 71-72 with every reach.

## Findings

1. **Wheel slip of up to ±15% cost nothing measurable, even after 120 s on the wheels alone.** slip90 against outage90 was slower on no course for any reach, with a median paired difference of 0 s everywhere (bridge120: 3/5, 5/7 and 2/2 seeds faster/slower). The slip was real: 14-18 spells a mission, a mean |slip| of 7.4-7.7%, and the reckoner's learned scale was off by 1.9-2.5% against 0.8-1.2% on outage90 at 120 s. A likely reason, not tested here: a wrong scale moves the reckoned position along the rover's path, not across it, and the pilot steers by the compass towards a checkpoint ahead and never reports a checkpoint without a fix.
2. **The compass drift is what costs, and it costs on clear sky too.** drift90 against outage90 was slower on every course for every reach, by +0.26 / +0.29 / +0.21% at 30 s and +0.55 / +0.49 / +0.23% at 120 s (4-8 s a mission). The drift roughly doubled the median heading error (2.7-3.3° to 5.3-5.9°) for every reach, because the pilot's compass-bias learner hardly follows a drifting error, as `pace_d.py` found. lie90 (both) cost about what drift90 did: +0.32 / +0.29 / +0.21% at 30 s, +0.48 / +0.49 / +0.28% at 120 s.
3. **The longer reach pays the lies a little more, and still wins by 10 times that.** On lie90 the lies cost the 120 s reach 0.07-0.20 percentage points more than the 30 s reach (L7), while the 120 s reach was 4.7-6.5% faster than 30 s and 2.1-2.7% faster than 60 s on the same lying profile. The median time stood still fell from 125-163 s a mission at 30 s to 3-6 s at 120 s.
4. **The position got a little worse, within the checkpoint tolerance.** At 120 s the 95th-percentile position error on lie90 was 8.8-9.3 m (outage90: 8.5-8.8 m), and the 95th-percentile distance from the course rose from 3.6 / 10.7 / 5.8 m to 4.3 / 11.1 / 7.4 m. Refused checkpoint reports rose from 0 to a mean 0.04 a mission on lie90 (about 3 in 72 missions) and 0.01 on slip90; every mission was still completed.
5. **Through 45 s outages 60 s and 120 s still fly the same**, with or without the lies, as in pace-k: a 45 s outage fits inside a 60 s reach.

## Limits

Simulated rovers only (pace_k.py's measured Mini+ profile), so speeds are upper bounds on what a sidewalk allows. The slip is one simple model: both sides' wheels read the same wrong factor, which changes in spells. There is no wheel spinning in place and no one-sided slip turning the rover. The drift is pace-d's model (SD 10°, 120 s time constant). Outages are clean cut-outs of fixed length. Why slip cost nothing (finding 1) is a likely reason, not a tested one. None of this has been measured on a live Mini+.
