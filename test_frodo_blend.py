"""Tests for frodo_blend. The blend's headings and paths are checked against
values worked out by hand; on test_frodo_compass_live's simulated ride the
course and running rows must equal frodo_compass_live's, pair for pair."""

import json
import os
import tempfile
import unittest

import frodo_blend as fb
import frodo_compass as fc
import frodo_compass_live as fl
from test_frodo_compass import CYCLE
from test_frodo_compass_live import ride_yz_plus


def straight_grid():
    """200 control rows 0.1 s apart at 100 RPM: 100 cells of 0.2 s, each at
    100 x 0.00668 = 0.668 m/s, so 0.1336 m per cell."""
    return fc.Grid([(i * 0.1, 0.8, 0.0, [100.0] * 4) for i in range(200)], [])


class BlendTests(unittest.TestCase):
    def test_variants(self):
        self.assertEqual(fb.VARIANTS, ("course", "running", "blend2", "blend5", "blend10",
                                       "hard5"))

    def test_hard_switch(self):
        psi = fb.blended(0.0, lambda k: 10.0, 0, 0.2, 5.0, decay=False)
        self.assertEqual(psi(24), 0.0)    # cell 24 starts 4.8 s after the fix
        self.assertEqual(psi(25), 10.0)   # cell 25 starts at 5.0 s
        self.assertEqual(psi(60), 10.0)

    def test_fading_shift(self):
        # Course 0, compass 10: shift -10 at the switch, fading over 5 s (25 cells).
        psi = fb.blended(0.0, lambda k: 10.0, 0, 0.2, 5.0)
        self.assertEqual(psi(24), 0.0)
        self.assertAlmostEqual(psi(25), 0.0, places=9)    # no jump
        self.assertAlmostEqual(psi(30), 2.0, places=9)    # 1 s on: 10 - 0.8 x 10
        self.assertAlmostEqual(psi(50), 10.0, places=9)   # 5 s on: shift gone
        self.assertAlmostEqual(psi(60), 10.0, places=9)

    def test_shift_wraps(self):
        # Course 350, compass 10: the shift is -20 deg, not +340.
        psi = fb.blended(350.0, lambda k: 10.0, 0, 0.2, 5.0)
        self.assertAlmostEqual(psi(25), 350.0, places=9)
        self.assertAlmostEqual(psi(35), 358.0, places=9)  # 2 s on: 10 - 0.6 x 20

    def test_switch_counts_from_the_anchor(self):
        psi = fb.blended(40.0, lambda k: 70.0, 7, 0.2, 2.0, decay=False)
        self.assertEqual(psi(16), 40.0)   # 1.8 s after boundary 7
        self.assertEqual(psi(17), 70.0)   # 2.0 s after

    def test_paths(self):
        grid = straight_grid()
        self.assertEqual(grid.n, 100)
        hard = fc.run(grid, 0, [10, 50], fb.blended(0.0, lambda k: 90.0, 0, 0.2, 5.0,
                                                    decay=False))
        # 10 cells north = 1.336 m; then 25 cells north and 25 cells east = 3.34 m each.
        self.assertAlmostEqual(hard[0][0], 0.0, places=9)
        self.assertAlmostEqual(hard[0][1], 1.336, places=9)
        self.assertAlmostEqual(hard[1][0], 3.34, places=9)
        self.assertAlmostEqual(hard[1][1], 3.34, places=9)

    def test_agreeing_compass_changes_nothing(self):
        grid = straight_grid()
        course = fc.run(grid, 0, [10, 30, 60], lambda k: 30.0)
        for psi in (fb.blended(30.0, lambda k: 30.0, 0, 0.2, b) for b in fb.BLEND_S):
            self.assertEqual(fc.run(grid, 0, [10, 30, 60], psi), course)
        hard = fb.blended(30.0, lambda k: 30.0, 0, 0.2, 5.0, decay=False)
        self.assertEqual(fc.run(grid, 0, [10, 30, 60], hard), course)

    def test_biased_compass_waits_for_the_switch(self):
        # A compass 10 deg off changes nothing before the switch at 25 cells.
        grid = straight_grid()
        course = fc.run(grid, 0, [5, 20], lambda k: 0.0)
        for decay in (True, False):
            psi = fb.blended(0.0, lambda k: 10.0, 0, 0.2, 5.0, decay)
            self.assertEqual(fc.run(grid, 0, [5, 20], psi), course)


