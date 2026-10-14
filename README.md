# earth-rover-pilot

A GPS waypoint pilot for the [FrodoBots Earth Rover SDK](https://github.com/frodobots-org/earth-rovers-sdk). It drives an Earth Rover through the checkpoints of an SDK mission and reports each one with `/checkpoint-reached`. Each leg can follow a walkable route planned on OpenStreetMap instead of a straight line.

The [Earth Rover Challenge](https://earth-rover-challenge.github.io/) uses this mission format: AI teams and human gamers drive the same sidewalk rovers in real cities over the internet. Its urban and marathon tracks are GPS-checkpoint missions; the marathon runs about 50 miles from UC Berkeley to Stanford. It is also BitRobot's [Earth Rover Grand Challenge](https://bitrobot.ai/grand-challenges/earth-rovers).

Made by **MV2 of Munim, Inc.** The code was written with AI agents.

**Status (v0.2.0):** tested only against the built-in simulator and synthetic maps. It has not driven a real rover yet. Treat the defaults as a starting point and tune them on the first real runs.

## Why not the plain example

The SDK ships a simple waypoint example. On a real rover, a bearing-follower like that runs into these problems, and this pilot handles each one:

| Problem | What the pilot does |
|---|---|
| With no fix, the rover reports latitude/longitude `1000`. Bad parsing turns missing values into 0/0. | `GpsFilter` drops no-fix, 0/0, NaN and impossible jumps. It smooths the remaining fixes and stops the rover if no fix has arrived for 3 s. |
| The compass is offset by the motors, the mount and local magnetic fields. | `HeadingEstimator` learns the bias as the rover drives. On straight stretches it fits a line through the GPS fixes and compares that course with the mean compass reading, then corrects the offset gradually. If the compass drops out, it falls back to the last GPS course. |
| A checkpoint a few hundred metres away is behind buildings, fences or water. | With `--osm` or `--fetch-osm`, each leg is planned on OpenStreetMap footways, paths and sidewalks (`route_planner.py`), and `PathFollower` steers along it (pure pursuit, 8 m lookahead). If the rover strays more than 30 m it replans. |
| GPS noise is about the size of a 2 m arrival radius, so the rover never "arrives". | Checkpoints are reported from 10 m, inside the server's 15 m tolerance. A refused report is retried every 2 s. Inside 3 m the rover holds still instead of circling. |
| The SDK confirms the last checkpoint only after a confirmed stop, and may hold that request for up to 12 s. | Before the final report the pilot sends stop commands for 1.5 s. It waits up to 20 s for the answer. If none arrives, it reads `/checkpoints-list` to see whether the report counted before trying again. |
| Commands arrive about 500 ms late. | Low steering gain (full turn rate needs a 60° error) and turn-in-place above 60°. |
| A kerb or wall blocks the rover. | If it's commanded forward but moves less than 1.5 m in 10 s, it backs up, turns (alternating sides) and drives on. |

## Run it

Standard library only, Python 3.8 or later.

Simulator (no rover needed): the built-in demo mission has 4 checkpoints over about 220 m, with 0.5 s command latency, 1.5 m GPS noise, 5% GPS dropouts and a compass that reads 25° low:

```
python rover_pilot.py --simulate --seed 1
```

Real rover: start the SDK server first, following its README, with `SDK_API_TOKEN`, `BOT_SLUG` and `MISSION_SLUG` set. Then:

```
python rover_pilot.py --sdk http://localhost:8000 --log run.jsonl
```

Options:
- `--cruise 0.6`: forward command, 0 to 1. The SDK suggests 0.3–0.5 for first tests.
- `--report-radius 10`
- `--osm area.json`: plan each leg on a saved map area (see below).
- `--fetch-osm`: fetch the map around each leg from Overpass as needed.
- `--timeout 3600`
- `--no-start`: resume a mission that has already started.

Ctrl-C sends a stop. The SDK also has a dead-man stop if commands stop arriving. The log (`--log`) records one JSON line per second, plus each checkpoint, refusal, plan and recovery, so a run can be checked afterwards.

## Route planning

`route_planner.py` fetches the ways a pedestrian may use in a bounding box from the [Overpass API](https://wiki.openstreetmap.org/wiki/Overpass_API). It builds a graph and finds the cheapest route with A*.

- Footways, paths and pedestrian streets cost 1 per metre.
- Roads cost more (1.3 for residential up to 2.0 for primary). A road tagged with a sidewalk costs 1.1. A road tagged `sidewalk=no` costs double.
- Steps, motorways, trunk roads and ways closed to pedestrians are left out.

Fetch an area once, check the route on a map, then drive with the saved file:

```
python route_planner.py fetch 37.85,-122.28,37.88,-122.25 -o berkeley.json
python route_planner.py route berkeley.json 37.8719,-122.2585 37.8700,-122.2650 -o route.geojson
python rover_pilot.py --osm berkeley.json --log run.jsonl
```

Open `route.geojson` in any GeoJSON viewer to see the route before the rover drives it. Please keep Overpass use light: one fetch per area, then reuse the file.

Map data © [OpenStreetMap contributors](https://www.openstreetmap.org/copyright), available under the ODbL. This repository contains no map data; it is fetched when you run the planner.

## Assumptions to check on the first real run

- `orientation` in `/data` is a compass heading in degrees, clockwise from north. This is how the SDK dashboard draws it; the SDK README gives no convention. A constant offset is learned and corrected; a different convention is not.
- A positive `angular` command turns right.
- The server judges a checkpoint against the rover's own latest GPS reading.
- OSM sidewalks are mapped well enough in the mission's area. Where they aren't, roads stand in for them, and the rover has to keep to the sidewalk by sight. It can't do that yet.

## Not done yet

- **No camera use.** The pilot steers from GPS, the compass and the map only, so it doesn't see obstacles, kerbs or crossings. The back-up-and-turn move is a fallback, not avoidance. The next step is a vision layer on the front camera (`/v2/front`) that vetoes and bends the planned heading.
- Indoor and off-road tracks use image goals, not GPS. This pilot covers only GPS checkpoint missions.
- The gains are tuned on the simulator's motion model (1.2 m/s, 60°/s at full command), not on a real rover.

## Tests

```
python -m unittest test_rover_pilot test_route_planner -v
```

The tests cover:
- geometry and the GPS filter
- compass-bias learning
- the steering law and path following
- the HTTP client, with a mocked SDK, including slow and unanswered checkpoint reports
- full simulated missions on several seeds, including heavy GPS dropouts, a rover stuck for its first 30 s, a planned dogleg route and a planner that fails
- the route planner on synthetic maps: detours, footways versus busy roads, sidewalks, disconnected networks, ways cut at the edge of the fetched area, and the command line

## License

MIT. Not affiliated with FrodoBots, BitRobot or the Earth Rover Challenge organisers.
