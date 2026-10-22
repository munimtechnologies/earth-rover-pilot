#!/usr/bin/env python3
"""pace_e: why the pilot's compass-bias learner goes quiet under noise, and what that costs.

pace_d.py (studies/pace-d/GRADE.md) found that with 10 deg of fresh compass
noise the shipped pilot steered with its whole -25 deg compass error: the bias
learner (HeadingEstimator) never calibrated. Under a slow drift it took out
almost none of the drift. Two of the learner's gates sit close to 10 deg of
noise: a stretch counts as straight only while the low-passed angular command
stays within +-0.1 (max_angular), and a fitted stretch is used only if its
compass readings agree (max_spread 0.985). This study counts what the learner
does in every mission (stretches broken off, fits that reach the spread test,
fits it turns down, calibrations), and measures how far the simulated rover
really drives from its course.

Profiles: pace_b.py's measured Mini+ with 3 (measured), 6, 8, 10
(measured-noise10) and 12 deg of compass noise, and pace_d.py's drift10.
Variants: shipped; cf0.3 (--smooth-heading); spread0.95 (max_spread 0.95);
straight0.3 (max_angular 0.3); both (the two together). Cruise 0.8.

    python pace_e.py --out-dir out --seeds 12 --check studies/pace-d/runs.jsonl

With --check, every shipped and cf0.3 mission on measured, measured-noise10
and drift10 must come out exactly as pace_d.py recorded it: the counting only
reads. Simulated rovers only, so the speeds are upper bounds. Standard library
only. By MV2 of Munim, Inc.; written with AI agents. Apache-2.0.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import statistics
import sys
import time

import pace_b as pb
import pace_c as pc
import pace_d as pd
import pace_study as ps
import rover_pilot as rp

__version__ = "0.1.0"


class CountingEstimator(rp.HeadingEstimator):
    """HeadingEstimator that counts what it does; it decides exactly as one.

    breaks: straight stretches cut off by a turn or by slowing down; fits:
    stretches long enough to fit; spread_checked: fits that reached the
    compass-spread test; spread_rejected: those it turned down; spreads: each
    checked fit's mean resultant length (1 = every reading the same)."""

    def __init__(self, **kw):
        super().__init__(**kw)
        self.breaks = 0
        self.fits = 0
        self.spread_checked = 0
        self.spread_rejected = 0
        self.spreads = []

    def update(self, t, new_fix, compass, linear, angular):
        was_straight = self._straight_since is not None
        super().update(t, new_fix, compass, linear, angular)
        if was_straight and self._straight_since is None:
            self.breaks += 1

    def _fit(self, t):
        self.fits += 1
        n = self._n
        spread = math.hypot(self._sin, self._cos) / n if n else None
        rejected_before = self.rejected_fits
        super()._fit(t)
        # It reached the spread test if the line fit set a course, there were
        # compass readings, and the residual gate (off by default) let it by.
        if self.last_course_t == t and n and self.rejected_fits == rejected_before:
            self.spread_checked += 1
            self.spreads.append(spread)
            if spread < self.max_spread:
                self.spread_rejected += 1


_MEASURED = pb.PROFILES["measured"]
PROFILES = {
    "measured": pb.PROFILES["measured"],
    "noise6": dict(_MEASURED, compass_noise_deg=6.0),
    "noise8": dict(_MEASURED, compass_noise_deg=8.0),
    "measured-noise10": pb.PROFILES["measured-noise10"],
    "noise12": dict(_MEASURED, compass_noise_deg=12.0),
    "drift10": pd.PROFILES["drift10"],
}
# The first is the reference every other profile is compared with.
BASE_PROFILE = next(iter(PROFILES))
# The first is the pilot as it ships.
VARIANTS = {
    "shipped": {},
    "cf0.3": {"smooth": rp.SMOOTH_HEADING},
    "spread0.95": {"estimator": {"max_spread": 0.95}},
    "straight0.3": {"estimator": {"max_angular": 0.3}},
    "both": {"estimator": {"max_spread": 0.95, "max_angular": 0.3}},
}
BASE_VARIANT = next(iter(VARIANTS))
CRUISES = (0.8,)
# pace_d.py flew these, and its runs.jsonl is the reference for --check.
CHECKED = {"profiles": ("measured", "measured-noise10", "drift10"),
           "variants": ("shipped", "cf0.3")}
OFFSET_EVERY_S = 1.0


def make_estimator(variant):
    return CountingEstimator(**VARIANTS[variant].get("estimator", {}))


def course_offset(points, north, east):
    """How far (north, east) is from the course: the distance to its nearest segment."""
    return min(ps._seg_dist((north, east), a, b) for a, b in zip(points, points[1:]))


