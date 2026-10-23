"""Tests for the study of bridging GPS outages when the GPS wanders first.

Run: python -m unittest test_pace_j -v
"""

import io
import json
import math
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pace_i as pi  # noqa: E402
import pace_j as pj  # noqa: E402
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
        self.assertEqual(list(pj.PROFILES), ["outage15", "wander15", "outage45", "wander45"])
        for a, b in pj.PROFILE_PAIRS:
            with self.subTest(profile=b):
                self.assertEqual(pj.PROFILES[a], pi.PROFILES[a])
                w = dict(pj.PROFILES[b])
                self.assertEqual((w.pop("wander_s"), w.pop("wander_m")), (20.0, 8.0))
                self.assertEqual(w, pi.PROFILES[a])
        self.assertEqual(pj.BASE_PROFILE, "outage15")

    def test_variants(self):
        self.assertEqual(list(pj.VARIANTS), ["cf0.3", "bridge+cf0.3", "dr+cf0.3"])
        for name, v in pj.VARIANTS.items():
            self.assertEqual(v, pi.VARIANTS[name])
        self.assertEqual(pj.BASE_VARIANT, "cf0.3")
        self.assertEqual(pj.CRUISES, (0.8,))
        self.assertEqual(pj.FIRST_SEED, 109)
        self.assertEqual(pj.CHECKED, {"profiles": ("outage15",),
                                      "variants": ("cf0.3", "bridge+cf0.3"),
                                      "seeds": (85, 86, 87)})


def clean_window(sim, room):
    """Index of an outage with at least `room` seconds of clear sky on each side."""
    for i, (a, b) in enumerate(sim.outages):
        before = a - (sim.outages[i - 1][1] if i else -1e9)
        after = (sim.outages[i + 1][0] if i + 1 < len(sim.outages) else 1e9) - b
        if before >= room and after >= room:
            return i
    raise AssertionError("no outage with %g s of sky on each side" % room)


class WanderTests(unittest.TestCase):
    def test_angles(self):
        a = pj.wander_angles(5, 4)
        self.assertEqual(a, pj.wander_angles(5, 4))
        self.assertNotEqual(a, pj.wander_angles(6, 4))
        self.assertEqual(len(a), 4)
        for x in a:
            self.assertGreaterEqual(x, 0.0)
            self.assertLess(x, 2.0 * math.pi)

    def test_one_angle_per_outage(self):
        sim = pj.WanderRover([(100.0, 0.0)], seed=5, **pj.PROFILES["wander15"])
        self.assertGreater(len(sim.outages), 10)
        self.assertEqual(sim._angles, pj.wander_angles(5, len(sim.outages)))

    def test_wander_at(self):
        sim = pj.WanderRover([(100.0, 0.0)], seed=5, **pj.PROFILES["wander15"])
        i = clean_window(sim, 2 * pj.WANDER_S + 1.0)
        a, b = sim.outages[i]
        ang = sim._angles[i]
        for t, metres in ((a - pj.WANDER_S - 1.0, 0.0), (a - 15.0, 2.0), (a - 10.0, 4.0),
                          ((a + b) / 2.0, 8.0), (b + 10.0, 4.0), (b + pj.WANDER_S + 1.0, 0.0)):
            with self.subTest(t=t - a):
                north, east = sim.wander_at(t)
                self.assertAlmostEqual(math.hypot(north, east), metres, places=9)
                if metres:
                    self.assertAlmostEqual(north, metres * math.cos(ang), places=9)
                    self.assertAlmostEqual(east, metres * math.sin(ang), places=9)

    def test_no_wander_without_it(self):
        sim = pj.WanderRover([(100.0, 0.0)], seed=5, **pj.PROFILES["outage15"])
        a, b = sim.outages[1]
        self.assertEqual(sim.wander_at(a - 5.0), (0.0, 0.0))
        self.assertEqual(sim.wander_at((a + b) / 2.0), (0.0, 0.0))

    def rovers(self, seed=3):
        cps = [(2000.0, 0.0)]
        return (pi.OutageRover(cps, seed=seed, **pi.PROFILES["outage15"]),
                pj.WanderRover(cps, seed=seed, **pj.PROFILES["wander15"]))

    def test_only_the_fix_moves(self):
        plain, sim = self.rovers()
        moved = same = 0
        for _ in range(1600):  # 800 s
            for r in (plain, sim):
                r.control(0.8, 0.0)
                r.sleep(0.5)
            got, want = sim.data(), plain.data()
            # The rover's own draws are untouched: only the fix can differ.
            self.assertEqual(got["orientation"], want["orientation"])
            self.assertEqual(got["timestamp"], want["timestamp"])
            if want["latitude"] == rp.NO_FIX:
                self.assertEqual(got["latitude"], rp.NO_FIX)
                continue
            sampled_at = sim._next_gps_t - sim.gps_period_s
            north, east = sim.wander_at(sampled_at)
            lat, lon = rp.offset_latlon(want["latitude"], want["longitude"], north, east)
            self.assertAlmostEqual(got["latitude"], lat, places=9)
            self.assertAlmostEqual(got["longitude"], lon, places=9)
            if math.hypot(north, east) > 0.5:
                moved += 1
            elif north == 0.0 and east == 0.0:
                same += 1
        self.assertGreater(sim.wandered, 0)
        self.assertGreater(moved, 0)
        self.assertGreater(same, moved)
        self.assertEqual(sim.withheld, plain.withheld)


