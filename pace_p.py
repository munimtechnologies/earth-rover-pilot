#!/usr/bin/env python3
"""pace_p: does a longer lookahead save time on straights, or only at corners?

pace_o.py (studies/pace-o/GRADE.md) found that with the corners kept a
24 m lookahead was 3.5-3.6% faster than 16 m on the city-blocks course, but
it turned before each corner (median 0.17 m past it, against 2.3 m with
16 m) and ran up to 1.6 m further from the course near corners, so 16 m
stayed. Its grade named the corners as the likely source of the time, not
tested.

This study splits the lookahead by where the path goes. A BendFollower aims
`lookahead_m` ahead (the long lookahead) while the path from the rover's place
to that point stays within `turn_deg` of the heading at the rover's place,
and `short_m` ahead otherwise. With a short lookahead of 16 m it should
behave like 16 m near every turn of at least `turn_deg` and like the long one
elsewhere.

Variants (all v0.18.1's real-rover pilot, pace_m.py's long20 learner on
pace_l.py's bridge120+cf0.3, on pace_o.py's `keep` planner; only the path
follower changes): keep16 (the pilot as it ships, a plain 16 m), keep24 (a
plain 24 m, as pace_o.py flew it), bend24 (24 m, 16 m when the path ahead
turns by 45 deg or more), calm24 (24 m, 16 m from 10 deg) and calm32 (32 m,
16 m from 10 deg). Profiles: pace_l.py's outage90 (a steady compass error)
and drift90.

    python pace_p.py --out-dir out --first-seed 253 --seeds 24 --check studies/pace-o/runs.jsonl

With --check it first flies seeds 229-231 of pace_o.py's outage90 and drift90
keep16 and keep24 missions again and compares each field by field with
pace_o.py's record: keep16 and keep24 are flown by pace_o.fly itself, and the
aim record only reads. Simulated rovers only, so the speeds are upper
bounds. Standard library only. By MV2 of Munim, Inc.; written with AI agents.
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
import pace_study as ps
import rover_pilot as rp

__version__ = "0.1.0"

PROFILES = {name: pl.PROFILES[name] for name in ("outage90", "drift90")}
# The first is always flown.
BASE_PROFILE = next(iter(PROFILES))
# (a, b): each variant on profile b against itself on profile a, paired by seed.
PROFILE_PAIRS = (("outage90", "drift90"),)
# Every mission is flown as this pace_m.py variant on pace_o.py's keep planner.
LEARNER = po.LEARNER
PLANNER = "keep"
# The path follower for each variant: a plain PathFollower with lookahead_m
# (flown by pace_o.fly), or a BendFollower when short_m is given.
VARIANTS = {
    "keep16": {"lookahead_m": 16.0},
    "keep24": {"lookahead_m": 24.0},
    "bend24": {"lookahead_m": 24.0, "short_m": 16.0, "turn_deg": 45.0},
    "calm24": {"lookahead_m": 24.0, "short_m": 16.0, "turn_deg": 10.0},
    "calm32": {"lookahead_m": 32.0, "short_m": 16.0, "turn_deg": 10.0},
}
# The pilot as it ships; every pair is against it, so it is always flown.
BASE_VARIANT = next(iter(VARIANTS))
# (a, b): b against a, paired by seed on every profile and course.
PAIRS = tuple((BASE_VARIANT, v) for v in VARIANTS if v != BASE_VARIANT)
CRUISES = (0.8,)
# pace_o.py flew seeds 229-252; these start after them.
FIRST_SEED = 253
# pace_o.py flew these; --check flies them again under the same names.
CHECKED = {"profiles": ("outage90", "drift90"), "variants": ("keep16", "keep24"),
           "seeds": (229, 230, 231)}
NO_AIM = {"targets": None, "long": None}


def headings(points, min_m=0.01):
    """Bearing (deg) of each segment of the (lat, lon) polyline `points`. A
    segment shorter than min_m takes the next longer one's, or at the end the
    last longer one's; with none, 0."""
    out = [None] * max(0, len(points) - 1)
    for k in range(len(out)):
        a, b = points[k], points[k + 1]
        if rp.haversine_m(a[0], a[1], b[0], b[1]) >= min_m:
            out[k] = rp.bearing_deg(a[0], a[1], b[0], b[1])
    later = None
    for k in reversed(range(len(out))):
        if out[k] is None:
            out[k] = later
        else:
            later = out[k]
    earlier = None
    for k in range(len(out)):
        if out[k] is None:
            out[k] = earlier
        else:
            earlier = out[k]
    return [0.0 if h is None else h for h in out]


