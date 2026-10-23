#!/usr/bin/env python3
"""pace_j: does bridging GPS outages still pay when the GPS wanders first?

pace_i.py's outages were clean: the fixes kept their usual noise until the
GPS cut out, and again as soon as it came back. Under trees and beside tall
buildings a real GPS usually wanders off by metres before it drops out, and
again while it recovers. This study flies pace_i.py's measured Mini+ with its
15 s and 45 s outages, alone or with every outage wrapped in wandering fixes:
for 20 s before it the fixes drift steadily away to 8 m off, in a direction
drawn for that outage, and for 20 s after it they drift back. A drift this
slow (0.4 m/s) passes the GPS filter's jump test. Variants (pace_i.py's):

- cf0.3: --smooth-heading only, v0.14.0's real-rover pilot;
- bridge+cf0.3: dead reckoning steered by only while the GPS has no fresh
  fix, the real-rover default since v0.15.0;
- dr+cf0.3: v0.13.0's real-rover pilot, for reference.

    python pace_j.py --out-dir out --first-seed 109 --seeds 24 --check studies/pace-i/runs.jsonl

With --check it first flies seeds 85-87 of pace_i.py's outage15 cf0.3 and
bridge+cf0.3 missions again and compares each field by field with
pace_i.py's record. Every mission is flown by pace_i.fly itself, on a
WanderRover. Simulated rovers only, so the speeds are upper bounds.
Standard library only. By MV2 of Munim, Inc.; written with AI agents.
Apache-2.0.
"""

from __future__ import annotations

import argparse
import bisect
import contextlib
import json
import math
import os
import random
import sys
import time

import dead_reckon as dr
import pace_e as pe
import pace_f as pf
import pace_g as pg
import pace_h as ph
import pace_i as pi
import pace_study as ps
import rover_pilot as rp

__version__ = "0.1.0"

# How long the fixes take to wander off before an outage (and back after it),
# and how far off they get.
WANDER_S = 20.0
WANDER_M = 8.0
# pace_i.py's outage profiles, alone and with wandering fixes.
PROFILES = {
    "outage15": pi.PROFILES["outage15"],
    "wander15": dict(pi.PROFILES["outage15"], wander_s=WANDER_S, wander_m=WANDER_M),
    "outage45": pi.PROFILES["outage45"],
    "wander45": dict(pi.PROFILES["outage45"], wander_s=WANDER_S, wander_m=WANDER_M),
}
# The first is always flown.
BASE_PROFILE = next(iter(PROFILES))
# (a, b): each variant on profile b against itself on profile a, paired by seed
# (same outages, same draws), so the difference is what wandering costs.
PROFILE_PAIRS = (("outage15", "wander15"), ("outage45", "wander45"))
# The first is the pilot as v0.14.0 flies a real rover; pace_i.PAIRS compares
# the others with it.
VARIANTS = {name: pi.VARIANTS[name] for name in ("cf0.3", "bridge+cf0.3", "dr+cf0.3")}
BASE_VARIANT = next(iter(VARIANTS))
CRUISES = (0.8,)
# pace_i.py flew seeds 85-108; these start after them.
FIRST_SEED = 109
# pace_i.py flew these with the same settings; --check flies them again.
CHECKED = {"profiles": ("outage15",), "variants": ("cf0.3", "bridge+cf0.3"),
           "seeds": (85, 86, 87)}
# The profile name pace_i.fly is given while a pace_j profile is flown.
_SLOT = "_pace_j"


def wander_angles(seed, count):
    """A direction (radians clockwise from north) for each outage's wandering
    fixes, drawn from a generator of their own."""
    rng = random.Random("pace-j-%d" % seed)
    return [rng.uniform(0.0, 2.0 * math.pi) for _ in range(count)]


