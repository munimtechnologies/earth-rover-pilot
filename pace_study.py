#!/usr/bin/env python3
"""pace_study: can the pilot drive an Earth Rover Mini+ fast enough to beat the human marathon time?

Human drivers took an Earth Rover Mini+ from UC Berkeley to Stanford, about
50 miles, by remote control in 29 h 38 min (FrodoBots, Sept 2026): 0.754 m/s
on average. The Mini+ tops out at 4 km/h (1.11 m/s; earth-rovers-sdk README),
so a rover that never slows down must still be commanded at least 68% of full
linear to match that, and the pilot cruises at 0.6.

The same README says the Mini+ sends telemetry every 2 s with one gyroscope
and one magnetometer sample per report, so the orientation the pilot steers
by can be up to 2 s old, on top of the command latency. At about 30 deg/s per
unit of angular that is up to 60 deg of turn the pilot can't see yet. The
simulator has so far given a fresh orientation on every poll.

This flies three synthetic courses (long straights, city blocks, a winding
path; 1.3-1.6 km each, followed through a planner the way the OSM one is) on
a simulated Mini+ (1.11 m/s per unit of linear, GPS every 2 s, SIM_REAL
latencies, steered with ROVER_STEERING) at cruise 0.6, 0.8 and 1.0, with:

- profiles: orientation fresh on every poll (as before), or held for 2 s
  like the Mini+ telemetry, turning at 30 or 20 deg/s per unit;
- pilot variants: as shipped, or with the heading predicted between
  reports from the angular commanded since (HeadingPredictor, assuming
  30 deg/s per unit and a 0.8 s lag, so it is wrong on the 20 deg/s rover).

Per run it records completion, time, speed made good along the course
against the human 0.754 m/s, where the time went (driving, turning in place,
stopped, reversing), refused reports and recoveries. It writes summary.json,
runs.jsonl and report.md.

    python pace_study.py --out-dir out --seeds 12

Simulated rovers only: real sidewalks add crossings, people and kerbs, so the
speeds here are upper bounds. If the 29 h 38 min includes stops between legs,
the humans drove faster than 0.754 m/s and the bar is higher still.
Standard library only. By MV2 of Munim, Inc.; written with AI agents. Apache-2.0.
"""

from __future__ import annotations

import argparse
import collections
import json
import math
import os
import statistics
import sys
import time

import rover_pilot as rp

__version__ = "0.1.0"

# The human benchmark (FrodoBots, Sept 2026): Berkeley to Stanford, 50 miles,
# 29 h 38 min by remote control on an Earth Rover Mini+.
MARATHON_M = 50 * 1609.344
HUMAN_S = 29 * 3600 + 38 * 60
HUMAN_MPS = MARATHON_M / HUMAN_S
MINIPLUS_TOP_MPS = 4.0 / 3.6  # 4 km/h, earth-rovers-sdk README


def cruise_floor(top_mps, efficiency=1.0):
    """The cruise command a rover with this top speed needs to average the human pace,
    if it makes good `efficiency` of its commanded speed."""
    return HUMAN_MPS / (top_mps * efficiency)


# --- courses ----------------------------------------------------------------

def _staircase(steps, block_m):
    """City blocks: alternately one block north and one block east."""
    pts = [(0.0, 0.0)]
    n = e = 0.0
    for k in range(steps):
        if k % 2 == 0:
            n += block_m
        else:
            e += block_m
        pts.append((n, e))
    return pts


def _winding(length_m, amplitude_m, wavelength_m, step_m):
    """A path heading north that swings east and west like a bike path."""
    pts = []
    k = 0
    while k * step_m <= length_m + 1e-9:
        n = k * step_m
        pts.append((n, amplitude_m * math.sin(2.0 * math.pi * n / wavelength_m)))
        k += 1
    return pts


