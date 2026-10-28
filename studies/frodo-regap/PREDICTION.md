# frodo-regap-v1: is a real rover's first GPS fix after a gap safe to restart from?

Pre-registered 2026-10-28 (~08:45 UTC), before frodo-regap-v1 reads any data. MV2 of Munim, Inc.; written with AI agents. CC BY-SA 4.0 (results derive from FrodoBots-2K). The code that will run, `frodo_regap.py` 0.1.0 and `test_frodo_regap.py`, is committed beside this file, and the job checks that its copies match these byte for byte before it starts.

## Why

pace-w (studies/pace-w/GRADE.md, 10 of 11) found in simulation that starting the pilot's GPS average again from the first fix after a gap longer than 3 s cut the worst position error through 90 s outages from 52-63 m to 10-11 m. It was rejected only because it was 2 s slower on one simulated course. But the simulator's first fix after a gap is as good as any other fix. A real receiver that has just got its signal back may report a worse first position, and a restart would then jump the pilot to it. Nobody has measured this for a sidewalk rover. We found no published measurement of first-fix error after GPS gaps on a low-cost robot, only studies of reacquisition time and of drift during an outage. This study measures it on recorded Earth Rover rides, using the pilot's own filter.

## Design (fixed before the run)

- Data: FrodoBots-2K (FrodoBots Lab, CC BY-SA 4.0). From each of the 24 parts, 60 rides spread evenly through those with control and GPS logs (`frodo_motion.pick_evenly`), read over HTTP range requests. Time budget 150 min.
- Each ride's GPS log (no-fix rows dropped, as in `frodo_motion.load_gps`) is fed, row by row, to two copies of rover_pilot 0.19.0's `GpsFilter`. One is **keep**, the shipped filter (alpha 0.3, jump gate 3 m/s + 10 m, fix lost after 3 s without a reading). The other is **restart**, the same filter, except that the first *new* fix it accepts after a gap of more than 3 s starts the average again from that fix. Which readings are accepted is identical in both.
- **Gap:** a reading that comes more than 3 s after the filter's last valid one (the pilot's own `has_fix` rule). The **first fix** is the first new accepted fix after it.
- **Reference:** a constant-velocity line fitted by least squares to the ride's new GPS positions (rows whose position changed) from 1.5 to 10.5 s after the fix, evaluated at the fix's time. It needs at least 4 positions spanning at least 4 s, and no gap over 3 s in the log from the fix to 10.5 s after it. The fix itself is never in its own fit.
- **Ordinary fixes (baseline):** every 10th new accepted fix with no gap and no ride start in the 20 s before it, judged against the same kind of reference.
- Per first fix: `r_first` (the fix's distance from the reference), `keep` and `restart` (each filter's estimate from the reference just after that fix), the gap's length, the wheels' distance through it (mean |RPM| x 0.00668 m/s, 1.5 s earlier on the wheels' clock), and the jump from the last fix before it.
- 95% interval of the ratio of medians: 200 resamples of rides, seed 1.

## Check (E1)

Gaps per hour in [1.0, 3.0] (frodo-gps-v4 found 1.8 per hour over 80.3 hours, counting rows), and at least 60 scored first fixes and 60 baseline fixes. If not, nothing is decided.

## Decision rules

- **D1 (the first fix is safe to restart from):** median `r_first` / median baseline miss <= 1.5, **and** at most 5% of first fixes more than 5 m from their reference.
- **D2 (restarting helps on real data):** on at least 20 scored gaps the wheels drove 2 m or more through, the median `restart` miss is below the median `keep` miss, **and** restart is more than 2 m worse than keep in at most 10% of them.
- What follows: if D1 fails, FINDINGS will say that a restart on a real rover must wait for a second fix that agrees with the first, and any later restart study builds that in. If D1 and D2 both hold, FINDINGS will say the recorded GPS supports a restart. The shipped pilot still keeps its average, because pace-w's rule rejected the restart on its simulated slowdown, which is not yet explained. In no case does this study change the pilot's code by itself.

## Predictions

- **P1:** E1 passes, and gaps per hour are between 1.2 and 2.6.
- **P2:** the median baseline miss is between 0.3 and 2.0 m.
- **P3:** on ordinary fixes, the shipped average sits a median 0.8 to 3.0 m from the reference (alpha 0.3's lag on real rides).
- **P4:** median `r_first` / median baseline miss is between 1.0 and 3.0, so the first fix after a gap is no better than an ordinary fix.
- **P5:** at most 10% of first fixes are more than 5 m from their reference.
- **P6:** the wheels drove 2 m or more through at least half of the gaps a new fix ended.
- **P7:** on gaps driven through, the median `restart` miss is below the median `keep` miss.
- **P8:** D1 is met.

## Limits known in advance

- The reference is the GPS's own next ~9 s, not surveyed truth. An error that the first fix shares with the fixes after it (slow drift, a multipath offset that persists) is invisible here. The study measures only whether the first fix disagrees with what the receiver says next.
- A straight constant-speed line is wrong on turns and when the speed changes. Ordinary fixes are judged the same way, so the ratio is fairer than either number alone, but gaps may come at different moments (turns, stops) than ordinary fixes.
- FrodoBots-2K was recorded on Earth Rovers driven by people, with GPS logged about once a second. An Earth Rover Mini+ reports every 2 s, and the pilot drives differently from people.
- The wheels' distance depends on frodo_gps's RPM-to-speed factor. A rover that was pushed or carried with its wheels still would count as standing.
