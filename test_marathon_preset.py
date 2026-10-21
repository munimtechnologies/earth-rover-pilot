# Copyright 2026 Munim, Inc. Licensed under the Apache License, Version 2.0.
import unittest

import rover_pilot


class MarathonPresetTest(unittest.TestCase):
    def test_default_unchanged(self):
        s = rover_pilot.make_steering(True)
        self.assertEqual(s.cruise, 0.6)
        self.assertEqual(s.max_angular, 0.6)

    def test_real_rover_default_unchanged(self):
        s = rover_pilot.make_steering(False)
        self.assertEqual(s.cruise, 0.6)
        self.assertEqual(s.max_angular, rover_pilot.ROVER_STEERING["max_angular"])

    def test_marathon_sets_cruise_and_rover_steering_in_sim(self):
        s = rover_pilot.make_steering(True, marathon=True)
        self.assertEqual(s.cruise, 0.8)
        self.assertEqual(s.max_angular, rover_pilot.ROVER_STEERING["max_angular"])
        self.assertEqual(s.turn_in_place_deg, rover_pilot.ROVER_STEERING["turn_in_place_deg"])

    def test_explicit_flags_win(self):
        s = rover_pilot.make_steering(True, cruise=0.7, max_angular=0.8, marathon=True)
        self.assertEqual(s.cruise, 0.7)
        self.assertEqual(s.max_angular, 0.8)


if __name__ == "__main__":
    unittest.main()