# points: (north_m, east_m) from the start, which is points[0]; checkpoints:
# indices into points, in order.
COURSES = {
    "boulevard": {"points": [(0.0, 0.0), (400.0, 0.0), (780.0, 140.0), (1150.0, 140.0),
                             (1500.0, 0.0)],
                  "checkpoints": [1, 2, 3, 4]},
    "blocks": {"points": _staircase(14, 100.0), "checkpoints": [3, 6, 9, 12, 14]},
    "bayside": {"points": _winding(1200.0, 15.0, 200.0, 20.0), "checkpoints": [15, 30, 45, 60]},
}


def route_m(course, upto=None):
    """Length along the course to its last checkpoint, or to the first `upto` checkpoints."""
    cps = course["checkpoints"]
    if upto is None:
        upto = len(cps)
    if upto <= 0:
        return 0.0
    pts = course["points"][:cps[upto - 1] + 1]
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:]))


def _seg_dist(p, a, b):
    dn, de = b[0] - a[0], b[1] - a[1]
    l2 = dn * dn + de * de
    f = 0.0 if l2 == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * dn + (p[1] - a[1]) * de) / l2))
    return math.hypot(p[0] - a[0] - f * dn, p[1] - a[1] - f * de)


def leg_points(course, leg, north, east):
    """The rest of leg `leg` from (north, east): that point, then the course points
    after the segment nearest to it, up to the leg's checkpoint."""
    cps = course["checkpoints"]
    pts = course["points"]
    a = 0 if leg == 0 else cps[leg - 1]
    b = cps[leg]
    p = (north, east)
    best, best_d = a, math.inf
    for j in range(a, b):
        d = _seg_dist(p, pts[j], pts[j + 1])
        if d < best_d:
            best, best_d = j, d
    return [p] + list(pts[best + 1:b + 1])


class CoursePlanner:
    """A planner for rp.Pilot that follows a course, as route_planner follows OSM paths."""

    def __init__(self, course, lat0, lon0):
        self.course = course
        self.lat0, self.lon0 = lat0, lon0
        self.calls = 0

    def __call__(self, lat, lon, cp_lat, cp_lon):
        self.calls += 1
        pts, cps = self.course["points"], self.course["checkpoints"]
        e, n = rp.to_enu(self.lat0, self.lon0, cp_lat, cp_lon)
        leg = min(range(len(cps)),
                  key=lambda k: math.hypot(pts[cps[k]][0] - n, pts[cps[k]][1] - e))
        pe, pn = rp.to_enu(self.lat0, self.lon0, lat, lon)
        return [rp.offset_latlon(self.lat0, self.lon0, a, b)
                for a, b in leg_points(self.course, leg, pn, pe)]


# --- rover and pilot variants -------------------------------------------------

class StudyRover(rp.SimRover):
    """SimRover that adds up where the time went (by the command being applied) and,
    with stale_orientation, reports orientation like the Mini+: sampled once per
    GPS report and held until the next, with /data's timestamp set to the report time."""

    def __init__(self, checkpoints_m, stale_orientation=False, **kw):
        self.stale_orientation = bool(stale_orientation)
        self._report = None
        self.time_in = {"driving": 0.0, "turning": 0.0, "stopped": 0.0, "reversing": 0.0}
        super().__init__(checkpoints_m, **kw)

    def _sample_gps(self):
        super()._sample_gps()
        if self.stale_orientation:
            self._report = rp.SimRover.data(self)

    def data(self):
        if self.stale_orientation and self._report is not None:
            return dict(self._report)
        return super().data()

    def _step(self):
        super()._step()
        linear, angular = self.applied
        if linear > 0:
            kind = "driving"
        elif linear < 0:
            kind = "reversing"
        elif angular != 0:
            kind = "turning"
        else:
            kind = "stopped"
        self.time_in[kind] += self.dt


def integrate(cmds, a, b, end_t):
    """Integral over [a, b] of piecewise-constant (t, value) commands, the last held to end_t."""
    total = 0.0
    for k, (t0, value) in enumerate(cmds):
        t1 = cmds[k + 1][0] if k + 1 < len(cmds) else end_t
        lo, hi = max(t0, a), min(t1, b)
        if hi > lo:
            total += value * (hi - lo)
    return total


