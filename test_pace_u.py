"""Tests for the second study of a warm-up before the stuck detector judges.

Run: python -m unittest test_pace_u -v
"""

import collections
import io
import json
import os
import sys
import tempfile
import types
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
import pace_t as pt  # noqa: E402
import pace_u as pu  # noqa: E402
import rover_pilot as rp  # noqa: E402

TINY = {"points": [(0.0, 0.0), (30.0, 0.0)], "checkpoints": [1]}
# One right-angle path corner at (60, 0); the only checkpoint is the end.
CORNER60 = {"points": [(0.0, 0.0), (60.0, 0.0), (60.0, 60.0)], "checkpoints": [2]}
GPS_FILTER = rp.GpsFilter
STUCK = rp.Pilot._stuck
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


def fake_pilot():
    """Just what Pilot._stuck reads: a 10 s window, 1.5 m, cruise 0.8."""
    return types.SimpleNamespace(
        _history=collections.deque(), stuck_window_s=10.0, stuck_min_move_m=1.5,
        steering=types.SimpleNamespace(cruise=0.8),
        gps=types.SimpleNamespace(lat=37.0, lon=-122.0))


def first_verdict(warmup_s, until=40.0):
    """When a rover that never moves is first called stuck, asked every 0.5 s
    from 0.25 s while the pilot asks for 0.8 forward, with this warm-up."""
    p = fake_pilot()
    times = []
    with pt._warming(warmup_s, times):
        t = 0.25
        while t < until:
            if rp.Pilot._stuck(p, t, 0.8):
                return t
            t += 0.5
    return None


class SetupTests(unittest.TestCase):
    def test_profiles(self):
        self.assertIs(pu.PROFILES, pt.PROFILES)
        self.assertEqual(list(pu.PROFILES),
                         ["outage90", "quiet90", "quietdrift90", "quiet45", "blocked30"])
        self.assertEqual(pu.BASE_PROFILE, "outage90")
        self.assertEqual(pu.BLOCKED, ("blocked30",))
        self.assertEqual(pu.BLOCK_S, pu.PROFILES["blocked30"]["blocked_until_s"])
        self.assertEqual(pu.BLOCK_S, 30.0)

    def test_variants(self):
        self.assertEqual(list(pu.VARIANTS),
                         ["a0.3", "warm5", "warm10", "restart+warm5", "restart+warm10"])
        for ours, theirs in pu.AS_PACE_T.items():
            self.assertEqual(pu.VARIANTS[ours], pt.VARIANTS[theirs])
        self.assertEqual(pu.VARIANTS["warm5"], {"alpha": 0.3, "warmup_s": 5.0})
        self.assertEqual(pu.VARIANTS["restart+warm5"],
                         {"alpha": 0.3, "beta": 0.0, "track": True, "warmup_s": 5.0})
        self.assertEqual(pu.BASE_VARIANT, "a0.3")
        self.assertEqual(pu.PAIRS, (("a0.3", "warm5"), ("a0.3", "warm10"), ("warm10", "warm5"),
                                    ("warm5", "restart+warm5"), ("warm10", "restart+warm10")))
        self.assertEqual(pu.CRUISES, (0.8,))
        self.assertEqual(pu.FIRST_SEED, 373)
        self.assertEqual(pu.FIRST_SEED, pt.FIRST_SEED + 24)
        self.assertIs(pu.CHECKED, pt.CHECKED)
        self.assertEqual(pu.EARLY_S, 30.0)
        self.assertEqual(pu.SNAP_M, 20.0)

    def test_checked_t(self):
        self.assertEqual(len(pu.CHECKED_T), 11)
        for (profile, theirs, ours, course, seed), (elapsed, rec) in pu.CHECKED_T.items():
            with self.subTest(profile=profile, variant=ours, course=course, seed=seed):
                self.assertIn(profile, pu.PROFILES)
                self.assertEqual(pu.AS_PACE_T[ours], theirs)
                self.assertIn(course, ps.COURSES)
                self.assertGreaterEqual(seed, pt.FIRST_SEED)
                self.assertLess(seed, pt.FIRST_SEED + 24)
                self.assertGreater(elapsed, 1000.0)
                self.assertIsInstance(rec, list)


