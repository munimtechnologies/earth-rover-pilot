"""Tests for dead_reckon.py and the pilot that uses it (rover_pilot.py 0.10.0).

Apache-2.0. By MV2 of Munim, Inc.; written with AI agents.
"""

import contextlib
import io
import math
import unittest

import dead_reckon as dm
import rover_pilot as rp

LAT0, LON0 = 37.87, -122.26
MINI, ZERO = dm.MINI_PLUS_MPS_PER_RPM, dm.ZERO_MPS_PER_RPM


def latlon(e, n):
    return (LAT0 + n / dm.M_PER_DEG,
            LON0 + e / (dm.M_PER_DEG * math.cos(math.radians(LAT0))))


def en(lat, lon):
    return ((lon - LON0) * dm.M_PER_DEG * math.cos(math.radians(LAT0)),
            (lat - LAT0) * dm.M_PER_DEG)


def at(hist, t):
    """(east, north) of the last truth point at or before t (the first one before it)."""
    best = hist[0]
    for h in hist:
        if h[0] <= t + 1e-9:
            best = h
        else:
            break
    return best[1], best[2]


def drive(dr, legs, true_mps_per_rpm, fix_period=1.0, lag=1.5, dt=0.1, gps_off=(),
          wheel_gain=1.0, state=None):
    """Drive legs [(seconds, speed_mps, heading_deg)], feeding dr wheels, GPS (lag s
    late) and compass as a rover would. Returns the state: t, truth history."""
    s = state or {"t": 0.0, "e": 0.0, "n": 0.0, "hist": [(0.0, 0.0, 0.0)], "next_fix": 0.0}
    for seconds, speed, heading in legs:
        for _ in range(int(round(seconds / dt))):
            r = math.radians(heading)
            s["e"] += speed * dt * math.sin(r)
            s["n"] += speed * dt * math.cos(r)
            s["t"] = round(s["t"] + dt, 6)
            t = s["t"]
            s["hist"].append((t, s["e"], s["n"]))
            rpm = wheel_gain * speed / true_mps_per_rpm
            dr.wheels(t, [[rpm, rpm, rpm, rpm, 1000.0 + t]])
            fix = None
            if t >= s["next_fix"] - 1e-9:
                s["next_fix"] += fix_period
                if not any(a <= t < b for a, b in gps_off):
                    fix = latlon(*at(s["hist"], t - lag))
            dr.update(t, fix, heading, heading)
    return s


def miss(dr, s):
    pos = dr.position(s["t"])
    e, n = en(*pos)
    return math.hypot(e - s["e"], n - s["n"])


class WheelTest(unittest.TestCase):
    def test_distance_from_rows(self):
        dr = dm.DeadReckoner(mps_per_rpm=0.01)
        for k in range(11):
            dr.wheels(k * 0.1, [[100, 100, 100, 100, 50.0 + k * 0.1]])
        self.assertAlmostEqual(dr.distance(0.0, 1.0), 1.0, places=6)

    def test_cached_reading_adds_nothing(self):
        dr = dm.DeadReckoner()
        rows = [[10, 10, 10, 10, 5.0], [10, 10, 10, 10, 5.1]]
        dr.wheels(1.0, rows)
        dr.wheels(1.1, rows)
        self.assertEqual(len(dr._st), 2)

    def test_rows_placed_by_their_timestamps(self):
        dr = dm.DeadReckoner(mps_per_rpm=0.01, hold_s=5.0)
        # One reading with 2 s of rows, seen at t = 10: rows from 8 to 10.
        dr.wheels(10.0, [[0, 0, 0, 0, 100.0], [100, 100, 100, 100, 101.0],
                         [100, 100, 100, 100, 102.0]])
        self.assertEqual(dr._st, [8.0, 9.0, 10.0])
        self.assertAlmostEqual(dr.distance(8.0, 10.0), 1.0, places=6)

    def test_wheels_count_as_stopped_after_hold(self):
        dr = dm.DeadReckoner(mps_per_rpm=0.01, hold_s=3.0)
        dr.wheels(0.0, [[100, 100, 100, 100]])
        self.assertAlmostEqual(dr.distance(0.0, 10.0), 3.0, places=6)

    def test_bad_rows_ignored(self):
        dr = dm.DeadReckoner()
        dr.wheels(0.0, None)
        dr.wheels(0.0, [[1, 2], "x", [1, "a", 3, 4, 5], [float("nan"), 1, 1, 1, 2]])
        self.assertEqual(dr._st, [])

    def test_reverse_is_negative(self):
        dr = dm.DeadReckoner(mps_per_rpm=0.01)
        dr.wheels(0.0, [[-100, -100, -100, -100]])
        dr.wheels(1.0, [[-100, -100, -100, -100]])
        self.assertAlmostEqual(dr.distance(0.0, 1.0), -1.0, places=6)


