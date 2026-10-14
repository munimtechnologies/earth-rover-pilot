"""Tests for frodo_motion, on synthetic zips and a simulated rover with known motion."""

import csv
import io
import json
import math
import random
import struct
import unittest
import zipfile
import zlib

import frodo_motion as fm

START = 1715000000.0
M_PER_DEG = math.pi / 180.0 * fm.R_EARTH


def bytes_fetch(blob, calls=None):
    def fetch(start, length):
        assert 0 <= start and start + length <= len(blob), (start, length, len(blob))
        if calls is not None:
            calls.append((start, length))
        return blob[start:start + length]
    return fetch


def synthetic_ride(seed=3, duration=900.0, start=START, gps_delay=2.0, yaw_per_unit=-40.0,
                   mps_per_rpm=0.01):
    """A rover driven by random commands at 10 Hz. A positive angular turns it
    at yaw_per_unit deg/s clockwise (negative: to the left); speed is
    mps_per_rpm * RPM with RPM = 100 * linear. GPS at 1 Hz reports where the
    rover was gps_delay seconds earlier."""
    rng = random.Random(seed)
    control, truth = [], []
    h = e = n = 0.0
    lin = ang = 0.0
    switch = start
    steps = int(duration / 0.1)
    for i in range(steps):
        t = start + i * 0.1
        if t >= switch:
            lin = rng.choice([0.0, 0.5, 0.7, 1.0, 1.0])
            ang = rng.choice([0.0, rng.uniform(-1.0, 1.0), rng.uniform(-1.0, 1.0)])
            switch = t + rng.uniform(3.0, 8.0)
        rpm = 100.0 * lin
        control.append((t, lin, ang, [rpm] * 4))
        truth.append((e, n))
        v = mps_per_rpm * rpm
        h += math.radians(yaw_per_unit * ang) * 0.1
        e += v * math.sin(h) * 0.1
        n += v * math.cos(h) * 0.1
    gps = []
    lat0, lon0 = 37.0, -122.0
    for j in range(3, int(duration) - 1):
        t = start + j
        k = int(round((t - gps_delay - start) / 0.1))
        e_, n_ = truth[k]
        gps.append((t, lat0 + n_ / M_PER_DEG, lon0 + e_ / (M_PER_DEG * math.cos(math.radians(lat0)))))
    return control, gps


def synthetic_gyro(control, yaw_per_unit=-40.0, seed=5):
    """One gyroscope sample a second. z is the rover's true turn rate in deg/s,
    counter-clockwise positive, plus a 0.4 bias; x and y are bias and noise."""
    rng = random.Random(seed)
    out = []
    for i in range(0, len(control), 10):
        t, _, ang, _ = control[i]
        out.append((t + 0.03, 3.0 + rng.gauss(0, 0.3), -2.7 + rng.gauss(0, 0.3),
                    0.4 - yaw_per_unit * ang + rng.gauss(0, 0.5)))
    return out


def imu_csv(gyro):
    """An imu_data CSV in the FrodoBots-2K layout: each cell a list of [x, y, z, t]."""
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["compass", "accelerometer", "gyroscope", "timestamp"])
    for t, x, y, z in gyro:
        w.writerow([json.dumps([["-900", "600", "100", "%.3f" % t]]),
                    json.dumps([["0.816", "0.09", "-0.44", "%.3f" % t]]),
                    json.dumps([["%.3f" % x, "%.3f" % y, "%.3f" % z, "%.3f" % t]]),
                    str(int(t * 1000) + 400)])
    return buf.getvalue().encode()


def ride_csvs(seed, start=START):
    control, gps = synthetic_ride(seed=seed, start=start)
    c = ["linear,angular,rpm_1,rpm_2,rpm_3,rpm_4,timestamp"]
    c += ["%.3f,%.4f,%d,%d,%d,%d,%.3f" % (l, a, q[0], q[1], q[2], q[3], t) for t, l, a, q in control]
    g = ["latitude,longitude,timestamp"]
    g += ["%.8f,%.8f,%d" % (la, lo, int(round(t * 1000))) for t, la, lo in gps]
    return ("\n".join(c) + "\n").encode(), ("\n".join(g) + "\n").encode(), imu_csv(synthetic_gyro(control))