class OutageTests(unittest.TestCase):
    def test_first_outage_is_the_rovers_own(self):
        for profile in ("outage90", "quiet45", "blocked30"):
            p = pu.PROFILES[profile]
            for seed in (352, 368, 373, 396):
                with self.subTest(profile=profile, seed=seed):
                    windows = pi.outage_windows(seed, p["outage_s"], p["clear_s"])
                    self.assertEqual(pu.first_outage_s(profile, seed),
                                     round(windows[0][0], 1))

    def test_same_windows_on_the_90_s_profiles(self):
        for seed in (352, 368, 380):
            with self.subTest(seed=seed):
                firsts = {pu.first_outage_s(p, seed)
                          for p in ("outage90", "quiet90", "quietdrift90", "blocked30")}
                self.assertEqual(len(firsts), 1)

    def test_no_outages(self):
        self.assertIsNone(pu._first_outage({}, 5))
        self.assertIsNone(pu._first_outage({"outage_s": 0.0, "clear_s": 600.0}, 5))

    def test_the_flown_rover_draws_the_same_windows(self):
        saved = pi.OutageRover.__init__
        seen = []

        def init(self, *args, **kw):
            saved(self, *args, **kw)
            seen.append(self.outages[0][0] if self.outages else None)

        pi.OutageRover.__init__ = init
        try:
            r = pu.fly("corner", 7, "blocked30", "warm5", 0.8, course=CORNER60)
        finally:
            pi.OutageRover.__init__ = saved
        self.assertTrue(seen)
        self.assertTrue(all(x == seen[0] for x in seen))
        self.assertEqual(round(seen[0], 1), r["stuck"]["first_outage_s"])


class WarmingTests(unittest.TestCase):
    def test_catch_times(self):
        # A rover that never moves: 9 s of window after the warm-up.
        self.assertEqual(first_verdict(0.0), 9.25)
        self.assertEqual(first_verdict(5.0), 14.25)
        self.assertEqual(first_verdict(10.0), 19.25)
        self.assertIs(rp.Pilot._stuck, STUCK)


class FlyTests(unittest.TestCase):
    def assert_restored(self):
        self.assertIs(rp.GpsFilter, GPS_FILTER)
        self.assertIs(rp.Pilot._stuck, STUCK)
        self.assertEqual(set(pl.PROFILES), KNOWN)

    def test_flies_as_pace_t(self):
        for ours, theirs in sorted(pu.AS_PACE_T.items()):
            with self.subTest(variant=ours):
                got = pu.fly("corner", 1, "quiet90", ours, 0.8, course=CORNER60)
                want = pt.fly("corner", 1, "quiet90", theirs, 0.8, course=CORNER60)
                stuck = got.pop("stuck")
                want_stuck = want.pop("stuck")
                self.assertEqual(got, want)
                self.assertEqual(stuck["first_outage_s"], pu.first_outage_s("quiet90", 1))
                del stuck["first_outage_s"]
                self.assertEqual(stuck, want_stuck)
        self.assert_restored()

    def test_warm5_variants(self):
        for variant in ("warm5", "restart+warm5"):
            with self.subTest(variant=variant):
                r = pu.fly("corner", 3, "quiet90", variant, 0.8, course=CORNER60)
                self.assertTrue(r["ok"], r["reason"])
                self.assertEqual(r["stuck"]["warmup_s"], 5.0)
                self.assertEqual(len(r["stuck"]["recovery_t"]), r["recoveries"])
                self.assertEqual(r["gps"]["filters"], 1)
                if variant == "warm5":
                    self.assertIsNone(r["gps"]["restarts"])
                else:
                    self.assertIsInstance(r["gps"]["restarts"], int)
        self.assert_restored()

    def test_a_blocked_rover_is_caught(self):
        for variant in ("a0.3", "warm5", "warm10"):
            with self.subTest(variant=variant):
                r = pu.fly("corner", 4, "blocked30", variant, 0.8, course=CORNER60)
                self.assertTrue(r["ok"], r["reason"])
                self.assertGreaterEqual(r["recoveries"], 1)
                self.assertLess(r["stuck"]["recovery_t"][0], 30.0)
        self.assert_restored()

    def test_restored_after_a_failure(self):
        with self.assertRaises(KeyError):
            pu.fly("corner", 1, "no-such-profile", "restart+warm5", 0.8, course=CORNER60)
        self.assert_restored()

    def test_failed_run_fields(self):
        r = pu.failed_run(ValueError("boom"))
        self.assertFalse(r["ok"])
        self.assertEqual(r["gps"], pq.NO_GPS)
        self.assertEqual(r["aim"], pp.NO_AIM)
        self.assertEqual(r["stuck"], pu.NO_STUCK)


