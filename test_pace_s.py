"""Tests for the study of starting the GPS average again after a gap.

Run: python -m unittest test_pace_s -v
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
import pace_o as po  # noqa: E402
import pace_p as pp  # noqa: E402
import pace_q as pq  # noqa: E402
import pace_s as pss  # noqa: E402
import pace_study as ps  # noqa: E402
import rover_pilot as rp  # noqa: E402

TINY = {"points": [(0.0, 0.0), (30.0, 0.0)], "checkpoints": [1]}
# One right-angle path corner at (60, 0); the only checkpoint is the end.
CORNER60 = {"points": [(0.0, 0.0), (60.0, 0.0), (60.0, 60.0)], "checkpoints": [2]}
GPS_FILTER = rp.GpsFilter
FOLLOWER = rp.PathFollower
SLIP_ROVER = pl.SlipRover
COUNTING = pe.CountingEstimator
PLANNER = ps.CoursePlanner
KNOWN = set(pl.PROFILES)
EMPTY = {"n": 0, "median_m": None, "p95_m": None, "max_m": None, "far": 0}


class tiny_courses:
    """Replace pace_study's courses with one short course while in use."""

    def __enter__(self):
        self.saved = dict(ps.COURSES)
        ps.COURSES.clear()
        ps.COURSES["tiny"] = TINY

    def __exit__(self, *exc):
        ps.COURSES.clear()
        ps.COURSES.update(self.saved)


def build(variant):
    """The GPS filter the Pilot gets for a variant, as pace_s.fly builds it."""
    made = []
    with pq._filtering(pss.VARIANTS[variant], made):
        f = rp.GpsFilter()
    return f


def feed(f, fixes):
    return [f.update(lat, lon, t) for t, lat, lon in fixes]


class SetupTests(unittest.TestCase):
    def test_profiles(self):
        self.assertEqual(list(pss.PROFILES), ["outage90", "quiet90", "quietdrift90", "quiet45"])
        for name in ("outage90", "quiet90", "quietdrift90"):
            self.assertIs(pss.PROFILES[name], pq.PROFILES[name])
        self.assertEqual(pss.PROFILES["quiet45"],
                         dict(pl.PROFILES["outage45"], gps_noise_m=0.22))
        self.assertEqual(pss.PROFILES["quiet45"]["outage_s"], 45.0)
        self.assertEqual(pss.PROFILES["quiet45"]["clear_s"], 300.0)
        self.assertEqual(pss.BASE_PROFILE, "outage90")
        self.assertEqual(pss.PROFILE_PAIRS, (("outage90", "quiet90"), ("quiet90", "quietdrift90"),
                                             ("quiet45", "quiet90")))

    def test_variants(self):
        self.assertEqual(pss.VARIANTS, {"a0.3": {"alpha": 0.3},
                                        "restart": {"alpha": 0.3, "beta": 0.0, "track": True}})
        # The shipped pilot's filter.
        self.assertEqual(pss.VARIANTS["a0.3"], pq.VARIANTS["a0.3"])
        self.assertEqual(pss.VARIANTS["a0.3"]["alpha"], rp.GpsFilter().alpha)
        self.assertEqual(pss.BASE_VARIANT, "a0.3")
        self.assertEqual(pss.PAIRS, (("a0.3", "restart"),))
        self.assertEqual(pss.CRUISES, (0.8,))
        self.assertEqual(pss.FIRST_SEED, 325)
        self.assertEqual(pss.CHECKED, {"profiles": ("outage90", "quiet90"),
                                       "variants": (("a0.3", "a0.3-16"),),
                                       "seeds": (311, 312, 313)})
        self.assertEqual(pss.SNAP_M, 20.0)


