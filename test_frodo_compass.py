"""Tests for frodo_compass, on simulated rides whose true path and heading are known."""

import csv
import io
import json
import math
import os
import tempfile
import unittest
import zipfile

import frodo_motion as fm
import frodo_compass as fc

START = 1715000000.0
LAT0, LON0 = 37.0, -122.0
M_PER_DEG = math.pi / 180.0 * fm.R_EARTH
K = 30.0       # the simulated rover turns this many deg/s per unit of angular
BIAS = 0.8     # gyroscope offset
MOUNT = 40.0   # the magnetometer reads this many degrees less than the true heading
CY, CZ, RADIUS = 300.0, -120.0, 200.0  # hard-iron centre and field strength of axes y, z
# Left turns of 150 deg between 30 s straights: the heading goes all the way round.
CYCLE = [(30, 0.8, 0.0), (10, 0.8, 0.5)] * 6


def to_latlon(e, n):
    return LAT0 + n / M_PER_DEG, LON0 + e / (M_PER_DEG * math.cos(math.radians(LAT0)))


def synthetic_ride(schedule):
    """Control at 10 Hz, gyroscope, compass and GPS at 1 Hz, for a rover following
    schedule [(seconds, linear, angular)] as in test_frodo_odometry. The compass
    is horizontal in axes y (forward at the true heading minus MOUNT) and z
    (pointing left there), so frame 'yz-' reads the heading minus MOUNT; x is
    vertical and nearly constant. Each fix shows where the rover was GPS_LAG_S earlier."""
    cmds = []
    for dur, lin, ang in schedule:
        cmds += [(lin, ang)] * int(round(dur / 0.1))
    lag = int(round(fc.CMD_LAG_S / 0.1))
    control, rates, truth, heading = [], [], [(0.0, 0.0)], [0.0]
    e = n = psi = 0.0
    for i, (lin, ang) in enumerate(cmds):
        rpm = lin / 0.8 * 100.0
        control.append((START + i * 0.1, lin, ang, [rpm] * 4))
        w = K * (cmds[i - lag][1] if i >= lag else 0.0)
        rates.append(w)
        v = rpm * fc.MPS_PER_RPM
        for _ in range(10):
            mid = math.radians(psi - w * 0.005)
            e += v * 0.01 * math.sin(mid)
            n += v * 0.01 * math.cos(mid)
            psi -= w * 0.01
            truth.append((e, n))
            heading.append(psi)
    secs = len(cmds) // 10
    gyro = [(START + m + 0.37, rates[10 * m + 3] + BIAS, 0.0, 0.0) for m in range(secs)]
    compass = []
    for m in range(secs):
        h = math.radians(heading[100 * m + 37] - MOUNT)
        compass.append((START + m + 0.37, 50.0 + 0.3 * math.sin(0.7 * m),
                        CY + RADIUS * math.cos(h), CZ - RADIUS * math.sin(h)))
    gps = []
    for j in range(2, secs - 1):
        pe, pn = truth[100 * j + 30 - int(round(fc.GPS_LAG_S * 100))]
        lat, lon = to_latlon(pe, pn)
        gps.append((START + j + 0.3, round(lat, 8), round(lon, 8)))
    return control, gps, gyro, compass


def circle(n, deg_from=0.0, deg_to=360.0, cx=5.0, cy=-3.0, r=2.0):
    out = []
    for i in range(n):
        a = math.radians(deg_from + (deg_to - deg_from) * i / n)
        out.append((float(i), 0.0, cx + r * math.cos(a), cy + r * math.sin(a)))
    return out


