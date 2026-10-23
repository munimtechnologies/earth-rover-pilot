#!/usr/bin/env python3
"""pace_i: should bridging GPS gaps on the wheels be the default?

pace_h.py found that dead reckoning used only while the GPS has no fresh fix
(bridge+cf0.3, rover_pilot's --dead-reckon-gaps since v0.14.0) was the
fastest pilot on every profile, but its GPS gaps were single fixes missing
at random (30% of them). Real GPS outages come in runs: under trees, beside
tall buildings, in an underpass. This study flies the measured Mini+ on
fresh seeds with outages that last 15 s (shorter than the 30 s the
reckoner may carry the position) or 45 s (longer), starting at random:

- cf0.3: --smooth-heading only, the real-rover pilot since v0.14.0;
- bridge+cf0.3: dead reckoning steered by only while the GPS has no fresh
  fix (pace_h.BridgePilot);
- bridge-r+cf0.3: the same, with the GPS filter starting its average again
  from the first fix after a gap longer than its 3 s limit, instead of
  blending that fix with fixes from before the gap (ResettingGpsFilter);
- dr+cf0.3: v0.13.0's real-rover pilot, for reference.

    python pace_i.py --out-dir out --first-seed 85 --seeds 24 --check studies/pace-h/runs.jsonl

With --check it first flies seeds 61-63 of pace_h.py's measured cf0.3 and
bridge+cf0.3 missions again and compares each field by field with
pace_h.py's record. Simulated rovers only, so the speeds are upper bounds.
Standard library only. By MV2 of Munim, Inc.; written with AI agents.
Apache-2.0.
"""

from __future__ import annotations

import argparse
import bisect
import json
import os
import random
import sys
import time

import dead_reckon as dr
import pace_d as pd
import pace_e as pe
import pace_f as pf
import pace_g as pg
import pace_h as ph
import pace_study as ps
import rover_pilot as rp

__version__ = "0.1.0"

# Outage windows are drawn this far ahead; no mission runs this long.
OUTAGE_HORIZON_S = 20000.0
_MEASURED = ph.PROFILES["measured"]
# pace_h.py's measured Mini+, and with GPS outages of outage_s seconds, each
# starting after clear_s seconds of sky on average (exponential).
PROFILES = {
    "measured": _MEASURED,
    "outage15": dict(_MEASURED, outage_s=15.0, clear_s=150.0),
    "outage45": dict(_MEASURED, outage_s=45.0, clear_s=300.0),
}
# The first is the reference every other profile is compared with.
BASE_PROFILE = next(iter(PROFILES))
# The first is the pilot as v0.14.0 flies a real rover.
VARIANTS = {
    "cf0.3": ph.VARIANTS["cf0.3"],
    "bridge+cf0.3": ph.VARIANTS["bridge+cf0.3"],
    "bridge-r+cf0.3": dict(ph.VARIANTS["bridge+cf0.3"], reset_gps=True),
    "dr+cf0.3": ph.VARIANTS["dr+cf0.3"],
}
BASE_VARIANT = next(iter(VARIANTS))
# (a, b): b against a, paired by seed on every profile and course.
PAIRS = (("cf0.3", "bridge+cf0.3"), ("cf0.3", "bridge-r+cf0.3"),
         ("bridge+cf0.3", "bridge-r+cf0.3"), ("cf0.3", "dr+cf0.3"),
         ("dr+cf0.3", "bridge-r+cf0.3"))
CRUISES = (0.8,)
# pace_h.py flew seeds 61-84; these start after them.
FIRST_SEED = 85
# pace_h.py flew these with the same settings; --check flies them again.
CHECKED = {"profiles": ("measured",), "variants": ("cf0.3", "bridge+cf0.3"),
           "seeds": (61, 62, 63)}


def outage_windows(seed, outage_s, clear_s, horizon_s=OUTAGE_HORIZON_S):
    """[(start, end)] of GPS outages outage_s long, each after an exponential
    clear spell of mean clear_s, drawn from a generator of their own."""
    if outage_s <= 0:
        return []
    rng = random.Random("pace-i-%d" % seed)
    windows = []
    t = rng.expovariate(1.0 / clear_s)
    while t < horizon_s:
        windows.append((t, t + outage_s))
        t += outage_s + rng.expovariate(1.0 / clear_s)
    return windows


