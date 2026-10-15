"""Tests for the tipped-rover stop (TipWatch) and the compass-bias fit's
residual gate and weighting (HeadingEstimator), new in v0.9.2.

Run: python -m unittest test_tip_and_bias -v
"""

import io
import math
import os
import sys
import unittest
from contextlib import redirect_stdout
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import rover_pilot as rp  # noqa: E402

LAT, LON = 37.8719, -122.2585


def rows(x, y, z, n=3, stamp=1725434620.858):
    """A /data accels list: rows of [x, y, z, timestamp], as the SDK README shows."""
    return [[x, y, z, stamp + 0.02 * k] for k in range(n)]


class GravityTests(unittest.TestCase):
    def test_mean_of_rows_in_g(self):
        g = rp.TipWatch.gravity(rows(0.998, 0.003, 0.005))
        self.assertAlmostEqual(g[0], 0.998)
        self.assertAlmostEqual(g[1], 0.003)
        self.assertAlmostEqual(g[2], 0.005)

    def test_metres_per_second_squared_are_scaled_to_g(self):
        g = rp.TipWatch.gravity(rows(0.0, 0.0, 9.81))
        self.assertAlmostEqual(g[2], 1.0, places=2)

    def test_bad_rows_are_skipped(self):
        self.assertIsNone(rp.TipWatch.gravity(None))
        self.assertIsNone(rp.TipWatch.gravity([]))
        self.assertIsNone(rp.TipWatch.gravity("0.9,0.1,0.0"))
        self.assertIsNone(rp.TipWatch.gravity([[1.0], ["a", "b", "c", 1.0],
                                               [float("nan"), 0.0, 0.0, 1.0]]))
        self.assertEqual(rp.TipWatch.gravity([[1.0], [0.0, 1.0, 0.0, 1.0]]), (0.0, 1.0, 0.0))


class WatchTests(unittest.TestCase):
    def feed(self, w, t0, t1, x, y, z, step=0.1):
        t, out = t0, None
        while t < t1 - 1e-9:
            out = w.update(t, rows(x, y, z))
            t += step
        return out

    def test_learns_up_then_notices_a_tip(self):
        w = rp.TipWatch()
        self.assertFalse(self.feed(w, 0.0, 5.0, 0.998, 0.003, 0.005))  # upright, x up
        self.assertIsNotNone(w.up)
        self.assertAlmostEqual(w.up[0], 1.0, places=2)
        self.assertLess(w.angle, 2.0)
        # on its side: gravity along y
        self.assertFalse(w.update(5.0, rows(0.02, 0.99, 0.01)))  # over, but not held yet
        self.assertFalse(w.update(5.5, rows(0.02, 0.99, 0.01)))
        self.assertTrue(w.update(6.0, rows(0.02, 0.99, 0.01)))   # held for 1 s
        self.assertGreater(w.angle, 80.0)
        self.assertTrue(w.tipped)
        # righted again
        self.assertFalse(w.update(7.0, rows(0.998, 0.003, 0.005)))
        self.assertFalse(w.tipped)

    def test_any_axis_can_be_up(self):
        for up in ((0.0, 0.0, -1.0), (0.0, 1.0, 0.0), (-1.0, 0.0, 0.0)):
            w = rp.TipWatch()
            self.feed(w, 0.0, 4.0, *up)
            self.assertLess(w.angle, 1.0, up)
            self.assertTrue(self.feed(w, 4.0, 6.0, 0.7, 0.7, 0.0) or
                            self.feed(w, 6.0, 8.0, 0.0, 0.0, 1.0), up)

    def test_a_slope_is_not_a_tip(self):
        w = rp.TipWatch()
        self.feed(w, 0.0, 4.0, 1.0, 0.0, 0.0)
        c, s = math.cos(math.radians(30.0)), math.sin(math.radians(30.0))
        self.assertFalse(self.feed(w, 4.0, 8.0, c, s, 0.0))  # 30 degrees over
        self.assertAlmostEqual(w.angle, 30.0, places=1)
        self.assertFalse(w.tipped)

    def test_short_knocks_do_not_count(self):
        w = rp.TipWatch()
        self.feed(w, 0.0, 4.0, 1.0, 0.0, 0.0)
        self.assertFalse(w.update(4.0, rows(0.0, 1.0, 0.0)))
        self.assertFalse(w.update(4.5, rows(1.0, 0.0, 0.0)))
        self.assertFalse(w.update(5.5, rows(0.0, 1.0, 0.0)))
        self.assertFalse(w.update(6.0, rows(1.0, 0.0, 0.0)))
        self.assertFalse(w.tipped)

    def test_readings_far_from_one_g_are_ignored(self):
        w = rp.TipWatch()
        self.feed(w, 0.0, 4.0, 1.0, 0.0, 0.0)
        n = w.samples
        self.assertFalse(self.feed(w, 4.0, 6.0, 0.0, 3.0, 0.0))  # a 3 g knock
        self.assertEqual(w.samples, n)
        self.assertFalse(self.feed(w, 6.0, 8.0, 0.0, 0.1, 0.0))  # a drop, or bad data
        self.assertEqual(w.samples, n)
        self.assertFalse(w.tipped)

    def test_no_accels_means_no_opinion(self):
        w = rp.TipWatch()
        for t in range(0, 100):
            self.assertFalse(w.update(float(t), None))
            self.assertFalse(w.update(float(t) + 0.5, []))
        self.assertIsNone(w.up)
        self.assertEqual(w.samples, 0)

    def test_zero_angle_turns_it_off(self):
        w = rp.TipWatch(angle_deg=0.0)
        self.feed(w, 0.0, 4.0, 1.0, 0.0, 0.0)
        self.assertFalse(self.feed(w, 4.0, 8.0, 0.0, 1.0, 0.0))
        self.assertIsNone(w.up)
        self.assertFalse(w.tipped)


