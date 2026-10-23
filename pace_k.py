#!/usr/bin/env python3
"""pace_k: how long should the wheels carry the position through a GPS outage?

Since v0.15.0 the pilot steers by the wheels while the GPS has no fresh fix
(pace_i.py), and pace_j.py found that this still pays when the fixes wander
before and after each outage. But the reckoner gives up 30 s after the last
fix (dead_reckon.py's max_s), so through 45 s outages the bridging pilot
still stood still a median 86-108 s a mission, against 9-13 s with 15 s
outages. This study flies the bridging pilot with the reckoner's reach at
30 s (v0.15.0), 60 s and 120 s:

- bridge+cf0.3: the real-rover default since v0.15.0 (reach 30 s);
- bridge60+cf0.3: the same, reach 60 s;
- bridge120+cf0.3: the same, reach 120 s.

Profiles: pace_j.py's outage15, outage45 and wander45, and outage90 (90 s
outages after 600 s of sky on average).

    python pace_k.py --out-dir out --first-seed 133 --seeds 24 --check studies/pace-j/runs.jsonl

With --check it first flies seeds 109-111 of pace_j.py's outage45 and
wander45 bridge+cf0.3 missions again and compares each field by field with
pace_j.py's record. Every mission is flown by pace_j.fly itself.
Simulated rovers only, so the speeds are upper bounds. Standard library
only. By MV2 of Munim, Inc.; written with AI agents. Apache-2.0.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import sys
import time

import dead_reckon as dr
import pace_e as pe
import pace_f as pf
import pace_g as pg
import pace_h as ph
import pace_i as pi
import pace_j as pj
import pace_study as ps
import rover_pilot as rp

__version__ = "0.1.0"

# pace_j.py's outage profiles, and outages twice as long again, half as often.
PROFILES = {
    "outage15": pj.PROFILES["outage15"],
    "outage45": pj.PROFILES["outage45"],
    "wander45": pj.PROFILES["wander45"],
    "outage90": dict(pi.PROFILES["outage45"], outage_s=90.0, clear_s=600.0),
}
# The first is always flown.
BASE_PROFILE = next(iter(PROFILES))
_BRIDGE = pi.VARIANTS["bridge+cf0.3"]


def _reach(max_s):
    """The bridging pilot with the reckoner carrying the position up to max_s
    seconds after the last fix."""
    return dict(_BRIDGE, reckoner=dict(_BRIDGE.get("reckoner", {}), max_s=max_s))


# The first is the pilot as v0.15.0 flies a real rover.
VARIANTS = {
    "bridge+cf0.3": _BRIDGE,
    "bridge60+cf0.3": _reach(60.0),
    "bridge120+cf0.3": _reach(120.0),
}
BASE_VARIANT = next(iter(VARIANTS))
# (a, b): b against a, paired by seed on every profile and course.
PAIRS = (("bridge+cf0.3", "bridge60+cf0.3"), ("bridge+cf0.3", "bridge120+cf0.3"),
         ("bridge60+cf0.3", "bridge120+cf0.3"))
CRUISES = (0.8,)
# pace_j.py flew seeds 109-132; these start after them.
FIRST_SEED = 133
# pace_j.py flew these with the same settings; --check flies them again.
CHECKED = {"profiles": ("outage45", "wander45"), "variants": ("bridge+cf0.3",),
           "seeds": (109, 110, 111)}


@contextlib.contextmanager
def _known(profile, variant):
    """While inside, pace_j.fly knows the profile and pace_i.fly the variant
    by name; a name they already know is left as it is."""
    add_profile = profile not in pj.PROFILES
    add_variant = variant not in pi.VARIANTS
    if add_profile:
        pj.PROFILES[profile] = PROFILES[profile]
    if add_variant:
        pi.VARIANTS[variant] = VARIANTS[variant]
    try:
        yield
    finally:
        if add_profile:
            del pj.PROFILES[profile]
        if add_variant:
            del pi.VARIANTS[variant]


def fly(course_name, seed, profile, variant, cruise, course=None):
    """One mission flown by pace_j.fly with the profile's settings and the
    variant's reckoner."""
    with _known(profile, variant):
        return pj.fly(course_name, seed, profile, variant, cruise, course=course)


def failed_run(exc):
    return pj.failed_run(exc)


