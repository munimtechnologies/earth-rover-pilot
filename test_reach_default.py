# Copyright 2026 Munim, Inc. Licensed under the Apache License, Version 2.0.
"""0.16.0: on a real rover the bridging reckoner (--dead-reckon-gaps, the
default since 0.15.0) carries the position up to 120 s after the last fix
instead of 30 s, as pace_k.py's pre-stated rules R1 and R2 say
(studies/pace-k/GRADE.md). --dead-reckon (steering by the wheels whenever it
can) keeps dead_reckon.py's 30 s, which pace_k.py did not fly. The simulator
and the Pilot class keep their defaults, so earlier studies fly as before.

Run: python -m unittest test_reach_default -v
"""
import contextlib
import io
import json
import os
import unittest
from unittest import mock

import dead_reckon as dm
import pace_h as ph
import pace_k as pk
import pace_study as ps
import rover_pilot as rp

HERE = os.path.dirname(os.path.abspath(__file__))
PACE_K_RUNS = os.path.join(HERE, "studies", "pace-k", "runs.jsonl")
# A long straight that 90 s outages interrupt (test_pace_k.FAR).
FAR = {"points": [(0.0, 0.0), (2000.0, 0.0)], "checkpoints": [1]}
# Settings the command line's reckoner must share with the study's.
SAME = ("max_s", "keep_s", "use_course", "course_hold_s", "fade", "prior", "gps_lag_s", "gain",
        "trust_after", "hold_s")


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


def study_reckoner():
    """bridge120+cf0.3's reckoner as pace_i.fly builds it."""
    return dm.DeadReckoner(**dict(rp.DEAD_RECKON, **pk.VARIANTS["bridge120+cf0.3"]["reckoner"]))


class DefaultTests(unittest.TestCase):
    def test_version(self):
        self.assertEqual(rp.__version__, "0.18.4")

    def test_reach_is_the_study_s(self):
        self.assertEqual(rp.BRIDGE_MAX_S, 120.0)
        self.assertEqual(pk.VARIANTS["bridge120+cf0.3"]["reckoner"], {"max_s": rp.BRIDGE_MAX_S})

    def test_dead_reckon_settings_unchanged(self):
        self.assertNotIn("max_s", rp.DEAD_RECKON)
        self.assertEqual(dm.DeadReckoner(**rp.DEAD_RECKON).max_s, 30.0)


class CommandLineTests(unittest.TestCase):
    def test_real_rover_bridges_with_the_study_s_reckoner(self):
        code, seen = built_with(["--sdk", "http://x"])
        self.assertEqual(code, 0)
        self.assertTrue(seen["dead_reckon_gaps"])
        reckoner = seen["dead_reckon"]
        self.assertIsInstance(reckoner, dm.DeadReckoner)
        self.assertEqual(reckoner.max_s, 120.0)
        study = study_reckoner()
        for name in SAME:
            self.assertEqual(getattr(reckoner, name), getattr(study, name), name)
        self.assertIsInstance(seen["smooth_heading"], rp.HeadingSmoother)

    def test_gaps_asked_on_a_real_rover(self):
        code, seen = built_with(["--sdk", "http://x", "--dead-reckon-gaps"])
        self.assertEqual(code, 0)
        self.assertTrue(seen["dead_reckon_gaps"])
        self.assertEqual(seen["dead_reckon"].max_s, 120.0)

    def test_dead_reckon_keeps_30_s(self):
        code, seen = built_with(["--sdk", "http://x", "--dead-reckon"])
        self.assertEqual(code, 0)
        self.assertFalse(seen["dead_reckon_gaps"])
        self.assertEqual(seen["dead_reckon"].max_s, 30.0)

    def test_mps_per_rpm_with_the_reach(self):
        code, seen = built_with(["--sdk", "http://x", "--mps-per-rpm", "0.00668"])
        self.assertEqual(code, 0)
        self.assertEqual(seen["dead_reckon"].max_s, 120.0)
        self.assertEqual(seen["dead_reckon"].prior, 0.00668)

    def test_gaps_in_the_simulator(self):
        code, seen = built_with(["--simulate", "--dead-reckon-gaps"])
        self.assertEqual(code, 0)
        self.assertEqual(seen["dead_reckon"].max_s, 120.0)

    def test_simulator_and_no_dead_reckon_unchanged(self):
        for argv in (["--simulate"], ["--sdk", "http://x", "--no-dead-reckon"]):
            with self.subTest(argv=argv):
                code, seen = built_with(argv)
                self.assertEqual(code, 0)
                self.assertIsNone(seen["dead_reckon"])
                self.assertFalse(seen["dead_reckon_gaps"])

    def test_pilot_class_unchanged(self):
        rover = rp.SimRover(rp.DEMO_MISSION, seed=2)
        pilot = rp.Pilot(rover, clock=rover.clock, sleep=rover.sleep,
                         dead_reckon=dm.DeadReckoner())
        self.assertFalse(pilot.dr_gaps_only)

    def test_help(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            with self.assertRaises(SystemExit):
                rp.main(["--help"])
        text = " ".join(out.getvalue().split())
        self.assertIn("up to 120 s after the last fix", text)
        self.assertIn("since v0.16.0", text)


class FliesAsTheStudyTests(unittest.TestCase):
    def test_gaps_fly_pace_k_bridge120_through_90_s_outages(self):
        withheld = 0
        for seed in (1, 2, 3):
            with self.subTest(seed=seed):
                want = pk.fly("far", seed, "outage90", "bridge120+cf0.3", 0.8, course=FAR)
                with mock.patch.object(ph, "BridgePilot", gaps_pilot):
                    got = pk.fly("far", seed, "outage90", "bridge120+cf0.3", 0.8, course=FAR)
                self.assertTrue(want["ok"], want["reason"])
                self.assertEqual(got, want)
                withheld += want["outage"]["withheld"]
        self.assertGreater(withheld, 0)

    @unittest.skipUnless(os.path.exists(PACE_K_RUNS), "studies/pace-k/runs.jsonl not here")
    def test_gaps_fly_a_sample_of_pace_k_exactly(self):
        # Seed 133 of pace_k.py's bridge120+cf0.3 missions on every profile and
        # course, flown with the release's bridging, against pace-k-v1's own record.
        want = {}
        with open(PACE_K_RUNS, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    r = json.loads(line)
                    if r["variant"] == "bridge120+cf0.3" and r["seed"] == 133:
                        want[(r["profile"], r["course"])] = r
        self.assertEqual(len(want), len(pk.PROFILES) * len(ps.COURSES))
        for (profile, course), ref in sorted(want.items()):
            with self.subTest(profile=profile, course=course):
                with mock.patch.object(ph, "BridgePilot", gaps_pilot):
                    got = pk.fly(course, 133, profile, "bridge120+cf0.3", ref["cruise"])
                got.update(profile=profile, variant="bridge120+cf0.3", cruise=ref["cruise"],
                           course=course, seed=133)
                got = json.loads(json.dumps(got))
                self.assertEqual(sorted(k for k in ref if got.get(k) != ref[k]), [])


if __name__ == "__main__":
    unittest.main()
