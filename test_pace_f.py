"""Tests for the study of whether --smooth-heading should be on by default.

Run: python -m unittest test_pace_f -v
"""

import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pace_b as pb  # noqa: E402
import pace_d as pd  # noqa: E402
import pace_e as pe  # noqa: E402
import pace_f as pf  # noqa: E402
import pace_study as ps  # noqa: E402
import rover_pilot as rp  # noqa: E402

TINY = {"points": [(0.0, 0.0), (30.0, 0.0)], "checkpoints": [1]}


class tiny_courses:
    """Replace pace_study's courses with one short course while in use."""

    def __enter__(self):
        self.saved = dict(ps.COURSES)
        ps.COURSES.clear()
        ps.COURSES["tiny"] = TINY

    def __exit__(self, *exc):
        ps.COURSES.clear()
        ps.COURSES.update(self.saved)


class SetupTests(unittest.TestCase):
    def test_profiles(self):
        m = pb.PROFILES["measured"]
        self.assertEqual(list(pf.PROFILES),
                         ["measured", "noise4", "noise5", "noise6", "yaw32", "yaw64", "lag1.0",
                          "yaw32-noise8", "yaw64-noise8", "bias60", "bias60-noise8"])
        self.assertIs(pf.PROFILES["measured"], m)
        self.assertIs(pf.PROFILES["noise6"], pe.PROFILES["noise6"])
        want = {"noise4": {"compass_noise_deg": 4.0}, "noise5": {"compass_noise_deg": 5.0},
                "yaw32": {"max_yaw_dps": 32.0}, "yaw64": {"max_yaw_dps": 64.0},
                "lag1.0": {"latency_s": 1.0},
                "yaw32-noise8": {"max_yaw_dps": 32.0, "compass_noise_deg": 8.0},
                "yaw64-noise8": {"max_yaw_dps": 64.0, "compass_noise_deg": 8.0},
                "bias60": {"compass_error_deg": -60.0},
                "bias60-noise8": {"compass_error_deg": -60.0, "compass_noise_deg": 8.0}}
        for name, change in want.items():
            with self.subTest(profile=name):
                self.assertEqual(pf.PROFILES[name], dict(m, **change))
        self.assertEqual(pf.BASE_PROFILE, "measured")

    def test_rovers_get_the_settings(self):
        r = pd.DistortedRover([(40.0, 0.0)], seed=1, **pf.PROFILES["bias60-noise8"])
        self.assertEqual((r.compass_error, r.compass_noise_deg), (-60.0, 8.0))
        r = pd.DistortedRover([(40.0, 0.0)], seed=1, **pf.PROFILES["yaw32"])
        self.assertEqual((r.max_yaw_dps, r.compass_error, r.compass_noise_deg), (32.0, -25.0, 3.0))
        r = pd.DistortedRover([(40.0, 0.0)], seed=1, **pf.PROFILES["lag1.0"])
        self.assertEqual((r.latency_s, r.max_yaw_dps), (1.0, 48.0))

    def test_variants(self):
        self.assertEqual(list(pf.VARIANTS), ["shipped", "cf0.3"])
        self.assertEqual(pf.VARIANTS["cf0.3"], {"smooth": rp.SMOOTH_HEADING})
        # The same as pace_e.py's, so pace_e.make_estimator builds the plain learner.
        for name in pf.VARIANTS:
            self.assertEqual(pf.VARIANTS[name], pe.VARIANTS[name])
        self.assertEqual(pf.BASE_VARIANT, "shipped")
        self.assertEqual(pf.CRUISES, (0.8,))
        self.assertEqual(pf.FIRST_SEED, 13)


class FlyTests(unittest.TestCase):
    COURSE = {"points": [(0.0, 0.0), (40.0, 0.0), (40.0, 40.0)], "checkpoints": [1, 2]}

    def test_flies_as_pace_e(self):
        for profile, variant, seed in (("measured", "shipped", 1), ("noise6", "cf0.3", 2)):
            with self.subTest(profile=profile, variant=variant):
                want = pe.fly("corner", seed, profile, variant, 0.8, course=self.COURSE)
                got = pf.fly("corner", seed, profile, variant, 0.8, course=self.COURSE)
                self.assertTrue(want["ok"], want["reason"])
                self.assertEqual(got, want)

    def test_new_profiles_fly(self):
        for profile in ("yaw32", "yaw64", "lag1.0"):
            for variant in pf.VARIANTS:
                with self.subTest(profile=profile, variant=variant):
                    r = pf.fly("corner", 1, profile, variant, 0.8, course=self.COURSE)
                    self.assertTrue(r["ok"], r["reason"])
                    self.assertEqual(r["reached"], 2)
                    self.assertIsNotNone(r["learner"])

    def test_bias60_is_flown_with_its_error(self):
        r = pf.fly("corner", 1, "bias60", "shipped", 0.8, course=self.COURSE)
        self.assertEqual(r["checkpoints"], 2)
        self.assertGreater(r["offset"]["n"], 0)
        # bias_error_deg is the learned bias plus the -60 deg error (both rounded
        # to 0.01, so they may differ by one step).
        self.assertAlmostEqual(r["learner"]["bias_error_deg"],
                               rp.wrap180(r["learner"]["bias_deg"] - 60.0), delta=0.011)

    def test_failed_run_fields(self):
        r = pf.failed_run(ValueError("boom"))
        self.assertFalse(r["ok"])
        self.assertEqual(r["reason"], "ValueError: boom")
        self.assertIsNone(r["learner"])
        self.assertEqual(r["offset"]["n"], 0)


