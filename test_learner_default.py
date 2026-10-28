# Copyright 2026 Munim, Inc. Licensed under the Apache License, Version 2.0.
"""0.17.0: on a real rover the compass-bias learner (HeadingEstimator) fits
its course over straight stretches of at least 20 m instead of 10 m, as
pace_m.py's pre-stated rule R2 says (studies/pace-m/GRADE.md): `long20` was
slower and lost on no course of any profile against the shipped learner and
faster on the most. The command line builds it (make_heading); the simulator
and the HeadingEstimator and Pilot classes keep their defaults, so earlier
studies fly as before.

Run: python -m unittest test_learner_default -v
"""
import contextlib
import io
import json
import os
import tempfile
import unittest
from unittest import mock

import pace_e as pe
import pace_l as pl
import pace_m as pm
import pace_study as ps
import rover_pilot as rp

HERE = os.path.dirname(os.path.abspath(__file__))
PACE_M_RUNS = os.path.join(HERE, "studies", "pace-m", "runs.jsonl")
# A long straight that 90 s outages interrupt (test_pace_k.FAR).
FAR = {"points": [(0.0, 0.0), (2000.0, 0.0)], "checkpoints": [1]}
# HeadingEstimator's settings (its constructor's arguments).
SETTINGS = ("min_move_m", "min_points", "min_speed_mps", "settle_s", "gain", "max_angular",
            "min_linear", "max_spread", "course_ttl_s", "max_residual_m", "weigh")


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


def settings(est):
    return {name: getattr(est, name) for name in SETTINGS}


@contextlib.contextmanager
def flying_with(learner):
    """While inside, pace_i.fly's learner is a CountingEstimator with
    `learner`'s settings, which decides exactly as `learner` does."""
    counting = pe.CountingEstimator

    def estimator():
        return counting(**settings(learner))

    with mock.patch.object(pe, "CountingEstimator", estimator):
        yield


class DefaultTests(unittest.TestCase):
    def test_version(self):
        self.assertEqual(rp.__version__, "0.19.0")

    def test_learner_is_the_study_s(self):
        self.assertEqual(rp.HEADING_LEARNER, {"min_move_m": 20.0})
        self.assertEqual(rp.HEADING_LEARNER, pm.VARIANTS["long20"])

    def test_class_defaults_unchanged(self):
        est = rp.HeadingEstimator()
        self.assertEqual(est.min_move_m, 10.0)
        self.assertEqual(est.gain, 0.3)

    def test_make_heading(self):
        h = rp.make_heading(rp.rover_conventions())
        self.assertIsInstance(h, rp.HeadingEstimator)
        self.assertEqual(settings(h), settings(rp.HeadingEstimator(min_move_m=20.0)))
        self.assertEqual(h.bias, 0.0)
        self.assertEqual(rp.make_heading().bias, 0.0)
        self.assertEqual(rp.make_heading(rp.Conventions(bias_deg=-12.5)).bias, -12.5)


class CommandLineTests(unittest.TestCase):
    def test_real_rover_gets_the_study_s_learner(self):
        code, pilot = built(["--sdk", "http://x"])
        self.assertEqual(code, 0)
        self.assertIsInstance(pilot.heading, rp.HeadingEstimator)
        self.assertEqual(settings(pilot.heading),
                         settings(rp.HeadingEstimator(**pm.VARIANTS["long20"])))
        self.assertEqual(pilot.heading.min_move_m, 20.0)
        self.assertEqual(pilot.heading.gain, 0.3)
        self.assertEqual(pilot.heading.bias, 0.0)

    def test_with_other_real_rover_options(self):
        for extra in (["--no-dead-reckon"], ["--dead-reckon"], ["--no-smooth-heading"],
                      ["--marathon"]):
            with self.subTest(extra=extra):
                code, pilot = built(["--sdk", "http://x"] + extra)
                self.assertEqual(code, 0)
                self.assertEqual(pilot.heading.min_move_m, 20.0)

    def test_a_calibration_s_bias_is_the_start(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "rover.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"ok": True, "angular_right_positive": False, "bias_deg": 12.0}, f)
            code, pilot = built(["--sdk", "http://x", "--calibration", path])
        self.assertEqual(code, 0)
        self.assertEqual(pilot.heading.bias, 12.0)
        self.assertEqual(pilot.heading.min_move_m, 20.0)

    def test_simulator_unchanged(self):
        for argv in (["--simulate"], ["--simulate", "--dead-reckon-gaps"],
                     ["--simulate", "--marathon"]):
            with self.subTest(argv=argv):
                code, pilot = built(argv)
                self.assertEqual(code, 0)
                self.assertFalse(hasattr(pilot, "heading"))

    def test_pilot_class_unchanged(self):
        rover = rp.SimRover(rp.DEMO_MISSION, seed=2)
        pilot = rp.Pilot(rover, clock=rover.clock, sleep=rover.sleep)
        self.assertEqual(pilot.heading.min_move_m, 10.0)
        pilot = rp.Pilot(rover, clock=rover.clock, sleep=rover.sleep,
                         conventions=rp.Conventions(bias_deg=5.0))
        self.assertEqual(pilot.heading.bias, 5.0)
        self.assertEqual(pilot.heading.min_move_m, 10.0)


class FliesAsTheStudyTests(unittest.TestCase):
    def test_release_learner_flies_pace_m_long20(self):
        code, pilot = built(["--sdk", "http://x"])
        self.assertEqual(code, 0)
        calibrations = 0
        for seed in (1, 2):
            with self.subTest(seed=seed):
                want = pm.fly("far", seed, "drift90", "long20", 0.8, course=FAR)
                with flying_with(pilot.heading):
                    got = pl.fly("far", seed, "drift90", pm.FLOWN_AS, 0.8, course=FAR)
                self.assertTrue(want["ok"], want["reason"])
                want.pop("fit_err")
                self.assertEqual(got, want)
                calibrations += want["learner"]["calibrations"]
        self.assertGreater(calibrations, 0)

    @unittest.skipUnless(os.path.exists(PACE_M_RUNS), "studies/pace-m/runs.jsonl not here")
    def test_release_learner_flies_a_sample_of_pace_m_exactly(self):
        # Seed 181 of pace_m.py's long20 missions on every profile and course,
        # flown with the learner the command line builds, against pace-m-v1's
        # own record (all but fit_err, which only the study's learner records).
        want = {}
        with open(PACE_M_RUNS, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    r = json.loads(line)
                    if r["variant"] == "long20" and r["seed"] == 181:
                        want[(r["profile"], r["course"])] = r
        self.assertEqual(len(want), len(pm.PROFILES) * len(ps.COURSES))
        code, pilot = built(["--sdk", "http://x"])
        self.assertEqual(code, 0)
        for (profile, course), ref in sorted(want.items()):
            with self.subTest(profile=profile, course=course):
                with flying_with(pilot.heading):
                    got = pl.fly(course, 181, profile, pm.FLOWN_AS, ref["cruise"])
                got.update(profile=profile, variant="long20", cruise=ref["cruise"],
                           course=course, seed=181)
                got = json.loads(json.dumps(got))
                self.assertEqual(sorted(k for k in ref if k != "fit_err" and got.get(k) != ref[k]),
                                 [])


if __name__ == "__main__":
    unittest.main()
