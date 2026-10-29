"""Tests for colosseum_rate.py: the turn rate reaches the simulator and only
there, the 60 deg/s flight is colosseum_hold's own, and the decision rule.
Apache-2.0."""

import unittest

import colosseum_compat as cc
import colosseum_hold as ch
import colosseum_rate as cr


def turned_deg(rate_dps):
    sim, _ = cr.make_sim_at(rate_dps)(1, 30.0)
    before = sim.heading
    sim.control(0.0, 1.0)
    sim.sleep(2.5)
    d = (sim.heading - before) % 360.0
    return min(d, 360.0 - d)


class RateTests(unittest.TestCase):
    def test_the_rate_is_set_and_nothing_else_changes(self):
        sim, goal = cr.make_sim_at(23.4)(1, 30.0)
        ref, ref_goal = cc.make_sim(1, 30.0)
        self.assertEqual(sim.max_yaw_dps, 23.4)
        self.assertEqual(ref.max_yaw_dps, 60.0)
        self.assertEqual(goal, ref_goal)
        self.assertEqual(sim.heading, ref.heading)

    def test_a_slower_rover_turns_less(self):
        self.assertLess(turned_deg(23.4), turned_deg(48.0))
        self.assertLess(turned_deg(48.0), turned_deg(60.0))
        self.assertGreater(turned_deg(23.4), 10.0)

    def test_patches_are_undone(self):
        original = cc.make_sim
        cr.fly(1, 30.0, "stale-m50", 1.5, 23.4)
        self.assertIs(cc.make_sim, original)
        self.assertNotIn("stale-m50", ch.ARMS)

    def test_at_60_live_is_colosseum_hold_exactly(self):
        mine = cr.fly(1, 30.0, "live", 1.5, 60.0)
        theirs = ch.fly(1, 30.0, "live", 1.5)
        for field in ("exit", "ok", "reason", "elapsed_s", "final_true_m", "travelled_m"):
            self.assertEqual(mine[field], theirs[field], field)
        self.assertEqual(mine["rate_dps"], 60.0)

    def test_every_arm_runs_at_both_rates(self):
        for rate in cr.RATES_DPS:
            for arm in cr.ARMS:
                r = cr.fly(1, 30.0, arm, 0.22, rate)
                self.assertIn(r["exit"], (0, 1), (rate, arm))
                self.assertLessEqual(set(r["calls"]), cc.SERVED | {"GET /status"}, arm)


def passes(fail=()):
    out = {}
    for rate in cr.RATES_DPS:
        out[str(rate)] = {a: (rate, a) not in fail for a in cr.STALE_ARMS}
    return out


class DecideTests(unittest.TestCase):
    SCORES = {"stale": 1.7, "stale-m30": 1.2, "stale-m50": 1.15, "stale-m70": 1.4}

    def test_r1_when_nothing_is_clearly_better_than_0_3(self):
        self.assertEqual(cr.decide(passes(), self.SCORES), {"rule": "R1", "arm": "stale-m30"})

    def test_r2_when_another_cap_is_clearly_better(self):
        scores = dict(self.SCORES, **{"stale-m30": 1.3})
        self.assertEqual(cr.decide(passes(), scores), {"rule": "R2", "arm": "stale-m50"})

    def test_r2_when_0_3_fails_at_one_rate(self):
        got = cr.decide(passes(fail={(23.4, "stale-m30")}), self.SCORES)
        self.assertEqual(got, {"rule": "R2", "arm": "stale-m50"})

    def test_r3_when_no_cap_passes_at_both_rates(self):
        fail = {(23.4, a) for a in cr.STALE_ARMS}
        self.assertEqual(cr.decide(passes(fail=fail), self.SCORES), {"rule": "R3", "arm": None})


def fake_runs(times):
    runs = []
    for rate in cr.RATES_DPS:
        for arm in cr.ARMS:
            for noise in cr.NOISES_M:
                for dist in cr.DISTANCES_M:
                    for seed in range(24):
                        runs.append({"rate_dps": rate, "arm": arm, "noise_m": noise,
                                     "distance_m": dist, "ok": True, "exit": 0,
                                     "reason": None, "elapsed_s": times[arm] * dist / 30.0,
                                     "accepted": True})
    return runs


class SummariseTests(unittest.TestCase):
    def test_passes_scores_and_decision(self):
        times = {"live": 50.0, "stale": 80.0, "stale-m30": 60.0, "stale-m50": 54.0,
                 "stale-m70": 52.0}
        s = cr.summarise(fake_runs(times))
        for rate in cr.RATES_DPS:
            self.assertEqual(s["passes"][str(rate)],
                             {"live": True, "stale": False, "stale-m30": True,
                              "stale-m50": True, "stale-m70": True})
            self.assertEqual(s["fastest_passing"][str(rate)], "stale-m70")
        self.assertEqual(s["scores"]["stale-m30"], 1.2)
        self.assertEqual(s["scores"]["stale-m70"], 1.04)
        self.assertEqual(s["decision"], {"rule": "R2", "arm": "stale-m70"})
        self.assertEqual(len(s["cells"]), 2 * 5 * 2 * 2)

    def test_a_cell_short_of_23_fails_the_arm(self):
        # m50 scores 1.08 against m30's 1.2, clear of the 0.10 margin
        times = {"live": 50.0, "stale": 80.0, "stale-m30": 60.0, "stale-m50": 54.0,
                 "stale-m70": 52.0}
        runs = fake_runs(times)
        dropped = 0
        for r in runs:
            if (r["rate_dps"] == 23.4 and r["arm"] == "stale-m70" and r["distance_m"] == 30.0
                    and r["noise_m"] == 1.5 and dropped < 2):
                r["ok"] = False
                dropped += 1
        s = cr.summarise(runs)
        self.assertFalse(s["passes"]["23.4"]["stale-m70"])
        self.assertTrue(s["passes"]["48.0"]["stale-m70"])
        self.assertEqual(s["decision"], {"rule": "R2", "arm": "stale-m50"})


if __name__ == "__main__":
    unittest.main()
