# colosseum-hold-confirm: does `--max-angular 0.3` still pass on fresh seeds?

Written 2026-10-29, before any flight was run. By MV2 of Munim, Inc.; the plan, code and analysis are made with AI agents. Text CC BY 4.0, code Apache-2.0.

## Why

`studies/colosseum-hold` (GRADE.md, 5 of 7 predictions held) flew earth-rover-pilot 0.19.1 behind a simulated RoboColosseum bridge that samples the pilot's command every 2-3 s and holds it. Its decision rule picked **R2, stale-m30**: with stale telemetry (`/data` refreshed only at each 2-3 s observation), the unchanged pilot took 1.66-1.84 times as long as live on 30 m trials, and `--max-angular 0.3` brought that to 1.10-1.27 times while completing all 96 flights. The plan said the chosen arm is flown again on fresh seeds 25-48 before the README recommends that flag for RoboColosseum. This is that flight.

## What runs

Exactly `studies/colosseum-hold/colosseum_hold.py` from main, unchanged, with `--first-seed 25 --seeds 24`: the same five arms (live, hold, stale, stale-m30, stale-m15), goals 30 m and 80 m, GPS noise 0.22 m and 1.5 m, 480 flights. `fetch_deps.py` downloads the study's code and tests from main, so the code is main's by construction, and records whether this PLAN.md is on main. The unit tests run first and must pass.

## Predictions (seeds 25-48; read from `summary.json`)

- **C1** stale-m30 passes: `passes["stale-m30"]` is true (every cell at least 23 of 24 completed, median time at most 1.5 times live's).
- **C2** stale fails again: `passes["stale"]` is false.
- **C3** hold passes again: `passes["hold"]` is true.
- **C4** stale-m30's `time_ratio` is between 1.05 and 1.40 in all four cells.
- **C5** In both 30 m cells, stale's `time_ratio` is at least 0.25 higher than stale-m30's.
- **C6** In at least 3 of 4 cells, stale's `median_recoveries` is higher than stale-m30's.
- **C7** No flight crashes: `crashed` is 0 in all 20 cells.

## What it decides

- **C1 holds:** the README's "Running under RoboColosseum" section recommends `--max-angular 0.3` when the bridge refreshes telemetry only at its observations, with both studies' numbers and the caveat that this is simulation of a described cadence. The pilot's default stays 1.0.
- **C1 fails:** the README states the cadence finding without recommending a flag, and a steering mode built for a sampled, held command gets its own pre-registration and fresh seeds.
- `decision` in the new summary is reported but not used: its R2 tie-break between 0.3 and 0.15 was within noise in colosseum-hold.

## Limits

As in colosseum-hold: a described cadence, not the bridge's code (no licence is published for it, so none of its code is used); simulation only, with a 60 deg/s simulator against the Mini+'s reported 48 deg/s; existing flags only.
