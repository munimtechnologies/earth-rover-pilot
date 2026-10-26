# pace-u: grade

MV2 of Munim, Inc. Written with AI agents. CC BY 4.0.

Graded strictly from the output fields of the `pace-u-v1` job (`summary.json`, `report.md`, `tests.txt`, `fetched.json` in this folder) against `PREDICTION.md`, which was on main before any mission was flown (`fetched.json` records its SHA-256, 18f9a689…, and the time the job fetched main, 2026-10-26 12:45 UTC). The job ran `pace_u.py` 0.1.0 (SHA-256 916fd5e8…) on rover_pilot.py 0.18.5, with `pace_t.py` (3c89c187…), `pace_s.py` (343feeb8…) and pace-s's record (180cd541…) as pre-stated. `test_pace_u`, `test_pace_t` and `test_pace_s`: 55 tests, all passed. 1800 missions in 44 minutes.

**9 of 11 predictions held. R1 passed. By the pre-stated rule R2 neither warm-up qualifies, so a real rover keeps today's stuck check. R3 is not reached.** Each warm-up failed two of R2's conditions, and one of those was the same for both: a corner measure on one profile that came out 0.02 m beyond its tolerance. The next release documents the result and changes no code.

## Predictions

| | prediction | result | |
|---|---|---|---|
| P1 | check against pace-s: 18 compared, 18 identical, 0 missing; against pace-t: 11 compared, 11 identical | 18, 18, 0; 11, 11 | held |
| P2 | all 1800 missions completed | 1800 of 1800 | held |
| P3 | `a0.3` on quiet90, quietdrift90, quiet45: `early` ≥ 20 of 24 on every course | 22-24 | held |
| P4 | `warm10` and `restart+warm10`: `early` 0 on every course of outage90, quiet90, quietdrift90, quiet45 | 0 on all 24 | held |
| P5 | `warm5` and `restart+warm5`: `early` ≤ 2 of 24 on every course of the same | 0 on 11 of 12 courses each; 1 on outage90 boulevard | held |
| P6 | `warm5` and `warm10`: `late` ≤ `a0.3`'s `late` + 1 on every course of the same | 0 everywhere (`a0.3` 0) | held |
| P7 | blocked30, every variant and course: `eligible` ≥ 20 and `early_eligible` = `eligible` | `eligible` 24 everywhere; `early_eligible` 24 for `a0.3`, `warm5`, `restart+warm5`; **23 for `warm10` and `restart+warm10` on every course** | **missed** |
| P8 | blocked30 `median_first_s`: `a0.3` ≤ 11.5; 5 s variants 13.5-16.5; 10 s variants 18.5-21.5 | 9.1; 14.2; 19.1 on every course | held |
| P9 | `warm5` and `warm10` faster than `a0.3` (p < 0.05) on every course of quiet90, quietdrift90, quiet45 | `groups_faster` 3 on each (every p ≤ 0.0075) | held |
| P10 | against `a0.3`, `warm5`'s and `warm10`'s `groups_slower` and `groups_lost` 0 on every profile, and `warm5`'s against `warm10` | `warm10`: 0 and 0. **`warm5` against `a0.3` slower on 2 blocked30 courses; against `warm10` slower on all 3 blocked30 courses.** `groups_lost` 0 everywhere | **missed** |
| P11 | restart against its warm-up: `groups_slower`, `groups_lost` 0 on every profile; restart variants' `median_max_m` ≤ 15 m on every course of the four outage profiles | 0 and 0 on all 10 pairs; 9.95-11.50 m | held |

## The decision rules

- **R1 passed.** The 18 pace-s missions and the 11 pace-t missions flown again were identical to their records.
- **R2: `warm10` does not qualify.** It met these conditions: `groups_slower` 0 and `groups_lost` 0 against `a0.3` on every profile; `early` 0 on every course of the four outage profiles; `eligible` 24 on every blocked30 course; `p95_offset_m` at most 0.26 m above `a0.3`'s on any course (quietdrift90 bayside, 6.63 against 6.37 m); blocks corner `median_past_m` 2.00-2.20 m. It failed two: on blocked30 `early_eligible` was 23 of 24 eligible on every course (seed 388, below), and on quiet45 its blocks corner `p95_m` was 3.37 m against `a0.3`'s 3.10 m, 0.27 m above, where the rule allowed 0.25 m.
- **R2: `warm5` does not qualify.** It caught every eligible blocked mission before 30 s (24 of 24 on every course) and its `early` was at most 1 of 24 on the outage profiles. It failed two conditions: against `a0.3` it was slower on 2 of 3 blocked30 courses (`groups_slower` 2), and it had the same quiet45 corner `p95_m` (3.37 against 3.10 m). Its offset and `median_past_m` conditions held (offset at most 0.26 m above; `median_past_m` 2.01-2.20 m).
- So neither qualifies, and a real rover keeps today's stuck check. The `warm5`-against-`warm10` comparison decides nothing.
- **R3 is not reached**, because it needs a warm-up chosen under R2. For the record only: `restart+warm10` met every pace-s condition against `warm10`, and `restart+warm5` met every one against `warm5`. Each had `groups_slower` 0 and `groups_lost` 0 on every profile. Blocks corner `p95_m` was lower on every profile, and `median_past_m` was 1.73-2.16 m. `p95_offset_m` was at most 0.07 m above (outage90 boulevard, 3.03 against 2.96 m). `median_max_m` was 9.95-11.50 m against 35-63 m. pace-t showed the same. A real rover keeps the GPS average across gaps until a warm-up is adopted.

