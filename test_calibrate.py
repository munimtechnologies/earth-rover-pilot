"""Offline tests for calibrate (standard library only; no rover needed).

Run: python -m unittest test_calibrate -v
"""

import math
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import calibrate as cal  # noqa: E402
import rover_pilot as rp  # noqa: E402

LAT, LON = 37.8719, -122.2585


def readings(scale, turns=2.0, start=0.3, n=200, sign=1.0):
    """Orientation readings over `turns` whole turns, starting `start` of a turn in."""
    return [((start + sign * turns * i / n) % 1.0) * scale for i in range(n + 1)]


class ScaleTests(unittest.TestCase):
    def test_degrees(self):
        self.assertEqual(cal.detect_scale(readings(360.0)), 360.0)

    def test_byte(self):
        self.assertEqual(cal.detect_scale(readings(256.0)), 256.0)

    def test_radians(self):
        self.assertAlmostEqual(cal.detect_scale(readings(2 * math.pi)), 2 * math.pi)

    def test_signed_degrees(self):
        self.assertEqual(cal.detect_scale([v - 180.0 for v in readings(360.0)]), 360.0)

    def test_turning_the_other_way(self):
        self.assertEqual(cal.detect_scale(readings(360.0, sign=-1.0)), 360.0)

    def test_needs_a_whole_turn(self):
        # 0.6 of a turn in degrees spans 216, which could pass for most of a 0-255 turn
        self.assertIsNone(cal.detect_scale(readings(360.0, turns=0.6)))
        self.assertIsNone(cal.detect_scale([128.0] * 50))
        self.assertIsNone(cal.detect_scale([1.0]))

    def test_unwrap_goes_the_short_way(self):
        self.assertEqual(cal.unwrap_total([350.0, 10.0, 30.0], 360.0), (40.0, 20.0))
        self.assertEqual(cal.unwrap_total([10.0, 350.0], 360.0), (-20.0, 20.0))


class FitTests(unittest.TestCase):
    def test_course_and_speed(self):
        pts = [(float(t),) + rp.offset_latlon(LAT, LON, 0.0, 0.5 * t) for t in range(11)]
        course, speed = cal.fit_course(pts)
        self.assertAlmostEqual(course, 90.0, delta=0.5)
        self.assertAlmostEqual(speed, 0.5, delta=0.01)

    def test_standing_still_has_no_course(self):
        self.assertIsNone(cal.fit_course([(float(t), LAT, LON) for t in range(11)]))
        self.assertIsNone(cal.fit_course([(0.0, LAT, LON), (1.0, LAT + 1e-4, LON)]))

    def test_circular_mean(self):
        self.assertAlmostEqual(rp.wrap180(cal.circular_mean_deg([350.0, 10.0])), 0.0, delta=1e-6)
        self.assertAlmostEqual(cal.circular_mean_deg([80.0, 100.0]), 90.0, delta=1e-6)


class SimCalibrationTests(unittest.TestCase):
    # The simulator's compass reads 25 degrees low, so the bias to find is about +25.
    def run_on(self, seed, **sim_kw):
        sim = rp.SimRover(rp.DEMO_MISSION, seed=seed, **sim_kw)
        res = cal.calibrate(sim, clock=sim.clock, sleep=sim.sleep)
        self.assertTrue(res["ok"], res)
        self.assertLess(abs(rp.wrap180(res["bias_deg"] - 25.0)), 30.0, res)
        # 60 degrees/s and 1.2 m/s at full command in the simulator
        self.assertAlmostEqual(res["yaw_dps_at_full"], 60.0, delta=10.0)
        self.assertAlmostEqual(res["speed_mps_at_full"], 1.2, delta=0.5)
        self.assertGreater(abs(res["turn_deg"]), 45.0, res)
        self.assertEqual(sim.queue[-1][1:], (0.0, 0.0))  # the last command is a stop
        return res

    def test_usual_rover(self):
        for seed in (1, 2):
            with self.subTest(seed=seed):
                res = self.run_on(seed)
                self.assertEqual(res["orientation_scale"], 360.0)
                self.assertTrue(res["orientation_clockwise"])
                self.assertTrue(res["angular_right_positive"])

    def test_quirky_rover(self):
        res = self.run_on(3, **rp.SIM_QUIRKS)
        self.assertEqual(res["orientation_scale"], 256.0)
        self.assertFalse(res["orientation_clockwise"])
        self.assertFalse(res["angular_right_positive"])
        self.assertIn("counter-clockwise", res["reason"])

    def test_mirrored_compass_only(self):
        res = self.run_on(4, orientation_clockwise=False)
        self.assertEqual(res["orientation_scale"], 360.0)
        self.assertFalse(res["orientation_clockwise"])
        self.assertTrue(res["angular_right_positive"])

    def test_left_turning_rover_only(self):
        res = self.run_on(5, angular_sign=-1.0)
        self.assertTrue(res["orientation_clockwise"])
        self.assertFalse(res["angular_right_positive"])

    def test_result_drives_the_pilot(self):
        sim = rp.SimRover(rp.DEMO_MISSION, seed=3, **rp.SIM_QUIRKS)
        res = cal.calibrate(sim, clock=sim.clock, sleep=sim.sleep)
        conv = rp.Conventions.from_dict(res)
        sim = rp.SimRover(rp.DEMO_MISSION, seed=2, **rp.SIM_QUIRKS)
        out = rp.Pilot(sim, clock=sim.clock, sleep=sim.sleep, conventions=conv).run(timeout_s=1500)
        self.assertTrue(out["ok"], out)
        self.assertEqual(out["reached"], [1, 2, 3, 4])

    def test_rover_that_cannot_move(self):
        sim = rp.SimRover(rp.DEMO_MISSION, seed=1, blocked_until_s=1e9)
        res = cal.calibrate(sim, clock=sim.clock, sleep=sim.sleep)
        self.assertFalse(res["ok"])
        self.assertIn("straight line", res["reason"])
        self.assertEqual(res["orientation_scale"], 360.0)  # the spin still worked


class FakeClock:
    def __init__(self):
        self.t = 0.0

    def clock(self):
        return self.t

    def sleep(self, seconds):
        self.t += max(seconds, 0.01)


class StillRover:
    """Has a fix, but its orientation never changes."""

    def __init__(self, lat=LAT, lon=LON):
        self.lat, self.lon = lat, lon
        self.commands = []

    def data(self):
        return {"latitude": self.lat, "longitude": self.lon, "orientation": 128}

    def control(self, linear, angular):
        self.commands.append((linear, angular))


class FailureTests(unittest.TestCase):
    def test_no_turn_seen(self):
        rover, c = StillRover(), FakeClock()
        res = cal.calibrate(rover, clock=c.clock, sleep=c.sleep)
        self.assertFalse(res["ok"])
        self.assertIn("full turn", res["reason"])
        self.assertEqual(rover.commands[-1], (0.0, 0.0))
        self.assertIn((0.0, 0.4), rover.commands)  # it did try to spin
        self.assertNotIn((0.4, 0.0), rover.commands)  # and never drove off

    def test_no_gps_fix(self):
        rover, c = StillRover(lat=1000, lon=1000), FakeClock()
        res = cal.calibrate(rover, clock=c.clock, sleep=c.sleep, fix_timeout_s=3.0)
        self.assertFalse(res["ok"])
        self.assertEqual(res["reason"], "no GPS fix")
        self.assertTrue(all(cmd == (0.0, 0.0) for cmd in rover.commands))


if __name__ == "__main__":
    unittest.main()
