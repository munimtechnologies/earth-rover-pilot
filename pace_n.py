#!/usr/bin/env python3
"""pace_n: how far ahead should the rover aim along its path?

With a planner (--osm on a real rover, CoursePlanner in the studies) the
pilot follows its path by pure pursuit (PathFollower): it aims at the point
8 m ahead of its place on the path. The 8 m has never been tested. pace_m.py's
records show the pilot's distance from the course on the blocks course, the
one with right-angle corners, at a 95th percentile of 10.6-11.0 m against
3.6-6.1 m on the others, and the pilot's idea of where it is about 6 m from
the truth at the median. A likely reason, not tested: the smoothed GPS lags
the rover by several metres along its track, so with an 8 m lookahead it
starts turning only about as it reaches a corner, and runs past it. Aiming
further ahead should turn earlier; aiming nearer should follow the path more
tightly between corners, and a longer lookahead holds the rover further to
one side for the same heading error (lookahead x tan(error)).

Variants (all v0.17.0's real-rover pilot: pace_m.py's long20 learner on
pace_l.py's bridge120+cf0.3; only the lookahead changes): look8 (as shipped),
look4, look12 and look16.
Profiles: pace_l.py's outage90 (a steady compass error) and drift90.
For every mission it also records the rover's true distance from the course
near each path corner (an interior course point, not a checkpoint, where the
course turns by at least 45 degrees) and how far the rover ran past it.

    python pace_n.py --out-dir out --first-seed 205 --seeds 24 --check studies/pace-m/runs.jsonl

With --check it first flies seeds 181-183 of pace_m.py's outage90 and drift90
long20 missions again as look8 and compares each field by field with
pace_m.py's record: the corner record only reads. Every mission is flown by
pace_m.fly itself. Simulated rovers only, so the speeds are upper bounds.
Standard library only. By MV2 of Munim, Inc.; written with AI agents.
Apache-2.0.
"""

from __future__ import annotations

import argparse
import contextlib
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
import pace_g as pg
import pace_h as ph
import pace_i as pi
import pace_j as pj
import pace_l as pl
import pace_m as pm
import pace_study as ps
import rover_pilot as rp

__version__ = "0.1.0"

PROFILES = {name: pl.PROFILES[name] for name in ("outage90", "drift90")}
# The first is always flown.
BASE_PROFILE = next(iter(PROFILES))
# (a, b): each variant on profile b against itself on profile a, paired by seed.
PROFILE_PAIRS = (("outage90", "drift90"),)
# Every mission is flown as this pace_m.py variant (v0.17.0's real-rover learner).
LEARNER = "long20"
# PathFollower settings for each variant; the first is the pilot as it ships.
VARIANTS = {
    "look8": {"lookahead_m": 8.0},
    "look4": {"lookahead_m": 4.0},
    "look12": {"lookahead_m": 12.0},
    "look16": {"lookahead_m": 16.0},
}
BASE_VARIANT = next(iter(VARIANTS))
# (a, b): b against a, paired by seed on every profile and course.
PAIRS = tuple((BASE_VARIANT, v) for v in VARIANTS if v != BASE_VARIANT)
CRUISES = (0.8,)
# pace_m.py flew seeds 181-204; these start after them.
FIRST_SEED = 205
# pace_m.py flew these as long20; --check flies them again as look8.
CHECKED = {"profiles": ("outage90", "drift90"), "variant": BASE_VARIANT,
           "seeds": (181, 182, 183)}
# A path corner: an interior course point, not a checkpoint, where the course
# turns by at least CORNER_DEG; a sample within CORNER_M of it is near it.
CORNER_DEG = 45.0
CORNER_M = 20.0


@contextlib.contextmanager
def _aiming(variant):
    """While inside, every PathFollower the Pilot builds has the variant's settings."""
    settings = VARIANTS[variant]
    saved = rp.PathFollower

    def follower(points, **kw):
        return saved(points, **dict(kw, **settings))

    rp.PathFollower = follower
    try:
        yield
    finally:
        rp.PathFollower = saved


