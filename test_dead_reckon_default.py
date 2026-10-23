# Copyright 2026 Munim, Inc. Licensed under the Apache License, Version 2.0.
"""0.14.0 (its real-rover default changed again in 0.15.0, test_bridge_default.py):
dead reckoning off by default on a real rover too, as pace_h.py's
pre-stated rule R3 says (studies/pace-h/GRADE.md), and --dead-reckon-gaps,
dead reckoning steered by only while the GPS has no fresh fix (pace_h.py's
bridge+cf0.3), off unless asked. The Pilot class keeps steering by the
wheels whenever dead reckoning has an estimate, so earlier studies fly as before.

Run: python -m unittest test_dead_reckon_default -v
"""
import contextlib
import io
import json
import os
import unittest
from unittest import mock

import dead_reckon as dm
import pace_h as ph
import pace_study as ps
import rover_pilot as rp

HERE = os.path.dirname(os.path.abspath(__file__))
PACE_H_RUNS = os.path.join(HERE, "studies", "pace-h", "runs.jsonl")
# A short course with a right-angle corner (test_pace_h.CORNER), and a long
# straight on which the reckoner is trusted before the end (test_pace_h.LONG).
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


def run_main(argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = rp.main(argv)
    return code, out.getvalue()


def gaps_pilot(*args, **kw):
    """The release's own bridging, in place of pace_h.BridgePilot."""
    return rp.Pilot(*args, dead_reckon_gaps=True, **kw)


class DefaultTests(unittest.TestCase):
    def test_real_rover_on_by_default(self):
        # 0.15.0: on again, steered by only through GPS gaps (test_bridge_default.py).
        self.assertTrue(rp.use_dead_reckoning(None, simulate=False, gps_lag=0.0))

    def test_simulator_off_by_default(self):
        self.assertFalse(rp.use_dead_reckoning(None, simulate=True, gps_lag=0.0))

    def test_explicit_choice_wins(self):
        self.assertTrue(rp.use_dead_reckoning(True, simulate=False, gps_lag=0.0))
        self.assertFalse(rp.use_dead_reckoning(False, simulate=False, gps_lag=0.0))

    def test_pilot_class_steers_by_the_wheels_whenever_it_can(self):
        rover = rp.SimRover(rp.DEMO_MISSION, seed=2)
        pilot = rp.Pilot(rover, clock=rover.clock, sleep=rover.sleep,
                         dead_reckon=dm.DeadReckoner())
        self.assertFalse(pilot.dr_gaps_only)


class _Gps:
    def __init__(self, fresh):
        self.fresh = fresh
        self.lat, self.lon, self.raw = 3.0, 4.0, (3.0, 4.0)

    def has_fix(self, t):
        return self.fresh


class _Reckoner:
    def __init__(self, pos):
        self.pos = pos
        self.asked = 0

    def position(self, t):
        self.asked += 1
        return self.pos


class PositionTests(unittest.TestCase):
    def pilot(self, fresh, pos, gaps):
        p = rp.Pilot.__new__(rp.Pilot)
        p.gps, p.dr, p.lag, p.dr_gaps_only = _Gps(fresh), _Reckoner(pos), None, gaps
        return p

    def test_gaps_only_uses_the_gps_while_it_has_a_fix(self):
        p = self.pilot(True, (1.0, 2.0), True)
        self.assertEqual(p._position(10.0), (3.0, 4.0))
        self.assertEqual(p.dr.asked, 1)

    def test_gaps_only_uses_the_wheels_through_a_gap(self):
        self.assertEqual(self.pilot(False, (1.0, 2.0), True)._position(10.0), (1.0, 2.0))

    def test_gaps_only_without_an_estimate(self):
        self.assertEqual(self.pilot(False, None, True)._position(10.0), (3.0, 4.0))

    def test_default_uses_the_wheels_whenever_it_can(self):
        self.assertEqual(self.pilot(True, (1.0, 2.0), False)._position(10.0), (1.0, 2.0))

    def test_same_choice_as_pace_h(self):
        for fresh in (True, False):
            for pos in ((1.0, 2.0), None):
                with self.subTest(fresh=fresh, pos=pos):
                    b = ph.BridgePilot.__new__(ph.BridgePilot)
                    b.gps, b.dr, b.lag = _Gps(fresh), _Reckoner(pos), None
                    self.assertEqual(self.pilot(fresh, pos, True)._position(10.0),
                                     b._position(10.0))


class CommandLineTests(unittest.TestCase):
    def test_no_dead_reckon_on_a_real_rover(self):
        # v0.14.0's real-rover pilot.
        code, seen = built_with(["--sdk", "http://x", "--no-dead-reckon"])
        self.assertEqual(code, 0)
        self.assertIsInstance(seen["rover"], rp.SdkClient)
        self.assertIsNone(seen["dead_reckon"])
        self.assertFalse(seen["dead_reckon_gaps"])
        self.assertIsInstance(seen["smooth_heading"], rp.HeadingSmoother)

    def test_dead_reckon_on_a_real_rover(self):
        code, seen = built_with(["--sdk", "http://x", "--dead-reckon"])
        self.assertEqual(code, 0)
        self.assertIsInstance(seen["dead_reckon"], dm.DeadReckoner)
        self.assertFalse(seen["dead_reckon_gaps"])

    def test_dead_reckon_gaps_on_a_real_rover(self):
        code, seen = built_with(["--sdk", "http://x", "--dead-reckon-gaps"])
        self.assertEqual(code, 0)
        self.assertIsInstance(seen["dead_reckon"], dm.DeadReckoner)
        self.assertTrue(seen["dead_reckon_gaps"])
        self.assertIsInstance(seen["smooth_heading"], rp.HeadingSmoother)

    def test_gaps_not_with_no_dead_reckon_or_gps_lag(self):
        for extra in (["--no-dead-reckon"], ["--gps-lag", "1.5"]):
            with self.subTest(extra=extra):
                with contextlib.redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit):
                        rp.main(["--simulate", "--dead-reckon-gaps"] + extra)

    def test_gaps_in_the_simulator(self):
        code, text = run_main(["--simulate", "--sim-real", "--dead-reckon-gaps",
                               "--smooth-heading", "--seed", "2"])
        self.assertEqual(code, 0, text[-500:])
        self.assertIn('"dead_reckon"', text)

    def test_help(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            with self.assertRaises(SystemExit):
                rp.main(["--help"])
        text = " ".join(out.getvalue().split())
        self.assertIn("--dead-reckon-gaps", text)
        self.assertIn("--no-dead-reckon", text)
        self.assertIn("(default: on for a real rover", text)


class FliesAsTheStudyTests(unittest.TestCase):
    def test_gaps_fly_pace_h_bridge_on_short_courses(self):
        cases = [("corner", CORNER, profile, seed)
                 for profile in ("measured", "dropout0.3") for seed in (1, 2)]
        cases.append(("long", LONG, "dropout0.3", 1))
        bridged = 0
        for name, course, profile, seed in cases:
            with self.subTest(course=name, profile=profile, seed=seed):
                want = ph.fly(name, seed, profile, "bridge+cf0.3", 0.8, course=course)
                with mock.patch.object(ph, "BridgePilot", gaps_pilot):
                    got = ph.fly(name, seed, profile, "bridge+cf0.3", 0.8, course=course)
                self.assertTrue(want["ok"], want["reason"])
                self.assertEqual(got, want)
                bridged += want["dead_reckon"]["bridged_s"] > 0
        self.assertGreater(bridged, 0)

    @unittest.skipUnless(os.path.exists(PACE_H_RUNS), "studies/pace-h/runs.jsonl not here")
    def test_gaps_fly_a_sample_of_pace_h_exactly(self):
        # Seed 61 of pace_h.py's bridge+cf0.3 missions on every profile and course,
        # flown with the release's bridging, against pace-h-v1's own record.
        want = {}
        with open(PACE_H_RUNS, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    r = json.loads(line)
                    if r["variant"] == "bridge+cf0.3" and r["seed"] == 61:
                        want[(r["profile"], r["course"])] = r
        self.assertEqual(len(want), len(ph.PROFILES) * len(ps.COURSES))
        for (profile, course), ref in sorted(want.items()):
            with self.subTest(profile=profile, course=course):
                with mock.patch.object(ph, "BridgePilot", gaps_pilot):
                    got = ph.fly(course, 61, profile, "bridge+cf0.3", ref["cruise"])
                got.update(profile=profile, variant="bridge+cf0.3", cruise=ref["cruise"],
                           course=course, seed=61)
                got = json.loads(json.dumps(got))
                self.assertEqual(sorted(k for k in ref if got.get(k) != ref[k]), [])


if __name__ == "__main__":
    unittest.main()
