# pace-i: should bridging GPS gaps on the wheels be the default? (pre-registered)

MV2 of Munim, Inc. Written with AI agents. CC BY 4.0.

This file is committed to main before any pace-i mission is flown. The job that flies them (`pace-i-v1`) waits until this file, `studies/pace-h/GRADE.md` and pace-h's `pace_h.py` are on main. It records this file's SHA-256 and the time it fetched main (`fetched.json`). The study code (`pace_i.py`, `test_pace_i.py`) will be published with the grade, byte for byte as the job ran it. No clock time is written here: the commit history and the job log show the order.

## Why

pace-h (`studies/pace-h/GRADE.md`, 9 of 10 predictions held) led to v0.14.0 turning dead reckoning off by default on a real rover. Without it the pilot stops whenever the GPS has had no fresh fix for 3 s. pace-h's bridging variant used dead reckoning only while the GPS had no fresh fix. On a clean GPS it flew like the pilot without dead reckoning. With 30% of fixes missing it was 4.8-5.4% faster, and it was the fastest pilot pooled on every profile. It lost on one course, so v0.14.0 offers it only as an option (`--dead-reckon-gaps`). But pace-h's gaps were single fixes missing at random. Real outages come in runs: under trees, beside tall buildings, in underpasses. The reckoner may carry the position for at most 30 s after the last fix.

A long gap raises a second question. The GPS filter averages fixes (each new one moves its position 0.3 of the way). After a long gap the first new fix is blended with an average of fixes from before the gap. A rover that kept moving on its wheels then suddenly appears to be far behind where it is. This is the position jump after a GNSS outage that Fixposition's field guide describes (https://www.fixposition.com/blogs/field-guide/position-jumps-after-gnss-outage). A pilot that stopped during the gap, as v0.14.0's does, barely moved, so the stale average does it little harm. `bridge-r+cf0.3` tests the simplest cure: after a gap longer than the filter's 3 s limit, start the average again from the first new fix.

Prior art: bridging GNSS outages with wheel odometry is standard practice (automotive dead reckoning; ROS robot_localization). The question here is narrower: on this rover's measured telemetry and this pilot, which default keeps the human marathon pace through outages of a given length, and what does each cost on a clean GPS?

## Design

