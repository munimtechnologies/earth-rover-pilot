# frodo-regap2-v1: restart the GPS average only on a second fix that agrees?

Pre-registered 2026-10-28 (~22:30 UTC), before frodo-regap2-v1 reads any data. MV2 of Munim, Inc.; written with AI agents. CC BY-SA 4.0 (results derive from FrodoBots-2K). The code that will run, `frodo_regap2.py` 0.1.0 and `test_frodo_regap2.py`, is committed beside this file. The job checks that its copies match these byte for byte before it starts, and it imports `studies/frodo-regap/frodo_regap.py` 0.1.0 unchanged.

## Why

frodo-regap-v1 (`studies/frodo-regap/GRADE.md`, 6 of 8) found on 1,359 recorded Earth Rover rides that the first GPS fix after a gap of more than 3 s sits a median 1.74 times as far from its reference as an ordinary fix (95% CI 1.47-2.18), and that 6.7% of first fixes are over 5 m off, against 0.35% of ordinary fixes. Its rule D1 failed, so by the rule written in advance a restart on a real rover must wait for a second fix that agrees with the first. The same study found that restarting from the first fix still landed nearer than the shipped average on gaps the rover drove through (median 1.49 m against 2.79 m). This study tests the safer rule on rides that study did not read. Waiting for two agreeing measurements before re-initialising a filter is a known idea in tracking (an "M-of-N" confirmation). We found no measurement of what it buys after GPS gaps on a low-cost sidewalk robot.

## Design (fixed before the run)

- **Data:** FrodoBots-2K (FrodoBots Lab, CC BY-SA 4.0). In each of the 24 parts, the 60 rides frodo-regap-v1 read are left out (`frodo_motion.pick_evenly(usable, 60)`). Then 80 rides are spread evenly through the rest (fewer where fewer are left; part 23 has none left). Rides are read over HTTP range requests, with a 150 min budget.
- **Three filters** replay each ride's GPS log (no-fix rows dropped), all built on rover_pilot 0.19.0's `GpsFilter`. Which readings are accepted is identical in all three:
  - **keep:** the shipped average (alpha 0.3).
  - **restart:** frodo-regap-v1's `RestartGpsFilter`, where the first new fix after a gap of more than 3 s starts the average again.
  - **confirm:** after such a gap, a new fix that lies within 2.0 m + 1.5 m/s × (time between them) of the previous new fix since the gap starts the average again from itself. Until that happens it averages as shipped. A further gap forgets the earlier fix.
- **Scoring:** at the **first** new fix after each gap (as in frodo-regap-v1), and at the **second** new fix after it, if one comes before the next gap. Each is scored against frodo-regap-v1's reference: a constant-velocity line through the ride's new GPS positions 1.5-10.5 s later, needing at least 4 positions spanning at least 4 s and no gap over 3 s. Ordinary fixes (every 10th, with no gap or ride start in the 20 s before) are judged the same way. A gap counts as **driven through** if the wheels went at least 2 m through it (mean |RPM| × 0.00668 m/s, 1.5 s earlier on the wheels' clock).
- 95% interval of the first-fix ratio: 200 resamples of rides, seed 1 (frodo-regap-v1's `ratio_ci`).

## Check (E1)

Gaps per hour must be in [1.0, 3.0], with at least 60 scored second fixes and 60 baseline fixes. If not, nothing is decided.

## Decision rules

- **D1 again (replication):** frodo-regap-v1's D1 fails again if the ratio of medians (first fix / ordinary fix) is over 1.5, or more than 5% of first fixes are over 5 m from their reference.
- **D3 (confirm is safe):** at the second fix, confirm is more than 5 m from the reference in at most 5% of scored gaps, **and** no more often than restart.
- **D4 (confirm helps):** on at least 20 scored gaps driven through, confirm's median miss at the second fix is below keep's, **and** confirm is more than 2 m worse than keep in at most 10% of them.
- **What follows.** If D3 and D4 hold, confirm earns a pre-registered simulated trial (pace-x) against the shipped average. That trial needs a simulator whose first fix after a gap is as bad as the real ones measured here. If not, a real rover keeps the average and the restart line is closed. In no case does this study change the pilot's code by itself.

## Predictions

- **P1:** E1 passes, with 1.2-2.6 gaps per hour.
- **P2:** D1 fails again.
- **P3:** the second fix agrees with the first in 70% to 97% of gaps that have a second fix.
- **P4:** where both are scored, the second fix's median miss is below the first fix's.
- **P5:** D3 is met.
- **P6:** D4 is met.
- **P7:** confirm starts the average again a median of at most 2.0 s after the first fix.
- **P8:** of the first fixes over 5 m off that have a second fix, confirm refuses at least half at the second fix. If there are fewer than 5 such fixes, P8 is graded "not testable".

## Limits known in advance

- The reference is the receiver's own next ~9 s, not surveyed truth. It favours any estimate equal to a raw fix, and at the second fix confirm is usually exactly that fix. So D4 partly measures the shipped average's ordinary lag (frodo-regap-v1: 1.94 m on ordinary fixes). The tail rule D3 and the comparison with restart are less exposed to this.
- A constant-velocity line is wrong on turns and speed changes.
- These are human-driven Earth Rover Zero-era rides with GPS logged about once a second. A Mini+ reports every 2 s, which doubles the time confirm waits.
- The thresholds (2.0 m + 1.5 m/s) were set from earlier measurements (0.22 m RMS sideways GPS noise; about 0.8 m/s top speed on recorded rides). They were not tuned on this data.
