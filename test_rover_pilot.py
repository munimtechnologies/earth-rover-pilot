"""Offline tests for rover_pilot (standard library only; no rover needed).

Run: python -m unittest test_rover_pilot -v
"""

import base64
import io
import json
import math
import os
import sys
import tempfile
import unittest
import urllib.error
from contextlib import redirect_stderr, redirect_stdout
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


class ConventionsTests(unittest.TestCase):
    def test_defaults_read_compass_degrees(self):
        c = rp.Conventions()
        self.assertAlmostEqual(c.heading(370), 10)
        self.assertAlmostEqual(c.heading("128"), 128)
        self.assertAlmostEqual(c.heading(-90), 270)
        self.assertIsNone(c.heading(None))
        self.assertIsNone(c.heading(float("nan")))
        self.assertEqual(c.angular(0.3), 0.3)

    def test_other_scales_and_directions(self):
        self.assertAlmostEqual(rp.Conventions(256.0).heading(64), 90)
        self.assertAlmostEqual(rp.Conventions(2 * math.pi).heading(math.pi), 180)
        self.assertAlmostEqual(rp.Conventions(360.0, False).heading(90), 270)
        self.assertAlmostEqual(rp.Conventions(256.0, False).heading(64), 270)

    def test_left_positive_angular_is_flipped(self):
        c = rp.Conventions(angular_right_positive=False)
        self.assertEqual(c.angular(0.3), -0.3)
        self.assertEqual(math.copysign(1.0, c.angular(0.0)), 1.0)  # a stop stays 0.0, not -0.0

    def test_from_dict(self):
        c = rp.Conventions.from_dict({"ok": True, "orientation_scale": 256,
                                      "orientation_clockwise": False,
                                      "angular_right_positive": False, "bias_deg": 12.5})
        self.assertEqual(c.orientation_scale, 256.0)
        self.assertFalse(c.orientation_clockwise)
        self.assertFalse(c.angular_right_positive)
        self.assertEqual(c.bias_deg, 12.5)
        self.assertIsNone(rp.Conventions.from_dict({}).bias_deg)

    def test_quirky_sim_reads_back_through_its_conventions(self):
        sim = rp.SimRover(rp.DEMO_MISSION, compass_noise_deg=0.0, **rp.SIM_QUIRKS)
        raw = sim.data()["orientation"]
        self.assertTrue(0.0 <= raw < 256.0)
        # heading 200 with a compass 25 degrees low reads 175
        self.assertAlmostEqual(rp.Conventions(256.0, False).heading(raw), 175.0, delta=1e-6)

    def test_sim_rover_that_turns_left(self):
        sim = rp.SimRover([(40.0, 0.0)], heading_deg=0.0, latency_s=0.0, angular_sign=-1.0)
        for _ in range(10):
            sim.control(0.0, 0.5)
            sim.sleep(0.1)
        self.assertAlmostEqual(sim.heading, 330.0, delta=1e-6)


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

    def test_sums_up_each_leg(self):
        sim, _, res = self.fly(1)
        legs = res["legs"]
        self.assertEqual([leg["seq"] for leg in legs], [1, 2, 3, 4])
        for leg in legs:
            self.assertGreater(leg["elapsed_s"], 0.0, leg)
            self.assertGreaterEqual(leg["reports"], 1, leg)
        self.assertEqual(sum(leg["reports"] for leg in legs), res["reports"])
        self.assertEqual(sum(leg["recoveries"] for leg in legs), res["recoveries"])
        self.assertLessEqual(sum(leg["elapsed_s"] for leg in legs), res["elapsed_s"] + 0.5)
        # the first checkpoint is 50 m from the start; the first fix is within a few metres of it
        self.assertAlmostEqual(legs[0]["straight_m"], 50.0, delta=8.0)

    def test_resumes_a_mission_already_under_way(self):
        # as after a restart with --no-start: the server says checkpoints 1 and 2 are done
        sim = rp.SimRover(rp.DEMO_MISSION, seed=1)
        sim.next_cp = 2
        starts = []
        sim.start_mission = lambda: starts.append(1) or True
        res = rp.Pilot(sim, clock=sim.clock, sleep=sim.sleep).run(start=False, timeout_s=1500)
        self.assertTrue(res["ok"], res)
        self.assertEqual(starts, [])
        self.assertEqual(res["checkpoints"], 2)
        self.assertEqual(res["reached"], [3, 4])
        self.assertEqual([leg["seq"] for leg in res["legs"]], [3, 4])
        self.assertEqual(sim.next_cp, 4)

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

    def test_quirky_rover_with_its_conventions(self):
        # orientation 0-255 counter-clockwise and a left-turning angular, undone by Conventions
        sim = rp.SimRover(rp.DEMO_MISSION, seed=1, **rp.SIM_QUIRKS)
        conv = rp.Conventions(256.0, False, False)
        res = rp.Pilot(sim, clock=sim.clock, sleep=sim.sleep, conventions=conv).run(timeout_s=1500)
        self.assertTrue(res["ok"], res)
        self.assertEqual(res["reached"], [1, 2, 3, 4])

    def test_left_turning_rover_without_conventions_goes_nowhere(self):
        # every correction turns it the wrong way, so it ends up pointing away and
        # turning in place; this is what --calibrate is for
        sim = rp.SimRover(rp.DEMO_MISSION, seed=1, angular_sign=-1.0)
        res = rp.Pilot(sim, clock=sim.clock, sleep=sim.sleep).run(timeout_s=120)
        self.assertFalse(res["ok"])
        self.assertEqual(res["reason"], "timeout")
        self.assertEqual(res["reached"], [])
        self.assertLess(math.hypot(sim.north, sim.east), 5.0)

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
        self.assertEqual(res["legs"], [])


