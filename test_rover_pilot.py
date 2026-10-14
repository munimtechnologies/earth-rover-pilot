"""Offline tests for rover_pilot (standard library only; no rover needed).

Run: python -m unittest test_rover_pilot -v
"""

import io
import json
import math
import os
import sys
import unittest
import urllib.error
from contextlib import redirect_stdout
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import rover_pilot as rp  # noqa: E402

LAT, LON = 37.8719, -122.2585


class GeoTests(unittest.TestCase):
    def test_one_degree_of_latitude(self):
        self.assertAlmostEqual(rp.haversine_m(0, 0, 1, 0), 111194.93, delta=0.1)

    def test_bearings_are_clockwise_from_north(self):
        for north, east, want in [(100, 0, 0), (0, 100, 90), (-100, 0, 180), (0, -100, 270)]:
            lat, lon = rp.offset_latlon(LAT, LON, north, east)
            got = rp.bearing_deg(LAT, LON, lat, lon)
            self.assertLess(abs(rp.wrap180(got - want)), 0.1, (north, east, got))

    def test_offset_round_trip(self):
        lat, lon = rp.offset_latlon(LAT, LON, 100, 50)
        self.assertAlmostEqual(rp.haversine_m(LAT, LON, lat, lon), math.hypot(100, 50), delta=0.5)
        east, north = rp.to_enu(LAT, LON, lat, lon)
        self.assertAlmostEqual(east, 50, delta=0.01)
        self.assertAlmostEqual(north, 100, delta=0.01)

    def test_wrap180(self):
        self.assertAlmostEqual(rp.wrap180(190), -170)
        self.assertAlmostEqual(rp.wrap180(-190), 170)
        self.assertAlmostEqual(rp.wrap180(370), 10)
        self.assertAlmostEqual(rp.wrap180(0), 0)

    def test_densify_spacing(self):
        a, b = (LAT, LON), rp.offset_latlon(LAT, LON, 9.0, 0.0)
        pts = rp.densify([a, b], step_m=2.0)
        self.assertEqual(len(pts), 6)
        self.assertEqual(pts[0], a)
        self.assertAlmostEqual(rp.haversine_m(*pts[-1], *b), 0.0, delta=1e-6)
        for p, q in zip(pts, pts[1:]):
            self.assertLessEqual(rp.haversine_m(*p, *q), 2.0 + 1e-6)


class GpsTests(unittest.TestCase):
    def test_rejects_no_fix_and_nonsense(self):
        for lat, lon in [(1000, 1000), (0, 0), (None, None), ("abc", 1), (float("nan"), 1)]:
            self.assertIsNone(rp.parse_fix(lat, lon), (lat, lon))
        self.assertEqual(rp.parse_fix("37.5", "-122.25"), (37.5, -122.25))

    def test_heading_parsing(self):
        self.assertAlmostEqual(rp.parse_heading(370), 10)
        self.assertAlmostEqual(rp.parse_heading("128"), 128)
        self.assertIsNone(rp.parse_heading(None))

    def test_jump_rejected_until_it_repeats(self):
        f = rp.GpsFilter()
        self.assertIsNotNone(f.update(LAT, LON, 0.0))
        far = [rp.offset_latlon(LAT, LON, 500 + 10 * i, 0) for i in range(3)]
        self.assertIsNone(f.update(*far[0], 1.0))
        self.assertIsNone(f.update(*far[0], 1.1))  # the same bad reading again counts once
        self.assertIsNone(f.update(*far[1], 2.0))
        self.assertEqual(f.update(*far[2], 3.0), far[2])  # third distinct one: the old fix was wrong
        self.assertAlmostEqual(f.lat, far[2][0])

    def test_fix_goes_stale(self):
        f = rp.GpsFilter(max_age_s=3.0)
        f.update(LAT, LON, 0.0)
        self.assertTrue(f.has_fix(2.0))
        f.update(1000, 1000, 2.5)
        self.assertFalse(f.has_fix(3.5))

    def test_smoothing(self):
        f = rp.GpsFilter(alpha=0.5)
        f.update(LAT, LON, 0.0)
        f.update(*rp.offset_latlon(LAT, LON, 2, 0), 1.0)
        self.assertAlmostEqual(rp.to_enu(LAT, LON, f.lat, f.lon)[1], 1.0, delta=0.01)