class HelperTests(unittest.TestCase):
    def test_frames(self):
        self.assertEqual(len(fc.FRAMES), 6)
        self.assertEqual(fc.FRAMES["yz-"], (1, 2, -1))
        self.assertEqual(fc.FRAMES["xy+"], (0, 1, 1))

    def test_solve3(self):
        x = fc.solve3([[2.0, 0.0, 1.0], [0.0, 3.0, 0.0], [1.0, 0.0, 4.0]], [4.0, 6.0, 9.0])
        for got, want in zip(x, (1.0, 2.0, 2.0)):
            self.assertAlmostEqual(got, want, places=9)
        self.assertIsNone(fc.solve3([[1.0, 2.0, 0.0], [2.0, 4.0, 0.0], [0.0, 0.0, 1.0]],
                                    [1.0, 2.0, 3.0]))

    def test_calibrate_full_circle(self):
        info, centre = fc.calibrate(circle(72), 1, 2)
        self.assertTrue(info["ok"], info)
        self.assertAlmostEqual(centre[0], 5.0, places=6)
        self.assertAlmostEqual(centre[1], -3.0, places=6)
        self.assertAlmostEqual(info["radius"], 2.0, places=2)
        self.assertEqual(info["cover"], 36)

    def test_calibrate_rejects(self):
        info, _ = fc.calibrate(circle(40, 0.0, 90.0), 1, 2)
        self.assertFalse(info["ok"])
        self.assertEqual(info["why"], "cover")
        info, centre = fc.calibrate([(float(i), 1.0, 2.0, 3.0) for i in range(30)], 1, 2)
        self.assertFalse(info["ok"])
        self.assertIsNone(centre)
        info, _ = fc.calibrate(circle(10), 1, 2)
        self.assertEqual(info["why"], "few samples")

    def test_headings_interpolate_across_north(self):
        control = [(i * 0.1, 0.8, 0.0, [100.0] * 4) for i in range(20)]
        grid = fc.Grid(control, [])
        self.assertEqual(grid.n, 10)
        self.assertIsNone(grid.gyro_yaw)
        samples = []
        for t, h in ((0.0, 350.0), (1.0, 10.0)):
            r = math.radians(h)
            samples.append((t, 0.0, math.cos(r), -math.sin(r)))
        where = fc.compass_cells(grid, [s[0] for s in samples])
        hs = fc.frame_headings(samples, where, 1, 2, -1, (0.0, 0.0))
        self.assertAlmostEqual(fc.wrap180(hs[2]), 0.0, places=6)    # cell centre 0.5 s
        self.assertAlmostEqual(fc.wrap180(hs[0] - 352.0), 0.0, places=6)  # 0.1 s
        self.assertAlmostEqual(hs[7], 10.0, places=6)  # 1.5 s: nearest sample, 1.0 s
        self.assertAlmostEqual(hs[9], 10.0, places=6)  # 1.9 s: still within COMPASS_NEAR_S
        far = [(5.0,) + s[1:] for s in samples[:1]] + [(6.0,) + s[1:] for s in samples[1:]]
        where = fc.compass_cells(grid, [s[0] for s in far])
        self.assertEqual(fc.frame_headings(far, where, 1, 2, -1, (0.0, 0.0)), [None] * 10)
        self.assertEqual(fc.filled([None, 3.0, None, 5.0, None]), [3.0, 3.0, 3.0, 5.0, 5.0])

    def test_fit_course(self):
        east = [(float(t), 0.7 * t, 0.0) for t in range(6)]
        self.assertAlmostEqual(fc.fit_course(east, 0.25), 90.0, places=9)
        self.assertIsNone(fc.fit_course([(float(t), 0.1 * t, 0.0) for t in range(6)], 0.25))

    def test_decide(self):
        def rows(course, heading, ct, t30):
            return [{"predictor": "odo_course", "horizon_s": 10, "stratum": "all", "median_m": course},
                    {"predictor": "heading", "horizon_s": 10, "stratum": "all", "median_m": heading},
                    {"predictor": "odo_course", "horizon_s": 10, "stratum": "turning", "median_m": ct},
                    {"predictor": "turn30", "horizon_s": 10, "stratum": "turning", "median_m": t30}]
        d = fc.decide(rows(2.0, 2.4, 2.0, 1.8))
        self.assertEqual(d["default"], "use_course=True")
        self.assertEqual(d["turn_rule"], "helps")
        d = fc.decide(rows(2.0, 2.1, 2.0, 2.2))
        self.assertEqual(d["default"], "use_course=False")
        self.assertEqual(d["turn_rule"], "hurts")
        self.assertEqual(fc.decide([]), {})


class LearnBiasTests(unittest.TestCase):
    def test_straight_ride_learns_the_mount(self):
        control, gps, gyro, compass = synthetic_ride([(90, 0.8, 0.0)])
        grid = fc.Grid(control, gyro)
        where = fc.compass_cells(grid, [c[0] for c in compass])
        heads = {"yz-": fc.frame_headings(compass, where, 1, 2, -1, (CY, CZ))}
        fits = fc.learn_bias(control, fc.fresh_fixes(gps), grid, heads)
        self.assertGreaterEqual(len(fits), 3)
        for _, bias in fits:
            self.assertAlmostEqual(bias["yz-"], MOUNT, delta=0.5)

    def test_guards(self):
        st = fc.analyse_ride([(START, 0.0, 0.0, [0.0] * 4)] * 10, [(START, LAT0, LON0)], [], [],
                             fc.new_pool())
        self.assertEqual(st["skipped"], "too little data")
        control, gps, gyro, compass = synthetic_ride([(60, 0.8, 0.0)])
        pool = fc.new_pool()
        self.assertEqual(fc.analyse_ride(control, gps, gyro, [], pool)["skipped"], "no compass")
        # Driving straight, the compass never turns: no frame calibrates.
        st = fc.analyse_ride(control, gps, gyro, compass, pool)
        self.assertEqual(st["skipped"], "no frame calibrates")
        self.assertEqual(pool["rides"], [])


