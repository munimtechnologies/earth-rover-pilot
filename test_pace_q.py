"""Tests for the study of the GPS filter's lag.

Run: python -m unittest test_pace_q -v
"""

import inspect
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
LAT0, LON0 = 37.0, -122.0
EMPTY = {"n": 0, "median_m": None, "p95_m": None, "max_m": None, "far": 0}


def north(m):
    """The (lat, lon) m metres north of (LAT0, LON0)."""
    return rp.offset_latlon(LAT0, LON0, m, 0.0)


def behind(f, m):
    """Metres between f's estimate and the point m metres north."""
    return rp.haversine_m(f.lat, f.lon, *north(m))


def steady(f, fixes, start=0):
    """Feed f a fix every 2 s from a rover going north at 1 m/s, for
    `fixes` fixes from second `start`; returns the last fix's metres."""
    for k in range(fixes):
        t = start + 2 * k
        f.update(*north(float(t)), float(t))
    return float(start + 2 * (fixes - 1))


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
        self.assertEqual(list(pq.PROFILES), ["outage90", "quiet90", "quietdrift90"])
        self.assertIs(pq.PROFILES["outage90"], pl.PROFILES["outage90"])
        self.assertEqual(pq.QUIET_NOISE_M, 0.22)
        self.assertEqual(pq.PROFILES["quiet90"],
                         dict(pl.PROFILES["outage90"], gps_noise_m=0.22))
        self.assertEqual(pq.PROFILES["quietdrift90"],
                         dict(pl.PROFILES["drift90"], gps_noise_m=0.22))
        # Without it the profiles fly the simulator's 1.5 m.
        for name in ("outage90", "drift90"):
            self.assertNotIn("gps_noise_m", pl.PROFILES[name])
        default = inspect.signature(rp.SimRover.__init__).parameters["gps_noise_m"].default
        self.assertEqual(default, 1.5)
        self.assertNotIn("quiet90", pl.PROFILES)
        self.assertEqual(pq.BASE_PROFILE, "outage90")
        self.assertEqual(pq.PROFILE_PAIRS, (("outage90", "quiet90"), ("quiet90", "quietdrift90")))

    def test_variants(self):
        self.assertEqual(pq.VARIANTS, {
            "a0.3": {"alpha": 0.3},
            "a0.6": {"alpha": 0.6},
            "raw": {"alpha": 1.0},
            "track": {"alpha": 0.3, "beta": 0.053, "track": True}})
        self.assertEqual(pq.BASE_VARIANT, "a0.3")
        self.assertEqual(pq.PAIRS, (("a0.3", "a0.6"), ("a0.3", "raw"), ("a0.3", "track")))
        # a0.3 is the filter as it ships.
        self.assertEqual(rp.GpsFilter().alpha, pq.VARIANTS["a0.3"]["alpha"])
        # beta = alpha^2 / (2 - alpha) = 0.0529...
        self.assertAlmostEqual(0.3 ** 2 / (2 - 0.3), pq.VARIANTS["track"]["beta"], places=3)
        # Every mission is otherwise v0.18.2's real-rover pilot as pace_p flies it.
        self.assertEqual(pq.FLOWN_AS, "keep16")
        self.assertEqual(pp.VARIANTS[pq.FLOWN_AS], {"lookahead_m": rp.PATH_LOOKAHEAD_M})
        self.assertEqual(pq.CRUISES, (0.8,))
        self.assertEqual(pq.FIRST_SEED, 277)
        self.assertEqual(pq.CHECKED, {"profiles": ("outage90", "drift90"), "variant": "a0.3",
                                      "against": "keep16", "seeds": (253, 254, 255)})


def _state(f):
    return (f.lat, f.lon, f.raw, f.raw_t, f.fix_t, f.rejected)


