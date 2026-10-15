#!/usr/bin/env python3
"""gps_noise_study: does the pilot hold up when GPS error drifts instead of jittering?

The simulator gives every GPS fix its own independent 1.5 m error. A real
receiver's error is correlated in time: it wanders off by a few metres and
stays there for tens of seconds (a Gauss-Markov process is the usual model).
That can hurt the pilot in ways white noise never does:

- the compass bias is learned by fitting a line through the fixes of a
  straight stretch, and a slowly drifting error bends that line;
- smoothing (GpsFilter alpha 0.3) removes jitter but not a drift, so it may
  only add lag;
- checkpoints are judged on the reported GPS, so a rover can be refused at
  the right spot or credited at the wrong one;
- a fix that hardly moves looks like a stuck rover.

This flies the same missions on a rover that moves like the FrodoBots-2K
ones (SIM_REAL, turning 30 deg/s per unit, steered with ROVER_STEERING) under
a grid of GPS error models (sigma per axis, correlation time T; T = 0 is the
simulator's white noise) and a few pilot variants (smoothing, report radius,
and since 0.2.0 the compass-bias fit: a residual gate, longer stretches and
weighting by fit quality, which rover_pilot 0.9.2 added as options).
FrodoBots-2K was recorded on Earth Rover Zeros, but the challenge now drives
the Earth Rover Mini+, whose telemetry the SDK README says comes every 2 s
(top speed 4 km/h), so two more profiles get a GPS fix every 2 s, one of
them also at 1.11 m/s per unit of linear.
Per run it records completion, time, refused reports, recoveries, the error
of the learned compass bias, how many bias fits were rejected, and how far
the rover truly was from each checkpoint when the server credited it. It
writes summary.json, runs.jsonl and report.md.

    python gps_noise_study.py --out-dir out --seeds 30

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

import gain_study as gs
import rover_pilot as rp

__version__ = "0.2.0"

# name: (sigma per axis in m, correlation time T in s; 0 = independent fixes).
# The first is the simulator's current GPS and the baseline.
NOISE = {
    "white1.5": (1.5, 0.0),
    "white3": (3.0, 0.0),
    "gm1.5-t30": (1.5, 30.0),
    "gm3-t10": (3.0, 10.0),
    "gm3-t30": (3.0, 30.0),
    "gm3-t120": (3.0, 120.0),
    "gm6-t30": (6.0, 30.0),
}
BASE_NOISE = next(iter(NOISE))
# Pilot variants; the first is the pilot as it ships. "heading" settings are
# set on the pilot's HeadingEstimator (rover_pilot 0.9.2 or later).
VARIANTS = {
    "default": {"alpha": 0.3, "report_radius_m": 10.0},
    "alpha1": {"alpha": 1.0, "report_radius_m": 10.0},
    "alpha0.15": {"alpha": 0.15, "report_radius_m": 10.0},
    "radius7": {"alpha": 0.3, "report_radius_m": 7.0},
    "radius12": {"alpha": 0.3, "report_radius_m": 12.0},
    "residual2": {"alpha": 0.3, "report_radius_m": 10.0, "heading": {"max_residual_m": 2.0}},
    "residual3": {"alpha": 0.3, "report_radius_m": 10.0, "heading": {"max_residual_m": 3.0}},
    "move20": {"alpha": 0.3, "report_radius_m": 10.0, "heading": {"min_move_m": 20.0}},
    "move30": {"alpha": 0.3, "report_radius_m": 10.0, "heading": {"min_move_m": 30.0}},
    "weigh": {"alpha": 0.3, "report_radius_m": 10.0, "heading": {"weigh": True}},
    "weigh-move20": {"alpha": 0.3, "report_radius_m": 10.0,
                     "heading": {"weigh": True, "min_move_m": 20.0}},
    "weigh-residual3": {"alpha": 0.3, "report_radius_m": 10.0,
                        "heading": {"weigh": True, "max_residual_m": 3.0}},
}
BASE_VARIANT = next(iter(VARIANTS))
# Rovers; the first moves like the FrodoBots-2K ones and is the baseline.
PROFILES = {
    "zero": dict(rp.SIM_REAL, max_yaw_dps=30.0),
    "gps2s": dict(rp.SIM_REAL, max_yaw_dps=30.0, gps_period_s=2.0),
    "miniplus": dict(rp.SIM_REAL, max_yaw_dps=30.0, gps_period_s=2.0, max_speed_mps=1.11),
}
BASE_PROFILE = next(iter(PROFILES))
TOLERANCE_M = 15.0


def gauss_markov_step(rng, err, sigma, phi):
    """The next value of a per-axis Gauss-Markov error: phi * err plus fresh noise
    sized so the error stays at sigma per axis (phi = exp(-dt / T))."""
    s = sigma * math.sqrt(max(0.0, 1.0 - phi * phi))
    return tuple(phi * e + rng.gauss(0, s) for e in err)


class CorrelatedGpsRover(rp.SimRover):
    """SimRover whose GPS error is a Gauss-Markov process with correlation time
    `gps_noise_tau_s` (sigma per axis = gps_noise_m). With tau 0 it is SimRover
    exactly. It also records how far the rover truly was from each checkpoint
    the server credited (credited_true_m)."""

    def __init__(self, checkpoints_m, gps_noise_tau_s=0.0, **kw):
        self.gps_noise_tau_s = float(gps_noise_tau_s)
        self._err = None
        self._checkpoints_m = list(checkpoints_m)
        self.credited_true_m = []
        super().__init__(checkpoints_m, **kw)

    def _sample_gps(self):
        if self.gps_noise_tau_s <= 0:
            super()._sample_gps()
            return
        north, east = self._delayed_position()
        sigma = self.gps_noise_m
        if self._err is None:
            self._err = (self.rng.gauss(0, sigma), self.rng.gauss(0, sigma))
        else:
            phi = math.exp(-self.gps_period_s / self.gps_noise_tau_s)
            self._err = gauss_markov_step(self.rng, self._err, sigma, phi)
        # The error keeps evolving through a dropout, as a receiver's would.
        if self.rng.random() < self.gps_dropout:
            self.gps = (rp.NO_FIX, rp.NO_FIX)
        else:
            self.gps = rp.offset_latlon(self.lat0, self.lon0,
                                        north + self._err[0], east + self._err[1])
        self._next_gps_t = self.t + self.gps_period_s

    def checkpoint_reached(self):
        i = self.next_cp
        res = super().checkpoint_reached()
        if res.get("ok"):
            n, e = self._checkpoints_m[i]
            self.credited_true_m.append(math.hypot(self.north - n, self.east - e))
        return res


def apply_heading(pilot, settings):
    """Set a variant's "heading" settings on the pilot's HeadingEstimator; a
    setting the installed rover_pilot doesn't know is an error, not a silent no-op."""
    for key, value in settings.items():
        if not hasattr(pilot.heading, key):
            raise AttributeError("rover_pilot %s has no HeadingEstimator.%s"
                                 % (rp.__version__, key))
        setattr(pilot.heading, key, value)


