"""Tests for frodo_between. The live headings are checked on hand-made samples;
on test_frodo_compass_live's simulated ride, course, interp and b2_interp must
give frodo_blend_b's course, running and blend2 misses exactly; the decision
rules are checked on tables worked out by hand."""

import json
import math
import os
import tempfile
import unittest

import frodo_blend as fb
import frodo_blend_b as fbb
import frodo_between as fbt
import frodo_compass as fc
from test_frodo_compass import CY, CYCLE, CZ
from test_frodo_compass_live import ride_yz_plus


def grid(secs):
    """A grid of 0.2 s cells from t0 = 0: control at 10 Hz for secs seconds."""
    control = [(i * 0.1, 0.8, 0.0, [100.0] * 4) for i in range(int(secs * 10))]
    return fc.Grid(control, [])


def sample(t, deg):
    """A compass sample that frame yz+ reads as deg about the centre (CY, CZ)."""
    r = math.radians(deg)
    return (t, 50.0, CY + 200.0 * math.cos(r), CZ + 200.0 * math.sin(r))


class NamesTests(unittest.TestCase):
    def test_names(self):
        self.assertEqual(fbt.NAMES, ("course", "interp", "last", "gyro05", "gyro1", "cmd20",
                                     "b2_interp", "b2_last", "b2_gyro05", "b2_gyro1",
                                     "b2_cmd20"))
        self.assertEqual(fbt.BETWEEN, ("gyro05", "gyro1", "cmd20"))


class AtTests(unittest.TestCase):
    def test_at(self):
        g = grid(3)                       # 15 cells, 16 boundaries
        self.assertEqual(g.n, 15)
        cum = [float(k) for k in range(g.n + 1)]
        self.assertAlmostEqual(fbt.at(cum, g, 0.3), 1.5, places=9)
        self.assertAlmostEqual(fbt.at(cum, g, 0.0), 0.0, places=9)
        self.assertAlmostEqual(fbt.at(cum, g, -5.0), 0.0, places=9)    # held at the start
        self.assertAlmostEqual(fbt.at(cum, g, 100.0), 15.0, places=9)  # and at the end
        self.assertAlmostEqual(fbt.at(cum, g, 2.9), 14.5, places=9)


class LastReadTests(unittest.TestCase):
    def setUp(self):
        self.g = grid(3)
        self.samples = [sample(0.37, 10.0), sample(1.37, 20.0), sample(2.37, 30.0)]

    def test_latest_sample_at_or_before_the_cell(self):
        hs, tt = fbt.last_reads(self.samples, self.g, [(0.0, (CY, CZ))])
        # Cell centres 0.1, 0.3, 0.5, ...: none before 0.37, then each sample held.
        self.assertEqual(hs[:2], [None, None])
        self.assertEqual(tt[:2], [None, None])
        for k, deg, t in ((2, 10.0, 0.37), (6, 10.0, 0.37), (7, 20.0, 1.37),
                          (11, 20.0, 1.37), (12, 30.0, 2.37), (14, 30.0, 2.37)):
            self.assertAlmostEqual(hs[k], deg, places=6, msg=k)
            self.assertEqual(tt[k], t, k)

    def test_no_heading_before_a_centre(self):
        hs, tt = fbt.last_reads(self.samples, self.g, [(1.0, (CY, CZ))])
        self.assertIsNone(hs[2])                 # 0.5 s: the fit has no centre yet
        self.assertAlmostEqual(hs[5], 10.0, places=6)   # 1.1 s
        self.assertEqual(tt[5], 0.37)
        hs, _ = fbt.last_reads(self.samples, self.g, [(0.0, None)])
        self.assertEqual(hs, [None] * 15)