class ZipTests(unittest.TestCase):
    def make_zip(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            z.writestr("output_rides_9/ride_1_20240501013650/control_data_1.csv",
                       b"linear,angular\n" * 200, compress_type=zipfile.ZIP_DEFLATED)
            z.writestr("output_rides_9/ride_1_20240501013650/gps_data_1.csv",
                       b"latitude,longitude,timestamp\n1,2,3\n", compress_type=zipfile.ZIP_STORED)
            z.writestr("output_rides_9/ride_1_20240501013650/recordings/a.ts", bytes(range(256)) * 40,
                       compress_type=zipfile.ZIP_DEFLATED)
            z.writestr("output_rides_9/ride_2_20240502013650/control_data_2.csv", b"x\n")
        return buf.getvalue()

    def test_lists_and_reads_like_zipfile(self):
        blob = self.make_zip()
        rz = fm.RemoteZip(len(blob), bytes_fetch(blob))
        self.assertEqual(rz.count, 4)
        entries = list(rz.entries(chunk=50))   # small chunks: entries span chunk edges
        ref = zipfile.ZipFile(io.BytesIO(blob))
        self.assertEqual([e.name for e in entries], ref.namelist())
        for e in entries:
            self.assertEqual(rz.read(e), ref.read(e.name))

    def test_filter_and_group(self):
        blob = self.make_zip()
        rz = fm.RemoteZip(len(blob), bytes_fetch(blob))
        rides = fm.group_rides(rz.entries(lambda name: name.endswith(".csv")))
        self.assertEqual(sorted(rides), ["output_rides_9/ride_1_20240501013650",
                                         "output_rides_9/ride_2_20240502013650"])
        self.assertEqual(sorted(rides["output_rides_9/ride_1_20240501013650"]),
                         ["control_data", "gps_data"])

    def test_zip64(self):
        data = b"latitude,longitude,timestamp\n1,2,3\n"
        name = b"a/gps_data_1.csv"
        crc = zlib.crc32(data)
        local = struct.pack("<4sHHHHHIIIHH", b"PK\x03\x04", 45, 0, 0, 0, 0, crc, len(data),
                            len(data), len(name), 0) + name + data
        extra = struct.pack("<HHQQQ", 1, 24, len(data), len(data), 0)
        central = struct.pack("<4sHHHHHHIIIHHHHHII", b"PK\x01\x02", 45, 45, 0, 0, 0, 0, crc,
                              0xFFFFFFFF, 0xFFFFFFFF, len(name), len(extra), 0, 0, 0, 0,
                              0xFFFFFFFF) + name + extra
        cd_offset, cd_size = len(local), len(central)
        end64 = struct.pack("<4sQHHIIQQQQ", b"PK\x06\x06", 44, 45, 45, 0, 0, 1, 1, cd_size, cd_offset)
        locator = struct.pack("<4sIQI", b"PK\x06\x07", 0, cd_offset + cd_size, 1)
        eocd = struct.pack("<4sHHHHIIH", b"PK\x05\x06", 0, 0, 0xFFFF, 0xFFFF, 0xFFFFFFFF,
                           0xFFFFFFFF, 0)
        blob = local + central + end64 + locator + eocd
        rz = fm.RemoteZip(len(blob), bytes_fetch(blob))
        self.assertEqual((rz.cd_offset, rz.cd_size, rz.count), (cd_offset, cd_size, 1))
        (entry,) = list(rz.entries())
        self.assertEqual((entry.name, entry.csize, entry.usize, entry.offset),
                         ("a/gps_data_1.csv", len(data), len(data), 0))
        self.assertEqual(rz.read(entry), data)

    def test_crc_mismatch(self):
        blob = self.make_zip()
        rz = fm.RemoteZip(len(blob), bytes_fetch(blob))
        e = next(rz.entries(lambda n: n.endswith("gps_data_1.csv")))
        with self.assertRaises(ValueError):
            rz.read(e._replace(crc=(e.crc + 1) & 0xFFFFFFFF))

    def test_not_a_zip(self):
        with self.assertRaises(ValueError):
            fm.RemoteZip(100, bytes_fetch(bytes(100)))


class HelperTests(unittest.TestCase):
    def test_norm_t(self):
        self.assertEqual(fm.norm_t(1681119426.41), 1681119426.41)
        self.assertAlmostEqual(fm.norm_t(1681119426410.0), 1681119426.41)
        self.assertAlmostEqual(fm.norm_t(1681119426410000.0), 1681119426.41)

    def test_pick_evenly(self):
        self.assertEqual(fm.pick_evenly(["c", "a", "b"], 5), ["a", "b", "c"])
        picked = fm.pick_evenly([str(i).zfill(3) for i in range(100)], 4)
        self.assertEqual(picked, ["012", "037", "062", "087"])

    def test_series_mean(self):
        s = fm.Series([0.0, 1.0, 2.0, 3.0], [1.0, 2.0, 3.0, 4.0])
        self.assertAlmostEqual(s.mean(0.5, 2.5), 2.5)
        self.assertAlmostEqual(s.mean(0.0, 3.0), 2.5)
        self.assertIsNone(s.mean(3.5, 4.0))

    def test_acc(self):
        a = fm.Acc()
        for x in (-2.0, -1.0, 1.0, 2.0):
            a.add(x, -3.0 * x, 0.5, 0.5)
        self.assertAlmostEqual(a.corr(), -1.0)
        self.assertAlmostEqual(a.slope0(), -3.0)
        self.assertAlmostEqual(a.slope(), -3.0)
        self.assertEqual((a.agree, a.disagree), (0, 4))
        b = fm.Acc()
        b.merge(a)
        self.assertEqual(b.n, 4)

    def test_slope_ignores_an_offset(self):
        a = fm.Acc()
        for x in (0.0, 1.0, 2.0, 3.0):
            a.add(x, 2.0 * x + 5.0)
        self.assertAlmostEqual(a.slope(), 2.0)
        self.assertGreater(a.slope0(), 3.0)
        self.assertIsNone(fm.Acc().slope())

    def test_median(self):
        self.assertEqual(fm.median([3.0, 1.0, 2.0]), 2.0)
        self.assertEqual(fm.median([5.0]), 5.0)

    def test_load_control_and_gps(self):
        ch, cr = fm.parse_csv(b"speed,angular,rpm_1,rpm_2,rpm_3,rpm_4,timestamp\n"
                              b"0.5,0.1,3,3,8,7,1681119427.154\n-0.45,0,0,0,0,0,1681119426.41\n"
                              b"bad,0,0,0,0,0,1681119428\n")
        control = fm.load_control(ch, cr)
        self.assertEqual(len(control), 2)
        self.assertEqual(control[0][1], -0.45)
        self.assertEqual(control[1][3], [3.0, 3.0, 8.0, 7.0])
        gh, gr = fm.parse_csv(b"latitude,longitude,timestamp\n1000,1000,1\n0,0,2\n"
                              b"37.1,-122.1,1681119427000\n37.1,-122.1,1681119427000\n"
                              b"37.2,-122.2,1681119426000\n")
        gps = fm.load_gps(gh, gr)
        self.assertEqual([g[0] for g in gps], [1681119426.0, 1681119427.0])
        with self.assertRaises(ValueError):
            fm.load_control(["a", "b"], [])

    def test_load_imu(self):
        # The layout of FrodoBots-2K's imu_data CSVs, with a sample repeated across rows.
        h, rows = fm.parse_csv(
            b'compass,accelerometer,gyroscope,timestamp\n'
            b'"[[""-928"", ""608"", ""116"", ""1705301256.972""]]",[],'
            b'"[[""3.344"", ""-2.763"", ""0.084"", ""1705301256.765""]]",1705301260848\n'
            b'x,y,"[[""3.5"", ""-2.7"", ""0.1"", ""1705301257.765""], '
            b'[""3.344"", ""-2.763"", ""0.084"", ""1705301256.765""]]",1\n'
            b'x,y,not json,2\n')
        gyro = fm.load_imu(h, rows)
        self.assertEqual(len(gyro), 2)
        self.assertEqual(gyro[0], (1705301256.765, 3.344, -2.763, 0.084))
        self.assertEqual(gyro[1][1], 3.5)
        self.assertEqual(fm.load_imu(h, rows, "compass"), [(1705301256.972, -928.0, 608.0, 116.0)])
        with self.assertRaises(ValueError):
            fm.load_imu(["a"], [])

    def test_parse_samples_rejects_junk(self):
        self.assertEqual(fm.parse_samples("not json"), [])
        self.assertEqual(fm.parse_samples('{"a": 1}'), [])
        self.assertEqual(fm.parse_samples('[["1", "2", "x", "3"]]'), [])
        self.assertEqual(fm.parse_samples('[["1", "2"]]'), [])
        self.assertEqual(fm.parse_samples('[[1, 2, 3, 4]]'), [(4.0, 1.0, 2.0, 3.0)])


class AnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        control, gps = synthetic_ride()
        cls.pooled, cls.bins = {}, {}
        cls.stats = fm.analyse_ride(control, gps, cls.pooled, cls.bins)
        cls.summary = fm.summarise(cls.pooled, cls.bins, min_n=30)

    def best(self, fam, s="2"):
        return self.summary[fam][s]["best"]

    def test_turn_sign_lag_and_rate(self):
        b = self.best("turn")
        self.assertLessEqual(abs(b["lag_s"] - 2.0), 1.0)
        self.assertLess(b["corr"], -0.5)
        self.assertGreater(b["agree"] + b["disagree"], 30)
        self.assertLess(b["agree"], b["disagree"] / 5.0)
        self.assertAlmostEqual(b["slope0"], -40.0, delta=12.0)
        self.assertEqual(self.stats["turn_best"]["lag_s"], b["lag_s"])

    def test_gps_delay_and_speed_per_rpm(self):
        b = self.best("speed_rpm")
        self.assertLessEqual(abs(b["lag_s"] - 2.0), 1.0)
        self.assertGreater(b["corr"], 0.8)
        self.assertAlmostEqual(b["slope0"], 0.01, delta=0.003)

    def test_speed_per_command(self):
        b = self.best("speed_lin")
        self.assertAlmostEqual(b["slope0"], 1.0, delta=0.3)
        top = self.summary["speed_by_linear"]["bins"][-1]
        self.assertEqual(top["linear"], "0.9-1.0")
        self.assertGreater(top["n"], 30)
        self.assertGreater(top["mean_mps"], 0.75)
        self.assertLess(top["mean_mps"], 1.1)

    def test_rpm_stats(self):
        self.assertEqual(self.stats["rpm_negative_rows"], 0)
        self.assertEqual(self.stats["reverse_rows"], 0)
        b = self.best("rpm_lag", "0")
        self.assertLessEqual(b["lag_s"], 0.4)

    def test_conclusions_name_the_turn_direction(self):
        lines = fm.conclusions(self.summary, fm.rpm_sign_totals([self.stats]))
        self.assertTrue(any("turned the rover left" in line for line in lines), lines)

    def test_no_gyro_means_no_gyro_results(self):
        self.assertNotIn("gyro_best", self.stats)
        self.assertNotIn("gyro_all", self.summary)
        self.assertIsNone(fm.yaw_axis(self.summary))

    def test_short_ride_is_skipped(self):
        st = fm.analyse_ride([(0.0, 0.0, 0.0, [0.0] * 4)] * 10, [], {}, {})
        self.assertEqual(st["skipped"], "too little data")


class GyroTests(unittest.TestCase):
    """The simulated gyroscope's z axis reads the turn rate in deg/s,
    counter-clockwise positive, and a positive angular turns left at 40 deg/s."""

    @classmethod
    def setUpClass(cls):
        control, gps = synthetic_ride()
        cls.pooled, cls.bins = {}, {}
        cls.stats = fm.analyse_ride(control, gps, cls.pooled, cls.bins, synthetic_gyro(control))
        cls.summary = fm.summarise(cls.pooled, cls.bins, min_n=30)

    def test_finds_the_yaw_axis(self):
        i, b = fm.yaw_axis(self.summary)
        self.assertEqual(i, 2)
        self.assertGreater(b["corr"], 0.8)
        self.assertLessEqual(abs(b["lag_s"]), 0.5)
        self.assertAlmostEqual(b["slope"], 40.0, delta=6.0)

    def test_other_axes_are_noise(self):
        for i in ("0", "1"):
            self.assertLess(abs(self.summary["gyro_all"][i]["best"]["corr"]), 0.3)

    def test_spin_in_place_rate(self):
        b = self.summary["gyro_spin"]["2"]["best"]
        self.assertGreaterEqual(b["n"], 30)
        self.assertAlmostEqual(b["slope"], 40.0, delta=8.0)

    def test_gps_course_checks_the_units(self):
        b = self.summary["course_gyro"]["2"]["best"]
        self.assertLess(b["corr"], -0.5)
        self.assertGreater(b["slope"], -1.4)
        self.assertLess(b["slope"], -0.6)
        self.assertLessEqual(abs(b["lag_s"] - 2.0), 1.0)

    def test_per_ride_stats(self):
        self.assertEqual(self.stats["gyro_samples"], 900)
        self.assertAlmostEqual(self.stats["gyro_median"][0], 3.0, delta=0.2)
        self.assertGreater(self.stats["gyro_best"]["z"]["corr"], 0.8)

    def test_conclusions(self):
        lines = fm.conclusions(self.summary, fm.rpm_sign_totals([self.stats]))
        self.assertTrue(any("axis z follows" in line and "gives a positive reading" in line
                            for line in lines), lines)
        self.assertTrue(any(line.startswith("Units check") for line in lines), lines)


class PartTests(unittest.TestCase):
    def test_process_part(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
            for i, seed in enumerate((3, 4)):
                c, g, imu = ride_csvs(seed, START + 10000 * i)
                base = "output_rides_7/ride_%d_2024050101365%d/" % (100 + i, i)
                z.writestr(base + "control_data_%d.csv" % (100 + i), c)
                z.writestr(base + "gps_data_%d.csv" % (100 + i), g)
                z.writestr(base + "imu_data_%d.csv" % (100 + i),
                           imu if i == 0 else b"accelerometer,timestamp\n1,2\n")
                z.writestr(base + "recordings/front_0001.ts", b"\0" * 500)
            z.writestr("output_rides_7/ride_999_20240501000000/control_data_999.csv", b"linear\n")
        blob = buf.getvalue()
        rz = fm.RemoteZip(len(blob), bytes_fetch(blob))
        pooled, bins, rides = {}, {}, []
        info = fm.process_part(rz, "output_rides_7", 2, pooled, bins, rides)
        self.assertEqual((info["rides_with_csvs"], info["rides_usable"], info["rides_sampled"]),
                         (3, 2, 2))
        self.assertEqual(info["csv_kinds"]["control_data"], 3)
        self.assertEqual(info["extensions"]["ts"], 2)
        self.assertEqual(info["samples"]["control"][0][0], "linear")
        self.assertEqual(info["samples"]["imu"][0][0],
                         ["compass", "accelerometer", "gyroscope", "timestamp"])
        self.assertEqual([r.get("error") for r in rides], [None, None])
        self.assertEqual(rides[0]["ride_id"], "100")
        self.assertEqual(rides[0]["gyro_samples"], 900)
        self.assertTrue(rides[1]["gyro_error"].startswith("ValueError"), rides[1])
        summary = fm.summarise(pooled, bins)
        turn = summary["turn"]["2"]["best"]
        self.assertLess(turn["corr"], -0.5)
        self.assertLessEqual(abs(turn["lag_s"] - 2.0), 1.0)
        self.assertEqual(fm.yaw_axis(summary)[0], 2)

    def test_big_imu_file_is_skipped(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
            c, g, imu = ride_csvs(3)
            base = "output_rides_7/ride_100_20240501013650/"
            z.writestr(base + "control_data_100.csv", c)
            z.writestr(base + "gps_data_100.csv", g)
            z.writestr(base + "imu_data_100.csv", imu)
        blob = buf.getvalue()
        rz = fm.RemoteZip(len(blob), bytes_fetch(blob))
        rides = []
        fm.process_part(rz, "output_rides_7", 1, {}, {}, rides, gyro_max_mb=0.01)
        self.assertIn("skipped", rides[0]["gyro_error"])
        self.assertNotIn("gyro_samples", rides[0])
        self.assertNotIn("error", rides[0])


if __name__ == "__main__":
    unittest.main()
