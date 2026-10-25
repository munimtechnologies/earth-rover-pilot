# Copyright 2026 Munim, Inc. Licensed under the Apache License, Version 2.0.
"""0.15.0: on a real rover dead reckoning is on again by default, steered by
only while the GPS has no fresh fix (--dead-reckon-gaps), as pace_i.py's
pre-stated rule R1 says (studies/pace-i/GRADE.md). --dead-reckon steers by the
wheels whenever it can (v0.13.0's pilot) and --no-dead-reckon by the smoothed
GPS alone (v0.14.0's). The simulator and the Pilot class keep their defaults,
so earlier studies fly as before.

Run: python -m unittest test_bridge_default -v
"""
import contextlib
import io
import json
import os
import unittest
from unittest import mock

import dead_reckon as dm
import pace_h as ph
import pace_i as pi
import pace_study as ps
import rover_pilot as rp

HERE = os.path.dirname(os.path.abspath(__file__))
PACE_I_RUNS = os.path.join(HERE, "studies", "pace-i", "runs.jsonl")
# A short course with a right-angle corner, and a long straight that 15 s
# outages interrupt (test_pace_i.CORNER and test_pace_i.LONG).
CORNER = {"points": [(0.0, 0.0), (40.0, 0.0), (40.0, 40.0)], "checkpoints": [1, 2]}
LONG = {"points": [(0.0, 0.0), (400.0, 0.0)], "checkpoints": [1]}


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


def gaps_pilot(*args, **kw):
    """The release's own bridging, in place of pace_h.BridgePilot."""
    return rp.Pilot(*args, dead_reckon_gaps=True, **kw)


class DefaultTests(unittest.TestCase):
    def test_version(self):
        self.assertEqual(rp.__version__, "0.18.2")

    def test_real_rover_bridges_by_default(self):
        self.assertTrue(rp.use_dead_reckoning(None, simulate=False, gps_lag=0.0))
        self.assertTrue(rp.use_dead_reckon_gaps(False, None, True))

    def test_simulator_off_by_default(self):
        self.assertFalse(rp.use_dead_reckoning(None, simulate=True, gps_lag=0.0))
        self.assertFalse(rp.use_dead_reckon_gaps(False, None, False))

    def test_gps_lag_keeps_it_off(self):
        self.assertFalse(rp.use_dead_reckoning(None, simulate=False, gps_lag=1.5))

    def test_asked_for_dead_reckoning_steers_by_the_wheels(self):
        self.assertFalse(rp.use_dead_reckon_gaps(False, True, True))

    def test_asked_for_gaps(self):
        self.assertTrue(rp.use_dead_reckon_gaps(True, True, True))

    def test_pilot_class_unchanged(self):
        rover = rp.SimRover(rp.DEMO_MISSION, seed=2)
        pilot = rp.Pilot(rover, clock=rover.clock, sleep=rover.sleep,
                         dead_reckon=dm.DeadReckoner())
        self.assertFalse(pilot.dr_gaps_only)