class GyroTests(unittest.TestCase):
    def test_offset(self):
        gyro = [(float(i), 0.8 + (5.0 if i % 4 == 0 else 0.0), 0.0, 0.0) for i in range(40)]
        self.assertAlmostEqual(fbt.gyro_offset(gyro, 30.0), 0.8, places=9)
        few = [(float(i), float(i), 0.0, 0.0) for i in range(5)]
        self.assertEqual(fbt.gyro_offset(few, 3.0), 2.0)     # fewer than 20: all of them
        self.assertEqual(fbt.gyro_offset([], 3.0), 0.0)

    def test_causal_rates(self):
        g = grid(3)
        gyro = [(0.37, 5.8, 0.0, 0.0), (1.37, -2.2, 0.0, 0.0)]
        r = fbt.causal_rates(g, gyro, 0.8)
        self.assertEqual(len(r), 15)
        self.assertEqual(r[1], 0.0)              # 0.3 s: no sample yet
        self.assertAlmostEqual(r[2], 5.0, places=9)
        self.assertAlmostEqual(r[6], 5.0, places=9)
        self.assertAlmostEqual(r[7], -3.0, places=9)
        self.assertAlmostEqual(r[13], -3.0, places=9)   # 2.7 s: 1.33 s old
        self.assertEqual(r[14], 0.0)                    # 2.9 s: 1.53 s old

    def test_between(self):
        g = grid(3)
        cum = [2.0 * k for k in range(g.n + 1)]   # 10 deg/s counter-clockwise
        hs = [None, 10.0, 10.0, 1.0]
        tt = [None, 0.37, 0.37, 0.37]
        out = fbt.between(hs, tt, g, cum, 1.0)
        self.assertIsNone(out[0])
        # Cell 2 centre 0.5 s: 5.0 - 3.7 = 1.3 deg turned left since the read.
        self.assertAlmostEqual(out[2], 8.7, places=6)
        self.assertAlmostEqual(out[3], 359.7 - 2.0, places=6)   # 0.7 s: 1.0 - 3.3
        self.assertAlmostEqual(fbt.between(hs, tt, g, cum, 0.5)[2], 9.35, places=6)
        # Cell 1 centre 0.3 s comes before the read: the turn runs back.
        self.assertAlmostEqual(out[1], 10.7, places=6)

    def test_with_fallback(self):
        self.assertEqual(fbt.with_fallback([None, 5.0, None], [1.0, 2.0, 3.0]),
                         [5.0, 5.0, 5.0])
        self.assertEqual(fbt.with_fallback([None, None], [1.0, 2.0]), [1.0, 2.0])


