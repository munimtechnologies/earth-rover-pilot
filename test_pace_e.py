"""Tests for the study of what the compass-bias learner does under noise.

Run: python -m unittest test_pace_e -v
"""

import io
import json
import os
import random
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pace_b as pb  # noqa: E402
import pace_d as pd  # noqa: E402
import pace_e as pe  # noqa: E402
import pace_study as ps  # noqa: E402
import rover_pilot as rp  # noqa: E402

LAT0, LON0 = 37.8719, -122.2585


def drive(est, ticks, noise_deg=2.0, seed=1, angular=None, linear=None, fixes=True):
    """Feed an estimator a rover driving east at 1 m/s: 10 ticks a second, a fix
    every 2 s, the compass reading 90 deg plus noise."""
    g = random.Random(seed)
    for k in range(ticks):
        t = round(k * 0.1, 1)
        fix = rp.offset_latlon(LAT0, LON0, 0.0, t) if fixes and k % 20 == 0 else None
        compass = (90.0 + g.gauss(0.0, noise_deg)) % 360.0
        est.update(t, fix, compass, 0.5 if linear is None else linear(k),
                   0.0 if angular is None else angular(k))
    return est


class EstimatorTests(unittest.TestCase):
    def test_decides_as_the_plain_estimator(self):
        a = drive(rp.HeadingEstimator(), 300)
        b = drive(pe.CountingEstimator(), 300)
        self.assertGreaterEqual(b.calibrations, 1)
        self.assertEqual((a.bias, a.calibrations, a.last_fit), (b.bias, b.calibrations, b.last_fit))
        self.assertGreaterEqual(b.fits, b.spread_checked)
        self.assertEqual(b.spread_checked, b.calibrations)
        self.assertEqual(b.spread_rejected, 0)
        self.assertEqual(len(b.spreads), b.spread_checked)
        self.assertTrue(all(s > 0.985 for s in b.spreads))

    def test_counts_the_spread_test_turning_fits_down(self):
        a = drive(rp.HeadingEstimator(), 300, noise_deg=20.0)
        b = drive(pe.CountingEstimator(), 300, noise_deg=20.0)
        self.assertEqual((a.bias, a.calibrations), (b.bias, b.calibrations))
        self.assertEqual(b.calibrations, 0)
        self.assertGreaterEqual(b.spread_checked, 1)
        self.assertEqual(b.spread_rejected, b.spread_checked)
        self.assertTrue(all(s < 0.985 for s in b.spreads))

    def test_counts_broken_stretches(self):
        # Straight for 5 s, a hard turn for 2 s, straight again (the low-passed
        # command falls back within 0.1 after 1.1 s), then stopped: two breaks.
        b = drive(pe.CountingEstimator(), 130, fixes=False,
                  angular=lambda k: 1.0 if 50 <= k < 70 else 0.0,
                  linear=lambda k: 0.0 if k >= 120 else 0.5)
        self.assertEqual(b.breaks, 2)
        self.assertEqual(b.fits, 0)

    def test_variant_settings(self):
        for name, want in (("shipped", (0.985, 0.1)), ("cf0.3", (0.985, 0.1)),
                           ("spread0.95", (0.95, 0.1)), ("straight0.3", (0.985, 0.3)),
                           ("both", (0.95, 0.3))):
            with self.subTest(variant=name):
                est = pe.make_estimator(name)
                self.assertIsInstance(est, pe.CountingEstimator)
                self.assertEqual((est.max_spread, est.max_angular), want)


class SetupTests(unittest.TestCase):
    def test_profiles(self):
        m = pb.PROFILES["measured"]
        self.assertIs(pe.PROFILES["measured"], m)
        self.assertIs(pe.PROFILES["measured-noise10"], pb.PROFILES["measured-noise10"])
        self.assertIs(pe.PROFILES["drift10"], pd.PROFILES["drift10"])
        for name, deg in (("noise6", 6.0), ("noise8", 8.0), ("noise12", 12.0)):
            self.assertEqual(pe.PROFILES[name], dict(m, compass_noise_deg=deg))
        rover = pd.DistortedRover([(40.0, 0.0)], seed=1, **pe.PROFILES["noise6"])
        self.assertEqual(rover.compass_noise_deg, 6.0)
        self.assertEqual(pe.BASE_PROFILE, "measured")

    def test_variants(self):
        self.assertEqual(list(pe.VARIANTS), ["shipped", "cf0.3", "spread0.95", "straight0.3",
                                             "both"])
        self.assertEqual(pe.VARIANTS["cf0.3"]["smooth"], rp.SMOOTH_HEADING)
        self.assertEqual(pe.BASE_VARIANT, "shipped")
        self.assertEqual(pe.CRUISES, (0.8,))


