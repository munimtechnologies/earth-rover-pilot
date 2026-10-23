"""Tests for the study of whether bridging GPS gaps should be the default.

Run: python -m unittest test_pace_i -v
"""

import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pace_d as pd  # noqa: E402
import pace_h as ph  # noqa: E402
import pace_i as pi  # noqa: E402
import pace_study as ps  # noqa: E402
import rover_pilot as rp  # noqa: E402

TINY = {"points": [(0.0, 0.0), (30.0, 0.0)], "checkpoints": [1]}
LONG = {"points": [(0.0, 0.0), (400.0, 0.0)], "checkpoints": [1]}
CORNER = {"points": [(0.0, 0.0), (40.0, 0.0), (40.0, 40.0)], "checkpoints": [1, 2]}


class tiny_courses:
    """Replace pace_study's courses with one short course while in use."""

    def __enter__(self):
        self.saved = dict(ps.COURSES)
        ps.COURSES.clear()
        ps.COURSES["tiny"] = TINY

    def __exit__(self, *exc):
        ps.COURSES.clear()
        ps.COURSES.update(self.saved)


class SetupTests(unittest.TestCase):
    def test_profiles(self):
        self.assertEqual(list(pi.PROFILES), ["measured", "outage15", "outage45"])
        self.assertEqual(pi.PROFILES["measured"], ph.PROFILES["measured"])
        for name, (outage, clear) in (("outage15", (15.0, 150.0)), ("outage45", (45.0, 300.0))):
            with self.subTest(profile=name):
                p = dict(pi.PROFILES[name])
                self.assertEqual((p.pop("outage_s"), p.pop("clear_s")), (outage, clear))
                self.assertEqual(p, ph.PROFILES["measured"])
        self.assertEqual(pi.BASE_PROFILE, "measured")

    def test_variants(self):
        self.assertEqual(list(pi.VARIANTS),
                         ["cf0.3", "bridge+cf0.3", "bridge-r+cf0.3", "dr+cf0.3"])
        for name in ("cf0.3", "bridge+cf0.3", "dr+cf0.3"):
            self.assertEqual(pi.VARIANTS[name], ph.VARIANTS[name])
        r = dict(pi.VARIANTS["bridge-r+cf0.3"])
        self.assertTrue(r.pop("reset_gps"))
        self.assertEqual(r, ph.VARIANTS["bridge+cf0.3"])
        self.assertEqual(pi.BASE_VARIANT, "cf0.3")
        for a, b in pi.PAIRS:
            self.assertIn(a, pi.VARIANTS)
            self.assertIn(b, pi.VARIANTS)
        self.assertEqual(len(pi.PAIRS), 5)
        self.assertEqual(pi.CRUISES, (0.8,))
        self.assertEqual(pi.FIRST_SEED, 85)
        self.assertEqual(pi.CHECKED, {"profiles": ("measured",),
                                      "variants": ("cf0.3", "bridge+cf0.3"),
                                      "seeds": (61, 62, 63)})


class OutageTests(unittest.TestCase):
    def test_windows(self):
        w = pi.outage_windows(5, 15.0, 150.0)
        self.assertEqual(w, pi.outage_windows(5, 15.0, 150.0))
        self.assertNotEqual(w, pi.outage_windows(6, 15.0, 150.0))
        self.assertGreater(w[0][0], 0.0)
        for (a, b), (c, _) in zip(w, w[1:]):
            self.assertAlmostEqual(b - a, 15.0)
            self.assertGreaterEqual(c, b)
        out = sum(min(b, pi.OUTAGE_HORIZON_S) - a for a, b in w) / pi.OUTAGE_HORIZON_S
        self.assertGreater(out, 0.06)
        self.assertLess(out, 0.13)

    def test_no_windows_without_outages(self):
        self.assertEqual(pi.outage_windows(5, 0.0, 150.0), [])
        sim = pi.OutageRover([(100.0, 0.0)], seed=5, **pi.PROFILES["measured"])
        self.assertEqual(sim.outages, [])
        self.assertFalse(sim.in_outage(10.0))

    def test_in_outage(self):
        sim = pi.OutageRover([(100.0, 0.0)], seed=5, **pi.PROFILES["outage15"])
        a, b = sim.outages[1]
        self.assertTrue(sim.in_outage(a))
        self.assertTrue(sim.in_outage((a + b) / 2.0))
        self.assertFalse(sim.in_outage(b))
        self.assertFalse(sim.in_outage(a - 0.01))

    def rovers(self, profile, seed=3):
        cps = [(2000.0, 0.0)]
        return (pd.DistortedRover(cps, seed=seed, **pi.PROFILES["measured"]),
                pi.OutageRover(cps, seed=seed, **pi.PROFILES[profile]))

    def test_rover_without_outages_is_pace_hs(self):
        plain, sim = self.rovers("measured")
        for _ in range(240):
            for r in (plain, sim):
                r.control(0.8, 0.05)
                r.sleep(0.5)
            self.assertEqual(sim.data(), plain.data())
        self.assertEqual(sim.withheld, 0)

    def test_no_fix_inside_an_outage(self):
        plain, sim = self.rovers("outage15")
        fixes = withheld = 0
        for _ in range(1600):  # 800 s
            for r in (plain, sim):
                r.control(0.8, 0.0)
                r.sleep(0.5)
            got, want = sim.data(), plain.data()
            # The rover's own draws are untouched: only the fix can differ.
            self.assertEqual(got["orientation"], want["orientation"])
            self.assertEqual(got["timestamp"], want["timestamp"])
            sampled_at = sim._next_gps_t - sim.gps_period_s
            if sim.in_outage(sampled_at):
                self.assertEqual(got["latitude"], rp.NO_FIX)
                self.assertEqual(got["gps_signal"], 0)
                withheld += 1
            else:
                self.assertEqual(got["latitude"], want["latitude"])
                self.assertEqual(got["longitude"], want["longitude"])
                fixes += 1
        self.assertGreater(sim.withheld, 0)
        self.assertGreater(withheld, 0)
        self.assertGreater(fixes, withheld)


