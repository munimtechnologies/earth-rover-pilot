"""Tests for the study of how long the wheels carry the position through a GPS outage.

Run: python -m unittest test_pace_k -v
"""

import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import dead_reckon as dr  # noqa: E402
import pace_i as pi  # noqa: E402
import pace_j as pj  # noqa: E402
import pace_k as pk  # noqa: E402
import pace_study as ps  # noqa: E402
import rover_pilot as rp  # noqa: E402

TINY = {"points": [(0.0, 0.0), (30.0, 0.0)], "checkpoints": [1]}
CORNER = {"points": [(0.0, 0.0), (40.0, 0.0), (40.0, 40.0)], "checkpoints": [1, 2]}
FAR = {"points": [(0.0, 0.0), (2000.0, 0.0)], "checkpoints": [1]}


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
        self.assertEqual(list(pk.PROFILES), ["outage15", "outage45", "wander45", "outage90"])
        for name in ("outage15", "outage45", "wander45"):
            self.assertIs(pk.PROFILES[name], pj.PROFILES[name])
        p = dict(pk.PROFILES["outage90"])
        self.assertEqual((p.pop("outage_s"), p.pop("clear_s")), (90.0, 600.0))
        q = dict(pi.PROFILES["outage45"])
        q.pop("outage_s")
        q.pop("clear_s")
        self.assertEqual(p, q)
        self.assertEqual(pk.BASE_PROFILE, "outage15")

    def test_variants(self):
        self.assertEqual(list(pk.VARIANTS), ["bridge+cf0.3", "bridge60+cf0.3", "bridge120+cf0.3"])
        self.assertIs(pk.VARIANTS["bridge+cf0.3"], pi.VARIANTS["bridge+cf0.3"])
        for name, reach in (("bridge60+cf0.3", 60.0), ("bridge120+cf0.3", 120.0)):
            with self.subTest(variant=name):
                v = dict(pk.VARIANTS[name])
                self.assertEqual(v.pop("reckoner"), {"max_s": reach})
                self.assertEqual(v, pi.VARIANTS["bridge+cf0.3"])
                made = dr.DeadReckoner(**dict(rp.DEAD_RECKON, **pk.VARIANTS[name]["reckoner"]))
                self.assertEqual(made.max_s, reach)
        self.assertEqual(dr.DeadReckoner(**rp.DEAD_RECKON).max_s, 30.0)
        self.assertEqual(pk.BASE_VARIANT, "bridge+cf0.3")
        self.assertEqual(pk.CRUISES, (0.8,))
        self.assertEqual(pk.FIRST_SEED, 133)
        self.assertEqual(pk.CHECKED, {"profiles": ("outage45", "wander45"),
                                      "variants": ("bridge+cf0.3",),
                                      "seeds": (109, 110, 111)})


class KnownTests(unittest.TestCase):
    def test_added_while_inside_only(self):
        with pk._known("outage90", "bridge60+cf0.3"):
            self.assertIs(pj.PROFILES["outage90"], pk.PROFILES["outage90"])
            self.assertIs(pi.VARIANTS["bridge60+cf0.3"], pk.VARIANTS["bridge60+cf0.3"])
        self.assertNotIn("outage90", pj.PROFILES)
        self.assertNotIn("bridge60+cf0.3", pi.VARIANTS)

    def test_known_names_left_alone(self):
        with pk._known("outage45", "bridge+cf0.3"):
            pass
        self.assertIn("outage45", pj.PROFILES)
        self.assertIn("bridge+cf0.3", pi.VARIANTS)

    def test_removed_after_a_failure(self):
        with self.assertRaises(ValueError):
            with pk._known("outage90", "bridge120+cf0.3"):
                raise ValueError("boom")
        self.assertNotIn("outage90", pj.PROFILES)
        self.assertNotIn("bridge120+cf0.3", pi.VARIANTS)


class FlyTests(unittest.TestCase):
    def test_flies_as_pace_j(self):
        for profile in ("outage45", "wander45"):
            with self.subTest(profile=profile):
                want = pj.fly("corner", 1, profile, "bridge+cf0.3", 0.8, course=CORNER)
                got = pk.fly("corner", 1, profile, "bridge+cf0.3", 0.8, course=CORNER)
                self.assertEqual(got, want)

    def test_longer_reach_drives_through(self):
        stopped = {}
        for variant in ("bridge+cf0.3", "bridge120+cf0.3"):
            stopped[variant] = 0.0
            for seed in (1, 2, 3):
                with self.subTest(variant=variant, seed=seed):
                    r = pk.fly("far", seed, "outage90", variant, 0.8, course=FAR)
                    self.assertTrue(r["ok"], r["reason"])
                    stopped[variant] += r["time_s"]["stopped"]
        self.assertNotIn("outage90", pj.PROFILES)
        self.assertNotIn("bridge120+cf0.3", pi.VARIANTS)
        self.assertLess(stopped["bridge120+cf0.3"], stopped["bridge+cf0.3"])

    def test_failed_run_fields(self):
        r = pk.failed_run(ValueError("boom"))
        self.assertFalse(r["ok"])
        self.assertEqual(r["wander"], {"wandered": None})
        self.assertEqual(r["outage"], {"withheld": None, "gps_resets": None})