class CheckTests(unittest.TestCase):
    def test_check_against_pace_e(self):
        with tiny_courses():
            ref = []
            for seed in (1, 2):
                r = pe.fly("tiny", seed, "measured", "shipped", 0.8)
                r.update(profile="measured", variant="shipped", cruise=0.8, course="tiny",
                         seed=seed)
                ref.append(r)
            ref[1]["elapsed_s"] += 1.0
            with tempfile.TemporaryDirectory() as d:
                path = os.path.join(d, "runs.jsonl")
                with open(path, "w", encoding="utf-8") as f:
                    for r in ref:
                        f.write(json.dumps(r) + "\n")
                    f.write("\n")
                out = pf.check_pace_e(path)
        # 2 profiles x 2 variants x 1 course x 3 seeds = 12 missions checked; the
        # reference has 2 of them, and seed 2 was altered.
        self.assertEqual((out["compared"], out["identical"], out["missing"]), (2, 1, 10))
        self.assertEqual(len(out["different"]), 1)
        self.assertEqual(out["different"][0]["seed"], 2)
        self.assertEqual(out["different"][0]["fields"], ["elapsed_s"])


class SummaryTests(unittest.TestCase):
    def test_offset_diffs(self):
        offsets = [{"profile": "measured", "variant": "shipped", "cruise": 0.8, "course": "blocks",
                    "missions": 2, "median_offset_m": 1.5, "p95_offset_m": 4.0},
                   {"profile": "measured", "variant": "cf0.3", "cruise": 0.8, "course": "blocks",
                    "missions": 2, "median_offset_m": 1.25, "p95_offset_m": 3.0},
                   {"profile": "yaw32", "variant": "cf0.3", "cruise": 0.8, "course": "blocks",
                    "missions": 2, "median_offset_m": 1.0, "p95_offset_m": 3.0}]
        # yaw32 has no shipped row, so it gets no difference.
        self.assertEqual(pf.offset_diffs(offsets),
                         [{"profile": "measured", "variant": "cf0.3", "cruise": 0.8,
                           "course": "blocks", "diff_m": -0.25}])

    def test_table(self):
        self.assertEqual(pf._table(["a", "b"], [(1, None)]),
                         ["| a | b |", "|---|---|", "| 1 | None |"])

    def test_main_small(self):
        with tiny_courses():
            with tempfile.TemporaryDirectory() as d, redirect_stdout(io.StringIO()):
                pf.main(["--out-dir", d, "--first-seed", "13", "--seeds", "2",
                         "--profiles", "yaw64", "--variants", "cf0.3"])
                with open(os.path.join(d, "summary.json")) as f:
                    out = json.load(f)
                with open(os.path.join(d, "report.md")) as f:
                    md = f.read()
                with open(os.path.join(d, "runs.jsonl")) as f:
                    lines = [json.loads(x) for x in f if x.strip()]
        # measured and shipped are always flown: 2 profiles x 2 variants x 2 seeds.
        self.assertEqual(out["runs"], 8)
        self.assertEqual(out["seeds"], [13, 14])
        self.assertEqual(sorted({r["seed"] for r in lines}), [13, 14])
        self.assertTrue(out["done"])
        self.assertEqual(len(out["learner"]), 4)
        self.assertEqual(len(out["offset"]), 4)
        self.assertEqual(len(out["offset_diff"]), 2)
        self.assertEqual(sorted((v["profile"], v["variant"]) for v in out["verdicts"]),
                         [("measured", "cf0.3"), ("yaw64", "cf0.3")])
        self.assertIsNone(out["check"])
        self.assertIn("## The learner", md)
        self.assertIn("Seeds 13-14.", md)


if __name__ == "__main__":
    unittest.main()
