"""Tests for marathon.py: the Berkeley-Stanford budget and the checks against it.

Run: python -m unittest test_marathon -v
"""

import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import marathon as mt  # noqa: E402


class BudgetTests(unittest.TestCase):
    def test_the_human_benchmark(self):
        b = mt.budget()
        self.assertAlmostEqual(b["distance_m"], 80467.2, places=1)
        self.assertEqual(b["time_s"], 106680)
        self.assertAlmostEqual(b["human_pace_mps"], 0.7543, places=4)
        self.assertEqual(b["legs"], 7)
        self.assertAlmostEqual(b["leg_m"], 11495.3, places=1)

    def test_what_it_asks_of_a_mini_plus(self):
        b = mt.budget()
        self.assertAlmostEqual(b["top_mps"], 1.1111, places=4)
        self.assertAlmostEqual(b["min_drive_h"], 20.12, places=2)
        self.assertAlmostEqual(b["max_stops_h"], 9.52, places=2)
        self.assertAlmostEqual(b["cruise_floor"], 0.6789, places=4)
        self.assertAlmostEqual(b["max_path_ratio"], 1.0439, places=4)

    def test_other_rovers(self):
        b = mt.budget(top_mps=3.0 / 3.6, range_m=15000.0)
        self.assertAlmostEqual(b["min_drive_h"], 26.82, places=2)
        self.assertAlmostEqual(b["cruise_floor"], 0.9051, places=4)
        self.assertAlmostEqual(b["max_path_ratio"], 1.3049, places=4)

    def test_needed_and_allowed(self):
        self.assertAlmostEqual(mt.needed_made_good(), 0.75429, places=5)
        # 6 h of stops leaves 23 h 38 min to drive 80.5 km
        self.assertAlmostEqual(mt.needed_made_good(6 * 3600), 80467.2 / 85080, places=6)
        self.assertIsNone(mt.needed_made_good(mt.HUMAN_S))
        self.assertAlmostEqual(mt.stops_allowed_s(1.0), 106680 - 80467.2, places=1)
        self.assertLess(mt.stops_allowed_s(0.7), 0)
        self.assertIsNone(mt.stops_allowed_s(0.0))
        self.assertIsNone(mt.stops_allowed_s(None))


class RouteTests(unittest.TestCase):
    def test_a_route_that_fits(self):
        out = mt.check_route({"ok": True, "route_m": 11200.0, "straight_m": 9800.0})
        self.assertTrue(out["fits_one_charge"])
        self.assertAlmostEqual(out["share_of_charge"], 0.933, places=3)
        self.assertAlmostEqual(out["headroom_m"], 800.0)
        self.assertAlmostEqual(out["detour_ratio"], 1.143, places=3)
        self.assertIn("800 m to spare", out["reason"])

    def test_a_route_too_long(self):
        out = mt.check_route({"ok": True, "route_m": 12500.0, "straight_m": 10000.0})
        self.assertFalse(out["fits_one_charge"])
        self.assertLess(out["headroom_m"], 0)
        self.assertIn("longer than one charge", out["reason"])

    def test_missing_legs_make_a_lower_bound(self):
        out = mt.check_route({"ok": False, "route_m": 5000.0, "straight_m": 9000.0})
        self.assertFalse(out["complete"])
        self.assertTrue(out["fits_one_charge"])
        self.assertIn("lower bound", out["reason"])

    def test_no_route(self):
        out = mt.check_route({"ok": False, "reason": "no GPS fix"})
        self.assertIsNone(out["fits_one_charge"])
        self.assertIsNone(mt.check_route({"ok": True, "route_m": 100.0})["detour_ratio"])

    def test_other_range(self):
        out = mt.check_route({"ok": True, "route_m": 11200.0, "straight_m": 9800.0}, range_m=10000.0)
        self.assertFalse(out["fits_one_charge"])


class PaceTests(unittest.TestCase):
    SUMMARY = {"overview": [
        {"profile": "mini+", "variant": "shipped", "cruise": 0.6, "completed": 36, "runs": 36,
         "median_made_good_mps": 0.62, "median_path_ratio": 1.01},
        {"profile": "mini+", "variant": "shipped", "cruise": 1.0, "completed": 35, "runs": 36,
         "median_made_good_mps": 1.0, "median_path_ratio": 1.06},
        {"profile": "mini+", "variant": "predict", "cruise": 0.8, "completed": 0, "runs": 36,
         "median_made_good_mps": None, "median_path_ratio": None},
    ]}

    def test_verdicts(self):
        v = mt.pace_verdicts(self.SUMMARY)
        self.assertEqual(len(v), 3)
        slow, fast, none = v
        self.assertFalse(slow["beats_with_no_stops"])
        self.assertLess(slow["stops_allowed_h"], 0)
        self.assertTrue(slow["path_fits_charge"])
        self.assertAlmostEqual(slow["drive_h"], 36.05, places=2)
        self.assertTrue(fast["beats_with_no_stops"])
        self.assertAlmostEqual(fast["drive_h"], 22.35, places=2)
        self.assertAlmostEqual(fast["stops_allowed_h"], 7.28, places=2)
        self.assertFalse(fast["path_fits_charge"])
        self.assertFalse(none["beats_with_no_stops"])
        self.assertIsNone(none["drive_h"])
        self.assertIsNone(none["path_fits_charge"])

    def test_empty(self):
        self.assertEqual(mt.pace_verdicts({}), [])


class CommandLineTests(unittest.TestCase):
    def run_main(self, argv):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = mt.main(argv)
        return code, json.loads(buf.getvalue())

    def test_budget(self):
        code, out = self.run_main(["budget"])
        self.assertEqual(code, 0)
        self.assertAlmostEqual(out["max_path_ratio"], 1.0439, places=4)
        code, out = self.run_main(["budget", "--range-km", "15", "--top-kmh", "3"])
        self.assertAlmostEqual(out["max_path_ratio"], 1.3049, places=4)

    def test_route_and_pace_files(self):
        with tempfile.TemporaryDirectory() as d:
            route = os.path.join(d, "check.json")
            with open(route, "w", encoding="utf-8") as f:
                json.dump({"ok": True, "route_m": 11200.0, "straight_m": 9800.0}, f)
            code, out = self.run_main(["route", route])
            self.assertEqual(code, 0)
            self.assertTrue(out["fits_one_charge"])
            pace = os.path.join(d, "summary.json")
            with open(pace, "w", encoding="utf-8") as f:
                json.dump(PaceTests.SUMMARY, f)
            code, out = self.run_main(["pace", pace])
            self.assertEqual(code, 0)
            self.assertEqual(len(out["verdicts"]), 3)
            self.assertAlmostEqual(out["budget"]["leg_m"], 11495.3, places=1)


if __name__ == "__main__":
    unittest.main()
