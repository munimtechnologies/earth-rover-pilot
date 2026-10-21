"""Tests for frodo_odometry, on simulated rides whose true path is known."""

import csv
import io
import json
import math
import os
import tempfile
import unittest
import zipfile

import frodo_motion as fm
import frodo_odometry as fo

START = 1715000000.0
LAT0, LON0 = 37.0, -122.0
M_PER_DEG = math.pi / 180.0 * fm.R_EARTH
K = 30.0     # the simulated rover turns this many deg/s per unit of angular, like odo_cmd30
BIAS = 0.8   # gyroscope offset


def to_latlon(e, n):
    return LAT0 + n / M_PER_DEG, LON0 + e / (M_PER_DEG * math.cos(math.radians(LAT0)))


def synthetic_ride(schedule):
    """Control at 10 Hz, gyroscope and GPS at 1 Hz, for a rover following
    schedule [(seconds, linear, angular)]: every wheel at linear / 0.8 x 100 RPM,
    turning K deg/s per unit of angular CMD_LAG_S after the command. The
    gyroscope reads the turn rate (counter-clockwise) plus BIAS; each fix shows
    exactly where the rover was GPS_LAG_S earlier."""
    cmds = []
    for dur, lin, ang in schedule:
        cmds += [(lin, ang)] * int(round(dur / 0.1))
    lag = int(round(fo.CMD_LAG_S / 0.1))
    control, rates, truth = [], [], [(0.0, 0.0)]
    e = n = psi = 0.0
    for i, (lin, ang) in enumerate(cmds):
        rpm = lin / 0.8 * 100.0
        control.append((START + i * 0.1, lin, ang, [rpm] * 4))
        w = K * (cmds[i - lag][1] if i >= lag else 0.0)
        rates.append(w)
        v = rpm * fo.MPS_PER_RPM
        for _ in range(10):
            mid = math.radians(psi - w * 0.005)
            e += v * 0.01 * math.sin(mid)
            n += v * 0.01 * math.cos(mid)
            psi -= w * 0.01
            truth.append((e, n))
    secs = len(cmds) // 10
    gyro = [(START + m + 0.37, rates[10 * m + 3] + BIAS, 0.0, 0.0) for m in range(secs)]
    gps = []
    for j in range(2, secs - 1):
        pe, pn = truth[100 * j + 30 - int(round(fo.GPS_LAG_S * 100))]
        lat, lon = to_latlon(pe, pn)
        gps.append((START + j + 0.3, round(lat, 8), round(lon, 8)))
    return control, gps, gyro


class HelperTests(unittest.TestCase):
    def test_nearest(self):
        times = [0.0, 1.0, 2.5]
        self.assertEqual(fo.nearest(times, 1.2, 0.5), 1)
        self.assertEqual(fo.nearest(times, 2.1, 0.5), 2)
        self.assertEqual(fo.nearest(times, -0.3, 0.5), 0)
        self.assertIsNone(fo.nearest(times, 1.75, 0.5))
        self.assertIsNone(fo.nearest([], 1.0, 0.5))

    def test_fresh_fixes(self):
        gps = [(0.0, 37.0, -122.0), (1.0, 37.0, -122.0), (2.0, 37.00001, -122.0)]
        fixes = fo.fresh_fixes(gps)
        self.assertEqual([f[0] for f in fixes], [0.0, 2.0])
        self.assertAlmostEqual(fixes[1][2], 1.112, places=2)

    def test_grid_and_dead_reckon(self):
        control = [(START + i * 0.1, 0.8, 0.5, [100.0] * 4) for i in range(100)]
        gyro = [(START + m + 0.37, BIAS, 0.0, 0.0) for m in range(10)]
        grid = fo.Grid(control, gyro)
        self.assertEqual(grid.n, 50)
        self.assertAlmostEqual(grid.v[10], 0.668, places=9)
        self.assertAlmostEqual(grid.gyro_bias, BIAS)
        self.assertAlmostEqual(grid.yaw["gyro"][-1], 0.0, places=9)
        # Commands shift 0.5 s later: cells 0 and 1 get none, cell 2 one row, 3 to 49 two.
        self.assertAlmostEqual(grid.yaw["cmd"][-1], 4.8, places=6)
        east = fo.dead_reckon(grid, "none", 0.0, 90.0, 0.0, 0, [5, 10])
        self.assertAlmostEqual(east[0][0], 0.668, places=9)
        self.assertAlmostEqual(east[1][0], 1.336, places=9)
        self.assertAlmostEqual(east[1][1], 0.0, places=9)

    def test_guards(self):
        st = fo.analyse_ride([(START, 0.0, 0.0, [0.0] * 4)] * 10, [(START, LAT0, LON0)], [],
                             fo.new_pool())
        self.assertEqual(st["skipped"], "too little data")
        control, gps, _ = synthetic_ride([(60, 0.8, 0.0)])
        pool = fo.new_pool()
        st = fo.analyse_ride(control, gps, [], pool)
        self.assertEqual(st["skipped"], "no gyroscope")
        self.assertEqual(pool["per_ride"], [])


