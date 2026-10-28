"""Tests for frodo_regap2, on rides whose GPS is exact except where a test moves it."""

import csv
import io
import json
import math
import os
import tempfile
import unittest
import zipfile

import frodo_motion as fm
import frodo_regap2 as f2
import rover_pilot as rp

START = 1715000000.0
LAT0, LON0 = 37.0, -122.0
K = math.pi / 180.0 * fm.R_EARTH
V = 100.0 * f2.fr.MPS_PER_RPM     # 0.668 m/s at 100 RPM
# alpha 0.3 on a fix every 1 s at V: the average settles (1 - a) V / a behind
LAG = 0.7 * V / 0.3               # 1.5587 m
AFTER_GAP = 0.7 * (LAG + 10 * V)  # 5.767 m behind just after a 10 s gap
AT_SECOND = 0.7 * (AFTER_GAP + V)  # 4.5045 m behind one fix later


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
        e, n = V * (t - START - f2.fr.GPS_LAG_S), 0.0
        if moved and j in moved:
            e, n = e + moved[j][0], n + moved[j][1]
        lat, lon = to_latlon(e, n)
        gps.append((t, lat, lon))
    return control, gps


class FilterTests(unittest.TestCase):
    def test_restart_on_agreeing_second_fix(self):
        keep, c = rp.GpsFilter(), f2.ConfirmGpsFilter()
        for f in (keep, c):
            f.update(37.0, -122.0, 0.0)
            f.update(37.0001, -122.0, 1.0)
            self.assertIsNotNone(f.update(37.0002, -122.0, 6.0))
        self.assertTrue(c.pending)
        self.assertEqual((c.lat, c.lon), (keep.lat, keep.lon))   # the first fix is only averaged
        c.update(37.00021, -122.0, 7.0)                           # 1.1 m from the first: agrees
        self.assertAlmostEqual(c.lat, 37.00021, places=9)
        self.assertFalse(c.pending)
        self.assertEqual(c.restarts, 1)

    def test_disagreeing_second_fix_waits(self):
        keep, c = rp.GpsFilter(), f2.ConfirmGpsFilter()
        for f in (keep, c):
            f.update(37.0, -122.0, 0.0)
            f.update(37.0001, -122.0, 1.0)
            f.update(37.0002, -122.0, 6.0)
            self.assertIsNotNone(f.update(37.0003, -122.0, 7.0))  # 11.1 m from the first
        self.assertTrue(c.pending)
        self.assertEqual(c.restarts, 0)
        self.assertEqual((c.lat, c.lon), (keep.lat, keep.lon))
        c.update(37.00031, -122.0, 8.0)                           # 1.1 m from the second
        self.assertAlmostEqual(c.lat, 37.00031, places=9)
        self.assertEqual(c.restarts, 1)

    def test_no_gap_no_restart(self):
        keep, c = rp.GpsFilter(), f2.ConfirmGpsFilter()
        for k in range(6):
            for f in (keep, c):
                f.update(37.0 + 0.00001 * k, -122.0, 2.0 * k)
        self.assertFalse(c.pending)
        self.assertEqual(c.restarts, 0)
        self.assertEqual((keep.lat, keep.lon), (c.lat, c.lon))


class ChooseTests(unittest.TestCase):
    def test_leaves_out_the_first_pick(self):
        usable = ["r%02d" % i for i in range(10)]
        first = fm.pick_evenly(usable, 2)
        got = f2.choose(usable, 3, 2)
        self.assertEqual(len(got), 3)
        self.assertFalse(set(got) & set(first))

    def test_nothing_left(self):
        self.assertEqual(f2.choose(["a"], 5, 60), [])
        self.assertEqual(f2.choose(["a"], 5, 0), ["a"])


