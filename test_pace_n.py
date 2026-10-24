"""Tests for the study of how far ahead the rover aims along its path.

Run: python -m unittest test_pace_n -v
"""

import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pace_e as pe  # noqa: E402
import pace_j as pj  # noqa: E402
import pace_l as pl  # noqa: E402
import pace_m as pm  # noqa: E402
import pace_n as pn  # noqa: E402
import pace_study as ps  # noqa: E402
import rover_pilot as rp  # noqa: E402

TINY = {"points": [(0.0, 0.0), (30.0, 0.0)], "checkpoints": [1]}
# One right-angle path corner at (60, 0); the only checkpoint is the end.
CORNER60 = {"points": [(0.0, 0.0), (60.0, 0.0), (60.0, 60.0)], "checkpoints": [2]}
FOLLOWER = rp.PathFollower
SLIP_ROVER = pl.SlipRover
COUNTING = pe.CountingEstimator
PATH = [(37.0, -122.0), (37.001, -122.0)]


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
        self.assertEqual(list(pn.PROFILES), ["outage90", "drift90"])
        for name in pn.PROFILES:
            self.assertIs(pn.PROFILES[name], pl.PROFILES[name])
        self.assertEqual(pn.BASE_PROFILE, "outage90")
        self.assertEqual(pn.PROFILE_PAIRS, (("outage90", "drift90"),))

    def test_variants(self):
        self.assertEqual(pn.VARIANTS, {"look8": {"lookahead_m": 8.0},
                                       "look4": {"lookahead_m": 4.0},
                                       "look12": {"lookahead_m": 12.0},
                                       "look16": {"lookahead_m": 16.0}})
        self.assertEqual(pn.BASE_VARIANT, "look8")
        self.assertEqual(pn.PAIRS, (("look8", "look4"), ("look8", "look12"),
                                    ("look8", "look16")))
        # v0.17.0's real-rover learner.
        self.assertEqual(pn.LEARNER, "long20")
        self.assertEqual(pm.VARIANTS[pn.LEARNER], rp.HEADING_LEARNER)
        self.assertEqual(pn.CRUISES, (0.8,))
        self.assertEqual(pn.FIRST_SEED, 205)
        self.assertEqual(pn.CHECKED, {"profiles": ("outage90", "drift90"), "variant": "look8",
                                      "seeds": (181, 182, 183)})
        # look8 is the path follower's own lookahead.
        self.assertEqual(FOLLOWER(PATH).lookahead_n, FOLLOWER(PATH, lookahead_m=8.0).lookahead_n)


class AimingTests(unittest.TestCase):
    def test_lookahead_inside_only(self):
        for variant, n in (("look4", 2), ("look8", 4), ("look12", 6), ("look16", 8)):
            with self.subTest(variant=variant):
                with pn._aiming(variant):
                    f = rp.PathFollower(PATH)
                    g = rp.PathFollower(PATH, step_m=4.0)
                self.assertIsInstance(f, FOLLOWER)
                self.assertEqual(f.lookahead_n, n)
                # Other settings pass through: 16 m over 4 m steps is 4 points.
                self.assertEqual(g.lookahead_n, max(1, int(round(n * 2.0 / 4.0))))
                self.assertIs(rp.PathFollower, FOLLOWER)
        self.assertEqual(rp.PathFollower(PATH).lookahead_n, 4)

    def test_restored_after_a_failure(self):
        with self.assertRaises(ValueError):
            with pn._aiming("look16"):
                raise ValueError("boom")
        self.assertIs(rp.PathFollower, FOLLOWER)


def drive(sim, steps=50):
    for _ in range(steps):
        sim.control(1.0, 0.0)
        sim.sleep(0.1)


