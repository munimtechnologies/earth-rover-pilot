"""Tests for the marathon pace study on a Mini+ that reports like the measured one.

Run: python -m unittest test_pace_b -v
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
import pace_study as ps  # noqa: E402


def run(profile, cruise, course, seed, elapsed, ok=True):
    return {"ok": ok, "reason": "mission completed" if ok else "timeout",
            "elapsed_s": elapsed, "reached": 4, "checkpoints": 4, "reports": 4,
            "recoveries": 0, "plans": 4, "route_m": 1000.0, "travelled_m": 1010.0,
            "made_good_mps": 1000.0 / elapsed, "ideal_mps": 1.0,
            "efficiency": 1000.0 / elapsed,
            "time_s": {"driving": elapsed, "turning": 0.0, "stopped": 0.0, "reversing": 0.0},
            "profile": profile, "variant": "shipped", "cruise": cruise, "course": course,
            "seed": seed}


class ProfileTests(unittest.TestCase):
    def test_baselines_are_pace_studys(self):
        self.assertEqual(list(pb.PROFILES)[:2], ["fresh", "mini+"])
        self.assertIs(pb.PROFILES["fresh"], ps.PROFILES["fresh"])
        self.assertIs(pb.PROFILES["mini+"], ps.PROFILES["mini+"])

    def test_measured(self):
        m = pb.PROFILES["measured"]
        self.assertEqual(m["max_yaw_dps"], 48.0)
        self.assertEqual(m["latency_s"], 0.5)
        self.assertEqual(m["orientation_period_s"], 0.5)
        self.assertEqual(m["gps_period_s"], 2.0)
        self.assertTrue(m["stale_orientation"])
        self.assertEqual(m["max_speed_mps"], ps.MINIPLUS_TOP_MPS)

    def test_variants_change_one_thing(self):
        m = pb.PROFILES["measured"]
        for name, key in (("measured-lag0.8", "latency_s"),
                          ("measured-noise10", "compass_noise_deg")):
            p = pb.PROFILES[name]
            self.assertEqual({k for k in p if p[k] != m.get(k)}, {key}, name)
        self.assertEqual(pb.PROFILES["measured-lag0.8"]["latency_s"], 0.8)
        self.assertEqual(pb.PROFILES["measured-noise10"]["compass_noise_deg"], 10.0)


class RoverTests(unittest.TestCase):
    def drive(self, rover):
        seen = []
        rover.control(0.5, 0.3)
        rover.sleep(3.0)
        seen.append(rover.data())
        rover.control(1.0, -0.2)
        rover.sleep(2.5)
        seen.append(rover.data())
        return seen, rover.heading, rover.travelled

    def test_period_zero_is_a_study_rover(self):
        a = ps.StudyRover([(50.0, 0.0)], seed=3, **ps.PROFILES["mini+"])
        b = pb.MeasuredRover([(50.0, 0.0)], seed=3, **pb.PROFILES["mini+"])
        self.assertEqual(self.drive(a), self.drive(b))

    def stamps(self, profile):
        sim = pb.MeasuredRover([(50.0, 0.0)], seed=1, **pb.PROFILES[profile])
        sim.control(0.0, 1.0)
        stamps = set()
        for _ in range(40):  # 4 s, one 0.1 s step at a time
            sim.sleep(0.1)
            stamps.add(sim.data()["timestamp"])
        return stamps

    def test_refreshed_every_half_second(self):
        # Reports at about 0.5, 1.0, ... 4.0 s, plus the first at 0 s.
        self.assertGreaterEqual(len(self.stamps("measured")), 8)
        # pace_study's Mini+ reports only with each 2 s GPS fix.
        self.assertLessEqual(len(self.stamps("mini+")), 3)

    def test_held_between_refreshes(self):
        sim = pb.MeasuredRover([(50.0, 0.0)], seed=1, **pb.PROFILES["measured"])
        sim.control(0.0, 1.0)
        sim.sleep(1.2)
        self.assertEqual(sim.data(), sim.data())


class FlyTests(unittest.TestCase):
    def test_short_course(self):
        course = {"points": [(0.0, 0.0), (60.0, 0.0)], "checkpoints": [1]}
        r = pb.fly("short", 1, "measured", 1.0, course=course)
        self.assertTrue(r["ok"], r)
        self.assertGreater(r["elapsed_s"], 60.0 / ps.MINIPLUS_TOP_MPS)
        self.assertEqual(r["route_m"], 60.0)
        self.assertAlmostEqual(sum(r["time_s"].values()), r["elapsed_s"], delta=0.5)

    def test_same_as_pace_study_on_its_own_profiles(self):
        course = {"points": [(0.0, 0.0), (40.0, 0.0)], "checkpoints": [1]}
        for profile in ("fresh", "mini+"):
            self.assertEqual(pb.fly("short", 2, profile, 0.8, course=course),
                             ps.fly("short", 2, profile, "shipped", 0.8, course=course),
                             profile)


class SummaryTests(unittest.TestCase):
    def runs(self):
        return [run("mini+", 1.0, "boulevard", 1, 1000.0),
                run("mini+", 1.0, "boulevard", 2, 1100.0),
                run("measured", 1.0, "boulevard", 1, 900.0),
                run("measured", 1.0, "boulevard", 2, 1000.0),
                run("measured", 0.6, "boulevard", 1, 1500.0)]

    def test_pair_effects(self):
        effects, tallies = pb.pair_effects(self.runs())
        # Only measured against mini+ at cruise 1.0 has both sides.
        self.assertEqual(len(effects), 1)
        e = effects[0]
        self.assertEqual((e["profile"], e["against"], e["cruise"]), ("measured", "mini+", 1.0))
        self.assertEqual((e["faster"], e["slower"], e["sign_test_p"]), (2, 0, 0.5))
        self.assertEqual(e["median_time_diff_s"], -100.0)
        # -100 s against a median of 1050 s.
        self.assertEqual(e["median_time_diff_share"], -0.0952)
        self.assertEqual(tallies, [{"profile": "measured", "against": "mini+", "groups": 1,
                                    "groups_faster": 0, "groups_slower": 0,
                                    "groups_lost": 0, "groups_gained": 0,
                                    "largest_median_diff_share": -0.0952}])

    def test_lost_completion(self):
        runs = [run("measured", 0.8, "blocks", 1, 1000.0),
                run("measured-noise10", 0.8, "blocks", 1, 3000.0, ok=False)]
        _, tallies = pb.pair_effects(runs)
        self.assertEqual(len(tallies), 1)
        self.assertEqual(tallies[0]["groups_lost"], 1)
        self.assertIsNone(tallies[0]["largest_median_diff_share"])

    def test_write_outputs(self):
        class Args:
            seeds = 2
        with tempfile.TemporaryDirectory() as d:
            pb.write_outputs(d, self.runs(), 0.0, Args, True)
            with open(os.path.join(d, "summary.json")) as f:
                out = json.load(f)
            self.assertEqual(out["runs"], 5)
            self.assertEqual(out["completed"], 5)
            self.assertEqual(len(out["pair_tallies"]), 1)
            with open(os.path.join(d, "report.md")) as f:
                md = f.read()
            self.assertIn("29 h 38 min", md)
            self.assertIn("| measured | mini+ | 0/1 |", md)

    def test_main_small(self):
        course = {"points": [(0.0, 0.0), (30.0, 0.0)], "checkpoints": [1]}
        saved = dict(ps.COURSES)
        ps.COURSES.clear()
        ps.COURSES["tiny"] = course
        try:
            with tempfile.TemporaryDirectory() as d, redirect_stdout(io.StringIO()):
                pb.main(["--out-dir", d, "--seeds", "1", "--cruises", "1.0",
                         "--profiles", "measured"])
                with open(os.path.join(d, "summary.json")) as f:
                    out = json.load(f)
            # fresh (always flown) and measured, one cruise, one course, one seed.
            self.assertEqual(out["runs"], 2)
            self.assertEqual(out["completed"], 2)
            self.assertTrue(out["done"])
        finally:
            ps.COURSES.clear()
            ps.COURSES.update(saved)


if __name__ == "__main__":
    unittest.main()