class CheckTests(unittest.TestCase):
    def assert_restored(self):
        self.assertIs(rp.GpsFilter, GPS_FILTER)
        self.assertIs(rp.Pilot._stuck, STUCK)
        self.assertEqual(set(pl.PROFILES), KNOWN)

    def test_check_against_pace_s(self):
        with tiny_courses():
            ref = []
            for seed in (325, 326):
                r = pz.fly("tiny", seed, "outage90", "a0.3", 0.8)
                r.update(profile="outage90", variant="a0.3", cruise=0.8, course="tiny",
                         seed=seed)
                ref.append(r)
            ref[1]["elapsed_s"] += 1.0
            with tempfile.TemporaryDirectory() as d:
                path = os.path.join(d, "runs.jsonl")
                with open(path, "w", encoding="utf-8") as f:
                    for r in ref:
                        f.write(json.dumps(r) + "\n")
                out = pu.check(path)
        # 2 profiles x 1 variant x 1 course x 3 seeds = 6 missions checked; the
        # reference has 2 of them, and seed 326 was altered.
        self.assertEqual((out["compared"], out["identical"], out["missing"]), (2, 1, 4))
        self.assertEqual(out["different"][0]["seed"], 326)
        self.assertEqual(out["different"][0]["fields"], ["elapsed_s"])
        self.assert_restored()

    def test_check_against_pace_t(self):
        with tiny_courses():
            a = pt.fly("tiny", 5, "blocked30", "warm", 0.8)
            b = pt.fly("tiny", 6, "quiet90", "a0.3", 0.8)
            expected = {
                ("blocked30", "warm", "warm10", "tiny", 5): (a["elapsed_s"],
                                                             a["stuck"]["recovery_t"]),
                ("quiet90", "a0.3", "a0.3", "tiny", 6): (b["elapsed_s"] + 1.0,
                                                         b["stuck"]["recovery_t"]),
            }
            out = pu.check_t(expected)
        self.assertEqual((out["compared"], out["identical"]), (2, 1))
        self.assertEqual(len(out["different"]), 1)
        self.assertEqual(out["different"][0]["seed"], 6)
        self.assertEqual(out["different"][0]["got"]["elapsed_s"], b["elapsed_s"])
        self.assert_restored()


def _run(variant, seed, elapsed, profile="quiet90", ok=True, recovery_t=(), restarts=None,
         first_outage=600.0):
    return {"profile": profile, "variant": variant, "cruise": 0.8, "course": "blocks",
            "seed": seed, "ok": ok, "elapsed_s": elapsed, "time_s": {"stopped": 10.0},
            "reports": 5, "reached": 5, "recoveries": len(recovery_t),
            "offset": {"n": 5, "median_m": 1.0, "p95_m": 3.0, "max_m": 5.0},
            "position_err": {"n": 5, "median_m": 2.0, "p95_m": 4.0, "max_m": 10.0},
            "corner": {"n": 0, "median_m": None, "p95_m": None, "max_m": None, "corners": 0,
                       "median_past_m": None, "max_past_m": None},
            "context": {c: EMPTY for c in po.CONTEXTS},
            "planner": {"plans": 5, "behind": 0},
            "aim": dict(pp.NO_AIM), "gps": {"filters": 1, "restarts": restarts},
            "stuck": {"warmup_s": 0.0, "recovery_t": list(recovery_t),
                      "first_outage_s": first_outage}}


