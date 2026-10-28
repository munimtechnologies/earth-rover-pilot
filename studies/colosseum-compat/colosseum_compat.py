"""colosseum_compat.py: does earth-rover-pilot run unchanged on RoboColosseum?

FrodoBots' RoboColosseum evaluates navigation policies on real Earth Rover
Mini+ rovers. Its colosseum-rover-sdk-bridge (frodobots-org/colosseum-policy-server
pull request 4, commit 92098db, merged 2026-10-26) serves the Earth Rovers
SDK's local HTTP API on localhost:8000 from the current trial, so that an SDK
policy can run unchanged. As that pull request describes it:

  /data               telemetry from the trial's navigation_state (latitude,
                      longitude, heading_deg, speed, battery, rpm_1..rpm_4),
                      orientation = heading, rpms as [[fl, fr, rl, rr, t]]
  /v2/front           the trial's cameras as base64 PNG
  /start-mission,
  /checkpoints-list   the trial's GPS goal as the only checkpoint, lat/lon as
                      strings like the SDK's
  /checkpoint-reached accepted within 15 m; the trial then ends (done)
  /control            SDK commands, held for --horizon steps

A trial also ends after navigation.timeout_s, 300 s by default
(colosseum-client docs/earth-rover-mini-plus.md). The pull request does not
mention a /data timestamp, gps_signal or accels, GET /status or GET /missions,
so BridgeClient serves none of them: the strictest reading of the contract.

BridgeClient is rover_pilot.SdkClient with its HTTP transport (_req) replaced
by that contract, served from a rover_pilot.SimRover that moves like the
rovers in FrodoBots-2K (SIM_REAL) and turns left on a positive angular, as a
real rover does. fly() runs rover_pilot.main() exactly as a real rover would
be run under the bridge (`python rover_pilot.py --timeout 300`), with the
simulator's clock in place of the wall clock. The same flights with the
fuller SDK surface (timestamp, gps_signal and GET /status kept) show what, if
anything, the missing fields cost. The expectations were written down first,
in studies/colosseum-compat/PLAN.md.

    python colosseum_compat.py --out-dir out --seeds 24

By MV2 of Munim, Inc.; written with AI agents. Apache-2.0.
"""

from __future__ import annotations

import argparse
import collections
import contextlib
import io
import json
import math
import os
import random
import statistics
import time
import types
from unittest import mock

import dead_reckon
import rover_pilot as rp

TRIAL_S = 300.0     # navigation.timeout_s's default
ACCEPT_M = 15.0     # the bridge accepts /checkpoint-reached within this
DISTANCES_M = (40.0, 80.0, 120.0)
NOISES_M = (1.5, 0.22)  # SimRover's default GPS noise; recorded FrodoBots-2K sideways RMS
SHAPES = ("bridge", "sdk")
SERVED = {"GET /data", "POST /control", "POST /start-mission", "GET /checkpoints-list",
          "POST /checkpoint-reached", "GET /v2/front"}


class BridgeClient(rp.SdkClient):
    """rover_pilot.SdkClient answered by the bridge's documented contract, from a SimRover.

    With full_sdk, /data also carries the SDK's timestamp and gps_signal and
    GET /status answers, as the Earth Rovers SDK itself does."""

    def __init__(self, sim, goal, full_sdk=False):
        super().__init__("http://localhost:8000")
        self.sim = sim
        self.goal = goal  # (lat, lon)
        self.full_sdk = full_sdk
        self.done = False
        self.accepted_at = None
        self.calls = collections.Counter()

    def _req(self, method, path, body=None, timeout=None):
        key = method + " " + path
        self.calls[key] += 1
        if key == "GET /data":
            return 200, self._data()
        if key == "POST /control":
            cmd = (body or {}).get("command") or {}
            self.sim.control(cmd.get("linear", 0.0), cmd.get("angular", 0.0))
            return 200, {"message": "Command sent successfully"}
        if key == "POST /start-mission":
            return 200, {"message": "Mission started successfully"}
        if key == "GET /checkpoints-list":
            return 200, {"checkpoints_list": [{"sequence": 1,
                                               "latitude": repr(self.goal[0]),
                                               "longitude": repr(self.goal[1])}],
                         "latest_scanned_checkpoint": 1 if self.done else 0}
        if key == "POST /checkpoint-reached":
            fix = rp.parse_fix(*self.sim.gps)
            if fix is not None and rp.haversine_m(fix[0], fix[1], *self.goal) <= ACCEPT_M:
                if not self.done:
                    self.done, self.accepted_at = True, self.sim.t
                return 200, {}
            return 400, {}
        if key == "GET /status" and self.full_sdk:
            return 200, {"telemetry_age_s": 0.0}
        return 404, {}

    def _data(self):
        d = self.sim.data()
        out = {"latitude": d["latitude"], "longitude": d["longitude"],
               "orientation": d["orientation"], "speed": 0.0, "battery": 100.0}
        if "rpms" in d:
            out["rpms"] = d["rpms"]
        if self.full_sdk:
            out["timestamp"] = d["timestamp"]
            out["gps_signal"] = d["gps_signal"]
        return out


def make_sim(seed, distance_m, noise_m=1.5):
    """A SimRover as the FrodoBots-2K rovers move, its goal distance_m away on a
    bearing drawn from (seed, distance_m); returns (sim, goal)."""
    bearing = random.Random(seed * 1000 + int(distance_m)).uniform(0.0, 360.0)
    north = distance_m * math.cos(math.radians(bearing))
    east = distance_m * math.sin(math.radians(bearing))
    sim = rp.SimRover([(north, east)], seed=seed, gps_noise_m=noise_m, angular_sign=-1.0,
                      wheel_mps_per_rpm=dead_reckon.MINI_PLUS_MPS_PER_RPM, **rp.SIM_REAL)
    return sim, sim.checkpoint_coords[0]