class TurnTests(unittest.TestCase):
    """Three rides of left turns with exact GPS and compass: rides 0 and 2 choose
    the frame, ride 1 is scored."""

    @classmethod
    def setUpClass(cls):
        cls.pool = fc.new_pool()
        cls.stats = []
        for i in range(3):
            control, gps, gyro, compass = synthetic_ride([(10 + 7 * i, 0.8, 0.0)] + CYCLE)
            cls.stats.append(fc.analyse_ride(control, gps, gyro, compass, cls.pool, no=i))
        cls.s = fc.summarise(cls.pool, min_pairs=50)

    def test_rides(self):
        for st in self.stats:
            self.assertNotIn("skipped", st)
            self.assertEqual(st["frames_ok"], ["yz+", "yz-"])
            self.assertGreater(st["anchors"], 40)
            self.assertGreaterEqual(st["bias_fits"], 4)
            self.assertAlmostEqual(st["bias_last"]["yz-"], MOUNT, delta=2.0)
        self.assertEqual(self.s["rides"], 3)
        self.assertEqual(self.s["test_rides"], 1)

    def test_frame_choice(self):
        self.assertEqual(self.s["chosen_frame"], "yz-")
        frames = self.s["frames"]
        self.assertLess(frames["yz-"]["cal_median_deg"], 3.0, frames)
        self.assertLess(frames["yz-"]["test_median_deg"], 3.0, frames)
        self.assertGreater(frames["yz+"]["cal_median_deg"], 10.0, frames)
        self.assertEqual(frames["xy+"]["rides_ok"], 0)
        self.assertEqual(self.s["ride_winners"], {"yz-": 3})

    def test_predictors(self):
        rows = self.s["table"]
        for h in (5, 10):
            course = fc.find(rows, "odo_course", h, "turning")["median_m"]
            # turn30 keeps the course for the first 30 deg of a turn, so it gains less.
            for kind, most in (("heading", 0.3), ("turn0", 0.3), ("turn30", 0.5)):
                r = fc.find(rows, kind, h, "turning")
                self.assertLess(r["median_m"], most * course, (kind, h, r, course))
            self.assertLess(fc.find(rows, "heading", h)["median_m"], 0.3)
        straight = fc.find(rows, "heading", 5, "straight")
        self.assertLess(straight["median_m"], 0.1, straight)
        self.assertEqual(self.s["decision"]["turn_rule"], "helps")
        self.assertIn(self.s["decision"]["default"], ("use_course=True", "use_course=False"))

    def test_outputs(self):
        with tempfile.TemporaryDirectory() as d:
            res = fc.write_outputs(d, [{"part": "x", "bytes_read": 5}],
                                   [{"no": 0}, {"no": 1, "skipped": "no compass"}],
                                   self.pool, 0.0, min_pairs=50)
            self.assertTrue(res["conclusions"])
            self.assertEqual(res["rides_skipped"], {"no compass": 1})
            with open(os.path.join(d, "summary.json")) as f:
                self.assertEqual(json.load(f)["version"], fc.__version__)
            with open(os.path.join(d, "report.md")) as f:
                self.assertIn("frame yz-", f.read())
            self.assertTrue(os.path.exists(os.path.join(d, "rides.jsonl")))


class PartTests(unittest.TestCase):
    def test_process_part(self):
        control, gps, gyro, compass = synthetic_ride([(20, 0.8, 0.0)] + CYCLE[:8])
        cbuf, gbuf, ibuf = io.StringIO(), io.StringIO(), io.StringIO()
        cw, gw, iw = csv.writer(cbuf), csv.writer(gbuf), csv.writer(ibuf)
        cw.writerow(["linear", "angular", "rpm_1", "rpm_2", "rpm_3", "rpm_4", "timestamp"])
        for t, lin, ang, rpm in control:
            cw.writerow([lin, ang] + rpm + [int(round(t * 1000))])
        gw.writerow(["latitude", "longitude", "timestamp"])
        for t, lat, lon in gps:
            gw.writerow([lat, lon, int(round(t * 1000))])
        iw.writerow(["compass", "accelerometer", "gyroscope", "timestamp"])
        for (t, gx, gy, gz), (_, mx, my, mz) in zip(gyro, compass):
            iw.writerow([json.dumps([[repr(mx), repr(my), repr(mz), "%.3f" % t]]), "[]",
                         json.dumps([[str(gx), str(gy), str(gz), "%.3f" % t]]),
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
        pool, rides = fc.new_pool(), []
        info = fc.process_part(rz, "output_rides_0", 5, pool, rides)
        self.assertEqual(info["rides_sampled"], 1)
        self.assertEqual(len(rides), 1)
        self.assertNotIn("error", rides[0])
        self.assertNotIn("skipped", rides[0])
        self.assertEqual(rides[0]["ride_id"], "123")
        self.assertEqual(rides[0]["frames_ok"], ["yz+", "yz-"])
        self.assertGreater(rides[0]["anchors"], 20)
        self.assertEqual(len(pool["rides"]), 1)


if __name__ == "__main__":
    unittest.main()
