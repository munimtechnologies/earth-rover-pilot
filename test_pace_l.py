"""Tests for the study of the 120 s reach on wheels and a compass that lie.

Run: python -m unittest test_pace_l -v
"""

import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pace_i as pi  # noqa: E402
import pace_j as pj  # noqa: E402
import pace_k as pk  # noqa: E402
import pace_l as pl  # noqa: E402
import pace_study as ps  # noqa: E402

TINY = {"points": [(0.0, 0.0), (30.0, 0.0)], "checkpoints": [1]}
CORNER = {"points": [(0.0, 0.0), (40.0, 0.0), (40.0, 40.0)], "checkpoints": [1, 2]}
FAR = {"points": [(0.0, 0.0), (2000.0, 0.0)], "checkpoints": [1]}
WANDER_ROVER = pj.WanderRover


class tiny_courses:
    """Replace pace_study's courses with one short course while in use."""

    def __enter__(self):
        self.saved = dict(ps.COURSES)
        ps.COURSES.clear()
        ps.COURSES["tiny"] = TINY

    def __exit__(self, *exc):
        ps.COURSES.clear()
        ps.COURSES.update(self.saved)


def without(profile, *names):
    p = dict(profile)
    for name in names:
        p.pop(name)
    return p


class SetupTests(unittest.TestCase):
    def test_profiles(self):
        self.assertEqual(list(pl.PROFILES),
                         ["outage45", "lie45", "outage90", "slip90", "drift90", "lie90"])
        self.assertIs(pl.PROFILES["outage45"], pk.PROFILES["outage45"])
        self.assertIs(pl.PROFILES["outage90"], pk.PROFILES["outage90"])
        lie = ("slip", "slip_every_s", "drift_deg", "drift_tau_s")
        self.assertEqual(without(pl.PROFILES["lie45"], *lie), pk.PROFILES["outage45"])
        self.assertEqual(without(pl.PROFILES["lie90"], *lie), pk.PROFILES["outage90"])
        self.assertEqual(without(pl.PROFILES["slip90"], "slip", "slip_every_s"),
                         pk.PROFILES["outage90"])
        self.assertEqual(without(pl.PROFILES["drift90"], "drift_deg", "drift_tau_s"),
                         pk.PROFILES["outage90"])
        for name in ("lie45", "slip90", "lie90"):
            self.assertEqual((pl.PROFILES[name]["slip"], pl.PROFILES[name]["slip_every_s"]),
                             (0.15, 120.0))
        for name in ("lie45", "drift90", "lie90"):
            self.assertEqual((pl.PROFILES[name]["drift_deg"], pl.PROFILES[name]["drift_tau_s"]),
                             (10.0, 120.0))
        self.assertEqual(pl.BASE_PROFILE, "outage45")
        self.assertEqual(pl.PROFILE_PAIRS, (("outage45", "lie45"), ("outage90", "slip90"),
                                            ("outage90", "drift90"), ("outage90", "lie90")))

    def test_variants(self):
        self.assertEqual(pl.VARIANTS, pk.VARIANTS)
        self.assertEqual(pl.BASE_VARIANT, "bridge+cf0.3")
        self.assertEqual(pl.PAIRS, pk.PAIRS)
        self.assertEqual(pl.CRUISES, (0.8,))
        self.assertEqual(pl.FIRST_SEED, 157)
        self.assertEqual(pl.CHECKED, {"profiles": ("outage45", "outage90"),
                                      "variants": ("bridge+cf0.3", "bridge120+cf0.3"),
                                      "seeds": (133, 134, 135)})


