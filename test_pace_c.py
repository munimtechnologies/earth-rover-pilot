"""Tests for the heading-smoothing study on a Mini+ with a noisy compass.

Run: python -m unittest test_pace_c -v
"""

import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pace_b as pb  # noqa: E402
import pace_c as pc  # noqa: E402
import pace_study as ps  # noqa: E402


class FakeRover:
    """Returns whatever orientation and timestamp it is given; records commands."""

    def __init__(self):
        self.t = 0.0
        self.orientation = 0.0
        self.ts = 0.0
        self.sent = []
        self.name = "fake"

    def clock(self):
        return self.t

    def data(self):
        return {"orientation": self.orientation, "timestamp": self.ts, "latitude": 1.0}

    def control(self, linear, angular):
        self.sent.append((linear, angular))


def smoother(**kw):
    rover = FakeRover()
    return rover, pc.HeadingSmoother(rover, rover.clock, **kw)


def report(rover, s, t, orientation):
    rover.t = rover.ts = t
    rover.orientation = orientation
    return s.data()["orientation"]


class SmootherTests(unittest.TestCase):
    def test_gain_one_returns_the_report(self):
        rover, s = smoother(gain=1.0)
        self.assertEqual(report(rover, s, 0.0, 10.0), 10.0)
        self.assertEqual(report(rover, s, 0.5, 50.0), 50.0)
        self.assertEqual(report(rover, s, 1.0, 90.0), 90.0)

    def test_average_moves_part_of_the_way(self):
        rover, s = smoother(gain=0.5)
        self.assertEqual(report(rover, s, 0.0, 0.0), 0.0)
        self.assertEqual(report(rover, s, 0.5, 40.0), 20.0)
        self.assertEqual(report(rover, s, 1.0, 40.0), 30.0)
        self.assertEqual(s.reports, 3)

    def test_across_north(self):
        rover, s = smoother(gain=0.5)
        report(rover, s, 0.0, 350.0)
        # 10 is 20 deg clockwise of 350: half way is 0, not 180.
        self.assertEqual(report(rover, s, 0.5, 10.0), 0.0)

    def test_held_between_reports(self):
        rover, s = smoother(gain=0.5)
        report(rover, s, 0.0, 0.0)
        report(rover, s, 0.5, 40.0)
        rover.t = 0.7  # same timestamp: not a new report
        rover.orientation = 90.0
        self.assertEqual(s.data()["orientation"], 20.0)
        self.assertEqual(s.reports, 2)

    def test_turned_by_the_command(self):
        rover, s = smoother(gain=0.3, yaw_dps=48.0, lag_s=0.5)
        report(rover, s, 0.0, 100.0)
        s.control(0.0, 1.0)  # sent at 0 s, landing at 0.5 s
        # Commands landing in [0, 1.0]: 1.0 s at full angular, 48 deg. The report
        # agrees with the prediction, so the estimate is the report: no lag.
        self.assertEqual(report(rover, s, 1.5, 148.0), 148.0)
        self.assertEqual(rover.sent, [(0.0, 1.0)])

    def test_plain_average_lags_the_turn(self):
        rover, s = smoother(gain=0.3)
        report(rover, s, 0.0, 100.0)
        s.control(0.0, 1.0)
        self.assertAlmostEqual(report(rover, s, 1.5, 148.0), 114.4, places=9)

    def test_other_fields_and_bad_orientation_pass_through(self):
        rover, s = smoother(gain=0.5)
        self.assertEqual(s.data()["latitude"], 1.0)
        rover.orientation = None
        self.assertEqual(s.data(), {"orientation": None, "timestamp": 0.0, "latitude": 1.0})
        self.assertEqual(s.name, "fake")


class SetupTests(unittest.TestCase):
    def test_profiles_are_pace_bs(self):
        self.assertIs(pc.PROFILES["measured"], pb.PROFILES["measured"])
        self.assertIs(pc.PROFILES["measured-noise10"], pb.PROFILES["measured-noise10"])

    def test_variants(self):
        self.assertEqual(list(pc.VARIANTS),
                         ["shipped", "ema0.5", "ema0.3", "cf0.3", "cf0.3-yaw30"])
        self.assertIsNone(pc.VARIANTS["shipped"])
        m = pc.PROFILES["measured"]
        # cf0.3 predicts with the measured profile's own turn rate and latency.
        self.assertEqual(pc.VARIANTS["cf0.3"]["yaw_dps"], m["max_yaw_dps"])
        self.assertEqual(pc.VARIANTS["cf0.3"]["lag_s"], m["latency_s"])
        self.assertEqual(pc.VARIANTS["cf0.3-yaw30"]["yaw_dps"], 30.0)
        self.assertEqual(pc.CRUISES, (0.7, 0.8))