class RideTests(unittest.TestCase):
    """test_frodo_compass_live's ride: 490 s of 150 deg left turns between 30 s
    straights, exact GPS and compass."""

    @classmethod
    def setUpClass(cls):
        control, gps, gyro, compass = ride_yz_plus([(10, 0.8, 0.0)] + CYCLE * 2)
        cls.lpool = fl.new_pool()
        fl.analyse_ride(control, gps, gyro, compass, cls.lpool)
        cls.pool = fb.new_pool()
        cls.st = fb.analyse_ride(control, gps, gyro, compass, cls.pool)
        cls.errs = cls.pool["rides"][0]["errs"]
        cls.s = fb.summarise(cls.pool)

    def test_ride(self):
        self.assertNotIn("skipped", self.st)
        self.assertIn("running", self.st["bias_fits"])
        self.assertGreater(self.st["anchors"], 0)

    def test_reproduces_live(self):
        lerrs = self.lpool["rides"][0]["errs"]
        self.assertTrue(lerrs[("all", "running", 10)])
        for h in fc.HORIZONS:
            self.assertEqual(list(self.errs.get(("miss", "running", h), ())),
                             list(lerrs.get(("all", "running", h), ())), h)
            self.assertEqual(list(self.errs.get(("miss", "course", h), ())),
                             list(lerrs.get(("course", "running", h), ())), h)

    def test_same_pairs(self):
        self.assertGreater(len(self.errs[("miss", "course", 10)]), 0)
        for h in fc.HORIZONS:
            n = len(self.errs.get(("miss", "course", h), ()))
            for v in fb.VARIANTS:
                self.assertEqual(len(self.errs.get(("miss", v, h), ())), n, (v, h))

    def test_course_before_the_switch(self):
        # A target h s ahead lies at most 5 h + 3 cells on (0.5 s target tolerance,
        # rounding to cells), before every switch here.
        for v, hs in (("blend2", (1,)), ("blend5", (1, 2, 3)), ("hard5", (1, 2, 3)),
                      ("blend10", (1, 2, 3, 5))):
            for h in hs:
                self.assertEqual(list(self.errs.get(("miss", v, h), ())),
                                 list(self.errs.get(("miss", "course", h), ())), (v, h))

    def test_summary(self):
        rows = self.s["table"]
        self.assertEqual(fb.find(rows, "course", 10)["over_course"], 1.0)
        self.assertEqual(fb.find(rows, "running", 10)["over_running"], 1.0)
        # One simulated ride has far fewer than 2,000 pairs: the check fails, nothing is decided.
        d = self.s["decision"]
        self.assertFalse(d["check"]["ok"])
        self.assertEqual(d["check"]["why"], "fewer than 2000 pairs")
        self.assertNotIn("default", d)
        self.assertEqual(self.s["ci"], {})

    def test_outputs(self):
        with tempfile.TemporaryDirectory() as d:
            res = fb.write_outputs(d, [{"part": "x", "bytes_read": 5}],
                                   [{"no": 0}, {"no": 1, "skipped": "no compass"}],
                                   self.pool, 0.0)
            self.assertTrue(any("Check E2" in x for x in res["conclusions"]))
            self.assertEqual(res["rides_skipped"], {"no compass": 1})
            with open(os.path.join(d, "summary.json")) as f:
                self.assertEqual(json.load(f)["version"], fb.__version__)
            with open(os.path.join(d, "report.md")) as f:
                self.assertIn("| hard5 |", f.read())


class DecideTests(unittest.TestCase):
    @staticmethod
    def rows(ratios):
        """Table rows with 3,000 pairs from {(variant, h): ratio over course}."""
        return [{"variant": v, "horizon_s": h, "n": 3000, "over_course": x}
                for (v, h), x in ratios.items()]

    def test_adopts_a_blend(self):
        d = fb.decide(self.rows({("running", 10): 0.93, ("running", 30): 0.69,
                                 ("blend2", 10): 0.91, ("blend5", 10): 0.88,
                                 ("blend10", 10): 0.90, ("blend5", 30): 0.70,
                                 ("hard5", 10): 0.885}))
        self.assertTrue(d["check"]["ok"])
        self.assertEqual(d["best_blend"], "blend5")
        self.assertEqual(d["cost_30s"], 0.01)
        self.assertEqual(d["default"], "blend5")         # 0.88 <= 0.93 - 0.03
        self.assertEqual(d["hard_minus_blend_10s"], 0.005)
        self.assertEqual(d["switch"], "hard")

    def test_keeps_running(self):
        d = fb.decide(self.rows({("running", 10): 0.93, ("running", 30): 0.69,
                                 ("blend2", 10): 0.92, ("blend5", 10): 0.91,
                                 ("blend10", 10): 0.95, ("blend5", 30): 0.69,
                                 ("hard5", 10): 0.94}))
        self.assertEqual(d["default"], "running")        # 0.91 > 0.93 - 0.03
        self.assertEqual(d["switch"], "fading shift")

    def test_cost_at_30s(self):
        d = fb.decide(self.rows({("running", 10): 0.93, ("running", 30): 0.69,
                                 ("blend2", 10): 0.85, ("blend5", 10): 0.88,
                                 ("blend10", 10): 0.90, ("blend2", 30): 0.72}))
        self.assertEqual(d["best_blend"], "blend2")
        self.assertEqual(d["cost_30s"], 0.03)
        self.assertEqual(d["default"], "running")        # 0.03 > 0.02 at 30 s
        self.assertNotIn("switch", d)

    def test_check_fails(self):
        d = fb.decide(self.rows({("running", 10): 0.96, ("blend5", 10): 0.80}))
        self.assertFalse(d["check"]["ok"])
        self.assertEqual(d["check"]["why"], "does not reproduce live-v1")
        self.assertEqual(fb.decide([])["check"]["ok"], False)


class GuardTests(unittest.TestCase):
    def test_guards(self):
        control, gps, gyro, compass = ride_yz_plus([(60, 0.8, 0.0)])
        pool = fb.new_pool()
        self.assertEqual(fb.analyse_ride(control, gps, gyro, [], pool)["skipped"], "no compass")
        st = fb.analyse_ride(control, gps, gyro, compass, pool)
        self.assertEqual(st["skipped"], "whole ride does not calibrate")
        self.assertEqual(pool["rides"], [])
        self.assertEqual(fb.conclusions(fb.summarise(pool)), [])


if __name__ == "__main__":
    unittest.main()
