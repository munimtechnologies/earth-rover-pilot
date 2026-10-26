#!/usr/bin/env python3
"""pace_t: should the stuck detector wait before it judges?

trace_s.py (studies/pace-s/TRACE.md) found that Pilot._stuck, which judges
progress on the smoothed GPS over the last 10 s, fires on rovers that are
not stuck. When the rover drives off from a standstill, or the GPS average
starts again from a single fix, the average barely moves for the first 10 s:
its fixes lag about 1.5 s and its lag has to build up. 210 of pace-s's 216
shipped missions with quiet GPS made a recovery move, and the simulator
never blocks the rover. On outage90 boulevard the same false alarm, after
each restart of the average, cost `restart` pace-s's rule R2.

Variants (all v0.18.2's real-rover pilot as pace_s.py flies it, with a 16 m
lookahead):
  a0.3          GpsFilter and Pilot._stuck as they ship
  warm          the same, but no stuck verdict until WARMUP_S after the
                stuck history was last cleared (the start, a stop, a
                bridged gap or a recovery move)
  restart+warm  warm, with pace_s.py's restart: the average started again
                from the fix after more than 3 s without one
Profiles: pace_s.py's outage90, quiet90, quietdrift90 and quiet45, and
blocked30 (quiet90 with a rover that cannot move for its first 30 s, to
see that a really stuck rover is still caught).

    python pace_t.py --out-dir out --first-seed 349 --seeds 24 --check studies/pace-s/runs.jsonl

With --check it first flies seeds 325-327 of pace_s.py's outage90 and
quiet90 a0.3 missions again and compares each field by field with the
record. Simulated rovers only, so the speeds are upper bounds. Standard
library only. By MV2 of Munim, Inc.; written with AI agents. Apache-2.0.
"""

from __future__ import annotations

import argparse
import collections
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
import pace_s as pz
import pace_study as ps
import rover_pilot as rp

__version__ = "0.1.0"

PROFILES = {
    "outage90": pz.PROFILES["outage90"],
    "quiet90": pz.PROFILES["quiet90"],
    "quietdrift90": pz.PROFILES["quietdrift90"],
    "quiet45": pz.PROFILES["quiet45"],
    "blocked30": dict(pz.PROFILES["quiet90"], blocked_until_s=30.0),
}
# The first is always flown.
BASE_PROFILE = next(iter(PROFILES))
# Profiles where the rover really is stuck for a while.
BLOCKED = ("blocked30",)
# (a, b): each variant on profile b against itself on profile a, paired by
# seed: what 30 s stuck at the start costs.
PROFILE_PAIRS = (("quiet90", "blocked30"),)
# Seconds after the stuck history was last cleared before the stuck check
# judges; Pilot._stuck then needs 0.9 of its own 10 s window on top.
WARMUP_S = 10.0
VARIANTS = {
    "a0.3": {"alpha": 0.3},
    "warm": {"alpha": 0.3, "warmup_s": WARMUP_S},
    "restart+warm": {"alpha": 0.3, "beta": 0.0, "track": True, "warmup_s": WARMUP_S},
}
# The pilot as it ships; it is always flown.
BASE_VARIANT = next(iter(VARIANTS))
# (a, b): b against a. The warm-up against the shipped pilot, and the
# restart against the warm-up alone.
PAIRS = (("a0.3", "warm"), ("warm", "restart+warm"))
CRUISES = (0.8,)
# pace_s.py flew seeds 325-348; these start after them.
FIRST_SEED = 349
# --check: pace_s.py's a0.3 flown again. Seed 327 is one trace_s.py traced.
# (ours, theirs).
CHECKED = {"profiles": ("outage90", "quiet90"), "variants": (("a0.3", "a0.3"),),
           "seeds": (325, 326, 327)}
SNAP_M = pz.SNAP_M
# A first recovery move before this many seconds counts as at the start.
EARLY_S = 30.0
NO_STUCK = {"warmup_s": None, "recovery_t": None}


class StuckHistory(collections.deque):
    """The Pilot's stuck history, noting each time the Pilot clears it."""

    cleared = True

    def clear(self):
        super().clear()
        self.cleared = True