class CheckTests(unittest.TestCase):
    def test_check_against_pace_j(self):
        with tiny_courses():
            ref = []
            for seed in (109, 110):
                r = pj.fly("tiny", seed, "outage45", "bridge+cf0.3", 0.8)
                r.update(profile="outage45", variant="bridge+cf0.3", cruise=0.8, course="tiny",
                         seed=seed)
                ref.append(r)
            ref[1]["elapsed_s"] += 1.0
            with tempfile.TemporaryDirectory() as d:
                path = os.path.join(d, "runs.jsonl")
                with open(path, "w", encoding="utf-8") as f:
                    for r in ref:
                        f.write(json.dumps(r) + "\n")
                    f.write("\n")
                out = pk.check_pace_j(path)
        # 2 profiles x 1 variant x 1 course x 3 seeds = 6 missions checked; the
        # reference has 2 of them, and seed 110 was altered.
        self.assertEqual((out["compared"], out["identical"], out["missing"]), (2, 1, 4))
        self.assertEqual(len(out["different"]), 1)
        self.assertEqual(out["different"][0]["seed"], 110)
        self.assertEqual(out["different"][0]["fields"], ["elapsed_s"])


def _run(variant, seed, elapsed, ok=True, course="blocks", profile="outage45"):
    return {"profile": profile, "variant": variant, "cruise": 0.8, "course": course,
            "seed": seed, "ok": ok, "elapsed_s": elapsed, "time_s": {"stopped": 10.0},
            "outage": {"withheld": 4, "gps_resets": None}, "wander": {"wandered": 0}}


class SummaryTests(unittest.TestCase):
    def test_pair_effects(self):
        runs = ([_run("bridge+cf0.3", s, 110.0) for s in range(1, 7)]
                + [_run("bridge60+cf0.3", s, 100.0) for s in range(1, 7)])
        effects, tallies = pk.pair_effects(runs)
        # pace_i's own pairs are back once it is done.
        self.assertEqual(pi.PAIRS[0], ("cf0.3", "bridge+cf0.3"))
        self.assertEqual(len(effects), 1)
        self.assertEqual((effects[0]["faster"], effects[0]["slower"]), (6, 0))
        self.assertEqual(effects[0]["median_time_diff_share"], -0.0909)
        self.assertEqual(tallies, [{"profile": "outage45", "variant": "bridge60+cf0.3",
                                    "against": "bridge+cf0.3", "groups": 1, "groups_faster": 1,
                                    "groups_slower": 0, "groups_lost": 0, "groups_gained": 0,
                                    "largest_median_diff_share": -0.0909}])

    def test_main_small(self):
        with tiny_courses():
            with tempfile.TemporaryDirectory() as d, redirect_stdout(io.StringIO()):
                pk.main(["--out-dir", d, "--first-seed", "133", "--seeds", "2",
                         "--profiles", "outage90", "--variants", "bridge60+cf0.3"])
                with open(os.path.join(d, "summary.json")) as f:
                    out = json.load(f)
                with open(os.path.join(d, "report.md")) as f:
                    md = f.read()
                with open(os.path.join(d, "runs.jsonl")) as f:
                    lines = [json.loads(x) for x in f if x.strip()]
        # outage15 and bridge+cf0.3 are always flown: 2 profiles x 2 variants x 2 seeds.
        self.assertEqual(out["runs"], 8)
        self.assertEqual(out["seeds"], [133, 134])
        self.assertEqual(sorted({r["seed"] for r in lines}), [133, 134])
        self.assertEqual(sorted({r["profile"] for r in lines}), ["outage15", "outage90"])
        self.assertTrue(out["done"])
        self.assertEqual(sorted((v["profile"], v["variant"], v["against"])
                                for v in out["verdicts"]),
                         [("outage15", "bridge60+cf0.3", "bridge+cf0.3"),
                          ("outage90", "bridge60+cf0.3", "bridge+cf0.3")])
        self.assertEqual(out["variants"]["bridge60+cf0.3"]["reckoner"], {"max_s": 60.0})
        self.assertIsNone(out["check"])
        self.assertIn("## Longer reach against shorter, same profile", md)
        self.assertIn("Seeds 133-134.", md)
        self.assertNotIn("outage90", pj.PROFILES)
        self.assertNotIn("bridge60+cf0.3", pi.VARIANTS)


if __name__ == "__main__":
    unittest.main()
