# frodo-spin: how far a real Earth Rover turns for an in-place turn held T seconds (pre-registration)

Written on 2026-10-29 (UTC) before any data is read. By MV2 of Munim, Inc.; the study, code and text were made with AI agents. Code Apache-2.0; text CC BY 4.0. Data: FrodoBots-2K by FrodoBots Lab, CC BY-SA 4.0.

## Why

RoboColosseum's Earth Rover bridge answers each observation, every 2 to 3 s, with the command current at that instant and holds it until the next answer. Its first Earth Rover baseline (GeNIE, `frodobots-org/colosseum-policy-server` `baselines/genie_rover`, merged 2026-10-29) says that each answered in-place turn rotates the rover roughly 45 degrees and that its short turns "never reached the rover" until they were made to last until sampled. A pilot that steers through that bridge has to know how far a held turn command really turns the rover. That includes the time it takes to start and the coast after it.

earth-rover-pilot's figure (about 28 deg/s per unit of angular while spinning in place; v0.7.0) comes from the gyroscope, read as deg/s counter-clockwise. frodo_motion's own check of the gyroscope's units against the GPS course was inconclusive (slope -0.14 where about -1 was expected). frodo_odometry fitted 20 deg/s per unit while driving, and the GPS course gave 23 deg/s per unit. No study has measured an in-place turn without the gyroscope, or looked at how the turn depends on how long the command is held.

## Method (frodo_spin.py 0.1.0, committed beside this file)

- Rides: `pick_evenly` 30 per part from all 24 parts, those with control and IMU files (IMU at most 30 MB).
- A turn is a maximal run of control rows with |linear| < 0.05 and |angular| >= 0.3, all of one sign, with no two rows more than 0.5 s apart. It is held T s, from its first row to the first row after it, and T must be 0.3 to 5 s. It must start and end at rest: the rows in the 1.5 s before it and in the 2.5 s from its end must all have |linear| < 0.05 and |angular| < 0.1, with at least 3 rows and no gap over 0.5 s. Its command is the mean angular of its rows.
- The heading comes from the compass in frame yz+ (frodo-compass-v1), about the hard-iron centre fitted to the whole ride (frodo_compass.calibrate; the ride is left out if the fit fails its coverage and RMS checks). The heading before is the last compass sample from 1.5 s before the start to 0.2 s after it. The heading after is the first sample from 1.0 s to 2.5 s after the end. A turn without both is left out.
- The turn is measured in the commanded direction (positive angular = counter-clockwise). It is read in (-60, 300] deg, so a negative turn went the other way.
- Fit: turn = g x |angular| x T + c by least squares. g is in deg/s per unit; c is the start-up lag and coast in deg. The 95% interval of g comes from 200 resamples of rides (seed 1).
- Bins by T: 0.3-1, 1-2, 2-3 and 3-5 s, each with the median turn and the median turn / (|angular| x T).
- Gyroscope check: the mean gyroscope x (less the ride's median) over the samples from 0.8 s after the start to the end. It is fitted through the origin on |angular| (gyro gain) and divided by g.

## Check E1 (else nothing is decided)

At least 100 turns from at least 40 rides, and of the turns of 10 deg or more, at least 85% went the commanded way. The gain g must also be positive.

## Decision rules

- **D1 (gyroscope units).** If gyro gain / g is between 0.75 and 1.33, the gyroscope reads deg/s and the pilot's 28-30 deg/s figure stands. If it is outside, FINDINGS must say so and restate the turn rate from the compass value g. Any design that converts gyroscope readings to degrees would then be wrong by that ratio.
- **D2 (short pulses).** If the median rate per unit for holds of 0.3-1 s is below half that for holds of 2-3 s (both bins at least 10 turns), short pulses cost turn on a real rover. A held-command steering mode for RoboColosseum (colosseum-hold's R3, if it comes to that) then turns by holding for the whole observation interval, as GeNIE does, not by a short pulse followed by zero. Otherwise pulses stay an option. With fewer than 10 turns in either bin, D2 is not decided.

## Predictions

- P1: g is between 20 and 36 deg/s per unit.
- P2: c is between -15 and +15 deg.
- P3: holds of 2-3 s with |angular| >= 0.8 (at least 10 such turns) turn a median 35 to 85 deg. GeNIE's "roughly 45" sits inside this range.
- P4: D1 holds: the gyro gain / g is between 0.75 and 1.33.
- P5: at least 90% of turns of 10 deg or more went the commanded way.
- P6: the median rate per unit is lower for 0.3-1 s holds than for 2-3 s holds.
- P7: the upper end of g's 95% interval is below 48 deg/s per unit (the rate the pilot assumes for a Mini+). The Earth Rover Zero in FrodoBots-2K would then turn slower than that.

## Limits stated in advance

- FrodoBots-2K was recorded mostly on the Earth Rover Zero, driven by people through the game, not through the SDK or RoboColosseum's bridge. The Mini+ may turn at a different rate, and the bridge scales commands by the operator's limits. This measures the Zero, and it gives a method to repeat on the Mini+ once RoboColosseum publishes its runs.
- The compass is read about once a second. A single sample on each side, with no tilt or soft-iron correction, carries frodo-compass's error (median 10.7 deg against the GPS course with a whole-ride fit). The fit averages this out but individual turns are noisy.
- Turns over about 300 deg would be misread; T is capped at 5 s for this reason.

## Reproduce

```
python studies/frodo-spin/frodo_spin.py --out-dir out-spin --parts all --rides-per-part 30 --budget-min 150
```
(needs frodo_motion.py from v0.8.0 and frodo_compass.py, frodo_compass_live.py from main beside it)
