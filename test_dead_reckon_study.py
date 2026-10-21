"""Tests for dead_reckon_study.py. Apache-2.0. By MV2 of Munim, Inc.; written with AI agents."""

import contextlib
import io
import json
import math
import os
import tempfile
import unittest

import dead_reckon_study as ds
import rover_pilot as rp


class StudyRoverTest(unittest.TestCase):
    def test_gaps_same_for_every_variant(self):
        a = ds.StudyRover(ds.MISSIONS["demo"], seed=4, gaps=True, **ds.PROFILES["zero"])
        b = ds.StudyRover(ds.MISSIONS["demo"], seed=4, gaps=True, **ds.PROFILES["zero"])
        self.assertEqual(a.outages, b.outages)
        self.assertGreater(len(a.outages), 10)
        for s, e in a.outages:
            self.assertTrue(ds.GAP_S[0] <= e - s <= ds.GAP_S[1])

    def test_no_fix_in_a_gap(self):
        sim = ds.StudyRover(ds.MISSIONS["demo"], seed=4, gaps=True, gps_dropout=0.0,
                            **ds.PROFILES["zero"])
        # The first outage with at least 3 s of GPS after it.
        s, e = next(o for o, n in zip(sim.outages, sim.outages[1:]) if n[0] - o[1] >= 3.0)
        sim.sleep(s + 1.0)
        self.assertEqual(sim.data()["latitude"], rp.NO_FIX)
        sim.sleep(e - s)
        self.assertNotEqual(sim.data()["latitude"], rp.NO_FIX)

    def test_gauss_markov_error_wanders_slowly(self):
        sim = ds.StudyRover(ds.MISSIONS["demo"], seed=1, tau_s=30.0, gps_noise_m=3.0,
                            gps_dropout=0.0, **ds.PROFILES["zero"])
        steps = []
        for _ in range(200):
            before = sim._err
            sim.sleep(1.0)
            steps.append(math.hypot(sim._err[0] - before[0], sim._err[1] - before[1]))
        self.assertLess(sorted(steps)[100], 1.5)  # white 3 m noise would jump ~4 m


class StudyTest(unittest.TestCase):
    def test_small_run(self):
        with tempfile.TemporaryDirectory() as d:
            with contextlib.redirect_stdout(io.StringIO()):
                ds.main(["--out-dir", d, "--seeds", "2", "--missions", "hairpin",
                         "--profiles", "zero", "--noise", "white1.5-gaps",
                         "--variants", "dr,dr-nolearn", "--timeout", "1500"])
            with open(os.path.join(d, "summary.json")) as f:
                s = json.load(f)
            self.assertTrue(s["done"])
            self.assertEqual(s["runs"], 6)
            for r in open(os.path.join(d, "runs.jsonl")):
                r = json.loads(r)
                self.assertNotIn("Error", r["reason"])
                self.assertIsNotNone(r["pos_err_median"])
            dr = [o for o in s["overview"] if o["variant"] == "dr-nolearn"][0]
            self.assertEqual(dr["trusted_share"], 1.0)
            self.assertIn("P2_gaps", s["predictions"])
            self.assertTrue(os.path.exists(os.path.join(d, "report.md")))


if __name__ == "__main__":
    unittest.main()
