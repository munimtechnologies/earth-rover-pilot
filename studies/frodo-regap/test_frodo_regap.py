"""Tests for frodo_regap, on rides whose GPS is exact except where a test moves it."""

import csv
import io
import json
import math
import os
import tempfile
import unittest
import zipfile

import frodo_motion as fm
import frodo_regap as fr
import rover_pilot as rp

START = 1715000000.0
LAT0, LON0 = 37.0, -122.0
K = math.pi / 180.0 * fm.R_EARTH
V = 100.0 * fr.MPS_PER_RPM        # 0.668 m/s at 100 RPM
# alpha 0.3 on a fix every 1 s at V: the average settles (1 - a) V / a behind
LAG = 0.7 * V / 0.3               # 1.5587 m
AFTER_GAP = 0.7 * (LAG + 10 * V)  # 5.767 m behind just after a 10 s gap


def to_latlon(e, n):
    return LAT0 + n / K, LON0 + e / (K * math.cos(math.radians(LAT0)))


def driving_ride(seconds=300, skip=range(151, 160), moved=None):
    """Control at 10 Hz at 100 RPM, and a GPS row every second (none at the
    seconds in skip) showing exactly where the rover was GPS_LAG_S earlier,
    driving east at V. moved maps a second to an (east, north) offset."""
    control = [(START + i * 0.1, 0.8, 0.0, [100.0] * 4) for i in range(seconds * 10)]
    gps = []
    for j in range(2, seconds):
        if j in skip:
            continue
        t = START + j + 0.3
        e, n = V * (t - START - fr.GPS_LAG_S), 0.0
        if moved and j in moved:
            e, n = e + moved[j][0], n + moved[j][1]
        lat, lon = to_latlon(e, n)
        gps.append((t, lat, lon))
    return control, gps


class FilterTests(unittest.TestCase):
    def test_restart_after_gap(self):
        keep, restart = rp.GpsFilter(), fr.RestartGpsFilter()
        for f in (keep, restart):
            f.update(37.0, -122.0, 0.0)
            f.update(37.0001, -122.0, 1.0)
        self.assertAlmostEqual(keep.lat, 37.00003, places=9)
        self.assertAlmostEqual(restart.lat, 37.00003, places=9)
        for f in (keep, restart):
            self.assertIsNotNone(f.update(37.0002, -122.0, 6.0))
        self.assertAlmostEqual(keep.lat, 37.000081, places=9)
        self.assertAlmostEqual(restart.lat, 37.0002, places=9)
        self.assertFalse(restart.pending)
        for f in (keep, restart):
            f.update(37.0003, -122.0, 7.0)
        self.assertAlmostEqual(restart.lat, 37.00023, places=9)

    def test_restart_waits_for_a_new_fix(self):
        keep, restart = rp.GpsFilter(), fr.RestartGpsFilter()
        for f in (keep, restart):
            f.update(37.0, -122.0, 0.0)
            f.update(37.0001, -122.0, 1.0)
            self.assertIsNone(f.update(37.0001, -122.0, 5.0))   # the old fix again, after a gap
        self.assertTrue(restart.pending)
        self.assertAlmostEqual(restart.lat, 37.00003, places=9)
        for f in (keep, restart):
            self.assertIsNotNone(f.update(37.0002, -122.0, 6.0))
        self.assertAlmostEqual(restart.lat, 37.0002, places=9)
        self.assertAlmostEqual(keep.lat, 37.000081, places=9)

    def test_no_gap_no_restart(self):
        keep, restart = rp.GpsFilter(), fr.RestartGpsFilter()
        for k in range(6):
            for f in (keep, restart):
                f.update(37.0 + 0.00001 * k, -122.0, 2.0 * k)
        self.assertFalse(restart.pending)
        self.assertEqual((keep.lat, keep.lon), (restart.lat, restart.lon))