class SimObstacleTests(unittest.TestCase):
    def test_obstacle_stops_the_rover_but_it_can_back_away(self):
        sim = rp.SimRover([(40.0, 0.0)], heading_deg=0.0, latency_s=0.0,
                          obstacles=[(2.0, 0.0, 1.0)])
        for _ in range(50):
            sim.control(1.0, 0.0)
            sim.sleep(0.1)
        self.assertGreater(sim.contacts, 0)
        # 0.12 m a step; the next step after 0.72 m would bring it within 1.2 m of the centre
        self.assertTrue(0.6 < sim.north <= 0.8, sim.north)
        before = sim.north
        for _ in range(10):
            sim.control(-1.0, 0.0)
            sim.sleep(0.1)
        self.assertLess(sim.north, before - 0.5)

    def test_no_obstacles_means_no_contacts(self):
        sim = rp.SimRover([(40.0, 0.0)], heading_deg=0.0)
        for _ in range(30):
            sim.control(1.0, 0.0)
            sim.sleep(0.1)
        self.assertEqual(sim.contacts, 0)
        self.assertEqual(sim.min_gap, math.inf)


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


def straight_planner(lat, lon, goal_lat, goal_lon):
    return [(lat, lon), (goal_lat, goal_lon)]


class CheckRouteTests(unittest.TestCase):
    def test_plans_each_remaining_leg_from_the_rovers_position(self):
        sim = rp.SimRover(rp.DEMO_MISSION, seed=1)
        sim.next_cp = 1
        res, legs = rp.check_route(sim, straight_planner, clock=sim.clock, sleep=sim.sleep)
        self.assertTrue(res["ok"], res)
        self.assertEqual([leg["seq"] for leg in res["legs"]], [2, 3, 4])
        for leg in res["legs"]:
            self.assertAlmostEqual(leg["route_m"], leg["straight_m"], delta=0.11)
            self.assertNotIn("points", leg)
        self.assertEqual(len(legs[0]["points"]), 2)
        # the rover is still at the start, so the first leg is measured from there
        self.assertAlmostEqual(res["legs"][0]["straight_m"], math.hypot(85.0, 5.0), delta=8.0)
        self.assertEqual(sim.next_cp, 1)  # nothing was reported
        self.assertEqual(len(sim.queue), 0)  # and nothing was driven

    def test_legs_without_a_route_fail_the_check(self):
        sim = rp.SimRover(rp.DEMO_MISSION, seed=1)
        res, _ = rp.check_route(sim, lambda *a: None, clock=sim.clock, sleep=sim.sleep)
        self.assertFalse(res["ok"])
        self.assertIn("4 of 4", res["reason"])
        self.assertTrue(all(leg["route_m"] is None for leg in res["legs"]))
        self.assertEqual(res["route_m"], 0.0)

    def test_no_fix_means_no_check(self):
        class NoFix:
            def data(self):
                return {"latitude": 1000, "longitude": 1000}

        c = FakeClock()
        res, legs = rp.check_route(NoFix(), straight_planner, clock=c.clock, sleep=c.sleep,
                                   fix_timeout_s=3.0)
        self.assertFalse(res["ok"])
        self.assertEqual(res["reason"], "no GPS fix")
        self.assertEqual(legs, [])

    def test_needs_a_map(self):
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            rp.main(["--simulate", "--check-route"])


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