class OutageRover(pd.DistortedRover):
    """DistortedRover whose GPS reports no fix (1000) for every report taken
    inside an outage window. The windows come from a generator of their own,
    so the rover's own draws (GPS noise, dropouts, compass) are a
    DistortedRover's with the same seed; without windows it flies exactly as one."""

    def __init__(self, checkpoints_m, seed=0, outage_s=0.0, clear_s=150.0, **kw):
        self.outage_s = float(outage_s)
        self.clear_s = float(clear_s)
        self.outages = outage_windows(seed, self.outage_s, self.clear_s)
        self._starts = [a for a, _ in self.outages]
        self.withheld = 0  # GPS reports turned into no-fix by an outage
        super().__init__(checkpoints_m, seed=seed, **kw)

    def in_outage(self, t):
        i = bisect.bisect_right(self._starts, t) - 1
        return i >= 0 and t < self.outages[i][1]

    def _sample_gps(self):
        super()._sample_gps()
        if self.outages and self.in_outage(self.t):
            self.gps = (rp.NO_FIX, rp.NO_FIX)
            self.withheld += 1
            if self._report is not None:
                # StudyRover took its held report with the fix; take it back.
                self._report = dict(self._report, latitude=rp.NO_FIX, longitude=rp.NO_FIX,
                                    gps_signal=0)


class ResettingGpsFilter(rp.GpsFilter):
    """GpsFilter that, when a new fix is accepted after the GPS has been out
    for longer than max_age_s, starts its average again from that fix instead
    of moving 0.3 of the way to it from the average of fixes before the gap."""

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.resets = 0

    def update(self, lat, lon, t):
        stale = self.fix_t is not None and t - self.fix_t > self.max_age_s
        fix = super().update(lat, lon, t)
        if fix is not None and stale:
            self.lat, self.lon = fix
            self.resets += 1
        return fix


def fly(course_name, seed, profile, variant, cruise, course=None):
    """One mission flown as pace_h.fly flies it, on an OutageRover, with the
    variant's GPS filter; also how many GPS reports the outages withheld."""
    course = course or ps.COURSES[course_name]
    pts = course["points"]
    sim = OutageRover([pts[i] for i in course["checkpoints"]], seed=seed, **PROFILES[profile])
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

    cls = ph.BridgePilot if v.get("bridge") else rp.Pilot
    pilot = cls(sim, clock=sim.clock, sleep=sleep,
                steering=rp.make_steering(False, cruise=cruise), planner=planner,
                smooth_heading=smoother, dead_reckon=reckoner)
    if v.get("reset_gps"):
        pilot.gps = ResettingGpsFilter()
    est = pe.CountingEstimator()
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
            "learner": {"calibrations": est.calibrations, "breaks": est.breaks,
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
                      "mean_abs_angular": round(steer[0] / steer[1], 4) if steer[1] else None},
            "outage": {"withheld": sim.withheld,
                       "gps_resets": pilot.gps.resets if v.get("reset_gps") else None}}


def failed_run(exc):
    return dict(ph.failed_run(exc), outage={"withheld": None, "gps_resets": None})