class SummaryTests(unittest.TestCase):
    def test_stuck_rows(self):
        runs = [_run("a0.3", 1, 100.0, profile="blocked30", recovery_t=(9.1, 24.1)),
                _run("a0.3", 2, 100.0, profile="blocked30", recovery_t=(9.1, 549.9)),
                # The GPS went out while the rover was blocked: not eligible.
                _run("a0.3", 3, 100.0, profile="blocked30", first_outage=5.0),
                # Eligible (the outage began as the block ended), not caught.
                _run("a0.3", 4, 100.0, profile="blocked30", first_outage=30.0,
                     recovery_t=(805.9,)),
                # No outages at all: eligible, not caught.
                _run("a0.3", 5, 100.0, profile="blocked30", first_outage=None),
                _run("a0.3", 6, 100.0, profile="blocked30", ok=False, recovery_t=(1.0,))]
        rows = pu.stuck_rows(runs)
        # 24.1 s is not late; 549.9 and 805.9 are.
        self.assertEqual(rows, [
            {"profile": "blocked30", "variant": "a0.3", "cruise": 0.8, "course": "blocks",
             "missions": 5, "with_recovery": 3, "recoveries": 5, "early": 2, "late": 2,
             "eligible": 4, "early_eligible": 2, "median_first_s": 9.1,
             "latest_first_s": 805.9}])

    def test_stuck_rows_without_recoveries(self):
        rows = pu.stuck_rows([_run("warm5", 1, 100.0), _run("warm5", 2, 100.0, ok=False)])
        self.assertEqual(rows[0]["missions"], 1)
        self.assertEqual(rows[0]["with_recovery"], 0)
        self.assertEqual((rows[0]["early"], rows[0]["late"]), (0, 0))
        self.assertEqual((rows[0]["eligible"], rows[0]["early_eligible"]), (1, 0))
        self.assertIsNone(rows[0]["median_first_s"])
        self.assertIsNone(rows[0]["latest_first_s"])

    def test_pair_effects(self):
        runs = ([_run("a0.3", s, 100.0, recovery_t=(9.1,)) for s in range(1, 7)]
                + [_run(v, s, 90.0) for v in ("warm5", "warm10") for s in range(1, 7)]
                + [_run(v, s, 90.0, restarts=2) for v in ("restart+warm5", "restart+warm10")
                   for s in range(1, 7)])
        effects, tallies = pu.pair_effects(runs)
        self.assertIsNot(pi.PAIRS, pu.PAIRS)
        self.assertEqual(len(effects), 5)
        self.assertEqual([(t["variant"], t["against"]) for t in tallies],
                         [("warm5", "a0.3"), ("warm10", "a0.3"), ("warm5", "warm10"),
                          ("restart+warm5", "warm5"), ("restart+warm10", "warm10")])
        self.assertEqual([t["groups_faster"] for t in tallies], [1, 1, 0, 0, 0])
        self.assertEqual([t["groups_slower"] for t in tallies], [0, 0, 0, 0, 0])

    def test_profile_effects(self):
        runs = ([_run("warm5", s, 100.0) for s in range(1, 7)]
                + [_run("warm5", s, 110.0, profile="blocked30") for s in range(1, 7)])
        effects, tallies = pu.profile_effects(runs)
        self.assertNotIn("warm5", pj.VARIANTS)
        self.assertEqual(len(tallies), 1)
        self.assertEqual(tallies[0]["groups_slower"], 1)
        self.assertEqual((tallies[0]["variant"], tallies[0]["profile"], tallies[0]["against"]),
                         ("warm5", "blocked30", "quiet90"))

    def test_main_small(self):
        with tiny_courses():
            with tempfile.TemporaryDirectory() as d, redirect_stdout(io.StringIO()):
                pu.main(["--out-dir", d, "--first-seed", "373", "--seeds", "2",
                         "--profiles", "quiet90,blocked30", "--variants", "warm5"])
                with open(os.path.join(d, "summary.json")) as f:
                    out = json.load(f)
                with open(os.path.join(d, "report.md")) as f:
                    md = f.read()
                with open(os.path.join(d, "runs.jsonl")) as f:
                    lines = [json.loads(x) for x in f if x.strip()]
        # outage90 and a0.3 are always flown: 3 profiles x 2 variants x 2 seeds.
        self.assertEqual(out["runs"], 12)
        self.assertEqual(out["seeds"], [373, 374])
        self.assertEqual(sorted({r["profile"] for r in lines}),
                         ["blocked30", "outage90", "quiet90"])
        self.assertEqual(sorted({r["variant"] for r in lines}), ["a0.3", "warm5"])
        self.assertTrue(all(r["stuck"]["warmup_s"] == (5.0 if r["variant"] == "warm5" else 0.0)
                            for r in lines))
        self.assertTrue(all(r["stuck"]["first_outage_s"]
                            == pu.first_outage_s(r["profile"], r["seed"]) for r in lines))
        self.assertTrue(all(len(r["stuck"]["recovery_t"]) == r["recoveries"]
                            for r in lines if r["ok"]))
        self.assertTrue(out["done"])
        self.assertEqual(sorted((v["profile"], v["variant"], v["against"])
                                for v in out["verdicts"]),
                         [("blocked30", "warm5", "a0.3"), ("outage90", "warm5", "a0.3"),
                          ("quiet90", "warm5", "a0.3")])
        self.assertEqual(out["block_s"], 30.0)
        self.assertIsNone(out["check"])
        self.assertIsNone(out["check_t"])
        self.assertEqual(len(out["stuck"]), 6)
        self.assertIn("eligible caught early", md)
        self.assertIn("Seeds 373-374.", md)
        self.assertIs(rp.GpsFilter, GPS_FILTER)
        self.assertIs(rp.Pilot._stuck, STUCK)
        self.assertEqual(set(pl.PROFILES), KNOWN)


if __name__ == "__main__":
    unittest.main()
