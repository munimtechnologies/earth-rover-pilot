#!/usr/bin/env python3
"""pace_m: is the compass-bias learner too slow for a drifting compass, or are its fits too noisy?

pace_l.py (studies/pace-l/GRADE.md) found that of the two lies it flew, only
the drifting compass cost the pilot time, also on clear sky, and that it
roughly doubled the median heading error. The pilot's compass-bias learner
(HeadingEstimator) fits a line through the GPS fixes of each straight stretch
of at least min_move_m (10 m), takes course minus mean compass as one
measurement of the bias, and moves its bias `gain` (0.3) of the way to it.
Read from pace-l's own records, two explanations fit: the learner forgets
too slowly to follow the drift, or each fit's measurement is so noisy that
following faster would only add noise. This study flies variants of the
learner that pull those apart, and records how far each measurement the
learner used was from the bias that would really have cancelled the compass
error at that moment (fit_err).

Variants (all v0.16.x's real-rover pilot, pace_k.py's bridge120+cf0.3; only
the learner changes): shipped (gain 0.3, 10 m stretches); gain0.5 (follows
faster); gain0.15 (follows slower); long20 (20 m stretches); long20-g0.5
(both 20 m stretches and gain 0.5).
Profiles: pace_l.py's outage90 (a steady compass error), drift90 and lie90.

    python pace_m.py --out-dir out --first-seed 181 --seeds 24 --check studies/pace-l/runs.jsonl

With --check it first flies seeds 157-159 of pace_l.py's outage90 and lie90
bridge120+cf0.3 missions again as `shipped` and compares each field by field
with pace_l.py's record: the recording only reads. Every mission is flown by
pace_l.fly itself. Simulated rovers only, so the speeds are upper bounds.
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
import pace_k as pk
import pace_l as pl
import pace_study as ps
import rover_pilot as rp

__version__ = "0.1.0"

PROFILES = {name: pl.PROFILES[name] for name in ("outage90", "drift90", "lie90")}
# The first is always flown.
BASE_PROFILE = next(iter(PROFILES))
# (a, b): each variant on profile b against itself on profile a, paired by seed.
PROFILE_PAIRS = (("outage90", "drift90"), ("outage90", "lie90"))
# Every mission is flown as this pace_l.py variant; only the learner differs.
FLOWN_AS = "bridge120+cf0.3"
# HeadingEstimator settings for each variant; the first is the pilot as it ships.
VARIANTS = {
    "shipped": {},
    "gain0.5": {"gain": 0.5},
    "gain0.15": {"gain": 0.15},
    "long20": {"min_move_m": 20.0},
    "long20-g0.5": {"min_move_m": 20.0, "gain": 0.5},
}
BASE_VARIANT = next(iter(VARIANTS))
# (a, b): b against a, paired by seed on every profile and course.
PAIRS = tuple((BASE_VARIANT, v) for v in VARIANTS if v != BASE_VARIANT)
CRUISES = (0.8,)
# pace_l.py flew seeds 157-180; these start after them.
FIRST_SEED = 181
# pace_l.py flew these as bridge120+cf0.3; --check flies them again as shipped.
CHECKED = {"profiles": ("outage90", "lie90"), "variant": BASE_VARIANT,
           "seeds": (157, 158, 159)}


class RecordingEstimator(pe.CountingEstimator):
    """CountingEstimator that also records, for every measurement it used,
    how far that measurement was from the bias truth() says would cancel the
    compass error at that moment (fit_errors, degrees). It decides exactly
    as a CountingEstimator with the same settings."""

    def __init__(self, truth=None, **kw):
        super().__init__(**kw)
        self.truth = truth
        self.fit_errors = []

    def _fit(self, t):
        before, bias0 = self.calibrations, self.bias
        super()._fit(t)
        if self.calibrations == before or self.truth is None or self.weigh:
            return
        if before == 0:
            measured = self.bias
        else:
            # The running update moved the bias `gain` of the way to the
            # measurement, across north the short way; undo it.
            measured = bias0 + rp.wrap180(self.bias - bias0) / self.gain
        self.fit_errors.append(rp.wrap180(measured - self.truth()))


@contextlib.contextmanager
def _learning(variant, seen):
    """While inside, pace_i.fly's learner is a RecordingEstimator with the
    variant's settings, checked against the rover pace_l.fly builds; both
    are put in `seen` ("est", "sim")."""
    settings = VARIANTS[variant]
    saved_rover, saved_est = pl.SlipRover, pe.CountingEstimator

    def rover(*args, **kw):
        sim = saved_rover(*args, **kw)
        seen["sim"] = sim
        return sim

    def estimator():
        # The bias that cancels the rover's compass error now.
        est = RecordingEstimator(truth=lambda: -seen["sim"].compass_error, **settings)
        seen["est"] = est
        return est

    pl.SlipRover, pe.CountingEstimator = rover, estimator
    try:
        yield
    finally:
        pl.SlipRover, pe.CountingEstimator = saved_rover, saved_est


def fly(course_name, seed, profile, variant, cruise, course=None):
    """One mission flown by pace_l.fly as bridge120+cf0.3 with the variant's
    learner; also fit_err, the error of each measurement the learner used."""
    seen = {}
    with _learning(variant, seen):
        r = pl.fly(course_name, seed, profile, FLOWN_AS, cruise, course=course)
    r["fit_err"] = pd.heading_stats(seen["est"].fit_errors if "est" in seen else [])
    return r


def failed_run(exc):
    return dict(pl.failed_run(exc), fit_err=pd.heading_stats([]))


def check_pace_l(path):
    """Fly the CHECKED missions again as shipped and compare each with
    pace_l.py's record of it as bridge120+cf0.3 (its runs.jsonl): every field
    pace_l.py recorded must be equal. A mission the record lacks is counted
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
                    want = ref.get((profile, FLOWN_AS, cruise, course, seed))
                    if want is None:
                        missing += 1
                        continue
                    got = fly(course, seed, profile, CHECKED["variant"], cruise)
                    got.update(profile=profile, variant=FLOWN_AS, cruise=cruise,
                               course=course, seed=seed)
                    got = json.loads(json.dumps(got))
                    compared += 1
                    fields = sorted(k for k in want if got.get(k) != want[k])
                    if fields:
                        different.append({"profile": profile, "cruise": cruise,
                                          "course": course, "seed": seed, "fields": fields})
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


