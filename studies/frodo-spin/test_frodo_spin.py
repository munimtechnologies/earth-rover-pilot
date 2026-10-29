"""Tests for frodo_spin.py. By MV2 of Munim, Inc.; written with AI agents. Apache-2.0."""

import json
import math
import os
import tempfile
import time
import unittest

import frodo_spin as fs


def ctl(spec, t0=1000.0, dt=0.1):
    """Control rows (t, linear, angular, rpms) from [(count, linear, angular)]."""
    rows, k = [], 0
    for count, lin, ang in spec:
        for _ in range(count):
            rows.append((t0 + k * dt, lin, ang, [0.0, 0.0, 0.0, 0.0]))
            k += 1
    return rows


def sample(t, h):
    """A compass sample (t, x, y, z) whose yz+ heading about (0, 0) is h deg."""
    r = math.radians(h)
    return (t, 0.0, math.cos(r), math.sin(r))


TURN = {"t_on": 1003.0, "t_off": 1005.0, "dur_s": 2.0, "a": 0.6}


class FindTurns(unittest.TestCase):
    def test_one_turn_from_rest(self):
        got = fs.find_turns(ctl([(30, 0, 0), (20, 0, 0.6), (40, 0, 0)]))
        self.assertEqual(len(got), 1)
        self.assertAlmostEqual(got[0]["t_on"], 1003.0, places=6)
        self.assertAlmostEqual(got[0]["t_off"], 1005.0, places=6)
        self.assertAlmostEqual(got[0]["dur_s"], 2.0, places=6)
        self.assertAlmostEqual(got[0]["a"], 0.6, places=6)

    def test_driving_before_is_not_from_rest(self):
        spec = [(20, 0, 0), (1, 0.5, 0), (9, 0, 0), (20, 0, 0.6), (40, 0, 0)]
        self.assertEqual(fs.find_turns(ctl(spec)), [])

    def test_turn_the_other_way_after_is_not_at_rest(self):
        spec = [(30, 0, 0), (20, 0, 0.6), (10, 0, -0.6), (40, 0, 0)]
        self.assertEqual(fs.find_turns(ctl(spec)), [])

    def test_too_short(self):
        self.assertEqual(fs.find_turns(ctl([(30, 0, 0), (2, 0, 0.6), (40, 0, 0)])), [])

    def test_turning_while_driving_is_not_in_place(self):
        self.assertEqual(fs.find_turns(ctl([(30, 0, 0), (20, 0.5, 0.6), (40, 0, 0)])), [])

    def test_no_rows_after(self):
        self.assertEqual(fs.find_turns(ctl([(30, 0, 0), (20, 0, 0.6)])), [])

    def test_two_turns(self):
        spec = [(30, 0, 0), (20, 0, 0.6), (40, 0, 0), (10, 0, -1.0), (40, 0, 0)]
        got = fs.find_turns(ctl(spec))
        self.assertEqual(len(got), 2)
        self.assertAlmostEqual(got[1]["dur_s"], 1.0, places=6)
        self.assertAlmostEqual(got[1]["a"], -1.0, places=6)


class Measure(unittest.TestCase):
    def test_signed_turn(self):
        self.assertAlmostEqual(fs.signed_turn(100.0, 70.0, 0.5), 30.0)
        self.assertAlmostEqual(fs.signed_turn(100.0, 130.0, -1.0), 30.0)
        self.assertAlmostEqual(fs.signed_turn(100.0, 110.0, 1.0), -10.0)
        self.assertAlmostEqual(fs.signed_turn(10.0, 340.0, 1.0), 30.0)
        self.assertAlmostEqual(fs.signed_turn(50.0, 50.0, 1.0), 0.0)
        self.assertAlmostEqual(fs.signed_turn(0.0, 160.0, 1.0), 200.0)

    def test_turn_of(self):
        compass = [sample(1002.5, 100.0), sample(1006.2, 70.0)]
        got = fs.turn_of(compass, [c[0] for c in compass], (0.0, 0.0), TURN)
        self.assertAlmostEqual(got[0], 30.0, places=6)
        self.assertAlmostEqual(got[1], 100.0, places=6)
        self.assertAlmostEqual(got[2], 70.0, places=6)

    def test_turn_of_needs_both_reads(self):
        late = [sample(1002.5, 100.0), sample(1008.0, 70.0)]
        self.assertIsNone(fs.turn_of(late, [c[0] for c in late], (0.0, 0.0), TURN))
        early = [sample(1001.0, 100.0), sample(1006.2, 70.0)]
        self.assertIsNone(fs.turn_of(early, [c[0] for c in early], (0.0, 0.0), TURN))

    def test_gyro_rate(self):
        gyro = [(1003.5, 100.0, 0, 0), (1004.0, 22.0, 0, 0), (1004.5, 32.0, 0, 0),
                (1005.5, 100.0, 0, 0)]
        gt = [g[0] for g in gyro]
        self.assertAlmostEqual(fs.gyro_rate(gyro, gt, 2.0, TURN), 25.0)
        right = dict(TURN, a=-0.6)
        self.assertAlmostEqual(fs.gyro_rate(gyro, gt, 2.0, right), -25.0)
        short = dict(TURN, t_off=1003.5)
        self.assertIsNone(fs.gyro_rate(gyro, gt, 2.0, short))