def fly(mission, seed, noise, variant, timeout_s, profile=BASE_PROFILE):
    sigma, tau = NOISE[noise]
    v = VARIANTS[variant]
    sim = CorrelatedGpsRover(gs.MISSIONS[mission], seed=seed, gps_noise_m=sigma,
                             gps_noise_tau_s=tau, **PROFILES[profile])
    pilot = rp.Pilot(sim, clock=sim.clock, sleep=sim.sleep,
                     steering=rp.make_steering(simulate=False),
                     report_radius_m=v["report_radius_m"])
    pilot.gps.alpha = v["alpha"]
    apply_heading(pilot, v.get("heading", {}))
    res = pilot.run(timeout_s=timeout_s)
    # The compass reads heading + compass_error, so the right bias is -compass_error.
    bias_err = abs(rp.wrap180(res["compass_bias_deg"] + sim.compass_error))
    return {"ok": res["ok"], "reason": res["reason"], "elapsed_s": res["elapsed_s"],
            "reached": len(res["reached"]), "checkpoints": res["checkpoints"],
            "reports": res["reports"], "recoveries": res["recoveries"],
            "travelled_m": round(sim.travelled, 1),
            "calibrations": res["calibrations"],
            "rejected_fits": getattr(pilot.heading, "rejected_fits", 0),
            "bias_err_deg": round(bias_err, 1) if res["calibrations"] else None,
            "credited_true_m": [round(d, 2) for d in sim.credited_true_m]}


def pct(values, q):
    """Nearest-rank percentile, or None for no values."""
    if not values:
        return None
    s = sorted(values)
    k = max(0, min(len(s) - 1, int(math.ceil(q / 100.0 * len(s))) - 1))
    return s[k]


