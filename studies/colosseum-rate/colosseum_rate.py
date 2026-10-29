"""colosseum_rate.py: does --max-angular 0.3 still suit RoboColosseum's 2-3 s
cadence on a rover that turns as slowly as a real one?

studies/colosseum-hold and studies/colosseum-hold-confirm flew earth-rover-pilot
behind a simulated RoboColosseum bridge that samples the pilot's command every
2-3 s, holds it, and refreshes /data only at the same observations ("stale").
There the unchanged pilot overshot and --max-angular 0.3 passed on two seed
sets, so the README recommends 0.3. But that simulator turns 60 deg/s at full
angular, so one 2.5 s hold at 0.3 turns it 45 deg. frodo-spin-v2 measured
recorded Earth Rovers turning in place at 23.4 deg/s per unit
(studies/frodo-spin/GRADE-v2.md), and the pilot assumes 48 for a Mini+. At
those rates 0.3 turns only 18-36 deg per observation, and a higher cap may no
longer overshoot.

This flies colosseum_hold.py's own bridge (HoldBridgeClient and fly(),
unchanged, fetched from main) with the simulator's max_yaw_dps set to each
rate, for the live arm, the unchanged pilot under stale telemetry, and stale
with --max-angular 0.3, 0.5 and 0.7. No pilot code changes. The predictions
and the decision rule were written down first, in
studies/colosseum-rate/PLAN.md.

    python colosseum_rate.py --out-dir out --seeds 24 --first-seed 49

By MV2 of Munim, Inc.; written with AI agents. Apache-2.0.
"""

from __future__ import annotations

import argparse
import collections
import json
import os
import statistics
import time
from unittest import mock

import colosseum_compat as cc
import colosseum_hold as ch
import rover_pilot as rp

# frodo-spin-v2's in-place fit on recorded Earth Rovers; the Mini+ rate the
# pilot's heading filter assumes (rover_pilot.SMOOTH_HEADING)
RATES_DPS = (23.4, 48.0)
DISTANCES_M = ch.DISTANCES_M
NOISES_M = cc.NOISES_M
ARMS = {
    "live": ch.ARMS["live"],
    "stale": ch.ARMS["stale"],
    "stale-m30": ch.ARMS["stale-m30"],
    "stale-m50": {"hold": True, "stale": True, "argv": ("--max-angular", "0.5")},
    "stale-m70": {"hold": True, "stale": True, "argv": ("--max-angular", "0.7")},
}
STALE_ARMS = ("stale", "stale-m30", "stale-m50", "stale-m70")
PASS_COMPLETED = ch.PASS_COMPLETED      # 23 of 24 flights per cell
PASS_TIME_RATIO = ch.PASS_TIME_RATIO    # median time against live's, per cell
KEEP_MARGIN = 0.10                      # how much better than 0.3 another cap must score


def make_sim_at(rate_dps):
    """colosseum_compat.make_sim, with the rover turning rate_dps at full angular."""
    make_sim = cc.make_sim

    def make(*args, **kwargs):
        sim, goal = make_sim(*args, **kwargs)
        sim.max_yaw_dps = float(rate_dps)
        return sim, goal
    return make


def fly(seed, distance_m, arm, noise_m, rate_dps):
    """colosseum_hold.fly() for one flight, on a rover turning at rate_dps."""
    with mock.patch.object(cc, "make_sim", make_sim_at(rate_dps)), \
            mock.patch.dict(ch.ARMS, ARMS):
        r = ch.fly(seed, distance_m, arm, noise_m)
    r["rate_dps"] = rate_dps
    return r


def _median(xs):
    xs = [x for x in xs if x is not None]
    return round(statistics.median(xs), 2) if xs else None


def decide(passes, scores, rates=RATES_DPS):
    """The rule in PLAN.md. passes[str(rate)][arm] is a bool, scores[arm] the
    mean over rates of the arm's summed median time over live's (or None)."""
    both = [a for a in STALE_ARMS
            if all(passes.get(str(r), {}).get(a) for r in rates) and scores.get(a) is not None]
    if not both:
        return {"rule": "R3", "arm": None}
    best = min(both, key=lambda a: scores[a])
    if "stale-m30" in both and scores["stale-m30"] - scores[best] < KEEP_MARGIN:
        return {"rule": "R1", "arm": "stale-m30"}
    return {"rule": "R2", "arm": best}


