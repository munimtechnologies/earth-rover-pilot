"""Tests for the marathon pace study.

Run: python -m unittest test_pace_study -v
"""

import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pace_study as ps  # noqa: E402
import rover_pilot as rp  # noqa: E402


def run(profile, variant, cruise, course, seed, elapsed, made_good, ok=True):
    return {"ok": ok, "reason": "mission completed" if ok else "timeout",
            "elapsed_s": elapsed, "reached": 4, "checkpoints": 4, "reports": 4,
            "recoveries": 0, "plans": 4, "route_m": 1000.0, "travelled_m": 1100.0,
            "made_good_mps": made_good, "ideal_mps": 1.0, "efficiency": made_good,
            "time_s": {"driving": elapsed * 0.9, "turning": elapsed * 0.1, "stopped": 0.0,
                       "reversing": 0.0},
            "profile": profile, "variant": variant, "cruise": cruise, "course": course,
            "seed": seed}


class FakeRover:
    def __init__(self):
        self.report = {"timestamp": 1, "orientation": 10.0}
        self.sent = []

    def data(self):
        return dict(self.report)

    def control(self, linear, angular):
        self.sent.append((linear, angular))

    def checkpoints(self):
        return [], 0


class PaceTests(unittest.TestCase):
    def test_human_pace(self):
        # 50 miles in 29 h 38 min.
        self.assertAlmostEqual(ps.MARATHON_M, 80467.2, places=6)
        self.assertEqual(ps.HUMAN_S, 106680)
        self.assertAlmostEqual(ps.HUMAN_MPS, 0.7543, places=4)

    def test_cruise_floor(self):
        # At 4 km/h and no losses at all, cruise 0.6 is not enough.
        self.assertAlmostEqual(ps.cruise_floor(ps.MINIPLUS_TOP_MPS), 0.679, places=3)
        self.assertGreater(ps.cruise_floor(ps.MINIPLUS_TOP_MPS), 0.6)
        self.assertAlmostEqual(ps.cruise_floor(ps.MINIPLUS_TOP_MPS, 0.8),
                               ps.cruise_floor(ps.MINIPLUS_TOP_MPS) / 0.8)


class CourseTests(unittest.TestCase):
    def test_lengths(self):
        blocks = ps.COURSES["blocks"]
        self.assertEqual(blocks["points"][3], (200.0, 100.0))
        self.assertEqual(blocks["points"][14], (700.0, 700.0))
        self.assertEqual(ps.route_m(blocks), 1400.0)
        self.assertEqual(ps.route_m(blocks, upto=1), 300.0)
        self.assertEqual(ps.route_m(blocks, upto=0), 0.0)
        bay = ps.COURSES["bayside"]["points"]
        self.assertEqual(len(bay), 61)
        self.assertEqual(bay[-1][0], 1200.0)
        for name, course in ps.COURSES.items():
            self.assertLess(course["checkpoints"][-1], len(course["points"]), name)
            self.assertTrue(1250.0 < ps.route_m(course) < 1600.0, name)

    def test_leg_points_start_and_middle(self):
        blocks = ps.COURSES["blocks"]
        self.assertEqual(ps.leg_points(blocks, 0, 0.0, 0.0),
                         [(0.0, 0.0), (100.0, 0.0), (100.0, 100.0), (200.0, 100.0)])
        self.assertEqual(ps.leg_points(blocks, 0, 100.0, 50.0),
                         [(100.0, 50.0), (100.0, 100.0), (200.0, 100.0)])
        # Leg 1 runs from point 3 to point 6.
        self.assertEqual(ps.leg_points(blocks, 1, 200.0, 100.0)[-1], (300.0, 300.0))

    def test_planner_round_trip(self):
        course = ps.COURSES["blocks"]
        sim = ps.StudyRover([course["points"][i] for i in course["checkpoints"]], seed=1)
        planner = ps.CoursePlanner(course, sim.lat0, sim.lon0)
        _, lat, lon = sim.checkpoints()[0][0]
        pts = planner(sim.lat0, sim.lon0, lat, lon)
        self.assertEqual(len(pts), 4)
        e, n = rp.to_enu(sim.lat0, sim.lon0, *pts[-1])
        self.assertAlmostEqual(n, 200.0, places=6)
        self.assertAlmostEqual(e, 100.0, places=6)
        # The second checkpoint is recognised as leg 1.
        _, lat2, lon2 = sim.checkpoints()[0][1]
        e, n = rp.to_enu(sim.lat0, sim.lon0, *planner(lat, lon, lat2, lon2)[-1])
        self.assertAlmostEqual(n, 300.0, places=6)
        self.assertAlmostEqual(e, 300.0, places=6)
        self.assertEqual(planner.calls, 2)


