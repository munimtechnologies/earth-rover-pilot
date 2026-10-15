"""Tests for stopping the rover when its telemetry stops coming in (TelemetryWatch).

The SDK caches the last telemetry it got, so after the rover's link drops
/data keeps answering with the same reading, GPS fix included.

Run: python -m unittest test_telemetry -v
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


class FrozenLink:
    """A SimRover whose telemetry stops reaching the SDK from freeze_s until
    thaw_s: /data keeps answering with the last reading, as the SDK's cache
    does, while commands still get through. With stamps=False the readings
    carry no timestamp."""

    def __init__(self, sim, freeze_s, thaw_s=math.inf, stamps=True):
        self.sim = sim
        self.freeze_s = freeze_s
        self.thaw_s = thaw_s
        self.stamps = stamps
        self.sent = []  # (t, linear, angular)
        self._last = None

    def frozen(self):
        return self.freeze_s <= self.sim.t < self.thaw_s

    def clock(self):
        return self.sim.clock()

    def sleep(self, seconds):
        self.sim.sleep(seconds)

    def data(self):
        if self._last is None or not self.frozen():
            d = self.sim.data()
            if not self.stamps:
                d.pop("timestamp")
            self._last = d
        return dict(self._last)

    def control(self, linear, angular):
        self.sent.append((self.sim.t, linear, angular))
        self.sim.control(linear, angular)

    def start_mission(self):
        return self.sim.start_mission()

    def checkpoints(self):
        return self.sim.checkpoints()

    def checkpoint_reached(self):
        return self.sim.checkpoint_reached()


class FrozenLinkWithStatus(FrozenLink):
    """The same, with the SDK's GET /status telemetry_age_s."""
    status_calls = 0

    def telemetry_age(self):
        self.status_calls += 1
        return self.sim.t - self.freeze_s if self.frozen() else 0.2


def moving(sent, after, before=math.inf):
    """Commands other than a stop sent between `after` and `before` (seconds)."""
    return [c for c in sent if after < c[0] < before and (c[1], c[2]) != (0.0, 0.0)]


def fly(link, timeout_s):
    events = []
    res = rp.Pilot(link, clock=link.clock, sleep=link.sleep,
                   log=events.append).run(timeout_s=timeout_s)
    return res, [e["event"] for e in events]


class WatchTests(unittest.TestCase):
    def test_a_frozen_fix_looks_fresh_to_the_gps_filter(self):
        # why the watch is needed: a repeated reading keeps the fix "current"
        g = rp.GpsFilter()
        g.update(LAT, LON, 0.25)
        g.update(LAT, LON, 60.25)
        self.assertTrue(g.has_fix(60.25))

    def test_stale_when_the_timestamp_stops_changing(self):
        w = rp.TelemetryWatch(5.0)
        w.update(100.25, 1724189733.2)
        self.assertFalse(w.stale(100.25))
        self.assertEqual(w.since(100.25), 0.0)
        w.update(105.0, 1724189733.2)
        self.assertFalse(w.stale(105.0))  # 4.75 s
        w.update(105.5, 1724189733.2)
        self.assertTrue(w.stale(105.5))   # 5.25 s
        w.update(105.75, "1724189735.2")  # a new reading, as text
        self.assertFalse(w.stale(105.75))
        self.assertEqual(w.since(105.75), 0.0)

    def test_no_usable_timestamp_skips_the_check(self):
        w = rp.TelemetryWatch(5.0)
        for t, stamp in ((0.25, None), (10.25, "abc"), (30.25, float("nan")), (50.25, None)):
            w.update(t, stamp)
        self.assertIsNone(w.since(50.25))
        self.assertFalse(w.stale(50.25))

    def test_zero_timeout_turns_it_off(self):
        w = rp.TelemetryWatch(0.0)
        w.update(0.25, 1.0)
        self.assertFalse(w.stale(100.25))

    def test_sdk_age_is_asked_at_most_once_a_second(self):
        ages = iter([0.4, 7.0, None])
        calls = []

        def age():
            calls.append(1)
            return next(ages)

        w = rp.TelemetryWatch(5.0, age=age)
        w.update(0.25, None)
        self.assertFalse(w.stale(0.25))
        w.update(0.75, None)
        self.assertEqual(len(calls), 1)
        w.update(1.25, None)
        self.assertEqual(len(calls), 2)
        self.assertTrue(w.stale(1.25))    # the SDK says 7 s
        w.update(2.25, None)
        self.assertEqual(len(calls), 3)
        self.assertFalse(w.stale(2.25))   # it no longer says


class SimulatorUnchangedTests(unittest.TestCase):
    def test_the_watch_never_fires_in_the_simulator(self):
        for sim_kw in ({}, rp.SIM_REAL):
            out = []
            for timeout in (rp.TELEMETRY_TIMEOUT_S, 0.0):
                sim = rp.SimRover(rp.DEMO_MISSION, seed=1, **sim_kw)
                events = []
                res = rp.Pilot(sim, clock=sim.clock, sleep=sim.sleep, telemetry_timeout_s=timeout,
                               log=events.append).run(timeout_s=1500)
                out.append((res, sim.t, sim.north, sim.east))
                self.assertFalse([e for e in events if e["event"].startswith("telemetry")])
            self.assertTrue(out[0][0]["ok"], out[0][0])
            self.assertEqual(out[0][0]["telemetry_stops"], 0)
            self.assertEqual(out[0], out[1])


