# colosseum-compat: grade

Graded 2026-10-29 against `PLAN.md` (committed da120cf on 2026-10-28, before any flight). By MV2 of Munim, Inc.; the grading and write-up are made with AI agents. Text CC BY 4.0.

**Result: 7 of 7 predictions held.** earth-rover-pilot 0.19.1 ran unchanged, through `rover_pilot.main(["--timeout", "300"])`, behind a simulated copy of the RoboColosseum Earth Rover bridge as its pull request (frodobots-org/colosseum-policy-server #4) describes it. All 288 flights completed and were accepted.

## The run

- Job `colosseum-compat-v1`, sealed container, 2026-10-29 02:39-02:42 UTC. Unit tests passed first, then 288 flights in 50.7 s of wall time.
- `fetched.json`: rover_pilot 0.19.1 (sha256 e971e188...), dead_reckon 0.2.0, and `PLAN.md` on main.
- Outputs beside this file: `summary.json` (every number below), `runs.jsonl` (one line per flight), `fetched.json`.

## Predictions

| | Prediction | Outcome | Held |
|---|---|---|---|
| P1 | No bridge flight crashes | `crashed` is 0 in all 6 bridge cells (144 flights) | yes |
| P2 | The pilot calls only the five bridge endpoints plus `GET /status`, which the bridge doesn't serve | `bridge_calls` lists exactly those six; `bridge_unserved_calls` is `["GET /status"]` | yes |
| P3 | At 40 m and 80 m, at least 23 of 24 complete per noise level | 24 of 24 in all four cells | yes |
| P4 | At 120 m, at least 20 of 24 complete, median 230-290 s | 24 of 24 at both noise levels; medians 244.1 s (0.22 m) and 242.1 s (1.5 m) | yes |
| P5 | Median 60-100 s at 40 m, 140-200 s at 80 m | 75.1 / 73.6 s at 40 m; 159.1 / 158.6 s at 80 m | yes |
| P6 | bridge and sdk shapes identical on every paired flight | `shape_differences` is empty | yes |
| P7 | Final true distance: median 6-11 m in every cell, at least 95% within 15 m | medians 8.61-9.75 m; 144 of 144 bridge flights within 15 m (largest 13.57 m) | yes |

## What it decides (PLAN.md, applied as written)

- **P1, P2 and P3 held**, so the next documentation release adds a "Running under RoboColosseum" section to the README: the pilot runs unchanged under the bridge's documented contract, with the command. MV2 applies for RoboColosseum's free evaluation once the form is open, saying the policy was written with AI agents.
- **P4 held**, so nothing is added about goal range. A 120 m goal takes about 245 s at the default cruise, inside the 300 s trial; a goal much past about 140 m would not fit.
- **P7's median is above 8 m in every cell**, so the README notes that `--report-radius` can be set lower when a trial is scored on arrival. The pilot reports at 10 m by default and the bridge accepts within 15 m, which is why the rover ends about 9 m out.

## Limits

This checks a *described* contract, served from the pilot's own simulator, not the bridge's code (the bridge publishes no licence, so none of its code is used). It passes every `/control` straight to the rover. A later pull request in the same repository says the real bridge samples commands only every 2-3 s; `studies/colosseum-hold` tests that. Only a real trial shows the real field names, units and timing.

Reproduce: `python fetch_deps.py && python -m unittest -v test_colosseum_compat && python colosseum_compat.py --out-dir out --seeds 24` in `studies/colosseum-compat/`.
