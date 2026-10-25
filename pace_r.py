#!/usr/bin/env python3
"""pace_r: is a truer GPS position worth anything once the rover really aims as far ahead?

pace_q.py found that with GPS as quiet as recorded Earth Rovers' (0.22 m),
filters without the shipped average's lag were 3-4% faster on city blocks,
but every one turned before the corners. The path follower's lookahead is
measured from where the pilot thinks it is: with GpsFilter's alpha 0.3 that
is a median 6.3-6.4 m behind the rover, so a 16 m lookahead really aims about
9.6 m ahead of it; with pace_q.py's TrackingGpsFilter (2.2-2.3 m behind) about
13.8 m. pace_p.py found that aiming further ahead on blocks saves time by
turning early. So pace_q.py's saving may be the longer real aim alone.

Variants, two filters by two lookaheads (all v0.18.2's real-rover pilot as
pace_q.py flies it, with pace_q.py's a0.3 or track filter; only the path
follower's lookahead changes):
  a0.3-16   GpsFilter as it ships, 16 m: the real-rover pilot (aims ~9.6 m)
  track-12  TrackingGpsFilter, 12 m: aims ~9.8 m, as the shipped pilot does
  a0.3-20   GpsFilter, 20 m: aims ~13.6 m, as the tracker does at 16 m
  track-16  TrackingGpsFilter, 16 m: pace_q.py's track (aims ~13.8 m)
Each lookahead is a whole number of the follower's 2 m steps: PathFollower
rounds lookahead / 2 m half to even, so 13 m would be flown as 12 m.
Profiles: pace_q.py's outage90 (the simulator's 1.5 m GPS noise), quiet90
(0.22 m) and quietdrift90 (0.22 m with a drifting compass).

    python pace_r.py --out-dir out --first-seed 301 --seeds 24 --check studies/pace-p/runs.jsonl \\
        --check-q studies/pace-q/runs.jsonl

With --check it first flies seeds 253-255 of pace_p.py's outage90 and drift90
keep16 missions again as a0.3-16; with --check-q, seeds 277-279 of pace_q.py's
quiet90 a0.3 and track missions again as a0.3-16 and track-16. Each is compared
field by field with the record. Simulated rovers only, so the speeds are
upper bounds. Standard library only. By MV2 of Munim, Inc.; written with AI
agents. Apache-2.0.
"""

from __future__ import annotations

import argparse
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
import pace_n as pn
import pace_o as po
import pace_p as pp
import pace_q as pq
import pace_study as ps
import rover_pilot as rp

__version__ = "0.1.0"

PROFILES = pq.PROFILES
# The first is always flown.
BASE_PROFILE = next(iter(PROFILES))
PROFILE_PAIRS = pq.PROFILE_PAIRS
# The GPS filter (a pace_q.py variant) and the path follower's lookahead for
# each variant.
VARIANTS = {
    "a0.3-16": {"filter": "a0.3", "lookahead_m": 16.0},
    "track-12": {"filter": "track", "lookahead_m": 12.0},
    "a0.3-20": {"filter": "a0.3", "lookahead_m": 20.0},
    "track-16": {"filter": "track", "lookahead_m": 16.0},
}
# The pilot as it ships; it is always flown.
BASE_VARIANT = next(iter(VARIANTS))
# (a, b): b against a, paired by seed on every profile and course. The first
# three are against the shipped pilot; then each filter at the same real aim
# (the tracker at 16 m against the shipped filter at 20 m), and the tracker's
# two lookaheads.
PAIRS = (("a0.3-16", "track-12"), ("a0.3-16", "a0.3-20"), ("a0.3-16", "track-16"),
         ("a0.3-20", "track-16"), ("track-12", "track-16"))
CRUISES = (0.8,)
# pace_q.py flew seeds 277-300; these start after them.
FIRST_SEED = 301
# --check: pace_p.py's keep16 flown again as a0.3-16. --check-q: pace_q.py's
# a0.3 and track flown again as a0.3-16 and track-16. (ours, theirs).
CHECKED_P = {"profiles": ("outage90", "drift90"), "variants": (("a0.3-16", "keep16"),),
             "seeds": (253, 254, 255)}
CHECKED_Q = {"profiles": ("quiet90",), "variants": (("a0.3-16", "a0.3"), ("track-16", "track")),
             "seeds": (277, 278, 279)}


def fly(course_name, seed, profile, variant, cruise, course=None):
    """One mission flown by pace_q.fly with the variant's GPS filter and its
    path follower aiming the variant's lookahead ahead, with pace_q.py's
    records. pace_o.fly sets 16 m inside this; the follower it builds calls the
    one set here, which sets the lookahead last, so the variant's wins."""
    v = VARIANTS[variant]
    with po._aiming(v["lookahead_m"]):
        return pq.fly(course_name, seed, profile, v["filter"], cruise, course=course)


def failed_run(exc):
    return pq.failed_run(exc)


def check(path, checked):
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


