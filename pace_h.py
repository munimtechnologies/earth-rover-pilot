#!/usr/bin/env python3
"""pace_h: should dead reckoning stay on by default, and in what form?

pace_g.py found that on a clean GPS the pilot is 1.5-7% slower with dead
reckoning (v0.13.0's real-rover default) than without it, while through GPS
gaps it saves the pilot from stopping. The reckoner starts again from every
fix, so the position it gives jumps with each fix's noise and drifts sideways
between fixes by the heading's error; the pilot weaves, its straight stretches
break, and the compass-bias learner fits a few stretches a mission instead of
dozens (studies/pace-g/GRADE.md).

This study flies, on fresh seeds, the measured Mini+ with 3 and 8 deg of
compass noise and with 30% of GPS fixes missing:

- dr+cf0.3: v0.13.0 on a real rover (dead reckoning and --smooth-heading);
- cf0.3: --smooth-heading only;
- bridge+cf0.3: dead reckoning used only while the GPS has no fresh fix
  (BridgePilot), otherwise the GPS filter's position, as cf0.3 drives;
- drg0.3+cf0.3: the reckoner moved 0.3 of the way to each fix (gain 0.3)
  instead of starting again from it;
- dr+cf0.3+kb: v0.13.0 with the compass bias known from the start, to tell
  the learner's part of the cost from the jumps' part.

Besides pace_g.py's fields every mission records how hard the pilot steers
while driving forward (the mean |angular| applied).

    python pace_h.py --out-dir out --first-seed 61 --seeds 24 --check studies/pace-g/runs.jsonl

With --check it first flies seeds 37-39 of pace_g.py's measured and
dropout0.3 missions with dr+cf0.3 and cf0.3 again and compares each field by
field with pace_g.py's record. Simulated rovers only, so the speeds are upper
bounds. Standard library only. By MV2 of Munim, Inc.; written with AI agents.
Apache-2.0.
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
import pace_study as ps
import rover_pilot as rp

__version__ = "0.1.0"

# pace_g.py's profiles (the measured Mini+ reporting its wheels' RPM).
PROFILES = {name: pg.PROFILES[name]
            for name in ("measured", "noise8", "dropout0.3", "dropout0.3-noise8")}
# The first is the reference every other profile is compared with.
BASE_PROFILE = next(iter(PROFILES))
# The first is the pilot as v0.13.0 flies a real rover.
VARIANTS = {
    "dr+cf0.3": {"dead_reckon": True, "smooth": rp.SMOOTH_HEADING},
    "cf0.3": {"smooth": rp.SMOOTH_HEADING},
    "bridge+cf0.3": {"dead_reckon": True, "bridge": True, "smooth": rp.SMOOTH_HEADING},
    "drg0.3+cf0.3": {"dead_reckon": True, "reckoner": {"gain": 0.3},
                     "smooth": rp.SMOOTH_HEADING},
    "dr+cf0.3+kb": {"dead_reckon": True, "known_bias": True, "smooth": rp.SMOOTH_HEADING},
}
BASE_VARIANT = next(iter(VARIANTS))
# (a, b): b against a, paired by seed on every profile and course.
PAIRS = (("cf0.3", "dr+cf0.3"), ("cf0.3", "bridge+cf0.3"), ("dr+cf0.3", "bridge+cf0.3"),
         ("dr+cf0.3", "drg0.3+cf0.3"), ("cf0.3", "drg0.3+cf0.3"),
         ("cf0.3", "dr+cf0.3+kb"), ("dr+cf0.3", "dr+cf0.3+kb"))
CRUISES = (0.8,)
# pace_g.py flew seeds 37-60; these start after them.
FIRST_SEED = 61
# pace_g.py flew these with the same settings; --check flies them again.
CHECKED = {"profiles": ("measured", "dropout0.3"), "variants": ("dr+cf0.3", "cf0.3"),
           "seeds": (37, 38, 39)}


class BridgePilot(rp.Pilot):
    """A Pilot that steers by the wheels' estimate only while the GPS has no
    fresh fix, and by the GPS filter otherwise. The estimate is still asked for
    every tick, so it follows the rover's turns as it does in the Pilot."""

    def _position(self, t):
        if self.dr is None:
            return super()._position(t)
        pos = self.dr.position(t)
        if pos is not None and not self.gps.has_fix(t):
            return pos
        return self.gps.lat, self.gps.lon


