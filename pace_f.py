#!/usr/bin/env python3
"""pace_f: should --smooth-heading be on by default? Fresh seeds, and rovers it doesn't expect.

pace_c.py, pace_d.py and pace_e.py found --smooth-heading (HeadingSmoother:
gain 0.3, 48 deg/s per unit of angular, 0.5 s lag) slower than the shipped
pilot in none of their groups, and pace_e.py found that without it the pilot
stops learning its compass bias once the compass noise reaches 6 deg. It is
off by default only because no real Mini+ compass has been measured. This
study flies it on fresh seeds against the cases where it could hurt: a rover
that turns slower (32 deg/s) or faster (64 deg/s) than it assumes, commands
that land after 1.0 s instead of 0.5 s, and a compass error of -60 deg instead
of -25, with 3 deg of compass noise and with 8. It also flies 4, 5 and 6 deg
of noise, to find where the shipped learner stops.

    python pace_f.py --out-dir out --first-seed 13 --seeds 24 --check studies/pace-e/runs.jsonl

With --check it first flies seeds 1-3 of pace_e.py's measured and noise6
missions again, shipped and --smooth-heading, and compares each field by field
with pace_e.py's record. Simulated rovers only, so the speeds are upper bounds.
Standard library only. By MV2 of Munim, Inc.; written with AI agents. Apache-2.0.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time

import pace_b as pb
import pace_c as pc
import pace_d as pd
import pace_e as pe
import pace_study as ps
import rover_pilot as rp

__version__ = "0.1.0"

_MEASURED = pb.PROFILES["measured"]
PROFILES = {
    "measured": _MEASURED,
    "noise4": dict(_MEASURED, compass_noise_deg=4.0),
    "noise5": dict(_MEASURED, compass_noise_deg=5.0),
    "noise6": pe.PROFILES["noise6"],
    "yaw32": dict(_MEASURED, max_yaw_dps=32.0),
    "yaw64": dict(_MEASURED, max_yaw_dps=64.0),
    "lag1.0": dict(_MEASURED, latency_s=1.0),
    "yaw32-noise8": dict(_MEASURED, max_yaw_dps=32.0, compass_noise_deg=8.0),
    "yaw64-noise8": dict(_MEASURED, max_yaw_dps=64.0, compass_noise_deg=8.0),
    "bias60": dict(_MEASURED, compass_error_deg=-60.0),
    "bias60-noise8": dict(_MEASURED, compass_error_deg=-60.0, compass_noise_deg=8.0),
}
# The first is the reference every other profile is compared with.
BASE_PROFILE = next(iter(PROFILES))
# The first is the pilot as it ships.
VARIANTS = {"shipped": {}, "cf0.3": {"smooth": rp.SMOOTH_HEADING}}
BASE_VARIANT = next(iter(VARIANTS))
CRUISES = (0.8,)
# pace_e.py flew seeds 1-12; these start after them.
FIRST_SEED = 13
# pace_e.py flew these with the same settings; --check flies them again.
CHECKED = {"profiles": ("measured", "noise6"), "variants": ("shipped", "cf0.3"),
           "seeds": (1, 2, 3)}


def fly(course_name, seed, profile, variant, cruise, course=None):
    """One mission flown as pace_e.fly flies it, on this study's profiles."""
    course = course or ps.COURSES[course_name]
    pts = course["points"]
    sim = pd.DistortedRover([pts[i] for i in course["checkpoints"]], seed=seed, **PROFILES[profile])
    v = VARIANTS[variant]
    smoother = rp.HeadingSmoother(**v["smooth"]) if "smooth" in v else None
    planner = ps.CoursePlanner(course, sim.lat0, sim.lon0)
    errors, offsets = [], []
    next_offset_t = [0.0]
    pilot = None

    def sleep(seconds):
        # Only reads; the mission is the same without it.
        if sim.applied[0] > 0:
            h = pilot._heading_now
            if h is not None:
                errors.append(rp.wrap180(h - sim.heading))
            if sim.t >= next_offset_t[0]:
                offsets.append(pe.course_offset(pts, sim.north, sim.east))
                next_offset_t[0] = sim.t + pe.OFFSET_EVERY_S
        sim.sleep(seconds)

    pilot = rp.Pilot(sim, clock=sim.clock, sleep=sleep,
                     steering=rp.make_steering(False, cruise=cruise), planner=planner,
                     smooth_heading=smoother)
    est = pe.make_estimator(variant)
    pilot.heading = est
    total_m = ps.route_m(course)
    ideal_mps = cruise * sim.max_speed_mps
    res = pilot.run(timeout_s=3.0 * total_m / ideal_mps + 300.0)
    reached = len(res["reached"])
    done_m = ps.route_m(course, upto=reached)
    elapsed = res["elapsed_s"]
    made_good = done_m / elapsed if elapsed else 0.0
    spreads = est.spreads
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
            "offset": pe.offset_stats(offsets)}


