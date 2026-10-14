"""Tests for the conventions the pilot assumes on a real, uncalibrated rover.

Run: python -m unittest test_rover_defaults -v
"""

import io
import json
import os
import sys
import tempfile
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


class RoverDefaultsTests(unittest.TestCase):
    def test_positive_angular_turns_left(self):
        c = rp.rover_conventions()
        self.assertFalse(c.angular_right_positive)
        self.assertEqual(c.angular(0.5), -0.5)   # a right turn is sent as a negative angular
        self.assertEqual(c.angular(-0.3), 0.3)
        self.assertAlmostEqual(c.heading(90), 90)
        self.assertIsNone(c.bias_deg)

    def test_class_defaults_still_match_the_simulator(self):
        c = rp.Conventions()
        self.assertTrue(c.angular_right_positive)
        self.assertEqual(c.angular(0.5), 0.5)

    def test_real_rover_cli_uses_the_rover_defaults(self):
        code, seen = run_main(["--sdk", "http://x"])
        self.assertEqual(code, 0)
        self.assertIsInstance(seen["rover"], rp.SdkClient)
        self.assertFalse(seen["conventions"].angular_right_positive)

    def test_a_calibration_wins_over_the_defaults(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "rover.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"ok": True, "orientation_scale": 256.0, "orientation_clockwise": True,
                           "angular_right_positive": True, "bias_deg": 12.0}, f)
            code, seen = run_main(["--sdk", "http://x", "--calibration", path])
        self.assertEqual(code, 0)
        self.assertTrue(seen["conventions"].angular_right_positive)
        self.assertEqual(seen["conventions"].orientation_scale, 256.0)
        self.assertEqual(seen["conventions"].bias_deg, 12.0)

    def test_simulator_keeps_its_own_defaults(self):
        code, seen = run_main(["--simulate"])
        self.assertEqual(code, 0)
        self.assertIsInstance(seen["rover"], rp.SimRover)
        self.assertIsNone(seen["conventions"])

    def test_left_turning_sim_rover_flies_the_mission_with_them(self):
        # The same rover that goes nowhere without conventions
        # (test_left_turning_rover_without_conventions_goes_nowhere).
        sim = rp.SimRover(rp.DEMO_MISSION, seed=1, angular_sign=-1.0)
        res = rp.Pilot(sim, clock=sim.clock, sleep=sim.sleep,
                       conventions=rp.rover_conventions()).run(timeout_s=1500)
        self.assertTrue(res["ok"], res)
        self.assertEqual(res["reached"], [1, 2, 3, 4])


if __name__ == "__main__":
    unittest.main()
