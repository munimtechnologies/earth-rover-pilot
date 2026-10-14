#!/usr/bin/env python3
"""route_planner: walkable routes on OpenStreetMap for the Earth Rover pilot.

A sidewalk rover that heads straight for a checkpoint a few hundred metres
away drives into buildings, fences and water. This module fetches the ways a
pedestrian may use (footways, paths, pedestrian streets and, at a higher cost,
roads, whose sidewalks the rover keeps to) from the Overpass API, builds a
graph and finds the cheapest route with A*.

    python route_planner.py fetch S,W,N,E -o area.json
    python route_planner.py route area.json LAT,LON LAT,LON [LAT,LON ...] -o route.geojson

The GeoJSON can be checked on any map viewer before a run. Map data from
OpenStreetMap (c) OpenStreetMap contributors, ODbL. Please keep Overpass use
light: fetch an area once, save it and reuse the file.

Standard library only. By MV2 of Munim, Inc.; written with AI agents.
"""

from __future__ import annotations

import argparse
import heapq
import json
import math
import sys
import urllib.parse
import urllib.request

from rover_pilot import M_PER_DEG, __version__, haversine_m

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
USER_AGENT = ("earth-rover-pilot/%s (MV2 of Munim, Inc.; "
              "https://github.com/munimtechnologies/earth-rover-pilot)" % __version__)

# Cost per metre by highway type. Ways built for walking are cheapest; roads
# are allowed (the rover keeps to their sidewalk) but cost more. Steps,
# motorways and trunk roads are left out: the rover can't use them.
WAY_COST = {
    "footway": 1.0, "pedestrian": 1.0, "path": 1.0, "cycleway": 1.1,
    "living_street": 1.1, "residential": 1.3, "service": 1.4, "track": 1.5,
    "unclassified": 1.5, "tertiary": 1.6, "tertiary_link": 1.8,
    "secondary": 1.8, "secondary_link": 2.0, "primary": 2.0, "primary_link": 2.2,
}
WALKWAYS = {"footway", "pedestrian", "path", "cycleway", "living_street"}
SIDEWALK_COST = 1.1  # a road mapped with a sidewalk is nearly as good as a footway
NO_SIDEWALK_FACTOR = 2.0
FOOT_OK = {"yes", "designated", "permissive"}
FOOT_NO = {"no", "private", "use_sidepath"}


def way_cost(tags):
    """Cost per metre of a way for a sidewalk rover, or None if it may not use it."""
    hw = tags.get("highway")
    if hw not in WAY_COST:
        return None
    foot = tags.get("foot")
    if foot in FOOT_NO:
        return None
    if tags.get("access") in ("no", "private") and foot not in FOOT_OK:
        return None
    cost = WAY_COST[hw]
    if hw not in WALKWAYS:
        sidewalk = tags.get("sidewalk") or tags.get("sidewalk:both")
        if sidewalk in ("both", "left", "right", "yes"):
            cost = min(cost, SIDEWALK_COST)
        elif sidewalk == "no":
            cost *= NO_SIDEWALK_FACTOR
    return cost


def overpass_query(south, west, north, east, timeout_s=120):
    types = "|".join(sorted(WAY_COST))
    return ('[out:json][timeout:%d];way["highway"~"^(%s)$"](%.6f,%.6f,%.6f,%.6f);out geom;'
            % (timeout_s, types, south, west, north, east))


