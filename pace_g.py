#!/usr/bin/env python3
"""pace_g: the real-rover defaults together: dead reckoning and --smooth-heading.

Since v0.13.0 the command line turns on two things for a real rover:
dead reckoning (dead_reckon.DeadReckoner with DEAD_RECKON: the position
carried from each GPS fix by the wheels along the pilot's heading) and
--smooth-heading (HeadingSmoother with SMOOTH_HEADING). Every pace study so
far flew the pilot without dead reckoning, and dead_reckon_study.py flew it
without the smoother, so the two have never been flown together. Here the
smoothed compass also feeds dead reckoning: its direction, and the test of
whether a stretch was straight enough to learn the wheel size on.

This study flies the four combinations on the measured Mini+ (pace_f.py's
`measured`, now also reporting its wheels' RPM like an Earth Rover) with 3, 6
and 8 deg of compass noise, with 30% of GPS fixes missing, and with wheels
that drive 0.85 of what the 95 mm prior says per RPM. Besides pace_f.py's
fields, every mission records how far the pilot's idea of its position is
from the truth, and when dead reckoning was first trusted.

    python pace_g.py --out-dir out --first-seed 37 --seeds 24 --check studies/pace-f/runs.jsonl

With --check it first flies seeds 13-15 of pace_f.py's measured and noise6
missions again, without dead reckoning and with --smooth-heading or without,
and compares each field by field with pace_f.py's record: the wheels'
reports must change nothing. Simulated rovers only, so the speeds are upper
bounds. Standard library only. By MV2 of Munim, Inc.; written with AI agents.
Apache-2.0.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import statistics
import sys
import time

import dead_reckon as dr
import pace_d as pd
import pace_e as pe
import pace_f as pf
import pace_study as ps
import rover_pilot as rp

__version__ = "0.1.0"

# The rover reports its wheels as the simulator's --dead-reckon does.
_MEASURED = dict(pf.PROFILES["measured"], wheel_mps_per_rpm=dr.MINI_PLUS_MPS_PER_RPM)
PROFILES = {
    "measured": _MEASURED,
    "noise6": dict(_MEASURED, compass_noise_deg=6.0),
    "noise8": dict(_MEASURED, compass_noise_deg=8.0),
    "dropout0.3": dict(_MEASURED, gps_dropout=0.3),
    "dropout0.3-noise8": dict(_MEASURED, gps_dropout=0.3, compass_noise_deg=8.0),
    # The wheels drive 0.85 of what the prior says per RPM: the reckoner must learn it.
    "wheels0.85": dict(_MEASURED, wheel_mps_per_rpm=0.85 * dr.MINI_PLUS_MPS_PER_RPM),
}
# The first is the reference every other profile is compared with.
BASE_PROFILE = next(iter(PROFILES))
# The first is the pilot as v0.13.0 flies a real rover; the last is pace_f.py's shipped pilot.
VARIANTS = {
    "dr+cf0.3": {"dead_reckon": True, "smooth": rp.SMOOTH_HEADING},
    "dr": {"dead_reckon": True},
    "cf0.3": {"smooth": rp.SMOOTH_HEADING},
    "plain": {},
}
BASE_VARIANT = next(iter(VARIANTS))
# What pace_f.py called the same pilots.
PACE_F_NAMES = {"plain": "shipped", "cf0.3": "cf0.3"}
# (a, b): b against a, paired by seed on every profile and course.
PAIRS = (("dr", "dr+cf0.3"), ("cf0.3", "dr+cf0.3"), ("plain", "dr"), ("plain", "cf0.3"))
CRUISES = (0.8,)
# pace_f.py flew seeds 13-36; these start after them.
FIRST_SEED = 37
# pace_f.py flew these with the same settings; --check flies them again.
CHECKED = {"profiles": ("measured", "noise6"), "variants": ("plain", "cf0.3"),
           "seeds": (13, 14, 15)}
POSITION_EVERY_S = pe.OFFSET_EVERY_S


def position_error(pos, sim):
    """Metres between the pilot's idea of where the rover is and where it is,
    or None while the pilot has no position."""
    if pos is None or pos[0] is None:
        return None
    east, north = rp.to_enu(sim.lat0, sim.lon0, pos[0], pos[1])
    return math.hypot(north - sim.north, east - sim.east)


def fly(course_name, seed, profile, variant, cruise, course=None):
    """One mission flown as pace_f.fly flies it, with dead reckoning if the
    variant asks, and the position error and the reckoner's record."""
    course = course or ps.COURSES[course_name]
    pts = course["points"]
    sim = pd.DistortedRover([pts[i] for i in course["checkpoints"]], seed=seed, **PROFILES[profile])
    v = VARIANTS[variant]
    smoother = rp.HeadingSmoother(**v["smooth"]) if "smooth" in v else None
    # As the command line builds it for a real rover.
    reckoner = dr.DeadReckoner(**rp.DEAD_RECKON) if v.get("dead_reckon") else None
    planner = ps.CoursePlanner(course, sim.lat0, sim.lon0)
    errors, offsets, misses = [], [], []
    next_offset_t = [0.0]
    trusted_at = [None]
    pilot = None

    def sleep(seconds):
        # Only reads; the mission is the same without it.
        if reckoner is not None and trusted_at[0] is None and reckoner.trusted:
            trusted_at[0] = sim.t
        if sim.applied[0] > 0:
            h = pilot._heading_now
            if h is not None:
                errors.append(rp.wrap180(h - sim.heading))
            if sim.t >= next_offset_t[0]:
                offsets.append(pe.course_offset(pts, sim.north, sim.east))
                miss = position_error(pilot.pos, sim)
                if miss is not None:
                    misses.append(miss)
                next_offset_t[0] = sim.t + POSITION_EVERY_S
        sim.sleep(seconds)

    pilot = rp.Pilot(sim, clock=sim.clock, sleep=sleep,
                     steering=rp.make_steering(False, cruise=cruise), planner=planner,
                     smooth_heading=smoother, dead_reckon=reckoner)
    est = pe.CountingEstimator()
    pilot.heading = est
    total_m = ps.route_m(course)
    ideal_mps = cruise * sim.max_speed_mps
    res = pilot.run(timeout_s=3.0 * total_m / ideal_mps + 300.0)
    reached = len(res["reached"])
    done_m = ps.route_m(course, upto=reached)
    elapsed = res["elapsed_s"]
    made_good = done_m / elapsed if elapsed else 0.0
    spreads = est.spreads
    reckoned = None
    if reckoner is not None:
        reckoned = dict(res["dead_reckon"],
                        trusted_at_s=None if trusted_at[0] is None else round(trusted_at[0], 1),
                        # The learned metres per RPM over the rover's own: 1 is right.
                        learned_scale=round(reckoner.mps_per_rpm / sim.wheel_mps_per_rpm, 4))
    return {"ok": res["ok"], "reason": res["reason"], "elapsed_s": elapsed,
            "reached": reached, "checkpoints": res["checkpoints"], "reports": res["reports"],
            "recoveries": res["recoveries"], "plans": res["plans"],
            "route_m": round(done_m, 1), "travelled_m": round(sim.travelled, 1),
            "made_good_mps": round(made_good, 4), "ideal_mps": round(ideal_mps, 4),
            "efficiency": round(made_good / ideal_mps, 4),
            "time_s": {k: round(x, 1) for k, x in sim.time_in.items()},
            "heading_err": pd.heading_stats(errors),
            "learner": {"calibrations": est.calibrations, "breaks": est.breaks, "fits": est.fits,
                        "spread_checked": est.spread_checked,
                        "spread_rejected": est.spread_rejected,
                        "median_spread": ps._median(spreads, 4),
                        "bias_deg": round(est.bias, 2),
                        # The bias that would cancel the compass error at the end.
                        "bias_error_deg": round(rp.wrap180(est.bias + sim.compass_error), 2)},
            "offset": pe.offset_stats(offsets),
            "position_err": pe.offset_stats(misses),
            "dead_reckon": reckoned}


