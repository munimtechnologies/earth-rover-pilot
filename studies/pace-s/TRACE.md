# Why was restarting the GPS average slower on outage90 boulevard? (diagnostic, simulated)

MV2 of Munim, Inc. Written with AI agents. CC BY 4.0.

**This is a diagnostic, not a pre-registered study.** pace-s (`studies/pace-s/GRADE.md`) failed its rule R2 on one cell. On outage90 boulevard, `restart` was slower than the shipped filter (`a0.3`) on 6 of 24 seeds and faster on none (p 0.031, median 0 s): seeds 327 (+8 s), 328 (+6), 331 (+2), 337 (+2), 338 (+94) and 339 (+4). `trace_s.py` 0.1.0 (job `trace-s-v1`, rover_pilot.py 0.18.4, pace_s.py 0.1.0) flew those six missions again with both filters, plus quietdrift90 seed 338, where both filters took exactly 1917.6 s. It logged one row a second of simulated time: the rover's true position, the GPS fix, the pilot's estimate, the filter's average, whether the fix was fresh, seconds bridged on the dead reckoner, the command applied, recovery moves, checkpoints reached, the true distance to the next checkpoint and filter restarts (`trace/trace-<profile>-<variant>-<seed>.csv`). All 14 traced missions came out **identical** to pace-s's record (`check.different` is empty for every one), so the trace did not change what it watched. Every number below is read from `trace/summary.json`, `trace/report.md` or the CSVs. Positions are metres north and east of the start. The boulevard runs north.

## What cost the time: a false "stuck" recovery move

In 5 of the 6 slower seeds, `restart` made exactly **one more recovery move** than `a0.3`: at 1353.6 s (seed 327), 477.6 s (328), 607.6 s (331), 1411.9 s (338) and 984.6 s (339). The pace-s simulator has no obstacles and never blocks the rover, so none of these was a real stuck rover. Each one cost a back-up-and-turn: 2 s reversing at −0.4, 1.5 s turning at ±0.6, 2.5 s forward at 0.5. The record shows it: `restart` spent 2.0-2.1 s more reversing and 1.5 s more turning on each of those seeds.

Why it fired: `Pilot._stuck` (rover_pilot.py 0.18.4) judges progress on the **smoothed** GPS. It keeps the last 10 s of `gps.lat, gps.lon` and calls the rover stuck if that moved less than 1.5 m while the pilot asked for at least 0.4 × cruise. The history is cleared while the pilot bridges a gap on the dead reckoner, so a fresh 10 s window starts the moment fixes return. Right after a restart the average starts from a single fix with none of its usual lag built up, and for the next 10 s it advances far more slowly than the rover:

- **Seed 328** (`trace-outage90-restart-328.csv`). The rover waited out an outage at the first checkpoint (stopped 451.6-467.6 s). At 468.6 s the first fix came, the filter restarted at (394.12, 1.77) and the checkpoint counted. The rover drove off at 0.8 from a standstill, and its fixes arrive about 1.5 s late. By 476.6 s the rover had gone 7.1 m north, but the average had moved only to (395.35, 1.34), **1.30 m**. At 477.6 s the pilot started a recovery. With the shipped filter, the same moment produced the usual jump: the average went from 344.66 to 383.40 north (`trace-outage90-a0.3-328.csv`). That is tens of metres of "progress", so no recovery was triggered.
- **Seed 327.** The same thing after the stop at the third checkpoint: restarted at (1148.03, 137.64) at 1344.8 s, (1149.23, 137.04) at 1352.5 s (1.34 m), recovery at 1353.6 s.
- **Seed 339** is the same mechanism without a stop. A short dropout (no fix from about 970 to 973.6 s) made the pilot bridge, clearing the history. At 974.6 s the filter restarted on a fix that happened to be only 0.48 m from the rover (827.95 north). The next fixes, noisy and 1.5 s late, read 826.62 and 825.58, pulling the average back while it built up its lag. Over the next nine seconds it reached 829.29 at 982.6 s, **1.34 m** on, and the recovery came at 984.6 s.

Seed 337 (+2 s) had no extra recovery. Its 2 s, one GPS period, came before the second checkpoint (910.6 against 912.6 s), and the trace does not show a single cause.

## Seed 338's 94 s: an outage met at the finish

`restart` reached the third checkpoint at the same moment as `a0.3` (1402.0 s), then made its false recovery at 1411.9 s. `a0.3` finished at 1823.6 s, **0.8 s before** the mission's fourth outage began at 1824.4 s. At 1824.4 s `restart` was still 9.83 m short. It bridged on the reckoner until its estimate reached the checkpoint at 1837.6 s, 4.44 m short in truth. There it stood, because the pilot does not report a checkpoint while bridging (`distance <= report_radius and not bridging`, rover_pilot.py ~1279). It waited until fixes returned and finished at 1917.6 s. About 11 s of lag became 94 s.

The same outage explains quietdrift90 seed 338. There **both** filters were still short when it began, both stood at the last checkpoint (1840.9 and 1843.1 s), and both finished at 1917.6 s, so the difference was 0 s.

## The same false alarm in the shipped pilot, at every start

The trace showed something larger than the pace-s question. Every traced `a0.3` mission but one (seed 328) made a recovery move at **9.6 s**, seconds after the start. The cause is the same. The rover starts from rest, first turns toward the course, and its fixes lag 1.5 s, so in the first 10 s the average barely moves. Seed 327: from (0.86, −1.38) at 0 s to (0.23, −0.06) at 9.6 s, 1.46 m, while the rover had driven 5.2 m.

pace-s's record (`studies/pace-s/runs.jsonl`) shows how common it is with the shipped filter. 241 of its 288 `a0.3` missions made at least one recovery move, 240 of them exactly one. With GPS as quiet as recorded Earth Rovers' (0.22 m: quiet90, quietdrift90, quiet45), the share was **210 of 216**, and all six without one were on bayside. With the simulator's 1.5 m noise (outage90), it was 31 of 72, because the noise itself often moves the average more than 1.5 m. None of them was a real stuck rover. On a live rover, the same move backs up 0.9 m blind and swings about 43° on a sidewalk, every time it starts or restarts from a standstill.

## What follows

- The cost of `restart` on boulevard was not the restart's estimate. It was the stuck detector misreading a freshly restarted average as a stuck rover, and on one seed an outage turning that into 94 s. pace-s's R2 still stands: a real rover keeps the shipped filter (v0.18.5, documentation only).
- The detector's false alarm is a fault in the shipped pilot, independent of any filter change. A **warm-up**, no stuck judgement until 10 s after the history was last cleared (at the start, after a stop, a bridged gap or a recovery), is pre-registered as **pace-t** (`studies/pace-t/PREDICTION.md`). It runs on fresh seeds, with a check that a rover that really cannot move is still caught. pace-t also flies `restart` with the warm-up and tests it again under pace-s's R2 conditions, openly prompted by this trace.
- Nothing in the pilot changes because of this trace alone.

## Limits

- Seven seeds, simulated. The prevalence figures come from pace-s's record, and the mechanism from reading the code and these traces. Rows are one a second, so a moment may be up to a second off.
- The simulator's outages are clean, and nothing in it can really stop the rover. How often a real Mini+ gets stuck, and how fast the detector must catch it, is not measured.
- Files: `trace_s.py`, `test_trace_s.py` (7 tests passed in the job, `trace/tests.txt`), `trace/summary.json`, `trace/report.md`, the 14 `trace/trace-*.csv`, `trace/fetched.json`.
