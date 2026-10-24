#!/usr/bin/env python3
"""pace_o: where does the rover stray from its course, and is it the study's planner?

pace_n.py (studies/pace-n/GRADE.md) found the rover's 95th-percentile
distance from the course near the city-blocks course's path corners only
3.3-5.7 m, against 9.0-11.1 m over the whole mission, so most of the large
distances lie elsewhere. The studies' planner (pace_study.CoursePlanner) is
a likely place, not tested: each leg is planned from where the pilot thinks
it is when it reports the checkpoint the leg starts from, about 10-16 m
before it, and leg_points goes from there straight to the end of the course
segment nearest the rover in the new leg. On blocks every interior
checkpoint is a right-angle corner, so each new leg begins with a 100 m
diagonal across the inside of the corner. The OSM planner a real rover uses
(route_planner) routes from the walkable node nearest the rover, which near
a street corner is usually the corner itself.

This study records, for every 1 s sample of the rover's true position while
it drives forward, where it was (within 20 m before to 60 m after an
interior checkpoint along the course, near a path corner, or elsewhere) and
whether the GPS was out, and flies a planner that keeps the checkpoint
corner (`keep`: when the rover is nearest the segment leading into the leg,
the path goes through the leg's first point) against the studies' planner
(`diag`).

Variants (all v0.18.0's real-rover pilot: pace_m.py's long20 learner on
pace_l.py's bridge120+cf0.3; only the planner and the lookahead change):
diag16 (as pace_n.py's look16 flew it), keep16, keep8 and keep24.
Profiles: pace_l.py's outage90 (a steady compass error) and drift90.

    python pace_o.py --out-dir out --first-seed 229 --seeds 24 --check studies/pace-n/runs.jsonl

With --check it first flies seeds 205-207 of pace_n.py's outage90 and drift90
look16 missions again as diag16 and compares each field by field with
pace_n.py's record: the context record and the planner's count only read.
Every mission is flown by pace_m.fly itself. Simulated rovers only, so the
speeds are upper bounds. Standard library only. By MV2 of Munim, Inc.;
written with AI agents. Apache-2.0.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import math
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
import pace_study as ps
import rover_pilot as rp

__version__ = "0.1.0"

PROFILES = {name: pl.PROFILES[name] for name in ("outage90", "drift90")}
# The first is always flown.
BASE_PROFILE = next(iter(PROFILES))
# (a, b): each variant on profile b against itself on profile a, paired by seed.
PROFILE_PAIRS = (("outage90", "drift90"),)
# Every mission is flown as this pace_m.py variant (v0.17.0's and v0.18.0's
# real-rover learner).
LEARNER = pn.LEARNER
# The planner ("diag": pace_study.CoursePlanner as every study so far flew it;
# "keep": goes through the checkpoint corner) and the path follower's
# lookahead for each variant. diag16 is v0.18.0's real-rover pilot as the
# studies fly it.
VARIANTS = {
    "diag16": {"planner": "diag", "lookahead_m": 16.0},
    "keep16": {"planner": "keep", "lookahead_m": 16.0},
    "keep8": {"planner": "keep", "lookahead_m": 8.0},
    "keep24": {"planner": "keep", "lookahead_m": 24.0},
}
# These two are always flown: every pair is against one of them.
ALWAYS = ("diag16", "keep16")
# (a, b): b against a, paired by seed on every profile and course.
PAIRS = (("diag16", "keep16"), ("keep16", "keep8"), ("keep16", "keep24"))
CRUISES = (0.8,)
# pace_n.py flew seeds 205-228; these start after them.
FIRST_SEED = 229
# pace_n.py flew these as look16; --check flies them again as diag16.
CHECKED = {"profiles": ("outage90", "drift90"), "variant": "diag16", "against": "look16",
           "seeds": (205, 206, 207)}
# A sample is near a checkpoint if, along the course, it is from
# CHECKPOINT_BEFORE_M before to CHECKPOINT_AFTER_M after an interior
# checkpoint (not the last); else near a path corner if within pace_n.CORNER_M
# of one (pace_n.corners); else elsewhere. Separately, in an outage or not.
CHECKPOINT_BEFORE_M = 20.0
CHECKPOINT_AFTER_M = 60.0
PLACES = ("checkpoint", "corner", "other")
CONTEXTS = PLACES + ("outage", "fix")
# A sample further than this from the course counts as far.
FAR_M = 8.0


def keep_points(course, leg, north, east):
    """pace_study.leg_points, except that the segment leading into the leg
    counts too: if the rover is nearest to it (it has not yet reached the
    point the leg starts from), the path goes through that point."""
    cps = course["checkpoints"]
    pts = course["points"]
    a = 0 if leg == 0 else cps[leg - 1]
    b = cps[leg]
    p = (north, east)
    best, best_d = a, math.inf
    for j in range(max(0, a - 1), b):
        d = ps._seg_dist(p, pts[j], pts[j + 1])
        if d < best_d:
            best, best_d = j, d
    return [p] + list(pts[max(best + 1, a):b + 1])


class LegPlanner(ps.CoursePlanner):
    """CoursePlanner that counts the plans made while the rover had not yet
    reached the point its leg starts from (`behind`: keep_points and
    leg_points differ) and, with `keep`, returns keep_points' path; without
    it, exactly CoursePlanner's."""

    def __init__(self, course, lat0, lon0, keep=False):
        super().__init__(course, lat0, lon0)
        self.keep = keep
        self.behind = 0

    def __call__(self, lat, lon, cp_lat, cp_lon):
        self.calls += 1
        pts, cps = self.course["points"], self.course["checkpoints"]
        e, n = rp.to_enu(self.lat0, self.lon0, cp_lat, cp_lon)
        leg = min(range(len(cps)),
                  key=lambda k: math.hypot(pts[cps[k]][0] - n, pts[cps[k]][1] - e))
        east, north = rp.to_enu(self.lat0, self.lon0, lat, lon)
        plain = ps.leg_points(self.course, leg, north, east)
        kept = keep_points(self.course, leg, north, east)
        if kept != plain:
            self.behind += 1
        return [rp.offset_latlon(self.lat0, self.lon0, a, b)
                for a, b in (kept if self.keep else plain)]


