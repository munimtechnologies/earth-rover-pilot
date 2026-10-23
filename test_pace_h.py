"""Tests for the study of whether dead reckoning stays on by default.

Run: python -m unittest test_pace_h -v
"""

import io
import json
import os
import sys
import tempfile
import types
import unittest
from contextlib import redirect_stdout

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pace_g as pg  # noqa: E402
import pace_h as ph  # noqa: E402
import pace_study as ps  # noqa: E402
import rover_pilot as rp  # noqa: E402

TINY = {"points": [(0.0, 0.0), (30.0, 0.0)], "checkpoints": [1]}
LONG = {"points": [(0.0, 0.0), (400.0, 0.0)], "checkpoints": [1]}
CORNER = {"points": [(0.0, 0.0), (40.0, 0.0), (40.0, 40.0)], "checkpoints": [1, 2]}


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
        self.assertEqual(list(ph.PROFILES),
                         ["measured", "noise8", "dropout0.3", "dropout0.3-noise8"])
        for name, settings in ph.PROFILES.items():
            with self.subTest(profile=name):
                self.assertEqual(settings, pg.PROFILES[name])
        self.assertEqual(ph.BASE_PROFILE, "measured")

    def test_variants(self):
        self.assertEqual(list(ph.VARIANTS),
                         ["dr+cf0.3", "cf0.3", "bridge+cf0.3", "drg0.3+cf0.3", "dr+cf0.3+kb"])
        self.assertEqual(ph.VARIANTS["dr+cf0.3"], pg.VARIANTS["dr+cf0.3"])
        self.assertEqual(ph.VARIANTS["cf0.3"], pg.VARIANTS["cf0.3"])
        for name in ("bridge+cf0.3", "drg0.3+cf0.3", "dr+cf0.3+kb"):
            v = ph.VARIANTS[name]
            self.assertTrue(v["dead_reckon"])
            self.assertEqual(v["smooth"], rp.SMOOTH_HEADING)
        self.assertTrue(ph.VARIANTS["bridge+cf0.3"]["bridge"])
        self.assertEqual(ph.VARIANTS["drg0.3+cf0.3"]["reckoner"], {"gain": 0.3})
        self.assertTrue(ph.VARIANTS["dr+cf0.3+kb"]["known_bias"])
        self.assertEqual(ph.BASE_VARIANT, "dr+cf0.3")
        for a, b in ph.PAIRS:
            self.assertIn(a, ph.VARIANTS)
            self.assertIn(b, ph.VARIANTS)
        self.assertEqual(len(ph.PAIRS), 7)
        self.assertEqual(ph.CRUISES, (0.8,))
        self.assertEqual(ph.FIRST_SEED, 61)
        self.assertEqual(ph.CHECKED, {"profiles": ("measured", "dropout0.3"),
                                      "variants": ("dr+cf0.3", "cf0.3"),
                                      "seeds": (37, 38, 39)})

    def test_known_bias(self):
        sim = types.SimpleNamespace(compass_error=-25.0)
        est, given = ph.make_estimator("dr+cf0.3+kb", sim)
        self.assertEqual((est.bias, est.calibrations, given), (25.0, 1, 1))
        est, given = ph.make_estimator("cf0.3", sim)
        self.assertEqual((est.bias, est.calibrations, given), (0.0, 0, 0))


class _Gps:
    def __init__(self, fresh):
        self.fresh = fresh
        self.lat, self.lon, self.raw = 3.0, 4.0, (3.0, 4.0)

    def has_fix(self, t):
        return self.fresh


class _Reckoner:
    def __init__(self, pos):
        self.pos = pos
        self.asked = 0

    def position(self, t):
        self.asked += 1
        return self.pos


