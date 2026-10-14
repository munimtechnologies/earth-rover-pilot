# How Earth Rovers respond to commands: measured from FrodoBots-2K

MV2 of Munim, Inc., 14 October 2026. The analysis code (`frodo_motion.py`, `sim_study.py`) was written with AI agents.

The Earth Rover SDK says `angular` is "rotation speed left/right (-1 to 1)" but not which way is positive. It doesn't give the speed or turn rate at a given command, the gyroscope's units or how late the GPS is. [FrodoBots-2K](https://huggingface.co/datasets/BitRobot/FrodoBots-2K) logs every command a human driver sent, the four wheel RPMs, the GPS and the IMU for about 2,000 hours of Earth Rover rides. So the answers can be measured instead of guessed.

## What was measured

`frodo_motion.py` 0.2.0 read all 24 parts of the dataset over HTTP range requests, about 317 MB in all and no video. From each part it took 12 rides spread evenly through it: 288 rides, 279 long enough to use, about 1 million control rows. All 279 had gyroscope readings. For every pair of GPS chords it lined the commands up with the GPS course and speed, at lags from -3 to 10 s, and it lined the commands up with each gyroscope axis at lags from -1 to 3 s. The full tables are in the job's `report.md`. The GPS numbers below are for 2 s chords. Version 0.1.0 gave the same GPS and wheel numbers on the same rides.

| Question | Answer | Evidence |
|---|---|---|
| Which way does a positive `angular` turn the rover? | **Left (counter-clockwise).** | When both were clearly non-zero (\|angular\| ≥ 0.2, course rate ≥ 5°/s), the GPS course turned left 440 times and right 57 times (89% left). The correlation of the course rate (clockwise positive) with angular is r = -0.243 (n = 24,446). The gyroscope agrees (below). |
| How fast does it turn? | About **30°/s per unit of `angular`** (28 to 36). | Gyroscope, below. At the pilot's angular cap of 0.6 that is about 18°/s, so a 90° turn in place takes about 5 s. |
| How late is the GPS? | About **1.5 s behind the wheels** and about **2.5 s behind the command**. | GPS speed tracks the mean wheel RPM best when the GPS is taken 1.5 s later (r = 0.686, n = 128,704). The course rate tracks angular best at 2.5 s (2.0 to 3.0 s are close). |
| How fast do the wheels respond? | About **0.8 s**. | Mean wheel RPM tracks the size of the command best 0.8 s later (r = 0.877, n = 486,900). 0.8 s plus 1.5 s matches the 2.5 s from command to GPS. |
| Speed at a given command? | About **0.8 m/s at full `linear`**, roughly in proportion below that. | 0.79 m/s per unit of linear, fitted through the origin (r = 0.698). Mean GPS speed by command band: 0.1–0.3 → 0.22 m/s; 0.3–0.5 → 0.30; 0.5–0.7 → 0.46; 0.7–0.9 → 0.60; 0.9–1.0 → 0.80 (sd about 0.3 m/s in each band). |
| Speed per wheel RPM? | **0.0067 m/s per RPM**, an effective wheel radius of **0.064 m**. | Fitted through the origin at a 1.5 s lag. |
| Are the logged RPMs signed? | **Yes.** | 4.4% of rows have a negative RPM. In 65% of the 39,560 spin-in-place rows (\|linear\| < 0.05, \|angular\| ≥ 0.3), the left wheels (rpm_1, rpm_3) and the right wheels (rpm_2, rpm_4) turn in opposite directions. |

## Gyroscope

Each IMU file holds lists of `[x, y, z, t]` samples. The gyroscope reads about once a second, and each axis has its own constant offset, so the slopes below allow for an offset.

- **Which axis is yaw?** Axis **x**. It follows the commanded `angular` with r = 0.524 (n = 115,487, 0.25 s after the command). Axes y and z show nothing (r = -0.007 and -0.049). The sensor is mounted with its x axis vertical.
- **Which sign?** A positive `angular` gives a **positive** x reading. A positive `angular` turns the rover left, so a positive x reading is a counter-clockwise turn seen from above.
- **How much?** 36.2 units per unit of `angular` over all rows. While spinning in place (\|linear\| < 0.05), 28.0 units per unit (r = 0.697, n = 24,855, 0.5 s after the command). Both are least-squares slopes over rows where the rover is still speeding up or slowing down, so the steady turn rate may be a little higher.
- **Units: almost certainly degrees per second.** Per unit of `angular`, the GPS course turns at least 23.3°/s and the x axis reads 36.2. The ratio is -0.64, about what 2 s GPS chords should give, since they smooth turns out. Radians per second would mean over 2,000°/s per unit, and raw counts from the MPU6050 the SDK lists (131 counts per °/s at its finest range) would mean under 0.3°/s. Neither fits a rover whose GPS course visibly turns at 23°/s or more.
- **A caution.** Fitting the GPS course rate directly on the x reading gives only -0.14 (r = -0.151, n = 24,453). Both series are noisy 1 Hz samples, and noise in the x reading pulls that slope toward zero. So that slope isn't used for the size; its sign agrees.

So a real rover turns at about **30°/s per unit of `angular`**, half the 60°/s the earth-rover-pilot simulator assumed.

## Other sources agree on the sign

The data alone shows how the Earth Rovers game app's commands moved the rovers. Two independent pieces of code show the SDK's `/control` uses the same sign:
- The SDK's own ROS2 bridge ([`examples/ros2/earth_rover_bridge.py`](https://github.com/frodobots-org/earth-rovers-sdk/tree/main/examples/ros2)) passes `cmd_vel` `angular.z` to `/control` `angular` unchanged. In ROS, a positive `angular.z` is counter-clockwise, a left turn.
- LeRobot's Earth Rover Mini+ keyboard teleop ([huggingface/lerobot](https://github.com/huggingface/lerobot)) sends a positive angular velocity for "turn left" (A, Q) and a negative one for "turn right" (D, E). Its robot class passes the value to `/control` unchanged.

So earth-rover-pilot since v0.6.0 drives an uncalibrated real rover with a positive `angular` turning left. Before v0.6.0 it assumed right, and in the simulator a rover with the opposite sign never leaves its start. `--calibrate` still measures the sign on the rover and overrides this default.

## What it means for a pilot

- **Speed.** A rover at full command covers about 0.8 m/s, not the 1.2 m/s the simulator assumes. A 50-mile marathon at 0.6 to 0.8 m/s is 28 to 37 hours of driving. That is in line with the human teams' 29 h 38 min.
- **Turn rate.** About 30°/s per unit of `angular`, not 60. Steering gains tuned on the simulator's rover turn a real one half as fast as intended. A study of gains for a real-like rover is the next step.
- **Calibration.** At 30°/s, `--calibrate`'s 30 s spin at 0.4 covers only about 350°, short of the whole turn it needs to read the compass scale. Up to v0.6.0 it would most likely have failed on a real rover. Since v0.7.0 it spins on, 10 s at a time, until a whole turn shows (up to 90 s).
- **GPS lag.** GPS shows a turn about 2.5 s after it is commanded. A controller that steers on GPS course alone keeps turning for 2.5 s too long and overshoots. The pilot steers on the compass and learns the compass bias only on straight stretches. That is the right shape, and the lag argues for keeping it.
- **Odometry.** An effective wheel radius of 0.064 m confirms the 0.065 m that earlier visual-SLAM work on this dataset assumed ([SlamMate/vSLAM-on-FrodoBots-2K](https://github.com/SlamMate/vSLAM-on-FrodoBots-2K)). Wheel odometry from RPMs, or the gyroscope for heading, can fill the 1 s gaps between GPS fixes.

## Does correcting for the late GPS help? Not clearly (simulation)

v0.7.0 adds `--gps-lag`: each GPS fix is moved forward by the driving commanded since it was taken, using the numbers above. `sim_study.py` flew two missions (the 4-checkpoint demo, about 220 m, and a 5-checkpoint zigzag) on 30 seeds each, with and without `--gps-lag 1.5`, on a simulated rover that moves like the recorded ones (`--sim-real`: 0.79 m/s at full `linear`, commands 0.8 s late, GPS 1.5 s behind) turning at 30 or 60°/s per unit, and on the simulator's default rover.

| Mission | Rover | Completed (plain / corrected) | Median time, plain → corrected | Corrected faster / slower (seeds) | Sign test p | Refused reports per run, plain → corrected |
|---|---|---|---|---|---|---|
| demo | real-like, 30°/s | 30/30 / 30/30 | 429.0 → 423.1 s | 17 / 11 | 0.34 | 0.07 → 0.23 |
| zigzag | real-like, 30°/s | 30/30 / 30/30 | 438.5 → 438.0 s | 16 / 8 | 0.15 | 0.13 → 0.27 |
| demo | real-like, 60°/s | 30/30 / 30/30 | 424.5 → 427.5 s | 11 / 16 | 0.44 | 0.07 → 0.17 |
| zigzag | real-like, 60°/s | 30/30 / 30/30 | 434.0 → 436.4 s | 7 / 20 | **0.019 (slower)** | 0.07 → 0.23 |
| demo | simulator default (no GPS delay) | 30/30 / 30/30 | 274.5 → 270.3 s | 23 / 5 | 0.0009 | 0.03 → 0.10 |
| zigzag | simulator default (no GPS delay) | 30/30 / 30/30 | 278.5 → 280.5 s | 12 / 15 | 0.70 | 0.10 → 0.23 |

Every mission was completed either way. On the real-like rover turning at the measured 30°/s, the correction saved a few seconds at most, and the result could be chance (p = 0.34 and 0.15). At 60°/s it made the zigzag slower. In every group it about doubled to tripled the refused checkpoint reports. The corrected position reaches the 10 m report radius before the GPS the server judges by does.

So `--gps-lag` stays **off by default**. It is there for experiments on a real rover. The likely reason it doesn't help: the pilot already steers on the compass, so a late position only matters for the aim point, and at 0.5 m/s, 1.5 s is under a metre. This is a simulation result with a simple motion model. A real rover may differ.

## Limits

- These are human-driven rides from the Earth Rovers game (Earth Rover Zero era, early 2024), logged on the rover. The SDK, newer rovers and other firmware may behave differently. The sign is backed by the SDK's and LeRobot's code; the speeds, turn rates and lags are only from this data.
- 288 of the 8,906 rides that have control and GPS files were sampled, 12 per part, so every part counts equally rather than every hour. The gyroscope figures come from the same 279 rides.
- Course rates from 1 Hz GPS are noisy. The turning correlation is weak (r = -0.24), even though the sign test is lopsided (440 to 57). The GPS turn rate is a lower bound.
- The gyroscope's units are inferred, not documented. Degrees per second is the only reading that fits the GPS, but the size could be off by the GPS smoothing factor.
- The control and GPS clocks were taken as they are. The results line up across lags (0.8 s + 1.5 s ≈ 2.5 s), which suggests no large offset in the sampled rides.
- Prior work: the University of Amsterdam report "Automatic Control, Calibration and Recording for the FrodoBots" (Zhang and Visser, 2024) describes the Earth Rover Zero's sensors and their rates (GPS 1 Hz, gyroscope 1 Hz, accelerometer 100 Hz). We could not read its full text, so it may cover some of the same ground. As far as we found, no earlier work has published these numbers measured across the whole dataset, together with the code to reproduce them.

## Reproduce it

```
python frodo_motion.py --out-dir out --rides-per-part 12 --imu-per-part 1 --gyro-max-mb 40
python sim_study.py --out-dir out-sim --seeds 30
```

Standard library only. Our `frodo_motion.py` run took 19 minutes and read about 317 MB. `out/summary.json` has every table and `out/rides.jsonl` has one line per ride. `sim_study.py` took about a minute.

## Licence and credit

Data: FrodoBots-2K by FrodoBots Lab, CC BY-SA 4.0. The numbers and tables in this file derive from it and are shared under CC BY-SA 4.0. The code (`frodo_motion.py`, `sim_study.py` and their tests) is Apache-2.0, like the rest of this repository. Not affiliated with FrodoBots, BitRobot or the Earth Rover Challenge organisers.
