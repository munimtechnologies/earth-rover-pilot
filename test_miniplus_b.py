# Copyright 2026 Munim, Inc. Licensed under the Apache License, Version 2.0.
"""Tests for miniplus_b.py on synthetic Mini+ recordings with known conventions."""

import contextlib
import io
import json
import os
import tempfile
import unittest
from unittest import mock

import miniplus_b as mb


def ep_turn(cmd=0.5, step=-2.0, gyro=20.0, n=100):
    """10 fps, linear 0.3 with angular `cmd`; orientation moves `step` degrees a
    frame (from 100, wrapping through 0); gyro_z alternates gyro, gyro + 1."""
    return {"episode": 0, "fps": 10, "t": [k / 10.0 for k in range(n)],
            "linear": [0.3] * n, "angular": [cmd] * n,
            "orientation": [float((100 + step * k) % 360) for k in range(n)],
            "gyro_x": [0.0] * n, "gyro_z": [gyro + (k % 2) for k in range(n)]}


def ep_forward(right_sign=1.0, n=50):
    """10 fps straight ahead; rpm0 = rpm2 alternate 100, 102; rpm1 = rpm3 = 110
    (times right_sign); speed is the wheels' speed in km/h at 95 mm."""
    r0 = [100.0 + 2 * (k % 2) for k in range(n)]
    r1 = [110.0 * right_sign] * n
    speed = [(2 * a + 2 * b) / 4.0 * mb.MPS_PER_RPM * 3.6 for a, b in zip(r0, r1)]
    return {"episode": 0, "fps": 10, "t": [k / 10.0 for k in range(n)],
            "linear": [0.5] * n, "angular": [0.0] * n, "orientation": [10.0] * n,
            "rpm0": r0, "rpm1": r1, "rpm2": list(r0), "rpm3": list(r1), "speed": speed}


def ep_spin(cmd, n=30):
    """10 fps spinning in place; the side the turn is towards reads -50, the
    other 50 or 51 (rpm1 is the right-hand side)."""
    hi = [50.0 + (k % 2) for k in range(n)]
    lo = [-50.0] * n
    r0, r1 = (lo, hi) if cmd > 0 else (hi, lo)
    return {"episode": 0, "fps": 10, "t": [k / 10.0 for k in range(n)],
            "linear": [0.0] * n, "angular": [cmd] * n,
            "rpm0": r0, "rpm1": r1, "rpm2": list(r0), "rpm3": list(r1)}


class HelperTests(unittest.TestCase):
    def test_angles(self):
        self.assertAlmostEqual(mb.wrap180(350.0), -10.0)
        self.assertEqual(mb.unwrap([10.0, 350.0, 330.0, 10.0]), [10.0, -10.0, -30.0, 10.0])

    def test_valid_fix(self):
        self.assertTrue(mb.valid_fix(37.0, -122.0))
        self.assertFalse(mb.valid_fix(1000.0, 1000.0))
        self.assertFalse(mb.valid_fix(0.0, 0.0))

    def test_slope_and_pearson(self):
        self.assertAlmostEqual(mb.slope([1.0, 2.0, 3.0], [2.0, 4.0, 6.0]), 2.0)
        self.assertIsNone(mb.slope([1.0, 1.0, 1.0], [1.0, 2.0, 3.0]))
        self.assertAlmostEqual(mb.pearson([1, 2, 3], [3, 2, 1]), -1.0)

    def test_live(self):
        self.assertTrue(mb.live({"a": [1.0, 2.0]}, "a"))
        self.assertFalse(mb.live({"a": [0.0, 0.0]}, "a"))
        self.assertFalse(mb.live({}, "a"))

    def test_frames(self):
        self.assertEqual(mb.frames(10, 0.5), 5)
        self.assertEqual(mb.frames(4, 0.5), 2)
        self.assertEqual(mb.frames(2, 2.0), 4)


