# earth-rover-pilot

A GPS waypoint pilot for the [FrodoBots Earth Rover SDK](https://github.com/frodobots-org/earth-rovers-sdk). It drives an Earth Rover through the checkpoints of an SDK mission and reports each one with `/checkpoint-reached`. Each leg can follow a walkable route planned on OpenStreetMap instead of a straight line, and every leg of a long mission can be planned and checked on a map before the rover moves. The front camera can steer it around obstacles in the way.

The [Earth Rover Challenge](https://earth-rover-challenge.github.io/) uses this mission format: AI teams and human gamers drive the same sidewalk rovers in real cities over the internet. Its urban and marathon tracks are GPS-checkpoint missions; the marathon runs about 50 miles from UC Berkeley to Stanford. It is also BitRobot's [Earth Rover Grand Challenge](https://bitrobot.ai/grand-challenges/earth-rovers).

Made by **MV2 of Munim, Inc.** The code was written with AI agents.

**Status (v0.4.0):** tested only against the built-in simulator, synthetic maps and synthetic camera images. It has not driven a real rover or seen a real camera frame yet. Treat the defaults as a starting point and tune them on the first real runs.

## Why not the plain example

The SDK ships a simple waypoint example. On a real rover, a bearing-follower like that runs into these problems, and this pilot handles each one:

| Problem | What the pilot does |
|---|---|
| With no fix, the rover reports latitude/longitude `1000`. Bad parsing turns missing values into 0/0. | `GpsFilter` drops no-fix, 0/0, NaN and impossible jumps. It smooths the remaining fixes and stops the rover if no fix has arrived for 3 s. |
| The compass is offset by the motors, the mount and local magnetic fields. | `HeadingEstimator` learns the bias as the rover drives. On straight stretches it fits a line through the GPS fixes and compares that course with the mean compass reading, then corrects the offset gradually. If the compass drops out, it falls back to the last GPS course. |
| A checkpoint a few hundred metres away is behind buildings, fences or water. | With `--osm` or `--fetch-osm`, each leg is planned on OpenStreetMap footways, paths and sidewalks (`route_planner.py`), and `PathFollower` steers along it (pure pursuit, 8 m lookahead). If the rover strays more than 30 m it replans. |
| A marathon has dozens of legs; finding a leg with no walkable route halfway through costs the run. | `--check-route` plans every remaining leg from where the rover stands, without driving, and reports each leg's straight-line and routed length (see below). |
| A bin, a planter or a parked scooter sits on the line the rover is driving. | With `--vision`, `free_space.py` reads the front camera 5 times a second, works out how far the rover could drive in each direction, and bends the heading to the nearest clear one (see below). |
| GPS noise is about the size of a 2 m arrival radius, so the rover never "arrives". | Checkpoints are reported from 10 m, inside the server's 15 m tolerance. A refused report is retried every 2 s. Inside 3 m the rover holds still instead of circling. |
| The SDK confirms the last checkpoint only after a confirmed stop, and may hold that request for up to 12 s. | Before the final report the pilot sends stop commands for 1.5 s. It waits up to 20 s for the answer. If none arrives, it reads `/checkpoints-list` to see whether the report counted before trying again. |
| Commands arrive about 500 ms late. | Low steering gain (full turn rate needs a 60° error) and turn-in-place above 60°. |
| A kerb or wall blocks the rover. | If it's commanded forward but moves less than 1.5 m in 10 s, it backs up, turns (alternating sides) and drives on. |
| The pilot or its connection drops in the middle of a mission. | `--no-start` resumes it: the pilot skips `/start-mission` and drives on from the server's latest reached checkpoint. |

## Run it

Standard library only, Python 3.8 or later. `--vision` on a real rover also needs Pillow (`pip install pillow`) to decode the camera's JPEG frames.

Simulator (no rover needed): the built-in demo mission has 4 checkpoints over about 220 m, with 0.5 s command latency, 1.5 m GPS noise, 5% GPS dropouts and a compass that reads 25° low:

```
python rover_pilot.py --simulate --seed 1
```

Add two 2 m-wide hedges on the route, and let the camera steer around them:

```
python rover_pilot.py --simulate --obstacles --vision
```

Without `--vision` the rover drives into the hedges and has to back out. The result shows `sim_contacts`, the number of 0.1 s steps a hedge held the rover back.

Real rover: start the SDK server first, following its README, with `SDK_API_TOKEN`, `BOT_SLUG` and `MISSION_SLUG` set. The pilot sends a command 10 times a second, so a short dead-man timeout is safe: the SDK suggests `CONTROL_WATCHDOG_S` of 0.5–1 for streaming clients, and 1 is a good choice here. The rover then stops within a second if the pilot hangs or loses its connection, for example while a checkpoint report is waiting for an answer. Then:

```
python rover_pilot.py --sdk http://localhost:8000 --log run.jsonl
```

Options:
- `--cruise 0.6`: forward command, 0 to 1. The SDK suggests 0.3–0.5 for first tests.
- `--report-radius 10`
- `--osm area.json`: plan each leg on a saved map area (see below).
- `--fetch-osm`: fetch the map around each leg from Overpass as needed.
- `--check-route`, `--route-out legs.geojson`: plan every remaining leg and report it, without driving (see below).
- `--vision`: steer around obstacles seen by the front camera.
- `--camera-fov 90`, `--camera-height 0.35`, `--camera-pitch 5`: the front camera's horizontal field of view (degrees), height above the ground (metres) and downward tilt (degrees). These are guesses; measure them on the rover.
- `--timeout 3600`
- `--no-start`: resume a mission that has already started.

Ctrl-C sends a stop. The log (`--log`) records one JSON line per second, plus each checkpoint, refusal, plan and recovery, so a run can be checked afterwards. With `--vision`, each line also has `clear_m`, how far ahead the camera saw clear ground.

### Leg summaries

The result printed at the end has a `legs` list, and the log has one `checkpoint` line per leg, with:
- `seq`: the checkpoint the leg ended at
- `elapsed_s`: time from the previous checkpoint (or the start) to this one
- `straight_m`: straight-line distance to the checkpoint when the leg began
- `reports`: how many `/checkpoint-reached` calls it took (1 means the first one counted)
- `recoveries`: how many back-up-and-turn moves the leg needed

On a long mission these show which legs were slow or hard, so the next run can be tuned for them.

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

## Front camera (`free_space.py`)

Each frame from `GET /v2/front` is shrunk to 64 × 36 pixels.

1. **Ground colour.** The band just in front of the rover (bottom 3 rows, middle 40%) gives the colour of the surface being driven on. Brightness may vary by a wide margin, so shadows still count as ground. A surface that keeps looking different for 3 s (say, from pavement onto a gravel path) becomes the new ground.
2. **Free space.** Every column is followed up from the bottom while it still looks like ground. With the camera's height and tilt, the row where it stops becomes a point on the ground, in metres to the right and ahead.
3. **Corridors.** For directions every 5° across the view, it measures how far a 0.8 m-wide corridor runs before it meets one of those points.
4. **Decision.** If the corridor toward the pilot's target is clear for 5 m (or up to the checkpoint, if that is nearer), nothing changes. Otherwise the pilot steers along the clear direction closest to the target. It keeps to the same side for 2 s, so it doesn't swing between the two sides of an obstacle. It slows down if even the best direction is short. When nothing is clear for 1.2 m, it turns in place toward the more open side for 1.5 s.

If no frame arrives for a second, the pilot drives on at half speed. Camera errors never stop the pilot.

What it can't do: it sees colour, not depth. An obstacle the same colour as the ground (a grey wall on grey pavement) is missed. A change of surface it hasn't learned yet (grass beside the path, a painted line, a hard shadow) can read as an obstacle. It has no memory, so something it has driven past and can no longer see doesn't count. It is a cheap first layer. A learned free-space model trained on the FrodoBots datasets could replace it later behind the same `advise()` call.

## Route planning

`route_planner.py` fetches the ways a pedestrian may use in a bounding box from the [Overpass API](https://wiki.openstreetmap.org/wiki/Overpass_API). It builds a graph and finds the cheapest route with A*.

- Footways, paths and pedestrian streets cost 1 per metre.
- Roads cost more (1.3 for residential up to 2.0 for primary). A road tagged with a sidewalk costs 1.1. A road tagged `sidewalk=no` costs double.
- Steps, motorways, trunk roads and ways closed to pedestrians are left out.

Fetch an area once, check the route on a map, then drive with the saved file:

```
python route_planner.py fetch 37.85,-122.28,37.88,-122.25 -o berkeley.json
python route_planner.py route berkeley.json 37.8719,-122.2585 37.8700,-122.2650 -o route.geojson
python rover_pilot.py --osm berkeley.json --vision --log run.jsonl
```

Open `route.geojson` in any GeoJSON viewer to see the route before the rover drives it. Please keep Overpass use light: one fetch per area, then reuse the file.

Map data © [OpenStreetMap contributors](https://www.openstreetmap.org/copyright), available under the ODbL. This repository contains no map data; it is fetched when you run the planner.

## Assumptions to check on the first real run

- `orientation` in `/data` is a compass heading in degrees, clockwise from north. This is how the SDK dashboard draws it; the SDK README gives no convention. A constant offset is learned and corrected; a different convention is not.
- A positive `angular` command turns right.
- The server judges a checkpoint against the rover's own latest GPS reading.
- `/checkpoints-list` returns the mission's checkpoints before the first `/start-mission`, so `--check-route` can run before the clock starts. If it returns none, the check has to run after the start, or from a copy of the checkpoints.
- The front camera's field of view, height and tilt (`--camera-*`). A wrong tilt makes obstacles look nearer or farther than they are. To check it, put an object at a known distance and compare `clear_m` in the log.
- OSM sidewalks are mapped well enough in the mission's area. Where they aren't, roads stand in for them.

## Not done yet

- The camera layer has only seen rendered images. The next step is to check it on recorded frames from the FrodoBots-2K dataset and on a real rover.
- Indoor and off-road tracks use image goals, not GPS. This pilot covers only GPS checkpoint missions.
- The gains are tuned on the simulator's motion model (1.2 m/s, 60°/s at full command), not on a real rover.

## Tests

```
python -m unittest test_rover_pilot test_route_planner test_free_space -v
```

The tests cover:
- geometry and the GPS filter
- compass-bias learning
- the steering law and path following
- the HTTP client, with a mocked SDK, including slow and unanswered checkpoint reports and camera frames
- full simulated missions on several seeds, including heavy GPS dropouts, a rover stuck for its first 30 s, a planned dogleg route and a planner that fails
- leg summaries, and resuming a mission whose first two checkpoints the server already counts
- the route check: each remaining leg measured from the rover's position, legs with no route, a planner error on one leg, no GPS fix, the GeoJSON output, and the command line on a synthetic map with nothing driven
- the camera model, ground-colour matching, corridors, and the guard's choices: leave the heading alone, steer to the nearer side, stop and turn at a wall, slow down with no frames, learn a new surface
- closed loop in the simulator: with a 2 m hedge on the straight line to the checkpoint, the rover without vision drives into it, and with vision it goes around without touching it (two seeds)
- the route planner on synthetic maps: detours, footways versus busy roads, sidewalks, disconnected networks, ways cut at the edge of the fetched area, and the command line

## License

MIT. Not affiliated with FrodoBots, BitRobot or the Earth Rover Challenge organisers.