class ResettingGpsFilterTests(unittest.TestCase):
    def test_blends_like_the_filter_without_a_gap(self):
        plain, reset = rp.GpsFilter(), pi.ResettingGpsFilter()
        for k, t in enumerate((0.0, 2.0, 4.0, 6.0)):
            fix = (37.0 + k * 1e-5, -122.0)
            self.assertEqual(reset.update(*fix, t), plain.update(*fix, t))
            self.assertEqual((reset.lat, reset.lon), (plain.lat, plain.lon))
        self.assertEqual(reset.resets, 0)

    def test_starts_again_after_a_gap(self):
        f = pi.ResettingGpsFilter()
        f.update(37.0, -122.0, 0.0)
        f.update(37.00001, -122.0, 2.0)
        f.update(rp.NO_FIX, rp.NO_FIX, 4.0)
        fix = (37.0002, -122.0)
        self.assertEqual(f.update(*fix, 20.0), fix)
        self.assertEqual((f.lat, f.lon), fix)
        self.assertEqual(f.resets, 1)
        self.assertTrue(f.has_fix(20.0))
        plain = rp.GpsFilter()
        plain.update(37.0, -122.0, 0.0)
        plain.update(37.00001, -122.0, 2.0)
        plain.update(*fix, 20.0)
        self.assertNotEqual((plain.lat, plain.lon), fix)

    def test_held_fix_is_not_a_gap(self):
        f = pi.ResettingGpsFilter()
        for k in range(50):  # the same fix read every 0.1 s for 5 s
            f.update(37.0, -122.0, k * 0.1)
        f.update(37.00001, -122.0, 5.0)
        self.assertEqual(f.resets, 0)


class FlyTests(unittest.TestCase):
    def test_flies_as_pace_h(self):
        for variant, seed in (("cf0.3", 1), ("bridge+cf0.3", 2), ("dr+cf0.3", 3)):
            with self.subTest(variant=variant):
                want = ph.fly("corner", seed, "measured", variant, 0.8, course=CORNER)
                got = pi.fly("corner", seed, "measured", variant, 0.8, course=CORNER)
                self.assertTrue(want["ok"], want["reason"])
                for k in want:
                    self.assertEqual(got[k], want[k], k)
                self.assertEqual(got["outage"], {"withheld": 0, "gps_resets": None})

    def test_reset_variant_flies(self):
        r = pi.fly("corner", 1, "measured", "bridge-r+cf0.3", 0.8, course=CORNER)
        self.assertTrue(r["ok"], r["reason"])
        self.assertEqual(r["reached"], 2)
        self.assertGreaterEqual(r["outage"]["gps_resets"], 0)

    def test_outages_flown(self):
        withheld = bridged = 0
        for seed in (1, 2, 3):
            for variant in ("cf0.3", "bridge-r+cf0.3"):
                with self.subTest(seed=seed, variant=variant):
                    r = pi.fly("long", seed, "outage15", variant, 0.8, course=LONG)
                    self.assertTrue(r["ok"], r["reason"])
                    withheld += r["outage"]["withheld"]
                    if r["dead_reckon"] is not None:
                        bridged += r["dead_reckon"]["bridged_s"] > 0
        self.assertGreater(withheld, 0)

    def test_failed_run_fields(self):
        r = pi.failed_run(ValueError("boom"))
        self.assertFalse(r["ok"])
        self.assertEqual(r["outage"], {"withheld": None, "gps_resets": None})
        self.assertEqual(r["steer"], {"n": 0, "mean_abs_angular": None})


