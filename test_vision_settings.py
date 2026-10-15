"""Tests for the real-rover camera settings (free_space.REAL_ROVER, rover_pilot.make_vision).

Run: python -m unittest test_vision_settings -v
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import free_space as fs  # noqa: E402
import frodo_frames as ff  # noqa: E402
import rover_pilot as rp  # noqa: E402

CAM = fs.Camera()
SHADOW = (40, 40, 40)


def shadow_frame(rows=(24, 25, 26)):
    """Open grey ground with a hard shadow band across it about 1 m ahead
    (rows 24-26 of 36): a third of the ground's brightness, same colour."""
    f = fs.render(CAM, [])
    for v in rows:
        for u in range(CAM.width):
            f.pixels[v * CAM.width + u] = SHADOW
    return f


class RealRoverSettingsTests(unittest.TestCase):
    def test_settings_are_the_measured_variant(self):
        flat = dict(fs.REAL_ROVER["scan_kw"], skip_rows=fs.REAL_ROVER["skip_rows"],
                    gap=fs.REAL_ROVER["gap"])
        self.assertEqual(flat, ff.VARIANTS["skip3-shadow-wide-gap4"])

    def test_shadow_band_stops_the_default_guard(self):
        f = shadow_frame()
        plain = fs.VisionGuard(lambda: f, camera=CAM)
        _, scale = plain.advise(0.0, 0.0, 50.0)
        self.assertLess(plain.clear_ahead, 1.2)
        self.assertEqual(scale, 0.0)

    def test_shadow_band_is_ground_for_the_real_rover_guard(self):
        f = shadow_frame()
        real = fs.VisionGuard(lambda: f, camera=CAM, **fs.REAL_ROVER)
        self.assertEqual(real.advise(0.0, 0.0, 50.0), (0.0, 1.0))
        self.assertEqual(real.clear_ahead, 8.0)
        self.assertEqual(real.stops, 0)

    def test_real_rover_guard_still_sees_a_hedge(self):
        f = fs.render(CAM, [(0.0, 2.0, 0.6, 1.0, fs.HEDGE_GREEN)])
        real = fs.VisionGuard(lambda: f, camera=CAM, **fs.REAL_ROVER)
        advice = real.advise(0.0, 0.0, 50.0)
        self.assertLess(real.clear_ahead, 5.0)
        self.assertNotEqual(advice, (0.0, 1.0))


class MakeVisionTests(unittest.TestCase):
    def test_simulator_keeps_the_defaults(self):
        g = rp.make_vision(lambda: None, CAM, simulate=True)
        self.assertEqual((g.skip_rows, g.gap, g.scan_kw), (0, 2, {}))

    def test_real_rover_gets_real_rover_settings(self):
        g = rp.make_vision(lambda: None, CAM, simulate=False)
        self.assertEqual((g.skip_rows, g.gap), (3, 4))
        self.assertEqual(g.scan_kw, fs.REAL_ROVER["scan_kw"])
        g.scan_kw["lum_lo"] = 0.9                       # the guard's copy, not the constant
        self.assertEqual(fs.REAL_ROVER["scan_kw"]["lum_lo"], 0.2)

    def test_plain_on_a_real_rover(self):
        g = rp.make_vision(lambda: None, CAM, simulate=False, plain=True)
        self.assertEqual((g.skip_rows, g.gap, g.scan_kw), (0, 2, {}))


if __name__ == "__main__":
    unittest.main()
