"""Tests for colosseum_hold.py: the held command, the stale telemetry, the turn
count, and that rover_pilot.main() runs under every arm. Apache-2.0."""

import random
import unittest

import colosseum_compat as cc
import colosseum_hold as ch


class HoldTests(unittest.TestCase):
    def setUp(self):
        self.sim, self.goal = cc.make_sim(1, 30.0)

    def client(self, **kw):
        return ch.HoldBridgeClient(self.sim, self.goal, random.Random(1), **kw)

    def test_live_passes_control_straight_through(self):
        client = self.client()
        client.control(0.5, -0.25)
        self.assertEqual(self.sim.queue[-1][1:], (0.5, -0.25))
        self.assertEqual(client.pending, (0.0, 0.0))

    def test_a_command_waits_for_the_next_observation(self):
        client = self.client(hold=True)
        t0 = self.sim.t
        client.tick()
        self.assertEqual(client.samples, 1)
        client.control(0.5, -0.25)
        self.assertEqual(client.pending, (0.5, -0.25))
        nxt = client.next_sample
        self.assertTrue(2.0 <= nxt - t0 <= 3.0)
        while self.sim.t < nxt - 1e-9:
            client.tick()
            self.assertEqual(client.held, (0.0, 0.0))
            self.sim.sleep(self.sim.dt)
        client.tick()
        self.assertEqual(client.held, (0.5, -0.25))
        self.assertEqual(client.samples, 2)

    def test_stale_telemetry_repeats_between_observations(self):
        client = self.client(hold=True, stale=True)
        client.tick()
        first = client.data()
        self.sim.sleep(1.0)
        self.assertEqual(client.data(), first)

    def test_held_turns_that_change_side_are_counted(self):
        client = self.client(hold=True)
        for angular in (0.5, -0.5, 0.01, 0.5):
            client.control(0.0, angular)
            client.next_sample = self.sim.t
            client.tick()
        self.assertEqual(client.flips, 2)

    def test_the_cadence_is_the_same_for_every_held_arm(self):
        a, b = ch.hold_rng(3, 30.0, 0.22), ch.hold_rng(3, 30.0, 0.22)
        self.assertEqual([a.uniform(*ch.HOLD_S) for _ in range(5)],
                         [b.uniform(*ch.HOLD_S) for _ in range(5)])


class FlightTests(unittest.TestCase):
    def test_live_is_colosseum_compat_bridge_exactly(self):
        live = ch.fly(1, 30.0, "live")
        v1 = cc.fly(1, 30.0, "bridge")
        for field in ("exit", "ok", "reason", "elapsed_s", "final_true_m", "travelled_m"):
            self.assertEqual(live[field], v1[field], field)

    def test_every_arm_runs_and_calls_only_known_endpoints(self):
        for arm in ch.ARMS:
            r = ch.fly(1, 30.0, arm)
            self.assertIn(r["exit"], (0, 1), arm)
            self.assertLessEqual(set(r["calls"]), cc.SERVED | {"GET /status"}, arm)
            if ch.ARMS[arm]["hold"]:
                self.assertGreater(r["samples"], 0, arm)
            else:
                self.assertIsNone(r["samples"])


if __name__ == "__main__":
    unittest.main()