class TrackingFilterTests(unittest.TestCase):
    def test_without_beta_or_restart_it_is_the_plain_filter(self):
        plain = rp.GpsFilter(alpha=0.3)
        tracking = pq.TrackingGpsFilter(alpha=0.3, beta=0.0, restart=False)
        # A repeat, a no-fix, three jumps that end in a reset, and an 8 s gap.
        readings = [(north(0.0), 0.0), (north(0.0), 0.1), (north(1.8), 2.0),
                    ((rp.NO_FIX, rp.NO_FIX), 2.1), (north(3.6), 4.0), (north(60.0), 6.0),
                    (north(60.0), 6.1), (north(62.0), 8.0), (north(64.0), 10.0),
                    (north(65.8), 12.0), (north(70.0), 20.0), (north(71.8), 22.0)]
        accepted = 0
        for (lat, lon), t in readings:
            with self.subTest(t=t):
                a = plain.update(lat, lon, t)
                b = tracking.update(lat, lon, t)
                self.assertEqual(a, b)
                self.assertEqual(_state(plain), _state(tracking))
                self.assertEqual(plain.has_fix(t), tracking.has_fix(t))
                accepted += a is not None
        # 0, 1.8, 3.6, 64 (the reset), 65.8, 70 and 71.8 were accepted.
        self.assertEqual(accepted, 7)
        self.assertEqual(tracking.restarts, 0)

    def test_tracks_a_steady_speed_without_lag(self):
        plain = rp.GpsFilter(alpha=0.3)
        tracking = pq.TrackingGpsFilter(alpha=0.3, beta=0.053)
        last = steady(plain, 60)
        steady(tracking, 60)
        # The average lags (1 - 0.3) / 0.3 fixes of 2 m: 4.67 m.
        self.assertGreater(behind(plain, last), 4.6)
        self.assertLess(behind(plain, last), 4.7)
        self.assertLess(behind(tracking, last), 0.01)
        self.assertEqual(tracking.restarts, 0)

    def test_starts_again_after_a_gap(self):
        f = pq.TrackingGpsFilter(alpha=0.3, beta=0.053)
        last = steady(f, 30)
        self.assertEqual(last, 58.0)
        self.assertGreater(f.v_lat, 0.0)
        # 10 s without a reading (more than max_age_s), then 10 m on.
        self.assertEqual(f.update(*north(68.0), 68.0), north(68.0))
        self.assertEqual((f.lat, f.lon), north(68.0))
        self.assertEqual((f.v_lat, f.v_lon), (0.0, 0.0))
        self.assertEqual(f.restarts, 1)
        # With no velocity yet it moves 0.3 of the 2 m to the next fix.
        f.update(*north(70.0), 70.0)
        self.assertAlmostEqual(behind(f, 70.0), 1.4, places=4)
        self.assertGreater(f.v_lat, 0.0)

    def test_without_restart_it_carries_the_velocity_over_the_gap(self):
        f = pq.TrackingGpsFilter(alpha=0.3, beta=0.053, restart=False)
        steady(f, 30)
        f.update(*north(68.0), 68.0)
        self.assertEqual(f.restarts, 0)
        self.assertLess(behind(f, 68.0), 0.5)

    def test_a_jump_is_still_dropped(self):
        f = pq.TrackingGpsFilter(alpha=0.3, beta=0.053)
        steady(f, 2)
        before = (f.lat, f.lon, f.v_lat, f.v_lon)
        # 58 m in 2 s: over 3 m/s x 2 s + 10 m.
        self.assertIsNone(f.update(*north(60.0), 4.0))
        self.assertEqual((f.lat, f.lon, f.v_lat, f.v_lon), before)
        self.assertEqual(f.rejected, 1)


class FilteringTests(unittest.TestCase):
    def test_inside_only(self):
        made = []
        with pq._filtering(pq.VARIANTS["raw"], made):
            f = rp.GpsFilter()
        self.assertIs(rp.GpsFilter, GPS_FILTER)
        self.assertIs(type(f), GPS_FILTER)
        self.assertEqual(f.alpha, 1.0)
        self.assertEqual(made, [f])

    def test_track(self):
        made = []
        with pq._filtering(pq.VARIANTS["track"], made):
            f = rp.GpsFilter()
        self.assertIsInstance(f, pq.TrackingGpsFilter)
        self.assertEqual((f.alpha, f.beta, f.restart), (0.3, 0.053, True))
        self.assertEqual(made, [f])

    def test_restored_after_a_failure(self):
        with self.assertRaises(ValueError):
            with pq._filtering(pq.VARIANTS["a0.6"], []):
                raise ValueError("boom")
        self.assertIs(rp.GpsFilter, GPS_FILTER)


class KnownProfileTests(unittest.TestCase):
    def test_a_new_profile_is_known_inside_only(self):
        with pq._known_profile("quiet90"):
            self.assertIs(pl.PROFILES["quiet90"], pq.PROFILES["quiet90"])
        self.assertNotIn("quiet90", pl.PROFILES)

    def test_a_known_profile_is_left_alone(self):
        saved = pl.PROFILES["outage90"]
        with pq._known_profile("outage90"):
            self.assertIs(pl.PROFILES["outage90"], saved)
        self.assertIs(pl.PROFILES["outage90"], saved)
        self.assertEqual(set(pl.PROFILES), KNOWN)


