"""Tests for frodo_gps, on simulated rides whose GPS error is known."""

import csv
import io
import json
import math
import os
import random
import tempfile
import unittest
import zipfile

import frodo_gps as fg
import frodo_motion as fm

START = 1715000000.0
LAT0, LON0 = 37.0, -122.0
M_PER_DEG = math.pi / 180.0 * fm.R_EARTH


def to_latlon(e, n):
    return LAT0 + n / M_PER_DEG, LON0 + e / (M_PER_DEG * math.cos(math.radians(LAT0)))


def white(sigma):
    def make(n, rng):
        return [(rng.gauss(0, sigma), rng.gauss(0, sigma)) for _ in range(n)]
    return make


def gauss_markov(sigma, T):
    def make(n, rng):
        rho = math.exp(-1.0 / T)
        s = math.sqrt(1.0 - rho * rho) * sigma
        x, y = rng.gauss(0, sigma), rng.gauss(0, sigma)
        out = []
        for _ in range(n):
            out.append((x, y))
            x = rho * x + rng.gauss(0, s)
            y = rho * y + rng.gauss(0, s)
        return out
    return make


def synthetic_ride(schedule, noise, seed=0):
    """Control at 10 Hz and GPS at 1 Hz (each fix logged twice, 0.5 s apart)
    for a rover that drives straight east at 100 RPM (lin 0.8) or stands still,
    following schedule [(seconds, moving)]. Each fix shows where the rover was
    GPS_LAG_S earlier, plus noise(n, rng)."""
    rng = random.Random(seed)
    control, truth = [], []
    e = 0.0
    i = 0
    for dur, moving in schedule:
        for _ in range(int(round(dur / 0.1))):
            rpm = 100.0 if moving else 0.0
            control.append((START + i * 0.1, 0.8 if moving else 0.0, 0.0, [rpm] * 4))
            truth.append(e)
            e += rpm * fg.MPS_PER_RPM * 0.1
            i += 1
    nj = int(len(control) * 0.1) - 1
    err = noise(nj, rng)
    gps = []
    for j in range(2, nj):
        tg = START + j + 0.3
        k = min(len(truth) - 1, int((tg - fg.GPS_LAG_S - START) / 0.1))
        lat, lon = to_latlon(truth[k] + err[j][0], err[j][1])
        gps.append((tg, round(lat, 6), round(lon, 6)))
        gps.append((tg + 0.5, round(lat, 6), round(lon, 6)))
    return control, gps


def carried_ride(seconds=300, speed=1.0):
    """Wheels and commands at 0 the whole time while the GPS moves east at
    `speed`: a rover carried, or a ride whose wheel log failed."""
    control = [(START + i * 0.1, 0.0, 0.0, [0.0] * 4) for i in range(int(seconds * 10))]
    gps = []
    for j in range(2, seconds):
        lat, lon = to_latlon(speed * j, 0.0)
        gps.append((START + j + 0.3, lat, lon))
    return control, gps


