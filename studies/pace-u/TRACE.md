# pace-u: trace (a diagnostic, not pre-registered)

MV2 of Munim, Inc. Written with AI agents. CC BY 4.0.

pace-u's grade (`GRADE.md`) left two misses unexplained. With a warm-up, the blocked rover of seed 388 was caught 11.9 s later than on the other seeds (P7), though its first GPS outage came only at 664.5 s. And with a 5 s warm-up most blocked missions made a second recovery move at 34.2 s, 4.2 s after the block had ended (P10). `trace_u.py` 0.1.0 flew nine of pace-u's boulevard missions again on rover_pilot.py 0.18.6 and logged every call of the stuck check up to 60 s: whether the history had been cleared since the call before, when the warm-up started, the history's length and span, the mean commanded speed, how far the GPS average moved over the history, the verdict, the pilot's stop and bridge counters, and whether a new fix had come in. It only reads. All nine missions came out identical to pace-u's record (elapsed time and every recovery move), and a test checks that a traced mission's record equals an untraced one's.

Job `trace-u-v1`, 2026-10-26 15:52-15:55 UTC. It fetched main with `pace_u.py` (SHA-256 916fd5e8…) and `pace_t.py` (3c89c187…) as pace-u ran them (`trace/fetched.json`). 7 of 8 tests passed. `test_restored` failed because of a fault in the test itself. It kept the saved function as a class attribute, which Python hands back as a bound method, so `assertIs` compared a function with a method. The published `test_trace_u.py` keeps the saved functions in a tuple, and nothing else in it changed. The tests that a traced mission equals the untraced one and that each matches the record both passed.

## Seed 388: a stop for two missing GPS reports

With a warm-up the clear came at 12.0 s on seed 388, blocked or not (`trace/calls-blocked30-warm10-388.csv`, `calls-blocked30-warm5-388.csv`, `calls-quiet90-warm10-388.csv`):

- New fixes came in at 2.0, 4.0 and 6.0 s, and none at 8.0 or 10.0 s. The simulated Mini+ sends a report every 2 s and drops each one with probability 0.05. Here two were dropped in a row.
- The last stuck check before the clear was at 10.9 s. For the next 1.1 s there was none. The simulator holds each report until the next, so the last valid reading was the 6.0 s report, seen until about 7.9 s, and the pilot treats the GPS as lost once it has had no valid reading for more than 3 s (`GpsFilter.max_age_s`). 11 s into the mission the dead reckoner had no estimate yet, so the pilot did not bridge (bridged +0.0 s). It stopped the rover and cleared the stuck history. No recovery move, telemetry stop or tip stop was counted.
- At 12.0 s the next report came, the pilot drove on, and the warm-up started again. With 10 s the history began at 22.0 s, was full at 31.0 s, and the GPS average had moved 0.16 m, so the check fired at 31.0 s, 1 s after the block. With 5 s it fired at 26.1 s.
- The shipped check fired at 9.1 s, so at 12.0 s it was in its recovery move, and the stop changed nothing for it. On quiet90 the 10 s warm-up also started again at 12.0 s and never fired. That rover was driving.

So P7's miss was not a blocked rover that the warm-up failed to catch with the GPS up. The pre-stated condition counted only the study's 90 s outages, and this was a 1 s stop for a short GPS gap. The warm-up did what it was built to do and started again after the stop. A warm-up that starts again after every clear pays its whole delay again after each such stop. With 2 s reports and 5% dropped, two in a row come about once in 400 pairs, so roughly 1 blocked mission in 40 meets one in its first 20 s. pace-u had 1 of 24.

Seed 373 is the same thing at t = 0. Its first report was dropped, so the pilot's first stuck check came at 2.0 s, and each of its catch times is 2 s later than the other seeds' (16.2 = 2.0 + 14.2 s with 5 s).

## The 5 s warm-up's move at 34.2 s: the average's lag after the block

Seed 374 with 5 s (`calls-blocked30-warm5-374.csv`) shows the cycle: a verdict at 14.2 s, the 6 s recovery move, a clear at 20.2 s, the warm-up until 25.2 s, then history from about 26 s. At 34.0 s the history spanned 8.8 s and the GPS average had moved 0.85 m. At 34.2 s the check fired. The block ended at 30.0 s, so the rover had been free for 4.2 s. But the simulated GPS reports run 1.5 s behind the wheels and come every 2 s, and the average moves 0.3 of the way to each one, so the average had barely begun to move. This is the same lag that makes the shipped check fire about 9 s after every start (`studies/pace-s/TRACE.md`). Afterwards the rover drove on: every full window from 54.2 s showed at least 6.0 m.

The other variants missed this by timing alone. The shipped check's second move came at 24.2 s, inside the block. Its next full window (from 39.2 s) showed 2.53 m, only about 1 m above the 1.5 m threshold. With 10 s the second window could not be full before about 45 s. By then the rover had moved at least 5.66 m.

## What this means

- **Both misses come from the same two things.** Any clear of the history starts the warm-up again, including a 1 s stop for missing fixes. And a GPS average judged over a 9 s window lags a rover that has just started moving by several seconds. A warm-up only moves the problem in time.
- **pace-u's eligibility rule was too narrow.** It looked for the study's outage windows but not for the simulator's dropped reports. The next pre-registration should count every stop and clear before the catch, not only outages. That was this series' lesson from pace-t too.
- **On a real rover this gap is rarer.** Recorded Earth Rovers had GPS gaps of over 3 s about 1.8 times an hour (FINDINGS-frodobots-2k.md), against about 4 an hour from two dropped 2 s reports in the simulator. The lag is real either way: the Mini+'s fixes are about 1.5 s behind the wheels and come every 2 s.
- Nothing here changes the pilot or pace-u's grade. A real rover keeps today's stuck check.

## Limits

Simulated rovers only, nine boulevard missions, the first 60 s of each. The reasons are read from the logged calls and from rover_pilot.py's code. Each was not tested by changing one thing at a time. Why seed 388 took exactly 1801.6 s with every variant was not looked at. None of this has been driven on a live Mini+.

## Files

`trace/` holds the job's outputs unchanged: `summary.json`, `report.md` (every call at each whole second up to 40 s, with clears and held windows), one `calls-<profile>-<variant>-<seed>.csv` per mission (one row per stuck check), `tests.txt` and `fetched.json`. Reproduce with `python trace_u.py --out-dir out-trace-u` (about 25 s).
