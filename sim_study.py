#!/usr/bin/env python3
"""sim_study: does moving the late GPS fix forward help a rover that moves like a real Earth Rover?

On the FrodoBots-2K rides (FINDINGS-frodobots-2k.md) the rover does about
0.79 m/s per unit of linear, its wheels answer 0.8 s after the command and its
GPS runs 1.5 s behind the wheels. This flies the same missions on the same
random seeds with the plain pilot and with --gps-lag 1.5, in three simulator
profiles:

- sim-default: the simulator as it was (1.2 m/s, 0.5 s latency, no GPS delay),
  to see what compensation costs a rover that doesn't need it;
- real-yaw60: SIM_REAL with the simulator's 60 deg/s per unit of angular;
- real-yaw30: SIM_REAL turning half as fast (the real yaw rate isn't measured yet).

and writes summary.json and report.md: missions completed, time, refused
reports, recoveries and distance driven, and a paired sign test of mission
time per seed.

    python sim_study.py --out-dir out --seeds 30

Standard library only. By MV2 of Munim, Inc.; written with AI agents. Apache-2.0.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import statistics
import sys
import time

import rover_pilot as rp

__version__ = "0.1.0"

MISSIONS = {
    "demo": rp.DEMO_MISSION,
    "zigzag": [(30.0, 20.0), (60.0, -20.0), (90.0, 20.0), (120.0, -20.0), (150.0, 20.0)],
}
PROFILES = {
    "sim-default": {},
    "real-yaw60": dict(rp.SIM_REAL),
    "real-yaw30": dict(rp.SIM_REAL, max_yaw_dps=30.0),
}
PILOTS = {"plain": {}, "gps-lag-1.5": {"gps_lag_s": 1.5}}


def straight_m(mission):
    pts = [(0.0, 0.0)] + list(mission)
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:]))


def fly(mission, seed, sim_kw, pilot_kw, timeout_s):
    sim = rp.SimRover(MISSIONS[mission], seed=seed, **sim_kw)
    res = rp.Pilot(sim, clock=sim.clock, sleep=sim.sleep, **pilot_kw).run(timeout_s=timeout_s)
    return {"ok": res["ok"], "reason": res["reason"], "elapsed_s": res["elapsed_s"],
            "reached": len(res["reached"]), "checkpoints": res["checkpoints"],
            "reports": res["reports"], "recoveries": res["recoveries"],
            "travelled_m": round(sim.travelled, 1)}


def sign_test_p(wins, losses):
    """Two-sided exact binomial p-value for wins against losses (ties left out)."""
    n = wins + losses
    if n == 0:
        return None
    k = min(wins, losses)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / 2.0 ** n
    return min(1.0, 2.0 * tail)


def _mean(values, digits=2):
    return round(statistics.fmean(values), digits) if values else None


def _median(values, digits=1):
    return round(statistics.median(values), digits) if values else None


def summarise(runs):
    groups = {}
    for r in runs:
        groups.setdefault((r["mission"], r["profile"], r["pilot"]), []).append(r)
    rows = []
    for (mission, profile, pilot), rs in sorted(groups.items()):
        ok = [r for r in rs if r["ok"]]
        rows.append({
            "mission": mission, "profile": profile, "pilot": pilot, "runs": len(rs),
            "completed": len(ok),
            "median_time_s": _median([r["elapsed_s"] for r in ok]),
            "mean_time_s": _mean([r["elapsed_s"] for r in ok], 1),
            "mean_refused_reports": _mean([r["reports"] - r["reached"] for r in rs]),
            "mean_recoveries": _mean([r["recoveries"] for r in rs]),
            "mean_path_ratio": _mean([r["travelled_m"] / straight_m(MISSIONS[mission])
                                      for r in ok], 3),
        })
    paired = []
    for mission in MISSIONS:
        for profile in PROFILES:
            a = {r["seed"]: r for r in groups.get((mission, profile, "plain"), [])}
            b = {r["seed"]: r for r in groups.get((mission, profile, "gps-lag-1.5"), [])}
            seeds = sorted(s for s in a if s in b)
            both = [s for s in seeds if a[s]["ok"] and b[s]["ok"]]
            diffs = [b[s]["elapsed_s"] - a[s]["elapsed_s"] for s in both]
            faster = sum(1 for d in diffs if d < 0)
            slower = sum(1 for d in diffs if d > 0)
            paired.append({
                "mission": mission, "profile": profile, "seeds": len(seeds),
                "both_completed": len(both),
                "only_plain_completed": sum(1 for s in seeds if a[s]["ok"] and not b[s]["ok"]),
                "only_compensated_completed": sum(1 for s in seeds
                                                  if b[s]["ok"] and not a[s]["ok"]),
                "compensated_faster": faster, "compensated_slower": slower,
                "median_time_diff_s": _median(diffs), "mean_time_diff_s": _mean(diffs, 1),
                "sign_test_p": None if sign_test_p(faster, slower) is None
                else round(sign_test_p(faster, slower), 4),
            })
    return rows, paired


def write_outputs(out_dir, runs, started, seeds, timeout_s, done):
    rows, paired = summarise(runs)
    result = {"version": __version__, "rover_pilot": rp.__version__, "done": done,
              "elapsed_s": round(time.monotonic() - started, 1), "seeds": seeds,
              "timeout_s": timeout_s, "sim_real": rp.SIM_REAL,
              "missions": {k: {"checkpoints": v, "straight_m": round(straight_m(v), 1)}
                           for k, v in MISSIONS.items()},
              "profiles": PROFILES, "pilots": PILOTS, "runs": len(runs),
              "groups": rows, "paired": paired}
    with open(os.path.join(out_dir, "summary.json"), "w") as f:
        json.dump(result, f, indent=1)
    with open(os.path.join(out_dir, "runs.jsonl"), "w") as f:
        for r in runs:
            f.write(json.dumps(r) + "\n")
    md = ["# Late-GPS compensation in the earth-rover-pilot simulator", "",
          "sim_study.py %s, rover_pilot.py %s, MV2 of Munim, Inc. Simulated rovers only; "
          "SIM_REAL = %s from FrodoBots-2K measurements. Seeds 1-%d, timeout %d s."
          % (__version__, rp.__version__, json.dumps(rp.SIM_REAL), seeds, timeout_s), "",
          "## Per group", "",
          "| mission | profile | pilot | completed | median s | mean s | refused/run | "
          "recoveries/run | path ratio |", "|---|---|---|---|---|---|---|---|---|"]
    md += ["| %s | %s | %s | %d/%d | %s | %s | %s | %s | %s |"
           % (r["mission"], r["profile"], r["pilot"], r["completed"], r["runs"],
              r["median_time_s"], r["mean_time_s"], r["mean_refused_reports"],
              r["mean_recoveries"], r["mean_path_ratio"]) for r in rows]
    md += ["", "## Paired by seed (compensated minus plain)", "",
           "| mission | profile | both done | only plain | only comp. | comp. faster | "
           "comp. slower | median diff s | mean diff s | sign test p |",
           "|---|---|---|---|---|---|---|---|---|---|"]
    md += ["| %s | %s | %d | %d | %d | %d | %d | %s | %s | %s |"
           % (p["mission"], p["profile"], p["both_completed"], p["only_plain_completed"],
              p["only_compensated_completed"], p["compensated_faster"], p["compensated_slower"],
              p["median_time_diff_s"], p["mean_time_diff_s"], p["sign_test_p"]) for p in paired]
    with open(os.path.join(out_dir, "report.md"), "w") as f:
        f.write("\n".join(md) + "\n")
    return result


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out-dir", default="out")
    ap.add_argument("--seeds", type=int, default=30)
    ap.add_argument("--timeout", type=float, default=1500.0, help="simulated seconds per mission")
    ap.add_argument("--budget-min", type=float, default=100.0)
    args = ap.parse_args(argv)
    os.makedirs(args.out_dir, exist_ok=True)
    started = time.monotonic()
    runs = []
    done = True
    for mission in MISSIONS:
        for profile, sim_kw in PROFILES.items():
            for pilot, pilot_kw in PILOTS.items():
                if time.monotonic() - started > args.budget_min * 60.0:
                    done = False
                    break
                for seed in range(1, args.seeds + 1):
                    try:
                        r = fly(mission, seed, sim_kw, pilot_kw, args.timeout)
                    except Exception as exc:
                        r = {"ok": False, "reason": "%s: %s" % (type(exc).__name__, exc),
                             "elapsed_s": None, "reached": 0, "checkpoints": None,
                             "reports": 0, "recoveries": 0, "travelled_m": 0.0}
                    r.update(mission=mission, profile=profile, pilot=pilot, seed=seed)
                    runs.append(r)
                print("%s / %s / %s: %d runs so far, %.0f s"
                      % (mission, profile, pilot, len(runs), time.monotonic() - started),
                      flush=True)
                write_outputs(args.out_dir, runs, started, args.seeds, args.timeout, False)
    result = write_outputs(args.out_dir, runs, started, args.seeds, args.timeout, done)
    for p in result["paired"]:
        print(json.dumps(p), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