def failed_run(exc):
    return dict(pf.failed_run(exc), position_err=pe.offset_stats([]), dead_reckon=None)


def check_pace_f(path):
    """Fly the CHECKED missions again and compare each with pace_f.py's record
    of it (its runs.jsonl, where `plain` is called `shipped`): every field
    pace_f.py recorded must be equal. A mission the record lacks is counted as
    missing and not flown."""
    ref = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                r = json.loads(line)
                ref[(r["profile"], r["variant"], r["cruise"], r["course"], r["seed"])] = r
    compared = missing = 0
    different = []
    for profile in CHECKED["profiles"]:
        for variant in CHECKED["variants"]:
            name = PACE_F_NAMES[variant]
            for cruise in CRUISES:
                for course in ps.COURSES:
                    for seed in CHECKED["seeds"]:
                        want = ref.get((profile, name, cruise, course, seed))
                        if want is None:
                            missing += 1
                            continue
                        got = fly(course, seed, profile, variant, cruise)
                        got.update(profile=profile, variant=name, cruise=cruise,
                                   course=course, seed=seed)
                        got = json.loads(json.dumps(got))
                        compared += 1
                        fields = sorted(k for k in want if got.get(k) != want[k])
                        if fields:
                            different.append({"profile": profile, "variant": variant,
                                              "cruise": cruise, "course": course, "seed": seed,
                                              "fields": fields})
    return {"reference": path, "compared": compared, "identical": compared - len(different),
            "missing": missing, "different": different[:20]}


