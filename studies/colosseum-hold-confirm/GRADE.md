# colosseum-hold-confirm: grade

Graded 2026-10-29 against `PLAN.md` (committed dfb4066 on 2026-10-29, before any flight). By MV2 of Munim, Inc.; the grading and write-up are made with AI agents. Text CC BY 4.0.

**Result: 5 of 7 predictions held, and C1, the one that decides, held.** On fresh seeds 25-48, `--max-angular 0.3` again completed all 96 stale-telemetry flights with a median time at most 1.5 times live's, and the unchanged pilot again did not. So, as the plan says, the README recommends `--max-angular 0.3` under a 2-3 s cadence. But the margin is smaller than colosseum-hold showed: on 30 m trials stale-m30 took 1.41 and 1.48 times as long as live (1.27 on seeds 1-24), so C4 failed, and at 1.5 m GPS noise its edge over the unchanged pilot was 0.17, not 0.25 (C5 failed).

## The run

- Job `colosseum-hold-confirm-v1`, sealed container, 2026-10-29 15:20-15:24 UTC. Unit tests passed first, then 480 flights in 64 s of wall time (seeds 25-48).
- `fetched.json`: rover_pilot 0.19.1 (sha256 e971e188..., the file colosseum-compat-v1 and colosseum-hold-v1 flew), `colosseum_hold.py` sha256 1d54b068... (`same_as_hold_v1: true`), and `PLAN.md` on main.
- Outputs beside this file: `summary.json`, `runs.jsonl` (one line per flight), `fetched.json`.

## Cells (24 flights each; times are medians over completed flights)

| arm | noise | goal | done | median s | x live | path ratio x live | median recoveries |
|---|---|---|---|---|---|---|---|
| live | 0.22 m | 30 m | 24 | 54.5 | 1.00 | 1.00 | 0 |
| live | 0.22 m | 80 m | 24 | 159.1 | 1.00 | 1.00 | 0 |
| live | 1.5 m | 30 m | 24 | 51.5 | 1.00 | 1.00 | 0 |
| live | 1.5 m | 80 m | 24 | 157.1 | 1.00 | 1.00 | 0 |
| hold | 0.22 m | 30 m | 24 | 65.6 | 1.20 | 1.13 | 0 |
| hold | 0.22 m | 80 m | 24 | 180.1 | 1.13 | 1.12 | 0 |
| hold | 1.5 m | 30 m | 24 | 62.0 | 1.20 | 1.09 | 0 |
| hold | 1.5 m | 80 m | 24 | 184.6 | 1.18 | 1.14 | 0 |
| stale | 0.22 m | 30 m | 24 | 92.95 | **1.71** | 1.53 | 1 |
| stale | 0.22 m | 80 m | 23 | 206.4 | 1.30 | 1.19 | 2 |
| stale | 1.5 m | 30 m | 24 | 84.7 | **1.65** | 1.42 | 1 |
| stale | 1.5 m | 80 m | 24 | 207.45 | 1.32 | 1.21 | 1.5 |
| stale-m30 | 0.22 m | 30 m | 24 | 76.75 | 1.41 | 1.23 | 0.5 |
| stale-m30 | 0.22 m | 80 m | 24 | 179.25 | 1.13 | 1.08 | 1 |
| stale-m30 | 1.5 m | 30 m | 24 | 76.2 | 1.48 | 1.24 | 1 |
| stale-m30 | 1.5 m | 80 m | 24 | 177.3 | 1.13 | 1.09 | 0.5 |
| stale-m15 | 0.22 m | 30 m | 24 | 74.4 | 1.37 | 1.15 | 1 |
| stale-m15 | 0.22 m | 80 m | 24 | 180.35 | 1.13 | 1.05 | 1 |
| stale-m15 | 1.5 m | 30 m | 24 | 76.05 | 1.48 | 1.17 | 1 |
| stale-m15 | 1.5 m | 80 m | 24 | 183.55 | 1.17 | 1.08 | 1 |

The one flight that didn't complete timed out at 300 s (not a crash): a stale flight at 0.22 m / 80 m.

## Predictions

| | Prediction | Outcome | Held |
|---|---|---|---|
| C1 | `passes["stale-m30"]` is true | true: 24 of 24 in every cell, time ratio at most 1.48 | yes |
| C2 | `passes["stale"]` is false | false: 1.71 and 1.65 times live at 30 m | yes |
| C3 | `passes["hold"]` is true | true: 96 of 96, 1.13-1.20 times live | yes |
| C4 | stale-m30's `time_ratio` in [1.05, 1.40] in all four cells | 1.408 and 1.480 at 30 m; 1.127 and 1.129 at 80 m | **no** |
| C5 | in both 30 m cells, stale's `time_ratio` at least 0.25 above stale-m30's | 0.22 m: 1.706 against 1.408 (+0.298); 1.5 m: 1.645 against 1.480 (+0.165) | **no** |
| C6 | stale's `median_recoveries` above stale-m30's in at least 3 of 4 cells | 1 > 0.5, 2 > 1, 1 = 1, 1.5 > 0.5: 3 of 4 | yes |
| C7 | `crashed` is 0 in all 20 cells | 0 crashes in 480 | yes |

## Why C4 and C5 failed

Live flew its 30 m trials a little faster on these seeds (51.5-54.5 s against 53.0-54.0 s on seeds 1-24) and stale-m30 a lot slower (76.2-76.75 s against 67.4-68.3 s), so its 30 m ratio rose from 1.27 to 1.41-1.48. The unchanged pilot under stale telemetry moved the other way at 1.5 m noise (1.84 to 1.65), which is why C5's gap closed. With 24 flights per cell, a 30 m trial's median moves by several seconds between seed sets, and the plan's bands were set from one seed set. On 80 m trials all three numbers repeated closely (stale-m30 1.10-1.15 before, 1.13 now; stale 1.20-1.25 before, 1.30-1.32 now).

Read honestly, the two seed sets together say: under stale 2-3 s telemetry, `--max-angular 0.3` completes every trial and costs 10-48% in time against live telemetry, where the unchanged pilot costs 20-84% and makes about one extra recovery move a flight. The saving is clear on 30 m trials at 0.22 m noise (both seed sets) and smaller but in the same direction at 1.5 m noise. stale-m15 again flew almost the same as stale-m30, so the choice between 0.3 and 0.15 is still not a finding.

## What it decides (PLAN.md, applied as written)

C1 holds, so the README's "Running under RoboColosseum" section recommends `--max-angular 0.3` when the bridge refreshes telemetry only at its observations, with both seed sets' numbers (1.10-1.48 times live, every trial completed) and the caveat that this is simulation of a described cadence. The pilot's default stays 1.0, and the pilot code doesn't change. `decision` in `summary.json` is R2 / stale-m30 again; as the plan says, it is reported but not used.

## Limits

- This checks one line of a pull request's description of the bridge's timing, not the bridge's code (no licence is published for it, so none of its code is used). The real cadence, and whether `/data` really refreshes only at observations, may differ.
- Simulation only. The simulator yaws 60 deg/s at full angular. FrodoBots-2K's Earth Rover Zero turned about 30 deg/s per unit in place (`studies/frodo-spin`), and the Mini+ is said to turn about 48. On a rover that turns slower, 0.3 bounds each held command more tightly than it did here.
- Only existing flags were tried.

Reproduce: `python fetch_deps.py && python -m unittest -v test_colosseum_hold && python colosseum_hold.py --out-dir out --seeds 24 --first-seed 25` in `studies/colosseum-hold-confirm/` (fetch_deps.py downloads the study code from main).
