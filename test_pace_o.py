"""Tests for the study of where the rover strays from its course.

Run: python -m unittest test_pace_o -v
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
import pace_i as pi  # noqa: E402
import pace_j as pj  # noqa: E402
import pace_l as pl  # noqa: E402
import pace_m as pm  # noqa: E402
import pace_n as pn  # noqa: E402
import pace_o as po  # noqa: E402
import pace_study as ps  # noqa: E402
import rover_pilot as rp  # noqa: E402

TINY = {"points": [(0.0, 0.0), (30.0, 0.0)], "checkpoints": [1]}
# One right-angle path corner at (60, 0); the only checkpoint is the end.
CORNER60 = {"points": [(0.0, 0.0), (60.0, 0.0), (60.0, 60.0)], "checkpoints": [2]}
# The same shape with a checkpoint at the corner.
KEEP60 = {"points": [(0.0, 0.0), (60.0, 0.0), (60.0, 60.0)], "checkpoints": [1, 2]}
# An interior checkpoint at (100, 0), a path corner at (100, 100).
CONTEXT = {"points": [(0.0, 0.0), (100.0, 0.0), (100.0, 100.0), (200.0, 100.0)],
           "checkpoints": [1, 3]}
FOLLOWER = rp.PathFollower
SLIP_ROVER = pl.SlipRover
COUNTING = pe.CountingEstimator
PLANNER = ps.CoursePlanner
PATH = [(37.0, -122.0), (37.001, -122.0)]
LAT0, LON0 = 37.0, -122.0
EMPTY = {"n": 0, "median_m": None, "p95_m": None, "max_m": None, "far": 0}


def latlon(p):
    return rp.offset_latlon(LAT0, LON0, p[0], p[1])


def north_east(q):
    e, n = rp.to_enu(LAT0, LON0, q[0], q[1])
    return n, e


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
        self.assertEqual(list(po.PROFILES), ["outage90", "drift90"])
        for name in po.PROFILES:
            self.assertIs(po.PROFILES[name], pl.PROFILES[name])
        self.assertEqual(po.BASE_PROFILE, "outage90")
        self.assertEqual(po.PROFILE_PAIRS, (("outage90", "drift90"),))

    def test_variants(self):
        self.assertEqual(po.VARIANTS, {
            "diag16": {"planner": "diag", "lookahead_m": 16.0},
            "keep16": {"planner": "keep", "lookahead_m": 16.0},
            "keep8": {"planner": "keep", "lookahead_m": 8.0},
            "keep24": {"planner": "keep", "lookahead_m": 24.0}})
        self.assertEqual(po.ALWAYS, ("diag16", "keep16"))
        self.assertEqual(po.PAIRS, (("diag16", "keep16"), ("keep16", "keep8"),
                                    ("keep16", "keep24")))
        # v0.18.0's real-rover pilot: its learner and its lookahead.
        self.assertEqual(po.LEARNER, "long20")
        self.assertEqual(pm.VARIANTS[po.LEARNER], rp.HEADING_LEARNER)
        self.assertEqual(rp.PATH_LOOKAHEAD_M, po.VARIANTS["diag16"]["lookahead_m"])
        self.assertEqual(po.CRUISES, (0.8,))
        self.assertEqual(po.FIRST_SEED, 229)
        self.assertEqual(po.CHECKED, {"profiles": ("outage90", "drift90"), "variant": "diag16",
                                      "against": "look16", "seeds": (205, 206, 207)})
        self.assertEqual(pn.VARIANTS["look16"], {"lookahead_m": 16.0})
        self.assertEqual((po.CHECKPOINT_BEFORE_M, po.CHECKPOINT_AFTER_M, po.FAR_M),
                         (20.0, 60.0, 8.0))
        self.assertEqual(po.CONTEXTS, ("checkpoint", "corner", "other", "outage", "fix"))


class KeepPointsTests(unittest.TestCase):
    def setUp(self):
        self.blocks = ps.COURSES["blocks"]
        self.pts = self.blocks["points"]

    def test_before_a_checkpoint_corner(self):
        # Leg 1 runs from checkpoint 3 (200, 100) to checkpoint 6 (300, 300).
        # 10 m before the corner and 0.5 m inside it, leg_points cuts across
        # to (200, 200); keep_points goes through the corner first.
        p = (190.0, 100.5)
        self.assertEqual(self.pts[3], (200.0, 100.0))
        self.assertEqual(ps.leg_points(self.blocks, 1, *p),
                         [p, (200.0, 200.0), (300.0, 200.0), (300.0, 300.0)])
        self.assertEqual(po.keep_points(self.blocks, 1, *p),
                         [p, (200.0, 100.0), (200.0, 200.0), (300.0, 200.0), (300.0, 300.0)])

    def test_otherwise_as_leg_points(self):
        for leg, p in ((1, (250.0, 201.0)),   # in the middle of the leg
                       (1, (203.0, 110.0)),   # just past the corner
                       (0, (1.0, 0.5)),       # at the start
                       (0, (-2.0, 0.0)),      # behind the start
                       (4, (690.0, 600.5))):  # the last leg, before its path corner
            with self.subTest(leg=leg, p=p):
                self.assertEqual(po.keep_points(self.blocks, leg, *p),
                                 ps.leg_points(self.blocks, leg, *p))


class PlannerTests(unittest.TestCase):
    def setUp(self):
        self.blocks = ps.COURSES["blocks"]
        self.cp = latlon(self.blocks["points"][6])

    def test_diag_is_course_planner(self):
        for p in ((190.0, 100.5), (250.0, 201.0), (0.0, 0.0)):
            with self.subTest(p=p):
                want = ps.CoursePlanner(self.blocks, LAT0, LON0)(*latlon(p), *self.cp)
                got = po.LegPlanner(self.blocks, LAT0, LON0)(*latlon(p), *self.cp)
                self.assertEqual(got, want)

    def test_keep_and_counts(self):
        p = (190.0, 100.5)
        for keep in (False, True):
            with self.subTest(keep=keep):
                planner = po.LegPlanner(self.blocks, LAT0, LON0, keep=keep)
                got = [north_east(q) for q in planner(*latlon(p), *self.cp)]
                want = (po.keep_points if keep else ps.leg_points)(self.blocks, 1, *p)
                self.assertEqual(len(got), len(want))
                for g, w in zip(got, want):
                    self.assertAlmostEqual(g[0], w[0], places=4)
                    self.assertAlmostEqual(g[1], w[1], places=4)
                self.assertEqual((planner.calls, planner.behind), (1, 1))
        planner = po.LegPlanner(self.blocks, LAT0, LON0, keep=True)
        planner(*latlon((250.0, 201.0)), *self.cp)
        self.assertEqual((planner.calls, planner.behind), (1, 0))

    def test_planning_inside_only(self):
        for kind in ("diag", "keep"):
            with self.subTest(kind=kind):
                made = []
                with po._planning(kind, made):
                    p = ps.CoursePlanner(self.blocks, LAT0, LON0)
                self.assertIs(ps.CoursePlanner, PLANNER)
                self.assertIsInstance(p, po.LegPlanner)
                self.assertEqual(p.keep, kind == "keep")
                self.assertEqual(made, [p])

    def test_restored_after_a_failure(self):
        with self.assertRaises(ValueError):
            with po._planning("keep", []):
                raise ValueError("boom")
        self.assertIs(ps.CoursePlanner, PLANNER)


class AimingTests(unittest.TestCase):
    def test_lookahead_inside_only(self):
        for metres, n in ((8.0, 4), (16.0, 8), (24.0, 12)):
            with self.subTest(metres=metres):
                with po._aiming(metres):
                    f = rp.PathFollower(PATH)
                    g = rp.PathFollower(PATH, lookahead_m=8.0, step_m=4.0)
                self.assertIsInstance(f, FOLLOWER)
                self.assertEqual(f.lookahead_n, n)
                # The lookahead given wins; other settings pass through.
                self.assertEqual(g.lookahead_n, int(round(metres / 4.0)))
                self.assertIs(rp.PathFollower, FOLLOWER)

    def test_restored_after_a_failure(self):
        with self.assertRaises(ValueError):
            with po._aiming(24.0):
                raise ValueError("boom")
        self.assertIs(rp.PathFollower, FOLLOWER)


def drive(sim, steps=50):
    for _ in range(steps):
        sim.control(1.0, 0.0)
        sim.sleep(0.1)


class WatchingTests(unittest.TestCase):
    def test_samples_while_driving_forward_and_only_reads(self):
        samples = []
        with po._watching(samples):
            sim = pl.SlipRover([(500.0, 0.0)], seed=3, **pl.PROFILES["outage90"])
        self.assertIs(pl.SlipRover, SLIP_ROVER)
        sim.control(0.0, 0.0)
        sim.sleep(0.5)
        self.assertEqual(samples, [])  # stopped: nothing
        drive(sim)
        self.assertGreaterEqual(len(samples), 3)
        self.assertLessEqual(len(samples), 6)
        self.assertNotEqual(samples[0][:2], samples[-1][:2])
        for s in samples:
            self.assertEqual(len(s), 3)
            self.assertIsInstance(s[2], bool)
        plain = pl.SlipRover([(500.0, 0.0)], seed=3, **pl.PROFILES["outage90"])
        plain.control(0.0, 0.0)
        plain.sleep(0.5)
        drive(plain)
        self.assertEqual((sim.north, sim.east, sim.t), (plain.north, plain.east, plain.t))

    def test_restored_after_a_failure(self):
        with self.assertRaises(ValueError):
            with po._watching([]):
                raise ValueError("boom")
        self.assertIs(pl.SlipRover, SLIP_ROVER)


class ContextTests(unittest.TestCase):
    def test_stations(self):
        pts = CONTEXT["points"]
        cum = po.stations(pts)
        self.assertEqual(cum, [0.0, 100.0, 200.0, 300.0])
        self.assertAlmostEqual(po.station(pts, cum, (50.0, 3.0)), 50.0)
        self.assertAlmostEqual(po.station(pts, cum, (110.0, 10.0)), 110.0)
        self.assertAlmostEqual(po.station(pts, cum, (150.0, 103.0)), 250.0)
        self.assertAlmostEqual(po.station(pts, cum, (-5.0, 0.0)), 0.0)

    def test_each_place(self):
        # (50, 0): 50 m before the checkpoint at (100, 0): elsewhere.
        # (85, 0): 15 m before it: near the checkpoint.
        # (110, 10): 10 m after it along the course, 10 m off, GPS out: near
        # the checkpoint, far.
        # (100, 95): 95 m after the checkpoint, 5 m from the path corner.
        # (150, 103): 3 m off, 50 m past the path corner: elsewhere.
        samples = [(50.0, 0.0, False), (85.0, 0.0, False), (110.0, 10.0, True),
                   (100.0, 95.0, False), (150.0, 103.0, False)]
        out = po.contexts(CONTEXT["points"], CONTEXT["checkpoints"], samples)
        self.assertEqual(out["checkpoint"],
                         {"n": 2, "median_m": 5.0, "p95_m": 0.0, "max_m": 10.0, "far": 1})
        self.assertEqual(out["corner"],
                         {"n": 1, "median_m": 0.0, "p95_m": 0.0, "max_m": 0.0, "far": 0})
        self.assertEqual(out["other"],
                         {"n": 2, "median_m": 1.5, "p95_m": 0.0, "max_m": 3.0, "far": 0})
        self.assertEqual(out["outage"],
                         {"n": 1, "median_m": 10.0, "p95_m": 10.0, "max_m": 10.0, "far": 1})
        self.assertEqual(out["fix"],
                         {"n": 4, "median_m": 0.0, "p95_m": 0.0, "max_m": 3.0, "far": 0})

    def test_the_last_checkpoint_does_not_count(self):
        out = po.contexts(TINY["points"], TINY["checkpoints"], [(25.0, 1.0, False)])
        self.assertEqual(out["other"]["n"], 1)
        self.assertEqual(out["checkpoint"], EMPTY)

    def test_blocks_places(self):
        blocks = ps.COURSES["blocks"]
        out = po.contexts(blocks["points"], blocks["checkpoints"],
                          [(150.0, 100.0, False),   # 150 m along: elsewhere
                           (100.0, 15.0, False),    # 115 m along, 15 m from (100, 0)'s corner
                           (190.0, 112.0, False),   # inside checkpoint 3's corner, 10 m off
                           (200.0, 150.0, False)])  # 50 m after checkpoint 3
        self.assertEqual((out["other"]["n"], out["corner"]["n"], out["checkpoint"]["n"]),
                         (1, 1, 2))
        self.assertEqual(out["checkpoint"]["far"], 1)

    def test_nothing(self):
        out = po.contexts([], [], [])
        self.assertEqual(out, {c: EMPTY for c in po.CONTEXTS})


class FlyTests(unittest.TestCase):
    def test_diag16_flies_as_pace_n_look16(self):
        for profile in ("outage90", "drift90"):
            with self.subTest(profile=profile):
                want = pn.fly("corner", 1, profile, "look16", 0.8, course=CORNER60)
                got = po.fly("corner", 1, profile, "diag16", 0.8, course=CORNER60)
                context = got.pop("context")
                planner = got.pop("planner")
                self.assertEqual(got, want)
                self.assertEqual(set(context), set(po.CONTEXTS))
                self.assertGreaterEqual(planner["plans"], 1)
                self.assertEqual(planner["behind"], 0)
        self.assertIs(rp.PathFollower, FOLLOWER)
        self.assertIs(pl.SlipRover, SLIP_ROVER)
        self.assertIs(pe.CountingEstimator, COUNTING)
        self.assertIs(ps.CoursePlanner, PLANNER)

    def test_keep_is_diag_without_an_interior_checkpoint(self):
        keep = po.fly("corner", 2, "drift90", "keep16", 0.8, course=CORNER60)
        diag = po.fly("corner", 2, "drift90", "diag16", 0.8, course=CORNER60)
        self.assertEqual(keep, diag)
        self.assertTrue(keep["ok"], keep["reason"])
        self.assertEqual(keep["corner"]["corners"], 1)
        self.assertGreater(keep["context"]["corner"]["n"], 0)
        self.assertEqual(keep["context"]["checkpoint"]["n"], 0)

    def test_a_checkpoint_corner(self):
        for variant in ("keep16", "diag16", "keep8", "keep24"):
            with self.subTest(variant=variant):
                r = po.fly("keep60", 2, "outage90", variant, 0.8, course=KEEP60)
                self.assertGreaterEqual(r["planner"]["plans"], 1)
                self.assertLessEqual(r["planner"]["behind"], r["planner"]["plans"])
                self.assertEqual(r["corner"]["corners"], 0)  # the corner is a checkpoint
                self.assertEqual(r["context"]["corner"]["n"], 0)
                self.assertIn("fit_err", r)
        self.assertIs(ps.CoursePlanner, PLANNER)
        self.assertIs(rp.PathFollower, FOLLOWER)

    def test_failed_run_fields(self):
        r = po.failed_run(ValueError("boom"))
        self.assertFalse(r["ok"])
        self.assertEqual(r["corner"]["n"], 0)
        self.assertEqual(r["fit_err"]["n"], 0)
        self.assertEqual(r["context"], {c: EMPTY for c in po.CONTEXTS})
        self.assertEqual(r["planner"], {"plans": None, "behind": None})


class CheckTests(unittest.TestCase):
    def test_check_against_pace_n(self):
        with tiny_courses():
            ref = []
            for seed in (205, 206):
                r = pn.fly("tiny", seed, "outage90", "look16", 0.8)
                r.update(profile="outage90", variant="look16", cruise=0.8, course="tiny",
                         seed=seed)
                ref.append(r)
            ref[1]["elapsed_s"] += 1.0
            with tempfile.TemporaryDirectory() as d:
                path = os.path.join(d, "runs.jsonl")
                with open(path, "w", encoding="utf-8") as f:
                    for r in ref:
                        f.write(json.dumps(r) + "\n")
                    f.write("\n")
                out = po.check_pace_n(path)
        # 2 profiles x 1 course x 3 seeds = 6 missions checked; the reference
        # has 2 of them, and seed 206 was altered.
        self.assertEqual((out["compared"], out["identical"], out["missing"]), (2, 1, 4))
        self.assertEqual(len(out["different"]), 1)
        self.assertEqual(out["different"][0]["seed"], 206)
        self.assertEqual(out["different"][0]["fields"], ["elapsed_s"])


def _run(variant, seed, elapsed, profile="outage90", ok=True, context=None, planner=None):
    return {"profile": profile, "variant": variant, "cruise": 0.8, "course": "blocks",
            "seed": seed, "ok": ok, "elapsed_s": elapsed, "time_s": {"stopped": 10.0},
            "reports": 5, "reached": 5,
            "offset": {"n": 5, "median_m": 1.0, "p95_m": 3.0, "max_m": 5.0},
            "corner": {"n": 0, "median_m": None, "p95_m": None, "max_m": None, "corners": 0,
                       "median_past_m": None, "max_past_m": None},
            "context": context or {c: EMPTY for c in po.CONTEXTS},
            "planner": planner or {"plans": 5, "behind": 4}}


def _ctx(**kw):
    out = {c: EMPTY for c in po.CONTEXTS}
    for name, (n, median, p95, mx, far) in kw.items():
        out[name] = {"n": n, "median_m": median, "p95_m": p95, "max_m": mx, "far": far}
    return out


class SummaryTests(unittest.TestCase):
    def test_pair_effects(self):
        runs = ([_run("diag16", s, 100.0) for s in range(1, 7)]
                + [_run("keep16", s, 110.0) for s in range(1, 7)])
        effects, tallies = po.pair_effects(runs)
        self.assertIsNot(pi.PAIRS, po.PAIRS)
        self.assertEqual(len(effects), 1)
        self.assertEqual((effects[0]["faster"], effects[0]["slower"]), (0, 6))
        self.assertEqual(tallies, [{"profile": "outage90", "variant": "keep16",
                                    "against": "diag16", "groups": 1, "groups_faster": 0,
                                    "groups_slower": 1, "groups_lost": 0, "groups_gained": 0,
                                    "largest_median_diff_share": 0.1}])

    def test_profile_effects(self):
        runs = ([_run("keep24", s, 100.0) for s in range(1, 7)]
                + [_run("keep24", s, 110.0, profile="drift90") for s in range(1, 7)])
        effects, tallies = po.profile_effects(runs)
        self.assertNotIn("keep24", pj.VARIANTS)
        self.assertEqual(len(effects), 1)
        self.assertEqual(tallies[0]["groups_slower"], 1)
        self.assertEqual((tallies[0]["variant"], tallies[0]["profile"], tallies[0]["against"]),
                         ("keep24", "drift90", "outage90"))

    def test_context_rows(self):
        runs = [_run("diag16", 1, 100.0, context=_ctx(checkpoint=(10, 3.0, 11.0, 13.0, 3),
                                                      other=(20, 1.0, 4.0, 9.0, 1),
                                                      fix=(30, 1.5, 9.0, 13.0, 4))),
                _run("diag16", 2, 100.0, context=_ctx(checkpoint=(12, 5.0, 9.0, 10.0, 4),
                                                      other=(18, 2.0, 6.0, 7.0, 0),
                                                      fix=(30, 2.0, 8.0, 10.0, 4))),
                _run("diag16", 3, 100.0, ok=False,
                     context=_ctx(checkpoint=(5, 30.0, 30.0, 30.0, 5)))]
        rows = po.context_rows(runs)
        self.assertEqual([x["context"] for x in rows], list(po.CONTEXTS))
        self.assertEqual(rows[0], {"profile": "outage90", "variant": "diag16", "cruise": 0.8,
                                   "course": "blocks", "context": "checkpoint", "missions": 2,
                                   "samples": 22, "far": 7, "far_share": 0.875,
                                   "median_m": 4.0, "p95_m": 10.0, "max_m": 11.5})
        self.assertEqual((rows[1]["missions"], rows[1]["far_share"], rows[1]["p95_m"]),
                         (0, 0.0, None))
        self.assertEqual((rows[2]["samples"], rows[2]["far_share"], rows[2]["p95_m"]),
                         (38, 0.125, 5.0))
        self.assertEqual((rows[4]["far"], rows[4]["far_share"], rows[4]["median_m"]),
                         (8, 1.0, 1.75))

    def test_planner_rows(self):
        runs = [_run("keep16", 1, 100.0, planner={"plans": 5, "behind": 4}),
                _run("keep16", 2, 100.0, planner={"plans": 7, "behind": 4}),
                _run("keep16", 3, 100.0, ok=False, planner={"plans": None, "behind": None})]
        self.assertEqual(po.planner_rows(runs),
                         [{"profile": "outage90", "variant": "keep16", "cruise": 0.8,
                           "course": "blocks", "missions": 2, "median_plans": 6.0,
                           "median_behind": 4.0}])

    def test_main_small(self):
        with tiny_courses():
            with tempfile.TemporaryDirectory() as d, redirect_stdout(io.StringIO()):
                po.main(["--out-dir", d, "--first-seed", "229", "--seeds", "2",
                         "--profiles", "drift90", "--variants", "keep24"])
                with open(os.path.join(d, "summary.json")) as f:
                    out = json.load(f)
                with open(os.path.join(d, "report.md")) as f:
                    md = f.read()
                with open(os.path.join(d, "runs.jsonl")) as f:
                    lines = [json.loads(x) for x in f if x.strip()]
        # outage90, diag16 and keep16 are always flown: 2 profiles x 3 variants x 2 seeds.
        self.assertEqual(out["runs"], 12)
        self.assertEqual(out["seeds"], [229, 230])
        self.assertEqual(sorted({r["profile"] for r in lines}), ["drift90", "outage90"])
        self.assertEqual(sorted({r["variant"] for r in lines}), ["diag16", "keep16", "keep24"])
        self.assertTrue(all("context" in r and "planner" in r and "corner" in r
                            and "fit_err" in r for r in lines))
        self.assertTrue(out["done"])
        self.assertEqual(sorted((v["profile"], v["variant"], v["against"])
                                for v in out["verdicts"]),
                         [("drift90", "keep16", "diag16"), ("drift90", "keep24", "keep16"),
                          ("outage90", "keep16", "diag16"), ("outage90", "keep24", "keep16")])
        self.assertEqual(sorted(v["variant"] for v in out["profile_verdicts"]),
                         ["diag16", "keep16", "keep24"])
        self.assertEqual(out["learner"], "long20")
        self.assertEqual(out["corner"], [])  # the tiny course has no corner
        # Its only checkpoint is the last, so nothing is near a checkpoint.
        self.assertTrue(all(x["missions"] == 0 for x in out["context"]
                            if x["context"] == "checkpoint"))
        self.assertIsNone(out["check"])
        self.assertIn("## Where the rover strays", md)
        self.assertIn("Seeds 229-230.", md)
        self.assertIs(rp.PathFollower, FOLLOWER)
        self.assertIs(pl.SlipRover, SLIP_ROVER)
        self.assertIs(pe.CountingEstimator, COUNTING)
        self.assertIs(ps.CoursePlanner, PLANNER)


if __name__ == "__main__":
    unittest.main()