class HeadingPredictor:
    """Wraps a rover so that between telemetry reports the orientation it returns is
    the last report's, turned by the angular commanded since: yaw_dps per unit of
    angular, each command taking effect lag_s after it is sent. A report is new
    when /data's timestamp changes. sign +1: a positive angular raises the reading
    (the simulator's default conventions)."""

    def __init__(self, rover, clock, yaw_dps=30.0, lag_s=0.8, sign=1.0, keep_s=10.0):
        self.rover = rover
        self.clock = clock
        self.yaw_dps = yaw_dps
        self.lag_s = lag_s
        self.sign = sign
        self.keep_s = keep_s
        self._cmds = collections.deque()
        self._ts = None
        self._seen_t = None

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
        now = self.clock()
        ts = d.get("timestamp")
        if self._seen_t is None or ts != self._ts:
            self._ts, self._seen_t = ts, now
        try:
            o = float(d.get("orientation"))
        except (TypeError, ValueError):
            return d
        if not math.isfinite(o):
            return d
        turn = self.sign * self.yaw_dps * integrate(
            list(self._cmds), self._seen_t - self.lag_s, now - self.lag_s, now)
        if turn == 0.0:
            return d
        return dict(d, orientation=(o + turn) % 360.0)


_MINIPLUS = dict(rp.SIM_REAL, max_speed_mps=MINIPLUS_TOP_MPS, gps_period_s=2.0)
# The first is the baseline: the simulator as earlier studies had it, at Mini+ speed.
PROFILES = {
    "fresh": dict(_MINIPLUS, max_yaw_dps=30.0),
    "mini+": dict(_MINIPLUS, max_yaw_dps=30.0, stale_orientation=True),
    "mini+yaw20": dict(_MINIPLUS, max_yaw_dps=20.0, stale_orientation=True),
}
BASE_PROFILE = next(iter(PROFILES))
# The first is the pilot as it ships.
VARIANTS = {
    "shipped": {"predict": False},
    "predict": {"predict": True, "yaw_dps": 30.0, "lag_s": 0.8},
}
BASE_VARIANT = next(iter(VARIANTS))
CRUISES = (0.6, 0.8, 1.0)


def fly(course_name, seed, profile, variant, cruise, course=None):
    course = course or COURSES[course_name]
    pts = course["points"]
    sim = StudyRover([pts[i] for i in course["checkpoints"]], seed=seed, **PROFILES[profile])
    v = VARIANTS[variant]
    rover = sim
    if v["predict"]:
        rover = HeadingPredictor(sim, sim.clock, yaw_dps=v["yaw_dps"], lag_s=v["lag_s"])
    planner = CoursePlanner(course, sim.lat0, sim.lon0)
    pilot = rp.Pilot(rover, clock=sim.clock, sleep=sim.sleep,
                     steering=rp.make_steering(False, cruise=cruise), planner=planner)
    total_m = route_m(course)
    ideal_mps = cruise * sim.max_speed_mps
    res = pilot.run(timeout_s=3.0 * total_m / ideal_mps + 300.0)
    reached = len(res["reached"])
    done_m = route_m(course, upto=reached)
    elapsed = res["elapsed_s"]
    made_good = done_m / elapsed if elapsed else 0.0
    return {"ok": res["ok"], "reason": res["reason"], "elapsed_s": elapsed,
            "reached": reached, "checkpoints": res["checkpoints"], "reports": res["reports"],
            "recoveries": res["recoveries"], "plans": res["plans"],
            "route_m": round(done_m, 1), "travelled_m": round(sim.travelled, 1),
            "made_good_mps": round(made_good, 4), "ideal_mps": round(ideal_mps, 4),
            "efficiency": round(made_good / ideal_mps, 4),
            "time_s": {k: round(x, 1) for k, x in sim.time_in.items()}}


# --- summaries ----------------------------------------------------------------

def sign_test_p(wins, losses):
    """Two-sided exact binomial p-value for wins against losses (ties left out)."""
    n = wins + losses
    if n == 0:
        return None
    k = min(wins, losses)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / 2.0 ** n
    return min(1.0, 2.0 * tail)


def _mean(values, digits=2):
    return round(statistics.fmean(values), digits) if values else None