class FlyTests(unittest.TestCase):
    def test_flies_as_pace_i_without_wandering(self):
        for variant in ("cf0.3", "bridge+cf0.3"):
            with self.subTest(variant=variant):
                want = pi.fly("corner", 1, "outage15", variant, 0.8, course=CORNER)
                got = pj.fly("corner", 1, "outage15", variant, 0.8, course=CORNER)
                self.assertEqual(got.pop("wander"), {"wandered": 0})
                self.assertEqual(got, want)

    def test_pace_i_left_as_it_was(self):
        pj.fly("corner", 1, "wander15", "cf0.3", 0.8, course=CORNER)
        self.assertNotIn(pj._SLOT, pi.PROFILES)
        self.assertIsNot(pi.OutageRover, pj.WanderRover)
        self.assertEqual(pi.OutageRover.__name__, "OutageRover")

    def test_wandering_flown(self):
        wandered = 0
        for seed in (1, 2, 3):
            for variant in ("cf0.3", "bridge+cf0.3"):
                with self.subTest(seed=seed, variant=variant):
                    r = pj.fly("long", seed, "wander15", variant, 0.8, course=LONG)
                    self.assertTrue(r["ok"], r["reason"])
                    wandered += r["wander"]["wandered"]
        self.assertGreater(wandered, 0)

    def test_failed_run_fields(self):
        r = pj.failed_run(ValueError("boom"))
        self.assertFalse(r["ok"])
        self.assertEqual(r["wander"], {"wandered": None})
        self.assertEqual(r["outage"], {"withheld": None, "gps_resets": None})


class CheckTests(unittest.TestCase):
    def test_check_against_pace_i(self):
        with tiny_courses():
            ref = []
            for seed in (85, 86):
                r = pi.fly("tiny", seed, "outage15", "cf0.3", 0.8)
                r.update(profile="outage15", variant="cf0.3", cruise=0.8, course="tiny",
                         seed=seed)
                ref.append(r)
            ref[1]["elapsed_s"] += 1.0
            with tempfile.TemporaryDirectory() as d:
                path = os.path.join(d, "runs.jsonl")
                with open(path, "w", encoding="utf-8") as f:
                    for r in ref:
                        f.write(json.dumps(r) + "\n")
                    f.write("\n")
                out = pj.check_pace_i(path)
        # 1 profile x 2 variants x 1 course x 3 seeds = 6 missions checked; the
        # reference has 2 of them, and seed 86 was altered.
        self.assertEqual((out["compared"], out["identical"], out["missing"]), (2, 1, 4))
        self.assertEqual(len(out["different"]), 1)
        self.assertEqual(out["different"][0]["seed"], 86)
        self.assertEqual(out["different"][0]["fields"], ["elapsed_s"])