class TippingRover(rp.SimRover):
    """A SimRover with an accelerometer: upright (gravity on x, as in the SDK
    README's example) except between tip_s and right_s, when it lies on its side."""

    def __init__(self, *a, tip_s=math.inf, right_s=math.inf, **kw):
        super().__init__(*a, **kw)
        self.tip_s = tip_s
        self.right_s = right_s
        self.sent = []  # (t, linear, angular)

    def control(self, linear, angular):
        self.sent.append((self.t, linear, angular))
        super().control(linear, angular)

    def data(self):
        d = super().data()
        g = (0.03, 0.97, 0.05) if self.tip_s <= self.t < self.right_s else (0.99, 0.02, 0.03)
        d["accels"] = [[g[0], g[1], g[2], 1725434620.0 + self.t + 0.02 * k] for k in range(5)]
        return d


def moving(sent, after, before=math.inf):
    """Commands other than a stop sent between `after` and `before` (seconds)."""
    return [c for c in sent if after < c[0] < before and (c[1], c[2]) != (0.0, 0.0)]


class PilotTests(unittest.TestCase):
    def fly(self, sim, timeout_s=1500, **kw):
        events = []
        res = rp.Pilot(sim, clock=sim.clock, sleep=sim.sleep, log=events.append,
                       **kw).run(timeout_s=timeout_s)
        return res, [e["event"] for e in events]

    def test_tipped_rover_is_stopped_and_drives_on_when_righted(self):
        sim = TippingRover(rp.DEMO_MISSION, seed=1, tip_s=20.0, right_s=40.0)
        res, names = self.fly(sim)
        self.assertTrue(res["ok"], res)
        self.assertEqual(res["reached"], [1, 2, 3, 4])
        self.assertEqual(res["tip_stops"], 1)
        self.assertTrue(moving(sim.sent, 0.0, 20.0))          # it was driving before
        self.assertEqual(moving(sim.sent, 21.5, 39.95), [])   # stopped within 1.5 s
        self.assertTrue(moving(sim.sent, 40.5))               # and drove on once righted
        self.assertEqual([n for n in names if n in ("tipped", "upright")],
                         ["tipped", "upright"])

    def test_tipped_for_good_stays_stopped(self):
        sim = TippingRover(rp.DEMO_MISSION, seed=1, tip_s=20.0)
        res, names = self.fly(sim, timeout_s=60)
        self.assertEqual(res["reason"], "timeout")
        self.assertEqual(moving(sim.sent, 21.5), [])
        self.assertEqual(res["tip_stops"], 1)
        self.assertIn("tipped", names)
        self.assertNotIn("upright", names)

    def test_zero_angle_drives_on(self):
        sim = TippingRover(rp.DEMO_MISSION, seed=1, tip_s=20.0)
        res, names = self.fly(sim, timeout_s=60, tip_angle_deg=0.0)
        self.assertTrue(moving(sim.sent, 25.0))
        self.assertEqual(res["tip_stops"], 0)
        self.assertNotIn("tipped", names)

    def test_simulator_without_accels_flies_as_before(self):
        out = []
        for angle in (rp.TIP_ANGLE_DEG, 0.0):
            sim = rp.SimRover(rp.DEMO_MISSION, seed=2)
            res = rp.Pilot(sim, clock=sim.clock, sleep=sim.sleep,
                           tip_angle_deg=angle).run(timeout_s=1500)
            out.append((res, sim.t, sim.north, sim.east))
        self.assertTrue(out[0][0]["ok"], out[0][0])
        self.assertEqual(out[0][0]["tip_stops"], 0)
        self.assertEqual(out[0], out[1])


