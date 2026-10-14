"""Tests for the steering-gain study.

Run: python -m unittest test_gain_study -v
"""

import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import gain_study as gs  # noqa: E402
import rover_pilot as rp  # noqa: E402


def run(config, seed, elapsed, ok=True, mission="demo", profile="real-yaw30"):
    return {"ok": ok, "reason": "mission completed" if ok else "timeout",
            "elapsed_s": elapsed, "reached": 4 if ok else 1, "checkpoints": 4,
            "reports": 5 if ok else 1, "recoveries": 0, "travelled_m": 250.0,
            "config": config, "mission": mission, "profile": profile, "seed": seed}


SAME_CRUISE = gs.config_name({"cruise": 0.6, "max_angular": 1.0, "full_turn_deg": 30.0,
                              "turn_in_place_deg": 90.0})
FASTER_CRUISE = gs.config_name({"cruise": 1.0, "max_angular": 1.0, "full_turn_deg": 30.0,
                                "turn_in_place_deg": 90.0})


class ConfigTests(unittest.TestCase):
    def test_grid(self):
        self.assertEqual(len(gs.CONFIGS), 24)
        self.assertEqual(gs.BASELINE, "c0.6-a0.6-k60-t60")
        self.assertIn(SAME_CRUISE, gs.CONFIGS)
        self.assertEqual(SAME_CRUISE, "c0.6-a1-k30-t90")

    def test_baseline_is_the_default_steering(self):
        a = rp.Steering(**gs.steer_kw(gs.CONFIGS[gs.BASELINE]))
        b = rp.Steering()
        for name in ("cruise", "kp", "max_angular", "turn_in_place_deg", "slow_radius_m"):
            self.assertEqual(getattr(a, name), getattr(b, name), name)

    def test_profiles_move_like_the_recorded_rovers(self):
        for name, kw in gs.PROFILES.items():
            self.assertEqual(kw["max_speed_mps"], 0.79, name)
            self.assertEqual(kw["gps_delay_s"], 1.5, name)
        self.assertEqual(gs.PROFILES["real-yaw30"]["max_yaw_dps"], 30.0)


class StatsTests(unittest.TestCase):
    def test_sign_test_p(self):
        self.assertIsNone(gs.sign_test_p(0, 0))
        self.assertAlmostEqual(gs.sign_test_p(5, 0), 0.0625)
        self.assertAlmostEqual(gs.sign_test_p(0, 5), 0.0625)
        self.assertEqual(gs.sign_test_p(3, 3), 1.0)

    def test_summarise_and_pick(self):
        runs = [run(gs.BASELINE, s, 100.0 + s) for s in range(1, 7)]
        runs += [run(SAME_CRUISE, s, 90.0 + s) for s in range(1, 7)]
        runs += [run(FASTER_CRUISE, s, 60.0 + s) for s in range(1, 6)]
        runs += [run(FASTER_CRUISE, 6, None, ok=False)]
        rows, paired, ranking = gs.summarise(runs)
        self.assertEqual(len(rows), 3)
        by = {p["config"]: p for p in paired}
        self.assertEqual(set(by), {SAME_CRUISE, FASTER_CRUISE})
        self.assertEqual(by[SAME_CRUISE]["faster"], 6)
        self.assertEqual(by[SAME_CRUISE]["slower"], 0)
        self.assertAlmostEqual(by[SAME_CRUISE]["sign_test_p"], 0.03125, delta=0.0002)
        self.assertEqual(by[FASTER_CRUISE]["only_baseline_completed"], 1)
        rank = {x["config"]: x for x in ranking}
        self.assertEqual(rank[gs.BASELINE]["time_ratio"], 1.0)
        self.assertAlmostEqual(rank[SAME_CRUISE]["time_ratio"], 0.9, places=2)
        self.assertEqual(rank[SAME_CRUISE]["groups_faster"], 1)
        self.assertEqual(rank[FASTER_CRUISE]["groups_lost"], 1)
        # The one that dropped a mission ranks last and is never picked.
        self.assertEqual(ranking[-1]["config"], FASTER_CRUISE)
        self.assertEqual(gs.pick(ranking)["config"], SAME_CRUISE)
        self.assertEqual(gs.pick(ranking, cruise=0.6)["config"], SAME_CRUISE)
        self.assertIsNone(gs.pick(ranking, cruise=1.0))


class FlyTests(unittest.TestCase):
    def test_baseline_flies_the_demo_on_a_real_like_rover(self):
        r = gs.fly("demo", 1, gs.PROFILES["real-yaw30"], gs.steer_kw(gs.CONFIGS[gs.BASELINE]),
                   1500.0)
        self.assertTrue(r["ok"], r)
        self.assertEqual(r["reached"], 4)
        # Checkpoints count from 10 m, so the rover drives a little less than the straight legs.
        self.assertGreater(r["travelled_m"], gs.straight_m(gs.MISSIONS["demo"]) * 0.5)

    def test_main_writes_outputs(self):
        with tempfile.TemporaryDirectory() as d, redirect_stdout(io.StringIO()):
            code = gs.main(["--out-dir", d, "--seeds", "1", "--missions", "demo",
                            "--profiles", "real-yaw30", "--configs", SAME_CRUISE])
            self.assertEqual(code, 0)
            with open(os.path.join(d, "summary.json")) as f:
                summary = json.load(f)
            with open(os.path.join(d, "report.md")) as f:
                report = f.read()
        self.assertEqual(summary["runs"], 2)
        self.assertTrue(summary["done"])
        self.assertEqual({x["config"] for x in summary["ranking"]}, {gs.BASELINE, SAME_CRUISE})
        self.assertIn(gs.BASELINE, report)

    def test_unknown_config_is_refused(self):
        with self.assertRaises(SystemExit):
            gs.main(["--configs", "c9-a9-k9-t9", "--seeds", "1"])


if __name__ == "__main__":
    unittest.main()
