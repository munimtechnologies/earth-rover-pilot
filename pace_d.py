#!/usr/bin/env python3
"""pace_d: what a compass error that lasts costs the pilot, and whether --smooth-heading still helps.

pace_c.py (studies/pace-c/GRADE.md) drew the compass noise afresh for every
orientation report, and rover_pilot 0.12.0's --smooth-heading (HeadingSmoother)
won back most of what 10 deg of it cost. A real compass is also wrong in ways
that last: a magnet near it that nobody corrected for (hard iron) bends every
reading by an amount that depends on the heading, and the error can wander
slowly. The pilot learns one compass bias from the GPS course on straight
stretches (HeadingEstimator). This study asks what errors like these cost the
pilot as it ships, how much of them that bias learner absorbs, and whether
--smooth-heading still helps, or hurts, with them.

Profiles, all pace_b.py's measured Mini+ (orientation every 0.5 s, 48 deg/s
per unit of angular, 0.5 s latency, GPS every 2 s, 3 deg of noise per report):

- measured, measured-noise10: pace_b.py's, flown again; with --check every
  mission must come out exactly as pace_c.py recorded it;
- hardiron10, hardiron20: the error gains A * sin(heading + phase), A = 10 or
  20 deg, with the phase drawn for each seed;
- drift10: the error gains a slow random drift (Ornstein-Uhlenbeck: standard
  deviation 10 deg, time constant 120 s, stepped every second of simulated time).

Variants: shipped (the pilot as it ships) and cf0.3 (--smooth-heading:
HeadingSmoother with SMOOTH_HEADING). Each profile is compared seed by seed
with measured, flown by the same variant, and cf0.3 with shipped on the same
profile. Each mission also records how far the heading the pilot steered by
was from where the rover really pointed, while it drove forward.

    python pace_d.py --out-dir out --seeds 12 --check studies/pace-c/runs.jsonl

Simulated rovers only, so the speeds are upper bounds. Standard library only.
By MV2 of Munim, Inc.; written with AI agents. Apache-2.0.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import statistics
import sys
import time

import pace_b as pb
import pace_c as pc
import pace_study as ps
import rover_pilot as rp

__version__ = "0.1.0"


class DistortedRover(pb.MeasuredRover):
    """MeasuredRover whose compass error also depends on the heading, or drifts.

    hard_iron_deg: the error gains hard_iron_deg * sin(heading + phase_deg), the
    once-per-turn error an uncorrected magnet near the compass gives. drift_deg,
    drift_tau_s: the error gains an Ornstein-Uhlenbeck drift with that standard
    deviation and time constant, stepped every drift_step_s of simulated time.
    The phase and the drift come from a generator of their own, seeded from
    the seed, so the rover's own draws (GPS, noise) are a MeasuredRover's with
    the same seed; with both 0 it flies exactly as one."""

    def __init__(self, checkpoints_m, seed=0, hard_iron_deg=0.0, drift_deg=0.0,
                 drift_tau_s=120.0, drift_step_s=1.0, **kw):
        self.hard_iron_deg = float(hard_iron_deg)
        self.drift_deg = float(drift_deg)
        self.drift_tau_s = float(drift_tau_s)
        self.drift_step_s = float(drift_step_s)
        self._drift_rng = random.Random("pace-d-%d" % seed)
        self.phase_deg = self._drift_rng.uniform(0.0, 360.0)
        self.drift = self._drift_rng.gauss(0.0, self.drift_deg) if self.drift_deg else 0.0
        self._next_drift_t = self.drift_step_s
        self._base_error = 0.0
        super().__init__(checkpoints_m, seed=seed, **kw)

    # SimRover.data() adds compass_error to every reading.
    @property
    def compass_error(self):
        e = self._base_error + self.drift
        if self.hard_iron_deg:
            e += self.hard_iron_deg * math.sin(math.radians(self.heading + self.phase_deg))
        return e

    @compass_error.setter
    def compass_error(self, value):
        self._base_error = value

    def _step(self):
        super()._step()
        while self.drift_deg and self.t >= self._next_drift_t - 1e-9:
            a = math.exp(-self.drift_step_s / self.drift_tau_s)
            self.drift = (a * self.drift + self.drift_deg * math.sqrt(1.0 - a * a)
                          * self._drift_rng.gauss(0.0, 1.0))
            self._next_drift_t += self.drift_step_s


_MEASURED = pb.PROFILES["measured"]
PROFILES = {
    "measured": pb.PROFILES["measured"],
    "measured-noise10": pb.PROFILES["measured-noise10"],
    "hardiron10": dict(_MEASURED, hard_iron_deg=10.0),
    "hardiron20": dict(_MEASURED, hard_iron_deg=20.0),
    "drift10": dict(_MEASURED, drift_deg=10.0, drift_tau_s=120.0),
}
# The first is the reference every other profile is compared with.
BASE_PROFILE = next(iter(PROFILES))
# The first is the pilot as it ships.
VARIANTS = {"shipped": None, "cf0.3": rp.SMOOTH_HEADING}
BASE_VARIANT = next(iter(VARIANTS))
CRUISES = (0.7, 0.8)


def heading_stats(errors):
    """How far the heading steered by was from the true one (degrees, signed)."""
    if not errors:
        return {"n": 0, "median_abs_deg": None, "rms_deg": None, "mean_deg": None}
    return {"n": len(errors),
            "median_abs_deg": round(statistics.median([abs(e) for e in errors]), 2),
            "rms_deg": round(math.sqrt(sum(e * e for e in errors) / len(errors)), 2),
            "mean_deg": round(statistics.fmean(errors), 2)}


def fly(course_name, seed, profile, variant, cruise, course=None):
    """One mission; pace_c.fly's fields, and heading_err."""
    course = course or ps.COURSES[course_name]
    pts = course["points"]
    sim = DistortedRover([pts[i] for i in course["checkpoints"]], seed=seed, **PROFILES[profile])
    v = VARIANTS[variant]
    smoother = None if v is None else rp.HeadingSmoother(**v)
    planner = ps.CoursePlanner(course, sim.lat0, sim.lon0)
    errors = []
    pilot = None

    def sleep(seconds):
        # The heading the pilot steers by against the rover's real one, while it
        # drives forward. Only reads; the mission is the same without it.
        h = pilot._heading_now
        if h is not None and sim.applied[0] > 0:
            errors.append(rp.wrap180(h - sim.heading))
        sim.sleep(seconds)

    pilot = rp.Pilot(sim, clock=sim.clock, sleep=sleep,
                     steering=rp.make_steering(False, cruise=cruise), planner=planner,
                     smooth_heading=smoother)
    total_m = ps.route_m(course)
    ideal_mps = cruise * sim.max_speed_mps
    res = pilot.run(timeout_s=3.0 * total_m / ideal_mps + 300.0)
    reached = len(res["reached"])
    done_m = ps.route_m(course, upto=reached)
    elapsed = res["elapsed_s"]
    made_good = done_m / elapsed if elapsed else 0.0
    return {"ok": res["ok"], "reason": res["reason"], "elapsed_s": elapsed,
            "reached": reached, "checkpoints": res["checkpoints"], "reports": res["reports"],
            "recoveries": res["recoveries"], "plans": res["plans"],
            "route_m": round(done_m, 1), "travelled_m": round(sim.travelled, 1),
            "made_good_mps": round(made_good, 4), "ideal_mps": round(ideal_mps, 4),
            "efficiency": round(made_good / ideal_mps, 4),
            "time_s": {k: round(x, 1) for k, x in sim.time_in.items()},
            "heading_err": heading_stats(errors)}


