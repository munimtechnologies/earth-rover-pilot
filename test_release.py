# Copyright 2026 Munim, Inc. Licensed under the Apache License, Version 2.0.
"""0.11.0 release settings: dead reckoning on by default for a real rover, along
the compass-corrected heading (dead_reckon_study.py), holding the fresh GPS course
for 2 s after each fix and fading the difference out over 2 s more, as
frodo_blend_b.py's pre-stated rule says (studies/frodo-blend-b/GRADE.md)."""
import contextlib
import io
import unittest
from unittest import mock

import dead_reckon as dm
import rover_pilot as rp

SETTING = {"use_course": False, "course_hold_s": 2.0, "fade": True}


def run_main(argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = rp.main(argv)
    return code, out.getvalue()


class Recorder(dm.DeadReckoner):
    """DeadReckoner that remembers the settings main() built it with."""
    made = []

    def __init__(self, **kw):
        Recorder.made.append(kw)
        super().__init__(**kw)


class DefaultTest(unittest.TestCase):
    def test_version(self):
        self.assertEqual(rp.__version__, "0.12.0")
        self.assertEqual(dm.__version__, "0.2.0")

    def test_study_setting(self):
        self.assertEqual(rp.DEAD_RECKON, SETTING)

    def test_setting_builds_a_hold(self):
        dr = dm.DeadReckoner(**rp.DEAD_RECKON)
        self.assertFalse(dr.use_course)
        self.assertEqual(dr.course_hold_s, 2.0)
        self.assertTrue(dr.fade)

    def test_real_rover_on_by_default(self):
        self.assertTrue(rp.use_dead_reckoning(None, simulate=False, gps_lag=0.0))

    def test_simulator_off_by_default(self):
        self.assertFalse(rp.use_dead_reckoning(None, simulate=True, gps_lag=0.0))

    def test_gps_lag_keeps_it_off(self):
        self.assertFalse(rp.use_dead_reckoning(None, simulate=False, gps_lag=1.5))

    def test_explicit_choice_wins(self):
        self.assertFalse(rp.use_dead_reckoning(False, simulate=False, gps_lag=0.0))
        self.assertTrue(rp.use_dead_reckoning(True, simulate=True, gps_lag=0.0))


class CommandLineTest(unittest.TestCase):
    def setUp(self):
        Recorder.made = []

    def test_simulator_default_has_no_dead_reckoning(self):
        code, text = run_main(["--simulate", "--seed", "2"])
        self.assertEqual(code, 0, text[-500:])
        self.assertNotIn('"dead_reckon"', text)

    def test_no_dead_reckon_flag(self):
        code, text = run_main(["--simulate", "--no-dead-reckon", "--seed", "2"])
        self.assertEqual(code, 0, text[-500:])
        self.assertNotIn('"dead_reckon"', text)

    def test_dead_reckon_uses_the_heading_and_the_hold(self):
        with mock.patch.object(dm, "DeadReckoner", Recorder):
            code, text = run_main(["--simulate", "--sim-real", "--dead-reckon", "--seed", "2"])
        self.assertEqual(code, 0, text[-500:])
        self.assertEqual(Recorder.made, [SETTING])
        self.assertIn('"dead_reckon"', text)

    def test_mps_per_rpm_passed_on(self):
        with mock.patch.object(dm, "DeadReckoner", Recorder):
            code, text = run_main(["--simulate", "--sim-real", "--dead-reckon",
                                   "--mps-per-rpm", "0.00668", "--seed", "2"])
        self.assertEqual(code, 0, text[-500:])
        self.assertEqual(Recorder.made, [{**SETTING, "mps_per_rpm": 0.00668}])

    def test_gps_lag_alone_still_allowed(self):
        code, text = run_main(["--simulate", "--sim-real", "--gps-lag", "1.5", "--seed", "2"])
        self.assertEqual(code, 0, text[-500:])
        self.assertNotIn('"dead_reckon"', text)

    def test_help_mentions_the_default(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            with self.assertRaises(SystemExit):
                rp.main(["--help"])
        self.assertIn("--no-dead-reckon", out.getvalue())
        self.assertIn("on for a real rover", " ".join(out.getvalue().split()))


if __name__ == "__main__":
    unittest.main()
