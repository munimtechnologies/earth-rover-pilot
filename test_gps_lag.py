"""Tests for the late-GPS compensator and the simulator's real-rover profile.

Run: python -m unittest test_gps_lag -v
"""

import io
import os
import sys
import unittest
from contextlib import redirect_stdout
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import rover_pilot as rp  # noqa: E402


class FakePilot:
    """Stands in for rp.Pilot and records what main() built it with."""
    seen = {}

    def __init__(self, rover, **kw):
        FakePilot.seen = dict(kw, rover=rover)

    def run(self, start=True, timeout_s=3600.0):
        return {"ok": True, "reason": "mission completed"}


class LagCompensatorTests(unittest.TestCase):
    def test_no_commands_no_offset(self):
        lag = rp.LagCompensator(1.5, cmd_latency_s=0.8, speed_mps=1.0)
        self.assertEqual(lag.offset(10.0, 9.0), (0.0, 0.0))

    def test_straight_east(self):
        lag = rp.LagCompensator(1.5, cmd_latency_s=0.8, speed_mps=1.0)
        for k in range(51):  # full ahead, heading east, t = 0.0 .. 5.0
            lag.record(k / 10.0, 1.0, 90.0)
        north, east = lag.offset(5.0, 4.0)
        # Commands between 4.0 - 1.5 - 0.8 = 1.7 and 5.0 - 0.8 = 4.2: 2.5 s at 1 m/s.
        self.assertAlmostEqual(east, 2.5, delta=0.01)
        self.assertAlmostEqual(north, 0.0, delta=1e-9)

    def test_older_fix_means_more_offset(self):
        lag = rp.LagCompensator(1.5, cmd_latency_s=0.8, speed_mps=1.0)
        for k in range(51):
            lag.record(k / 10.0, 1.0, 0.0)
        fresh, _ = lag.offset(5.0, 5.0)
        stale, _ = lag.offset(5.0, 4.0)
        self.assertAlmostEqual(fresh, 1.5, delta=0.01)
        self.assertAlmostEqual(stale, 2.5, delta=0.01)

    def test_stop_and_reverse(self):
        lag = rp.LagCompensator(1.0, cmd_latency_s=0.0, speed_mps=2.0)
        lag.record(0.0, 1.0, 0.0)    # north at 2 m/s for 1 s
        lag.record(1.0, 0.0, 0.0)    # stopped for 1 s
        lag.record(2.0, -0.5, 0.0)   # back at 1 m/s for 1 s
        north, east = lag.offset(3.0, 1.0)  # commands from 0.0 to 3.0
        self.assertAlmostEqual(north, 1.0, delta=1e-9)
        self.assertAlmostEqual(east, 0.0, delta=1e-9)

    def test_unknown_heading_is_skipped(self):
        lag = rp.LagCompensator(1.0, cmd_latency_s=0.0, speed_mps=1.0)
        lag.record(0.0, 1.0, None)
        self.assertEqual(lag.offset(1.0, 1.0), (0.0, 0.0))

    def test_old_commands_are_dropped(self):
        lag = rp.LagCompensator(1.0, cmd_latency_s=0.5, speed_mps=1.0)
        for k in range(1000):
            lag.record(k * 0.1, 1.0, 0.0)
        self.assertLess(len(lag._cmds), 200)


