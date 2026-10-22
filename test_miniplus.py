# Copyright 2026 Munim, Inc. Licensed under the Apache License, Version 2.0.
"""Tests for miniplus.py on synthetic Mini+ recordings with known conventions."""

import contextlib
import io
import json
import os
import tempfile
import unittest
from unittest import mock

import miniplus as mp

try:
    import pyarrow  # noqa: F401
    HAVE_ARROW = True
except ImportError:
    HAVE_ARROW = False

M_PER_DEG = 111195.0


def ep_turn():
    """20 s spinning left (angular +0.5) at 15 deg/s; orientation clockwise,
    held 2 s between updates, starting at 100 and wrapping through 0."""
    n = 200
    return {"episode": 0, "t": [k / 10.0 for k in range(n)],
            "linear": [0.0] * n, "angular": [0.5] * n,
            "orientation": [float((100 - 30 * (k // 20)) % 360) for k in range(n)],
            "gyro_x": [0.0] * n, "gyro_y": [0.0] * n, "gyro_z": [15.0] * n}


def ep_straight():
    """30 s straight north at 1 m/s, GPS updated every second, orientation 10,
    left wheels positive and right wheels negative."""
    n = 300
    return {"episode": 0, "t": [k / 10.0 for k in range(n)],
            "linear": [0.5] * n, "angular": [0.0] * n,
            "orientation": [10.0] * n,
            "lat": [37.0 + (k // 10) / M_PER_DEG for k in range(n)], "lon": [-122.0] * n,
            "rpm0": [100.0] * n, "rpm1": [100.0] * n, "rpm2": [-100.0] * n, "rpm3": [-100.0] * n}


class HelperTests(unittest.TestCase):
    def test_angles(self):
        self.assertAlmostEqual(mp.wrap180(350.0), -10.0)
        self.assertAlmostEqual(mp.wrap180(-190.0), 170.0)
        self.assertAlmostEqual(mp.bearing(37.0, -122.0, 37.001, -122.0), 0.0, places=6)
        self.assertAlmostEqual(mp.bearing(37.0, -122.0, 37.0, -121.999), 90.0, delta=0.01)
        self.assertAlmostEqual(mp.metres(37.0, -122.0, 37.0 + 10 / M_PER_DEG, -122.0), 10.0, delta=0.05)

    def test_unwrap(self):
        self.assertEqual(mp.unwrap([10.0, 350.0, 330.0, 10.0]), [10.0, -10.0, -30.0, 10.0])

    def test_valid_fix(self):
        self.assertTrue(mp.valid_fix(37.0, -122.0))
        self.assertFalse(mp.valid_fix(0.0, 0.0))
        self.assertFalse(mp.valid_fix(1000.0, 1000.0))
        self.assertFalse(mp.valid_fix(None, -122.0))

    def test_change_intervals(self):
        ts = [float(k) for k in range(8)]
        vals = [0, 0, 1, 1, 1, 2, 2, 3]
        self.assertEqual(mp.change_intervals(ts, vals), [3.0, 2.0])
        self.assertEqual(mp.change_intervals(ts, vals, keep=lambda i: i != 7), [3.0])

    def test_at(self):
        ts = [0.0, 0.1, 0.2]
        self.assertIsNone(mp.at(ts, -0.05))
        self.assertEqual(mp.at(ts, 0.1), 1)
        self.assertEqual(mp.at(ts, 5.0), 2)

    def test_pearson_and_circ_mean(self):
        self.assertAlmostEqual(mp.pearson([1, 2, 3], [2, 4, 6]), 1.0)
        self.assertIsNone(mp.pearson([1, 1, 1], [2, 4, 6]))
        self.assertAlmostEqual(mp.circ_mean([350.0, 10.0]) % 360.0, 0.0, delta=1e-6)


class TurnTests(unittest.TestCase):
    def test_left_turn_clockwise_orientation(self):
        wins = mp.turn_windows(ep_turn())
        self.assertGreaterEqual(len(wins), 3)
        for w in wins:
            self.assertLess(w["d_orient"], 0)
            self.assertAlmostEqual(abs(w["d_orient"]) / (w["cmd"] * w["seconds"]), 30.0, delta=1.5)
            self.assertAlmostEqual(w["gyro_z"], 15.0)

    def test_no_windows_without_turning(self):
        self.assertEqual(mp.turn_windows(ep_straight()), [])

    def test_mixed_sign_window_skipped(self):
        ep = ep_turn()
        ep["angular"] = [0.5 if (k // 5) % 2 else -0.5 for k in range(len(ep["t"]))]
        self.assertEqual(mp.turn_windows(ep), [])

    def test_no_orientation(self):
        ep = ep_turn()
        del ep["orientation"]
        self.assertEqual(mp.turn_windows(ep), [])


class CourseTests(unittest.TestCase):
    def test_pairs(self):
        pairs = mp.course_pairs(ep_straight())
        self.assertEqual(len(pairs), 5)
        for p in pairs:
            self.assertAlmostEqual(p["course"], 0.0, places=6)
            self.assertAlmostEqual(p["cw"], -10.0, places=6)
            self.assertAlmostEqual(p["ccw"], 10.0, places=6)
            self.assertAlmostEqual(p["metres"], 5.0, delta=0.05)

    def test_turning_spans_skipped(self):
        ep = ep_straight()
        ep["angular"] = [0.3] * len(ep["t"])
        self.assertEqual(mp.course_pairs(ep), [])

    def test_spread(self):
        by_ep = [[{"cw": 5.0}, {"cw": 15.0}], [{"cw": -100.0}]]
        spread, n = mp.spread_about_episode_offset(by_ep, "cw")
        self.assertEqual(n, 2)
        self.assertAlmostEqual(spread, 5.0, delta=0.01)


class WheelTests(unittest.TestCase):
    def test_signs_forward(self):
        sel = lambda lin, ang: lin >= 0.3 and abs(ang) < 0.1  # noqa: E731
        c = mp.wheel_signs(ep_straight(), sel)
        self.assertEqual(c["rpm0"], [290, 0, 0])
        self.assertEqual(c["rpm3"], [0, 290, 0])
        self.assertEqual(mp.all_same_sign_frames(ep_straight(), sel), (290, 0))

    def test_missing_wheels(self):
        sel = lambda lin, ang: True  # noqa: E731
        self.assertEqual(mp.wheel_signs(ep_turn(), sel), {})
        self.assertEqual(mp.all_same_sign_frames(ep_turn(), sel), (0, 0))


class AnalyseTests(unittest.TestCase):
    def setUp(self):
        self.res = mp.analyse([({"id": "a"}, [ep_turn()]), ({"id": "b"}, [ep_straight()]),
                               ({"id": "c", "skipped": "robot_type 'x'"}, [])])

    def test_counts(self):
        self.assertEqual(self.res["datasets"], 2)
        self.assertEqual(self.res["episodes"], 2)
        self.assertEqual(self.res["frames"], 500)

    def test_holds(self):
        self.assertEqual(self.res["orientation_hold_turning_s"], {"median": 2.0, "n": 8})
        self.assertEqual(self.res["gps_hold_s"]["median"], 1.0)
        self.assertEqual(self.res["orientation_min"], 10.0)
        self.assertEqual(self.res["orientation_max"], 340.0)
        self.assertEqual(self.res["orientation_integer_share"], 1.0)

    def test_turns(self):
        tw = self.res["turn_windows"]
        self.assertGreaterEqual(tw["n"], 3)
        self.assertEqual(tw["datasets"], 1)
        self.assertEqual(tw["share_clockwise"], 1.0)
        self.assertAlmostEqual(tw["deg_per_s_per_unit"], 30.0, delta=1.5)
        self.assertAlmostEqual(self.res["gyroscope"]["gyro_z"]["per_unit_cmd"], 30.0, delta=0.01)
        self.assertIsNone(self.res["gyroscope"]["gyro_x"]["r_with_orientation_rate"])

    def test_wheels_and_course(self):
        fw = self.res["wheels"]["forward"]
        self.assertEqual(fw["frames_all_nonzero"], 290)
        self.assertEqual(fw["share_one_sign"], 0.0)
        c = self.res["course"]
        self.assertEqual(c["pairs"], 5)
        self.assertEqual(c["raw_median_abs_cw"], 10.0)
        self.assertEqual(c["spread_cw"], 0.0)

    def test_decide_on_the_synthetic_data(self):
        dec = mp.decide(self.res)
        self.assertTrue(dec["D1"].startswith("too few turn windows"))
        self.assertTrue(dec["D2"].startswith("the wheels do not share a sign"))

    def test_report(self):
        text = mp.report([{"id": "a", "license": "apache-2.0", "episodes": 1, "frames": 200,
                           "fields": ["angular"]}, {"id": "c", "skipped": "robot_type 'x'"}],
                         self.res, mp.decide(self.res))
        self.assertIn("| a | apache-2.0 | 1 | 200 | angular |", text)
        self.assertIn("c: robot_type 'x'", text)
        self.assertIn("D2:", text)


def res_with(n, datasets, share, frames, one_sign):
    return {"turn_windows": {"n": n, "datasets": datasets, "share_clockwise": share},
            "wheels": {"forward": {"frames_all_nonzero": frames, "share_one_sign": one_sign}}}


class DecideTests(unittest.TestCase):
    def test_clockwise(self):
        self.assertTrue(mp.decide(res_with(12, 2, 0.9, 0, None))["D1"].startswith("clockwise"))

    def test_counter_clockwise(self):
        self.assertTrue(mp.decide(res_with(12, 2, 0.1, 0, None))["D1"].startswith("counter-clockwise"))

    def test_mixed(self):
        self.assertTrue(mp.decide(res_with(12, 3, 0.5, 0, None))["D1"].startswith("mixed"))

    def test_one_dataset_is_not_enough(self):
        self.assertTrue(mp.decide(res_with(40, 1, 1.0, 0, None))["D1"].startswith("too few"))

    def test_wheels(self):
        self.assertTrue(mp.decide(res_with(0, 0, None, 60, 0.95))["D2"].startswith("all four"))
        self.assertTrue(mp.decide(res_with(0, 0, None, 60, 0.5))["D2"].startswith("the wheels do not"))
        self.assertTrue(mp.decide(res_with(0, 0, None, 49, 1.0))["D2"].startswith("too few"))


class ReadTests(unittest.TestCase):
    def test_columns(self):
        info = {"features": {"observation.state": {"names": ["speed", "battery_level", "orientation",
                                                            "gps_latitude", "gps_longitude", "wheel_rpm_0"]},
                             "action": {"names": ["linear_velocity", "angular_velocity"]}}}
        cols = mp.columns(info)
        self.assertEqual(cols["orientation"], ("observation.state", 2))
        self.assertEqual(cols["rpm0"], ("observation.state", 5))
        self.assertEqual(cols["angular"], ("action", 1))
        info2 = {"features": {"observation.state": {"names": {"motors": ["linear.vel", "orientation.deg",
                                                                         "gps.latitude"]}},
                              "action": {"names": ["linear.vel", "angular.vel"]}}}
        cols2 = mp.columns(info2)
        self.assertEqual(cols2["orientation"], ("observation.state", 1))
        self.assertEqual(cols2["lat"], ("observation.state", 2))
        self.assertIsNone(mp.columns({"features": {"action": {"names": ["x.vel"]}}}))

    def test_episodes_from_rows(self):
        cols = {"orientation": ("observation.state", 0), "lat": ("observation.state", 1),
                "linear": ("action", 0), "angular": ("action", 1)}
        rows = [{"episode_index": 0, "frame_index": f, "observation.state": [float(f), None if f == 1 else 37.0],
                 "action": [0.5, 0.0]} for f in (2, 0, 1)]
        rows.append({"episode_index": 1, "frame_index": 0, "observation.state": [5.0, 37.0], "action": [0.1, 0.2]})
        eps = mp.episodes_from_rows(rows, cols, 10)
        self.assertEqual(len(eps), 2)
        self.assertEqual(eps[0]["t"], [0.0, 0.1, 0.2])
        self.assertEqual(eps[0]["orientation"], [0.0, 1.0, 2.0])
        self.assertNotIn("lat", eps[0])
        self.assertEqual(eps[1]["angular"], [0.2])

    @unittest.skipUnless(HAVE_ARROW, "pyarrow not installed")
    def test_read_parquet(self):
        import pyarrow as pa
        import pyarrow.parquet as pq
        t = pa.table({"episode_index": [0, 0], "frame_index": [0, 1], "timestamp": [0.0, 0.1],
                      "observation.state": [[1.0, 2.0], [3.0, 4.0]], "action": [[0.5, 0.0], [0.5, 0.1]],
                      "other": [1, 2]})
        buf = io.BytesIO()
        pq.write_table(t, buf)
        rows = mp.read_parquet(buf.getvalue())
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[1]["observation.state"], [3.0, 4.0])
        self.assertNotIn("other", rows[0])


class MainTests(unittest.TestCase):
    def test_main_writes_outputs(self):
        loaded = {"a": ({"id": "a", "license": "apache-2.0", "episodes": 1, "frames": 200}, [ep_turn()]),
                  "b": ({"id": "b", "license": "not stated", "episodes": 1, "frames": 300}, [ep_straight()])}
        with tempfile.TemporaryDirectory() as d:
            with mock.patch.object(mp, "load_dataset", side_effect=lambda ds, log: loaded[ds]):
                with contextlib.redirect_stdout(io.StringIO()):
                    code = mp.main(["--out-dir", d, "--datasets", "a,b"])
            self.assertEqual(code, 0)
            with open(os.path.join(d, "summary.json"), encoding="utf-8") as f:
                s = json.load(f)
            self.assertEqual(s["version"], mp.__version__)
            self.assertEqual(s["results"]["datasets"], 2)
            self.assertIn("D1", s["decisions"])
            self.assertTrue(os.path.exists(os.path.join(d, "report.md")))


if __name__ == "__main__":
    unittest.main()
