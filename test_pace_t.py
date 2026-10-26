"""Tests for the study of a warm-up before the stuck detector judges.

Run: python -m unittest test_pace_t -v
"""

import collections
import inspect
import io
import json
import os
import sys
import tempfile
import types
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
import pace_s as pz  # noqa: E402
import pace_study as ps  # noqa: E402
import pace_t as pt  # noqa: E402
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


def verdicts(p, until, clear_at=None, step_lat=0.0, stuck=None):
    """Ask `stuck` (Pilot._stuck as it is now) every 0.5 s from 0.25 s, the
    pilot asking for 0.8 forward; clear the history just before clear_at and
    move the GPS step_lat degrees north each time."""
    stuck = stuck or rp.Pilot._stuck
    out = []
    t = 0.25
    while t < until:
        if clear_at is not None and t == clear_at:
            p._history.clear()
        out.append((t, stuck(p, t, 0.8)))
        p.gps.lat += step_lat
        t += 0.5
    return out


def first_true(out):
    return next((t for t, v in out if v), None)


class SetupTests(unittest.TestCase):
    def test_profiles(self):
        self.assertEqual(list(pt.PROFILES),
                         ["outage90", "quiet90", "quietdrift90", "quiet45", "blocked30"])
        for name in ("outage90", "quiet90", "quietdrift90", "quiet45"):
            self.assertIs(pt.PROFILES[name], pz.PROFILES[name])
        self.assertEqual(pt.PROFILES["blocked30"],
                         dict(pq.PROFILES["quiet90"], blocked_until_s=30.0))
        self.assertNotIn("blocked_until_s", pq.PROFILES["quiet90"])
        self.assertEqual(pt.BASE_PROFILE, "outage90")
        self.assertEqual(pt.BLOCKED, ("blocked30",))
        self.assertEqual(pt.PROFILE_PAIRS, (("quiet90", "blocked30"),))

    def test_variants(self):
        self.assertEqual(pt.WARMUP_S, 10.0)
        self.assertEqual(pt.VARIANTS, {
            "a0.3": {"alpha": 0.3},
            "warm": {"alpha": 0.3, "warmup_s": 10.0},
            "restart+warm": {"alpha": 0.3, "beta": 0.0, "track": True, "warmup_s": 10.0}})
        self.assertEqual(pt.VARIANTS["a0.3"], pz.VARIANTS["a0.3"])
        self.assertEqual(pt.BASE_VARIANT, "a0.3")
        self.assertEqual(pt.PAIRS, (("a0.3", "warm"), ("warm", "restart+warm")))
        self.assertEqual(pt.CRUISES, (0.8,))
        self.assertEqual(pt.FIRST_SEED, 349)
        self.assertEqual(pt.CHECKED, {"profiles": ("outage90", "quiet90"),
                                      "variants": (("a0.3", "a0.3"),),
                                      "seeds": (325, 326, 327)})
        self.assertEqual(pt.SNAP_M, 20.0)
        self.assertEqual(pt.EARLY_S, 30.0)

    def test_the_shipped_stuck_check(self):
        # fake_pilot's settings are the Pilot's own: a 10 s window and 1.5 m.
        params = inspect.signature(rp.Pilot.__init__).parameters
        p = fake_pilot()
        self.assertEqual(params["stuck_window_s"].default, p.stuck_window_s)
        self.assertEqual(params["stuck_min_move_m"].default, p.stuck_min_move_m)
        self.assertEqual((p.stuck_window_s, p.stuck_min_move_m), (10.0, 1.5))


class WarmingTests(unittest.TestCase):
    def test_no_warm_up_is_the_shipped_check(self):
        times = []
        with pt._warming(0.0, times):
            got = verdicts(fake_pilot(), 30.0)
        want = verdicts(fake_pilot(), 30.0, stuck=STUCK)
        self.assertEqual(got, want)
        # A rover that doesn't move is stuck once 9 s of the window are filled.
        t = first_true(got)
        self.assertGreater(t, 9.0)
        self.assertLessEqual(t, 10.0)
        self.assertEqual(times, [x for x, v in got if v])
        self.assertIs(rp.Pilot._stuck, STUCK)

    def test_warm_up_holds_the_verdict(self):
        times = []
        with pt._warming(10.0, times):
            got = verdicts(fake_pilot(), 30.0)
        t = first_true(got)
        # 10 s of warm-up, then 9 s of window.
        self.assertGreater(t, 19.0)
        self.assertLessEqual(t, 20.0)
        self.assertTrue(all(not v for x, v in got if x < 19.0))
        self.assertEqual(times[0], t)
        self.assertIs(rp.Pilot._stuck, STUCK)

    def test_a_clear_starts_the_warm_up_again(self):
        times = []
        with pt._warming(10.0, times):
            got = verdicts(fake_pilot(), 40.0, clear_at=15.25)
        t = first_true(got)
        self.assertGreater(t, 34.0)
        self.assertLessEqual(t, 35.0)
        self.assertIs(rp.Pilot._stuck, STUCK)

    def test_a_moving_rover_is_never_stuck(self):
        # About 1.1 m every 0.5 s.
        for warmup in (0.0, 10.0):
            with self.subTest(warmup=warmup):
                times = []
                with pt._warming(warmup, times):
                    got = verdicts(fake_pilot(), 40.0, step_lat=0.00001)
                self.assertIsNone(first_true(got))
                self.assertEqual(times, [])

    def test_restored_after_a_failure(self):
        with self.assertRaises(ValueError):
            with pt._warming(10.0, []):
                raise ValueError("boom")
        self.assertIs(rp.Pilot._stuck, STUCK)