class SimDelayTests(unittest.TestCase):
    def drive_north(self, **kw):
        sim = rp.SimRover([(100.0, 0.0)], heading_deg=0.0, max_speed_mps=1.0, latency_s=0.0,
                          gps_noise_m=0.0, gps_dropout=0.0, compass_noise_deg=0.0, **kw)
        for _ in range(100):  # 10 s at full speed
            sim.control(1.0, 0.0)
            sim.sleep(0.1)
        _, gps_north = rp.to_enu(sim.lat0, sim.lon0, sim.gps[0], sim.gps[1])
        return sim, gps_north

    def test_no_delay(self):
        sim, gps_north = self.drive_north()
        self.assertAlmostEqual(sim.north, 10.0, delta=0.2)
        self.assertAlmostEqual(gps_north, 10.0, delta=0.2)
        self.assertAlmostEqual(sim.travelled, 10.0, delta=0.2)

    def test_gps_shows_where_the_rover_was(self):
        sim, gps_north = self.drive_north(gps_delay_s=1.5)
        self.assertAlmostEqual(sim.north, 10.0, delta=0.2)
        self.assertAlmostEqual(gps_north, 8.5, delta=0.2)

    def test_delay_keeps_the_noise_sequence(self):
        # A rover standing still reads the same noisy fixes with or without a delay,
        # so adding the option doesn't change the random numbers a run draws.
        a = rp.SimRover([(10.0, 0.0)], seed=3)
        b = rp.SimRover([(10.0, 0.0)], seed=3, gps_delay_s=1.5)
        for _ in range(5):
            self.assertEqual(a.gps, b.gps)
            a.sleep(1.0)
            b.sleep(1.0)


class PilotLagTests(unittest.TestCase):
    def fly(self, seed, sim_kw, pilot_kw):
        sim = rp.SimRover(rp.DEMO_MISSION, seed=seed, **sim_kw)
        pilot = rp.Pilot(sim, clock=sim.clock, sleep=sim.sleep, **pilot_kw)
        return sim, pilot.run(timeout_s=1500.0)

    def test_zero_lag_is_the_plain_pilot(self):
        _, a = self.fly(2, {}, {})
        _, b = self.fly(2, {}, {"gps_lag_s": 0.0})
        self.assertEqual(a, b)

    def test_real_like_rover_with_and_without_compensation(self):
        for kw in ({}, {"gps_lag_s": 1.5}):
            _, res = self.fly(1, rp.SIM_REAL, kw)
            self.assertTrue(res["ok"], (kw, res))
            self.assertEqual(res["reached"], [1, 2, 3, 4])

    def test_compensated_position_runs_ahead_of_the_fix(self):
        sim = rp.SimRover([(200.0, 0.0)], heading_deg=0.0, compass_error_deg=0.0,
                          gps_noise_m=0.0, gps_dropout=0.0, **rp.SIM_REAL)
        pilot = rp.Pilot(sim, clock=sim.clock, sleep=sim.sleep, gps_lag_s=1.5)
        pilot.run(timeout_s=60.0)  # times out half way along the 200 m leg
        _, fix_north = rp.to_enu(sim.lat0, sim.lon0, *pilot.gps.raw)
        _, pos_north = rp.to_enu(sim.lat0, sim.lon0, *pilot.pos)
        self.assertGreater(pos_north, fix_north + 0.3)
        self.assertLess(abs(pos_north - sim.north), abs(fix_north - sim.north))


class CliTests(unittest.TestCase):
    def run_main(self, argv):
        buf = io.StringIO()
        with mock.patch.object(rp, "Pilot", FakePilot), redirect_stdout(buf):
            code = rp.main(argv)
        return code, FakePilot.seen

    def test_gps_lag_is_off_by_default(self):
        code, seen = self.run_main(["--sdk", "http://x"])
        self.assertEqual(code, 0)
        self.assertEqual(seen["gps_lag_s"], 0.0)

    def test_gps_lag_and_real_sim(self):
        code, seen = self.run_main(["--simulate", "--sim-real", "--gps-lag", "1.5"])
        self.assertEqual(code, 0)
        self.assertEqual(seen["gps_lag_s"], 1.5)
        self.assertEqual(seen["rover"].max_speed_mps, 0.79)
        self.assertEqual(seen["rover"].gps_delay_s, 1.5)
        self.assertEqual(seen["rover"].latency_s, 0.8)

    def test_real_sim_flies_the_demo(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = rp.main(["--simulate", "--sim-real", "--gps-lag", "1.5"])
        self.assertEqual(code, 0, buf.getvalue()[-500:])


if __name__ == "__main__":
    unittest.main()