class HeadingTests(unittest.TestCase):
    def drive(self, est, course, compass_error, seconds, angular=0.0, speed=0.7):
        r = math.radians(course)
        for i in range(int(seconds * 10)):
            t = i / 10.0
            fix = None
            if i % 10 == 0:  # GPS once a second
                fix = rp.offset_latlon(LAT, LON, speed * t * math.cos(r), speed * t * math.sin(r))
            est.update(t, fix, (course + compass_error) % 360.0, 0.6, angular)

    def test_learns_compass_bias_on_a_straight(self):
        est = rp.HeadingEstimator()
        self.drive(est, course=60.0, compass_error=-25.0, seconds=30)
        self.assertGreaterEqual(est.calibrations, 1)
        self.assertAlmostEqual(est.bias, 25.0, delta=0.5)
        self.assertAlmostEqual(est.heading(35.0, 30.0), 60.0, delta=0.5)

    def test_no_calibration_while_turning(self):
        est = rp.HeadingEstimator()
        self.drive(est, course=60.0, compass_error=-25.0, seconds=30, angular=0.5)
        self.assertEqual(est.calibrations, 0)
        self.assertEqual(est.bias, 0.0)

    def test_gps_course_when_compass_missing(self):
        est = rp.HeadingEstimator()
        self.drive(est, course=60.0, compass_error=0.0, seconds=30)
        t_fit = est.last_course_t
        self.assertAlmostEqual(est.heading(None, t_fit + 1.0), 60.0, delta=0.5)
        self.assertIsNone(est.heading(None, t_fit + 60.0))


class SteeringTests(unittest.TestCase):
    def test_straight_ahead(self):
        linear, angular = rp.Steering(cruise=0.6).command(50.0, 0.0)
        self.assertAlmostEqual(linear, 0.6)
        self.assertAlmostEqual(angular, 0.0)

    def test_turns_toward_target(self):
        s = rp.Steering()
        self.assertGreater(s.command(50.0, 30.0)[1], 0)  # target to the right: positive angular
        self.assertLess(s.command(50.0, -30.0)[1], 0)

    def test_turns_in_place_when_far_off(self):
        linear, angular = rp.Steering().command(50.0, -120.0)
        self.assertEqual(linear, 0.0)
        self.assertAlmostEqual(angular, -0.6)

    def test_slows_near_target(self):
        s = rp.Steering(cruise=0.6)
        self.assertLess(s.command(3.0, 0.0)[0], s.command(30.0, 0.0)[0])


class PathFollowerTests(unittest.TestCase):
    def test_aims_ahead_on_the_path(self):
        path = [(LAT, LON), rp.offset_latlon(LAT, LON, 100.0, 0.0)]
        f = rp.PathFollower(path, lookahead_m=8.0)
        aim, off = f.target(*rp.offset_latlon(LAT, LON, 10.0, 3.0))
        east, north = rp.to_enu(LAT, LON, *aim)
        self.assertAlmostEqual(north, 18.0, delta=2.1)
        self.assertAlmostEqual(east, 0.0, delta=0.1)
        self.assertAlmostEqual(off, 3.0, delta=1.1)

    def test_end_of_path_aims_at_the_goal(self):
        goal = rp.offset_latlon(LAT, LON, 20.0, 0.0)
        f = rp.PathFollower([(LAT, LON), goal])
        aim, _ = f.target(*rp.offset_latlon(LAT, LON, 19.0, 0.0))
        self.assertAlmostEqual(rp.haversine_m(*aim, *goal), 0.0, delta=1e-6)


