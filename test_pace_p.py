"""Tests for the study of where a longer lookahead saves time.

Run: python -m unittest test_pace_p -v
"""

import io
import json
import math
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pace_e as pe  # noqa: E402
import pace_i as pi  # noqa: E402
import pace_j as pj  # noqa: E402
import pace_l as pl  # noqa: E402
import pace_m as pm  # noqa: E402
import pace_o as po  # noqa: E402
import pace_p as pp  # noqa: E402
import pace_study as ps  # noqa: E402
import rover_pilot as rp  # noqa: E402

TINY = {"points": [(0.0, 0.0), (30.0, 0.0)], "checkpoints": [1]}
# One right-angle path corner at (60, 0); the only checkpoint is the end.
CORNER60 = {"points": [(0.0, 0.0), (60.0, 0.0), (60.0, 60.0)], "checkpoints": [2]}
FOLLOWER = rp.PathFollower
SLIP_ROVER = pl.SlipRover
COUNTING = pe.CountingEstimator
PLANNER = ps.CoursePlanner
LAT0, LON0 = 37.0, -122.0
EMPTY = {"n": 0, "median_m": None, "p95_m": None, "max_m": None, "far": 0}
# 61 m legs: 31 steps of just under 2 m each, so no step count sits on a
# rounding boundary.
SIDE = 61.0


def latlon(p):
    return rp.offset_latlon(LAT0, LON0, p[0], p[1])


# North 61 m, then east 61 m: densified, the corner is point 31, segments
# 0-30 head north and 31-61 east.
RIGHT = [latlon(p) for p in ((0.0, 0.0), (SIDE, 0.0), (SIDE, SIDE))]
# North 61 m, then 61 m turning 20 deg to the east.
GENTLE = [latlon(p) for p in ((0.0, 0.0), (SIDE, 0.0),
                              (SIDE + SIDE * math.cos(math.radians(20.0)),
                               SIDE * math.sin(math.radians(20.0))))]


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
        self.assertEqual(list(pp.PROFILES), ["outage90", "drift90"])
        for name in pp.PROFILES:
            self.assertIs(pp.PROFILES[name], pl.PROFILES[name])
        self.assertEqual(pp.BASE_PROFILE, "outage90")
        self.assertEqual(pp.PROFILE_PAIRS, (("outage90", "drift90"),))

    def test_variants(self):
        self.assertEqual(pp.VARIANTS, {
            "keep16": {"lookahead_m": 16.0},
            "keep24": {"lookahead_m": 24.0},
            "bend24": {"lookahead_m": 24.0, "short_m": 16.0, "turn_deg": 45.0},
            "calm24": {"lookahead_m": 24.0, "short_m": 16.0, "turn_deg": 10.0},
            "calm32": {"lookahead_m": 32.0, "short_m": 16.0, "turn_deg": 10.0}})
        self.assertEqual(pp.BASE_VARIANT, "keep16")
        self.assertEqual(pp.PAIRS, (("keep16", "keep24"), ("keep16", "bend24"),
                                    ("keep16", "calm24"), ("keep16", "calm32")))
        # The plain variants are pace_o.py's, flown by pace_o.fly.
        self.assertEqual(po.VARIANTS["keep16"], {"planner": "keep", "lookahead_m": 16.0})
        self.assertEqual(po.VARIANTS["keep24"], {"planner": "keep", "lookahead_m": 24.0})
        # v0.18.1's real-rover pilot: its learner and its lookahead.
        self.assertEqual(pp.LEARNER, "long20")
        self.assertEqual(pm.VARIANTS[pp.LEARNER], rp.HEADING_LEARNER)
        self.assertEqual(rp.PATH_LOOKAHEAD_M, pp.VARIANTS["keep16"]["lookahead_m"])
        self.assertEqual(pp.PLANNER, "keep")
        self.assertEqual(pp.CRUISES, (0.8,))
        self.assertEqual(pp.FIRST_SEED, 253)
        self.assertEqual(pp.CHECKED, {"profiles": ("outage90", "drift90"),
                                      "variants": ("keep16", "keep24"),
                                      "seeds": (229, 230, 231)})


