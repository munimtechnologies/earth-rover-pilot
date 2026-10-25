# Copyright 2026 Munim, Inc. Licensed under the Apache License, Version 2.0.
"""0.18.0: on a real rover the path follower (PathFollower) aims 16 m ahead
along its planned path instead of 8 m, as pace_n.py's pre-stated rule R2 says
(studies/pace-n/GRADE.md): `look16` was the only lookahead that was slower and
lost nowhere against 8 m and stayed within its limits on distance from the
course. The command line sets it (PATH_LOOKAHEAD_M); the simulator and the
PathFollower and Pilot classes keep 8 m, so earlier studies fly as before.

Run: python -m unittest test_lookahead_default -v
"""
import contextlib
import io
import json
import os
import unittest
from unittest import mock

import pace_m as pm
import pace_n as pn
import pace_study as ps
import rover_pilot as rp

HERE = os.path.dirname(os.path.abspath(__file__))
PACE_N_RUNS = os.path.join(HERE, "studies", "pace-n", "runs.jsonl")
# One right-angle path corner at (60, 0); the only checkpoint is the end
# (test_pace_n.CORNER60).
CORNER60 = {"points": [(0.0, 0.0), (60.0, 0.0), (60.0, 60.0)], "checkpoints": [2]}
PATH = [(37.0, -122.0), (37.001, -122.0)]


class FakePilot:
    """Stands in for rp.Pilot and keeps the last one main() built."""
    last = None

    def __init__(self, rover, **kw):
        self.kw = dict(kw, rover=rover)
        FakePilot.last = self

    def run(self, start=True, timeout_s=3600.0):
        return {"ok": True, "reason": "mission completed"}


def built(argv):
    out = io.StringIO()
    FakePilot.last = None
    with mock.patch.object(rp, "Pilot", FakePilot), contextlib.redirect_stdout(out):
        code = rp.main(argv)
    return code, FakePilot.last


@contextlib.contextmanager
def flying_with(lookahead_m):
    """While inside, every Pilot built (also by the studies) is given
    `lookahead_m` as the command line gives a real rover's."""
    init = rp.Pilot.__init__

    def patched(self, *args, **kw):
        init(self, *args, **kw)
        self.path_lookahead_m = lookahead_m

    with mock.patch.object(rp.Pilot, "__init__", patched):
        yield


def sim_pilot():
    rover = rp.SimRover(rp.DEMO_MISSION, seed=2)
    return rp.Pilot(rover, clock=rover.clock, sleep=rover.sleep,
                    planner=lambda lat, lon, clat, clon: list(PATH))


class DefaultTests(unittest.TestCase):
    def test_version(self):
        self.assertEqual(rp.__version__, "0.18.4")

    def test_lookahead_is_the_study_s(self):
        self.assertEqual(rp.PATH_LOOKAHEAD_M, 16.0)
        self.assertEqual(rp.PATH_LOOKAHEAD_M, pn.VARIANTS["look16"]["lookahead_m"])

    def test_class_defaults_unchanged(self):
        self.assertEqual(rp.PathFollower(PATH).lookahead_n, 4)
        self.assertEqual(sim_pilot().path_lookahead_m, 8.0)

    def test_pilot_plans_with_its_lookahead(self):
        pilot = sim_pilot()
        pilot._plan(0.0, 1, *PATH[1])
        self.assertIsInstance(pilot.path, rp.PathFollower)
        self.assertEqual(pilot.path.lookahead_n, 4)
        pilot = sim_pilot()
        pilot.path_lookahead_m = rp.PATH_LOOKAHEAD_M
        pilot._plan(0.0, 1, *PATH[1])
        self.assertEqual(pilot.path.lookahead_n, 8)
        # A failed plan still heads straight for the checkpoint.
        pilot.planner = lambda *a: None
        pilot._plan(1.0, 1, *PATH[1])
        self.assertIsNone(pilot.path)


class CommandLineTests(unittest.TestCase):
    def test_real_rover_gets_the_study_s_lookahead(self):
        code, pilot = built(["--sdk", "http://x"])
        self.assertEqual(code, 0)
        self.assertEqual(pilot.path_lookahead_m, 16.0)

    def test_with_other_real_rover_options(self):
        for extra in (["--no-dead-reckon"], ["--dead-reckon"], ["--no-smooth-heading"],
                      ["--marathon"]):
            with self.subTest(extra=extra):
                code, pilot = built(["--sdk", "http://x"] + extra)
                self.assertEqual(code, 0)
                self.assertEqual(pilot.path_lookahead_m, 16.0)
                self.assertEqual(pilot.heading.min_move_m, 20.0)

    def test_simulator_unchanged(self):
        for argv in (["--simulate"], ["--simulate", "--dead-reckon-gaps"],
                     ["--simulate", "--marathon"]):
            with self.subTest(argv=argv):
                code, pilot = built(argv)
                self.assertEqual(code, 0)
                self.assertFalse(hasattr(pilot, "path_lookahead_m"))


class FliesAsTheStudyTests(unittest.TestCase):
    def test_release_lookahead_flies_pace_n_look16(self):
        code, pilot = built(["--sdk", "http://x"])
        self.assertEqual(code, 0)
        for profile in ("outage90", "drift90"):
            with self.subTest(profile=profile):
                want = pn.fly("corner", 1, profile, "look16", 0.8, course=CORNER60)
                with flying_with(pilot.path_lookahead_m):
                    got = pm.fly("corner", 1, profile, pn.LEARNER, 0.8, course=CORNER60)
                self.assertTrue(want["ok"], want["reason"])
                want.pop("corner")
                self.assertEqual(got, want)
        # And it is not 8 m's mission.
        look8 = pn.fly("corner", 1, "drift90", "look8", 0.8, course=CORNER60)
        look8.pop("corner")
        self.assertNotEqual(got, look8)

    @unittest.skipUnless(os.path.exists(PACE_N_RUNS), "studies/pace-n/runs.jsonl not here")
    def test_release_lookahead_flies_a_sample_of_pace_n_exactly(self):
        # Seed 205 of pace_n.py's look16 missions on every profile and course,
        # flown with the lookahead the command line gives a real rover, against
        # pace-n-v1's own record (all but corner, which only the study records).
        want = {}
        with open(PACE_N_RUNS, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    r = json.loads(line)
                    if r["variant"] == "look16" and r["seed"] == 205:
                        want[(r["profile"], r["course"])] = r
        self.assertEqual(len(want), len(pn.PROFILES) * len(ps.COURSES))
        code, pilot = built(["--sdk", "http://x"])
        self.assertEqual(code, 0)
        for (profile, course), ref in sorted(want.items()):
            with self.subTest(profile=profile, course=course):
                with flying_with(pilot.path_lookahead_m):
                    got = pm.fly(course, 205, profile, pn.LEARNER, ref["cruise"])
                got.update(profile=profile, variant="look16", cruise=ref["cruise"],
                           course=course, seed=205)
                got = json.loads(json.dumps(got))
                self.assertEqual(sorted(k for k in ref if k != "corner" and got.get(k) != ref[k]),
                                 [])


if __name__ == "__main__":
    unittest.main()