class WanderRover(pi.OutageRover):
    """OutageRover whose fixes, for wander_s seconds before each outage, drift
    steadily away to wander_m metres off in a direction drawn for that outage,
    and for wander_s seconds after it drift back. The directions come from a
    generator of their own, so the rover's own draws are an OutageRover's with
    the same seed; with wander_m 0 it flies exactly as one."""

    def __init__(self, checkpoints_m, seed=0, wander_s=0.0, wander_m=0.0, **kw):
        self.wander_s = float(wander_s)
        self.wander_m = float(wander_m)
        self.wandered = 0  # GPS reports moved by wandering
        # Set before the rover starts, which may already take a fix.
        count = len(pi.outage_windows(seed, float(kw.get("outage_s", 0.0)),
                                      float(kw.get("clear_s", 150.0))))
        self._angles = wander_angles(seed, count)
        super().__init__(checkpoints_m, seed=seed, **kw)

    def wander_at(self, t):
        """(north, east) metres a fix taken at time t is moved by."""
        if self.wander_m <= 0.0 or self.wander_s <= 0.0 or not self.outages:
            return 0.0, 0.0
        # The latest outage starting before t + wander_s: t is in its run-up,
        # in it, or in its run-out, or in none.
        i = bisect.bisect_right(self._starts, t + self.wander_s) - 1
        if i < 0:
            return 0.0, 0.0
        a, b = self.outages[i]
        if t < a - self.wander_s or t >= b + self.wander_s:
            return 0.0, 0.0
        if t < a:
            share = (t - (a - self.wander_s)) / self.wander_s
        elif t < b:
            share = 1.0
        else:
            share = 1.0 - (t - b) / self.wander_s
        off = share * self.wander_m
        return off * math.cos(self._angles[i]), off * math.sin(self._angles[i])

    def _sample_gps(self):
        super()._sample_gps()
        if self.gps[0] == rp.NO_FIX:
            return
        north, east = self.wander_at(self.t)
        if north == 0.0 and east == 0.0:
            return
        self.gps = rp.offset_latlon(self.gps[0], self.gps[1], north, east)
        self.wandered += 1
        if self._report is not None:
            # StudyRover took its held report with the fix; move it too.
            self._report = dict(self._report, latitude=self.gps[0], longitude=self.gps[1])


@contextlib.contextmanager
def _flown_by_pace_i(profile, made):
    """While inside, pace_i.fly flies the profile under _SLOT on a WanderRover,
    and each rover it makes is appended to `made`."""
    def make(*args, **kw):
        sim = WanderRover(*args, **kw)
        made.append(sim)
        return sim

    saved = pi.OutageRover
    pi.PROFILES[_SLOT] = PROFILES[profile]
    pi.OutageRover = make
    try:
        yield _SLOT
    finally:
        pi.OutageRover = saved
        del pi.PROFILES[_SLOT]


def fly(course_name, seed, profile, variant, cruise, course=None):
    """One mission flown by pace_i.fly on a WanderRover with the profile's
    settings; also how many GPS reports wandering moved."""
    made = []
    with _flown_by_pace_i(profile, made) as slot:
        r = pi.fly(course_name, seed, slot, variant, cruise, course=course)
    r["wander"] = {"wandered": made[0].wandered if made else None}
    return r


def failed_run(exc):
    return dict(pi.failed_run(exc), wander={"wandered": None})


