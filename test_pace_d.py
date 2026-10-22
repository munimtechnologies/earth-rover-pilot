"""Tests for the study of compass errors that last (hard iron, slow drift).

Run: python -m unittest test_pace_d -v
"""

import io
import json
import math
import os
import random
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pace_b as pb  # noqa: E402
import pace_c as pc  # noqa: E402
import pace_d as pd  # noqa: E402
import pace_study as ps  # noqa: E402
import rover_pilot as rp  # noqa: E402

CPS = [(40.0, 0.0)]


def rover(seed=1, **kw):
    return pd.DistortedRover(CPS, seed=seed, **dict(pd.PROFILES["measured"], **kw))


class RoverTests(unittest.TestCase):
    def test_undistorted_reports_as_measured(self):
        a = pb.MeasuredRover(CPS, seed=4, **pb.PROFILES["measured"])
        b = pd.DistortedRover(CPS, seed=4, **pd.PROFILES["measured"])
        self.assertEqual(a.data(), b.data())
        a.sleep(5.0)
        b.sleep(5.0)
        self.assertEqual(a.data(), b.data())

    def test_hard_iron_follows_the_heading(self):
        r = rover(hard_iron_deg=10.0)
        r.heading = 90.0 - r.phase_deg
        self.assertAlmostEqual(r.compass_error, -15.0, places=9)
        r.heading = 270.0 - r.phase_deg
        self.assertAlmostEqual(r.compass_error, -35.0, places=9)
        r.heading = -r.phase_deg
        self.assertAlmostEqual(r.compass_error, -25.0, places=9)

    def test_hard_iron_moves_the_report(self):
        # Same seed, same draws: the reports differ by the hard-iron term alone,
        # at the starting heading of 200 deg.
        a = pb.MeasuredRover(CPS, seed=3, **pb.PROFILES["measured"])
        b = pd.DistortedRover(CPS, seed=3, **pd.PROFILES["hardiron20"])
        want = 20.0 * math.sin(math.radians(200.0 + b.phase_deg))
        self.assertAlmostEqual(rp.wrap180(b.data()["orientation"] - a.data()["orientation"]),
                               want, places=6)
        self.assertEqual(a.data()["latitude"], b.data()["latitude"])

    def test_phase_and_drift_from_their_own_generator(self):
        g = random.Random("pace-d-3")
        phase = g.uniform(0.0, 360.0)
        d0 = g.gauss(0.0, 10.0)
        z = g.gauss(0.0, 1.0)
        r = rover(seed=3, drift_deg=10.0, drift_tau_s=120.0)
        self.assertEqual(r.phase_deg, phase)
        self.assertEqual(r.drift, d0)
        r.sleep(0.5)
        self.assertEqual(r.drift, d0)  # stepped every 1 s
        r.sleep(0.5)
        a = math.exp(-1.0 / 120.0)
        self.assertAlmostEqual(r.drift, a * d0 + 10.0 * math.sqrt(1.0 - a * a) * z, places=12)
        self.assertAlmostEqual(r.compass_error, -25.0 + r.drift, places=12)

    def test_no_drift_without_drift(self):
        r = rover(seed=2, hard_iron_deg=10.0)
        r.sleep(3.0)
        self.assertEqual(r.drift, 0.0)


class SetupTests(unittest.TestCase):
    def test_profiles(self):
        self.assertIs(pd.PROFILES["measured"], pb.PROFILES["measured"])
        self.assertIs(pd.PROFILES["measured-noise10"], pb.PROFILES["measured-noise10"])
        for name, extra in (("hardiron10", {"hard_iron_deg": 10.0}),
                            ("hardiron20", {"hard_iron_deg": 20.0}),
                            ("drift10", {"drift_deg": 10.0, "drift_tau_s": 120.0})):
            self.assertEqual(pd.PROFILES[name], dict(pb.PROFILES["measured"], **extra))
        self.assertEqual(pd.BASE_PROFILE, "measured")

    def test_variants(self):
        self.assertEqual(list(pd.VARIANTS), ["shipped", "cf0.3"])
        self.assertIsNone(pd.VARIANTS["shipped"])
        self.assertEqual(pd.VARIANTS["cf0.3"], rp.SMOOTH_HEADING)
        self.assertEqual(pd.VARIANTS["cf0.3"], pc.VARIANTS["cf0.3"])
        self.assertEqual(pd.CRUISES, (0.7, 0.8))