class HeadingsTests(unittest.TestCase):
    def test_north_then_east(self):
        hs = pp.headings(RIGHT)
        self.assertEqual(len(hs), 2)
        self.assertAlmostEqual(hs[0], 0.0, places=6)
        self.assertAlmostEqual(hs[1], 90.0, places=2)

    def test_a_repeated_point_takes_the_next_heading(self):
        hs = pp.headings([RIGHT[0], RIGHT[0], RIGHT[1], RIGHT[2]])
        self.assertEqual(len(hs), 3)
        self.assertEqual(hs[0], hs[1])
        self.assertAlmostEqual(hs[2], 90.0, places=2)

    def test_a_repeated_last_point_takes_the_last_heading(self):
        hs = pp.headings([RIGHT[1], RIGHT[2], RIGHT[2]])
        self.assertEqual(hs[1], hs[0])
        self.assertAlmostEqual(hs[0], 90.0, places=2)

    def test_nothing_to_go_on(self):
        self.assertEqual(pp.headings([]), [])
        self.assertEqual(pp.headings([RIGHT[0]]), [])
        self.assertEqual(pp.headings([RIGHT[0], RIGHT[0]]), [0.0])


class TurnAheadTests(unittest.TestCase):
    def test_turns(self):
        hs = [0.0, 0.0, 90.0, 90.0]
        self.assertEqual(pp.turn_ahead(hs, 0, 2), 0.0)
        self.assertEqual(pp.turn_ahead(hs, 0, 3), 90.0)
        self.assertEqual(pp.turn_ahead(hs, 1, 3), 90.0)
        self.assertEqual(pp.turn_ahead(hs, 2, 5), 0.0)
        self.assertEqual(pp.turn_ahead(hs, 9, 3), 0.0)  # past the end: the last segment

    def test_wraps(self):
        self.assertEqual(pp.turn_ahead([350.0, 10.0], 0, 2), 20.0)
        self.assertEqual(pp.turn_ahead([10.0, 350.0], 0, 2), 20.0)

    def test_nothing(self):
        self.assertEqual(pp.turn_ahead([], 0, 3), 0.0)


def aim_at(f, k):
    """f's target and distance with the rover on f's point k."""
    return f.target(*f.points[k])


class BendFollowerTests(unittest.TestCase):
    def test_short_only_when_the_corner_is_within_the_long_lookahead(self):
        f = pp.BendFollower(RIGHT, lookahead_m=24.0, short_m=16.0, turn_deg=45.0)
        self.assertEqual(len(f.points), 63)
        self.assertEqual((f.lookahead_n, f.short_n), (12, 8))
        # (rover on point, aims at point): 24 m (12 points) ahead while the
        # 12 segments ahead all head north; 16 m (8) once the corner's first
        # east segment (31) is among them; 24 m again past the corner.
        for k, want in ((10, 22), (19, 31), (20, 28), (25, 33), (31, 43), (55, 62)):
            with self.subTest(k=k):
                got, distance = aim_at(f, k)
                self.assertEqual(f.i, k)
                self.assertEqual(got, f.points[want])
                self.assertEqual(distance, 0.0)
        self.assertEqual((f.targets, f.long), (6, 4))

    def test_the_turn_threshold(self):
        # A 20 deg bend: under the 45 deg threshold, over the 10 deg one.
        for turn_deg, want in ((45.0, 32), (10.0, 28)):
            with self.subTest(turn_deg=turn_deg):
                f = pp.BendFollower(GENTLE, lookahead_m=24.0, short_m=16.0, turn_deg=turn_deg)
                self.assertEqual(len(f.points), 63)
                got, _ = aim_at(f, 20)
                self.assertEqual(got, f.points[want])
                got, _ = aim_at(f, 31)
                self.assertEqual(got, f.points[43])

    def test_equal_lookaheads_are_a_plain_follower(self):
        f = pp.BendFollower(RIGHT, lookahead_m=16.0, short_m=16.0, turn_deg=45.0)
        g = rp.PathFollower(RIGHT, lookahead_m=16.0)
        for k in (0, 5, 20, 29, 31, 40, 60):
            with self.subTest(k=k):
                self.assertEqual(aim_at(f, k), aim_at(g, k))
                self.assertEqual(f.i, g.i)
        self.assertEqual(f.targets, f.long)


class BendingTests(unittest.TestCase):
    def test_inside_only(self):
        made = []
        settings = pp.VARIANTS["calm32"]
        with pp._bending(settings, made):
            f = rp.PathFollower(RIGHT, lookahead_m=8.0)
        self.assertIs(rp.PathFollower, FOLLOWER)
        self.assertIsInstance(f, pp.BendFollower)
        self.assertIsInstance(f, FOLLOWER)
        # The variant's settings win over the lookahead the Pilot passes.
        self.assertEqual((f.lookahead_n, f.short_n, f.turn_deg), (16, 8, 10.0))
        self.assertEqual(made, [f])

    def test_restored_after_a_failure(self):
        with self.assertRaises(ValueError):
            with pp._bending(pp.VARIANTS["bend24"], []):
                raise ValueError("boom")
        self.assertIs(rp.PathFollower, FOLLOWER)