def _mean(values, digits=2):
    return round(statistics.fmean(values), digits) if values else None


def _median(values, digits=1):
    return round(statistics.median(values), digits) if values else None


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
            "faster": faster, "slower": slower, "median_time_diff_s": _median(diffs),
            "sign_test_p": None if p is None else round(p, 4)}


def _row(rs):
    ok = [r for r in rs if r["ok"]]
    credits = [d for r in rs for d in r["credited_true_m"]]
    biases = [r["bias_err_deg"] for r in rs if r["bias_err_deg"] is not None]
    return {"runs": len(rs), "completed": len(ok),
            "median_time_s": _median([r["elapsed_s"] for r in ok]),
            "mean_refused_reports": _mean([r["reports"] - r["reached"] for r in rs]),
            "mean_recoveries": _mean([r["recoveries"] for r in rs]),
            "mean_calibrations": _mean([r["calibrations"] for r in rs]),
            "mean_rejected_fits": _mean([r.get("rejected_fits", 0) for r in rs]),
            "median_bias_err_deg": _median(biases), "p90_bias_err_deg": pct(biases, 90),
            "credits": len(credits), "median_credit_true_m": _median(credits, 2),
            "p90_credit_true_m": pct(credits, 90),
            "max_credit_true_m": max(credits) if credits else None,
            "credits_beyond_tolerance": sum(1 for d in credits if d > TOLERANCE_M)}


def summarise(runs):
    """Rows per (profile, noise, variant, mission) and pooled over missions; within each
    profile, the effect of each noise model on the shipped pilot and each variant against
    the shipped pilot; and each profile's shipped pilot on white noise against the first's."""
    groups, pooled = {}, {}
    for r in runs:
        groups.setdefault((r["profile"], r["noise"], r["variant"], r["mission"]), []).append(r)
        pooled.setdefault((r["profile"], r["noise"], r["variant"]), []).append(r)
    rows = [dict(profile=k[0], noise=k[1], variant=k[2], mission=k[3], **_row(groups[k]))
            for k in sorted(groups)]
    overview = []
    for key in pooled:
        row = dict(profile=key[0], noise=key[1], variant=key[2], **_row(pooled[key]))
        ratios = []
        for (p, n, v, m), rs in groups.items():
            base = groups.get((p, BASE_NOISE, BASE_VARIANT, m))
            if (p, n, v) != key or base is None:
                continue
            a, b = _row(base)["median_time_s"], _row(rs)["median_time_s"]
            if a and b:
                ratios.append(b / a)
        row["time_ratio_to_baseline"] = round(statistics.fmean(ratios), 3) if ratios else None
        overview.append(row)
    noise_effect, variant_effect, verdicts, profile_effect = [], [], [], []
    for (p, n, v, m) in sorted(groups):
        if v != BASE_VARIANT or n != BASE_NOISE or p == BASE_PROFILE:
            continue
        base = groups.get((BASE_PROFILE, BASE_NOISE, BASE_VARIANT, m))
        if base is not None:
            profile_effect.append(dict(profile=p, mission=m,
                                       **compare(base, groups[(p, n, v, m)])))
    for (p, n, v, m) in sorted(groups):
        if v != BASE_VARIANT or n == BASE_NOISE:
            continue
        base = groups.get((p, BASE_NOISE, BASE_VARIANT, m))
        if base is not None:
            noise_effect.append(dict(profile=p, noise=n, mission=m,
                                     **compare(base, groups[(p, n, v, m)])))
    for (profile, noise) in dict.fromkeys(k[:2] for k in groups):
        for variant in dict.fromkeys(k[2] for k in groups if k[:2] == (profile, noise)):
            if variant == BASE_VARIANT:
                continue
            faster = slower = lost = gained = n_groups = 0
            for (p, n, v, m) in sorted(groups):
                if (p, n, v) != (profile, noise, variant):
                    continue
                if (p, n, BASE_VARIANT, m) not in groups:
                    continue
                c = compare(groups[(p, n, BASE_VARIANT, m)], groups[(p, n, v, m)])
                variant_effect.append(dict(profile=p, noise=n, variant=v, mission=m, **c))
                n_groups += 1
                if c["sign_test_p"] is not None and c["sign_test_p"] < 0.05:
                    faster += c["faster"] > c["slower"]
                    slower += c["slower"] > c["faster"]
                lost += c["only_a_completed"] > c["only_b_completed"]
                gained += c["only_b_completed"] > c["only_a_completed"]
            if n_groups:
                verdicts.append({
                    "profile": profile, "noise": noise, "variant": variant,
                    "missions": n_groups, "missions_faster": faster,
                    "missions_slower": slower, "missions_lost": lost,
                    "missions_gained": gained,
                    "better": not lost and not slower and (faster > 0 or gained > 0)
                              and 2 * (faster + gained) >= n_groups,
                    "worse": bool(lost or slower)})
    return rows, overview, noise_effect, variant_effect, verdicts, profile_effect