class RideTests(unittest.TestCase):
    """test_frodo_compass_live's ride: 490 s of 150 deg left turns between 30 s
    straights, exact GPS, gyroscope and compass, all read once a second."""

    @classmethod
    def setUpClass(cls):
        control, gps, gyro, compass = ride_yz_plus([(10, 0.8, 0.0)] + CYCLE * 2)
        cls.bpool = fbb.new_pool()
        fbb.analyse_ride(control, gps, gyro, compass, cls.bpool)
        cls.pool = fbt.new_pool()
        cls.st = fbt.analyse_ride(control, gps, gyro, compass, cls.pool)
        cls.errs = cls.pool["rides"][0]["errs"]
        cls.s = fbt.summarise(cls.pool)

    def test_reproduces_frodo_blend_b(self):
        b = self.bpool["rides"][0]["errs"]
        self.assertTrue(b[("miss", "running", 10)])
        for mine, theirs in (("course", "course"), ("interp", "running"),
                             ("b2_interp", "blend2")):
            for h in fc.HORIZONS:
                self.assertEqual(list(self.errs.get(("miss", mine, h), ())),
                                 list(b.get(("miss", theirs, h), ())), (mine, h))

    def test_ride(self):
        self.assertNotIn("skipped", self.st)
        self.assertGreater(self.st["anchors"], 0)
        self.assertAlmostEqual(self.st["gyro_offset"], 0.8, places=3)   # test_frodo_compass BIAS

    def test_same_pairs(self):
        self.assertGreater(len(self.errs[("miss", "course", 10)]), 0)
        for h in fc.HORIZONS:
            n = len(self.errs.get(("miss", "course", h), ()))
            for v in fbt.NAMES:
                self.assertEqual(len(self.errs.get(("miss", v, h), ())), n, (v, h))

    def test_holding_the_last_read_costs_on_turns(self):
        # Exact samples a second apart through 15 deg/s turns: the held read lags
        # the turn, while interpolating, or turning by the exact gyroscope, does not.
        last = sum(self.errs[("miss", "last", 10)])
        self.assertLess(sum(self.errs[("miss", "interp", 10)]), last)
        self.assertLess(sum(self.errs[("miss", "gyro1", 10)]), last)

    def test_hold_before_the_switch(self):
        # A target 1 s ahead lies inside the 2 s hold: every b2 variant is the course.
        for s in fbt.SOURCES:
            self.assertEqual(list(self.errs[("miss", "b2_" + s, 1)]),
                             list(self.errs[("miss", "course", 1)]), s)

    def test_summary(self):
        rows = self.s["table"]
        self.assertEqual(fb.find(rows, "course", 10)["over_course"], 1.0)
        self.assertEqual(fb.find(rows, "last", 10)["over_last"], 1.0)
        self.assertEqual(fb.find(rows, "interp", 10)["over_interp"], 1.0)
        d = self.s["decision"]
        self.assertFalse(d["check"]["ok"])
        self.assertEqual(d["check"]["why"], "fewer than 2000 pairs")
        self.assertNotIn("build", d)

    def test_outputs(self):
        with tempfile.TemporaryDirectory() as d:
            res = fbt.write_outputs(d, [{"part": "x", "bytes_read": 5}],
                                    [{"no": 0}, {"no": 1, "skipped": "no compass"}],
                                    self.pool, 0.0)
            self.assertTrue(any(x.startswith("Check E1 (stated") for x in res["conclusions"]))
            self.assertEqual(res["rides_skipped"], {"no compass": 1})
            with open(os.path.join(d, "summary.json")) as f:
                self.assertEqual(json.load(f)["version"], fbt.__version__)
            with open(os.path.join(d, "report.md")) as f:
                self.assertIn("| b2_gyro05 |", f.read())


def rows(spec, n=3000):
    """Table rows with n pairs from {(variant, h): (over_course, over_last, over_interp)}."""
    out = []
    for (v, h), (oc, ol, oi) in spec.items():
        out.append({"variant": v, "horizon_s": h, "n": n, "over_course": oc,
                    "over_last": ol, "over_interp": oi})
    return out


BASE = {("interp", 10): (0.883, 0.97, 1.0), ("b2_interp", 10): (0.834, 0.92, 0.944),
        ("last", 10): (0.91, 1.0, 1.03), ("last", 30): (0.66, 1.0, 1.02),
        ("gyro05", 10): (0.90, 0.99, 1.02), ("gyro05", 30): (0.66, 1.0, 1.02),
        ("gyro1", 10): (0.92, 1.01, 1.04), ("gyro1", 30): (0.67, 1.01, 1.03),
        ("cmd20", 10): (0.905, 0.995, 1.025), ("cmd20", 30): (0.66, 1.0, 1.02),
        ("b2_last", 10): (0.86, 0.95, 0.97)}
GOOD_CI = {"gyro05/last": [0.97, 1.01], "gyro1/last": [0.99, 1.03],
           "cmd20/last": [0.98, 1.01], "b2_last/last": [0.93, 0.97]}