def _run(variant, seed, elapsed, ok=True, course="blocks", profile="wander15", wandered=6):
    return {"profile": profile, "variant": variant, "cruise": 0.8, "course": course,
            "seed": seed, "ok": ok, "elapsed_s": elapsed, "time_s": {"stopped": 10.0},
            "outage": {"withheld": 4, "gps_resets": None}, "wander": {"wandered": wandered}}


class SummaryTests(unittest.TestCase):
    def test_profile_effects(self):
        runs = ([_run("bridge+cf0.3", s, 100.0, profile="outage15") for s in range(1, 7)]
                + [_run("bridge+cf0.3", s, 110.0) for s in range(1, 7)])
        effects, tallies = pj.profile_effects(runs)
        self.assertEqual(len(effects), 1)
        self.assertEqual((effects[0]["faster"], effects[0]["slower"]), (0, 6))
        self.assertEqual(effects[0]["median_time_diff_share"], 0.1)
        self.assertEqual(tallies, [{"variant": "bridge+cf0.3", "profile": "wander15",
                                    "against": "outage15", "groups": 1, "groups_faster": 0,
                                    "groups_slower": 1, "groups_lost": 0, "groups_gained": 0,
                                    "largest_median_diff_share": 0.1}])

    def test_wander_rows(self):
        runs = [_run("cf0.3", 1, 100.0, wandered=4), _run("cf0.3", 2, 100.0, wandered=8),
                _run("cf0.3", 3, None, ok=False, wandered=50)]
        self.assertEqual(pj.wander_rows(runs), [
            {"profile": "wander15", "variant": "cf0.3", "cruise": 0.8, "course": "blocks",
             "missions": 2, "median_wandered": 6.0}])

    def test_main_small(self):
        with tiny_courses():
            with tempfile.TemporaryDirectory() as d, redirect_stdout(io.StringIO()):
                pj.main(["--out-dir", d, "--first-seed", "109", "--seeds", "2",
                         "--profiles", "wander15", "--variants", "bridge+cf0.3"])
                with open(os.path.join(d, "summary.json")) as f:
                    out = json.load(f)
                with open(os.path.join(d, "report.md")) as f:
                    md = f.read()
                with open(os.path.join(d, "runs.jsonl")) as f:
                    lines = [json.loads(x) for x in f if x.strip()]
        # outage15 and cf0.3 are always flown: 2 profiles x 2 variants x 2 seeds.
        self.assertEqual(out["runs"], 8)
        self.assertEqual(out["seeds"], [109, 110])
        self.assertEqual(sorted({r["seed"] for r in lines}), [109, 110])
        self.assertTrue(all("wander" in r for r in lines))
        self.assertTrue(out["done"])
        self.assertEqual(sorted((v["profile"], v["variant"], v["against"])
                                for v in out["verdicts"]),
                         [("outage15", "bridge+cf0.3", "cf0.3"),
                          ("wander15", "bridge+cf0.3", "cf0.3")])
        self.assertEqual(sorted((v["variant"], v["profile"]) for v in out["profile_verdicts"]),
                         [("bridge+cf0.3", "wander15"), ("cf0.3", "wander15")])
        self.assertEqual(len(out["wandering"]), 4)
        self.assertIsNone(out["check"])
        self.assertIn("## What wandering costs each pilot", md)
        self.assertIn("Seeds 109-110.", md)
        self.assertNotIn(pj._SLOT, pi.PROFILES)


if __name__ == "__main__":
    unittest.main()
