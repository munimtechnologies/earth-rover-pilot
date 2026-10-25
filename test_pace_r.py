"""Tests for the study of a truer GPS position at a matched real aim.

Run: python -m unittest test_pace_r -v
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
import pace_r as pr  # noqa: E402
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


class SetupTests(unittest.TestCase):
    def test_profiles(self):
        self.assertIs(pr.PROFILES, pq.PROFILES)
        self.assertEqual(list(pr.PROFILES), ["outage90", "quiet90", "quietdrift90"])
        self.assertEqual(pr.BASE_PROFILE, "outage90")
        self.assertEqual(pr.PROFILE_PAIRS, (("outage90", "quiet90"), ("quiet90", "quietdrift90")))

    def test_variants(self):
        self.assertEqual(pr.VARIANTS, {
            "a0.3-16": {"filter": "a0.3", "lookahead_m": 16.0},
            "track-12": {"filter": "track", "lookahead_m": 12.0},
            "a0.3-20": {"filter": "a0.3", "lookahead_m": 20.0},
            "track-16": {"filter": "track", "lookahead_m": 16.0}})
        self.assertEqual(pr.BASE_VARIANT, "a0.3-16")
        for v in pr.VARIANTS.values():
            self.assertIn(v["filter"], pq.VARIANTS)
        # The shipped pilot: the filter as it ships and the real-rover lookahead.
        self.assertEqual(pq.VARIANTS["a0.3"], {"alpha": rp.GpsFilter().alpha})
        self.assertEqual(pr.VARIANTS["a0.3-16"]["lookahead_m"], rp.PATH_LOOKAHEAD_M)
        self.assertEqual(pr.PAIRS, (("a0.3-16", "track-12"), ("a0.3-16", "a0.3-20"),
                                    ("a0.3-16", "track-16"), ("a0.3-20", "track-16"),
                                    ("track-12", "track-16")))
        self.assertEqual(pr.CRUISES, (0.8,))
        self.assertEqual(pr.FIRST_SEED, 301)
        self.assertEqual(pr.CHECKED_P, {"profiles": ("outage90", "drift90"),
                                        "variants": (("a0.3-16", "keep16"),),
                                        "seeds": (253, 254, 255)})
        self.assertEqual(pr.CHECKED_Q, {"profiles": ("quiet90",),
                                        "variants": (("a0.3-16", "a0.3"), ("track-16", "track")),
                                        "seeds": (277, 278, 279)})

    def test_lookaheads_are_whole_steps(self):
        # PathFollower rounds lookahead / 2 m half to even: 13 m would be 12 m.
        self.assertEqual(round(13.0 / 2.0), 6)
        for v in pr.VARIANTS.values():
            self.assertEqual(v["lookahead_m"] % 2.0, 0.0)


class AimingTests(unittest.TestCase):
    def test_the_outer_lookahead_wins(self):
        seen = []

        def fake(points, **kw):
            seen.append(kw["lookahead_m"])

        rp.PathFollower = fake
        try:
            # As in pr.fly: the variant's outside, pace_o.fly's 16 m inside.
            with po._aiming(12.0), po._aiming(16.0):
                rp.PathFollower(None, lookahead_m=8.0)
            rp.PathFollower(None, lookahead_m=8.0)
        finally:
            rp.PathFollower = FOLLOWER
        self.assertEqual(seen, [12.0, 8.0])


class FlyTests(unittest.TestCase):
    def assert_restored(self):
        self.assertIs(rp.GpsFilter, GPS_FILTER)
        self.assertIs(rp.PathFollower, FOLLOWER)
        self.assertIs(pl.SlipRover, SLIP_ROVER)
        self.assertIs(pe.CountingEstimator, COUNTING)
        self.assertIs(ps.CoursePlanner, PLANNER)
        self.assertEqual(set(pl.PROFILES), KNOWN)

    def test_16_m_flies_as_pace_q(self):
        for variant, filt, profile in (("a0.3-16", "a0.3", "outage90"),
                                       ("a0.3-16", "a0.3", "quiet90"),
                                       ("track-16", "track", "quiet90")):
            with self.subTest(variant=variant, profile=profile):
                got = pr.fly("corner", 1, profile, variant, 0.8, course=CORNER60)
                want = pq.fly("corner", 1, profile, filt, 0.8, course=CORNER60)
                self.assertEqual(got, want)
        self.assert_restored()

    def test_a03_16_flies_as_pace_p_keep16(self):
        got = pr.fly("corner", 2, "drift90", "a0.3-16", 0.8, course=CORNER60)
        gps = got.pop("gps")
        want = pp.fly("corner", 2, "drift90", "keep16", 0.8, course=CORNER60)
        self.assertEqual(got, want)
        self.assertEqual(gps, {"filters": 1, "restarts": None})
        self.assert_restored()

    def test_the_lookahead_changes_the_mission(self):
        for filt in ("track", "a0.3"):
            with self.subTest(filter=filt):
                short, long_ = (("track-12", "track-16") if filt == "track"
                                else ("a0.3-16", "a0.3-20"))
                a = pr.fly("corner", 3, "quiet90", short, 0.8, course=CORNER60)
                b = pr.fly("corner", 3, "quiet90", long_, 0.8, course=CORNER60)
                self.assertNotEqual(a, b)
                self.assertEqual(a["gps"]["filters"], 1)
                if filt == "track":
                    self.assertIsInstance(a["gps"]["restarts"], int)
                for key in ("aim", "corner", "context", "planner", "fit_err", "position_err"):
                    self.assertIn(key, a)
        self.assert_restored()

    def test_restored_after_a_failure(self):
        with self.assertRaises(KeyError):
            pr.fly("corner", 1, "no-such-profile", "track-12", 0.8, course=CORNER60)
        self.assert_restored()

    def test_failed_run_fields(self):
        r = pr.failed_run(ValueError("boom"))
        self.assertFalse(r["ok"])
        self.assertEqual(r["gps"], pq.NO_GPS)
        self.assertEqual(r["aim"], pp.NO_AIM)


class CheckTests(unittest.TestCase):
    def test_check_against_pace_q(self):
        with tiny_courses():
            ref = []
            for seed in (277, 278):
                r = pq.fly("tiny", seed, "quiet90", "track", 0.8)
                r.update(profile="quiet90", variant="track", cruise=0.8, course="tiny", seed=seed)
                ref.append(r)
            ref[1]["elapsed_s"] += 1.0
            with tempfile.TemporaryDirectory() as d:
                path = os.path.join(d, "runs.jsonl")
                with open(path, "w", encoding="utf-8") as f:
                    for r in ref:
                        f.write(json.dumps(r) + "\n")
                    f.write("\n")
                out = pr.check(path, pr.CHECKED_Q)
        # 1 profile x 2 variants x 1 course x 3 seeds = 6 missions checked; the
        # reference has 2 of them (track), and seed 278 was altered.
        self.assertEqual((out["compared"], out["identical"], out["missing"]), (2, 1, 4))
        self.assertEqual(len(out["different"]), 1)
        self.assertEqual(out["different"][0]["seed"], 278)
        self.assertEqual(out["different"][0]["variant"], "track-16")
        self.assertEqual(out["different"][0]["against"], "track")
        self.assertEqual(out["different"][0]["fields"], ["elapsed_s"])
        self.assertIs(rp.GpsFilter, GPS_FILTER)
        self.assertIs(rp.PathFollower, FOLLOWER)

    def test_check_against_pace_p(self):
        with tiny_courses():
            r = pp.fly("tiny", 253, "outage90", "keep16", 0.8)
            r.update(profile="outage90", variant="keep16", cruise=0.8, course="tiny", seed=253)
            with tempfile.TemporaryDirectory() as d:
                path = os.path.join(d, "runs.jsonl")
                with open(path, "w", encoding="utf-8") as f:
                    f.write(json.dumps(r) + "\n")
                out = pr.check(path, pr.CHECKED_P)
        # 2 profiles x 1 course x 3 seeds = 6; the reference has 1.
        self.assertEqual((out["compared"], out["identical"], out["missing"]), (1, 1, 5))


def _run(variant, seed, elapsed, profile="outage90", ok=True, restarts=None):
    return {"profile": profile, "variant": variant, "cruise": 0.8, "course": "blocks",
            "seed": seed, "ok": ok, "elapsed_s": elapsed, "time_s": {"stopped": 10.0},
            "reports": 5, "reached": 5, "recoveries": 0,
            "offset": {"n": 5, "median_m": 1.0, "p95_m": 3.0, "max_m": 5.0},
            "corner": {"n": 0, "median_m": None, "p95_m": None, "max_m": None, "corners": 0,
                       "median_past_m": None, "max_past_m": None},
            "context": {c: EMPTY for c in po.CONTEXTS},
            "planner": {"plans": 5, "behind": 0},
            "aim": dict(pp.NO_AIM), "gps": {"filters": 1, "restarts": restarts}}


class SummaryTests(unittest.TestCase):
    def test_pair_effects(self):
        runs = ([_run("a0.3-16", s, 100.0) for s in range(1, 7)]
                + [_run("track-12", s, 90.0, restarts=1) for s in range(1, 7)])
        effects, tallies = pr.pair_effects(runs)
        self.assertIsNot(pi.PAIRS, pr.PAIRS)
        # Only the pair with both variants flown.
        self.assertEqual(len(effects), 1)
        self.assertEqual((effects[0]["faster"], effects[0]["slower"]), (6, 0))
        self.assertEqual(tallies, [{"profile": "outage90", "variant": "track-12",
                                    "against": "a0.3-16", "groups": 1, "groups_faster": 1,
                                    "groups_slower": 0, "groups_lost": 0, "groups_gained": 0,
                                    "largest_median_diff_share": -0.1}])

    def test_a_pair_not_against_the_shipped_pilot(self):
        runs = ([_run("a0.3-20", s, 100.0) for s in range(1, 7)]
                + [_run("track-16", s, 110.0, restarts=1) for s in range(1, 7)])
        effects, tallies = pr.pair_effects(runs)
        self.assertEqual([(t["variant"], t["against"], t["groups_slower"]) for t in tallies],
                         [("track-16", "a0.3-20", 1)])

    def test_profile_effects(self):
        runs = ([_run("track-12", s, 100.0) for s in range(1, 7)]
                + [_run("track-12", s, 110.0, profile="quiet90") for s in range(1, 7)])
        effects, tallies = pr.profile_effects(runs)
        self.assertNotIn("track-12", pj.VARIANTS)
        self.assertEqual(len(effects), 1)
        self.assertEqual(len(tallies), 1)
        self.assertEqual(tallies[0]["groups_slower"], 1)
        self.assertEqual((tallies[0]["variant"], tallies[0]["profile"], tallies[0]["against"]),
                         ("track-12", "quiet90", "outage90"))

    def test_main_small(self):
        with tiny_courses():
            with tempfile.TemporaryDirectory() as d, redirect_stdout(io.StringIO()):
                pr.main(["--out-dir", d, "--first-seed", "301", "--seeds", "2",
                         "--profiles", "quiet90", "--variants", "track-12"])
                with open(os.path.join(d, "summary.json")) as f:
                    out = json.load(f)
                with open(os.path.join(d, "report.md")) as f:
                    md = f.read()
                with open(os.path.join(d, "runs.jsonl")) as f:
                    lines = [json.loads(x) for x in f if x.strip()]
        # outage90 and a0.3-16 are always flown: 2 profiles x 2 variants x 2 seeds.
        self.assertEqual(out["runs"], 8)
        self.assertEqual(out["seeds"], [301, 302])
        self.assertEqual(sorted({r["profile"] for r in lines}), ["outage90", "quiet90"])
        self.assertEqual(sorted({r["variant"] for r in lines}), ["a0.3-16", "track-12"])
        self.assertTrue(all("gps" in r and "aim" in r and "context" in r and "corner" in r
                            and "position_err" in r for r in lines))
        self.assertTrue(all(r["gps"]["filters"] == 1 for r in lines))
        self.assertTrue(out["done"])
        self.assertEqual(sorted((v["profile"], v["variant"], v["against"])
                                for v in out["verdicts"]),
                         [("outage90", "track-12", "a0.3-16"), ("quiet90", "track-12", "a0.3-16")])
        self.assertEqual(sorted((v["variant"], v["profile"], v["against"])
                                for v in out["profile_verdicts"]),
                         [("a0.3-16", "quiet90", "outage90"), ("track-12", "quiet90", "outage90")])
        self.assertEqual(out["flown_as"], "keep16")
        self.assertEqual(out["filters"], {"a0.3": {"alpha": 0.3},
                                          "track": {"alpha": 0.3, "beta": 0.053, "track": True}})
        self.assertIsNone(out["check"])
        self.assertIsNone(out["check_q"])
        self.assertEqual(len(out["position"]), 4)
        self.assertIn("## Where the pilot thinks it is, against where it is", md)
        self.assertIn("Seeds 301-302.", md)
        self.assertIs(rp.GpsFilter, GPS_FILTER)
        self.assertIs(rp.PathFollower, FOLLOWER)
        self.assertEqual(set(pl.PROFILES), KNOWN)


if __name__ == "__main__":
    unittest.main()