class WatchingTests(unittest.TestCase):
    def test_samples_while_driving_forward_and_only_reads(self):
        samples = []
        with pn._watching(samples):
            sim = pl.SlipRover([(500.0, 0.0)], seed=3, **pl.PROFILES["outage90"])
        self.assertIs(pl.SlipRover, SLIP_ROVER)
        sim.control(0.0, 0.0)
        sim.sleep(0.5)
        self.assertEqual(samples, [])  # stopped: nothing
        drive(sim)
        # Commands land 0.8 s late; one sample a second after that, over 5 s.
        self.assertGreaterEqual(len(samples), 3)
        self.assertLessEqual(len(samples), 6)
        self.assertNotEqual(samples[0], samples[-1])
        plain = pl.SlipRover([(500.0, 0.0)], seed=3, **pl.PROFILES["outage90"])
        plain.control(0.0, 0.0)
        plain.sleep(0.5)
        drive(plain)
        self.assertEqual((sim.north, sim.east, sim.t), (plain.north, plain.east, plain.t))

    def test_restored_after_a_failure(self):
        with self.assertRaises(ValueError):
            with pn._watching([]):
                raise ValueError("boom")
        self.assertIs(pl.SlipRover, SLIP_ROVER)


class CornerTests(unittest.TestCase):
    def test_blocks_has_nine_path_corners(self):
        blocks = ps.COURSES["blocks"]
        cs = pn.corners(blocks["points"], blocks["checkpoints"])
        self.assertEqual([v for v, _ in cs],
                         [blocks["points"][k] for k in (1, 2, 4, 5, 7, 8, 10, 11, 13)])
        self.assertEqual(cs[0], ((100.0, 0.0), (1.0, 0.0)))
        self.assertEqual(cs[1], ((100.0, 100.0), (0.0, 1.0)))
        # Without the checkpoints left out, every interior point is a corner.
        self.assertEqual(len(pn.corners(blocks["points"])), 13)

    def test_gentle_courses_have_none(self):
        for name in ("boulevard", "bayside"):
            with self.subTest(course=name):
                c = ps.COURSES[name]
                self.assertEqual(pn.corners(c["points"], c["checkpoints"]), [])
        # A 26.6 deg bend is not a corner.
        self.assertEqual(pn.corners([(0.0, 0.0), (60.0, 0.0), (120.0, 30.0)]), [])

    def test_running_past_a_corner(self):
        # (50, 0): on the course, 10 m before the corner. (65, 0): 5 m past it
        # and 5 m off the course. (60, 10): on the next leg. (0, 0) and (20, 0)
        # are more than 20 m from the corner and do not count.
        samples = [(0.0, 0.0), (20.0, 0.0), (50.0, 0.0), (65.0, 0.0), (60.0, 10.0)]
        out = pn.corner_stats(CORNER60["points"], CORNER60["checkpoints"], samples)
        self.assertEqual(out, {"n": 3, "median_m": 0.0, "p95_m": 0.0, "max_m": 5.0,
                               "corners": 1, "median_past_m": 5.0, "max_past_m": 5.0})

    def test_turning_before_a_corner(self):
        # (55, 5) is inside the corner: 5 m from both legs, 5 m before it.
        samples = [(50.0, 0.0), (55.0, 5.0)]
        out = pn.corner_stats(CORNER60["points"], CORNER60["checkpoints"], samples)
        self.assertEqual((out["n"], out["max_m"], out["median_past_m"]), (2, 5.0, -5.0))

    def test_no_corner(self):
        samples = [(50.0, 0.0), (65.0, 0.0)]
        # With the corner a checkpoint, the course has no path corner.
        for points, cps in ((CORNER60["points"], [1, 2]), ([], [])):
            with self.subTest(points=points):
                out = pn.corner_stats(points, cps, samples if points else [])
                self.assertEqual(out, {"n": 0, "median_m": None, "p95_m": None, "max_m": None,
                                       "corners": 0, "median_past_m": None,
                                       "max_past_m": None})


