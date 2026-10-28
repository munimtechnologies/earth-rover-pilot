# colosseum-compat: can earth-rover-pilot run unchanged on RoboColosseum?

Written 2026-10-28, before any flight was run. By MV2 of Munim, Inc.; the plan, code and analysis are made with AI agents. Text CC BY 4.0, code Apache-2.0.

## Why

FrodoBots is building **RoboColosseum** (frodobots-org/robo-colosseum, colosseum-client, colosseum-policy-server, colosseum-router), a service that evaluates robot policies on real robots. Its launch page, merged 2026-10-27, offers "10,000 hours of free evaluation" with an "Apply for free evaluation" form. The form isn't built yet. The Earth Rover Mini+ was added as a body in October 2026. Its trials are GPS-goal (or photo-goal) navigation, with a 300 s default timeout. An operator scores each run 0-4, and a 4 needs the policy to declare done, hold still, arrive, and have no collision, boundary violation or human help.

The bridge `colosseum-rover-sdk-bridge` (colosseum-policy-server PR 4, commit 92098db, merged 2026-10-26) serves the Earth Rovers SDK's local HTTP API on localhost:8000 from the current trial, so "Earth Rovers SDK policies run unchanged". earth-rover-pilot is such a policy. Running on real rovers has been the binding constraint for earth-rover-pilot, the entry for BitRobot's Earth Rover Grand Challenge (GC/01), so this is the first route to real-rover runs that needs no rover of its own.

The bridge as its pull request describes it: `/data` built from navigation_state (latitude, longitude, heading_deg, speed, battery, rpm_1..rpm_4; orientation = heading; rpms as `[[fl, fr, rl, rr, t]]`). `/start-mission` and `/checkpoints-list` give the trial's GPS goal as the only checkpoint, with lat/lon as strings. `/checkpoint-reached` is accepted within 15 m, and the trial then ends. `/control` commands are held for `--horizon` steps. The pull request never mentions a `/data` timestamp, `gps_signal`, `accels`, `GET /status` or `GET /missions`. This check takes the strictest reading and serves none of them.

## What runs

`colosseum_compat.py` replaces `rover_pilot.SdkClient`'s HTTP transport with that contract, served from the pilot's own `SimRover`. The simulator moves like the FrodoBots-2K rovers (`SIM_REAL`: 0.79 m/s at full linear, commands 0.8 s late, GPS 1.5 s behind) and turns left on a positive angular, as a real rover does. Each flight then runs `rover_pilot.main(["--timeout", "300"])`, the command line a real rover runs, with every real-rover default (dead reckoning through gaps, compass smoothing and learning, 16 m lookahead, 10 s stuck warm-up). The simulator's clock replaces the wall clock.

- Goals 40, 80 and 120 m away, on a bearing drawn from the seed; seeds 1-24; GPS noise 1.5 m (the simulator default) and 0.22 m (recorded FrodoBots-2K). That is 144 flights per shape.
- Two shapes per flight: **bridge** (the strict contract above) and **sdk** (the same, plus a `/data` timestamp, `gps_signal` and `GET /status`, like the SDK itself).
- Unit tests check the contract BridgeClient serves, that a flight runs, and that the end of a trial (the bridge's SIGINT) leaves the rover stopped. They run first and must pass.

## Predictions (bridge shape unless said)

- **P1** No flight crashes: `main()` returns 0 or 1 in all 144 bridge flights.
- **P2** The pilot calls only `/data`, `/control`, `/start-mission`, `/checkpoints-list`, `/checkpoint-reached` and `GET /status`. The bridge doesn't serve `/status`, and the pilot then treats telemetry age as unknown.
- **P3** At 40 m and at 80 m, at least 23 of 24 flights per noise level end "mission completed" within 300 s.
- **P4** At 120 m, at least 20 of 24 flights per noise level complete, with a median time of 230-290 s, close to the 300 s trial limit (cruise 0.6 is about 0.47 m/s).
- **P5** Median time is 60-100 s at 40 m and 140-200 s at 80 m.
- **P6** The bridge and sdk shapes give identical results (exit, ok, reason, time, reports, recoveries, accepted, final distance, distance driven) on every paired flight. The simulator's compass changes on every read, so the heading smoother's new-reading rule gives the same answer with or without a timestamp.
- **P7** Completed flights end with the rover's true position a median 6-11 m from the goal in every cell, and within 15 m in at least 95% of them.

## What it decides

- **P1, P2 and P3 hold:** the next documentation release adds a "Running under RoboColosseum" section to the README. It says the pilot runs unchanged under the bridge's documented contract and gives the command. MV2 applies for RoboColosseum's free evaluation once the form is open, saying the policy was written with AI agents.
- **Any of P1-P3 fails:** the cause is traced and fixed in the pilot first, with tests, before any application.
- **P4 fails:** the README says how far a goal can be at the default cruise within a 300 s trial. Nothing changes in the pilot because of this check.
- **P7's median is above 8 m:** the README notes that `--report-radius` can be set lower when a trial is scored on arrival.
- This is a check against a *described* contract, not the bridge's code (no licence is published for it), and it runs in simulation. Only a real trial shows the real bridge's field names, units and timing.
