# How Earth Rovers respond to commands: measured from FrodoBots-2K

MV2 of Munim, Inc., 14 October 2026. The analysis code (`frodo_motion.py`) was written with AI agents.

The Earth Rover SDK says `angular` is "rotation speed left/right (-1 to 1)" but not which way is positive. It doesn't give the speed at a given command or how late the GPS is. [FrodoBots-2K](https://huggingface.co/datasets/BitRobot/FrodoBots-2K) logs every command a human driver sent, the four wheel RPMs and the GPS for about 2,000 hours of Earth Rover rides. So the answers can be measured instead of guessed.

## What was measured

`frodo_motion.py` 0.1.0 read all 24 parts of the dataset over HTTP range requests, about 230 MB in all and no video. From each part it took 12 rides spread evenly through it: 288 rides, 279 long enough to use, about 1 million control rows. For every pair of GPS chords it lined the commands up with the GPS course and speed, at lags from -3 to 10 s. The full tables are in the job's `report.md`. The numbers below are for 2 s chords.

| Question | Answer | Evidence |
|---|---|---|
| Which way does a positive `angular` turn the rover? | **Left (counter-clockwise).** | When both were clearly non-zero (\|angular\| ≥ 0.2, course rate ≥ 5°/s), the GPS course turned left 440 times and right 57 times (89% left). The correlation of the course rate (clockwise positive) with angular is r = -0.243 (n = 24,446). |
| How late is the GPS? | About **1.5 s behind the wheels** and about **2.5 s behind the command**. | GPS speed tracks the mean wheel RPM best when the GPS is taken 1.5 s later (r = 0.686, n = 128,704). The course rate tracks angular best at 2.5 s (2.0 to 3.0 s are close). |
| How fast do the wheels respond? | About **0.8 s**. | Mean wheel RPM tracks the size of the command best 0.8 s later (r = 0.877, n = 486,900). 0.8 s plus 1.5 s matches the 2.5 s from command to GPS. |
| Speed at a given command? | About **0.8 m/s at full `linear`**, roughly in proportion below that. | 0.79 m/s per unit of linear, fitted through the origin (r = 0.698). Mean GPS speed by command band: 0.1–0.3 → 0.22 m/s; 0.3–0.5 → 0.30; 0.5–0.7 → 0.46; 0.7–0.9 → 0.60; 0.9–1.0 → 0.80 (sd about 0.3 m/s in each band). |
| Speed per wheel RPM? | **0.0067 m/s per RPM**, an effective wheel radius of **0.064 m**. | Fitted through the origin at a 1.5 s lag. |
| Turn rate while driving? | **At least about 23°/s** per unit of `angular`. | Slope of the course rate on angular, through the origin. This is a lower bound: GPS noise and 2 s chords smooth the turns out. |
| Are the logged RPMs signed? | **Yes.** | 4.4% of rows have a negative RPM. In 65% of the 39,560 spin-in-place rows (\|linear\| < 0.05, \|angular\| ≥ 0.3), the left wheels (rpm_1, rpm_3) and the right wheels (rpm_2, rpm_4) turn in opposite directions. |

## Other sources agree on the sign

The data alone shows how the Earth Rovers game app's commands moved the rovers. Two independent pieces of code show the SDK's `/control` uses the same sign:
- The SDK's own ROS2 bridge ([`examples/ros2/earth_rover_bridge.py`](https://github.com/frodobots-org/earth-rovers-sdk/tree/main/examples/ros2)) passes `cmd_vel` `angular.z` to `/control` `angular` unchanged. In ROS, a positive `angular.z` is counter-clockwise, a left turn.
- LeRobot's Earth Rover Mini+ keyboard teleop ([huggingface/lerobot](https://github.com/huggingface/lerobot)) sends a positive angular velocity for "turn left" (A, Q) and a negative one for "turn right" (D, E). Its robot class passes the value to `/control` unchanged.

So earth-rover-pilot v0.6.0 drives an uncalibrated real rover with a positive `angular` turning left. Before v0.6.0 it assumed right, and in the simulator a rover with the opposite sign never leaves its start. `--calibrate` still measures the sign on the rover and overrides this default.

## What it means for a pilot

- **Speed.** A rover at full command covers about 0.8 m/s, not the 1.2 m/s the simulator assumes. A 50-mile marathon at 0.6 to 0.8 m/s is 28 to 37 hours of driving. That is in line with the human teams' 29 h 38 min.
- **GPS lag.** GPS shows a turn about 2.5 s after it is commanded. A controller that steers on GPS course alone keeps turning for 2.5 s too long and overshoots. The pilot steers on the compass and learns the compass bias only on straight stretches. That is the right shape, and the lag argues for keeping it.
- **Odometry.** An effective wheel radius of 0.064 m confirms the 0.065 m that earlier visual-SLAM work on this dataset assumed ([SlamMate/vSLAM-on-FrodoBots-2K](https://github.com/SlamMate/vSLAM-on-FrodoBots-2K)). Wheel odometry from RPMs can fill the 1 s gaps between GPS fixes.

## Limits

- These are human-driven rides from the Earth Rovers game (Earth Rover Zero era, early 2024), logged on the rover. The SDK, newer rovers and other firmware may behave differently. The sign is backed by the SDK's and LeRobot's code; the speeds and lags are only from this data.
- 288 of the 8,906 rides that have control and GPS files were sampled, 12 per part, so every part counts equally rather than every hour.
- Course rates from 1 Hz GPS are noisy. The turning correlation is weak (r = -0.24), even though the sign test is lopsided (440 to 57). The turn rate is a lower bound.
- The control and GPS clocks were taken as they are. The results line up across lags (0.8 s + 1.5 s ≈ 2.5 s), which suggests no large offset in the sampled rides.
- Prior work: the University of Amsterdam report "Automatic Control, Calibration and Recording for the FrodoBots" (Zhang and Visser, 2024) describes the Earth Rover Zero's sensors and their rates (GPS 1 Hz, gyroscope 1 Hz, accelerometer 100 Hz). We could not read its full text, so it may cover some of the same ground. As far as we found, no earlier work has published these numbers measured across the whole dataset, together with the code to reproduce them.

## Reproduce it

```
python frodo_motion.py --out-dir out --rides-per-part 12
```

Standard library only. Our run took 12 minutes and read about 230 MB. `out/summary.json` has every table and `out/rides.jsonl` has one line per ride. A version that also reads the IMU (which gyroscope axis is yaw, its units and the turn rate while spinning in place) is being run next.

## Licence and credit

Data: FrodoBots-2K by FrodoBots Lab, CC BY-SA 4.0. The numbers and tables in this file derive from it and are shared under CC BY-SA 4.0. The code (`frodo_motion.py`, `test_frodo_motion.py`) is Apache-2.0, like the rest of this repository. Not affiliated with FrodoBots, BitRobot or the Earth Rover Challenge organisers.