def _groups(runs):
    groups = {}
    for r in runs:
        groups.setdefault((r["profile"], r["variant"], r["cruise"], r["course"]), []).append(r)
    return groups


def profile_effects(runs):
    """Each profile against measured flown by the same variant, per cruise x
    course, paired by seed, with the median time difference as a share of
    measured's median; and per (profile, variant): groups faster / slower
    (paired sign test p < 0.05), lost / gained completions, the largest share."""
    groups = _groups(runs)
    effects, tallies = [], []
    for profile, variant in dict.fromkeys(k[:2] for k in sorted(groups)):
        if profile == BASE_PROFILE:
            continue
        faster = slower = lost = gained = n = 0
        largest = None
        for (p, v, c, m) in sorted(groups):
            if (p, v) != (profile, variant) or (BASE_PROFILE, v, c, m) not in groups:
                continue
            base = groups[(BASE_PROFILE, v, c, m)]
            cmp_ = ps.compare(base, groups[(p, v, c, m)])
            base_med = ps._median([r["elapsed_s"] for r in base if r["ok"]])
            share = (round(cmp_["median_time_diff_s"] / base_med, 4)
                     if base_med and cmp_["median_time_diff_s"] is not None else None)
            effects.append(dict(profile=p, variant=v, against=BASE_PROFILE, cruise=c, course=m,
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
            tallies.append({"profile": profile, "variant": variant, "against": BASE_PROFILE,
                            "groups": n, "groups_faster": faster, "groups_slower": slower,
                            "groups_lost": lost, "groups_gained": gained,
                            "largest_median_diff_share": largest})
    return effects, tallies


def heading_rows(runs):
    """Per (profile, variant, cruise, course): over the completed missions, the
    median of each mission's median |heading error| and of its RMS."""
    rows = []
    for k, rs in sorted(_groups(runs).items()):
        hs = [r["heading_err"] for r in rs if r["ok"] and r.get("heading_err", {}).get("n")]
        rows.append({"profile": k[0], "variant": k[1], "cruise": k[2], "course": k[3],
                     "missions": len(hs),
                     "median_abs_deg": ps._median([h["median_abs_deg"] for h in hs], 2),
                     "rms_deg": ps._median([h["rms_deg"] for h in hs], 2)})
    return rows


def check_against(runs, path):
    """Each measured / measured-noise10 mission against pace_c.py's record of the
    same one (its runs.jsonl): every field pace_c.py recorded must be equal."""
    ref = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                r = json.loads(line)
                ref[(r["profile"], r["variant"], r["cruise"], r["course"], r["seed"])] = r
    compared = missing = 0
    different = []
    for r in runs:
        if r["profile"] not in pc.PROFILES:
            continue
        key = (r["profile"], r["variant"], r["cruise"], r["course"], r["seed"])
        want = ref.get(key)
        if want is None:
            missing += 1
            continue
        got = json.loads(json.dumps(r))
        compared += 1
        fields = sorted(k for k in want if got.get(k) != want[k])
        if fields:
            different.append({"profile": key[0], "variant": key[1], "cruise": key[2],
                              "course": key[3], "seed": key[4], "fields": fields})
    return {"reference": path, "compared": compared, "identical": compared - len(different),
            "missing": missing, "different": different[:20]}


def write_outputs(out_dir, runs, started, args, done, check=None):
    s = ps.summarise(runs)
    effects, largest = pc.variant_tallies(runs, s["variant_effect"])
    p_effects, p_tallies = profile_effects(runs)
    headings = heading_rows(runs)
    result = {"version": __version__, "pace_b": pb.__version__, "pace_c": pc.__version__,
              "pace_study": ps.__version__, "rover_pilot": rp.__version__, "done": done,
              "elapsed_s": round(time.monotonic() - started, 1), "seeds": args.seeds,
              "human": {"marathon_m": ps.MARATHON_M, "time_s": ps.HUMAN_S,
                        "mps": round(ps.HUMAN_MPS, 4)},
              "profiles": PROFILES, "variants": VARIANTS, "cruises": list(CRUISES),
              "steering": rp.ROVER_STEERING,
              "runs": len(runs), "completed": sum(1 for r in runs if r["ok"]),
              "overview": s["overview"], "cruise_needed": s["cruise_needed"],
              "variant_effect": effects, "verdicts": s["verdicts"], "largest": largest,
              "profile_effect": p_effects, "profile_tallies": p_tallies,
              "heading": headings, "check": check}
    with open(os.path.join(out_dir, "summary.json"), "w") as f:
        json.dump(result, f, indent=1)
    with open(os.path.join(out_dir, "runs.jsonl"), "w") as f:
        for r in runs:
            f.write(json.dumps(r) + "\n")
    md = ["# Compass errors that last, and --smooth-heading (simulated)", "",
          "pace_d.py %s (pace_c.py %s, pace_b.py %s, pace_study.py %s, rover_pilot.py %s), "
          "MV2 of Munim, Inc. Human benchmark: %.4f m/s made good. Every profile is pace_b.py's "
          "measured Mini+ (orientation every 0.5 s, 48 deg/s, 0.5 s latency, 3 deg compass "
          "noise); measured-noise10 has 10 deg of noise; hardiron10/20 add A sin(heading + "
          "phase); drift10 adds a drift with SD 10 deg and a 120 s time constant. Variants: "
          "shipped, cf0.3 (--smooth-heading). Seeds 1-%d. %d of %d missions completed. "
          "Simulated rovers only, so these speeds are upper bounds."
          % (__version__, pc.__version__, pb.__version__, ps.__version__, rp.__version__,
             ps.HUMAN_MPS, args.seeds, result["completed"], len(runs)), ""]
    if check is not None:
        md += ["Check against pace_c.py's runs: %d compared, %d identical, %d missing."
               % (check["compared"], check["identical"], check["missing"]), ""]
    md += ["## Overview (courses pooled)", "",
           "| profile | variant | cruise | completed | made good m/s (median) | efficiency | "
           "runs beating 0.754 | every course? | path ratio |",
           "|---|---|---|---|---|---|---|---|---|"]
    md += ["| %s | %s | %g | %d/%d | %s | %s | %d | %s | %s |"
           % (o["profile"], o["variant"], o["cruise"], o["completed"], o["runs"],
              o["median_made_good_mps"], o["median_efficiency"], o["beat_human_pace"],
              "yes" if o["beats_on_every_course"] else "no", o["median_path_ratio"])
           for o in s["overview"]]
    md += ["", "## Each profile against measured, same variant", "",
           "Faster / slower: cruise x course groups where a paired sign test gives p < 0.05.", "",
           "| profile | variant | faster | slower | lost | gained | largest median diff |",
           "|---|---|---|---|---|---|---|"]
    md += ["| %s | %s | %d/%d | %d | %d | %d | %s |"
           % (t["profile"], t["variant"], t["groups_faster"], t["groups"], t["groups_slower"],
              t["groups_lost"], t["groups_gained"], t["largest_median_diff_share"])
           for t in p_tallies]
    md += ["", "| profile | variant | cruise | course | faster | slower | median diff s | share | p |",
           "|---|---|---|---|---|---|---|---|---|"]
    md += ["| %s | %s | %g | %s | %d | %d | %s | %s | %s |"
           % (e["profile"], e["variant"], e["cruise"], e["course"], e["faster"], e["slower"],
              e["median_time_diff_s"], e["median_time_diff_share"], e["sign_test_p"])
           for e in p_effects]
    md += ["", "## cf0.3 against the shipped pilot, same profile", "",
           "| profile | variant | faster | slower | lost | gained | largest median diff |",
           "|---|---|---|---|---|---|---|"]
    big = {(x["profile"], x["variant"]): x["largest_median_diff_share"] for x in largest}
    md += ["| %s | %s | %d/%d | %d | %d | %d | %s |"
           % (v["profile"], v["variant"], v["groups_faster"], v["groups"], v["groups_slower"],
              v["groups_lost"], v["groups_gained"], big.get((v["profile"], v["variant"])))
           for v in s["verdicts"]]
    md += ["", "| profile | variant | cruise | course | faster | slower | median diff s | share | p |",
           "|---|---|---|---|---|---|---|---|---|"]
    md += ["| %s | %s | %g | %s | %d | %d | %s | %s | %s |"
           % (e["profile"], e["variant"], e["cruise"], e["course"], e["faster"], e["slower"],
              e["median_time_diff_s"], e["median_time_diff_share"], e["sign_test_p"])
           for e in effects]
    md += ["", "## Heading steered by against the true heading, while driving forward", "",
           "Medians over the completed missions of each mission's median |error| and RMS error.", "",
           "| profile | variant | cruise | course | missions | median abs deg | RMS deg |",
           "|---|---|---|---|---|---|---|"]
    md += ["| %s | %s | %g | %s | %d | %s | %s |"
           % (h["profile"], h["variant"], h["cruise"], h["course"], h["missions"],
              h["median_abs_deg"], h["rms_deg"])
           for h in headings]
    with open(os.path.join(out_dir, "report.md"), "w") as f:
        f.write("\n".join(md) + "\n")
    return result


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out-dir", default="out")
    ap.add_argument("--seeds", type=int, default=12)
    ap.add_argument("--budget-min", type=float, default=150.0)
    ap.add_argument("--courses", help="comma-separated subset of: " + ",".join(ps.COURSES))
    ap.add_argument("--profiles", help="comma-separated subset of: " + ",".join(PROFILES))
    ap.add_argument("--variants", help="comma-separated subset of: " + ",".join(VARIANTS))
    ap.add_argument("--cruises", help="comma-separated cruise commands (default 0.7,0.8)")
    ap.add_argument("--check", help="pace_c.py's runs.jsonl: measured and measured-noise10 "
                                    "missions must match it")
    args = ap.parse_args(argv)
    courses = ps._names(args.courses, ps.COURSES, "course")
    profiles = ps._names(args.profiles, PROFILES, "profile")
    variants = ps._names(args.variants, VARIANTS, "variant")
    # measured and the shipped pilot are always flown: everything is compared with them.
    profiles = [BASE_PROFILE] + [p for p in profiles if p != BASE_PROFILE]
    variants = [BASE_VARIANT] + [v for v in variants if v != BASE_VARIANT]
    cruises = ([float(x) for x in args.cruises.split(",") if x.strip()]
               if args.cruises else list(CRUISES))
    os.makedirs(args.out_dir, exist_ok=True)
    started = time.monotonic()
    runs = []
    done = True
    for profile in profiles:
        for variant in variants:
            if time.monotonic() - started > args.budget_min * 60.0:
                done = False
                break
            for cruise in cruises:
                for course in courses:
                    for seed in range(1, args.seeds + 1):
                        try:
                            r = fly(course, seed, profile, variant, cruise)
                        except Exception as exc:
                            r = {"ok": False, "reason": "%s: %s" % (type(exc).__name__, exc),
                                 "elapsed_s": None, "reached": 0, "checkpoints": None,
                                 "reports": 0, "recoveries": 0, "plans": 0, "route_m": 0.0,
                                 "travelled_m": 0.0, "made_good_mps": 0.0, "ideal_mps": None,
                                 "efficiency": 0.0, "time_s": {}, "heading_err": heading_stats([])}
                        r.update(profile=profile, variant=variant, cruise=cruise,
                                 course=course, seed=seed)
                        runs.append(r)
            print("%s / %s: %d runs so far, %.0f s"
                  % (profile, variant, len(runs), time.monotonic() - started), flush=True)
            write_outputs(args.out_dir, runs, started, args, False)
        if not done:
            break
    check = check_against(runs, args.check) if args.check else None
    result = write_outputs(args.out_dir, runs, started, args, done, check)
    print(json.dumps({"check": None if check is None else
                      {k: check[k] for k in ("compared", "identical", "missing")},
                      "profile_tallies": result["profile_tallies"],
                      "verdicts": result["verdicts"]}), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
