"""Tests for trace_s.py. By MV2 of Munim, Inc.; written with AI agents. Apache-2.0."""

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
import pace_s as pz  # noqa: E402
import trace_s as ts  # noqa: E402

PROFILE, SEED = "outage90", 338


class TraceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pilot, cls.rover = ph.BridgePilot, pl.SlipRover
        cls.plain = pz.fly(ts.COURSE, SEED, PROFILE, "restart", ts.CRUISE)
        cls.traced, cls.rows = ts.fly_traced(PROFILE, "restart", SEED)

    def test_the_trace_leaves_the_mission_alone(self):
        self.assertEqual(json.loads(json.dumps(self.traced)), json.loads(json.dumps(self.plain)))

    def test_restored(self):
        self.assertIs(ph.BridgePilot, self.pilot)
        self.assertIs(pl.SlipRover, self.rover)

    def test_rows_read_the_rover(self):
        self.assertGreater(len(self.rows), 100)
        ts_ = [x["t"] for x in self.rows]
        self.assertEqual(ts_, sorted(ts_))
        self.assertEqual(len(set(ts_)), len(ts_))
        self.assertTrue(any(x["outage"] for x in self.rows))
        self.assertTrue(any(not x["outage"] for x in self.rows))
        for x in self.rows:
            self.assertEqual(set(x), set(ts.FIELDS))
            self.assertIn(x["has_fix"], (True, False))
            if x["cp_m"] is not None:
                self.assertGreaterEqual(x["cp_m"], 0.0)
        reached = [x["reached"] for x in self.rows]
        self.assertEqual(reached, sorted(reached))
        self.assertGreaterEqual(reached[-1], 1)
        bridged = [x["bridged_s"] for x in self.rows]
        self.assertEqual(bridged, sorted(bridged))
        self.assertGreater(bridged[-1], 0.0)
        # The restarting filter counts its restarts; the rows carry the count.
        self.assertTrue(all(x["restarts"] is not None for x in self.rows))
        # Some rows have the rover driving, and the stops found are at least STOP_S long.
        self.assertTrue(any(x["lin"] > 0 for x in self.rows))
        for s in ts.stops(self.rows):
            self.assertGreaterEqual(s["end"] - s["start"] + ts.EVERY_S, ts.STOP_S)


def _row(t, lin, outage=False, has_fix=True, reached=1, cp_m=3.0, rec=0, n=0.0, e=0.0):
    return {"t": t, "lin": lin, "ang": 0.0, "outage": outage, "has_fix": has_fix,
            "reached": reached, "cp_m": cp_m, "recoveries": rec, "err_m": 1.0,
            "true_n": n, "true_e": e}


class HelperTests(unittest.TestCase):
    def test_stops(self):
        rows = ([_row(0, 0.5)]
                + [_row(1, 0.0, outage=True, has_fix=False), _row(2, 0.0, outage=True)]
                + [_row(t, 0.0) for t in (3, 4, 5)]
                + [_row(6, 0.5), _row(7, 0.0)])
        self.assertEqual(ts.stops(rows), [
            {"start": 1, "end": 5, "outage_share": 0.4, "has_fix": False, "reached": 1,
             "cp_m": 3.0}])
        # A turn on the spot is not a stop.
        turning = [dict(_row(t, 0.0), ang=0.6) for t in range(6)]
        self.assertEqual(ts.stops(turning), [])

    def test_changes(self):
        rows = [_row(0, 0.5, rec=0), _row(1, 0.5, rec=0), _row(2, 0.5, rec=1),
                dict(_row(3, 0.5), recoveries=None), _row(4, 0.5, rec=2)]
        got = ts.changes(rows, "recoveries")
        self.assertEqual([(x["t"], x["recoveries"]) for x in got], [(2, 1), (4, 2)])

    def test_diverged(self):
        a = [_row(0, 0.5), _row(1, 0.5, n=1.0)]
        self.assertIsNone(ts.diverged(a, [dict(x) for x in a]))
        self.assertEqual(ts.diverged(a, [_row(0, 0.5), _row(1, 0.5, n=1.5)]), 1)
        self.assertEqual(ts.diverged(a, [_row(0, 0.5), _row(2, 0.5, n=1.0)]), 1)


class MainTests(unittest.TestCase):
    def test_main_small(self):
        with tempfile.TemporaryDirectory() as tmp:
            runs = os.path.join(tmp, "runs.jsonl")
            elapsed = {}
            with open(runs, "w", encoding="utf-8") as f:
                for variant in ts.VARIANTS:
                    r = pz.fly(ts.COURSE, SEED, PROFILE, variant, ts.CRUISE)
                    elapsed[variant] = r["elapsed_s"]
                    r.update(profile=PROFILE, variant=variant, cruise=ts.CRUISE,
                             course=ts.COURSE, seed=SEED)
                    f.write(json.dumps(r) + "\n")
            out = os.path.join(tmp, "out")
            self.assertEqual(ts.main(["--out-dir", out, "--missions", "%s:%d" % (PROFILE, SEED),
                                      "--check", runs]), 0)
            with open(os.path.join(out, "summary.json"), encoding="utf-8") as f:
                s = json.load(f)
            self.assertEqual(len(s["missions"]), 1)
            m = s["missions"][0]
            self.assertEqual((m["profile"], m["seed"]), (PROFILE, SEED))
            self.assertEqual(list(m["variants"]), list(ts.VARIANTS))
            for variant, v in m["variants"].items():
                self.assertEqual(v["check"], {"found": True, "different": []})
                self.assertEqual(v["record"]["elapsed_s"], elapsed[variant])
                with open(os.path.join(out, v["csv"]), encoding="utf-8") as f:
                    rows = list(csv.DictReader(f))
                self.assertEqual(len(rows), v["rows"])
                self.assertEqual(tuple(rows[0]), ts.FIELDS)
            self.assertTrue(math.isclose(m["diff_s"], elapsed["restart"] - elapsed["a0.3"],
                                         abs_tol=0.05))
            self.assertTrue(os.path.exists(os.path.join(out, "report.md")))


if __name__ == "__main__":
    unittest.main()
