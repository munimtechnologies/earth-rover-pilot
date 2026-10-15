# How Earth Rovers respond to commands: measured from FrodoBots-2K

MV2 of Munim, Inc., 14–15 October 2026. The analysis code (`frodo_motion.py`, `sim_study.py`, `gain_study.py`, `frodo_frames.py`, `gps_noise_study.py`) was written with AI agents.

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

## GPS error that drifts instead of jittering (simulation)

The simulator gave every GPS fix its own independent 1.5 m error. A real receiver's error is correlated in time: it wanders a few metres off and stays there for tens of seconds (a Gauss-Markov process is the usual model). `gps_noise_study.py` 0.1.0 flew the same 3 missions on 30 seeds on rover_pilot 0.8.0 (the simulator and pilot logic are unchanged since), steered as a real rover is (`ROVER_STEERING`), under 7 GPS error models: independent fixes with 1.5 or 3 m per axis, and drifting error of 1.5, 3 or 6 m per axis with a correlation time T of 10, 30 or 120 s. It used 3 rovers: one that moves like the recorded ones (`SIM_REAL`, 30°/s per unit), the same with a GPS fix only every 2 s, and a stand-in for the Earth Rover Mini+ that the challenge now uses (a fix every 2 s, as the SDK README says, and 1.11 m/s at full `linear`, its 4 km/h top speed; that the top speed comes at full `linear` is an assumption). It also flew 4 pilot variants: no GPS smoothing (alpha 1), heavier smoothing (alpha 0.15), and reporting checkpoints from 7 or 12 m instead of 10. That is 9,450 missions; it took 14 minutes, and its 11 tests passed.

**Every one of the 9,450 missions was completed**, under every error model, including 6 m of drifting error.

The checkpoint server judges the rover's reported GPS, as the real one does, so the study also recorded how far the rover truly was from each checkpoint when the server credited it.

| Rover | GPS error | Time vs 1.5 m white | Compass bias error, median / p90 | Credits with the rover truly beyond 15 m |
|---|---|---|---|---|
| recorded-like, 1 s fixes | white 1.5 m (the old simulator) | 1.000 | 2.2° / 5.1° | 0 of 390 |
| recorded-like, 1 s fixes | white 3 m | 1.100 | 8.2° / 29.1° | 22 of 390 (6%) |
| recorded-like, 1 s fixes | drift 1.5 m, T 30 s | 1.030 | 2.1° / 5.6° | 0 of 390 |
| recorded-like, 1 s fixes | drift 3 m, T 10 s | 1.123 | 6.7° / 16.5° | 16 of 390 (4%) |
| recorded-like, 1 s fixes | drift 3 m, T 30 s | 1.083 | 5.0° / 12.6° | 8 of 390 (2%) |
| recorded-like, 1 s fixes | drift 3 m, T 120 s | 1.032 | 2.2° / 6.8° | 12 of 390 (3%) |
| recorded-like, 1 s fixes | drift 6 m, T 30 s | 1.170 | 10.9° / 30.6° | 92 of 390 (24%) |
| Mini+ stand-in, 2 s fixes | white 1.5 m | 1.000 | 3.0° / 8.0° | 0 of 390 |
| Mini+ stand-in, 2 s fixes | drift 3 m, T 10 s | 1.047 | 4.5° / 11.8° | 10 of 390 (3%) |
| Mini+ stand-in, 2 s fixes | drift 3 m, T 30 s | 1.028 | 4.1° / 8.3° | 10 of 390 (3%) |
| Mini+ stand-in, 2 s fixes | drift 3 m, T 120 s | 1.022 | 2.2° / 5.4° | 11 of 390 (3%) |
| Mini+ stand-in, 2 s fixes | drift 6 m, T 30 s | 1.101 | 9.4° / 21.5° | 60 of 390 (15%) |

