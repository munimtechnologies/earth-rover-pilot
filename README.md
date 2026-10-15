# earth-rover-pilot

A GPS waypoint pilot for the [FrodoBots Earth Rover SDK](https://github.com/frodobots-org/earth-rovers-sdk). It drives an Earth Rover through the checkpoints of an SDK mission and reports each one with `/checkpoint-reached`. Each leg can follow a walkable route planned on OpenStreetMap instead of a straight line, and every leg of a long mission can be planned and checked on a map before the rover moves. A short calibration run on the rover works out which way its compass and turn commands run, so the pilot never steers backwards. An experimental front-camera layer can steer it around obstacles.

The [Earth Rover Challenge](https://earth-rover-challenge.github.io/) uses this mission format: AI teams and human gamers drive the same sidewalk rovers in real cities over the internet. Its urban and marathon tracks are GPS-checkpoint missions; the marathon runs about 50 miles from UC Berkeley to Stanford. It is also BitRobot's [Earth Rover Grand Challenge](https://bitrobot.ai/grand-challenges/earth-rovers).

Made by **MV2 of Munim, Inc.** The code was written with AI agents.

**Status (v0.9.0):** the pilot has been tested only against the built-in simulator, synthetic maps and recorded data. It has not driven a real rover yet. What real rovers do with its commands has been measured on 279 recorded rides from the public FrodoBots-2K dataset ([FINDINGS-frodobots-2k.md](FINDINGS-frodobots-2k.md)), the simulator can move like them (`--sim-real`), and the steering for a real rover was chosen by a simulation study on that motion (`gain_study.py`). v0.9.0 reads a real rover's camera with the settings that saw the fewest phantom obstacles on 493 recorded front-camera frames: about 1 in 12 clear paths instead of 1 in 3 (see "Front camera" below). It is still experimental. Treat the defaults as a starting point and tune them on the first real runs, starting with `--calibrate`. Since v0.8.1 the rover is stopped when its telemetry stops coming in (see "Lost telemetry" below).

## What the recorded rides say

`frodo_motion.py` reads the control, wheel-RPM, GPS and IMU logs of a sample of FrodoBots-2K rides straight from the dataset's zip files, without downloading the video. On 279 rides across all 24 parts:

- a positive `angular` turns the rover **left** (440 to 57 in a sign test). The SDK's ROS2 bridge and LeRobot's Earth Rover driver both send a left turn as a positive `angular`, too.
- it turns at about **30°/s per unit of `angular`** (the gyroscope's x axis, which reads degrees per second, counter-clockwise positive)
- at full `linear` the rover covers about **0.8 m/s**
- the wheels respond about **0.8 s** after a command, and GPS shows the motion about **1.5 s** after the wheels, so a turn reaches the GPS course about **2.5 s** after it is commanded
- the effective wheel radius is **0.064 m** (0.0067 m/s per RPM)

`frodo_frames.py` reads front-camera frames from 48 rides and labels each one with what the driver did next: on frames after which the driver went at least 2 m straight, the camera layer's default settings saw a wall within 1.2 m 35% of the time. Shadows did most of it.

So since v0.6.0, a real rover without `--calibration` is driven with a positive `angular` turning left. Earlier versions assumed right, which would make every correction turn the rover further away. Details, limits and credits are in [FINDINGS-frodobots-2k.md](FINDINGS-frodobots-2k.md). The numbers there derive from FrodoBots-2K (FrodoBots Lab, CC BY-SA 4.0) and are shared under the same licence.

## Why not the plain example

The SDK ships a simple waypoint example. On a real rover, a bearing-follower like that runs into these problems, and this pilot handles each one:

| Problem | What the pilot does |
|---|---|
| The SDK doesn't say which way a positive `angular` turns, or what `orientation` reads (its example shows `128`). Guess wrong and every correction turns the rover further away. | Without a calibration, a real rover is driven with a positive `angular` turning left, as the recorded rides show. `--calibrate` spins the rover, drives two short straights with a turn between them and measures both (see below). `--calibration` applies the result. |
| With no fix, the rover reports latitude/longitude `1000`. Bad parsing turns missing values into 0/0. | `GpsFilter` drops no-fix, 0/0, NaN and impossible jumps. It smooths the remaining fixes and stops the rover if no fix has arrived for 3 s. |
| The SDK caches the last telemetry it got, so when the rover's link drops, `/data` keeps showing the same GPS fix and the rover would be steered blind. | `TelemetryWatch` stops the rover once no new telemetry has come in for 5 s, and lets it drive on when telemetry is back (see "Lost telemetry" below). |
| The compass is offset by the motors, the mount and local magnetic fields. | `HeadingEstimator` learns the bias as the rover drives. On straight stretches it fits a line through the GPS fixes and compares that course with the mean compass reading, then corrects the offset gradually. If the compass drops out, it falls back to the last GPS course. |
| A checkpoint a few hundred metres away is behind buildings, fences or water. | With `--osm` or `--fetch-osm`, each leg is planned on OpenStreetMap footways, paths and sidewalks (`route_planner.py`), and `PathFollower` steers along it (pure pursuit, 8 m lookahead). If the rover strays more than 30 m it replans. |
| A marathon has dozens of legs; finding a leg with no walkable route halfway through costs the run. | `--check-route` plans every remaining leg from where the rover stands, without driving, and reports each leg's straight-line and routed length (see below). |
| A bin, a planter or a parked scooter sits on the line the rover is driving. | With `--vision`, `free_space.py` reads the front camera 5 times a second, works out how far the rover could drive in each direction, and bends the heading to the nearest clear one. Experimental: on recorded frames it still sees a phantom obstacle on about 1 in 12 clear paths, and how many real ones it misses isn't measured (see below). |
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

Make the simulated rover move like the recorded ones (0.79 m/s at full `linear`, commands 0.8 s late, GPS 1.5 s behind the wheels):

```
python rover_pilot.py --simulate --sim-real
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
- `--cruise 0.6`: forward command, 0 to 1. The SDK suggests 0.3–0.5 for first tests. On the recorded rides, 0.6 covered about 0.46 m/s.
- `--max-angular`: the largest `angular` the pilot sends, 0 to 1. Default 1.0 on a real rover, 0.6 in the simulator.
- `--turn-in-place`: turn in place when the heading error is above this many degrees. Default 90 on a real rover, 60 in the simulator.
- `--report-radius 10`
- `--gps-lag 0`: seconds the GPS runs behind the rover. Above 0, each fix is moved forward by the driving commanded since it was taken, assuming 0.79 m/s at full `linear` and commands 0.8 s late. Off by default; see "Late GPS" below.
- `--telemetry-timeout 5`: stop the rover while no new telemetry has come in for this many seconds; 0 turns it off. See "Lost telemetry" below.
- `--osm area.json`: plan each leg on a saved map area (see below).
- `--fetch-osm`: fetch the map around each leg from Overpass as needed.
- `--check-route`, `--route-out legs.geojson`: plan every remaining leg and report it, without driving (see below).
- `--vision`: steer around obstacles seen by the front camera. Experimental. On a real rover it uses `free_space.REAL_ROVER` (see "Front camera" below); in the simulator, the `VisionGuard` defaults.
- `--vision-plain`: with `--vision` on a real rover, use the `VisionGuard` defaults instead. They see far more phantom obstacles; this is for comparison.
- `--camera-fov 90`, `--camera-height 0.35`, `--camera-pitch 5`: the front camera's horizontal field of view (degrees), height above the ground (metres) and downward tilt (degrees). These are guesses; measure them on the rover.
- `--simulate`, `--seed 1`, `--sim-real`, `--sim-quirks`, `--obstacles`: simulator options.
- `--timeout 3600`
- `--no-start`: resume a mission that has already started.

Ctrl-C sends a stop. The log (`--log`) records one JSON line per second, plus each checkpoint, refusal, plan and recovery, and each time telemetry is lost (`telemetry-stale`) or back (`telemetry-back`), so a run can be checked afterwards. With `--vision`, each line also has `clear_m`, how far ahead the camera saw clear ground.

### Leg summaries

The result printed at the end has a `legs` list, and the log has one `checkpoint` line per leg, with:
- `seq`: the checkpoint the leg ended at
- `elapsed_s`: time from the previous checkpoint (or the start) to this one
- `straight_m`: straight-line distance to the checkpoint when the leg began
- `reports`: how many `/checkpoint-reached` calls it took (1 means the first one counted)
- `recoveries`: how many back-up-and-turn moves the leg needed

On a long mission these show which legs were slow or hard, so the next run can be tuned for them. The result also has `telemetry_stops`, how many times the rover was stopped for lost telemetry.

## Lost telemetry (`--telemetry-timeout`)

The SDK caches the telemetry the rover pushes to it, and `/data` serves the latest copy. Its README says the rover "executes its last command until a new one arrives", and that the SDK's own watchdog can't help when the rover itself loses its connection. Before v0.8.1, a repeated GPS reading counted as the fix still holding, so if telemetry stopped while commands still got through, the pilot went on steering toward the checkpoint from a position that no longer moved. In the simulator, with telemetry frozen 15 s into the demo, it kept sending drive and turn commands until the mission timed out.

Now the pilot counts a reading as new only when its `/data` `timestamp` changes. It also asks `GET /status` once a second for the SDK's `telemetry_age_s` (seconds since the last telemetry message), where the SDK has it. When either shows no new telemetry for more than 5 s, the pilot sends stop commands and logs `telemetry-stale`. When readings come in again, it logs `telemetry-back` and drives on. An Earth Rover Mini+ reports every 2 s (SDK README), so one late or lost report doesn't stop it, and two in a row do.

Limits: the SDK README doesn't define the `/data` `timestamp`. If it turns out to change on every request rather than with each rover report, only `/status` catches a stall. An SDK without `/status` and without a usable timestamp gives the pilot nothing to go on, and it drives as before (`test_telemetry.py` checks that case too). If a real rover is stopped for this when its telemetry is fine, the log shows `telemetry-stale` lines; `--telemetry-timeout 0` turns the check off. In the simulator the timestamp changes on every reading, so simulated missions fly exactly as before.

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

Every mission was completed either way. On the real-like rover turning at the measured 30°/s, the correction saved a few seconds at most, and the result could be chance (17 faster to 11 slower on the demo, p = 0.34; 16 to 8 on the zigzag, p = 0.15). At 60°/s it made the zigzag slower (7 faster to 20 slower, p = 0.019). In every group it about doubled to tripled the refused checkpoint reports, because the corrected position reaches the report radius before the GPS the server judges by does. So it stays off by default. The full table is in [FINDINGS-frodobots-2k.md](FINDINGS-frodobots-2k.md). This is a simulation result; a real rover may differ.

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

## Measure the rovers from FrodoBots-2K (`frodo_motion.py`, `frodo_frames.py`)

```
python frodo_motion.py --out-dir out --rides-per-part 12
```

It reads the dataset's index, then each of the 24 zip parts (2 to 95 GB each) through HTTP range requests: first the zip's central directory, then only the control, GPS and IMU CSVs of 12 rides spread through the part (an IMU file above `--gyro-max-mb`, 40 by default, is skipped). It refuses to go on if the server ignores range requests, so it never downloads a whole part. Our run read about 317 MB in 19 minutes. `out/report.md` sums up the findings, `out/summary.json` has every table and `out/rides.jsonl` has one line per ride. Standard library only.

```
python frodo_frames.py --out-dir out-frames --parts all --rides-per-part 2 --segments 4 --offsets 2,7,12
```

It reads a few front-camera video segments and the control log of 2 rides per part, takes frames at the given seconds into each segment (with ffmpeg), runs 8 settings of the camera scan on each, and labels each frame with how far the driver went straight on afterwards. Our run read 708 MB in 23 minutes. It writes `report.md`, `summary.json`, `frames.jsonl` and a thumbnail of each frame. Needs ffmpeg and Pillow.

## Check a mission before driving it

```
python rover_pilot.py --fetch-osm --check-route --route-out legs.geojson
```

This reads the rover's GPS position and the mission's checkpoints, plans every leg that is still to be driven, and prints a summary. No command is sent to the rover. For each leg it gives `straight_m`, `route_m` (the planned walkable route, or `null` where none was found) and `detour` (route length divided by straight-line length). The exit code is 0 only if every leg has a route. Open `legs.geojson` in any GeoJSON viewer to see each leg on a map.

Things to look at before a long run:
- a leg with `route_m: null`: the pilot would head straight at that checkpoint. Check the map there, or fetch a bigger area.
- a large `detour` (say above 2): the map may be missing a crossing or a path. Look at that leg on the map.
- an `error` on a leg: the planner failed there (for example, Overpass was busy). Run the check again later.

Try it in the simulator with any saved map that covers its start point (37.8719, -122.2585): `python rover_pilot.py --simulate --osm area.json --check-route`.

## Front camera (`free_space.py`, experimental)

Each frame from `GET /v2/front` is shrunk to 64 × 36 pixels.

1. **Ground colour.** The band just in front of the rover (bottom 3 rows, middle 40%) gives the colour of the surface being driven on. Brightness may vary by a wide margin, so shadows still count as ground. A surface that keeps looking different for 3 s (say, from pavement onto a gravel path) becomes the new ground.
2. **Free space.** Every column is followed up from the bottom while it still looks like ground. With the camera's height and tilt, the row where it stops becomes a point on the ground, in metres to the right and ahead.
3. **Corridors.** For directions every 5° across the view, it measures how far a 0.8 m-wide corridor runs before it meets one of those points.
4. **Decision.** If the corridor toward the pilot's target is clear for 5 m (or up to the checkpoint, if that is nearer), nothing changes. Otherwise the pilot steers along the clear direction closest to the target. It keeps to the same side for 2 s, so it doesn't swing between the two sides of an obstacle. It slows down if even the best direction is short. When nothing is clear for 1.2 m, it turns in place toward the more open side for 1.5 s.

If no frame arrives for a second, the pilot drives on at half speed. Camera errors never stop the pilot.

**Measured on real frames.** `frodo_frames.py` ran 8 settings of the scan on 493 front-camera frames from 48 recorded FrodoBots-2K rides. Each frame is labelled with what the human driver did next. With the defaults, on frames after which the driver went at least 2 m straight, the scan saw less than 1.2 m clear (so the guard would turn in place) 35% of the time. After a 5.5 m straight run, it saw less than 5 m clear (so the guard would swerve or slow) 79% of the time. Tree shadows, glare and the rover's own body at the bottom of the frame caused most of these. `free_space.REAL_ROVER` leaves out the 3 bottom rows, accepts ground from 0.2 to 2.5 times the patch brightness, allows a wider colour spread, and needs 4 non-ground rows in a row before it calls something an obstacle. That brought the phantom stops to 8% (95% CI 4–15%) and the phantom swerves to 7% (2–23%). So since v0.9.0, `--vision` on a real rover uses `REAL_ROVER`. The simulator keeps the defaults, and `--vision-plain` brings them back on a real rover.

Still experimental, for three reasons. The recorded data has no obstacle labels, so how many real obstacles the new setting misses is not known. The setting was chosen as the best of 8 on the same frames, and a check on other rides is queued. And the frames come from Earth Rover Zero-era rovers, not the Mini+. Details are in [FINDINGS-frodobots-2k.md](FINDINGS-frodobots-2k.md).

What it can't do in any case: it sees colour, not depth. An obstacle the same colour as the ground (a grey wall on grey pavement) is missed. It has no memory, so something it has driven past and can no longer see doesn't count. It can't tell that the rover has tipped over: one recorded frame, turned 90°, read as clear. It is a cheap first layer. A learned free-space model trained on the FrodoBots datasets could replace it later behind the same `advise()` call.

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
- The front camera's field of view, height and tilt (`--camera-*`), if `--vision` is tried. A wrong tilt makes obstacles look nearer or farther than they are. Watch `clear_m` in the log on the first runs.
- OSM sidewalks are mapped well enough in the mission's area. Where they aren't, roads stand in for them.

## Not done yet

- The camera layer's miss rate on real obstacles is unknown, and the chosen setting still has to be checked on other recorded rides and on a Mini+. A learned model may be needed in the end.
- Indoor and off-road tracks use image goals, not GPS. This pilot covers only GPS checkpoint missions.
- The steering for a real rover comes from simulation. It still has to be checked on a real rover.
- Wheel RPMs or the gyroscope could carry the position and heading between GPS fixes. Not tried yet.

## Tests

```
python -m unittest test_rover_pilot test_rover_defaults test_steering_defaults test_telemetry test_calibrate test_calibrate_real test_route_planner test_free_space test_free_space_skip test_vision_settings test_frodo_motion test_frodo_frames test_gps_lag test_gain_study -v
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

## License

Code: Apache-2.0 (see `LICENSE`) from 14 October 2026; releases up to v0.5.0 keep the licence they were published with. Copyright 2026 Munim, Inc. The FrodoBots-2K numbers in `FINDINGS-frodobots-2k.md` derive from FrodoBots-2K (FrodoBots Lab, CC BY-SA 4.0) and are shared under CC BY-SA 4.0. Map data fetched at run time is © OpenStreetMap contributors (ODbL). Not affiliated with FrodoBots, BitRobot or the Earth Rover Challenge organisers.