class HelperTests(unittest.TestCase):
    def test_new_positions(self):
        track = [(0.0, 0.0, 0.0), (0.5, 0.0, 0.0), (1.0, 1.0, 0.0), (1.5, 1.0, 0.0), (2.0, 0.0, 0.0)]
        self.assertEqual(fr.new_positions(track), [(0.0, 0.0, 0.0), (1.0, 1.0, 0.0), (2.0, 0.0, 0.0)])

    def test_ref_at_line(self):
        track = [(float(t), 2.0 * (t - 100), 1.0) for t in range(100, 113)]
        times = [p[0] for p in track]
        e, n = fr.ref_at(track, times, times, 100.0)
        self.assertAlmostEqual(e, 0.0, places=9)
        self.assertAlmostEqual(n, 1.0, places=9)

    def test_ref_at_needs_points_and_no_gap(self):
        track = [(float(t), 2.0 * (t - 100), 1.0) for t in range(100, 113)]
        times = [p[0] for p in track]
        self.assertIsNone(fr.ref_at(track[:5], times[:5], times[:5], 100.0))   # 102..104: 3 points
        holed = [p for p in track if not 104 < p[0] < 109]
        ht = [p[0] for p in holed]
        self.assertIsNone(fr.ref_at(holed, ht, ht, 100.0))                     # a 5 s gap
        self.assertIsNone(fr.ref_at(holed, ht, ht, 106.0))                     # 109..112 span 3 s

    def test_too_little(self):
        pool = fr.new_pool()
        st = fr.analyse_ride([(START, 0.0, 0.0, [0.0] * 4)] * 10, [(START, LAT0, LON0)], pool)
        self.assertEqual(st["skipped"], "too little data")
        self.assertEqual(pool["rides"], [])


class RideTests(unittest.TestCase):
    """A rover driving east at V with exact GPS and one 10 s gap."""

    @classmethod
    def setUpClass(cls):
        cls.pool = fr.new_pool()
        control, gps = driving_ride()
        cls.st = fr.analyse_ride(control, gps, cls.pool, no=0)
        cls.ride = cls.pool["rides"][0]

    def test_counts(self):
        self.assertEqual(self.st["gaps"], 1)
        self.assertEqual(self.st["first_fixes"], 1)
        self.assertEqual(self.st["first_fixes_scored"], 1)
        self.assertGreaterEqual(self.st["baseline"], 15)
        self.assertAlmostEqual(self.pool["gaps"][0], 10.0, places=6)

    def test_first_fix(self):
        ev = self.ride["events"][0]
        self.assertEqual(ev["gap_s"], 10.0)
        self.assertEqual(ev["since_s"], 10.0)
        self.assertTrue(6.6 < ev["drove_m"] < 6.76, ev)
        self.assertTrue(6.6 < ev["jump_m"] < 6.76, ev)
        self.assertLess(ev["r_first_m"], 0.01)
        self.assertLess(ev["restart_m"], 0.01)
        self.assertTrue(AFTER_GAP - 0.05 < ev["keep_m"] < AFTER_GAP + 0.05, ev)

    def test_baseline(self):
        for b in self.ride["base"]:
            self.assertLess(b["r_m"], 0.01)
            self.assertTrue(LAG - 0.05 < b["keep_m"] < LAG + 0.05, b)


class FarFixTests(unittest.TestCase):
    """The same ride, but the first fix after the gap is 8 m north of the line."""

    def test_far_first_fix(self):
        pool = fr.new_pool()
        control, gps = driving_ride(moved={160: (0.0, 8.0)})
        st = fr.analyse_ride(control, gps, pool)
        self.assertEqual(st["first_fixes_scored"], 1)
        ev = pool["rides"][0]["events"][0]
        self.assertTrue(7.95 < ev["r_first_m"] < 8.05, ev)
        self.assertTrue(7.95 < ev["restart_m"] < 8.05, ev)
        # keep: AFTER_GAP behind east and 0.3 * 8 = 2.4 m north
        want = math.hypot(AFTER_GAP, 2.4)
        self.assertTrue(want - 0.05 < ev["keep_m"] < want + 0.05, ev)