def _check_line(name, c):
    return ("Check against %s: %d compared, %d identical, %d missing."
            % (name, c["compared"], c["identical"], c["missing"]))


def write_outputs(out_dir, runs, started, seeds, done, check_p=None, check_q=None):
    s = ps.summarise(runs)
    effects, tallies = pair_effects(runs)
    p_effects, p_tallies = profile_effects(runs)
    gps = pq.gps_rows(runs)
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
              "flown_as": pq.FLOWN_AS, "filters": {k: pq.VARIANTS[k] for k in ("a0.3", "track")},
              "variants": VARIANTS, "pairs": [list(x) for x in PAIRS],
              "profile_pairs": [list(x) for x in PROFILE_PAIRS], "cruises": list(CRUISES),
              "corner_deg": pn.CORNER_DEG, "corner_m": pn.CORNER_M, "far_m": po.FAR_M,
              "runs": len(runs), "completed": sum(1 for r in runs if r["ok"]),
              "overview": s["overview"], "pair_effect": effects, "verdicts": tallies,
              "profile_effect": p_effects, "profile_verdicts": p_tallies, "gps": gps,
              "position": positions, "corner": corner, "offset": offsets,
              "offset_max": maxes, "context": context, "heading": headings_,
              "steer": steering, "check": check_p, "check_q": check_q}
    with open(os.path.join(out_dir, "summary.json"), "w") as f:
        json.dump(result, f, indent=1)
    with open(os.path.join(out_dir, "runs.jsonl"), "w") as f:
        for r in runs:
            f.write(json.dumps(r) + "\n")
    md = ["# Is a truer GPS position worth anything once the rover really aims as far ahead? "
          "(simulated)",
          "",
          "pace_r.py %s (pace_q.py %s, pace_p.py %s, rover_pilot.py %s, dead_reckon.py %s), MV2 "
          "of Munim, Inc. Every mission is v0.18.2's real-rover pilot as pace_q.py flies it "
          "(pace_p.py's keep16: pace_m.py's long20 learner on pace_l.py's bridge120+cf0.3 and "
          "pace_o.py's keep planner) with pace_q.py's a0.3 filter (as it ships) or its track "
          "filter (alpha 0.3 with a tracked velocity), and a path follower aiming 12, 16 or 20 m "
          "ahead. Profiles: outage90 (90 s GPS outages, a steady compass error, 1.5 m of GPS "
          "noise per axis), quiet90 (the same with %g m) and quietdrift90 (a drifting compass "
          "with %g m). Seeds %s. %d of %d missions completed. Simulated rovers only, so these "
          "speeds are upper bounds."
          % (__version__, pq.__version__, pp.__version__, rp.__version__, dr.__version__,
             pq.QUIET_NOISE_M, pq.QUIET_NOISE_M,
             "%d-%d" % (seeds[0], seeds[-1]) if seeds else "none",
             result["completed"], len(runs)), ""]
    if check_p is not None:
        md += [_check_line("pace_p.py's runs", check_p), ""]
    if check_q is not None:
        md += [_check_line("pace_q.py's runs", check_q), ""]
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
    ap.add_argument("--check", help="pace_p.py's runs.jsonl: fly CHECKED_P again and compare")
    ap.add_argument("--check-q", help="pace_q.py's runs.jsonl: fly CHECKED_Q again and compare")
    args = ap.parse_args(argv)
    courses = ps._names(args.courses, ps.COURSES, "course")
    profiles = ps._names(args.profiles, PROFILES, "profile")
    variants = ps._names(args.variants, VARIANTS, "variant")
    # outage90 and a0.3-16 are always flown: the rest are compared with them.
    profiles = [BASE_PROFILE] + [p for p in profiles if p != BASE_PROFILE]
    variants = [BASE_VARIANT] + [v for v in variants if v != BASE_VARIANT]
    seeds = list(range(args.first_seed, args.first_seed + args.seeds))
    os.makedirs(args.out_dir, exist_ok=True)
    started = time.monotonic()
    check_p = check(args.check, CHECKED_P) if args.check else None
    check_q = check(args.check_q, CHECKED_Q) if args.check_q else None
    for name, c in (("pace_p.py's runs", check_p), ("pace_q.py's runs", check_q)):
        if c is not None:
            print(_check_line(name, c), flush=True)
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
            write_outputs(args.out_dir, runs, started, seeds, False, check_p, check_q)
        if not done:
            break
    result = write_outputs(args.out_dir, runs, started, seeds, done, check_p, check_q)
    brief = {k: None if c is None else {x: c[x] for x in ("compared", "identical", "missing")}
             for k, c in (("check", check_p), ("check_q", check_q))}
    print(json.dumps(dict(brief, completed=result["completed"], runs=result["runs"],
                          verdicts=[{k: v[k] for k in ("profile", "variant", "against",
                                                       "groups_faster", "groups_slower",
                                                       "groups_lost")}
                                    for v in result["verdicts"]])), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