class FlyTests(unittest.TestCase):
    def assert_restored(self):
        self.assertIs(rp.PathFollower, FOLLOWER)
        self.assertIs(pl.SlipRover, SLIP_ROVER)
        self.assertIs(pe.CountingEstimator, COUNTING)
        self.assertIs(ps.CoursePlanner, PLANNER)

    def test_plain_variants_fly_as_pace_o(self):
        for variant in ("keep16", "keep24"):
            with self.subTest(variant=variant):
                got = pp.fly("corner", 1, "drift90", variant, 0.8, course=CORNER60)
                aim = got.pop("aim")
                want = po.fly("corner", 1, "drift90", variant, 0.8, course=CORNER60)
                self.assertEqual(got, want)
                self.assertEqual(aim, pp.NO_AIM)
        self.assert_restored()

    def test_a_straight_course_flies_as_the_long_lookahead(self):
        # Each leg's path is one straight segment, so bend24 always aims 24 m
        # ahead and flies exactly as keep24.
        bend = pp.fly("tiny", 3, "outage90", "bend24", 0.8, course=TINY)
        plain = pp.fly("tiny", 3, "outage90", "keep24", 0.8, course=TINY)
        aim = bend.pop("aim")
        plain.pop("aim")
        self.assertEqual(bend, plain)
        self.assertGreater(aim["targets"], 0)
        self.assertEqual(aim["long"], aim["targets"])
        self.assert_restored()

    def test_bend_variants_at_a_corner(self):
        for variant in ("bend24", "calm24", "calm32"):
            with self.subTest(variant=variant):
                r = pp.fly("corner", 2, "outage90", variant, 0.8, course=CORNER60)
                self.assertTrue(r["ok"], r["reason"])
                self.assertGreater(r["aim"]["targets"], 0)
                self.assertGreater(r["aim"]["long"], 0)
                self.assertLess(r["aim"]["long"], r["aim"]["targets"])
                self.assertEqual(r["corner"]["corners"], 1)
                self.assertGreaterEqual(r["planner"]["plans"], 1)
                self.assertEqual(set(r["context"]), set(po.CONTEXTS))
                self.assertIn("fit_err", r)
        self.assert_restored()

    def test_failed_run_fields(self):
        r = pp.failed_run(ValueError("boom"))
        self.assertFalse(r["ok"])
        self.assertEqual(r["corner"]["n"], 0)
        self.assertEqual(r["context"], {c: EMPTY for c in po.CONTEXTS})
        self.assertEqual(r["planner"], {"plans": None, "behind": None})
        self.assertEqual(r["aim"], pp.NO_AIM)


class CheckTests(unittest.TestCase):
    def test_check_against_pace_o(self):
        with tiny_courses():
            ref = []
            for seed in (229, 230):
                r = po.fly("tiny", seed, "outage90", "keep16", 0.8)
                r.update(profile="outage90", variant="keep16", cruise=0.8, course="tiny",
                         seed=seed)
                ref.append(r)
            ref[1]["elapsed_s"] += 1.0
            with tempfile.TemporaryDirectory() as d:
                path = os.path.join(d, "runs.jsonl")
                with open(path, "w", encoding="utf-8") as f:
                    for r in ref:
                        f.write(json.dumps(r) + "\n")
                    f.write("\n")
                out = pp.check_pace_o(path)
        # 2 profiles x 2 variants x 1 course x 3 seeds = 12 missions checked;
        # the reference has 2 of them, and seed 230 was altered.
        self.assertEqual((out["compared"], out["identical"], out["missing"]), (2, 1, 10))
        self.assertEqual(len(out["different"]), 1)
        self.assertEqual(out["different"][0]["seed"], 230)
        self.assertEqual(out["different"][0]["variant"], "keep16")
        self.assertEqual(out["different"][0]["fields"], ["elapsed_s"])


def _run(variant, seed, elapsed, profile="outage90", ok=True, aim=None):
    return {"profile": profile, "variant": variant, "cruise": 0.8, "course": "blocks",
            "seed": seed, "ok": ok, "elapsed_s": elapsed, "time_s": {"stopped": 10.0},
            "reports": 5, "reached": 5,
            "offset": {"n": 5, "median_m": 1.0, "p95_m": 3.0, "max_m": 5.0},
            "corner": {"n": 0, "median_m": None, "p95_m": None, "max_m": None, "corners": 0,
                       "median_past_m": None, "max_past_m": None},
            "context": {c: EMPTY for c in po.CONTEXTS},
            "planner": {"plans": 5, "behind": 0},
            "aim": aim or dict(pp.NO_AIM)}


