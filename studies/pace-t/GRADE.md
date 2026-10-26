# pace-t: grade

MV2 of Munim, Inc. Written with AI agents. CC BY 4.0.

Graded strictly from the output fields of the `pace-t-v1` job (`summary.json`, `report.md`, `tests.txt`, `fetched.json` in this folder) against `PREDICTION.md`, which was on main before any mission was flown (`fetched.json` records its SHA-256, 2511682a…, and the time the job fetched main, 2026-10-26 08:27 UTC). The job ran `pace_t.py` 0.1.0 (SHA-256 3c89c187…) on rover_pilot.py 0.18.5, with `pace_s.py` (343feeb8…) and pace-s's record (180cd541…) as pre-stated. `test_pace_t` and `test_pace_s`: 35 tests, all passed. 1080 missions in 31 minutes.

**8 of 10 predictions held. R1 passed. By the pre-stated rule R2 the warm-up does not qualify, so a real rover keeps today's stuck check. R3 is not reached.** v0.18.6 documents the result and changes no code.

## Predictions

| | prediction | result | |
|---|---|---|---|
| P1 | check: 18 compared, 18 identical, 0 missing | 18, 18, 0 | held |
| P2 | all 1080 missions completed | 1080 of 1080 | held |
| P3 | `a0.3` on quiet90, quietdrift90, quiet45: `with_recovery` ≥ 20 and `early` ≥ 20 of 24 on every course | `with_recovery` 22-24, `early` 22-23 | held |
| P4 | `warm` on outage90, quiet90, quietdrift90, quiet45: `with_recovery` ≤ 2 of 24 on every course | 0 on 11 of 12 courses; **3 on quietdrift90 blocks** | **missed** |
| P5 | `restart+warm` on the same: `with_recovery` ≤ 2 of 24 on every course | 0 on 11 courses, 2 on quietdrift90 blocks | held |
| P6 | blocked30: `early` 24 of 24 for every variant and course | **`a0.3` 23, `warm` 22, `restart+warm` 22 on every course** | **missed** |
| P7 | `warm` faster than `a0.3` (p < 0.05) on every course of quiet90, quietdrift90, quiet45, `median_time_diff_share` in [−0.01, 0] | faster on all 9 (p 0.0001-0.0074); shares −0.0042 to 0 | held |
| P8 | `warm`'s `groups_slower` and `groups_lost` 0 on every profile | 0 and 0 on all 5 | held |
| P9 | `restart+warm` against `warm`: `groups_slower` and `groups_lost` 0 on every profile | 0 and 0 on all 5 | held |
| P10 | `restart+warm`: `median_max_m` ≤ 15 m on every course of the four outage profiles; `over_snap` ≤ 2 on outage90, quiet90, quiet45 | 9.91-12.13 m; `over_snap` 0 on all 9 | held |

## The decision rules

- **R1 passed.** The 18 pace-s missions flown again were identical in every field.
- **R2: `warm` does not qualify.** Against `a0.3` it met every condition but one: `groups_slower` 0 and `groups_lost` 0 on every profile; `p95_offset_m` at most 0.37 m above `a0.3`'s on any course (quietdrift90 blocks 6.99 against 6.62 m, outage90 bayside 3.23 against 2.87 m; it was lower on 9 of 15 courses); blocks corner `median_past_m` 2.00-2.37 m (≥ 0) and corner `p95_m` at most 0.07 m above `a0.3`'s (quiet90, 2.59 against 2.52 m). The condition it failed: on blocked30 its `early` was 22 of 24 on every course, and the rule asked for 24. So a real rover keeps today's stuck check, and v0.18.6 changes documentation only.
- **R3 is not reached**, because it needs `warm` to qualify. For the record only: against `warm`, `restart+warm` met every one of its own conditions (`groups_slower` 0 and `groups_lost` 0 on every profile, `p95_offset_m` lower on all 15 courses, blocks corner `p95_m` at most 0.12 m above `warm`'s and `median_past_m` 1.90-2.37 m, and `median_max_m` 9.91-12.13 m against `warm`'s 35.45-63.35 m on every course of the four outage profiles). That does not change the rule's outcome. A real rover keeps the GPS average across gaps.

## What the misses were