class CommandLineTests(unittest.TestCase):
    def test_real_rover_flies_pace_i_bridge(self):
        # What pace_i.py's bridge+cf0.3 flies: the study's reckoner, the smoother
        # and bridging (with a 120 s reach since 0.16.0, test_reach_default.py).
        code, seen = built_with(["--sdk", "http://x"])
        self.assertEqual(code, 0)
        self.assertIsInstance(seen["rover"], rp.SdkClient)
        reckoner = seen["dead_reckon"]
        self.assertIsInstance(reckoner, dm.DeadReckoner)
        self.assertFalse(reckoner.use_course)
        self.assertEqual(reckoner.course_hold_s, 2.0)
        self.assertTrue(reckoner.fade)
        self.assertTrue(seen["dead_reckon_gaps"])
        self.assertIsInstance(seen["smooth_heading"], rp.HeadingSmoother)
        self.assertEqual(pi.VARIANTS["bridge+cf0.3"]["smooth"], rp.SMOOTH_HEADING)

    def test_dead_reckon_is_v0130s_pilot(self):
        code, seen = built_with(["--sdk", "http://x", "--dead-reckon"])
        self.assertEqual(code, 0)
        self.assertIsInstance(seen["dead_reckon"], dm.DeadReckoner)
        self.assertFalse(seen["dead_reckon_gaps"])

    def test_no_dead_reckon_is_v0140s_pilot(self):
        code, seen = built_with(["--sdk", "http://x", "--no-dead-reckon"])
        self.assertEqual(code, 0)
        self.assertIsNone(seen["dead_reckon"])
        self.assertFalse(seen["dead_reckon_gaps"])
        self.assertIsInstance(seen["smooth_heading"], rp.HeadingSmoother)

    def test_gaps_asked_on_a_real_rover(self):
        code, seen = built_with(["--sdk", "http://x", "--dead-reckon-gaps"])
        self.assertEqual(code, 0)
        self.assertIsInstance(seen["dead_reckon"], dm.DeadReckoner)
        self.assertTrue(seen["dead_reckon_gaps"])

    def test_gps_lag_on_a_real_rover(self):
        code, seen = built_with(["--sdk", "http://x", "--gps-lag", "1.5"])
        self.assertEqual(code, 0)
        self.assertIsNone(seen["dead_reckon"])
        self.assertFalse(seen["dead_reckon_gaps"])

    def test_simulator_unchanged(self):
        code, seen = built_with(["--simulate"])
        self.assertEqual(code, 0)
        self.assertIsNone(seen["dead_reckon"])
        self.assertFalse(seen["dead_reckon_gaps"])

    def test_help(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            with self.assertRaises(SystemExit):
                rp.main(["--help"])
        text = " ".join(out.getvalue().split())
        self.assertIn("(default: on for a real rover", text)
        self.assertIn("since v0.15.0", text)


class FliesAsTheStudyTests(unittest.TestCase):
    def test_gaps_fly_pace_i_bridge_through_outages(self):
        cases = [("corner", CORNER, "measured", 1), ("long", LONG, "outage15", 1),
                 ("long", LONG, "outage15", 2)]
        withheld = 0
        for name, course, profile, seed in cases:
            with self.subTest(course=name, profile=profile, seed=seed):
                want = pi.fly(name, seed, profile, "bridge+cf0.3", 0.8, course=course)
                with mock.patch.object(ph, "BridgePilot", gaps_pilot):
                    got = pi.fly(name, seed, profile, "bridge+cf0.3", 0.8, course=course)
                self.assertTrue(want["ok"], want["reason"])
                self.assertEqual(got, want)
                withheld += want["outage"]["withheld"]
        self.assertGreater(withheld, 0)

    @unittest.skipUnless(os.path.exists(PACE_I_RUNS), "studies/pace-i/runs.jsonl not here")
    def test_gaps_fly_a_sample_of_pace_i_exactly(self):
        # Seed 85 of pace_i.py's bridge+cf0.3 missions on every profile and course,
        # flown with the release's bridging, against pace-i-v1's own record.
        want = {}
        with open(PACE_I_RUNS, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    r = json.loads(line)
                    if r["variant"] == "bridge+cf0.3" and r["seed"] == 85:
                        want[(r["profile"], r["course"])] = r
        self.assertEqual(len(want), len(pi.PROFILES) * len(ps.COURSES))
        for (profile, course), ref in sorted(want.items()):
            with self.subTest(profile=profile, course=course):
                with mock.patch.object(ph, "BridgePilot", gaps_pilot):
                    got = pi.fly(course, 85, profile, "bridge+cf0.3", ref["cruise"])
                got.update(profile=profile, variant="bridge+cf0.3", cruise=ref["cruise"],
                           course=course, seed=85)
                got = json.loads(json.dumps(got))
                self.assertEqual(sorted(k for k in ref if got.get(k) != ref[k]), [])


if __name__ == "__main__":
    unittest.main()