def _groups(runs):
    groups = {}
    for r in runs:
        groups.setdefault((r["profile"], r["variant"], r["cruise"], r["course"]), []).append(r)
    return groups


def pair_effects(runs):
    """For each PAIRS (a, b) and profile: b against a per cruise x course, paired
    by seed, with the median time difference as a share of a's median; and the
    tally per (a, b, profile): groups faster / slower (paired sign test
    p < 0.05), courses where a or b completed more, the largest share."""
    groups = _groups(runs)
    seen = {k[0] for k in groups}
    profiles = [p for p in PROFILES if p in seen] + sorted(seen - set(PROFILES))
    effects, tallies = [], []
    for a, b in PAIRS:
        for profile in profiles:
            faster = slower = lost = gained = n = 0
            largest = None
            for (p, v, c, m) in sorted(groups):
                if (p, v) != (profile, b) or (p, a, c, m) not in groups:
                    continue
                base = groups[(p, a, c, m)]
                cmp_ = ps.compare(base, groups[(p, b, c, m)])
                base_med = ps._median([r["elapsed_s"] for r in base if r["ok"]])
                share = (round(cmp_["median_time_diff_s"] / base_med, 4)
                         if base_med and cmp_["median_time_diff_s"] is not None else None)
                effects.append(dict(profile=p, variant=b, against=a, cruise=c, course=m,
                                    median_time_diff_share=share, **cmp_))
                n += 1
                if cmp_["sign_test_p"] is not None and cmp_["sign_test_p"] < 0.05:
                    faster += cmp_["faster"] > cmp_["slower"]
                    slower += cmp_["slower"] > cmp_["faster"]
                lost += cmp_["only_a_completed"] > cmp_["only_b_completed"]
                gained += cmp_["only_b_completed"] > cmp_["only_a_completed"]
                if share is not None and (largest is None or abs(share) > abs(largest)):
                    largest = share
            if n:
                tallies.append({"profile": profile, "variant": b, "against": a, "groups": n,
                                "groups_faster": faster, "groups_slower": slower,
                                "groups_lost": lost, "groups_gained": gained,
                                "largest_median_diff_share": largest})
    return effects, tallies


def position_rows(runs):
    """Per (profile, variant, cruise, course): over the completed missions, the
    median of each mission's median and 95th-percentile position error."""
    rows = []
    for k, rs in sorted(_groups(runs).items()):
        xs = [r["position_err"] for r in rs if r["ok"] and r.get("position_err", {}).get("n")]
        rows.append({"profile": k[0], "variant": k[1], "cruise": k[2], "course": k[3],
                     "missions": len(xs),
                     "median_position_err_m": ps._median([x["median_m"] for x in xs], 2),
                     "p95_position_err_m": ps._median([x["p95_m"] for x in xs], 2)})
    return rows