class TracedSim(rp.SimRover):
    """SimRover that records its true (north, east) track."""

    def __init__(self, *args, **kw):
        self.trace = []
        super().__init__(*args, **kw)

    def _step(self):
        super()._step()
        self.trace.append((self.north, self.east))


class SimMissionTests(unittest.TestCase):
    def fly(self, seed, planner=None, **sim_kw):
        sim = rp.SimRover(rp.DEMO_MISSION, seed=seed, **sim_kw)
        pilot = rp.Pilot(sim, clock=sim.clock, sleep=sim.sleep, planner=planner)
        return sim, pilot, pilot.run(timeout_s=1500)

    def test_completes_demo_mission(self):
        for seed in (1, 2, 3):
            with self.subTest(seed=seed):
                sim, pilot, res = self.fly(seed)
                self.assertTrue(res["ok"], res)
                self.assertEqual(res["reached"], [1, 2, 3, 4])
                self.assertEqual(sim.next_cp, 4)
                self.assertGreaterEqual(res["calibrations"], 2, res)
                # the compass reads 25 degrees low; the pilot should have learned +25
                self.assertLess(abs(rp.wrap180(pilot.heading.bias + sim.compass_error)), 12, res)

    def test_survives_frequent_gps_dropouts(self):
        sim, _, res = self.fly(5, gps_dropout=0.2)
        self.assertTrue(res["ok"], res)
        self.assertEqual(sim.next_cp, 4)

    def test_backs_out_when_stuck(self):
        sim, _, res = self.fly(6, blocked_until_s=30.0)
        self.assertTrue(res["ok"], res)
        self.assertGreaterEqual(res["recoveries"], 1, res)
        self.assertTrue(sim.reverse_seen)

    def test_follows_planned_path(self):
        sim = TracedSim(rp.DEMO_MISSION, seed=2)
        # the first leg goes 30 m east, then 40 m north; a straight line passes 24 m from the corner
        corner = rp.offset_latlon(sim.lat0, sim.lon0, 0.0, 30.0)
        calls = []

        def planner(lat, lon, goal_lat, goal_lon):
            calls.append((lat, lon, goal_lat, goal_lon))
            if len(calls) == 1:
                return [(lat, lon), corner, (goal_lat, goal_lon)]
            return [(lat, lon), (goal_lat, goal_lon)]

        pilot = rp.Pilot(sim, clock=sim.clock, sleep=sim.sleep, planner=planner)
        res = pilot.run(timeout_s=1500)
        self.assertTrue(res["ok"], res)
        self.assertGreaterEqual(res["plans"], 4, res)
        closest = min(math.hypot(n, e - 30.0) for n, e in sim.trace)
        self.assertLess(closest, 10.0)

    def test_planner_failure_falls_back_to_straight(self):
        def planner(*_):
            raise RuntimeError("no map here")

        sim, _, res = self.fly(3, planner=planner)
        self.assertTrue(res["ok"], res)
        self.assertEqual(sim.next_cp, 4)

    def test_no_checkpoints(self):
        class Empty:
            def start_mission(self):
                return True

            def checkpoints(self):
                return [], 0

            def control(self, linear, angular):
                pass

        res = rp.Pilot(Empty(), clock=lambda: 0.0, sleep=lambda s: None).run()
        self.assertFalse(res["ok"])
        self.assertIn("no checkpoints", res["reason"])


class FakeClock:
    def __init__(self):
        self.t = 0.0

    def clock(self):
        return self.t

    def sleep(self, seconds):
        self.t += max(seconds, 0.01)


class SilentServerRover:
    """Sits on its only checkpoint; every report gets no answer (status 0)."""

    def __init__(self, counts_reports):
        self.counts_reports = counts_reports
        self.latest = 0
        self.reports = 0

    def start_mission(self):
        return True

    def checkpoints(self):
        return [(1, LAT, LON)], self.latest

    def data(self):
        return {"latitude": LAT, "longitude": LON, "orientation": 0}

    def control(self, linear, angular):
        pass

    def checkpoint_reached(self):
        self.reports += 1
        if self.counts_reports:
            self.latest = 1
        return {"ok": False, "status": 0, "distance": None, "mission_completed": False}