class RoverTests(unittest.TestCase):
    def test_time_accounting(self):
        sim = ps.StudyRover([(50.0, 0.0)], seed=1, **ps.PROFILES["mini+"])
        sim.control(0.0, 0.5)
        sim.sleep(2.0)
        t = sim.time_in
        self.assertAlmostEqual(sum(t.values()), 2.0, places=6)
        # The command lands 0.8 s after it was sent.
        self.assertTrue(0.7 < t["stopped"] < 1.0, t)
        self.assertTrue(1.0 < t["turning"] < 1.3, t)
        self.assertEqual(t["driving"], 0.0)
        self.assertEqual(t["reversing"], 0.0)

    def test_stale_orientation_holds_between_reports(self):
        sim = ps.StudyRover([(50.0, 0.0)], seed=1, **ps.PROFILES["mini+"])
        d0 = sim.data()
        sim.control(0.0, 1.0)
        sim.sleep(1.0)
        self.assertEqual(sim.data(), d0)
        sim.sleep(1.0)
        d2 = sim.data()
        self.assertNotEqual(d2["timestamp"], d0["timestamp"])
        self.assertNotEqual(d2["orientation"], d0["orientation"])

    def test_fresh_orientation_changes_every_poll(self):
        sim = ps.StudyRover([(50.0, 0.0)], seed=1, **ps.PROFILES["fresh"])
        self.assertFalse(sim.stale_orientation)
        self.assertNotEqual(sim.data()["orientation"], sim.data()["orientation"])


class PredictorTests(unittest.TestCase):
    def test_integrate(self):
        cmds = [(0.0, 1.0), (1.0, 0.0), (2.0, -0.5)]
        self.assertEqual(ps.integrate(cmds, 0.5, 2.5, 3.0), 0.25)
        self.assertEqual(ps.integrate(cmds, -5.0, -1.0, 3.0), 0.0)
        self.assertEqual(ps.integrate([], 0.0, 1.0, 1.0), 0.0)

    def test_turns_the_held_orientation(self):
        fake = FakeRover()
        clock = [0.0]
        hp = ps.HeadingPredictor(fake, lambda: clock[0], yaw_dps=30.0, lag_s=0.8)
        self.assertEqual(hp.data()["orientation"], 10.0)
        hp.control(0.0, 1.0)
        clock[0] = 2.0
        # Turning since 0.8 s: 1.2 s at 30 deg/s.
        self.assertAlmostEqual(hp.data()["orientation"], 46.0, places=6)
        # A new report starts again from its own reading, and wraps at 360.
        fake.report = {"timestamp": 2, "orientation": 350.0}
        clock[0] = 2.1
        self.assertEqual(hp.data()["orientation"], 350.0)
        clock[0] = 3.1
        self.assertAlmostEqual(hp.data()["orientation"], 20.0, places=6)
        fake.report = {"timestamp": 3, "orientation": None}
        self.assertIsNone(hp.data()["orientation"])
        self.assertEqual(fake.sent, [(0.0, 1.0)])
        self.assertEqual(hp.checkpoints(), ([], 0))


class FlyTests(unittest.TestCase):
    def test_short_course(self):
        course = {"points": [(0.0, 0.0), (60.0, 0.0)], "checkpoints": [1]}
        r = ps.fly("short", 1, "fresh", "shipped", 1.0, course=course)
        self.assertTrue(r["ok"], r)
        self.assertGreater(r["elapsed_s"], 60.0 / ps.MINIPLUS_TOP_MPS)
        self.assertEqual(r["route_m"], 60.0)
        self.assertAlmostEqual(sum(r["time_s"].values()), r["elapsed_s"], delta=0.5)
        r2 = ps.fly("short", 1, "mini+", "predict", 1.0, course=course)
        for key in ("made_good_mps", "efficiency", "time_s", "recoveries"):
            self.assertIn(key, r2)

    def test_predictor_is_a_no_op_on_fresh_orientation(self):
        course = {"points": [(0.0, 0.0), (40.0, 0.0)], "checkpoints": [1]}
        a = ps.fly("short", 2, "fresh", "shipped", 0.8, course=course)
        b = ps.fly("short", 2, "fresh", "predict", 0.8, course=course)
        self.assertEqual(a, b)


