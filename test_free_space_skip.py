"""Tests for free_space's skip_rows: leaving out the rover's own body at the bottom of the frame.

Run: python -m unittest test_free_space_skip -v
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import free_space as fs  # noqa: E402

CAM = fs.Camera()
BODY = (200, 60, 60)


def frame_with_body(rows=3, columns=tuple(range(20, 25)) + tuple(range(40, 45))):
    """Open grey ground, with the rover's body showing in the bottom `rows` rows
    of two bands of columns (like the rails on some FrodoBots-2K front frames)."""
    f = fs.render(CAM, [])
    for v in range(CAM.height - rows, CAM.height):
        for u in columns:
            f.pixels[v * CAM.width + u] = BODY
    return f


class SkipRowsTests(unittest.TestCase):
    def test_defaults_are_unchanged(self):
        f = fs.render(CAM, [(0.0, 3.0, 0.6, 1.0, fs.HEDGE_GREEN)], noise=fs.make_noise(seed=3))
        self.assertEqual(fs.ground_patch(f), fs.ground_patch(f, skip_rows=0))
        m = fs.GroundModel.fit(fs.ground_patch(f))
        self.assertEqual(fs.scan(f, CAM, m), fs.scan(f, CAM, m, gap=2, skip_rows=0))

    def test_body_in_view_reads_as_an_obstacle_by_default(self):
        f = frame_with_body()
        m = fs.GroundModel.fit(fs.ground_patch(f))
        pts = fs.scan(f, CAM, m)
        self.assertEqual(len(pts), CAM.width)          # every column stops at the bottom row
        self.assertLess(fs.clearance(pts, 0.0), 1.0)

    def test_skipping_the_body_rows_sees_open_ground(self):
        f = frame_with_body()
        m = fs.GroundModel.fit(fs.ground_patch(f, skip_rows=3))
        self.assertLess(m.spread, 1e-9)                 # the patch is clean ground now
        pts = fs.scan(f, CAM, m, skip_rows=3)
        self.assertEqual(pts, [])
        self.assertEqual(fs.clearance(pts, 0.0), 8.0)

    def test_guard_passes_skip_rows_on(self):
        f = frame_with_body()
        plain = fs.VisionGuard(lambda: f, camera=CAM)
        error, scale = plain.advise(0.0, 0.0, 50.0)
        self.assertEqual(scale, 0.0)                    # nothing clear for 1.2 m: turn in place
        self.assertEqual(plain.stops, 1)
        skipping = fs.VisionGuard(lambda: f, camera=CAM, skip_rows=3)
        self.assertEqual(skipping.advise(0.0, 0.0, 50.0), (0.0, 1.0))
        self.assertEqual(skipping.clear_ahead, 8.0)
        self.assertEqual(skipping.stops, 0)


if __name__ == "__main__":
    unittest.main()