class FlyTests(unittest.TestCase):
    def assert_restored(self):
        self.assertIs(rp.GpsFilter, GPS_FILTER)
        self.assertIs(rp.Pilot._stuck, STUCK)
        self.assertEqual(set(pl.PROFILES), KNOWN)

    def test_a03_flies_as_pace_s(self):
        for profile in ("outage90", "quiet90"):
            with self.subTest(profile=profile):
                got = pt.fly("corner", 1, profile, "a0.3", 0.8, course=CORNER60)
                stuck = got.pop("stuck")
                want = pz.fly("corner", 1, profile, "a0.3", 0.8, course=CORNER60)
                self.assertEqual(got, want)
                self.assertEqual(stuck["warmup_s"], 0.0)
                self.assertEqual(len(stuck["recovery_t"]), got["recoveries"])
        self.assert_restored()

    def test_warm_variants(self):
        for variant in ("warm", "restart+warm"):
            with self.subTest(variant=variant):
                r = pt.fly("corner", 3, "quiet90", variant, 0.8, course=CORNER60)
                self.assertTrue(r["ok"], r["reason"])
                self.assertEqual(r["stuck"]["warmup_s"], 10.0)
                self.assertEqual(len(r["stuck"]["recovery_t"]), r["recoveries"])
                self.assertEqual(r["gps"]["filters"], 1)
                if variant == "warm":
                    self.assertIsNone(r["gps"]["restarts"])
                else:
                    self.assertIsInstance(r["gps"]["restarts"], int)
                for key in ("aim", "corner", "context", "planner", "position_err"):
                    self.assertIn(key, r)
        self.assert_restored()

    def test_a_blocked_rover_is_still_caught(self):
        for variant in ("a0.3", "warm"):
            with self.subTest(variant=variant):
                r = pt.fly("corner", 4, "blocked30", variant, 0.8, course=CORNER60)
                self.assertTrue(r["ok"], r["reason"])
                self.assertGreaterEqual(r["recoveries"], 1)
                self.assertLess(r["stuck"]["recovery_t"][0], 30.0)
        self.assert_restored()

    def test_restored_after_a_failure(self):
        with self.assertRaises(KeyError):
            pt.fly("corner", 1, "no-such-profile", "restart+warm", 0.8, course=CORNER60)
        self.assert_restored()

    def test_failed_run_fields(self):
        r = pt.failed_run(ValueError("boom"))
        self.assertFalse(r["ok"])
        self.assertEqual(r["gps"], pq.NO_GPS)
        self.assertEqual(r["aim"], pp.NO_AIM)
        self.assertEqual(r["stuck"], pt.NO_STUCK)


class CheckTests(unittest.TestCase):
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
                    f.write("\n")
                out = pt.check(path)
        # 2 profiles x 1 variant x 1 course x 3 seeds = 6 missions checked; the
        # reference has 2 of them, and seed 326 was altered.
        self.assertEqual((out["compared"], out["identical"], out["missing"]), (2, 1, 4))
        self.assertEqual(len(out["different"]), 1)
        self.assertEqual(out["different"][0]["seed"], 326)
        self.assertEqual(out["different"][0]["fields"], ["elapsed_s"])
        self.assertIs(rp.GpsFilter, GPS_FILTER)
        self.assertIs(rp.Pilot._stuck, STUCK)
        self.assertEqual(set(pl.PROFILES), KNOWN)


def _run(variant, seed, elapsed, profile="quiet90", ok=True, recovery_t=(), restarts=None):
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
            "stuck": {"warmup_s": 0.0, "recovery_t": list(recovery_t)}}


