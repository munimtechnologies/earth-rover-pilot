# Copyright 2026 Munim, Inc. Licensed under the Apache License, Version 2.0.
"""0.19.2-0.19.3 (documentation only): the README's "Running under
RoboColosseum" section recommends --max-angular 0.3 when the bridge refreshes
telemetry only at its 2-3 s observations, as colosseum-hold-confirm's rule C1
said (studies/colosseum-hold-confirm/GRADE.md) and colosseum-rate's rule R1
kept at the recorded turn rate (studies/colosseum-rate/GRADE.md), while a
real rover's default stays 1.0."""
import os
import unittest

import rover_pilot as rp

HERE = os.path.dirname(os.path.abspath(__file__))


def read(name):
    with open(os.path.join(HERE, name), encoding="utf-8") as f:
        return f.read()


def readme_section(title):
    text = read("README.md")
    start = text.index("\n## " + title + "\n")
    end = text.find("\n## ", start + 1)
    return text[start:end if end >= 0 else len(text)]


class ColosseumDocsTest(unittest.TestCase):
    def test_version(self):
        self.assertEqual(rp.__version__, "0.19.3")

    def test_real_rover_default_unchanged(self):
        self.assertEqual(rp.ROVER_STEERING, {"max_angular": 1.0, "turn_in_place_deg": 90.0})

    def test_section_recommends_the_flag(self):
        section = readme_section("Running under RoboColosseum")
        self.assertIn("python rover_pilot.py --timeout 300 --max-angular 0.3", section)
        self.assertIn("studies/colosseum-hold-confirm", section)
        self.assertIn("The default stays 1.0", section)

    def test_section_uses_the_recorded_turn_rate(self):
        section = readme_section("Running under RoboColosseum")
        self.assertIn("studies/colosseum-rate", section)
        self.assertIn("studies/frodo-spin/GRADE-v2.md", section)
        self.assertIn("23.4°/s per unit", section)
        self.assertIn("about 14°", section)
        self.assertNotIn("about 19°", section)

    def test_findings_records_frodo_spin_v2(self):
        findings = read("FINDINGS-frodobots-2k.md")
        self.assertIn("v2 passed its check and all 7 predictions held", findings)
        self.assertNotIn("its check failed, so nothing is decided", findings)

    def test_flag_bounds_a_real_rover_turn(self):
        steering = rp.make_steering(False, max_angular=0.3)
        self.assertEqual(steering.max_angular, 0.3)
        self.assertEqual(steering.turn_in_place_deg, 90.0)
        # 80 degrees off asks for 80/60 of full angular; 0.3 caps it.
        self.assertEqual(steering.command(20.0, 80.0)[1], 0.3)
        self.assertEqual(steering.command(20.0, -80.0)[1], -0.3)


if __name__ == "__main__":
    unittest.main()
