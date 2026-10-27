# pace-v: grade

MV2 of Munim, Inc. Written with AI agents. CC BY 4.0.

This grade reads only the output fields of the `pace-v-v1` job (`summary.json`, `report.md`, `tests.txt` and `fetched.json` in this folder) and checks them against `PREDICTION.md`. That file was on main before any mission was flown: `fetched.json` records its SHA-256 (008411e5…) and the time the job fetched main (2026-10-27 15:35 UTC). The job ran `pace_v.py` 0.1.0 (SHA-256 79ad43ed…) on rover_pilot.py 0.18.6, with `pace_u.py` (916fd5e8…) and `pace_t.py` (3c89c187…) as pre-stated. `test_pace_v`, `test_pace_u` and `test_pace_t` ran 66 tests, and all passed (`tests_exit` 0). The 1728 missions took 48 minutes.

**10 of 11 predictions held, and R1 passed. Under the pre-stated rule R2, both warm-ups qualify. `warmstand10` was slower than `warm10` on 4 blocked courses, so a real rover gets `warm10`: no stuck verdict until 10 s after the stuck history was last cleared.** v0.19.0 adds `Pilot.stuck_warmup_s`. Its default of 0 keeps today's verdicts, so the simulator and every earlier study fly as before. The command line gives a real rover's pilot 10 s. The one miss (P11) was a guess about noise, and it decides nothing.

## Predictions

| | prediction | result | |
|---|---|---|---|
| P1 | check against pace-u: 8 compared, 8 identical | 8, 8 | held |
| P2 | all 1728 missions completed | 1728 of 1728 | held |
| P3 | `a0.3` on quiet90, quietdrift90, quiet45: `early` ≥ 20 of 24 on every course | 22-23 | held |
| P4 | `early` 0 for `warm10` and ≤ 1 for `warmstand10` on every course of outage90, quiet90, quietdrift90, quiet45 | 0 for both on all 12 courses | held |
| P5 | `blockedstart`, every variant and course: `eligible` ≥ 20; `missed` 0 for `a0.3` and `warmstand10`, ≤ 2 for `warm10` | `eligible` 20 (24 for `a0.3:B`); `missed` 0 everywhere | held |
| P6 | `blockedstart` `median_catch_s`: `a0.3` ≤ 11.5; `warm10` and `warmstand10` 18.5-21.5 | 9.1; 19.1 and 19.1 on every course | held |
| P7 | `blockedmid`, every variant and course: `eligible` ≥ 12, `median_catch_s` 12-26; `missed` ≤ 1 for `a0.3` and `warmstand10` | `eligible` 21; 16.6-16.8 s; `missed` 0 everywhere | held |
| P8 | `blockedstart` `post` summed over courses: `warm10` < `a0.3`, and `warmstand10` ≥ `warm10` | `a0.3` 30, `warm10` 6, `warmstand10` 27 | held |
| P9 | `warm10` and `warmstand10` faster than `a0.3` on every course of quiet90, quietdrift90, quiet45 | `groups_faster` 3 on each | held |
| P10 | against `a0.3`: `groups_slower` and `groups_lost` 0 for both on outage90, quiet90, quietdrift90, quiet45 | 0 and 0 | held |
| P11 | `corner_spread_m` > 0.25 and `offset_spread_m` ≤ 0.5 | 0.94; **1.40** | **missed** |

## The decision rules

- **R1 passed.** The 8 pace-u missions flown again (three of them blocked30 missions flown through pace-v's own block) matched their records exactly.
- **Tolerances**, set by the formula fixed in advance: `corner_tol_m` 0.95 (spread 0.94, blockedmid) and `offset_tol_m` 1.40 (spread 1.40, outage90 bayside: 4.28 m for `a0.3` against 2.88 m for `a0.3:B`).
- **R2: `warm10` qualifies.** Against `a0.3`, `groups_slower` and `groups_lost` were 0 on all six profiles. `early` was 0 on every course of the four outage profiles. On both blocked profiles `eligible` was 20 or 21 and `missed` was 0, the same as `a0.3`'s 0. Its `p95_offset_m` was at most 0.78 m above `a0.3`'s (outage90 boulevard, 4.38 against 3.60 m), within 1.40. Its blocks corner `p95_m` was at most 0.84 m above (outage90, 4.26 against 3.42 m), within 0.95, and its `median_past_m` was 1.94-2.30 m.
- **R2: `warmstand10` qualifies.** It met every condition by the same margins. Against `a0.3` on blockedstart it was neither faster nor slower on any course. Its `median_past_m` was 1.97-2.30 m.
- **Both qualify, so the rule compares `warmstand10` with `warm10`.** `warmstand10` had `groups_slower` 1 on blockedmid (boulevard: 1 seed faster, 8 slower, p 0.039) and 3 on blockedstart (p 0.0039, 0.0034 and 0.0215), so a real rover gets `warm10`. Under R2, v0.19.0 adds `stuck_warmup_s` (default 0). `stuck_stand_s` belongs only to `warmstand10`, so it is not added. A test checks that `Pilot`'s own warm-up matches `pace_v._warming`'s `warm10` verdicts.
- **R3:** this grade, the outputs and the code are published here.

## What the miss was

**P11: the offset figure is noisier than predicted.** Flown twice, on two disjoint seed sets, the shipped pilot's 95th-percentile distance from the course differed by up to 1.40 m on one course (outage90 bayside, with the simulator's 1.5 m GPS noise). The prediction had expected at most 0.5 m. Quiet GPS did not make it steady: the two sets differed by at most 0.55 m on quiet90, but by 1.18 m on blockedmid bayside and 1.08 m on quietdrift90 boulevard. The corner figure's spread was 0.94 m, far above the 0.25 m pace-u had allowed. That 0.25 m was what failed both of pace-u's warm-ups by 0.02 m, so the tolerance that sank them was well inside the seed-to-seed noise. Because the formula took the tolerances from this measured spread, R2's distance conditions were loose this time. The warm-ups' largest excesses (0.78 m offset, 0.84 m corner) were smaller than the shipped pilot's own difference between its two seed sets.