def summarise(runs, rates=RATES_DPS):
    cells = collections.defaultdict(list)
    for r in runs:
        cells[(r["rate_dps"], r["arm"], r["noise_m"], r["distance_m"])].append(r)
    table = {}
    for key, rs in cells.items():
        done = [r for r in rs if r["ok"]]
        table[key] = {
            "rate_dps": key[0], "arm": key[1], "noise_m": key[2], "distance_m": key[3],
            "n": len(rs),
            "completed": len(done),
            "accepted": sum(bool(r.get("accepted")) for r in rs),
            "timeouts": sum(r.get("reason") == "timeout" for r in rs),
            "crashed": sum(r["exit"] not in (0, 1) for r in rs),
            "median_elapsed_s": _median([r["elapsed_s"] for r in done]),
            "median_final_true_m": _median([r.get("final_true_m") for r in done]),
            "median_path_ratio": _median([r.get("path_ratio") for r in done]),
            "median_recoveries": _median([r.get("recoveries") for r in rs]),
            "median_flips": _median([r.get("flips") for r in rs]),
        }
    for key, c in table.items():
        live = table.get((key[0], "live") + key[2:])
        c["time_ratio"] = (round(c["median_elapsed_s"] / live["median_elapsed_s"], 3)
                           if live and c["median_elapsed_s"] and live["median_elapsed_s"]
                           else None)
    by_arm = collections.defaultdict(list)
    for c in table.values():
        by_arm[(c["rate_dps"], c["arm"])].append(c)
    passes = {}
    for (rate, arm), cs in by_arm.items():
        passes.setdefault(str(rate), {})[arm] = all(
            c["completed"] >= PASS_COMPLETED and c["time_ratio"] is not None
            and c["time_ratio"] <= PASS_TIME_RATIO for c in cs)
    scores = {}
    for arm in STALE_ARMS:
        per_rate = []
        for rate in rates:
            mine = by_arm.get((rate, arm), [])
            live = by_arm.get((rate, "live"), [])
            if (not mine or not live or any(c["median_elapsed_s"] is None for c in mine + live)):
                per_rate = None
                break
            per_rate.append(sum(c["median_elapsed_s"] for c in mine)
                            / sum(c["median_elapsed_s"] for c in live))
        scores[arm] = round(sum(per_rate) / len(per_rate), 4) if per_rate else None
    fastest = {}
    for rate in rates:
        ok = [a for a in STALE_ARMS if passes.get(str(rate), {}).get(a)]
        fastest[str(rate)] = (min(ok, key=lambda a: sum(c["median_elapsed_s"]
                                                         for c in by_arm[(rate, a)]))
                              if ok else None)
    order = list(ARMS)
    return {
        "cells": sorted(table.values(), key=lambda c: (c["rate_dps"], order.index(c["arm"]),
                                                        c["noise_m"], c["distance_m"])),
        "passes": passes, "scores": scores, "fastest_passing": fastest,
        "decision": decide(passes, scores, rates),
    }


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--out-dir", required=True)
    p.add_argument("--seeds", type=int, default=24)
    p.add_argument("--first-seed", type=int, default=49)
    args = p.parse_args(argv)
    os.makedirs(args.out_dir, exist_ok=True)
    started = time.time()
    runs = []
    with open(os.path.join(args.out_dir, "runs.jsonl"), "w", encoding="utf-8") as f:
        for rate in RATES_DPS:
            for noise in NOISES_M:
                for dist in DISTANCES_M:
                    for seed in range(args.first_seed, args.first_seed + args.seeds):
                        for arm in ARMS:
                            r = fly(seed, dist, arm, noise, rate)
                            runs.append(r)
                            f.write(json.dumps(r) + "\n")
                    print("rate %.1f noise %.2f distance %.0f done (%.0f s)"
                          % (rate, noise, dist, time.time() - started), flush=True)
    summary = summarise(runs)
    summary.update({"rover_pilot": rp.__version__, "trial_s": ch.TRIAL_S,
                    "hold_s": list(ch.HOLD_S), "rates_dps": list(RATES_DPS),
                    "seeds": [args.first_seed, args.first_seed + args.seeds - 1],
                    "flights": len(runs), "wall_s": round(time.time() - started, 1)})
    with open(os.path.join(args.out_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=1)
    print(json.dumps(summary, indent=1), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
