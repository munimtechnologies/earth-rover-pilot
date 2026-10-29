# colosseum-rate: is `--max-angular 0.3` still right on a rover that turns as slowly as a real one?

Written 2026-10-29, before any flight was run. By MV2 of Munim, Inc.; the plan, code and analysis are made with AI agents. Text CC BY 4.0, code Apache-2.0.

## Why

The README's "Running under RoboColosseum" section recommends `--max-angular 0.3` when RoboColosseum's bridge samples the pilot's command every 2-3 s, holds it, and refreshes `/data` only at those observations ("stale" telemetry). That rests on `studies/colosseum-hold` and `studies/colosseum-hold-confirm`, both flown in a simulator that turns **60°/s** at full `angular`, where one 2.5 s hold at 0.3 turns the rover 45°.

`studies/frodo-spin/GRADE-v2.md` has since measured recorded Earth Rovers turning in place at **23.4°/s per unit** (95% CI 20.5-26.6, 297 turns), and the pilot assumes **48** for a Mini+. The pilot steers at 1/60 of full angular per degree of error, so one held command removes about rate × hold / 60 of the error: 2-3 times the error at 60°/s (which is why the unchanged pilot overshot), 1.6-2.4 times at 48, and 0.8-1.2 times at 23.4. At 23.4 the cap of 0.3 also allows only about 14-18° per observation, so a large heading error takes many observations to remove. A higher cap might be better on a real rover, or the cap might not be needed at all.

## What runs

`colosseum_rate.py` (beside this plan) imports `studies/colosseum-hold/colosseum_hold.py` from main, unchanged (`fetch_deps.py` stops unless its sha256 is 1d54b068..., the file both earlier studies flew), and runs its `fly()` with the simulator's `max_yaw_dps` set to each rate. Nothing else in the simulator or the pilot changes. The unit tests run first and must pass; one checks that at 60°/s the live arm reproduces `colosseum_hold.fly()` exactly. `fetch_deps.py` waits for this PLAN.md to be on main before anything flies.

- **Rates:** 23.4 and 48.0°/s per unit of `angular`.
- **Arms** (as in colosseum-hold): `live` (commands and telemetry pass straight through), `stale` (the unchanged pilot, default cap 1.0), and `stale` with `--max-angular` 0.3, 0.5 and 0.7 (`stale-m30`, `stale-m50`, `stale-m70`).
- **Trials:** goals 30 m and 80 m, GPS noise 0.22 m and 1.5 m, fresh seeds 49-72, 300 s trials. 2 × 5 × 2 × 2 × 24 = **960 flights**. Every arm of a seed flies the same goal and the same observation cadence.

**Pass** (as before): an arm passes at a rate if, in each of the 4 cells at that rate, at least 23 of 24 flights complete and the median time is at most 1.5 times live's at the same rate. **Score:** for each stale arm, its summed median time over the 4 cells divided by live's, averaged over the two rates.

## Predictions (read from `summary.json`)

- **S1** `stale-m30` passes at 48.
- **S2** `stale-m30` passes at 23.4.
- **S3** The unchanged pilot (`stale`) passes at 23.4.
- **S4** The unchanged pilot fails at 48.
- **S5** At 23.4, `stale-m30`'s summed median time over the 4 cells is higher than `stale-m50`'s.
- **S6** The decision below is **R1** (0.3 stays).
- **S7** No flight crashes (`crashed` is 0 in all 40 cells).
- **S8** `live` is slower at 23.4 than at 48 in all 4 cells (median time).

## What it decides (`decision` in summary.json)

Of the stale arms that pass at both rates, take the one with the lowest score.

- **R1:** `stale-m30` passes at both rates and its score is less than 0.10 above the best. The README keeps recommending 0.3 and adds that it also passed at 23.4 and 48°/s per unit.
- **R2:** otherwise, if some arm passes at both rates. That arm's cap is flown again on fresh seeds 73-96 at both rates, beside 0.3. The README changes its recommendation only if it passes again.
- **R3:** no stale arm passes at both rates. The README says that no single cap has been shown to suit both measured turn rates, and keeps 0.3 only as a result of the 60°/s simulator.

Whatever the rule, S3's result is reported: if the unchanged pilot passes at the recorded Zero's rate, the README says so.

## Limits

- **A described cadence, not the bridge's code.** The bridge publishes no licence, so none of its code is used. The 2-3 s cadence comes from the GeNIE baseline's notes (frodobots-org/colosseum-policy-server #8).
- **A simple turning model.** The simulator turns at a constant rate per unit after its 0.8 s command latency. Recorded rovers lose turn on short holds (frodo-spin-v2, D2), so a real rover may turn less per held command than the simulator does, mostly on holds under 2 s, which the bridge's 2-3 s cadence avoids.
- **The rates.** 23.4 comes from human-driven, mostly Earth Rover Zero-era rides in FrodoBots-2K. 48 is the Mini+ figure the pilot assumes, not one measured here. A real RoboColosseum trial is the only real test.
- **Simulation only, existing flags only.** No pilot code changes.

## Reproduce

```
python fetch_deps.py
python -m unittest -v test_colosseum_rate
python colosseum_rate.py --out-dir out --seeds 24 --first-seed 49
```