@contextlib.contextmanager
def _planning(kind, made):
    """While inside, every planner pace_i.fly builds is a LegPlanner (keeping
    corners if `kind` is "keep"), each appended to `made`."""
    saved = ps.CoursePlanner

    def planner(course, lat0, lon0):
        p = LegPlanner(course, lat0, lon0, keep=(kind == "keep"))
        made.append(p)
        return p

    ps.CoursePlanner = planner
    try:
        yield
    finally:
        ps.CoursePlanner = saved


@contextlib.contextmanager
def _aiming(lookahead_m):
    """While inside, every PathFollower the Pilot builds aims lookahead_m ahead."""
    saved = rp.PathFollower

    def follower(points, **kw):
        return saved(points, **dict(kw, lookahead_m=lookahead_m))

    rp.PathFollower = follower
    try:
        yield
    finally:
        rp.PathFollower = saved


@contextlib.contextmanager
def _watching(samples):
    """While inside, every rover pace_l.fly builds appends its true (north,
    east) and whether its GPS is out to `samples` every pace_e.OFFSET_EVERY_S
    while driving forward, as pace_n._watching samples."""
    saved = pl.SlipRover

    def rover(*args, **kw):
        sim = saved(*args, **kw)
        sleep, due = sim.sleep, [0.0]

        def watched(seconds):
            # Only reads; the mission is the same without it.
            if sim.applied[0] > 0 and sim.t >= due[0]:
                samples.append((sim.north, sim.east, sim.in_outage(sim.t)))
                due[0] = sim.t + pe.OFFSET_EVERY_S
            sleep(seconds)

        sim.sleep = watched
        return sim

    pl.SlipRover = rover
    try:
        yield
    finally:
        pl.SlipRover = saved


def stations(points):
    """Distance along the course to each of its points."""
    out = [0.0]
    for a, b in zip(points, points[1:]):
        out.append(out[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    return out


def station(points, cum, p):
    """Distance along the course to the point of it nearest p."""
    best, best_d, best_f = 0, math.inf, 0.0
    for j in range(len(points) - 1):
        a, b = points[j], points[j + 1]
        dn, de = b[0] - a[0], b[1] - a[1]
        l2 = dn * dn + de * de
        f = 0.0 if l2 == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * dn + (p[1] - a[1]) * de) / l2))
        d = math.hypot(p[0] - a[0] - f * dn, p[1] - a[1] - f * de)
        if d < best_d:
            best, best_d, best_f = j, d, f
    return cum[best] + best_f * (cum[best + 1] - cum[best])


def contexts(points, checkpoints, samples):
    """For each context, the distance from the course (pace_e.offset_stats) of
    the (north, east, outage) samples in it, and how many were further than
    FAR_M. Each sample is in one place (PLACES) and in outage or fix."""
    out = {name: [] for name in CONTEXTS}
    if samples and len(points) >= 2:
        cum = stations(points)
        marks = [cum[k] for k in checkpoints[:-1]]
        vertices = [v for v, _ in pn.corners(points, checkpoints)]
        for north, east, outage in samples:
            s = station(points, cum, (north, east))
            if any(-CHECKPOINT_BEFORE_M <= s - c <= CHECKPOINT_AFTER_M for c in marks):
                place = "checkpoint"
            elif any(math.hypot(north - v[0], east - v[1]) <= pn.CORNER_M for v in vertices):
                place = "corner"
            else:
                place = "other"
            x = pe.course_offset(points, north, east)
            out[place].append(x)
            out["outage" if outage else "fix"].append(x)
    return {name: dict(pe.offset_stats(xs), far=sum(1 for x in xs if x > FAR_M))
            for name, xs in out.items()}


