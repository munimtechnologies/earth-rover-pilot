#!/usr/bin/env python3
"""pace_c: does smoothing the heading win back what a noisy compass costs?

pace_b.py 0.1.0 (studies/pace-b/GRADE.md) found that 10 deg of compass noise on
a Mini+ that reports like the measured one (orientation every 0.5 s, 48 deg/s
per unit of angular, 0.5 s latency) cost 2.4-3.1% in every cruise x course
group, and took cruise 0.7 below the human marathon pace. Its rule D3 said the
next study tests smoothing the heading. This one flies pace_study's three
courses at cruise 0.7 and 0.8 with the shipped pilot and ROVER_STEERING, on the
`measured` and `measured-noise10` profiles, with five variants:

- shipped: the pilot as it ships;
- ema0.5, ema0.3: each new orientation report moves the heading the pilot sees
  only 0.5 or 0.3 of the way towards it (a circular exponential average);
- cf0.3: the same 0.3 step, but first turned by the angular commanded since
  the last report, at the turn rate the measured profile really has (48 deg/s,
  commands landing 0.5 s late), so the average doesn't lag behind turns;
- cf0.3-yaw30: cf0.3 assuming 30 deg/s, a wrong rate, to see what a rover with
  an unknown rate would get.

Each variant is a wrapper around the simulated rover (HeadingSmoother); the
pilot's code is not changed. Each variant is compared seed by seed with the
shipped pilot on the same profile, cruise and course.

    python pace_c.py --out-dir out --seeds 12

Simulated rovers only, so the speeds are upper bounds; the compass noise is
independent per report. Standard library only.
By MV2 of Munim, Inc.; written with AI agents. Apache-2.0.
"""

from __future__ import annotations

import argparse
import collections
import json
import math
import os
import sys
import time

import pace_b as pb
import pace_study as ps
import rover_pilot as rp

__version__ = "0.1.0"


class HeadingSmoother:
    """Wraps a rover so that the orientation it returns is smoothed over reports.

    A report is new when /data's timestamp changes. On each new report the
    estimate is first turned by the angular commanded since the previous one
    (yaw_dps per unit, each command taking effect lag_s after it is sent; none
    with yaw_dps 0), then moved `gain` of the way towards the report, across
    north the short way. Between reports the estimate is held. With gain 1 the
    report comes back unchanged. sign +1: a positive angular raises the reading
    (the simulator's default conventions)."""

    def __init__(self, rover, clock, gain=0.3, yaw_dps=0.0, lag_s=0.5, sign=1.0, keep_s=10.0):
        self.rover = rover
        self.clock = clock
        self.gain = float(gain)
        self.yaw_dps = float(yaw_dps)
        self.lag_s = float(lag_s)
        self.sign = sign
        self.keep_s = keep_s
        self._cmds = collections.deque()
        self._est = None
        self._ts = None
        self._est_t = None
        self.reports = 0

    def __getattr__(self, name):
        return getattr(self.rover, name)

    def control(self, linear, angular):
        t = self.clock()
        self._cmds.append((t, float(angular)))
        while len(self._cmds) > 1 and self._cmds[1][0] < t - self.keep_s:
            self._cmds.popleft()
        self.rover.control(linear, angular)

    def data(self):
        d = self.rover.data() or {}
        try:
            o = float(d.get("orientation"))
        except (TypeError, ValueError):
            return d
        if not math.isfinite(o):
            return d
        now = self.clock()
        ts = d.get("timestamp")
        if self._est is None:
            self._est, self._ts, self._est_t = o % 360.0, ts, now
            self.reports = 1
        elif ts != self._ts:
            turn = 0.0
            if self.yaw_dps:
                turn = self.sign * self.yaw_dps * ps.integrate(
                    list(self._cmds), self._est_t - self.lag_s, now - self.lag_s, now)
            pred = self._est + turn
            self._est = (pred + self.gain * rp.wrap180(o - pred)) % 360.0
            self._ts, self._est_t = ts, now
            self.reports += 1
        return dict(d, orientation=self._est)


PROFILES = {
    "measured": pb.PROFILES["measured"],
    "measured-noise10": pb.PROFILES["measured-noise10"],
}
# The first is the pilot as it ships.
VARIANTS = {
    "shipped": None,
    "ema0.5": {"gain": 0.5, "yaw_dps": 0.0},
    "ema0.3": {"gain": 0.3, "yaw_dps": 0.0},
    "cf0.3": {"gain": 0.3, "yaw_dps": 48.0, "lag_s": 0.5},
    "cf0.3-yaw30": {"gain": 0.3, "yaw_dps": 30.0, "lag_s": 0.5},
}
BASE_VARIANT = next(iter(VARIANTS))
CRUISES = (0.7, 0.8)