class SummaryTests(unittest.TestCase):
    @staticmethod
    def pool(n_rides, first, base, keep, restart, drove=5.0, hours_each=1.0, gaps_each=2):
        pool = fr.new_pool()
        for i in range(n_rides):
            ev = [{"no": i, "drove_m": drove, "jump_m": 3.0, "r_first_m": first,
                   "keep_m": keep, "restart_m": restart}]
            pool["rides"].append({"no": i, "events": ev,
                                  "base": [{"r_m": base, "keep_m": 1.0}] * 3})
            pool["gps_s"] += 3600.0 * hours_each
            pool["gaps"].extend([5.0] * gaps_each)
        return pool

    def test_safe_and_helps(self):
        s = fr.summarise(self.pool(80, first=1.2, base=1.0, keep=4.0, restart=1.2))
        self.assertEqual(s["gaps"]["per_hour"], 2.0)
        self.assertEqual(s["ratio_median"], 1.2)
        self.assertEqual(s["ratio_ci95"], [1.2, 1.2])
        self.assertEqual(s["drove"]["n"], 80)
        self.assertEqual(s["still"]["n"], 0)
        d = fr.decide(s)
        self.assertTrue(d["check"]["ok"])
        self.assertTrue(d["d1_first_fix_ok"])
        self.assertTrue(d["d2_restart_helps"])
        self.assertIn("backs a restart", d["verdict"])

    def test_far_first_fixes(self):
        s = fr.summarise(self.pool(80, first=6.0, base=1.0, keep=4.0, restart=6.0))
        self.assertEqual(s["first"]["share_far"], 1.0)
        self.assertEqual(s["drove"]["share_restart_worse"], 0.0)
        d = fr.decide(s)
        self.assertFalse(d["d1_first_fix_ok"])
        self.assertIn("second fix", d["verdict"])

    def test_restart_worse(self):
        s = fr.summarise(self.pool(80, first=1.0, base=1.0, keep=1.0, restart=3.5))
        self.assertEqual(s["drove"]["share_restart_worse"], 1.0)
        d = fr.decide(s)
        self.assertTrue(d["d1_first_fix_ok"])
        self.assertFalse(d["d2_restart_helps"])
        self.assertIn("does not land nearer", d["verdict"])

    def test_check_fails(self):
        d = fr.decide(fr.summarise(self.pool(80, 1.0, 1.0, 2.0, 1.0, gaps_each=5)))
        self.assertFalse(d["check"]["ok"])
        self.assertIn("gaps per hour", d["check"]["why"])
        d = fr.decide(fr.summarise(self.pool(30, 1.0, 1.0, 2.0, 1.0)))
        self.assertFalse(d["check"]["ok"])
        self.assertIn("fewer than", d["check"]["why"])
        self.assertNotIn("verdict", d)

    def test_outputs(self):
        pool = self.pool(80, first=1.2, base=1.0, keep=4.0, restart=1.2)
        with tempfile.TemporaryDirectory() as d:
            res = fr.write_outputs(d, [{"part": "x", "bytes_read": 5}], [{"ride_id": "1"}], pool, 0.0,
                                   fetched={"rover_pilot": "0.19.0"})
            self.assertEqual(res["decision"]["d1_first_fix_ok"], True)
            self.assertTrue(any(line.startswith("Verdict: ") for line in res["conclusions"]))
            with open(os.path.join(d, "summary.json")) as f:
                got = json.load(f)
            self.assertEqual(got["version"], fr.__version__)
            self.assertEqual(got["fetched"], {"rover_pilot": "0.19.0"})
            with open(os.path.join(d, "events.jsonl")) as f:
                self.assertEqual(len(f.read().splitlines()), 80)
            self.assertTrue(os.path.exists(os.path.join(d, "report.md")))


class PartTests(unittest.TestCase):
    def test_process_part(self):
        control, gps = driving_ride()
        cbuf, gbuf = io.StringIO(), io.StringIO()
        cw, gw = csv.writer(cbuf), csv.writer(gbuf)
        cw.writerow(["linear", "angular", "rpm_1", "rpm_2", "rpm_3", "rpm_4", "timestamp"])
        for t, lin, ang, rpm in control:
            cw.writerow([lin, ang] + rpm + [int(round(t * 1000))])
        gw.writerow(["latitude", "longitude", "timestamp"])
        for t, lat, lon in gps:
            gw.writerow([repr(lat), repr(lon), int(round(t * 1000))])
        mem = io.BytesIO()
        with zipfile.ZipFile(mem, "w", zipfile.ZIP_DEFLATED) as z:
            base = "output_rides_0/ride_123_20240101000000/"
            z.writestr(base + "control_data_123.csv", cbuf.getvalue())
            z.writestr(base + "gps_data_123.csv", gbuf.getvalue())
            z.writestr(base + "front_camera.mp4", b"\x00" * 100)
        blob = mem.getvalue()
        rz = fm.RemoteZip(len(blob), lambda s, k: blob[s:s + k])
        pool, rides = fr.new_pool(), []
        info = fr.process_part(rz, "output_rides_0", 5, pool, rides)
        self.assertEqual(info["rides_sampled"], 1)
        self.assertNotIn("error", rides[0])
        self.assertEqual(rides[0]["ride_id"], "123")
        self.assertEqual(rides[0]["gaps"], 1)
        self.assertEqual(rides[0]["first_fixes_scored"], 1)


if __name__ == "__main__":
    unittest.main()
