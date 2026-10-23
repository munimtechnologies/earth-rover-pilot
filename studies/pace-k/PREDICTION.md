# pace-k: how long should the wheels carry the position through a GPS outage? (pre-registered)

MV2 of Munim, Inc. Written with AI agents. CC BY 4.0.

This file is committed to main before any pace-k mission is flown. The job that flies them (`pace-k-v1`) waits until this file, `studies/pace-j/GRADE.md`, `studies/pace-j/runs.jsonl` and pace-j's `pace_j.py` (SHA-256 6a73b2fb…) are on main. It records this file's SHA-256 and the time it fetched main (`fetched.json`). The study code (`pace_k.py`, `test_pace_k.py`) will be published with the grade, byte for byte as the job ran it. No clock time is written here: the commit history and the job log show the order.

## Why

Since v0.15.0 the pilot steers by the wheels while the GPS has no fresh fix (pace-i), and pace-j (9 of 9 predictions held) found that this still pays when the fixes wander off before and after each outage. But the wheel reckoner (`dead_reckon.py`) gives up 30 s after the last fix (`max_s`). In pace-j the bridging pilot stood still a median 86-108 s a mission through 45 s outages, against 9-13 s through 15 s outages: the last ~15 s of each long outage are spent waiting. A longer reach would drive through them, but the reckoned position drifts further from the truth the longer it runs, and the GPS filter's catch-up after the outage starts from further away.

Prior art: navigation filters cap how long they dead-reckon without an absolute fix (for example PX4's EKF2 has a maximum dead-reckoning time). This study does not propose a new method. It measures, for this pilot on this rover's measured telemetry, what the cap costs and what lifting it costs.

## Design

Profiles (pace_i.py's measured Mini+, cruise 0.8, pace_study's three courses):
- `outage15`, `outage45`, `wander45`: pace_j.py's profiles exactly (15 s outages after a mean of 150 s of sky; 45 s after 300 s; 45 s with fixes drifting out to 8 m over 20 s before each outage and back over 20 s after);
- `outage90`: 90 s outages after a mean of 600 s of sky.

Variants: the bridging pilot (`bridge+cf0.3`, the real-rover default since v0.15.0) with the reckoner's reach (`max_s`) at 30 s (unchanged), 60 s (`bridge60+cf0.3`) or 120 s (`bridge120+cf0.3`). Nothing else differs. Every mission is flown by pace_j.py's own `fly` (and so by pace_i.py's). **Seeds 133-156** (none flown before). 4 × 3 × 3 × 24 = **864 missions**.

Before the study, `--check` flies seeds 109-111 of pace-j's outage45 and wander45 `bridge+cf0.3` missions again (18 missions) and compares every field with pace-j's record.

Output fields: `verdicts` compare pairs on the same profile, paired by seed per course: `bridge60+cf0.3` against `bridge+cf0.3`, `bridge120+cf0.3` against `bridge+cf0.3`, and `bridge120+cf0.3` against `bridge60+cf0.3`. "Faster" or "slower" means a paired sign test with p < 0.05 (`groups_faster`, `groups_slower`); `groups_lost` counts courses where the first completed more missions; `median_time_diff_share` (in `pair_effect`) is the median paired difference over the first's median time. `overview` gives each profile and variant's pooled `median_made_good_mps`, `share_stopped` and `beat_human_pace`; `position` gives the pilot's 95th-percentile position error (`p95_position_err_m`) per course.

## Predictions

Each is graded from those output fields.

- **K1.** The check: compared 18, identical 18, missing 0.
- **K2.** All 864 missions are completed.
- **K3.** A longer reach changes nothing that matters with 15 s outages: on outage15, `bridge60+cf0.3` against `bridge+cf0.3` has `groups_slower` 0 and `groups_lost` 0, and every course's `median_time_diff_share` is between −0.005 and +0.005.
- **K4.** It drives through 45 s outages: on outage45, `bridge60+cf0.3` against `bridge+cf0.3` has `groups_faster` 3, `groups_slower` 0, `groups_lost` 0, and every course's `median_time_diff_share` is between −0.08 and −0.025.
- **K5.** Also when the fixes wander first: on wander45, `bridge60+cf0.3` against `bridge+cf0.3` has `groups_faster` 3, `groups_slower` 0, `groups_lost` 0.
- **K6.** Through 90 s outages each step helps: on outage90, `bridge60+cf0.3` against `bridge+cf0.3` and `bridge120+cf0.3` against `bridge60+cf0.3` each have `groups_faster` 3, `groups_slower` 0, `groups_lost` 0.
- **K7.** The waiting goes: on outage45, `bridge60+cf0.3`'s pooled `share_stopped` is at most 0.02 (pace-j: 0.057 for `bridge+cf0.3`).
- **K8.** The pilot knows less well where it is: on outage45, `bridge60+cf0.3`'s `p95_position_err_m` is above `bridge+cf0.3`'s on every course.
- **K9.** Marathon pace: `bridge60+cf0.3`'s `beat_human_pace` is 72 on outage45 and at least 70 on wander45; `bridge120+cf0.3`'s is at least 66 on outage90.

Why these:
- K3: with 15 s outages the gap between fixes stays under 30 s except when two outages fall a few seconds apart, and a longer reach only keeps more history, which the reckoner's look-ups (nearest fix or compass reading within a tolerance) don't reach.
- K4, K7: pace-j's bridging pilot stood still 77-97 s a mission more on outage45 than on outage15 (a median 1,708 s mission), so driving through would save about 4.5-5.7%. A 45 s outage, plus up to 2 s to the last fix before it and the GPS's 1.5 s delay, fits inside 60 s.
- K5: pace-j found wandering cost the bridging pilot only 0.4-0.6% on wander45.
- K6: with 90 s outages a 30 s reach stands still about 60 s per outage and a 60 s reach about 30 s; a 120 s reach covers them.
- K8: the reckoned position drifts with every second it runs, and when the GPS comes back the filter's average starts from fixes taken further back along the route.
- K9: pace-j's bridging pilot beat the human pace (0.754 m/s) in 72 of 72 missions on outage45 and 71 on wander45.

## Decision rules

- **R1.** If K1 is not failed and `bridge60+cf0.3` against `bridge+cf0.3` has `groups_slower` 0 and `groups_lost` 0 on all four profiles and `groups_faster` at least 2 on outage45 and on wander45, the next release (v0.16.0) builds the real-rover default's reckoner (bridging GPS gaps) with a 60 s reach, with a test that flies pace_k.py's `bridge60+cf0.3` missions exactly. `--dead-reckon` (always on) keeps 30 s, since this study does not fly it.
- **R2.** If R1 applies and `bridge120+cf0.3` against `bridge60+cf0.3` also has `groups_slower` 0 and `groups_lost` 0 on all four profiles and `groups_faster` at least 2 on outage90, the reach is 120 s instead of 60 s.
- **R3.** If R1 does not apply, the reach stays 30 s, and the README says on which profiles and courses a longer reach was slower or lost missions.
- **R4.** If the check finds any difference, nothing from this study is published as a finding until the difference is explained.
- **R5.** Whatever the outcome, the grade and the outputs are published in studies/pace-k/ with the code. K3-K9 decide nothing beyond what R1-R2 read from the verdicts.

Limits: simulated rovers only, so speeds are bounds on what a real sidewalk allows. Outages are clean cut-outs of fixed length (except wander45's drift); the simulated wheels report the commanded speed exactly and never slip, so the reckoner's drift here is a lower bound on a real rover's. None of this has been measured on a live Mini+.
