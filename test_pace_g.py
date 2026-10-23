"""Tests for the study of dead reckoning and --smooth-heading together.

Run: python -m unittest test_pace_g -v
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

import dead_reckon as dr  # noqa: E402
import pace_d as pd  # noqa: E402
import pace_f as pf  # noqa: E402
import pace_g as pg  # noqa: E402
import pace_study as ps  # noqa: E402
import rover_pilot as rp  # noqa: E402

TINY = {"points": [(0.0, 0.0), (30.0, 0.0)], "checkpoints": [1]}
STRAIGHT = {"points": [(0.0, 0.0), (200.0, 0.0)], "checkpoints": [1]}
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
        m = pf.PROFILES["measured"]
        wheels = {"wheel_mps_per_rpm": dr.MINI_PLUS_MPS_PER_RPM}
        self.assertEqual(list(pg.PROFILES),
                         ["measured", "noise6", "noise8", "dropout0.3", "dropout0.3-noise8",
                          "wheels0.85"])
        want = {"measured": {}, "noise6": {"compass_noise_deg": 6.0},
                "noise8": {"compass_noise_deg": 8.0}, "dropout0.3": {"gps_dropout": 0.3},
                "dropout0.3-noise8": {"gps_dropout": 0.3, "compass_noise_deg": 8.0},
                "wheels0.85": {"wheel_mps_per_rpm": 0.85 * dr.MINI_PLUS_MPS_PER_RPM}}
        for name, change in want.items():
            with self.subTest(profile=name):
                self.assertEqual(pg.PROFILES[name], dict(m, **dict(wheels, **change)))
        # pace_f.py's noise6, with wheels.
        self.assertEqual(pg.PROFILES["noise6"], dict(pf.PROFILES["noise6"], **wheels))
        self.assertEqual(pg.BASE_PROFILE, "measured")

    def test_variants(self):
        self.assertEqual(list(pg.VARIANTS), ["dr+cf0.3", "dr", "cf0.3", "plain"])
        self.assertEqual(pg.VARIANTS["dr+cf0.3"],
                         {"dead_reckon": True, "smooth": rp.SMOOTH_HEADING})
        self.assertEqual(pg.VARIANTS["dr"], {"dead_reckon": True})
        self.assertEqual(pg.VARIANTS["cf0.3"], {"smooth": rp.SMOOTH_HEADING})
        self.assertEqual(pg.VARIANTS["plain"], {})
        self.assertEqual(pg.BASE_VARIANT, "dr+cf0.3")
        self.assertEqual(pg.PAIRS, (("dr", "dr+cf0.3"), ("cf0.3", "dr+cf0.3"),
                                    ("plain", "dr"), ("plain", "cf0.3")))
        for name in pg.CHECKED["variants"]:
            self.assertIn(pg.PACE_F_NAMES[name], pf.VARIANTS)
        self.assertEqual(pg.CRUISES, (0.8,))
        self.assertEqual(pg.FIRST_SEED, 37)
        self.assertEqual(pg.POSITION_EVERY_S, 1.0)

    def test_rovers_report_their_wheels(self):
        r = pd.DistortedRover([(40.0, 0.0)], seed=1, **pg.PROFILES["wheels0.85"])
        r.control(1.0, 0.0)
        r.sleep(1.0)
        rows = r.data()["rpms"]
        self.assertTrue(rows)
        left, right = rows[-1][0], rows[-1][1]
        self.assertEqual(left, right)
        self.assertAlmostEqual(left, (4.0 / 3.6) / (0.85 * dr.MINI_PLUS_MPS_PER_RPM), delta=0.01)


class FlyTests(unittest.TestCase):
    def test_flies_as_pace_f(self):
        for profile, variant, seed in (("measured", "plain", 1), ("noise6", "cf0.3", 2)):
            with self.subTest(profile=profile, variant=variant):
                want = pf.fly("corner", seed, profile, pg.PACE_F_NAMES[variant], 0.8,
                              course=CORNER)
                got = pg.fly("corner", seed, profile, variant, 0.8, course=CORNER)
                self.assertTrue(want["ok"], want["reason"])
                for k in want:
                    self.assertEqual(got[k], want[k], k)
                self.assertIsNone(got["dead_reckon"])
                self.assertGreater(got["position_err"]["n"], 0)

    def test_dead_reckoning_flies(self):
        for profile in ("measured", "dropout0.3-noise8"):
            for variant in ("dr+cf0.3", "dr"):
                with self.subTest(profile=profile, variant=variant):
                    r = pg.fly("corner", 1, profile, variant, 0.8, course=CORNER)
                    self.assertTrue(r["ok"], r["reason"])
                    self.assertEqual(r["reached"], 2)
                    for key in ("trusted", "trusted_at_s", "learned_scale", "bridged_s",
                                "scale_samples", "scale_rejects", "mps_per_rpm"):
                        self.assertIn(key, r["dead_reckon"])

    def test_dead_reckoning_knows_better_where_it_is(self):
        reckoned = pg.fly("straight", 1, "measured", "dr", 0.8, course=STRAIGHT)
        plain = pg.fly("straight", 1, "measured", "plain", 0.8, course=STRAIGHT)
        self.assertTrue(reckoned["ok"], reckoned["reason"])
        self.assertTrue(plain["ok"], plain["reason"])
        self.assertIsNotNone(reckoned["dead_reckon"]["trusted_at_s"])
        self.assertLess(reckoned["dead_reckon"]["trusted_at_s"], 200.0)
        self.assertLess(reckoned["position_err"]["median_m"], plain["position_err"]["median_m"])

    def test_wheel_size_is_learned(self):
        r = pg.fly("straight", 2, "wheels0.85", "dr", 0.8, course=STRAIGHT)
        self.assertTrue(r["ok"], r["reason"])
        d = r["dead_reckon"]
        self.assertGreaterEqual(d["scale_samples"], 2)
        # Unlearned it would be 1 / 0.85, about 1.18.
        self.assertLess(abs(d["learned_scale"] - 1.0), 0.15)

    def test_position_error(self):
        sim = types.SimpleNamespace(lat0=37.87, lon0=-122.25, north=1.0, east=2.0)
        pos = rp.offset_latlon(37.87, -122.25, 4.0, 6.0)
        self.assertAlmostEqual(pg.position_error(pos, sim), 5.0, places=6)
        self.assertIsNone(pg.position_error(None, sim))
        self.assertIsNone(pg.position_error((None, None), sim))

    def test_failed_run_fields(self):
        r = pg.failed_run(ValueError("boom"))
        self.assertFalse(r["ok"])
        self.assertEqual(r["reason"], "ValueError: boom")
        self.assertIsNone(r["learner"])
        self.assertIsNone(r["dead_reckon"])
        self.assertEqual(r["position_err"]["n"], 0)


class CheckTests(unittest.TestCase):
    def test_check_against_pace_f(self):
        with tiny_courses():
            ref = []
            for seed in (13, 14):
                r = pf.fly("tiny", seed, "measured", "shipped", 0.8)
                r.update(profile="measured", variant="shipped", cruise=0.8, course="tiny",
                         seed=seed)
                ref.append(r)
            ref[1]["elapsed_s"] += 1.0
            with tempfile.TemporaryDirectory() as d:
                path = os.path.join(d, "runs.jsonl")
                with open(path, "w", encoding="utf-8") as f:
                    for r in ref:
                        f.write(json.dumps(r) + "\n")
                    f.write("\n")
                out = pg.check_pace_f(path)
        # 2 profiles x 2 variants x 1 course x 3 seeds = 12 missions checked; the
        # reference has 2 of them, and seed 14 was altered.
        self.assertEqual((out["compared"], out["identical"], out["missing"]), (2, 1, 10))
        self.assertEqual(len(out["different"]), 1)
        self.assertEqual(out["different"][0]["seed"], 14)
        self.assertEqual(out["different"][0]["variant"], "plain")
        self.assertEqual(out["different"][0]["fields"], ["elapsed_s"])


def _run(variant, seed, elapsed, ok=True, course="blocks", dead_reckon=None):
    return {"profile": "measured", "variant": variant, "cruise": 0.8, "course": course,
            "seed": seed, "ok": ok, "elapsed_s": elapsed, "dead_reckon": dead_reckon}


class SummaryTests(unittest.TestCase):
    def test_pair_effects(self):
        runs = ([_run("dr", s, 100.0) for s in range(1, 7)]
                + [_run("dr+cf0.3", s, 90.0) for s in range(1, 7)]
                + [_run("dr", s, 100.0, course="bayside") for s in range(1, 7)]
                + [_run("dr+cf0.3", s, 110.0, ok=s != 6, course="bayside")
                   for s in range(1, 7)])
        effects, tallies = pg.pair_effects(runs)
        self.assertEqual([(e["course"], e["against"]) for e in effects],
                         [("bayside", "dr"), ("blocks", "dr")])
        blocks = effects[1]
        self.assertEqual((blocks["faster"], blocks["slower"]), (6, 0))
        self.assertEqual(blocks["median_time_diff_share"], -0.1)
        self.assertLess(blocks["sign_test_p"], 0.05)
        # bayside: 5 slower is not enough for p < 0.05; one mission lost.
        self.assertEqual(effects[0]["median_time_diff_share"], 0.1)
        self.assertEqual(tallies, [{"profile": "measured", "variant": "dr+cf0.3",
                                    "against": "dr", "groups": 2, "groups_faster": 1,
                                    "groups_slower": 0, "groups_lost": 1, "groups_gained": 0,
                                    "largest_median_diff_share": 0.1}])

    def test_dr_rows(self):
        def rec(at):
            return {"trusted": at is not None, "trusted_at_s": at, "scale_samples": 4,
                    "scale_rejects": 0, "bridged_s": 2.0, "learned_scale": 0.98}

        runs = [_run("dr", s, 100.0, dead_reckon=rec(at))
                for s, at in ((1, 40.0), (2, 60.0), (3, None))] + [_run("plain", 1, 100.0)]
        self.assertEqual(pg.dr_rows(runs),
                         [{"profile": "measured", "variant": "dr", "cruise": 0.8,
                           "course": "blocks", "missions": 3, "trusted_missions": 2,
                           "never_trusted": 1, "median_trusted_at_s": 60.0,
                           "median_scale_samples": 4, "median_scale_rejects": 0,
                           "median_bridged_s": 2.0, "median_abs_scale_error": 0.02}])

    def test_median_or_never(self):
        self.assertEqual(pg._median_or_never([None, 5.0, 3.0]), 5.0)
        self.assertIsNone(pg._median_or_never([None, None, 5.0]))
        self.assertIsNone(pg._median_or_never([]))

    def test_main_small(self):
        with tiny_courses():
            with tempfile.TemporaryDirectory() as d, redirect_stdout(io.StringIO()):
                pg.main(["--out-dir", d, "--first-seed", "37", "--seeds", "2",
                         "--profiles", "noise8", "--variants", "dr,plain"])
                with open(os.path.join(d, "summary.json")) as f:
                    out = json.load(f)
                with open(os.path.join(d, "report.md")) as f:
                    md = f.read()
                with open(os.path.join(d, "runs.jsonl")) as f:
                    lines = [json.loads(x) for x in f if x.strip()]
        # measured and dr+cf0.3 are always flown: 2 profiles x 3 variants x 2 seeds.
        self.assertEqual(out["runs"], 12)
        self.assertEqual(out["seeds"], [37, 38])
        self.assertEqual(sorted({r["seed"] for r in lines}), [37, 38])
        self.assertTrue(out["done"])
        self.assertEqual(sorted((v["profile"], v["variant"], v["against"])
                                for v in out["verdicts"]),
                         [("measured", "dr", "plain"), ("measured", "dr+cf0.3", "dr"),
                          ("noise8", "dr", "plain"), ("noise8", "dr+cf0.3", "dr")])
        self.assertEqual(len(out["position"]), 6)
        self.assertEqual(len(out["reckoner"]), 4)
        self.assertEqual(len(out["learner"]), 6)
        self.assertIsNone(out["check"])
        self.assertIn("## Dead reckoning", md)
        self.assertIn("Seeds 37-38.", md)


if __name__ == "__main__":
    unittest.main()