def fly(seed, distance_m, shape="bridge", noise_m=1.5, trial_s=TRIAL_S, interrupt_at=None):
    """Run rover_pilot.main() against the bridge contract on one simulated trial.

    interrupt_at: raise KeyboardInterrupt (the bridge's SIGINT at the end of a
    trial) from the clock's sleep once the simulator reaches this time."""
    sim, goal = make_sim(seed, distance_m, noise_m)
    client = BridgeClient(sim, goal, full_sdk=(shape == "sdk"))

    def sleep(seconds):
        sim.sleep(seconds)
        if interrupt_at is not None and sim.t >= interrupt_at:
            raise KeyboardInterrupt

    clock = types.SimpleNamespace(monotonic=sim.clock, sleep=sleep)
    out, err = io.StringIO(), io.StringIO()
    error = None
    with mock.patch.object(rp, "SdkClient", lambda *a, **k: client), \
            mock.patch.object(rp, "time", clock), \
            contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = rp.main(["--timeout", str(trial_s)])
        except Exception as e:  # a crash is a finding (P1), not the end of the run
            code, error = "exception", repr(e)
    text = out.getvalue().strip()
    result = json.loads(text) if text and error is None else None
    true_lat, true_lon = rp.offset_latlon(sim.lat0, sim.lon0, sim.north, sim.east)
    return {
        "seed": seed, "distance_m": distance_m, "shape": shape, "noise_m": noise_m,
        "exit": code,
        "ok": bool(result and result.get("ok")),
        "reason": result.get("reason") if result else None,
        "elapsed_s": result.get("elapsed_s") if result else None,
        "reports": result.get("reports") if result else None,
        "recoveries": result.get("recoveries") if result else None,
        "accepted": client.done,
        "accepted_at_s": None if client.accepted_at is None else round(client.accepted_at, 1),
        "final_true_m": round(rp.haversine_m(true_lat, true_lon, goal[0], goal[1]), 2),
        "travelled_m": round(sim.travelled, 1),
        "reversed": sim.reverse_seen,
        "last_cmd": list(sim.queue[-1][1:]) if sim.queue else list(sim.applied),
        "calls": dict(sorted(client.calls.items())),
        "error": error,
        "stderr": err.getvalue().strip()[-300:],
    }


def summarise(runs):
    cells = collections.defaultdict(list)
    for r in runs:
        cells[(r["shape"], r["noise_m"], r["distance_m"])].append(r)
    table = []
    for (shape, noise, dist), rs in sorted(cells.items()):
        done = [r for r in rs if r["ok"]]
        el = [r["elapsed_s"] for r in done]
        table.append({
            "shape": shape, "noise_m": noise, "distance_m": dist, "n": len(rs),
            "completed": len(done),
            "accepted": sum(r["accepted"] for r in rs),
            "timeouts": sum(r["reason"] == "timeout" for r in rs),
            "crashed": sum(r["exit"] not in (0, 1) for r in rs),
            "median_elapsed_s": round(statistics.median(el), 1) if el else None,
            "max_elapsed_s": max(el) if el else None,
            "median_final_true_m": round(statistics.median(r["final_true_m"] for r in done), 2)
            if done else None,
            "median_recoveries": statistics.median(r["recoveries"] for r in rs
                                                   if r["recoveries"] is not None)
            if any(r["recoveries"] is not None for r in rs) else None,
        })
    pairs = collections.defaultdict(dict)
    for r in runs:
        pairs[(r["seed"], r["noise_m"], r["distance_m"])][r["shape"]] = r
    fields = ("exit", "ok", "reason", "elapsed_s", "reports", "recoveries", "accepted",
              "final_true_m", "travelled_m")
    differ = []
    for key, p in sorted(pairs.items()):
        if "bridge" in p and "sdk" in p:
            diff = [f for f in fields if p["bridge"][f] != p["sdk"][f]]
            if diff:
                differ.append({"seed": key[0], "noise_m": key[1], "distance_m": key[2],
                               "fields": diff})
    called = collections.Counter()
    for r in runs:
        if r["shape"] == "bridge":
            called.update(r["calls"])
    unserved = sorted(k for k in called if k not in SERVED)
    return {"cells": table, "shape_differences": differ, "bridge_calls": dict(called),
            "bridge_unserved_calls": unserved}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--out-dir", required=True)
    p.add_argument("--seeds", type=int, default=24)
    p.add_argument("--first-seed", type=int, default=1)
    args = p.parse_args(argv)
    os.makedirs(args.out_dir, exist_ok=True)
    started = time.time()
    runs = []
    with open(os.path.join(args.out_dir, "runs.jsonl"), "w", encoding="utf-8") as f:
        for noise in NOISES_M:
            for dist in DISTANCES_M:
                for seed in range(args.first_seed, args.first_seed + args.seeds):
                    for shape in SHAPES:
                        r = fly(seed, dist, shape, noise)
                        runs.append(r)
                        f.write(json.dumps(r) + "\n")
                print("noise %.2f distance %.0f done (%.0f s)"
                      % (noise, dist, time.time() - started), flush=True)
    summary = summarise(runs)
    summary.update({"rover_pilot": rp.__version__, "trial_s": TRIAL_S, "accept_m": ACCEPT_M,
                    "seeds": [args.first_seed, args.first_seed + args.seeds - 1],
                    "flights": len(runs), "wall_s": round(time.time() - started, 1)})
    with open(os.path.join(args.out_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=1)
    print(json.dumps(summary, indent=1), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