class GeometryTests(unittest.TestCase):
    def test_course_offset(self):
        pts = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0)]
        self.assertAlmostEqual(pe.course_offset(pts, 5.0, 3.0), 3.0, places=9)
        self.assertAlmostEqual(pe.course_offset(pts, 12.0, 5.0), 2.0, places=9)
        self.assertAlmostEqual(pe.course_offset(pts, 10.0, 4.0), 0.0, places=9)

    def test_offset_stats(self):
        self.assertEqual(pe.offset_stats([4.0, 1.0, 100.0, 2.0, 3.0]),
                         {"n": 5, "median_m": 3.0, "p95_m": 4.0, "max_m": 100.0})
        self.assertEqual(pe.offset_stats([]),
                         {"n": 0, "median_m": None, "p95_m": None, "max_m": None})


class FlyTests(unittest.TestCase):
    COURSE = {"points": [(0.0, 0.0), (40.0, 0.0), (40.0, 40.0)], "checkpoints": [1, 2]}

    def same_as_pace_d(self, profile, variant, seed):
        want = pd.fly("corner", seed, profile, variant, 0.8, course=self.COURSE)
        got = pe.fly("corner", seed, profile, variant, 0.8, course=self.COURSE)
        self.assertTrue(want["ok"], want)
        self.assertEqual({k: got[k] for k in want}, want)
        self.assertEqual(set(got) - set(want), {"learner", "offset"})
        return got

    def test_flies_as_pace_d(self):
        self.same_as_pace_d("measured", "shipped", 1)
        self.same_as_pace_d("measured-noise10", "cf0.3", 2)
        self.same_as_pace_d("drift10", "shipped", 1)

    def test_learner_and_offset_recorded(self):
        got = self.same_as_pace_d("measured", "shipped", 3)
        x = got["learner"]
        self.assertGreaterEqual(x["fits"], x["spread_checked"])
        self.assertGreaterEqual(x["spread_checked"], x["spread_rejected"])
        # Without the residual gate, a fit is used exactly when it passes the spread test.
        self.assertEqual(x["calibrations"], x["spread_checked"] - x["spread_rejected"])
        self.assertGreater(got["offset"]["n"], 10)
        self.assertLess(got["offset"]["median_m"], 20.0)

    def test_loosened_variants_fly(self):
        for variant in ("spread0.95", "straight0.3", "both"):
            with self.subTest(variant=variant):
                r = pe.fly("corner", 1, "measured-noise10", variant, 0.8, course=self.COURSE)
                self.assertTrue(r["ok"], r["reason"])
                self.assertEqual(r["reached"], 2)
                self.assertIsNotNone(r["learner"])


def run(profile, variant, course, seed, elapsed, learner, offset, ok=True):
    return {"ok": ok, "reason": "mission completed" if ok else "timeout",
            "elapsed_s": elapsed, "reached": 4, "checkpoints": 4, "reports": 4,
            "recoveries": 0, "plans": 4, "route_m": 1000.0, "travelled_m": 1010.0,
            "made_good_mps": 1000.0 / elapsed, "ideal_mps": 1.0,
            "efficiency": 1000.0 / elapsed,
            "time_s": {"driving": elapsed, "turning": 0.0, "stopped": 0.0, "reversing": 0.0},
            "heading_err": {"n": 100, "median_abs_deg": 2.0, "rms_deg": 3.0, "mean_deg": 0.0},
            "learner": learner, "offset": offset,
            "profile": profile, "variant": variant, "cruise": 0.8, "course": course,
            "seed": seed}


L1 = {"calibrations": 0, "breaks": 30, "fits": 4, "spread_checked": 2, "spread_rejected": 2,
      "median_spread": 0.98, "bias_deg": 0.0, "bias_error_deg": -25.0}
