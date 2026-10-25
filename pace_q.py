#!/usr/bin/env python3
"""pace_q: does the GPS filter's lag cost time once the GPS is as quiet as a real one?

In every pace study since pace_g.py the pilot's idea of where the rover is
has been a median 6.4-6.6 m behind where it really is. Most of that is
GpsFilter itself: an exponential average (alpha 0.3) of fixes that come every
2 s lags a rover at a steady speed by (1 - alpha) / alpha fixes, 4.7 s or
about 4.1 m at 0.889 m/s; the fix is 1.5 s old when it comes (1.3 m) and on
average 1 s older when it is read (0.9 m). The average was kept in
gps_noise_study.py because without it the pilot was slower under the
simulator's GPS noise, 1.5 m per axis, independent from fix to fix. But
frodo_gps.py measured recorded Earth Rovers' fixes scattering only 0.22 m
RMS about a straight line while driving: about six times less. With that
little jitter the average has little to smooth and its lag is all that is left.

Variants (all v0.18.2's real-rover pilot as pace_p.py flies keep16: pace_m.py's
long20 learner on pace_l.py's bridge120+cf0.3, pace_o.py's keep planner and a
16 m lookahead; only the GPS filter changes): a0.3 (GpsFilter as it ships),
a0.6 (alpha 0.6), raw (alpha 1: each new fix as it comes) and track (a
TrackingGpsFilter: alpha 0.3 with a tracked velocity, beta 0.053, starting
again from the fix after a gap). Profiles: pace_l.py's outage90 (90 s GPS
outages, a steady compass error, the simulator's 1.5 m noise), quiet90
(outage90 with 0.22 m of noise per axis) and quietdrift90 (pace_l.py's drift90
with 0.22 m). The noise is drawn from the same generator in the same order,
so a seed's fixes differ between profiles only in size.

    python pace_q.py --out-dir out --first-seed 277 --seeds 24 --check studies/pace-p/runs.jsonl

With --check it first flies seeds 253-255 of pace_p.py's outage90 and drift90
keep16 missions again as a0.3 and compares each field by field with
pace_p.py's record. Simulated rovers only, so the speeds are upper bounds.
Standard library only. By MV2 of Munim, Inc.; written with AI agents.
Apache-2.0.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import sys
import time

import dead_reckon as dr
import pace_d as pd
import pace_e as pe
import pace_f as pf
import pace_g as pg
import pace_h as ph
import pace_i as pi
import pace_j as pj
import pace_l as pl
import pace_m as pm
import pace_n as pn
import pace_o as po
import pace_p as pp
import pace_study as ps
import rover_pilot as rp

__version__ = "0.1.0"

# frodo_gps.py 0.2.0: recorded fixes scatter 0.22 m RMS sideways about a
# straight line in 10 s of straight driving (FINDINGS-frodobots-2k.md).
QUIET_NOISE_M = 0.22
PROFILES = {
    "outage90": pl.PROFILES["outage90"],
    "quiet90": dict(pl.PROFILES["outage90"], gps_noise_m=QUIET_NOISE_M),
    "quietdrift90": dict(pl.PROFILES["drift90"], gps_noise_m=QUIET_NOISE_M),
}
# The first is always flown.
BASE_PROFILE = next(iter(PROFILES))
# (a, b): each variant on profile b against itself on profile a, paired by
# seed: what quieter fixes are worth, and what a drifting compass costs then.
PROFILE_PAIRS = (("outage90", "quiet90"), ("quiet90", "quietdrift90"))
# The GPS filter for each variant: GpsFilter with alpha, or with track a
# TrackingGpsFilter with alpha and beta. Every mission is otherwise flown
# as pace_p.py's keep16.
FLOWN_AS = pp.BASE_VARIANT
# beta = alpha^2 / (2 - alpha), Benedict and Bordner's pairing for alpha 0.3.
VARIANTS = {
    "a0.3": {"alpha": 0.3},
    "a0.6": {"alpha": 0.6},
    "raw": {"alpha": 1.0},
    "track": {"alpha": 0.3, "beta": 0.053, "track": True},
}
# The pilot as it ships; every pair is against it, so it is always flown.
BASE_VARIANT = next(iter(VARIANTS))
# (a, b): b against a, paired by seed on every profile and course.
PAIRS = tuple((BASE_VARIANT, v) for v in VARIANTS if v != BASE_VARIANT)
CRUISES = (0.8,)
# pace_p.py flew seeds 253-276; these start after them.
FIRST_SEED = 277
# pace_p.py flew these as keep16; --check flies them again as a0.3.
CHECKED = {"profiles": ("outage90", "drift90"), "variant": BASE_VARIANT, "against": FLOWN_AS,
           "seeds": (253, 254, 255)}
NO_GPS = {"filters": None, "restarts": None}


class TrackingGpsFilter(rp.GpsFilter):
    """GpsFilter that also tracks the rover's velocity (an alpha-beta filter).

    Each accepted fix is compared with the estimate carried forward at the
    tracked velocity; the estimate moves alpha of the way to the fix and the
    velocity beta / dt of the difference. At a steady speed it settles on the
    fixes themselves, where the plain average lags (1 - alpha) / alpha fixes
    behind them. With `restart`, after more than max_age_s without a valid
    reading it starts again from the fix with no velocity (`restarts` counts
    these), as a velocity can't be carried across an outage. Bad readings are
    dropped exactly as GpsFilter drops them; with beta 0 and no restart it is
    a GpsFilter."""

    def __init__(self, alpha=0.3, beta=0.053, restart=True, **kw):
        super().__init__(alpha=alpha, **kw)
        self.beta = beta
        self.restart = restart
        self.v_lat = self.v_lon = 0.0  # degrees per second
        self.restarts = 0

    def update(self, lat, lon, t):
        # GpsFilter.update's checks, line for line; only the smoothing differs.
        fix = rp.parse_fix(lat, lon)
        if fix is None:
            return None
        if fix == self.raw:
            self.fix_t = t
            return None
        if self.raw is not None:
            dt = max(t - self.raw_t, 1e-3)
            jump = rp.haversine_m(self.raw[0], self.raw[1], fix[0], fix[1])
            if jump > self.max_speed_mps * dt + self.jump_slack_m:
                if fix != self._last_rejected:
                    self._last_rejected = fix
                    self.rejected += 1
                if self.rejected < self.reset_after:
                    return None
                self.lat = self.lon = None  # the old fix was the bad one
        self.rejected = 0
        self._last_rejected = None
        gap = (self.restart and self.lat is not None
               and t - self.fix_t > self.max_age_s)
        dt = max(t - self.raw_t, 1e-3) if self.raw_t is not None else 1e-3
        self.raw, self.raw_t, self.fix_t = fix, t, t
        if self.lat is None or gap:
            self.lat, self.lon = fix
            self.v_lat = self.v_lon = 0.0
            self.restarts += gap
            return fix
        p_lat = self.lat + self.v_lat * dt
        p_lon = self.lon + self.v_lon * dt
        r_lat, r_lon = fix[0] - p_lat, fix[1] - p_lon
        self.lat = p_lat + self.alpha * r_lat
        self.lon = p_lon + self.alpha * r_lon
        self.v_lat += self.beta * r_lat / dt
        self.v_lon += self.beta * r_lon / dt
        return fix


@contextlib.contextmanager
def _known_profile(profile):
    """While inside, pace_l.fly knows the profile by name; a name it already
    knows is left as it is."""
    add = profile not in pl.PROFILES
    if add:
        pl.PROFILES[profile] = PROFILES[profile]
    try:
        yield
    finally:
        if add:
            del pl.PROFILES[profile]


@contextlib.contextmanager
def _filtering(settings, made):
    """While inside, every GPS filter the Pilot builds is the variant's
    (`settings`: a VARIANTS entry), each appended to `made`."""
    saved = rp.GpsFilter

    def make(*args, **kw):
        if settings.get("track"):
            f = TrackingGpsFilter(alpha=settings["alpha"], beta=settings["beta"])
        else:
            f = saved(alpha=settings["alpha"])
        made.append(f)
        return f

    rp.GpsFilter = make
    try:
        yield
    finally:
        rp.GpsFilter = saved


def fly(course_name, seed, profile, variant, cruise, course=None):
    """One mission flown by pace_p.fly as keep16 with the variant's GPS
    filter, with pace_p.py's records; also the gps record: how many filters
    the pilot built and, for track, how often it started again."""
    v = VARIANTS[variant]
    made = []
    with _known_profile(profile), _filtering(v, made):
        r = pp.fly(course_name, seed, profile, FLOWN_AS, cruise, course=course)
    r["gps"] = {"filters": len(made),
                "restarts": sum(f.restarts for f in made) if v.get("track") else None}
    return r


def failed_run(exc):
    return dict(pp.failed_run(exc), gps=dict(NO_GPS))


def check_pace_p(path):
    """Fly the CHECKED missions again as a0.3 and compare each with
    pace_p.py's record of it as keep16 (its runs.jsonl): every field
    pace_p.py recorded must be equal. A mission the record lacks is counted
    as missing and not flown."""
    ref = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                r = json.loads(line)
                ref[(r["profile"], r["variant"], r["cruise"], r["course"], r["seed"])] = r
    compared = missing = 0
    different = []
    for profile in CHECKED["profiles"]:
        for cruise in CRUISES:
            for course in ps.COURSES:
                for seed in CHECKED["seeds"]:
                    want = ref.get((profile, CHECKED["against"], cruise, course, seed))
                    if want is None:
                        missing += 1
                        continue
                    got = fly(course, seed, profile, CHECKED["variant"], cruise)
                    got.update(profile=profile, variant=CHECKED["against"], cruise=cruise,
                               course=course, seed=seed)
                    got = json.loads(json.dumps(got))
                    compared += 1
                    fields = sorted(k for k in want if got.get(k) != want[k])
                    if fields:
                        different.append({"profile": profile, "variant": CHECKED["variant"],
                                          "cruise": cruise, "course": course, "seed": seed,
                                          "fields": fields})
    return {"reference": path, "compared": compared, "identical": compared - len(different),
            "missing": missing, "different": different[:20]}


def pair_effects(runs):
    """pace_i.pair_effects with this study's PAIRS."""
    saved = pi.PAIRS
    pi.PAIRS = PAIRS
    try:
        return pi.pair_effects(runs)
    finally:
        pi.PAIRS = saved


