"""Tests for the study of the compass-bias learner on a drifting compass.

Run: python -m unittest test_pace_m -v
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
import pace_study as ps  # noqa: E402
import rover_pilot as rp  # noqa: E402

TINY = {"points": [(0.0, 0.0), (30.0, 0.0)], "checkpoints": [1]}
CORNER = {"points": [(0.0, 0.0), (40.0, 0.0), (40.0, 40.0)], "checkpoints": [1, 2]}
FAR = {"points": [(0.0, 0.0), (2000.0, 0.0)], "checkpoints": [1]}
SLIP_ROVER = pl.SlipRover
COUNTING = pe.CountingEstimator
LAT0, LON0 = 37.0, -122.0


class tiny_courses:
    """Replace pace_study's courses with one short course while in use."""

    def __enter__(self):
        self.saved = dict(ps.COURSES)
        ps.COURSES.clear()
        ps.COURSES["tiny"] = TINY

    def __exit__(self, *exc):
        ps.COURSES.clear()
        ps.COURSES.update(self.saved)


def drive_east(est, compass_at, seconds=200.0):
    """Drive due east at 0.8 m/s with an exact fix every 2 s and a compass
    reading compass_at(t) every 0.5 s; return the bias after every tick."""
    biases = []
    for i in range(int(seconds / 0.5) + 1):
        t = i * 0.5
        fix = rp.offset_latlon(LAT0, LON0, 0.0, 0.8 * t) if i % 4 == 0 else None
        est.update(t, fix, compass_at(t), 0.8, 0.0)
        biases.append(est.bias)
    return biases


class SetupTests(unittest.TestCase):
    def test_profiles(self):
        self.assertEqual(list(pm.PROFILES), ["outage90", "drift90", "lie90"])
        for name in pm.PROFILES:
            self.assertIs(pm.PROFILES[name], pl.PROFILES[name])
        self.assertEqual(pm.BASE_PROFILE, "outage90")
        self.assertEqual(pm.PROFILE_PAIRS, (("outage90", "drift90"), ("outage90", "lie90")))

    def test_variants(self):
        self.assertEqual(pm.VARIANTS, {"shipped": {}, "gain0.5": {"gain": 0.5},
                                       "gain0.15": {"gain": 0.15},
                                       "long20": {"min_move_m": 20.0},
                                       "long20-g0.5": {"min_move_m": 20.0, "gain": 0.5}})
        self.assertEqual(pm.BASE_VARIANT, "shipped")
        self.assertEqual(pm.PAIRS, (("shipped", "gain0.5"), ("shipped", "gain0.15"),
                                    ("shipped", "long20"), ("shipped", "long20-g0.5")))
        self.assertEqual(pm.FLOWN_AS, "bridge120+cf0.3")
        self.assertIn(pm.FLOWN_AS, pl.VARIANTS)
        self.assertEqual(pm.CRUISES, (0.8,))
        self.assertEqual(pm.FIRST_SEED, 181)
        self.assertEqual(pm.CHECKED, {"profiles": ("outage90", "lie90"), "variant": "shipped",
                                      "seeds": (157, 158, 159)})
        # The shipped learner is the pilot's own.
        est = rp.HeadingEstimator()
        self.assertEqual((est.gain, est.min_move_m), (0.3, 10.0))


class RecordingTests(unittest.TestCase):
    def test_decides_as_a_counting_estimator(self):
        for settings in ({}, {"gain": 0.5}, {"gain": 0.15}, {"min_move_m": 20.0}):
            with self.subTest(**settings):
                a = pm.RecordingEstimator(truth=lambda: 10.0, **settings)
                b = COUNTING(**settings)
                step = lambda t: 80.0 if t < 60.0 else 70.0  # noqa: E731
                self.assertEqual(drive_east(a, step), drive_east(b, step))
                self.assertEqual((a.calibrations, a.fits, a.breaks),
                                 (b.calibrations, b.fits, b.breaks))
                self.assertGreater(a.calibrations, 3)
                self.assertEqual(len(a.fit_errors), a.calibrations)

    def test_fit_errors_are_the_measurements_against_the_truth(self):
        # Due east (90 deg) with the compass reading 80: every measurement is
        # 10, the truth, until the compass turns to read 70 (a measurement of 20).
        for gain in (0.3, 0.5, 0.15):
            with self.subTest(gain=gain):
                est = pm.RecordingEstimator(truth=lambda: 10.0, gain=gain)
                drive_east(est, lambda t: 80.0)
                self.assertGreater(len(est.fit_errors), 5)
                for e in est.fit_errors:
                    self.assertAlmostEqual(e, 0.0, places=6)
                est = pm.RecordingEstimator(truth=lambda: 10.0, gain=gain)
                drive_east(est, lambda t: 80.0 if t < 60.0 else 70.0)
                self.assertAlmostEqual(est.fit_errors[0], 0.0, places=6)
                self.assertAlmostEqual(est.fit_errors[-1], 10.0, places=6)

    def test_across_north(self):
        # Heading 90, compass 260: the bias is -170; truth -170 gives no error.
        est = pm.RecordingEstimator(truth=lambda: -170.0)
        drive_east(est, lambda t: 260.0 if t < 60.0 else 250.0)
        self.assertAlmostEqual(est.fit_errors[0], 0.0, places=6)
        self.assertAlmostEqual(est.fit_errors[-1], 10.0, places=6)

    def test_without_truth_nothing_is_recorded(self):
        est = pm.RecordingEstimator()
        drive_east(est, lambda t: 80.0)
        self.assertGreater(est.calibrations, 0)
        self.assertEqual(est.fit_errors, [])


