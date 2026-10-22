# Copyright 2026 Munim, Inc. Licensed under the Apache License, Version 2.0.
"""--smooth-heading (rover_pilot 0.12.0): HeadingSmoother, pace_c.py's
complementary filter moved inside the pilot, off by default (studies/pace-c/GRADE.md, D1).

Run: python -m unittest test_smooth_heading -v
"""
import contextlib
import io
import json
import math
import os
import tempfile
import unittest

import pace_b as pb
import pace_c as pc
import pace_study as ps
import rover_pilot as rp

# A short course with a right-angle corner, so the turn prediction matters.
CORNER = {"points": [(0.0, 0.0), (40.0, 0.0), (40.0, 40.0)], "checkpoints": [1, 2]}


def fly_inside(course, seed, profile, cruise, smoother):
    """pace_c.fly's mission with the smoothing done by the pilot instead of a
    wrapper around the rover; the same fields as pace_c.fly."""
    pts = course["points"]
    sim = pb.MeasuredRover([pts[i] for i in course["checkpoints"]], seed=seed,
                           **pc.PROFILES[profile])
    planner = ps.CoursePlanner(course, sim.lat0, sim.lon0)
    pilot = rp.Pilot(sim, clock=sim.clock, sleep=sim.sleep,
                     steering=rp.make_steering(False, cruise=cruise), planner=planner,
                     smooth_heading=smoother)
    total_m = ps.route_m(course)
    ideal_mps = cruise * sim.max_speed_mps
    res = pilot.run(timeout_s=3.0 * total_m / ideal_mps + 300.0)
    reached = len(res["reached"])
    done_m = ps.route_m(course, upto=reached)
    elapsed = res["elapsed_s"]
    made_good = done_m / elapsed if elapsed else 0.0
    return {"ok": res["ok"], "reason": res["reason"], "elapsed_s": elapsed,
            "reached": reached, "checkpoints": res["checkpoints"], "reports": res["reports"],
            "recoveries": res["recoveries"], "plans": res["plans"],
            "route_m": round(done_m, 1), "travelled_m": round(sim.travelled, 1),
            "made_good_mps": round(made_good, 4), "ideal_mps": round(ideal_mps, 4),
            "efficiency": round(made_good / ideal_mps, 4),
            "time_s": {k: round(x, 1) for k, x in sim.time_in.items()}}


