"""colosseum_hold.py: does earth-rover-pilot still steer when RoboColosseum's
bridge takes its commands only every 2-3 s?

colosseum_compat.py (studies/colosseum-compat) serves the Earth Rovers SDK API
the way colosseum-rover-sdk-bridge's first pull request (frodobots-org/
colosseum-policy-server #4) describes it, and passes every /control straight
to the rover. A later pull request in the same repository (#8, the GeNIE
baseline for the Earth Rover track, opened 2026-10-27) says how the bridge
really paces an SDK program: "the bridge answers each observation, every 2-3 s,
with the command current at that instant", so "advances hold until the next
plan, and in-place turns last until an observation has sampled them".

earth-rover-pilot sends a command every 0.1 s. Its steering turns
kp * error = error/60 of full angular, and the simulator (like the pilot's
model of a Mini+) yaws 60 deg/s at full angular, so a command held for T s
turns the rover by about error * T degrees. For T of 2-3 s that is 2-3 times
the error: each held turn overshoots, until the max_angular clamp bounds it.

HoldBridgeClient is colosseum_compat.BridgeClient with that cadence:
  hold   /control is stored; at each observation (every U(2, 3) s) the latest
         command is taken and the rover keeps getting it until the next one
  stale  as hold, and /data is the observation's telemetry, also refreshed
         only every 2-3 s
  live   colosseum_compat.BridgeClient's behaviour exactly (the control arm)
The fix arms fly stale with the pilot's existing --max-angular flag lowered,
which bounds how far one held command can turn the rover. No pilot code
changes. The expectations were written down first, in
studies/colosseum-hold/PLAN.md.

    python colosseum_hold.py --out-dir out --seeds 24

By MV2 of Munim, Inc.; written with AI agents. Apache-2.0.
"""

from __future__ import annotations

import argparse
import collections
import contextlib
import io
import json
import os
import random
import statistics
import time
import types
from unittest import mock

import colosseum_compat as cc
import rover_pilot as rp

TRIAL_S = cc.TRIAL_S
DISTANCES_M = (30.0, 80.0)
NOISES_M = cc.NOISES_M
HOLD_S = (2.0, 3.0)     # "every 2-3 s" (colosseum-policy-server pull request 8)
TURN_SIGN = 0.05        # angular commands smaller than this count as straight
ARMS = {
    "live": {"hold": False, "stale": False, "argv": ()},
    "hold": {"hold": True, "stale": False, "argv": ()},
    "stale": {"hold": True, "stale": True, "argv": ()},
    "stale-m30": {"hold": True, "stale": True, "argv": ("--max-angular", "0.3")},
    "stale-m15": {"hold": True, "stale": True, "argv": ("--max-angular", "0.15")},
}
FIX_ARMS = ("stale-m30", "stale-m15")
PASS_COMPLETED = 23     # of 24 flights per cell
PASS_TIME_RATIO = 1.5   # median time against live's, per cell


class HoldBridgeClient(cc.BridgeClient):
    """colosseum_compat.BridgeClient whose rover gets a sampled, held command.

    hold=False passes /control straight through, exactly as BridgeClient does.
    With hold=True, tick() must run before every simulator step."""

    def __init__(self, sim, goal, rng=None, hold=False, stale=False):
        super().__init__(sim, goal)
        self.rng = rng
        self.hold = hold
        self.stale = stale
        self.pending = (0.0, 0.0)
        self.held = (0.0, 0.0)
        self.next_sample = 0.0
        self.samples = 0
        self.flips = 0
        self._last_sign = 0
        self.obs = None

    def _req(self, method, path, body=None, timeout=None):
        if method + " " + path != "POST /control":
            return super()._req(method, path, body, timeout)
        self.calls["POST /control"] += 1
        cmd = (body or {}).get("command") or {}
        if not self.hold:
            self._count(cmd.get("angular", 0.0))
            self.sim.control(cmd.get("linear", 0.0), cmd.get("angular", 0.0))
        else:
            self.pending = (float(cmd.get("linear", 0.0)), float(cmd.get("angular", 0.0)))
        return 200, {"message": "Command sent successfully"}

    def _data(self):
        if self.stale and self.obs is not None:
            return dict(self.obs)
        return super()._data()

    def _count(self, angular):
        sign = (angular > TURN_SIGN) - (angular < -TURN_SIGN)
        if sign and self._last_sign and sign != self._last_sign:
            self.flips += 1
        if sign:
            self._last_sign = sign

    def tick(self):
        """One observation if one is due, then the held command to the rover."""
        if self.sim.t >= self.next_sample - 1e-9:
            self.held = self.pending
            self.samples += 1
            self._count(self.held[1])
            if self.stale:
                self.obs = cc.BridgeClient._data(self)
            self.next_sample = self.sim.t + self.rng.uniform(*HOLD_S)
        self.sim.control(*self.held)


def hold_rng(seed, distance_m, noise_m):
    """The observation cadence for one flight, shared by every held arm."""
    return random.Random("hold-%d-%d-%d" % (seed, int(distance_m), round(noise_m * 100)))