class SlipTests(unittest.TestCase):
    def test_spells(self):
        self.assertEqual(pl.slip_spells(5, 0.0, 120.0), [])
        spells = pl.slip_spells(5, 0.15, 120.0)
        self.assertEqual(spells, pl.slip_spells(5, 0.15, 120.0))
        self.assertNotEqual(spells, pl.slip_spells(6, 0.15, 120.0))
        self.assertEqual(spells[0][0], 0.0)
        starts = [a for a, _ in spells]
        self.assertEqual(starts, sorted(starts))
        self.assertGreater(starts[-1], pi.OUTAGE_HORIZON_S - 2000.0)
        self.assertTrue(all(0.85 <= k <= 1.15 for _, k in spells))
        # About one spell every 120 s over the horizon.
        self.assertGreater(len(spells), 100)
        self.assertLess(len(spells), 300)

    def test_slip_at(self):
        rover = pl.SlipRover([(500.0, 0.0)], seed=5, **pl.PROFILES["slip90"])
        (a, k0), (b, k1) = rover.spells[0], rover.spells[1]
        self.assertEqual(rover.slip_at(a), k0)
        self.assertEqual(rover.slip_at((a + b) / 2.0), k0)
        self.assertEqual(rover.slip_at(b), k1)
        plain = pl.SlipRover([(500.0, 0.0)], seed=5, **pl.PROFILES["outage90"])
        self.assertEqual(plain.spells, [])
        self.assertEqual(plain.slip_at(100.0), 1.0)
        self.assertIsNone(plain.slip_stats())

    def test_slip_changes_the_wheels_only(self):
        kw = pl.PROFILES["slip90"]
        a = pl.SlipRover([(500.0, 0.0)], seed=5, **kw)
        b = WANDER_ROVER([(500.0, 0.0)], seed=5, **without(kw, "slip", "slip_every_s"))
        checked = slipped = 0
        for step in range(3000):
            for rover in (a, b):
                rover.control(0.8, 0.2 if step % 400 < 50 else 0.0)
                rover.sleep(0.1)
            self.assertEqual((a.north, a.east, a.heading), (b.north, b.east, b.heading))
            self.assertEqual(a.data()["orientation"], b.data()["orientation"])
            self.assertEqual(len(a.rpms), len(b.rpms))
            for ra, rb in zip(a.rpms, b.rpms):
                self.assertEqual(ra[4], rb[4])
                k = a.slip_at(ra[4])
                for j in range(4):
                    self.assertLessEqual(abs(ra[j] - rb[j] * k), 0.02)
                checked += 1
                slipped += k != 1.0 and rb[0] != 0
        self.assertGreater(checked, 1000)
        self.assertGreater(slipped, 100)
        stats = a.slip_stats()
        self.assertGreaterEqual(stats["spells"], 1)
        self.assertLessEqual(stats["mean_abs_slip"], 0.15)

    def test_no_slip_is_a_wander_rover(self):
        kw = pl.PROFILES["outage90"]
        a = pl.SlipRover([(500.0, 0.0)], seed=7, **kw)
        b = WANDER_ROVER([(500.0, 0.0)], seed=7, **kw)
        for step in range(600):
            for rover in (a, b):
                rover.control(0.8, 0.1)
                rover.sleep(0.1)
            self.assertEqual(a.rpms, b.rpms)
            self.assertEqual(a.data(), b.data())


class KnownTests(unittest.TestCase):
    def test_added_while_inside_only(self):
        with pl._known("lie90", "bridge120+cf0.3"):
            self.assertIs(pj.PROFILES["lie90"], pl.PROFILES["lie90"])
            self.assertIs(pi.VARIANTS["bridge120+cf0.3"], pl.VARIANTS["bridge120+cf0.3"])
        self.assertNotIn("lie90", pj.PROFILES)
        self.assertNotIn("bridge120+cf0.3", pi.VARIANTS)

    def test_known_names_left_alone(self):
        with pl._known("outage45", "bridge+cf0.3"):
            pass
        self.assertIn("outage45", pj.PROFILES)
        self.assertIn("bridge+cf0.3", pi.VARIANTS)

    def test_removed_after_a_failure(self):
        made = []
        with self.assertRaises(ValueError):
            with pl._known("slip90", "bridge60+cf0.3"), pl._slipping(made):
                raise ValueError("boom")
        self.assertNotIn("slip90", pj.PROFILES)
        self.assertNotIn("bridge60+cf0.3", pi.VARIANTS)
        self.assertIs(pj.WanderRover, WANDER_ROVER)


class FlyTests(unittest.TestCase):
    def test_flies_as_pace_k(self):
        for profile, variant in (("outage45", "bridge+cf0.3"), ("outage90", "bridge120+cf0.3")):
            with self.subTest(profile=profile, variant=variant):
                want = pk.fly("corner", 1, profile, variant, 0.8, course=CORNER)
                got = pl.fly("corner", 1, profile, variant, 0.8, course=CORNER)
                self.assertIsNone(got.pop("slip"))
                self.assertEqual(got, want)
        self.assertIs(pj.WanderRover, WANDER_ROVER)

    def test_lies_fly(self):
        for profile in ("slip90", "drift90", "lie90"):
            with self.subTest(profile=profile):
                r = pl.fly("far", 2, profile, "bridge120+cf0.3", 0.8, course=FAR)
                self.assertTrue(r["ok"], r["reason"])
                if "slip" in pl.PROFILES[profile]:
                    self.assertGreaterEqual(r["slip"]["spells"], 1)
                else:
                    self.assertIsNone(r["slip"])
        self.assertNotIn("lie90", pj.PROFILES)
        self.assertNotIn("bridge120+cf0.3", pi.VARIANTS)
        self.assertIs(pj.WanderRover, WANDER_ROVER)

    def test_failed_run_fields(self):
        r = pl.failed_run(ValueError("boom"))
        self.assertFalse(r["ok"])
        self.assertIsNone(r["slip"])
        self.assertEqual(r["wander"], {"wandered": None})
        self.assertEqual(r["outage"], {"withheld": None, "gps_resets": None})


