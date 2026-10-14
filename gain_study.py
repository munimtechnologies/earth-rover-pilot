#!/usr/bin/env python3
"""gain_study: which steering gains suit a rover that moves like a real Earth Rover?

The pilot's gains (cruise 0.6, full turn rate at a 60 deg error, angular capped
at 0.6, turn in place above 60 deg) were tuned on the simulator's own rover:
1.2 m/s and 60 deg/s per unit of command. On the FrodoBots-2K rides
(FINDINGS-frodobots-2k.md) a real rover does about 0.79 m/s per unit of linear
and its gyroscope reads about 28-36 deg/s per unit of angular, with the wheels
0.8 s behind the command and the GPS 1.5 s behind the wheels. Capped at 0.6, a
real rover turns at only about 18 deg/s.

This flies the same missions on the same random seeds with a grid of steering
settings, in three real-like profiles (SIM_REAL turning at 20, 30 and 45 deg/s
per unit, since the yaw rate is only roughly known), and compares each setting
with the current defaults: missions completed, time, refused reports,
recoveries, distance driven, and a paired sign test of mission time per seed.
It writes summary.json, runs.jsonl and report.md.

    python gain_study.py --out-dir out --seeds 30

Simulated rovers only. Standard library only. By MV2 of Munim, Inc.; written
with AI agents. Apache-2.0.
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
    # Right-angle corners and a leg that doubles back.
    "hairpin": [(40.0, 0.0), (40.0, 25.0), (0.0, 25.0), (0.0, 50.0)],
}
PROFILES = {
    "real-yaw20": dict(rp.SIM_REAL, max_yaw_dps=20.0),
    "real-yaw30": dict(rp.SIM_REAL, max_yaw_dps=30.0),
    "real-yaw45": dict(rp.SIM_REAL, max_yaw_dps=45.0),
}


def config_name(c):
    return "c%g-a%g-k%g-t%g" % (c["cruise"], c["max_angular"], c["full_turn_deg"],
                                c["turn_in_place_deg"])


def _grid():
    configs = {}
    for cruise in (0.6, 0.8, 1.0):
        for max_angular in (0.6, 1.0):
            for full_turn_deg in (60.0, 30.0):
                for tip in (60.0, 90.0):
                    c = {"cruise": cruise, "max_angular": max_angular,
                         "full_turn_deg": full_turn_deg, "turn_in_place_deg": tip}
                    configs[config_name(c)] = c
    return configs


# The first one is the pilot's current default steering.
CONFIGS = _grid()
BASELINE = next(iter(CONFIGS))


def steer_kw(c):
    """rp.Steering keyword arguments for a config."""
    return {"cruise": c["cruise"], "kp": 1.0 / c["full_turn_deg"],
            "max_angular": c["max_angular"], "turn_in_place_deg": c["turn_in_place_deg"],
            "slow_radius_m": 8.0}


def straight_m(mission):
    pts = [(0.0, 0.0)] + list(mission)
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:]))


def fly(mission, seed, sim_kw, steering_kw, timeout_s):
    sim = rp.SimRover(MISSIONS[mission], seed=seed, **sim_kw)
    pilot = rp.Pilot(sim, clock=sim.clock, sleep=sim.sleep, steering=rp.Steering(**steering_kw))
    res = pilot.run(timeout_s=timeout_s)
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
    """Per-group rows, paired comparisons with the baseline, and a ranking of configs."""
    groups = {}
    for r in runs:
        groups.setdefault((r["config"], r["mission"], r["profile"]), []).append(r)
    rows = {}
    for key, rs in groups.items():
        ok = [r for r in rs if r["ok"]]
        rows[key] = {
            "config": key[0], "mission": key[1], "profile": key[2], "runs": len(rs),
            "completed": len(ok),
            "median_time_s": _median([r["elapsed_s"] for r in ok]),
            "mean_time_s": _mean([r["elapsed_s"] for r in ok], 1),
            "mean_refused_reports": _mean([r["reports"] - r["reached"] for r in rs]),
            "mean_recoveries": _mean([r["recoveries"] for r in rs]),
            "mean_path_ratio": _mean([r["travelled_m"] / straight_m(MISSIONS[r["mission"]])
                                      for r in ok], 3),
        }
    configs = []
    for r in runs:
        if r["config"] not in configs:
            configs.append(r["config"])
    paired, ranking = [], []
    for config in configs:
        mine = [k for k in rows if k[0] == config]
        sig_faster = sig_slower = lost = 0
        ratios = []
        for _, mission, profile in sorted(mine):
            base_row = rows.get((BASELINE, mission, profile))
            if base_row is None:
                continue
            row = rows[(config, mission, profile)]
            if base_row["completed"] and row["completed"]:
                ratios.append(row["median_time_s"] / base_row["median_time_s"])
            if config == BASELINE:
                continue
            a = {r["seed"]: r for r in groups[(BASELINE, mission, profile)]}
            b = {r["seed"]: r for r in groups[(config, mission, profile)]}
            seeds = sorted(s for s in a if s in b)
            both = [s for s in seeds if a[s]["ok"] and b[s]["ok"]]
            diffs = [b[s]["elapsed_s"] - a[s]["elapsed_s"] for s in both]
            faster = sum(1 for d in diffs if d < 0)
            slower = sum(1 for d in diffs if d > 0)
            p = sign_test_p(faster, slower)
            only_base = sum(1 for s in seeds if a[s]["ok"] and not b[s]["ok"])
            only_config = sum(1 for s in seeds if b[s]["ok"] and not a[s]["ok"])
            if p is not None and p < 0.05:
                if faster > slower:
                    sig_faster += 1
                elif slower > faster:
                    sig_slower += 1
            if only_base > only_config:
                lost += 1
            paired.append({
                "config": config, "mission": mission, "profile": profile, "seeds": len(seeds),
                "both_completed": len(both), "only_baseline_completed": only_base,
                "only_config_completed": only_config, "faster": faster, "slower": slower,
                "median_time_diff_s": _median(diffs), "mean_time_diff_s": _mean(diffs, 1),
                "sign_test_p": None if p is None else round(p, 4),
            })
        rs = [r for k in mine for r in groups[k]]
        ranking.append({
            "config": config, "settings": CONFIGS[config], "groups": len(mine),
            "runs": len(rs), "completed": sum(1 for r in rs if r["ok"]),
            "time_ratio": round(statistics.fmean(ratios), 3) if ratios else None,
            "groups_faster": sig_faster, "groups_slower": sig_slower, "groups_lost": lost,
            "mean_refused_reports": _mean([r["reports"] - r["reached"] for r in rs]),
            "mean_recoveries": _mean([r["recoveries"] for r in rs]),
        })
    ranking.sort(key=lambda x: (-(x["completed"] / x["runs"]) if x["runs"] else 0.0,
                                x["time_ratio"] if x["time_ratio"] is not None else math.inf))
    return [rows[k] for k in sorted(rows)], paired, ranking


def pick(ranking, cruise=None):
    """The fastest config that never completes fewer missions than the baseline in a group,
    is never significantly slower, and is significantly faster in at least half the groups."""
    best = None
    for x in ranking:
        if x["config"] == BASELINE or x["time_ratio"] is None:
            continue
        if cruise is not None and x["settings"]["cruise"] != cruise:
            continue
        if x["groups_lost"] or x["groups_slower"] or 2 * x["groups_faster"] < x["groups"]:
            continue
        if best is None or x["time_ratio"] < best["time_ratio"]:
            best = x
    return best


def write_outputs(out_dir, runs, started, args, done):
    rows, paired, ranking = summarise(runs)
    best = pick(ranking)
    best_same_cruise = pick(ranking, cruise=CONFIGS[BASELINE]["cruise"])
    result = {"version": __version__, "rover_pilot": rp.__version__, "done": done,
              "elapsed_s": round(time.monotonic() - started, 1), "seeds": args.seeds,
              "timeout_s": args.timeout, "sim_real": rp.SIM_REAL, "baseline": BASELINE,
              "missions": {k: {"checkpoints": v, "straight_m": round(straight_m(v), 1)}
                           for k, v in MISSIONS.items()},
              "profiles": PROFILES, "runs": len(runs), "ranking": ranking,
              "best": best, "best_same_cruise": best_same_cruise,
              "groups": rows, "paired": paired}
    with open(os.path.join(out_dir, "summary.json"), "w") as f:
        json.dump(result, f, indent=1)
    with open(os.path.join(out_dir, "runs.jsonl"), "w") as f:
        for r in runs:
            f.write(json.dumps(r) + "\n")
    md = ["# Steering gains for a real-like Earth Rover in the earth-rover-pilot simulator", "",
          "gain_study.py %s, rover_pilot.py %s, MV2 of Munim, Inc. Simulated rovers only: "
          "SIM_REAL = %s from FrodoBots-2K, turning at 20, 30 or 45 deg/s per unit of angular. "
          "Seeds 1-%d, timeout %d s. Config names: c = cruise, a = largest angular, "
          "k = heading error (deg) for full angular, t = turn in place above this error (deg). "
          "Baseline (the current default): %s."
          % (__version__, rp.__version__, json.dumps(rp.SIM_REAL), args.seeds, args.timeout,
             BASELINE), "",
          "Time ratio: the config's median mission time over the baseline's, averaged over "
          "mission x profile groups. Faster / slower: groups where a paired sign test per seed "
          "gives p < 0.05. Lost: groups where the baseline completed more seeds.", "",
          "## Ranking", "",
          "| config | completed | time ratio | faster | slower | lost | refused/run | "
          "recoveries/run |", "|---|---|---|---|---|---|---|---|"]
    md += ["| %s | %d/%d | %s | %d/%d | %d | %d | %s | %s |"
           % (x["config"], x["completed"], x["runs"], x["time_ratio"], x["groups_faster"],
              x["groups"], x["groups_slower"], x["groups_lost"], x["mean_refused_reports"],
              x["mean_recoveries"]) for x in ranking]
    md += ["", "Best overall (never slower or losing a group, faster in at least half): %s"
           % (best["config"] if best else "none"),
           "Best at the baseline's cruise %g: %s"
           % (CONFIGS[BASELINE]["cruise"], best_same_cruise["config"] if best_same_cruise
              else "none"), ""]
    shown = [BASELINE] + [x["config"] for x in (best, best_same_cruise) if x]
    md += ["## Groups for the baseline and the picks", "",
           "| config | mission | profile | completed | median s | refused/run | "
           "recoveries/run | path ratio |", "|---|---|---|---|---|---|---|---|"]
    md += ["| %s | %s | %s | %d/%d | %s | %s | %s | %s |"
           % (r["config"], r["mission"], r["profile"], r["completed"], r["runs"],
              r["median_time_s"], r["mean_refused_reports"], r["mean_recoveries"],
              r["mean_path_ratio"])
           for c in dict.fromkeys(shown) for r in rows if r["config"] == c]
    with open(os.path.join(out_dir, "report.md"), "w") as f:
        f.write("\n".join(md) + "\n")
    return result


def _names(text, known, what):
    if not text:
        return list(known)
    names = [n.strip() for n in text.split(",") if n.strip()]
    for n in names:
        if n not in known:
            raise SystemExit("unknown %s: %s" % (what, n))
    return names


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out-dir", default="out")
    ap.add_argument("--seeds", type=int, default=30)
    ap.add_argument("--timeout", type=float, default=1500.0, help="simulated seconds per mission")
    ap.add_argument("--budget-min", type=float, default=100.0)
    ap.add_argument("--missions", help="comma-separated subset of: " + ",".join(MISSIONS))
    ap.add_argument("--profiles", help="comma-separated subset of: " + ",".join(PROFILES))
    ap.add_argument("--configs", help="comma-separated config names (the baseline is always flown)")
    args = ap.parse_args(argv)
    missions = _names(args.missions, MISSIONS, "mission")
    profiles = _names(args.profiles, PROFILES, "profile")
    configs = _names(args.configs, CONFIGS, "config")
    configs = [BASELINE] + [c for c in configs if c != BASELINE]
    os.makedirs(args.out_dir, exist_ok=True)
    started = time.monotonic()
    runs = []
    done = True
    for config in configs:
        if time.monotonic() - started > args.budget_min * 60.0:
            done = False
            break
        kw = steer_kw(CONFIGS[config])
        for mission in missions:
            for profile in profiles:
                for seed in range(1, args.seeds + 1):
                    try:
                        r = fly(mission, seed, PROFILES[profile], kw, args.timeout)
                    except Exception as exc:
                        r = {"ok": False, "reason": "%s: %s" % (type(exc).__name__, exc),
                             "elapsed_s": None, "reached": 0, "checkpoints": None,
                             "reports": 0, "recoveries": 0, "travelled_m": 0.0}
                    r.update(config=config, mission=mission, profile=profile, seed=seed)
                    runs.append(r)
        print("%s: %d runs so far, %.0f s" % (config, len(runs), time.monotonic() - started),
              flush=True)
        write_outputs(args.out_dir, runs, started, args, False)
    result = write_outputs(args.out_dir, runs, started, args, done)
    print(json.dumps({"best": result["best"], "best_same_cruise": result["best_same_cruise"]}),
          flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
