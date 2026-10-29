# frodo-spin-v2: the same pre-registered study on a larger sample

Written 2026-10-29, before frodo-spin-v2 reads any data. By MV2 of Munim, Inc.; the plan, code and text are made with AI agents. Text CC BY 4.0; results derive from FrodoBots-2K (FrodoBots Lab, CC BY-SA 4.0).

## Why

frodo-spin-v1 (`GRADE.md`) failed its check E1: in-place turns from rest to rest are rare in the recorded rides (59 turns on 49 of 720 sampled rides, where E1 asks for 100 turns on 40 rides), so nothing was decided. Its figures all fell inside the predicted ranges, but on too few turns to settle the gyroscope's units (D1) or whether short pulses cost turn (D2).

## What changes, and what doesn't

- **Only the sample size.** `frodo_spin.py` 0.1.0 and `test_frodo_spin.py` run byte for byte as in v1: `fetch_deps_v2.py` (committed beside this plan) downloads them from main and stops if either differs from the file v1 ran (sha256 194b3bca... and 7fbc1bb0...). The command is v1's with `--rides-per-part 200 --budget-min 220` instead of 30 and 150. That is up to about 4,170 rides (fewer where a part has fewer usable rides); at v1's rate it should give about 300 turns and about 12 full-angular 2-3 s holds.
- **Unchanged:** the turn definition, the compass method, the fit, the bins, check E1, rules D1 and D2, and predictions P1-P7, all as in `PREDICTION.md` (155ed3b).

## Honest limits of this re-run

- **Not blind and not independent.** v1's figures were seen before this plan was written. `pick_evenly` with 200 per part will include many of the 720 rides v1 read, so v2 is a larger sample that contains much of v1's, not a replication. v1 alone failed E1, so v2's turns will be mostly new, but the predictions it is graded on were set before v1, not before v2.
- Everything listed in `PREDICTION.md`'s limits still applies: Earth Rover Zero-era rides driven by people, one compass sample each side of a turn, holds capped at 5 s.

## What it decides

Exactly `PREDICTION.md`'s rules. If E1 passes: D1 says whether FINDINGS keeps the gyroscope-based 28-30 deg/s per unit or restates the turn rate from the compass value g; D2 says whether a held-command steering mode for RoboColosseum should turn by holding for the whole observation rather than a short pulse. If E1 fails again, nothing is decided and the in-place-turn line on FrodoBots-2K is closed: the next measurement waits for real Mini+ runs.

## Reproduce

```
python fetch_deps_v2.py
python -m unittest -v test_frodo_spin
python frodo_spin.py --out-dir out-spin2 --parts all --rides-per-part 200 --budget-min 220
```
