"""Tests for dead_reckon.py 0.2.0's GPS-course hold (course_hold_s, fade).

The rover drives due north; the pilot's heading reads 20 deg too far right, so
following it alone drifts east, and following the fresh GPS course does not.
Apache-2.0. By MV2 of Munim, Inc.; written with AI agents.
"""

import math
import unittest

import dead_reckon as dm
from test_dead_reckon import MINI, drive, en, miss

BIAS = 20.0


class Biased(dm.DeadReckoner):
    """DeadReckoner whose heading (and compass) read BIAS deg too far right."""

    def update(self, t, new_fix, compass=None, heading=None):
        super().update(t, new_fix, None if compass is None else compass + BIAS,
                       None if heading is None else heading + BIAS)


def reckoner(**kw):
    return Biased(mps_per_rpm=MINI, learn_scale=False, use_course=False, **kw)


def ticks(dr, s, n, gps_off=()):
    """n more 0.1 s ticks due north at 0.5 m/s, asking position() after each."""
    seen = []
    for _ in range(n):
        s = drive(dr, [(0.1, 0.5, 0.0)], MINI, gps_off=gps_off, state=s)
        seen.append((s["t"], dr.position(s["t"])))
    return s, seen


class HoldTest(unittest.TestCase):
    def test_version_and_default_off(self):
        self.assertEqual(dm.__version__, "0.2.0")
        dr = dm.DeadReckoner()
        self.assertEqual(dr.course_hold_s, 0.0)
        self.assertTrue(dr.fade)

    def test_course_used_inside_the_hold(self):
        # The fix seen at 20.0 s shows the rover at 18.5 s (9.25 m north); the hold
        # runs to 20.5 s, so at 20.0 s the 0.75 m since go along the course (0 deg).
        held = reckoner(course_hold_s=2.0, fade=False)
        s = drive(held, [(20.0, 0.5, 0.0)], MINI)
        self.assertEqual(held._hold, (20.5, 0.0))
        self.assertLess(miss(held, s), 0.02)
        plain = reckoner()
        s = drive(plain, [(20.0, 0.5, 0.0)], MINI)
        # Along the heading: 0.75 m at 20 deg, 0.257 m east and 0.045 m short.
        self.assertAlmostEqual(miss(plain, s), 0.2605, delta=0.002)

    def test_hard_switch_at_the_end_of_the_hold(self):
        # No fix after 20.0 s; asked once at 23.0 s: 1.0 m north on the course up
        # to 20.5 s, then 1.25 m along the heading (20 deg).
        dr = reckoner(course_hold_s=2.0, fade=False)
        s = drive(dr, [(20.0, 0.5, 0.0)], MINI)
        s = drive(dr, [(3.0, 0.5, 0.0)], MINI, gps_off=[(20.05, 100.0)], state=s)
        e, n = en(*dr.position(s["t"]))
        r = math.radians(BIAS)
        self.assertAlmostEqual(e, 1.25 * math.sin(r), delta=0.002)
        self.assertAlmostEqual(n, 9.25 + 1.0 + 1.25 * math.cos(r), delta=0.002)

    def test_fade_is_continuous_and_fades_out(self):
        dr = reckoner(course_hold_s=2.0, fade=True)
        s = drive(dr, [(20.0, 0.5, 0.0)], MINI)
        s, seen = ticks(dr, s, 30, gps_off=[(20.05, 100.0)])
        at = dict((round(t, 1), p) for t, p in seen)
        # At the switch (20.5 s) the estimate is still on the course: 1.0 m north.
        e, n = en(*at[20.5])
        self.assertAlmostEqual(e, 0.0, places=6)
        self.assertAlmostEqual(n, 10.25, places=6)
        # Each 0.1 s step (0.05 m) after the switch goes along the direction seen at
        # its start: k deg at 20.5 + 0.1 k s (the 20 deg shift fading over 2 s),
        # then 20 deg from 22.5 s on.
        dirs = [math.radians(min(BIAS, float(k))) for k in range(25)]
        e, n = en(*at[23.0])
        self.assertAlmostEqual(e, sum(0.05 * math.sin(d) for d in dirs), delta=0.001)
        self.assertAlmostEqual(n, 10.25 + sum(0.05 * math.cos(d) for d in dirs), delta=0.001)
        # Less sideways drift than switching hard, far less than the heading alone.
        self.assertLess(e, 1.25 * math.sin(math.radians(BIAS)) - 0.1)

    def test_no_hold_without_a_fresh_course(self):
        dr = reckoner(course_hold_s=2.0)
        drive(dr, [(20.0, 0.0, 0.0)], MINI)  # standing still: no course
        self.assertIsNone(dr._hold)

    def test_off_is_unchanged(self):
        legs = [(10.0, 0.5, 0.0), (1.0, 0.0, 90.0), (5.0, 0.5, 90.0), (5.0, 0.4, 200.0)]
        steps = [(0.1, v, h) for sec, v, h in legs for _ in range(int(round(sec / 0.1)))]
        for kw_a, kw_b in (({}, {"course_hold_s": 0.0, "fade": False}),
                           ({"use_course": True}, {"use_course": True, "course_hold_s": 2.0})):
            a = Biased(mps_per_rpm=MINI, learn_scale=False, **dict({"use_course": False}, **kw_a))
            b = Biased(mps_per_rpm=MINI, learn_scale=False, **dict({"use_course": False}, **kw_b))
            sa = sb = None
            for step in steps:
                sa = drive(a, [step], MINI, state=sa)
                sb = drive(b, [step], MINI, state=sb)
                self.assertEqual(a.position(sa["t"]), b.position(sb["t"]), (kw_b, sa["t"]))
            self.assertIsNone(b._hold)


if __name__ == "__main__":
    unittest.main()