class FilterTests(unittest.TestCase):
    def test_the_filters_built(self):
        a, b = build("a0.3"), build("restart")
        self.assertIs(type(a), GPS_FILTER)
        self.assertIsInstance(b, pq.TrackingGpsFilter)
        self.assertEqual((b.alpha, b.beta, b.restart, b.max_age_s), (0.3, 0.0, True, 3.0))
        self.assertIs(rp.GpsFilter, GPS_FILTER)

    def test_without_a_gap_restart_is_the_shipped_average(self):
        # A fix every 2 s, one reading repeated: never more than 3 s without one.
        fixes = [(0.0, 37.0, -122.0), (2.0, 37.00001, -122.0), (3.0, 37.00001, -122.0),
                 (4.0, 37.00002, -122.00001), (6.0, 37.00003, -122.00001),
                 (8.0, 37.00005, -122.00002)]
        a, b = build("a0.3"), build("restart")
        self.assertEqual(feed(a, fixes), feed(b, fixes))
        self.assertEqual((a.lat, a.lon), (b.lat, b.lon))
        self.assertEqual(b.restarts, 0)

    def test_after_a_gap_restart_starts_from_the_fix(self):
        # 98 s without a fix, then one 89 m on: within the 3 m/s x 98 s + 10 m
        # the jump check allows, so both take it.
        fixes = [(0.0, 37.0, -122.0), (2.0, 37.0001, -122.0), (100.0, 37.0009, -122.0)]
        a, b = build("a0.3"), build("restart")
        feed(a, fixes)
        feed(b, fixes)
        self.assertEqual(a.raw, (37.0009, -122.0))
        self.assertEqual(b.raw, (37.0009, -122.0))
        # The shipped average: 37.0 + 0.3 x 0.0001, then 0.3 of the way to the
        # new fix: 37.00003 + 0.3 x 0.00087.
        self.assertAlmostEqual(a.lat, 37.000291, places=9)
        self.assertEqual((b.lat, b.lon), b.raw)
        self.assertEqual(b.restarts, 1)
        # The next fix is averaged again: 37.0009 + 0.3 x 0.00002.
        feed(a, [(102.0, 37.00092, -122.0)])
        feed(b, [(102.0, 37.00092, -122.0)])
        self.assertAlmostEqual(b.lat, 37.000906, places=9)
        self.assertEqual(b.restarts, 1)

    def test_a_far_jump_is_still_dropped(self):
        # 111 m in 2 s is more than 3 m/s x 2 s + 10 m: both drop it.
        fixes = [(0.0, 37.0, -122.0), (2.0, 37.00001, -122.0)]
        a, b = build("a0.3"), build("restart")
        feed(a, fixes)
        feed(b, fixes)
        before = (a.lat, a.lon)
        self.assertEqual(feed(a, [(4.0, 37.00101, -122.0)]), [None])
        self.assertEqual(feed(b, [(4.0, 37.00101, -122.0)]), [None])
        self.assertEqual((a.lat, a.lon), before)
        self.assertEqual((b.lat, b.lon), before)


class FlyTests(unittest.TestCase):
    def assert_restored(self):
        self.assertIs(rp.GpsFilter, GPS_FILTER)
        self.assertIs(rp.PathFollower, FOLLOWER)
        self.assertIs(pl.SlipRover, SLIP_ROVER)
        self.assertIs(pe.CountingEstimator, COUNTING)
        self.assertIs(ps.CoursePlanner, PLANNER)
        self.assertEqual(set(pl.PROFILES), KNOWN)

    def test_a03_flies_as_pace_q(self):
        for profile in ("outage90", "quiet90", "quietdrift90"):
            with self.subTest(profile=profile):
                got = pss.fly("corner", 1, profile, "a0.3", 0.8, course=CORNER60)
                want = pq.fly("corner", 1, profile, "a0.3", 0.8, course=CORNER60)
                self.assertEqual(got, want)
        self.assert_restored()

    def test_a03_flies_as_pace_p_keep16(self):
        got = pss.fly("corner", 2, "drift90", "a0.3", 0.8, course=CORNER60)
        gps = got.pop("gps")
        want = pp.fly("corner", 2, "drift90", "keep16", 0.8, course=CORNER60)
        self.assertEqual(got, want)
        self.assertEqual(gps, {"filters": 1, "restarts": None})
        self.assert_restored()

    def test_restart_and_quiet45(self):
        for profile in ("quiet90", "quiet45"):
            with self.subTest(profile=profile):
                r = pss.fly("corner", 3, profile, "restart", 0.8, course=CORNER60)
                self.assertEqual(r["gps"]["filters"], 1)
                self.assertIsInstance(r["gps"]["restarts"], int)
                for key in ("aim", "corner", "context", "planner", "position_err"):
                    self.assertIn(key, r)
        self.assert_restored()

    def test_restored_after_a_failure(self):
        with self.assertRaises(KeyError):
            pss.fly("corner", 1, "no-such-profile", "restart", 0.8, course=CORNER60)
        self.assert_restored()

    def test_failed_run_fields(self):
        r = pss.failed_run(ValueError("boom"))
        self.assertFalse(r["ok"])
        self.assertEqual(r["gps"], pq.NO_GPS)
        self.assertEqual(r["aim"], pp.NO_AIM)


