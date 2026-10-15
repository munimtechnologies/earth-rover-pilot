"""Tests for the time-correlated GPS error study.

Run: python -m unittest test_gps_noise_study -v
"""

import io
import json
import math
import os
import random
import statistics
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import gps_noise_study as gns  # noqa: E402
import rover_pilot as rp  # noqa: E402


def run(noise, variant, seed, elapsed, ok=True, mission="demo", credit=5.0, profile="zero"):
    return {"ok": ok, "reason": "mission completed" if ok else "timeout",
            "elapsed_s": elapsed if ok else None, "reached": 4 if ok else 1, "checkpoints": 4,
            "reports": 5 if ok else 1, "recoveries": 0, "travelled_m": 250.0,
            "calibrations": 3, "bias_err_deg": 2.0,
            "credited_true_m": [credit] * (4 if ok else 1), "profile": profile,
            "noise": noise, "variant": variant, "mission": mission, "seed": seed}


def lag1(xs):
    m = statistics.fmean(xs)
    num = sum((a - m) * (b - m) for a, b in zip(xs, xs[1:]))
    return num / sum((a - m) ** 2 for a in xs)


class NoiseTests(unittest.TestCase):
    def test_gauss_markov_keeps_sigma_and_correlation(self):
        rng = random.Random(7)
        phi = math.exp(-1.0 / 15.0)
        err = (rng.gauss(0, 2.0), rng.gauss(0, 2.0))
        xs = []
        for _ in range(20000):
            err = gns.gauss_markov_step(rng, err, 2.0, phi)
            xs.append(err[0])
        self.assertLess(abs(statistics.pstdev(xs) - 2.0), 0.24)
        self.assertLess(abs(lag1(xs) - phi), 0.02)

    def test_phi_zero_is_white_noise(self):
        rng = random.Random(8)
        err = (0.0, 0.0)
        xs = []
        for _ in range(20000):
            err = gns.gauss_markov_step(rng, err, 3.0, 0.0)
            xs.append(err[1])
        self.assertLess(abs(statistics.pstdev(xs) - 3.0), 0.15)
        self.assertLess(abs(lag1(xs)), 0.03)

    def test_tau_zero_is_the_plain_simulator(self):
        a = rp.SimRover(rp.DEMO_MISSION, seed=3, **rp.SIM_REAL)
        b = gns.CorrelatedGpsRover(rp.DEMO_MISSION, seed=3, gps_noise_tau_s=0.0, **rp.SIM_REAL)
        self.assertEqual(a.gps, b.gps)
        for _ in range(60):
            for sim in (a, b):
                sim.control(0.5, 0.2)
                sim.sleep(1.0)
            self.assertEqual(a.gps, b.gps)
            self.assertEqual(a.data(), b.data())

    def _steps(self, tau):
        sim = gns.CorrelatedGpsRover(rp.DEMO_MISSION, seed=5, gps_noise_m=3.0,
                                     gps_noise_tau_s=tau, gps_dropout=0.0)
        fixes = [sim.gps]
        for _ in range(120):
            sim.sleep(1.0)  # standing still, no commands
            fixes.append(sim.gps)
        return statistics.fmean(rp.haversine_m(*p, *q) for p, q in zip(fixes, fixes[1:]))

    def test_correlated_error_moves_slowly(self):
        white, drift = self._steps(0.0), self._steps(60.0)
        self.assertGreater(white, 3.0)  # about 5.3 m between independent fixes
        self.assertLess(drift, 0.3 * white)  # about 0.7 m with T = 60 s


class FlyTests(unittest.TestCase):
    def test_baseline_flies_the_demo_and_records_credits(self):
        r = gns.fly("demo", 1, gns.BASE_NOISE, gns.BASE_VARIANT, 1500.0)
        self.assertTrue(r["ok"], r)
        self.assertEqual(r["reached"], 4)
        self.assertEqual(len(r["credited_true_m"]), 4)
        for d in r["credited_true_m"]:
            self.assertLess(d, 25.0)
        if r["calibrations"]:
            self.assertTrue(0.0 <= r["bias_err_deg"] <= 180.0)
        else:
            self.assertIsNone(r["bias_err_deg"])

    def test_variant_settings_reach_the_pilot(self):
        self.assertEqual(gns.VARIANTS[gns.BASE_VARIANT],
                         {"alpha": rp.GpsFilter().alpha, "report_radius_m": 10.0})
        self.assertEqual(gns.NOISE[gns.BASE_NOISE], (1.5, 0.0))
        self.assertEqual(gns.BASE_PROFILE, "zero")
        self.assertEqual(gns.PROFILES["zero"]["max_speed_mps"], 0.79)
        self.assertEqual(gns.PROFILES["zero"]["gps_delay_s"], 1.5)
        self.assertNotIn("gps_period_s", gns.PROFILES["zero"])  # SimRover's 1 s
        self.assertEqual(gns.PROFILES["miniplus"]["gps_period_s"], 2.0)

    def test_two_second_gps_flies_the_demo(self):
        r = gns.fly("demo", 2, gns.BASE_NOISE, gns.BASE_VARIANT, 1500.0, "miniplus")
        self.assertEqual(r["reports"] >= r["reached"], True)
        self.assertEqual(len(r["credited_true_m"]), r["reached"])