class LearningTests(unittest.TestCase):
    def test_settings_reach_the_learner_while_inside_only(self):
        seen = {}
        with pm._learning("long20-g0.5", seen):
            sim = pl.SlipRover([(500.0, 0.0)], seed=3, **pl.PROFILES["drift90"])
            est = pe.CountingEstimator()
        self.assertIs(seen["sim"], sim)
        self.assertIs(seen["est"], est)
        self.assertIsInstance(est, pm.RecordingEstimator)
        self.assertEqual((est.gain, est.min_move_m), (0.5, 20.0))
        self.assertEqual(est.truth(), -sim.compass_error)
        self.assertIs(pl.SlipRover, SLIP_ROVER)
        self.assertIs(pe.CountingEstimator, COUNTING)

    def test_restored_after_a_failure(self):
        with self.assertRaises(ValueError):
            with pm._learning("gain0.5", {}):
                raise ValueError("boom")
        self.assertIs(pl.SlipRover, SLIP_ROVER)
        self.assertIs(pe.CountingEstimator, COUNTING)


class FlyTests(unittest.TestCase):
    def test_shipped_flies_as_pace_l(self):
        for profile in ("outage90", "lie90"):
            with self.subTest(profile=profile):
                want = pl.fly("corner", 1, profile, "bridge120+cf0.3", 0.8, course=CORNER)
                got = pm.fly("corner", 1, profile, "shipped", 0.8, course=CORNER)
                fit = got.pop("fit_err")
                self.assertEqual(got, want)
                self.assertEqual(fit["n"], got["learner"]["calibrations"])
        self.assertIs(pl.SlipRover, SLIP_ROVER)
        self.assertIs(pe.CountingEstimator, COUNTING)
        self.assertNotIn("lie90", pj.PROFILES)
        self.assertNotIn("bridge120+cf0.3", pi.VARIANTS)

    def test_a_variant_flies_a_drifting_compass(self):
        r = pm.fly("far", 2, "drift90", "gain0.5", 0.8, course=FAR)
        self.assertTrue(r["ok"], r["reason"])
        self.assertGreaterEqual(r["fit_err"]["n"], 10)
        self.assertEqual(r["fit_err"]["n"], r["learner"]["calibrations"])
        self.assertIsNotNone(r["fit_err"]["rms_deg"])
        self.assertIs(pe.CountingEstimator, COUNTING)

    def test_failed_run_fields(self):
        r = pm.failed_run(ValueError("boom"))
        self.assertFalse(r["ok"])
        self.assertEqual(r["fit_err"]["n"], 0)
        self.assertIsNone(r["slip"])


class CheckTests(unittest.TestCase):
    def test_check_against_pace_l(self):
        with tiny_courses():
            ref = []
            for seed in (157, 158):
                r = pl.fly("tiny", seed, "outage90", "bridge120+cf0.3", 0.8)
                r.update(profile="outage90", variant="bridge120+cf0.3", cruise=0.8,
                         course="tiny", seed=seed)
                ref.append(r)
            ref[1]["elapsed_s"] += 1.0
            with tempfile.TemporaryDirectory() as d:
                path = os.path.join(d, "runs.jsonl")
                with open(path, "w", encoding="utf-8") as f:
                    for r in ref:
                        f.write(json.dumps(r) + "\n")
                    f.write("\n")
                out = pm.check_pace_l(path)
        # 2 profiles x 1 course x 3 seeds = 6 missions checked; the reference
        # has 2 of them, and seed 158 was altered.
        self.assertEqual((out["compared"], out["identical"], out["missing"]), (2, 1, 4))
        self.assertEqual(len(out["different"]), 1)
        self.assertEqual(out["different"][0]["seed"], 158)
        self.assertEqual(out["different"][0]["fields"], ["elapsed_s"])