def profile_effects(runs):
    """pace_j.profile_effects with this study's variants and PROFILE_PAIRS."""
    saved = pj.VARIANTS, pj.PROFILE_PAIRS
    pj.VARIANTS, pj.PROFILE_PAIRS = VARIANTS, PROFILE_PAIRS
    try:
        return pj.profile_effects(runs)
    finally:
        pj.VARIANTS, pj.PROFILE_PAIRS = saved


def gps_rows(runs):
    """Per (profile, variant, cruise, course), over the completed missions:
    the median of recovery moves and, for track, of its restarts."""
    rows = []
    for k, rs in sorted(pg._groups(runs).items()):
        ok = [r for r in rs if r["ok"]]
        if not ok:
            continue
        restarts = [r["gps"]["restarts"] for r in ok
                    if (r.get("gps") or {}).get("restarts") is not None]
        rows.append({"profile": k[0], "variant": k[1], "cruise": k[2], "course": k[3],
                     "missions": len(ok),
                     "median_recoveries": ps._median([r["recoveries"] for r in ok]),
                     "median_restarts": ps._median(restarts) if restarts else None})
    return rows


def write_outputs(out_dir, runs, started, seeds, done, check=None):
    s = ps.summarise(runs)
    effects, tallies = pair_effects(runs)
    p_effects, p_tallies = profile_effects(runs)
    gps = gps_rows(runs)
    context = po.context_rows(runs)
    corner = pn.corner_rows(runs)
    maxes = pn.offset_max_rows(runs)
    offsets = pe.offset_rows(runs)
    headings_ = pd.heading_rows(runs)
    positions = pg.position_rows(runs)
    steering = ph.steer_rows(runs)
    result = {"version": __version__, "pace_p": pp.__version__, "pace_o": po.__version__,
              "pace_n": pn.__version__, "pace_m": pm.__version__, "pace_l": pl.__version__,
              "pace_j": pj.__version__, "pace_i": pi.__version__, "pace_e": pe.__version__,
              "pace_d": pd.__version__, "pace_study": ps.__version__,
              "rover_pilot": rp.__version__, "dead_reckon": dr.__version__, "done": done,
              "elapsed_s": round(time.monotonic() - started, 1), "seeds": seeds,
              "human": {"marathon_m": ps.MARATHON_M, "time_s": ps.HUMAN_S,
                        "mps": round(ps.HUMAN_MPS, 4)},
              "profiles": PROFILES, "quiet_noise_m": QUIET_NOISE_M, "flown_as": FLOWN_AS,
              "learner": pp.LEARNER, "planner_kind": pp.PLANNER,
              "lookahead_m": pp.VARIANTS[FLOWN_AS]["lookahead_m"], "variants": VARIANTS,
              "pairs": [list(x) for x in PAIRS],
              "profile_pairs": [list(x) for x in PROFILE_PAIRS], "cruises": list(CRUISES),
              "corner_deg": pn.CORNER_DEG, "corner_m": pn.CORNER_M, "far_m": po.FAR_M,
              "runs": len(runs), "completed": sum(1 for r in runs if r["ok"]),
              "overview": s["overview"], "pair_effect": effects, "verdicts": tallies,
              "profile_effect": p_effects, "profile_verdicts": p_tallies, "gps": gps,
              "position": positions, "corner": corner, "offset": offsets,
              "offset_max": maxes, "context": context, "heading": headings_,
              "steer": steering, "check": check}
    with open(os.path.join(out_dir, "summary.json"), "w") as f:
        json.dump(result, f, indent=1)
    with open(os.path.join(out_dir, "runs.jsonl"), "w") as f:
        for r in runs:
            f.write(json.dumps(r) + "\n")
    md = ["# Does the GPS filter's lag cost time once the GPS is as quiet as a real one? "
          "(simulated)",
          "",
          "pace_q.py %s (pace_p.py %s, pace_o.py %s, rover_pilot.py %s, dead_reckon.py %s), MV2 "
          "of Munim, Inc. Every mission is v0.18.2's real-rover pilot as pace_p.py flies keep16 "
          "(pace_m.py's long20 learner on pace_l.py's bridge120+cf0.3, pace_o.py's keep planner, "
          "a 16 m lookahead); only the GPS filter changes (a0.3 as it ships, a0.6, raw = alpha "
          "1, track = alpha 0.3 with a tracked velocity). Profiles: outage90 (90 s GPS outages, "
          "a steady compass error, 1.5 m of GPS noise per axis), quiet90 (the same with %g m) "
          "and quietdrift90 (pace_l.py's drift90 with %g m). Seeds %s. %d of %d missions "
          "completed. Simulated rovers only, so these speeds are upper bounds."
          % (__version__, pp.__version__, po.__version__, rp.__version__, dr.__version__,
             QUIET_NOISE_M, QUIET_NOISE_M,
             "%d-%d" % (seeds[0], seeds[-1]) if seeds else "none",
             result["completed"], len(runs)), ""]
    if check is not None:
        md += ["Check against pace_p.py's runs: %d compared, %d identical, %d missing."
               % (check["compared"], check["identical"], check["missing"]), ""]
    md += ["## Overview (courses pooled)", ""]
    md += pf._table(["profile", "variant", "completed", "made good m/s (median)", "efficiency",
                     "runs beating 0.754", "path ratio", "share stopped"],
                    [(o["profile"], o["variant"], "%d/%d" % (o["completed"], o["runs"]),
                      o["median_made_good_mps"], o["median_efficiency"], o["beat_human_pace"],
                      o["median_path_ratio"], o["share_stopped"]) for o in s["overview"]])
    md += ["", "## Pairs, same profile", "",
           "Faster / slower: courses where a paired sign test gives p < 0.05.", ""]
    md += pf._table(["profile", "variant", "against", "faster", "slower", "lost", "gained",
                     "largest median diff"],
                    [(t["profile"], t["variant"], t["against"],
                      "%d/%d" % (t["groups_faster"], t["groups"]), t["groups_slower"],
                      t["groups_lost"], t["groups_gained"], t["largest_median_diff_share"])
                     for t in tallies])
    md += [""]
    md += pf._table(["profile", "variant", "against", "course", "faster", "slower",
                     "median diff s", "share", "p"],
                    [(e["profile"], e["variant"], e["against"], e["course"], e["faster"],
                      e["slower"], e["median_time_diff_s"], e["median_time_diff_share"],
                      e["sign_test_p"]) for e in effects])
    md += ["", "## What the profile costs each variant", ""]
    md += pf._table(["variant", "profile", "against", "faster", "slower", "lost", "gained",
                     "largest median diff"],
                    [(t["variant"], t["profile"], t["against"],
                      "%d/%d" % (t["groups_faster"], t["groups"]), t["groups_slower"],
                      t["groups_lost"], t["groups_gained"], t["largest_median_diff_share"])
                     for t in p_tallies])
    md += ["", "## Where the pilot thinks it is, against where it is", ""]
    md += pf._table(["profile", "variant", "course", "missions", "median m", "p95 m"],
                    [(x["profile"], x["variant"], x["course"], x["missions"],
                      x["median_position_err_m"], x["p95_position_err_m"]) for x in positions])
    md += ["", "## Recovery moves and filter restarts", ""]
    md += pf._table(["profile", "variant", "course", "missions", "recoveries (median)",
                     "restarts (median)"],
                    [(x["profile"], x["variant"], x["course"], x["missions"],
                      x["median_recoveries"], x["median_restarts"]) for x in gps])
    md += ["", "## Near path corners (pace_n.py's record)", ""]
    md += pf._table(["profile", "variant", "course", "missions", "corners", "median m", "p95 m",
                     "max m", "median past m", "max past m"],
                    [(x["profile"], x["variant"], x["course"], x["missions"], x["corners"],
                      x["median_m"], x["p95_m"], x["max_m"], x["median_past_m"],
                      x["max_past_m"]) for x in corner])
    md += ["", "## Distance from the course while driving forward", ""]
    md += pf._table(["profile", "variant", "course", "missions", "median m", "p95 m"],
                    [(x["profile"], x["variant"], x["course"], x["missions"],
                      x["median_offset_m"], x["p95_offset_m"]) for x in offsets])
    md += ["", "## Largest distance from the course, and refused reports", ""]
    md += pf._table(["profile", "variant", "course", "missions", "median of max m",
                     "largest m", "refused", "missions refused"],
                    [(x["profile"], x["variant"], x["course"], x["missions"], x["median_max_m"],
                      x["largest_max_m"], x["refused"], x["missions_refused"]) for x in maxes])
    md += ["", "## Where the rover strays (true distance from the course by context; far: "
           "over %g m)" % po.FAR_M, ""]
    md += pf._table(["profile", "variant", "course", "context", "missions", "samples", "far",
                     "far share", "median m", "p95 m", "max m"],
                    [(x["profile"], x["variant"], x["course"], x["context"], x["missions"],
                      x["samples"], x["far"], x["far_share"], x["median_m"], x["p95_m"],
                      x["max_m"]) for x in context])
    md += ["", "## Heading error", ""]
    md += pf._table(["profile", "variant", "course", "missions", "median abs deg", "rms deg"],
                    [(x["profile"], x["variant"], x["course"], x["missions"],
                      x["median_abs_deg"], x["rms_deg"]) for x in headings_])
    md += ["", "## How hard the pilot steers", ""]
    md += pf._table(["profile", "variant", "course", "missions", "mean abs angular"],
                    [(x["profile"], x["variant"], x["course"], x["missions"],
                      x["median_mean_abs_angular"]) for x in steering])
    with open(os.path.join(out_dir, "report.md"), "w") as f:
        f.write("\n".join(md) + "\n")
    return result


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out-dir", default="out")
    ap.add_argument("--first-seed", type=int, default=FIRST_SEED)
    ap.add_argument("--seeds", type=int, default=24, help="how many seeds, from --first-seed")
    ap.add_argument("--budget-min", type=float, default=180.0)
    ap.add_argument("--courses", help="comma-separated subset of: " + ",".join(ps.COURSES))
    ap.add_argument("--profiles", help="comma-separated subset of: " + ",".join(PROFILES))
    ap.add_argument("--variants", help="comma-separated subset of: " + ",".join(VARIANTS))
    ap.add_argument("--check", help="pace_p.py's runs.jsonl: fly the CHECKED missions again "
                                    "and compare")
    args = ap.parse_args(argv)
    courses = ps._names(args.courses, ps.COURSES, "course")
    profiles = ps._names(args.profiles, PROFILES, "profile")
    variants = ps._names(args.variants, VARIANTS, "variant")
    # outage90 and a0.3 are always flown: the rest are compared with them.
    profiles = [BASE_PROFILE] + [p for p in profiles if p != BASE_PROFILE]
    variants = [BASE_VARIANT] + [v for v in variants if v != BASE_VARIANT]
    seeds = list(range(args.first_seed, args.first_seed + args.seeds))
    os.makedirs(args.out_dir, exist_ok=True)
    started = time.monotonic()
    check = check_pace_p(args.check) if args.check else None
    if check is not None:
        print("check: %d compared, %d identical, %d missing"
              % (check["compared"], check["identical"], check["missing"]), flush=True)
    runs = []
    done = True
    for profile in profiles:
        for variant in variants:
            if time.monotonic() - started > args.budget_min * 60.0:
                done = False
                break
            for cruise in CRUISES:
                for course in courses:
                    for seed in seeds:
                        try:
                            r = fly(course, seed, profile, variant, cruise)
                        except Exception as exc:
                            r = failed_run(exc)
                        r.update(profile=profile, variant=variant, cruise=cruise,
                                 course=course, seed=seed)
                        runs.append(r)
            print("%s / %s: %d runs so far, %.0f s"
                  % (profile, variant, len(runs), time.monotonic() - started), flush=True)
            write_outputs(args.out_dir, runs, started, seeds, False, check)
        if not done:
            break
    result = write_outputs(args.out_dir, runs, started, seeds, done, check)
    print(json.dumps({"check": None if check is None else
                      {k: check[k] for k in ("compared", "identical", "missing")},
                      "completed": result["completed"], "runs": result["runs"],
                      "verdicts": [{k: v[k] for k in ("profile", "variant", "against",
                                                      "groups_faster", "groups_slower",
                                                      "groups_lost")}
                                   for v in result["verdicts"]]}), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