class EstimateTest(unittest.TestCase):
    def test_straight_line_no_learning(self):
        dr = dm.DeadReckoner(mps_per_rpm=MINI, learn_scale=False)
        s = drive(dr, [(20.0, 0.5, 0.0)], MINI)
        self.assertLess(miss(dr, s), 0.15)
        # The last fix alone is 1.5 s (0.75 m) behind.
        last = en(*latlon(*at(s["hist"], s["t"] - 1.5)))
        self.assertGreater(math.hypot(last[0] - s["e"], last[1] - s["n"]), 0.6)

    def test_learns_wheel_size_and_then_trusts(self):
        dr = dm.DeadReckoner(mps_per_rpm=MINI)  # a Zero's wheels, a Mini+ prior
        s = drive(dr, [(15.0, 0.6, 30.0)], ZERO)
        self.assertIsNone(dr.position(s["t"]))
        self.assertFalse(dr.trusted)
        s = drive(dr, [(60.0, 0.6, 30.0)], ZERO, state=s)
        self.assertTrue(dr.trusted)
        self.assertAlmostEqual(dr.mps_per_rpm / ZERO, 1.0, delta=0.03)
        self.assertLess(miss(dr, s), 0.3)

    def test_zero_wheels_never_trusted(self):
        dr = dm.DeadReckoner()
        s = drive(dr, [(80.0, 0.6, 0.0)], MINI, wheel_gain=0.0)
        self.assertEqual(dr.scale_samples, 0)
        self.assertIsNone(dr.position(s["t"]))

    def test_implausible_wheels_rejected(self):
        dr = dm.DeadReckoner(mps_per_rpm=MINI)
        s = drive(dr, [(80.0, 0.6, 0.0)], MINI, wheel_gain=3.0)
        self.assertGreaterEqual(dr.scale_rejects, 1)
        self.assertEqual(dr.scale_samples, 0)
        self.assertIsNone(dr.position(s["t"]))

    def test_no_learning_on_a_curve(self):
        dr = dm.DeadReckoner(mps_per_rpm=MINI)
        legs = [(1.0, 0.6, h) for h in range(0, 360 * 2, 9)]  # a circle every 40 s
        drive(dr, legs, MINI)
        self.assertEqual(dr.scale_samples, 0)

    def test_turn_follows_the_compass(self):
        dr = dm.DeadReckoner(mps_per_rpm=MINI, learn_scale=False)
        s = drive(dr, [(10.0, 0.5, 0.0), (1.0, 0.0, 90.0), (2.0, 0.5, 90.0)], MINI)
        self.assertLess(miss(dr, s), 0.3)

    def test_heading_only(self):
        dr = dm.DeadReckoner(mps_per_rpm=MINI, learn_scale=False, use_course=False)
        s = drive(dr, [(10.0, 0.5, 45.0)], MINI)
        self.assertLess(miss(dr, s), 0.15)

    def test_gain_smooths_toward_fixes(self):
        dr = dm.DeadReckoner(mps_per_rpm=MINI, learn_scale=False, gain=0.3)
        s = drive(dr, [(20.0, 0.5, 0.0)], MINI)
        self.assertLess(miss(dr, s), 0.15)
        # A fix 3 m ahead of where the estimate was 1.5 s ago moves it 0.9 m,
        # plus the 0.05 m the wheels drove in the 0.1 s since.
        before = en(*dr.position(s["t"]))
        t = s["t"] + 0.1
        dr.update(t, latlon(before[0], before[1] - 0.75 + 3.0), 0.0, 0.0)
        after = en(*dr.position(t))
        self.assertAlmostEqual(after[1] - before[1], 0.3 * 2.95 + 0.05, delta=0.05)
        self.assertAlmostEqual(after[0], before[0], delta=0.05)

    def test_far_fix_resets(self):
        dr = dm.DeadReckoner(mps_per_rpm=MINI, learn_scale=False, gain=0.3)
        s = drive(dr, [(10.0, 0.5, 0.0)], MINI)
        t = s["t"] + 0.1
        dr.update(t, latlon(40.0, 0.0), 0.0, 0.0)
        self.assertEqual(dr.resets, 1)
        e, n = en(*dr.position(t))
        self.assertLess(math.hypot(e - 40.0, n - 0.0), 1.0)

    def test_estimate_expires_without_fixes(self):
        dr = dm.DeadReckoner(mps_per_rpm=MINI, learn_scale=False)
        s = drive(dr, [(45.0, 0.5, 0.0)], MINI, gps_off=[(20.0, 100.0)])
        self.assertIsNotNone(dr.position(s["t"]))  # 25 s without a fix
        self.assertLess(miss(dr, s), 0.5)
        s = drive(dr, [(10.0, 0.5, 0.0)], MINI, gps_off=[(0.0, 100.0)], state=s)
        self.assertIsNone(dr.position(s["t"]))  # 35 s