def _median(values, digits=1):
    return round(statistics.median(values), digits) if values else None


def _row(rs):
    ok = [r for r in rs if r["ok"]]

    def share(kind):
        return _mean([r["time_s"][kind] / r["elapsed_s"] for r in ok if r["elapsed_s"]], 3)

    return {"runs": len(rs), "completed": len(ok),
            "median_time_s": _median([r["elapsed_s"] for r in ok]),
            "median_made_good_mps": _median([r["made_good_mps"] for r in ok], 3),
            "median_efficiency": _median([r["efficiency"] for r in ok], 3),
            "beat_human_pace": sum(1 for r in ok if r["made_good_mps"] > HUMAN_MPS),
            "share_driving": share("driving"), "share_turning": share("turning"),
            "share_stopped": share("stopped"), "share_reversing": share("reversing"),
            "mean_refused_reports": _mean([r["reports"] - r["reached"] for r in rs]),
            "mean_recoveries": _mean([r["recoveries"] for r in rs]),
            "median_path_ratio": _median([r["travelled_m"] / r["route_m"]
                                          for r in ok if r["route_m"]], 3)}


def compare(a_runs, b_runs):
    """b against a, paired by seed: who completed, and a sign test of time."""
    a = {r["seed"]: r for r in a_runs}
    b = {r["seed"]: r for r in b_runs}
    seeds = sorted(s for s in a if s in b)
    both = [s for s in seeds if a[s]["ok"] and b[s]["ok"]]
    diffs = [b[s]["elapsed_s"] - a[s]["elapsed_s"] for s in both]
    faster = sum(1 for d in diffs if d < 0)
    slower = sum(1 for d in diffs if d > 0)
    p = sign_test_p(faster, slower)
    return {"seeds": len(seeds), "both_completed": len(both),
            "only_a_completed": sum(1 for s in seeds if a[s]["ok"] and not b[s]["ok"]),
            "only_b_completed": sum(1 for s in seeds if b[s]["ok"] and not a[s]["ok"]),
            "faster": faster, "slower": slower, "median_time_diff_s": _median(diffs),
            "sign_test_p": None if p is None else round(p, 4)}


def summarise(runs):
    """Rows per (profile, variant, cruise, course); pooled over courses with whether
    the median beats the human pace on every course; the lowest such cruise; the
    effect of stale orientation (each profile against the first, shipped pilot);
    and each variant against the shipped pilot, with a verdict per profile."""
    groups, pooled = {}, {}
    for r in runs:
        groups.setdefault((r["profile"], r["variant"], r["cruise"], r["course"]), []).append(r)
        pooled.setdefault((r["profile"], r["variant"], r["cruise"]), []).append(r)
    rows = [dict(profile=k[0], variant=k[1], cruise=k[2], course=k[3], **_row(groups[k]))
            for k in sorted(groups)]
    overview = []
    for key, rs in pooled.items():
        per_course = [_row(g) for k, g in groups.items() if k[:3] == key]
        row = dict(profile=key[0], variant=key[1], cruise=key[2], **_row(rs))
        row["beats_on_every_course"] = bool(per_course) and all(
            x["completed"] == x["runs"] and x["median_made_good_mps"] is not None
            and x["median_made_good_mps"] > HUMAN_MPS for x in per_course)
        overview.append(row)
    cruise_needed = []
    for pv in dict.fromkeys((o["profile"], o["variant"]) for o in overview):
        good = sorted(o["cruise"] for o in overview
                      if (o["profile"], o["variant"]) == pv and o["beats_on_every_course"])
        cruise_needed.append({"profile": pv[0], "variant": pv[1],
                              "lowest_cruise_beating_human_pace": good[0] if good else None})
    stale_effect, variant_effect, verdicts = [], [], []
    for (p, v, c, m) in sorted(groups):
        if p == BASE_PROFILE or v != BASE_VARIANT:
            continue
        base = groups.get((BASE_PROFILE, BASE_VARIANT, c, m))
        if base is not None:
            stale_effect.append(dict(profile=p, cruise=c, course=m,
                                     **compare(base, groups[(p, v, c, m)])))
    for (profile, variant) in dict.fromkeys(k[:2] for k in groups):
        if variant == BASE_VARIANT:
            continue
        faster = slower = lost = gained = n_groups = 0
        for (p, v, c, m) in sorted(groups):
            if (p, v) != (profile, variant) or (p, BASE_VARIANT, c, m) not in groups:
                continue
            cmp_ = compare(groups[(p, BASE_VARIANT, c, m)], groups[(p, v, c, m)])
            variant_effect.append(dict(profile=p, variant=v, cruise=c, course=m, **cmp_))
            n_groups += 1
            if cmp_["sign_test_p"] is not None and cmp_["sign_test_p"] < 0.05:
                faster += cmp_["faster"] > cmp_["slower"]
                slower += cmp_["slower"] > cmp_["faster"]
            lost += cmp_["only_a_completed"] > cmp_["only_b_completed"]
            gained += cmp_["only_b_completed"] > cmp_["only_a_completed"]
        if n_groups:
            verdicts.append({
                "profile": profile, "variant": variant, "groups": n_groups,
                "groups_faster": faster, "groups_slower": slower,
                "groups_lost": lost, "groups_gained": gained,
                "better": not lost and not slower and (faster > 0 or gained > 0)
                          and 2 * (faster + gained) >= n_groups,
                "worse": bool(lost or slower)})
    return {"groups": rows, "overview": overview, "cruise_needed": cruise_needed,
            "stale_effect": stale_effect, "variant_effect": variant_effect,
            "verdicts": verdicts}


