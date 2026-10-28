#!/usr/bin/env python3
"""pace_w: should a real rover's GPS average start again after a gap, now that
its stuck check has a warm-up?

trace_r.py (studies/pace-r/TRACE.md) found that GpsFilter, as it ships,
keeps its exponential average through a GPS outage and blends the first fix
after it with the average from before it: after 90 s without fixes the
pilot's idea of its position jumped about 57 m back along the course.
pace_s.py's `restart` (the average started again from the fix after more
than 3 s without a valid reading) removed that jump, but failed its rule on
outage90 boulevard. trace_s.py (studies/pace-s/TRACE.md) found why: a freshly
restarted average lags the rover for about 10 s, and the stuck check, which
judges on it, called the rover stuck. pace-t and pace-u flew `restart` with a
warm-up for the stuck check and it met every condition against the warm-up
alone, but their rule R3 could only adopt it on top of an adopted warm-up,
and none was adopted. pace_v.py (studies/pace-v/GRADE.md) adopted one, and
v0.19.0 gives a real rover 10 s (`warm10`). pace_w.py asks the R3 question
again, on fresh seeds, against v0.19.0's real-rover pilot, with tolerances
from the seed-to-seed spread and with blocked rovers at the start and
mid-route.

Variants (all v0.18.2's real-rover pilot as pace_v.py flies it, with
pace_v.py's warm10, which test_stuck_warmup_default.py shows flies as
v0.19.0's Pilot.stuck_warmup_s = 10):
  warm10           GpsFilter as it ships, the stuck check as v0.19.0 gives
                   a real rover
  restart+warm10   the same with pace_s.py's restart (pace_q.py's
                   TrackingGpsFilter with beta 0); pace_u.py's restart+warm10
  warm10:B         warm10 on the second seed set, for the spread only
Profiles: pace_v.py's outage90, quiet90, quietdrift90, quiet45,
blockedstart and blockedmid.

    python pace_w.py --out-dir out --first-seed 445 --seeds 24 --check

With --check it first flies 4 of pace_v.py's warm10 missions and 3 of
pace_s.py's restart missions again and compares them with those records.
Simulated rovers only, so the speeds are upper bounds. Standard library
only. By MV2 of Munim, Inc.; written with AI agents. Apache-2.0.
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
import pace_s as pz
import pace_study as ps
import pace_u as pu
import pace_v as pv
import rover_pilot as rp

__version__ = "0.1.0"

PROFILES = pv.PROFILES
# The first is always flown.
BASE_PROFILE = next(iter(PROFILES))
BLOCKS = pv.BLOCKS
BLOCKED = pv.BLOCKED
UNBLOCKED = pv.UNBLOCKED
# The profiles whose outages last 90 s (quiet45's last 45 s).
LONG_OUTAGE = ("outage90", "quiet90", "quietdrift90", "blockedstart", "blockedmid")
PROFILE_PAIRS = pv.PROFILE_PAIRS
WARMUP_S = pv.WARMUP_S
VARIANTS = {
    "warm10": {"alpha": 0.3, "warmup_s": WARMUP_S, "warm": "always"},
    "restart+warm10": {"alpha": 0.3, "beta": 0.0, "track": True, "warmup_s": WARMUP_S,
                       "warm": "always"},
    "warm10:B": {"alpha": 0.3, "warmup_s": WARMUP_S, "warm": "always"},
}
# v0.19.0's real-rover pilot; it is always flown.
BASE_VARIANT = next(iter(VARIANTS))
# The same pilot again on the second seed set: only the spread is read from it.
NOISE_VARIANT = "warm10:B"
# (a, b): b against a, paired by seed per course.
PAIRS = (("warm10", "restart+warm10"),)
CRUISES = (0.8,)
# pace_v.py flew seeds 397-444; these start after them, and the second set after these.
FIRST_SEED = 445
FIRST_SEED_B = 469
CATCH_S = pv.CATCH_S
POST_S = pv.POST_S
CORNER_TOL_MIN_M = pv.CORNER_TOL_MIN_M
OFFSET_TOL_MIN_M = pv.OFFSET_TOL_MIN_M
TOL_STEP_M = pv.TOL_STEP_M
EARLY_S = pv.EARLY_S
SNAP_M = pz.SNAP_M
# --check, pace_v.py's warm10: (profile, course, seed) -> (elapsed_s,
# recovery_t) in pace_v.py's record (compete pace-v-v1, runs.jsonl lines
# 73, 385, 1225 and 1531): a quiet outage mission, a quiet one, one blocked
# at the start (block 0-57.1 s) and one blocked mid-route.
CHECKED_V = {
    ("outage90", "boulevard", 397): (1747.6, []),
    ("quiet90", "blocks", 397): (1569.6, []),
    ("blockedstart", "boulevard", 397): (1799.6, [19.1, 44.1]),
    ("blockedmid", "boulevard", 415): (1823.6, [397.9, 422.9]),
}
# --check, pace_s.py's restart (no warm-up): (profile, course, seed) ->
# (elapsed_s, recoveries, gps restarts) in pace_s.py's record
# (studies/pace-s/runs.jsonl lines 86, 87 and 230): seed 338's 94 s loss
# that trace_s.py traced, seed 339's false alarm after a dropout, and 338
# on quiet90.
CHECKED_S = {
    ("outage90", "boulevard", 338): (1917.6, 2, 6),
    ("outage90", "boulevard", 339): (1761.6, 2, 4),
    ("quiet90", "boulevard", 338): (1823.6, 1, 5),
}
# pace_s.py's restart, flown only by the check.
RESTART = {"alpha": 0.3, "beta": 0.0, "track": True}


def fly(course_name, seed, profile, variant, cruise, course=None, block="profile",
        settings=None):
    """One mission flown as pace_v.fly flies it, with this study's variant
    (or `settings`, a VARIANTS-like entry, instead) and the profile's block
    (or `block`, [start, end] or None), with pace_v.py's gps and stuck
    records."""
    v = VARIANTS[variant] if settings is None else settings
    warmup_s = v.get("warmup_s", 0.0)
    warm = v.get("warm", "never")
    window = pv.block_window(profile, seed) if block == "profile" else block
    made, times, stands = [], [], []
    with pv._known_profile(profile), pq._filtering(v, made), \
            pv._warming(warmup_s, warm, times, stands), pv._blocking(window):
        r = pp.fly(course_name, seed, profile, pq.FLOWN_AS, cruise, course=course)
    windows = pv.outages(profile, seed)
    r["gps"] = {"filters": len(made),
                "restarts": sum(f.restarts for f in made) if v.get("track") else None}
    r["stuck"] = {"warmup_s": warmup_s, "warm": warm,
                  "recovery_t": [round(x, 1) for x in times],
                  "stands": [[round(a, 1), round(b, 1)] for a, b in stands],
                  "block": None if window is None else list(window),
                  "block_outage": (None if window is None
                                   else pv.overlaps(windows, window[0], window[0] + CATCH_S)),
                  "first_outage_s": round(windows[0][0], 1) if windows else None}
    return r


def failed_run(exc):
    return pv.failed_run(exc)


def check(expected_v=None, expected_s=None):
    """Fly pace_v.py's warm10 missions in `expected_v` (CHECKED_V by default)
    and pace_s.py's restart missions in `expected_s` (CHECKED_S) again, and
    compare each one's time and recovery moves (and, for restart, its
    filter restarts) with the record."""
    expected_v = CHECKED_V if expected_v is None else expected_v
    expected_s = CHECKED_S if expected_s is None else expected_s
    compared = 0
    different = []
    for (profile, course, seed), (elapsed, recovery_t) in sorted(expected_v.items()):
        got = json.loads(json.dumps(fly(course, seed, profile, BASE_VARIANT, CRUISES[0])))
        compared += 1
        want = {"elapsed_s": elapsed, "recovery_t": list(recovery_t)}
        have = {"elapsed_s": got["elapsed_s"], "recovery_t": got["stuck"]["recovery_t"]}
        if have != want:
            different.append({"reference": "pace_v.py", "profile": profile, "course": course,
                              "seed": seed, "want": want, "got": have})
    for (profile, course, seed), (elapsed, recoveries, restarts) in sorted(expected_s.items()):
        got = json.loads(json.dumps(fly(course, seed, profile, None, CRUISES[0],
                                        settings=RESTART)))
        compared += 1
        want = {"elapsed_s": elapsed, "recoveries": recoveries, "restarts": restarts}
        have = {"elapsed_s": got["elapsed_s"], "recoveries": got["recoveries"],
                "restarts": got["gps"]["restarts"]}
        if have != want:
            different.append({"reference": "pace_s.py", "profile": profile, "course": course,
                              "seed": seed, "want": want, "got": have})
    return {"reference": "pace_v.py's warm10 and pace_s.py's restart runs", "compared": compared,
            "identical": compared - len(different), "different": different[:20]}


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


def tolerances(corner, offsets):
    """pace_v.tolerances between this study's BASE_VARIANT and NOISE_VARIANT."""
    saved = pv.BASE_VARIANT, pv.NOISE_VARIANT
    pv.BASE_VARIANT, pv.NOISE_VARIANT = BASE_VARIANT, NOISE_VARIANT
    try:
        return pv.tolerances(corner, offsets)
    finally:
        pv.BASE_VARIANT, pv.NOISE_VARIANT = saved


