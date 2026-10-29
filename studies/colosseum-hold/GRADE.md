# colosseum-hold: grade

Graded 2026-10-29 against `PLAN.md` (committed 9a1cbd8 on 2026-10-28, before any flight). By MV2 of Munim, Inc.; the grading and write-up are made with AI agents. Text CC BY 4.0.

**Result: 5 of 7 predictions held, and the decision rule picked R2 with `--max-angular 0.3`.** The pilot coped with a command sampled and held every 2-3 s much better than predicted. What hurt was stale telemetry: when `/data` also refreshes only every 2-3 s, short trials took 1.66-1.84 times as long. Lowering `--max-angular` to 0.3 brought that back to 1.10-1.27 times. Under the plan, this is checked again on fresh seeds 25-48 before the README recommends it.

## The run

- Job `colosseum-hold-v1`, sealed container, 2026-10-29 07:17-07:23 UTC. Unit tests passed first, then 480 flights in 64.1 s of wall time.
- `fetched.json`: rover_pilot 0.19.1 (sha256 e971e188..., the same file colosseum-compat-v1 flew), `PLAN.md` on main, and `colosseum_hold.py` identical to main's copy (`same_as_main: true`).
- Outputs beside this file: `summary.json`, `runs.jsonl` (one line per flight), `fetched.json`.

## Cells (24 flights each; times are medians over completed flights)

| arm | noise | goal | done | median s | x live | path ratio x live | median recoveries |
|---|---|---|---|---|---|---|---|
| live | 0.22 m | 30 m | 24 | 54.0 | 1.00 | 1.00 | 0 |
| live | 0.22 m | 80 m | 24 | 159.1 | 1.00 | 1.00 | 0 |
| live | 1.5 m | 30 m | 24 | 53.0 | 1.00 | 1.00 | 0 |
| live | 1.5 m | 80 m | 24 | 158.6 | 1.00 | 1.00 | 0 |
| hold | 0.22 m | 30 m | 24 | 61.5 | 1.14 | 1.11 | 0 |
| hold | 0.22 m | 80 m | 24 | 181.1 | 1.14 | 1.12 | 0 |
| hold | 1.5 m | 30 m | 24 | 60.0 | 1.13 | 1.08 | 0 |
| hold | 1.5 m | 80 m | 24 | 182.1 | 1.15 | 1.12 | 0.5 |
| stale | 0.22 m | 30 m | 24 | 89.5 | **1.66** | 1.48 | 1 |
| stale | 0.22 m | 80 m | 23 | 190.9 | 1.20 | 1.13 | 1 |
| stale | 1.5 m | 30 m | 24 | 97.5 | **1.84** | 1.60 | 1.5 |
| stale | 1.5 m | 80 m | 24 | 198.8 | 1.25 | 1.17 | 1 |
| stale-m30 | 0.22 m | 30 m | 24 | 68.3 | 1.27 | 1.18 | 0 |
| stale-m30 | 0.22 m | 80 m | 24 | 175.45 | 1.10 | 1.07 | 0.5 |
| stale-m30 | 1.5 m | 30 m | 24 | 67.4 | 1.27 | 1.15 | 0 |
| stale-m30 | 1.5 m | 80 m | 24 | 181.6 | 1.15 | 1.08 | 1 |
| stale-m15 | 0.22 m | 30 m | 24 | 68.3 | 1.27 | 1.15 | 0 |
| stale-m15 | 0.22 m | 80 m | 24 | 180.95 | 1.14 | 1.05 | 1 |
| stale-m15 | 1.5 m | 30 m | 24 | 63.6 | 1.20 | 1.09 | 0 |
| stale-m15 | 1.5 m | 80 m | 23 | 182.8 | 1.15 | 1.05 | 1 |

The two flights that didn't complete both timed out at 300 s (exit 1, not a crash): one stale flight at 0.22 m / 80 m and one stale-m15 flight at 1.5 m / 80 m.

## Predictions

| | Prediction | Outcome | Held |
|---|---|---|---|
| H1 | live: at least 23 of 24 in every cell, and its 80 m flights equal colosseum-compat-v1's bridge flights | 24 of 24 in all four cells. All 48 live 80 m flights match compat's bridge flights for the same seed and noise on exit, ok, reason, time, final distance and distance driven | yes |
| H2 | hold: fewer than 23 of 24 in at least 3 of 4 cells | hold completed 24 of 24 in all four cells | **no** |
| H3 | stale completes no more flights in total than hold | stale 95, hold 96 | yes |
| H4 | in at least 3 of 4 cells, both hold and stale have a path ratio at least 1.2 times live's | hold's path ratio was 1.08-1.12 times live's in every cell, so no cell qualifies | **no** |
| H5 | stale-m30 or stale-m15 completes at least 23 of 24 in every cell | both do (stale-m30 24 in all four) | yes |
| H6 | that arm's median time is at most 1.5 times live's in every cell | stale-m30 1.10-1.27, stale-m15 1.14-1.27 | yes |
| H7 | no flight crashes in any arm | 0 crashes in 480 | yes |

## Why H2 and H4 failed

The plan reasoned that a held turn of `error/60` at 60 deg/s turns 2-3 times the heading error, so each hold overshoots and the next sample starts from the other side. That may hold for a single in-place turn, but a likely reason it didn't matter over a whole flight (not traced in this study) is that the pilot's 16 m lookahead keeps heading errors small while it drives, so a 2-3x overshoot of a few degrees costs little. Holding cost about 14% in time and 8-12% in path, not a failed trial. The plan overrated the hold and underrated stale telemetry. With stale `/data`, the pilot steers on a position and heading up to 3 s old (plus the simulator's 1.5 s GPS lag), its stuck detector fires about once a flight (median recoveries 1-1.5, against 0 for live and hold), and short 30 m trials take 66-84% longer. Lowering `--max-angular` bounds how far one held command can swing the rover: at 0.3, one 3 s hold turns at most about 54°, close to the 45° per answered turn that the GeNIE baseline's notes report on a real rover.

## What it decides (PLAN.md, applied as written)

`passes`: live yes, hold yes, stale **no** (time 1.66 and 1.84 times live's at 30 m), stale-m30 yes, stale-m15 yes. R1 needs both hold and stale to pass, so it doesn't apply. **R2**: of the two passing fix arms, stale-m30 has the lower total of median times (492.75 s against 495.65 s), so `decision` is `{"rule": "R2", "arm": "stale-m30"}`. As the plan says, stale-m30 is flown again on fresh seeds 25-48 (`studies/colosseum-hold-confirm`) before the README recommends `--max-angular 0.3` for RoboColosseum. The pilot code doesn't change.

Note that stale-m30's margin over stale-m15 (2.9 s across four cells) is far smaller than the seed-to-seed spread, so the choice between 0.3 and 0.15 is a tie-break, not a finding.

## Limits

- This checks one line of a pull request's description of the bridge's timing, not the bridge's code (no licence is published for it, so none of its code is used). The real cadence, and whether `/data` really refreshes only at observations, may differ.
- Simulation only. The simulator yaws 60 deg/s at full angular; the Mini+ is said to yaw about 48.
- Only existing flags were tried. A pilot built for a 2-3 s cadence could do better than any arm here.

Reproduce: `python fetch_deps.py && python -m unittest -v test_colosseum_hold && python colosseum_hold.py --out-dir out --seeds 24` in `studies/colosseum-hold/`.