class CheckTests(unittest.TestCase):
    def test_check_against_pace_r(self):
        with tiny_courses():
            ref = []
            for seed in (311, 312):
                r = pss.fly("tiny", seed, "outage90", "a0.3", 0.8)
                r.update(profile="outage90", variant="a0.3-16", cruise=0.8, course="tiny",
                         seed=seed)
                ref.append(r)
            ref[1]["elapsed_s"] += 1.0
            with tempfile.TemporaryDirectory() as d:
                path = os.path.join(d, "runs.jsonl")
                with open(path, "w", encoding="utf-8") as f:
                    for r in ref:
                        f.write(json.dumps(r) + "\n")
                    f.write("\n")
                out = pss.check(path)
        # 2 profiles x 1 variant x 1 course x 3 seeds = 6 missions checked; the
        # reference has 2 of them, and seed 312 was altered.
        self.assertEqual((out["compared"], out["identical"], out["missing"]), (2, 1, 4))
        self.assertEqual(len(out["different"]), 1)
        self.assertEqual(out["different"][0]["seed"], 312)
        self.assertEqual(out["different"][0]["variant"], "a0.3")
        self.assertEqual(out["different"][0]["against"], "a0.3-16")
        self.assertEqual(out["different"][0]["fields"], ["elapsed_s"])
        self.assertIs(rp.GpsFilter, GPS_FILTER)
        self.assertEqual(set(pl.PROFILES), KNOWN)


def _run(variant, seed, elapsed, profile="outage90", ok=True, restarts=None, max_m=10.0):
    return {"profile": profile, "variant": variant, "cruise": 0.8, "course": "blocks",
            "seed": seed, "ok": ok, "elapsed_s": elapsed, "time_s": {"stopped": 10.0},
            "reports": 5, "reached": 5, "recoveries": 0,
            "offset": {"n": 5, "median_m": 1.0, "p95_m": 3.0, "max_m": 5.0},
            "position_err": {"n": 5, "median_m": 2.0, "p95_m": 4.0, "max_m": max_m},
            "corner": {"n": 0, "median_m": None, "p95_m": None, "max_m": None, "corners": 0,
                       "median_past_m": None, "max_past_m": None},
            "context": {c: EMPTY for c in po.CONTEXTS},
            "planner": {"plans": 5, "behind": 0},
            "aim": dict(pp.NO_AIM), "gps": {"filters": 1, "restarts": restarts}}


