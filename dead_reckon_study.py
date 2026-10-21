#!/usr/bin/env python3
"""dead_reckon_study: should earth-rover-pilot dead-reckon between GPS fixes?

On FrodoBots-2K rides, wheel distance along the last GPS course predicted the
next fix better than anything else (frodo_odometry.py). dead_reckon.py puts
that in the pilot (--dead-reckon). This flies the same missions on the same
seeds with and without it, on simulated rovers that move like the recorded
ones (SIM_REAL turning at 30 deg/s per unit, ROVER_STEERING) and report wheel
RPMs, and measures what it changes:

- how far the pilot's position is from the truth, every tick (all ticks, and
  from 120 s into the mission, when the wheels have had time to be checked);
- mission time and completion, refused reports, recoveries, and how far from
  each checkpoint the rover truly was when the server credited it;
- what the dead reckoner learned (metres per RPM, against the simulated
  truth) and how long it drove on the wheels alone through GPS dropouts.

Profiles: "zero" (GPS every 1 s, wheels of an Earth Rover Zero), "real" (a
fresh fix every 1.54 s, as on the recorded rides) and "miniplus" (telemetry
every 2 s with the wheel rows in one batch, 1.11 m/s at full linear, 95 mm
wheels). GPS: white1.5 (independent 1.5 m per axis), gm3-t30 (Gauss-Markov,
3 m, 30 s) and white1.5-gaps (white1.5 with dropouts of 5-15 s about every
90 s, a stress test: far more than the twice an hour seen on the rides).

Variants: default (smoothed GPS, as shipped); lag1.5 (--gps-lag 1.5); dr
(dead reckoning, gain 1, the rover's true wheel size as the prior, learned);
dr-a0.3 (gain 0.3); dr-heading (the pilot's heading instead of the GPS
course); dr-miniprior (Mini+ wheel size as the prior on every rover, learned)
and dr-nolearn (Mini+ prior, not learned, used at once).

The predictions, written before the run (PREDICTION.md), are checked in
summary.json "predictions".

    python dead_reckon_study.py --out-dir out --seeds 20

Simulated rovers only. Standard library only. By MV2 of Munim, Inc.; written
with AI agents. Apache-2.0.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import statistics
import sys
import time

import dead_reckon as dm
import gain_study as gs
import rover_pilot as rp

__version__ = "0.1.0"

MISSIONS = dict(gs.MISSIONS)
# A longer square, so the wheels have been checked for most of the mission.
MISSIONS["square"] = [(120.0, 0.0), (120.0, 120.0), (0.0, 120.0), (0.0, 0.0)]

PROFILES = {
    "zero": dict(rp.SIM_REAL, max_yaw_dps=30.0, wheel_mps_per_rpm=dm.ZERO_MPS_PER_RPM),
    "real": dict(rp.SIM_REAL, max_yaw_dps=30.0, gps_period_s=1.54,
                 wheel_mps_per_rpm=dm.ZERO_MPS_PER_RPM),
    "miniplus": dict(rp.SIM_REAL, max_yaw_dps=30.0, gps_period_s=2.0, max_speed_mps=1.11,
                     wheel_mps_per_rpm=dm.MINI_PLUS_MPS_PER_RPM, rpm_period_s=2.0),
}
# name: (sigma per axis m, correlation time s (0 = independent), dropouts)
NOISE = {
    "white1.5": (1.5, 0.0, False),
    "gm3-t30": (3.0, 30.0, False),
    "white1.5-gaps": (1.5, 0.0, True),
}
GAP_EVERY_S = 90.0
GAP_S = (5.0, 15.0)
# name: Pilot settings; "dr" holds DeadReckoner settings ("prior": "true" = the
# rover's own wheel size, "mini" = the Mini+'s).
VARIANTS = {
    "default": {},
    "lag1.5": {"gps_lag_s": 1.5},
    "dr": {"dr": {"prior": "true"}},
    "dr-a0.3": {"dr": {"prior": "true", "gain": 0.3}},
    "dr-heading": {"dr": {"prior": "true", "use_course": False}},
    "dr-miniprior": {"dr": {"prior": "mini"}},
    "dr-nolearn": {"dr": {"prior": "mini", "learn_scale": False}},
}
BASE_VARIANT = "default"
LATE_S = 120.0
TOLERANCE_M = 15.0


class StudyRover(rp.SimRover):
    """SimRover with Gauss-Markov GPS error (tau > 0), GPS dropouts drawn from their
    own seeded generator (the same for every variant), and a record of how far the
    rover truly was from each checkpoint the server credited."""

    def __init__(self, checkpoints_m, tau_s=0.0, gaps=False, **kw):
        self.tau_s = float(tau_s)
        self._err = None
        self._cps = list(checkpoints_m)
        self.credited_true_m = []
        self.outages = []
        if gaps:
            g = random.Random(kw.get("seed", 0) * 7919 + 17)
            t = g.expovariate(1.0 / GAP_EVERY_S)
            while t < 7200.0:
                d = g.uniform(*GAP_S)
                self.outages.append((t, t + d))
                t += d + g.expovariate(1.0 / GAP_EVERY_S)
        super().__init__(checkpoints_m, **kw)

    def _sample_gps(self):
        if self.tau_s <= 0:
            super()._sample_gps()
        else:
            north, east = self._delayed_position()
            sigma = self.gps_noise_m
            if self._err is None:
                self._err = (self.rng.gauss(0, sigma), self.rng.gauss(0, sigma))
            else:
                phi = math.exp(-self.gps_period_s / self.tau_s)
                s = sigma * math.sqrt(max(0.0, 1.0 - phi * phi))
                self._err = tuple(phi * e + self.rng.gauss(0, s) for e in self._err)
            if self.rng.random() < self.gps_dropout:
                self.gps = (rp.NO_FIX, rp.NO_FIX)
            else:
                self.gps = rp.offset_latlon(self.lat0, self.lon0,
                                            north + self._err[0], east + self._err[1])
            self._next_gps_t = self.t + self.gps_period_s
        if any(a <= self.t < b for a, b in self.outages):
            self.gps = (rp.NO_FIX, rp.NO_FIX)

    def checkpoint_reached(self):
        i = self.next_cp
        res = super().checkpoint_reached()
        if res.get("ok"):
            n, e = self._cps[i]
            self.credited_true_m.append(math.hypot(self.north - n, self.east - e))
        return res


class MeasuredPilot(rp.Pilot):
    """Pilot that records how far its position is from the simulated truth."""

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.errs = []

    def _position(self, t):
        pos = super()._position(t)
        if pos[0] is not None:
            e, n = rp.to_enu(self.rover.lat0, self.rover.lon0, pos[0], pos[1])
            self.errs.append((t, math.hypot(e - self.rover.east, n - self.rover.north)))
        return pos


def make_reckoner(settings, true_mps_per_rpm):
    kw = dict(settings)
    prior = kw.pop("prior", "true")
    kw["mps_per_rpm"] = true_mps_per_rpm if prior == "true" else dm.MINI_PLUS_MPS_PER_RPM
    return dm.DeadReckoner(**kw)


def pct(values, q):
    """Nearest-rank percentile, or None for no values."""
    if not values:
        return None
    s = sorted(values)
    return s[max(0, min(len(s) - 1, int(math.ceil(q / 100.0 * len(s))) - 1))]


def fly(mission, seed, noise, variant, timeout_s, profile):
    sigma, tau, gaps = NOISE[noise]
    p = PROFILES[profile]
    sim = StudyRover(MISSIONS[mission], seed=seed, gps_noise_m=sigma, tau_s=tau, gaps=gaps, **p)
    v = VARIANTS[variant]
    dr = make_reckoner(v["dr"], p["wheel_mps_per_rpm"]) if "dr" in v else None
    pilot = MeasuredPilot(sim, clock=sim.clock, sleep=sim.sleep,
                          steering=rp.make_steering(simulate=False),
                          gps_lag_s=v.get("gps_lag_s", 0.0), dead_reckon=dr)
    res = pilot.run(timeout_s=timeout_s)
    errs = [e for _, e in pilot.errs]
    late = [e for t, e in pilot.errs if t >= LATE_S]
    out = {"ok": res["ok"], "reason": res["reason"], "elapsed_s": res["elapsed_s"],
           "reached": len(res["reached"]), "checkpoints": res["checkpoints"],
           "reports": res["reports"], "recoveries": res["recoveries"],
           "travelled_m": round(sim.travelled, 1),
           "pos_err_median": round(statistics.median(errs), 3) if errs else None,
           "pos_err_p90": round(pct(errs, 90), 3) if errs else None,
           "pos_err_late_median": round(statistics.median(late), 3) if late else None,
           "credited_true_m": [round(d, 2) for d in sim.credited_true_m],
           "outage_s": round(sum(min(b, sim.t) - a for a, b in sim.outages if a < sim.t), 1)}
    if dr is not None:
        st = res.get("dead_reckon", {})
        out.update(dr_trusted=st.get("trusted"), dr_scale_ratio=round(
            dr.mps_per_rpm / p["wheel_mps_per_rpm"], 4), dr_scale_samples=st.get("scale_samples"),
            dr_scale_rejects=st.get("scale_rejects"), dr_resets=st.get("resets"),
            bridged_s=st.get("bridged_s"))
    return out


def _median(values, digits=2):
    values = [v for v in values if v is not None]
    return round(statistics.median(values), digits) if values else None


def _mean(values, digits=2):
    values = [v for v in values if v is not None]
    return round(statistics.fmean(values), digits) if values else None


def compare(a_runs, b_runs):
    """b against a, paired by seed: who completed, and a sign test of mission time."""
    a = {r["seed"]: r for r in a_runs}
    b = {r["seed"]: r for r in b_runs}
    seeds = sorted(s for s in a if s in b)
    both = [s for s in seeds if a[s]["ok"] and b[s]["ok"]]
    diffs = [b[s]["elapsed_s"] - a[s]["elapsed_s"] for s in both]
    faster = sum(1 for d in diffs if d < 0)
    slower = sum(1 for d in diffs if d > 0)
    p = gs.sign_test_p(faster, slower)
    return {"seeds": len(seeds), "both_completed": len(both),
            "only_a_completed": sum(1 for s in seeds if a[s]["ok"] and not b[s]["ok"]),
            "only_b_completed": sum(1 for s in seeds if b[s]["ok"] and not a[s]["ok"]),
            "faster": faster, "slower": slower, "median_time_diff_s": _median(diffs, 1),
            "sign_test_p": None if p is None else round(p, 4)}


def _row(rs):
    ok = [r for r in rs if r["ok"]]
    credits = [d for r in rs for d in r["credited_true_m"]]
    row = {"runs": len(rs), "completed": len(ok),
           "median_time_s": _median([r["elapsed_s"] for r in ok], 1),
           "pos_err_median": _median([r["pos_err_median"] for r in rs]),
           "pos_err_late_median": _median([r["pos_err_late_median"] for r in rs]),
           "pos_err_p90_median": _median([r["pos_err_p90"] for r in rs]),
           "mean_refused_reports": _mean([r["reports"] - r["reached"] for r in rs]),
           "mean_recoveries": _mean([r["recoveries"] for r in rs]),
           "median_credit_true_m": _median(credits), "p90_credit_true_m": pct(credits, 90),
           "credits_beyond_tolerance": sum(1 for d in credits if d > TOLERANCE_M)}
    if "dr_trusted" in rs[0]:
        ratios = [r["dr_scale_ratio"] for r in rs if r.get("dr_scale_samples")]
        row.update(trusted_share=round(sum(1 for r in rs if r["dr_trusted"]) / len(rs), 3),
                   scale_ratio_median=_median(ratios, 4),
                   scale_within_10pct_share=(round(sum(1 for x in ratios if abs(x - 1) <= 0.1)
                                                   / len(ratios), 3) if ratios else None),
                   mean_bridged_s=_mean([r["bridged_s"] for r in rs], 1),
                   mean_resets=_mean([r["dr_resets"] for r in rs]))
    return row


def verdict(groups, profile, noise, variant):
    """The variant against the default over the missions of one profile and noise."""
    faster = slower = lost = gained = n = 0
    per_mission = []
    for (p, nz, v, m), rs in sorted(groups.items()):
        if (p, nz, v) != (profile, noise, variant) or (p, nz, BASE_VARIANT, m) not in groups:
            continue
        c = compare(groups[(p, nz, BASE_VARIANT, m)], rs)
        per_mission.append(dict(mission=m, **c))
        n += 1
        if c["sign_test_p"] is not None and c["sign_test_p"] < 0.05:
            faster += c["faster"] > c["slower"]
            slower += c["slower"] > c["faster"]
        lost += c["only_a_completed"] > c["only_b_completed"]
        gained += c["only_b_completed"] > c["only_a_completed"]
    return {"profile": profile, "noise": noise, "variant": variant, "missions": n,
            "missions_faster": faster, "missions_slower": slower, "missions_lost": lost,
            "missions_gained": gained, "worse": bool(lost or slower),
            "better": not lost and not slower and n > 0 and 2 * (faster + gained) >= n,
            "per_mission": per_mission}


def check_predictions(overview, verdicts):
    """PREDICTION.md, checked. Each is True, False, or None when its runs are missing."""
    ov = {(o["profile"], o["noise"], o["variant"]): o for o in overview}
    vd = {(v["profile"], v["noise"], v["variant"]): v for v in verdicts}
    out = {}

    def ratio(profile, noise, variant):
        a, b = ov.get((profile, noise, BASE_VARIANT)), ov.get((profile, noise, variant))
        if not a or not b or not a["pos_err_late_median"] or b["pos_err_late_median"] is None:
            return None
        return b["pos_err_late_median"] / a["pos_err_late_median"]

    # P1: on white1.5, from 120 s on, some dead-reckoning variant's median position
    # error is at most 0.75 of the default's in every profile.
    best = {}
    for p in PROFILES:
        rs = [(ratio(p, "white1.5", v), v) for v in ("dr", "dr-a0.3", "dr-heading")]
        rs = [x for x in rs if x[0] is not None]
        best[p] = min(rs) if rs else None
    out["P1_position_white"] = {
        "best_ratio_per_profile": {p: (None if b is None else [round(b[0], 3), b[1]])
                                   for p, b in best.items()},
        "met": None if any(b is None for b in best.values())
        else all(b[0] <= 0.75 for b in best.values())}
    # P2: with GPS dropouts, dr completes at least as many runs as the default in
    # every profile and mission, and is faster in at least half of them.
    g = [vd.get((p, "white1.5-gaps", "dr")) for p in PROFILES]
    if any(x is None for x in g):
        out["P2_gaps"] = {"met": None}
    else:
        groups = [m for x in g for m in x["per_mission"]]
        fast = sum(1 for m in groups if m["sign_test_p"] is not None
                   and m["sign_test_p"] < 0.05 and m["faster"] > m["slower"])
        lost = sum(1 for m in groups if m["only_a_completed"] > m["only_b_completed"])
        out["P2_gaps"] = {"groups": len(groups), "faster": fast, "lost": lost,
                          "met": lost == 0 and 2 * fast >= len(groups)}
    # P3: with a Mini+ prior on Zero wheels (34% off), the learned size is within
    # 10% of the truth in the median, and trusted in at least 80% of runs (white1.5).
    rows = [ov.get((p, "white1.5", "dr-miniprior")) for p in ("zero", "real")]
    if any(r is None for r in rows):
        out["P3_scale"] = {"met": None}
    else:
        out["P3_scale"] = {
            "rows": {p: {k: r[k] for k in ("scale_ratio_median", "trusted_share",
                                           "scale_within_10pct_share")}
                     for p, r in zip(("zero", "real"), rows)},
            "met": all(r["scale_ratio_median"] is not None
                       and abs(r["scale_ratio_median"] - 1) <= 0.1
                       and r["trusted_share"] >= 0.8 for r in rows)}
    # P4: without dropouts, dr is not worse than the default (no lost or slower
    # missions) in any profile, on white1.5 and gm3-t30. No gain in time is predicted.
    v4 = [vd.get((p, n, "dr")) for p in PROFILES for n in ("white1.5", "gm3-t30")]
    out["P4_no_harm"] = {"met": None if any(x is None for x in v4)
                         else not any(x["worse"] for x in v4),
                         "worse_in": [[x["profile"], x["noise"]] for x in v4
                                      if x is not None and x["worse"]]}
    return out


def summarise(runs):
    groups, pooled = {}, {}
    for r in runs:
        groups.setdefault((r["profile"], r["noise"], r["variant"], r["mission"]), []).append(r)
        pooled.setdefault((r["profile"], r["noise"], r["variant"]), []).append(r)
    overview = []
    for key, rs in pooled.items():
        row = dict(profile=key[0], noise=key[1], variant=key[2], **_row(rs))
        ratios = []
        for (p, n, v, m), grs in groups.items():
            base = groups.get((p, n, BASE_VARIANT, m))
            if (p, n, v) != key or base is None:
                continue
            a, b = _row(base)["median_time_s"], _row(grs)["median_time_s"]
            if a and b:
                ratios.append(b / a)
        row["time_ratio_to_default"] = round(statistics.fmean(ratios), 3) if ratios else None
        overview.append(row)
    verdicts = [verdict(groups, p, n, v) for (p, n, v) in pooled if v != BASE_VARIANT]
    return overview, verdicts, check_predictions(overview, verdicts)


def write_outputs(out_dir, runs, started, args, done):
    overview, verdicts, predictions = summarise(runs)
    result = {"version": __version__, "rover_pilot": rp.__version__,
              "dead_reckon": dm.__version__, "done": done,
              "elapsed_s": round(time.monotonic() - started, 1), "seeds": args.seeds,
              "timeout_s": args.timeout, "profiles": PROFILES, "noise": NOISE,
              "gaps": {"every_s": GAP_EVERY_S, "length_s": GAP_S}, "variants": VARIANTS,
              "steering": rp.ROVER_STEERING, "late_s": LATE_S,
              "missions": {k: {"checkpoints": v, "straight_m": round(gs.straight_m(v), 1)}
                           for k, v in MISSIONS.items()},
              "runs": len(runs), "predictions": predictions, "overview": overview,
              "verdicts": verdicts}
    with open(os.path.join(out_dir, "summary.json"), "w") as f:
        json.dump(result, f, indent=1)
    with open(os.path.join(out_dir, "runs.jsonl"), "w") as f:
        for r in runs:
            f.write(json.dumps(r) + "\n")
    md = ["# Dead reckoning in earth-rover-pilot (simulated)", "",
          "dead_reckon_study.py %s, rover_pilot.py %s, dead_reckon.py %s, MV2 of Munim, Inc. "
          "Simulated rovers only. Seeds 1-%d, timeout %d s. Position error: distance from the "
          "pilot's position to the simulated truth, each tick; 'late' from %d s on."
          % (__version__, rp.__version__, dm.__version__, args.seeds, args.timeout, LATE_S),
          "", "## Predictions (PREDICTION.md)", "", "```", json.dumps(predictions, indent=1),
          "```", "", "## Overview (missions pooled)", "",
          "| profile | GPS | variant | completed | time ratio | pos err median / late / p90 (m) "
          "| refused/run | recoveries/run | credit dist median / p90 (m) | trusted | scale ratio "
          "| bridged s/run |", "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for o in overview:
        md.append("| %s | %s | %s | %d/%d | %s | %s / %s / %s | %s | %s | %s / %s | %s | %s | %s |"
                  % (o["profile"], o["noise"], o["variant"], o["completed"], o["runs"],
                     o["time_ratio_to_default"], o["pos_err_median"], o["pos_err_late_median"],
                     o["pos_err_p90_median"], o["mean_refused_reports"], o["mean_recoveries"],
                     o["median_credit_true_m"], o["p90_credit_true_m"],
                     o.get("trusted_share", "-"), o.get("scale_ratio_median", "-"),
                     o.get("mean_bridged_s", "-")))
    md += ["", "## Variants against the default (paired sign test per mission, p < 0.05)", "",
           "| profile | GPS | variant | faster | slower | lost | gained | verdict |",
           "|---|---|---|---|---|---|---|---|"]
    for v in verdicts:
        md.append("| %s | %s | %s | %d/%d | %d | %d | %d | %s |"
                  % (v["profile"], v["noise"], v["variant"], v["missions_faster"],
                     v["missions"], v["missions_slower"], v["missions_lost"],
                     v["missions_gained"],
                     "better" if v["better"] else "worse" if v["worse"] else "no clear difference"))
    with open(os.path.join(out_dir, "report.md"), "w") as f:
        f.write("\n".join(md) + "\n")
    return result


def _names(text, known, what):
    if not text:
        return list(known)
    names = [x.strip() for x in text.split(",") if x.strip()]
    for x in names:
        if x not in known:
            raise SystemExit("unknown %s %r" % (what, x))
    return names


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out-dir", default="out")
    ap.add_argument("--seeds", type=int, default=20)
    ap.add_argument("--timeout", type=float, default=2400.0, help="simulated seconds per mission")
    ap.add_argument("--budget-min", type=float, default=100.0)
    ap.add_argument("--missions")
    ap.add_argument("--noise")
    ap.add_argument("--variants")
    ap.add_argument("--profiles")
    args = ap.parse_args(argv)
    missions = _names(args.missions, MISSIONS, "mission")
    noises = _names(args.noise, NOISE, "noise")
    variants = _names(args.variants, VARIANTS, "variant")
    profiles = _names(args.profiles, PROFILES, "profile")
    variants = [BASE_VARIANT] + [v for v in variants if v != BASE_VARIANT]
    os.makedirs(args.out_dir, exist_ok=True)
    started = time.monotonic()
    runs, done = [], True
    for noise in noises:
        for profile in profiles:
            if time.monotonic() - started > args.budget_min * 60.0:
                done = False
                break
            for variant in variants:
                for mission in missions:
                    for seed in range(1, args.seeds + 1):
                        try:
                            r = fly(mission, seed, noise, variant, args.timeout, profile)
                        except Exception as exc:
                            r = {"ok": False, "reason": "%s: %s" % (type(exc).__name__, exc),
                                 "elapsed_s": None, "reached": 0, "checkpoints": None,
                                 "reports": 0, "recoveries": 0, "travelled_m": 0.0,
                                 "pos_err_median": None, "pos_err_p90": None,
                                 "pos_err_late_median": None, "credited_true_m": [],
                                 "outage_s": None}
                            if "dr" in VARIANTS[variant]:
                                r.update(dr_trusted=False, dr_scale_ratio=None,
                                         dr_scale_samples=0, dr_scale_rejects=0,
                                         dr_resets=0, bridged_s=0.0)
                        r.update(profile=profile, noise=noise, variant=variant,
                                 mission=mission, seed=seed)
                        runs.append(r)
            print("%s %s: %d runs, %.0f s" % (noise, profile, len(runs),
                                              time.monotonic() - started), flush=True)
            write_outputs(args.out_dir, runs, started, args, False)
        if not done:
            break
    result = write_outputs(args.out_dir, runs, started, args, done)
    print(json.dumps({"predictions": result["predictions"]}, indent=1), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