def fly(course_name, seed, profile, variant, cruise, course=None):
    """One mission; the same fields as pace_study.fly. The shipped variant flies
    exactly as pace_b.fly."""
    course = course or ps.COURSES[course_name]
    pts = course["points"]
    sim = pb.MeasuredRover([pts[i] for i in course["checkpoints"]], seed=seed, **PROFILES[profile])
    v = VARIANTS[variant]
    rover = sim if v is None else HeadingSmoother(sim, sim.clock, **v)
    planner = ps.CoursePlanner(course, sim.lat0, sim.lon0)
    pilot = rp.Pilot(rover, clock=sim.clock, sleep=sim.sleep,
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


def variant_tallies(runs, effects):
    """Per (profile, variant): pace_study.summarise's variant_effect rows with the
    median time difference as a share of the shipped pilot's median, and the
    largest such share (by size) over the profile's groups."""
    base = {}
    for r in runs:
        if r["variant"] == BASE_VARIANT and r["ok"]:
            base.setdefault((r["profile"], r["cruise"], r["course"]), []).append(r["elapsed_s"])
    rows, worst = [], {}
    for e in effects:
        med = ps._median(base.get((e["profile"], e["cruise"], e["course"]), []))
        share = (round(e["median_time_diff_s"] / med, 4)
                 if med and e["median_time_diff_s"] is not None else None)
        rows.append(dict(e, median_time_diff_share=share))
        key = (e["profile"], e["variant"])
        if share is not None and (key not in worst or worst[key] is None
                                  or abs(share) > abs(worst[key])):
            worst[key] = share
        worst.setdefault(key, None)
    return rows, [{"profile": k[0], "variant": k[1], "largest_median_diff_share": w}
                  for k, w in worst.items()]


def write_outputs(out_dir, runs, started, args, done):
    s = ps.summarise(runs)
    effects, largest = variant_tallies(runs, s["variant_effect"])
    result = {"version": __version__, "pace_b": pb.__version__, "pace_study": ps.__version__,
              "rover_pilot": rp.__version__, "done": done,
              "elapsed_s": round(time.monotonic() - started, 1), "seeds": args.seeds,
              "human": {"marathon_m": ps.MARATHON_M, "time_s": ps.HUMAN_S,
                        "mps": round(ps.HUMAN_MPS, 4)},
              "profiles": PROFILES, "variants": VARIANTS, "cruises": list(CRUISES),
              "steering": rp.ROVER_STEERING,
              "runs": len(runs), "completed": sum(1 for r in runs if r["ok"]),
              "groups": s["groups"], "overview": s["overview"],
              "cruise_needed": s["cruise_needed"], "variant_effect": effects,
              "verdicts": s["verdicts"], "largest": largest}
    with open(os.path.join(out_dir, "summary.json"), "w") as f:
        json.dump(result, f, indent=1)
    with open(os.path.join(out_dir, "runs.jsonl"), "w") as f:
        for r in runs:
            f.write(json.dumps(r) + "\n")
    md = ["# Smoothing the heading on a Mini+ with a noisy compass (simulated)", "",
          "pace_c.py %s (pace_b.py %s, pace_study.py %s, rover_pilot.py %s), MV2 of Munim, Inc. "
          "Human benchmark: %.4f m/s made good. Profiles from pace_b.py: measured = orientation "
          "every 0.5 s, 48 deg/s, 0.5 s latency, 3 deg compass noise; measured-noise10 = the same "
          "with 10 deg. Variants: %s. Seeds 1-%d. %d of %d missions completed. Simulated rovers "
          "only, so these speeds are upper bounds."
          % (__version__, pb.__version__, ps.__version__, rp.__version__, ps.HUMAN_MPS,
             json.dumps(VARIANTS), args.seeds, result["completed"], len(runs)), "",
          "## Overview (courses pooled)", "",
          "| profile | variant | cruise | completed | made good m/s (median) | efficiency | "
          "runs beating 0.754 | every course? | path ratio |",
          "|---|---|---|---|---|---|---|---|---|"]
    md += ["| %s | %s | %g | %d/%d | %s | %s | %d | %s | %s |"
           % (o["profile"], o["variant"], o["cruise"], o["completed"], o["runs"],
              o["median_made_good_mps"], o["median_efficiency"], o["beat_human_pace"],
              "yes" if o["beats_on_every_course"] else "no", o["median_path_ratio"])
           for o in s["overview"]]
    md += ["", "## Each variant against the shipped pilot", "",
           "Faster / slower: cruise x course groups where a paired sign test gives p < 0.05.", "",
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
    args = ap.parse_args(argv)
    courses = ps._names(args.courses, ps.COURSES, "course")
    profiles = ps._names(args.profiles, PROFILES, "profile")
    variants = ps._names(args.variants, VARIANTS, "variant")
    # The shipped pilot is always flown: every variant is compared with it.
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
                                 "efficiency": 0.0, "time_s": {}}
                        r.update(profile=profile, variant=variant, cruise=cruise,
                                 course=course, seed=seed)
                        runs.append(r)
            print("%s / %s: %d runs so far, %.0f s"
                  % (profile, variant, len(runs), time.monotonic() - started), flush=True)
            write_outputs(args.out_dir, runs, started, args, False)
        if not done:
            break
    result = write_outputs(args.out_dir, runs, started, args, done)
    print(json.dumps({"verdicts": result["verdicts"], "largest": result["largest"]}), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