class DecideTests(unittest.TestCase):
    def test_nothing_to_build_and_the_hold_stays(self):
        d = fbt.decide(rows(BASE), GOOD_CI)
        self.assertTrue(d["check"]["ok"])
        self.assertEqual(d["last_over_interp_10s"], 1.03)
        self.assertEqual(d["last_over_interp_30s"], 1.02)
        self.assertIsNone(d["build"])
        self.assertFalse(any(g["passes"] for g in d["between"].values()))
        self.assertTrue(d["hold_stays"])
        self.assertEqual(d["hold_over_last_10s"], 0.95)

    def test_a_clear_gain_is_built(self):
        spec = {**BASE, ("gyro05", 10): (0.88, 0.97, 1.0), ("cmd20", 10): (0.89, 0.975, 1.01)}
        ci = {**GOOD_CI, "gyro05/last": [0.95, 0.99], "cmd20/last": [0.96, 0.99]}
        d = fbt.decide(rows(spec), ci)
        self.assertTrue(d["between"]["gyro05"]["passes"])
        self.assertTrue(d["between"]["cmd20"]["passes"])
        self.assertEqual(d["build"], "gyro05")              # the lower at 10 s

    def test_a_gain_whose_interval_reaches_one_is_not(self):
        spec = {**BASE, ("gyro05", 10): (0.88, 0.97, 1.0)}
        d = fbt.decide(rows(spec), GOOD_CI)                 # CI [0.97, 1.01]
        self.assertFalse(d["between"]["gyro05"]["passes"])
        self.assertIsNone(d["build"])

    def test_a_gain_that_costs_at_30s_is_not(self):
        spec = {**BASE, ("gyro05", 10): (0.88, 0.97, 1.0), ("gyro05", 30): (0.69, 1.05, 1.07)}
        d = fbt.decide(rows(spec), {**GOOD_CI, "gyro05/last": [0.95, 0.99]})
        self.assertAlmostEqual(d["between"]["gyro05"]["cost_30s"], 0.03, places=6)
        self.assertFalse(d["between"]["gyro05"]["passes"])  # 0.69 - 0.66 > 0.02

    def test_a_small_gain_is_not(self):
        spec = {**BASE, ("gyro05", 10): (0.89, 0.985, 1.01)}
        d = fbt.decide(rows(spec), {**GOOD_CI, "gyro05/last": [0.97, 0.995]})
        self.assertFalse(d["between"]["gyro05"]["passes"])  # 0.985 > 0.98

    def test_the_hold_is_re_examined(self):
        spec = {**BASE, ("b2_last", 10): (0.89, 0.98, 1.01)}
        self.assertFalse(fbt.decide(rows(spec), GOOD_CI)["hold_stays"])
        d = fbt.decide(rows(BASE), {**GOOD_CI, "b2_last/last": [0.93, 1.0]})
        self.assertFalse(d["hold_stays"])                   # the CI must end below 1
        self.assertFalse(fbt.decide(rows(BASE), {})["hold_stays"])

    def test_check_fails(self):
        d = fbt.decide(rows(BASE, n=1500), GOOD_CI)
        self.assertFalse(d["check"]["ok"])
        self.assertEqual(d["check"]["why"], "fewer than 2000 pairs")
        self.assertNotIn("build", d)
        d = fbt.decide(rows({**BASE, ("interp", 10): (0.890, 0.97, 1.0)}), GOOD_CI)
        self.assertEqual(d["check"]["why"], "does not reproduce frodo-blend-b-v2")
        d = fbt.decide(rows({**BASE, ("b2_interp", 10): (0.834, 0.92, 0.95)}), GOOD_CI)
        self.assertEqual(d["check"]["why"], "does not reproduce frodo-blend-b-v2")
        d = fbt.decide(rows({**BASE, ("interp", 10): (0.885, 0.97, 1.0)}), GOOD_CI)
        self.assertTrue(d["check"]["ok"])                   # within 0.002
        self.assertFalse(fbt.decide([], {})["check"]["ok"])


class GuardTests(unittest.TestCase):
    def test_guards(self):
        control, gps, gyro, compass = ride_yz_plus([(60, 0.8, 0.0)])
        pool = fbt.new_pool()
        self.assertEqual(fbt.analyse_ride(control, gps, gyro, [], pool)["skipped"], "no compass")
        st = fbt.analyse_ride(control, gps, gyro, compass, pool)
        self.assertEqual(st["skipped"], "whole ride does not calibrate")
        self.assertEqual(pool["rides"], [])
        self.assertEqual(fbt.conclusions(fbt.summarise(pool)), [])


if __name__ == "__main__":
    unittest.main()