def check_pace_j(path):
    """Fly the CHECKED missions again and compare each with pace_j.py's record
    of it (its runs.jsonl): every field pace_j.py recorded must be equal. A
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
                                              "cruise": cruise, "course": course, "seed": seed,
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


def write_outputs(out_dir, runs, started, seeds, done, check=None):
    s = ps.summarise(runs)
    effects, tallies = pair_effects(runs)
    outages = pi.outage_rows(runs)
    steering = ph.steer_rows(runs)
    positions = pg.position_rows(runs)
    reckoning = pg.dr_rows(runs)
    offsets = pe.offset_rows(runs)
    result = {"version": __version__, "pace_j": pj.__version__, "pace_i": pi.__version__,
              "pace_h": ph.__version__, "pace_g": pg.__version__, "pace_study": ps.__version__,
              "rover_pilot": rp.__version__, "dead_reckon": dr.__version__, "done": done,
              "elapsed_s": round(time.monotonic() - started, 1), "seeds": seeds,
              "human": {"marathon_m": ps.MARATHON_M, "time_s": ps.HUMAN_S,
                        "mps": round(ps.HUMAN_MPS, 4)},
              "profiles": PROFILES, "variants": VARIANTS, "pairs": [list(x) for x in PAIRS],
              "cruises": list(CRUISES), "steering": rp.ROVER_STEERING,
              "dead_reckon_settings": rp.DEAD_RECKON,
              "runs": len(runs), "completed": sum(1 for r in runs if r["ok"]),
              "overview": s["overview"], "pair_effect": effects, "verdicts": tallies,
              "outage": outages, "steer": steering, "position": positions,
              "reckoner": reckoning, "offset": offsets, "check": check}
    with open(os.path.join(out_dir, "summary.json"), "w") as f:
        json.dump(result, f, indent=1)
    with open(os.path.join(out_dir, "runs.jsonl"), "w") as f:
        for r in runs:
            f.write(json.dumps(r) + "\n")
    md = ["# How long should the wheels carry the position through a GPS outage? (simulated)",
          "",
          "pace_k.py %s (pace_j.py %s, pace_i.py %s, rover_pilot.py %s, dead_reckon.py %s), MV2 "
          "of Munim, Inc. Every profile is pace_i.py's measured Mini+ with GPS outages of 15 s "
          "(after 150 s of sky on average), 45 s (after 300 s), 45 s with the fixes wandering "
          "8 m off over the 20 s before and after each outage (pace_j.py's wander45), or 90 s "
          "(after 600 s). Variants: the bridging pilot (v0.15.0 on a real rover) with the "
          "reckoner carrying the position up to 30 s (bridge+cf0.3), 60 s (bridge60+cf0.3) or "
          "120 s (bridge120+cf0.3) after the last fix. Seeds %s. %d of %d missions completed. "
          "Simulated rovers only, so these speeds are upper bounds."
          % (__version__, pj.__version__, pi.__version__, rp.__version__, dr.__version__,
             "%d-%d" % (seeds[0], seeds[-1]) if seeds else "none",
             result["completed"], len(runs)), ""]
    if check is not None:
        md += ["Check against pace_j.py's runs: %d compared, %d identical, %d missing."
               % (check["compared"], check["identical"], check["missing"]), ""]
    md += ["## Overview (courses pooled)", ""]
    md += pf._table(["profile", "variant", "completed", "made good m/s (median)", "efficiency",
                     "runs beating 0.754", "path ratio", "share stopped"],
                    [(o["profile"], o["variant"], "%d/%d" % (o["completed"], o["runs"]),
                      o["median_made_good_mps"], o["median_efficiency"], o["beat_human_pace"],
                      o["median_path_ratio"], o["share_stopped"]) for o in s["overview"]])
    md += ["", "## Longer reach against shorter, same profile", "",
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
    md += ["", "## GPS outages", ""]
    md += pf._table(["profile", "variant", "course", "missions", "reports withheld",
                     "s stood still"],
                    [(x["profile"], x["variant"], x["course"], x["missions"],
                      x["median_withheld"], x["median_stopped_s"]) for x in outages])
    md += ["", "## How hard the pilot steers", ""]
    md += pf._table(["profile", "variant", "course", "missions", "mean abs angular"],
                    [(x["profile"], x["variant"], x["course"], x["missions"],
                      x["median_mean_abs_angular"]) for x in steering])
    md += ["", "## Where the pilot thinks it is, against where it is", ""]
    md += pf._table(["profile", "variant", "course", "missions", "median m", "p95 m"],
                    [(x["profile"], x["variant"], x["course"], x["missions"],
                      x["median_position_err_m"], x["p95_position_err_m"]) for x in positions])
    md += ["", "## Dead reckoning", ""]
    md += pf._table(["profile", "variant", "course", "missions", "never trusted",
                     "first trusted s", "s on wheels alone", "abs scale error"],
                    [(x["profile"], x["variant"], x["course"], x["missions"],
                      x["never_trusted"], x["median_trusted_at_s"], x["median_bridged_s"],
                      x["median_abs_scale_error"]) for x in reckoning])
    md += ["", "## Distance from the course while driving forward", ""]
    md += pf._table(["profile", "variant", "course", "missions", "median m", "p95 m"],
                    [(x["profile"], x["variant"], x["course"], x["missions"],
                      x["median_offset_m"], x["p95_offset_m"]) for x in offsets])
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
    ap.add_argument("--check", help="pace_j.py's runs.jsonl: fly the CHECKED missions again "
                                    "and compare")
    args = ap.parse_args(argv)
    courses = ps._names(args.courses, ps.COURSES, "course")
    profiles = ps._names(args.profiles, PROFILES, "profile")
    variants = ps._names(args.variants, VARIANTS, "variant")
    # outage15 and v0.15.0's real-rover pilot are always flown: the rest are compared with them.
    profiles = [BASE_PROFILE] + [p for p in profiles if p != BASE_PROFILE]
    variants = [BASE_VARIANT] + [v for v in variants if v != BASE_VARIANT]
    seeds = list(range(args.first_seed, args.first_seed + args.seeds))
    os.makedirs(args.out_dir, exist_ok=True)
    started = time.monotonic()
    check = check_pace_j(args.check) if args.check else None
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