class StatsTests(unittest.TestCase):
    def test_pct(self):
        self.assertIsNone(gns.pct([], 50))
        self.assertEqual(gns.pct([5.0], 90), 5.0)
        self.assertEqual(gns.pct(list(range(1, 11)), 90), 9)

    def test_summarise(self):
        runs = [run("white1.5", "default", s, 100.0 + s) for s in range(1, 7)]
        runs += [run("white1.5", "alpha1", s, 90.0 + s) for s in range(1, 7)]
        runs += [run("gm3-t30", "default", s, 120.0 + s, credit=16.0 if s == 1 else 5.0)
                 for s in range(1, 6)]
        runs += [run("gm3-t30", "default", 6, None, ok=False)]
        runs += [run("gm3-t30", "alpha1", s, 110.0 + s) for s in range(1, 7)]
        runs += [run("white1.5", "default", s, 110.0 + s, profile="gps2s") for s in range(1, 7)]
        rows, overview, noise_effect, variant_effect, verdicts, profile_effect = \
            gns.summarise(runs)
        self.assertEqual(len(rows), 5)
        self.assertEqual(len(variant_effect), 2)
        self.assertEqual(len(profile_effect), 1)
        self.assertEqual((profile_effect[0]["profile"], profile_effect[0]["slower"],
                          profile_effect[0]["faster"]), ("gps2s", 6, 0))
        self.assertAlmostEqual(profile_effect[0]["sign_test_p"], 0.0312, places=4)
        v = {(x["noise"], x["variant"]): x for x in verdicts}
        self.assertTrue(v[("white1.5", "alpha1")]["better"])
        self.assertEqual(v[("white1.5", "alpha1")]["missions_faster"], 1)
        self.assertTrue(v[("gm3-t30", "alpha1")]["better"])
        self.assertEqual(v[("gm3-t30", "alpha1")]["missions_gained"], 1)
        self.assertEqual(v[("gm3-t30", "alpha1")]["missions_faster"], 0)
        self.assertEqual(len(noise_effect), 1)
        e = noise_effect[0]
        self.assertEqual((e["noise"], e["only_a_completed"], e["faster"], e["slower"]),
                         ("gm3-t30", 1, 0, 5))
        self.assertAlmostEqual(e["sign_test_p"], 0.0625)
        o = {(x["profile"], x["noise"], x["variant"]): x for x in overview}
        self.assertEqual(o[("zero", "white1.5", "default")]["time_ratio_to_baseline"], 1.0)
        self.assertEqual(o[("gps2s", "white1.5", "default")]["time_ratio_to_baseline"], 1.0)
        self.assertAlmostEqual(o[("zero", "gm3-t30", "default")]["time_ratio_to_baseline"],
                               1.188, places=3)
        self.assertEqual(o[("zero", "gm3-t30", "default")]["credits_beyond_tolerance"], 4)
        self.assertEqual(o[("zero", "gm3-t30", "default")]["completed"], 5)

    def test_main_writes_outputs(self):
        with tempfile.TemporaryDirectory() as d, redirect_stdout(io.StringIO()):
            code = gns.main(["--out-dir", d, "--seeds", "1", "--missions", "demo",
                             "--noise", "gm3-t30", "--variants", "alpha1",
                             "--profiles", "zero"])
            self.assertEqual(code, 0)
            with open(os.path.join(d, "summary.json")) as f:
                summary = json.load(f)
            with open(os.path.join(d, "report.md")) as f:
                report = f.read()
        self.assertEqual(summary["runs"], 4)
        self.assertTrue(summary["done"])
        self.assertEqual({(x["noise"], x["variant"]) for x in summary["overview"]},
                         {("white1.5", "default"), ("white1.5", "alpha1"),
                          ("gm3-t30", "default"), ("gm3-t30", "alpha1")})
        self.assertIn("gm3-t30", report)

    def test_unknown_noise_is_refused(self):
        with self.assertRaises(SystemExit):
            gns.main(["--noise", "gm99", "--seeds", "1"])


if __name__ == "__main__":
    unittest.main()