class FlyTests(unittest.TestCase):
    def test_shipped_is_pace_b(self):
        course = {"points": [(0.0, 0.0), (40.0, 0.0)], "checkpoints": [1]}
        self.assertEqual(pc.fly("short", 2, "measured", "shipped", 0.8, course=course),
                         pb.fly("short", 2, "measured", 0.8, course=course))

    def test_smoothed_short_course(self):
        course = {"points": [(0.0, 0.0), (60.0, 0.0)], "checkpoints": [1]}
        for variant in ("ema0.3", "cf0.3"):
            r = pc.fly("short", 1, "measured-noise10", variant, 1.0, course=course)
            self.assertTrue(r["ok"], (variant, r))
            self.assertEqual(r["route_m"], 60.0)
            self.assertGreater(r["elapsed_s"], 60.0 / ps.MINIPLUS_TOP_MPS)


def run(variant, cruise, course, seed, elapsed, ok=True, profile="measured"):
    return {"ok": ok, "reason": "mission completed" if ok else "timeout",
            "elapsed_s": elapsed, "reached": 4, "checkpoints": 4, "reports": 4,
            "recoveries": 0, "plans": 4, "route_m": 1000.0, "travelled_m": 1010.0,
            "made_good_mps": 1000.0 / elapsed, "ideal_mps": 1.0,
            "efficiency": 1000.0 / elapsed,
            "time_s": {"driving": elapsed, "turning": 0.0, "stopped": 0.0, "reversing": 0.0},
            "profile": profile, "variant": variant, "cruise": cruise, "course": course,
            "seed": seed}


class SummaryTests(unittest.TestCase):
    def runs(self):
        return [run("shipped", 0.8, "boulevard", 1, 1000.0),
                run("shipped", 0.8, "boulevard", 2, 1100.0),
                run("cf0.3", 0.8, "boulevard", 1, 900.0),
                run("cf0.3", 0.8, "boulevard", 2, 1000.0)]

    def test_shares(self):
        runs = self.runs()
        effects, largest = pc.variant_tallies(runs, ps.summarise(runs)["variant_effect"])
        self.assertEqual(len(effects), 1)
        e = effects[0]
        self.assertEqual((e["variant"], e["faster"], e["slower"], e["sign_test_p"]),
                         ("cf0.3", 2, 0, 0.5))
        # -100 s against the shipped median of 1050 s.
        self.assertEqual(e["median_time_diff_share"], -0.0952)
        self.assertEqual(largest, [{"profile": "measured", "variant": "cf0.3",
                                    "largest_median_diff_share": -0.0952}])

    def test_lost_completion(self):
        runs = [run("shipped", 0.8, "blocks", 1, 1000.0),
                run("cf0.3", 0.8, "blocks", 1, 3000.0, ok=False)]
        s = ps.summarise(runs)
        effects, largest = pc.variant_tallies(runs, s["variant_effect"])
        self.assertIsNone(effects[0]["median_time_diff_share"])
        self.assertIsNone(largest[0]["largest_median_diff_share"])
        self.assertEqual(s["verdicts"][0]["groups_lost"], 1)

    def test_write_outputs(self):
        class Args:
            seeds = 2
        with tempfile.TemporaryDirectory() as d:
            pc.write_outputs(d, self.runs(), 0.0, Args, True)
            with open(os.path.join(d, "summary.json")) as f:
                out = json.load(f)
            self.assertEqual(out["runs"], 4)
            self.assertEqual(out["completed"], 4)
            self.assertEqual(len(out["verdicts"]), 1)
            self.assertEqual(out["largest"][0]["largest_median_diff_share"], -0.0952)
            with open(os.path.join(d, "report.md")) as f:
                md = f.read()
            self.assertIn("| measured | cf0.3 | 0/1 | 0 | 0 | 0 | -0.0952 |", md)

    def test_main_small(self):
        course = {"points": [(0.0, 0.0), (30.0, 0.0)], "checkpoints": [1]}
        saved = dict(ps.COURSES)
        ps.COURSES.clear()
        ps.COURSES["tiny"] = course
        try:
            with tempfile.TemporaryDirectory() as d, redirect_stdout(io.StringIO()):
                pc.main(["--out-dir", d, "--seeds", "1", "--cruises", "1.0",
                         "--profiles", "measured", "--variants", "cf0.3"])
                with open(os.path.join(d, "summary.json")) as f:
                    out = json.load(f)
            # shipped (always flown) and cf0.3, one cruise, one course, one seed.
            self.assertEqual(out["runs"], 2)
            self.assertEqual(out["completed"], 2)
            self.assertTrue(out["done"])
        finally:
            ps.COURSES.clear()
            ps.COURSES.update(saved)


if __name__ == "__main__":
    unittest.main()
