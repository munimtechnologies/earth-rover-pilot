# Copyright 2026 Munim, Inc. Licensed under the Apache License, Version 2.0.
"""0.13.0: --smooth-heading on by default for a real rover, as pace_f.py's
pre-stated rule F1 says (studies/pace-f/GRADE.md). The simulator and the Pilot
class keep it off unless asked, so earlier studies fly as before.

Run: python -m unittest test_smooth_default -v
"""
import contextlib
import io
import json
import os
import tempfile
import unittest
from unittest import mock

import pace_f as pf
import rover_pilot as rp

# A short course with a right-angle corner (test_smooth_heading.CORNER).
CORNER = {"points": [(0.0, 0.0), (40.0, 0.0), (40.0, 40.0)], "checkpoints": [1, 2]}
CALIBRATION = {"ok": True, "orientation_scale": 360.0, "orientation_clockwise": True,
               "angular_right_positive": True, "bias_deg": 0.0, "yaw_dps_at_full": 55.0}


class FakePilot:
    """Stands in for rp.Pilot and records what main() built it with."""
    seen = {}

    def __init__(self, rover, **kw):
        FakePilot.seen = dict(kw, rover=rover)

    def run(self, start=True, timeout_s=3600.0):
        return {"ok": True, "reason": "mission completed"}


def built_with(argv):
    out = io.StringIO()
    with mock.patch.object(rp, "Pilot", FakePilot), contextlib.redirect_stdout(out):
        code = rp.main(argv)
    return code, FakePilot.seen


def run_main(argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = rp.main(argv)
    return code, out.getvalue()


class DefaultTests(unittest.TestCase):
    def test_real_rover_on_by_default(self):
        self.assertTrue(rp.use_smooth_heading(None, simulate=False))

    def test_simulator_off_by_default(self):
        self.assertFalse(rp.use_smooth_heading(None, simulate=True))

    def test_explicit_choice_wins(self):
        self.assertFalse(rp.use_smooth_heading(False, simulate=False))
        self.assertTrue(rp.use_smooth_heading(True, simulate=True))

    def test_pilot_class_keeps_it_off(self):
        rover = rp.SimRover(rp.DEMO_MISSION, seed=2)
        self.assertIsNone(rp.Pilot(rover, clock=rover.clock, sleep=rover.sleep).smoother)

    def test_setting_is_the_studys(self):
        self.assertEqual(rp.SMOOTH_HEADING, pf.VARIANTS["cf0.3"]["smooth"])


class CommandLineTests(unittest.TestCase):
    def test_real_rover_gets_the_smoother(self):
        code, seen = built_with(["--sdk", "http://x"])
        self.assertEqual(code, 0)
        self.assertIsInstance(seen["rover"], rp.SdkClient)
        self.assertIsInstance(seen["smooth_heading"], rp.HeadingSmoother)
        self.assertEqual(seen["smooth_heading"].stats(),
                         {"gain": 0.3, "yaw_dps": 48.0, "lag_s": 0.5, "readings": 0})

    def test_no_smooth_heading_on_a_real_rover(self):
        code, seen = built_with(["--sdk", "http://x", "--no-smooth-heading"])
        self.assertEqual(code, 0)
        self.assertIsNone(seen["smooth_heading"])

    def test_calibrated_rate_on_a_real_rover(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "rover.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(CALIBRATION, f)
            code, seen = built_with(["--sdk", "http://x", "--calibration", path])
        self.assertEqual(code, 0)
        self.assertEqual(seen["smooth_heading"].yaw_dps, 55.0)

    def test_simulator_only_when_asked(self):
        code, seen = built_with(["--simulate"])
        self.assertEqual(code, 0)
        self.assertIsNone(seen["smooth_heading"])
        code, seen = built_with(["--simulate", "--smooth-heading"])
        self.assertEqual(code, 0)
        self.assertIsInstance(seen["smooth_heading"], rp.HeadingSmoother)

    def test_no_smooth_heading_in_the_simulator(self):
        code, text = run_main(["--simulate", "--seed", "2", "--no-smooth-heading"])
        self.assertEqual(code, 0, text[-500:])
        self.assertNotIn('"smooth_heading"', text)

    def test_with_dead_reckoning(self):
        # A real rover's defaults together: dead reckoning and the smoother.
        code, text = run_main(["--simulate", "--sim-real", "--dead-reckon", "--smooth-heading",
                               "--seed", "2"])
        self.assertEqual(code, 0, text[-500:])
        res = json.loads(text)
        self.assertIn("dead_reckon", res)
        self.assertGreater(res["smooth_heading"]["readings"], 100)

    def test_help(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            with self.assertRaises(SystemExit):
                rp.main(["--help"])
        text = " ".join(out.getvalue().split())
        self.assertIn("--no-smooth-heading", text)
        self.assertIn("one, otherwise 48 deg/s per unit of angular (default: on for a real "
                      "rover, off in the simulator)", text)


class FliesAsTheStudyTests(unittest.TestCase):
    def test_command_line_smoother_flies_pace_f_cf03(self):
        # The smoother main() now builds for a real rover has to fly pace_f.py's
        # cf0.3 missions exactly (rule F1).
        for profile in ("measured", "noise6", "yaw32"):
            for seed in (13, 14):
                with self.subTest(profile=profile, seed=seed):
                    want = pf.fly("corner", seed, profile, "cf0.3", 0.8, course=CORNER)
                    code, seen = built_with(["--sdk", "http://x"])
                    self.assertEqual(code, 0)
                    cli = seen["smooth_heading"]
                    asked = []

                    def make(**kw):
                        asked.append(kw)
                        return cli

                    with mock.patch.object(rp, "HeadingSmoother", make):
                        got = pf.fly("corner", seed, profile, "cf0.3", 0.8, course=CORNER)
                    self.assertTrue(want["ok"], want)
                    self.assertEqual(asked, [rp.SMOOTH_HEADING])
                    self.assertGreater(cli.readings, 10)
                    self.assertEqual(got, want)


if __name__ == "__main__":
    unittest.main()