def _median_or_never(values, digits=1):
    """Median with None counted as never (after every other value); None if
    that median is never."""
    if not values:
        return None
    m = statistics.median([math.inf if x is None else x for x in values])
    return None if math.isinf(m) else round(m, digits)


def dr_rows(runs):
    """Per (profile, variant, cruise, course) with dead reckoning: over the
    completed missions, how many ended trusted, the median time it was first
    trusted (never counted last), the missions never trusted, the median
    straight stretches it learned the wheel size on and turned down, the
    median seconds driven on the wheels alone, and the median |learned
    scale - 1|."""
    rows = []
    for k, rs in sorted(_groups(runs).items()):
        ds = [r["dead_reckon"] for r in rs if r["ok"] and r.get("dead_reckon")]
        if not ds:
            continue
        rows.append({"profile": k[0], "variant": k[1], "cruise": k[2], "course": k[3],
                     "missions": len(ds),
                     "trusted_missions": sum(1 for d in ds if d["trusted"]),
                     "never_trusted": sum(1 for d in ds if d["trusted_at_s"] is None),
                     "median_trusted_at_s": _median_or_never([d["trusted_at_s"] for d in ds]),
                     "median_scale_samples": ps._median([d["scale_samples"] for d in ds]),
                     "median_scale_rejects": ps._median([d["scale_rejects"] for d in ds]),
                     "median_bridged_s": ps._median([d["bridged_s"] for d in ds]),
                     "median_abs_scale_error": ps._median(
                         [abs(d["learned_scale"] - 1.0) for d in ds], 4)})
    return rows