def make_estimator(variant, sim):
    """The learner as pace_g.py counts it, and how many calibrations it was given:
    with known_bias it starts at the bias that cancels the rover's compass error,
    counted as one calibration so that later fits move it by the learner's gain."""
    est = pe.CountingEstimator()
    if VARIANTS[variant].get("known_bias"):
        est.bias = rp.wrap180(-sim.compass_error)
        est.calibrations = 1
        return est, 1
    return est, 0


def fly(course_name, seed, profile, variant, cruise, course=None):
    """One mission flown as pace_g.fly flies it, with the variant's dead
    reckoning, and how hard the pilot steered while driving forward."""
    course = course or ps.COURSES[course_name]
    pts = course["points"]
    sim = pd.DistortedRover([pts[i] for i in course["checkpoints"]], seed=seed, **PROFILES[profile])
    v = VARIANTS[variant]
    smoother = rp.HeadingSmoother(**v["smooth"]) if "smooth" in v else None
    # As the command line builds it for a real rover, with the variant's changes.
    reckoner = (dr.DeadReckoner(**dict(rp.DEAD_RECKON, **v.get("reckoner", {})))
                if v.get("dead_reckon") else None)
    planner = ps.CoursePlanner(course, sim.lat0, sim.lon0)
    errors, offsets, misses = [], [], []
    steer = [0.0, 0]
    next_offset_t = [0.0]
    trusted_at = [None]
    pilot = None

    def sleep(seconds):
        # Only reads; the mission is the same without it.
        if reckoner is not None and trusted_at[0] is None and reckoner.trusted:
            trusted_at[0] = sim.t
        if sim.applied[0] > 0:
            steer[0] += abs(sim.applied[1])
            steer[1] += 1
            h = pilot._heading_now
            if h is not None:
                errors.append(rp.wrap180(h - sim.heading))
            if sim.t >= next_offset_t[0]:
                offsets.append(pe.course_offset(pts, sim.north, sim.east))
                miss = pg.position_error(pilot.pos, sim)
                if miss is not None:
                    misses.append(miss)
                next_offset_t[0] = sim.t + pg.POSITION_EVERY_S
        sim.sleep(seconds)

    cls = BridgePilot if v.get("bridge") else rp.Pilot
    pilot = cls(sim, clock=sim.clock, sleep=sleep,
                steering=rp.make_steering(False, cruise=cruise), planner=planner,
                smooth_heading=smoother, dead_reckon=reckoner)
    est, given = make_estimator(variant, sim)
    pilot.heading = est
    total_m = ps.route_m(course)
    ideal_mps = cruise * sim.max_speed_mps
    res = pilot.run(timeout_s=3.0 * total_m / ideal_mps + 300.0)
    reached = len(res["reached"])
    done_m = ps.route_m(course, upto=reached)
    elapsed = res["elapsed_s"]
    made_good = done_m / elapsed if elapsed else 0.0
    spreads = est.spreads
    reckoned = None
    if reckoner is not None:
        reckoned = dict(res["dead_reckon"],
                        trusted_at_s=None if trusted_at[0] is None else round(trusted_at[0], 1),
                        # The learned metres per RPM over the rover's own: 1 is right.
                        learned_scale=round(reckoner.mps_per_rpm / sim.wheel_mps_per_rpm, 4))
    return {"ok": res["ok"], "reason": res["reason"], "elapsed_s": elapsed,
            "reached": reached, "checkpoints": res["checkpoints"], "reports": res["reports"],
            "recoveries": res["recoveries"], "plans": res["plans"],
            "route_m": round(done_m, 1), "travelled_m": round(sim.travelled, 1),
            "made_good_mps": round(made_good, 4), "ideal_mps": round(ideal_mps, 4),
            "efficiency": round(made_good / ideal_mps, 4),
            "time_s": {k: round(x, 1) for k, x in sim.time_in.items()},
            "heading_err": pd.heading_stats(errors),
            # Calibrations the learner made itself (a known bias is not counted).
            "learner": {"calibrations": est.calibrations - given, "breaks": est.breaks,
                        "fits": est.fits, "spread_checked": est.spread_checked,
                        "spread_rejected": est.spread_rejected,
                        "median_spread": ps._median(spreads, 4),
                        "bias_deg": round(est.bias, 2),
                        # The bias that would cancel the compass error at the end.
                        "bias_error_deg": round(rp.wrap180(est.bias + sim.compass_error), 2)},
            "offset": pe.offset_stats(offsets),
            "position_err": pe.offset_stats(misses),
            "dead_reckon": reckoned,
            "steer": {"n": steer[1],
                      "mean_abs_angular": round(steer[0] / steer[1], 4) if steer[1] else None}}