def write_outputs(out_dir, runs, started, args, done):
    s = summarise(runs)
    result = {"version": __version__, "rover_pilot": rp.__version__, "done": done,
              "elapsed_s": round(time.monotonic() - started, 1), "seeds": args.seeds,
              "human": {"marathon_m": MARATHON_M, "time_s": HUMAN_S,
                        "mps": round(HUMAN_MPS, 4)},
              "miniplus_top_mps": round(MINIPLUS_TOP_MPS, 4),
              "cruise_floor_at_full_efficiency": round(cruise_floor(MINIPLUS_TOP_MPS), 3),
              "profiles": PROFILES, "variants": VARIANTS, "cruises": list(CRUISES),
              "steering": rp.ROVER_STEERING,
              "courses": {k: {"route_m": round(route_m(c), 1),
                              "checkpoints": len(c["checkpoints"])}
                          for k, c in COURSES.items()},
              "runs": len(runs)}
    result.update(s)
    with open(os.path.join(out_dir, "summary.json"), "w") as f:
        json.dump(result, f, indent=1)
    with open(os.path.join(out_dir, "runs.jsonl"), "w") as f:
        for r in runs:
            f.write(json.dumps(r) + "\n")
    md = ["# Can earth-rover-pilot keep the human marathon pace on a Mini+? (simulated)", "",
          "pace_study.py %s, rover_pilot.py %s, MV2 of Munim, Inc. Human benchmark: 50 miles "
          "Berkeley to Stanford in 29 h 38 min = %.4f m/s. Simulated Mini+: %.3f m/s per unit "
          "of linear, GPS every 2 s, latencies from SIM_REAL, steered with ROVER_STEERING %s. "
          "At full efficiency the cruise must be at least %.3f. Seeds 1-%d. Simulated rovers "
          "only, so these speeds are upper bounds."
          % (__version__, rp.__version__, HUMAN_MPS, MINIPLUS_TOP_MPS,
             json.dumps(rp.ROVER_STEERING), cruise_floor(MINIPLUS_TOP_MPS), args.seeds), "",
          "Profiles: fresh = orientation fresh on every poll; mini+ = orientation held 2 s "
          "between reports like the Mini+ telemetry; mini+yaw20 = the same, turning at 20 "
          "instead of 30 deg/s per unit. Variants: shipped = the pilot as released; predict "
          "= heading predicted between reports from the angular commanded since (assumes "
          "30 deg/s, 0.8 s lag).", "",
          "## Overview (courses pooled)", "",
          "| profile | variant | cruise | completed | made good m/s (median) | efficiency | "
          "runs beating 0.754 | every course? | driving / turning / stopped | "
          "recoveries/run | path ratio |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    md += ["| %s | %s | %g | %d/%d | %s | %s | %d | %s | %s / %s / %s | %s | %s |"
           % (o["profile"], o["variant"], o["cruise"], o["completed"], o["runs"],
              o["median_made_good_mps"], o["median_efficiency"], o["beat_human_pace"],
              "yes" if o["beats_on_every_course"] else "no", o["share_driving"],
              o["share_turning"], o["share_stopped"], o["mean_recoveries"],
              o["median_path_ratio"])
           for o in s["overview"]]
    md += ["", "## Lowest cruise whose median beats the human pace on every course", "",
           "| profile | variant | cruise |", "|---|---|---|"]
    md += ["| %s | %s | %s |" % (c["profile"], c["variant"],
                                 c["lowest_cruise_beating_human_pace"] or "none")
           for c in s["cruise_needed"]]
    md += ["", "## Predicting the heading between reports, against the shipped pilot", "",
           "Faster / slower: cruise x course groups where a paired sign test per seed gives "
           "p < 0.05. Lost / gained: groups where one side completed more seeds.", "",
           "| profile | variant | faster | slower | lost | gained | verdict |",
           "|---|---|---|---|---|---|---|"]
    md += ["| %s | %s | %d/%d | %d | %d | %d | %s |"
           % (v["profile"], v["variant"], v["groups_faster"], v["groups"], v["groups_slower"],
              v["groups_lost"], v["groups_gained"],
              "better" if v["better"] else "worse" if v["worse"] else "no clear difference")
           for v in s["verdicts"]]
    md += ["", "## Orientation held 2 s against fresh, shipped pilot, per cruise and course", "",
           "| profile | cruise | course | completed (fresh / this) | faster | slower | "
           "median diff s | p |", "|---|---|---|---|---|---|---|---|"]
    md += ["| %s | %g | %s | -%d / +%d | %d | %d | %s | %s |"
           % (e["profile"], e["cruise"], e["course"], e["only_a_completed"],
              e["only_b_completed"], e["faster"], e["slower"], e["median_time_diff_s"],
              e["sign_test_p"])
           for e in s["stale_effect"]]
    with open(os.path.join(out_dir, "report.md"), "w") as f:
        f.write("\n".join(md) + "\n")
    return result


