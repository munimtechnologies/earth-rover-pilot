"""Tests for colosseum_compat.py: the bridge contract BridgeClient serves, and
that rover_pilot.main() runs and stops through it. Apache-2.0."""

import unittest

import colosseum_compat as cc
import rover_pilot as rp


class BridgeContractTests(unittest.TestCase):
    def setUp(self):
        self.sim, self.goal = cc.make_sim(1, 40.0)
        self.client = cc.BridgeClient(self.sim, self.goal)

    def test_data_has_only_the_bridge_fields(self):
        self.assertEqual(set(self.client.data()),
                         {"latitude", "longitude", "orientation", "speed", "battery", "rpms"})

    def test_full_sdk_data_keeps_timestamp_and_signal(self):
        client = cc.BridgeClient(self.sim, self.goal, full_sdk=True)
        self.assertIn("timestamp", client.data())
        self.assertIn("gps_signal", client.data())

    def test_goal_is_the_only_checkpoint_parsed_from_strings(self):
        self.assertEqual(self.client.checkpoints(), ([(1, self.goal[0], self.goal[1])], 0))

    def test_goal_is_the_asked_distance_away(self):
        d = rp.haversine_m(self.sim.lat0, self.sim.lon0, self.goal[0], self.goal[1])
        self.assertAlmostEqual(d, 40.0, delta=0.1)

    def test_report_from_20_m_is_refused(self):
        self.sim.gps = rp.offset_latlon(self.goal[0], self.goal[1], 20.0, 0.0)
        res = self.client.checkpoint_reached()
        self.assertFalse(res["ok"])
        self.assertEqual(res["status"], 400)
        self.assertFalse(self.client.done)

    def test_report_at_the_goal_is_accepted_and_ends_the_trial(self):
        self.sim.gps = self.goal
        res = self.client.checkpoint_reached()
        self.assertTrue(res["ok"])
        self.assertTrue(self.client.done)
        self.assertEqual(self.client.checkpoints()[1], 1)

    def test_no_status_and_no_missions(self):
        self.assertIsNone(self.client.telemetry_age())
        self.assertIsNone(self.client.missions())
        self.assertIsNone(self.client.front_image())

    def test_full_sdk_answers_status(self):
        client = cc.BridgeClient(self.sim, self.goal, full_sdk=True)
        self.assertEqual(client.telemetry_age(), 0.0)

    def test_control_reaches_the_rover(self):
        self.client.control(0.5, -0.25)
        self.assertEqual(self.sim.queue[-1][1:], (0.5, -0.25))


class FlightTests(unittest.TestCase):
    def test_a_flight_runs_and_calls_only_known_endpoints(self):
        r = cc.fly(1, 40.0)
        self.assertIn(r["exit"], (0, 1))
        self.assertLessEqual(set(r["calls"]), cc.SERVED | {"GET /status"})
        self.assertEqual(r["calls"]["POST /start-mission"], 1)

    def test_the_end_of_a_trial_stops_the_rover(self):
        r = cc.fly(1, 80.0, interrupt_at=20.0)
        self.assertEqual(r["exit"], 130)
        self.assertFalse(r["ok"])
        self.assertEqual(r["last_cmd"], [0.0, 0.0])


if __name__ == "__main__":
    unittest.main()
