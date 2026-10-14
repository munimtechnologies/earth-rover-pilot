"""Tests for the steering the pilot uses on a real rover (ROVER_STEERING, from gain_study.py).

Run: python -m unittest test_steering_defaults -v
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


class MakeSteeringTests(unittest.TestCase):
    def test_real_rover_gets_the_study_gains(self):
        s = rp.make_steering(False)
        self.assertEqual(s.max_angular, 1.0)
        self.assertEqual(s.turn_in_place_deg, 90.0)
        self.assertEqual(s.cruise, 0.6)
        self.assertAlmostEqual(s.kp, 1.0 / 60.0)

    def test_simulator_keeps_the_class_defaults(self):
        s = rp.make_steering(True)
        self.assertEqual(s.max_angular, 0.6)
        self.assertEqual(s.turn_in_place_deg, 60.0)

    def test_options_override_either(self):
        for simulate in (False, True):
            s = rp.make_steering(simulate, cruise=0.4, max_angular=0.5, turn_in_place_deg=45.0)
            self.assertEqual((s.cruise, s.max_angular, s.turn_in_place_deg), (0.4, 0.5, 45.0))

    def test_a_75_degree_error_drives_on_a_real_rover(self):
        linear, angular = rp.make_steering(False).command(50.0, 75.0)
        self.assertAlmostEqual(linear, 0.6 * math.cos(math.radians(75.0)))
        self.assertEqual(angular, 1.0)
        linear, angular = rp.make_steering(True).command(50.0, 75.0)
        self.assertEqual(linear, 0.0)   # the simulator default turns in place above 60
        self.assertEqual(angular, 0.6)


class CommandLineTests(unittest.TestCase):
    def test_real_rover_cli_uses_rover_steering(self):
        code, seen = run_main(["--sdk", "http://x"])
        self.assertEqual(code, 0)
        self.assertEqual(seen["steering"].max_angular, 1.0)
        self.assertEqual(seen["steering"].turn_in_place_deg, 90.0)

    def test_options_win_on_a_real_rover(self):
        code, seen = run_main(["--sdk", "http://x", "--cruise", "0.4", "--max-angular", "0.5",
                               "--turn-in-place", "45"])
        self.assertEqual(code, 0)
        s = seen["steering"]
        self.assertEqual((s.cruise, s.max_angular, s.turn_in_place_deg), (0.4, 0.5, 45.0))

    def test_simulator_cli_keeps_its_steering(self):
        code, seen = run_main(["--simulate"])
        self.assertEqual(code, 0)
        self.assertEqual(seen["steering"].max_angular, 0.6)
        self.assertEqual(seen["steering"].turn_in_place_deg, 60.0)


class ClosedLoopTests(unittest.TestCase):
    def test_real_like_left_turning_rover_flies_the_demo(self):
        # Moves like the recorded rovers (SIM_REAL, 30 deg/s per unit) and turns
        # left on a positive angular; driven the way the command line drives a
        # real rover without a calibration.
        sim = rp.SimRover(rp.DEMO_MISSION, seed=1, angular_sign=-1.0, max_yaw_dps=30.0,
                          **rp.SIM_REAL)
        res = rp.Pilot(sim, clock=sim.clock, sleep=sim.sleep,
                       steering=rp.make_steering(False),
                       conventions=rp.rover_conventions()).run(timeout_s=1500)
        self.assertTrue(res["ok"], res)
        self.assertEqual(res["reached"], [1, 2, 3, 4])


if __name__ == "__main__":
    unittest.main()