def check_pace_h(path):
    """Fly the CHECKED missions again and compare each with pace_h.py's record
    of it (its runs.jsonl): every field pace_h.py recorded must be equal. A
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


def outage_rows(runs):
    """Per (profile, variant, cruise, course), over the completed missions: the
    median GPS reports withheld by outages, seconds stood still, and GPS
    filter restarts (None for a variant without them)."""
    rows = []
    for k, rs in sorted(pg._groups(runs).items()):
        done = [r for r in rs if r["ok"] and r.get("outage")]
        resets = [r["outage"]["gps_resets"] for r in done
                  if r["outage"]["gps_resets"] is not None]
        rows.append({"profile": k[0], "variant": k[1], "cruise": k[2], "course": k[3],
                     "missions": len(done),
                     "median_withheld": ps._median([r["outage"]["withheld"] for r in done], 1),
                     "median_stopped_s": ps._median([r["time_s"]["stopped"] for r in done], 1),
                     "median_gps_resets": ps._median(resets, 1) if resets else None})
    return rows


def write_outputs(out_dir, runs, started, seeds, done, check=None):
    s = ps.summarise(runs)
    effects, tallies = pair_effects(runs)
    headings = pd.heading_rows(runs)
    learner = pe.learner_rows(runs)
    offsets = pe.offset_rows(runs)
    positions = pg.position_rows(runs)
    reckoning = pg.dr_rows(runs)
    steering = ph.steer_rows(runs)
    outages = outage_rows(runs)
    result = {"version": __version__, "pace_h": ph.__version__, "pace_g": pg.__version__,
              "pace_f": pf.__version__, "pace_e": pe.__version__, "pace_d": pd.__version__,
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
              "outage": outages, "steer": steering, "position": positions,
              "reckoner": reckoning, "learner": learner, "offset": offsets,
              "heading": headings, "check": check}
    with open(os.path.join(out_dir, "summary.json"), "w") as f:
        json.dump(result, f, indent=1)
    with open(os.path.join(out_dir, "runs.jsonl"), "w") as f:
        for r in runs:
            f.write(json.dumps(r) + "\n")
    md = ["# Should bridging GPS gaps be the default? (simulated)", "",
          "pace_i.py %s (pace_h.py %s, rover_pilot.py %s, dead_reckon.py %s), MV2 of Munim, Inc. "
          "Every profile is pace_h.py's measured Mini+ (orientation every 0.5 s, 48 deg/s, 0.5 s "
          "latency, GPS every 2 s and 1.5 s late, 3 deg of compass noise, a -25 deg compass error "
          "to learn, wheels reporting RPM), alone or with GPS outages of 15 s (after 150 s of sky "
          "on average) or 45 s (after 300 s). Variants: cf0.3 (v0.14.0 on a real rover), "
          "bridge+cf0.3 (dead reckoning only while the GPS has no fresh fix), bridge-r+cf0.3 (the "
          "same, the GPS filter starting again from the first fix after a gap), dr+cf0.3 (v0.13.0 "
          "on a real rover). Seeds %s. %d of %d missions completed. Simulated rovers only, so "
          "these speeds are upper bounds."
          % (__version__, ph.__version__, rp.__version__, dr.__version__,
             "%d-%d" % (seeds[0], seeds[-1]) if seeds else "none",
             result["completed"], len(runs)), ""]
    if check is not None:
        md += ["Check against pace_h.py's runs: %d compared, %d identical, %d missing."
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
    md += ["", "## GPS outages", ""]
    md += pf._table(["profile", "variant", "course", "missions", "reports withheld",
                     "s stood still", "GPS filter restarts"],
                    [(x["profile"], x["variant"], x["course"], x["missions"],
                      x["median_withheld"], x["median_stopped_s"], x["median_gps_resets"])
                     for x in outages])
    md += ["", "## How hard the pilot steers", ""]
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
    ap.add_argument("--check", help="pace_h.py's runs.jsonl: fly the CHECKED missions again "
                                    "and compare")
    args = ap.parse_args(argv)
    courses = ps._names(args.courses, ps.COURSES, "course")
    profiles = ps._names(args.profiles, PROFILES, "profile")
    variants = ps._names(args.variants, VARIANTS, "variant")
    # measured and v0.14.0's real-rover pilot are always flown: the rest are compared with them.
    profiles = [BASE_PROFILE] + [p for p in profiles if p != BASE_PROFILE]
    variants = [BASE_VARIANT] + [v for v in variants if v != BASE_VARIANT]
    seeds = list(range(args.first_seed, args.first_seed + args.seeds))
    os.makedirs(args.out_dir, exist_ok=True)
    started = time.monotonic()
    check = check_pace_h(args.check) if args.check else None
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