def failed_run(exc):
    return {"ok": False, "reason": "%s: %s" % (type(exc).__name__, exc),
            "elapsed_s": None, "reached": 0, "checkpoints": None,
            "reports": 0, "recoveries": 0, "plans": 0, "route_m": 0.0,
            "travelled_m": 0.0, "made_good_mps": 0.0, "ideal_mps": None,
            "efficiency": 0.0, "time_s": {},
            "heading_err": pd.heading_stats([]), "learner": None,
            "offset": pe.offset_stats([])}


def check_pace_e(path):
    """Fly the CHECKED missions again and compare each with pace_e.py's record
    of it (its runs.jsonl): every field pace_e.py recorded must be equal. A
    mission the record lacks is counted as missing and not flown."""
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
            for cruise in CRUISES:
                for course in ps.COURSES:
                    for seed in CHECKED["seeds"]:
                        key = (profile, variant, cruise, course, seed)
                        want = ref.get(key)
                        if want is None:
                            missing += 1
                            continue
                        got = fly(course, seed, profile, variant, cruise)
                        got.update(profile=profile, variant=variant, cruise=cruise,
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


def offset_diffs(offsets):
    """Per (profile, variant, cruise, course): the variant's median distance from
    the course minus the shipped pilot's on the same profile and course (metres)."""
    base = {(o["profile"], o["cruise"], o["course"]): o["median_offset_m"]
            for o in offsets if o["variant"] == BASE_VARIANT}
    rows = []
    for o in offsets:
        b = base.get((o["profile"], o["cruise"], o["course"]))
        if o["variant"] == BASE_VARIANT or b is None or o["median_offset_m"] is None:
            continue
        rows.append({"profile": o["profile"], "variant": o["variant"], "cruise": o["cruise"],
                     "course": o["course"], "diff_m": round(o["median_offset_m"] - b, 2)})
    return rows


def _table(header, rows):
    return (["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
            + ["| " + " | ".join(str(x) for x in row) + " |" for row in rows])


def write_outputs(out_dir, runs, started, seeds, done, check=None):
    s = ps.summarise(runs)
    effects, largest = pc.variant_tallies(runs, s["variant_effect"])
    p_effects, p_tallies = pd.profile_effects(runs)
    headings = pd.heading_rows(runs)
    learner = pe.learner_rows(runs)
    offsets = pe.offset_rows(runs)
    diffs = offset_diffs(offsets)
    result = {"version": __version__, "pace_e": pe.__version__, "pace_d": pd.__version__,
              "pace_c": pc.__version__, "pace_b": pb.__version__, "pace_study": ps.__version__,
              "rover_pilot": rp.__version__, "done": done,
              "elapsed_s": round(time.monotonic() - started, 1), "seeds": seeds,
              "human": {"marathon_m": ps.MARATHON_M, "time_s": ps.HUMAN_S,
                        "mps": round(ps.HUMAN_MPS, 4)},
              "profiles": PROFILES, "variants": VARIANTS, "cruises": list(CRUISES),
              "steering": rp.ROVER_STEERING,
              "runs": len(runs), "completed": sum(1 for r in runs if r["ok"]),
              "overview": s["overview"], "variant_effect": effects, "verdicts": s["verdicts"],
              "largest": largest, "profile_effect": p_effects, "profile_tallies": p_tallies,
              "learner": learner, "offset": offsets, "offset_diff": diffs, "heading": headings,
              "check": check}
    with open(os.path.join(out_dir, "summary.json"), "w") as f:
        json.dump(result, f, indent=1)
    with open(os.path.join(out_dir, "runs.jsonl"), "w") as f:
        for r in runs:
            f.write(json.dumps(r) + "\n")
    md = ["# Should --smooth-heading be on by default? (simulated)", "",
          "pace_f.py %s (pace_e.py %s, pace_d.py %s, rover_pilot.py %s), MV2 of Munim, Inc. "
          "Every profile is pace_b.py's measured Mini+ (orientation every 0.5 s, 48 deg/s, 0.5 s "
          "latency, 3 deg of compass noise, a -25 deg compass error to learn) with one or two "
          "things changed: 4, 5, 6 or 8 deg of noise, a rover turning at 32 or 64 deg/s, commands "
          "landing after 1.0 s, or a -60 deg compass error. Variants: shipped; cf0.3 "
          "(--smooth-heading, which assumes 48 deg/s and 0.5 s). Seeds %s. %d of %d missions "
          "completed. Simulated rovers only, so these speeds are upper bounds."
          % (__version__, pe.__version__, pd.__version__, rp.__version__,
             "%d-%d" % (seeds[0], seeds[-1]) if seeds else "none",
             result["completed"], len(runs)), ""]
    if check is not None:
        md += ["Check against pace_e.py's runs: %d compared, %d identical, %d missing."
               % (check["compared"], check["identical"], check["missing"]), ""]
    md += ["## Overview (courses pooled)", ""]
    md += _table(["profile", "variant", "completed", "made good m/s (median)", "efficiency",
                  "runs beating 0.754", "path ratio"],
                 [(o["profile"], o["variant"], "%d/%d" % (o["completed"], o["runs"]),
                   o["median_made_good_mps"], o["median_efficiency"], o["beat_human_pace"],
                   o["median_path_ratio"]) for o in s["overview"]])
    md += ["", "## --smooth-heading against the shipped pilot, same profile", "",
           "Faster / slower: courses where a paired sign test gives p < 0.05.", ""]
    big = {(x["profile"], x["variant"]): x["largest_median_diff_share"] for x in largest}
    md += _table(["profile", "variant", "faster", "slower", "lost", "gained",
                  "largest median diff"],
                 [(v["profile"], v["variant"], "%d/%d" % (v["groups_faster"], v["groups"]),
                   v["groups_slower"], v["groups_lost"], v["groups_gained"],
                   big.get((v["profile"], v["variant"]))) for v in s["verdicts"]])
    md += [""]
    md += _table(["profile", "variant", "course", "faster", "slower", "median diff s", "share",
                  "p"],
                 [(e["profile"], e["variant"], e["course"], e["faster"], e["slower"],
                   e["median_time_diff_s"], e["median_time_diff_share"], e["sign_test_p"])
                  for e in effects])
    md += ["", "## The learner", ""]
    md += _table(["profile", "variant", "course", "missions", "median calibrations",
                  "missions with none", "fits / mission", "turned down",
                  "median abs bias error deg"],
                 [(x["profile"], x["variant"], x["course"], x["missions"],
                   x["median_calibrations"], x["zero_calibration_missions"],
                   x["fits_per_mission"], x["spread_rejected_share"],
                   x["median_abs_bias_error_deg"]) for x in learner])
    md += ["", "## Distance from the course while driving forward", "",
           "Medians over the completed missions of each mission's median and 95th percentile; "
           "diff is --smooth-heading's median minus the shipped pilot's.", ""]
    diff = {(d["profile"], d["variant"], d["course"]): d["diff_m"] for d in diffs}
    md += _table(["profile", "variant", "course", "missions", "median m", "p95 m", "diff m"],
                 [(x["profile"], x["variant"], x["course"], x["missions"], x["median_offset_m"],
                   x["p95_offset_m"], diff.get((x["profile"], x["variant"], x["course"]), ""))
                  for x in offsets])
    md += ["", "## Heading steered by against the true heading, while driving forward", ""]
    md += _table(["profile", "variant", "course", "missions", "median abs deg", "RMS deg"],
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
    ap.add_argument("--budget-min", type=float, default=150.0)
    ap.add_argument("--courses", help="comma-separated subset of: " + ",".join(ps.COURSES))
    ap.add_argument("--profiles", help="comma-separated subset of: " + ",".join(PROFILES))
    ap.add_argument("--variants", help="comma-separated subset of: " + ",".join(VARIANTS))
    ap.add_argument("--check", help="pace_e.py's runs.jsonl: fly the CHECKED missions again "
                                    "and compare")
    args = ap.parse_args(argv)
    courses = ps._names(args.courses, ps.COURSES, "course")
    profiles = ps._names(args.profiles, PROFILES, "profile")
    variants = ps._names(args.variants, VARIANTS, "variant")
    # measured and the shipped pilot are always flown: everything is compared with them.
    profiles = [BASE_PROFILE] + [p for p in profiles if p != BASE_PROFILE]
    variants = [BASE_VARIANT] + [v for v in variants if v != BASE_VARIANT]
    seeds = list(range(args.first_seed, args.first_seed + args.seeds))
    os.makedirs(args.out_dir, exist_ok=True)
    started = time.monotonic()
    check = check_pace_e(args.check) if args.check else None
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
                      "verdicts": [{k: v[k] for k in ("profile", "groups_faster", "groups_slower",
                                                      "groups_lost")}
                                   for v in result["verdicts"]]}), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