class CheckTests(unittest.TestCase):
    def test_check_against_pace_k(self):
        with tiny_courses():
            ref = []
            for seed in (133, 134):
                r = pk.fly("tiny", seed, "outage90", "bridge120+cf0.3", 0.8)
                r.update(profile="outage90", variant="bridge120+cf0.3", cruise=0.8,
                         course="tiny", seed=seed)
                ref.append(r)
            ref[1]["elapsed_s"] += 1.0
            with tempfile.TemporaryDirectory() as d:
                path = os.path.join(d, "runs.jsonl")
                with open(path, "w", encoding="utf-8") as f:
                    for r in ref:
                        f.write(json.dumps(r) + "\n")
                    f.write("\n")
                out = pl.check_pace_k(path)
        # 2 profiles x 2 variants x 1 course x 3 seeds = 12 missions checked; the
        # reference has 2 of them, and seed 134 was altered.
        self.assertEqual((out["compared"], out["identical"], out["missing"]), (2, 1, 10))
        self.assertEqual(len(out["different"]), 1)
        self.assertEqual(out["different"][0]["seed"], 134)
        self.assertEqual(out["different"][0]["fields"], ["elapsed_s"])


def _run(variant, seed, elapsed, ok=True, course="blocks", profile="outage90"):
    return {"profile": profile, "variant": variant, "cruise": 0.8, "course": course,
            "seed": seed, "ok": ok, "elapsed_s": elapsed, "time_s": {"stopped": 10.0},
            "outage": {"withheld": 4, "gps_resets": None}, "wander": {"wandered": 0},
            "slip": None}


class SummaryTests(unittest.TestCase):
    def test_profile_effects(self):
        runs = ([_run("bridge120+cf0.3", s, 100.0) for s in range(1, 7)]
                + [_run("bridge120+cf0.3", s, 110.0, profile="lie90") for s in range(1, 7)])
        effects, tallies = pl.profile_effects(runs)
        # pace_j's own variants and pairs are back once it is done.
        self.assertEqual(pj.PROFILE_PAIRS, (("outage15", "wander15"), ("outage45", "wander45")))
        self.assertNotIn("bridge120+cf0.3", pj.VARIANTS)
        self.assertEqual(len(effects), 1)
        self.assertEqual((effects[0]["faster"], effects[0]["slower"]), (0, 6))
        self.assertEqual(effects[0]["median_time_diff_share"], 0.1)
        self.assertEqual(tallies, [{"variant": "bridge120+cf0.3", "profile": "lie90",
                                    "against": "outage90", "groups": 1, "groups_faster": 0,
                                    "groups_slower": 1, "groups_lost": 0, "groups_gained": 0,
                                    "largest_median_diff_share": 0.1}])

    def test_slip_rows(self):
        runs = [_run("bridge+cf0.3", s, 100.0, profile="slip90") for s in range(1, 4)]
        for r, spells in zip(runs, (3, 5, 4)):
            r["slip"] = {"spells": spells, "mean_abs_slip": 0.07}
        runs.append(_run("bridge+cf0.3", 1, 100.0))
        rows = pl.slip_rows(runs)
        self.assertEqual(rows, [{"profile": "slip90", "variant": "bridge+cf0.3", "cruise": 0.8,
                                 "course": "blocks", "missions": 3, "median_spells": 4,
                                 "median_mean_abs_slip": 0.07}])

    def test_main_small(self):
        with tiny_courses():
            with tempfile.TemporaryDirectory() as d, redirect_stdout(io.StringIO()):
                pl.main(["--out-dir", d, "--first-seed", "157", "--seeds", "2",
                         "--profiles", "outage90,lie90", "--variants", "bridge120+cf0.3"])
                with open(os.path.join(d, "summary.json")) as f:
                    out = json.load(f)
                with open(os.path.join(d, "report.md")) as f:
                    md = f.read()
                with open(os.path.join(d, "runs.jsonl")) as f:
                    lines = [json.loads(x) for x in f if x.strip()]
        # outage45 and bridge+cf0.3 are always flown: 3 profiles x 2 variants x 2 seeds.
        self.assertEqual(out["runs"], 12)
        self.assertEqual(out["seeds"], [157, 158])
        self.assertEqual(sorted({r["seed"] for r in lines}), [157, 158])
        self.assertEqual(sorted({r["profile"] for r in lines}), ["lie90", "outage45", "outage90"])
        self.assertTrue(out["done"])
        self.assertEqual(sorted((v["profile"], v["variant"], v["against"])
                                for v in out["verdicts"]),
                         [("lie90", "bridge120+cf0.3", "bridge+cf0.3"),
                          ("outage45", "bridge120+cf0.3", "bridge+cf0.3"),
                          ("outage90", "bridge120+cf0.3", "bridge+cf0.3")])
        self.assertEqual(sorted((v["variant"], v["profile"], v["against"])
                                for v in out["profile_verdicts"]),
                         [("bridge+cf0.3", "lie90", "outage90"),
                          ("bridge120+cf0.3", "lie90", "outage90")])
        self.assertEqual(out["profiles"]["lie90"]["slip"], 0.15)
        self.assertIsNone(out["check"])
        self.assertIn("## What the lies cost, same variant", md)
        self.assertIn("Seeds 157-158.", md)
        self.assertNotIn("lie90", pj.PROFILES)
        self.assertNotIn("bridge120+cf0.3", pi.VARIANTS)
        self.assertIs(pj.WanderRover, WANDER_ROVER)


if __name__ == "__main__":
    unittest.main()