@contextlib.contextmanager
def _warming(warmup_s, times):
    """While inside, every Pilot's stuck check gives no verdict until
    `warmup_s` after its history was last cleared, and the time of each
    stuck verdict is appended to `times`. With warmup_s 0 the verdicts are
    Pilot._stuck's own."""
    saved = rp.Pilot._stuck

    def _stuck(self, t, linear):
        h = self._history
        if not isinstance(h, StuckHistory):
            h = self._history = StuckHistory(h)
        if h.cleared:
            h.cleared = False
            self._warm_from = t
        if t - self._warm_from < warmup_s:
            return False
        stuck = saved(self, t, linear)
        if stuck:
            times.append(t)
        return stuck

    rp.Pilot._stuck = _stuck
    try:
        yield
    finally:
        rp.Pilot._stuck = saved


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
    filter and stuck warm-up, as pace_s.fly flies it, with its records;
    also the stuck record: the warm-up and the time of every recovery move."""
    v = VARIANTS[variant]
    warmup_s = v.get("warmup_s", 0.0)
    made, times = [], []
    with _known_profile(profile), pq._filtering(v, made), _warming(warmup_s, times):
        r = pp.fly(course_name, seed, profile, pq.FLOWN_AS, cruise, course=course)
    r["gps"] = {"filters": len(made),
                "restarts": sum(f.restarts for f in made) if v.get("track") else None}
    r["stuck"] = {"warmup_s": warmup_s, "recovery_t": [round(x, 1) for x in times]}
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


def stuck_rows(runs):
    """Per (profile, variant, cruise, course), over the completed missions:
    how many made a recovery move, how many moves in all, how many made
    their first before EARLY_S, and the median and latest first move."""
    rows = []
    for k, rs in sorted(pg._groups(runs).items()):
        ok = [r for r in rs if r["ok"]]
        firsts = [r["stuck"]["recovery_t"][0] for r in ok
                  if (r.get("stuck") or {}).get("recovery_t")]
        rows.append({"profile": k[0], "variant": k[1], "cruise": k[2], "course": k[3],
                     "missions": len(ok),
                     "with_recovery": sum(1 for r in ok if r["recoveries"] > 0),
                     "recoveries": sum(r["recoveries"] for r in ok),
                     "early": sum(1 for x in firsts if x < EARLY_S),
                     "median_first_s": ps._median(firsts),
                     "latest_first_s": max(firsts) if firsts else None})
    return rows


def _check_line(c):
    return ("Check against pace_s.py's runs: %d compared, %d identical, %d missing."
            % (c["compared"], c["identical"], c["missing"]))


def write_outputs(out_dir, runs, started, seeds, done, check_r=None):
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
    result = {"version": __version__, "pace_s": pz.__version__, "pace_q": pq.__version__,
              "pace_p": pp.__version__, "pace_study": ps.__version__,
              "rover_pilot": rp.__version__, "dead_reckon": dr.__version__, "done": done,
              "elapsed_s": round(time.monotonic() - started, 1), "seeds": seeds,
              "human": {"marathon_m": ps.MARATHON_M, "time_s": ps.HUMAN_S,
                        "mps": round(ps.HUMAN_MPS, 4)},
              "profiles": PROFILES, "blocked": list(BLOCKED), "flown_as": pq.FLOWN_AS,
              "variants": VARIANTS, "warmup_s": WARMUP_S, "early_s": EARLY_S,
              "pairs": [list(x) for x in PAIRS],
              "profile_pairs": [list(x) for x in PROFILE_PAIRS], "cruises": list(CRUISES),
              "snap_m": SNAP_M, "corner_deg": pn.CORNER_DEG, "corner_m": pn.CORNER_M,
              "far_m": po.FAR_M, "runs": len(runs),
              "completed": sum(1 for r in runs if r["ok"]),
              "overview": s["overview"], "pair_effect": effects, "verdicts": tallies,
              "profile_effect": p_effects, "profile_verdicts": p_tallies, "stuck": stuck,
              "gps": gps, "worst": worst, "position": positions, "corner": corner,
              "offset": offsets, "offset_max": maxes, "context": context,
              "heading": headings_, "steer": steering, "check": check_r}
    with open(os.path.join(out_dir, "summary.json"), "w") as f:
        json.dump(result, f, indent=1)
    with open(os.path.join(out_dir, "runs.jsonl"), "w") as f:
        for r in runs:
            f.write(json.dumps(r) + "\n")
    md = ["# Should the stuck detector wait before it judges? (simulated)",
          "",
          "pace_t.py %s (pace_s.py %s, pace_q.py %s, pace_p.py %s, rover_pilot.py %s, "
          "dead_reckon.py %s), MV2 of Munim, Inc. Every mission is v0.18.2's real-rover pilot "
          "as pace_s.py flies it, with Pilot._stuck as it ships (a0.3), with no stuck verdict "
          "until %g s after the stuck history was last cleared (warm), or with that and the GPS "
          "average started again from the fix after more than 3 s without one (restart+warm). "
          "Profiles: outage90 (90 s GPS outages, 1.5 m of GPS noise per axis), quiet90, "
          "quietdrift90 and quiet45 (the same idea with %g m), and blocked30 (quiet90 with a rover "
          "that cannot move for its first 30 s). Seeds %s. %d of %d missions completed. "
          "Simulated rovers only, so these speeds are upper bounds."
          % (__version__, pz.__version__, pq.__version__, pp.__version__, rp.__version__,
             dr.__version__, WARMUP_S, pq.QUIET_NOISE_M,
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
    md += ["", "## Recovery moves (first before %g s: at the start)" % EARLY_S, ""]
    md += pf._table(["profile", "variant", "course", "missions", "with a recovery",
                     "recoveries", "first before %g s" % EARLY_S, "median first s",
                     "latest first s"],
                    [(x["profile"], x["variant"], x["course"], x["missions"],
                      x["with_recovery"], x["recoveries"], x["early"], x["median_first_s"],
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
                          stuck=[{k: x[k] for k in ("profile", "variant", "course",
                                                    "with_recovery", "early")}
                                 for x in result["stuck"]])), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