def turn_ahead(hs, i, n):
    """The largest change of heading (deg) from segment i over segments i to
    i + n - 1 of a polyline whose segment headings are hs."""
    if not hs:
        return 0.0
    i = min(i, len(hs) - 1)
    return max(abs(rp.wrap180(h - hs[i])) for h in hs[i:i + n])


class BendFollower(rp.PathFollower):
    """PathFollower that aims lookahead_m ahead while the path from the
    rover's place to that point turns by less than turn_deg, and short_m ahead
    otherwise. It counts its targets and how many were long ones."""

    def __init__(self, points, lookahead_m=24.0, short_m=16.0, turn_deg=45.0,
                 search_m=60.0, step_m=2.0):
        super().__init__(points, lookahead_m=lookahead_m, search_m=search_m, step_m=step_m)
        self.short_n = max(1, int(round(short_m / step_m)))
        self.turn_deg = turn_deg
        self.headings = headings(self.points)
        self.targets = self.long = 0

    def target(self, lat, lon):
        _, distance = super().target(lat, lon)
        i = self.i
        n = self.lookahead_n
        if turn_ahead(self.headings, i, n) >= self.turn_deg:
            n = self.short_n
        self.targets += 1
        if n == self.lookahead_n:
            self.long += 1
        return self.points[min(len(self.points) - 1, i + n)], distance


@contextlib.contextmanager
def _bending(settings, made):
    """While inside, every PathFollower the Pilot builds is a BendFollower with
    `settings`, each appended to `made`."""
    saved = rp.PathFollower

    def follower(points, **kw):
        f = BendFollower(points, **dict(kw, **settings))
        made.append(f)
        return f

    rp.PathFollower = follower
    try:
        yield
    finally:
        rp.PathFollower = saved


def fly(course_name, seed, profile, variant, cruise, course=None):
    """One mission of the variant on pace_o.py's keep planner, with pace_o.py's
    records (corner, context, planner) and the aim record: the follower's
    targets and how many were long ones (None for a plain follower)."""
    course = course or ps.COURSES[course_name]
    v = VARIANTS[variant]
    if "short_m" not in v:
        r = po.fly(course_name, seed, profile, variant, cruise, course=course)
        r["aim"] = dict(NO_AIM)
        return r
    samples, made, followers = [], [], []
    with po._planning(PLANNER, made), _bending(v, followers), po._watching(samples):
        r = pm.fly(course_name, seed, profile, LEARNER, cruise, course=course)
    pts, cps = course["points"], course["checkpoints"]
    r["corner"] = pn.corner_stats(pts, cps, [(n, e) for n, e, _ in samples])
    r["context"] = po.contexts(pts, cps, samples)
    r["planner"] = {"plans": sum(p.calls for p in made), "behind": sum(p.behind for p in made)}
    r["aim"] = {"targets": sum(f.targets for f in followers),
                "long": sum(f.long for f in followers)}
    return r


def failed_run(exc):
    return dict(po.failed_run(exc), aim=dict(NO_AIM))