class FlyTests(unittest.TestCase):
    def test_look8_flies_as_pace_m_long20(self):
        for profile in ("outage90", "drift90"):
            with self.subTest(profile=profile):
                want = pm.fly("corner", 1, profile, "long20", 0.8, course=CORNER60)
                got = pn.fly("corner", 1, profile, "look8", 0.8, course=CORNER60)
                corner = got.pop("corner")
                self.assertEqual(got, want)
                self.assertTrue(got["ok"], got["reason"])
                self.assertEqual(corner["corners"], 1)
                self.assertGreater(corner["n"], 0)
        self.assertIs(rp.PathFollower, FOLLOWER)
        self.assertIs(pl.SlipRover, SLIP_ROVER)
        self.assertIs(pe.CountingEstimator, COUNTING)

    def test_a_variant_flies_a_corner(self):
        r = pn.fly("corner", 2, "drift90", "look16", 0.8, course=CORNER60)
        self.assertTrue(r["ok"], r["reason"])
        self.assertEqual(r["corner"]["corners"], 1)
        self.assertIsNotNone(r["corner"]["median_past_m"])
        self.assertIn("fit_err", r)
        self.assertIs(rp.PathFollower, FOLLOWER)

    def test_failed_run_fields(self):
        r = pn.failed_run(ValueError("boom"))
        self.assertFalse(r["ok"])
        self.assertEqual(r["corner"]["n"], 0)
        self.assertEqual(r["fit_err"]["n"], 0)


class CheckTests(unittest.TestCase):
    def test_check_against_pace_m(self):
        with tiny_courses():
            ref = []
            for seed in (181, 182):
                r = pm.fly("tiny", seed, "outage90", "long20", 0.8)
                r.update(profile="outage90", variant="long20", cruise=0.8, course="tiny",
                         seed=seed)
                ref.append(r)
            ref[1]["elapsed_s"] += 1.0
            with tempfile.TemporaryDirectory() as d:
                path = os.path.join(d, "runs.jsonl")
                with open(path, "w", encoding="utf-8") as f:
                    for r in ref:
                        f.write(json.dumps(r) + "\n")
                    f.write("\n")
                out = pn.check_pace_m(path)
        # 2 profiles x 1 course x 3 seeds = 6 missions checked; the reference
        # has 2 of them, and seed 182 was altered.
        self.assertEqual((out["compared"], out["identical"], out["missing"]), (2, 1, 4))
        self.assertEqual(len(out["different"]), 1)
        self.assertEqual(out["different"][0]["seed"], 182)
        self.assertEqual(out["different"][0]["fields"], ["elapsed_s"])


NO_CORNER = {"n": 0, "median_m": None, "p95_m": None, "max_m": None, "corners": 0,
             "median_past_m": None, "max_past_m": None}


def _run(variant, seed, elapsed, profile="outage90", corner=None, ok=True, max_m=5.0,
         reports=5, reached=5):
    return {"profile": profile, "variant": variant, "cruise": 0.8, "course": "blocks",
            "seed": seed, "ok": ok, "elapsed_s": elapsed, "time_s": {"stopped": 10.0},
            "reports": reports, "reached": reached,
            "offset": {"n": 5, "median_m": 1.0, "p95_m": 3.0, "max_m": max_m},
            "corner": corner or NO_CORNER}


def _corner(n, median, p95, mx, corners, past, max_past):
    return {"n": n, "median_m": median, "p95_m": p95, "max_m": mx, "corners": corners,
            "median_past_m": past, "max_past_m": max_past}