class FlyTests(unittest.TestCase):
    def assert_restored(self):
        self.assertIs(rp.GpsFilter, GPS_FILTER)
        self.assertIs(rp.PathFollower, FOLLOWER)
        self.assertIs(pl.SlipRover, SLIP_ROVER)
        self.assertIs(pe.CountingEstimator, COUNTING)
        self.assertIs(ps.CoursePlanner, PLANNER)
        self.assertEqual(set(pl.PROFILES), KNOWN)

    def test_a03_flies_as_pace_p_keep16(self):
        for profile in ("outage90", "drift90"):
            with self.subTest(profile=profile):
                got = pq.fly("corner", 1, profile, "a0.3", 0.8, course=CORNER60)
                gps = got.pop("gps")
                want = pp.fly("corner", 1, profile, "keep16", 0.8, course=CORNER60)
                self.assertEqual(got, want)
                self.assertEqual(gps, {"filters": 1, "restarts": None})
        self.assert_restored()

    def test_the_quiet_profile_reaches_the_rover(self):
        loud = pq.fly("tiny", 3, "outage90", "a0.3", 0.8, course=TINY)
        quiet = pq.fly("tiny", 3, "quiet90", "a0.3", 0.8, course=TINY)
        self.assertNotEqual(loud["position_err"], quiet["position_err"])
        self.assert_restored()

    def test_each_variant_builds_its_filter(self):
        for variant in ("a0.6", "raw", "track"):
            with self.subTest(variant=variant):
                r = pq.fly("corner", 2, "quiet90", variant, 0.8, course=CORNER60)
                self.assertEqual(r["gps"]["filters"], 1)
                if variant == "track":
                    self.assertIsInstance(r["gps"]["restarts"], int)
                else:
                    self.assertIsNone(r["gps"]["restarts"])
                for key in ("aim", "corner", "context", "planner", "fit_err", "position_err"):
                    self.assertIn(key, r)
        self.assert_restored()

    def test_failed_run_fields(self):
        r = pq.failed_run(ValueError("boom"))
        self.assertFalse(r["ok"])
        self.assertEqual(r["gps"], pq.NO_GPS)
        self.assertEqual(r["aim"], pp.NO_AIM)
        self.assertEqual(r["planner"], {"plans": None, "behind": None})


class CheckTests(unittest.TestCase):
    def test_check_against_pace_p(self):
        with tiny_courses():
            ref = []
            for seed in (253, 254):
                r = pp.fly("tiny", seed, "outage90", "keep16", 0.8)
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
                out = pq.check_pace_p(path)
        # 2 profiles x 1 course x 3 seeds = 6 missions checked; the reference
        # has 2 of them, and seed 254 was altered.
        self.assertEqual((out["compared"], out["identical"], out["missing"]), (2, 1, 4))
        self.assertEqual(len(out["different"]), 1)
        self.assertEqual(out["different"][0]["seed"], 254)
        self.assertEqual(out["different"][0]["variant"], "a0.3")
        self.assertEqual(out["different"][0]["fields"], ["elapsed_s"])
        self.assertIs(rp.GpsFilter, GPS_FILTER)


def _run(variant, seed, elapsed, profile="outage90", ok=True, restarts=None, recoveries=0):
    return {"profile": profile, "variant": variant, "cruise": 0.8, "course": "blocks",
            "seed": seed, "ok": ok, "elapsed_s": elapsed, "time_s": {"stopped": 10.0},
            "reports": 5, "reached": 5, "recoveries": recoveries,
            "offset": {"n": 5, "median_m": 1.0, "p95_m": 3.0, "max_m": 5.0},
            "corner": {"n": 0, "median_m": None, "p95_m": None, "max_m": None, "corners": 0,
                       "median_past_m": None, "max_past_m": None},
            "context": {c: EMPTY for c in po.CONTEXTS},
            "planner": {"plans": 5, "behind": 0},
            "aim": dict(pp.NO_AIM), "gps": {"filters": 1, "restarts": restarts}}