class WindowTests(unittest.TestCase):
    def test_left_turn_clockwise(self):
        ws = mb.windows(ep_turn())
        self.assertEqual(len(ws), 4)
        for w in ws:
            self.assertTrue(mb.qualifies(w))
            self.assertEqual(w["d"], -40.0)
            self.assertEqual(w["rate"], -20.0)
            self.assertAlmostEqual(w["gyro_z"], 431.0 / 21.0)
            self.assertNotIn("gyro_x", w)  # constant: a missing sensor

    def test_lag(self):
        n = 26
        ep = {"fps": 10, "t": [k / 10.0 for k in range(n)], "linear": [0.0] * n, "angular": [0.5] * n,
              "orientation": [0.0] * 5 + [10.0] * 20 + [50.0]}
        ws = mb.windows(ep)
        self.assertEqual(len(ws), 1)
        self.assertEqual(ws[0]["d"], 40.0)  # read from frame 5 to frame 25

    def test_signs(self):
        ep = ep_turn()
        ep["angular"] = [0.5 if (k // 5) % 2 else -0.5 for k in range(100)]
        self.assertFalse(any(mb.qualifies(w) for w in mb.windows(ep)))
        ep["angular"] = [0.5 if k % 4 else 0.0 for k in range(100)]
        self.assertTrue(all(mb.qualifies(w) for w in mb.windows(ep)))

    def test_small_change_or_command(self):
        ep = ep_turn(step=-0.1)
        self.assertFalse(any(mb.qualifies(w) for w in mb.windows(ep)))  # 2 degrees a window
        ep = ep_turn(cmd=0.1)
        self.assertFalse(any(mb.qualifies(w) for w in mb.windows(ep)))

    def test_no_orientation(self):
        self.assertEqual(mb.windows(ep_spin(0.8)), [])


class WheelTests(unittest.TestCase):
    def test_held(self):
        ep = ep_forward()
        ep["linear"] = [0.5] * 6 + [0.0] * 44
        self.assertTrue(mb.held(ep, 10, mb.forward))
        self.assertFalse(mb.held(ep, 11, mb.forward))
        self.assertFalse(mb.held(ep, 9, mb.forward))

    def test_forward(self):
        c = mb.wheels(ep_forward())
        self.assertEqual(c["moving"], 50)
        self.assertEqual(c["duplicated"], 50)
        self.assertEqual(c["forward"], 40)
        self.assertEqual(c["forward_all_nonzero"], 40)
        self.assertEqual(c["forward_one_sign"], 40)
        self.assertEqual(c["forward_all_positive"], 40)
        self.assertEqual(len(c["speed_ratios"]), 50)
        for r in c["speed_ratios"]:
            self.assertAlmostEqual(r, 1.0, places=9)

    def test_opposite_sides(self):
        c = mb.wheels(ep_forward(right_sign=-1.0))
        self.assertEqual(c["forward_one_sign"], 0)
        self.assertEqual(c["speed_ratios"], [])

    def test_spins(self):
        left = mb.wheels(ep_spin(0.8))
        self.assertEqual((left["left"], left["left_rpm1_higher"], left["right"]), (20, 20, 0))
        right = mb.wheels(ep_spin(-0.8))
        self.assertEqual((right["right"], right["right_rpm0_higher"], right["left"]), (20, 20, 0))

    def test_no_wheels(self):
        self.assertIsNone(mb.wheels(ep_turn()))
        ep = ep_forward()
        ep["rpm0"] = ep["rpm2"] = [100.0] * 50
        ep["rpm1"] = ep["rpm3"] = [110.0] * 50
        self.assertIsNone(mb.wheels(ep))  # constant wheels: not a reading

    def test_refresh(self):
        n = 50
        ep = {"fps": 10, "t": [k / 10.0 for k in range(n)], "orientation": [10.0 * (k // 5) for k in range(n)]}
        self.assertEqual(mb.refresh_intervals(ep, ("orientation", "speed")), [0.5] * 8)
        self.assertEqual(mb.refresh_intervals(ep, ("speed",)), [])


class AnalyseTests(unittest.TestCase):
    def setUp(self):
        self.res = mb.analyse([({"id": "a"}, [ep_turn(), ep_forward()]),
                               ({"id": "b"}, [ep_turn(cmd=-0.5, step=2.0, gyro=-20.0), ep_spin(0.8), ep_spin(-0.8)]),
                               ({"id": "c", "skipped": "robot_type 'x'"}, [])])
        self.p = self.res["pooled"]

    def test_counts(self):
        self.assertEqual(self.p["datasets"], 2)
        self.assertEqual(self.p["episodes"], 5)
        self.assertEqual(self.p["frames"], 310)
        self.assertEqual(sorted(self.res["per_dataset"]), ["a", "b"])

    def test_turns(self):
        t = self.p["turns"]
        self.assertEqual((t["qualifying"], t["clockwise"], t["counter_clockwise"]), (8, 8, 0))
        self.assertEqual(t["share_clockwise"], 1.0)
        self.assertEqual(t["deg_per_s_per_unit"], 40.0)
        self.assertAlmostEqual(t["slope_deg_per_s_per_unit"], -40.0)
        self.assertEqual(self.p["turn_datasets"], 2)
        self.assertEqual(self.res["per_dataset"]["a"]["turns"]["qualifying"], 4)

    def test_gyroscope(self):
        g = self.p["gyroscope"]
        self.assertEqual(g["gyro_z"]["n"], 8)
        self.assertAlmostEqual(g["gyro_z"]["r_with_orientation_rate"], -1.0, places=3)
        self.assertAlmostEqual(g["gyro_z"]["over_orientation_rate"], -1.0, delta=0.01)
        self.assertEqual(g["gyro_x"]["n"], 0)
        self.assertIsNone(g["gyro_x"]["r_with_orientation_rate"])

    def test_wheels(self):
        w = self.p["wheels"]
        self.assertEqual(w["moving"], 110)
        self.assertEqual(w["duplicated_share"], 1.0)
        self.assertEqual(w["forward_all_nonzero"], 40)
        self.assertEqual(w["forward_one_sign_share"], 1.0)
        self.assertEqual(w["left_rpm1_higher_share"], 1.0)
        self.assertEqual(w["right_rpm0_higher_share"], 1.0)
        self.assertEqual(w["speed_ratio"]["n"], 50)
        self.assertEqual(w["speed_ratio"]["median"], 1.0)

    def test_gps_and_refresh(self):
        self.assertEqual(self.p["gps"], {"frames": 0, "valid_share": None})
        self.assertEqual(self.res["per_dataset"]["a"]["orientation_change_s"]["median"], 0.1)
        ep = ep_forward()
        ep["lat"], ep["lon"] = [1000.0] * 50, [1000.0] * 50
        self.assertEqual(mb.summarise([ep])["gps"], {"frames": 50, "valid_share": 0.0})

    def test_decide(self):
        dec = mb.decide(self.res)
        self.assertTrue(dec["D1"].startswith("too few turn windows (8 from 2"))
        self.assertTrue(dec["D2"].startswith("all four"))
        self.assertTrue(dec["D3"].startswith("speed (km/h) matches"))

    def test_report(self):
        meta = [{"id": "a", "license": "apache-2.0", "fps": 10, "episodes": 2, "frames": 150,
                 "live_fields": ["orientation"]}, {"id": "c", "skipped": "robot_type 'x'"}]
        text = mb.report(meta, self.res, mb.decide(self.res))
        self.assertIn("| a | apache-2.0 | 10 | 2 | 150 | orientation |", text)
        self.assertIn("c: robot_type 'x'", text)
        self.assertIn("D3:", text)

    def test_empty(self):
        p = mb.analyse([])["pooled"]
        self.assertEqual(p["turns"]["qualifying"], 0)
        self.assertIsNone(p["wheels"])
        dec = mb.decide({"pooled": p})
        self.assertTrue(dec["D2"].startswith("too few"))
        self.assertTrue(dec["D3"].startswith("too few"))


def res_with(q, datasets, share, fwd, one_sign, ratio_n=0, ratio=None):
    w = {"forward_all_nonzero": fwd, "forward_one_sign_share": one_sign,
         "speed_ratio": {"median": ratio, "n": ratio_n}}
    return {"pooled": {"turns": {"qualifying": q, "share_clockwise": share}, "turn_datasets": datasets,
                       "wheels": w}}


class DecideTests(unittest.TestCase):
    def test_d1(self):
        self.assertTrue(mb.decide(res_with(30, 2, 0.8, 0, None))["D1"].startswith("clockwise"))
        self.assertTrue(mb.decide(res_with(30, 2, 0.2, 0, None))["D1"].startswith("counter-clockwise"))
        self.assertTrue(mb.decide(res_with(30, 3, 0.5, 0, None))["D1"].startswith("mixed"))
        self.assertTrue(mb.decide(res_with(29, 2, 1.0, 0, None))["D1"].startswith("too few"))
        self.assertTrue(mb.decide(res_with(90, 1, 1.0, 0, None))["D1"].startswith("too few"))

    def test_d2(self):
        self.assertTrue(mb.decide(res_with(0, 0, None, 30, 0.9))["D2"].startswith("all four"))
        self.assertTrue(mb.decide(res_with(0, 0, None, 30, 0.89))["D2"].startswith("the wheels do not"))
        self.assertTrue(mb.decide(res_with(0, 0, None, 29, 1.0))["D2"].startswith("too few"))

    def test_d3(self):
        self.assertTrue(mb.decide(res_with(0, 0, None, 0, None, 50, 0.95))["D3"].startswith("speed (km/h)"))
        self.assertTrue(mb.decide(res_with(0, 0, None, 0, None, 50, 3.4))["D3"].startswith("speed and wheels"))
        self.assertTrue(mb.decide(res_with(0, 0, None, 0, None, 49, 1.0))["D3"].startswith("too few"))


class ReadTests(unittest.TestCase):
    def test_columns(self):
        ecot = {"features": {"observation.state": {"names": ["linear.vel", "angular.vel", "battery.level",
                                                            "orientation.deg", "gps.latitude", "gps.longitude",
                                                            "imu.gyro.x", "imu.gyro.y", "imu.gyro.z"]},
                             "action": {"names": ["linear.vel", "angular.vel"]}}}
        c = mb.columns(ecot)
        self.assertEqual(c["orientation"], ("observation.state", 3))
        self.assertEqual(c["gyro_z"], ("observation.state", 8))
        self.assertEqual(c["linear"], ("action", 0))
        scout = {"features": {"observation.state": {"names": ["battery", "latitude", "longitude", "orientation",
                                                             "speed", "gyro_x", "gyro_y", "gyro_z"]},
                              "action": {"names": ["linear", "angular", "lamp"]}}}
        c = mb.columns(scout)
        self.assertEqual(c["lat"], ("observation.state", 1))
        self.assertEqual(c["gyro_x"], ("observation.state", 5))
        self.assertEqual(c["angular"], ("action", 1))
        self.assertIsNone(mb.columns({"features": {"action": {"names": ["x.vel"]}}}))

    def test_episodes_from_rows(self):
        cols = {"orientation": ("observation.state", 0), "lat": ("observation.state", 1),
                "linear": ("action", 0), "angular": ("action", 1)}
        rows = [{"episode_index": 0, "frame_index": f, "observation.state": [float(f), None if f == 1 else 37.0],
                 "action": [0.5, 0.0]} for f in (2, 0, 1)]
        eps = mb.episodes_from_rows(rows, cols, 4)
        self.assertEqual(eps[0]["t"], [0.0, 0.25, 0.5])
        self.assertEqual(eps[0]["fps"], 4)
        self.assertEqual(eps[0]["orientation"], [0.0, 1.0, 2.0])
        self.assertNotIn("lat", eps[0])


class MainTests(unittest.TestCase):
    def test_main_writes_outputs(self):
        loaded = {"a": ({"id": "a", "license": "apache-2.0", "fps": 10, "episodes": 1, "frames": 100,
                         "live_fields": ["orientation"]}, [ep_turn()]),
                  "b": ({"id": "b", "skipped": "robot_type 'x'"}, [])}
        with tempfile.TemporaryDirectory() as d:
            with mock.patch.object(mb, "load_dataset", side_effect=lambda ds, log: loaded[ds]):
                with contextlib.redirect_stdout(io.StringIO()):
                    code = mb.main(["--out-dir", d, "--datasets", "a,b"])
            self.assertEqual(code, 0)
            with open(os.path.join(d, "summary.json"), encoding="utf-8") as f:
                s = json.load(f)
            self.assertEqual(s["version"], mb.__version__)
            self.assertEqual(s["skipped"], 1)
            self.assertEqual(s["results"]["pooled"]["datasets"], 1)
            self.assertIn("D3", s["decisions"])
            self.assertTrue(os.path.exists(os.path.join(d, "report.md")))


if __name__ == "__main__":
    unittest.main()
