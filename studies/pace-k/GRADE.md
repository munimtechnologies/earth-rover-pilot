# pace-k grade: how long the wheels should carry the position through a GPS outage

MV2 of Munim, Inc. Graded with AI agents. CC BY 4.0.

Predictions: `studies/pace-k/PREDICTION.md` (SHA-256 9f0d31c5…, on main before the job fetched it; see `fetched.json`). Job `pace-k-v1`: fetched main at 2026-10-23T19:51:37Z (rover_pilot.py 0.15.0, pace_j.py 6a73b2fb… as pace-j-v1 ran it, with `studies/pace-j/GRADE.md` and `runs.jsonl`), `tests_exit` 0 (26 tests: test_pace_k and test_pace_j), then flew 864 missions in 1,540 s (peak memory 0.08 GB). Every number below is read from `summary.json` in this folder. The code is `pace_k.py` and `test_pace_k.py` as the job ran them (pace_k.py SHA-256 92b1642f…, test_pace_k.py cc43f0c0…).

**Result: 9 of 9 predictions held. Rules R1 and R2 apply: the real-rover default's reckoner (bridging GPS gaps) gets a 120 s reach in v0.16.0.**

## Predictions

| | prediction | result | |
|---|---|---|---|
| K1 | check: compared 18, identical 18, missing 0 | 18, 18, 0 | held |
| K2 | all 864 missions completed | 864 of 864 | held |
| K3 | outage15, bridge60 against bridge: slower 0, lost 0, every course's share within ±0.005 | 0 / 0; 0.0, 0.0, 0.0 (identical missions) | held |
| K4 | outage45, bridge60 against bridge: faster 3, slower 0, lost 0, every share in [−0.08, −0.025] | 3 / 0 / 0; −0.0338, −0.0392, −0.0472 | held |
| K5 | wander45, bridge60 against bridge: faster 3, slower 0, lost 0 | 3 / 0 / 0 | held |
| K6 | outage90: bridge60 against bridge, and bridge120 against bridge60, each faster 3, slower 0, lost 0 | 3 / 0 / 0; 3 / 0 / 0 | held |
| K7 | outage45, bridge60 pooled share_stopped ≤ 0.02 | 0.016 | held |
| K8 | outage45, bridge60 p95 position error above bridge's on every course | bayside 9.20 / 9.12, blocks 9.18 / 9.11, boulevard 9.56 / 9.26 m | held (by 0.07-0.30 m) |
| K9 | beat_human_pace: bridge60 72 on outage45 and ≥ 70 on wander45; bridge120 ≥ 66 on outage90 | 72; 72; 72 | held |

(bridge = `bridge+cf0.3`, reach 30 s, the real-rover default since v0.15.0; bridge60 = `bridge60+cf0.3`; bridge120 = `bridge120+cf0.3`.)

## Decision

- **R1 applies.** K1 held, and bridge60 against bridge has `groups_slower` 0 and `groups_lost` 0 on all four profiles, with `groups_faster` 3 on outage45 and on wander45.
- **R2 applies.** bridge120 against bridge60 also has `groups_slower` 0 and `groups_lost` 0 on all four profiles, and `groups_faster` 3 on outage90. So the next release (v0.16.0) builds the real-rover default's reckoner, which bridges GPS gaps (`--dead-reckon-gaps`), with a **120 s** reach, with a test that flies pace_k.py's `bridge120+cf0.3` missions exactly. `--dead-reckon` (steering by the wheels whenever it can) keeps 30 s, because this study did not fly it.
- R3 and R4 do not apply: the check found no difference (18 of 18 identical).

## What a longer reach did (paired by seed, same outages)

Median paired time difference per course (bayside / blocks / boulevard), as a share of the shorter reach's median, and seeds faster of 24:

| profile | 60 s against 30 s | 120 s against 30 s | 120 s against 60 s |
|---|---|---|---|
| outage15 | 0 / 0 / 0 (identical) | 0 / 0 / 0 (identical) | 0 / 0 / 0 (identical) |
| outage45 | −52 / −67 / −89 s (−3.4 / −3.9 / −4.7%), 24/24/24 | same as 60 s | 0; 1 seed faster on blocks and boulevard (not significant) |
| wander45 | −57 / −56 / −84 s (−3.7 / −3.3 / −4.4%), 24/24/24 | same as 60 s | 0; 1 seed faster on blocks and boulevard (not significant) |
| outage90 | −42 / −66 / −66 s (−2.6 / −3.7 / −3.4%), 21/23/24 | −93 / −121 / −128 s (−5.8 / −6.8 / −6.6%), 21/23/24 | −36 / −39 / −59 s (−2.3 / −2.3 / −3.2%), 19/22/24 |

No seed was slower in any of these 36 comparisons. Pooled made good (m/s), 30 / 60 / 120 s: outage15 0.870 / 0.870 / 0.870; outage45 0.820 / 0.862 / 0.864; wander45 0.818 / 0.858 / 0.858; outage90 0.797 / 0.826 / 0.864. Missions beating the human marathon pace (0.754 m/s), of 72: outage45 72 / 72 / 72; wander45 71 / 72 / 72; outage90 **52** / 70 / 72.

## Findings

1. **The waiting goes.** The median time stood still a mission (bayside / blocks / boulevard) fell on outage45 from 101 / 104 / 121 s at 30 s to 3 / 27 / 20 s at 60 s, and on outage90 from 169 s on every course at 30 s to 109 / 97 / 102 s at 60 s and 2 / 3 / 10 s at 120 s. The share of time stood still on outage90 went 9.6% → 5.7% → 2.0%. What is left at 120 s is likely outages that come before the reckoner is first trusted (a median 86-100 s into a mission); that was not checked mission by mission.
2. **Through 45 s outages a 60 s reach is all it takes.** 60 s and 120 s flew the same missions on outage45 and wander45 except one seed on each of two courses: a 45 s outage plus up to 2 s to the last fix and the GPS's 1.5 s delay fits inside 60 s, as predicted.
3. **On 15 s outages nothing changed at all.** Every outage15 mission flew identically with all three reaches, so the longer reach has no cost where it is not needed.
4. **The position got only a little worse in this simulator.** The 95th-percentile position error rose 0.07-0.30 m on outage45 (K8 held, but narrowly) and 1.0-1.4 m on wander45 (to 12.4-13.3 m), and on outage90 it was mixed (bayside 8.81 → 8.54 m at 120 s, boulevard 8.73 → 8.83 m). The 95th-percentile distance from the course on outage90 grew from 2.37 to 3.74 m on bayside and from 5.32 to 7.56 m on boulevard with 120 s. The wheels' learned scale stayed within about 1-1.5% of the truth. Steering effort did not change (median mean |angular| 0.043-0.061 for every reach).
5. **The cap was the main cost of long outages.** With a 30 s reach, 90 s outages took the pilot below the human marathon pace in 20 of 72 missions; with 120 s none were below it.

## Limits

Simulated rovers only (pace_i.py's measured Mini+ profile), so speeds are upper bounds on what a sidewalk allows. The simulated wheels report the commanded speed exactly and never slip, and the compass error is the simulator's, so how far a real rover's reckoned position drifts over 60-120 s on the wheels alone is a lower bound here, not a measurement. The pilot never reports a checkpoint without a fix, so a drifted estimate costs path, not false checkpoints, but a 120 s drift on a real sidewalk is untested. Outages are clean cut-outs of fixed length, except wander45's simple drift. Not yet driven on a live Mini+. A follow-up study with wheels that slip and scale errors that vary is the next check on the 120 s reach.