class SummaryTests(unittest.TestCase):
    def test_pair_effects(self):
        runs = ([_run("a0.3", s, 100.0) for s in range(1, 7)]
                + [_run("raw", s, 90.0) for s in range(1, 7)])
        effects, tallies = pq.pair_effects(runs)
        self.assertIsNot(pi.PAIRS, pq.PAIRS)
        self.assertEqual(len(effects), 1)
        self.assertEqual((effects[0]["faster"], effects[0]["slower"]), (6, 0))
        self.assertEqual(tallies, [{"profile": "outage90", "variant": "raw",
                                    "against": "a0.3", "groups": 1, "groups_faster": 1,
                                    "groups_slower": 0, "groups_lost": 0, "groups_gained": 0,
                                    "largest_median_diff_share": -0.1}])

    def test_profile_effects(self):
        runs = ([_run("raw", s, 100.0) for s in range(1, 7)]
                + [_run("raw", s, 110.0, profile="quiet90") for s in range(1, 7)])
        effects, tallies = pq.profile_effects(runs)
        self.assertNotIn("raw", pj.VARIANTS)
        self.assertEqual(len(effects), 1)
        self.assertEqual(len(tallies), 1)
        self.assertEqual(tallies[0]["groups_slower"], 1)
        self.assertEqual((tallies[0]["variant"], tallies[0]["profile"], tallies[0]["against"]),
                         ("raw", "quiet90", "outage90"))

    def test_gps_rows(self):
        runs = [_run("track", 1, 100.0, restarts=2, recoveries=0),
                _run("track", 2, 100.0, restarts=4, recoveries=2),
                _run("track", 3, 100.0, ok=False, restarts=9, recoveries=9),
                _run("a0.3", 1, 100.0)]
        self.assertEqual(pq.gps_rows(runs), [
            {"profile": "outage90", "variant": "a0.3", "cruise": 0.8, "course": "blocks",
             "missions": 1, "median_recoveries": 0, "median_restarts": None},
            {"profile": "outage90", "variant": "track", "cruise": 0.8, "course": "blocks",
             "missions": 2, "median_recoveries": 1.0, "median_restarts": 3.0}])

    def test_main_small(self):
        with tiny_courses():
            with tempfile.TemporaryDirectory() as d, redirect_stdout(io.StringIO()):
                pq.main(["--out-dir", d, "--first-seed", "277", "--seeds", "2",
                         "--profiles", "quiet90", "--variants", "raw"])
                with open(os.path.join(d, "summary.json")) as f:
                    out = json.load(f)
                with open(os.path.join(d, "report.md")) as f:
                    md = f.read()
                with open(os.path.join(d, "runs.jsonl")) as f:
                    lines = [json.loads(x) for x in f if x.strip()]
        # outage90 and a0.3 are always flown: 2 profiles x 2 variants x 2 seeds.
        self.assertEqual(out["runs"], 8)
        self.assertEqual(out["seeds"], [277, 278])
        self.assertEqual(sorted({r["profile"] for r in lines}), ["outage90", "quiet90"])
        self.assertEqual(sorted({r["variant"] for r in lines}), ["a0.3", "raw"])
        self.assertTrue(all("gps" in r and "aim" in r and "context" in r and "corner" in r
                            and "fit_err" in r and "position_err" in r for r in lines))
        self.assertTrue(all(r["gps"]["filters"] == 1 for r in lines))
        self.assertTrue(out["done"])
        self.assertEqual(sorted((v["profile"], v["variant"], v["against"])
                                for v in out["verdicts"]),
                         [("outage90", "raw", "a0.3"), ("quiet90", "raw", "a0.3")])
        self.assertEqual(sorted((v["variant"], v["profile"], v["against"])
                                for v in out["profile_verdicts"]),
                         [("a0.3", "quiet90", "outage90"), ("raw", "quiet90", "outage90")])
        self.assertEqual(out["flown_as"], "keep16")
        self.assertEqual(out["quiet_noise_m"], 0.22)
        self.assertEqual(out["lookahead_m"], 16.0)
        self.assertIsNone(out["check"])
        self.assertEqual(len(out["position"]), 4)
        self.assertIn("## Where the pilot thinks it is, against where it is", md)
        self.assertIn("## Recovery moves and filter restarts", md)
        self.assertIn("Seeds 277-278.", md)
        self.assertIs(rp.GpsFilter, GPS_FILTER)
        self.assertIs(rp.PathFollower, FOLLOWER)
        self.assertEqual(set(pl.PROFILES), KNOWN)


if __name__ == "__main__":
    unittest.main()
