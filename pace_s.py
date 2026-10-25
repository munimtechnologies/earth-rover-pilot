#!/usr/bin/env python3
"""pace_s: should the GPS average start again after a gap?

trace_r.py (studies/pace-r/TRACE.md) found that GpsFilter, as it ships,
keeps its exponential average through a GPS outage and blends the first fix
after it with the average from before it. After 90 s without fixes the
pilot's idea of its position jumped about 57 m back along the course, and
came within 10 m of the rover again only about 19 s later. pace_r.py's
record shows a jump like it (a largest position error over 20 m) in 65 of
the shipped pilot's 72 outage90 missions. The jump check does not stop it,
because the jump it allows grows with the time since the last fix (3 m/s
for about 92 s, plus 10 m, is about 290 m).

Variants (all v0.18.2's real-rover pilot as pace_q.py flies it, with a 16 m
lookahead; only the GPS filter changes):
  a0.3     GpsFilter as it ships
  restart  the same average, started again from the fix after more than
           3 s (GpsFilter's max_age_s) without a valid reading: pace_q.py's
           TrackingGpsFilter with beta 0, which is otherwise GpsFilter
Profiles: pace_q.py's outage90, quiet90 and quietdrift90, and quiet45
(pace_l.py's outage45, 45 s outages after a mean of 300 s of sky, with
0.22 m of GPS noise).

    python pace_s.py --out-dir out --first-seed 325 --seeds 24 --check studies/pace-r/runs.jsonl

With --check it first flies seeds 311-313 of pace_r.py's outage90 and
quiet90 a0.3-16 missions again as a0.3 and compares each field by field
with the record. Simulated rovers only, so the speeds are upper bounds.
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
import pace_n as pn
import pace_o as po
import pace_p as pp
import pace_q as pq
import pace_study as ps
import rover_pilot as rp

__version__ = "0.1.0"

PROFILES = {
    "outage90": pq.PROFILES["outage90"],
    "quiet90": pq.PROFILES["quiet90"],
    "quietdrift90": pq.PROFILES["quietdrift90"],
    "quiet45": dict(pl.PROFILES["outage45"], gps_noise_m=pq.QUIET_NOISE_M),
}
# The first is always flown.
BASE_PROFILE = next(iter(PROFILES))
# (a, b): each variant on profile b against itself on profile a, paired by
# seed: what quieter fixes are worth, what a drifting compass costs, and
# what twice as long an outage costs.
PROFILE_PAIRS = (("outage90", "quiet90"), ("quiet90", "quietdrift90"), ("quiet45", "quiet90"))
# The GPS filter for each variant, as pace_q._filtering builds it: GpsFilter
# with alpha, or with track a TrackingGpsFilter. With beta 0 its velocity
# stays 0, so it is GpsFilter except that it starts again from the fix after
# more than max_age_s (3 s) without a valid reading.
VARIANTS = {
    "a0.3": {"alpha": 0.3},
    "restart": {"alpha": 0.3, "beta": 0.0, "track": True},
}
# The pilot as it ships; it is always flown.
BASE_VARIANT = next(iter(VARIANTS))
PAIRS = (("a0.3", "restart"),)
CRUISES = (0.8,)
# pace_r.py flew seeds 301-324; these start after them.
FIRST_SEED = 325
# --check: pace_r.py's a0.3-16 flown again as a0.3. Seed 313 is the boulevard
# mission trace_r.py traced. (ours, theirs).
CHECKED = {"profiles": ("outage90", "quiet90"), "variants": (("a0.3", "a0.3-16"),),
           "seeds": (311, 312, 313)}
# A mission whose largest position error is over this has had its estimate
# thrown off by more than any lag or reckoning drift seen without the jump
# (at most 17.6 m in pace_r.py's shipped missions that had none).
SNAP_M = 20.0


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


def fly(course_name, seed, profile, variant, cruise, course=None):
    """One mission flown by pace_p.fly as keep16 with the variant's GPS
    filter, as pace_q.fly flies it, with its records; also the gps record:
    how many filters the pilot built and, for restart, how often it started
    again."""
    v = VARIANTS[variant]
    made = []
    with _known_profile(profile), pq._filtering(v, made):
        r = pp.fly(course_name, seed, profile, pq.FLOWN_AS, cruise, course=course)
    r["gps"] = {"filters": len(made),
                "restarts": sum(f.restarts for f in made) if v.get("track") else None}
    return r


def failed_run(exc):
    return pq.failed_run(exc)


def check(path, checked=CHECKED):
    """Fly the `checked` missions again and compare each with the record of
    it in `path` (a runs.jsonl): every field the record has must be equal. A
    mission the record lacks is counted as missing and not flown."""
    ref = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                r = json.loads(line)
                ref[(r["profile"], r["variant"], r["cruise"], r["course"], r["seed"])] = r
    compared = missing = 0
    different = []
    for profile in checked["profiles"]:
        for ours, theirs in checked["variants"]:
            for cruise in CRUISES:
                for course in ps.COURSES:
                    for seed in checked["seeds"]:
                        want = ref.get((profile, theirs, cruise, course, seed))
                        if want is None:
                            missing += 1
                            continue
                        got = fly(course, seed, profile, ours, cruise)
                        got.update(profile=profile, variant=theirs, cruise=cruise,
                                   course=course, seed=seed)
                        got = json.loads(json.dumps(got))
                        compared += 1
                        fields = sorted(k for k in want if got.get(k) != want[k])
                        if fields:
                            different.append({"profile": profile, "variant": ours,
                                              "against": theirs, "cruise": cruise,
                                              "course": course, "seed": seed,
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


def worst_rows(runs):
    """Per (profile, variant, cruise, course), over the completed missions: the
    median and the largest of each mission's largest position error, and how
    many missions had one over SNAP_M."""
    rows = []
    for k, rs in sorted(pg._groups(runs).items()):
        xs = [(r.get("position_err") or {}).get("max_m") for r in rs if r["ok"]]
        xs = [x for x in xs if x is not None]
        rows.append({"profile": k[0], "variant": k[1], "cruise": k[2], "course": k[3],
                     "missions": len(xs), "median_max_m": ps._median(xs, 2),
                     "largest_m": max(xs) if xs else None,
                     "over_snap": sum(1 for x in xs if x > SNAP_M)})
    return rows


def _check_line(c):
    return ("Check against pace_r.py's runs: %d compared, %d identical, %d missing."
            % (c["compared"], c["identical"], c["missing"]))


def write_outputs(out_dir, runs, started, seeds, done, check_r=None):
    s = ps.summarise(runs)
    effects, tallies = pair_effects(runs)
    p_effects, p_tallies = profile_effects(runs)
    gps = pq.gps_rows(runs)
    worst = worst_rows(runs)
    context = po.context_rows(runs)
    corner = pn.corner_rows(runs)
    maxes = pn.offset_max_rows(runs)
    offsets = pe.offset_rows(runs)
    headings_ = pd.heading_rows(runs)
    positions = pg.position_rows(runs)
    steering = ph.steer_rows(runs)
    result = {"version": __version__, "pace_q": pq.__version__, "pace_p": pp.__version__,
              "pace_o": po.__version__, "pace_n": pn.__version__, "pace_study": ps.__version__,
              "rover_pilot": rp.__version__, "dead_reckon": dr.__version__, "done": done,
              "elapsed_s": round(time.monotonic() - started, 1), "seeds": seeds,
              "human": {"marathon_m": ps.MARATHON_M, "time_s": ps.HUMAN_S,
                        "mps": round(ps.HUMAN_MPS, 4)},
              "profiles": PROFILES, "quiet_noise_m": pq.QUIET_NOISE_M,
              "flown_as": pq.FLOWN_AS, "variants": VARIANTS, "pairs": [list(x) for x in PAIRS],
              "profile_pairs": [list(x) for x in PROFILE_PAIRS], "cruises": list(CRUISES),
              "snap_m": SNAP_M, "corner_deg": pn.CORNER_DEG, "corner_m": pn.CORNER_M,
              "far_m": po.FAR_M, "runs": len(runs),
              "completed": sum(1 for r in runs if r["ok"]),
              "overview": s["overview"], "pair_effect": effects, "verdicts": tallies,
              "profile_effect": p_effects, "profile_verdicts": p_tallies, "gps": gps,
              "worst": worst, "position": positions, "corner": corner, "offset": offsets,
              "offset_max": maxes, "context": context, "heading": headings_,
              "steer": steering, "check": check_r}
    with open(os.path.join(out_dir, "summary.json"), "w") as f:
        json.dump(result, f, indent=1)
    with open(os.path.join(out_dir, "runs.jsonl"), "w") as f:
        for r in runs:
            f.write(json.dumps(r) + "\n")
    md = ["# Should the GPS average start again after a gap? (simulated)",
          "",
          "pace_s.py %s (pace_q.py %s, pace_p.py %s, rover_pilot.py %s, dead_reckon.py %s), MV2 "
          "of Munim, Inc. Every mission is v0.18.2's real-rover pilot as pace_q.py flies it "
          "(pace_p.py's keep16: pace_m.py's long20 learner on pace_l.py's bridge120+cf0.3, "
          "pace_o.py's keep planner and a 16 m lookahead) with GpsFilter as it ships (a0.3) or "
          "the same average started again from the fix after more than 3 s without one "
          "(restart). Profiles: outage90 (90 s GPS outages, a steady compass error, 1.5 m of GPS "
          "noise per axis), quiet90 (the same with %g m), quietdrift90 (a drifting compass with "
          "%g m) and quiet45 (45 s outages with %g m). Seeds %s. %d of %d missions completed. "
          "Simulated rovers only, so these speeds are upper bounds."
          % (__version__, pq.__version__, pp.__version__, rp.__version__, dr.__version__,
             pq.QUIET_NOISE_M, pq.QUIET_NOISE_M, pq.QUIET_NOISE_M,
             "%d-%d" % (seeds[0], seeds[-1]) if seeds else "none",
             result["completed"], len(runs)), ""]
    if check_r is not None:
        md += [_check_line(check_r), ""]
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
    md += ["", "## The pilot's worst idea of where it is, per mission (over %g m: thrown off)"
           % SNAP_M, ""]
    md += pf._table(["profile", "variant", "course", "missions", "median of max m",
                     "largest m", "missions over %g m" % SNAP_M],
                    [(x["profile"], x["variant"], x["course"], x["missions"],
                      x["median_max_m"], x["largest_m"], x["over_snap"]) for x in worst])
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
    ap.add_argument("--check", help="pace_r.py's runs.jsonl: fly CHECKED again and compare")
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
    check_r = check(args.check) if args.check else None
    if check_r is not None:
        print(_check_line(check_r), flush=True)
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
            write_outputs(args.out_dir, runs, started, seeds, False, check_r)
        if not done:
            break
    result = write_outputs(args.out_dir, runs, started, seeds, done, check_r)
    brief = None if check_r is None else {x: check_r[x]
                                          for x in ("compared", "identical", "missing")}
    print(json.dumps(dict(check=brief, completed=result["completed"], runs=result["runs"],
                          verdicts=[{k: v[k] for k in ("profile", "variant", "against",
                                                       "groups_faster", "groups_slower",
                                                       "groups_lost")}
                                    for v in result["verdicts"]],
                          worst=[{k: w[k] for k in ("profile", "variant", "course",
                                                    "median_max_m", "over_snap")}
                                 for w in result["worst"]])), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
