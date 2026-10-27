"""Tests for the study of a warm-up only after a stand, with blocks of many lengths.

Run: python -m unittest test_pace_v -v
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
import pace_study as ps  # noqa: E402
import pace_t as pt  # noqa: E402
import pace_u as pu  # noqa: E402
import pace_v as pv  # noqa: E402
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


def fake_pilot():
    """Just what Pilot._stuck and the warm-up read: a 10 s window, 1.5 m,
    cruise 0.8, a GPS that never moves and a count of recovery moves."""
    return types.SimpleNamespace(
        _history=collections.deque(), stuck_window_s=10.0, stuck_min_move_m=1.5,
        steering=types.SimpleNamespace(cruise=0.8), recoveries=0,
        gps=types.SimpleNamespace(lat=37.0, lon=-122.0))


def first_verdict(warmup_s, warm, stop=None, recover=False, until=60.0):
    """When a rover that never moves is first called stuck, asked every 0.5 s
    from 0.25 s while the pilot asks for 0.8 forward. With `stop` (a, b) no
    check is made from a until b and the history is cleared, as at a stop;
    with `recover` a recovery move is counted in that time. Returns the time
    (or None) and the stands recorded."""
    p = fake_pilot()
    times, stands = [], []
    with pv._warming(warmup_s, warm, times, stands):
        t = 0.25
        stopped = False
        while t < until:
            if stop and stop[0] <= t < stop[1]:
                if not stopped:
                    p._history.clear()
                    if recover:
                        p.recoveries += 1
                    stopped = True
                t += 0.5
                continue
            if rp.Pilot._stuck(p, t, 0.8):
                return t, stands
            t += 0.5
    return None, stands


def assert_restored(case):
    case.assertIs(rp.GpsFilter, SAVED[0])
    case.assertIs(rp.Pilot._stuck, SAVED[1])
    case.assertIs(rp.SimRover._step, SAVED[2])
    case.assertEqual(set(pl.PROFILES), KNOWN)


class SetupTests(unittest.TestCase):
    def test_profiles(self):
        self.assertEqual(list(pv.PROFILES), ["outage90", "quiet90", "quietdrift90", "quiet45",
                                             "blockedstart", "blockedmid"])
        for name in ("outage90", "quiet90", "quietdrift90", "quiet45"):
            self.assertIs(pv.PROFILES[name], pt.PROFILES[name])
        self.assertIs(pv.PROFILES["blockedstart"], pt.PROFILES["quiet90"])
        self.assertIs(pv.PROFILES["blockedmid"], pt.PROFILES["quiet90"])
        self.assertNotIn("blocked_until_s", pv.PROFILES["blockedmid"])
        self.assertEqual(pv.BASE_PROFILE, "outage90")
        self.assertEqual(pv.BLOCKED, ("blockedstart", "blockedmid"))
        self.assertEqual(pv.UNBLOCKED, ("outage90", "quiet90", "quietdrift90", "quiet45"))
        self.assertEqual(pv.BLOCKS["blockedstart"], ((0.0, 0.0), (30.0, 60.0)))
        self.assertEqual(pv.BLOCKS["blockedmid"], ((240.0, 600.0), (30.0, 60.0)))

    def test_variants(self):
        self.assertEqual(list(pv.VARIANTS), ["a0.3", "warm10", "warmstand10", "a0.3:B"])
        self.assertEqual(pv.VARIANTS["a0.3"], pu.VARIANTS["a0.3"])
        self.assertEqual(pv.VARIANTS["a0.3:B"], pu.VARIANTS["a0.3"])
        self.assertEqual(pv.VARIANTS["warm10"],
                         dict(pu.VARIANTS["warm10"], warm="always"))
        self.assertEqual(pv.VARIANTS["warmstand10"],
                         {"alpha": 0.3, "warmup_s": 10.0, "warm": "stand"})
        self.assertEqual(pv.BASE_VARIANT, "a0.3")
        self.assertEqual(pv.NOISE_VARIANT, "a0.3:B")
        self.assertEqual(pv.PAIRS, (("a0.3", "warm10"), ("a0.3", "warmstand10"),
                                    ("warm10", "warmstand10")))
        self.assertEqual(pv.CRUISES, (0.8,))
        self.assertEqual(pv.FIRST_SEED, pu.FIRST_SEED + 24)
        self.assertEqual(pv.FIRST_SEED, 397)
        self.assertEqual(pv.FIRST_SEED_B, 421)
        self.assertEqual((pv.STAND_S, pv.CATCH_S, pv.POST_S), (3.0, 30.0, 10.0))
        self.assertEqual((pv.CORNER_TOL_MIN_M, pv.OFFSET_TOL_MIN_M), (0.25, 0.5))
        self.assertEqual(pv.EARLY_S, 30.0)

    def test_checked_u(self):
        self.assertEqual(len(pv.CHECKED_U), 8)
        for (profile, variant, course, seed), (elapsed, rec) in pv.CHECKED_U.items():
            with self.subTest(profile=profile, variant=variant, course=course, seed=seed):
                self.assertIn(profile, pv.AS_PACE_U)
                self.assertIn(profile, pu.PROFILES)
                self.assertIn(variant, ("a0.3", "warm10"))
                self.assertIn(course, ps.COURSES)
                self.assertGreaterEqual(seed, pu.FIRST_SEED)
                self.assertLess(seed, pu.FIRST_SEED + 24)
                self.assertGreater(elapsed, 1000.0)
                self.assertIsInstance(rec, list)
        self.assertEqual(pv.AS_PACE_U["blocked30"],
                         ("quiet90", (0.0, pu.PROFILES["blocked30"]["blocked_until_s"])))


class BlockTests(unittest.TestCase):
    def test_no_block(self):
        for profile in pv.UNBLOCKED:
            self.assertIsNone(pv.block_window(profile, 400))

    def test_block_windows(self):
        for seed in (397, 410, 421, 444):
            with self.subTest(seed=seed):
                s, e = pv.block_window("blockedstart", seed)
                self.assertEqual(s, 0.0)
                self.assertGreaterEqual(e - s, 30.0 - 0.05)
                self.assertLessEqual(e - s, 60.0 + 0.05)
                s, e = pv.block_window("blockedmid", seed)
                self.assertGreaterEqual(s, 240.0)
                self.assertLessEqual(s, 600.0)
                self.assertGreaterEqual(e - s, 30.0 - 0.15)
                self.assertLessEqual(e - s, 60.0 + 0.15)
                self.assertEqual(pv.block_window("blockedmid", seed),
                                 pv.block_window("blockedmid", seed))

    def test_outages_are_the_rovers_own(self):
        for profile in ("outage90", "quiet45", "blockedmid"):
            p = pv.PROFILES[profile]
            windows = pv.outages(profile, 400)
            self.assertEqual(windows, pi.outage_windows(400, p["outage_s"], p["clear_s"]))
        self.assertEqual(pv.outages("blockedstart", 400), pv.outages("quiet90", 400))

    def test_overlaps(self):
        self.assertTrue(pv.overlaps([(10.0, 20.0)], 15.0, 45.0))
        self.assertTrue(pv.overlaps([(10.0, 20.0)], 0.0, 10.5))
        self.assertFalse(pv.overlaps([(10.0, 20.0)], 20.0, 50.0))
        self.assertFalse(pv.overlaps([(10.0, 20.0)], 0.0, 10.0))
        self.assertFalse(pv.overlaps([], 0.0, 30.0))
        self.assertTrue(pv.overlaps([[1.0, 2.0], [31.5, 36.0]], 30.0, 60.0))

    def test_blocking_holds_the_rover(self):
        sim = rp.SimRover([(100.0, 0.0)], seed=1)
        sim.applied = (1.0, 0.0)
        with pv._blocking([0.0, 1.0]):
            for _ in range(10):
                sim._step()
            self.assertEqual(sim.travelled, 0.0)
            for _ in range(10):
                sim._step()
            self.assertGreater(sim.travelled, 0.0)
            self.assertEqual(sim.blocked_until_s, 0.0)
        assert_restored(self)

    def test_no_window_changes_nothing(self):
        with pv._blocking(None):
            self.assertIs(rp.SimRover._step, SAVED[2])
        assert_restored(self)


class WarmingTests(unittest.TestCase):
    def test_catch_times_from_the_start(self):
        # 9 s of history after the warm-up; the first check starts both warm-ups.
        self.assertEqual(first_verdict(0.0, "never")[0], 9.25)
        self.assertEqual(first_verdict(10.0, "always")[0], 19.25)
        self.assertEqual(first_verdict(10.0, "stand")[0], 19.25)
        assert_restored(self)

    def test_a_short_stop_starts_no_warm_up(self):
        # Checks at 12.25 and 12.75 are missed: a 1.5 s gap, as at a stop for
        # two dropped fixes. The history starts again at 13.25.
        t, stands = first_verdict(10.0, "stand", stop=(12.0, 13.0))
        self.assertEqual((t, stands), (22.25, []))
        t, stands = first_verdict(10.0, "always", stop=(12.0, 13.0))
        self.assertEqual((t, stands), (32.25, []))

    def test_a_stand_starts_one(self):
        # From 12.0 to 16.0 nothing is checked: a 4.5 s gap since 11.75.
        for warm in ("stand", "always"):
            with self.subTest(warm=warm):
                t, stands = first_verdict(10.0, warm, stop=(12.0, 16.0))
                self.assertEqual((t, stands), (35.25, [(11.75, 16.25)]))
        t, stands = first_verdict(0.0, "never", stop=(12.0, 16.0))
        self.assertEqual(t, 9.25)

    def test_a_recovery_move_is_no_stand(self):
        t, stands = first_verdict(10.0, "stand", stop=(12.0, 16.0), recover=True)
        self.assertEqual((t, stands), (25.25, []))
        t, stands = first_verdict(10.0, "always", stop=(12.0, 16.0), recover=True)
        self.assertEqual((t, stands), (35.25, []))
        assert_restored(self)


class FlyTests(unittest.TestCase):
    def test_flies_as_pace_u(self):
        for variant in ("a0.3", "warm10"):
            with self.subTest(variant=variant):
                got = pv.fly("corner", 1, "quiet90", variant, 0.8, course=CORNER60)
                want = pu.fly("corner", 1, "quiet90", variant, 0.8, course=CORNER60)
                stuck = got.pop("stuck")
                want_stuck = want.pop("stuck")
                self.assertEqual(got, want)
                for k in ("warmup_s", "recovery_t", "first_outage_s"):
                    self.assertEqual(stuck[k], want_stuck[k])
                self.assertIsNone(stuck["block"])
                self.assertIsNone(stuck["block_outage"])
        assert_restored(self)

    def test_a_start_block_flies_as_blocked30(self):
        for variant in ("a0.3", "warm10"):
            with self.subTest(variant=variant):
                got = pv.fly("corner", 4, "quiet90", variant, 0.8, course=CORNER60,
                             block=[0.0, 30.0])
                want = pu.fly("corner", 4, "blocked30", variant, 0.8, course=CORNER60)
                stuck = got.pop("stuck")
                want_stuck = want.pop("stuck")
                self.assertEqual(got, want)
                self.assertEqual(stuck["recovery_t"], want_stuck["recovery_t"])
                self.assertEqual(stuck["block"], [0.0, 30.0])
                self.assertLess(stuck["recovery_t"][0], 30.0)
        assert_restored(self)

    def test_block_profiles_draw_their_block(self):
        for profile in pv.BLOCKED:
            with self.subTest(profile=profile):
                r = pv.fly("corner", 4, profile, "warmstand10", 0.8, course=CORNER60)
                self.assertTrue(r["ok"], r["reason"])
                self.assertEqual(r["stuck"]["block"], pv.block_window(profile, 4))
                self.assertIsInstance(r["stuck"]["block_outage"], bool)
                self.assertEqual(r["stuck"]["warm"], "stand")
                self.assertEqual(len(r["stuck"]["recovery_t"]), r["recoveries"])
                self.assertIsInstance(r["stuck"]["stands"], list)
        assert_restored(self)

    def test_restored_after_a_failure(self):
        with self.assertRaises(Exception):
            pv.fly("no-such-course", 1, "blockedmid", "warmstand10", 0.8)
        assert_restored(self)

    def test_failed_run_fields(self):
        r = pv.failed_run(ValueError("boom"))
        self.assertFalse(r["ok"])
        self.assertEqual(r["gps"], pq.NO_GPS)
        self.assertEqual(r["aim"], pp.NO_AIM)
        self.assertEqual(r["stuck"], pv.NO_STUCK)


class CheckTests(unittest.TestCase):
    def test_check_against_pace_u(self):
        with tiny_courses():
            a = pu.fly("tiny", 5, "blocked30", "warm10", 0.8)
            b = pu.fly("tiny", 6, "quiet90", "a0.3", 0.8)
            expected = {
                ("blocked30", "warm10", "tiny", 5): (a["elapsed_s"], a["stuck"]["recovery_t"]),
                ("quiet90", "a0.3", "tiny", 6): (b["elapsed_s"] + 1.0,
                                                 b["stuck"]["recovery_t"]),
            }
            out = pv.check_u(expected)
        self.assertEqual((out["compared"], out["identical"]), (2, 1))
        self.assertEqual(len(out["different"]), 1)
        self.assertEqual(out["different"][0]["seed"], 6)
        self.assertEqual(out["different"][0]["got"]["elapsed_s"], b["elapsed_s"])
        assert_restored(self)


def _run(variant, seed, elapsed, profile="quiet90", ok=True, recovery_t=(), stands=(),
         block=None, block_outage=None, course="blocks"):
    return {"profile": profile, "variant": variant, "cruise": 0.8, "course": course,
            "seed": seed, "ok": ok, "elapsed_s": elapsed, "time_s": {"stopped": 10.0},
            "reports": 5, "reached": 5, "recoveries": len(recovery_t),
            "offset": {"n": 5, "median_m": 1.0, "p95_m": 3.0, "max_m": 5.0},
            "position_err": {"n": 5, "median_m": 2.0, "p95_m": 4.0, "max_m": 10.0},
            "corner": {"n": 0, "median_m": None, "p95_m": None, "max_m": None, "corners": 0,
                       "median_past_m": None, "max_past_m": None},
            "context": {c: EMPTY for c in po.CONTEXTS},
            "planner": {"plans": 5, "behind": 0},
            "aim": dict(pp.NO_AIM), "gps": {"filters": 1, "restarts": None},
            "stuck": {"warmup_s": 0.0, "warm": "never", "recovery_t": list(recovery_t),
                      "stands": [list(x) for x in stands], "block": block,
                      "block_outage": block_outage, "first_outage_s": 600.0}}


class SummaryTests(unittest.TestCase):
    def test_block_record(self):
        self.assertIsNone(pv.block_record({"block": None, "recovery_t": [9.1]}))
        self.assertEqual(
            pv.block_record({"block": [0.0, 40.0], "recovery_t": [9.1, 24.2, 41.0, 55.0],
                             "stands": [], "block_outage": False}),
            {"caught_s": 9.1, "eligible": True, "post": 1})
        # A stand inside the first 30 s makes it ineligible; 318.4 is 18.4 s in.
        self.assertEqual(
            pv.block_record({"block": [300.0, 345.5],
                             "recovery_t": [100.0, 318.4, 333.5, 350.0],
                             "stands": [[310.0, 314.0]], "block_outage": False}),
            {"caught_s": 18.4, "eligible": False, "post": 1})
        # 285 is 35 s in: not caught. An outage makes it ineligible.
        self.assertEqual(
            pv.block_record({"block": [250.0, 290.0], "recovery_t": [285.0],
                             "stands": [[200.0, 204.0]], "block_outage": True}),
            {"caught_s": None, "eligible": False, "post": 0})

    def test_block_rows(self):
        runs = [_run("a0.3", 1, 100.0, profile="blockedstart", block=[0.0, 40.0],
                     block_outage=False, recovery_t=(9.1, 24.2, 41.0)),
                _run("a0.3", 2, 100.0, profile="blockedstart", block=[0.0, 35.0],
                     block_outage=False, recovery_t=(11.1, 26.2)),
                # Eligible, caught only after 30 s: missed.
                _run("a0.3", 3, 100.0, profile="blockedstart", block=[0.0, 50.0],
                     block_outage=False, recovery_t=(31.0,)),
                # An outage: not eligible, but caught.
                _run("a0.3", 4, 100.0, profile="blockedstart", block=[0.0, 30.0],
                     block_outage=True, recovery_t=(9.1,)),
                _run("a0.3", 5, 100.0, profile="blockedstart", block=[0.0, 30.0],
                     ok=False, block_outage=False),
                _run("a0.3", 6, 100.0)]
        rows = pv.block_rows(runs)
        self.assertEqual(rows, [
            {"profile": "blockedstart", "variant": "a0.3", "cruise": 0.8, "course": "blocks",
             "missions": 4, "eligible": 3, "caught": 2, "missed": 1, "caught_any": 3,
             "median_catch_s": 10.1, "latest_catch_s": 11.1, "post": 1,
             "post_missions": 1}])

    def test_stuck_rows(self):
        runs = [_run("warmstand10", 1, 100.0, recovery_t=(9.1, 549.9),
                     stands=((100.0, 190.0), (700.0, 704.0))),
                _run("warmstand10", 2, 100.0),
                _run("warmstand10", 3, 100.0, ok=False, recovery_t=(1.0,))]
        self.assertEqual(pv.stuck_rows(runs), [
            {"profile": "quiet90", "variant": "warmstand10", "cruise": 0.8, "course": "blocks",
             "missions": 2, "with_recovery": 1, "recoveries": 2, "early": 1, "late": 1,
             "stands": 2, "median_first_s": 9.1, "latest_first_s": 9.1}])

    def test_tolerances(self):
        corner = [{"profile": "quiet90", "variant": "a0.3", "course": "blocks", "p95_m": 3.10},
                  {"profile": "quiet90", "variant": "a0.3:B", "course": "blocks", "p95_m": 3.42},
                  {"profile": "outage90", "variant": "a0.3", "course": "blocks", "p95_m": 2.0},
                  {"profile": "outage90", "variant": "a0.3:B", "course": "blocks",
                   "p95_m": 2.05},
                  # Only blocks counts for corners.
                  {"profile": "quiet90", "variant": "a0.3", "course": "bayside", "p95_m": 1.0},
                  {"profile": "quiet90", "variant": "a0.3:B", "course": "bayside",
                   "p95_m": 3.0},
                  {"profile": "quiet90", "variant": "a0.3", "course": "boulevard",
                   "p95_m": None},
                  {"profile": "quiet90", "variant": "a0.3:B", "course": "boulevard",
                   "p95_m": None},
                  {"profile": "quiet90", "variant": "warm10", "course": "blocks",
                   "p95_m": 9.0}]
        offsets = [{"profile": "quiet90", "variant": "a0.3", "course": "bayside",
                    "p95_offset_m": 1.0},
                   {"profile": "quiet90", "variant": "a0.3:B", "course": "bayside",
                    "p95_offset_m": 1.1},
                   {"profile": "outage90", "variant": "a0.3", "course": "blocks",
                    "p95_offset_m": 2.0},
                   {"profile": "outage90", "variant": "a0.3:B", "course": "blocks",
                    "p95_offset_m": 2.0}]
        self.assertEqual(pv.tolerances(corner, offsets),
                         {"corner_spread_m": 0.32, "corner_tol_m": 0.35,
                          "offset_spread_m": 0.1, "offset_tol_m": 0.5})
        self.assertEqual(pv.tolerances([], []),
                         {"corner_spread_m": None, "corner_tol_m": None,
                          "offset_spread_m": None, "offset_tol_m": None})

    def test_step_up(self):
        self.assertEqual(pv._step_up(0.3), 0.3)
        self.assertEqual(pv._step_up(0.32), 0.35)
        self.assertEqual(pv._step_up(0.75), 0.75)
        self.assertEqual(pv._step_up(0.0), 0.0)

    def test_pair_effects(self):
        runs = ([_run("a0.3", s, 100.0, recovery_t=(9.1,)) for s in range(1, 7)]
                + [_run(v, s, 90.0) for v in ("warm10", "warmstand10") for s in range(1, 7)]
                + [_run("a0.3:B", s, 50.0) for s in range(21, 27)])
        effects, tallies = pv.pair_effects(runs)
        self.assertIsNot(pi.PAIRS, pv.PAIRS)
        self.assertEqual(len(effects), 3)
        self.assertEqual([(t["variant"], t["against"]) for t in tallies],
                         [("warm10", "a0.3"), ("warmstand10", "a0.3"),
                          ("warmstand10", "warm10")])
        self.assertEqual([t["groups_faster"] for t in tallies], [1, 1, 0])
        self.assertEqual([t["groups_slower"] for t in tallies], [0, 0, 0])

    def test_profile_effects(self):
        runs = ([_run("warmstand10", s, 100.0) for s in range(1, 7)]
                + [_run("warmstand10", s, 110.0, profile="blockedmid") for s in range(1, 7)])
        effects, tallies = pv.profile_effects(runs)
        self.assertNotIn("warmstand10", pj.VARIANTS)
        self.assertEqual(len(tallies), 1)
        self.assertEqual(tallies[0]["groups_slower"], 1)
        self.assertEqual((tallies[0]["variant"], tallies[0]["profile"], tallies[0]["against"]),
                         ("warmstand10", "blockedmid", "quiet90"))

    def test_main_small(self):
        with tiny_courses():
            with tempfile.TemporaryDirectory() as d, redirect_stdout(io.StringIO()):
                pv.main(["--out-dir", d, "--seeds", "2", "--profiles", "quiet90,blockedstart",
                         "--variants", "warmstand10,a0.3:B"])
                with open(os.path.join(d, "summary.json")) as f:
                    out = json.load(f)
                with open(os.path.join(d, "report.md")) as f:
                    md = f.read()
                with open(os.path.join(d, "runs.jsonl")) as f:
                    lines = [json.loads(x) for x in f if x.strip()]
        # outage90 and a0.3 are always flown: 3 profiles x 3 variants x 2 seeds.
        self.assertEqual(out["runs"], 18)
        self.assertEqual(out["seeds"], [397, 398])
        self.assertEqual(out["seeds_b"], [421, 422])
        self.assertEqual(sorted({r["profile"] for r in lines}),
                         ["blockedstart", "outage90", "quiet90"])
        self.assertEqual(sorted({r["variant"] for r in lines}),
                         ["a0.3", "a0.3:B", "warmstand10"])
        self.assertEqual(sorted({r["seed"] for r in lines if r["variant"] == "a0.3:B"}),
                         [421, 422])
        self.assertEqual(sorted({r["seed"] for r in lines if r["variant"] != "a0.3:B"}),
                         [397, 398])
        self.assertTrue(all(r["stuck"]["block"] == pv.block_window(r["profile"], r["seed"])
                            for r in lines if r["ok"]))
        self.assertTrue(all(len(r["stuck"]["recovery_t"]) == r["recoveries"]
                            for r in lines if r["ok"]))
        self.assertTrue(out["done"])
        self.assertEqual(sorted((v["profile"], v["variant"], v["against"])
                                for v in out["verdicts"]),
                         [("blockedstart", "warmstand10", "a0.3"),
                          ("outage90", "warmstand10", "a0.3"),
                          ("quiet90", "warmstand10", "a0.3")])
        self.assertEqual(sorted(out["tolerance"]),
                         ["corner_spread_m", "corner_tol_m", "offset_spread_m", "offset_tol_m"])
        self.assertEqual({x["profile"] for x in out["block"]}, {"blockedstart"})
        self.assertIsNone(out["check_u"])
        self.assertIn("Blocked rovers", md)
        self.assertIn("Seeds 397-398;", md)
        assert_restored(self)


if __name__ == "__main__":
    unittest.main()