## What the misses were

**P7 and R2 (`warm10`): one seed whose catch came 12 s late, and 1 s after the block.** On blocked30 the 10 s variants made their first recovery move at 19.1 s in 22 missions per course and 21.1 s in one, all before 30 s, all with GPS up. Seed 388 was the exception on every course: 31.0 s, 1 s after the block ended (`runs.jsonl`). The shipped check fired on that seed at 9.1 s and again at 24.2 s, both normal. `warm5` fired at 26.1 s instead of its usual 14.2 s, so it was still before 30 s and counted. Both warm-ups were late by the same 11.9 s. That fits one clear of the stuck history at about 11.9 s, with the GPS up (its first outage began at 664.5 s). A clear starts the warm-up again. The shipped pilot was making its recovery move at that time, so for it the clear changed nothing. The pilot clears the history at a stop for stale telemetry or a missing fix, while bridging, inside the hold radius and at a recovery move. Which of these happened at 11.9 s is not known yet. `trace_u.py` (a diagnostic, queued) logs every stuck check of this mission to find out. Seed 388 took 1801.6 s with every variant, blocked or not, so the late move cost no time.

**P10 and R2 (`warm5`): a second recovery move just after the block.** On blocked30, `warm5` made its first move at 14.2 s. The move takes 6 s and clears the history, then the warm-up adds 5 s, and the check needs 9 s of history after that. So its next verdict was due at 34.2 s. It came in 19 of 24 missions on every course (`late` 19, 43 recovery moves per course). Its window was 25.2-34.2 s, and the rover could move only from 30 s. In the 4 s after the block the lagging GPS average moved less than 1.5 m, so the check still called the rover stuck, and the pilot backed up and turned though nothing held it any more. The shipped check's cycle is 9.1 s plus 6 s, so its second move came at 24.2 s, inside the block, and ended at 30.2 s, as the block ended. `warm10`'s second verdict would have been due at 19.1 + 6 + 10 + 9.1 ≈ 44 s, by which time the rover was driving. Against `a0.3` this cost `warm5` a median of 0-3 s per blocked mission (blocks: 1 faster, 11 slower, p 0.0063; boulevard: 2 faster, 13 slower, p 0.0074). This comes from where the check's cycle falls against a 30 s block, so a block of another length would shift which variant pays. Only one block length was flown.

**R2 (both): the corner tolerance on quiet45.** On quiet45 blocks, both warm-ups (identical there) had a corner `p95_m` of 3.37 m against `a0.3`'s 3.10 m, and a `max_past_m` of 4.41 against 3.68 m. On the other four profiles their `p95_m` was lower than `a0.3`'s, except `warm10` on blocked30 (0.01 m above). `p95_m` is the 95th percentile of 216 corner passes (24 missions × 9 corners), so it moves with a few passes. A warm-up shifts every later moment of a mission by the 6 s recovery move it saves, which changes where the rover is when an outage begins. That a 0.25 m tolerance on this tail figure is tighter than its seed-to-seed spread is a guess. pace-u did not measure that spread. The rule binds as written.

## What the warm-ups did

- **Both removed the false alarm at the start.** With quiet GPS the shipped check made a recovery move about 9 s into 22-24 of 24 missions per course. Neither warm-up made one before 30 s on quiet90, quietdrift90 or quiet45. With the simulator's 1.5 m noise the shipped check fired in 11-14 of 24, and `warm5` in 1 mission (outage90 boulevard, 14.2 s), `warm10` in none.
- **Both were faster with quiet GPS and identical to each other there.** Against `a0.3`, each was faster on all 9 quiet courses (median −6 to −8 s a mission on boulevard and bayside, −2 to −5 s on blocks) and on 2 of 3 outage90 courses, and slower on none of those. On the four outage profiles `warm5` and `warm10` took the same time in every mission but one, because the only verdict they could differ on comes at the start.
- **A blocked rover was caught 5 or 10 s later.** First recovery moves came at a median of 14.2 s (`warm5`) and 19.1 s (`warm10`), against 9.1 s as shipped.
- **pace-t's result held on fresh seeds.** On seeds 373-396 the 10 s warm-up again removed every early false alarm and was slower nowhere against the shipped check. pace-t's two blocked seeds without GPS have no counterpart here: every blocked30 mission kept its GPS until at least 61.7 s.

## Limits

Simulated rovers only (`pace_l.py`'s measured Mini+ profile), so the speeds are upper bounds. Only one block length (30 s, at the start) was flown. A rover stuck mid-route, after a checkpoint stop or after an outage was not flown either. Only 5 s and 10 s warm-ups were tried. Why seed 388's history was cleared at about 11.9 s is inferred from the timings and is being traced. None of this has been driven on a live Mini+.

## Files

`summary.json`, `report.md`, `tests.txt` and `fetched.json` are the job's outputs, unchanged. The study code (`pace_u.py`, `test_pace_u.py`) is published byte for byte as the job ran it. The per-mission record (`runs.jsonl`, 1800 lines, about 4.8 MB) is larger than this repository's 2 MB file limit. A follow-up job flies the same 1800 missions again, checks that the summary comes out identical, and splits the record by profile.