class Ride(unittest.TestCase):
    def control(self):
        return ctl([(30, 0, 0), (20, 0, 0.6), (40, 0, 0)])

    def test_end_to_end(self):
        compass = [sample(1002.5, 100.0), sample(1006.2, 70.0)]
        compass += [sample(1010.0 + k, 10.0 * k) for k in range(36)]
        pool = fs.new_pool()
        st = fs.analyse_ride(self.control(), None, compass, pool, no=3)
        self.assertNotIn("skipped", st)
        self.assertEqual(st["turns"], 1)
        e = pool["rides"][0]["events"][0]
        self.assertEqual(e["no"], 3)
        self.assertAlmostEqual(e["turn_deg"], 30.0, places=6)
        self.assertAlmostEqual(e["dur_s"], 2.0, places=6)
        self.assertNotIn("gyro_dps", e)

    def test_uncalibrated_compass(self):
        compass = [sample(1002.5, 100.0), sample(1006.2, 70.0)]
        compass += [sample(1010.0 + k, 200.0) for k in range(18)]
        pool = fs.new_pool()
        st = fs.analyse_ride(self.control(), None, compass, pool)
        self.assertEqual(st["skipped"], "compass does not calibrate")
        self.assertEqual(pool["rides"], [])

    def test_no_turn(self):
        st = fs.analyse_ride(ctl([(90, 0, 0)]), None, [], fs.new_pool())
        self.assertEqual(st["skipped"], "no in-place turn from rest")


class Summary(unittest.TestCase):
    def test_fit(self):
        ev = [{"a": 1.0, "dur_s": 1.0, "turn_deg": 20.0},
              {"a": -1.0, "dur_s": 2.0, "turn_deg": 45.0},
              {"a": 1.0, "dur_s": 3.0, "turn_deg": 70.0}]
        g, c = fs.fit(ev)
        self.assertAlmostEqual(g, 25.0)
        self.assertAlmostEqual(c, -5.0)
        self.assertEqual(fs.fit(ev[:2]), (None, None))

    def test_gyro_gain(self):
        ev = [{"a": 0.5, "gyro_dps": 14.0}, {"a": -1.0, "gyro_dps": 28.0}, {"a": 1.0}]
        g, n = fs.gyro_gain(ev)
        self.assertAlmostEqual(g, 28.0)
        self.assertEqual(n, 2)

    def test_sign_share(self):
        ev = [{"turn_deg": x} for x in (30.0, -15.0, 5.0, 40.0)]
        self.assertEqual(fs.sign_share(ev), 0.667)

    def test_bins(self):
        ev = [{"a": 1.0, "dur_s": 0.5, "turn_deg": 10.0},
              {"a": 1.0, "dur_s": 2.5, "turn_deg": 60.0},
              {"a": 0.5, "dur_s": 5.0, "turn_deg": 60.0}]
        rows = fs.bin_rows(ev)
        self.assertEqual([r["n"] for r in rows], [1, 0, 1, 1])
        self.assertEqual(rows[0]["median_rate"], 20.0)
        self.assertIsNone(rows[1]["median_deg"])
        self.assertEqual(rows[2]["median_rate"], 24.0)
        self.assertEqual(rows[2]["full_n"], 1)
        self.assertEqual(rows[3]["median_rate"], 24.0)
        self.assertEqual(rows[3]["full_n"], 0)

    def test_decide(self):
        s = {"turns": 200, "rides_with_turns": 50, "sign_share": 0.95, "gain": 28.0,
             "gyro_over_gain": 1.0,
             "bins": [{"n": 20, "median_rate": 10.0}, {"n": 0, "median_rate": None},
                      {"n": 30, "median_rate": 25.0}, {"n": 5, "median_rate": 26.0}]}
        d = fs.decide(s)
        self.assertTrue(d["check"]["ok"])
        self.assertTrue(d["d1_gyro_reads_dps"])
        self.assertTrue(d["d2_pulses_cost"])
        self.assertFalse(fs.decide(dict(s, gyro_over_gain=0.5))["d1_gyro_reads_dps"])
        self.assertFalse(fs.decide(dict(s, sign_share=0.8))["check"]["ok"])
        self.assertFalse(fs.decide(dict(s, turns=99))["check"]["ok"])
        few = dict(s, bins=[{"n": 5, "median_rate": 10.0}] + s["bins"][1:])
        self.assertIsNone(fs.decide(few)["d2_pulses_cost"])

    def test_write_outputs(self):
        compass = [sample(1002.5, 100.0), sample(1006.2, 70.0)]
        compass += [sample(1010.0 + k, 10.0 * k) for k in range(36)]
        pool = fs.new_pool()
        st = fs.analyse_ride(ctl([(30, 0, 0), (20, 0, 0.6), (40, 0, 0)]), None, compass, pool)
        with tempfile.TemporaryDirectory() as out:
            res = fs.write_outputs(out, [], [st], pool, time.monotonic())
            self.assertFalse(res["decision"]["check"]["ok"])
            self.assertEqual(res["results"]["turns"], 1)
            with open(os.path.join(out, "summary.json")) as f:
                self.assertEqual(json.load(f)["version"], fs.__version__)
            self.assertTrue(os.path.exists(os.path.join(out, "report.md")))
            self.assertTrue(os.path.exists(os.path.join(out, "events.jsonl")))


if __name__ == "__main__":
    unittest.main()
