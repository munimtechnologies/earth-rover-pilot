# pace-s: grade

MV2 of Munim, Inc. Written with AI agents. CC BY 4.0.

Graded strictly from the output fields named in `studies/pace-s/PREDICTION.md`, which was on main before any mission was flown (the job recorded its SHA-256, 671fb333…, in `fetched.json`). The job `pace-s-v1` fetched main at 2026-10-25T22:00:44Z (rover_pilot.py 0.18.4, `pace_q.py` e65c9b56…, pace-r's `runs.jsonl` 486ce42e…) and flew 576 missions plus the 18-mission check in 19 minutes. All 37 tests passed first (`test_pace_s` 16, `test_pace_q` 21; `tests.txt`). `pace_s.py` and `test_pace_s.py` are published next to this file byte for byte as the job ran them (SHA-256 343feeb8… and e109ec2c…).

**8 of 10 predictions held. By the pre-stated rule R2, `restart` does not qualify, so a real rover keeps the shipped GPS filter for now.** Starting the average again after a gap removed the 55-63 m position jumps, held the rover closer to the course everywhere and was faster on city blocks and bayside. But on the straight boulevard course with the simulator's 1.5 m GPS noise it was slower on 6 of 24 seeds and faster on none (p 0.031), and R2 asked for no slower course on any profile.

## Predictions

| | prediction | result | |
|---|---|---|---|
| P1 | check: compared 18, identical 18, missing 0 | compared 18, identical 18, missing 0 (`check.different` []) | held |
| P2 | all 576 missions completed | 576 of 576 | held |
| P3 | `a0.3` on outage90, quiet90, quietdrift90: `median_max_m` ≥ 40 m and `over_snap` ≥ 18 of 24 on every course | `median_max_m` 55.24-63.47 m, `over_snap` 21-22 on all nine | held |
| P4 | `a0.3` on quiet45: `median_max_m` between 20 and 40 m on every course | 35.55 (bayside), 35.36 (blocks), 36.22 (boulevard) | held |
| P5 | `restart`: `median_max_m` ≤ 15 m and `over_snap` ≤ 2 of 24, every profile and course | `median_max_m` 9.90-12.45 m everywhere; `over_snap` 0 on outage90, quiet90 and quiet45, but 1, 1 and **4** on quietdrift90 (boulevard 4, largest 26.72 m) | **missed** |
| P6 | `restart`'s `median_position_err_m` no more than 0.1 m above `a0.3`'s and no more than 1.0 m below | 0.06-0.16 m below on all 12 profile × course cells | held |
| P7 | `restart`'s `groups_slower` 0 on every profile | 0 on quiet90, quietdrift90, quiet45; **1 on outage90** (boulevard) | **missed** |
| P8 | `restart`'s `groups_lost` 0 on every profile | 0 everywhere | held |
| P9 | blocks corner `median_past_m` ≥ 0 and within 0.5 m of `a0.3`'s, every profile | 1.85 / 1.92 / 1.91 / 1.85 m against 1.98 / 2.01 / 2.00 / 1.85 (outage90 / quiet45 / quiet90 / quietdrift90) | held |
| P10 | on outage90 and quiet90, `restart` faster on blocks (p < 0.05) with `median_time_diff_share` between −0.03 and 0 | outage90 −0.0051 (15 faster, 1 slower, p 0.0005); quiet90 −0.0070 (21 faster, 0 slower, p < 0.0001) | held |

## Decision rules

- **R1:** the check found no difference, so the results stand as findings.
- **R2:** not met. Every other condition held: `groups_lost` 0 on every profile; blocks corner `median_past_m` 1.85-1.92 m (at least 0); blocks corner `p95_m` at most 0.09 m above `a0.3`'s (outage90 3.06 against 2.97; lower on the other three profiles); `p95_offset_m` below `a0.3`'s on all 12 cells; `median_max_m` below `a0.3`'s on all 12 cells. The one condition that failed is `groups_slower` 0 on outage90: on boulevard `restart` was slower on 6 seeds and faster on none, with 18 ties (sign test p 0.0312, median paired difference 0 s). So, as written, a real rover keeps `GpsFilter` as it ships, and the results go into v0.18.5 (documentation only).
- **R3:** this grade, the outputs and the code are published in `studies/pace-s/`.

The rule is applied as written. Its margin was tiny (6 of 24 seeds, a median of 0 s), but loosening it after seeing the result would make the pre-registration meaningless.

## What the fields show

**The jump, as shipped.** Through 90 s outages the shipped filter's largest position error per mission had a median of 55.2-63.5 m, over 20 m in 21-22 of 24 missions on every course; through 45 s outages, 35.4-36.2 m, over 20 m in all 72. This confirms on 24 fresh seeds what `studies/pace-r/TRACE.md` found on one mission: the average carried across the outage and blended with the first fix after it pulls the estimate back about 0.7 of the distance driven through the gap.

**The fix removes it.** With `restart` the median of the largest errors was 10.4-10.7 m (outage90), 9.9-10.1 m (quiet90), 10.3-10.4 m (quiet45) and 11.5-12.5 m (quietdrift90), the size of the average's lag when an outage starts plus the reckoner's drift. Only quietdrift90 had missions over 20 m (1, 1 and 4, largest 26.7 m). With a drifting compass the dead reckoner drifts during the outage, and restarting from the fix does not prevent that. The median position error fell 0.06-0.16 m everywhere and its 95th percentile fell from 8.2-9.1 m to 7.7-8.2 m.

**Time.** On blocks `restart` was faster on all four profiles (−0.50 to −0.70%, 8-11 s a mission; 15-22 seeds faster, 0-1 slower), and on bayside too (−0.14 to −0.28%). On boulevard the median paired difference was 0 s on every profile. With quiet GPS it was faster on 1 and 4 seeds and slower on none (quiet90, quiet45). With 1.5 m noise (outage90) it was slower on 6 seeds and faster on none: by 8, 6, 2, 2, 94 and 4 s (seeds 327, 328, 331, 337, 338, 339; read from `runs.jsonl`). With quiet GPS and a drifting compass (quietdrift90) it was slower on 6 and faster on 2, which was not significant (p 0.29). Seed 338's 94 s is 80 s more stopped and one more recovery move. On quietdrift90 the same seed took exactly 1917.6 s with both filters, so a long stop like that may come from where an outage happens to fall rather than from the filter. The trace below is meant to find out.

**Where the rover drove.** `restart` held the rover closer to the course on every profile and course: 95th-percentile distance 0.07-1.47 m lower (quiet90 bayside 1.23 m against 2.70). The heading error was about the same (medians within 0.21°). It steered slightly less hard on bayside and blocks. Its median recovery moves were 1.0 against 0.0 on outage90 blocks and 0.5 against 0.0 on outage90 boulevard. On the quiet profiles they were the same.

**This is the second time.** `pace_i.py` (v0.15.0) flew the same restart (`ResettingGpsFilter`) through 45 s outages with the simulator's noise. It was faster on blocks but 2-4 s slower on bayside and boulevard, with more recovery moves, and it was not adopted. pace-s found the same small cost on boulevard with 1.5 m noise, but not with the 0.22 m of noise measured on recorded Earth Rovers. pace-i guessed then that a single fresh fix carries the full noise of one fix, which the average had damped. That has still not been tested.

## What happens next

- v0.18.5 documents pace-s and `TRACE.md` in the README and FINDINGS. The pilot, its GPS filter and every default stay as they are.
- `trace_s.py` (a diagnostic, not pre-registered) flies the six slower outage90 boulevard seeds and quietdrift90 seed 338 again with both filters. Each second it records the command the rover applies, whether the filter has a fresh fix, the time bridged, recovery moves, checkpoints and the true distance to the next one, so that each lost second can be placed.
- Any later proposal to change a real rover's filter will be a new pre-registered study on fresh seeds, stating openly that pace-s's boulevard result prompted it.

## Limits

- Simulated rovers only (pace_l.py's measured Mini+ profile), so the speeds are upper bounds.
- The outages are idealised: no fix at all for exactly 45 or 90 s, and fixes that come back with the same independent noise. A 10 m multipath fix right after an outage, which a restart would adopt in full, is not modelled.
- `restart` starts from the raw fix. Starting the average from the dead reckoner's estimate and blending the fix in was not tested.
- Three idealised courses with corners of only 90° or under 25°, and no sidewalk width.
- None of this has been measured on a live Mini+.
