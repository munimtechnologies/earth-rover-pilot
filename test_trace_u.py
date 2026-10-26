"""Tests for trace_u.py. By MV2 of Munim, Inc.; written with AI agents. Apache-2.0."""

import csv
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pace_t as pt  # noqa: E402
import pace_u as pu  # noqa: E402
import rover_pilot as rp  # noqa: E402
import trace_u as tu  # noqa: E402

PROFILE, SEED = "blocked30", 388


class TraceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # In a tuple: a function kept as a class attribute would come back bound.
        cls.saved = (pt._warming, rp.Pilot._stuck)
        cls.plain = pu.fly(tu.COURSE, SEED, PROFILE, "warm10", tu.CRUISE)
        cls.traced, cls.calls = tu.fly_traced(PROFILE, "warm10", SEED)
        cls.shipped, cls.shipped_calls = tu.fly_traced(PROFILE, "a0.3", SEED)

    def test_the_trace_leaves_the_mission_alone(self):
        self.assertEqual(json.loads(json.dumps(self.traced)), json.loads(json.dumps(self.plain)))

    def test_restored(self):
        self.assertIs(pt._warming, self.saved[0])
        self.assertIs(rp.Pilot._stuck, self.saved[1])

    def test_as_recorded(self):
        for variant, r in (("warm10", self.traced), ("a0.3", self.shipped)):
            with self.subTest(variant=variant):
                want = tu.MISSIONS[(PROFILE, variant, SEED)]
                self.assertEqual((r["elapsed_s"], r["stuck"]["recovery_t"]), want)

    def test_rows_read_the_check(self):
        for variant, calls, r in (("warm10", self.calls, self.traced),
                                  ("a0.3", self.shipped_calls, self.shipped)):
            with self.subTest(variant=variant):
                warmup = pu.VARIANTS[variant].get("warmup_s", 0.0)
                self.assertGreater(len(calls), 100)
                ts = [x["t"] for x in calls]
                self.assertEqual(ts, sorted(ts))
                self.assertLessEqual(ts[-1], tu.UNTIL_S)
                self.assertTrue(calls[0]["cleared"])
                self.assertIsNone(calls[0]["gap_s"])
                for x in calls:
                    self.assertEqual(set(x), set(tu.FIELDS))
                    # Rounded times: leave out calls within 0.05 s of the warm-up's end.
                    if x["t"] - x["warm_from"] < warmup - 0.05:
                        # The warm-up holds the verdict before the history is kept.
                        self.assertEqual(x["n"], 0)
                        self.assertFalse(x["verdict"])
                    elif x["t"] - x["warm_from"] > warmup + 0.05:
                        self.assertGreaterEqual(x["n"], 1)
                    if x["verdict"]:
                        self.assertTrue(x["full"])
                        self.assertFalse(x["slow"])
                        self.assertLess(x["moved_m"], 1.5)
                verdicts = [x["t"] for x in calls if x["verdict"]]
                want = [t for t in r["stuck"]["recovery_t"] if t <= tu.UNTIL_S]
                self.assertEqual(len(verdicts), len(want))
                for a, b in zip(verdicts, want):
                    self.assertAlmostEqual(a, b, delta=0.06)
                # A verdict clears the history: the next call says so.
                for i, x in enumerate(calls[:-1]):
                    if x["verdict"]:
                        self.assertTrue(calls[i + 1]["cleared"])


def _call(t, cleared=False, full=False, verdict=False, slow=False, moved=2.0, gap=0.1,
          rec=0, stops=0, bridged=0.0, new_fix=False):
    return {"t": t, "gap_s": gap, "cleared": cleared, "full": full, "verdict": verdict,
            "slow": slow, "moved_m": moved, "new_fix": new_fix, "recoveries": rec,
            "telemetry_stops": stops, "tip_stops": 0, "bridged_s": bridged}


class HelperTests(unittest.TestCase):
    def test_clears(self):
        calls = [_call(0.0, cleared=True, gap=None), _call(0.25),
                 _call(3.5, cleared=True, gap=3.25, stops=1, new_fix=True),
                 _call(3.75, cleared=True, stops=1, bridged=0.5)]
        self.assertEqual(tu.clears(calls), [
            {"t": 0.0, "gap_s": None, "new_fix": False, "recoveries": None,
             "telemetry_stops": None, "tip_stops": None, "bridged_s": None},
            {"t": 3.5, "gap_s": 3.25, "new_fix": True, "recoveries": 0, "telemetry_stops": 1,
             "tip_stops": 0, "bridged_s": 0.0},
            {"t": 3.75, "gap_s": 0.1, "new_fix": False, "recoveries": 0, "telemetry_stops": 0,
             "tip_stops": 0, "bridged_s": 0.5}])

    def test_held(self):
        calls = [_call(1.0), _call(2.0, full=True, slow=True, moved=0.5),
                 _call(2.25, full=True, moved=1.75), _call(2.5, full=True, verdict=True, moved=1.0),
                 _call(3.0, full=True, moved=2.5)]
        self.assertEqual(tu.held(calls), [
            {"start": 2.0, "end": 2.25, "calls": 2, "slow": 1, "least_moved_m": 0.5},
            {"start": 3.0, "end": 3.0, "calls": 1, "slow": 0, "least_moved_m": 2.5}])

    def test_each_second(self):
        calls = [_call(t) for t in (0.0, 0.5, 1.25, 1.75, 2.0, 41.0)]
        self.assertEqual([x["t"] for x in tu.each_second(calls)], [0.0, 1.25, 2.0])


class MainTests(unittest.TestCase):
    def test_main_small(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(tu.main(["--out-dir", tmp, "--missions",
                                      "%s:warm10:%d" % (PROFILE, SEED)]), 0)
            with open(os.path.join(tmp, "summary.json"), encoding="utf-8") as f:
                s = json.load(f)
            self.assertTrue(s["all_as_recorded"])
            self.assertEqual(len(s["missions"]), 1)
            m = s["missions"][0]
            self.assertEqual((m["profile"], m["variant"], m["seed"]), (PROFILE, "warm10", SEED))
            self.assertTrue(m["as_recorded"])
            self.assertEqual(m["first_outage_s"], 664.5)
            with open(os.path.join(tmp, m["csv"]), encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
            self.assertEqual(len(rows), m["calls"])
            self.assertEqual(tuple(rows[0]), tu.FIELDS)
            self.assertTrue(os.path.exists(os.path.join(tmp, "report.md")))


if __name__ == "__main__":
    unittest.main()