def drive(est, course_deg, compass_deg, seconds=30, speed=0.5, across=lambda k: 0.0, t0=0.0):
    """Feed `seconds` of straight driving at `speed` m/s along `course_deg`, the
    compass reading `compass_deg`, one fix a second, each pushed `across(k)` metres
    to the right of the course."""
    r = math.radians(course_deg)
    est.update(t0 - 0.5, None, compass_deg, 0.0, 0.0)  # a stopped tick: a fresh stretch
    for k in range(seconds):
        along, side = speed * k, across(k)
        north = along * math.cos(r) - side * math.sin(r)
        east = along * math.sin(r) + side * math.cos(r)
        est.update(t0 + k, rp.offset_latlon(LAT, LON, north, east), compass_deg, 0.6, 0.0)


class BiasFitTests(unittest.TestCase):
    def test_defaults_are_off_and_a_clean_stretch_fits(self):
        est = rp.HeadingEstimator()
        self.assertIsNone(est.max_residual_m)
        self.assertFalse(est.weigh)
        self.assertIsNone(est.last_fit)
        drive(est, 90.0, 60.0)
        self.assertEqual(est.calibrations, 1)
        self.assertEqual(est.rejected_fits, 0)
        self.assertAlmostEqual(est.bias, 30.0, delta=0.5)
        self.assertLess(est.last_fit["residual_m"], 0.1)
        self.assertGreater(est.last_fit["length_m"], 9.5)
        self.assertLess(est.last_fit["length_m"], 11.5)
        self.assertGreaterEqual(est.last_fit["points"], 5)

    def test_residual_gate_rejects_a_bent_stretch(self):
        bent = lambda k: 3.0 * math.sin(k / 3.0)  # noqa: E731
        gated = rp.HeadingEstimator(max_residual_m=1.0)
        drive(gated, 90.0, 60.0, across=bent)
        self.assertEqual(gated.calibrations, 0)
        self.assertEqual(gated.rejected_fits, 1)
        self.assertEqual(gated.bias, 0.0)
        self.assertGreater(gated.last_fit["residual_m"], 1.0)
        self.assertIsNotNone(gated.last_course)  # the course is still kept for a compass outage
        plain = rp.HeadingEstimator()
        drive(plain, 90.0, 60.0, across=bent)
        self.assertEqual(plain.calibrations, 1)
        self.assertEqual(plain.rejected_fits, 0)

    def test_weighting_trusts_the_straighter_stretch(self):
        # Stretch A: fixes scattered 2 m either side of a line turned 10 degrees
        # off the true course (what a drifting error can do), so it says bias 40.
        # Stretch B: clean, bias 30. The true bias is 30.
        skew = math.tan(math.radians(10.0))
        noisy = lambda k: 2.0 * (1 if k % 2 else -1) + 0.5 * k * skew  # noqa: E731
        results = {}
        for weigh in (False, True):
            est = rp.HeadingEstimator(weigh=weigh)
            drive(est, 90.0, 60.0, seconds=25, across=noisy)
            self.assertEqual(est.calibrations, 1)
            self.assertAlmostEqual(est.bias, 40.0, delta=3.0)
            self.assertGreater(est.last_fit["residual_m"], 1.5)
            drive(est, 90.0, 60.0, seconds=25, t0=100.0)
            self.assertEqual(est.calibrations, 2)
            results[weigh] = est.bias
        self.assertGreater(abs(results[False] - 30.0), 5.0)  # the gain update keeps a third
        self.assertLess(abs(results[True] - 30.0), 2.0)      # the weights all but drop it

    def test_weighted_bias_wraps(self):
        est = rp.HeadingEstimator(weigh=True)
        drive(est, 10.0, 185.0)   # bias -175
        drive(est, 10.0, 180.0, t0=100.0)  # bias -170
        self.assertEqual(est.calibrations, 2)
        self.assertAlmostEqual(abs(est.bias), 172.5, delta=1.0)

    def test_settings_fly_the_demo(self):
        sim = rp.SimRover(rp.DEMO_MISSION, seed=3, **rp.SIM_REAL)
        pilot = rp.Pilot(sim, clock=sim.clock, sleep=sim.sleep)
        pilot.heading.weigh = True
        pilot.heading.max_residual_m = 3.0
        res = pilot.run(timeout_s=1500)
        self.assertTrue(res["ok"], res)
        self.assertGreaterEqual(res["calibrations"], 1)
        self.assertIsNotNone(pilot.heading.last_fit)


