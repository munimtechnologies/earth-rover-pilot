"""Tests for frodo_compass_live, on test_frodo_compass's simulated rides with the
compass mirrored so that frame yz+ reads the true heading."""

import json
import math
import os
import tempfile
import unittest

import frodo_compass as fc
import frodo_compass_live as fl
from test_frodo_compass import CYCLE, CY, CZ, circle, synthetic_ride


def ride_yz_plus(schedule):
    """synthetic_ride with axis z mirrored about CZ: frame yz+ then reads the true
    heading minus MOUNT, as yz- does on the original."""
    control, gps, gyro, compass = synthetic_ride(schedule)
    return control, gps, gyro, [(t, x, y, 2 * CZ - z) for t, x, y, z in compass]


class HelperTests(unittest.TestCase):
    def test_frame(self):
        self.assertEqual(fl.FRAME, "yz+")
        self.assertEqual((fl.A, fl.B, fl.S), (1, 2, 1))

    def test_before_and_masked(self):
        samples = [(float(i), 0.0, 0.0, 0.0) for i in range(10)]
        self.assertEqual([s[0] for s in fl.before(samples, 3.0)], [0.0, 1.0, 2.0])
        control = [(i * 0.1, 0.8, 0.0, [100.0] * 4) for i in range(20)]
        grid = fc.Grid(control, [])
        # Cell centres 0.1, 0.3, ..., 1.9 s: the first five are before 1.0 s.
        self.assertEqual(fl.masked([1.0] * 10, grid, 1.0), [None] * 5 + [1.0] * 5)

    def test_heading_of(self):
        r = math.radians(30.0)
        sample = (0.0, 7.0, CY + 200.0 * math.cos(r), CZ + 200.0 * math.sin(r))
        self.assertAlmostEqual(fl.heading_of(sample, (CY, CZ)), 30.0, places=9)
        same = fc.frame_headings([sample], [(0, 0, 0.0)], 1, 2, 1, (CY, CZ))[0]
        self.assertAlmostEqual(fl.heading_of(sample, (CY, CZ)), same, places=9)

    def test_running_centres(self):
        # 120 s on a quarter circle, then 120 s round the whole circle at 3 deg/s.
        first = circle(120, 0.0, 90.0)
        second = [(120.0 + s[0],) + s[1:] for s in circle(120)]
        cents = fl.running_centres(first + second, 250.0)
        self.assertEqual([t for t, _ in cents], [60.0, 120.0, 180.0, 240.0])
        # By 180 s the samples span 0-177 deg: 18 of 36 directions, just enough.
        self.assertEqual([c is None for _, c in cents], [True, True, False, False])
        self.assertAlmostEqual(cents[2][1][0], 5.0, places=6)
        self.assertAlmostEqual(cents[2][1][1], -3.0, places=6)

    def test_calibration_windows(self):
        samples = circle(600)  # 0.6 deg per second, 599 s
        info, centre = fc.calibrate(samples, 1, 2)
        self.assertTrue(info["ok"])
        cal = fl.calibration(samples, info, centre)
        self.assertFalse(cal["1"]["ok"])   # 0-35.4 deg
        self.assertFalse(cal["2"]["ok"])   # 0-71.4 deg
        self.assertTrue(cal["5"]["ok"])    # 0-179.4 deg
        self.assertLess(cal["5"]["centre_err"], 0.01)
        self.assertEqual(cal["10"], {"short": True})


class RideTests(unittest.TestCase):
    """490 s of 150 deg left turns between 30 s straights, exact GPS and compass.
    By 60 s the heading has swept 150 deg (too little), by 120 s 300 deg."""

    @classmethod
    def setUpClass(cls):
        control, gps, gyro, compass = ride_yz_plus([(10, 0.8, 0.0)] + CYCLE * 2)
        cls.pool = fl.new_pool()
        cls.st = fl.analyse_ride(control, gps, gyro, compass, cls.pool)
        cls.s = fl.summarise(cls.pool)

    def test_ride(self):
        st = self.st
        self.assertNotIn("skipped", st)
        self.assertTrue(st["full"]["ok"])
        self.assertEqual(st["variants"], ["first2", "first5", "full", "raw", "running"])
        self.assertEqual(st["running_first_ok_min"], 2.0)
        self.assertIn("first5", st["bias_fits"])
        self.assertGreater(st["anchors"], 20)
        self.assertEqual(st["common_anchors"], 0)   # first1 never calibrates

    def test_misses(self):
        rows = self.s["table"]
        for v in ("first2", "first5", "running", "full"):
            r = fl.find(rows, "all", v, 10)
            self.assertIsNotNone(r, v)
            self.assertLess(r["median_m"], 0.3, r)
        self.assertGreater(fl.find(rows, "all", "raw", 10)["median_m"],
                           fl.find(rows, "all", "full", 10)["median_m"])
        self.assertEqual(fl.find(rows, "all", "full", 10)["over_full"], 1.0)
        self.assertIsNone(fl.find(rows, "common", "full", 10))
        self.assertEqual(self.s["decision"]["live_compass"], "keeps the gain")

    def test_calibration_summary(self):
        c = self.s["calibration"]
        self.assertEqual(c["1"]["rides"], 1)
        self.assertEqual(c["1"]["ok"], 0.0)
        self.assertEqual(c["2"]["ok"], 1.0)
        self.assertEqual(c["5"]["ok"], 1.0)
        self.assertEqual(c["10"]["rides"], 0)
        self.assertIsNone(c["10"]["ok"])
        self.assertEqual(c["running"]["by_min"]["1"], 0.0)
        self.assertEqual(c["running"]["by_min"]["2"], 1.0)

    def test_outputs(self):
        with tempfile.TemporaryDirectory() as d:
            res = fl.write_outputs(d, [{"part": "x", "bytes_read": 5}],
                                   [{"no": 0}, {"no": 1, "skipped": "no compass"}],
                                   self.pool, 0.0)
            self.assertTrue(res["conclusions"])
            self.assertEqual(res["rides_skipped"], {"no compass": 1})
            with open(os.path.join(d, "summary.json")) as f:
                self.assertEqual(json.load(f)["version"], fl.__version__)
            with open(os.path.join(d, "report.md")) as f:
                self.assertIn("Calibrating", f.read())
            self.assertTrue(os.path.exists(os.path.join(d, "rides.jsonl")))


class GuardTests(unittest.TestCase):
    def test_guards(self):
        control, gps, gyro, compass = ride_yz_plus([(60, 0.8, 0.0)])
        pool = fl.new_pool()
        self.assertEqual(fl.analyse_ride(control, gps, gyro, [], pool)["skipped"], "no compass")
        # Driving straight, the compass never turns: the whole record does not calibrate.
        st = fl.analyse_ride(control, gps, gyro, compass, pool)
        self.assertEqual(st["skipped"], "whole ride does not calibrate")
        self.assertEqual(st["windows"]["1"], {"short": True})   # 59 s of compass
        self.assertEqual(len(pool["cal"]), 1)
        self.assertEqual(pool["rides"], [])
        self.assertTrue(fl.conclusions(fl.summarise(pool)))


if __name__ == "__main__":
    unittest.main()