def _names(text, known, what):
    if not text:
        return list(known)
    names = [n.strip() for n in text.split(",") if n.strip()]
    for n in names:
        if n not in known:
            raise SystemExit("unknown %s: %s" % (what, n))
    return names


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out-dir", default="out")
    ap.add_argument("--seeds", type=int, default=12)
    ap.add_argument("--budget-min", type=float, default=150.0)
    ap.add_argument("--courses", help="comma-separated subset of: " + ",".join(COURSES))
    ap.add_argument("--profiles", help="comma-separated subset of: " + ",".join(PROFILES))
    ap.add_argument("--variants", help="comma-separated subset of: " + ",".join(VARIANTS))
    ap.add_argument("--cruises", help="comma-separated cruise commands (default 0.6,0.8,1)")
    args = ap.parse_args(argv)
    courses = _names(args.courses, COURSES, "course")
    profiles = _names(args.profiles, PROFILES, "profile")
    variants = _names(args.variants, VARIANTS, "variant")
    cruises = ([float(x) for x in args.cruises.split(",") if x.strip()]
               if args.cruises else list(CRUISES))
    # The baselines are always flown, so every comparison has its reference.
    profiles = [BASE_PROFILE] + [p for p in profiles if p != BASE_PROFILE]
    variants = [BASE_VARIANT] + [v for v in variants if v != BASE_VARIANT]
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
            print("%s/%s: %d runs so far, %.0f s"
                  % (profile, variant, len(runs), time.monotonic() - started), flush=True)
            write_outputs(args.out_dir, runs, started, args, False)
    result = write_outputs(args.out_dir, runs, started, args, done)
    print(json.dumps({"cruise_needed": result["cruise_needed"],
                      "verdicts": result["verdicts"]}), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
