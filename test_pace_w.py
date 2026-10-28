"""Tests for the study of starting the GPS average again after a gap, with the
stuck check's warm-up.

Run: python -m unittest test_pace_w -v
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
import pace_l as pl  # noqa: E402
import pace_o as po  # noqa: E402
import pace_p as pp  # noqa: E402
import pace_q as pq  # noqa: E402
import pace_s as pz  # noqa: E402
import pace_study as ps  # noqa: E402
import pace_u as pu  # noqa: E402
import pace_v as pv  # noqa: E402
import pace_w as pw  # noqa: E402
import rover_pilot as rp  # noqa: E402

TINY = {"points": [(0.0, 0.0), (30.0, 0.0)], "checkpoints": [1]}
# One right-angle path corner at (60, 0); the only checkpoint is the end.
CORNER60 = {"points": [(0.0, 0.0), (60.0, 0.0), (60.0, 60.0)], "checkpoints": [2]}
# What the patches replace, kept in a tuple so they come back unbound.
SAVED = (rp.GpsFilter, rp.Pilot._stuck, rp.SimRover._step)
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


def assert_restored(case):
    case.assertIs(rp.GpsFilter, SAVED[0])
    case.assertIs(rp.Pilot._stuck, SAVED[1])
    case.assertIs(rp.SimRover._step, SAVED[2])
    case.assertEqual(set(pl.PROFILES), KNOWN)
    case.assertEqual((pv.BASE_VARIANT, pv.NOISE_VARIANT), ("a0.3", "a0.3:B"))


class SetupTests(unittest.TestCase):
    def test_profiles(self):
        self.assertIs(pw.PROFILES, pv.PROFILES)
        self.assertEqual(pw.BASE_PROFILE, "outage90")
        self.assertEqual(pw.BLOCKED, ("blockedstart", "blockedmid"))
        self.assertEqual(pw.LONG_OUTAGE, ("outage90", "quiet90", "quietdrift90", "blockedstart",
                                          "blockedmid"))
        self.assertEqual(set(pw.LONG_OUTAGE) | {"quiet45"}, set(pw.PROFILES))

    def test_variants(self):
        self.assertEqual(list(pw.VARIANTS), ["warm10", "restart+warm10", "warm10:B"])
        self.assertEqual(pw.VARIANTS["warm10"], pv.VARIANTS["warm10"])
        self.assertEqual(pw.VARIANTS["warm10:B"], pv.VARIANTS["warm10"])
        self.assertEqual(pw.VARIANTS["restart+warm10"],
                         dict(pu.VARIANTS["restart+warm10"], warm="always"))
        self.assertEqual(pw.RESTART, pz.VARIANTS["restart"])
        self.assertEqual(pw.BASE_VARIANT, "warm10")
        self.assertEqual(pw.NOISE_VARIANT, "warm10:B")
        self.assertEqual(pw.PAIRS, (("warm10", "restart+warm10"),))
        self.assertEqual(pw.WARMUP_S, rp.STUCK_WARMUP_S)

    def test_seeds_are_fresh(self):
        self.assertEqual(pw.FIRST_SEED, pv.FIRST_SEED_B + 24)
        self.assertEqual(pw.FIRST_SEED_B, pw.FIRST_SEED + 24)

    def test_checked(self):
        self.assertEqual(len(pw.CHECKED_V), 4)
        self.assertEqual(len(pw.CHECKED_S), 3)
        for profile, course, seed in pw.CHECKED_V:
            self.assertIn(profile, pw.PROFILES)
            self.assertIn(course, ps.COURSES)
            self.assertTrue(pv.FIRST_SEED <= seed < pv.FIRST_SEED_B)
        for profile, course, seed in pw.CHECKED_S:
            self.assertIs(pw.PROFILES[profile], pz.PROFILES[profile])
            self.assertIn(course, ps.COURSES)
        # pace-v's record of seed 397 on blockedstart: blocked from 0 to 57.1 s.
        self.assertEqual(pv.block_window("blockedstart", 397), [0.0, 57.1])


class FlyTests(unittest.TestCase):
    def test_warm10_flies_as_pace_v(self):
        for profile in ("quiet90", "blockedstart"):
            with self.subTest(profile=profile):
                got = pw.fly("corner", 1, profile, "warm10", 0.8, course=CORNER60)
                want = pv.fly("corner", 1, profile, "warm10", 0.8, course=CORNER60)
                self.assertEqual(got, want)
        assert_restored(self)

    def test_restart_flies_as_pace_u(self):
        got = pw.fly("corner", 2, "outage90", "restart+warm10", 0.8, course=CORNER60)
        want = pu.fly("corner", 2, "outage90", "restart+warm10", 0.8, course=CORNER60)
        stuck = got.pop("stuck")
        want_stuck = want.pop("stuck")
        self.assertEqual(got, want)
        self.assertEqual(stuck["recovery_t"], want_stuck["recovery_t"])
        self.assertEqual(stuck["warmup_s"], 10.0)
        self.assertEqual(stuck["warm"], "always")
        self.assertIsInstance(got["gps"]["restarts"], int)
        assert_restored(self)

    def test_settings_replace_the_variant(self):
        got = pw.fly("corner", 3, "quiet90", None, 0.8, course=CORNER60, settings=pw.RESTART)
        self.assertEqual(got["stuck"]["warmup_s"], 0.0)
        self.assertEqual(got["stuck"]["warm"], "never")
        self.assertIsInstance(got["gps"]["restarts"], int)
        plain = pw.fly("corner", 3, "quiet90", "warm10", 0.8, course=CORNER60)
        self.assertIsNone(plain["gps"]["restarts"])
        assert_restored(self)

    def test_restored_after_a_failure(self):
        with self.assertRaises(Exception):
            pw.fly("no-such-course", 1, "blockedmid", "restart+warm10", 0.8)
        assert_restored(self)

    def test_failed_run_fields(self):
        r = pw.failed_run(ValueError("boom"))
        self.assertFalse(r["ok"])
        self.assertEqual(r["gps"], pq.NO_GPS)
        self.assertEqual(r["stuck"], pv.NO_STUCK)


class CheckTests(unittest.TestCase):
    def test_check(self):
        with tiny_courses():
            a = pv.fly("tiny", 5, "blockedstart", "warm10", 0.8)
            b = pz.fly("tiny", 6, "outage90", "restart", 0.8)
            expected_v = {("blockedstart", "tiny", 5): (a["elapsed_s"], a["stuck"]["recovery_t"])}
            expected_s = {("outage90", "tiny", 6): (b["elapsed_s"], b["recoveries"] + 1,
                                                    b["gps"]["restarts"])}
            out = pw.check(expected_v, expected_s)
        self.assertEqual((out["compared"], out["identical"]), (2, 1))
        self.assertEqual(len(out["different"]), 1)
        self.assertEqual(out["different"][0]["reference"], "pace_s.py")
        self.assertEqual(out["different"][0]["got"]["recoveries"], b["recoveries"])
        assert_restored(self)


def _run(variant, seed, elapsed, profile="quiet90", ok=True, course="blocks"):
    return {"profile": profile, "variant": variant, "cruise": 0.8, "course": course,
            "seed": seed, "ok": ok, "elapsed_s": elapsed, "time_s": {"stopped": 10.0},
            "reports": 5, "reached": 5, "recoveries": 0,
            "offset": {"n": 5, "median_m": 1.0, "p95_m": 3.0, "max_m": 5.0},
            "position_err": {"n": 5, "median_m": 2.0, "p95_m": 4.0, "max_m": 10.0},
            "corner": {"n": 0, "median_m": None, "p95_m": None, "max_m": None, "corners": 0,
                       "median_past_m": None, "max_past_m": None},
            "context": {c: EMPTY for c in po.CONTEXTS},
            "planner": {"plans": 5, "behind": 0},
            "aim": dict(pp.NO_AIM), "gps": {"filters": 1, "restarts": None},
            "stuck": {"warmup_s": 10.0, "warm": "always", "recovery_t": [], "stands": [],
                      "block": None, "block_outage": None, "first_outage_s": 600.0}}


class SummaryTests(unittest.TestCase):
    def test_tolerances(self):
        corner = [{"profile": "quiet90", "variant": "warm10", "course": "blocks", "p95_m": 3.0},
                  {"profile": "quiet90", "variant": "warm10:B", "course": "blocks",
                   "p95_m": 3.5},
                  # Only warm10 and warm10:B count.
                  {"profile": "quiet90", "variant": "a0.3", "course": "blocks", "p95_m": 9.0},
                  {"profile": "quiet90", "variant": "restart+warm10", "course": "blocks",
                   "p95_m": 1.0}]
        offsets = [{"profile": "outage90", "variant": "warm10", "course": "bayside",
                    "p95_offset_m": 2.0},
                   {"profile": "outage90", "variant": "warm10:B", "course": "bayside",
                    "p95_offset_m": 2.25},
                   {"profile": "outage90", "variant": "restart+warm10", "course": "bayside",
                    "p95_offset_m": 7.0}]
        self.assertEqual(pw.tolerances(corner, offsets),
                         {"corner_spread_m": 0.5, "corner_tol_m": 0.5,
                          "offset_spread_m": 0.25, "offset_tol_m": 0.5})
        assert_restored(self)

    def test_pair_effects(self):
        runs = ([_run("warm10", s, 100.0) for s in range(1, 7)]
                + [_run("restart+warm10", s, 90.0) for s in range(1, 7)]
                + [_run("warm10:B", s, 50.0) for s in range(21, 27)])
        effects, tallies = pw.pair_effects(runs)
        self.assertIsNot(pi.PAIRS, pw.PAIRS)
        self.assertEqual(len(effects), 1)
        self.assertEqual([(t["variant"], t["against"]) for t in tallies],
                         [("restart+warm10", "warm10")])
        self.assertEqual(tallies[0]["groups_faster"], 1)
        self.assertEqual(tallies[0]["groups_slower"], 0)

    def test_profile_effects(self):
        runs = ([_run("restart+warm10", s, 100.0) for s in range(1, 7)]
                + [_run("restart+warm10", s, 110.0, profile="blockedmid") for s in range(1, 7)])
        effects, tallies = pw.profile_effects(runs)
        self.assertNotIn("restart+warm10", pj.VARIANTS)
        self.assertEqual(len(tallies), 1)
        self.assertEqual(tallies[0]["groups_slower"], 1)
        self.assertEqual((tallies[0]["variant"], tallies[0]["profile"], tallies[0]["against"]),
                         ("restart+warm10", "blockedmid", "quiet90"))

    def test_main_small(self):
        with tiny_courses():
            with tempfile.TemporaryDirectory() as d, redirect_stdout(io.StringIO()):
                pw.main(["--out-dir", d, "--seeds", "1", "--profiles", "quiet90",
                         "--variants", "restart+warm10"])
                with open(os.path.join(d, "summary.json")) as f:
                    out = json.load(f)
                with open(os.path.join(d, "report.md")) as f:
                    md = f.read()
                with open(os.path.join(d, "runs.jsonl")) as f:
                    lines = [json.loads(x) for x in f if x.strip()]
        # outage90 and warm10 are always flown: 2 profiles x 2 variants x 1 seed.
        self.assertEqual(out["runs"], 4)
        self.assertEqual(out["seeds"], [445])
        self.assertEqual(out["seeds_b"], [])
        self.assertEqual(sorted({r["profile"] for r in lines}), ["outage90", "quiet90"])
        self.assertEqual(sorted({r["variant"] for r in lines}), ["restart+warm10", "warm10"])
        self.assertTrue(all((r["gps"]["restarts"] is None) == (r["variant"] == "warm10")
                            for r in lines if r["ok"]))
        self.assertTrue(out["done"])
        self.assertEqual(sorted((v["profile"], v["variant"], v["against"])
                                for v in out["verdicts"]),
                         [("outage90", "restart+warm10", "warm10"),
                          ("quiet90", "restart+warm10", "warm10")])
        self.assertEqual(sorted(out["tolerance"]),
                         ["corner_spread_m", "corner_tol_m", "offset_spread_m", "offset_tol_m"])
        self.assertEqual({x["variant"] for x in out["worst"]}, {"warm10", "restart+warm10"})
        self.assertIsNone(out["check"])
        self.assertEqual(out["rover_pilot"], rp.__version__)
        self.assertIn("thrown off", md)
        self.assertIn("Seeds 445-445;", md)
        assert_restored(self)


if __name__ == "__main__":
    unittest.main()