def write_outputs(out_dir, runs, started, seeds, done, check=None):
    s = ps.summarise(runs)
    effects, tallies = pair_effects(runs)
    p_effects, p_tallies = pd.profile_effects(runs)
    headings = pd.heading_rows(runs)
    learner = pe.learner_rows(runs)
    offsets = pe.offset_rows(runs)
    positions = position_rows(runs)
    reckoning = dr_rows(runs)
    result = {"version": __version__, "pace_f": pf.__version__, "pace_e": pe.__version__,
              "pace_d": pd.__version__, "pace_study": ps.__version__,
              "rover_pilot": rp.__version__, "dead_reckon": dr.__version__, "done": done,
              "elapsed_s": round(time.monotonic() - started, 1), "seeds": seeds,
              "human": {"marathon_m": ps.MARATHON_M, "time_s": ps.HUMAN_S,
                        "mps": round(ps.HUMAN_MPS, 4)},
              "profiles": PROFILES, "variants": VARIANTS, "pairs": [list(x) for x in PAIRS],
              "cruises": list(CRUISES), "steering": rp.ROVER_STEERING,
              "dead_reckon_settings": rp.DEAD_RECKON,
              "runs": len(runs), "completed": sum(1 for r in runs if r["ok"]),
              "overview": s["overview"], "pair_effect": effects, "verdicts": tallies,
              "profile_effect": p_effects, "profile_tallies": p_tallies,
              "position": positions, "reckoner": reckoning, "learner": learner,
              "offset": offsets, "heading": headings, "check": check}
    with open(os.path.join(out_dir, "summary.json"), "w") as f:
        json.dump(result, f, indent=1)
    with open(os.path.join(out_dir, "runs.jsonl"), "w") as f:
        for r in runs:
            f.write(json.dumps(r) + "\n")
    md = ["# Dead reckoning and --smooth-heading together (simulated)", "",
          "pace_g.py %s (pace_f.py %s, rover_pilot.py %s, dead_reckon.py %s), MV2 of Munim, Inc. "
          "Every profile is pace_f.py's measured Mini+ (orientation every 0.5 s, 48 deg/s, 0.5 s "
          "latency, GPS every 2 s and 1.5 s late, 3 deg of compass noise, a -25 deg compass error "
          "to learn), reporting its wheels' RPM, with one or two things changed: 6 or 8 deg of "
          "noise, 30%% of GPS fixes missing, or wheels driving 0.85 of the 95 mm prior per RPM. "
          "Variants: dr+cf0.3 (v0.13.0 on a real rover), dr (dead reckoning only), cf0.3 "
          "(--smooth-heading only), plain (neither; pace_f.py's shipped). Seeds %s. %d of %d "
          "missions completed. Simulated rovers only, so these speeds are upper bounds."
          % (__version__, pf.__version__, rp.__version__, dr.__version__,
             "%d-%d" % (seeds[0], seeds[-1]) if seeds else "none",
             result["completed"], len(runs)), ""]
    if check is not None:
        md += ["Check against pace_f.py's runs: %d compared, %d identical, %d missing."
               % (check["compared"], check["identical"], check["missing"]), ""]
    md += ["## Overview (courses pooled)", ""]
    md += pf._table(["profile", "variant", "completed", "made good m/s (median)", "efficiency",
                     "runs beating 0.754", "path ratio"],
                    [(o["profile"], o["variant"], "%d/%d" % (o["completed"], o["runs"]),
                      o["median_made_good_mps"], o["median_efficiency"], o["beat_human_pace"],
                      o["median_path_ratio"]) for o in s["overview"]])
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
    md += ["", "## Where the pilot thinks it is, against where it is", "",
           "Sampled once a second while driving forward; medians over the completed missions "
           "of each mission's median and 95th percentile.", ""]
    md += pf._table(["profile", "variant", "course", "missions", "median m", "p95 m"],
                    [(x["profile"], x["variant"], x["course"], x["missions"],
                      x["median_position_err_m"], x["p95_position_err_m"]) for x in positions])
    md += ["", "## Dead reckoning", "",
           "Trusted after two straight stretches of about 20 s agree with the wheel-size prior; "
           "'first trusted' is a median with missions never trusted counted last (blank if most "
           "never were).", ""]
    md += pf._table(["profile", "variant", "course", "missions", "trusted at end",
                     "never trusted", "first trusted s", "stretches learned", "turned down",
                     "s on wheels alone", "abs scale error"],
                    [(x["profile"], x["variant"], x["course"], x["missions"],
                      x["trusted_missions"], x["never_trusted"], x["median_trusted_at_s"],
                      x["median_scale_samples"], x["median_scale_rejects"],
                      x["median_bridged_s"], x["median_abs_scale_error"]) for x in reckoning])
    md += ["", "## The compass-bias learner", ""]
    md += pf._table(["profile", "variant", "course", "missions", "median calibrations",
                     "missions with none", "median abs bias error deg"],
                    [(x["profile"], x["variant"], x["course"], x["missions"],
                      x["median_calibrations"], x["zero_calibration_missions"],
                      x["median_abs_bias_error_deg"]) for x in learner])
    md += ["", "## Distance from the course while driving forward", ""]
    md += pf._table(["profile", "variant", "course", "missions", "median m", "p95 m"],
                    [(x["profile"], x["variant"], x["course"], x["missions"],
                      x["median_offset_m"], x["p95_offset_m"]) for x in offsets])
    md += ["", "## Heading steered by against the true heading, while driving forward", ""]
    md += pf._table(["profile", "variant", "course", "missions", "median abs deg", "RMS deg"],
                    [(h["profile"], h["variant"], h["course"], h["missions"], h["median_abs_deg"],
                      h["rms_deg"]) for h in headings])
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
    ap.add_argument("--check", help="pace_f.py's runs.jsonl: fly the CHECKED missions again "
                                    "and compare")
    args = ap.parse_args(argv)
    courses = ps._names(args.courses, ps.COURSES, "course")
    profiles = ps._names(args.profiles, PROFILES, "profile")
    variants = ps._names(args.variants, VARIANTS, "variant")
    # measured and v0.13.0's real-rover pilot are always flown: the rest are compared with them.
    profiles = [BASE_PROFILE] + [p for p in profiles if p != BASE_PROFILE]
    variants = [BASE_VARIANT] + [v for v in variants if v != BASE_VARIANT]
    seeds = list(range(args.first_seed, args.first_seed + args.seeds))
    os.makedirs(args.out_dir, exist_ok=True)
    started = time.monotonic()
    check = check_pace_f(args.check) if args.check else None
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
