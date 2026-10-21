"""Tests for frodo_blend_b. On test_frodo_compass_live's simulated ride, its ride
analysis with frodo_blend's variants must give frodo_blend's misses exactly; the
held-out sample must not share a ride with frodo_blend's; the decision rules are
checked on tables worked out by hand."""

import json
import os
import tempfile
import unittest

import frodo_blend as fb
import frodo_blend_b as fbb
import frodo_motion as fm
from test_frodo_compass import CYCLE
from test_frodo_compass_live import ride_yz_plus

A_SPEC = (("course", None, False), ("running", None, False), ("blend2", 2, True),
          ("blend5", 5, True), ("blend10", 10, True), ("hard5", 5, False))


class SettingTests(unittest.TestCase):
    def test_variants(self):
        self.assertEqual(fbb.NAMES, ("course", "running", "hard1", "hard2", "hard3", "hard4",
                                     "blend1", "blend2", "blend3"))
        self.assertEqual(fbb.HOLDS, fbb.NAMES[2:])
        self.assertIn(fbb.ADOPTED, fbb.NAMES)

    def test_setting(self):
        self.assertEqual(fbb.setting("running"), {"course_hold_s": 0.0})
        self.assertEqual(fbb.setting("hard3"), {"course_hold_s": 3.0, "fade": False})
        self.assertEqual(fbb.setting("blend2"), {"course_hold_s": 2.0, "fade": True})
        self.assertIsNone(fbb.setting("blend7"))


class HeldOutTests(unittest.TestCase):
    def test_small_part(self):
        keys = ["ride_%03d" % i for i in range(53)]
        first = fm.pick_evenly(keys, 30)
        held = fbb.held_out(keys, 30)
        self.assertEqual(len(first), 30)
        self.assertEqual(len(held), 23)          # every ride the first sample left
        self.assertFalse(set(first) & set(held))
        self.assertEqual(set(first) | set(held), set(keys))

    def test_large_part(self):
        keys = ["ride_%04d" % i for i in range(977)]
        held = fbb.held_out(keys, 30)
        self.assertEqual(len(held), 30)
        self.assertEqual(len(set(held)), 30)
        self.assertFalse(set(fm.pick_evenly(keys, 30)) & set(held))

    def test_part_smaller_than_the_first_sample(self):
        self.assertEqual(fbb.held_out(["a", "b", "c"], 30), [])


class RideTests(unittest.TestCase):
    """test_frodo_compass_live's ride: 490 s of 150 deg left turns between 30 s
    straights, exact GPS and compass."""

    @classmethod
    def setUpClass(cls):
        control, gps, gyro, compass = ride_yz_plus([(10, 0.8, 0.0)] + CYCLE * 2)
        cls.apool = fb.new_pool()
        fb.analyse_ride(control, gps, gyro, compass, cls.apool)
        cls.spool = fbb.new_pool()
        fbb.analyse_ride(control, gps, gyro, compass, cls.spool, variants=A_SPEC)
        cls.pool = fbb.new_pool()
        cls.st = fbb.analyse_ride(control, gps, gyro, compass, cls.pool)
        cls.errs = cls.pool["rides"][0]["errs"]
        cls.s = fbb.summarise(cls.pool)

    def test_reproduces_frodo_blend(self):
        a = self.apool["rides"][0]["errs"]
        b = self.spool["rides"][0]["errs"]
        self.assertTrue(a[("miss", "running", 10)])
        self.assertEqual(sorted(a), sorted(b))
        for key in a:
            self.assertEqual(list(a[key]), list(b[key]), key)

    def test_shared_variants_unchanged(self):
        a = self.apool["rides"][0]["errs"]
        for v in ("course", "running", "blend2"):
            for h in (1, 5, 10, 30):
                self.assertEqual(list(self.errs.get(("miss", v, h), ())),
                                 list(a.get(("miss", v, h), ())), (v, h))

    def test_ride(self):
        self.assertNotIn("skipped", self.st)
        self.assertGreater(self.st["anchors"], 0)

    def test_same_pairs(self):
        self.assertGreater(len(self.errs[("miss", "course", 10)]), 0)
        for h in (1, 2, 3, 5, 10, 20, 30):
            n = len(self.errs.get(("miss", "course", h), ()))
            for v in fbb.NAMES:
                self.assertEqual(len(self.errs.get(("miss", v, h), ())), n, (v, h))

    def test_course_before_the_switch(self):
        # A target h s ahead lies at most 5 h + 3 cells on, before these switches.
        for v, hs in (("hard2", (1,)), ("blend2", (1,)), ("hard3", (1, 2)),
                      ("blend3", (1, 2)), ("hard4", (1, 2, 3))):
            for h in hs:
                self.assertEqual(list(self.errs.get(("miss", v, h), ())),
                                 list(self.errs.get(("miss", "course", h), ())), (v, h))

    def test_summary(self):
        rows = self.s["table"]
        self.assertEqual(fb.find(rows, "course", 10)["over_course"], 1.0)
        self.assertEqual(fb.find(rows, "running", 10)["over_running"], 1.0)
        d = self.s["decision"]
        self.assertFalse(d["check"]["ok"])
        self.assertEqual(d["check"]["why"], "fewer than 2000 pairs")
        self.assertNotIn("default", d)

    def test_outputs(self):
        with tempfile.TemporaryDirectory() as d:
            res = fbb.write_outputs(d, [{"part": "x", "bytes_read": 5}],
                                    [{"no": 0}, {"no": 1, "skipped": "no compass"}],
                                    self.pool, 0.0)
            self.assertTrue(any(x.startswith("Check (stated") for x in res["conclusions"]))
            self.assertEqual(res["rides_skipped"], {"no compass": 1})
            with open(os.path.join(d, "summary.json")) as f:
                self.assertEqual(json.load(f)["version"], fbb.__version__)
            with open(os.path.join(d, "report.md")) as f:
                self.assertIn("| hard3 |", f.read())


