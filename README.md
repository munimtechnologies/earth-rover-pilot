# earth-rover-pilot

A GPS waypoint pilot for the [FrodoBots Earth Rover SDK](https://github.com/frodobots-org/earth-rovers-sdk). It drives an Earth Rover through the checkpoints of an SDK mission and reports each one with `/checkpoint-reached`. Each leg can follow a walkable route planned on OpenStreetMap instead of a straight line, and every leg of a long mission can be planned and checked on a map before the rover moves. A short calibration run on the rover works out which way its compass and turn commands run, so the pilot never steers backwards. Between GPS fixes it carries the rover's position forward on its wheels. An experimental front-camera layer can steer it around obstacles.

The [Earth Rover Challenge](https://earth-rover-challenge.github.io/) uses this mission format: AI teams and human gamers drive the same sidewalk rovers in real cities over the internet. Its urban and marathon tracks are GPS-checkpoint missions; the marathon runs about 50 miles from UC Berkeley to Stanford. It is also BitRobot's [Earth Rover Grand Challenge](https://bitrobot.ai/grand-challenges/earth-rovers).

Made by **MV2 of Munim, Inc.** The code was written with AI agents.

**Status (v0.12.0):** the pilot has been tested only against the built-in simulator, synthetic maps and recorded data. It has not driven a real rover yet. What real rovers do with its commands has been measured on recorded rides from the public FrodoBots-2K dataset ([FINDINGS-frodobots-2k.md](FINDINGS-frodobots-2k.md)), the simulator can move like them (`--sim-real`), and the steering for a real rover was chosen by a simulation study on that motion (`gain_study.py`). v0.9.0 reads a real rover's camera with the settings that saw the fewest phantom obstacles on recorded front-camera frames, and a check on 72 other rides held up: about 1 in 25 clear paths instead of 2 in 5 (see "Front camera" below). It is still experimental. v0.9.1 adds `gps_noise_study.py`: the pilot completed all 9,450 simulated missions under GPS error that drifts, up to 6 m (see "Drifting GPS" below). v0.9.2 stops a rover that has tipped over, read from its accelerometer (see "Tipped rover" below). v0.9.3 adds `marathon.py`, which works out what beating the human Berkeley-Stanford time asks of a Mini+ (see "Marathon budget" below).

v0.10.0 carries the rover's position between GPS fixes on its wheels, along the compass-corrected heading (`dead_reckon.py`, on by default on a real rover): in 5,040 simulated missions this cut the late position error by up to 63% and mission time by 2-3%, or 7% with GPS dropouts. The simulator favoured following the compass heading, and on 140 recorded FrodoBots-2K rides it held: wheels carried along the raw compass plus the learned bias missed the next GPS fix 10 s later by 1.59 m against 1.90 m along the last GPS course, and 3.2 m against 5.4 m at 30 s; calibrated while driving, the compass still won (0.93x at 10 s). A real rover's GPS turned out far calmer than the simulator's noise: standing still, its fixes drifted 0.5 m in 10 s and 2.7 m in 5 minutes (`frodo_gps.py`). v0.10.0 also logs `/data` `battery` against distance, and `--marathon` sets cruise 0.8, the cruise that beat the human marathon pace in every simulated run of the main Mini+ profile, where 0.6 beat it in none (see "Marathon pace" below). Treat the defaults as a starting point and tune them on the first real runs, starting with `--calibrate`. Since v0.8.1 the rover is stopped when its telemetry stops coming in (see "Lost telemetry" below).

v0.11.0 holds the fresh GPS course for 2 s after each fix before following the compass heading, the difference fading out over 2 s more. On recorded FrodoBots-2K rides the course is better than the compass right after a fix and the compass wins from about 5 s on. On 145 rides held out from the study that chose it, the hold missed the next GPS fix 10 s later by 1.62 m, against 1.71 m for the compass alone and 1.94 m for the course alone (0.944x the compass, 95% CI 0.915-0.962), with no cost at 30 s (see "Dead reckoning" below).

v0.11.1 doesn't change the pilot. It adds `frodo_between.py`, which checks whether the compass studies' figures hold for a pilot that has only the compass reads it has already made (the studies had interpolated between the 1 Hz reads, looking up to a second ahead). They do: on the same 145 held-out rides, the last read missed the next GPS fix 10 s later by 1.72 m against 1.71 m interpolated, turning it by the gyroscope or the turn command between reads gained nothing, and the 2 s course hold still helped (0.943x, 95% CI 0.920-0.963).

v0.11.2 doesn't change the pilot either. It adds `miniplus.py` and `miniplus_b.py`, which measure the Earth Rover Mini+'s telemetry on 10 public LeRobot recordings (52 episodes): its `orientation` changes about every 0.5 s (earlier simulation had assumed 2 s); `rpms` column 0 is the left wheels and column 1 the right; `speed` is in km/h and matches the wheels at 95 mm; and no public recording has a GPS fix. Which way `orientation` runs came out mixed (52 of 77 turn windows the way the pilot assumes, short of the 0.8 the pre-stated rule needed), so `--calibrate` stays the way to find out (see "The Earth Rover Mini+'s telemetry" in FINDINGS-frodobots-2k.md).

v0.11.3 doesn't change the pilot either. It adds `pace_b.py`, which flies the marathon-pace simulation again with the Mini+ telemetry those recordings showed (orientation every 0.5 s, 48°/s per unit of `angular`, 0.5 s latency). All 720 missions were completed and 6 of 8 predictions written before the run held: at the `--marathon` cruise of 0.8 the rover made good 0.878 m/s, leaving about 4.2 h for every stop of the 80.5 km (3.9 h on the earlier 2 s profile). 10° of compass noise cost 2.4-3.1% on every course and cruise, so a noisy heading is now the main simulated risk to the pace (see "Marathon pace" below).

v0.12.0 adds `--smooth-heading`, off by default. Each new compass reading moves the heading the pilot steers by only 0.3 of the way from its last estimate, after turning that estimate by the `angular` commanded since (a complementary filter). `pace_c.py` flew it on a simulated Mini+ with 10° of compass noise, and all 8 predictions written before the run held. It was faster in every course and cruise group (2.1-2.5%) and made good 0.874 m/s at cruise 0.8, against 0.855 without it and 0.878 with a clean compass. With a clean compass it cost nothing. It stays off until a real Mini+'s compass noise is measured. With `--calibration` it uses the measured turn rate (see "Marathon pace" below).

## What the recorded rides say

`frodo_motion.py` reads the control, wheel-RPM, GPS and IMU logs of a sample of FrodoBots-2K rides straight from the dataset's zip files, without downloading the video. On 279 rides across all 24 parts:

- a positive `angular` turns the rover **left** (440 to 57 in a sign test). The SDK's ROS2 bridge and LeRobot's Earth Rover driver both send a left turn as a positive `angular`, too.
- it turns at about **30°/s per unit of `angular`** (the gyroscope's x axis, which reads degrees per second, counter-clockwise positive)
- at full `linear` the rover covers about **0.8 m/s**
- the wheels respond about **0.8 s** after a command, and GPS shows the motion about **1.5 s** after the wheels, so a turn reaches the GPS course about **2.5 s** after it is commanded
- the effective wheel radius is **0.064 m** (0.0067 m/s per RPM)

Later studies, each on its own sample of 480 to 720 rides:

- the GPS is smooth while driving (0.22 m sideways scatter over 10 s) and, standing still, outside one faulty ride, drifted **0.5 m in 10 s and 2.7 m in 5 minutes** (`frodo_gps.py`)
- between fixes, wheel distance predicts the next fix 24% better than the GPS's own velocity at 10 s; turning by the gyroscope makes it worse (`frodo_odometry.py`)
- the magnetometer's **x axis points up**; headings come from y and z. Calibrated per ride, it carries the wheels better than the last GPS course (`frodo_compass.py`), and a fit redone every minute while driving keeps most of that gain; 5 minutes of driving calibrates about three rides in four, 2 minutes only one in three (`frodo_compass_live.py`)

`frodo_frames.py` reads front-camera frames from 48 rides and labels each one with what the driver did next: on frames after which the driver went at least 2 m straight, the camera layer's default settings saw a wall within 1.2 m 35% of the time. Shadows did most of it.

So since v0.6.0, a real rover without `--calibration` is driven with a positive `angular` turning left. Earlier versions assumed right, which would make every correction turn the rover further away. Details, limits and credits are in [FINDINGS-frodobots-2k.md](FINDINGS-frodobots-2k.md). The numbers there derive from FrodoBots-2K (FrodoBots Lab, CC BY-SA 4.0) and are shared under the same licence.

## Why not the plain example

The SDK ships a simple waypoint example. On a real rover, a bearing-follower like that runs into these problems, and this pilot handles each one:

| Problem | What the pilot does |
|---|---|
| The SDK doesn't say which way a positive `angular` turns, or what `orientation` reads (its example shows `128`). Guess wrong and every correction turns the rover further away. | Without a calibration, a real rover is driven with a positive `angular` turning left, as the recorded rides show. `--calibrate` spins the rover, drives two short straights with a turn between them and measures both (see below). `--calibration` applies the result. |
| With no fix, the rover reports latitude/longitude `1000`. Bad parsing turns missing values into 0/0. | `GpsFilter` drops no-fix, 0/0, NaN and impossible jumps. It smooths the remaining fixes and stops the rover if no fix has arrived for 3 s (with dead reckoning on, it drives on the wheels for up to 30 s instead). |
| A fix comes only every 1 to 2 s and shows where the rover was 1.5 s earlier, so the pilot's idea of where it is runs metres behind. | `DeadReckoner` (`dead_reckon.py`) carries the position from the last fix by the wheel RPMs along the compass-corrected heading, once straight stretches have checked the wheels against the GPS (see "Dead reckoning" below). |
| The SDK caches the last telemetry it got, so when the rover's link drops, `/data` keeps showing the same GPS fix and the rover would be steered blind. | `TelemetryWatch` stops the rover once no new telemetry has come in for 5 s, and lets it drive on when telemetry is back (see "Lost telemetry" below). |
| A rover on its side still has a GPS fix and a compass, and its camera, turned 90°, may read as clear ground; a pilot would keep driving its wheels in the air. | `TipWatch` learns which way gravity points in the accelerometer at the start of the mission and stops the rover once it has pointed more than 50° away for a second, until it is upright again (see "Tipped rover" below). |
| The compass is offset by the motors, the mount and local magnetic fields. | `HeadingEstimator` learns the bias as the rover drives. On straight stretches it fits a line through the GPS fixes and compares that course with the mean compass reading, then corrects the offset gradually. It measures how straight the fixes lie, and can leave out or down-weight stretches bent by drifting GPS (off by default; in simulation neither helped). If the compass drops out, it falls back to the last GPS course. |
| A checkpoint a few hundred metres away is behind buildings, fences or water. | With `--osm` or `--fetch-osm`, each leg is planned on OpenStreetMap footways, paths and sidewalks (`route_planner.py`), and `PathFollower` steers along it (pure pursuit, 8 m lookahead). If the rover strays more than 30 m it replans. |
| A marathon has dozens of legs; finding a leg with no walkable route halfway through costs the run. | `--check-route` plans every remaining leg from where the rover stands, without driving, and reports each leg's straight-line and routed length (see below). `marathon.py route` then says whether the planned route fits one Mini+ charge. |
| A bin, a planter or a parked scooter sits on the line the rover is driving. | With `--vision`, `free_space.py` reads the front camera 5 times a second, works out how far the rover could drive in each direction, and bends the heading to the nearest clear one. Experimental: on recorded frames from rides it wasn't tuned on it still sees a phantom obstacle on about 1 in 25 clear paths, and how many real ones it misses isn't measured (see below). |
| GPS noise is about the size of a 2 m arrival radius, so the rover never "arrives". | Checkpoints are reported from 10 m, inside the server's 15 m tolerance. A refused report is retried every 2 s. Inside 3 m the rover holds still instead of circling. |
| The SDK confirms the last checkpoint only after a confirmed stop, and may hold that request for up to 12 s. | Before the final report the pilot sends stop commands for 1.5 s. It waits up to 20 s for the answer. If none arrives, it reads `/checkpoints-list` to see whether the report counted before trying again. |
| Commands arrive late, GPS shows a turn about 2.5 s after it is commanded, and a real rover turns at only about 30°/s per unit of `angular`. | The pilot steers on the compass, not the GPS course, and learns the compass bias only on straight stretches. The gain stays low (full turn rate needs a 60° error). On a real rover `angular` may reach 1.0 and it turns in place only above 90°, the setting that did best in the gain study (see below). `--gps-lag` can also move each late fix forward, but in simulation it didn't clearly help, so it is off by default. |
| A kerb or wall blocks the rover. | If it's commanded forward but moves less than 1.5 m in 10 s, it backs up, turns (alternating sides) and drives on. |
| The pilot or its connection drops in the middle of a mission. | `--no-start` resumes it: the pilot skips `/start-mission` and drives on from the server's latest reached checkpoint. |

## Run it

Standard library only, Python 3.8 or later. `--vision` on a real rover also needs Pillow (`pip install pillow`) to decode the camera's JPEG frames.

Simulator (no rover needed): the built-in demo mission has 4 checkpoints over about 220 m, with 0.5 s command latency, 1.5 m GPS noise, 5% GPS dropouts and a compass that reads 25° low:

```
python rover_pilot.py --simulate --seed 1
```

Make the simulated rover move like the recorded ones (0.79 m/s at full `linear`, commands 0.8 s late, GPS 1.5 s behind the wheels), and carry its position on its wheels as a real rover does:

```
python rover_pilot.py --simulate --sim-real
python rover_pilot.py --simulate --sim-real --dead-reckon
```

`--sim-real` keeps the simulator's 60°/s turn rate per unit of `angular`. The recorded rides show about 30°/s, and `sim_study.py` and `gain_study.py` fly that too. The simulator also keeps its own steering (angular capped at 0.6, turn in place above 60°); add `--max-angular 1 --turn-in-place 90` to fly it the way a real rover is driven.

Add two 2 m-wide hedges on the route, and let the camera steer around them:

```
python rover_pilot.py --simulate --obstacles --vision
```

Without `--vision` the rover drives into the hedges and has to back out. The result shows `sim_contacts`, the number of 0.1 s steps a hedge held the rover back.

Real rover: start the SDK server first, following its README, with `SDK_API_TOKEN`, `BOT_SLUG` and `MISSION_SLUG` set. The pilot sends a command 10 times a second, so a short dead-man timeout is safe: the SDK suggests `CONTROL_WATCHDOG_S` of 0.5–1 for streaming clients, and 1 is a good choice here. The rover then stops within a second if the pilot hangs or loses its connection, for example while a checkpoint report is waiting for an answer.

On a new rover, list its missions, calibrate once on open ground, then drive with the calibration:

```
python rover_pilot.py --sdk http://localhost:8000 --list-missions
python rover_pilot.py --sdk http://localhost:8000 --calibrate --calibration-out rover.json
python rover_pilot.py --sdk http://localhost:8000 --calibration rover.json --log run.jsonl
```

Options:
- `--list-missions`: print the missions the SDK lists for this bot (`GET /missions`: slug, distance and number of checkpoints) and exit. Set one as `MISSION_SLUG`.
- `--calibrate`, `--calibration-out rover.json`: measure which way orientation and angular run, and save the result (see below).
- `--calibration rover.json`: drive with a saved calibration. Without it, the pilot assumes orientation in degrees clockwise from north and a positive angular turning left on a real rover. The simulator keeps its own defaults (positive angular turning right).
- `--cruise 0.6`: forward command, 0 to 1. The SDK suggests 0.3–0.5 for first tests. On the recorded rides, 0.6 covered about 0.46 m/s. On a Mini+ (4 km/h at full `linear`) 0.6 made good about 0.66 m/s in simulation, below the human marathon pace of 0.754 m/s; 0.8 made good about 0.87 m/s. See "Marathon pace" below.
- `--marathon`: the long-mission preset from `pace_study.py`: cruise 0.8 and the real-rover steering, also in the simulator. `--cruise`, `--max-angular` and `--turn-in-place` still override it. Measure the range at this cruise first.
- `--max-angular`: the largest `angular` the pilot sends, 0 to 1. Default 1.0 on a real rover, 0.6 in the simulator.
- `--turn-in-place`: turn in place when the heading error is above this many degrees. Default 90 on a real rover, 60 in the simulator.
- `--dead-reckon`, `--no-dead-reckon`: carry the position between GPS fixes on the wheels. On by default on a real rover, off in the simulator unless `--dead-reckon` is given (see "Dead reckoning" below).
- `--mps-per-rpm`: the wheel size dead reckoning starts from, in metres per second per RPM (default: the Mini+'s 95 mm wheels, 0.00497; the recorded Zero rides measured 0.00668). It is learned while driving.
- `--smooth-heading`: smooth the compass over its readings, turning the estimate by the `angular` commanded since each one. Off by default. It uses the turn rate from `--calibration` when the calibration has one, otherwise 48°/s per unit of `angular` (public Mini+ recordings). See "Marathon pace" below.
- `--report-radius 10`: report a checkpoint once the rover is this many metres from it (the server's tolerance is about 15). In simulation 12 was 4–7% faster, but with noisy GPS more of its credits came with the rover truly beyond 15 m; see "Drifting GPS" below.
- `--gps-lag 0`: seconds the GPS runs behind the rover. Above 0, each fix is moved forward by the driving commanded since it was taken, assuming 0.79 m/s at full `linear` and commands 0.8 s late. Off by default; see "Late GPS" below. It replaces dead reckoning: on a real rover `--gps-lag` turns dead reckoning off, and the two can't be asked for together.
- `--telemetry-timeout 5`: stop the rover while no new telemetry has come in for this many seconds; 0 turns it off. See "Lost telemetry" below.
- `--tip-angle 50`: stop the rover while its accelerometer shows gravity more than this many degrees from where it pointed when the mission began; 0 turns it off. See "Tipped rover" below.
- `--osm area.json`: plan each leg on a saved map area (see below).
- `--fetch-osm`: fetch the map around each leg from Overpass as needed.
- `--check-route`, `--route-out legs.geojson`: plan every remaining leg and report it, without driving (see below).
- `--vision`: steer around obstacles seen by the front camera. Experimental. On a real rover it uses `free_space.REAL_ROVER` (see "Front camera" below); in the simulator, the `VisionGuard` defaults.
- `--vision-plain`: with `--vision` on a real rover, use the `VisionGuard` defaults instead. They see far more phantom obstacles; this is for comparison.
- `--camera-fov 90`, `--camera-height 0.35`, `--camera-pitch 5`: the front camera's horizontal field of view (degrees), height above the ground (metres) and downward tilt (degrees). These are guesses; measure them on the rover.
- `--simulate`, `--seed 1`, `--sim-real`, `--sim-quirks`, `--obstacles`: simulator options.
- `--timeout 3600`
- `--no-start`: resume a mission that has already started.

Ctrl-C sends a stop. The log (`--log`) records one JSON line per second, plus each checkpoint, refusal, plan and recovery, each time telemetry is lost (`telemetry-stale`) or back (`telemetry-back`), and each time the rover tips over (`tipped`) or is upright again (`upright`), so a run can be checked afterwards. With `--vision`, each line also has `clear_m`, how far ahead the camera saw clear ground.

### Leg summaries

The result printed at the end has a `legs` list, and the log has one `checkpoint` line per leg, with:
- `seq`: the checkpoint the leg ended at
- `elapsed_s`: time from the previous checkpoint (or the start) to this one
- `straight_m`: straight-line distance to the checkpoint when the leg began
- `reports`: how many `/checkpoint-reached` calls it took (1 means the first one counted)
- `recoveries`: how many back-up-and-turn moves the leg needed
- `battery_pct`: the rover's `/data` `battery` when the leg ended (`null` if it reports none)

On a long mission these show which legs were slow or hard, so the next run can be tuned for them. The result also has `telemetry_stops`, how many times the rover was stopped for lost telemetry, `tip_stops`, how many times it was stopped for having tipped over, and `battery`: the charge at the start and end, the percent used, the metres driven (summed from GPS fixes at least 3 m apart), metres per percent once 2% has been used, and the range that leaves on the remaining charge. With dead reckoning on, `dead_reckon` gives whether the wheels were trusted, the learned and starting wheel size, the straight stretches used and rejected for learning it, the fixes seen, the resets, and `bridged_s`, the seconds driven on the wheels alone through GPS gaps.

## Lost telemetry (`--telemetry-timeout`)

The SDK caches the telemetry the rover pushes to it, and `/data` serves the latest copy. Its README says the rover "executes its last command until a new one arrives", and that the SDK's own watchdog can't help when the rover itself loses its connection. Before v0.8.1, a repeated GPS reading counted as the fix still holding, so if telemetry stopped while commands still got through, the pilot went on steering toward the checkpoint from a position that no longer moved. In the simulator, with telemetry frozen 15 s into the demo, it kept sending drive and turn commands until the mission timed out.

Now the pilot counts a reading as new only when its `/data` `timestamp` changes. It also asks `GET /status` once a second for the SDK's `telemetry_age_s` (seconds since the last telemetry message), where the SDK has it. When either shows no new telemetry for more than 5 s, the pilot sends stop commands and logs `telemetry-stale`. When readings come in again, it logs `telemetry-back` and drives on. An Earth Rover Mini+ reports every 2 s (SDK README), so one late or lost report doesn't stop it, and two in a row do.

Limits: the SDK README doesn't define the `/data` `timestamp`. If it turns out to change on every request rather than with each rover report, only `/status` catches a stall. An SDK without `/status` and without a usable timestamp gives the pilot nothing to go on, and it drives as before (`test_telemetry.py` checks that case too). If a real rover is stopped for this when its telemetry is fine, the log shows `telemetry-stale` lines; `--telemetry-timeout 0` turns the check off. In the simulator the timestamp changes on every reading, so simulated missions fly exactly as before.

## Tipped rover (`--tip-angle`)

A sidewalk rover that has gone over a kerb edge or been knocked onto its side still reports a GPS fix and a compass heading, and its front camera, now turned 90°, can read as clear ground (one recorded FrodoBots-2K frame did). Nothing in the GPS loop would notice, and the pilot would keep driving its wheels in the air, or drag the rover along the pavement.

The SDK's `/data` carries the rover's accelerometer (`accels`, rows of `[x, y, z, timestamp]`; the README's example reads about 1 on one axis while the rover stands, so the unit is g; on a Mini+ there are 100 rows per 2 s report). The README doesn't say which axis points up, and the Mini+ may mount its IMU differently from the rovers the dataset was recorded on. So since v0.9.2 the pilot doesn't assume an axis: `TipWatch` averages the rows of each reading and, over the first 3 s of the mission, learns the direction gravity has while the rover is upright. From then on it measures the angle between gravity now and that direction. Once the angle has been above 50° for a second, the pilot sends stop commands and logs `tipped` with the angle; as soon as the angle is back under, it logs `upright` and drives on. The result has `tip_stops`.

Readings whose size is far from 1 g (below 0.5 or above 1.5: a knock, a drop, a rover in the air) are ignored rather than read as a tilt, and readings above 5 are taken as m/s² and scaled. A ramp or a kerb tilts a rover by 10 to 20°, well under the threshold; `--tip-angle` changes it and 0 turns the check off. A rover that reports no `accels` (the simulator) is never stopped for this, so simulated missions fly exactly as before (`test_tip_and_bias.py` checks that, and a simulated rover with an accelerometer being stopped within 1.5 s of tipping and driving on once righted).

Limits: the upright direction is learned at the start, so a rover that begins the mission already on its side, or on a steep slope, learns the wrong one. The pilot only stops; righting the rover needs a person.

## Steering for a real rover (`gain_study.py`)

The steering defaults were tuned on the simulator's rover, which turns at 60°/s per unit of `angular`. A recorded rover turns at about 30°/s, so with the old cap of 0.6 it turned at only about 18°/s. `gain_study.py` flew 24 steering settings × 3 missions × 30 seeds on a simulated rover that moves like the recorded ones, turning at 20, 30 or 45°/s per unit (6,480 missions, about 6 minutes):

```
python gain_study.py --out-dir out --seeds 30
```

Every setting completed every mission. At the same cruise of 0.6, letting `angular` reach 1.0 and turning in place only above 90° was faster than the old defaults in all 9 mission × turn-rate groups (sign test p < 0.05 in each, about 3% overall) and needed a third fewer back-up moves. So since v0.8.0 that is how a real rover is driven; the simulator keeps its own defaults. A stiffer gain (full turn at a 30° error) was slower. A faster cruise was much faster in simulation, but the simulator has no pedestrians or kerbs, so the cruise stays 0.6 and is yours to choose. The full table is in [FINDINGS-frodobots-2k.md](FINDINGS-frodobots-2k.md). This is a simulation result; a real rover may differ.

## Late GPS (`--gps-lag`, `sim_study.py`)

On the recorded rides the GPS runs about 1.5 s behind the wheels. `--gps-lag 1.5` takes the rover's position as the last raw fix moved forward by the driving commanded between the moment the fix shows and now. The stuck check still uses the raw GPS.

`sim_study.py` flies the demo and a zigzag mission on 30 seeds each, with and without `--gps-lag 1.5`, on a real-like rover turning at 30 or 60°/s and on the simulator's default rover:

```
python sim_study.py --out-dir out --seeds 30
```

Every mission was completed either way. On the real-like rover turning at the measured 30°/s, the correction saved a few seconds at most, and the result could be chance (17 faster to 11 slower on the demo, p = 0.34; 16 to 8 on the zigzag, p = 0.15). At 60°/s it made the zigzag slower (7 faster to 20 slower, p = 0.019). In every group it about doubled to tripled the refused checkpoint reports, because the corrected position reaches the report radius before the GPS the server judges by does. So it stays off by default; since v0.10.0 dead reckoning on the wheels does this job instead. The full table is in [FINDINGS-frodobots-2k.md](FINDINGS-frodobots-2k.md). This is a simulation result; a real rover may differ.

## Drifting GPS (`gps_noise_study.py`, `frodo_gps.py`)

The simulator gives every GPS fix its own independent 1.5 m error. A real receiver's error drifts: it wanders a few metres off and stays there for tens of seconds. `gps_noise_study.py` flies 3 missions on 30 seeds under 7 error models (independent 1.5 or 3 m; drifting 1.5, 3 or 6 m with a correlation time of 10, 30 or 120 s), on a rover that moves like the recorded ones, the same with a GPS fix every 2 s, and a stand-in for the Earth Rover Mini+ (a fix every 2 s, 1.11 m/s at full `linear`), with 4 pilot variants (9,450 missions, about 14 minutes):

```
python gps_noise_study.py --out-dir out --seeds 30
```

- Every mission was completed, even with 6 m of drifting error.
- How fast the error moves matters more than its size. 3 m drifting over 120 s made the missions 3% slower; the same 3 m changing over 10 s made them 12% slower.
- The server judges the reported GPS, so with 6 m of drift, 15–24% of the credited checkpoints were credited with the rover truly more than 15 m from them. That holds for any driver, human or AI.
- The GPS smoothing stays: without it the pilot was slower with 14 of 21 rover × error combinations. Heavier smoothing was mixed.
- Reporting from 12 m was faster everywhere (4–7%), but with noisy GPS more of its credits came with the rover truly beyond 15 m, and on the 1 s rover with 3 m jitter it added refused reports. The default stays 10 m until a real rover shows how its server answers; `--report-radius 12` is there to try.

v0.9.2 gave the compass-bias fit two options against drifting GPS: a residual gate (`max_residual_m`), which leaves out a straight stretch whose fixes don't lie on a line, and weighting (`weigh`), which gives longer, cleaner stretches more say. `gps_noise_study.py` 0.2.0 flew them and five variants in 7,200 missions. No variant was faster anywhere: drifting error keeps the fixes on a straight line, just one pointing the wrong way, so the gate can't see it, and fitting only over longer stretches made the bias three times more accurate without making the rover any faster. The time is lost to the position error, not the heading, so both options stay off.

How noisy is a real rover's GPS? `frodo_gps.py` measured it on 567 recorded FrodoBots-2K rides against the wheels: while driving straight the fixes scatter only 0.22 m sideways over 10 s, and standing still, outside one faulty ride, they drifted 0.52 m in 10 s, 1.5 m in 60 s and 2.7 m in 5 minutes. Every simulated error model above is harsher than that (independent 1.5 m noise gives 3.0 m between any two fixes), so the simulated results are stress tests. No single drifting model fits the measurement (the error still grows at 5 minutes), so the simulator keeps its default. The full tables are in [FINDINGS-frodobots-2k.md](FINDINGS-frodobots-2k.md).

## Dead reckoning (`dead_reckon.py`)

Between GPS fixes, `DeadReckoner` carries the position forward from the last fix by wheel distance (the four `/data` `rpms` columns times metres per RPM), along the pilot's compass-corrected heading. It learns the wheel size on straight stretches by comparing the wheels with the GPS, and uses the wheels only once two such stretches agree. If the GPS drops out, the rover drives on the wheels' estimate for up to 30 s, but it never reports a checkpoint without a fix.

Dead reckoning is on by default on a real rover (`--no-dead-reckon` turns it off; `--dead-reckon` turns it on in the simulator; `--mps-per-rpm` sets the starting wheel size, which is learned while driving). To follow the last GPS course instead of the compass heading, set `DEAD_RECKON["use_course"]` to `True` in `rover_pilot.py`; there is no flag for it. Since v0.11.0, `DEAD_RECKON` also holds the fresh GPS course for `course_hold_s` (2 s) after each fix and fades the difference out over as long again (`fade`); `course_hold_s` 0 turns the hold off.

```
python rover_pilot.py --simulate --sim-real --dead-reckon
python dead_reckon_study.py --out-dir out --seeds 20 --timeout 2400
```

- **Simulation.** In 5,040 simulated missions (3 rovers, 3 GPS error models, 4 missions, 20 seeds), carrying the position between GPS fixes by the wheels along the compass heading cut the late position error by up to 63% (4.79 m to 1.79 m on the Mini+ stand-in) and mission time by 2-3%, or 7% with GPS dropouts, with no failed missions. A side effect: checkpoints were credited with the rover slightly further away in truth (median 10.5 m against 9.2 m), because its own estimate reaches the report radius sooner.
- **On recorded rides, with the wheels along the last GPS course** (`frodo_odometry.py`, 449 rides): wheel distance missed the next fix by 24% less than the GPS's own velocity at 10 s and 35% less at 30 s. Turning by the gyroscope made it worse.
- **On recorded rides, with the wheels along the compass** (`frodo_compass.py`, 140 rides): the raw compass heading was better than the last GPS course for carrying the wheels (0.84x the miss at 10 s, 0.60x at 30 s), so 0.10.0 follows the heading.
- **Calibrated while driving** (refit every minute) rather than with the whole ride in hand, the compass still beat the GPS course on 211 recorded rides (`frodo_compass_live.py`: 0.93x the miss at 10 s, 0.69x at 30 s). A raw-magnetometer rover should turn through at least half a circle within the first 5 minutes; 2 minutes calibrated only a third of the rides.
- **The first seconds after a fix** (`frodo_blend.py`, 146 rides; `frodo_blend_b.py`, 145 other rides): right after a fix the GPS course is better than the live compass (8% at 1 s), and the compass wins from about 5 s on. Holding the course for 2 s, then following the compass with the difference fading out over 2 s more, missed the fix 10 s later by 1.60 m against 1.72 m for the compass alone on the first sample, and by 1.62 m against 1.71 m on the held-out rides (0.944x, 95% CI 0.915-0.962), with no cost at 30 s. So 0.11.0 holds the course for 2 s (`DEAD_RECKON["course_hold_s"]`). Holds of 2-4 s, hard or fading, came within 0.012 of each other.
- **What a live pilot reads** (`frodo_between.py`, the same 145 rides): the studies above interpolated the compass between its 1 Hz reads, looking up to a second ahead. Holding the last read instead cost 0.6% at 10 s (1.72 m against 1.71 m) and 0.4% at 30 s. Turning the held read by half or all of the gyroscope's turn, or by the turn command, between reads was no better (0.998x to 1.010x the held read), so the pilot keeps using its latest reading. The course hold still helped on the held read (0.943x, 95% CI 0.920-0.963).

Limits: the recorded rides are the Earth Rover Zero with a raw magnetometer; the Mini+ reports an `orientation` it computes on board, and its `rpms` columns are undocumented (the SDK README shows only zeros). On public Mini+ recordings column 0 is the left side and column 1 the right, and columns 2 and 3 repeat them on some; the pilot's average of the four is the centre's speed either way. If the wheels don't add up to forward motion, the trust check never switches them on and the pilot steers on GPS alone, as before. Its gain on a real rover is measured only on recorded rides, not on a live one.

## Calibrate a rover (`calibrate.py`)

The SDK describes `angular` as "rotation speed left/right (-1 to 1)" and shows `orientation` as a bare number, without saying which way is positive or what a full turn reads. The recorded rides answer the `angular` question for the rovers they were made on, but not for `orientation`, which they don't log. The pilot learns a constant compass offset by itself, but a compass that runs the other way, or a turn command with the opposite sign, makes it steer away from every checkpoint: in the simulator, a rover whose `angular` runs the other way from what the pilot assumes ends up facing away from the first checkpoint and turning on the spot until it times out.

`--calibrate` finds out on the rover, in about 75 to 130 seconds:

1. **Spin** in place for 30 s at `angular` 0.4, reading `orientation` 10 times a second. If the readings don't show a whole turn yet, it spins on 10 s at a time, up to 90 s. The spread of the readings over at least one full turn gives the full-turn value: 360 (degrees), 256 (one byte) or 2π (radians). Readings from -180 to 180 work too. The total turn gives the turn rate.
2. **Drive straight** for 20 s at `linear` 0.4, and fit the GPS course (a least-squares line through the fixes, after 2 s to settle).
3. **Turn** about 90° with a positive `angular`, using the turn rate from step 1, then **drive straight** for 20 s again.

The change in GPS course over the turn shows which way a positive `angular` turns the rover. The change in `orientation` over the same turn shows whether it runs clockwise, and the spin must agree with it. GPS course minus heading on the two straights gives a starting compass bias. The rover moves about 20 m in all, so pick open ground with a clear GPS view. It needs a GPS fix within 30 s.

Why the spin can run past 30 s (since v0.7.0): the recorded rides show about 30°/s per unit of `angular`, so a real rover spinning at 0.4 turns about 12°/s. After the 0.8 s command delay, 30 s covers only about 350°, short of the whole turn calibration needs. Up to v0.6.0, `--calibrate` would most likely have stopped with "orientation did not show one full turn" on a real rover. In the simulator, a rover that moves like the recorded ones now calibrates after about 40 s of spinning (`test_calibrate_real.py`). The simulator's own rover turns twice as fast and still stops spinning at 30 s.

The result has this shape (shortened; the values are illustrative, for the simulator with `--sim-quirks`):

```json
{
  "ok": true,
  "orientation_scale": 256.0,
  "orientation_clockwise": false,
  "angular_right_positive": false,
  "bias_deg": 24.1,
  "yaw_dps_at_full": 59.0,
  "speed_mps_at_full": 1.2,
  "turn_deg": -91.3,
  "reason": "orientation: full turn 256, counter-clockwise; a positive angular turns left"
}
```

`yaw_dps_at_full` and `speed_mps_at_full` are the turn rate and speed at a full command. The simulator uses 60°/s and 1.2 m/s; the recorded rides suggest about 30°/s and 0.8 m/s on a real rover. If a step fails, `ok` is false and `reason` says which one. A failed result is never saved, and `--calibration` refuses one.

Try it in the simulator with a rover whose orientation reads 0–255 counter-clockwise and whose positive `angular` turns left:

```
python rover_pilot.py --simulate --sim-quirks --calibrate --calibration-out quirky.json
python rover_pilot.py --simulate --sim-quirks --calibration quirky.json
```

## Measure the rovers from FrodoBots-2K (`frodo_motion.py` and friends)

```
python frodo_motion.py --out-dir out --rides-per-part 12
```

It reads the dataset's index, then each of the 24 zip parts (2 to 95 GB each) through HTTP range requests: first the zip's central directory, then only the control, GPS and IMU CSVs of 12 rides spread through the part (an IMU file above `--gyro-max-mb`, 40 by default, is skipped). It refuses to go on if the server ignores range requests, so it never downloads a whole part. Our run read about 317 MB in 19 minutes. `out/report.md` sums up the findings, `out/summary.json` has every table and `out/rides.jsonl` has one line per ride. Standard library only.

The other readers work the same way and use `frodo_motion.py`'s zip reader:

```
python frodo_gps.py --out-dir out-frodo-gps --parts all --rides-per-part 25 --budget-min 150
python frodo_odometry.py --out-dir out-frodo-odometry --parts all --rides-per-part 20 --budget-min 120 --gyro-max-mb 30
python frodo_compass.py --out-dir out-compass --parts all --rides-per-part 20 --budget-min 120 --imu-max-mb 30
python frodo_compass_live.py --out-dir out-compass-live --parts all --rides-per-part 30 --budget-min 120 --imu-max-mb 30
python frodo_blend.py --out-dir out-blend --parts all --rides-per-part 30 --budget-min 120 --imu-max-mb 30
python frodo_blend_b.py --out-dir out-blend-b --parts all --rides-per-part 30 --budget-min 130 --imu-max-mb 30
python frodo_between.py --out-dir out-between --parts all --rides-per-part 30 --budget-min 130 --imu-max-mb 30
```

- `frodo_gps.py` measures the GPS error against the wheels: scatter about a line while driving straight, and drift while the wheels stand still.
- `frodo_odometry.py` scores ways to predict the next GPS fix between fixes: holding still, the GPS's own velocity, and wheel distance turned by the GPS course, the gyroscope or the command.
- `frodo_compass.py` finds which magnetometer axes are horizontal, fits a hard-iron circle and the mount bias per ride, and scores the compass heading against the GPS course for carrying the wheels, choosing on even rides and scoring on odd ones. `frodo_compass_live.py` repeats it with calibrations a pilot could make while driving (needs `frodo_compass.py` next to it).
- `frodo_blend.py` holds the last GPS course for a few seconds after each fix before switching to the live compass, and `frodo_blend_b.py` checks the chosen hold on rides the first sample left out (both need `frodo_compass.py`, `frodo_compass_live.py` and `frodo_motion.py` next to them).
- `frodo_between.py` re-scores `frodo_blend_b.py`'s rides with headings a live pilot can compute: the last compass read held, or turned by the gyroscope or the turn command since (needs `frodo_blend.py`, `frodo_blend_b.py`, `frodo_compass.py`, `frodo_compass_live.py` and `frodo_motion.py` next to it).

Each read 227 to 479 MB in 20 to 51 minutes and writes `report.md`, `summary.json` and `rides.jsonl`. Standard library only.

```
python frodo_frames.py --out-dir out-frames --parts all --rides-per-part 2 --segments 4 --offsets 2,7,12
```

It reads a few front-camera video segments and the control log of 2 rides per part, takes frames at the given seconds into each segment (with ffmpeg), runs 8 settings of the camera scan on each, and labels each frame with how far the driver went straight on afterwards. Our run read 708 MB in 23 minutes. It writes `report.md`, `summary.json`, `frames.jsonl` and a thumbnail of each frame. Needs ffmpeg and Pillow.

```
python miniplus_b.py --out-dir out-miniplus-b
```

It finds public LeRobot recordings of the Earth Rover Mini+ on the Hugging Face Hub, reads their table files (no video) and measures how often `orientation` changes, which way it runs under a turn command, which `rpms` column is which side, whether `speed` matches the wheels, and whether there is a GPS fix. `miniplus.py` is its first version, kept for the record. Both need pyarrow and write `report.md` and `summary.json`; a run takes a few minutes. Only measurements are written out, with each recording's id and licence.

## Check a mission before driving it

```
python rover_pilot.py --fetch-osm --check-route --route-out legs.geojson > check.json
```

This reads the rover's GPS position and the mission's checkpoints, plans every leg that is still to be driven, and prints a summary. No command is sent to the rover. For each leg it gives `straight_m`, `route_m` (the planned walkable route, or `null` where none was found) and `detour` (route length divided by straight-line length). The exit code is 0 only if every leg has a route. Open `legs.geojson` in any GeoJSON viewer to see each leg on a map.

Things to look at before a long run:
- a leg with `route_m: null`: the pilot would head straight at that checkpoint. Check the map there, or fetch a bigger area.
- a large `detour` (say above 2): the map may be missing a crossing or a path. Look at that leg on the map.
- an `error` on a leg: the planner failed there (for example, Overpass was busy). Run the check again later.
- the total `route_m` against the rover's range: `python marathon.py route check.json` (see below).

Try it in the simulator with any saved map that covers its start point (37.8719, -122.2585): `python rover_pilot.py --simulate --osm area.json --check-route`.

## Marathon budget (`marathon.py`)

Human drivers took an Earth Rover Mini+ from UC Berkeley to Stanford, about 50 miles in seven legs, by remote control in 29 h 38 min (FrodoBots, Sept 2026). The SDK README gives the Mini+ "12 km range per charge, top speed 4 km/h". Put together:

```
python marathon.py budget
```

- 50 miles is 80.5 km. At its top speed a Mini+ needs at least **20.1 h** of driving, so the human time can hold at most **9.5 h** of stops, however the legs and the charging were arranged.
- With no stops at all, beating the human time needs **0.754 m/s** made good: **68%** of the top speed, held for 80 km. At the pilot's default cruise of 0.6 a Mini+ can't reach that even if it never slows down.
- Seven legs of **11.5 km** on a **12 km** charge leave about **4%** for anything driven beyond the route: detours, re-plans, back-up moves, weaving around obstacles. A pilot whose path is more than about **1.04 times** the route would run out of battery before the end of a leg, if the 12 km holds at its speed.

```
python marathon.py route check.json      # a saved --check-route summary against one charge
python marathon.py pace summary.json     # pace_study.py's summary.json against the budget
```

`route` gives the planned route's share of a charge, the metres to spare and its detour against straight lines; a route with legs that have no walkable route is flagged as a lower bound. `pace` takes the simulated marathon-pace study and, for each cruise, gives the hours of driving the 80.5 km would take at its median speed made good, the stops that leaves, and whether its median path ratio fits in a charge. `--range-km` and `--top-kmh` change the rover's figures.

Limits: the 12 km and 4 km/h are the README's figures, not measurements. How far a charge really goes depends on speed, slope, surface and temperature; since v0.10.0 the pilot logs `/data` `battery` against distance, so the first long run measures it. Whether the 29 h 38 min includes the time between legs isn't published; if it does, the humans drove faster than 0.754 m/s.

## Marathon pace (`pace_study.py`, `pace_b.py`, `pace_c.py`)

```
python pace_study.py --out-dir out --seeds 12
python marathon.py pace out/summary.json
python pace_b.py --out-dir out-b --seeds 12
python pace_c.py --out-dir out-c --seeds 12
```

648 simulated missions on a Mini+ stand-in (1.11 m/s at full `linear`, a fix and an orientation every 2 s), on three 1.3-1.6 km courses, at cruise 0.6, 0.8 and 1.0. Every mission was completed.

- At cruise **0.6** the rover made good **0.66 m/s**: no run reached the human pace of 0.754 m/s.
- At **0.8** it made good **0.87 m/s** and every run beat the human pace. Over 80.5 km that is about 25.8 h of driving, leaving about **3.9 h** for every stop of the marathon.
- At **1.0** it made good **1.08 m/s**, leaving about **8.9 h**, but on a course of right-angle corners its path grew to **1.035-1.059 times** the route, close to or past the 1.044 a 12 km charge allows.
- The orientation arriving only every 2 s costs under 1.5%. Public Mini+ recordings later showed it changing about every 0.5 s, so this was a pessimistic case. Predicting the heading between reports helped when the predictor knew the turn rate and hurt when it didn't, so it isn't used.
- `pace_b.py` (720 missions) flew it again with the telemetry public Mini+ recordings show (orientation every 0.5 s, 48°/s, 0.5 s latency): **0.878 m/s** at 0.8, every run beating the human pace, about **4.2 h** left for stops; at 1.0 the city-blocks path was 1.028 times the route. Cruise 0.7 beat the pace on every course, but by only about 2%.
- **Compass noise is the risk to watch.** 10° of noise on each orientation reading cost 2.4-3.1% in every group (0.855 m/s at 0.8, about 3.5 h for stops) and took cruise 0.7 below the human pace. Commands landing after 0.8 s instead of 0.5 s cost under 1%.
- **Smoothing the heading wins most of it back.** `pace_c.py` (720 missions, pre-registered, all 8 predictions held) moved each new reading only 0.3 of the way from the last estimate, after turning that estimate by the commanded `angular` at 48°/s. With 10° of noise it was faster in all 6 cruise × course groups (2.1-2.5%): **0.874 m/s** at 0.8 (about 4.1 h for stops) and 0.768 at 0.7, where every run beat the human pace again. With a clean compass it cost nothing. A plain average without the turn helped about half as much with noise, and with a clean compass it was slower, because it lags behind turns. Assuming 30°/s instead of 48°/s changed almost nothing. This is `--smooth-heading`, off by default until a real Mini+'s compass noise is measured.

The cruise stays 0.6 by default: the simulator has no people, crossings or kerbs, and the SDK suggests 0.3-0.5 for first tests. For the marathon, `--marathon` sets 0.8 with the real-rover steering; measure the range at that cruise first. Details in [FINDINGS-frodobots-2k.md](FINDINGS-frodobots-2k.md).

## Front camera (`free_space.py`, experimental)

Each frame from `GET /v2/front` is shrunk to 64 × 36 pixels.

1. **Ground colour.** The band just in front of the rover (bottom 3 rows, middle 40%) gives the colour of the surface being driven on. Brightness may vary by a wide margin, so shadows still count as ground. A surface that keeps looking different for 3 s (say, from pavement onto a gravel path) becomes the new ground.
2. **Free space.** Every column is followed up from the bottom while it still looks like ground. With the camera's height and tilt, the row where it stops becomes a point on the ground, in metres to the right and ahead.
3. **Corridors.** For directions every 5° across the view, it measures how far a 0.8 m-wide corridor runs before it meets one of those points.
4. **Decision.** If the corridor toward the pilot's target is clear for 5 m (or up to the checkpoint, if that is nearer), nothing changes. Otherwise the pilot steers along the clear direction closest to the target. It keeps to the same side for 2 s, so it doesn't swing between the two sides of an obstacle. It slows down if even the best direction is short. When nothing is clear for 1.2 m, it turns in place toward the more open side for 1.5 s.

If no frame arrives for a second, the pilot drives on at half speed. Camera errors never stop the pilot.

**Measured on real frames.** `frodo_frames.py` ran 8 settings of the scan on 493 front-camera frames from 48 recorded FrodoBots-2K rides. Each frame is labelled with what the human driver did next. With the defaults, on frames after which the driver went at least 2 m straight, the scan saw less than 1.2 m clear (so the guard would turn in place) 35% of the time. After a 5.5 m straight run, it saw less than 5 m clear (so the guard would swerve or slow) 79% of the time. Tree shadows, glare and the rover's own body at the bottom of the frame caused most of these. `free_space.REAL_ROVER` leaves out the 3 bottom rows, accepts ground from 0.2 to 2.5 times the patch brightness, allows a wider colour spread, and needs 4 non-ground rows in a row before it calls something an obstacle. That brought the phantom stops to 8% (95% CI 4–15%) and the phantom swerves to 7% (2–23%). So since v0.9.0, `--vision` on a real rover uses `REAL_ROVER`. The simulator keeps the defaults, and `--vision-plain` brings them back on a real rover.

**Checked on other rides.** The setting was chosen as the best of 8 on those same frames, so it was run unchanged on 837 frames from 72 other rides at other frame times, with the prediction written down first. Phantom stops fell from 39% (default) to 4% (95% CI 2–7%), as predicted; phantom swerves from 78% to 22%, less good than the 7% first measured.

Still experimental, for two reasons. The recorded data has no obstacle labels, so how many real obstacles the new setting misses is not known: on the frames just before a moving driver stopped or turned hard, it called 30% blocked against the default's 88%, and if a real obstacle looks like a shadow it is more likely to drive at it. And the frames come from Earth Rover Zero-era rovers, not the Mini+. Details are in [FINDINGS-frodobots-2k.md](FINDINGS-frodobots-2k.md).

What it can't do in any case: it sees colour, not depth. An obstacle the same colour as the ground (a grey wall on grey pavement) is missed. It has no memory, so something it has driven past and can no longer see doesn't count. It can't tell that the rover has tipped over: one recorded frame, turned 90°, read as clear; since v0.9.2 the accelerometer does that (see "Tipped rover" above). It is a cheap first layer. A learned free-space model trained on the FrodoBots datasets could replace it later behind the same `advise()` call.

## Route planning

`route_planner.py` fetches the ways a pedestrian may use in a bounding box from the [Overpass API](https://wiki.openstreetmap.org/wiki/Overpass_API). It builds a graph and finds the cheapest route with A*.

- Footways, paths and pedestrian streets cost 1 per metre.
- Roads cost more (1.3 for residential up to 2.0 for primary). A road tagged with a sidewalk costs 1.1. A road tagged `sidewalk=no` costs double.
- Steps, motorways, trunk roads and ways closed to pedestrians are left out.

Fetch an area once, check the route on a map, then drive with the saved file:

```
python route_planner.py fetch 37.85,-122.28,37.88,-122.25 -o berkeley.json
python route_planner.py route berkeley.json 37.8719,-122.2585 37.8700,-122.2650 -o route.geojson
python rover_pilot.py --osm berkeley.json --calibration rover.json --log run.jsonl
```

Open `route.geojson` in any GeoJSON viewer to see the route before the rover drives it. Please keep Overpass use light: one fetch per area, then reuse the file.

Map data © [OpenStreetMap contributors](https://www.openstreetmap.org/copyright), available under the ODbL. This repository contains no map data; it is fetched when you run the planner.

## Assumptions to check on the first real run

- Which way `orientation` and `angular` run: `--calibrate` measures this. Without a calibration, the pilot assumes compass degrees clockwise from north (as the SDK dashboard draws it) and a positive `angular` turning left (as the recorded rides, the SDK's ROS2 bridge and LeRobot's driver show).
- `orientation` updates often enough to follow a 0.4 spin. If it jumps by more than a third of a turn between readings, calibration stops and says so.
- The server judges a checkpoint against the rover's own latest GPS reading.
- `/checkpoints-list` returns the mission's checkpoints before the first `/start-mission`, so `--check-route` can run before the clock starts. If it returns none, the check has to run after the start, or from a copy of the checkpoints.
- The shape of the `/missions` answer: the pilot accepts a list, or a list under `missions`, `items` or `data`.
- The steering (`angular` up to 1.0, turn in place above 90°) comes from a simulation of the recorded motion. Watch the first legs; `--max-angular` and `--turn-in-place` change it.
- The `/data` `timestamp` changes with each telemetry report from the rover. If the log shows `telemetry-stale` while the rover's telemetry is plainly fine, it doesn't; use `--telemetry-timeout 0` and rely on the SDK watchdog.
- `/data` `accels` rows are `[x, y, z, ...]` in g (or m/s²), and the rover starts the mission upright. If the log shows `tipped` while the rover is plainly upright, look at the logged angle; `--tip-angle 0` turns the check off.
- `/data` `rpms` rows hold four signed wheel speeds in RPM, forward positive, followed by a timestamp. Public Mini+ recordings fit this so far (all four positive when driving forward, on 17 frames). If the result's `dead_reckon` shows the wheels never trusted, check the rows; `--no-dead-reckon` steers on GPS alone.
- `/data` `battery` is a percent. The result's `battery` gives metres per percent; if it reads nonsense, the unit is something else.
- The front camera's field of view, height and tilt (`--camera-*`), if `--vision` is tried. A wrong tilt makes obstacles look nearer or farther than they are. Watch `clear_m` in the log on the first runs.
- OSM sidewalks are mapped well enough in the mission's area. Where they aren't, roads stand in for them.
- A Mini+ charge covers 12 km at the cruise you choose (`marathon.py` assumes it). The result's `battery` measures it on the first long run.
- With `--smooth-heading`: the `/data` `timestamp` changes with each new orientation reading, and `angular` turns the rover at about the rate assumed (48°/s per unit, or the calibration's). The result's `smooth_heading` counts the readings used; if it stays near 1, the timestamp doesn't change and the heading is frozen, so leave the option off.

## Not done yet

- The camera layer's miss rate on real obstacles is unknown, and the chosen setting still has to be checked on a Mini+. A learned model may be needed in the end.
- Indoor and off-road tracks use image goals, not GPS. This pilot covers only GPS checkpoint missions.
- The steering for a real rover comes from simulation. It still has to be checked on a real rover.
- The gyroscope isn't used between GPS fixes yet; the wheels are (`dead_reckon.py`). Their gain on a real rover is measured only on recorded rides, not on a live one.
- A still rover's GPS has been measured on 150 recorded rides: it drifts 0.5 m in 10 s and 2.7 m in 5 minutes (see FINDINGS). A steady offset of the whole track can't be measured that way. A bias fit that uses the wheels or the gyroscope may be the next gain.
- Battery: since v0.10.0 the pilot logs `/data` `battery` against distance; the 12 km range per charge is still the README's figure until a real run measures it.
- Marathon pace was simulated on 1.3-1.6 km courses. A long run (an 11.5 km leg) and the battery used at cruise 0.8 still have to be measured.

## Tests

```
python -m unittest test_rover_pilot test_rover_defaults test_steering_defaults test_telemetry test_tip_and_bias test_calibrate test_calibrate_real test_route_planner test_free_space test_free_space_skip test_vision_settings test_frodo_motion test_frodo_frames test_gps_lag test_gain_study test_gps_noise_study test_marathon test_dead_reckon test_battery_log test_marathon_preset test_release test_frodo_gps test_frodo_odometry test_frodo_compass test_frodo_compass_live test_dead_reckon_study test_pace_study test_frodo_blend test_frodo_blend_b test_course_hold test_frodo_between test_miniplus test_miniplus_b test_pace_b test_pace_c test_smooth_heading -v
```

The tests cover:
- geometry and the GPS filter
- compass-bias learning
- the steering law and path following
- the HTTP client, with a mocked SDK, including slow and unanswered checkpoint reports, camera frames and the missions list
- full simulated missions on several seeds, including heavy GPS dropouts, a rover stuck for its first 30 s, a planned dogleg route and a planner that fails
- leg summaries, and resuming a mission whose first two checkpoints the server already counts
- orientation and turn conventions: degrees, 0–255 and radians, either direction, a left-turning `angular`; a rover with the opposite `angular` sign going nowhere without a calibration, and a rover with every convention reversed flying the whole mission with one
- the real-rover defaults: a positive `angular` turning left, used by the command line on a real SDK without `--calibration`, overridden by a calibration, not used in the simulator, and flying the whole mission on a simulated left-turning rover
- the real-rover steering: `angular` up to 1.0 and turning in place above 90° on a real SDK, the simulator's own steering kept, `--max-angular` and `--turn-in-place` overriding either, and a real-like left-turning rover at 30°/s flying the demo with it
- lost telemetry: the timestamp and `/status` checks, `/status` asked at most once a second, the simulator flying exactly as with the check off, a rover whose telemetry freezes 15 s into the demo stopped within about 5 s (by timestamp, or by `/status` alone), the same freeze going unnoticed with neither, a rover that drives on and finishes the mission when telemetry is back, `GET /status` parsing, and `--telemetry-timeout`
- the tipped rover: reading `accels` rows (in g or m/s², bad rows skipped), learning the upright direction on any axis, a 30° slope not counting, short knocks and readings far from 1 g ignored, no `accels` meaning no opinion, `--tip-angle 0`; a simulated rover with an accelerometer stopped within 1.5 s of tipping 20 s into the demo and finishing the mission once righted, one that stays tipped staying stopped, and the plain simulator flying exactly as before
- the compass-bias fit: a clean stretch's length, points and residual, the residual gate leaving out a bent stretch (and the plain fit not), weighting all but dropping a scattered, skewed stretch next to a clean one, the weighted bias wrapping across ±180°, and the demo flown with both options on
- calibration in the simulator: the usual rover, one with every convention reversed, a mirrored compass only, a left-turning `angular` only; the starting bias, turn rate and speed it measures; and failures (no GPS fix, no turn seen, a rover that can't move), each ending with a stop
- calibration on a rover that moves like the recorded ones (30°/s per unit): a 30 s spin falls short of a whole turn, and the longer spin calibrates it, turning either way
- the command line: calibrate a quirky simulated rover, save the result and fly the mission with it; a failed calibration is refused
- the route check: each remaining leg measured from the rover's position, legs with no route, a planner error on one leg, no GPS fix, the GeoJSON output, and the command line on a synthetic map with nothing driven
- the camera model, ground-colour matching, corridors, and the guard's choices: leave the heading alone, steer to the nearer side, stop and turn at a wall, slow down with no frames, learn a new surface
- `skip_rows`: the defaults unchanged; the rover's body in the bottom rows read as an obstacle by default, and open ground seen once those rows are left out, in the scan and in the guard
- the real-rover camera settings: `REAL_ROVER` being the setting the frame study measured; a hard shadow band 1 m ahead stopping the default guard but read as ground with `REAL_ROVER`; a hedge still seen with `REAL_ROVER`; and the command line using `REAL_ROVER` on a real rover, the defaults in the simulator and with `--vision-plain`
- closed loop in the simulator: with a 2 m hedge on the straight line to the checkpoint, the rover without vision drives into it, and with vision it goes around without touching it (two seeds)
- the route planner on synthetic maps: detours, footways versus busy roads, sidewalks, disconnected networks, ways cut at the edge of the fetched area, and the command line
- `frodo_motion.py`: reading zips through range requests (including zip64 and CRC checks), IMU parsing, and the analysis on a simulated rover with a known turn direction, speed, GPS delay and gyroscope axis
- `frodo_frames.py`: segment times in UTC, wheel speed, the distance driven straight after a frame and what ends it, event frames, the Wilson interval, each scan setting on open ground and with a hedge ahead, and the summary
- late GPS: the compensator's offsets (straight, stopped and reversing, stale fixes, unknown heading), the simulator's GPS delay keeping its random sequence, zero lag being exactly the plain pilot, the corrected position running ahead of the fix, and `--sim-real --gps-lag 1.5` flying the demo
- `gain_study.py`: the grid, the baseline being the simulator's steering, the real-like profiles, the sign test, picking the best setting, flying the demo, and the command line's outputs
- `gps_noise_study.py`: the drifting error keeping its size and correlation, zero correlation being independent noise, zero correlation time being exactly the plain simulator, drifting error moving slowly while the rover stands still, flying the demo with 1 s and 2 s fixes and recording how far the rover truly was at each credit, the bias-fit variants naming real settings and flying drifting GPS, the summary and verdicts, and the command line's outputs
- `marathon.py`: the human benchmark (80.5 km, 29 h 38 min, 0.754 m/s), what it asks of a Mini+ (20.1 h of driving at least, 9.5 h of stops at most, 68% of top speed, a path at most 1.044 times the route on a 12 km charge), other top speeds and ranges, a route that fits a charge, one too long and one with unrouted legs, the pace study's rows against the budget, and the command line on saved files
- dead reckoning: wheel distance from `rpms` rows placed by their timestamps, cached readings adding nothing, bad rows ignored, reversing; the position carried between late fixes, the wheel size learned from a wrong prior and only then trusted, wheels that read zero or implausibly never trusted, no learning on curves, turns following the compass, a far fix resetting the estimate, the estimate expiring 30 s after the last fix; the simulator reporting wheels only when asked, a mission flown with it, a GPS gap driven through on the wheels, and no dead reckoning together with `--gps-lag`
- the 0.10.0 defaults: dead reckoning along the heading on a real rover, off in the simulator and with `--gps-lag`, `--no-dead-reckon`, `--mps-per-rpm`, and the help text; the battery log (a straight drive, jitter while standing still not counted, bad levels left out, no range until enough charge is used, a rover with no `battery`); the `--marathon` preset and explicit flags winning over it; a simulated mission reporting battery and leg levels, and a marathon-preset mission with dead reckoning reporting both
- `frodo_gps.py`: still periods and straight stretches, the line fit, the drift fit recovering a known drift and refusing a fit on its search bound, wander growing with time, a carried ride flagged, jumps and gaps, and reading a zip part
- `frodo_odometry.py`: the nearest fix, fresh fixes, dead reckoning on a grid, the guards, anchors and misses, heading sources, the best gains, the straight stratum, intervals and outputs, and reading a zip part
- `frodo_compass.py`: the six axis frames, the hard-iron circle on a full circle and its refusals, headings across north, the course fit, the decision rule, learning the mount on a straight ride, frame choice, the predictors, outputs and reading a zip part; `frodo_compass_live.py`: data before a time, running centres, calibration windows, a whole ride, misses, the summary, outputs and guards
- the GPS-course hold (`dead_reckon.py` 0.2.0, `test_course_hold.py`): the course followed inside the hold, the hard switch at its end, the fade continuous and fading out, no hold without a fresh course, and the pilot unchanged with the hold off; the 0.11.0 setting reaching the pilot from the command line
- `frodo_blend.py` and `frodo_blend_b.py`: the hard and fading switches, the shift wrapping across north, the switch counted from the anchor, reproducing `frodo_compass_live.py`'s and `frodo_blend.py`'s misses exactly, the decision rules, and the held-out sample sharing no ride with the first
- `frodo_between.py`: the latest read at or before each step and none before a centre, the gyroscope rate taken only from the past and its offset, the gyroscope and command turns, the hold before the switch, holding the last read costing on turns, reproducing `frodo_blend_b.py`'s misses exactly, the same pairs for every variant, and the decision rules
- `miniplus.py` and `miniplus_b.py`: angles across north, a GPS reading of 1000 being no fix, fields that never change counted as missing, turn windows on synthetic recordings whose orientation runs either way, the lag between command and state, mixed-sign and small windows left out, forward and turning wheel frames, repeated wheel columns and which side is which, the speed check, refresh intervals, the gyroscope against the turns, the decision rules, LeRobot column names and episodes, and the command line's outputs
- `dead_reckon_study.py`: the GPS gaps being the same for every variant, no fix inside a gap, drifting error wandering slowly, and a small run end to end
- `pace_study.py`: the human pace and cruise floor, the courses and their planner, a rover whose orientation holds between reports, the heading predictor (a no-op on fresh orientation), flying a short course, time accounting, the sign test, the summary and the command line's outputs
- `pace_b.py`: the baseline profiles being `pace_study.py`'s, the measured profile, each variant changing one thing from it, a rover whose orientation refreshes every 0.5 s and holds in between, a zero period being `pace_study.py`'s rover, the same missions as `pace_study.py` on its own profiles, a short course, a lost completion, the paired effects, the summary and the command line's outputs
- `pace_c.py`: the smoother's average, crossing north, holding between reports and turning by the command; a plain average lagging a turn; the profiles being `pace_b.py`'s; the shipped variant flying exactly as `pace_b.py`; smoothed short courses; the shares of the shipped time; and the command line's outputs
- `--smooth-heading` (`HeadingSmoother`, `test_smooth_heading.py`): the average, crossing north, holding between readings with or without a timestamp, turning by the command either way, a missing reading, old commands dropped; the pilot recording its own `angular` whatever the rover's convention; flying exactly the same missions as `pace_c.py`'s `cf0.3`, `cf0.3-yaw30` and `ema0.3` on a short course with a corner; off by default; a quirky rover flown with its conventions; and the command line, with the turn rate taken from a calibration

## License

Code: Apache-2.0 (see `LICENSE`) from 14 October 2026; releases up to v0.5.0 keep the licence they were published with. Copyright 2026 Munim, Inc. The FrodoBots-2K numbers in `FINDINGS-frodobots-2k.md` derive from FrodoBots-2K (FrodoBots Lab, CC BY-SA 4.0) and are shared under CC BY-SA 4.0. Map data fetched at run time is © OpenStreetMap contributors (ODbL). Not affiliated with FrodoBots, BitRobot or the Earth Rover Challenge organisers.
