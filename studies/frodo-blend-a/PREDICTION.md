# frodo-blend-a-v1: predictions (frozen 2026-10-21 ~18:20 UTC, when the job was queued)

By MV2 of Munim, Inc.; written with AI agents. Code Apache-2.0; FrodoBots-2K data CC BY-SA 4.0.
Everything below was written before the job ran and is graded as written.

## Question
frodo-compass-live-v1 (211 scored rides of FrodoBots-2K; shipped in earth-rover-pilot v0.10.0)
found that wheels along a live-calibrated compass heading (`running` fit, learned bias) beat
wheels along the last GPS course: median miss ratio 0.926 at 10 s (95% CI 0.874-0.999), 0.687 at
30 s. The 10 s margin is thin, and right after a fix the last GPS course is fresh and carries no
mount bias. Does a pilot do better by holding the GPS course for the first B seconds after a fix
and switching to the compass after that, and what is the best B?

## Variants (all causal: they use only samples before the anchor time)
- `course`: wheels along the last GPS course (baseline, as in v1/live-v1).
- `running`: live-v1's running compass fit (frame yz+, REFIT_S 60, learned bias), unchanged code
  (imported from frodo_compass_live.py at tag v0.10.0, not copied).
- `blendB` for B in (2, 5, 10) s: the course heading in every 0.2 s cell that starts less than B
  seconds after the anchor fix's cell boundary, then the `running` compass heading, re-anchored so
  the heading does not jump at the switch (offset = course - compass in the switch cell, wrapped
  to +-180; the offset fades linearly to 0 over the next B seconds).
- `hard5`: the same switch at B = 5 s with no re-anchoring (shows whether the fade matters).
Horizons reported: 5, 10, 30 s. Same ride sample, anchors and skip rules as live-v1 (30 rides per
part, all 24 parts, anchors 5+ min after the first compass sample, rides whose whole record
calibrates). Every variant is scored on exactly the anchors where live-v1 scored `running`, so
`course` and `running` reproduce live-v1's running rows pair for pair (a unit test checks this on
a simulated ride). Code: frodo_compass.py and frodo_compass_live.py from v0.10.0, frodo_motion.py
from v0.8.0 (the copy live-v1 ran on).

## Prior art (re-searched 2026-10-21 before queueing)
Combining course and heading is textbook (complementary and Kalman filters on GNSS course plus
magnetometer). Searches for a measured switch time between the GNSS course and a magnetometer
heading on small ground robots, and for any such work on FrodoBots-2K, found general dead-reckoning
sources and earth-rover-pilot itself, but no measured switch time between the GPS course and a
live-calibrated magnetometer heading on crowd-driven sidewalk rovers (FrodoBots-2K or any fleet).
The claim is that narrow: one tuned constant and what it costs or gains on real rides.

## Grading rules (implemented in frodo_blend.decide)
- E1 (tests): test_frodo_compass, test_frodo_compass_live and test_frodo_blend pass.
- E2 (check): `running` / `course` at 10 s within 0.02 of live-v1's 0.926, on at least 2,000
  pairs at 10 s. If not: stop, report the mismatch as the finding, no release change.
- D1 (default switch): best B by median miss ratio vs `course` at 10 s. Adopt `blendB` as the
  pilot's default only if its ratio is <= `running`'s ratio - 0.03 at 10 s AND it is not worse
  than `running` by more than 0.02 at 30 s. Otherwise keep pure `running` and say the blend did
  not help.
- D2 (re-anchoring): if `hard5` is within 0.01 of `blend5` at 10 s, ship the simpler hard switch.
- Transfer limit, stated up front: FrodoBots-2K is the Earth Rover Zero with a raw 1 Hz
  magnetometer and 1 Hz GPS; the Mini+ reports an on-rover `orientation`, so B is a starting value
  for the Mini+, not a measured one.

## Predictions (each graded met / not met)
- P1: at 5 s, `course` beats `running` (ratio running/course > 1.00).
- P2: the best B is 5 s; blend5 / course at 10 s lands in 0.84-0.91 (running: 0.926).
- P3: D1 adopts the blend (margin >= 0.03 at 10 s, cost at 30 s <= 0.02).
- P4: `hard5` is worse than `blend5` by more than 0.01 at 10 s (the jump at the switch costs).
- P5: blend2 / course at 30 s is within 0.02 of running / course at 30 s (0.687).

If the first run's tests fail, the code is fixed and the job re-run as -v2; these predictions
stay frozen.
