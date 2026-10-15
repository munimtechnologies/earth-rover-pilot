"""Tests for frodo_frames 0.2.0's helpers. Run: python -m unittest test_frodo_frames -v"""

import math
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import free_space  # noqa: E402
import frodo_frames as ff  # noqa: E402

RPM = 90.0  # 90 * 0.00668 = 0.6012 m/s
V = RPM * ff.MPS_PER_RPM


def control(n=200, start=100.0, angular_from=None, angular=0.0, stop_from=None):
    """Rows every 0.1 s: driving straight at 0.6, optionally turning or stopping from a time."""
    rows = []
    for k in range(n):
        t = start + k / 10.0
        lin, ang, rpm = 0.6, 0.0, RPM
        if angular_from is not None and t >= angular_from - 1e-9:
            ang = angular
        if stop_from is not None and t >= stop_from - 1e-9:
            lin, rpm = 0.0, 0.0
        rows.append((t, lin, ang, [rpm, rpm, rpm, rpm]))
    return rows, [r[0] for r in rows]


class HelperTests(unittest.TestCase):
    def test_seg_time_is_utc(self):
        t = ff.seg_time("x/abc_ride_18397__uid_s_1000__uid_e_video_20240215043203990.ts")
        self.assertAlmostEqual(t, 1707971523.99, places=3)
        self.assertIsNone(ff.seg_time("playlist.m3u8"))

    def test_stream_and_ride(self):
        self.assertEqual(ff.stream_of("abc__uid_s_1000__uid_e_video_17.ts"),
                         ("abc__uid_s_1000__uid_e_video_", 17))
        self.assertEqual(ff.ride_key("output_rides_1/ride_123_20240115083000/recordings/a.ts"),
                         "output_rides_1/ride_123_20240115083000")

    def test_wheel_speed(self):
        self.assertAlmostEqual(ff.wheel_speed((0, 0.6, 0, [90, 90, 90, 90])), V)
        self.assertAlmostEqual(ff.wheel_speed((0, 0.5, 0, [None] * 4)), 0.5 * 0.79)
        self.assertAlmostEqual(ff.wheel_speed((0, 0.0, 0.5, [-60, 60, -60, 60])), 0.0)
        self.assertAlmostEqual(ff.wheel_motion((0, 0.0, 0.5, [-60, 60, -60, 60])),
                               60 * ff.MPS_PER_RPM)

    def test_wilson(self):
        self.assertIsNone(ff.wilson(0, 0))
        lo, hi = ff.wilson(5, 10)
        self.assertLess(lo, 0.5)
        self.assertGreater(hi, 0.5)


class DriveAheadTests(unittest.TestCase):
    def test_straight_until_the_horizon(self):
        ctl, times = control()
        d = ff.drive_ahead(ctl, times, 101.0)
        self.assertEqual(d["ended"], "horizon")
        self.assertAlmostEqual(d["dist_m"], 15.0 * V, delta=0.2)

    def test_a_turn_ends_it(self):
        ctl, times = control(angular_from=105.0, angular=0.5)
        d = ff.drive_ahead(ctl, times, 101.0)
        self.assertEqual(d["ended"], "turn")
        self.assertAlmostEqual(d["dist_m"], 4.0 * V, delta=0.1)

    def test_a_stop_ends_it(self):
        ctl, times = control(stop_from=104.0)
        d = ff.drive_ahead(ctl, times, 101.0)
        self.assertEqual(d["ended"], "stop")
        self.assertAlmostEqual(d["dist_m"], 3.0 * V, delta=0.1)

    def test_a_slow_curve_ends_it(self):
        # 0.1 angular is under the 0.15 limit, but at 30 deg/s it adds up to 20 deg in 6.7 s.
        ctl, times = control(angular_from=100.0, angular=0.1)
        d = ff.drive_ahead(ctl, times, 101.0)
        self.assertEqual(d["ended"], "curve")
        self.assertAlmostEqual(d["dist_m"], (20.0 / 3.0) * V, delta=0.15)

    def test_no_control_data_near_the_frame(self):
        ctl, times = control()
        self.assertIsNone(ff.drive_ahead(ctl, times, 200.0))
        self.assertIsNone(ff.drive_ahead(ctl, times, 50.0))
        self.assertIsNone(ff.drive_ahead([], [], 100.0))

    def test_events(self):
        ctl, times = control(stop_from=102.0)
        self.assertTrue(ff.events(ctl, times, 101.5)["event"])
        self.assertTrue(ff.events(ctl, times, 101.5)["stopped_after"])
        ctl, times = control()
        self.assertFalse(ff.events(ctl, times, 101.5)["event"])


class ClockLagTests(unittest.TestCase):
    def test_finds_the_offset(self):
        def motion(ride, t):
            return math.sin(t / 3.0) + 1.5
        samples = [("r", t * 1.3, motion("r", t * 1.3 + 1.0)) for t in range(150)]
        table, best = ff.clock_lag(samples, motion)
        self.assertEqual(best, 1.0)
        self.assertAlmostEqual(table[1.0]["r"], 1.0, places=3)

    def test_too_few_samples(self):
        table, best = ff.clock_lag([("r", 1.0, 2.0)], lambda ride, t: 1.0)
        self.assertIsNone(best)


class VariantTests(unittest.TestCase):
    def test_open_ground_is_clear_for_every_variant(self):
        cam = free_space.Camera()
        frame = free_space.render(cam, [])
        for name, v in ff.VARIANTS.items():
            self.assertEqual(ff.check_variant(frame, cam, v)["clear"], 8.0, name)

    def test_hedge_ahead_is_seen_by_every_variant(self):
        cam = free_space.Camera()
        frame = free_space.render(cam, [(0.0, 3.0, 0.6, 1.0, free_space.HEDGE_GREEN)])
        for name, v in ff.VARIANTS.items():
            self.assertLess(ff.check_variant(frame, cam, v)["clear"], 3.5, name)

    def test_image_change(self):
        cam = free_space.Camera()
        a = free_space.render(cam, [])
        self.assertEqual(ff.image_change(a, a), 0.0)
        b = free_space.render(cam, [(0.0, 3.0, 0.6, 1.0, free_space.HEDGE_GREEN)])
        self.assertGreater(ff.image_change(a, b), 0.0)

    def test_summarise(self):
        def frame(dist, clear, event=False):
            return {"drive": {"dist_m": dist, "ended": "horizon"},
                    "events": {"event": event},
                    "variants": {name: {"clear": clear, "cols": 0} for name in ff.VARIANTS}}
        frames = [frame(8.0, 0.53), frame(8.0, 8.0), frame(3.0, 1.0), frame(1.0, 0.5, True)]
        s = ff.summarise(frames)["default"]
        self.assertEqual(s["drove_2m"], 3)
        self.assertEqual(s["phantom_stops"], 2)          # 0.53 and 1.0 with 8 m and 3 m driven
        self.assertEqual(s["drove_5_5m"], 2)
        self.assertEqual(s["phantom_swerves"], 1)
        self.assertEqual(s["agrees_with_driver"], round(1 / 3, 3))
        self.assertEqual(s["event_frames"], 1)
        self.assertEqual(s["blocked_on_event_frames"], 1.0)


if __name__ == "__main__":
    unittest.main()
