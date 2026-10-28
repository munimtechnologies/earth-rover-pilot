# Copyright 2026 Munim, Inc. Licensed under the Apache License, Version 2.0.
"""0.19.0: on a real rover the stuck check gives no verdict until 10 s after
its history was last cleared, as pace_v.py's pre-stated rule R2 says
(studies/pace-v/GRADE.md): `warm10` and `warmstand10` both qualified, and
`warmstand10` was slower than `warm10` on 4 of 6 blocked courses, so a real
rover gets `warm10`. The command line sets it (STUCK_WARMUP_S); the simulator
and the Pilot class keep 0 (no warm-up), so earlier studies fly as before.

Run: python -m unittest test_stuck_warmup_default -v
"""
import contextlib
import io
import unittest
from unittest import mock

import pace_v as pv
import rover_pilot as rp

STUCK = rp.Pilot._stuck
# (profile, course, seed) -> (elapsed_s, recovery_t) of pace_v.py's warm10
# missions in pace-v-v1's record (runs.jsonl): two rovers blocked at the
# start, one blocked mid-route, and a quiet mission with no recovery move.
WARM10 = {
    ("blockedstart", "boulevard", 397): (1799.6, [19.1, 44.1]),
    ("blockedstart", "boulevard", 398): (1779.6, [19.1]),
    ("blockedmid", "boulevard", 415): (1823.6, [397.9, 422.9]),
    ("quiet90", "blocks", 397): (1569.6, []),
}
# Fields of the stuck record that say how the study flew, not what happened.
HOW = ("warmup_s", "warm", "stands")


class FakePilot:
    """Stands in for rp.Pilot and keeps the last one main() built."""
    last = None

    def __init__(self, rover, **kw):
        self.kw = dict(kw, rover=rover)
        FakePilot.last = self

    def run(self, start=True, timeout_s=3600.0):
        return {"ok": True, "reason": "mission completed"}


def built(argv):
    out = io.StringIO()
    FakePilot.last = None
    with mock.patch.object(rp, "Pilot", FakePilot), contextlib.redirect_stdout(out):
        code = rp.main(argv)
    return code, FakePilot.last


@contextlib.contextmanager
def flying_with(warmup_s):
    """While inside, every Pilot built (also by the studies) is given
    `warmup_s` as the command line gives a real rover's."""
    init = rp.Pilot.__init__

    def patched(self, *args, **kw):
        init(self, *args, **kw)
        self.stuck_warmup_s = warmup_s

    with mock.patch.object(rp.Pilot, "__init__", patched):
        yield


def sim_pilot():
    rover = rp.SimRover(rp.DEMO_MISSION, seed=2)
    return rp.Pilot(rover, clock=rover.clock, sleep=rover.sleep)


def without_how(r):
    r = dict(r, stuck=dict(r["stuck"]))
    for k in HOW:
        r["stuck"].pop(k)
    return r


class DefaultTests(unittest.TestCase):
    def test_version(self):
        self.assertEqual(rp.__version__, "0.19.1")

    def test_warmup_is_the_study_s(self):
        self.assertEqual(rp.STUCK_WARMUP_S, 10.0)
        self.assertEqual(rp.STUCK_WARMUP_S, pv.VARIANTS["warm10"]["warmup_s"])
        self.assertEqual(pv.VARIANTS["warm10"]["warm"], "always")

    def test_class_default_unchanged(self):
        pilot = sim_pilot()
        self.assertEqual(pilot.stuck_warmup_s, 0.0)
        self.assertIsInstance(pilot._history, rp.StuckHistory)
        # With no warm-up nothing is held back and the history's mark is left alone.
        for t in (0.0, 5.0, 20.0):
            self.assertFalse(pilot._warming(t))
        self.assertTrue(pilot._history.cleared)

    def test_history_marks_each_clear(self):
        h = rp.StuckHistory()
        self.assertTrue(h.cleared)
        h.cleared = False
        h.append((1.0, 37.0, -122.0, 0.8))
        self.assertFalse(h.cleared)
        h.clear()
        self.assertTrue(h.cleared)
        self.assertEqual(len(h), 0)

    def test_warm_up_after_each_clear(self):
        pilot = sim_pilot()
        pilot.stuck_warmup_s = 10.0
        self.assertTrue(pilot._warming(0.25))
        self.assertFalse(pilot._history.cleared)
        self.assertTrue(pilot._warming(10.0))
        self.assertFalse(pilot._warming(10.25))
        self.assertFalse(pilot._warming(30.0))
        pilot._history.append((30.0, 37.0, -122.0, 0.8))
        pilot._history.clear()
        self.assertTrue(pilot._warming(31.5))
        self.assertTrue(pilot._warming(41.25))
        self.assertFalse(pilot._warming(41.5))


class CommandLineTests(unittest.TestCase):
    def test_real_rover_gets_the_study_s_warmup(self):
        code, pilot = built(["--sdk", "http://x"])
        self.assertEqual(code, 0)
        self.assertEqual(pilot.stuck_warmup_s, 10.0)

    def test_with_other_real_rover_options(self):
        for extra in (["--no-dead-reckon"], ["--dead-reckon"], ["--no-smooth-heading"],
                      ["--marathon"]):
            with self.subTest(extra=extra):
                code, pilot = built(["--sdk", "http://x"] + extra)
                self.assertEqual(code, 0)
                self.assertEqual(pilot.stuck_warmup_s, 10.0)
                self.assertEqual(pilot.path_lookahead_m, 16.0)

    def test_simulator_unchanged(self):
        for argv in (["--simulate"], ["--simulate", "--dead-reckon-gaps"],
                     ["--simulate", "--marathon"]):
            with self.subTest(argv=argv):
                code, pilot = built(argv)
                self.assertEqual(code, 0)
                self.assertFalse(hasattr(pilot, "stuck_warmup_s"))


class FliesAsTheStudyTests(unittest.TestCase):
    def test_release_warmup_flies_pace_v_warm10(self):
        # pace_v.py's warm10 missions, against the shipped check flown with the
        # warm-up the command line gives a real rover: the same missions, the
        # same recovery moves, and both as pace-v-v1 recorded them.
        code, pilot = built(["--sdk", "http://x"])
        self.assertEqual(code, 0)
        for (profile, course, seed), (elapsed_s, recovery_t) in sorted(WARM10.items()):
            with self.subTest(profile=profile, course=course, seed=seed):
                want = pv.fly(course, seed, profile, "warm10", 0.8)
                with flying_with(pilot.stuck_warmup_s):
                    got = pv.fly(course, seed, profile, "a0.3", 0.8)
                self.assertTrue(want["ok"], want["reason"])
                self.assertEqual((want["elapsed_s"], want["stuck"]["recovery_t"]),
                                 (elapsed_s, recovery_t))
                self.assertEqual(without_how(got), without_how(want))
        self.assertIs(rp.Pilot._stuck, STUCK)

    def test_not_the_shipped_check(self):
        warm = pv.fly("boulevard", 397, "blockedstart", "warm10", 0.8)
        shipped = pv.fly("boulevard", 397, "blockedstart", "a0.3", 0.8)
        self.assertNotEqual(shipped["stuck"]["recovery_t"], warm["stuck"]["recovery_t"])
        self.assertLess(shipped["stuck"]["recovery_t"][0], warm["stuck"]["recovery_t"][0])


if __name__ == "__main__":
    unittest.main()