class CheckTests(unittest.TestCase):
    def test_check_against_pace_h(self):
        with tiny_courses():
            ref = []
            for seed in (61, 62):
                r = ph.fly("tiny", seed, "measured", "cf0.3", 0.8)
                r.update(profile="measured", variant="cf0.3", cruise=0.8, course="tiny",
                         seed=seed)
                ref.append(r)
            ref[1]["elapsed_s"] += 1.0
            with tempfile.TemporaryDirectory() as d:
                path = os.path.join(d, "runs.jsonl")
                with open(path, "w", encoding="utf-8") as f:
                    for r in ref:
                        f.write(json.dumps(r) + "\n")
                    f.write("\n")
                out = pi.check_pace_h(path)
        # 1 profile x 2 variants x 1 course x 3 seeds = 6 missions checked; the
        # reference has 2 of them, and seed 62 was altered.
        self.assertEqual((out["compared"], out["identical"], out["missing"]), (2, 1, 4))
        self.assertEqual(len(out["different"]), 1)
        self.assertEqual(out["different"][0]["seed"], 62)
        self.assertEqual(out["different"][0]["fields"], ["elapsed_s"])


def _run(variant, seed, elapsed, ok=True, course="blocks", profile="outage15", withheld=4,
         stopped=10.0, resets=None):
    return {"profile": profile, "variant": variant, "cruise": 0.8, "course": course,
            "seed": seed, "ok": ok, "elapsed_s": elapsed, "time_s": {"stopped": stopped},
            "outage": {"withheld": withheld, "gps_resets": resets}}


class SummaryTests(unittest.TestCase):
    def test_pair_effects(self):
        runs = ([_run("cf0.3", s, 100.0) for s in range(1, 7)]
                + [_run("bridge-r+cf0.3", s, 90.0) for s in range(1, 7)])
        effects, tallies = pi.pair_effects(runs)
        self.assertEqual(len(effects), 1)
        self.assertEqual((effects[0]["faster"], effects[0]["slower"]), (6, 0))
        self.assertEqual(effects[0]["median_time_diff_share"], -0.1)
        self.assertEqual(tallies, [{"profile": "outage15", "variant": "bridge-r+cf0.3",
                                    "against": "cf0.3", "groups": 1, "groups_faster": 1,
                                    "groups_slower": 0, "groups_lost": 0, "groups_gained": 0,
                                    "largest_median_diff_share": -0.1}])

    def test_outage_rows(self):
        runs = [_run("bridge-r+cf0.3", 1, 100.0, withheld=2, stopped=4.0, resets=1),
                _run("bridge-r+cf0.3", 2, 100.0, withheld=6, stopped=8.0, resets=3),
                _run("bridge-r+cf0.3", 3, None, ok=False, withheld=50, stopped=90.0, resets=9),
                _run("cf0.3", 1, 100.0, withheld=4, stopped=20.0)]
        self.assertEqual(pi.outage_rows(runs), [
            {"profile": "outage15", "variant": "bridge-r+cf0.3", "cruise": 0.8,
             "course": "blocks", "missions": 2, "median_withheld": 4.0,
             "median_stopped_s": 6.0, "median_gps_resets": 2.0},
            {"profile": "outage15", "variant": "cf0.3", "cruise": 0.8, "course": "blocks",
             "missions": 1, "median_withheld": 4.0, "median_stopped_s": 20.0,
             "median_gps_resets": None}])

    def test_main_small(self):
        with tiny_courses():
            with tempfile.TemporaryDirectory() as d, redirect_stdout(io.StringIO()):
                pi.main(["--out-dir", d, "--first-seed", "85", "--seeds", "2",
                         "--profiles", "outage45", "--variants", "bridge-r+cf0.3"])
                with open(os.path.join(d, "summary.json")) as f:
                    out = json.load(f)
                with open(os.path.join(d, "report.md")) as f:
                    md = f.read()
                with open(os.path.join(d, "runs.jsonl")) as f:
                    lines = [json.loads(x) for x in f if x.strip()]
        # measured and cf0.3 are always flown: 2 profiles x 2 variants x 2 seeds.
        self.assertEqual(out["runs"], 8)
        self.assertEqual(out["seeds"], [85, 86])
        self.assertEqual(sorted({r["seed"] for r in lines}), [85, 86])
        self.assertTrue(out["done"])
        self.assertEqual(sorted((v["profile"], v["variant"], v["against"])
                                for v in out["verdicts"]),
                         [("measured", "bridge-r+cf0.3", "cf0.3"),
                          ("outage45", "bridge-r+cf0.3", "cf0.3")])
        self.assertEqual(len(out["outage"]), 4)
        self.assertEqual(len(out["steer"]), 4)
        self.assertIsNone(out["check"])
        self.assertIn("## GPS outages", md)
        self.assertIn("Seeds 85-86.", md)


if __name__ == "__main__":
    unittest.main()