class GapRover(rp.SimRover):
    """SimRover with no GPS fix from gap[0] to gap[1] s."""

    def __init__(self, *a, gap=(40.0, 55.0), **kw):
        self.gap = gap
        super().__init__(*a, **kw)

    def _sample_gps(self):
        super()._sample_gps()
        if self.gap[0] <= self.t < self.gap[1]:
            self.gps = (rp.NO_FIX, rp.NO_FIX)


class PilotTest(unittest.TestCase):
    def test_version(self):
        self.assertEqual(rp.__version__, "0.11.2")

    def test_sim_rover_reports_wheels_only_when_asked(self):
        plain = rp.SimRover(rp.DEMO_MISSION, seed=1)
        self.assertNotIn("rpms", plain.data())
        sim = rp.SimRover(rp.DEMO_MISSION, seed=1, wheel_mps_per_rpm=MINI, rpm_period_s=1.0)
        sim.control(0.5, 0.0)
        sim.sleep(3.0)
        rows = sim.data()["rpms"]
        self.assertGreaterEqual(len(rows), 9)
        speed = sum(rows[-1][:4]) / 4.0 * MINI
        self.assertAlmostEqual(speed, 0.5 * sim.max_speed_mps, delta=0.01)

    def test_sim_rover_turning_wheels(self):
        sim = rp.SimRover(rp.DEMO_MISSION, seed=1, wheel_mps_per_rpm=MINI)
        sim.control(0.0, 0.5)  # turn right in place
        sim.sleep(1.5)
        row = sim.data()["rpms"][-1]
        self.assertGreater(row[0], 0)
        self.assertLess(row[1], 0)
        self.assertAlmostEqual(sum(row[:4]), 0.0, places=6)

    def test_mission_with_dead_reckoning(self):
        sim = rp.SimRover(rp.DEMO_MISSION, seed=3, wheel_mps_per_rpm=ZERO, **rp.SIM_REAL)
        pilot = rp.Pilot(sim, clock=sim.clock, sleep=sim.sleep,
                         steering=rp.make_steering(simulate=False),
                         dead_reckon=dm.DeadReckoner(mps_per_rpm=MINI))
        res = pilot.run(timeout_s=2000)
        self.assertTrue(res["ok"], res["reason"])
        self.assertIn("dead_reckon", res)
        self.assertGreater(res["dead_reckon"]["fixes"], 50)

    def test_drives_through_a_gps_gap(self):
        def fly(dr):
            sim = GapRover(rp.DEMO_MISSION, seed=2, wheel_mps_per_rpm=ZERO, **rp.SIM_REAL)
            pilot = rp.Pilot(sim, clock=sim.clock, sleep=sim.sleep,
                             steering=rp.make_steering(simulate=False), dead_reckon=dr)
            return pilot.run(timeout_s=2000)
        res = fly(dm.DeadReckoner(mps_per_rpm=ZERO, learn_scale=False))
        self.assertTrue(res["ok"], res["reason"])
        self.assertGreater(res["dead_reckon"]["bridged_s"], 5.0)
        base = fly(None)
        self.assertTrue(base["ok"])
        self.assertNotIn("dead_reckon", base)

    def test_not_with_gps_lag(self):
        with self.assertRaises(ValueError):
            rp.Pilot(rp.SimRover(rp.DEMO_MISSION), gps_lag_s=1.5,
                     dead_reckon=dm.DeadReckoner())
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                rp.main(["--simulate", "--dead-reckon", "--gps-lag", "1.5"])

    def test_command_line(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = rp.main(["--simulate", "--sim-real", "--dead-reckon", "--seed", "2"])
        self.assertEqual(code, 0, out.getvalue()[-500:])
        self.assertIn('"dead_reckon"', out.getvalue())


class TogetherTest(unittest.TestCase):
    """Battery log, leg levels, the marathon preset and dead reckoning in one mission."""

    def test_sim_mission_reports_battery_and_leg_levels(self):
        sim = rp.SimRover(rp.DEMO_MISSION, seed=1)
        pilot = rp.Pilot(sim, clock=sim.clock, sleep=sim.sleep,
                         steering=rp.make_steering(simulate=True))
        res = pilot.run(timeout_s=2000)
        self.assertTrue(res["ok"], res["reason"])
        battery = res["battery"]
        self.assertIsNone(battery["start_pct"])  # the simulator reports no battery
        self.assertGreater(battery["driven_m"], 10.0)
        self.assertTrue(res["legs"])
        self.assertTrue(all("battery_pct" in leg for leg in res["legs"]))

    def test_command_line_marathon_with_dead_reckoning(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = rp.main(["--simulate", "--sim-real", "--marathon", "--dead-reckon",
                            "--seed", "2"])
        self.assertEqual(code, 0, out.getvalue()[-500:])
        text = out.getvalue()
        self.assertIn('"dead_reckon"', text)
        self.assertIn('"battery"', text)


if __name__ == "__main__":
    unittest.main()