class BridgePilotTests(unittest.TestCase):
    def pilot(self, fresh, pos):
        p = ph.BridgePilot.__new__(ph.BridgePilot)
        p.gps, p.dr, p.lag = _Gps(fresh), _Reckoner(pos), None
        return p

    def test_gps_while_it_has_a_fix(self):
        p = self.pilot(True, (1.0, 2.0))
        self.assertEqual(p._position(10.0), (3.0, 4.0))
        self.assertEqual(p.dr.asked, 1)  # still stepped every tick

    def test_wheels_through_a_gap(self):
        self.assertEqual(self.pilot(False, (1.0, 2.0))._position(10.0), (1.0, 2.0))

    def test_gps_when_the_wheels_have_nothing(self):
        self.assertEqual(self.pilot(False, None)._position(10.0), (3.0, 4.0))

    def test_without_dead_reckoning(self):
        p = self.pilot(True, None)
        p.dr = None
        self.assertEqual(p._position(10.0), (3.0, 4.0))


class FlyTests(unittest.TestCase):
    def test_flies_as_pace_g(self):
        for profile, variant, seed in (("measured", "dr+cf0.3", 1), ("measured", "cf0.3", 2),
                                       ("dropout0.3", "dr+cf0.3", 3)):
            with self.subTest(profile=profile, variant=variant):
                want = pg.fly("corner", seed, profile, variant, 0.8, course=CORNER)
                got = ph.fly("corner", seed, profile, variant, 0.8, course=CORNER)
                self.assertTrue(want["ok"], want["reason"])
                for k in want:
                    self.assertEqual(got[k], want[k], k)
                self.assertGreater(got["steer"]["n"], 0)
                self.assertIsNotNone(got["steer"]["mean_abs_angular"])

    def test_bridge_is_cf03_without_gaps(self):
        same = 0
        for seed in (1, 2, 3):
            bridge = ph.fly("corner", seed, "measured", "bridge+cf0.3", 0.8, course=CORNER)
            plain = ph.fly("corner", seed, "measured", "cf0.3", 0.8, course=CORNER)
            self.assertTrue(bridge["ok"], bridge["reason"])
            if bridge["dead_reckon"]["bridged_s"] == 0.0:
                same += 1
                for k in plain:
                    if k != "dead_reckon":
                        self.assertEqual(bridge[k], plain[k], k)
        self.assertGreater(same, 0)

    def test_bridge_drives_through_gaps(self):
        r = ph.fly("long", 1, "dropout0.3", "bridge+cf0.3", 0.8, course=LONG)
        self.assertTrue(r["ok"], r["reason"])
        self.assertIsNotNone(r["dead_reckon"]["trusted_at_s"])
        self.assertGreater(r["dead_reckon"]["bridged_s"], 0.0)

    def test_other_variants_fly(self):
        for variant in ("drg0.3+cf0.3", "dr+cf0.3+kb"):
            with self.subTest(variant=variant):
                r = ph.fly("corner", 1, "measured", variant, 0.8, course=CORNER)
                self.assertTrue(r["ok"], r["reason"])
                self.assertEqual(r["reached"], 2)
                self.assertIn("learned_scale", r["dead_reckon"])
                self.assertGreaterEqual(r["learner"]["calibrations"], 0)

    def test_known_bias_starts_right(self):
        r = ph.fly("corner", 1, "measured", "dr+cf0.3+kb", 0.8, course=CORNER)
        self.assertLess(abs(r["learner"]["bias_error_deg"]), 10.0)

    def test_failed_run_fields(self):
        r = ph.failed_run(ValueError("boom"))
        self.assertFalse(r["ok"])
        self.assertIsNone(r["dead_reckon"])
        self.assertEqual(r["steer"], {"n": 0, "mean_abs_angular": None})


class CheckTests(unittest.TestCase):
    def test_check_against_pace_g(self):
        with tiny_courses():
            ref = []
            for seed in (37, 38):
                r = pg.fly("tiny", seed, "measured", "cf0.3", 0.8)
                r.update(profile="measured", variant="cf0.3", cruise=0.8, course="tiny",
                         seed=seed)
                ref.append(r)
            ref[1]["elapsed_s"] += 1.0
            with tempfile.TemporaryDirectory() as d:
                path = os.path.join(d, "runs.jsonl")
                with open(path, "w", encoding="utf-8") as f:
                    for r in ref:
                        f.write(json.dumps(r) + "\n")
                    f.write("\n")
                out = ph.check_pace_g(path)
        # 2 profiles x 2 variants x 1 course x 3 seeds = 12 missions checked; the
        # reference has 2 of them, and seed 38 was altered.
        self.assertEqual((out["compared"], out["identical"], out["missing"]), (2, 1, 10))
        self.assertEqual(len(out["different"]), 1)
        self.assertEqual(out["different"][0]["seed"], 38)
        self.assertEqual(out["different"][0]["variant"], "cf0.3")
        self.assertEqual(out["different"][0]["fields"], ["elapsed_s"])