**P6 and R2: two blocked missions with no recovery move, and no time lost.** The six blocked30 missions on each course with no recovery move before 30 s were the same two seeds on all three courses: seed 352 for every variant and seed 368 for `warm` and `restart+warm` (`runs.jsonl`). In the boulevard missions of those seeds read in full (and in seed 352's quiet90 boulevard mission), the rover stood still for 88.5 s (`time_s.stopped`) and the dead reckoner was trusted only from 146-176 s. That fits a 90 s GPS outage that began while the rover was blocked, before the reckoner could bridge it: the pilot stops when it has neither a fix nor a trusted reckoner, and clears the stuck history while it stands. The outage start is inferred, because pace-t does not record it. On seed 352 even the shipped check gave no verdict, so the outage began before 9.1 s. That seed's shipped quietdrift90 blocks mission (the same outage windows) made its first recovery move at 805.9 s, not 9.1 s. On seed 368 the shipped check fired at 9.1 s, and the warm-up's verdict was due at about 19 s, so the outage began between about 9 s and 19 s. The block (30 s) was over before the fixes came back. Not being "caught" cost those missions nothing. On boulevard, seed 368 took 1845.6 s both with the shipped check's recovery move and without one (`warm`), and seed 352 took 1837.6 s for both `a0.3` and `warm`.

So P6 and R2 asked for a recovery move in every blocked mission, and a mission whose GPS is out while it is blocked cannot make one and does not need one. That was a flaw in how the prediction and the rule were written, not a stuck rover left uncaught: in every blocked mission whose GPS stayed up, the warm-up caught the rover at 19.1-21.1 s (`median_first_s` 19.1, `latest_first_s` 21.1; as shipped 9.1-11.1 s). The rule still binds as written. pace-u (pre-registered next, on fresh seeds) tests the warm-up again with the blocked condition restricted to missions whose first outage begins after the block ends, and records each mission's first outage start.

**P4: three late recovery moves on quietdrift90 blocks, also made as shipped.** `warm`'s three quietdrift90 blocks missions with a recovery move made it at 805.9 s (seed 352), 1434.0 s (358) and 1470.0 s (359), long after any start. The shipped pilot made a recovery move in the same three missions at 805.9, 1436.0 and 1470.0 s, and one more on seed 351 at 549.9 s. `restart+warm` made one on seeds 352 (793.9 s) and 358 (1420.0 s). The warm-up did not add these. It removed one of the four, and P4 counted missions, not new false alarms. Their cause is not traced yet: the simulator never blocks the rover in these profiles, and they come only with the drifting compass on the course with right-angle corners. A drifting heading that makes the rover lose ground near a corner for 10 s is a guess, not a finding.

## What the warm-up did

- **It removed the false alarm at the start.** With quiet GPS the shipped check fired a median 9.1 s into 22-23 of 24 missions per course (quiet90, quietdrift90, quiet45). `warm` made no recovery move before 30 s in any of its 288 missions on the four outage profiles. `restart+warm` made none in 288 either. With the simulator's 1.5 m noise the shipped check fired in 8-9 of 24 per course, and both warm variants in none.
- **It was a little faster and never slower.** `warm` against `a0.3`: faster on all 9 courses of the quiet profiles (median −4 to −6 s on boulevard and bayside, 0 s on blocks, where 10-11 seeds were faster and none slower), faster on 1 of 3 outage90 courses and 2 of 3 blocked30 courses, slower on none. Median made good on quiet90 went from 0.877 to 0.881 m/s. One quiet90 boulevard mission (seed 349) took 1839.6 s as shipped and 1745.6 s with the warm-up, which looks like seed 338's 94 s in pace-s: a recovery move that leaves the rover short of a checkpoint when an outage begins. It is not traced.
- **It caught a blocked rover 10 s later.** On blocked30 the first recovery move came at 19.1-21.1 s, against 9.1-11.1 s as shipped. The shipped pilot made 48 recovery moves per course, two in most missions, because it was called stuck again after its first move while the rover was still blocked. `warm` made 22, one per caught mission.
- **The restart, measured against the warm-up.** With the warm-up, `restart` was faster than `warm` on 2 of 3 courses of every profile (blocks, median −0.31% to −0.56%; bayside, median 0 to −0.14%) and slower on none. The one course where it had lost in pace-s, outage90 boulevard, gave 0 faster and 2 slower (p 0.5). It removed the post-outage jump (each mission's largest position error 9.9-12.1 m against 35-63 m). trace-s's explanation, that the restart's boulevard cost came from false recovery moves, fits this result, but R3 decides nothing because R2 failed.

## Limits

Simulated rovers only (`pace_l.py`'s measured Mini+ profile), so the speeds are upper bounds. In these profiles the only time anything stops the rover is blocked30's first 30 s. A rover stuck mid-route (a kerb, a bush, a wheel in a gap), right after a checkpoint stop or after an outage is where a warm-up delays the catch, and that was not flown. Only a 10 s warm-up was tried. The outages are idealised. None of this has been driven on a live Mini+.

## Files

`summary.json`, `report.md`, `tests.txt` and `fetched.json` are the job's outputs, unchanged. The study code (`pace_t.py`, `test_pace_t.py`) is published byte for byte as the job ran it. The per-mission record (`runs.jsonl`, 1080 lines) is larger than this repository's 2 MB file limit. A follow-up job flies the same 1080 missions again, checks that the summary comes out identical, and splits the record by profile for publishing.