class HelperTests(unittest.TestCase):
    def test_runs(self):
        rows = [(float(t), t != 4) for t in range(10)]
        self.assertEqual(fg.runs(rows, lambda r: r[1], 2.0), [(0.0, 3.0), (5.0, 9.0)])
        rows = [(float(t), True) for t in (0, 1, 2, 5, 6, 7)]
        self.assertEqual(fg.runs(rows, lambda r: r[1], 2.0), [(0.0, 2.0), (5.0, 7.0)])
        self.assertEqual(fg.runs(rows, lambda r: r[1], 2.5), [])

    def test_grid(self):
        track = [(0.0, 0.0, 0.0), (1.0, 1.0, 0.0), (5.0, 2.0, 0.0)]
        self.assertEqual(fg.grid(track, -1.0, 5.0, max_age=2.5),
                         [None, (0.0, 0.0), (1.0, 0.0), (1.0, 0.0), (1.0, 0.0), None, (2.0, 0.0)])

    def test_still_and_straight(self):
        self.assertTrue(fg.is_still((0.0, 0.0, 0.01, [0.0, 0.5, 0.0, 0.0])))
        self.assertFalse(fg.is_still((0.0, 0.0, 0.0, [0.0, None, 0.0, 0.0])))
        self.assertFalse(fg.is_still((0.0, 0.3, 0.0, [0.0, 0.0, 0.0, 0.0])))
        self.assertTrue(fg.is_straight((0.0, 0.8, 0.0, [100.0, 95.0, 100.0, 95.0])))
        self.assertFalse(fg.is_straight((0.0, 0.8, 0.0, [100.0, 60.0, 100.0, 60.0])))
        self.assertFalse(fg.is_straight((0.0, 0.8, 0.3, [100.0, 100.0, 100.0, 100.0])))
        self.assertFalse(fg.is_straight((0.0, 0.8, 0.0, [5.0, 5.0, 5.0, 5.0])))

    def test_line_fit(self):
        times = [float(t) for t in range(10)]
        pts = [(2.0 * t, 1.0 + t) for t in times]
        lateral, speed = fg.line_fit(times, pts)
        self.assertLess(lateral, 1e-6)
        self.assertAlmostEqual(speed, math.sqrt(5.0), places=6)

    def test_fit_exact(self):
        msd = {t: 4 * 1.5 ** 2 * (1 - math.exp(-t / 20.0)) for t in fg.TAUS}
        sigma, T, err = fg.fit_gauss_markov(msd)
        self.assertLess(abs(sigma - 1.5), 0.1)
        self.assertTrue(15.0 < T < 27.0, T)
        self.assertLess(err, 0.05)
        self.assertTrue(fg.fit_ok({"T_s": round(T, 1), "relative_rms_error": round(err, 3)}))

    def test_fit_on_edge_not_ok(self):
        # A random walk never levels off, so the best T is the largest searched:
        # a close fit by error alone (what 0.2.0 checked), but not one to offer.
        msd = {t: 0.5 * t for t in fg.TAUS}
        sigma, T, err = fg.fit_gauss_markov(msd)
        self.assertAlmostEqual(T, fg.T_RANGE_S[1], places=6)
        self.assertLess(err, fg.FIT_OK)
        self.assertFalse(fg.fit_ok({"T_s": round(T, 1), "relative_rms_error": round(err, 3)}))
        self.assertFalse(fg.fit_ok({"T_s": 0.5, "relative_rms_error": 0.0}))
        self.assertFalse(fg.fit_ok({"T_s": 30.0, "relative_rms_error": 0.4}))
        self.assertTrue(fg.fit_ok({"T_s": 30.0, "relative_rms_error": 0.1}))

    def test_too_little(self):
        pool = fg.new_pool()
        st = fg.analyse_ride([(START, 0.0, 0.0, [0.0] * 4)] * 10, [(START, LAT0, LON0)], pool)
        self.assertEqual(st["skipped"], "too little data")

    def test_msd_summary_empty(self):
        self.assertEqual(fg.msd_summary([]), ([], None))


class DriftTests(unittest.TestCase):
    """A rover whose GPS error drifts slowly (sigma 2 m per axis, T 30 s)."""

    @classmethod
    def setUpClass(cls):
        cls.pool = fg.new_pool()
        for i in range(4):
            control, gps = synthetic_ride([(60, True), (600, False)] * 6, gauss_markov(2.0, 30.0), seed=i)
            cls.stats = fg.analyse_ride(control, gps, cls.pool, ride=str(i))
        cls.s = fg.summarise(cls.pool)

    def test_windows(self):
        st = self.s["still"]
        self.assertEqual(st["windows"], 24)
        self.assertEqual(st["rides"], 4)
        self.assertEqual(st["frozen_windows"], 0)
        self.assertEqual(st["clean"]["windows_left_out"], 0)
        self.assertEqual(st["clean"]["windows"], 24)

    def test_fit_recovers_drift(self):
        gm = self.s["still"]["gauss_markov"]
        self.assertTrue(1.5 < gm["sigma_m"] < 2.5, gm)
        self.assertTrue(12.0 < gm["T_s"] < 75.0, gm)
        self.assertEqual(self.s["still"]["clean"]["gauss_markov"], gm)

    def test_wander_grows(self):
        rows = {r["lag_s"]: r["rms_m"] for r in self.s["still"]["rms_displacement_m"]}
        self.assertLess(rows[1], 1.0)
        self.assertGreater(rows[60], 2.0 * rows[1])

    def test_log(self):
        g = self.s["gps"]
        self.assertEqual(g["jumps"], 0)
        self.assertEqual(g["gaps_over_3s"], 0)
        self.assertTrue(1.9 < g["rows_per_s"] < 2.1, g)
        self.assertTrue(0.9 < g["position_changes_per_s"] < 1.01, g)