def fly(course_name, seed, profile, variant, cruise, course=None):
    """One mission flown by pace_m.fly as long20 with the variant's planner
    and lookahead; also pace_n.py's corner record, the context record and
    the planner's counts."""
    course = course or ps.COURSES[course_name]
    v = VARIANTS[variant]
    samples, made = [], []
    with _planning(v["planner"], made), _aiming(v["lookahead_m"]), _watching(samples):
        r = pm.fly(course_name, seed, profile, LEARNER, cruise, course=course)
    pts, cps = course["points"], course["checkpoints"]
    r["corner"] = pn.corner_stats(pts, cps, [(n, e) for n, e, _ in samples])
    r["context"] = contexts(pts, cps, samples)
    r["planner"] = {"plans": sum(p.calls for p in made), "behind": sum(p.behind for p in made)}
    return r


def failed_run(exc):
    return dict(pn.failed_run(exc), context=contexts([], [], []),
                planner={"plans": None, "behind": None})


def check_pace_n(path):
    """Fly the CHECKED missions again as diag16 and compare each with
    pace_n.py's record of it as look16 (its runs.jsonl): every field
    pace_n.py recorded must be equal. A mission the record lacks is counted
    as missing and not flown."""
    ref = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                r = json.loads(line)
                ref[(r["profile"], r["variant"], r["cruise"], r["course"], r["seed"])] = r
    compared = missing = 0
    different = []
    against = CHECKED["against"]
    for profile in CHECKED["profiles"]:
        for cruise in CRUISES:
            for course in ps.COURSES:
                for seed in CHECKED["seeds"]:
                    want = ref.get((profile, against, cruise, course, seed))
                    if want is None:
                        missing += 1
                        continue
                    got = fly(course, seed, profile, CHECKED["variant"], cruise)
                    got.update(profile=profile, variant=against, cruise=cruise,
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


def context_rows(runs):
    """Per (profile, variant, cruise, course) and context, over the completed
    missions with a sample in that context: how many, their samples, the far
    ones and their share of the group's far samples, and the median of each
    mission's median, p95 and largest distance from the course there."""
    rows = []
    for k, rs in sorted(pg._groups(runs).items()):
        ok = [r for r in rs if r["ok"] and r.get("context")]
        if not ok:
            continue
        total = sum(r["context"][c]["far"] for r in ok for c in PLACES)
        for c in CONTEXTS:
            cs = [r["context"][c] for r in ok if r["context"][c]["n"]]
            far = sum(x["far"] for x in cs)
            rows.append({"profile": k[0], "variant": k[1], "cruise": k[2], "course": k[3],
                         "context": c, "missions": len(cs), "samples": sum(x["n"] for x in cs),
                         "far": far, "far_share": round(far / total, 3) if total else None,
                         "median_m": ps._median([x["median_m"] for x in cs], 2),
                         "p95_m": ps._median([x["p95_m"] for x in cs], 2),
                         "max_m": ps._median([x["max_m"] for x in cs], 2)})
    return rows


def planner_rows(runs):
    """Per (profile, variant, cruise, course), over the completed missions: the
    median plans and plans made behind the leg's first point."""
    rows = []
    for k, rs in sorted(pg._groups(runs).items()):
        ok = [r for r in rs if r["ok"] and r.get("planner", {}).get("plans") is not None]
        if not ok:
            continue
        rows.append({"profile": k[0], "variant": k[1], "cruise": k[2], "course": k[3],
                     "missions": len(ok),
                     "median_plans": ps._median([r["planner"]["plans"] for r in ok]),
                     "median_behind": ps._median([r["planner"]["behind"] for r in ok])})
    return rows


def write_outputs(out_dir, runs, started, seeds, done, check=None):
    s = ps.summarise(runs)
    effects, tallies = pair_effects(runs)
    p_effects, p_tallies = profile_effects(runs)
    context = context_rows(runs)
    planner = planner_rows(runs)
    corner = pn.corner_rows(runs)
    maxes = pn.offset_max_rows(runs)
    offsets = pe.offset_rows(runs)
    headings = pd.heading_rows(runs)
    positions = pg.position_rows(runs)
    steering = ph.steer_rows(runs)
    result = {"version": __version__, "pace_n": pn.__version__, "pace_m": pm.__version__,
              "pace_l": pl.__version__, "pace_j": pj.__version__, "pace_i": pi.__version__,
              "pace_e": pe.__version__, "pace_d": pd.__version__,
              "pace_study": ps.__version__, "rover_pilot": rp.__version__,
              "dead_reckon": dr.__version__, "done": done,
              "elapsed_s": round(time.monotonic() - started, 1), "seeds": seeds,
              "human": {"marathon_m": ps.MARATHON_M, "time_s": ps.HUMAN_S,
                        "mps": round(ps.HUMAN_MPS, 4)},
              "profiles": PROFILES, "learner": LEARNER, "learner_settings": pm.VARIANTS[LEARNER],
              "flown_as": pm.FLOWN_AS, "variants": VARIANTS, "pairs": [list(x) for x in PAIRS],
              "profile_pairs": [list(x) for x in PROFILE_PAIRS], "cruises": list(CRUISES),
              "checkpoint_before_m": CHECKPOINT_BEFORE_M,
              "checkpoint_after_m": CHECKPOINT_AFTER_M, "corner_deg": pn.CORNER_DEG,
              "corner_m": pn.CORNER_M, "far_m": FAR_M,
              "runs": len(runs), "completed": sum(1 for r in runs if r["ok"]),
              "overview": s["overview"], "pair_effect": effects, "verdicts": tallies,
              "profile_effect": p_effects, "profile_verdicts": p_tallies,
              "context": context, "planner": planner, "corner": corner, "offset_max": maxes,
              "offset": offsets, "heading": headings, "position": positions,
              "steer": steering, "check": check}
    with open(os.path.join(out_dir, "summary.json"), "w") as f:
        json.dump(result, f, indent=1)
    with open(os.path.join(out_dir, "runs.jsonl"), "w") as f:
        for r in runs:
            f.write(json.dumps(r) + "\n")
    md = ["# Where does the rover stray from its course? (simulated)",
          "",
          "pace_o.py %s (pace_n.py %s, pace_m.py %s, rover_pilot.py %s, dead_reckon.py %s), MV2 "
          "of Munim, Inc. Every mission is v0.18.0's real-rover pilot (pace_m.py's long20 learner "
          "on pace_l.py's bridge120+cf0.3) on pace_l.py's outage90 (90 s GPS outages, a steady "
          "compass error) or drift90 (the compass error drifts, SD 10 deg, 120 s time constant); "
          "only the planner (diag: the studies' CoursePlanner; keep: through each checkpoint "
          "corner) and the path follower's lookahead (metres) change. Seeds %s. %d of %d "
          "missions completed. Simulated rovers only, so these speeds are upper bounds."
          % (__version__, pn.__version__, pm.__version__, rp.__version__, dr.__version__,
             "%d-%d" % (seeds[0], seeds[-1]) if seeds else "none",
             result["completed"], len(runs)), ""]
    if check is not None:
        md += ["Check against pace_n.py's runs: %d compared, %d identical, %d missing."
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
    md += ["", "## Where the rover strays (true distance from the course by context; far: "
           "over %g m)" % FAR_M, ""]
    md += pf._table(["profile", "variant", "course", "context", "missions", "samples", "far",
                     "far share", "median m", "p95 m", "max m"],
                    [(x["profile"], x["variant"], x["course"], x["context"], x["missions"],
                      x["samples"], x["far"], x["far_share"], x["median_m"], x["p95_m"],
                      x["max_m"]) for x in context])
    md += ["", "## Plans, and plans made before reaching the leg's first point", ""]
    md += pf._table(["profile", "variant", "course", "missions", "plans (median)",
                     "behind (median)"],
                    [(x["profile"], x["variant"], x["course"], x["missions"], x["median_plans"],
                      x["median_behind"]) for x in planner])
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
    ap.add_argument("--check", help="pace_n.py's runs.jsonl: fly the CHECKED missions again "
                                    "and compare")
    args = ap.parse_args(argv)
    courses = ps._names(args.courses, ps.COURSES, "course")
    profiles = ps._names(args.profiles, PROFILES, "profile")
    variants = ps._names(args.variants, VARIANTS, "variant")
    # outage90, diag16 and keep16 are always flown: the rest are compared with them.
    profiles = [BASE_PROFILE] + [p for p in profiles if p != BASE_PROFILE]
    variants = list(ALWAYS) + [v for v in variants if v not in ALWAYS]
    seeds = list(range(args.first_seed, args.first_seed + args.seeds))
    os.makedirs(args.out_dir, exist_ok=True)
    started = time.monotonic()
    check = check_pace_n(args.check) if args.check else None
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