def write_outputs(out_dir, runs, started, args, done):
    rows, overview, noise_effect, variant_effect, verdicts, profile_effect = summarise(runs)
    result = {"version": __version__, "rover_pilot": rp.__version__, "done": done,
              "elapsed_s": round(time.monotonic() - started, 1), "seeds": args.seeds,
              "timeout_s": args.timeout, "profiles": PROFILES,
              "steering": rp.ROVER_STEERING, "noise_models": NOISE, "variants": VARIANTS,
              "baseline": {"profile": BASE_PROFILE, "noise": BASE_NOISE,
                           "variant": BASE_VARIANT},
              "missions": {k: {"checkpoints": v, "straight_m": round(gs.straight_m(v), 1)}
                           for k, v in gs.MISSIONS.items()},
              "runs": len(runs), "overview": overview, "verdicts": verdicts,
              "profile_effect": profile_effect, "noise_effect": noise_effect,
              "variant_effect": variant_effect, "groups": rows}
    with open(os.path.join(out_dir, "summary.json"), "w") as f:
        json.dump(result, f, indent=1)
    with open(os.path.join(out_dir, "runs.jsonl"), "w") as f:
        for r in runs:
            f.write(json.dumps(r) + "\n")
    md = ["# earth-rover-pilot on time-correlated GPS error (simulated)", "",
          "gps_noise_study.py %s, rover_pilot.py %s, MV2 of Munim, Inc. Simulated rovers only: "
          "profiles %s, steered with ROVER_STEERING %s. Seeds 1-%d, timeout %d s, missions %s. "
          "Noise models: name = sigma per axis (m) and correlation time T (s); white = "
          "independent fixes, gmS-tT = Gauss-Markov. Within each profile the baseline is %s "
          "with the %s pilot. Variants: %s."
          % (__version__, rp.__version__, json.dumps(PROFILES), json.dumps(rp.ROVER_STEERING),
             args.seeds, args.timeout, ", ".join(dict.fromkeys(r["mission"] for r in runs)),
             BASE_NOISE, BASE_VARIANT,
             json.dumps({k: VARIANTS[k] for k in dict.fromkeys(r["variant"] for r in runs)})),
          "",
          "Bias error: how far the learned compass bias ended from the true one. Credit "
          "distance: how far the rover truly was from a checkpoint when the server (which "
          "judges the reported GPS, like the real one) credited it; tolerance %g m. Fits: "
          "compass-bias fits accepted / rejected per run." % TOLERANCE_M,
          "", "## Overview (all missions pooled; time ratio against the profile's baseline)", "",
          "| profile | noise | variant | completed | time ratio | refused/run | recoveries/run | "
          "fits accepted / rejected per run | bias err median / p90 (deg) | credit dist median "
          "/ p90 / max (m) | credits beyond %g m |" % TOLERANCE_M,
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    md += ["| %s | %s | %s | %d/%d | %s | %s | %s | %s / %s | %s / %s | %s / %s / %s | %d/%d |"
           % (o["profile"], o["noise"], o["variant"], o["completed"], o["runs"],
              o["time_ratio_to_baseline"], o["mean_refused_reports"], o["mean_recoveries"],
              o["mean_calibrations"], o["mean_rejected_fits"],
              o["median_bias_err_deg"], o["p90_bias_err_deg"], o["median_credit_true_m"],
              o["p90_credit_true_m"], o["max_credit_true_m"], o["credits_beyond_tolerance"],
              o["credits"])
           for o in overview]
    md += ["", "## Variants against the shipped pilot, per profile and noise model", "",
           "Faster / slower: missions where a paired sign test per seed gives p < 0.05. "
           "Lost / gained: missions where one side completed more seeds.", "",
           "| profile | noise | variant | faster | slower | lost | gained | verdict |",
           "|---|---|---|---|---|---|---|---|"]
    md += ["| %s | %s | %s | %d/%d | %d | %d | %d | %s |"
           % (v["profile"], v["noise"], v["variant"], v["missions_faster"], v["missions"],
              v["missions_slower"], v["missions_lost"], v["missions_gained"],
              "better" if v["better"] else "worse" if v["worse"] else "no clear difference")
           for v in verdicts]
    md += ["", "## The shipped pilot under each noise model against %s, per mission" % BASE_NOISE,
           "", "| profile | noise | mission | completed (base / this) | faster | slower | "
           "median diff s | p |", "|---|---|---|---|---|---|---|---|"]
    md += ["| %s | %s | %s | -%d / +%d | %d | %d | %s | %s |"
           % (e["profile"], e["noise"], e["mission"], e["only_a_completed"],
              e["only_b_completed"], e["faster"], e["slower"], e["median_time_diff_s"],
              e["sign_test_p"])
           for e in noise_effect]
    md += ["", "## Each profile against %s, shipped pilot on %s, per mission"
           % (BASE_PROFILE, BASE_NOISE), "",
           "| profile | mission | completed (base / this) | faster | slower | median diff s | p |",
           "|---|---|---|---|---|---|---|"]
    md += ["| %s | %s | -%d / +%d | %d | %d | %s | %s |"
           % (e["profile"], e["mission"], e["only_a_completed"], e["only_b_completed"],
              e["faster"], e["slower"], e["median_time_diff_s"], e["sign_test_p"])
           for e in profile_effect]
    with open(os.path.join(out_dir, "report.md"), "w") as f:
        f.write("\n".join(md) + "\n")
    return result


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out-dir", default="out")
    ap.add_argument("--seeds", type=int, default=30)
    ap.add_argument("--timeout", type=float, default=1500.0, help="simulated seconds per mission")
    ap.add_argument("--budget-min", type=float, default=100.0)
    ap.add_argument("--missions", help="comma-separated subset of: " + ",".join(gs.MISSIONS))
    ap.add_argument("--noise", help="comma-separated subset of: " + ",".join(NOISE))
    ap.add_argument("--variants", help="comma-separated subset of: " + ",".join(VARIANTS))
    ap.add_argument("--profiles", help="comma-separated subset of: " + ",".join(PROFILES))
    args = ap.parse_args(argv)
    missions = gs._names(args.missions, gs.MISSIONS, "mission")
    noises = gs._names(args.noise, NOISE, "noise model")
    variants = gs._names(args.variants, VARIANTS, "variant")
    profiles = gs._names(args.profiles, PROFILES, "profile")
    # The baselines are always flown, so every comparison has its reference.
    noises = [BASE_NOISE] + [n for n in noises if n != BASE_NOISE]
    variants = [BASE_VARIANT] + [v for v in variants if v != BASE_VARIANT]
    profiles = [BASE_PROFILE] + [p for p in profiles if p != BASE_PROFILE]
    os.makedirs(args.out_dir, exist_ok=True)
    started = time.monotonic()
    runs = []
    done = True
    for noise in noises:
        if time.monotonic() - started > args.budget_min * 60.0:
            done = False
            break
        for profile in profiles:
            for variant in variants:
                for mission in missions:
                    for seed in range(1, args.seeds + 1):
                        try:
                            r = fly(mission, seed, noise, variant, args.timeout, profile)
                        except Exception as exc:
                            r = {"ok": False, "reason": "%s: %s" % (type(exc).__name__, exc),
                                 "elapsed_s": None, "reached": 0, "checkpoints": None,
                                 "reports": 0, "recoveries": 0, "travelled_m": 0.0,
                                 "calibrations": 0, "rejected_fits": 0, "bias_err_deg": None,
                                 "credited_true_m": []}
                        r.update(profile=profile, noise=noise, variant=variant,
                                 mission=mission, seed=seed)
                        runs.append(r)
        print("%s: %d runs so far, %.0f s" % (noise, len(runs), time.monotonic() - started),
              flush=True)
        write_outputs(args.out_dir, runs, started, args, False)
    result = write_outputs(args.out_dir, runs, started, args, done)
    print(json.dumps({"verdicts": result["verdicts"]}), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
