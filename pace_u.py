#!/usr/bin/env python3
"""pace_u: the stuck detector's warm-up again, 5 s or 10 s, with a fair test
of a rover that really is stuck.

pace_t.py (studies/pace-t/GRADE.md) found that a 10 s warm-up after each
clear of the stuck history removed the false recovery move the shipped
Pilot._stuck makes seconds after every start (in 0 of 288 missions against
22-23 of 24 per course with quiet GPS), was faster on every quiet course and
slower on none. It still failed its pre-stated rule R2, which asked for a
recovery move before 30 s in every mission of a rover blocked for its first
30 s: on two seeds a GPS outage began while the rover was blocked, so the
pilot stood still with no fix, and the block was over when the fixes came
back. pace_u.py flies the warm-up again on fresh seeds, with a 5 s warm-up
too, records when each mission's first GPS outage begins, and counts a
blocked mission as one the check must catch only if its first outage
begins after the block ends.

Variants (all v0.18.2's real-rover pilot as pace_t.py flies it):
  a0.3            GpsFilter and Pilot._stuck as they ship
  warm5, warm10   no stuck verdict until 5 s or 10 s after the stuck
                  history was last cleared (warm10 is pace_t.py's warm)
  restart+warm5,  the same with pace_s.py's restart: the GPS average
  restart+warm10  started again from the fix after more than 3 s without
                  one (restart+warm10 is pace_t.py's restart+warm)
Profiles: pace_t.py's outage90, quiet90, quietdrift90, quiet45 and
blocked30.

    python pace_u.py --out-dir out --first-seed 373 --seeds 24 --check studies/pace-s/runs.jsonl --check-t

With --check it first flies seeds 325-327 of pace_s.py's outage90 and
quiet90 a0.3 missions again and compares each field by field with the
record; with --check-t it flies 11 of pace_t.py's missions again and
compares their times and recovery moves with pace_t.py's record. Simulated
rovers only, so the speeds are upper bounds. Standard library only.
By MV2 of Munim, Inc.; written with AI agents. Apache-2.0.
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
import pace_t as pt
import rover_pilot as rp

__version__ = "0.1.0"

PROFILES = pt.PROFILES
BASE_PROFILE = pt.BASE_PROFILE
BLOCKED = pt.BLOCKED
PROFILE_PAIRS = pt.PROFILE_PAIRS
# blocked30's rover cannot move before this; a blocked mission counts as one
# the stuck check must catch only if its first GPS outage begins at or after it.
BLOCK_S = 30.0
VARIANTS = {
    "a0.3": {"alpha": 0.3},
    "warm5": {"alpha": 0.3, "warmup_s": 5.0},
    "warm10": {"alpha": 0.3, "warmup_s": 10.0},
    "restart+warm5": {"alpha": 0.3, "beta": 0.0, "track": True, "warmup_s": 5.0},
    "restart+warm10": {"alpha": 0.3, "beta": 0.0, "track": True, "warmup_s": 10.0},
}
# The pilot as it ships; it is always flown.
BASE_VARIANT = next(iter(VARIANTS))
# (a, b): b against a. Each warm-up against the shipped pilot, the shorter
# against the longer, and each restart against its warm-up alone.
PAIRS = (("a0.3", "warm5"), ("a0.3", "warm10"), ("warm10", "warm5"),
         ("warm5", "restart+warm5"), ("warm10", "restart+warm10"))
CRUISES = (0.8,)
# pace_t.py flew seeds 349-372; these start after them.
FIRST_SEED = 373
# --check: pace_s.py's a0.3 flown again, as pace_t.py did.
CHECKED = pt.CHECKED
# pace_t.py's names for the variants it flew.
AS_PACE_T = {"a0.3": "a0.3", "warm10": "warm", "restart+warm10": "restart+warm"}
# --check-t: (profile, pace_t.py's variant, ours, course, seed) ->
# (elapsed_s, recovery_t) in pace_t.py's record (studies/pace-t/runs.jsonl):
# both blocked30 seeds without a recovery move, the late recovery moves on
# quietdrift90 blocks, and seed 349's 94 s on quiet90 boulevard.
CHECKED_T = {
    ("quiet90", "a0.3", "a0.3", "boulevard", 349): (1839.6, [9.1]),
    ("quiet90", "warm", "warm10", "boulevard", 349): (1745.6, []),
    ("quiet90", "a0.3", "a0.3", "boulevard", 368): (1839.6, [9.1]),
    ("blocked30", "a0.3", "a0.3", "boulevard", 352): (1837.6, []),
    ("blocked30", "a0.3", "a0.3", "boulevard", 368): (1845.6, [9.1]),
    ("blocked30", "warm", "warm10", "boulevard", 349): (1839.6, [19.1]),
    ("blocked30", "warm", "warm10", "boulevard", 352): (1837.6, []),
    ("blocked30", "warm", "warm10", "boulevard", 368): (1845.6, []),
    ("quietdrift90", "warm", "warm10", "blocks", 358): (1645.6, [1434.0]),
    ("quietdrift90", "warm", "warm10", "blocks", 359): (1683.6, [1470.0]),
    ("quietdrift90", "restart+warm", "restart+warm10", "blocks", 352): (1673.6, [793.9]),
}
SNAP_M = pz.SNAP_M
# A first recovery move before this many seconds counts as at the start.
EARLY_S = pt.EARLY_S
NO_STUCK = {"warmup_s": None, "recovery_t": None, "first_outage_s": None}


def _first_outage(profile, seed):
    """When the first GPS outage of a mission on this profile (a dict)
    begins, from the same windows OutageRover draws; None without outages."""
    windows = pi.outage_windows(seed, float(profile.get("outage_s", 0.0)),
                                float(profile.get("clear_s", 150.0)))
    return round(windows[0][0], 1) if windows else None


def first_outage_s(profile, seed):
    return _first_outage(PROFILES[profile], seed)


def fly(course_name, seed, profile, variant, cruise, course=None):
    """One mission flown as pace_t.fly flies it, with the variant's GPS filter
    and warm-up; the stuck record also gives when the first outage began."""
    v = VARIANTS[variant]
    warmup_s = v.get("warmup_s", 0.0)
    made, times = [], []
    with pt._known_profile(profile), pq._filtering(v, made), pt._warming(warmup_s, times):
        r = pp.fly(course_name, seed, profile, pq.FLOWN_AS, cruise, course=course)
    r["gps"] = {"filters": len(made),
                "restarts": sum(f.restarts for f in made) if v.get("track") else None}
    r["stuck"] = {"warmup_s": warmup_s, "recovery_t": [round(x, 1) for x in times],
                  "first_outage_s": first_outage_s(profile, seed)}
    return r


def failed_run(exc):
    return dict(pz.failed_run(exc), stuck=dict(NO_STUCK))


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


def check_t(expected=None):
    """Fly pace_t.py's missions in `expected` (CHECKED_T by default) again and
    compare each one's time and recovery moves with pace_t.py's record."""
    expected = CHECKED_T if expected is None else expected
    compared = 0
    different = []
    for (profile, theirs, ours, course, seed), (elapsed, recovery_t) in sorted(expected.items()):
        got = json.loads(json.dumps(fly(course, seed, profile, ours, CRUISES[0])))
        compared += 1
        want = {"elapsed_s": elapsed, "recovery_t": list(recovery_t)}
        have = {"elapsed_s": got["elapsed_s"], "recovery_t": got["stuck"]["recovery_t"]}
        if have != want:
            different.append({"profile": profile, "variant": ours, "against": theirs,
                              "course": course, "seed": seed, "want": want, "got": have})
    return {"reference": "pace_t.py's runs", "compared": compared,
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


def _eligible(r):
    """A mission whose GPS stayed up until the block was over: its first
    outage begins at or after BLOCK_S, or it has none."""
    first = (r.get("stuck") or {}).get("first_outage_s")
    return first is None or first >= BLOCK_S


def stuck_rows(runs):
    """Per (profile, variant, cruise, course), over the completed missions:
    how many made a recovery move, how many moves in all, how many made
    their first before EARLY_S, how many moves came at or after EARLY_S
    (late), how many missions had GPS until BLOCK_S (eligible) and how many
    of those made their first move before EARLY_S, and the median and
    latest first move."""
    rows = []
    for k, rs in sorted(pg._groups(runs).items()):
        ok = [r for r in rs if r["ok"]]
        times = [(r.get("stuck") or {}).get("recovery_t") or [] for r in ok]
        firsts = [x[0] for x in times if x]
        eligible = [r for r in ok if _eligible(r)]
        caught = sum(1 for r in eligible
                     if r["stuck"]["recovery_t"] and r["stuck"]["recovery_t"][0] < EARLY_S)
        rows.append({"profile": k[0], "variant": k[1], "cruise": k[2], "course": k[3],
                     "missions": len(ok),
                     "with_recovery": sum(1 for r in ok if r["recoveries"] > 0),
                     "recoveries": sum(r["recoveries"] for r in ok),
                     "early": sum(1 for x in firsts if x < EARLY_S),
                     "late": sum(1 for x in times for y in x if y >= EARLY_S),
                     "eligible": len(eligible), "early_eligible": caught,
                     "median_first_s": ps._median(firsts),
                     "latest_first_s": max(firsts) if firsts else None})
    return rows


def _check_line(c):
    return ("Check against pace_s.py's runs: %d compared, %d identical, %d missing."
            % (c["compared"], c["identical"], c["missing"]))


def _check_t_line(c):
    return ("Check against pace_t.py's runs: %d compared, %d identical."
            % (c["compared"], c["identical"]))


def write_outputs(out_dir, runs, started, seeds, done, check_r=None, check_t_r=None):
    s = ps.summarise(runs)
    effects, tallies = pair_effects(runs)
    p_effects, p_tallies = profile_effects(runs)
    stuck = stuck_rows(runs)
    gps = pq.gps_rows(runs)
    worst = pz.worst_rows(runs)
    context = po.context_rows(runs)
    corner = pn.corner_rows(runs)
    maxes = pn.offset_max_rows(runs)
    offsets = pe.offset_rows(runs)
    headings_ = pd.heading_rows(runs)
    positions = pg.position_rows(runs)
    steering = ph.steer_rows(runs)
    result = {"version": __version__, "pace_t": pt.__version__, "pace_s": pz.__version__,
              "pace_q": pq.__version__, "pace_p": pp.__version__,
              "pace_study": ps.__version__, "rover_pilot": rp.__version__,
              "dead_reckon": dr.__version__, "done": done,
              "elapsed_s": round(time.monotonic() - started, 1), "seeds": seeds,
              "human": {"marathon_m": ps.MARATHON_M, "time_s": ps.HUMAN_S,
                        "mps": round(ps.HUMAN_MPS, 4)},
              "profiles": PROFILES, "blocked": list(BLOCKED), "block_s": BLOCK_S,
              "flown_as": pq.FLOWN_AS, "variants": VARIANTS, "early_s": EARLY_S,
              "pairs": [list(x) for x in PAIRS],
              "profile_pairs": [list(x) for x in PROFILE_PAIRS], "cruises": list(CRUISES),
              "snap_m": SNAP_M, "corner_deg": pn.CORNER_DEG, "corner_m": pn.CORNER_M,
              "far_m": po.FAR_M, "runs": len(runs),
              "completed": sum(1 for r in runs if r["ok"]),
              "overview": s["overview"], "pair_effect": effects, "verdicts": tallies,
              "profile_effect": p_effects, "profile_verdicts": p_tallies, "stuck": stuck,
              "gps": gps, "worst": worst, "position": positions, "corner": corner,
              "offset": offsets, "offset_max": maxes, "context": context,
              "heading": headings_, "steer": steering, "check": check_r,
              "check_t": check_t_r}
    with open(os.path.join(out_dir, "summary.json"), "w") as f:
        json.dump(result, f, indent=1)
    with open(os.path.join(out_dir, "runs.jsonl"), "w") as f:
        for r in runs:
            f.write(json.dumps(r) + "\n")
    md = ["# The stuck detector's warm-up again: 5 s or 10 s, and a fair stuck test (simulated)",
          "",
          "pace_u.py %s (pace_t.py %s, pace_s.py %s, pace_q.py %s, pace_p.py %s, rover_pilot.py "
          "%s, dead_reckon.py %s), MV2 of Munim, Inc. Every mission is v0.18.2's real-rover pilot "
          "as pace_t.py flies it, with Pilot._stuck as it ships (a0.3), with no stuck verdict "
          "until 5 s or 10 s after the stuck history was last cleared (warm5, warm10), or with "
          "that and the GPS average started again from the fix after more than 3 s without one "
          "(restart+warm5, restart+warm10). Profiles: outage90 (90 s GPS outages, 1.5 m of GPS "
          "noise per axis), quiet90, quietdrift90 and quiet45 (the same idea with %g m), and "
          "blocked30 (quiet90 with a rover that cannot move for its first %g s). Seeds %s. %d of "
          "%d missions completed. Simulated rovers only, so these speeds are upper bounds."
          % (__version__, pt.__version__, pz.__version__, pq.__version__, pp.__version__,
             rp.__version__, dr.__version__, pq.QUIET_NOISE_M, BLOCK_S,
             "%d-%d" % (seeds[0], seeds[-1]) if seeds else "none",
             result["completed"], len(runs)), ""]
    if check_r is not None:
        md += [_check_line(check_r), ""]
    if check_t_r is not None:
        md += [_check_t_line(check_t_r), ""]
    md += ["## Overview (courses pooled)", ""]
    md += pf._table(["profile", "variant", "completed", "made good m/s (median)", "efficiency",
                     "runs beating 0.754", "path ratio", "share stopped"],
                    [(o["profile"], o["variant"], "%d/%d" % (o["completed"], o["runs"]),
                      o["median_made_good_mps"], o["median_efficiency"], o["beat_human_pace"],
                      o["median_path_ratio"], o["share_stopped"]) for o in s["overview"]])
    md += ["", "## Recovery moves (first before %g s: at the start; late: moves at or after "
           "%g s; eligible: GPS up until %g s)" % (EARLY_S, EARLY_S, BLOCK_S), ""]
    md += pf._table(["profile", "variant", "course", "missions", "with a recovery",
                     "recoveries", "first before %g s" % EARLY_S, "late", "eligible",
                     "eligible caught early", "median first s", "latest first s"],
                    [(x["profile"], x["variant"], x["course"], x["missions"],
                      x["with_recovery"], x["recoveries"], x["early"], x["late"],
                      x["eligible"], x["early_eligible"], x["median_first_s"],
                      x["latest_first_s"]) for x in stuck])
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
    md += ["", "## Recovery moves and filter restarts (medians)", ""]
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
    ap.add_argument("--check", help="pace_s.py's runs.jsonl: fly CHECKED again and compare")
    ap.add_argument("--check-t", action="store_true",
                    help="fly CHECKED_T again and compare with pace_t.py's record")
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
    check_t_r = check_t() if args.check_t else None
    if check_t_r is not None:
        print(_check_t_line(check_t_r), flush=True)
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
            write_outputs(args.out_dir, runs, started, seeds, False, check_r, check_t_r)
        if not done:
            break
    result = write_outputs(args.out_dir, runs, started, seeds, done, check_r, check_t_r)
    brief = None if check_r is None else {x: check_r[x]
                                          for x in ("compared", "identical", "missing")}
    brief_t = None if check_t_r is None else {x: check_t_r[x]
                                              for x in ("compared", "identical")}
    print(json.dumps(dict(check=brief, check_t=brief_t, completed=result["completed"],
                          runs=result["runs"],
                          verdicts=[{k: v[k] for k in ("profile", "variant", "against",
                                                       "groups_faster", "groups_slower",
                                                       "groups_lost")}
                                    for v in result["verdicts"]],
                          stuck=[{k: x[k] for k in ("profile", "variant", "course",
                                                    "with_recovery", "early", "late",
                                                    "eligible", "early_eligible")}
                                 for x in result["stuck"]])), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