class FakePilot:
    """Stands in for rp.Pilot and records what main() built it with."""
    seen = {}

    def __init__(self, rover, **kw):
        FakePilot.seen = dict(kw, rover=rover)

    def run(self, start=True, timeout_s=3600.0):
        return {"ok": True, "reason": "mission completed"}


def run_main(argv):
    buf = io.StringIO()
    with mock.patch.object(rp, "Pilot", FakePilot), redirect_stdout(buf):
        code = rp.main(argv)
    return code, FakePilot.seen


class CommandLineTests(unittest.TestCase):
    def test_default_tip_angle(self):
        for argv in (["--sdk", "http://x"], ["--simulate"]):
            code, seen = run_main(argv)
            self.assertEqual(code, 0)
            self.assertEqual(seen["tip_angle_deg"], rp.TIP_ANGLE_DEG)
        self.assertEqual(rp.TIP_ANGLE_DEG, 50.0)

    def test_tip_angle_option(self):
        code, seen = run_main(["--sdk", "http://x", "--tip-angle", "0"])
        self.assertEqual(code, 0)
        self.assertEqual(seen["tip_angle_deg"], 0.0)

    def test_pilot_has_a_tip_watch(self):
        sim = rp.SimRover(rp.DEMO_MISSION)
        pilot = rp.Pilot(sim, clock=sim.clock, sleep=sim.sleep, tip_angle_deg=40.0)
        self.assertEqual(pilot.tip.angle_deg, 40.0)
        self.assertEqual(pilot.tip_stops, 0)


if __name__ == "__main__":
    unittest.main()