class SummaryTests(unittest.TestCase):
    def test_stuck_rows(self):
        runs = ([_run("a0.3", 1, 100.0, recovery_t=(9.6,)),
                 _run("a0.3", 2, 100.0, recovery_t=(9.6, 500.0)),
                 _run("a0.3", 3, 100.0),
                 _run("a0.3", 4, 100.0, ok=False, recovery_t=(1.0,))]
                + [_run("warm", 1, 100.0, recovery_t=(20.0,)),
                   _run("warm", 2, 100.0, recovery_t=(40.0,))])
        rows = pt.stuck_rows(runs)
        self.assertEqual(rows, [
            {"profile": "quiet90", "variant": "a0.3", "cruise": 0.8, "course": "blocks",
             "missions": 3, "with_recovery": 2, "recoveries": 3, "early": 2,
             "median_first_s": 9.6, "latest_first_s": 9.6},
            {"profile": "quiet90", "variant": "warm", "cruise": 0.8, "course": "blocks",
             "missions": 2, "with_recovery": 2, "recoveries": 2, "early": 1,
             "median_first_s": 30.0, "latest_first_s": 40.0}])

    def test_stuck_rows_without_recoveries(self):
        rows = pt.stuck_rows([_run("warm", 1, 100.0), _run("warm", 2, 100.0, ok=False)])
        self.assertEqual(rows[0]["missions"], 1)
        self.assertEqual(rows[0]["with_recovery"], 0)
        self.assertIsNone(rows[0]["median_first_s"])
        self.assertIsNone(rows[0]["latest_first_s"])

    def test_pair_effects(self):
        runs = ([_run("a0.3", s, 100.0, recovery_t=(9.6,)) for s in range(1, 7)]
                + [_run("warm", s, 90.0) for s in range(1, 7)]
                + [_run("restart+warm", s, 90.0, restarts=2) for s in range(1, 7)])
        effects, tallies = pt.pair_effects(runs)
        self.assertIsNot(pi.PAIRS, pt.PAIRS)
        self.assertEqual(len(effects), 2)
        self.assertEqual(tallies, [
            {"profile": "quiet90", "variant": "warm", "against": "a0.3", "groups": 1,
             "groups_faster": 1, "groups_slower": 0, "groups_lost": 0, "groups_gained": 0,
             "largest_median_diff_share": -0.1},
            {"profile": "quiet90", "variant": "restart+warm", "against": "warm", "groups": 1,
             "groups_faster": 0, "groups_slower": 0, "groups_lost": 0, "groups_gained": 0,
             "largest_median_diff_share": 0.0}])

    def test_profile_effects(self):
        runs = ([_run("warm", s, 100.0) for s in range(1, 7)]
                + [_run("warm", s, 110.0, profile="blocked30") for s in range(1, 7)])
        effects, tallies = pt.profile_effects(runs)
        self.assertNotIn("warm", pj.VARIANTS)
        self.assertEqual(len(effects), 1)
        self.assertEqual(len(tallies), 1)
        self.assertEqual(tallies[0]["groups_slower"], 1)
        self.assertEqual((tallies[0]["variant"], tallies[0]["profile"], tallies[0]["against"]),
                         ("warm", "blocked30", "quiet90"))

    def test_main_small(self):
        with tiny_courses():
            with tempfile.TemporaryDirectory() as d, redirect_stdout(io.StringIO()):
                pt.main(["--out-dir", d, "--first-seed", "349", "--seeds", "2",
                         "--profiles", "quiet90,blocked30", "--variants", "warm"])
                with open(os.path.join(d, "summary.json")) as f:
                    out = json.load(f)
                with open(os.path.join(d, "report.md")) as f:
                    md = f.read()
                with open(os.path.join(d, "runs.jsonl")) as f:
                    lines = [json.loads(x) for x in f if x.strip()]
        # outage90 and a0.3 are always flown: 3 profiles x 2 variants x 2 seeds.
        self.assertEqual(out["runs"], 12)
        self.assertEqual(out["seeds"], [349, 350])
        self.assertEqual(sorted({r["profile"] for r in lines}),
                         ["blocked30", "outage90", "quiet90"])
        self.assertEqual(sorted({r["variant"] for r in lines}), ["a0.3", "warm"])
        self.assertTrue(all("stuck" in r and "gps" in r and "position_err" in r
                            for r in lines))
        self.assertTrue(all(r["stuck"]["warmup_s"] == (10.0 if r["variant"] == "warm" else 0.0)
                            for r in lines))
        self.assertTrue(all(len(r["stuck"]["recovery_t"]) == r["recoveries"]
                            for r in lines if r["ok"]))
        self.assertTrue(out["done"])
        self.assertEqual(sorted((v["profile"], v["variant"], v["against"])
                                for v in out["verdicts"]),
                         [("blocked30", "warm", "a0.3"), ("outage90", "warm", "a0.3"),
                          ("quiet90", "warm", "a0.3")])
        self.assertEqual(sorted((v["variant"], v["profile"], v["against"])
                                for v in out["profile_verdicts"]),
                         [("a0.3", "blocked30", "quiet90"), ("warm", "blocked30", "quiet90")])
        self.assertEqual(out["flown_as"], "keep16")
        self.assertEqual(out["warmup_s"], 10.0)
        self.assertIsNone(out["check"])
        self.assertEqual(len(out["stuck"]), 6)
        self.assertIn("## Recovery moves (first before 30 s: at the start)", md)
        self.assertIn("Seeds 349-350.", md)
        self.assertIs(rp.GpsFilter, GPS_FILTER)
        self.assertIs(rp.Pilot._stuck, STUCK)
        self.assertEqual(set(pl.PROFILES), KNOWN)


if __name__ == "__main__":
    unittest.main()
