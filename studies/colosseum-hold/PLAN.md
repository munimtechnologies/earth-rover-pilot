# colosseum-hold: does earth-rover-pilot still steer when RoboColosseum's bridge takes a command only every 2-3 s?

Written 2026-10-28, before any flight was run. By MV2 of Munim, Inc.; the plan, code and analysis are made with AI agents. Text CC BY 4.0, code Apache-2.0.

## Why

FrodoBots' RoboColosseum evaluates robot policies on real robots, and the Earth Rover Mini+ is being added. Its `colosseum-rover-sdk-bridge` serves the Earth Rovers SDK API to an unchanged SDK program, and earth-rover-pilot is such a program. `studies/colosseum-compat` (filed the same day, not yet run) checks the pilot against the bridge's endpoints and fields. Like the bridge's first pull request, it passes every `/control` straight to the rover.

A later pull request in the same repository describes the timing. It is frodobots-org/colosseum-policy-server #8, "GeNIE baseline for the Earth Rover track", opened 2026-10-27 and still open. It says "the bridge answers each observation, every 2-3 s, with the command current at that instant", so "advances hold until the next plan, and in-place turns last until an observation has sampled them". It also says its own first two real-rover trials "showed both problems before the fix". Those trials ran on the Wuhan mission 1, checkpoint 1 to 2, about 27-32 m.

earth-rover-pilot sends a command every 0.1 s. While driving, it turns `kp * error` with kp = 1/60 per degree, clamped to `max_angular` (1.0 on a real rover). Above a 90° error it turns in place with the same clamped command. The simulator yaws 60°/s at full angular, so a command held for T seconds turns the rover by about `error * T` degrees. For T = 2-3 s that is 2-3 times the error, so each held turn overshoots and the next sample starts from the other side. Only the clamp bounds the swing: one hold turns at most `60 * max_angular * T` degrees, 120-180° at max_angular 1.0. A smaller `--max-angular` (an existing flag) bounds each hold's turn at the cost of slower turns. Commands also reach the rover 0.8 s late (`SIM_REAL`).

## What runs

`colosseum_hold.py` extends `colosseum_compat.BridgeClient` (fetched from main) and flies `rover_pilot.main(["--timeout", "300", ...])` exactly as `colosseum_compat.fly` does. Five arms:

- **live**: `colosseum_compat`'s bridge shape unchanged. It is the control arm, and the tests check that it matches `colosseum_compat.fly` exactly.
- **hold**: `/control` is stored. At each observation, every U(2, 3) s, the latest command is taken, and the rover receives it on every simulator step until the next observation. `/data` stays live.
- **stale**: as hold, plus `/data` is the observation's telemetry, refreshed only at each observation. This is the most literal reading of "answers each observation".
- **stale-m30** and **stale-m15**: stale with `--max-angular 0.3` or `0.15`. These are the candidate fixes. They need no code change.

The flights use goals 30 m away (about the GeNIE trials) and 80 m away, with GPS noise of 1.5 m and 0.22 m and seeds 1-24. That is 96 flights per arm, 480 in all. One observation cadence per (seed, distance, noise) is shared by every held arm. The record keeps completions, time, final true distance, the path ratio (distance driven divided by goal distance), recoveries, and turn-side flips (held turns that change side; live counts every command, so flips are descriptive only).

## Predictions

- **H1** live: at least 23 of 24 flights complete within 300 s in each of its 4 cells. Its 80 m flights equal colosseum-compat-v1's bridge flights for the same seed and noise (exit, ok, reason, time, final distance, distance driven). That half is graded when colosseum-compat-v1 has results.
- **H2** hold: fewer than 23 of 24 complete in at least 3 of its 4 cells.
- **H3** stale completes no more flights in total than hold.
- **H4** In at least 3 of 4 cells, both hold and stale have a median path ratio, over completed flights, at least 1.2 times live's. A cell with fewer than 5 completions counts as meeting this.
- **H5** At least one of stale-m30 and stale-m15 completes at least 23 of 24 in every cell.
- **H6** That arm's median time is at most 1.5 times live's in every cell.
- **H7** No flight in any arm crashes: `main()` returns 0 or 1 in all 480.

## What it decides (computed by `summarise()` as `decision`)

An arm **passes** when every one of its 4 cells has at least 23 of 24 completed and a median time at most 1.5 times live's in the same cell.

- **R1** hold and stale both pass: the pilot runs unchanged under the described cadence. The README's "Running under RoboColosseum" section says so, with the cadence as a caveat.
- **R2** otherwise, a fix arm passes: the one with the lower total of median times is chosen. It is flown again on fresh seeds 25-48 (colosseum-hold-confirm) before the README recommends that `--max-angular` for RoboColosseum. The pilot code does not change.
- **R3** neither: the next step is a steering change in the pilot for a sampled, held command, for example a gain matched to the hold period. It gets its own pre-registration and fresh seeds.

## Limits

- This checks a pull request's one-line description of the timing, not the bridge's code. The bridge publishes no licence, so its code is not copied here. The real cadence, and whether /data is really refreshed only at observations, may differ.
- It is simulation. The Mini+ is said to yaw about 48°/s at full angular, not the simulator's 60, so real overshoots would be about a fifth smaller.
- It tests the pilot's existing flags only. A pilot designed for a 2-3 s cadence could do better than any arm here.
