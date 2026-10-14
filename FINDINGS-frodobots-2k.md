# How Earth Rovers respond to commands: measured from FrodoBots-2K

MV2 of Munim, Inc., 14 October 2026. The analysis code (`frodo_motion.py`, `sim_study.py`, `gain_study.py`) was written with AI agents.

The Earth Rover SDK says `angular` is "rotation speed left/right (-1 to 1)" but not which way is positive. It doesn't give the speed or turn rate at a given command, the gyroscope's units or how late the GPS is. [FrodoBots-2K](https://huggingface.co/datasets/BitRobot/FrodoBots-2K) logs every command a human driver sent, the four wheel RPMs, the GPS and the IMU for about 2,000 hours of Earth Rover rides. So the answers can be measured instead of guessed.

## What was measured

`frodo_motion.py` 0.2.0 read all 24 parts of the dataset over HTTP range requests, about 317 MB in all and no video. From each part it took 12 rides spread evenly through it: 288 rides, 279 long enough to use, about 1 million control rows. All 279 had gyroscope readings. For every pair of GPS chords it lined the commands up with the GPS course and speed, at lags from -3 to 10 s, and it lined the commands up with each gyroscope axis at lags from -1 to 3 s. The full tables are in the job's `report.md`. The GPS numbers below are for 2 s chords. Version 0.1.0 gave the same GPS and wheel numbers on the same rides.

| Question | Answer | Evidence |
|---|---|---|
| Which way does a positive `angular` turn the rover? | **Left (counter-clockwise).** | When both were clearly non-zero (\|angular\| ≥ 0.2, course rate ≥ 5°/s), the GPS course turned left 440 times and right 57 times (89% left). The correlation of the course rate (clockwise positive) with angular is r = -0.243 (n = 24,446). The gyroscope agrees (below). |
| How fast does it turn? | About **30°/s per unit of `angular`** (28 to 36). | Gyroscope, below. At the pilot's old angular cap of 0.6 that is about 18°/s, so a 90° turn in place takes about 5 s. |
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
- **Turn rate.** About 30°/s per unit of `angular`, not 60. Steering gains tuned on the simulator's rover turn a real one half as fast as intended. The gain study below finds better ones.
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

## Steering gains for a rover that turns at 30°/s (simulation)

`gain_study.py` 0.1.0 flew 24 steering settings on rover_pilot 0.7.0: cruise 0.6, 0.8 or 1.0; angular capped at 0.6 or 1.0; full angular at a 30° or 60° heading error; turn in place above 60° or 90°. Each setting flew 3 missions (the demo, 221 m; a zigzag, 236 m; a hairpin, 130 m) on 30 seeds, on a simulated rover that moves like the recorded ones (`SIM_REAL`) turning at 20, 30 or 45°/s per unit of `angular`, because the turn rate is only roughly known. That is 6,480 missions; it took under 6 minutes. Each setting is compared with the old defaults (cruise 0.6, cap 0.6, full turn at 60°, turn in place above 60°) seed by seed, with a sign test in each of the 9 mission × turn-rate groups.

Every setting completed all 270 of its missions.

| Setting | Mission time vs old defaults | Groups faster (p < 0.05) | Groups slower | Back-up moves per run | Refused reports per run |
|---|---|---|---|---|---|
| old defaults: cruise 0.6, cap 0.6, full turn 60°, turn in place > 60° | 1.000 | — | — | 1.62 | 0.09 |
| **cruise 0.6, cap 1.0, full turn 60°, turn in place > 90°** | **0.970** | **9 of 9** | 0 | **1.07** | 0.07 |
| cruise 0.6, cap 1.0, full turn 60°, turn in place > 60° | 0.975 | 9 of 9 | 0 | 1.23 | 0.09 |
| cruise 0.6, cap 0.6, full turn 60°, turn in place > 90° | 0.992 | 6 of 9 | 0 | 1.39 | 0.09 |
| cruise 0.6, full turn at 30° (any cap or threshold) | 1.053 to 1.072 | 0 | 7 to 9 of 9 | 1.57 to 2.03 | 0.06 to 0.09 |
| cruise 0.8, best setting (cap 1.0, full turn 60°, > 90°) | 0.744 | 9 of 9 | 0 | 0.44 | 0.06 |
| cruise 1.0, best setting (cap 1.0, full turn 60°, > 90°) | 0.614 | 9 of 9 | 0 | 0.38 | 0.03 |

At the measured 30°/s, the median times with the new setting against the old were 421.5 vs 429.0 s (demo), 219.6 vs 229.1 s (hairpin) and 431.2 vs 438.5 s (zigzag).

What this means:
- **At the same speed, sharper turns help, a little but consistently.** Letting `angular` reach 1.0 lets a real rover turn at about 30°/s instead of 18°/s, and turning in place only above 90° keeps it moving through medium turns. It was faster in all 9 groups, by about 3% overall, needed a third fewer back-up-and-turn moves, and lost nothing. So since v0.8.0, **a real rover is steered with a cap of 1.0 and turns in place only above 90°** (`ROVER_STEERING`). The simulator keeps its own defaults, so earlier simulator results don't move. `--max-angular` and `--turn-in-place` override either.
- **Reaching full angular at 30° of error is worse** than at 60°: it was slower in 7 to 9 of the 9 groups at cruise 0.6. With commands 0.8 s late and a turn rate of 30°/s, a stiffer gain overshoots.
- **Driving faster wins by far the most in simulation** (39% less time at cruise 1.0), but the cruise **stays at 0.6**. The simulator has no pedestrians, kerbs, slopes or rough ground, and the SDK suggests 0.3–0.5 for first tests. Speed is a choice for whoever runs the rover (`--cruise`), not something this study can settle.
- Limits: simulated rovers only, with a simple motion model fitted to the recorded rides; 3 missions; one GPS noise level. Real rovers may differ.

## The front camera on real frames: a first look (negative)

`free_space.py`, the camera layer behind `--vision`, had only seen frames the simulator drew. `frodo_frames.py` 0.1.0 read a few HLS video segments from 4 rides in parts 1 and 12 (about 55 MB) and ran the scan on one frame from each.

- **Which stream is which.** Each ride has two video streams. `uid_s_1000` is 1024 × 576 H.264 at 20 fps in 16.5 s segments, a normal wide-angle view ahead: the **front camera**. `uid_s_1001` is 540 × 360 with a circular fisheye image that shows the rover's own rails and flag mast, most likely the rear camera (the rides also log `rear_camera_timestamps`). The audio is AAC, 48 kHz mono.
- **Clocks.** A segment's file name is its start time in UTC, and it lines up with the control log's timestamps: on ride 18397 the control log ends at 04:32:23 UTC and the last video segment at about 04:32:25.
- **The result.** On the 11 front-camera frames, the scan saw less than 5 m clear ahead on 10 and less than 1.2 m on 4 (median 1.76 m). Looking at the frames ourselves (small thumbnails, our own judgement, not a labelled set), 9 or 10 of the 11 show an open path at least 5 m ahead. So on a real rover, `--vision` as it stands would slow, swerve or turn in place for nothing most of the time.
- **Why, from the frames.** Tree shadows across pavement; a sunlit, over-exposed paved plaza; and on one ride, parts of the rover's own body at the bottom edge of the frame. Those set the ground colour and block the bottom row, so all three frames of that ride read 0.53 m, the distance of the bottom row. On the fisheye stream every frame read 0.53 m, because the black border and the rover's body fill its bottom rows. The scan must only be used on the front camera.
- **What changed.** `free_space.py` 0.4.0 adds `skip_rows`, which leaves out the bottom rows where the rover's body shows, both from the ground colour and from the scan. Its defaults are unchanged, and `--vision` now says that it is experimental. `frodo_frames.py` 0.2.0 measures the phantom rate properly on up to 576 front-camera frames from all 24 parts, using what the driver did next as the label: the distance driven straight on afterwards (from the wheel RPMs) is a lower bound on how far the way ahead was clear. It compares 8 variants of the scan and checks the video clock against the wheel motion. A variant becomes the default only if it clearly lowers the phantom rate.
- Limits: 11 frames from 4 rides, judged by eye. This is why the measurement above is being run.

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
python gain_study.py --out-dir out-gains --seeds 30
```

Standard library only. Our `frodo_motion.py` run took 19 minutes and read about 317 MB. `out/summary.json` has every table and `out/rides.jsonl` has one line per ride. `sim_study.py` took about a minute and `gain_study.py` about 6 minutes; both write `report.md`, `summary.json` and `runs.jsonl`. The study numbers above were made with rover_pilot 0.7.0; v0.8.0 leaves the simulator's defaults as they were, so it gives the same numbers.

## Licence and credit

Data: FrodoBots-2K by FrodoBots Lab, CC BY-SA 4.0. The numbers and tables in this file derive from it and are shared under CC BY-SA 4.0. The code (`frodo_motion.py`, `sim_study.py`, `gain_study.py` and their tests) is Apache-2.0, like the rest of this repository. Not affiliated with FrodoBots, BitRobot or the Earth Rover Challenge organisers.
