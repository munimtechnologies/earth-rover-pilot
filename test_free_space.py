"""Offline tests for free_space, the front-camera obstacle check (no rover needed).

Run: python -m unittest test_free_space -v
"""

import io
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import free_space as fs  # noqa: E402
import rover_pilot as rp  # noqa: E402

try:
    import PIL  # noqa: F401
    HAVE_PIL = True
except ImportError:
    HAVE_PIL = False

CAM = fs.Camera()


def frame(*obstacles, ground=fs.GROUND_GREY):
    """A rendered frame with (x, y, radius) hedges in the rover frame."""
    return fs.render(CAM, [(x, y, r, 1.0, fs.HEDGE_GREEN) for x, y, r in obstacles],
                     ground=ground)


def guard_over(frames, **kw):
    frames = list(frames)
    calls = []

    def source():
        calls.append(1)
        return frames.pop(0) if frames else None
    return fs.VisionGuard(source, camera=CAM, **kw), calls


class CameraTests(unittest.TestCase):
    def test_bottom_centre_is_just_ahead(self):
        x, y = CAM.ground_point(31, 35)
        self.assertLess(abs(x), 0.05)
        self.assertTrue(0.3 < y < 0.8, y)

    def test_top_rows_are_above_the_horizon(self):
        self.assertIsNone(CAM.ground_point(32, 0))
        self.assertIsNone(CAM.ground_point(32, 14))
        self.assertIsNotNone(CAM.ground_point(32, 16))

    def test_right_columns_are_to_the_right(self):
        self.assertGreater(CAM.ground_point(60, 30)[0], 0)
        self.assertLess(CAM.ground_point(3, 30)[0], 0)

    def test_ground_distance_matches_the_tilt(self):
        u, v = 32, 30
        b = (v + 0.5 - CAM.height / 2.0) / CAM.f
        want = CAM.height_m / math.tan(math.radians(CAM.pitch_deg) + math.atan(b))
        self.assertAlmostEqual(CAM.ground_point(u, v)[1], want, places=9)


class GroundModelTests(unittest.TestCase):
    def test_shadow_is_ground_and_hedge_is_not(self):
        matches = fs.GroundModel.fit([fs.GROUND_GREY] * 10).matcher()
        self.assertTrue(matches((128, 128, 128)))
        self.assertTrue(matches((70, 70, 70)))
        self.assertFalse(matches(fs.HEDGE_GREEN))
        self.assertFalse(matches((250, 250, 250)))


class ClearanceTests(unittest.TestCase):
    def test_corridor(self):
        self.assertEqual(fs.clearance([(0.0, 3.0)], 0.0), 3.0)
        self.assertEqual(fs.clearance([(0.3, 3.0)], 0.0), 3.0)
        self.assertEqual(fs.clearance([(0.5, 3.0)], 0.0), 8.0)
        self.assertEqual(fs.clearance([(0.0, 3.0)], 20.0), 8.0)
        self.assertEqual(fs.clearance([(0.0, -1.0)], 0.0), 8.0)
        self.assertEqual(fs.clearance([], 0.0), 8.0)


class ScanTests(unittest.TestCase):
    def model(self, f):
        return fs.GroundModel.fit(fs.ground_patch(f))

    def test_empty_scene_is_clear(self):
        f = frame()
        self.assertEqual(fs.scan(f, CAM, self.model(f)), [])

    def test_obstacle_ahead(self):
        f = frame((0.0, 4.5, 0.5))  # its near side is 4 m ahead
        pts = fs.scan(f, CAM, self.model(f))
        self.assertTrue(pts)
        ahead = fs.clearance(pts, 0.0)
        self.assertTrue(3.0 < ahead < 4.0, ahead)
        self.assertEqual(fs.clearance(pts, 30.0), 8.0)
        self.assertEqual(fs.clearance(pts, -30.0), 8.0)