def rows(over_course, blend2_over_running=0.925, n=3000):
    """Table rows with n pairs from {(variant, h): ratio over course}."""
    out = []
    for (v, h), x in over_course.items():
        out.append({"variant": v, "horizon_s": h, "n": n, "over_course": x,
                    "over_running": (blend2_over_running if (v, h) == ("blend2", 10)
                                     else 1.0 if v == "running" else None)})
    return out


BASE = {("running", 10): 0.93, ("running", 30): 0.69, ("blend2", 10): 0.86,
        ("blend2", 30): 0.68, ("hard1", 10): 0.90, ("hard2", 10): 0.87, ("hard3", 10): 0.865,
        ("hard4", 10): 0.88, ("blend1", 10): 0.89, ("blend3", 10): 0.875,
        ("hard3", 30): 0.70}
GOOD_CI = {"blend2/running": [0.91, 0.95]}


class DecideTests(unittest.TestCase):
    def test_confirmed_keeps_blend2(self):
        d = fbb.decide(rows(BASE), GOOD_CI)
        self.assertTrue(d["check"]["ok"])
        self.assertTrue(d["c1"] and d["c2"] and d["confirmed"])
        self.assertAlmostEqual(d["cost_30s"], -0.01, places=6)
        self.assertEqual(d["best"], "blend2")
        self.assertEqual(d["default"], "blend2")
        self.assertEqual(d["setting"], {"course_hold_s": 2.0, "fade": True})
        self.assertAlmostEqual(d["hard_minus_blend_10s"]["hard2-blend2"], 0.01, places=6)

    def test_clearly_better_hold_replaces_it(self):
        d = fbb.decide(rows({**BASE, ("hard3", 10): 0.845}), GOOD_CI)
        self.assertEqual(d["best"], "hard3")
        self.assertEqual(d["default"], "hard3")             # 0.845 <= 0.86 - 0.01
        self.assertEqual(d["setting"], {"course_hold_s": 3.0, "fade": False})

    def test_slightly_better_hold_does_not(self):
        d = fbb.decide(rows({**BASE, ("hard3", 10): 0.855}), GOOD_CI)
        self.assertEqual(d["best"], "hard3")
        self.assertEqual(d["default"], "blend2")            # 0.855 > 0.85

    def test_better_hold_that_costs_at_30s_does_not(self):
        d = fbb.decide(rows({**BASE, ("hard3", 10): 0.845, ("hard3", 30): 0.72}),
                       GOOD_CI)
        self.assertEqual(d["default"], "blend2")            # 0.72 - 0.69 > 0.02

    def test_interval_reaching_one_is_not_confirmed(self):
        d = fbb.decide(rows(BASE), {"blend2/running": [0.90, 1.01]})
        self.assertFalse(d["c1"])
        self.assertFalse(d["confirmed"])
        self.assertEqual(d["default"], "running")
        self.assertNotIn("setting", d)

    def test_small_gain_is_not_confirmed(self):
        d = fbb.decide(rows(BASE, blend2_over_running=0.98), GOOD_CI)
        self.assertFalse(d["c1"])
        self.assertEqual(d["default"], "running")

    def test_cost_at_30s_is_not_confirmed(self):
        d = fbb.decide(rows({**BASE, ("blend2", 30): 0.72}), GOOD_CI)
        self.assertTrue(d["c1"])
        self.assertFalse(d["c2"])
        self.assertEqual(d["default"], "running")

    def test_no_interval_is_not_confirmed(self):
        self.assertEqual(fbb.decide(rows(BASE), {})["default"], "running")

    def test_check_fails(self):
        d = fbb.decide(rows(BASE, n=1500), GOOD_CI)
        self.assertFalse(d["check"]["ok"])
        self.assertEqual(d["check"]["why"], "fewer than 2000 pairs")
        self.assertNotIn("default", d)
        self.assertFalse(fbb.decide([], {})["check"]["ok"])


class GuardTests(unittest.TestCase):
    def test_guards(self):
        control, gps, gyro, compass = ride_yz_plus([(60, 0.8, 0.0)])
        pool = fbb.new_pool()
        self.assertEqual(fbb.analyse_ride(control, gps, gyro, [], pool)["skipped"], "no compass")
        st = fbb.analyse_ride(control, gps, gyro, compass, pool)
        self.assertEqual(st["skipped"], "whole ride does not calibrate")
        self.assertEqual(pool["rides"], [])
        self.assertEqual(fbb.conclusions(fbb.summarise(pool)), [])


if __name__ == "__main__":
    unittest.main()