def fit_rows(runs):
    """Per (profile, variant, cruise, course), over the completed missions with
    at least one measurement: the median measurements a mission, and the median
    of each mission's median |fit error| and of its RMS."""
    rows = []
    for k, rs in sorted(pg._groups(runs).items()):
        fs = [r["fit_err"] for r in rs if r["ok"] and r.get("fit_err", {}).get("n")]
        if not fs:
            continue
        rows.append({"profile": k[0], "variant": k[1], "cruise": k[2], "course": k[3],
                     "missions": len(fs), "median_fits": ps._median([x["n"] for x in fs]),
                     "median_abs_deg": ps._median([x["median_abs_deg"] for x in fs], 2),
                     "rms_deg": ps._median([x["rms_deg"] for x in fs], 2)})
    return rows


def write_outputs(out_dir, runs, started, seeds, done, check=None):
    s = ps.summarise(runs)
    effects, tallies = pair_effects(runs)
    p_effects, p_tallies = profile_effects(runs)
    headings = pd.heading_rows(runs)
    fits = fit_rows(runs)
    learners = pe.learner_rows(runs)
    outages = pi.outage_rows(runs)
    positions = pg.position_rows(runs)
    offsets = pe.offset_rows(runs)
    steering = ph.steer_rows(runs)
    result = {"version": __version__, "pace_l": pl.__version__, "pace_k": pk.__version__,
              "pace_j": pj.__version__, "pace_i": pi.__version__, "pace_e": pe.__version__,
              "pace_d": pd.__version__, "pace_study": ps.__version__,
              "rover_pilot": rp.__version__, "dead_reckon": dr.__version__, "done": done,
              "elapsed_s": round(time.monotonic() - started, 1), "seeds": seeds,
              "human": {"marathon_m": ps.MARATHON_M, "time_s": ps.HUMAN_S,
                        "mps": round(ps.HUMAN_MPS, 4)},
              "profiles": PROFILES, "flown_as": FLOWN_AS, "flown_as_settings": pl.VARIANTS[FLOWN_AS],
              "variants": VARIANTS, "pairs": [list(x) for x in PAIRS],
              "profile_pairs": [list(x) for x in PROFILE_PAIRS], "cruises": list(CRUISES),
              "runs": len(runs), "completed": sum(1 for r in runs if r["ok"]),
              "overview": s["overview"], "pair_effect": effects, "verdicts": tallies,
              "profile_effect": p_effects, "profile_verdicts": p_tallies,
              "heading": headings, "fit": fits, "learner": learners, "outage": outages,
              "position": positions, "offset": offsets, "steer": steering, "check": check}
    with open(os.path.join(out_dir, "summary.json"), "w") as f:
        json.dump(result, f, indent=1)
    with open(os.path.join(out_dir, "runs.jsonl"), "w") as f:
        for r in runs:
            f.write(json.dumps(r) + "\n")
    md = ["# Is the compass-bias learner too slow for a drifting compass, or are its fits "
          "too noisy? (simulated)",
          "",
          "pace_m.py %s (pace_l.py %s, rover_pilot.py %s, dead_reckon.py %s), MV2 of Munim, Inc. "
          "Every mission is pace_l.py's bridge120+cf0.3 (v0.16.x on a real rover) on pace_l.py's "
          "outage90 (90 s GPS outages, a steady compass error), drift90 (the compass error "
          "drifts, SD 10 deg, 120 s time constant) or lie90 (drift and wheel slip); only the "
          "compass-bias learner changes: shipped (gain 0.3, 10 m stretches), gain0.5, gain0.15, "
          "long20 (20 m stretches) and long20-g0.5. Seeds %s. %d of %d missions completed. "
          "Simulated rovers only, so these speeds are upper bounds."
          % (__version__, pl.__version__, rp.__version__, dr.__version__,
             "%d-%d" % (seeds[0], seeds[-1]) if seeds else "none",
             result["completed"], len(runs)), ""]
    if check is not None:
        md += ["Check against pace_l.py's runs: %d compared, %d identical, %d missing."
               % (check["compared"], check["identical"], check["missing"]), ""]
    md += ["## Overview (courses pooled)", ""]
    md += pf._table(["profile", "variant", "completed", "made good m/s (median)", "efficiency",
                     "runs beating 0.754", "path ratio", "share stopped"],
                    [(o["profile"], o["variant"], "%d/%d" % (o["completed"], o["runs"]),
                      o["median_made_good_mps"], o["median_efficiency"], o["beat_human_pace"],
                      o["median_path_ratio"], o["share_stopped"]) for o in s["overview"]])
    md += ["", "## Each learner against the shipped one, same profile", "",
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
    md += ["", "## What the drift costs each learner", ""]
    md += pf._table(["variant", "profile", "against", "faster", "slower", "lost", "gained",
                     "largest median diff"],
                    [(t["variant"], t["profile"], t["against"],
                      "%d/%d" % (t["groups_faster"], t["groups"]), t["groups_slower"],
                      t["groups_lost"], t["groups_gained"], t["largest_median_diff_share"])
                     for t in p_tallies])
    md += [""]
    md += pf._table(["variant", "profile", "against", "course", "faster", "slower",
                     "median diff s", "share", "p"],
                    [(e["variant"], e["profile"], e["against"], e["course"], e["faster"],
                      e["slower"], e["median_time_diff_s"], e["median_time_diff_share"],
                      e["sign_test_p"]) for e in p_effects])
    md += ["", "## Heading error", ""]
    md += pf._table(["profile", "variant", "course", "missions", "median abs deg", "rms deg"],
                    [(x["profile"], x["variant"], x["course"], x["missions"],
                      x["median_abs_deg"], x["rms_deg"]) for x in headings])
    md += ["", "## Error of each measurement the learner used", ""]
    md += pf._table(["profile", "variant", "course", "missions", "measurements",
                     "median abs deg", "rms deg"],
                    [(x["profile"], x["variant"], x["course"], x["missions"], x["median_fits"],
                      x["median_abs_deg"], x["rms_deg"]) for x in fits])
    md += ["", "## The learner", ""]
    md += pf._table(["profile", "variant", "course", "missions", "calibrations",
                     "stretches broken off", "abs bias error at the end"],
                    [(x["profile"], x["variant"], x["course"], x["missions"],
                      x["median_calibrations"], x["median_breaks"],
                      x["median_abs_bias_error_deg"]) for x in learners])
    md += ["", "## Where the pilot thinks it is, against where it is", ""]
    md += pf._table(["profile", "variant", "course", "missions", "median m", "p95 m"],
                    [(x["profile"], x["variant"], x["course"], x["missions"],
                      x["median_position_err_m"], x["p95_position_err_m"]) for x in positions])
    md += ["", "## Distance from the course while driving forward", ""]
    md += pf._table(["profile", "variant", "course", "missions", "median m", "p95 m"],
                    [(x["profile"], x["variant"], x["course"], x["missions"],
                      x["median_offset_m"], x["p95_offset_m"]) for x in offsets])
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
    ap.add_argument("--check", help="pace_l.py's runs.jsonl: fly the CHECKED missions again "
                                    "and compare")
    args = ap.parse_args(argv)
    courses = ps._names(args.courses, ps.COURSES, "course")
    profiles = ps._names(args.profiles, PROFILES, "profile")
    variants = ps._names(args.variants, VARIANTS, "variant")
    # outage90 and the shipped learner are always flown: the rest are compared with them.
    profiles = [BASE_PROFILE] + [p for p in profiles if p != BASE_PROFILE]
    variants = [BASE_VARIANT] + [v for v in variants if v != BASE_VARIANT]
    seeds = list(range(args.first_seed, args.first_seed + args.seeds))
    os.makedirs(args.out_dir, exist_ok=True)
    started = time.monotonic()
    check = check_pace_l(args.check) if args.check else None
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