@contextlib.contextmanager
def _watching(samples):
    """While inside, every rover pace_l.fly builds appends its true (north,
    east) to `samples` every pace_e.OFFSET_EVERY_S while driving forward."""
    saved = pl.SlipRover

    def rover(*args, **kw):
        sim = saved(*args, **kw)
        sleep, due = sim.sleep, [0.0]

        def watched(seconds):
            # Only reads; the mission is the same without it.
            if sim.applied[0] > 0 and sim.t >= due[0]:
                samples.append((sim.north, sim.east))
                due[0] = sim.t + pe.OFFSET_EVERY_S
            sleep(seconds)

        sim.sleep = watched
        return sim

    pl.SlipRover = rover
    try:
        yield
    finally:
        pl.SlipRover = saved


def corners(points, checkpoints=()):
    """[(vertex, (dn, de))]: each path corner and the unit direction of the
    course into it."""
    out = []
    skip = set(checkpoints)
    for k in range(1, len(points) - 1):
        if k in skip:
            continue
        a, v, b = points[k - 1], points[k], points[k + 1]
        h1 = math.atan2(v[1] - a[1], v[0] - a[0])
        h2 = math.atan2(b[1] - v[1], b[0] - v[0])
        if abs(rp.wrap180(math.degrees(h2 - h1))) < CORNER_DEG:
            continue
        length = math.hypot(v[0] - a[0], v[1] - a[1])
        out.append((v, ((v[0] - a[0]) / length, (v[1] - a[1]) / length)))
    return out


def corner_stats(points, checkpoints, samples):
    """Over the samples near a path corner: their distance from the course
    (pace_e.offset_stats), how many corners had one, and for each such corner
    how far the rover got past it along the course into it (past_m: above 0
    it ran past the corner, below 0 it turned before it), as the median and
    the largest over the corners."""
    cs = corners(points, checkpoints)
    offsets, past = [], {}
    for p in (samples if cs else ()):
        k = min(range(len(cs)), key=lambda i: math.hypot(p[0] - cs[i][0][0], p[1] - cs[i][0][1]))
        (vn, ve), (dn, de) = cs[k]
        if math.hypot(p[0] - vn, p[1] - ve) > CORNER_M:
            continue
        offsets.append(pe.course_offset(points, p[0], p[1]))
        along = (p[0] - vn) * dn + (p[1] - ve) * de
        past[k] = max(past.get(k, -math.inf), along)
    out = pe.offset_stats(offsets)
    out["corners"] = len(past)
    out["median_past_m"] = round(statistics.median(past.values()), 2) if past else None
    out["max_past_m"] = round(max(past.values()), 2) if past else None
    return out


def fly(course_name, seed, profile, variant, cruise, course=None):
    """One mission flown by pace_m.fly as long20 with the variant's lookahead;
    also the corner record."""
    course = course or ps.COURSES[course_name]
    samples = []
    with _aiming(variant), _watching(samples):
        r = pm.fly(course_name, seed, profile, LEARNER, cruise, course=course)
    r["corner"] = corner_stats(course["points"], course["checkpoints"], samples)
    return r


def failed_run(exc):
    return dict(pm.failed_run(exc), corner=corner_stats([], [], []))


