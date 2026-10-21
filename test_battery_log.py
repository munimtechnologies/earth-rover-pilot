# Copyright 2026 Munim, Inc. Licensed under the Apache License, Version 2.0.
"""BatteryLog: charge used, distance driven and the range that leaves."""
import math
import unittest

from rover_pilot import BatteryLog, offset_latlon

LAT0, LON0 = 37.87, -122.26


class BatteryLogTest(unittest.TestCase):
    def test_straight_drive(self):
        log = BatteryLog()
        for k in range(1001):  # 1 m steps north, 100% down to 90%
            log.update(100.0 - k / 100.0, offset_latlon(LAT0, LON0, float(k), 0.0))
        out = log.result()
        self.assertEqual(out["start_pct"], 100.0)
        self.assertEqual(out["end_pct"], 90.0)
        self.assertEqual(out["used_pct"], 10.0)
        self.assertAlmostEqual(out["driven_m"], 1000.0, delta=5.0)
        self.assertAlmostEqual(out["m_per_pct"], 100.0, delta=1.0)
        self.assertAlmostEqual(out["range_left_m"], 9000.0, delta=90.0)

    def test_jitter_standing_still(self):
        log = BatteryLog()
        for k in range(600):  # +-1 m back and forth: never 3 m from the anchor
            north = 1.0 if k % 2 else -1.0
            log.update(80, offset_latlon(LAT0, LON0, north, 0.0))
        out = log.result()
        self.assertEqual(out["driven_m"], 0.0)
        self.assertEqual(out["used_pct"], 0.0)
        self.assertIsNone(out["m_per_pct"])
        self.assertIsNone(out["range_left_m"])

    def test_bad_levels_left_out(self):
        log = BatteryLog()
        for value in (None, "x", -5, 150, float("nan"), "100%", True):
            log.update(value, None)
        self.assertIsNone(log.result()["start_pct"])
        log.update("87", None)
        log.update(150, None)
        self.assertEqual(log.result()["end_pct"], 87.0)

    def test_too_little_used(self):
        log = BatteryLog()
        log.update(100, offset_latlon(LAT0, LON0, 0.0, 0.0))
        log.update(99, offset_latlon(LAT0, LON0, 500.0, 0.0))
        out = log.result()
        self.assertAlmostEqual(out["driven_m"], 500.0, delta=1.0)
        self.assertEqual(out["used_pct"], 1.0)
        self.assertIsNone(out["m_per_pct"])

    def test_no_battery_field(self):
        log = BatteryLog()
        for k in range(10):
            log.update(None, offset_latlon(LAT0, LON0, 10.0 * k, 0.0))
        out = log.result()
        self.assertIsNone(out["start_pct"])
        self.assertIsNone(out["used_pct"])
        self.assertTrue(math.isclose(out["driven_m"], 90.0, abs_tol=1.0))


if __name__ == "__main__":
    unittest.main()