def offset_stats(offsets):
    """Distance from the course, sampled while driving forward (metres)."""
    if not offsets:
        return {"n": 0, "median_m": None, "p95_m": None, "max_m": None}
    s = sorted(offsets)
    return {"n": len(s), "median_m": round(statistics.median(s), 2),
            "p95_m": round(s[int(0.95 * (len(s) - 1))], 2), "max_m": round(s[-1], 2)}


def fly(course_name, seed, profile, variant, cruise, course=None):
    """One mission: pace_d.fly's fields, the learner's counts and the offset."""
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
                offsets.append(course_offset(pts, sim.north, sim.east))
                next_offset_t[0] = sim.t + OFFSET_EVERY_S
        sim.sleep(seconds)

    pilot = rp.Pilot(sim, clock=sim.clock, sleep=sleep,
                     steering=rp.make_steering(False, cruise=cruise), planner=planner,
                     smooth_heading=smoother)
    est = make_estimator(variant)
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
                        "median_spread": (round(statistics.median(spreads), 4)
                                          if spreads else None),
                        "bias_deg": round(est.bias, 2),
                        # The bias that would cancel the compass error at the end.
                        "bias_error_deg": round(rp.wrap180(est.bias + sim.compass_error), 2)},
            "offset": offset_stats(offsets)}


def _groups(runs):
    groups = {}
    for r in runs:
        groups.setdefault((r["profile"], r["variant"], r["cruise"], r["course"]), []).append(r)
    return groups


def learner_rows(runs):
    """Per (profile, variant, cruise, course), over the completed missions: the
    median calibrations, missions with none, fits and spread checks per mission,
    the share of checked fits the spread test turned down, the median spread,
    the median stretches broken off, and the median |bias error| at the end."""
    rows = []
    for k, rs in sorted(_groups(runs).items()):
        ls = [r["learner"] for r in rs if r["ok"] and r.get("learner")]
        checked = sum(x["spread_checked"] for x in ls)
        spreads = [x["median_spread"] for x in ls if x["median_spread"] is not None]
        rows.append({"profile": k[0], "variant": k[1], "cruise": k[2], "course": k[3],
                     "missions": len(ls),
                     "median_calibrations": ps._median([x["calibrations"] for x in ls]),
                     "zero_calibration_missions": sum(1 for x in ls if x["calibrations"] == 0),
                     "fits_per_mission": (round(sum(x["fits"] for x in ls) / len(ls), 2)
                                          if ls else None),
                     "spread_checked_per_mission": round(checked / len(ls), 2) if ls else None,
                     "spread_rejected_share": (round(sum(x["spread_rejected"] for x in ls)
                                                     / checked, 4) if checked else None),
                     "median_spread": ps._median(spreads, 4),
                     "median_breaks": ps._median([x["breaks"] for x in ls]),
                     "median_abs_bias_error_deg": ps._median(
                         [abs(x["bias_error_deg"]) for x in ls], 2)})
    return rows


def offset_rows(runs):
    """Per (profile, variant, cruise, course): over the completed missions, the
    median of each mission's median and 95th-percentile distance from the course."""
    rows = []
    for k, rs in sorted(_groups(runs).items()):
        os_ = [r["offset"] for r in rs if r["ok"] and r.get("offset", {}).get("n")]
        rows.append({"profile": k[0], "variant": k[1], "cruise": k[2], "course": k[3],
                     "missions": len(os_),
                     "median_offset_m": ps._median([o["median_m"] for o in os_], 2),
                     "p95_offset_m": ps._median([o["p95_m"] for o in os_], 2)})
    return rows


def check_against(runs, path):
    """Each CHECKED mission against pace_d.py's record of the same one (its
    runs.jsonl): every field pace_d.py recorded must be equal."""
    ref = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                r = json.loads(line)
                ref[(r["profile"], r["variant"], r["cruise"], r["course"], r["seed"])] = r
    compared = missing = 0
    different = []
    for r in runs:
        if r["profile"] not in CHECKED["profiles"] or r["variant"] not in CHECKED["variants"]:
            continue
        key = (r["profile"], r["variant"], r["cruise"], r["course"], r["seed"])
        want = ref.get(key)
        if want is None:
            missing += 1
            continue
        got = json.loads(json.dumps(r))
        compared += 1
        fields = sorted(k for k in want if got.get(k) != want[k])
        if fields:
            different.append({"profile": key[0], "variant": key[1], "cruise": key[2],
                              "course": key[3], "seed": key[4], "fields": fields})
    return {"reference": path, "compared": compared, "identical": compared - len(different),
            "missing": missing, "different": different[:20]}


