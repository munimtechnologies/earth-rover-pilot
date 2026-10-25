"""Tests for trace_r.py. By MV2 of Munim, Inc.; written with AI agents. Apache-2.0."""

import csv
import json
import math
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pace_h as ph  # noqa: E402
import pace_l as pl  # noqa: E402
import pace_r as pr  # noqa: E402
import trace_r as tr  # noqa: E402


class TraceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pilot, cls.rover = ph.BridgePilot, pl.SlipRover
        cls.plain = pr.fly(tr.COURSE, tr.SEED, tr.PROFILE, "track-12", tr.CRUISE)
        cls.traced, cls.rows = tr.fly_traced("track-12")

    def test_the_trace_leaves_the_mission_alone(self):
        self.assertEqual(json.loads(json.dumps(self.traced)), json.loads(json.dumps(self.plain)))

    def test_restored(self):
        self.assertIs(ph.BridgePilot, self.pilot)
        self.assertIs(pl.SlipRover, self.rover)

    def test_rows_read_the_rover(self):
        self.assertGreater(len(self.rows), 100)
        ts = [x["t"] for x in self.rows]
        self.assertEqual(ts, sorted(ts))
        self.assertEqual(len(set(ts)), len(ts))
        self.assertTrue(any(x["outage"] for x in self.rows))
        self.assertTrue(any(not x["outage"] for x in self.rows))
        with_err = [x for x in self.rows if x["err_m"] is not None]
        self.assertGreater(len(with_err), 100)
        for x in with_err:
            self.assertEqual(set(x), set(tr.FIELDS))
            self.assertAlmostEqual(x["err_m"], math.hypot(x["est_n"] - x["true_n"],
                                                          x["est_e"] - x["true_e"]), delta=0.03)
        # The tracker counts its restarts; the rows carry the count.
        self.assertTrue(all(x["restarts"] is not None for x in with_err))


class IntervalTests(unittest.TestCase):
    ROWS = [{"t": 0, "x": 1.0, "outage": False}, {"t": 1, "x": 9.0, "outage": True},
            {"t": 2, "x": 12.0, "outage": False}, {"t": 3, "x": None, "outage": True},
            {"t": 4, "x": 9.0, "outage": False}]

    def test_intervals(self):
        self.assertEqual(tr.intervals(self.ROWS, "x", 8.0), [
            {"start": 1, "end": 2, "peak": 12.0, "peak_t": 2, "outage_share": 0.5},
            {"start": 4, "end": 4, "peak": 9.0, "peak_t": 4, "outage_share": 0.0}])
        self.assertEqual(tr.intervals(self.ROWS, "x", 20.0), [])

    def test_outages(self):
        self.assertEqual(tr.outages(self.ROWS), [[1, 1], [3, 3]])

    def test_window(self):
        self.assertEqual([x["t"] for x in tr.window(self.ROWS, "x", half_s=1)], [1, 2, 3])
        self.assertEqual(tr.window([{"t": 0, "x": None}], "x"), [])

    def test_compare(self):
        want = {"a": 1, "b": [1, 2], "seed": 313, "variant": "track-12"}
        self.assertEqual(tr.compare({"a": 1, "b": (1, 2)}, want), [])
        self.assertEqual(tr.compare({"a": 2, "b": [1, 2]}, want), ["a"])


class MainTests(unittest.TestCase):
    def test_main_small(self):
        with tempfile.TemporaryDirectory() as tmp:
            r, _ = tr.fly_traced("a0.3-16")
            rec = dict(json.loads(json.dumps(r)), profile=tr.PROFILE, variant="a0.3-16",
                       cruise=tr.CRUISE, course=tr.COURSE, seed=tr.SEED)
            runs = os.path.join(tmp, "runs.jsonl")
            with open(runs, "w", encoding="utf-8") as f:
                f.write(json.dumps(rec) + "\n")
            out = os.path.join(tmp, "out")
            self.assertEqual(tr.main(["--out-dir", out, "--variants", "a0.3-16",
                                      "--check", runs]), 0)
            with open(os.path.join(out, "summary.json"), encoding="utf-8") as f:
                s = json.load(f)
            v = s["variants"]["a0.3-16"]
            self.assertEqual(v["check"], {"found": True, "different": []})
            self.assertGreater(v["rows"], 100)
            self.assertEqual(list(s["variants"]), ["a0.3-16"])
            with open(os.path.join(out, v["csv"]), encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
            self.assertEqual(len(rows), v["rows"])
            self.assertEqual(tuple(rows[0]), tr.FIELDS)
            self.assertTrue(os.path.exists(os.path.join(out, "report.md")))


if __name__ == "__main__":
    unittest.main()