class GuardTests(unittest.TestCase):
    def test_clear_view_leaves_heading_alone(self):
        g, _ = guard_over([frame()])
        self.assertEqual(g.advise(0.0, 12.0), (12.0, 1.0))
        self.assertEqual(g.avoidances, 0)

    def test_steers_around_on_the_nearer_side(self):
        g, _ = guard_over([frame((0.2, 4.5, 0.5))])  # a bit right of centre: go left
        error, scale = g.advise(0.0, 0.0)
        self.assertTrue(-40.0 <= error < 0.0, error)
        self.assertGreater(scale, 0.0)
        self.assertEqual(g.avoidances, 1)
        g, _ = guard_over([frame((-0.2, 4.5, 0.5))])
        error, _ = g.advise(0.0, 0.0)
        self.assertTrue(0.0 < error <= 40.0, error)

    def test_close_checkpoint_needs_less_room(self):
        g, _ = guard_over([frame((0.2, 4.5, 0.5))])
        self.assertEqual(g.advise(0.0, 0.0, distance_m=2.0), (0.0, 1.0))

    def test_wall_ahead_turns_in_place(self):
        wall = [(k * 0.2, 1.0, 0.3) for k in range(-8, 9)]
        g, _ = guard_over([frame(*wall)])
        error, scale = g.advise(0.0, 0.0)
        self.assertEqual(abs(error), 90.0)
        self.assertEqual(scale, 0.0)
        self.assertEqual(g.stops, 1)
        self.assertEqual(g.advise(0.5, 0.0), (error, 0.0))  # keeps turning the same way

    def test_no_frame_slows_down(self):
        g, _ = guard_over([])
        self.assertEqual(g.advise(0.0, 7.0), (7.0, g.blind_scale))
        self.assertEqual(g.failures, 1)

    def test_camera_error_slows_down(self):
        def broken():
            raise OSError("camera gone")
        g = fs.VisionGuard(broken, camera=CAM)
        self.assertEqual(g.advise(0.0, 7.0), (7.0, g.blind_scale))

    def test_wrong_size_frame_is_ignored(self):
        small = fs.render(fs.Camera(width=32, height=18), [])
        g = fs.VisionGuard(lambda: small, camera=CAM)
        self.assertEqual(g.advise(0.0, 7.0), (7.0, g.blind_scale))
        self.assertEqual(g.failures, 1)

    def test_polls_at_most_every_period(self):
        g, calls = guard_over([frame()] * 5)
        for t in (0.0, 0.05, 0.1, 0.25):
            g.advise(t, 0.0)
        self.assertEqual(len(calls), 2)

    def test_old_scan_is_not_trusted(self):
        g, _ = guard_over([frame()])
        self.assertEqual(g.advise(0.0, 5.0), (5.0, 1.0))
        self.assertEqual(g.advise(0.5, 5.0), (5.0, 1.0))  # no new frame, but the last is recent
        self.assertEqual(g.advise(1.2, 5.0), (5.0, g.blind_scale))

    def test_learns_a_new_ground_after_a_while(self):
        grass = frame(ground=fs.HEDGE_GREEN)
        g, _ = guard_over([frame(), grass, grass, grass], refit_after=3)
        self.assertEqual(g.advise(0.0, 0.0), (0.0, 1.0))
        self.assertEqual(g.advise(0.2, 0.0)[1], 0.0)  # new surface: treated as blocked at first
        self.assertEqual(g.advise(2.0, 0.0)[1], 0.0)
        self.assertEqual(g.advise(4.0, 0.0), (0.0, 1.0))  # third look in a row: it's the ground
        self.assertEqual(g.refits, 1)

    @unittest.skipUnless(HAVE_PIL, "Pillow not installed")
    def test_decode_frame(self):
        from PIL import Image
        buf = io.BytesIO()
        Image.new("RGB", (128, 72), (128, 128, 128)).save(buf, format="PNG")
        f = fs.decode_frame(buf.getvalue(), 64, 36)
        self.assertEqual((f.width, f.height), (64, 36))
        self.assertEqual(f.at(10, 10), (128, 128, 128))


class ClosedLoopTests(unittest.TestCase):
    """The pilot and the simulator together: a 2 m hedge on the straight line to the checkpoint."""

    MISSION = [(40.0, 0.0)]
    HEDGE = [(15.0, 0.3, 1.0)]

    def fly(self, vision, seed=1):
        sim = rp.SimRover(self.MISSION, seed=seed, heading_deg=0.0, compass_error_deg=0.0,
                          gps_dropout=0.0, obstacles=self.HEDGE)
        guard = fs.VisionGuard(lambda: sim.camera_frame(CAM), camera=CAM) if vision else None
        res = rp.Pilot(sim, clock=sim.clock, sleep=sim.sleep, vision=guard).run(timeout_s=600)
        return sim, guard, res

    def test_without_vision_it_drives_into_the_hedge(self):
        sim, _, _ = self.fly(False)
        self.assertGreater(sim.contacts, 0)

    def test_with_vision_it_goes_around(self):
        for seed in (1, 2):
            with self.subTest(seed=seed):
                sim, guard, res = self.fly(True, seed)
                self.assertTrue(res["ok"], res)
                self.assertEqual(sim.contacts, 0, (sim.min_gap, res))
                self.assertGreaterEqual(guard.avoidances, 1, res)
                self.assertIn("vision", res)


if __name__ == "__main__":
    unittest.main()
