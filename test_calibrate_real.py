"""Calibration on a simulated rover that moves like the FrodoBots-2K rovers.

They turn at about 30 deg/s per unit of angular (FINDINGS-frodobots-2k.md),
so a 30 s spin at 0.4 falls just short of a whole turn.

Run: python -m unittest test_calibrate_real -v
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import calibrate as cal  # noqa: E402
import rover_pilot as rp  # noqa: E402

REAL_LIKE = dict(rp.SIM_REAL, max_yaw_dps=30.0)


class RealLikeCalibrationTests(unittest.TestCase):
    def test_a_30_s_spin_is_not_enough(self):
        # 0.4 x 30 deg/s = 12 deg/s, for about 29 s once the 0.8 s latency is over: ~350 deg.
        sim = rp.SimRover(rp.DEMO_MISSION, seed=1, compass_noise_deg=0.0, **REAL_LIKE)
        # max_spin_s below spin_s: the 30 s spin and no more, as before this change.
        res = cal.calibrate(sim, clock=sim.clock, sleep=sim.sleep, max_spin_s=25.0)
        self.assertFalse(res["ok"])
        self.assertIn("full turn", res["reason"])

    def test_the_spin_goes_on_until_a_whole_turn(self):
        for seed, sign in ((1, 1.0), (2, -1.0)):
            with self.subTest(seed=seed, angular_sign=sign):
                # No compass noise, so the first 30 s fall short by the same ~10 deg every time.
                sim = rp.SimRover(rp.DEMO_MISSION, seed=seed, angular_sign=sign,
                                  compass_noise_deg=0.0, **REAL_LIKE)
                res = cal.calibrate(sim, clock=sim.clock, sleep=sim.sleep)
                self.assertTrue(res["ok"], res)
                self.assertEqual(res["orientation_scale"], 360.0)
                self.assertTrue(res["orientation_clockwise"])
                self.assertEqual(res["angular_right_positive"], sign > 0)
                self.assertGreater(res["spin_s"], 35.0)
                self.assertLess(res["spin_s"], 61.0)
                self.assertGreaterEqual(abs(res["spin_deg"]), 360.0)
                self.assertAlmostEqual(res["yaw_dps_at_full"], 30.0, delta=8.0)
                self.assertAlmostEqual(res["speed_mps_at_full"], 0.79, delta=0.4)
                self.assertEqual(sim.queue[-1][1:], (0.0, 0.0))  # the last command is a stop

    def test_the_simulator_rover_still_spins_30_s(self):
        sim = rp.SimRover(rp.DEMO_MISSION, seed=1)
        res = cal.calibrate(sim, clock=sim.clock, sleep=sim.sleep)
        self.assertTrue(res["ok"], res)
        self.assertLess(res["spin_s"], 30.5)


if __name__ == "__main__":
    unittest.main()