## What the warm-ups did

- **Both removed the false alarm at the start, again.** With quiet GPS the shipped check made a recovery move about 9 s in, in 22-23 of 24 missions per course (`a0.3:B`: 24 of 24). Neither warm-up made one before 30 s on any of the four outage profiles. Neither made a single recovery move on quiet90, quiet45 or outage90. On quietdrift90 blocks each made one, at 1021.9 s.
- **Both were faster.** Against `a0.3` each was faster on every course of quiet90, quietdrift90, quiet45 and blockedmid (paired sign test p < 0.05; median 0 to −7 s a mission) and on 2 of 3 outage90 courses. `warm10` was also faster on all 3 blockedstart courses. Neither was slower on any course of any profile.
- **A rover blocked at the start was caught 10 s later; a rover blocked mid-route was caught as fast.** On blockedstart the first move came at a median 19.1 s with either warm-up, against 9.1 s. On blockedmid every variant caught the block at a median 16.6-16.8 s (latest 18.8 s, `a0.3:B` 22.6 s). Mid-route nothing clears the history when the block begins, so no warm-up runs. The catch waits for the lagging GPS average to close on the stopped rover, as P7's reasoning expected. No eligible blocked mission was missed by any variant.
- **Why `warm10` beat `warmstand10` on the blocked profiles.** `warmstand10` keeps no warm-up after a recovery move, so while blocked it judges again every 15.1 s, as the shipped check does. `warm10` starts its warm-up again after each move and judges every 25.1 s. A simulated block can't be escaped by a recovery move, so each extra move only cost time. On blockedstart `warmstand10` made 56 moves per course against `warm10`'s 35 (`a0.3`: 73). It also made 9 moves per course in the 10 s after the block had ended, against `warm10`'s 2, when the lagging average still showed less than 1.5 m though the rover was free. pace-u found that lag (`studies/pace-u/TRACE.md`). On blockedmid the counts were 63 against 42, with 10 against 5 moves after the block. This is what P8 predicted, and it decided R2.
- **The stand rule fixed what it was built for, but it wasn't needed.** No eligible blocked mission was missed by `warm10` either. With block lengths drawn per seed, the late catch that pace-u's seed 388 showed did not happen here.

## Limits

Simulated rovers only (`pace_l.py`'s measured Mini+ profile), so the speeds are upper bounds. A block here is a rover that can turn but cannot move, and it lasts 30-60 s whatever the rover does. On a real snag a recovery move may free the rover. There, `warm10`'s slower retry cadence (25.1 s against 15.1 s while stuck) could cost time instead of saving it. How often a real Mini+ gets stuck, and whether backing up frees it, is not measured. With `warm10` a rover stuck at the very start is first helped about 19 s in, instead of about 9 s. Only one warm-up length (10 s) and one stand threshold (3 s) were flown. The tolerances came out loose because the tail figures they guard are noisy, so R2's distance conditions screened only for large changes. None of this has been driven on a live Mini+.

## Files

`summary.json`, `report.md`, `tests.txt` and `fetched.json` are the job's outputs, unchanged. The study code (`pace_v.py`, `test_pace_v.py`) is published byte for byte as the job ran it. The per-mission record (`runs.jsonl`, 1728 lines, about 4.7 MB) is over this repository's 2 MB file limit. A follow-up job flies the same missions again, checks that the summary comes out identical, and splits the record by profile.