MISSIONS = [{"slug": "berkeley-loop", "distance_in_m": 1200, "checkpoints_count": 6},
            {"slug": "campus-short", "distance_in_m": 300, "checkpoints_count": 3}]


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

    def test_front_image_is_decoded_from_base64(self):
        payload = {"front_frame": base64.b64encode(b"jpeg bytes").decode(), "timestamp": 1.0}
        with mock.patch.object(rp.urllib.request, "urlopen",
                               return_value=FakeResp(200, payload)) as m:
            self.assertEqual(rp.SdkClient("http://x").front_image(), b"jpeg bytes")
        self.assertEqual(m.call_args[0][0].full_url, "http://x/v2/front")
        payload = {"front_frame": "data:image/jpeg;base64," + base64.b64encode(b"x").decode()}
        with mock.patch.object(rp.urllib.request, "urlopen", return_value=FakeResp(200, payload)):
            self.assertEqual(rp.SdkClient("http://x").front_image(), b"x")

    def test_missing_front_image(self):
        with mock.patch.object(rp.urllib.request, "urlopen",
                               side_effect=urllib.error.URLError("refused")):
            self.assertIsNone(rp.SdkClient().front_image())
        with mock.patch.object(rp.urllib.request, "urlopen", return_value=FakeResp(200, {})):
            self.assertIsNone(rp.SdkClient().front_image())
            self.assertIsNone(rp.SdkCamera(rp.SdkClient(), None)())

    def test_missions_as_a_list_or_wrapped(self):
        for payload in (MISSIONS, {"missions": MISSIONS}):
            with mock.patch.object(rp.urllib.request, "urlopen",
                                   return_value=FakeResp(200, payload)) as m:
                self.assertEqual(rp.SdkClient("http://x").missions(), MISSIONS)
            self.assertEqual(m.call_args[0][0].full_url, "http://x/missions")
        with mock.patch.object(rp.urllib.request, "urlopen", return_value=FakeResp(200, {})):
            self.assertEqual(rp.SdkClient().missions(), [])

    def test_missions_call_failed(self):
        with mock.patch.object(rp.urllib.request, "urlopen",
                               side_effect=urllib.error.URLError("refused")):
            self.assertIsNone(rp.SdkClient().missions())


class MainTests(unittest.TestCase):
    def test_simulate_cli(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = rp.main(["--simulate", "--seed", "4"])
        self.assertEqual(code, 0, buf.getvalue())
        res = json.loads(buf.getvalue())
        self.assertTrue(res["ok"])
        self.assertEqual(len(res["legs"]), 4)

    def test_simulate_cli_with_vision(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = rp.main(["--simulate", "--vision", "--obstacles", "--seed", "4",
                            "--timeout", "20"])
        res = json.loads(buf.getvalue())
        self.assertEqual(code, 1)  # 20 s is too short for the whole mission
        self.assertEqual(res["reason"], "timeout")
        self.assertGreaterEqual(res["vision"]["frames"], 1, res)
        self.assertIn("sim_contacts", res)

    def test_calibrate_then_fly_cli(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "calibration.json")
            buf = io.StringIO()
            with redirect_stdout(buf):
                code = rp.main(["--simulate", "--sim-quirks", "--calibrate",
                                "--calibration-out", path])
            self.assertEqual(code, 0, buf.getvalue())
            with open(path, encoding="utf-8") as f:
                saved = json.load(f)
            self.assertEqual(saved["orientation_scale"], 256.0)
            self.assertFalse(saved["orientation_clockwise"])
            self.assertFalse(saved["angular_right_positive"])
            buf = io.StringIO()
            with redirect_stdout(buf):
                code = rp.main(["--simulate", "--sim-quirks", "--seed", "4",
                                "--calibration", path])
            self.assertEqual(code, 0, buf.getvalue())
            self.assertEqual(json.loads(buf.getvalue())["reached"], [1, 2, 3, 4])

    def test_failed_calibration_is_refused(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "calibration.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"ok": False, "reason": "no GPS fix"}, f)
            with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                rp.main(["--simulate", "--calibration", path])

    def test_list_missions_cli(self):
        buf = io.StringIO()
        with mock.patch.object(rp.urllib.request, "urlopen",
                               return_value=FakeResp(200, MISSIONS)), redirect_stdout(buf):
            code = rp.main(["--sdk", "http://x", "--list-missions"])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(buf.getvalue())["missions"], MISSIONS)
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            rp.main(["--simulate", "--list-missions"])


if __name__ == "__main__":
    unittest.main()
