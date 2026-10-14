"""Offline tests for route_planner (standard library only; no network).

Run: python -m unittest test_route_planner -v
"""

import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import rover_pilot as rp  # noqa: E402
import route_planner as planner  # noqa: E402

LAT, LON = 37.8719, -122.2585


def pt(north, east):
    return rp.offset_latlon(LAT, LON, north, east)


def way(wid, nodes, **tags):
    """An Overpass `out geom` way through nodes given as (id, north_m, east_m)."""
    return {"type": "way", "id": wid, "nodes": [n[0] for n in nodes],
            "geometry": [dict(zip(("lat", "lon"), pt(n[1], n[2]))) for n in nodes],
            "tags": tags}


A, B = (1, 0.0, 0.0), (4, 0.0, 100.0)

# Two corners 80 m north of A and B; nothing runs straight from A to B.
DETOUR = {"elements": [
    way(10, [A, (2, 80.0, 0.0)], highway="footway"),
    way(11, [(2, 80.0, 0.0), (3, 80.0, 100.0)], highway="footway"),
    way(12, [(3, 80.0, 100.0), B], highway="footway"),
]}


def near(points, north, east, within_m=1.0):
    target = pt(north, east)
    return any(rp.haversine_m(*p, *target) < within_m for p in points)


class WayCostTests(unittest.TestCase):
    def test_what_the_rover_may_use(self):
        self.assertEqual(planner.way_cost({"highway": "footway"}), 1.0)
        self.assertIsNone(planner.way_cost({"highway": "steps"}))
        self.assertIsNone(planner.way_cost({"highway": "motorway"}))
        self.assertIsNone(planner.way_cost({"highway": "footway", "foot": "no"}))
        self.assertIsNone(planner.way_cost({"highway": "primary", "foot": "use_sidepath"}))
        self.assertIsNone(planner.way_cost({"highway": "service", "access": "private"}))
        self.assertEqual(planner.way_cost({"highway": "footway", "access": "private",
                                           "foot": "yes"}), 1.0)
        self.assertIsNone(planner.way_cost({"building": "yes"}))

    def test_sidewalks_change_road_cost(self):
        plain = planner.way_cost({"highway": "residential"})
        self.assertAlmostEqual(plain, 1.3)
        self.assertAlmostEqual(planner.way_cost({"highway": "residential", "sidewalk": "both"}),
                               planner.SIDEWALK_COST)
        self.assertAlmostEqual(planner.way_cost({"highway": "residential", "sidewalk": "no"}),
                               plain * planner.NO_SIDEWALK_FACTOR)
        # a footway is a footway, whatever its sidewalk tag says
        self.assertEqual(planner.way_cost({"highway": "footway", "sidewalk": "no"}), 1.0)

    def test_query_asks_only_for_usable_ways(self):
        q = planner.overpass_query(37.0, -122.5, 37.1, -122.4)
        self.assertIn("footway", q)
        self.assertNotIn("steps", q)
        self.assertNotIn("motorway", q)
        self.assertIn("(37.000000,-122.500000,37.100000,-122.400000)", q)
        self.assertTrue(q.startswith("[out:json]"))
        self.assertTrue(q.endswith("out geom;"))


class RouteTests(unittest.TestCase):
    def test_goes_around_when_there_is_no_straight_way(self):
        g = planner.build_graph(DETOUR)
        path = g.route(*pt(0, 0), *pt(0, 100))
        self.assertIsNotNone(path)
        self.assertAlmostEqual(planner.path_length_m(path), 260.0, delta=1.0)
        self.assertTrue(near(path, 80, 0) and near(path, 80, 100))

    def test_snaps_start_and_goal_to_the_network(self):
        g = planner.build_graph(DETOUR)
        start, goal = pt(5, -10), pt(-6, 108)
        path = g.route(*start, *goal)
        self.assertEqual(path[0], start)
        self.assertEqual(path[-1], goal)
        self.assertTrue(near(path, 0, 0))

    def test_prefers_a_footway_to_a_busy_road(self):
        osm = {"elements": [
            way(20, [A, B], highway="primary"),
            way(21, [A, (5, 30.0, 50.0), B], highway="footway"),
        ]}
        path = planner.build_graph(osm).route(*pt(0, 0), *pt(0, 100))
        self.assertTrue(near(path, 30, 50))

    def test_takes_the_road_when_it_has_a_sidewalk(self):
        osm = {"elements": [
            way(20, [A, B], highway="primary", sidewalk="both"),
            way(21, [A, (5, 30.0, 50.0), B], highway="footway"),
        ]}
        path = planner.build_graph(osm).route(*pt(0, 0), *pt(0, 100))
        self.assertFalse(near(path, 30, 50, within_m=5.0))
        self.assertAlmostEqual(planner.path_length_m(path), 100.0, delta=1.0)

    def test_no_route_between_separate_networks(self):
        osm = {"elements": [
            way(30, [A, (2, 0.0, 20.0)], highway="footway"),
            way(31, [(3, 0.0, 80.0), B], highway="footway"),
        ]}
        self.assertIsNone(planner.build_graph(osm).route(*pt(0, 0), *pt(0, 100)))

    def test_nothing_nearby(self):
        g = planner.build_graph(DETOUR)
        self.assertIsNone(g.route(*pt(0, 0), *pt(0, 2000)))

    def test_way_is_cut_where_geometry_is_missing(self):
        w = way(40, [A, (2, 0.0, 50.0), B], highway="footway")
        w["geometry"][1] = None
        g = planner.build_graph({"elements": [w]})
        self.assertEqual(g.adj, {})
        self.assertIsNone(g.route(*pt(0, 0), *pt(0, 100)))


class OsmPlannerTests(unittest.TestCase):
    def test_fetches_once_per_area(self):
        boxes = []

        def fetcher(south, west, north, east):
            boxes.append((south, west, north, east))
            return DETOUR

        plan = planner.OsmPlanner(fetch=True, fetcher=fetcher)
        path = plan(*pt(0, 0), *pt(0, 100))
        self.assertAlmostEqual(planner.path_length_m(path), 260.0, delta=1.0)
        south, west, north, east = boxes[0]
        self.assertTrue(south < LAT < north and west < LON < east)
        plan(*pt(80, 0), *pt(0, 100))
        self.assertEqual(len(boxes), 1)

    def test_saved_area_without_fetching(self):
        plan = planner.OsmPlanner(osm=DETOUR)
        self.assertIsNotNone(plan(*pt(0, 0), *pt(0, 100)))
        self.assertIsNone(planner.OsmPlanner()(*pt(0, 0), *pt(0, 100)))


class CliTests(unittest.TestCase):
    def test_route_command_writes_geojson(self):
        with tempfile.TemporaryDirectory() as d:
            osm_path = os.path.join(d, "area.json")
            out_path = os.path.join(d, "route.geojson")
            with open(osm_path, "w", encoding="utf-8") as f:
                json.dump(DETOUR, f)
            args = ["route", osm_path, "%.7f,%.7f" % pt(0, 0), "%.7f,%.7f" % pt(0, 100),
                    "-o", out_path]
            with redirect_stdout(io.StringIO()):
                self.assertEqual(planner.main(args), 0)
            with open(out_path, encoding="utf-8") as f:
                gj = json.load(f)
        feature = gj["features"][0]
        self.assertEqual(feature["geometry"]["type"], "LineString")
        self.assertAlmostEqual(feature["properties"]["length_m"], 260.0, delta=1.0)
        lon, lat = feature["geometry"]["coordinates"][0]
        self.assertAlmostEqual(lat, LAT, places=5)


if __name__ == "__main__":
    unittest.main()