def failed_run(exc):
    return dict(pg.failed_run(exc), steer={"n": 0, "mean_abs_angular": None})


def check_pace_g(path):
    """Fly the CHECKED missions again and compare each with pace_g.py's record
    of it (its runs.jsonl): every field pace_g.py recorded must be equal. A
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
    """For each PAIRS (a, b) and profile: b against a per cruise x course, paired
    by seed, with the median time difference as a share of a's median; and the
    tally per (a, b, profile): groups faster / slower (paired sign test
    p < 0.05), courses where a or b completed more, the largest share."""
    groups = pg._groups(runs)
    seen = {k[0] for k in groups}
    profiles = [p for p in PROFILES if p in seen] + sorted(seen - set(PROFILES))
    effects, tallies = [], []
    for a, b in PAIRS:
        for profile in profiles:
            faster = slower = lost = gained = n = 0
            largest = None
            for (p, v, c, m) in sorted(groups):
                if (p, v) != (profile, b) or (p, a, c, m) not in groups:
                    continue
                base = groups[(p, a, c, m)]
                cmp_ = ps.compare(base, groups[(p, b, c, m)])
                base_med = ps._median([r["elapsed_s"] for r in base if r["ok"]])
                share = (round(cmp_["median_time_diff_s"] / base_med, 4)
                         if base_med and cmp_["median_time_diff_s"] is not None else None)
                effects.append(dict(profile=p, variant=b, against=a, cruise=c, course=m,
                                    median_time_diff_share=share, **cmp_))
                n += 1
                if cmp_["sign_test_p"] is not None and cmp_["sign_test_p"] < 0.05:
                    faster += cmp_["faster"] > cmp_["slower"]
                    slower += cmp_["slower"] > cmp_["faster"]
                lost += cmp_["only_a_completed"] > cmp_["only_b_completed"]
                gained += cmp_["only_b_completed"] > cmp_["only_a_completed"]
                if share is not None and (largest is None or abs(share) > abs(largest)):
                    largest = share
            if n:
                tallies.append({"profile": profile, "variant": b, "against": a, "groups": n,
                                "groups_faster": faster, "groups_slower": slower,
                                "groups_lost": lost, "groups_gained": gained,
                                "largest_median_diff_share": largest})
    return effects, tallies


def steer_rows(runs):
    """Per (profile, variant, cruise, course): over the completed missions, the
    median of each mission's mean |angular| applied while driving forward."""
    rows = []
    for k, rs in sorted(pg._groups(runs).items()):
        xs = [r["steer"]["mean_abs_angular"] for r in rs
              if r["ok"] and r.get("steer") and r["steer"]["mean_abs_angular"] is not None]
        rows.append({"profile": k[0], "variant": k[1], "cruise": k[2], "course": k[3],
                     "missions": len(xs), "median_mean_abs_angular": ps._median(xs, 4)})
    return rows