def _run(variant, seed, elapsed, ok=True, course="blocks", steer=None):
    return {"profile": "measured", "variant": variant, "cruise": 0.8, "course": course,
            "seed": seed, "ok": ok, "elapsed_s": elapsed,
            "steer": {"n": 10, "mean_abs_angular": steer}}


class SummaryTests(unittest.TestCase):
    def test_pair_effects(self):
        runs = ([_run("dr+cf0.3", s, 100.0) for s in range(1, 7)]
                + [_run("bridge+cf0.3", s, 90.0) for s in range(1, 7)]
                + [_run("dr+cf0.3", s, 100.0, course="bayside") for s in range(1, 7)]
                + [_run("bridge+cf0.3", s, 110.0, ok=s != 6, course="bayside")
                   for s in range(1, 7)])
        effects, tallies = ph.pair_effects(runs)
        self.assertEqual([(e["course"], e["against"]) for e in effects],
                         [("bayside", "dr+cf0.3"), ("blocks", "dr+cf0.3")])
        blocks = effects[1]
        self.assertEqual((blocks["faster"], blocks["slower"]), (6, 0))
        self.assertEqual(blocks["median_time_diff_share"], -0.1)
        self.assertLess(blocks["sign_test_p"], 0.05)
        self.assertEqual(effects[0]["median_time_diff_share"], 0.1)
        self.assertEqual(tallies, [{"profile": "measured", "variant": "bridge+cf0.3",
                                    "against": "dr+cf0.3", "groups": 2, "groups_faster": 1,
                                    "groups_slower": 0, "groups_lost": 1, "groups_gained": 0,
                                    "largest_median_diff_share": 0.1}])

    def test_steer_rows(self):
        runs = ([_run("cf0.3", s, 100.0, steer=x) for s, x in ((1, 0.1), (2, 0.3), (3, None))]
                + [_run("cf0.3", 4, None, ok=False, steer=0.5)])
        self.assertEqual(ph.steer_rows(runs),
                         [{"profile": "measured", "variant": "cf0.3", "cruise": 0.8,
                           "course": "blocks", "missions": 2,
                           "median_mean_abs_angular": 0.2}])

    def test_main_small(self):
        with tiny_courses():
            with tempfile.TemporaryDirectory() as d, redirect_stdout(io.StringIO()):
                ph.main(["--out-dir", d, "--first-seed", "61", "--seeds", "2",
                         "--profiles", "noise8", "--variants", "bridge+cf0.3"])
                with open(os.path.join(d, "summary.json")) as f:
                    out = json.load(f)
                with open(os.path.join(d, "report.md")) as f:
                    md = f.read()
                with open(os.path.join(d, "runs.jsonl")) as f:
                    lines = [json.loads(x) for x in f if x.strip()]
        # measured and dr+cf0.3 are always flown: 2 profiles x 2 variants x 2 seeds.
        self.assertEqual(out["runs"], 8)
        self.assertEqual(out["seeds"], [61, 62])
        self.assertEqual(sorted({r["seed"] for r in lines}), [61, 62])
        self.assertTrue(out["done"])
        self.assertEqual(sorted((v["profile"], v["variant"], v["against"])
                                for v in out["verdicts"]),
                         [("measured", "bridge+cf0.3", "dr+cf0.3"),
                          ("noise8", "bridge+cf0.3", "dr+cf0.3")])
        self.assertEqual(len(out["position"]), 4)
        self.assertEqual(len(out["reckoner"]), 4)
        self.assertEqual(len(out["steer"]), 4)
        self.assertEqual(len(out["learner"]), 4)
        self.assertIsNone(out["check"])
        self.assertIn("## How hard the pilot steers", md)
        self.assertIn("Seeds 61-62.", md)


if __name__ == "__main__":
    unittest.main()