L2 = {"calibrations": 3, "breaks": 10, "fits": 6, "spread_checked": 4, "spread_rejected": 1,
      "median_spread": 0.99, "bias_deg": 26.0, "bias_error_deg": 1.0}
O1 = {"n": 10, "median_m": 1.0, "p95_m": 3.0, "max_m": 4.0}
O2 = {"n": 10, "median_m": 2.0, "p95_m": 5.0, "max_m": 6.0}


class SummaryTests(unittest.TestCase):
    def runs(self):
        return [run("measured", "shipped", "blocks", 1, 1000.0, L1, O1),
                run("measured", "shipped", "blocks", 2, 1100.0, L2, O2),
                run("measured", "shipped", "blocks", 3, 1200.0, None, pe.offset_stats([]),
                    ok=False),
                run("measured", "both", "blocks", 1, 1000.0, L2, O1),
                run("noise6", "shipped", "blocks", 1, 1050.0, L1, O2)]

    def test_learner_rows(self):
        rows = pe.learner_rows(self.runs())
        m = [r for r in rows if (r["profile"], r["variant"]) == ("measured", "shipped")]
        self.assertEqual(len(m), 1)
        m = m[0]
        self.assertEqual((m["missions"], m["median_calibrations"], m["zero_calibration_missions"],
                          m["fits_per_mission"], m["spread_checked_per_mission"],
                          m["spread_rejected_share"], m["median_breaks"],
                          m["median_abs_bias_error_deg"]),
                         (2, 1.5, 1, 5.0, 3.0, 0.5, 20.0, 13.0))
        self.assertAlmostEqual(m["median_spread"], 0.985, places=4)

    def test_offset_rows(self):
        rows = pe.offset_rows(self.runs())
        m = [r for r in rows if (r["profile"], r["variant"]) == ("measured", "shipped")]
        self.assertEqual(m, [{"profile": "measured", "variant": "shipped", "cruise": 0.8,
                              "course": "blocks", "missions": 2, "median_offset_m": 1.5,
                              "p95_offset_m": 4.0}])

    def test_check_against(self):
        runs = self.runs()
        ref = dict(runs[1])
        del ref["learner"], ref["offset"]
        ref["elapsed_s"] = 1101.0
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "runs.jsonl")
            with open(path, "w", encoding="utf-8") as f:
                f.write(json.dumps(ref) + "\n\n")
            out = pe.check_against(runs, path)
        # Seeds 1-3 of measured/shipped are checked (1 and 3 are not in the
        # reference); "both" and noise6 are not.
        self.assertEqual((out["compared"], out["identical"], out["missing"]), (1, 0, 2))
        self.assertEqual(out["different"][0]["fields"], ["elapsed_s"])
        self.assertEqual(out["different"][0]["seed"], 2)

    def test_main_small(self):
        course = {"points": [(0.0, 0.0), (30.0, 0.0)], "checkpoints": [1]}
        saved = dict(ps.COURSES)
        ps.COURSES.clear()
        ps.COURSES["tiny"] = course
        try:
            with tempfile.TemporaryDirectory() as d, redirect_stdout(io.StringIO()):
                pe.main(["--out-dir", d, "--seeds", "1", "--profiles", "noise6",
                         "--variants", "both"])
                with open(os.path.join(d, "summary.json")) as f:
                    out = json.load(f)
                with open(os.path.join(d, "report.md")) as f:
                    md = f.read()
            # measured and shipped are always flown: 2 profiles x 2 variants.
            self.assertEqual(out["runs"], 4)
            self.assertTrue(out["done"])
            self.assertEqual(len(out["learner"]), 4)
            self.assertEqual(len(out["offset"]), 4)
            self.assertEqual(sorted((r["profile"], r["variant"]) for r in out["overview"]),
                             [("measured", "both"), ("measured", "shipped"),
                              ("noise6", "both"), ("noise6", "shipped")])
            self.assertIn("## The learner", md)
            self.assertIsNone(out["check"])
        finally:
            ps.COURSES.clear()
            ps.COURSES.update(saved)


if __name__ == "__main__":
    unittest.main()