def check_pace_m(path):
    """Fly the CHECKED missions again as look8 and compare each with
    pace_m.py's record of it as long20 (its runs.jsonl): every field pace_m.py
    recorded must be equal. A mission the record lacks is counted as missing
    and not flown."""
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
                    want = ref.get((profile, LEARNER, cruise, course, seed))
                    if want is None:
                        missing += 1
                        continue
                    got = fly(course, seed, profile, CHECKED["variant"], cruise)
                    got.update(profile=profile, variant=LEARNER, cruise=cruise,
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


def corner_rows(runs):
    """Per (profile, variant, cruise, course), over the completed missions with
    a sample near a path corner: the median of each mission's median, p95 and
    largest distance from the course near corners, and of its median and
    largest past_m."""
    rows = []
    for k, rs in sorted(pg._groups(runs).items()):
        cs = [r["corner"] for r in rs if r["ok"] and r.get("corner", {}).get("n")]
        if not cs:
            continue
        rows.append({"profile": k[0], "variant": k[1], "cruise": k[2], "course": k[3],
                     "missions": len(cs), "corners": ps._median([c["corners"] for c in cs]),
                     "median_m": ps._median([c["median_m"] for c in cs], 2),
                     "p95_m": ps._median([c["p95_m"] for c in cs], 2),
                     "max_m": ps._median([c["max_m"] for c in cs], 2),
                     "median_past_m": ps._median([c["median_past_m"] for c in cs], 2),
                     "max_past_m": ps._median([c["max_past_m"] for c in cs], 2)})
    return rows


def offset_max_rows(runs):
    """Per (profile, variant, cruise, course), over the completed missions: the
    median of each mission's largest distance from the course, the largest of
    them, and the reports the server refused (reports less checkpoints reached)."""
    rows = []
    for k, rs in sorted(pg._groups(runs).items()):
        ok = [r for r in rs if r["ok"]]
        maxes = [r["offset"]["max_m"] for r in ok if r.get("offset", {}).get("n")]
        if not ok:
            continue
        refused = [r["reports"] - r["reached"] for r in ok]
        rows.append({"profile": k[0], "variant": k[1], "cruise": k[2], "course": k[3],
                     "missions": len(ok),
                     "median_max_m": ps._median(maxes, 2) if maxes else None,
                     "largest_max_m": max(maxes) if maxes else None,
                     "refused": sum(refused),
                     "missions_refused": sum(1 for x in refused if x > 0)})
    return rows


def write_outputs(out_dir, runs, started, seeds, done, check=None):
    s = ps.summarise(runs)
    effects, tallies = pair_effects(runs)
    p_effects, p_tallies = profile_effects(runs)
    corner = corner_rows(runs)
    maxes = offset_max_rows(runs)
    offsets = pe.offset_rows(runs)
    headings = pd.heading_rows(runs)
    positions = pg.position_rows(runs)
    steering = ph.steer_rows(runs)
    result = {"version": __version__, "pace_m": pm.__version__, "pace_l": pl.__version__,
              "pace_j": pj.__version__, "pace_i": pi.__version__, "pace_e": pe.__version__,
              "pace_d": pd.__version__, "pace_study": ps.__version__,
              "rover_pilot": rp.__version__, "dead_reckon": dr.__version__, "done": done,
              "elapsed_s": round(time.monotonic() - started, 1), "seeds": seeds,
              "human": {"marathon_m": ps.MARATHON_M, "time_s": ps.HUMAN_S,
                        "mps": round(ps.HUMAN_MPS, 4)},
              "profiles": PROFILES, "learner": LEARNER, "learner_settings": pm.VARIANTS[LEARNER],
              "flown_as": pm.FLOWN_AS, "variants": VARIANTS, "pairs": [list(x) for x in PAIRS],
              "profile_pairs": [list(x) for x in PROFILE_PAIRS], "cruises": list(CRUISES),
              "corner_deg": CORNER_DEG, "corner_m": CORNER_M,
              "runs": len(runs), "completed": sum(1 for r in runs if r["ok"]),
              "overview": s["overview"], "pair_effect": effects, "verdicts": tallies,
              "profile_effect": p_effects, "profile_verdicts": p_tallies,
              "corner": corner, "offset_max": maxes, "offset": offsets, "heading": headings,
              "position": positions, "steer": steering, "check": check}
    with open(os.path.join(out_dir, "summary.json"), "w") as f:
        json.dump(result, f, indent=1)
    with open(os.path.join(out_dir, "runs.jsonl"), "w") as f:
        for r in runs:
            f.write(json.dumps(r) + "\n")
    md = ["# How far ahead should the rover aim along its path? (simulated)",
          "",
          "pace_n.py %s (pace_m.py %s, rover_pilot.py %s, dead_reckon.py %s), MV2 of Munim, Inc. "
          "Every mission is v0.17.0's real-rover pilot (pace_m.py's long20 learner on pace_l.py's "
          "bridge120+cf0.3) on pace_l.py's outage90 (90 s GPS outages, a steady compass error) "
          "or drift90 (the compass error drifts, SD 10 deg, 120 s time constant); only the path "
          "follower's lookahead changes: look8 (as shipped), look4, look12 and look16 metres. "
          "Seeds %s. %d of %d missions completed. Simulated rovers only, so these speeds are "
          "upper bounds."
          % (__version__, pm.__version__, rp.__version__, dr.__version__,
             "%d-%d" % (seeds[0], seeds[-1]) if seeds else "none",
             result["completed"], len(runs)), ""]
    if check is not None:
        md += ["Check against pace_m.py's runs: %d compared, %d identical, %d missing."
               % (check["compared"], check["identical"], check["missing"]), ""]
    md += ["## Overview (courses pooled)", ""]
    md += pf._table(["profile", "variant", "completed", "made good m/s (median)", "efficiency",
                     "runs beating 0.754", "path ratio", "share stopped"],
                    [(o["profile"], o["variant"], "%d/%d" % (o["completed"], o["runs"]),
                      o["median_made_good_mps"], o["median_efficiency"], o["beat_human_pace"],
                      o["median_path_ratio"], o["share_stopped"]) for o in s["overview"]])
    md += ["", "## Each lookahead against 8 m, same profile", "",
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
    md += ["", "## What the drift costs each lookahead", ""]
    md += pf._table(["variant", "profile", "against", "faster", "slower", "lost", "gained",
                     "largest median diff"],
                    [(t["variant"], t["profile"], t["against"],
                      "%d/%d" % (t["groups_faster"], t["groups"]), t["groups_slower"],
                      t["groups_lost"], t["groups_gained"], t["largest_median_diff_share"])
                     for t in p_tallies])
    md += ["", "## Near path corners (true distance from the course; past: how far beyond "
           "the corner)", ""]
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
    md += ["", "## Heading error", ""]
    md += pf._table(["profile", "variant", "course", "missions", "median abs deg", "rms deg"],
                    [(x["profile"], x["variant"], x["course"], x["missions"],
                      x["median_abs_deg"], x["rms_deg"]) for x in headings])
    md += ["", "## Where the pilot thinks it is, against where it is", ""]
    md += pf._table(["profile", "variant", "course", "missions", "median m", "p95 m"],
                    [(x["profile"], x["variant"], x["course"], x["missions"],
                      x["median_position_err_m"], x["p95_position_err_m"]) for x in positions])
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
    ap.add_argument("--check", help="pace_m.py's runs.jsonl: fly the CHECKED missions again "
                                    "and compare")
    args = ap.parse_args(argv)
    courses = ps._names(args.courses, ps.COURSES, "course")
    profiles = ps._names(args.profiles, PROFILES, "profile")
    variants = ps._names(args.variants, VARIANTS, "variant")
    # outage90 and look8 are always flown: the rest are compared with them.
    profiles = [BASE_PROFILE] + [p for p in profiles if p != BASE_PROFILE]
    variants = [BASE_VARIANT] + [v for v in variants if v != BASE_VARIANT]
    seeds = list(range(args.first_seed, args.first_seed + args.seeds))
    os.makedirs(args.out_dir, exist_ok=True)
    started = time.monotonic()
    check = check_pace_m(args.check) if args.check else None
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