def run_main(argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = rp.main(argv)
    return code, out.getvalue()


class SmootherTests(unittest.TestCase):
    def test_settings_are_the_studys(self):
        self.assertEqual(rp.SMOOTH_HEADING, {"gain": 0.3, "yaw_dps": 48.0, "lag_s": 0.5})
        self.assertEqual(rp.SMOOTH_HEADING, pc.VARIANTS["cf0.3"])

    def test_gain_one_returns_the_reading(self):
        s = rp.HeadingSmoother(gain=1.0)
        self.assertEqual(s.update(0.0, 10.0, 0.0), 10.0)
        self.assertEqual(s.update(0.5, 50.0, 0.5), 50.0)
        self.assertEqual(s.update(1.0, 90.0, 1.0), 90.0)

    def test_average_moves_part_of_the_way(self):
        s = rp.HeadingSmoother(gain=0.5, yaw_dps=0.0)
        self.assertEqual(s.update(0.0, 0.0, 0.0), 0.0)
        self.assertEqual(s.update(0.5, 40.0, 0.5), 20.0)
        self.assertEqual(s.update(1.0, 40.0, 1.0), 30.0)
        self.assertEqual(s.readings, 3)

    def test_across_north(self):
        s = rp.HeadingSmoother(gain=0.5, yaw_dps=0.0)
        s.update(0.0, 350.0, 0.0)
        # 10 is 20 deg clockwise of 350: half way is 0, not 180.
        self.assertEqual(s.update(0.5, 10.0, 0.5), 0.0)

    def test_held_while_the_timestamp_stays(self):
        s = rp.HeadingSmoother(gain=0.5, yaw_dps=0.0)
        s.update(0.0, 0.0, 0.0)
        s.update(0.5, 40.0, 0.5)
        self.assertEqual(s.update(0.7, 90.0, 0.5), 20.0)
        self.assertEqual(s.readings, 2)

    def test_without_a_timestamp_a_new_value_is_a_new_reading(self):
        s = rp.HeadingSmoother(gain=0.5, yaw_dps=0.0)
        s.update(0.0, 0.0)
        self.assertEqual(s.update(0.1, 0.0), 0.0)
        self.assertEqual(s.readings, 1)
        self.assertEqual(s.update(0.2, 40.0), 20.0)
        self.assertEqual(s.readings, 2)

    def test_turned_by_the_command(self):
        s = rp.HeadingSmoother(gain=0.3, yaw_dps=48.0, lag_s=0.5)
        s.update(0.0, 100.0, 0.0)
        s.record(0.0, 1.0)  # sent at 0 s, turning from 0.5 s
        # Commands landing in [0, 1.0]: 1.0 s at full angular, 48 deg. The reading
        # agrees with the prediction, so the estimate is the reading: no lag.
        self.assertEqual(s.update(1.5, 148.0, 1.5), 148.0)

    def test_a_left_turn_lowers_the_prediction(self):
        s = rp.HeadingSmoother(gain=0.3, yaw_dps=48.0, lag_s=0.5)
        s.update(0.0, 100.0, 0.0)
        s.record(0.0, -0.5)
        self.assertEqual(s.update(1.5, 76.0, 1.5), 76.0)

    def test_plain_average_lags_the_turn(self):
        s = rp.HeadingSmoother(gain=0.3, yaw_dps=0.0)
        s.update(0.0, 100.0, 0.0)
        s.record(0.0, 1.0)
        self.assertAlmostEqual(s.update(1.5, 148.0, 1.5), 114.4, places=9)

    def test_no_reading_changes_nothing(self):
        s = rp.HeadingSmoother(gain=0.5, yaw_dps=0.0)
        self.assertIsNone(s.update(0.0, None, 0.0))
        self.assertEqual(s.readings, 0)
        s.update(0.5, 40.0, 0.5)
        self.assertIsNone(s.update(1.0, None, 1.0))
        self.assertEqual(s.update(1.5, 0.0, 1.5), 20.0)

    def test_old_commands_dropped(self):
        s = rp.HeadingSmoother()
        for t in (0.0, 5.0, 20.0):
            s.record(t, 0.5)
        self.assertEqual(len(s._cmds), 2)

    def test_stats(self):
        s = rp.HeadingSmoother(**rp.SMOOTH_HEADING)
        s.update(0.0, 10.0, 0.0)
        self.assertEqual(s.stats(), {"gain": 0.3, "yaw_dps": 48.0, "lag_s": 0.5, "readings": 1})


class FakeRover:
    def __init__(self):
        self.sent = []

    def control(self, linear, angular):
        self.sent.append((linear, angular))


class PilotTests(unittest.TestCase):
    def test_off_by_default(self):
        rover = rp.SimRover(rp.DEMO_MISSION, seed=2)
        pilot = rp.Pilot(rover, clock=rover.clock, sleep=rover.sleep)
        self.assertIsNone(pilot.smoother)
        res = pilot.run()
        self.assertTrue(res["ok"])
        self.assertNotIn("smooth_heading", res)

    def test_records_the_pilots_own_angular(self):
        s = rp.HeadingSmoother()
        rover = FakeRover()
        pilot = rp.Pilot(rover, clock=lambda: 3.0, sleep=lambda x: None,
                         conventions=rp.Conventions(angular_right_positive=False),
                         smooth_heading=s)
        pilot.send(0.5, 0.25)
        # The rover gets a left-positive angular; the smoother keeps the pilot's.
        self.assertEqual(rover.sent, [(0.5, -0.25)])
        self.assertEqual(list(s._cmds), [(3.0, 0.25)])

    def test_flies_exactly_as_the_study(self):
        # pace_c.py smoothed the rover's reports in a wrapper; the pilot's own
        # smoother has to give the very same missions.
        for variant in ("cf0.3", "cf0.3-yaw30", "ema0.3"):
            for profile in ("measured", "measured-noise10"):
                for seed in (1, 2):
                    with self.subTest(variant=variant, profile=profile, seed=seed):
                        want = pc.fly("corner", seed, profile, variant, 0.8, course=CORNER)
                        got = fly_inside(CORNER, seed, profile, 0.8,
                                         rp.HeadingSmoother(**pc.VARIANTS[variant]))
                        self.assertTrue(want["ok"], want)
                        self.assertEqual(got, want)

    def test_result_reports_the_smoother(self):
        rover = rp.SimRover(rp.DEMO_MISSION, seed=3)
        pilot = rp.Pilot(rover, clock=rover.clock, sleep=rover.sleep,
                         smooth_heading=rp.HeadingSmoother(**rp.SMOOTH_HEADING))
        res = pilot.run()
        self.assertTrue(res["ok"], res["reason"])
        self.assertEqual(res["smooth_heading"]["yaw_dps"], 48.0)
        self.assertGreater(res["smooth_heading"]["readings"], 100)

    def test_quirky_rover_with_its_conventions(self):
        rover = rp.SimRover(rp.DEMO_MISSION, seed=1, **rp.SIM_QUIRKS)
        conv = rp.Conventions(orientation_scale=256.0, orientation_clockwise=False,
                              angular_right_positive=False)
        pilot = rp.Pilot(rover, clock=rover.clock, sleep=rover.sleep, conventions=conv,
                         smooth_heading=rp.HeadingSmoother(**rp.SMOOTH_HEADING))
        res = pilot.run()
        self.assertTrue(res["ok"], res["reason"])


class MakeSmootherTests(unittest.TestCase):
    def test_default_rate(self):
        self.assertEqual(rp.make_smoother().stats()["yaw_dps"], 48.0)
        self.assertEqual(rp.make_smoother({"ok": True}).stats()["yaw_dps"], 48.0)

    def test_calibrated_rate(self):
        s = rp.make_smoother({"ok": True, "yaw_dps_at_full": 30.5})
        self.assertEqual(s.stats(), {"gain": 0.3, "yaw_dps": 30.5, "lag_s": 0.5, "readings": 0})

    def test_bad_rates_ignored(self):
        for bad in ("fast", -5.0, 0.0, float("nan"), float("inf"), None, [30]):
            with self.subTest(bad=bad):
                s = rp.make_smoother({"ok": True, "yaw_dps_at_full": bad})
                self.assertEqual(s.yaw_dps, 48.0)


class CommandLineTests(unittest.TestCase):
    def test_off_unless_asked(self):
        code, text = run_main(["--simulate", "--seed", "2"])
        self.assertEqual(code, 0, text[-500:])
        self.assertNotIn('"smooth_heading"', text)

    def test_flag_in_the_simulator(self):
        code, text = run_main(["--simulate", "--seed", "2", "--smooth-heading"])
        self.assertEqual(code, 0, text[-500:])
        self.assertEqual(json.loads(text)["smooth_heading"]["yaw_dps"], 48.0)

    def test_rate_from_the_calibration(self):
        cal = {"ok": True, "orientation_scale": 360.0, "orientation_clockwise": True,
               "angular_right_positive": True, "bias_deg": 0.0, "yaw_dps_at_full": 55.0}
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "rover.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(cal, f)
            code, text = run_main(["--simulate", "--seed", "2", "--smooth-heading",
                                   "--calibration", path])
        self.assertEqual(code, 0, text[-500:])
        self.assertEqual(json.loads(text)["smooth_heading"]["yaw_dps"], 55.0)

    def test_help(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            with self.assertRaises(SystemExit):
                rp.main(["--help"])
        text = " ".join(out.getvalue().split())
        self.assertIn("--smooth-heading", text)
        self.assertIn("default: off", text)


if __name__ == "__main__":
    unittest.main()