def check_pace_o(path):
    """Fly the CHECKED missions again and compare each with pace_o.py's record
    of it (its runs.jsonl): every field pace_o.py recorded must be equal. A
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
                        want = ref.get((profile, variant, cruise, course, seed))
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
                                              "cruise": cruise, "course": course,
                                              "seed": seed, "fields": fields})
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


def aim_rows(runs):
    """Per (profile, variant, cruise, course), over the completed missions with
    an aim record: the median of each mission's share of long targets."""
    rows = []
    for k, rs in sorted(pg._groups(runs).items()):
        ok = [r for r in rs if r["ok"] and (r.get("aim") or {}).get("targets")]
        if not ok:
            continue
        rows.append({"profile": k[0], "variant": k[1], "cruise": k[2], "course": k[3],
                     "missions": len(ok),
                     "median_targets": ps._median([r["aim"]["targets"] for r in ok]),
                     "median_long_share": ps._median(
                         [r["aim"]["long"] / r["aim"]["targets"] for r in ok], 3)})
    return rows


def write_outputs(out_dir, runs, started, seeds, done, check=None):
    s = ps.summarise(runs)
    effects, tallies = pair_effects(runs)
    p_effects, p_tallies = profile_effects(runs)
    aim = aim_rows(runs)
    context = po.context_rows(runs)
    planner = po.planner_rows(runs)
    corner = pn.corner_rows(runs)
    maxes = pn.offset_max_rows(runs)
    offsets = pe.offset_rows(runs)
    headings_ = pd.heading_rows(runs)
    positions = pg.position_rows(runs)
    steering = ph.steer_rows(runs)
    result = {"version": __version__, "pace_o": po.__version__, "pace_n": pn.__version__,
              "pace_m": pm.__version__, "pace_l": pl.__version__, "pace_j": pj.__version__,
              "pace_i": pi.__version__, "pace_e": pe.__version__, "pace_d": pd.__version__,
              "pace_study": ps.__version__, "rover_pilot": rp.__version__,
              "dead_reckon": dr.__version__, "done": done,
              "elapsed_s": round(time.monotonic() - started, 1), "seeds": seeds,
              "human": {"marathon_m": ps.MARATHON_M, "time_s": ps.HUMAN_S,
                        "mps": round(ps.HUMAN_MPS, 4)},
              "profiles": PROFILES, "learner": LEARNER, "learner_settings": pm.VARIANTS[LEARNER],
              "flown_as": pm.FLOWN_AS, "planner_kind": PLANNER, "variants": VARIANTS,
              "pairs": [list(x) for x in PAIRS],
              "profile_pairs": [list(x) for x in PROFILE_PAIRS], "cruises": list(CRUISES),
              "corner_deg": pn.CORNER_DEG, "corner_m": pn.CORNER_M, "far_m": po.FAR_M,
              "runs": len(runs), "completed": sum(1 for r in runs if r["ok"]),
              "overview": s["overview"], "pair_effect": effects, "verdicts": tallies,
              "profile_effect": p_effects, "profile_verdicts": p_tallies, "aim": aim,
              "context": context, "planner": planner, "corner": corner, "offset_max": maxes,
              "offset": offsets, "heading": headings_, "position": positions,
              "steer": steering, "check": check}
    with open(os.path.join(out_dir, "summary.json"), "w") as f:
        json.dump(result, f, indent=1)
    with open(os.path.join(out_dir, "runs.jsonl"), "w") as f:
        for r in runs:
            f.write(json.dumps(r) + "\n")
    md = ["# Does a longer lookahead save time on straights, or only at corners? (simulated)",
          "",
          "pace_p.py %s (pace_o.py %s, pace_m.py %s, rover_pilot.py %s, dead_reckon.py %s), MV2 "
          "of Munim, Inc. Every mission is v0.18.1's real-rover pilot (pace_m.py's long20 learner "
          "on pace_l.py's bridge120+cf0.3) on pace_o.py's keep planner, on pace_l.py's outage90 "
          "(90 s GPS outages, a steady compass error) or drift90 (the compass error drifts, SD "
          "10 deg, 120 s time constant); only the path follower changes (keep: a plain "
          "lookahead; bend and calm: the long lookahead unless the path ahead turns by 45 or "
          "10 deg, then 16 m). Seeds %s. %d of %d missions completed. Simulated rovers only, so "
          "these speeds are upper bounds."
          % (__version__, po.__version__, pm.__version__, rp.__version__, dr.__version__,
             "%d-%d" % (seeds[0], seeds[-1]) if seeds else "none",
             result["completed"], len(runs)), ""]
    if check is not None:
        md += ["Check against pace_o.py's runs: %d compared, %d identical, %d missing."
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
    md += ["", "## What the drift costs each variant", ""]
    md += pf._table(["variant", "profile", "against", "faster", "slower", "lost", "gained",
                     "largest median diff"],
                    [(t["variant"], t["profile"], t["against"],
                      "%d/%d" % (t["groups_faster"], t["groups"]), t["groups_slower"],
                      t["groups_lost"], t["groups_gained"], t["largest_median_diff_share"])
                     for t in p_tallies])
    md += ["", "## How often the follower aimed long", ""]
    md += pf._table(["profile", "variant", "course", "missions", "targets (median)",
                     "long share (median)"],
                    [(x["profile"], x["variant"], x["course"], x["missions"],
                      x["median_targets"], x["median_long_share"]) for x in aim])
    md += ["", "## Near path corners (pace_n.py's record)", ""]
    md += pf._table(["profile", "variant", "course", "missions", "corners", "median m", "p95 m",
                     "max m", "median past m", "max past m"],
                    [(x["profile"], x["variant"], x["course"], x["missions"], x["corners"],
                      x["median_m"], x["p95_m"], x["max_m"], x["median_past_m"],
                      x["max_past_m"]) for x in corner])
    md += ["", "## Where the rover strays (true distance from the course by context; far: "
           "over %g m)" % po.FAR_M, ""]
    md += pf._table(["profile", "variant", "course", "context", "missions", "samples", "far",
                     "far share", "median m", "p95 m", "max m"],
                    [(x["profile"], x["variant"], x["course"], x["context"], x["missions"],
                      x["samples"], x["far"], x["far_share"], x["median_m"], x["p95_m"],
                      x["max_m"]) for x in context])
    md += ["", "## Distance from the course while driving forward", ""]
    md += pf._table(["profile", "variant", "course", "missions", "median m", "p95 m"],
                    [(x["profile"], x["variant"], x["course"], x["missions"],
                      x["median_offset_m"], x["p95_offset_m"]) for x in offsets])
    md += ["", "## Largest distance from the course, and refused reports", ""]
    md += pf._table(["profile", "variant", "course", "missions", "median of max m",
                     "largest m", "refused", "missions refused"],
                    [(x["profile"], x["variant"], x["course"], x["missions"], x["median_max_m"],
                      x["largest_max_m"], x["refused"], x["missions_refused"]) for x in maxes])
    md += ["", "## Plans, and plans made before reaching the leg's first point", ""]
    md += pf._table(["profile", "variant", "course", "missions", "plans (median)",
                     "behind (median)"],
                    [(x["profile"], x["variant"], x["course"], x["missions"], x["median_plans"],
                      x["median_behind"]) for x in planner])
    md += ["", "## Heading error", ""]
    md += pf._table(["profile", "variant", "course", "missions", "median abs deg", "rms deg"],
                    [(x["profile"], x["variant"], x["course"], x["missions"],
                      x["median_abs_deg"], x["rms_deg"]) for x in headings_])
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
    ap.add_argument("--check", help="pace_o.py's runs.jsonl: fly the CHECKED missions again "
                                    "and compare")
    args = ap.parse_args(argv)
    courses = ps._names(args.courses, ps.COURSES, "course")
    profiles = ps._names(args.profiles, PROFILES, "profile")
    variants = ps._names(args.variants, VARIANTS, "variant")
    # outage90 and keep16 are always flown: the rest are compared with them.
    profiles = [BASE_PROFILE] + [p for p in profiles if p != BASE_PROFILE]
    variants = [BASE_VARIANT] + [v for v in variants if v != BASE_VARIANT]
    seeds = list(range(args.first_seed, args.first_seed + args.seeds))
    os.makedirs(args.out_dir, exist_ok=True)
    started = time.monotonic()
    check = check_pace_o(args.check) if args.check else None
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