Profiles (pace_h.py's `measured` Mini+, which reports its wheels' RPM):
- `measured`: no outages;
- `outage15`: GPS outages of 15 s (shorter than the reckoner's 30 s), each after a clear spell drawn from an exponential distribution with a mean of 150 s, so about 9% of the time is out;
- `outage45`: outages of 45 s (longer than 30 s), after a mean of 300 s, about 13% out.

During an outage every GPS report reads no fix (1000). The windows come from a generator of their own seeded from the seed, so the rover's own draws (GPS noise, the measured 5% random dropouts, compass noise) are the same as without outages.

Variants:

| variant | what it is |
|---|---|
| cf0.3 | `--smooth-heading` only: v0.14.0 on a real rover |
| bridge+cf0.3 | dead reckoning steered by only while the GPS has no fresh fix (pace_h's `BridgePilot`, v0.14.0's `--dead-reckon-gaps`) |
| bridge-r+cf0.3 | bridge+cf0.3, with the GPS filter starting its average again from the first fix after a gap longer than 3 s (`ResettingGpsFilter`) |
| dr+cf0.3 | v0.13.0 on a real rover, for reference |

Cruise 0.8 (`--marathon`), pace_study's three courses (boulevard, blocks, bayside), **seeds 85-108**, none flown by an earlier study. 3 × 4 × 3 × 24 = **864 missions**. Every mission records pace_h.py's fields, plus `outage.withheld` (GPS reports the outages turned into no-fix) and `outage.gps_resets` (filter restarts; bridge-r+cf0.3 only).

Before the study, if `studies/pace-h/runs.jsonl` is on main, `--check` flies seeds 61-63 of pace-h's measured cf0.3 and bridge+cf0.3 missions again (18 missions) and compares every field with pace-h's record.

`verdicts` compare pairs paired by seed per course, b against a: (cf0.3 → bridge+cf0.3), (cf0.3 → bridge-r+cf0.3), (bridge+cf0.3 → bridge-r+cf0.3), (cf0.3 → dr+cf0.3), (dr+cf0.3 → bridge-r+cf0.3). "Faster" or "slower" means a paired sign test with p < 0.05 (`groups_faster`, `groups_slower`). `groups_lost` counts courses where a completed more missions. `median_time_diff_share` is the median paired difference over a's median time. `overview` gives each profile and variant's pooled `median_made_good_mps`, `beat_human_pace` and `share_stopped`.

## Predictions

Each is graded from those output fields.

- **I1.** If the check runs: compared 18, identical 18, missing 0. If `studies/pace-h/runs.jsonl` is not on main, I1 is graded "not tested".
- **I2.** All 864 missions are completed.
- **I3.** On a clean GPS bridging costs nothing: on measured, bridge+cf0.3 and bridge-r+cf0.3 against cf0.3 each have `groups_slower` 0, `groups_lost` 0 and |`median_time_diff_share`| ≤ 0.005 on every course.
- **I4.** Through 15 s outages the restarting bridge pays: bridge-r+cf0.3 against cf0.3 is faster on all 3 courses of outage15, with `median_time_diff_share` ≤ −0.04 on each.
- **I5.** Through 45 s outages it still pays: bridge-r+cf0.3 against cf0.3 is faster on all 3 courses of outage45, with `median_time_diff_share` ≤ −0.03 on each.
- **I6.** Restarting the filter matters after long gaps: bridge-r+cf0.3 against bridge+cf0.3 is faster on at least 2 of the 3 courses of outage45.
- **I7.** Outages stop v0.14.0's pilot and bridging takes most of that back: cf0.3's `share_stopped` is ≥ 0.05 on outage15 and ≥ 0.08 on outage45, and bridge-r+cf0.3's is at most half of cf0.3's on both.
- **I8.** pace-g's cost replicates a third time: dr+cf0.3 against cf0.3 is slower on all 3 courses of measured.
- **I9.** Marathon pace: bridge-r+cf0.3's pooled `median_made_good_mps` is ≥ 0.85 on outage15 and ≥ 0.80 on outage45, with `beat_human_pace` 72 on both; cf0.3's is ≤ 0.80 on outage45.

Why these:
- I3: with a fresh fix both bridging variants steer as cf0.3 does. They can differ only after a gap of more than 3 s, which on measured (5% of fixes missing at random) is rare. pace-h measured shares of 0.0014 or less.
- I4, I7: cf0.3 stops about 3 s into an outage and starts again with the first fix after it. That is about 12-13 s of a 165 s cycle, or 7-8% of the time. Bridging drives through a 15 s outage once dead reckoning is trusted, which took 58-104 s in pace-h. Only an outage before then stops it.
- I5, I7: the reckoner carries the position for 30 s after the last fix, so bridging stops for about the last 15 s of a 45 s outage. cf0.3 stops for about 42 s. Per 345 s cycle that is roughly 4.5-5% against 12%.
- I6: after bridging 30 s (about 25 m), the filter without a restart puts the rover about 0.7 × 25 ≈ 18 m behind where it is. The pilot's 8 m lookahead target is then behind the rover, so it turns back until later fixes pull the average forward.
- I8: pace-g and pace-h both measured +6.5-7.0% on bayside and boulevard, +1.2-1.5% on blocks, and 24 of 24 seeds slower on each.
- I9: 0.878 m/s (cf0.3 on measured in pace-h) less 4.5-5% stopped is about 0.83-0.84, and less 12% is about 0.77. The human marathon pace is 0.754.

## Decision rules

- **R1.** A bridging variant qualifies if, against cf0.3, it has `groups_slower` 0 and `groups_lost` 0 on every profile and is faster on at least 2 courses of each outage profile. If I1 is not failed and one qualifies, the next release makes bridging the real-rover default, with `--no-dead-reckon` restoring v0.14.0's pilot. If bridge-r+cf0.3 qualifies and is slower than bridge+cf0.3 on no course of any profile, it is the one chosen, and `--dead-reckon-gaps` gains the filter restart. Otherwise bridge+cf0.3 is chosen if it qualifies. The release is assembled and must fly a sample of pace-i's missions of the chosen variant exactly, as v0.14.0 flies pace-h's. The `Pilot` class keeps its defaults, so old studies reproduce.
- **R2.** If neither qualifies, the defaults stay as v0.14.0 has them (dead reckoning off), and README reports what outages cost each pilot.
- **R3.** If the check finds any difference, nothing from this study is published as a finding until the difference is explained.
- **R4.** Whatever the outcome, the grade and the outputs are published in studies/pace-i/ with the code, and the results go into FINDINGS-frodobots-2k.md and the README. I6, I7 and I9 decide nothing.

Limits: simulated rovers only, so speeds are bounds on what a real sidewalk allows. Outages here are all-or-nothing and of fixed length; a real GPS often degrades before it drops out (fixes wander off by metres under trees), which this study does not model. The simulated wheels report the commanded speed exactly. None of this has been measured on a live Mini+.