class CleanTests(unittest.TestCase):
    """The drifting rides above plus one carried ride: the carried ride's
    still period is left out of the clean fit, which then matches the drift."""

    @classmethod
    def setUpClass(cls):
        cls.pool = fg.new_pool()
        for i in range(4):
            control, gps = synthetic_ride([(60, True), (600, False)] * 6, gauss_markov(2.0, 30.0), seed=i)
            fg.analyse_ride(control, gps, cls.pool, ride=str(i))
        control, gps = carried_ride()
        cls.carried = fg.analyse_ride(control, gps, cls.pool, ride="carried")
        cls.s = fg.summarise(cls.pool)

    def test_carried_window_flagged(self):
        self.assertEqual(self.carried["still_windows"], 1)
        self.assertEqual(self.carried["still_windows_travelled"], 1)
        self.assertEqual(self.carried["jumps"], 0)
        w = [w for w in self.pool["windows"] if w["ride"] == "carried"]
        self.assertTrue(w[0]["travelled"])
        self.assertTrue(55.0 < w[0]["rms_by_lag"]["60"] < 65.0, w[0])

    def test_counts(self):
        st = self.s["still"]
        self.assertEqual(st["windows"], 25)
        self.assertEqual(st["rides"], 5)
        cl = st["clean"]
        self.assertEqual(cl["windows_left_out"], 1)
        self.assertEqual(cl["rides_left_out"], 1)
        self.assertEqual(cl["windows"], 24)
        self.assertEqual(cl["rides"], 4)
        self.assertEqual(cl["not_frozen"]["rides"], 4)
        self.assertLess(cl["share_beyond_m"]["10.0"], st["share_beyond_m"]["10.0"])

    def test_clean_fit(self):
        cl = self.s["still"]["clean"]
        gm = cl["gauss_markov"]
        self.assertTrue(1.5 < gm["sigma_m"] < 2.5, gm)
        self.assertTrue(12.0 < gm["T_s"] < 75.0, gm)
        every = {r["lag_s"]: r["rms_m"] for r in self.s["still"]["rms_displacement_m"]}
        clean = {r["lag_s"]: r["rms_m"] for r in cl["rms_displacement_m"]}
        self.assertGreater(every[60], 1.5 * clean[60])

    def test_outputs_use_clean_fit(self):
        with tempfile.TemporaryDirectory() as d:
            res = fg.write_outputs(d, [{"part": "x", "bytes_read": 5}], [{"ride_id": "1"}], self.pool, 0.0)
            gm = self.s["still"]["clean"]["gauss_markov"]
            self.assertEqual(res["sim_suggestion"]["gps_noise_m"], gm["sigma_m"])
            self.assertEqual(res["sim_suggestion"]["fit_ok"], fg.fit_ok(gm))
            self.assertTrue(any("Leaving out 1 still periods" in line for line in res["conclusions"]))
            with open(os.path.join(d, "report.md")) as f:
                self.assertIn("Clean: still periods", f.read())
            with open(os.path.join(d, "windows.jsonl")) as f:
                rows = [json.loads(line) for line in f]
            self.assertEqual(sum(1 for r in rows if r["travelled"]), 1)