class SummaryTests(unittest.TestCase):
    def test_pair_effects(self):
        runs = ([_run("a0.3", s, 100.0) for s in range(1, 7)]
                + [_run("restart", s, 90.0, restarts=1) for s in range(1, 7)])
        effects, tallies = pss.pair_effects(runs)
        self.assertIsNot(pi.PAIRS, pss.PAIRS)
        self.assertEqual(len(effects), 1)
        self.assertEqual((effects[0]["faster"], effects[0]["slower"]), (6, 0))
        self.assertEqual(tallies, [{"profile": "outage90", "variant": "restart",
                                    "against": "a0.3", "groups": 1, "groups_faster": 1,
                                    "groups_slower": 0, "groups_lost": 0, "groups_gained": 0,
                                    "largest_median_diff_share": -0.1}])

    def test_profile_effects(self):
        runs = ([_run("restart", s, 100.0, profile="quiet45") for s in range(1, 7)]
                + [_run("restart", s, 110.0, profile="quiet90") for s in range(1, 7)])
        effects, tallies = pss.profile_effects(runs)
        self.assertNotIn("restart", pj.VARIANTS)
        self.assertEqual(len(effects), 1)
        self.assertEqual(len(tallies), 1)
        self.assertEqual(tallies[0]["groups_slower"], 1)
        self.assertEqual((tallies[0]["variant"], tallies[0]["profile"], tallies[0]["against"]),
                         ("restart", "quiet90", "quiet45"))

    def test_worst_rows(self):
        runs = ([_run("a0.3", s, 100.0, max_m=m) for s, m in ((1, 10.0), (2, 30.0), (3, 50.0))]
                + [_run("a0.3", 4, 100.0, ok=False, max_m=99.0)]
                + [_run("restart", 1, 100.0, restarts=2, max_m=None)])
        rows = pss.worst_rows(runs)
        self.assertEqual(rows, [
            {"profile": "outage90", "variant": "a0.3", "cruise": 0.8, "course": "blocks",
             "missions": 3, "median_max_m": 30.0, "largest_m": 50.0, "over_snap": 2},
            {"profile": "outage90", "variant": "restart", "cruise": 0.8, "course": "blocks",
             "missions": 0, "median_max_m": None, "largest_m": None, "over_snap": 0}])

    def test_main_small(self):
        with tiny_courses():
            with tempfile.TemporaryDirectory() as d, redirect_stdout(io.StringIO()):
                pss.main(["--out-dir", d, "--first-seed", "325", "--seeds", "2",
                          "--profiles", "quiet90,quiet45", "--variants", "restart"])
                with open(os.path.join(d, "summary.json")) as f:
                    out = json.load(f)
                with open(os.path.join(d, "report.md")) as f:
                    md = f.read()
                with open(os.path.join(d, "runs.jsonl")) as f:
                    lines = [json.loads(x) for x in f if x.strip()]
        # outage90 and a0.3 are always flown: 3 profiles x 2 variants x 2 seeds.
        self.assertEqual(out["runs"], 12)
        self.assertEqual(out["seeds"], [325, 326])
        self.assertEqual(sorted({r["profile"] for r in lines}), ["outage90", "quiet45", "quiet90"])
        self.assertEqual(sorted({r["variant"] for r in lines}), ["a0.3", "restart"])
        self.assertTrue(all("gps" in r and "aim" in r and "context" in r and "corner" in r
                            and "position_err" in r for r in lines))
        self.assertTrue(all(r["gps"]["filters"] == 1 for r in lines))
        self.assertTrue(all(isinstance(r["gps"]["restarts"], int)
                            for r in lines if r["variant"] == "restart"))
        self.assertTrue(all(r["gps"]["restarts"] is None for r in lines if r["variant"] == "a0.3"))
        self.assertTrue(out["done"])
        self.assertEqual(sorted((v["profile"], v["variant"], v["against"])
                                for v in out["verdicts"]),
                         [("outage90", "restart", "a0.3"), ("quiet45", "restart", "a0.3"),
                          ("quiet90", "restart", "a0.3")])
        self.assertEqual(sorted((v["variant"], v["profile"], v["against"])
                                for v in out["profile_verdicts"]),
                         [("a0.3", "quiet90", "outage90"), ("a0.3", "quiet90", "quiet45"),
                          ("restart", "quiet90", "outage90"), ("restart", "quiet90", "quiet45")])
        self.assertEqual(out["flown_as"], "keep16")
        self.assertEqual(out["snap_m"], 20.0)
        self.assertIsNone(out["check"])
        self.assertEqual(len(out["worst"]), 6)
        self.assertEqual(len(out["position"]), 6)
        self.assertIn("## The pilot's worst idea of where it is, per mission", md)
        self.assertIn("Seeds 325-326.", md)
        self.assertIs(rp.GpsFilter, GPS_FILTER)
        self.assertIs(rp.PathFollower, FOLLOWER)
        self.assertEqual(set(pl.PROFILES), KNOWN)


if __name__ == "__main__":
    unittest.main()
