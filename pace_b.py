#!/usr/bin/env python3
"""pace_b: the marathon pace study again, on a Mini+ that reports like the measured one.

pace_study.py 0.1.0 flew the pilot on a Mini+ stand-in whose orientation was
held 2 s between reports, turning at 30 deg/s per unit of angular, with
commands landing 0.8 s after they were sent. Public Mini+ recordings
(miniplus_b.py, studies/miniplus-b) later measured something else: orientation
changing about every 0.5 s, the state following the command about 0.5 s
later, and a median turn of 48 deg/s per unit of angular. Which way the
orientation runs came out mixed on those (mostly indoor) recordings, so a
noisier compass is flown too.

This flies pace_study's three courses (long straights, city blocks, a winding
path; 1.3-1.6 km each) with the shipped pilot and ROVER_STEERING at cruise
0.6, 0.7, 0.8 and 1.0, under five profiles:

- fresh: orientation fresh on every poll (pace_study's baseline);
- mini+: pace_study's Mini+ (held 2 s, 30 deg/s, 0.8 s latency), flown again
  to check that the old numbers reproduce;
- measured: orientation refreshed every 0.5 s, 48 deg/s, 0.5 s latency, GPS
  every 2 s;
- measured-lag0.8: the same with pace_study's 0.8 s latency;
- measured-noise10: the same with 10 deg of compass noise instead of 3.

Per run it records what pace_study.fly records. It writes summary.json,
runs.jsonl and report.md, with each measured profile compared seed by seed
against mini+ and the two variants against measured.

    python pace_b.py --out-dir out --seeds 12

Simulated rovers only: real sidewalks add crossings, people and kerbs, so the
speeds here are upper bounds. The Mini+ GPS rate is not known from public
data (no public recording has a fix); 2 s is kept from pace_study.
Standard library only. By MV2 of Munim, Inc.; written with AI agents. Apache-2.0.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time

import pace_study as ps
import rover_pilot as rp

__version__ = "0.1.0"


class MeasuredRover(ps.StudyRover):
    """StudyRover whose held orientation report is also refreshed every
    orientation_period_s, not only with each GPS fix. With 0 it is a StudyRover."""

    def __init__(self, checkpoints_m, orientation_period_s=0.0, **kw):
        self.orientation_period_s = float(orientation_period_s)
        self._next_orient_t = self.orientation_period_s
        super().__init__(checkpoints_m, **kw)

    def _step(self):
        super()._step()
        if (self.stale_orientation and self.orientation_period_s > 0
                and self.t >= self._next_orient_t - 1e-9):
            self._report = rp.SimRover.data(self)
            self._next_orient_t = self.t + self.orientation_period_s


_MEASURED = dict(ps._MINIPLUS, max_yaw_dps=48.0, latency_s=0.5, stale_orientation=True,
                 orientation_period_s=0.5)
# The first is pace_study's baseline; the second its Mini+, flown again.
PROFILES = {
    "fresh": ps.PROFILES["fresh"],
    "mini+": ps.PROFILES["mini+"],
    "measured": _MEASURED,
    "measured-lag0.8": dict(_MEASURED, latency_s=0.8),
    "measured-noise10": dict(_MEASURED, compass_noise_deg=10.0),
}
CRUISES = (0.6, 0.7, 0.8, 1.0)
# (profile, against): each pair compared seed by seed in every cruise x course group.
PAIRS = (("measured", "mini+"), ("measured-lag0.8", "measured"),
         ("measured-noise10", "measured"))


def fly(course_name, seed, profile, cruise, course=None):
    """One mission with the shipped pilot; the same fields as pace_study.fly."""
    course = course or ps.COURSES[course_name]
    pts = course["points"]
    sim = MeasuredRover([pts[i] for i in course["checkpoints"]], seed=seed, **PROFILES[profile])
    planner = ps.CoursePlanner(course, sim.lat0, sim.lon0)
    pilot = rp.Pilot(sim, clock=sim.clock, sleep=sim.sleep,
                     steering=rp.make_steering(False, cruise=cruise), planner=planner)
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
            "time_s": {k: round(x, 1) for k, x in sim.time_in.items()}}


def pair_effects(runs):
    """Each PAIRS profile against its reference, per cruise x course, with a tally:
    groups faster / slower (paired sign test p < 0.05), lost / gained completions,
    and the largest median time difference as a share of the reference median."""
    groups = {}
    for r in runs:
        groups.setdefault((r["profile"], r["cruise"], r["course"]), []).append(r)
    effects, tallies = [], []
    for profile, against in PAIRS:
        faster = slower = lost = gained = n = 0
        worst_share = None
        for (p, c, m) in sorted(groups):
            if p != profile or (against, c, m) not in groups:
                continue
            base = groups[(against, c, m)]
            cmp_ = ps.compare(base, groups[(p, c, m)])
            base_med = ps._median([r["elapsed_s"] for r in base if r["ok"]])
            share = (round(cmp_["median_time_diff_s"] / base_med, 4)
                     if base_med and cmp_["median_time_diff_s"] is not None else None)
            effects.append(dict(profile=p, against=against, cruise=c, course=m,
                                median_time_diff_share=share, **cmp_))
            n += 1
            if cmp_["sign_test_p"] is not None and cmp_["sign_test_p"] < 0.05:
                faster += cmp_["faster"] > cmp_["slower"]
                slower += cmp_["slower"] > cmp_["faster"]
            lost += cmp_["only_a_completed"] > cmp_["only_b_completed"]
            gained += cmp_["only_b_completed"] > cmp_["only_a_completed"]
            if share is not None and (worst_share is None or abs(share) > abs(worst_share)):
                worst_share = share
        if n:
            tallies.append({"profile": profile, "against": against, "groups": n,
                            "groups_faster": faster, "groups_slower": slower,
                            "groups_lost": lost, "groups_gained": gained,
                            "largest_median_diff_share": worst_share})
    return effects, tallies


def write_outputs(out_dir, runs, started, args, done):
    s = ps.summarise(runs)
    effects, tallies = pair_effects(runs)
    result = {"version": __version__, "pace_study": ps.__version__,
              "rover_pilot": rp.__version__, "done": done,
              "elapsed_s": round(time.monotonic() - started, 1), "seeds": args.seeds,
              "human": {"marathon_m": ps.MARATHON_M, "time_s": ps.HUMAN_S,
                        "mps": round(ps.HUMAN_MPS, 4)},
              "miniplus_top_mps": round(ps.MINIPLUS_TOP_MPS, 4),
              "profiles": PROFILES, "cruises": list(CRUISES),
              "steering": rp.ROVER_STEERING,
              "courses": {k: {"route_m": round(ps.route_m(c), 1),
                              "checkpoints": len(c["checkpoints"])}
                          for k, c in ps.COURSES.items()},
              "runs": len(runs), "completed": sum(1 for r in runs if r["ok"]),
              "groups": s["groups"], "overview": s["overview"],
              "cruise_needed": s["cruise_needed"], "pair_effects": effects,
              "pair_tallies": tallies}
    with open(os.path.join(out_dir, "summary.json"), "w") as f:
        json.dump(result, f, indent=1)
    with open(os.path.join(out_dir, "runs.jsonl"), "w") as f:
        for r in runs:
            f.write(json.dumps(r) + "\n")
    md = ["# The marathon pace on a Mini+ that reports like the measured one (simulated)", "",
          "pace_b.py %s (pace_study.py %s, rover_pilot.py %s), MV2 of Munim, Inc. Human "
          "benchmark: 50 miles Berkeley to Stanford in 29 h 38 min = %.4f m/s. Simulated "
          "Mini+: %.3f m/s per unit of linear, GPS every 2 s, steered with ROVER_STEERING %s. "
          "Seeds 1-%d. %d of %d missions completed. Simulated rovers only, so these speeds "
          "are upper bounds."
          % (__version__, ps.__version__, rp.__version__, ps.HUMAN_MPS, ps.MINIPLUS_TOP_MPS,
             json.dumps(rp.ROVER_STEERING), args.seeds, result["completed"], len(runs)), "",
          "Profiles: fresh = orientation fresh on every poll (30 deg/s, 0.8 s latency); "
          "mini+ = pace_study's Mini+ (held 2 s, 30 deg/s, 0.8 s); measured = refreshed every "
          "0.5 s, 48 deg/s, 0.5 s latency; measured-lag0.8 = the same with 0.8 s latency; "
          "measured-noise10 = the same with 10 deg compass noise.", "",
          "## Overview (courses pooled)", "",
          "| profile | cruise | completed | made good m/s (median) | efficiency | "
          "runs beating 0.754 | every course? | recoveries/run | path ratio |",
          "|---|---|---|---|---|---|---|---|---|"]
    md += ["| %s | %g | %d/%d | %s | %s | %d | %s | %s | %s |"
           % (o["profile"], o["cruise"], o["completed"], o["runs"], o["median_made_good_mps"],
              o["median_efficiency"], o["beat_human_pace"],
              "yes" if o["beats_on_every_course"] else "no", o["mean_recoveries"],
              o["median_path_ratio"])
           for o in s["overview"]]
    md += ["", "## Per course", "",
           "| profile | cruise | course | completed | made good m/s (median) | path ratio |",
           "|---|---|---|---|---|---|"]
    md += ["| %s | %g | %s | %d/%d | %s | %s |"
           % (g["profile"], g["cruise"], g["course"], g["completed"], g["runs"],
              g["median_made_good_mps"], g["median_path_ratio"])
           for g in s["groups"]]
    md += ["", "## Lowest cruise whose median beats the human pace on every course", "",
           "| profile | cruise |", "|---|---|"]
    md += ["| %s | %s |" % (c["profile"], c["lowest_cruise_beating_human_pace"] or "none")
           for c in s["cruise_needed"]]
    md += ["", "## Seed-by-seed comparisons", "",
           "Faster / slower: cruise x course groups where a paired sign test gives p < 0.05. "
           "Lost / gained: groups where one side completed more seeds.", "",
           "| profile | against | faster | slower | lost | gained | largest median diff |",
           "|---|---|---|---|---|---|---|"]
    md += ["| %s | %s | %d/%d | %d | %d | %d | %s |"
           % (t["profile"], t["against"], t["groups_faster"], t["groups"], t["groups_slower"],
              t["groups_lost"], t["groups_gained"], t["largest_median_diff_share"])
           for t in tallies]
    md += ["", "| profile | against | cruise | course | faster | slower | median diff s | p |",
           "|---|---|---|---|---|---|---|---|"]
    md += ["| %s | %s | %g | %s | %d | %d | %s | %s |"
           % (e["profile"], e["against"], e["cruise"], e["course"], e["faster"], e["slower"],
              e["median_time_diff_s"], e["sign_test_p"])
           for e in effects]
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
    ap.add_argument("--cruises", help="comma-separated cruise commands (default 0.6,0.7,0.8,1)")
    args = ap.parse_args(argv)
    courses = ps._names(args.courses, ps.COURSES, "course")
    profiles = ps._names(args.profiles, PROFILES, "profile")
    cruises = ([float(x) for x in args.cruises.split(",") if x.strip()]
               if args.cruises else list(CRUISES))
    # The baseline is always flown, as pace_study's summary expects.
    first = next(iter(PROFILES))
    profiles = [first] + [p for p in profiles if p != first]
    os.makedirs(args.out_dir, exist_ok=True)
    started = time.monotonic()
    runs = []
    done = True
    for profile in profiles:
        if time.monotonic() - started > args.budget_min * 60.0:
            done = False
            break
        for cruise in cruises:
            for course in courses:
                for seed in range(1, args.seeds + 1):
                    try:
                        r = fly(course, seed, profile, cruise)
                    except Exception as exc:
                        r = {"ok": False, "reason": "%s: %s" % (type(exc).__name__, exc),
                             "elapsed_s": None, "reached": 0, "checkpoints": None,
                             "reports": 0, "recoveries": 0, "plans": 0, "route_m": 0.0,
                             "travelled_m": 0.0, "made_good_mps": 0.0, "ideal_mps": None,
                             "efficiency": 0.0, "time_s": {}}
                    r.update(profile=profile, variant="shipped", cruise=cruise,
                             course=course, seed=seed)
                    runs.append(r)
        print("%s: %d runs so far, %.0f s" % (profile, len(runs), time.monotonic() - started),
              flush=True)
        write_outputs(args.out_dir, runs, started, args, False)
    result = write_outputs(args.out_dir, runs, started, args, done)
    print(json.dumps({"cruise_needed": result["cruise_needed"],
                      "pair_tallies": result["pair_tallies"]}), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