class StraightTests(unittest.TestCase):
    """A rover driving straight at 0.668 m/s for 300 s, with exact GPS."""

    @classmethod
    def setUpClass(cls):
        cls.pool = fo.new_pool()
        control, gps, gyro = synthetic_ride([(300, 0.8, 0.0)])
        cls.st = fo.analyse_ride(control, gps, gyro, cls.pool, ride="s")
        cls.s = fo.summarise(cls.pool)

    def test_anchors(self):
        self.assertNotIn("skipped", self.st)
        self.assertTrue(90 <= self.st["anchors"] <= 99, self.st)
        self.assertAlmostEqual(self.st["gyro_bias"], BIAS)

    def test_misses(self):
        rows = self.s["table"]
        for h in (1, 5, 10, 30):
            self.assertAlmostEqual(fo.find(rows, "hold", h)["median_m"], 0.668 * h, delta=0.01)
            for name in ("gps_cv", "odo_course", "odo_gyro", "odo_gyro_flip", "odo_cmd30"):
                self.assertLess(fo.find(rows, name, h)["median_m"], 0.03, (name, h))
        self.assertIsNone(fo.find(rows, "hold", 10, "turning"))
        self.assertIsNone(self.s["best_cmd_gain_10s_turning"])


class TurnTests(unittest.TestCase):
    """Rovers turning 150 deg left and right between 30 s straights, with exact GPS."""

    @classmethod
    def setUpClass(cls):
        cls.pool = fo.new_pool()
        cls.stats = []
        cycle = [(30, 0.8, 0.0), (10, 0.8, 0.5), (30, 0.8, 0.0), (10, 0.8, -0.5)] * 4
        for i in range(3):
            control, gps, gyro = synthetic_ride([(10 + 7 * i, 0.8, 0.0)] + cycle)
            cls.stats.append(fo.analyse_ride(control, gps, gyro, cls.pool, ride=str(i)))
        cls.s = fo.summarise(cls.pool)

    def test_bias(self):
        for st in self.stats:
            self.assertAlmostEqual(st["gyro_bias"], BIAS)

    def test_heading_sources(self):
        rows = self.s["table"]
        for h, cmd_max in ((5, 0.6), (10, 1.0)):
            m = {n: fo.find(rows, n, h, "turning")["median_m"] for n in fo.NAMES}
            self.assertLess(m["odo_cmd30"], cmd_max, m)
            self.assertLess(m["odo_cmd30"], 0.5 * m["odo_course"], m)
            self.assertLess(m["odo_gyro"], 0.7 * m["odo_course"], m)
            self.assertLess(m["odo_gyro"], m["odo_gyro_flip"], m)
            self.assertLess(m["odo_gyro"], m["hold"], m)

    def test_best_gains(self):
        self.assertEqual(self.s["best_cmd_gain_10s_turning"], "odo_cmd30")
        self.assertEqual(self.s["best_gyro_gain_10s_turning"], "odo_gyro")

    def test_straight_stratum(self):
        r = fo.find(self.s["table"], "odo_gyro", 5, "straight")
        self.assertLess(r["median_m"], 0.1, r)

    def test_ci_and_outputs(self):
        self.assertIn("odo_gyro|10", self.s["ci"])
        with tempfile.TemporaryDirectory() as d:
            res = fo.write_outputs(d, [{"part": "x", "bytes_read": 5}], [{"ride_id": "1"}],
                                   self.pool, 0.0)
            self.assertTrue(res["conclusions"])
            with open(os.path.join(d, "summary.json")) as f:
                self.assertEqual(json.load(f)["version"], fo.__version__)
            for name in ("report.md", "rides.jsonl"):
                self.assertTrue(os.path.exists(os.path.join(d, name)), name)


class PartTests(unittest.TestCase):
    def test_process_part(self):
        control, gps, gyro = synthetic_ride([(60, 0.8, 0.0), (10, 0.8, 0.5), (60, 0.8, 0.0)])
        cbuf, gbuf, ibuf = io.StringIO(), io.StringIO(), io.StringIO()
        cw, gw, iw = csv.writer(cbuf), csv.writer(gbuf), csv.writer(ibuf)
        cw.writerow(["linear", "angular", "rpm_1", "rpm_2", "rpm_3", "rpm_4", "timestamp"])
        for t, lin, ang, rpm in control:
            cw.writerow([lin, ang] + rpm + [int(round(t * 1000))])
        gw.writerow(["latitude", "longitude", "timestamp"])
        for t, lat, lon in gps:
            gw.writerow([lat, lon, int(round(t * 1000))])
        iw.writerow(["compass", "accelerometer", "gyroscope", "timestamp"])
        for t, x, y, z in gyro:
            iw.writerow(["[]", "[]", json.dumps([[str(x), str(y), str(z), "%.3f" % t]]),
                         int(round(t * 1000))])
        mem = io.BytesIO()
        with zipfile.ZipFile(mem, "w", zipfile.ZIP_DEFLATED) as z:
            base = "output_rides_0/ride_123_20240101000000/"
            z.writestr(base + "control_data_123.csv", cbuf.getvalue())
            z.writestr(base + "gps_data_123.csv", gbuf.getvalue())
            z.writestr(base + "imu_data_123.csv", ibuf.getvalue())
            z.writestr(base + "front_camera.mp4", b"\x00" * 100)
        blob = mem.getvalue()
        rz = fm.RemoteZip(len(blob), lambda s, k: blob[s:s + k])
        pool, rides = fo.new_pool(), []
        info = fo.process_part(rz, "output_rides_0", 5, pool, rides)
        self.assertEqual(info["rides_sampled"], 1)
        self.assertEqual(len(rides), 1)
        self.assertNotIn("error", rides[0])
        self.assertNotIn("skipped", rides[0])
        self.assertEqual(rides[0]["ride_id"], "123")
        self.assertGreater(rides[0]["anchors"], 30)
        self.assertAlmostEqual(rides[0]["gyro_bias"], BIAS)


if __name__ == "__main__":
    unittest.main()