class RideTests(unittest.TestCase):
    """A rover driving east at V with exact GPS and one 10 s gap."""

    @classmethod
    def setUpClass(cls):
        cls.pool = f2.new_pool()
        control, gps = driving_ride()
        cls.st = f2.analyse_ride(control, gps, cls.pool, no=0)
        cls.ev = cls.pool["rides"][0]["events"][0]

    def test_counts(self):
        self.assertEqual(self.st["gaps"], 1)
        self.assertEqual(self.st["first_fixes"], 1)
        self.assertEqual(self.st["first_fixes_scored"], 1)
        self.assertEqual(self.st["second_fixes"], 1)
        self.assertEqual(self.st["second_fixes_scored"], 1)
        self.assertGreaterEqual(self.st["baseline"], 15)

    def test_first_fix(self):
        ev = self.ev
        self.assertEqual(ev["gap_s"], 10.0)
        self.assertLess(ev["r_first_m"], 0.01)
        self.assertLess(ev["restart_m"], 0.01)
        self.assertTrue(AFTER_GAP - 0.05 < ev["keep_m"] < AFTER_GAP + 0.05, ev)
        self.assertEqual(ev["confirm_m"], ev["keep_m"])

    def test_second_fix(self):
        ev = self.ev
        self.assertEqual(ev["dt2_s"], 1.0)
        self.assertTrue(ev["agree"])
        self.assertEqual(ev["confirm_after_s"], 1.0)
        self.assertLess(ev["r_second_m"], 0.01)
        self.assertLess(ev["confirm2_m"], 0.01)
        self.assertTrue(0.7 * V - 0.03 < ev["restart2_m"] < 0.7 * V + 0.03, ev)
        self.assertTrue(AT_SECOND - 0.05 < ev["keep2_m"] < AT_SECOND + 0.05, ev)


class FarFixTests(unittest.TestCase):
    """The same ride, but the first fix after the gap is 8 m north of the line."""

    @classmethod
    def setUpClass(cls):
        cls.pool = f2.new_pool()
        control, gps = driving_ride(moved={160: (0.0, 8.0)})
        cls.st = f2.analyse_ride(control, gps, cls.pool)
        cls.ev = cls.pool["rides"][0]["events"][0]

    def test_far_first_fix_refused(self):
        ev = self.ev
        self.assertTrue(7.95 < ev["r_first_m"] < 8.05, ev)
        self.assertFalse(ev["agree"])
        self.assertEqual(ev["confirm_after_s"], 2.0)
        self.assertEqual(ev["confirm2_m"], ev["keep2_m"])
        # keep: 4.5045 m behind east and 0.7 * 0.3 * 8 = 1.68 m north
        want = math.hypot(AT_SECOND, 1.68)
        self.assertTrue(want - 0.05 < ev["keep2_m"] < want + 0.05, ev)
        # restart: 0.7 V behind east and 0.7 * 8 = 5.6 m north
        want = math.hypot(0.7 * V, 5.6)
        self.assertTrue(want - 0.05 < ev["restart2_m"] < want + 0.05, ev)

    def test_summary_counts_the_refusal(self):
        s = f2.summarise(self.pool, final=False)
        self.assertEqual(s["far_first"]["n"], 1)
        self.assertEqual(s["far_first"]["share_refused"], 1.0)
        self.assertEqual(s["second"]["share_agree"], 0.0)
        self.assertEqual(s["confirm"]["median_after_s"], 2.0)
        self.assertEqual(s["at2"]["share_restart_far"], 1.0)
        self.assertEqual(s["at2"]["share_confirm_far"], 0.0)