def check_pace_i(path):
    """Fly the CHECKED missions again and compare each with pace_i.py's record
    of it (its runs.jsonl): every field pace_i.py recorded must be equal. A
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


def profile_effects(runs):
    """For each variant and PROFILE_PAIRS (a, b): the variant on b against
    itself on a, per cruise x course, paired by seed, with the median time
    difference as a share of a's median; and the tally per (variant, a, b):
    groups faster / slower (paired sign test p < 0.05), courses where a or b
    completed more, the largest share."""
    groups = pg._groups(runs)
    effects, tallies = [], []
    for variant in VARIANTS:
        for a, b in PROFILE_PAIRS:
            faster = slower = lost = gained = n = 0
            largest = None
            for (p, v, c, m) in sorted(groups):
                if (p, v) != (b, variant) or (a, v, c, m) not in groups:
                    continue
                base = groups[(a, v, c, m)]
                cmp_ = ps.compare(base, groups[(p, v, c, m)])
                base_med = ps._median([r["elapsed_s"] for r in base if r["ok"]])
                share = (round(cmp_["median_time_diff_s"] / base_med, 4)
                         if base_med and cmp_["median_time_diff_s"] is not None else None)
                effects.append(dict(variant=v, profile=p, against=a, cruise=c, course=m,
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
                tallies.append({"variant": variant, "profile": b, "against": a, "groups": n,
                                "groups_faster": faster, "groups_slower": slower,
                                "groups_lost": lost, "groups_gained": gained,
                                "largest_median_diff_share": largest})
    return effects, tallies


def wander_rows(runs):
    """Per (profile, variant, cruise, course), over the completed missions: the
    median GPS reports wandering moved."""
    rows = []
    for k, rs in sorted(pg._groups(runs).items()):
        done = [r for r in rs if r["ok"] and r.get("wander")
                and r["wander"]["wandered"] is not None]
        rows.append({"profile": k[0], "variant": k[1], "cruise": k[2], "course": k[3],
                     "missions": len(done),
                     "median_wandered": ps._median([r["wander"]["wandered"] for r in done], 1)})
    return rows


def write_outputs(out_dir, runs, started, seeds, done, check=None):
    s = ps.summarise(runs)
    effects, tallies = pi.pair_effects(runs)
    p_effects, p_tallies = profile_effects(runs)
    outages = pi.outage_rows(runs)
    wanders = wander_rows(runs)
    steering = ph.steer_rows(runs)
    positions = pg.position_rows(runs)
    reckoning = pg.dr_rows(runs)
    offsets = pe.offset_rows(runs)
    result = {"version": __version__, "pace_i": pi.__version__, "pace_h": ph.__version__,
              "pace_g": pg.__version__, "pace_study": ps.__version__,
              "rover_pilot": rp.__version__, "dead_reckon": dr.__version__, "done": done,
              "elapsed_s": round(time.monotonic() - started, 1), "seeds": seeds,
              "human": {"marathon_m": ps.MARATHON_M, "time_s": ps.HUMAN_S,
                        "mps": round(ps.HUMAN_MPS, 4)},
              "profiles": PROFILES, "variants": VARIANTS,
              "profile_pairs": [list(x) for x in PROFILE_PAIRS], "cruises": list(CRUISES),
              "wander": {"wander_s": WANDER_S, "wander_m": WANDER_M},
              "steering": rp.ROVER_STEERING, "dead_reckon_settings": rp.DEAD_RECKON,
              "runs": len(runs), "completed": sum(1 for r in runs if r["ok"]),
              "overview": s["overview"], "pair_effect": effects, "verdicts": tallies,
              "profile_effect": p_effects, "profile_verdicts": p_tallies,
              "outage": outages, "wandering": wanders, "steer": steering,
              "position": positions, "reckoner": reckoning, "offset": offsets,
              "check": check}
    with open(os.path.join(out_dir, "summary.json"), "w") as f:
        json.dump(result, f, indent=1)
    with open(os.path.join(out_dir, "runs.jsonl"), "w") as f:
        for r in runs:
            f.write(json.dumps(r) + "\n")
    md = ["# Does bridging GPS outages still pay when the GPS wanders first? (simulated)", "",
          "pace_j.py %s (pace_i.py %s, rover_pilot.py %s, dead_reckon.py %s), MV2 of Munim, Inc. "
          "Every profile is pace_i.py's measured Mini+ with GPS outages of 15 s (after 150 s of "
          "sky on average) or 45 s (after 300 s), alone (outage15, outage45) or with the fixes "
          "drifting steadily away to %g m off over the %g s before each outage and back over "
          "the %g s after it (wander15, wander45). Variants: cf0.3 (v0.14.0 on a real rover), "
          "bridge+cf0.3 (dead reckoning only while the GPS has no fresh fix; v0.15.0 on a real "
          "rover), dr+cf0.3 (v0.13.0 on a real rover). Seeds %s. %d of %d missions completed. "
          "Simulated rovers only, so these speeds are upper bounds."
          % (__version__, pi.__version__, rp.__version__, dr.__version__, WANDER_M, WANDER_S,
             WANDER_S, "%d-%d" % (seeds[0], seeds[-1]) if seeds else "none",
             result["completed"], len(runs)), ""]
    if check is not None:
        md += ["Check against pace_i.py's runs: %d compared, %d identical, %d missing."
               % (check["compared"], check["identical"], check["missing"]), ""]
    md += ["## Overview (courses pooled)", ""]
    md += pf._table(["profile", "variant", "completed", "made good m/s (median)", "efficiency",
                     "runs beating 0.754", "path ratio", "share stopped"],
                    [(o["profile"], o["variant"], "%d/%d" % (o["completed"], o["runs"]),
                      o["median_made_good_mps"], o["median_efficiency"], o["beat_human_pace"],
                      o["median_path_ratio"], o["share_stopped"]) for o in s["overview"]])
    md += ["", "## Pilots against v0.14.0's, same profile", "",
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
    md += ["", "## What wandering costs each pilot", "",
           "Each variant with wandering fixes against itself on the same outages, paired by "
           "seed.", ""]
    md += pf._table(["variant", "profile", "against", "faster", "slower", "lost", "gained",
                     "largest median diff"],
                    [(t["variant"], t["profile"], t["against"],
                      "%d/%d" % (t["groups_faster"], t["groups"]), t["groups_slower"],
                      t["groups_lost"], t["groups_gained"], t["largest_median_diff_share"])
                     for t in p_tallies])
    md += [""]
    md += pf._table(["variant", "profile", "against", "course", "faster", "slower",
                     "median diff s", "share", "p"],
                    [(e["variant"], e["profile"], e["against"], e["course"], e["faster"],
                      e["slower"], e["median_time_diff_s"], e["median_time_diff_share"],
                      e["sign_test_p"]) for e in p_effects])
    md += ["", "## GPS outages and wandering fixes", ""]
    moved = {(x["profile"], x["variant"], x["cruise"], x["course"]): x["median_wandered"]
             for x in wanders}
    md += pf._table(["profile", "variant", "course", "missions", "reports withheld",
                     "reports moved", "s stood still"],
                    [(x["profile"], x["variant"], x["course"], x["missions"],
                      x["median_withheld"],
                      moved.get((x["profile"], x["variant"], x["cruise"], x["course"])),
                      x["median_stopped_s"]) for x in outages])
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
    ap.add_argument("--check", help="pace_i.py's runs.jsonl: fly the CHECKED missions again "
                                    "and compare")
    args = ap.parse_args(argv)
    courses = ps._names(args.courses, ps.COURSES, "course")
    profiles = ps._names(args.profiles, PROFILES, "profile")
    variants = ps._names(args.variants, VARIANTS, "variant")
    # outage15 and v0.14.0's real-rover pilot are always flown: the rest are compared with them.
    profiles = [BASE_PROFILE] + [p for p in profiles if p != BASE_PROFILE]
    variants = [BASE_VARIANT] + [v for v in variants if v != BASE_VARIANT]
    seeds = list(range(args.first_seed, args.first_seed + args.seeds))
    os.makedirs(args.out_dir, exist_ok=True)
    started = time.monotonic()
    check = check_pace_i(args.check) if args.check else None
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
                                   for v in result["verdicts"]],
                      "profile_verdicts": [{k: v[k] for k in ("variant", "profile", "against",
                                                              "groups_faster", "groups_slower",
                                                              "groups_lost")}
                                           for v in result["profile_verdicts"]]}), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