def _check_line(c):
    return ("Check against pace_v.py's warm10 and pace_s.py's restart runs: %d compared, "
            "%d identical." % (c["compared"], c["identical"]))


def write_outputs(out_dir, runs, started, seeds, seeds_b, done, check_r=None):
    s = ps.summarise(runs)
    effects, tallies = pair_effects(runs)
    p_effects, p_tallies = profile_effects(runs)
    stuck = pv.stuck_rows(runs)
    blocks = pv.block_rows(runs)
    gps = pq.gps_rows(runs)
    worst = pz.worst_rows(runs)
    context = po.context_rows(runs)
    corner = pn.corner_rows(runs)
    maxes = pn.offset_max_rows(runs)
    offsets = pe.offset_rows(runs)
    headings_ = pd.heading_rows(runs)
    positions = pg.position_rows(runs)
    steering = ph.steer_rows(runs)
    tol = tolerances(corner, offsets)
    result = {"version": __version__, "pace_v": pv.__version__, "pace_u": pu.__version__,
              "pace_s": pz.__version__, "pace_q": pq.__version__, "pace_p": pp.__version__,
              "pace_study": ps.__version__, "rover_pilot": rp.__version__,
              "dead_reckon": dr.__version__, "done": done,
              "elapsed_s": round(time.monotonic() - started, 1), "seeds": seeds,
              "seeds_b": seeds_b,
              "human": {"marathon_m": ps.MARATHON_M, "time_s": ps.HUMAN_S,
                        "mps": round(ps.HUMAN_MPS, 4)},
              "profiles": PROFILES, "blocks": BLOCKS, "flown_as": pq.FLOWN_AS,
              "variants": VARIANTS, "catch_s": CATCH_S, "post_s": POST_S,
              "early_s": EARLY_S, "pairs": [list(x) for x in PAIRS],
              "profile_pairs": [list(x) for x in PROFILE_PAIRS], "cruises": list(CRUISES),
              "snap_m": SNAP_M, "corner_deg": pn.CORNER_DEG, "corner_m": pn.CORNER_M,
              "far_m": po.FAR_M, "runs": len(runs),
              "completed": sum(1 for r in runs if r["ok"]),
              "overview": s["overview"], "pair_effect": effects, "verdicts": tallies,
              "profile_effect": p_effects, "profile_verdicts": p_tallies, "stuck": stuck,
              "block": blocks, "tolerance": tol, "gps": gps, "worst": worst,
              "position": positions, "corner": corner, "offset": offsets,
              "offset_max": maxes, "context": context, "heading": headings_,
              "steer": steering, "check": check_r}
    with open(os.path.join(out_dir, "summary.json"), "w") as f:
        json.dump(result, f, indent=1)
    with open(os.path.join(out_dir, "runs.jsonl"), "w") as f:
        for r in runs:
            f.write(json.dumps(r) + "\n")
    md = ["# Starting the GPS average again after a gap, with the stuck check's warm-up "
          "(simulated)",
          "",
          "pace_w.py %s (pace_v.py %s, pace_u.py %s, pace_s.py %s, pace_q.py %s, pace_p.py %s, "
          "rover_pilot.py %s, dead_reckon.py %s), MV2 of Munim, Inc. Every mission is v0.18.2's "
          "real-rover pilot with v0.19.0's %g s warm-up for the stuck check after every clear of "
          "its history (warm10), with the GPS average as it ships or started again from the fix "
          "after more than 3 s without one (restart+warm10). Profiles: outage90, quiet90, "
          "quietdrift90, quiet45, blockedstart and blockedmid as in pace-v. Seeds %s; warm10:B "
          "is warm10 on seeds %s, for the seed-to-seed spread. %d of %d missions completed. "
          "Simulated rovers only, so these speeds are upper bounds."
          % (__version__, pv.__version__, pu.__version__, pz.__version__, pq.__version__,
             pp.__version__, rp.__version__, dr.__version__, WARMUP_S,
             "%d-%d" % (seeds[0], seeds[-1]) if seeds else "none",
             "%d-%d" % (seeds_b[0], seeds_b[-1]) if seeds_b else "none",
             result["completed"], len(runs)), ""]
    if check_r is not None:
        md += [_check_line(check_r), ""]
    md += ["## Tolerances from the spread between the two seed sets of warm10", ""]
    md += pf._table(["figure", "spread m", "tolerance m"],
                    [("blocks corner p95", tol["corner_spread_m"], tol["corner_tol_m"]),
                     ("p95 offset", tol["offset_spread_m"], tol["offset_tol_m"])])
    md += ["", "## The pilot's worst idea of where it is, per mission (over %g m: thrown off)"
           % SNAP_M, ""]
    md += pf._table(["profile", "variant", "course", "missions", "median of max m",
                     "largest m", "missions over %g m" % SNAP_M],
                    [(x["profile"], x["variant"], x["course"], x["missions"],
                      x["median_max_m"], x["largest_m"], x["over_snap"]) for x in worst])
    md += ["", "## Overview (courses pooled)", ""]
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
    md += ["", "## Blocked rovers (caught: a recovery move within %g s of the block's start; "
           "eligible: no outage and no stand in that time; post: moves within %g s after the "
           "block)" % (CATCH_S, POST_S), ""]
    md += pf._table(["profile", "variant", "course", "missions", "eligible", "caught", "missed",
                     "caught at all", "median catch s", "latest catch s", "post moves",
                     "missions with one"],
                    [(x["profile"], x["variant"], x["course"], x["missions"], x["eligible"],
                      x["caught"], x["missed"], x["caught_any"], x["median_catch_s"],
                      x["latest_catch_s"], x["post"], x["post_missions"]) for x in blocks])
    md += ["", "## Recovery moves (first before %g s: at the start; late: moves at or after "
           "%g s)" % (EARLY_S, EARLY_S), ""]
    md += pf._table(["profile", "variant", "course", "missions", "with a recovery",
                     "recoveries", "first before %g s" % EARLY_S, "late", "stands",
                     "median first s", "latest first s"],
                    [(x["profile"], x["variant"], x["course"], x["missions"],
                      x["with_recovery"], x["recoveries"], x["early"], x["late"], x["stands"],
                      x["median_first_s"], x["latest_first_s"]) for x in stuck])
    md += ["", "## Recovery moves and filter restarts (medians)", ""]
    md += pf._table(["profile", "variant", "course", "missions", "recoveries (median)",
                     "restarts (median)"],
                    [(x["profile"], x["variant"], x["course"], x["missions"],
                      x["median_recoveries"], x["median_restarts"]) for x in gps])
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
    ap.add_argument("--first-seed-b", type=int, default=FIRST_SEED_B)
    ap.add_argument("--seeds", type=int, default=24, help="how many seeds in each set")
    ap.add_argument("--budget-min", type=float, default=180.0)
    ap.add_argument("--courses", help="comma-separated subset of: " + ",".join(ps.COURSES))
    ap.add_argument("--profiles", help="comma-separated subset of: " + ",".join(PROFILES))
    ap.add_argument("--variants", help="comma-separated subset of: " + ",".join(VARIANTS))
    ap.add_argument("--check", action="store_true",
                    help="fly CHECKED_V and CHECKED_S again and compare with their records")
    args = ap.parse_args(argv)
    courses = ps._names(args.courses, ps.COURSES, "course")
    profiles = ps._names(args.profiles, PROFILES, "profile")
    variants = ps._names(args.variants, VARIANTS, "variant")
    # outage90 and warm10 are always flown: the rest are compared with them.
    profiles = [BASE_PROFILE] + [p for p in profiles if p != BASE_PROFILE]
    variants = [BASE_VARIANT] + [v for v in variants if v != BASE_VARIANT]
    seeds = list(range(args.first_seed, args.first_seed + args.seeds))
    seeds_b = (list(range(args.first_seed_b, args.first_seed_b + args.seeds))
               if NOISE_VARIANT in variants else [])
    os.makedirs(args.out_dir, exist_ok=True)
    started = time.monotonic()
    check_r = check() if args.check else None
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
                    for seed in (seeds_b if variant == NOISE_VARIANT else seeds):
                        try:
                            r = fly(course, seed, profile, variant, cruise)
                        except Exception as exc:
                            r = failed_run(exc)
                        r.update(profile=profile, variant=variant, cruise=cruise,
                                 course=course, seed=seed)
                        runs.append(r)
            print("%s / %s: %d runs so far, %.0f s"
                  % (profile, variant, len(runs), time.monotonic() - started), flush=True)
            write_outputs(args.out_dir, runs, started, seeds, seeds_b, False, check_r)
        if not done:
            break
    result = write_outputs(args.out_dir, runs, started, seeds, seeds_b, done, check_r)
    brief = None if check_r is None else {x: check_r[x] for x in ("compared", "identical")}
    print(json.dumps(dict(check=brief, completed=result["completed"], runs=result["runs"],
                          tolerance=result["tolerance"],
                          verdicts=[{k: v[k] for k in ("profile", "variant", "against",
                                                       "groups_faster", "groups_slower",
                                                       "groups_lost")}
                                    for v in result["verdicts"]],
                          worst=[{k: x[k] for k in ("profile", "variant", "course",
                                                    "median_max_m", "over_snap")}
                                 for x in result["worst"]],
                          block=[{k: x[k] for k in ("profile", "variant", "course", "eligible",
                                                    "missed", "median_catch_s", "post")}
                                 for x in result["block"]])), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