class FlyTests(unittest.TestCase):
    COURSE = {"points": [(0.0, 0.0), (40.0, 0.0), (40.0, 40.0)], "checkpoints": [1, 2]}

    def same_as_pace_c(self, profile, variant, seed):
        want = pc.fly("corner", seed, profile, variant, 0.8, course=self.COURSE)
        got = pd.fly("corner", seed, profile, variant, 0.8, course=self.COURSE)
        self.assertTrue(want["ok"], want)
        self.assertEqual({k: got[k] for k in want}, want)
        self.assertEqual(set(got) - set(want), {"heading_err"})
        return got

    def test_shipped_flies_as_pace_c(self):
        self.same_as_pace_c("measured", "shipped", 1)
        self.same_as_pace_c("measured-noise10", "shipped", 2)

    def test_smoothed_flies_as_pace_c(self):
        self.same_as_pace_c("measured", "cf0.3", 1)
        self.same_as_pace_c("measured-noise10", "cf0.3", 2)

    def test_heading_error_recorded(self):
        got = self.same_as_pace_c("measured", "shipped", 3)
        h = got["heading_err"]
        self.assertGreater(h["n"], 10)
        self.assertGreater(h["rms_deg"], 0.0)
        self.assertLess(h["median_abs_deg"], 90.0)

    def test_distorted_short_course(self):
        for profile in ("hardiron20", "drift10"):
            for variant in ("shipped", "cf0.3"):
                with self.subTest(profile=profile, variant=variant):
                    r = pd.fly("corner", 1, profile, variant, 0.8, course=self.COURSE)
                    self.assertTrue(r["ok"], r["reason"])
                    self.assertEqual(r["reached"], 2)
                    self.assertGreater(r["heading_err"]["n"], 0)


class StatsTests(unittest.TestCase):
    def test_heading_stats(self):
        self.assertEqual(pd.heading_stats([-3.0, 1.0, 2.0]),
                         {"n": 3, "median_abs_deg": 2.0, "rms_deg": 2.16, "mean_deg": 0.0})
        self.assertEqual(pd.heading_stats([]),
                         {"n": 0, "median_abs_deg": None, "rms_deg": None, "mean_deg": None})


def run(profile, variant, cruise, course, seed, elapsed, ok=True, med=2.0, rms=3.0):
    return {"ok": ok, "reason": "mission completed" if ok else "timeout",
            "elapsed_s": elapsed, "reached": 4, "checkpoints": 4, "reports": 4,
            "recoveries": 0, "plans": 4, "route_m": 1000.0, "travelled_m": 1010.0,
            "made_good_mps": 1000.0 / elapsed, "ideal_mps": 1.0,
            "efficiency": 1000.0 / elapsed,
            "time_s": {"driving": elapsed, "turning": 0.0, "stopped": 0.0, "reversing": 0.0},
            "heading_err": {"n": 100, "median_abs_deg": med, "rms_deg": rms, "mean_deg": 0.0},
            "profile": profile, "variant": variant, "cruise": cruise, "course": course,
            "seed": seed}