def write_outputs(out_dir, runs, started, args, done, check=None):
    s = ps.summarise(runs)
    effects, largest = pc.variant_tallies(runs, s["variant_effect"])
    p_effects, p_tallies = pd.profile_effects(runs)
    headings = pd.heading_rows(runs)
    learner = learner_rows(runs)
    offsets = offset_rows(runs)
    result = {"version": __version__, "pace_d": pd.__version__, "pace_c": pc.__version__,
              "pace_b": pb.__version__, "pace_study": ps.__version__,
              "rover_pilot": rp.__version__, "done": done,
              "elapsed_s": round(time.monotonic() - started, 1), "seeds": args.seeds,
              "human": {"marathon_m": ps.MARATHON_M, "time_s": ps.HUMAN_S,
                        "mps": round(ps.HUMAN_MPS, 4)},
              "profiles": PROFILES, "variants": VARIANTS, "cruises": list(CRUISES),
              "steering": rp.ROVER_STEERING,
              "runs": len(runs), "completed": sum(1 for r in runs if r["ok"]),
              "overview": s["overview"], "variant_effect": effects, "verdicts": s["verdicts"],
              "largest": largest, "profile_effect": p_effects, "profile_tallies": p_tallies,
              "learner": learner, "offset": offsets, "heading": headings, "check": check}
    with open(os.path.join(out_dir, "summary.json"), "w") as f:
        json.dump(result, f, indent=1)
    with open(os.path.join(out_dir, "runs.jsonl"), "w") as f:
        for r in runs:
            f.write(json.dumps(r) + "\n")
    md = ["# What the compass-bias learner does under noise (simulated)", "",
          "pace_e.py %s (pace_d.py %s, pace_c.py %s, pace_b.py %s, pace_study.py %s, "
          "rover_pilot.py %s), MV2 of Munim, Inc. Every profile is pace_b.py's measured Mini+ "
          "(orientation every 0.5 s, 48 deg/s, 0.5 s latency, a -25 deg compass error to learn) "
          "with 3, 6, 8, 10 or 12 deg of compass noise, or pace_d.py's drift10. Variants: "
          "shipped; cf0.3 (--smooth-heading); spread0.95, straight0.3 and both (the learner's "
          "gates loosened). Seeds 1-%d. %d of %d missions completed. Simulated rovers only, so "
          "these speeds are upper bounds."
          % (__version__, pd.__version__, pc.__version__, pb.__version__, ps.__version__,
             rp.__version__, args.seeds, result["completed"], len(runs)), ""]
    if check is not None:
        md += ["Check against pace_d.py's runs: %d compared, %d identical, %d missing."
               % (check["compared"], check["identical"], check["missing"]), ""]
    md += ["## Overview (courses pooled)", "",
           "| profile | variant | cruise | completed | made good m/s (median) | efficiency | "
           "runs beating 0.754 | path ratio |",
           "|---|---|---|---|---|---|---|---|"]
    md += ["| %s | %s | %g | %d/%d | %s | %s | %d | %s |"
           % (o["profile"], o["variant"], o["cruise"], o["completed"], o["runs"],
              o["median_made_good_mps"], o["median_efficiency"], o["beat_human_pace"],
              o["median_path_ratio"])
           for o in s["overview"]]
    md += ["", "## The learner", "",
           "Per mission: calibrations (fits it used), stretches broken off, fits that reached "
           "the spread test; the share of those it turned down; the median spread of a checked "
           "fit; and |bias error| at the end (0 = the compass error fully cancelled).", "",
           "| profile | variant | course | missions | median calibrations | missions with none | "
           "fits / mission | spread checks / mission | turned down | median spread | "
           "median breaks | median abs bias error deg |",
           "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    md += ["| %s | %s | %s | %d | %s | %d | %s | %s | %s | %s | %s | %s |"
           % (x["profile"], x["variant"], x["course"], x["missions"], x["median_calibrations"],
              x["zero_calibration_missions"], x["fits_per_mission"],
              x["spread_checked_per_mission"], x["spread_rejected_share"], x["median_spread"],
              x["median_breaks"], x["median_abs_bias_error_deg"])
           for x in learner]
    md += ["", "## Distance from the course while driving forward", "",
           "Medians over the completed missions of each mission's median and 95th percentile.", "",
           "| profile | variant | course | missions | median m | p95 m |",
           "|---|---|---|---|---|---|"]
    md += ["| %s | %s | %s | %d | %s | %s |"
           % (x["profile"], x["variant"], x["course"], x["missions"], x["median_offset_m"],
              x["p95_offset_m"])
           for x in offsets]
    md += ["", "## Each variant against the shipped pilot, same profile", "",
           "Faster / slower: courses where a paired sign test gives p < 0.05.", "",
           "| profile | variant | faster | slower | lost | gained | largest median diff |",
           "|---|---|---|---|---|---|---|"]
    big = {(x["profile"], x["variant"]): x["largest_median_diff_share"] for x in largest}
    md += ["| %s | %s | %d/%d | %d | %d | %d | %s |"
           % (v["profile"], v["variant"], v["groups_faster"], v["groups"], v["groups_slower"],
              v["groups_lost"], v["groups_gained"], big.get((v["profile"], v["variant"])))
           for v in s["verdicts"]]
    md += ["", "| profile | variant | cruise | course | faster | slower | median diff s | share | p |",
           "|---|---|---|---|---|---|---|---|---|"]
    md += ["| %s | %s | %g | %s | %d | %d | %s | %s | %s |"
           % (e["profile"], e["variant"], e["cruise"], e["course"], e["faster"], e["slower"],
              e["median_time_diff_s"], e["median_time_diff_share"], e["sign_test_p"])
           for e in effects]
    md += ["", "## Heading steered by against the true heading, while driving forward", "",
           "| profile | variant | course | missions | median abs deg | RMS deg |",
           "|---|---|---|---|---|---|"]
    md += ["| %s | %s | %s | %d | %s | %s |"
           % (h["profile"], h["variant"], h["course"], h["missions"], h["median_abs_deg"],
              h["rms_deg"])
           for h in headings]
    with open(os.path.join(out_dir, "report.md"), "w") as f:
        f.write("\n".join(md) + "\n")
    return result


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out-dir", default="out")
    ap.add_argument("--seeds", type=int, default=12)
    ap.add_argument("--budget-min", type=float, default=150.0)
    ap.add_argument("--courses", help="comma-separated subset of: " + ",".join(ps.COURSES))
    ap.add_argument("--profiles", help="comma-separated subset of: " + ",".join(PROFILES))
    ap.add_argument("--variants", help="comma-separated subset of: " + ",".join(VARIANTS))
    ap.add_argument("--cruises", help="comma-separated cruise commands (default 0.8)")
    ap.add_argument("--check", help="pace_d.py's runs.jsonl: the CHECKED missions must match it")
    args = ap.parse_args(argv)
    courses = ps._names(args.courses, ps.COURSES, "course")
    profiles = ps._names(args.profiles, PROFILES, "profile")
    variants = ps._names(args.variants, VARIANTS, "variant")
    # measured and the shipped pilot are always flown: everything is compared with them.
    profiles = [BASE_PROFILE] + [p for p in profiles if p != BASE_PROFILE]
    variants = [BASE_VARIANT] + [v for v in variants if v != BASE_VARIANT]
    cruises = ([float(x) for x in args.cruises.split(",") if x.strip()]
               if args.cruises else list(CRUISES))
    os.makedirs(args.out_dir, exist_ok=True)
    started = time.monotonic()
    runs = []
    done = True
    for profile in profiles:
        for variant in variants:
            if time.monotonic() - started > args.budget_min * 60.0:
                done = False
                break
            for cruise in cruises:
                for course in courses:
                    for seed in range(1, args.seeds + 1):
                        try:
                            r = fly(course, seed, profile, variant, cruise)
                        except Exception as exc:
                            r = {"ok": False, "reason": "%s: %s" % (type(exc).__name__, exc),
                                 "elapsed_s": None, "reached": 0, "checkpoints": None,
                                 "reports": 0, "recoveries": 0, "plans": 0, "route_m": 0.0,
                                 "travelled_m": 0.0, "made_good_mps": 0.0, "ideal_mps": None,
                                 "efficiency": 0.0, "time_s": {},
                                 "heading_err": pd.heading_stats([]), "learner": None,
                                 "offset": offset_stats([])}
                        r.update(profile=profile, variant=variant, cruise=cruise,
                                 course=course, seed=seed)
                        runs.append(r)
            print("%s / %s: %d runs so far, %.0f s"
                  % (profile, variant, len(runs), time.monotonic() - started), flush=True)
            write_outputs(args.out_dir, runs, started, args, False)
        if not done:
            break
    check = check_against(runs, args.check) if args.check else None
    result = write_outputs(args.out_dir, runs, started, args, done, check)
    print(json.dumps({"check": None if check is None else
                      {k: check[k] for k in ("compared", "identical", "missing")},
                      "learner": [{k: x[k] for k in ("profile", "variant", "course",
                                                     "median_calibrations",
                                                     "spread_checked_per_mission")}
                                  for x in result["learner"]]}), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