class WhiteTests(unittest.TestCase):
    """A rover whose GPS has independent 1 m noise per axis, mostly driving straight."""

    @classmethod
    def setUpClass(cls):
        cls.pool = fg.new_pool()
        for i in range(3):
            control, gps = synthetic_ride([(120, True), (40, False)] * 5, white(1.0), seed=10 + i)
            fg.analyse_ride(control, gps, cls.pool, ride=str(i))
        cls.s = fg.summarise(cls.pool)

    def test_straight(self):
        sr = self.s["straight"]
        self.assertTrue(150 <= sr["chunks"] <= 165, sr)
        self.assertTrue(0.7 < sr["lateral_rms_m"] < 1.1, sr)
        self.assertTrue(0.93 < sr["gps_over_wheel_speed"]["median"] < 1.07, sr)
        self.assertTrue(0.6 < sr["wheel_speed_mps_median"] < 0.7, sr)

    def test_white_still(self):
        rows = {r["lag_s"]: r["rms_m"] for r in self.s["still"]["rms_displacement_m"]}
        self.assertTrue(1.7 < rows[1] < 2.3, rows)
        self.assertNotIn(60, rows)

    def test_outputs(self):
        with tempfile.TemporaryDirectory() as d:
            res = fg.write_outputs(d, [{"part": "x", "bytes_read": 5}], [{"ride_id": "1"}], self.pool, 0.0)
            self.assertTrue(res["conclusions"])
            with open(os.path.join(d, "summary.json")) as f:
                self.assertEqual(json.load(f)["version"], fg.__version__)
            for name in ("report.md", "rides.jsonl", "windows.jsonl"):
                self.assertTrue(os.path.exists(os.path.join(d, name)), name)


class JumpTests(unittest.TestCase):
    def test_jump_and_gap(self):
        control = [(START + i * 0.1, 0.0, 0.0, [0.0] * 4) for i in range(3000)]
        gps = []
        for j in range(300):
            if 200 < j < 210:
                continue
            e = 40.0 if j == 100 else (0.3 if j % 2 else 0.0)
            lat, lon = to_latlon(e, 0.0)
            gps.append((START + j + 0.3, lat, lon))
        pool = fg.new_pool()
        st = fg.analyse_ride(control, gps, pool)
        self.assertEqual(st["jumps"], 2)
        self.assertEqual(st["jumps_while_still"], 2)
        self.assertEqual(st["gaps"], 1)
        self.assertTrue(9.5 < st["gap_s"] < 10.5, st)
        self.assertEqual(st["still_windows"], 1)


class PartTests(unittest.TestCase):
    def test_process_part(self):
        control, gps = synthetic_ride([(120, True), (40, False)] * 2, white(1.0), seed=3)
        cbuf, gbuf = io.StringIO(), io.StringIO()
        cw, gw = csv.writer(cbuf), csv.writer(gbuf)
        cw.writerow(["linear", "angular", "rpm_1", "rpm_2", "rpm_3", "rpm_4", "timestamp"])
        for t, lin, ang, rpm in control:
            cw.writerow([lin, ang] + rpm + [int(round(t * 1000))])
        gw.writerow(["latitude", "longitude", "timestamp"])
        for t, lat, lon in gps:
            gw.writerow([lat, lon, int(round(t * 1000))])
        mem = io.BytesIO()
        with zipfile.ZipFile(mem, "w", zipfile.ZIP_DEFLATED) as z:
            base = "output_rides_0/ride_123_20240101000000/"
            z.writestr(base + "control_data_123.csv", cbuf.getvalue())
            z.writestr(base + "gps_data_123.csv", gbuf.getvalue())
            z.writestr(base + "front_camera.mp4", b"\x00" * 100)
        blob = mem.getvalue()
        rz = fm.RemoteZip(len(blob), lambda s, k: blob[s:s + k])
        pool, rides = fg.new_pool(), []
        info = fg.process_part(rz, "output_rides_0", 5, pool, rides)
        self.assertEqual(info["rides_sampled"], 1)
        self.assertEqual(len(rides), 1)
        self.assertNotIn("error", rides[0])
        self.assertEqual(rides[0]["ride_id"], "123")
        self.assertGreater(rides[0]["straight_chunks"], 10)
        self.assertEqual(rides[0]["still_windows"], 2)


if __name__ == "__main__":
    unittest.main()
