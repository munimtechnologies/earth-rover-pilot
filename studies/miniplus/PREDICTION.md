# miniplus-v1: the Earth Rover Mini+'s telemetry, from public LeRobot recordings

Pre-registered 2026-10-22 (~04:30 UTC), before miniplus-v1 ran. MV2 of Munim, Inc.; written with AI agents. Text CC BY 4.0; code Apache-2.0.

## Why

Every FrodoBots-2K study so far measured the Earth Rover Zero. The Earth Rover Challenge now drives the Mini+, which reports an `orientation` computed on board. Its SDK documents neither which way `orientation` runs nor how often it updates, nor the order and signs of the four `rpms` columns. earth-rover-pilot 0.11.0 assumes `orientation` is degrees clockwise from north and averages the four wheels for dead reckoning. If the right-hand wheels report negative RPM when driving forward, that average is near zero, the wheels never pass the trust check, and dead reckoning stays off on a real Mini+ without saying so.

LeRobot's `earthrover_mini_plus` robot records the SDK's `/data` fields at 10 fps, and a few people have published such recordings on the Hugging Face Hub (for example lilkm/earthrover-navigation, lilkm/earthrover-test, AmitGMU/earthrover-navigation_20260610_165303, dkuzmenko/earth-rover-mini-test-4). As far as we found, no one has used them to measure these conventions.

## Design (fixed before the run)

- Search the Hub for datasets (terms: earthrover, earth-rover, earth_rover, earthrover_mini, mini_plus, frodobots, rover_mini, erm). Keep those whose `meta/info.json` says `robot_type` `earthrover_mini_plus` and names linear and angular actions. Read the table data only (`data/*.parquet`), no video.
- Time is frame index / fps.
- **Turn windows:** non-overlapping 4 s windows where every `angular` command has one sign and |mean| >= 0.3. The orientation change (unwrapped, in degrees) is taken from 1 s after the window's start to 1 s after its end. "Clockwise" means `orientation` falls while a positive `angular` (a left turn, from FrodoBots-2K, the SDK's ROS2 bridge and LeRobot's teleop) is commanded.
- **Holds:** seconds between consecutive changes of `orientation` (all frames, and with |angular| >= 0.3 at both changes), and of the GPS position.
- **Wheels:** signs of each `wheel_rpm_i` on frames where for the past 1 s `linear` >= 0.3 and |`angular`| < 0.1 (forward), and with |`linear`| < 0.1 and `angular` >= 0.3 or <= -0.3 (spinning left, right).
- **Gyroscope:** for each axis, Pearson r between its window mean and the window's orientation rate, and its mean per unit of command.
- **Course:** on straight forward stretches (`linear` >= 0.3 and |`angular`| < 0.1 throughout), GPS course between distinct fixes at least 5 s and 3 m apart, against `orientation` at the middle. It is read both clockwise (course - o) and counter-clockwise (course - (360 - o)). Spread is the median |difference - that episode's circular mean difference|, over episodes with at least 2 pairs.

## Decision rules

- **D1:** with at least 10 turn windows from at least 2 datasets: clockwise share >= 0.8 means the pilot's default is consistent and nothing changes. A share <= 0.2 means the next release changes the real-rover default to counter-clockwise, with tests. Anything between means no change, and `--calibrate` stays the way to find out. With fewer windows: no change.
- **D2:** with at least 50 forward frames where all four RPMs are non-zero: if all four share a sign on >= 90% of them, averaging is right. Otherwise the next release makes `dead_reckon.py` combine the wheels with signed sides (as measured), with tests. With fewer frames: no change.

## Predictions

- **P1:** at least 3 Mini+ datasets are readable, with at least 2,000 frames in all.
- **P2:** every `orientation` reading lies in [0, 360].
- **P3:** while turning, `orientation` changes at a median interval of 1.5-2.5 s (the pilot assumes it is held about 2 s).
- **P4:** D1 has enough windows, and the clockwise share is >= 0.8.
- **P5:** the turn rate is 20-60 deg/s per unit of `angular` (the Zero: about 30).
- **P6:** D2 has enough frames, and all four wheels share a sign driving forward on >= 90% of them.
- **P7:** the GPS position changes at a median interval of 0.5-2.5 s.
- **P8:** with at least 20 course pairs, the clockwise reading's spread is smaller than the counter-clockwise one's.
- **P9:** the gyroscope axis with the largest |r| is z (an IMU mounted flat, unlike the Zero's x-up).

A prediction whose data falls short of its stated minimum is reported as ungraded, not as held or missed.

## Limits known in advance

- A handful of short, hobby recordings (minutes, not hours), likely from a few rovers. They are evidence about the conventions, not about accuracy.
- LeRobot keeps only the newest row of `gyros`, `mags` and `rpms` per frame and reuses the last `/data` response if a request fails. So a repeated value may come from the network, not the rover.
- LeRobot stores the state as float32, so latitude and longitude are good to about 0.5 m.
- Turn windows need someone to have spun the rover for 4 s or more. Course pairs need straight driving with a GPS fix.
