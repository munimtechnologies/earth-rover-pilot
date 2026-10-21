# How Earth Rovers respond to commands: measured from FrodoBots-2K

MV2 of Munim, Inc., 14–16 October 2026. The analysis code (`frodo_motion.py`, `frodo_frames.py`, `frodo_gps.py`, `frodo_odometry.py`, `frodo_compass.py`, `frodo_compass_live.py`, `sim_study.py`, `gain_study.py`, `gps_noise_study.py`, `dead_reckon_study.py`, `pace_study.py`) was written with AI agents. Every study from `frodo_gps.py` on had its predictions and its decision rule written down before it ran; the grades below say which predictions held.

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
- **Odometry.** An effective wheel radius of 0.064 m confirms the 0.065 m that earlier visual-SLAM work on this dataset assumed ([SlamMate/vSLAM-on-FrodoBots-2K](https://github.com/SlamMate/vSLAM-on-FrodoBots-2K)). Wheel odometry from RPMs can fill the gaps between GPS fixes; "Driving between GPS fixes" below measures how well, and "Does the compass carry the wheels?" which heading to carry them along.

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

So `--gps-lag` stays **off by default**. It is there for experiments on a real rover. The likely reason it doesn't help: the pilot already steers on the compass, so a late position only matters for the aim point, and at 0.5 m/s, 1.5 s is under a metre. This is a simulation result with a simple motion model. A real rover may differ. (Dead reckoning, below, carries the position forward on the wheels instead, and can't be combined with `--gps-lag`.)

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
- **How fast the error moves matters more than how big it is.** The pilot learns the compass bias by fitting a line through the fixes of a straight stretch. 3 m of error that drifts over 120 s barely bends that line (bias error 2.2°, 3% slower); the same 3 m changing over 10 s bends it (6.7°, 12% slower), about as much as 3 m of independent jitter. The slowdowns come with the wrong compass bias: the rover heads a few degrees off and corrects later. (The next section shows that fixing the bias alone doesn't win the time back.)
- **With large drifting error, many credits come when the rover is truly beyond the tolerance.** The server can't tell, because it judges the same GPS. At 6 m of drift, 15–24% of the credited checkpoints were credited with the rover more than 15 m from them in truth, and some more than 28 m. With 1.5 m of error, none were. In the real challenge this would apply to AI and human drivers alike: the ~15 m tolerance is 15 m from where the GPS says, not from where the rover is.
- **Keep the smoothing.** Without it (alpha 1) the pilot was slower with 14 of the 21 rover × error combinations, faster with 1, and needed up to ten times as many back-up moves (10.9 against 1.1 per run on the recorded-like rover with 1.5 m jitter). Heavier smoothing (alpha 0.15) was mixed: faster with 3 combinations, slower with 8, no clear difference with 10. The shipped alpha 0.3 stays.
- **Reporting from 12 m instead of 10 was faster with every rover and error model**, in all 63 mission groups (sign test p < 0.05 in each), by about 4–7%. On the 2 s rovers it never added a refused report. On the 1 s rover with 3 m jitter, refused reports rose from 0.36 to 0.59 per run, and with every error model more credits came with the rover truly beyond 15 m (at 3 m drift, T 30 s: 40 of 390 against 8). Reporting from 7 m was slower everywhere (7–12%) and cut those far credits by half or more, but didn't end them (41 of 390 at 6 m drift on the 1 s rover). The default **stays at 10 m** until a real rover shows how its server answers early reports; `--report-radius 12` is there for whoever wants the time.
- **A fix only every 2 s costs a little.** On the recorded-like rover with 1.5 m jitter, 2 s fixes made the missions slower by a median of 4.5–10 s (p = 0.04, 0.008 and 0.016 on the 3 missions). The Mini+ stand-in is much faster overall only because it is assumed to drive at 1.11 m/s.
- **Which row is the real one?** None of them: "How noisy a real Earth Rover's GPS is" below measures the recorded rovers' GPS, and every error model here is harsher than what it found. These rows are stress tests.
- Limits: simulated rovers only; 3 short missions (130–236 m); Gauss-Markov error, the same on both axes; the Mini+ speed is assumed. The server in the simulator answers every report at once and never penalises a refused one.

## Can a smarter compass-bias fit win back the time lost to drifting GPS? No (simulation)

The section above found that drifting GPS error slows the pilot and comes with a wrong compass bias. The obvious next step was to make the bias fit harder to fool. `gps_noise_study.py` 0.2.0 flew the same 3 missions on 30 seeds on rover_pilot 0.9.2 with the recorded-like rover (1 s fixes) and the Mini+ stand-in (2 s fixes, 1.11 m/s). It used 5 GPS error models (white 1.5 and 3 m; drift 3 m with T 10 s and 30 s; drift 6 m with T 30 s), and the shipped fit plus 7 variants of it:
- **residual gate** (`max_residual_m` 2 or 3): throw away a straight stretch if its fixes stray more than 2 or 3 m from the fitted line;
- **minimum stretch** (`min_move_m` 20 or 30): fit only over stretches at least 20 or 30 m long;
- **weighting** (`weigh`): give longer, cleaner stretches more say in the bias;
- weighting combined with a 20 m minimum stretch or a 3 m residual gate.

That is 7,200 missions. It took 7 minutes, and its 13 tests passed. 7,198 were completed. The 2 failures were both on the recorded-like rover with 3 m jitter, one with the 2 m gate and one with weighting plus the 3 m gate. The prediction, written before the run, was that the residual gate would cut the bias error under fast-drifting error and win back some of the time; it cut the median a little (2 m gate) or not at all (3 m gate) and won back no time.

**The shipped pilot's numbers reproduced exactly.** Under every error model its rows match the 0.1.0 study (on rover_pilot 0.8.0) to the last digit: 1.123 time ratio, 6.7° / 16.5° bias error and 16 far credits at 3 m drift with T 10 s; 1.170, 10.9° / 30.6° and 92 at 6 m drift. Nothing between 0.8.0 and 0.9.2 changed how it drives in simulation.

| Rover | GPS error | Fit | Time vs 1.5 m white | Fits kept / thrown away per run | Compass bias error, median / p90 | Verdict vs shipped |
|---|---|---|---|---|---|---|
| recorded-like | white 1.5 m | shipped | 1.000 | 13.4 / 0 | 2.2° / 5.1° | — |
| recorded-like | white 1.5 m | 20 m stretch | 0.999 | 5.6 / 0 | 0.7° / 2.5° | worse (1 of 3 missions slower) |
| recorded-like | white 1.5 m | 30 m stretch | 1.027 | 2.7 / 0 | 0.5° / 1.4° | worse (3 of 3 slower) |
| recorded-like | white 3 m | shipped | 1.100 | 14.0 / 0 | 8.2° / 29.1° | — |
| recorded-like | white 3 m | 2 m gate | 1.130 | 3.7 / 12.8 | 16.5° / 33.2° | worse (1 mission lost a seed) |
| recorded-like | white 3 m | 20 m stretch | 1.085 | 2.8 / 0 | 2.9° / 8.3° | no clear difference (1 of 3 faster) |
| recorded-like | drift 3 m, T 10 s | shipped | 1.123 | 9.1 / 0 | 6.7° / 16.5° | — |
| recorded-like | drift 3 m, T 10 s | 2 m gate | 1.123 | 8.7 / 0.3 | 5.8° / 19.1° | no clear difference |
| recorded-like | drift 3 m, T 10 s | 3 m gate | 1.123 | 9.1 / 0 | 6.7° / 16.5° | no clear difference (identical) |
| recorded-like | drift 3 m, T 10 s | 30 m stretch | 1.144 | 1.2 / 0 | 5.8° / 14.0° | worse (1 of 3 slower) |
| recorded-like | drift 6 m, T 30 s | shipped | 1.170 | 10.6 / 0 | 10.9° / 30.6° | — |
| recorded-like | drift 6 m, T 30 s | weighting | 1.177 | 11.1 / 0 | 14.3° / 31.3° | no clear difference |
| Mini+ stand-in | drift 3 m, T 10 s | shipped | 1.047 | 10.3 / 0 | 4.5° / 11.8° | — |
| Mini+ stand-in | drift 3 m, T 10 s | 2 m gate | 1.047 | 9.7 / 0.7 | 4.2° / 13.3° | no clear difference |
| Mini+ stand-in | drift 6 m, T 30 s | shipped | 1.101 | 9.7 / 0 | 9.4° / 21.5° | — |
| Mini+ stand-in | drift 6 m, T 30 s | 30 m stretch | 1.129 | 1.8 / 0 | 6.0° / 16.7° | no clear difference |

(Verdicts: a paired sign test per seed on each of the 3 missions; "faster" or "slower" means p < 0.05. All 80 rows are in the study's report.md.)

What it shows:
- **No variant was better anywhere.** Across 70 comparisons (7 variants × 2 rovers × 5 error models) no variant made any mission group reliably faster without making another slower or losing a seed. The shipped fit stays.
- **A residual gate can't see drifting error.** Drifting error moves slowly, so the fixes along a stretch lie close to a straight line, just a line pointing the wrong way. Under drifting error the 3 m gate threw away 0 to 0.11 fits per run (none at all with the recorded-like rover at 3 m drift, T 10 s), so it changed nothing there. Only under independent 3 m jitter did it reject some (2.1-2.8 per run), with no clear effect. The 2 m gate rejected more, mostly under independent 3 m jitter, where the bad stretches it rejected weren't the problem. There it kept too few fits and the bias error doubled (8.2° → 16.5°).
- **Longer stretches give a much more accurate compass bias, but not a faster rover.** Fitting only over stretches of 20 or 30 m cut the bias error about threefold under independent error: 2.2° → 0.7° / 0.5° with 1.5 m jitter and 8.2° → 2.9° / 1.9° with 3 m jitter on the recorded-like rover; 3.0° → 1.1° / 0.8° on the Mini+ stand-in. But it fits 2-8 times less often, so the early legs run before any bias is learned. The 30 m version was slower in 8 of the 10 rover × error combinations, the 20 m one in 4.
- **This corrects the reading of the section above.** That section tied the slowdown under drifting error to the wrong compass bias. Fixing the bias doesn't remove the slowdown: on the Mini+ stand-in with 6 m drift the 30 m stretch cut the median bias error from 9.4° to 6.0°, and the missions were no faster (time ratio 1.129 against 1.101, no clear difference). The time is lost to the position error itself, as the rover chases a GPS position that wanders, not to the heading. Better position is the place to look, not a cleverer bias fit; the wheel-odometry and dead-reckoning sections below do that.
- **Weighting made no clear difference** under any model (0 better, 0 worse); its median bias error moved by up to ±3.4° either way.
- Limits: simulated rovers only; 3 short missions (130–236 m); Gauss-Markov error, the same on both axes; the Mini+ speed is assumed; a sign test on 30 seeds can miss small differences, so "no clear difference" doesn't mean "no difference".

## How noisy a real Earth Rover's GPS is (FrodoBots-2K)

The simulator draws every fix with fresh, independent 1.5 m noise per axis, and the drifting-GPS sections above tried 3 m and 6 m of slowly drifting error. Neither came from a real rover. `frodo_gps.py` measures the GPS against the wheels. When all four wheels read 0 for 30 s or more, the rover is standing still, so any movement in the fixes is error. When both sides' wheels turn equally with no turn command, it is driving straight, so the fixes should lie on a line at the wheel speed. It sampled 25 rides from each of the 24 parts of FrodoBots-2K (600 rides, 567 with enough data, 80.3 hours of GPS, 227 MB read).

The first run (0.1.0) predicted it would pick a noise model for the simulator. It didn't: its automatic fit had a relative error of 0.77, because one ride out of 567 (ride 30518, 43 minutes) accounts for all six still periods where a fix strayed more than 5 m, and for 30 of the 33 jumps logged while the wheels were still. In those periods the wheels and the commands read 0, but the GPS moved steadily, up to 273 m from the period's mean at about walking pace. That isn't GPS noise: either the rover was carried or its wheel log failed. A second run (0.2.0, same rides) left out still periods whose fixes spread more than 20 m, a rule written down before it ran, along with the prediction that it would drop exactly those 6 periods (it did), that the clean error 60 s apart would be at most 3 m (it was 1.5 m) and that a Gauss-Markov fit would then give at most 1.5 m per axis (it didn't; see below).

What it shows:
- **While driving, the fixes are smooth.** In 997 ten-second chunks of straight driving (median 0.62 m/s by the wheels), the fixes scatter only 0.22 m RMS sideways about a straight line (median chunk 0.17 m, 90th percentile 0.33 m). The simulator's independent 1.5 m noise per axis would scatter them about 1.4 m, about six times more. A line fit can't see an error that drifts slowly or stays put, so this says nothing about how far off the whole line is.
- **GPS speed matches the wheels.** In the median chunk the GPS speed is 0.975 times the speed from the wheel RPMs (middle half 0.82 to 1.10). The wheel scale measured earlier (0.064 m wheel radius, 0.00668 m/s per RPM) agrees with the GPS within 2.5%.
- **The position updates less often than the log suggests.** The log has 0.97 rows a second, but the reported position changes only 0.65 times a second. 147 gaps of over 3 s (1.8 an hour) add up to 3.3% of the time.
- **A still rover's position mostly doesn't move at all.** 229 still periods of 30 s or more (4.9 hours, 150 rides): in the median period the fixes wandered 0.09 m RMS about their mean, and 94 periods (41%) never moved by even 5 cm. The receiver appears to hold its position while the rover stands still.
- **Without the faulty ride, a still rover's GPS drifts slowly and stays within a few metres.** Leaving out the 6 periods of ride 30518, 223 periods in 150 rides remain, and no still fix was more than 5 m from its period's mean. The RMS distance between two fixes of a still rover is **0.14 m 1 s apart, 0.52 m 10 s apart, 1.50 m 60 s apart, 2.21 m 2 min apart and 2.74 m 5 min apart** (95% intervals from resampling rides: 0.10-0.18, 0.39-0.65, 0.97-1.92, 1.49-2.82, 1.44-3.12 m). Leaving out the 94 periods where the position never moved at all gives nearly the same numbers (0.61 m at 10 s, 1.61 m at 60 s), so the receiver's freezing doesn't explain them.
- **No single noise model fits.** The error still grows at 5 min, so a Gauss-Markov model fitted to it puts the correlation time at the edge of the search (5,000 s) and can't say how large the error gets in the end; only the ratio sigma²/T is pinned down (about 0.006 m² per s per axis). By the rule set before the run, no simulator noise setting is adopted. `frodo_gps.py` 0.2.1 marks such a fit as not usable (`fit_ok` now also needs both parameters inside their search range).
- **The simulator's noise settings are all harsher than this.** Independent 1.5 m noise per axis gives 3.0 m between any two fixes, about 6 times the measured 0.52 m at 10 s. The drifting scenarios used in the sections above are harsher still at short range: 3 m with a 10 s correlation time gives 4.8 m at 10 s, and 3 m with 30 s gives 3.2 m at 10 s and 5.6 m at 60 s, against 0.5 m and 1.5 m measured. So the simulated results in this file are stress tests, not estimates of what a real rover would see.
- **Jumps are rare.** 68 jumps of over 5 m, faster than 3 m/s, in 80 hours. 35 of them are in ride 30518; the other 33 are spread over the remaining 79.6 hours, about 0.4 an hour, median size 6.1 m.

What this means for the pilot: random wander alone shouldn't cost a checkpoint. Over a 5-minute leg a still rover's fixes moved about 2.7 m RMS, well inside the 15 m radius, and fixes while driving lie within a few tenths of a metre of a line. What this study can't measure is a steady offset (the whole track shifted by a few metres), because a still rover's mean and a driving rover's line both absorb it, and how far the drift goes beyond 5 minutes.

Limits: the error is measured relative to the rover's own mean or line, not to a surveyed truth, so a constant offset is invisible. Still periods are 30 s to about 5 min long and partly frozen by the receiver, which may hide error that a moving rover sees. The data are from the Earth Rover Zero era (2024), not the current Mini+. 25 rides per part, chosen evenly by ride name. The 20 m "travelled" rule was chosen after seeing ride 30518.

Prior art: Zhang & Visser 2024 ("Automatic Control, Calibration and Recording for the FrodoBots", University of Amsterdam, IRL-UVA-24-01) list the usual GPS error sources for this rover and quote the challenge's 15 m checkpoint tolerance, but give no measured accuracy or drift. MBRA (arXiv 2505.05592) models a random-walk GPS bias in its filter without publishing error figures. As far as found, this drift curve is the first measured on the Earth Rover.

## Driving between GPS fixes: wheels beat the GPS's own velocity (FrodoBots-2K)

An Earth Rover's position updates about 0.65 times a second, with gaps of over 3 s about twice an hour, and the GPS runs about 1.5 s behind the wheels. Between fixes the pilot can hold the last fix, carry it forward at the GPS's own velocity, or dead-reckon from the wheels. `frodo_odometry.py` measures which is best on real rides. From every fix while the rover was moving (the anchor), each method predicts where the next fix 1 to 30 s later will be, and the miss is the distance to that fix. It sampled 20 rides from each of the 24 parts (480 rides, 449 analysed, 63.1 hours of GPS, 253,942 anchor–target pairs, 383 MB read). Its unit tests passed. The prediction, written before the run: the pilot adopts wheel dead reckoning only if it beats GPS-only position.

The methods:
- **hold**: the last fix stays put.
- **gps_cv**: the last fix, carried on at the velocity of the last two fixes.
- **odo_course**: distance from the wheel RPMs (0.00668 m/s per RPM), along the last GPS course.
- **odo_gyro**: the same, turning by the integrated gyroscope (×0.5, ×1, ×1.5, and with the sign flipped).
- **odo_cmd**: the same, turning by the angular command at 20, 30 or 40°/s per unit.

Median miss in metres, all anchors (95% intervals by resampling rides are in the study's report):

| Method | 2 s | 5 s | 10 s | 30 s |
|---|---|---|---|---|
| hold | 1.57 | 3.73 | 7.31 | 20.37 |
| gps_cv | 0.56 | 1.24 | 2.53 | 8.63 |
| **odo_course** | **0.51** | **1.04** | **1.93** | **5.57** |
| odo_gyro ×1 | 0.55 | 1.19 | 2.33 | 7.69 |
| odo_gyro ×0.5 | 0.51 | 1.06 | 2.00 | 6.16 |
| odo_cmd 20°/s | 0.50 | 1.02 | 1.90 | 5.93 |
| odo_cmd 30°/s | 0.50 | 1.03 | 1.94 | 6.43 |

- **Wheels win, and the gap grows with time.** Wheel distance along the last GPS course misses the next fix by 24% less than the GPS's own velocity at 10 s and 35% less at 30 s. Relative to holding the last fix, its median miss is 0.26–0.27 of hold's at 10 s against 0.34–0.36 for the GPS velocity (rides resampled); the intervals don't overlap.
- **The gyroscope makes it worse, not better.** Turning by the gyroscope at face value misses more than ignoring turns altogether (2.33 against 1.93 m at 10 s), even on anchors where the rover turned 30° or more (2.95 against 2.17 m). Half the gyroscope's turn does better than the full turn, and the flipped sign does worst, so the sign is right but the size is too large compared with what the GPS course shows. Two likely reasons: the gyroscope is logged about once a second, and the GPS course that serves as the reference smooths turns. This study can't tell which.
- **The turn command helps a little on turns.** At 20°/s per unit, the command beats the plain course while turning (2.07 against 2.17 m at 10 s), but it's no better overall. The earlier measurement of about 30°/s per unit came from GPS course rates and may read high for the same smoothing reason.
- **Decision.** The pilot got a dead reckoner that carries the position forward between fixes by wheel distance, with no gyroscope. Which heading to carry it along was then settled in simulation and on recorded rides (the next three sections).

Limits: the reference is the next GPS fix, not surveyed truth, so this measures how well each method predicts the GPS, including its lag and smoothing. A method that predicted the true position better than the GPS would be marked down. Rides like 30518 (wheels at 0 while the GPS moves) count against the wheels; none was in this sample, and the medians are robust to a few. The data is from the Earth Rover Zero era (2024), not the current Mini+. The gyroscope's units and rate are inferred, not documented.

Prior art: MBRA (arXiv 2505.05592) filters GPS with an EKF that models its bias, but reports no comparison of ways to predict position between fixes. Zhang and Visser (2024) list the sensor rates (GPS 1 Hz, gyroscope 1 Hz). As far as we found, no one has published how far each way of bridging GPS gaps misses on this rover, across the whole dataset, with the code to reproduce it.

## Carrying the position between GPS fixes with the wheels (simulation)

The pilot steers on GPS smoothed over a few fixes, and on the recorded rides the GPS runs about 1.5 s behind the wheels. On a rover that gets a fix every 2 s, that puts its idea of where it is several metres behind. `dead_reckon.py` carries the position forward from the last fix by wheel distance (the four `rpms` columns times metres per RPM), learning the wheel size on straight stretches by comparing the wheels with the GPS, and using the wheels only once two such stretches agree. If the GPS drops out, the rover drives on the wheels' estimate for up to 30 s, but it never reports a checkpoint without a fix.

`dead_reckon_study.py` flew 5,040 simulated missions: three rover profiles (Zero-like; the same with the 1.5 s GPS lag, 0.8 s command lag and 1.54 s fix period measured on FrodoBots-2K; and a Mini+ stand-in with 95 mm wheels, 1.11 m/s top speed and fixes every 2 s), three GPS error models (independent 1.5 m per axis; 3 m drifting with a 30 s correlation time; and the 1.5 m noise with 5-15 s dropouts about every 90 s), four missions (demo, zigzag, hairpin, square) and 20 seeds, comparing the 0.9.3 pilot with six variants. Every one of the 5,040 runs finished its mission. Four predictions were written before the run, with the rule that dead reckoning becomes the real-rover default only if the dropout, wheel-size and no-harm predictions all hold; all four held.

What it shows (medians; time is relative to the 0.9.3 pilot on the same seeds):

| Rover / GPS | 0.9.3 pilot: position error late in the mission | following the heading (dr-heading) | mission time with dr-heading |
|---|---|---|---|
| Zero-like, 1.5 m noise | 2.15 m | 1.76 m | 0.98 |
| Recorded-ride lags, 1.5 m noise | 2.97 m | 1.76 m | 0.98 |
| Mini+ stand-in, 1.5 m noise | 4.79 m | 1.79 m | 0.97 |
| Recorded-ride lags, 3 m drifting | 4.39 m | 3.67 m | 0.98 |
| Mini+ stand-in, 3 m drifting | 5.42 m | 3.71 m | 0.98 |
| Recorded-ride lags, with dropouts | 3.02 m | 1.77 m | 0.93 |
| Mini+ stand-in, with dropouts | 4.88 m | 1.80 m | 0.93 |

- **Following the compass-corrected heading beat following the last GPS course.** With noisy simulated fixes, a course measured over 3 s is mostly noise, and plain dead reckoning along it (dr) was no better than the 0.9.3 pilot on the Zero-like rover (2.33 m vs 2.15 m late). Following the heading was the best variant on the two lagged profiles and faster than the 0.9.3 pilot in every one of the 36 profile x GPS x mission groups (sign test p < 0.05).
- **Through GPS dropouts it saves about 7% of the mission time** (0.925 to 0.934), because the 0.9.3 pilot stops and waits for a fix, while dead reckoning drives on (about 22-34 s per mission on the wheels alone). None of the dropout runs failed.
- **The wheel size is learned.** Starting from the Mini+ wheel size on Zero wheels (34% off), the learned value ended 0.8-2.2% from the truth in the median, and within 10% in 94% of runs with 1.5 m noise. With 3 m drifting GPS it learns worse (within 10% in 66-86% of runs), and the wheels were trusted in 97.5-100% of runs.
- **A side effect: checkpoints are credited from slightly further away.** The rover's position estimate reaches the report radius sooner, so the median true distance when a checkpoint was credited went from 9.2 to 10.5 m (recorded-ride lags, 1.5 m noise). With 3 m drifting GPS, the true distance was over 15 m at 15 credits in 80 runs, against 3 for the 0.9.3 pilot. The server judges by the rover's own GPS, so these still count, but it means the rover was farther from the real checkpoint than its GPS said.
- **Decision.** Dead reckoning along the compass-corrected heading (`use_course=False`) is on by default for a real rover since v0.10.0. It stays off in the simulator unless asked for, so earlier simulated studies remain comparable.

Limits: simulated rovers only. The simulator's wheels never slip and always agree with the motion, and its compass has only the bias the pilot already learns, so the heading variant could do worse on a real rover with a noisy compass; the next two sections check that on recorded rides. Its GPS error models are harsher than the real rover's measured above. The Mini+ `rpms` column order and signs are undocumented (the SDK README shows only zeros). If they don't add up to forward motion, the trust check never switches the wheels on and the pilot steers on GPS alone, as before. The heading variant with a wrong wheel-size prior was not run as its own combination (dr-miniprior used the GPS course).

Prior art: MBRA / LogoNav (arXiv 2505.05592, §IV-B) fuse actions, wheel speed, GPS and compass on FrodoBots-2K in a bidirectional EKF to make training labels, call the result too noisy for direct training, and don't compare ways to predict position between fixes. As far as found, an open, tested between-fix dead reckoner for the Earth Rover SDK, with a measured comparison like this, hasn't been published.

## Does the compass carry the wheels? (frodo_compass.py 0.1.0, FrodoBots-2K)

The simulator chose to carry the rover between GPS fixes along the compass heading rather than the last GPS course, but its compass was ideal. This checks the choice on real rides. FrodoBots-2K logs the raw magnetometer at 1 Hz with no word on which axes are horizontal; so each of the six axis frames (a pair of axes and a handedness) was tried, with a hard-iron offset from a circle fitted to the ride's samples and the mount bias learned from the GPS course on straight stretches, the way the pilot learns it. The frame was chosen on the even-numbered rides and every predictor scored on the odd ones, on the same anchor and target fixes as the wheel-odometry study.

- Rides: 140 with a calibrating frame and a learned bias (29.6 hours of GPS), of 480 sampled across all 24 parts; 70 odd rides for scoring. The pre-stated bar was 150 rides, so by its own rule this study could not change the default; it is reported as measured. Rides dropped: 195 had no straight stretch long enough to learn the bias, 114 had no frame that calibrates, 25 too little data, 6 no compass.
- Only one frame calibrates on nearly every ride: the y-z pair (138 of 140), chosen on the even rides with a median heading error of 9.4 deg; the x-y and x-z pairs calibrate on 32 and 22 rides with medians of 24-30 deg. So the magnetometer's x axis points up, as the gyroscope's x axis (the yaw axis) already suggested.
- On the odd rides the chosen frame's heading is within a median 10.7 deg of the GPS course (90th percentile 32.1 deg, 6,492 samples), with only a per-ride circle fit and no tilt or soft-iron correction.
- 10 s ahead (odd rides, 6,612 pairs): wheels along the last GPS course missed the next fix by a median 1.90 m; along the compass heading plus the learned bias 1.59 m (0.84x, 95% CI 0.80-0.89 with rides resampled); the course turned by the compass only past 30 deg 1.86 m, turned by every compass change 1.81 m; GPS constant velocity 2.46 m; holding still 6.85 m. The heading is 4% worse at 1 s, level by 3 s, and better the longer the gap: 2.49 m against 3.55 m at 20 s and 3.23 m against 5.35 m at 30 s. While the rover was turning 30 deg or more, the heading's 10 s miss was 1.57 m against the course's 2.06 m.
- Decision rule, stated before the run: switch 0.10.0 to the GPS course only if the heading missed by more than 1.10x the course. It missed by 0.84x, so 0.10.0 keeps following the compass heading (`use_course=False`). The predicted outcome was the opposite (a raw compass 1.2-1.6x worse); five of the six predictions held and this one did not.
- Turning the course by the compass only past 30 deg helped on turning anchors (0.91x the course at 10 s), so `turn_deg` stays 30 for `use_course=True`.

Limits: FrodoBots-2K is the Earth Rover Zero with a raw magnetometer, calibrated here per ride with the whole ride in hand; a live pilot calibrates as it goes and has less (the next section measures that). The Mini+ SDK reports an on-board `orientation` instead, whose convention is undocumented (the on-rover calibration routine finds it). A good raw compass here is evidence, not proof, about the Mini+. The chosen frame was picked on the even rides and scored on the odd ones, but both come from the same 24 parts. 71% of sampled rides were dropped, mostly for lacking a straight stretch to learn the bias on, so the usable rides are the smoother ones.

Prior art: Zhang & Visser 2024 (IRL-UVA-24-01) and arXiv 2407.05735 describe the Zero's sensors (magnetometer and gyroscope at 1 Hz, GPS at 1 Hz) and fuse them in an EKF but publish no heading or GPS accuracy figures and no comparison of ways to carry the position between fixes; MBRA (arXiv 2505.05592) fuses the compass for training labels without reporting its accuracy. As far as found, this is the first held-out measurement of the Earth Rover's raw magnetometer heading against its GPS, and the first word on which of its axes is vertical.

## Calibrating the compass while driving (frodo_compass_live.py 0.1.0, FrodoBots-2K)

The compass study above fitted each ride's hard-iron centre to the whole ride's magnetometer record, which a pilot only has once the ride is over. This repeats it with calibrations a pilot could make as it drives: none (raw), a fit to the first 1, 2 or 5 minutes, and a running fit redone every minute on everything so far. Each variant learns its own mount bias from its own headings. Scoring starts 5 minutes into each ride. Grading rules and predictions were written before the run.

- Data: 211 scored rides of 720 sampled from all 24 parts (47.4 hours of GPS). 673 had a magnetometer record and 488 of those calibrate over the whole record. Dropped: 277 had no straight stretch to learn the bias on, 185 never calibrate, 43 too little data, 4 no compass.
- How long a drive is enough. Among rides whose whole record calibrates, the first 1 / 2 / 5 / 10 minutes calibrate on 11% / 34% / 73% / 93%. A 5-minute fit's centre lies a median 0.037 of the circle's radius from the whole-ride centre (90th percentile 0.18). The running fit has its first centre at a median of minute 3 (75th percentile minute 5).
- Cost in dead reckoning, 10 s ahead, each variant on its own anchors: running fit 1.72 m against 1.85 m along the last GPS course (0.93x, 95% CI 0.87-1.00 with rides resampled); first 5 minutes 1.73 against 1.89 m (0.92x); whole-ride hindsight fit 1.56 against 1.86 m (0.84x, the same as the first study's 0.835); no calibration 4.53 against 1.86 m (2.44x). At 30 s: running 3.60 against 5.23 m (0.69x), hindsight 3.20 against 5.32 m (0.60x), raw 12.5 m.
- So a compass calibrated while driving still carries the wheels better than the GPS course, as was predicted, though by less. It keeps about half of the hindsight gain at 10 s and most of it at 30 s. It is level with the course at 5 s and 2 cm worse at 1 s; the hindsight fit is level by 3 s. Uncalibrated, the compass is useless: a median heading error of 39 deg (90th percentile 122) against 12 deg for the running fit.
- Calibration drive: by the rule set before the run, the shortest fixed window within 1.10x of the hindsight fit at 10 s is 5 minutes (1.097x, so only just); 2 minutes gives 1.42x and 1 minute 2.09x. The prediction was 2 minutes and it was wrong. The running fit does as well as the 5-minute window and has a heading on twice as many anchors, so a pilot should keep refitting rather than calibrate once.

Limits: FrodoBots-2K is the Earth Rover Zero with a raw 1 Hz magnetometer. The Mini+ SDK reports an `orientation` it computes on the rover, so these numbers describe the Zero and are only a hint about the Mini+. The scored rides are the ones that calibrate and contain straight stretches, so the smoother 29% of those sampled. The frame (y-z) was fixed from the first study, which used the same 24 parts. Rides were driven by people, who turn more than a checkpoint pilot does on a long straight leg; a pilot may need to turn on purpose to calibrate.

Prior art: online hard- and soft-iron calibration methods are well known (for example MAVBE, arXiv 2201.02449; RoSLAC, arXiv 2604.14353). As far as found, no one has measured how many minutes of ordinary sidewalk driving such a fit needs on a crowd-driven rover fleet, or what a live fit costs in dead reckoning against the GPS course.

## Can the pilot keep the human marathon pace on a Mini+? (simulation)

`pace_study.py` 0.1.0 flew rover_pilot 0.8.0 (the steering and GPS logic are unchanged since) on a simulated Earth Rover Mini+: 1.11 m/s per unit of `linear` (the SDK README's 4 km/h top speed; that it comes at full `linear` is an assumption), a GPS fix every 2 s, `SIM_REAL` latencies, steered with `ROVER_STEERING`. It flew 3 synthetic courses followed through a planner (long straights 1,552 m, city blocks 1,400 m, a winding bayside path 1,262 m; 4-5 checkpoints each) at cruise 0.6, 0.8 and 1.0, on 12 seeds, under 3 rover profiles: orientation fresh on every poll; orientation held 2 s between reports, as the Mini+ telemetry sends it, turning at 30°/s per unit; the same turning at 20°/s. Each was flown as shipped and with `HeadingPredictor`, which turns the held orientation by the `angular` commanded since the last report (assuming 30°/s and a 0.8 s lag). That is 648 missions; it took 14 minutes, and its 16 tests passed.

**All 648 missions were completed.** The human benchmark is 50 miles (80.5 km) in 29 h 38 min, 0.754 m/s made good (see `marathon.py`).

| Mini+ profile (orientation held 2 s, 30°/s) | cruise 0.6 | cruise 0.8 | cruise 1.0 |
|---|---|---|---|
| speed made good, median | 0.657 m/s | 0.868 m/s | 1.079 m/s |
| runs beating the human 0.754 m/s | 0 of 36 | 36 of 36 | 36 of 36 |
| 80.5 km at that speed | 34.0 h of driving | 25.8 h | 20.7 h |
| stops the 29 h 38 min then allows | none (4.4 h short) | 3.9 h | 8.9 h |
| path / route, median (all courses) | 1.002 | 1.008 | 1.013 |
| path / route, city blocks | 0.991 | 1.010 | 1.035 |

What it shows:
- **Cruise decides it.** At the default 0.6 no run reached the human pace on any course, with the rover driving 99.4% of the time. At 0.8 every run did. In the simulator the pilot turns 98.5% of the commanded speed into progress along the course at 0.6, 97.7% at 0.8 and 97.1% at 1.0, so the shortfall at 0.6 is the speed, not the steering.
- **0.8 leaves little room.** Driving the whole marathon at 0.868 m/s takes about 25.8 h, so all the stops of the run together (six battery changes between seven legs, crossings, people, recoveries) must fit in about 3.9 h to beat 29 h 38 min. At 1.0 they may take about 8.9 h.
- **Faster also means wider paths.** On the city-blocks course, with its right-angle corners, the path grew from 1.010 times the route at 0.8 to 1.035 at 1.0, and to 1.041-1.059 on the rover turning at 20°/s. The Mini+ budget (`marathon.py`) leaves about 1.044 per 12 km charge, so a corner-heavy leg at full speed could empty the battery before its end, if the 12 km holds at that speed.
- **The 2 s-old orientation costs little.** Against a fresh orientation, it made missions 6-20 s slower on 1.3-1.6 km courses (sign test p < 0.05 in 16 of 18 cruise × course groups), under 1.5%. On the rover turning at 30°/s the city blocks showed no clear cost; on the one turning at 20°/s they showed the largest (18-20 s).
- **Predicting the heading between reports is not adopted.** With the turn rate it assumes (30°/s), `HeadingPredictor` was faster in 7 of 9 groups (by 4-9 s) and slower in none. On a rover turning at 20°/s it was faster in 2 groups and slower in 2: on the city blocks at cruise 0.8 and 1.0 it lost 5-9 s, because it turns the held heading further than the rover did. The gain is under 1% and depends on knowing the turn rate, so the pilot stays as it is. `--calibrate` measures the turn rate (`yaw_dps_at_full`), so a predictor that uses the calibrated rate is the version worth testing on a real rover.
- **What changed.** v0.10.0 adds `--marathon`, a preset with cruise 0.8 and the real-rover steering. The default cruise stays 0.6.
- Limits: simulated rovers on synthetic courses of 1.3-1.6 km, not 11.5 km legs. The simulator has no pedestrians, crossings, kerbs, slopes or traffic lights, so these speeds are upper bounds and the stop allowance is what is left for all of them. The Mini+ speed per unit of `linear` is assumed, the range is the README's figure, and whether the 29 h 38 min includes the time between legs isn't published.

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
- **By eye.** We looked at 16 of the frames. Where the default stopped and the new setting didn't, the frames show open paths with tree shadows across them, sunlit gravel and a rover's wheels at the bottom edge. The new setting's remaining phantom stops that we looked at were a night frame with headlight glare and raindrops on the lens, a deep shadow band with grass at the path's edge, a dark wet patch on the path, and a person in a wheelchair close on the right. The last two may well be things a rover should slow for. One frame shows the camera turned 90° (the rover had tipped over), and the new setting read it as clear. The camera layer can't tell that a rover has fallen; since v0.9.2 the accelerometer does.
- **What we can't say yet: how many real obstacles it misses.** The data has no obstacle labels. 14 frames came just before the driver stopped or turned hard while moving. The default called 12 of them blocked and the new setting 5. But of the 6 such frames we looked at, 5 show an open path, so drivers stopped or turned there for other reasons, and these frames say little about missed obstacles.
- **Clock check: inconclusive.** How much the picture changes in half a second correlates only weakly with wheel speed at any clock offset from -4 to 4 s (r = 0.10 to 0.18, best at -3.5 s), so it neither confirms nor rules out an offset between the video and control clocks. Labelled at the -3.5 s offset instead, the results are about the same: phantom stops 40% (default) against 6% (new setting).
- **What changed.** `free_space.py` 0.5.0 adds `REAL_ROVER`, the skip3 + shadow + wide + gap4 settings. Since v0.9.0, `--vision` on a real rover uses them (`make_vision`); `--vision-plain` goes back to the old defaults. The simulator keeps the defaults, so simulated results don't move. `--vision` stays marked experimental.
- **Limits.** 493 frames from 48 rides of Earth Rover Zero-era rovers; the Mini+ camera may differ. The setting was picked as the best of 8 on these same frames, which flatters it a little; the check on other rides follows. The study fits a fresh ground model to each frame, while the guard on a rover blends it over time. Driving on is a lower bound on clear space, so a few "phantoms" may be real obstacles the driver steered past within the corridor. No real rover has been driven with it yet.
- **Prior art.** We found no published evaluation of an obstacle or free-space check on FrodoBots-2K, nor any use of the drivers' own commands as labels for one. The dataset card lists no obstacle annotations.

**The check on other rides (frodo-frames holdout, pre-registered).** The setting above was chosen as the best of 8 on the same 493 frames, so it was re-run unchanged (the v0.9.0 code) on 72 other rides, 3 from each part, none of them among the first 48, at other frame times (4, 9 and 14 s into each segment). That gave 837 frames, 737 with control data. The prediction, written before the run: the new setting's phantom-stop rate is at most 15%, and its 95% interval's top lies below the bottom of the default's interval.

| Setting | Phantom stops (of 190) | 95% CI | Phantom swerves (of 79) | 95% CI | Blocked on the 33 stop/turn frames |
|---|---|---|---|---|---|
| default | 74 (39%) | 32–46% | 62 (78%) | 68–86% | 88% |
| shadow | 34 (18%) | 13–24% | 40 (51%) | 40–61% | 55% |
| gap4 | 56 (29%) | 23–36% | 43 (54%) | 44–65% | 70% |
| skip3 + shadow + gap4 | 24 (13%) | 9–18% | 25 (32%) | 22–43% | 39% |
| **skip3 + shadow + wide + gap4 (REAL_ROVER)** | **7 (4%)** | **2–7%** | **17 (22%)** | **14–32%** | **30%** |

(skip3, skip5 and wide alone: 31%, 28%, 37% phantom stops; full table in the study's report.)

- **Prediction met.** Phantom stops fall from 39% to 4% on rides the setting was not chosen on. The new setting's interval (2–7%) lies well below the default's (32–46%). The order of the eight settings is the same as on the first frames, and shadows still matter most.
- **Phantom swerves held up less well.** 22% here against 7% on the first frames (of 79 frames here, 28 there). It is still far below the default's 78%, but the first figure was optimistic, which is what choosing on the same frames does.
- **The price is unknown, and it may be real.** On the 33 frames taken just before a moving driver stopped or turned hard, the default called 88% blocked and the new setting 30%. The first look by eye found most such frames showed an open path, so this isn't a miss rate. It does mean that if a real obstacle looks like a shadow or a colour change, the new setting is more likely to drive at it. The data has no obstacle labels, so how many real obstacles it misses is still not measured.
- **Clock offset.** Labelled at the clock offset where image change best follows the wheels (-3.5 s, again only r = 0.14), the results are about the same: 46% against 4% phantom stops.
- **Decision.** `REAL_ROVER` stays the real-rover setting for `--vision`, and `--vision` stays experimental. The next step for the camera layer is a label for real obstacles, not more tuning on driving-on labels.

## Limits

- These are human-driven rides from the Earth Rovers game (Earth Rover Zero era, early 2024), logged on the rover. The SDK, newer rovers and other firmware may behave differently. The sign is backed by the SDK's and LeRobot's code; the speeds, turn rates and lags are only from this data.
- The first measurement sampled 288 of the 8,906 rides that have control and GPS files, 12 per part, so every part counts equally rather than every hour. The gyroscope figures come from the same 279 rides. The later studies sampled 20 to 30 rides per part the same way.
- Course rates from 1 Hz GPS are noisy. The turning correlation is weak (r = -0.24), even though the sign test is lopsided (440 to 57). The GPS turn rate is a lower bound.
- The gyroscope's units are inferred, not documented. Degrees per second is the only reading that fits the GPS, but the size could be off by the GPS smoothing factor.
- The control and GPS clocks were taken as they are. The results line up across lags (0.8 s + 1.5 s ≈ 2.5 s), which suggests no large offset in the sampled rides.
- Some rides log wheels and commands at 0 while the GPS moves at walking pace (1 of 567 sampled by `frodo_gps.py`: ride 30518, part output_rides_13). Any analysis that uses the wheels to decide "still" should check for this.
- Prior work: the University of Amsterdam report "Automatic Control, Calibration and Recording for the FrodoBots" (Zhang and Visser, 2024, IRL-UVA-24-01; read in full for this release) describes the Earth Rover Zero's sensors and their rates (accelerometer 100 Hz, gyroscope, magnetometer and GPS 1 Hz, wheel RPM 10 Hz), fuses them in an EKF and tests visual SLAM, object detection and depth models, but publishes no measured GPS error, drift or heading accuracy. It also gives the Zero's top speed as about 3 m/s at full `linear`, far above the 0.8 m/s measured here on the recorded rides; that may differ by firmware or speed setting. As far as we found, no earlier work has published these numbers measured across the whole dataset, together with the code to reproduce them.

## Reproduce it

```
python frodo_motion.py --out-dir out --rides-per-part 12 --imu-per-part 1 --gyro-max-mb 40
python sim_study.py --out-dir out-sim --seeds 30
python gain_study.py --out-dir out-gains --seeds 30
python gps_noise_study.py --out-dir out-gps-noise --seeds 30
python gps_noise_study.py --out-dir out-gps-noise-v2 --seeds 30 --timeout 1500 --noise white1.5,white3,gm3-t10,gm3-t30,gm6-t30 --profiles zero,miniplus --variants residual2,residual3,move20,move30,weigh,weigh-move20,weigh-residual3
python frodo_frames.py --out-dir out-frames --parts all --rides-per-part 2 --segments 4 --offsets 2,7,12
python frodo_gps.py --out-dir out-frodo-gps --parts all --rides-per-part 25 --budget-min 150
python frodo_odometry.py --out-dir out-frodo-odometry --parts all --rides-per-part 20 --budget-min 120 --gyro-max-mb 30
python dead_reckon_study.py --out-dir out-dead-reckon --seeds 20 --timeout 2400
python frodo_compass.py --out-dir out-compass --parts all --rides-per-part 20 --budget-min 120 --imu-max-mb 30
python frodo_compass_live.py --out-dir out-compass-live --parts all --rides-per-part 30 --budget-min 120 --imu-max-mb 30
python pace_study.py --out-dir out-pace --seeds 12
```

All of these but `frodo_frames.py` use the standard library only. Our `frodo_motion.py` run took 19 minutes and read about 317 MB. `out/summary.json` has every table and `out/rides.jsonl` has one line per ride. `sim_study.py` took about a minute, `gain_study.py` about 6 minutes, `gps_noise_study.py` about 14 and 7, `dead_reckon_study.py` about 21 and `pace_study.py` about 14; each writes `report.md`, `summary.json` and `runs.jsonl`. The FrodoBots-2K readers (`frodo_gps.py`, `frodo_odometry.py`, `frodo_compass.py`, `frodo_compass_live.py`) read 227-479 MB each over range requests and took 20-48 minutes. The study numbers above were made with rover_pilot 0.7.0 (`sim_study.py`, `gain_study.py`), 0.8.0 (`gps_noise_study.py` 0.1.0, `pace_study.py`), 0.9.2 (`gps_noise_study.py` 0.2.0) and 0.10.0.dev1 (`dead_reckon_study.py`); later versions leave the simulator and the pilot's steering and GPS handling as they were (`gps_noise_study.py` 0.2.0 reproduced 0.1.0's rows exactly on 0.9.2), and dead reckoning stays off in the simulator unless asked for, so they should give the same numbers; the studies have not been re-run on 0.10.0 itself. `frodo_frames.py` needs ffmpeg and Pillow; it writes `report.md`, `summary.json`, `frames.jsonl` (every frame's scan results and label) and a small thumbnail of each frame.

## Licence and credit

Data: FrodoBots-2K by FrodoBots Lab, CC BY-SA 4.0. The numbers and tables in this file derive from it and are shared under CC BY-SA 4.0. The code (`frodo_motion.py`, `frodo_frames.py`, `frodo_gps.py`, `frodo_odometry.py`, `frodo_compass.py`, `frodo_compass_live.py`, `sim_study.py`, `gain_study.py`, `gps_noise_study.py`, `dead_reckon_study.py`, `pace_study.py` and their tests) is Apache-2.0, like the rest of this repository. Not affiliated with FrodoBots, BitRobot or the Earth Rover Challenge organisers.