class SummaryTests(unittest.TestCase):
    @staticmethod
    def pool(n_rides, first=1.2, base=1.0, keep2=4.0, restart2=1.5, confirm2=(1.0,),
             drove=5.0, gaps_each=2):
        pool = f2.new_pool()
        for i in range(n_rides):
            ev = {"no": i, "drove_m": drove, "jump_m": 3.0, "r_first_m": first, "keep_m": keep2,
                  "restart_m": first, "confirm_m": keep2, "dt2_s": 1.0, "agree": True,
                  "confirm_after_s": 1.0, "r_second_m": 1.0, "keep2_m": keep2,
                  "restart2_m": restart2, "confirm2_m": confirm2[i % len(confirm2)]}
            pool["rides"].append({"no": i, "events": [ev], "base": [{"r_m": base, "keep_m": 1.0}] * 3})
            pool["gps_s"] += 3600.0
            pool["gaps"].extend([5.0] * gaps_each)
        return pool

    def test_safe_and_helps(self):
        s = f2.summarise(self.pool(80))
        self.assertEqual(s["gaps"]["per_hour"], 2.0)
        self.assertEqual(s["ratio_median"], 1.2)
        self.assertEqual(s["at2"]["n"], 80)
        self.assertEqual(s["drove2"]["n"], 80)
        self.assertEqual(s["still2"]["n"], 0)
        d = f2.decide(s)
        self.assertTrue(d["check"]["ok"])
        self.assertFalse(d["d1_fails_again"])
        self.assertTrue(d["d3_confirm_safe"])
        self.assertTrue(d["d4_confirm_helps"])
        self.assertIn("earns", d["verdict"])

    def test_first_fix_fails_again(self):
        d = f2.decide(f2.summarise(self.pool(80, first=2.0)))
        self.assertTrue(d["d1_fails_again"])

    def test_helps_but_far(self):
        s = f2.summarise(self.pool(80, keep2=7.0, restart2=7.0, confirm2=(1.0, 6.0)))
        self.assertEqual(s["at2"]["share_confirm_far"], 0.5)
        self.assertEqual(s["drove2"]["median_confirm_m"], 6.0)
        d = f2.decide(s)
        self.assertFalse(d["d3_confirm_safe"])
        self.assertTrue(d["d4_confirm_helps"])
        self.assertIn("too many", d["verdict"])

    def test_no_help(self):
        d = f2.decide(f2.summarise(self.pool(80, keep2=1.0, restart2=1.0, confirm2=(3.5,))))
        self.assertTrue(d["d3_confirm_safe"])
        self.assertFalse(d["d4_confirm_helps"])
        self.assertIn("does not land nearer", d["verdict"])

    def test_check_fails(self):
        d = f2.decide(f2.summarise(self.pool(80, gaps_each=5)))
        self.assertFalse(d["check"]["ok"])
        self.assertIn("gaps per hour", d["check"]["why"])
        d = f2.decide(f2.summarise(self.pool(30)))
        self.assertFalse(d["check"]["ok"])
        self.assertIn("fewer than", d["check"]["why"])
        self.assertNotIn("verdict", d)

    def test_outputs(self):
        with tempfile.TemporaryDirectory() as d:
            res = f2.write_outputs(d, [{"part": "x", "bytes_read": 5}], [{"ride_id": "1"}],
                                   self.pool(80), 0.0, fetched={"rover_pilot": "0.19.0"})
            self.assertTrue(res["decision"]["d4_confirm_helps"])
            self.assertTrue(any(line.startswith("Verdict: ") for line in res["conclusions"]))
            with open(os.path.join(d, "summary.json")) as f:
                got = json.load(f)
            self.assertEqual(got["version"], f2.__version__)
            self.assertEqual(got["settings"]["agree_m"], 2.0)
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
        pool, rides = f2.new_pool(), []
        info = f2.process_part(rz, "output_rides_0", 5, pool, rides, skip_first=0)
        self.assertEqual(info["rides_sampled"], 1)
        self.assertNotIn("error", rides[0])
        self.assertEqual(rides[0]["ride_id"], "123")
        self.assertEqual(rides[0]["second_fixes_scored"], 1)
        info = f2.process_part(rz, "output_rides_0", 5, f2.new_pool(), [])
        self.assertEqual(info["rides_sampled"], 0)   # its only ride is one frodo-regap-v1 read


if __name__ == "__main__":
    unittest.main()