class SummaryTests(unittest.TestCase):
    def test_pair_effects(self):
        runs = ([_run("keep16", s, 100.0) for s in range(1, 7)]
                + [_run("bend24", s, 90.0) for s in range(1, 7)])
        effects, tallies = pp.pair_effects(runs)
        self.assertIsNot(pi.PAIRS, pp.PAIRS)
        self.assertEqual(len(effects), 1)
        self.assertEqual((effects[0]["faster"], effects[0]["slower"]), (6, 0))
        self.assertEqual(tallies, [{"profile": "outage90", "variant": "bend24",
                                    "against": "keep16", "groups": 1, "groups_faster": 1,
                                    "groups_slower": 0, "groups_lost": 0, "groups_gained": 0,
                                    "largest_median_diff_share": -0.1}])

    def test_profile_effects(self):
        runs = ([_run("bend24", s, 100.0) for s in range(1, 7)]
                + [_run("bend24", s, 110.0, profile="drift90") for s in range(1, 7)])
        effects, tallies = pp.profile_effects(runs)
        self.assertNotIn("bend24", pj.VARIANTS)
        self.assertEqual(len(effects), 1)
        self.assertEqual(tallies[0]["groups_slower"], 1)
        self.assertEqual((tallies[0]["variant"], tallies[0]["profile"], tallies[0]["against"]),
                         ("bend24", "drift90", "outage90"))

    def test_aim_rows(self):
        runs = [_run("bend24", 1, 100.0, aim={"targets": 100, "long": 75}),
                _run("bend24", 2, 100.0, aim={"targets": 200, "long": 100}),
                _run("bend24", 3, 100.0, ok=False, aim={"targets": 10, "long": 0}),
                _run("keep16", 1, 100.0)]
        self.assertEqual(pp.aim_rows(runs),
                         [{"profile": "outage90", "variant": "bend24", "cruise": 0.8,
                           "course": "blocks", "missions": 2, "median_targets": 150.0,
                           "median_long_share": 0.625}])

    def test_main_small(self):
        with tiny_courses():
            with tempfile.TemporaryDirectory() as d, redirect_stdout(io.StringIO()):
                pp.main(["--out-dir", d, "--first-seed", "253", "--seeds", "2",
                         "--profiles", "drift90", "--variants", "bend24"])
                with open(os.path.join(d, "summary.json")) as f:
                    out = json.load(f)
                with open(os.path.join(d, "report.md")) as f:
                    md = f.read()
                with open(os.path.join(d, "runs.jsonl")) as f:
                    lines = [json.loads(x) for x in f if x.strip()]
        # outage90 and keep16 are always flown: 2 profiles x 2 variants x 2 seeds.
        self.assertEqual(out["runs"], 8)
        self.assertEqual(out["seeds"], [253, 254])
        self.assertEqual(sorted({r["profile"] for r in lines}), ["drift90", "outage90"])
        self.assertEqual(sorted({r["variant"] for r in lines}), ["bend24", "keep16"])
        self.assertTrue(all("aim" in r and "context" in r and "planner" in r
                            and "corner" in r and "fit_err" in r for r in lines))
        self.assertTrue(out["done"])
        self.assertEqual(sorted((v["profile"], v["variant"], v["against"])
                                for v in out["verdicts"]),
                         [("drift90", "bend24", "keep16"), ("outage90", "bend24", "keep16")])
        self.assertEqual(sorted(v["variant"] for v in out["profile_verdicts"]),
                         ["bend24", "keep16"])
        self.assertEqual(out["learner"], "long20")
        self.assertEqual(out["planner_kind"], "keep")
        # Only the bending follower keeps an aim record; on the straight tiny
        # course it always aims long.
        self.assertEqual(sorted((x["profile"], x["variant"]) for x in out["aim"]),
                         [("drift90", "bend24"), ("outage90", "bend24")])
        self.assertTrue(all(x["median_long_share"] == 1.0 for x in out["aim"]))
        self.assertIsNone(out["check"])
        self.assertIn("## How often the follower aimed long", md)
        self.assertIn("Seeds 253-254.", md)
        self.assertIs(rp.PathFollower, FOLLOWER)
        self.assertIs(pl.SlipRover, SLIP_ROVER)
        self.assertIs(pe.CountingEstimator, COUNTING)
        self.assertIs(ps.CoursePlanner, PLANNER)


if __name__ == "__main__":
    unittest.main()