class UnansweredReportTests(unittest.TestCase):
    def test_counted_report_is_confirmed_from_the_list(self):
        rover, c = SilentServerRover(counts_reports=True), FakeClock()
        res = rp.Pilot(rover, clock=c.clock, sleep=c.sleep).run(timeout_s=60)
        self.assertTrue(res["ok"], res)
        self.assertEqual(res["reached"], [1])
        self.assertEqual(rover.reports, 1)

    def test_uncounted_report_is_retried(self):
        rover, c = SilentServerRover(counts_reports=False), FakeClock()
        res = rp.Pilot(rover, clock=c.clock, sleep=c.sleep).run(timeout_s=10)
        self.assertFalse(res["ok"])
        self.assertEqual(res["reason"], "timeout")
        self.assertGreaterEqual(rover.reports, 2)


class FakeResp:
    def __init__(self, status, payload):
        self.status = status
        self._body = json.dumps(payload).encode()

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class SdkClientTests(unittest.TestCase):
    def test_checkpoints_parsed_and_sorted(self):
        payload = {"checkpoints_list": [
            {"id": 9, "sequence": 2, "latitude": "37.2", "longitude": "-122.1"},
            {"id": 8, "sequence": 1, "latitude": "37.1", "longitude": "-122.0"}],
            "latest_scanned_checkpoint": 1}
        with mock.patch.object(rp.urllib.request, "urlopen", return_value=FakeResp(200, payload)) as m:
            cps, latest = rp.SdkClient("http://x").checkpoints()
        self.assertEqual(cps, [(1, 37.1, -122.0), (2, 37.2, -122.1)])
        self.assertEqual(latest, 1)
        req = m.call_args[0][0]
        self.assertEqual(req.full_url, "http://x/checkpoints-list")
        self.assertEqual(req.get_method(), "GET")

    def test_refused_checkpoint_reports_distance(self):
        body = json.dumps({"detail": {"error": "Bot is not within range",
                                      "proximate_distance_to_checkpoint": 23.4}}).encode()
        err = urllib.error.HTTPError("http://x/checkpoint-reached", 400, "Bad Request", {},
                                     io.BytesIO(body))
        with mock.patch.object(rp.urllib.request, "urlopen", side_effect=err):
            res = rp.SdkClient("http://x").checkpoint_reached()
        self.assertFalse(res["ok"])
        self.assertEqual(res["status"], 400)
        self.assertAlmostEqual(res["distance"], 23.4)

    def test_report_waits_for_the_stop_check(self):
        with mock.patch.object(rp.urllib.request, "urlopen",
                               return_value=FakeResp(200, {"mission_completed": True})) as m:
            res = rp.SdkClient("http://x").checkpoint_reached()
        self.assertTrue(res["ok"])
        self.assertTrue(res["mission_completed"])
        self.assertGreaterEqual(m.call_args[1]["timeout"], 15)

    def test_control_payload(self):
        with mock.patch.object(rp.urllib.request, "urlopen",
                               return_value=FakeResp(200, {"message": "ok"})) as m:
            rp.SdkClient("http://x/").control(1.7, -0.25)
        req = m.call_args[0][0]
        self.assertEqual(req.full_url, "http://x/control")
        self.assertEqual(json.loads(req.data),
                         {"command": {"linear": 1.0, "angular": -0.25, "lamp": 0}})

    def test_unreachable_sdk_means_no_data(self):
        with mock.patch.object(rp.urllib.request, "urlopen",
                               side_effect=urllib.error.URLError("refused")):
            self.assertEqual(rp.SdkClient().data(), {})


class MainTests(unittest.TestCase):
    def test_simulate_cli(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = rp.main(["--simulate", "--seed", "4"])
        self.assertEqual(code, 0, buf.getvalue())
        self.assertTrue(json.loads(buf.getvalue())["ok"])


if __name__ == "__main__":
    unittest.main()