class FrozenTelemetryTests(unittest.TestCase):
    def test_rover_stops_when_the_timestamp_freezes(self):
        link = FrozenLink(rp.SimRover(rp.DEMO_MISSION, seed=1), freeze_s=15.0)
        res, names = fly(link, 40)
        self.assertFalse(res["ok"])
        self.assertEqual(res["reason"], "timeout")
        self.assertTrue(moving(link.sent, 0.0, 15.0))   # it was driving before
        self.assertEqual(moving(link.sent, 20.3), [])   # and stopped 5 s after the freeze
        self.assertEqual(res["telemetry_stops"], 1)
        self.assertIn("telemetry-stale", names)

    def test_rover_stops_on_the_sdk_status_without_timestamps(self):
        link = FrozenLinkWithStatus(rp.SimRover(rp.DEMO_MISSION, seed=1), freeze_s=15.0,
                                    stamps=False)
        res, names = fly(link, 40)
        self.assertEqual(res["reason"], "timeout")
        self.assertTrue(moving(link.sent, 0.0, 15.0))
        self.assertEqual(moving(link.sent, 21.5), [])   # /status is asked once a second
        self.assertIn("telemetry-stale", names)
        self.assertGreater(link.status_calls, 20)
        self.assertLessEqual(link.status_calls, 42)

    def test_without_timestamp_or_status_it_cannot_tell(self):
        # the limit of the watch: nothing shows the reading is old, so it drives on
        # (no GPS dropouts, so the frozen reading surely has a fix)
        link = FrozenLink(rp.SimRover(rp.DEMO_MISSION, seed=1, gps_dropout=0.0), freeze_s=15.0,
                          stamps=False)
        res, names = fly(link, 40)
        self.assertTrue(moving(link.sent, 20.3))
        self.assertEqual(res["telemetry_stops"], 0)
        self.assertNotIn("telemetry-stale", names)

    def test_rover_drives_on_when_telemetry_is_back(self):
        link = FrozenLink(rp.SimRover(rp.DEMO_MISSION, seed=1), freeze_s=15.0, thaw_s=30.0)
        res, names = fly(link, 1500)
        self.assertTrue(res["ok"], res)
        self.assertEqual(res["reached"], [1, 2, 3, 4])
        self.assertEqual(res["telemetry_stops"], 1)
        self.assertEqual(moving(link.sent, 20.3, 29.95), [])
        self.assertEqual([n for n in names if n.startswith("telemetry")],
                         ["telemetry-stale", "telemetry-back"])


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


class SdkStatusTests(unittest.TestCase):
    def test_telemetry_age_from_status(self):
        payload = {"browser_ready": True, "mission_started": True, "ingest_connected": True,
                   "telemetry_age_s": 0.42}
        with mock.patch.object(rp.urllib.request, "urlopen",
                               return_value=FakeResp(200, payload)) as m:
            self.assertEqual(rp.SdkClient("http://x").telemetry_age(), 0.42)
        req = m.call_args[0][0]
        self.assertEqual(req.full_url, "http://x/status")
        self.assertEqual(req.get_method(), "GET")

    def test_no_age_when_status_says_nothing(self):
        for payload in ({"telemetry_age_s": None}, {}, {"telemetry_age_s": True},
                        {"telemetry_age_s": "soon"}):
            with mock.patch.object(rp.urllib.request, "urlopen",
                                   return_value=FakeResp(200, payload)):
                self.assertIsNone(rp.SdkClient("http://x").telemetry_age(), payload)

    def test_no_age_from_an_sdk_without_status(self):
        err = urllib.error.HTTPError("http://x/status", 404, "Not Found", {},
                                     io.BytesIO(b'{"detail": "Not Found"}'))
        with mock.patch.object(rp.urllib.request, "urlopen", side_effect=err):
            self.assertIsNone(rp.SdkClient("http://x").telemetry_age())
        with mock.patch.object(rp.urllib.request, "urlopen",
                               side_effect=urllib.error.URLError("refused")):
            self.assertIsNone(rp.SdkClient("http://x").telemetry_age())


class FakePilot:
    """Stands in for rp.Pilot and records what main() built it with."""
    seen = {}

    def __init__(self, rover, **kw):
        FakePilot.seen = dict(kw, rover=rover)

    def run(self, start=True, timeout_s=3600.0):
        return {"ok": True, "reason": "mission completed"}


def run_main(argv):
    buf = io.StringIO()
    with mock.patch.object(rp, "Pilot", FakePilot), redirect_stdout(buf):
        code = rp.main(argv)
    return code, FakePilot.seen


class CommandLineTests(unittest.TestCase):
    def test_default_timeout(self):
        for argv in (["--sdk", "http://x"], ["--simulate"]):
            code, seen = run_main(argv)
            self.assertEqual(code, 0)
            self.assertEqual(seen["telemetry_timeout_s"], 5.0)

    def test_timeout_option(self):
        code, seen = run_main(["--sdk", "http://x", "--telemetry-timeout", "0"])
        self.assertEqual(code, 0)
        self.assertEqual(seen["telemetry_timeout_s"], 0.0)

    def test_sdk_client_is_watched_through_status(self):
        pilot = rp.Pilot(rp.SdkClient("http://x"))
        self.assertIsNotNone(pilot.telemetry.age)
        sim = rp.SimRover(rp.DEMO_MISSION)
        self.assertIsNone(rp.Pilot(sim, clock=sim.clock, sleep=sim.sleep).telemetry.age)


if __name__ == "__main__":
    unittest.main()