def write_outputs(out_dir, runs, started, seeds, done, check=None):
    s = ps.summarise(runs)
    effects, tallies = pair_effects(runs)
    headings = pd.heading_rows(runs)
    learner = pe.learner_rows(runs)
    offsets = pe.offset_rows(runs)
    positions = pg.position_rows(runs)
    reckoning = pg.dr_rows(runs)
    steering = steer_rows(runs)
    result = {"version": __version__, "pace_g": pg.__version__, "pace_f": pf.__version__,
              "pace_e": pe.__version__, "pace_d": pd.__version__,
              "pace_study": ps.__version__, "rover_pilot": rp.__version__,
              "dead_reckon": dr.__version__, "done": done,
              "elapsed_s": round(time.monotonic() - started, 1), "seeds": seeds,
              "human": {"marathon_m": ps.MARATHON_M, "time_s": ps.HUMAN_S,
                        "mps": round(ps.HUMAN_MPS, 4)},
              "profiles": PROFILES, "variants": VARIANTS, "pairs": [list(x) for x in PAIRS],
              "cruises": list(CRUISES), "steering": rp.ROVER_STEERING,
              "dead_reckon_settings": rp.DEAD_RECKON,
              "runs": len(runs), "completed": sum(1 for r in runs if r["ok"]),
              "overview": s["overview"], "pair_effect": effects, "verdicts": tallies,
              "steer": steering, "position": positions, "reckoner": reckoning,
              "learner": learner, "offset": offsets, "heading": headings, "check": check}
    with open(os.path.join(out_dir, "summary.json"), "w") as f:
        json.dump(result, f, indent=1)
    with open(os.path.join(out_dir, "runs.jsonl"), "w") as f:
        for r in runs:
            f.write(json.dumps(r) + "\n")
    md = ["# Should dead reckoning stay on by default? (simulated)", "",
          "pace_h.py %s (pace_g.py %s, rover_pilot.py %s, dead_reckon.py %s), MV2 of Munim, Inc. "
          "Every profile is pace_g.py's measured Mini+ (orientation every 0.5 s, 48 deg/s, 0.5 s "
          "latency, GPS every 2 s and 1.5 s late, 3 deg of compass noise, a -25 deg compass error "
          "to learn, wheels reporting RPM), with 8 deg of noise, 30%% of GPS fixes missing, or "
          "both. Variants: dr+cf0.3 (v0.13.0 on a real rover), cf0.3 (--smooth-heading only), "
          "bridge+cf0.3 (dead reckoning only through GPS gaps), drg0.3+cf0.3 (dead reckoning "
          "moved 0.3 of the way to each fix), dr+cf0.3+kb (v0.13.0 with the compass bias known "
          "from the start). Seeds %s. %d of %d missions completed. Simulated rovers only, so "
          "these speeds are upper bounds."
          % (__version__, pg.__version__, rp.__version__, dr.__version__,
             "%d-%d" % (seeds[0], seeds[-1]) if seeds else "none",
             result["completed"], len(runs)), ""]
    if check is not None:
        md += ["Check against pace_g.py's runs: %d compared, %d identical, %d missing."
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
    md += ["", "## How hard the pilot steers", "",
           "Median over the completed missions of each mission's mean |angular| applied while "
           "driving forward.", ""]
    md += pf._table(["profile", "variant", "course", "missions", "mean abs angular"],
                    [(x["profile"], x["variant"], x["course"], x["missions"],
                      x["median_mean_abs_angular"]) for x in steering])
    md += ["", "## The compass-bias learner", ""]
    md += pf._table(["profile", "variant", "course", "missions", "median calibrations",
                     "median breaks", "median abs bias error deg"],
                    [(x["profile"], x["variant"], x["course"], x["missions"],
                      x["median_calibrations"], x["median_breaks"],
                      x["median_abs_bias_error_deg"]) for x in learner])
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
    ap.add_argument("--check", help="pace_g.py's runs.jsonl: fly the CHECKED missions again "
                                    "and compare")
    args = ap.parse_args(argv)
    courses = ps._names(args.courses, ps.COURSES, "course")
    profiles = ps._names(args.profiles, PROFILES, "profile")
    variants = ps._names(args.variants, VARIANTS, "variant")
    # measured and v0.13.0's real-rover pilot are always flown: the rest are compared with them.
    profiles = [BASE_PROFILE] + [p for p in profiles if p != BASE_PROFILE]
    variants = [BASE_VARIANT] + [v for v in variants if v != BASE_VARIANT]
    seeds = list(range(args.first_seed, args.first_seed + args.seeds))
    os.makedirs(args.out_dir, exist_ok=True)
    started = time.monotonic()
    check = check_pace_g(args.check) if args.check else None
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
