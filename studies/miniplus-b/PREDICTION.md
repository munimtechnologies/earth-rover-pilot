# miniplus-b-v1: the Earth Rover Mini+'s conventions, second pass

Pre-registered 2026-10-22 (~06:30 UTC), before miniplus-b-v1 ran. MV2 of Munim, Inc.; written with AI agents. Text CC BY 4.0; code Apache-2.0.

## Why a second pass

miniplus-v1 (studies/miniplus/PREDICTION.md) read 8 public Mini+ datasets (44 episodes, 16,939 frames) and could grade almost nothing. It found only 2 turn windows and no forward wheel frames, because:

- these recordings are keyboard teleop, which sends a turn as linear 0.3 with angular +-1, plus short autonomous runs with small commands (|angular| <= 0.8, mostly below 0.3). v1 needed 4 s of one-signed angular >= 0.3, and spins with linear below 0.1;
- the `/data` state refreshes about every 0.5 s and arrives about 0.5 s after the command, so v1's "1 s of one pure command, then the state" almost never happened;
- v1 missed the `imu.gyro.*` field names and two robot_type spellings (`earth_rover_mini_plus`, `earth-rover-mini`).

It also showed that no public Mini+ recording has a GPS fix: latitude and longitude read the no-fix value 1000 throughout. So v1's orientation-against-GPS-course check (its P7, P8) can't be done on public data.

**What we saw before writing this.** We read v1's output, the meta/info.json and meta/stats.json of five datasets, and about 190 rows of lilkm/earthrover-test and AmitGMU/earthrover-navigation_20260610_165303 through the Hub's dataset viewer. In those rows: rpm2 equalled rpm0 and rpm3 equalled rpm1; `speed` (km/h) was about 0.95 times the wheels' speed at 95 mm; orientation fell during left-turn commands and rose during right-turn ones; gyroscope_z went positive during left turns. So Q3, Q6, Q8 and part of Q1 are informed by a look at one dataset. The test that adds the most is the larger datasets nobody here has looked at row by row: cagataydev/scout-earthrover-ecot (11,762 frames), cagataydev/scout-earth-rover-mini-20260616-053232 (4,176) and the lilkm navigation sets.

## Design (fixed before the run; miniplus_b.py 0.1.0)

- Datasets: the 10 known ids plus any Hub search hit (earthrover, earth-rover, earth_rover, rover_mini, rover-mini) whose robot_type is `earthrover_mini_plus`, `earth_rover_mini_plus` or `earth-rover-mini` and which names linear and angular actions. Table data only.
- A field counts only in episodes where it changes (a constant gyroscope or GPS is a missing sensor).
- Everything is in frames. Lag = round(0.5 s x fps) frames, window = round(2 s x fps), hold = round(1 s x fps).
- **Turn windows:** non-overlapping 2 s windows of commands. A window qualifies if no two commands have opposite signs (zeros allowed), |mean angular| >= 0.2, and the orientation changes by at least 3 degrees from one lag after its first frame to one lag after its end (unwrapped). "Clockwise" = orientation falls under a positive angular (or rises under a negative one).
- **Turn rate:** median |rate| / |mean angular| over qualifying windows; least-squares slope of rate on mean angular over all one-signed windows.
- **Gyroscope:** per axis, Pearson r of the axis averaged over the orientation span against the window's orientation rate (all windows); median axis / rate where |rate| >= 5 deg/s.
- **Wheels:** a forward frame is one whose command was linear >= 0.3 and |angular| < 0.1 on every frame from 1 s to 0.5 s before it. Turning frames: angular >= 0.5 (left) or <= -0.5 (right) over the same span, any linear, with some wheel non-zero. Duplication: share of frames with some wheel non-zero where rpm2 = rpm0 and rpm3 = rpm1.
- **Speed check:** on frames with all four RPMs positive, mean RPM >= 20 and `speed` > 0: (speed / 3.6) / (mean RPM x pi x 0.095 / 60).
- **Refresh:** seconds between consecutive frames where any live field among orientation, speed, wheels and gyroscope changes.

## Decision rules

- **D1:** with >= 30 qualifying windows from >= 2 datasets: clockwise share >= 0.8 means the pilot's default (orientation degrees clockwise, with a positive angular turning left) is consistent; <= 0.2 means the next release changes the real-rover default, with tests; in between, no change and `--calibrate` stays the way to find out. Fewer: no change.
- **D2:** with >= 30 forward frames where all four RPMs are non-zero: if all four share a sign on >= 90% of them, dead_reckon's average of the four is right. Otherwise the next release combines them with signed sides, with tests. Fewer: no change.
- **D3:** with >= 50 speed-check frames: a median ratio in [0.8, 1.25] keeps the 0.00497 m/s per RPM prior. Outside that, document it; the pilot already learns the scale from GPS. Fewer: no change.

## Predictions

- **Q1:** D1 has enough windows, and the pooled clockwise share is >= 0.8.
- **Q2:** every dataset with >= 10 qualifying windows has a clockwise share >= 0.7.
- **Q3:** rpm2 = rpm0 and rpm3 = rpm1 on >= 99% of frames with a wheel turning (pooled).
- **Q4:** D2 has enough frames, and the four share a sign on >= 90% of them.
- **Q5:** rpm1 is the right-hand side: with >= 20 frames each, rpm1 > rpm0 on >= 60% of left-turn frames and rpm0 > rpm1 on >= 60% of right-turn frames.
- **Q6:** the speed check's median is in [0.85, 1.05] (>= 50 frames).
- **Q7:** in lilkm/earthrover-test and AmitGMU/earthrover-navigation_20260610_165303 the median refresh is 0.4-0.6 s.
- **Q8:** of the gyroscope axes, z has the largest |r| with the orientation rate, and its r is negative.
- **Q9:** the pooled median turn rate is 15-90 deg/s per unit of angular.
- **Q10:** no dataset has a valid GPS fix (valid share 0 wherever latitude is recorded).

A prediction whose data falls short of its stated minimum is ungraded, not held or missed.

## Limits known in advance

- Hobby and test recordings, minutes long, probably from a handful of rovers, mostly indoors (no GPS). They are evidence about the conventions, not about accuracy.
- D1 measures how orientation moves against the command, which is what the pilot's steering needs. Saying that orientation is clockwise from north also needs "positive angular turns left", which rests on earlier evidence (FrodoBots-2K GPS course 440 to 57, the SDK's ROS2 bridge, LeRobot's teleop), not on this data. Without GPS, these recordings can't tie orientation to north.
- Indoors, a magnetometer-based orientation can be pulled by nearby steel; this adds noise to D1 but shouldn't flip its sign.
- LeRobot keeps the newest row of `rpms` and `gyros` per frame and repeats the last `/data` response if a request fails, so the refresh interval includes the network.
- cagataydev/scout-earth-rover-mini-20260616-053232's robot_type says "earth-rover-mini", not "plus". It is reported on its own line.