def _run(variant, seed, elapsed, profile="outage90", fits=None):
    return {"profile": profile, "variant": variant, "cruise": 0.8, "course": "blocks",
            "seed": seed, "ok": True, "elapsed_s": elapsed, "time_s": {"stopped": 10.0},
            "outage": {"withheld": 4, "gps_resets": None}, "wander": {"wandered": 0},
            "slip": None, "fit_err": fits or {"n": 0, "median_abs_deg": None,
                                              "rms_deg": None, "mean_deg": None}}


class SummaryTests(unittest.TestCase):
    def test_pair_effects(self):
        runs = ([_run("shipped", s, 100.0) for s in range(1, 7)]
                + [_run("gain0.5", s, 90.0) for s in range(1, 7)])
        effects, tallies = pm.pair_effects(runs)
        self.assertIsNot(pi.PAIRS, pm.PAIRS)
        self.assertEqual(len(effects), 1)
        self.assertEqual((effects[0]["faster"], effects[0]["slower"]), (6, 0))
        self.assertEqual(tallies, [{"profile": "outage90", "variant": "gain0.5",
                                    "against": "shipped", "groups": 1, "groups_faster": 1,
                                    "groups_slower": 0, "groups_lost": 0, "groups_gained": 0,
                                    "largest_median_diff_share": -0.1}])

    def test_profile_effects(self):
        runs = ([_run("long20", s, 100.0) for s in range(1, 7)]
                + [_run("long20", s, 110.0, profile="drift90") for s in range(1, 7)])
        effects, tallies = pm.profile_effects(runs)
        self.assertEqual(pj.PROFILE_PAIRS, (("outage15", "wander15"), ("outage45", "wander45")))
        self.assertNotIn("long20", pj.VARIANTS)
        self.assertEqual(len(effects), 1)
        self.assertEqual(tallies[0]["groups_slower"], 1)
        self.assertEqual((tallies[0]["variant"], tallies[0]["profile"], tallies[0]["against"]),
                         ("long20", "drift90", "outage90"))

    def test_fit_rows(self):
        runs = [_run("shipped", s, 100.0, fits={"n": n, "median_abs_deg": m, "rms_deg": q,
                                                 "mean_deg": 0.0})
                for s, (n, m, q) in enumerate(((40, 5.0, 9.0), (50, 6.0, 10.0),
                                               (60, 7.0, 11.0)), 1)]
        runs.append(_run("gain0.5", 1, 100.0))
        self.assertEqual(pm.fit_rows(runs),
                         [{"profile": "outage90", "variant": "shipped", "cruise": 0.8,
                           "course": "blocks", "missions": 3, "median_fits": 50,
                           "median_abs_deg": 6.0, "rms_deg": 10.0}])

    def test_main_small(self):
        with tiny_courses():
            with tempfile.TemporaryDirectory() as d, redirect_stdout(io.StringIO()):
                pm.main(["--out-dir", d, "--first-seed", "181", "--seeds", "2",
                         "--profiles", "drift90", "--variants", "gain0.5"])
                with open(os.path.join(d, "summary.json")) as f:
                    out = json.load(f)
                with open(os.path.join(d, "report.md")) as f:
                    md = f.read()
                with open(os.path.join(d, "runs.jsonl")) as f:
                    lines = [json.loads(x) for x in f if x.strip()]
        # outage90 and shipped are always flown: 2 profiles x 2 variants x 2 seeds.
        self.assertEqual(out["runs"], 8)
        self.assertEqual(out["seeds"], [181, 182])
        self.assertEqual(sorted({r["profile"] for r in lines}), ["drift90", "outage90"])
        self.assertEqual(sorted({r["variant"] for r in lines}), ["gain0.5", "shipped"])
        self.assertTrue(all("fit_err" in r for r in lines))
        self.assertTrue(out["done"])
        self.assertEqual(sorted((v["profile"], v["variant"], v["against"])
                                for v in out["verdicts"]),
                         [("drift90", "gain0.5", "shipped"), ("outage90", "gain0.5", "shipped")])
        self.assertEqual(sorted((v["variant"], v["profile"], v["against"])
                                for v in out["profile_verdicts"]),
                         [("gain0.5", "drift90", "outage90"), ("shipped", "drift90", "outage90")])
        self.assertEqual(out["flown_as"], "bridge120+cf0.3")
        self.assertIsNone(out["check"])
        self.assertIn("## Error of each measurement the learner used", md)
        self.assertIn("Seeds 181-182.", md)
        self.assertIs(pl.SlipRover, SLIP_ROVER)
        self.assertIs(pe.CountingEstimator, COUNTING)


if __name__ == "__main__":
    unittest.main()
