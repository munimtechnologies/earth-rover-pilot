# pace-w: graded (10 of 11 predictions held; restart not adopted)

MV2 of Munim, Inc. Written with AI agents. CC BY 4.0.

The predictions and rules are in `PREDICTION.md`, committed to main (31389a4) before the job fetched it. The job `pace-w-v1` fetched main at 2026-10-28T01:45:59Z with rover_pilot 0.19.0, and its `fetched.json` records PREDICTION.md's SHA-256 (c3992ae2…) and pace_w.py's (88fc82fa…). All 51 tests passed before anything was flown (`tests.txt`). The study then flew 1296 missions in 1826 s. Every figure below is read from `summary.json` (field names in brackets) or from `report.md`, which prints the same fields.

## The check (R1)

`check`: 7 compared, 7 identical, `different` empty. That is pace-v's four `warm10` missions (outage90 boulevard 397, quiet90 blocks 397, blockedstart boulevard 397, blockedmid boulevard 415) and pace-s's three `restart` missions (outage90 boulevard 338 and 339, quiet90 boulevard 338), each with the same time, recovery-move times and filter restarts as recorded. R1 does not stop the study.

## Predictions

| | prediction | result | held |
|---|---|---|---|
| P1 | check: 7 compared, 7 identical | 7 of 7 identical | yes |
| P2 | all 1296 missions completed | `completed` 1296 | yes |
| P3 | `warm10`: `median_max_m` ≥ 45 m and `over_snap` ≥ 15 on every course of the five 90 s profiles; quiet45 25-45 m | 51.62-63.08 m, `over_snap` 20-24; quiet45 35.35-36.55 m | yes |
| P4 | `restart+warm10`: `median_max_m` ≤ 15 m everywhere; `over_snap` ≤ 4 on quietdrift90, ≤ 1 elsewhere | 10.00-11.37 m; quietdrift90 2, 1, 3; blockedmid 1 per course; 0 elsewhere | yes |
| P5 | `early` 0 for both on outage90, quiet90, quietdrift90, quiet45 | 0 on all 12 courses for both | yes |
| P6 | `groups_faster` ≥ 2 on every profile | 2 of 3 on all six | yes |
| P7 | `groups_slower` and `groups_lost` 0 on every profile | quietdrift90 `groups_slower` 1 (boulevard); `groups_lost` 0 everywhere | **no** |
| P8 | blocked: `eligible` ≥ 12, `missed` ≤ `warm10`'s, `median_catch_s` within 1.0 s | `eligible` 22 on all six courses, `missed` 0 for both; catch 19.1 vs 19.1 s (blockedstart), 16.5 vs 16.6 s (blockedmid) | yes |
| P9 | `median_restarts` 3-9 on every course | 4-7 (quiet45 5.5-7) | yes |
| P10 | blocks corner `p95_m` ≤ `warm10`'s + `corner_tol_m`; `p95_offset_m` ≤ `warm10`'s + `offset_tol_m` | corner p95 lower than `warm10`'s on all six profiles (2.62-4.45 vs 2.78-4.83 m); offset p95 lower on all 18 courses | yes |
| P11 | `corner_spread_m` and `offset_spread_m` 0.25-2.0 m | 0.73 m and 0.77 m (`corner_tol_m` 0.75, `offset_tol_m` 0.8) | yes |

## The miss (P7)

On quietdrift90 boulevard (quiet GPS, a compass error drifting by 10° with a 120 s time scale, the straight course), `restart+warm10` was slower than `warm10` on 14 seeds and faster on 1, with 9 ties: a median of +2.0 s a mission (+0.11%), sign test p = 0.001. On outage90 boulevard it was 2 faster and 4 slower (p = 0.69, not a verdict). On the other four profiles' boulevard courses it was never slower (2-4 seeds faster, the rest tied).

This was the prediction marked most at risk. In pace-u the same pair on quietdrift90 boulevard was 3 faster and 6 slower (p = 0.51). On fresh seeds the lean became a clear verdict. The slowdown did not come from recovery moves: neither variant made a recovery move on any quietdrift90 boulevard mission, and both stood still in 12 missions of 24. Its cause is not traced. The steering tables show only a small difference: mean |angular| 0.0252 against 0.0249, heading error 4.93° against 4.88° at the median.

## Decision (R2)

R2 needs every condition. All but the first held:

- `groups_slower` 0 and `groups_lost` 0 on every profile: **fails** (quietdrift90 boulevard).
- `early` at most 2 of 24 on the four outage profiles: 0 everywhere.
- blocked: `eligible` ≥ 12 (22) and `missed` ≤ `warm10`'s (0 and 0).
- `p95_offset_m` within `warm10`'s + 0.8 m: lower on every course.
- blocks corner `median_past_m` ≥ 0 m (1.90-2.08 m) and `p95_m` within `warm10`'s + 0.75 m (lower on every profile).
- `median_max_m` below `warm10`'s on every course of the five 90 s profiles: 10.0-11.4 m against 51.6-63.1 m.

**`restart+warm10` does not qualify.** A real rover keeps the GPS average across gaps, as v0.19.0 ships it. No release changes the pilot because of this study, and the results are documented only (R3).

## What it means

- Restarting the average after a gap removes the jump after an outage. On the 90 s outage profiles, the median of each mission's worst position error fell from 51.6-63.1 m to 10.0-11.4 m. Without the restart, 20-24 of 24 missions per course were thrown off by more than 20 m; with it, 0-3 were. The restart also held the rover closer to its course (95th-percentile offset lower on all 18 courses).
- It was faster on bayside and blocks on every profile: a median of 0-4 s a mission on bayside and 9-14 s on blocks, where 19-22 of 24 seeds were faster and none slower.
- On the straight course with a drifting compass it costs about 2 s a mission, consistently. Under a rule that allows no slower course, that small, reproducible cost decides it.
- With the stuck check's warm-up in place, restarting no longer causes false recovery moves: none on any outage profile, and blocked rovers were caught exactly as without it.

## Limits

- Simulated rovers only, on the measured Mini+ profile, idealised courses and outages that stop and start cleanly. A real first fix after an outage can be poor. A restart adopts it in full, and how often that happens on a real rover is not measured.
- The boulevard slowdown's mechanism is not traced. A diagnostic like `trace_s.py`, run on the 14 slower seeds, would be needed to say whether it is the drifting compass, the restart's first seconds, or both.
- R2 was written after pace-s, pace-t and pace-u had flown this variant. This grade reads only the fields the rule names, on fresh seeds 445-468 (469-492 for `warm10:B`).
- None of this has been driven on a live Mini+.

## Files

`summary.json`, `report.md`, `fetched.json` and `tests.txt` are the job's outputs as written. `pace_w.py` and `test_pace_w.py` (repository root) are byte for byte the code the job ran (SHA-256 in `fetched.json`). The per-mission record (`runs.jsonl`, about 2.7 MB) is over the repository's 2 MB file limit, so a separate job flies the study again from main and splits it by profile.