def fly(seed, distance_m, arm="hold", noise_m=1.5, trial_s=TRIAL_S):
    """Run rover_pilot.main() on one simulated trial under one arm's bridge."""
    spec = ARMS[arm]
    sim, goal = cc.make_sim(seed, distance_m, noise_m)
    client = HoldBridgeClient(sim, goal, hold_rng(seed, distance_m, noise_m),
                              hold=spec["hold"], stale=spec["stale"])

    def sleep(seconds):
        if not client.hold:
            sim.sleep(seconds)
            return
        end = sim.t + seconds
        while True:
            client.tick()
            sim.sleep(sim.dt)
            if sim.t >= end - 1e-9:
                break

    clock = types.SimpleNamespace(monotonic=sim.clock, sleep=sleep)
    out, err = io.StringIO(), io.StringIO()
    error = None
    with mock.patch.object(rp, "SdkClient", lambda *a, **k: client), \
            mock.patch.object(rp, "time", clock), \
            contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = rp.main(["--timeout", str(trial_s)] + list(spec["argv"]))
        except Exception as e:  # a crash is a finding (H7), not the end of the run
            code, error = "exception", repr(e)
    text = out.getvalue().strip()
    result = json.loads(text) if text and error is None else None
    true_lat, true_lon = rp.offset_latlon(sim.lat0, sim.lon0, sim.north, sim.east)
    return {
        "seed": seed, "distance_m": distance_m, "arm": arm, "noise_m": noise_m,
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
        "path_ratio": round(sim.travelled / distance_m, 3),
        "samples": client.samples if client.hold else None,
        "flips": client.flips,
        "calls": dict(sorted(client.calls.items())),
        "error": error,
        "stderr": err.getvalue().strip()[-300:],
    }


def _median(xs):
    xs = [x for x in xs if x is not None]
    return round(statistics.median(xs), 2) if xs else None


def summarise(runs):
    cells = collections.defaultdict(list)
    for r in runs:
        cells[(r["arm"], r["noise_m"], r["distance_m"])].append(r)
    table = {}
    for key, rs in cells.items():
        done = [r for r in rs if r["ok"]]
        table[key] = {
            "arm": key[0], "noise_m": key[1], "distance_m": key[2], "n": len(rs),
            "completed": len(done),
            "accepted": sum(r["accepted"] for r in rs),
            "timeouts": sum(r["reason"] == "timeout" for r in rs),
            "crashed": sum(r["exit"] not in (0, 1) for r in rs),
            "median_elapsed_s": _median([r["elapsed_s"] for r in done]),
            "median_final_true_m": _median([r["final_true_m"] for r in done]),
            "median_path_ratio": _median([r["path_ratio"] for r in done]),
            "median_recoveries": _median([r["recoveries"] for r in rs]),
            "median_flips": _median([r["flips"] for r in rs]),
        }
    for key, c in table.items():
        live = table.get(("live",) + key[1:])
        c["time_ratio"] = (round(c["median_elapsed_s"] / live["median_elapsed_s"], 3)
                           if live and c["median_elapsed_s"] and live["median_elapsed_s"]
                           else None)
        c["path_ratio_vs_live"] = (round(c["median_path_ratio"] / live["median_path_ratio"], 3)
                                   if live and c["median_path_ratio"] and live["median_path_ratio"]
                                   else None)
    arms = collections.defaultdict(list)
    for c in table.values():
        arms[c["arm"]].append(c)
    passes = {}
    for arm, cs in arms.items():
        passes[arm] = all(c["completed"] >= PASS_COMPLETED and c["time_ratio"] is not None
                          and c["time_ratio"] <= PASS_TIME_RATIO for c in cs)
    if passes.get("hold") and passes.get("stale"):
        decision = {"rule": "R1", "arm": None}
    else:
        passing = [a for a in FIX_ARMS if passes.get(a)]
        if passing:
            best = min(passing, key=lambda a: sum(c["median_elapsed_s"] for c in arms[a]))
            decision = {"rule": "R2", "arm": best}
        else:
            decision = {"rule": "R3", "arm": None}
    called = collections.Counter()
    for r in runs:
        called.update(r["calls"])
    order = list(ARMS)
    return {
        "cells": sorted(table.values(),
                        key=lambda c: (order.index(c["arm"]), c["noise_m"], c["distance_m"])),
        "passes": passes, "decision": decision,
        "calls": dict(called),
        "unserved_calls": sorted(k for k in called if k not in cc.SERVED),
    }


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
                    for arm in ARMS:
                        r = fly(seed, dist, arm, noise)
                        runs.append(r)
                        f.write(json.dumps(r) + "\n")
                print("noise %.2f distance %.0f done (%.0f s)"
                      % (noise, dist, time.time() - started), flush=True)
    summary = summarise(runs)
    summary.update({"rover_pilot": rp.__version__, "trial_s": TRIAL_S, "hold_s": list(HOLD_S),
                    "seeds": [args.first_seed, args.first_seed + args.seeds - 1],
                    "flights": len(runs), "wall_s": round(time.time() - started, 1)})
    with open(os.path.join(args.out_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=1)
    print(json.dumps(summary, indent=1), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