class SummaryTests(unittest.TestCase):
    def test_pair_effects(self):
        runs = ([_run("look8", s, 100.0) for s in range(1, 7)]
                + [_run("look16", s, 90.0) for s in range(1, 7)])
        effects, tallies = pn.pair_effects(runs)
        self.assertEqual(len(effects), 1)
        self.assertEqual((effects[0]["faster"], effects[0]["slower"]), (6, 0))
        self.assertEqual(tallies, [{"profile": "outage90", "variant": "look16",
                                    "against": "look8", "groups": 1, "groups_faster": 1,
                                    "groups_slower": 0, "groups_lost": 0, "groups_gained": 0,
                                    "largest_median_diff_share": -0.1}])

    def test_profile_effects(self):
        runs = ([_run("look16", s, 100.0) for s in range(1, 7)]
                + [_run("look16", s, 110.0, profile="drift90") for s in range(1, 7)])
        effects, tallies = pn.profile_effects(runs)
        self.assertEqual(pj.PROFILE_PAIRS, (("outage15", "wander15"), ("outage45", "wander45")))
        self.assertNotIn("look16", pj.VARIANTS)
        self.assertEqual(len(effects), 1)
        self.assertEqual(tallies[0]["groups_slower"], 1)
        self.assertEqual((tallies[0]["variant"], tallies[0]["profile"], tallies[0]["against"]),
                         ("look16", "drift90", "outage90"))

    def test_corner_rows(self):
        runs = [_run("look8", 1, 100.0, corner=_corner(10, 1.0, 4.0, 6.0, 9, 2.0, 5.0)),
                _run("look8", 2, 100.0, corner=_corner(12, 2.0, 6.0, 8.0, 9, 3.0, 7.0)),
                _run("look8", 3, 100.0, corner=_corner(11, 3.0, 8.0, 10.0, 8, 4.0, 9.0)),
                _run("look8", 4, 100.0),
                _run("look8", 5, 100.0, ok=False, corner=_corner(1, 9.0, 9.0, 9.0, 1, 9.0, 9.0)),
                _run("look4", 1, 100.0)]
        self.assertEqual(pn.corner_rows(runs),
                         [{"profile": "outage90", "variant": "look8", "cruise": 0.8,
                           "course": "blocks", "missions": 3, "corners": 9, "median_m": 2.0,
                           "p95_m": 6.0, "max_m": 8.0, "median_past_m": 3.0,
                           "max_past_m": 7.0}])

    def test_offset_max_rows(self):
        runs = [_run("look8", 1, 100.0, max_m=4.0),
                _run("look8", 2, 100.0, max_m=9.0, reports=6),
                _run("look8", 3, 100.0, max_m=6.0),
                _run("look8", 4, 100.0, max_m=30.0, ok=False)]
        self.assertEqual(pn.offset_max_rows(runs),
                         [{"profile": "outage90", "variant": "look8", "cruise": 0.8,
                           "course": "blocks", "missions": 3, "median_max_m": 6.0,
                           "largest_max_m": 9.0, "refused": 1, "missions_refused": 1}])

    def test_main_small(self):
        with tiny_courses():
            with tempfile.TemporaryDirectory() as d, redirect_stdout(io.StringIO()):
                pn.main(["--out-dir", d, "--first-seed", "205", "--seeds", "2",
                         "--profiles", "drift90", "--variants", "look16"])
                with open(os.path.join(d, "summary.json")) as f:
                    out = json.load(f)
                with open(os.path.join(d, "report.md")) as f:
                    md = f.read()
                with open(os.path.join(d, "runs.jsonl")) as f:
                    lines = [json.loads(x) for x in f if x.strip()]
        # outage90 and look8 are always flown: 2 profiles x 2 variants x 2 seeds.
        self.assertEqual(out["runs"], 8)
        self.assertEqual(out["seeds"], [205, 206])
        self.assertEqual(sorted({r["profile"] for r in lines}), ["drift90", "outage90"])
        self.assertEqual(sorted({r["variant"] for r in lines}), ["look16", "look8"])
        self.assertTrue(all("corner" in r and "fit_err" in r for r in lines))
        self.assertTrue(out["done"])
        self.assertEqual(sorted((v["profile"], v["variant"], v["against"])
                                for v in out["verdicts"]),
                         [("drift90", "look16", "look8"), ("outage90", "look16", "look8")])
        self.assertEqual(sorted((v["variant"], v["profile"], v["against"])
                                for v in out["profile_verdicts"]),
                         [("look16", "drift90", "outage90"), ("look8", "drift90", "outage90")])
        self.assertEqual(out["learner"], "long20")
        self.assertEqual(out["corner"], [])  # the tiny course has no corner
        self.assertEqual(len(out["offset_max"]), 4)
        self.assertIsNone(out["check"])
        self.assertIn("## Near path corners", md)
        self.assertIn("Seeds 205-206.", md)
        self.assertIs(rp.PathFollower, FOLLOWER)
        self.assertIs(pl.SlipRover, SLIP_ROVER)
        self.assertIs(pe.CountingEstimator, COUNTING)


if __name__ == "__main__":
    unittest.main()