What it shows:
- **How fast the error moves matters more than how big it is.** The pilot learns the compass bias by fitting a line through the fixes of a straight stretch. 3 m of error that drifts over 120 s barely bends that line (bias error 2.2°, 3% slower); the same 3 m changing over 10 s bends it (6.7°, 12% slower), about as much as 3 m of independent jitter. The slowdowns come with the wrong compass bias: the rover heads a few degrees off and corrects later.
- **With large drifting error, many credits come when the rover is truly beyond the tolerance.** The server can't tell, because it judges the same GPS. At 6 m of drift, 15–24% of the credited checkpoints were credited with the rover more than 15 m from them in truth, and some more than 28 m. With 1.5 m of error, none were. In the real challenge this would apply to AI and human drivers alike: the ~15 m tolerance is 15 m from where the GPS says, not from where the rover is.
- **Keep the smoothing.** Without it (alpha 1) the pilot was slower with 14 of the 21 rover × error combinations, faster with 1, and needed up to ten times as many back-up moves (10.9 against 1.1 per run on the recorded-like rover with 1.5 m jitter). Heavier smoothing (alpha 0.15) was mixed: faster with 3 combinations, slower with 8, no clear difference with 10. The shipped alpha 0.3 stays.
- **Reporting from 12 m instead of 10 was faster with every rover and error model**, in all 63 mission groups (sign test p < 0.05 in each), by about 4–7%. On the 2 s rovers it never added a refused report. On the 1 s rover with 3 m jitter, refused reports rose from 0.36 to 0.59 per run, and with every error model more credits came with the rover truly beyond 15 m (at 3 m drift, T 30 s: 40 of 390 against 8). Reporting from 7 m was slower everywhere (7–12%) and cut those far credits by half or more, but didn't end them (41 of 390 at 6 m drift on the 1 s rover). The default **stays at 10 m** until a real rover shows how its server answers early reports; `--report-radius 12` is there for whoever wants the time.
- **A fix only every 2 s costs a little.** On the recorded-like rover with 1.5 m jitter, 2 s fixes made the missions slower by a median of 4.5–10 s (p = 0.04, 0.008 and 0.016 on the 3 missions). The Mini+ stand-in is much faster overall only because it is assumed to drive at 1.11 m/s.
- **Which row is the real one isn't known yet.** `frodo_gps.py`, which measures the error of the recorded rovers' GPS against their wheel sensors (standing still and driving straight), is queued. Its answer picks the model the simulator should use.
- Limits: simulated rovers only; 3 short missions (130–236 m); Gauss-Markov error, the same on both axes; the Mini+ speed is assumed. The server in the simulator answers every report at once and never penalises a refused one.

## The front camera on real frames: phantom obstacles, measured

`free_space.py`, the camera layer behind `--vision`, scans each front-camera frame for where the ground stops looking like the patch just ahead of the rover. It had only seen frames the simulator drew.

**A first look (frodo_frames.py 0.1.0, negative).** On 11 front-camera frames from 4 rides, the default scan saw less than 5 m clear on 10, though by eye 9 or 10 showed an open path. The causes were tree shadows, an over-exposed plaza and the rover's own body at the bottom of the frame. That run also found which stream is which: `uid_s_1000` is the 1024 × 576 front camera (H.264, 20 fps, 16.5 s segments) and `uid_s_1001` a 540 × 360 fisheye that shows the rover's rails and mast, most likely the rear camera. A segment's file name is its start time in UTC, which lines up with the control log.

**The measurement (frodo_frames.py 0.2.0).** It took 569 front-camera frames from 48 rides, 2 from each of the 24 parts, at 2, 7 and 12 s into 4 segments per ride (708 MB read, 23 minutes). 493 frames had control data at the frame's time. The label is what the driver did next: from the frame's time it adds up the distance driven (from the wheel RPMs, 0.0067 m/s per RPM) until the driver turned, stopped, reversed or 15 s passed. That distance is a lower bound on how far the way straight ahead was clear, because the human drove it. A **phantom stop** is a frame where the scan saw less than 1.2 m clear straight ahead (the guard turns in place) but the driver then went at least 2 m straight. A **phantom swerve** is less than 5 m clear (the guard bends or slows) when the driver went at least 5.5 m. Eight settings of the scan were fixed before the run. Wilson 95% intervals:

| Setting | Phantom stops (of 110) | 95% CI | Phantom swerves (of 28) | 95% CI |
|---|---|---|---|---|
| default | 39 (35%) | 27–45% | 22 (79%) | 61–90% |
| skip3 (leave out the 3 bottom rows) | 38 (35%) | 26–44% | 22 (79%) | 61–90% |
| skip5 | 34 (31%) | 23–40% | 23 (82%) | 64–92% |
| shadow (ground from 0.2× to 2.5× the patch brightness) | 18 (16%) | 11–24% | 11 (39%) | 24–58% |
| wide (colour tolerance 0.05, up to 0.12) | 35 (32%) | 24–41% | 19 (68%) | 49–82% |
| gap4 (4 non-ground rows in a row to call an obstacle) | 33 (30%) | 22–39% | 14 (50%) | 33–67% |
| skip3 + shadow + gap4 | 13 (12%) | 7–19% | 4 (14%) | 6–32% |
| **skip3 + shadow + wide + gap4** | **9 (8%)** | **4–15%** | **2 (7%)** | **2–23%** |