class SummaryTests(unittest.TestCase):
    def runs(self):
        return [run("measured", "shipped", 0.8, "blocks", 1, 1000.0, med=2.0, rms=3.0),
                run("measured", "shipped", 0.8, "blocks", 2, 1100.0, med=4.0, rms=5.0),
                run("hardiron10", "shipped", 0.8, "blocks", 1, 1010.0),
                run("hardiron10", "shipped", 0.8, "blocks", 2, 1120.0),
                run("hardiron10", "cf0.3", 0.8, "blocks", 1, 1000.0),
                run("hardiron10", "cf0.3", 0.8, "blocks", 2, 1100.0)]

    def test_profile_effects(self):
        effects, tallies = pd.profile_effects(self.runs())
        # hardiron10/cf0.3 has no measured/cf0.3 to be compared with.
        self.assertEqual(len(effects), 1)
        e = effects[0]
        self.assertEqual((e["profile"], e["variant"], e["against"], e["faster"], e["slower"]),
                         ("hardiron10", "shipped", "measured", 0, 2))
        self.assertEqual(e["median_time_diff_s"], 15.0)
        # +15 s against measured's median of 1050 s.
        self.assertEqual(e["median_time_diff_share"], 0.0143)
        self.assertEqual(tallies, [{"profile": "hardiron10", "variant": "shipped",
                                    "against": "measured", "groups": 1, "groups_faster": 0,
                                    "groups_slower": 0, "groups_lost": 0, "groups_gained": 0,
                                    "largest_median_diff_share": 0.0143}])

    def test_heading_rows(self):
        rows = pd.heading_rows(self.runs())
        m = [r for r in rows if (r["profile"], r["variant"]) == ("measured", "shipped")]
        self.assertEqual(m, [{"profile": "measured", "variant": "shipped", "cruise": 0.8,
                              "course": "blocks", "missions": 2, "median_abs_deg": 3.0,
                              "rms_deg": 4.0}])

    def test_check_against(self):
        runs = self.runs()
        ref = [dict(r) for r in runs if r["profile"] == "measured"]
        for r in ref:
            del r["heading_err"]
        ref[1]["elapsed_s"] = 1101.0
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "runs.jsonl")
            with open(path, "w", encoding="utf-8") as f:
                for r in ref[1:]:
                    f.write(json.dumps(r) + "\n")
                f.write("\n")
            out = pd.check_against(runs, path)
        self.assertEqual((out["compared"], out["identical"], out["missing"]), (1, 0, 1))
        self.assertEqual(out["different"][0]["fields"], ["elapsed_s"])
        self.assertEqual(out["different"][0]["seed"], 2)

    def test_write_outputs(self):
        class Args:
            seeds = 2
        with tempfile.TemporaryDirectory() as d:
            pd.write_outputs(d, self.runs(), 0.0, Args, True)
            with open(os.path.join(d, "summary.json")) as f:
                out = json.load(f)
            self.assertEqual(out["runs"], 6)
            self.assertEqual(out["completed"], 6)
            self.assertIsNone(out["check"])
            self.assertEqual(out["profile_tallies"][0]["largest_median_diff_share"], 0.0143)
            with open(os.path.join(d, "report.md")) as f:
                md = f.read()
            self.assertIn("| hardiron10 | shipped | 0/1 | 0 | 0 | 0 | 0.0143 |", md)
            self.assertIn("| measured | shipped | 0.8 | blocks | 2 | 3.0 | 4.0 |", md)

    def test_main_small(self):
        course = {"points": [(0.0, 0.0), (30.0, 0.0)], "checkpoints": [1]}
        saved = dict(ps.COURSES)
        ps.COURSES.clear()
        ps.COURSES["tiny"] = course
        try:
            with tempfile.TemporaryDirectory() as d, redirect_stdout(io.StringIO()):
                pd.main(["--out-dir", d, "--seeds", "1", "--cruises", "1.0",
                         "--profiles", "hardiron10", "--variants", "cf0.3"])
                with open(os.path.join(d, "summary.json")) as f:
                    out = json.load(f)
            # measured and shipped are always flown: 2 profiles x 2 variants.
            self.assertEqual(out["runs"], 4)
            self.assertTrue(out["done"])
            self.assertEqual(sorted((r["profile"], r["variant"]) for r in out["overview"]),
                             [("hardiron10", "cf0.3"), ("hardiron10", "shipped"),
                              ("measured", "cf0.3"), ("measured", "shipped")])
        finally:
            ps.COURSES.clear()
            ps.COURSES.update(saved)


if __name__ == "__main__":
    unittest.main()