class SummaryTests(unittest.TestCase):
    def runs(self):
        return [run("fresh", "shipped", 1.0, "boulevard", 1, 1000.0, 0.9),
                run("fresh", "shipped", 1.0, "boulevard", 2, 1100.0, 0.8),
                run("fresh", "predict", 1.0, "boulevard", 1, 900.0, 0.95),
                run("fresh", "predict", 1.0, "boulevard", 2, 1000.0, 0.85),
                run("fresh", "shipped", 0.6, "boulevard", 1, 1500.0, 0.6),
                run("fresh", "shipped", 0.6, "boulevard", 2, 1500.0, 0.6)]

    def test_sign_test(self):
        self.assertEqual(ps.sign_test_p(9, 0), 0.00390625)
        self.assertEqual(ps.sign_test_p(2, 0), 0.5)
        self.assertIsNone(ps.sign_test_p(0, 0))

    def test_summarise(self):
        s = ps.summarise(self.runs())
        over = {(o["profile"], o["variant"], o["cruise"]): o for o in s["overview"]}
        fast = over[("fresh", "shipped", 1.0)]
        self.assertEqual(fast["median_made_good_mps"], 0.85)
        self.assertEqual(fast["beat_human_pace"], 2)
        self.assertTrue(fast["beats_on_every_course"])
        self.assertEqual(fast["share_driving"], 0.9)
        self.assertEqual(fast["median_path_ratio"], 1.1)
        self.assertFalse(over[("fresh", "shipped", 0.6)]["beats_on_every_course"])
        need = {(c["profile"], c["variant"]): c["lowest_cruise_beating_human_pace"]
                for c in s["cruise_needed"]}
        self.assertEqual(need, {("fresh", "shipped"): 1.0, ("fresh", "predict"): 1.0})
        self.assertEqual(len(s["variant_effect"]), 1)
        e = s["variant_effect"][0]
        self.assertEqual((e["faster"], e["slower"], e["sign_test_p"]), (2, 0, 0.5))
        self.assertEqual(e["median_time_diff_s"], -100.0)
        v = s["verdicts"][0]
        self.assertEqual((v["groups"], v["groups_faster"]), (1, 0))
        self.assertFalse(v["better"])
        self.assertFalse(v["worse"])
        self.assertEqual(s["stale_effect"], [])

    def test_write_outputs(self):
        class Args:
            seeds = 2
        with tempfile.TemporaryDirectory() as d:
            ps.write_outputs(d, self.runs(), 0.0, Args, True)
            with open(os.path.join(d, "summary.json")) as f:
                out = json.load(f)
            self.assertEqual(out["runs"], 6)
            self.assertEqual(out["human"]["time_s"], 106680)
            with open(os.path.join(d, "report.md")) as f:
                md = f.read()
            self.assertIn("29 h 38 min", md)
            self.assertIn("| fresh | shipped | 1 |", md)

    def test_main_small(self):
        course = {"points": [(0.0, 0.0), (30.0, 0.0)], "checkpoints": [1]}
        saved = dict(ps.COURSES)
        ps.COURSES.clear()
        ps.COURSES["tiny"] = course
        try:
            with tempfile.TemporaryDirectory() as d, redirect_stdout(io.StringIO()):
                ps.main(["--out-dir", d, "--seeds", "1", "--cruises", "1.0",
                         "--profiles", "mini+"])
                with open(os.path.join(d, "summary.json")) as f:
                    out = json.load(f)
            # fresh and mini+, shipped and predict, one cruise, one course, one seed.
            self.assertEqual(out["runs"], 4)
            self.assertTrue(out["done"])
        finally:
            ps.COURSES.clear()
            ps.COURSES.update(saved)


if __name__ == "__main__":
    unittest.main()