- **Shadows matter most**, and the changes add up. Allowing darker and brighter ground alone halves the phantom stops. With all four changes, phantom stops fall from 35% to 8% and phantom swerves from 79% to 7%. Neither interval overlaps the default's.
- **By eye.** We looked at 16 of the frames. Where the default stopped and the new setting didn't, the frames show open paths with tree shadows across them, sunlit gravel and a rover's wheels at the bottom edge. The new setting's remaining phantom stops that we looked at were a night frame with headlight glare and raindrops on the lens, a deep shadow band with grass at the path's edge, a dark wet patch on the path, and a person in a wheelchair close on the right. The last two may well be things a rover should slow for. One frame shows the camera turned 90° (the rover had tipped over), and the new setting read it as clear. The camera layer can't tell that a rover has fallen; the pilot's stuck check has to.
- **What we can't say yet: how many real obstacles it misses.** The data has no obstacle labels. 14 frames came just before the driver stopped or turned hard while moving. The default called 12 of them blocked and the new setting 5. But of the 6 such frames we looked at, 5 show an open path, so drivers stopped or turned there for other reasons, and these frames say little about missed obstacles.
- **Clock check: inconclusive.** How much the picture changes in half a second correlates only weakly with wheel speed at any clock offset from -4 to 4 s (r = 0.10 to 0.18, best at -3.5 s), so it neither confirms nor rules out an offset between the video and control clocks. Labelled at the -3.5 s offset instead, the results are about the same: phantom stops 40% (default) against 6% (new setting).
- **What changed.** `free_space.py` 0.5.0 adds `REAL_ROVER`, the skip3 + shadow + wide + gap4 settings. Since v0.9.0, `--vision` on a real rover uses them (`make_vision`); `--vision-plain` goes back to the old defaults. The simulator keeps the defaults, so simulated results don't move. `--vision` stays marked experimental.
- **Limits.** 493 frames from 48 rides of Earth Rover Zero-era rovers; the Mini+ camera may differ. The setting was picked as the best of 8 on these same frames, which flatters it a little. A check on other rides and other frame times (`--rides-per-part 3 --offsets 4,9,14`) is queued. The study fits a fresh ground model to each frame, while the guard on a rover blends it over time. Driving on is a lower bound on clear space, so a few "phantoms" may be real obstacles the driver steered past within the corridor. No real rover has been driven with it yet.
- **Prior art.** We found no published evaluation of an obstacle or free-space check on FrodoBots-2K, nor any use of the drivers' own commands as labels for one. The dataset card lists no obstacle annotations.

## Limits

- These are human-driven rides from the Earth Rovers game (Earth Rover Zero era, early 2024), logged on the rover. The SDK, newer rovers and other firmware may behave differently. The sign is backed by the SDK's and LeRobot's code; the speeds, turn rates and lags are only from this data.
- 288 of the 8,906 rides that have control and GPS files were sampled, 12 per part, so every part counts equally rather than every hour. The gyroscope figures come from the same 279 rides.
- Course rates from 1 Hz GPS are noisy. The turning correlation is weak (r = -0.24), even though the sign test is lopsided (440 to 57). The GPS turn rate is a lower bound.
- The gyroscope's units are inferred, not documented. Degrees per second is the only reading that fits the GPS, but the size could be off by the GPS smoothing factor.
- The control and GPS clocks were taken as they are. The results line up across lags (0.8 s + 1.5 s ≈ 2.5 s), which suggests no large offset in the sampled rides.
- Prior work: the University of Amsterdam report "Automatic Control, Calibration and Recording for the FrodoBots" (Zhang and Visser, 2024) describes the Earth Rover Zero's sensors and their rates (GPS 1 Hz, gyroscope 1 Hz, accelerometer 100 Hz) and tests visual SLAM, object detection and depth models on the dataset. We could not read its full text, so it may cover some of the same ground. As far as we found, no earlier work has published these numbers measured across the whole dataset, together with the code to reproduce them.

## Reproduce it

```
python frodo_motion.py --out-dir out --rides-per-part 12 --imu-per-part 1 --gyro-max-mb 40
python sim_study.py --out-dir out-sim --seeds 30
python gain_study.py --out-dir out-gains --seeds 30
python gps_noise_study.py --out-dir out-gps-noise --seeds 30
python frodo_frames.py --out-dir out-frames --parts all --rides-per-part 2 --segments 4 --offsets 2,7,12
```

`frodo_motion.py`, `sim_study.py`, `gain_study.py` and `gps_noise_study.py` use the standard library only. Our `frodo_motion.py` run took 19 minutes and read about 317 MB. `out/summary.json` has every table and `out/rides.jsonl` has one line per ride. `sim_study.py` took about a minute, `gain_study.py` about 6 minutes and `gps_noise_study.py` about 14; each writes `report.md`, `summary.json` and `runs.jsonl`. The study numbers above were made with rover_pilot 0.7.0 (`sim_study.py`, `gain_study.py`) and 0.8.0 (`gps_noise_study.py`); later versions leave the simulator and the pilot's steering and GPS handling as they were, so they give the same numbers. `frodo_frames.py` needs ffmpeg and Pillow; it writes `report.md`, `summary.json`, `frames.jsonl` (every frame's scan results and label) and a small thumbnail of each frame.

## Licence and credit

Data: FrodoBots-2K by FrodoBots Lab, CC BY-SA 4.0. The numbers and tables in this file derive from it and are shared under CC BY-SA 4.0. The code (`frodo_motion.py`, `sim_study.py`, `gain_study.py`, `gps_noise_study.py`, `frodo_frames.py` and their tests) is Apache-2.0, like the rest of this repository. Not affiliated with FrodoBots, BitRobot or the Earth Rover Challenge organisers.