def fetch_osm(south, west, north, east, url=OVERPASS_URL, timeout_s=180):
    """Overpass JSON of the usable ways in a bounding box."""
    data = urllib.parse.urlencode({"data": overpass_query(south, west, north, east)})
    req = urllib.request.Request(url, data=data.encode("utf-8"),
                                 headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:
        return json.loads(resp.read().decode("utf-8"))


def bbox_around(points, pad_m=300.0):
    """(south, west, north, east) around `points`, padded by pad_m metres."""
    lats = [p[0] for p in points]
    lons = [p[1] for p in points]
    mid = math.radians(sum(lats) / len(lats))
    dlat = pad_m / M_PER_DEG
    dlon = pad_m / (M_PER_DEG * max(0.01, math.cos(mid)))
    return (min(lats) - dlat, min(lons) - dlon, max(lats) + dlat, max(lons) + dlon)


class Graph:
    """Walkable ways as a graph: node id -> (lat, lon), node id -> [(node, cost, metres)]."""

    def __init__(self, coords, adj, cell_deg=0.002):
        self.coords = coords
        self.adj = adj
        self.cell = cell_deg
        self._grid = {}
        for nid in adj:
            lat, lon = coords[nid]
            self._grid.setdefault(self._key(lat, lon), []).append(nid)

    def _key(self, lat, lon):
        return int(math.floor(lat / self.cell)), int(math.floor(lon / self.cell))

    def bbox(self):
        if not self.adj:
            return None
        return bbox_around([self.coords[n] for n in self.adj], 0.0)

    def nearest(self, lat, lon, max_m=250.0):
        """The routable node nearest to (lat, lon) within max_m metres, or None."""
        ki, kj = self._key(lat, lon)
        ri = int(max_m / (M_PER_DEG * self.cell)) + 1
        rj = int(max_m / (M_PER_DEG * max(0.01, math.cos(math.radians(lat))) * self.cell)) + 1
        best, best_d = None, max_m
        for i in range(ki - ri, ki + ri + 1):
            for j in range(kj - rj, kj + rj + 1):
                for nid in self._grid.get((i, j), ()):
                    d = haversine_m(lat, lon, *self.coords[nid])
                    if d <= best_d:
                        best, best_d = nid, d
        return best

    def route(self, lat0, lon0, lat1, lon1, max_snap_m=250.0):
        """Cheapest walkable path as [(lat, lon), ...] from start to goal, or None."""
        a = self.nearest(lat0, lon0, max_snap_m)
        b = self.nearest(lat1, lon1, max_snap_m)
        if a is None or b is None:
            return None
        goal = self.coords[b]
        best = {a: 0.0}
        came = {}
        heap = [(haversine_m(*self.coords[a], *goal), 0.0, a)]
        while heap:
            _, g, n = heapq.heappop(heap)
            if n == b:
                break
            if g > best.get(n, math.inf):
                continue
            for m, cost, _ in self.adj.get(n, ()):
                ng = g + cost
                if ng < best.get(m, math.inf):
                    best[m] = ng
                    came[m] = n
                    # costs are at least 1 per metre, so straight-line metres never overestimate
                    heapq.heappush(heap, (ng + haversine_m(*self.coords[m], *goal), ng, m))
        else:
            return None
        nodes = [b]
        while nodes[-1] != a:
            nodes.append(came[nodes[-1]])
        nodes.reverse()
        return [(lat0, lon0)] + [self.coords[n] for n in nodes] + [(lat1, lon1)]


def build_graph(osm):
    """Graph from Overpass JSON (`out geom`)."""
    coords, adj = {}, {}
    for el in osm.get("elements") or []:
        if el.get("type") != "way":
            continue
        cost = way_cost(el.get("tags") or {})
        if cost is None:
            continue
        ids, geom = el.get("nodes") or [], el.get("geometry") or []
        if len(ids) != len(geom):
            continue
        prev = None
        for nid, g in zip(ids, geom):
            try:
                pt = (float(g["lat"]), float(g["lon"]))
            except (TypeError, KeyError, ValueError):
                prev = None  # a node outside the fetched area: the way is cut here
                continue
            coords[nid] = pt
            if prev is not None and prev != nid:
                metres = haversine_m(coords[prev][0], coords[prev][1], pt[0], pt[1])
                adj.setdefault(prev, []).append((nid, metres * cost, metres))
                adj.setdefault(nid, []).append((prev, metres * cost, metres))
            prev = nid
    return Graph(coords, adj)


def path_length_m(points):
    return sum(haversine_m(a[0], a[1], b[0], b[1]) for a, b in zip(points, points[1:]))


class OsmPlanner:
    """A planner for Pilot: (lat, lon, goal_lat, goal_lon) -> path points or None.

    Uses a saved Overpass JSON, and/or fetches the area around each leg when
    `fetch` is set and the leg runs outside what is loaded.
    """

    def __init__(self, osm=None, fetch=False, pad_m=300.0, fetcher=None):
        self.fetch = fetch
        self.pad_m = pad_m
        self.fetcher = fetcher or fetch_osm
        self.graph = None
        self.box = None
        if osm is not None:
            self.graph = build_graph(osm)
            self.box = self.graph.bbox()

    def _covers(self, lat, lon):
        if self.box is None:
            return False
        south, west, north, east = self.box
        return south <= lat <= north and west <= lon <= east

    def __call__(self, lat0, lon0, lat1, lon1):
        if self.fetch and not (self._covers(lat0, lon0) and self._covers(lat1, lon1)):
            box = bbox_around([(lat0, lon0), (lat1, lon1)], self.pad_m)
            self.graph = build_graph(self.fetcher(*box))
            self.box = box
        if self.graph is None:
            return None
        return self.graph.route(lat0, lon0, lat1, lon1)


def plan_legs(planner, start, checkpoints):
    """Plan every leg of a mission before driving it.

    `planner` is called the way Pilot calls it; `checkpoints` are (sequence,
    lat, lon) in driving order and the first leg starts at `start`. Returns
    one dict per leg: its sequence, the straight-line and routed length in
    metres, the detour factor and the route's points. route_m is None where
    no walkable route was found (the pilot would head straight there).
    """
    legs = []
    lat0, lon0 = start
    for seq, lat1, lon1 in checkpoints:
        leg = {"seq": seq, "straight_m": round(haversine_m(lat0, lon0, lat1, lon1), 1),
               "route_m": None, "detour": None, "points": None}
        try:
            points = planner(lat0, lon0, lat1, lon1)
        except Exception as e:  # note it and go on checking the rest of the mission
            points = None
            leg["error"] = str(e)
        if points and len(points) >= 2:
            length = path_length_m(points)
            leg["route_m"] = round(length, 1)
            leg["points"] = points
            if leg["straight_m"] >= 1.0:
                leg["detour"] = round(length / leg["straight_m"], 2)
        legs.append(leg)
        lat0, lon0 = lat1, lon1
    return legs


def to_geojson(points, **properties):
    return {"type": "FeatureCollection", "features": [{
        "type": "Feature", "properties": properties,
        "geometry": {"type": "LineString",
                     "coordinates": [[round(lon, 7), round(lat, 7)] for lat, lon in points]}}]}


def legs_geojson(legs):
    """One LineString per routed leg from plan_legs, to check a whole mission on a map."""
    features = []
    for leg in legs:
        if not leg.get("points"):
            continue
        props = {k: v for k, v in leg.items() if k != "points"}
        features.extend(to_geojson(leg["points"], **props)["features"])
    return {"type": "FeatureCollection", "features": features}


def _latlon(text):
    lat, lon = (float(x) for x in text.split(","))
    return lat, lon


def main(argv=None):
    p = argparse.ArgumentParser(description="Walkable OpenStreetMap routes for the Earth Rover pilot.")
    sub = p.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("fetch", help="save the usable ways in a bounding box from Overpass")
    f.add_argument("bbox", help="south,west,north,east in degrees")
    f.add_argument("-o", "--out", required=True, help="where to save the Overpass JSON")
    r = sub.add_parser("route", help="route through points on a saved area; prints GeoJSON")
    r.add_argument("osm", help="Overpass JSON saved by `fetch`")
    r.add_argument("points", nargs="+", help="LAT,LON of the start, then each checkpoint")
    r.add_argument("-o", "--out", help="write the GeoJSON here instead of printing it")
    args = p.parse_args(argv)

    if args.cmd == "fetch":
        south, west, north, east = (float(x) for x in args.bbox.split(","))
        osm = fetch_osm(south, west, north, east)
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(osm, fh)
        print("saved %d ways to %s" % (len(osm.get("elements") or []), args.out))
        return 0

    with open(args.osm, encoding="utf-8") as fh:
        graph = build_graph(json.load(fh))
    stops = [_latlon(t) for t in args.points]
    if len(stops) < 2:
        p.error("give at least a start and one checkpoint")
    path = [stops[0]]
    for (lat0, lon0), (lat1, lon1) in zip(stops, stops[1:]):
        leg = graph.route(lat0, lon0, lat1, lon1)
        if leg is None:
            print("no walkable route from %.6f,%.6f to %.6f,%.6f" % (lat0, lon0, lat1, lon1),
                  file=sys.stderr)
            return 1
        path.extend(leg[1:])
    text = json.dumps(to_geojson(path, length_m=round(path_length_m(path), 1)))
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text)
        print("route of %.0f m written to %s" % (path_length_m(path), args.out))
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
