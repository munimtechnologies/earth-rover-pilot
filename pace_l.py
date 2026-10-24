#!/usr/bin/env python3
"""pace_l: does the 120 s reach hold up when the wheels and the compass lie?

Since v0.16.0 the bridging reckoner (the real-rover default) carries the
position up to 120 s after the last fix (pace_k.py). In pace_k.py's
simulator the wheels report the commanded speed exactly and the compass
error only wobbles, so the reckoned position barely drifted. On a real
rover the wheels slip more on grass than on pavement, so metres per RPM
change along the way, and the compass error drifts. This study flies
pace_k.py's three reaches on rovers that do both:

- slip: the wheels report a factor times their true RPM, drawn uniformly
  from [1 - SLIP, 1 + SLIP] for each spell, with spells lasting
  SLIP_EVERY_S on average (exponential); the rover itself drives exactly
  as before;
- drift: pace_d.py's drifting compass error (SD 10 deg, 120 s time constant).

Profiles: pace_k.py's outage45 and outage90, lie45 (outage45 with both),
slip90, drift90 and lie90 (outage90 with slip, with drift, with both).
Variants: pace_k.py's bridge+cf0.3 (reach 30 s), bridge60+cf0.3 and
bridge120+cf0.3 (v0.16.0 on a real rover).

    python pace_l.py --out-dir out --first-seed 157 --seeds 24 --check studies/pace-k/runs.jsonl

With --check it first flies seeds 133-135 of pace_k.py's outage45 and
outage90 bridge+cf0.3 and bridge120+cf0.3 missions again and compares each
field by field with pace_k.py's record. Every mission is flown by
pace_j.fly itself, on a SlipRover. Simulated rovers only, so the speeds are
upper bounds. Standard library only. By MV2 of Munim, Inc.; written with AI
agents. Apache-2.0.
"""

from __future__ import annotations

import argparse
import bisect
import contextlib
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
import pace_i as pi
import pace_j as pj
import pace_k as pk
import pace_study as ps
import rover_pilot as rp

__version__ = "0.1.0"

# How far off the wheels' metres per RPM can be in a spell, and how long a
# spell lasts on average.
SLIP = 0.15
SLIP_EVERY_S = 120.0
# pace_d.py's drift10.
DRIFT = {"drift_deg": 10.0, "drift_tau_s": 120.0}
_SLIP = {"slip": SLIP, "slip_every_s": SLIP_EVERY_S}
PROFILES = {
    "outage45": pk.PROFILES["outage45"],
    "lie45": dict(pk.PROFILES["outage45"], **_SLIP, **DRIFT),
    "outage90": pk.PROFILES["outage90"],
    "slip90": dict(pk.PROFILES["outage90"], **_SLIP),
    "drift90": dict(pk.PROFILES["outage90"], **DRIFT),
    "lie90": dict(pk.PROFILES["outage90"], **_SLIP, **DRIFT),
}
# The first is always flown.
BASE_PROFILE = next(iter(PROFILES))
# (a, b): each variant on profile b against itself on profile a, paired by seed
# (same outages, same draws), so the difference is what the lies cost.
PROFILE_PAIRS = (("outage45", "lie45"), ("outage90", "slip90"), ("outage90", "drift90"),
                 ("outage90", "lie90"))
# pace_k.py's reaches; the first is v0.15.0's.
VARIANTS = dict(pk.VARIANTS)
BASE_VARIANT = next(iter(VARIANTS))
PAIRS = pk.PAIRS
CRUISES = (0.8,)
# pace_k.py flew seeds 133-156; these start after them.
FIRST_SEED = 157
# pace_k.py flew these with the same settings; --check flies them again.
CHECKED = {"profiles": ("outage45", "outage90"),
           "variants": ("bridge+cf0.3", "bridge120+cf0.3"), "seeds": (133, 134, 135)}


def slip_spells(seed, slip, every_s, horizon_s=pi.OUTAGE_HORIZON_S):
    """[(start, factor)]: from each start the wheels report factor times their
    true RPM, drawn from a generator of their own; [] without slip."""
    if slip <= 0:
        return []
    rng = random.Random("pace-l-%d" % seed)
    spells = []
    t = 0.0
    while t < horizon_s:
        spells.append((t, rng.uniform(1.0 - slip, 1.0 + slip)))
        t += rng.expovariate(1.0 / every_s)
    return spells


class SlipRover(pj.WanderRover):
    """WanderRover whose wheels report slip_at(t) times their true RPM. It
    drives exactly as a WanderRover with the same seed, and with slip 0 it
    reports the same wheels too."""

    def __init__(self, checkpoints_m, seed=0, slip=0.0, slip_every_s=SLIP_EVERY_S, **kw):
        self.slip = float(slip)
        self.slip_every_s = float(slip_every_s)
        self.spells = slip_spells(seed, self.slip, self.slip_every_s)
        self._spell_starts = [a for a, _ in self.spells]
        super().__init__(checkpoints_m, seed=seed, **kw)

    def slip_at(self, t):
        i = bisect.bisect_right(self._spell_starts, t) - 1
        return self.spells[i][1] if i >= 0 else 1.0

    def _wheel_row(self, linear, angular):
        k = self.slip_at(self.t)
        if k == 1.0:
            super()._wheel_row(linear, angular)
            return
        true = self.wheel_mps_per_rpm
        self.wheel_mps_per_rpm = true / k
        try:
            super()._wheel_row(linear, angular)
        finally:
            self.wheel_mps_per_rpm = true

    def slip_stats(self):
        """Spells begun by now and their mean |factor - 1|; None without slip."""
        seen = [k for a, k in self.spells if a <= self.t]
        if not seen:
            return None
        return {"spells": len(seen),
                "mean_abs_slip": round(sum(abs(k - 1.0) for k in seen) / len(seen), 4)}


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


@contextlib.contextmanager
def _slipping(made):
    """While inside, pace_j.fly builds its rovers as SlipRovers, each appended
    to `made`."""
    def make(*args, **kw):
        sim = SlipRover(*args, **kw)
        made.append(sim)
        return sim

    saved = pj.WanderRover
    pj.WanderRover = make
    try:
        yield
    finally:
        pj.WanderRover = saved


def fly(course_name, seed, profile, variant, cruise, course=None):
    """One mission flown by pace_j.fly on a SlipRover with the profile's
    settings and the variant's reckoner; also the wheels' slip spells."""
    made = []
    with _known(profile, variant), _slipping(made):
        r = pj.fly(course_name, seed, profile, variant, cruise, course=course)
    r["slip"] = made[0].slip_stats() if made else None
    return r


def failed_run(exc):
    return dict(pk.failed_run(exc), slip=None)


def check_pace_k(path):
    """Fly the CHECKED missions again and compare each with pace_k.py's record
    of it (its runs.jsonl): every field pace_k.py recorded must be equal. A
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
    return pk.pair_effects(runs)


def profile_effects(runs):
    """pace_j.profile_effects with this study's variants and PROFILE_PAIRS."""
    saved = pj.VARIANTS, pj.PROFILE_PAIRS
    pj.VARIANTS, pj.PROFILE_PAIRS = VARIANTS, PROFILE_PAIRS
    try:
        return pj.profile_effects(runs)
    finally:
        pj.VARIANTS, pj.PROFILE_PAIRS = saved


def slip_rows(runs):
    """Per (profile, variant, cruise, course), over the completed missions with
    slip: the median spells begun and the median of their mean |factor - 1|."""
    rows = []
    for k, rs in sorted(pg._groups(runs).items()):
        done = [r for r in rs if r["ok"] and r.get("slip")]
        if not done:
            continue
        rows.append({"profile": k[0], "variant": k[1], "cruise": k[2], "course": k[3],
                     "missions": len(done),
                     "median_spells": ps._median([r["slip"]["spells"] for r in done], 1),
                     "median_mean_abs_slip": ps._median([r["slip"]["mean_abs_slip"]
                                                         for r in done], 4)})
    return rows


def write_outputs(out_dir, runs, started, seeds, done, check=None):
    s = ps.summarise(runs)
    effects, tallies = pair_effects(runs)
    p_effects, p_tallies = profile_effects(runs)
    outages = pi.outage_rows(runs)
    steering = ph.steer_rows(runs)
    positions = pg.position_rows(runs)
    reckoning = pg.dr_rows(runs)
    offsets = pe.offset_rows(runs)
    headings = pd.heading_rows(runs)
    slips = slip_rows(runs)
    result = {"version": __version__, "pace_k": pk.__version__, "pace_j": pj.__version__,
              "pace_i": pi.__version__, "pace_d": pd.__version__, "pace_study": ps.__version__,
              "rover_pilot": rp.__version__, "dead_reckon": dr.__version__, "done": done,
              "elapsed_s": round(time.monotonic() - started, 1), "seeds": seeds,
              "human": {"marathon_m": ps.MARATHON_M, "time_s": ps.HUMAN_S,
                        "mps": round(ps.HUMAN_MPS, 4)},
              "profiles": PROFILES, "variants": VARIANTS, "pairs": [list(x) for x in PAIRS],
              "profile_pairs": [list(x) for x in PROFILE_PAIRS], "cruises": list(CRUISES),
              "steering": rp.ROVER_STEERING, "dead_reckon_settings": rp.DEAD_RECKON,
              "runs": len(runs), "completed": sum(1 for r in runs if r["ok"]),
              "overview": s["overview"], "pair_effect": effects, "verdicts": tallies,
              "profile_effect": p_effects, "profile_verdicts": p_tallies,
              "outage": outages, "steer": steering, "position": positions,
              "reckoner": reckoning, "offset": offsets, "heading": headings, "slip": slips,
              "check": check}
    with open(os.path.join(out_dir, "summary.json"), "w") as f:
        json.dump(result, f, indent=1)
    with open(os.path.join(out_dir, "runs.jsonl"), "w") as f:
        for r in runs:
            f.write(json.dumps(r) + "\n")
    md = ["# Does the 120 s reach hold up when the wheels and the compass lie? (simulated)",
          "",
          "pace_l.py %s (pace_k.py %s, pace_j.py %s, rover_pilot.py %s, dead_reckon.py %s), MV2 "
          "of Munim, Inc. Every profile is pace_k.py's measured Mini+ with 45 s GPS outages "
          "(after 300 s of sky on average) or 90 s outages (after 600 s); slip: the wheels "
          "report a factor drawn from [%.2f, %.2f] times their true RPM, changing every %.0f s "
          "on average; drift: the compass error drifts (SD %.0f deg, %.0f s time constant); "
          "lie: both. Variants: the bridging pilot with the reckoner carrying the position up "
          "to 30 s (bridge+cf0.3), 60 s (bridge60+cf0.3) or 120 s (bridge120+cf0.3, v0.16.0 on "
          "a real rover) after the last fix. Seeds %s. %d of %d missions completed. Simulated "
          "rovers only, so these speeds are upper bounds."
          % (__version__, pk.__version__, pj.__version__, rp.__version__, dr.__version__,
             1.0 - SLIP, 1.0 + SLIP, SLIP_EVERY_S, DRIFT["drift_deg"], DRIFT["drift_tau_s"],
             "%d-%d" % (seeds[0], seeds[-1]) if seeds else "none",
             result["completed"], len(runs)), ""]
    if check is not None:
        md += ["Check against pace_k.py's runs: %d compared, %d identical, %d missing."
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
    md += ["", "## What the lies cost, same variant", ""]
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
    md += ["", "## GPS outages", ""]
    md += pf._table(["profile", "variant", "course", "missions", "reports withheld",
                     "s stood still"],
                    [(x["profile"], x["variant"], x["course"], x["missions"],
                      x["median_withheld"], x["median_stopped_s"]) for x in outages])
    md += ["", "## Where the pilot thinks it is, against where it is", ""]
    md += pf._table(["profile", "variant", "course", "missions", "median m", "p95 m"],
                    [(x["profile"], x["variant"], x["course"], x["missions"],
                      x["median_position_err_m"], x["p95_position_err_m"]) for x in positions])
    md += ["", "## Distance from the course while driving forward", ""]
    md += pf._table(["profile", "variant", "course", "missions", "median m", "p95 m"],
                    [(x["profile"], x["variant"], x["course"], x["missions"],
                      x["median_offset_m"], x["p95_offset_m"]) for x in offsets])
    md += ["", "## Heading error", ""]
    md += pf._table(["profile", "variant", "course", "missions", "median abs deg", "rms deg"],
                    [(x["profile"], x["variant"], x["course"], x["missions"],
                      x["median_abs_deg"], x["rms_deg"]) for x in headings])
    md += ["", "## How hard the pilot steers", ""]
    md += pf._table(["profile", "variant", "course", "missions", "mean abs angular"],
                    [(x["profile"], x["variant"], x["course"], x["missions"],
                      x["median_mean_abs_angular"]) for x in steering])
    md += ["", "## Dead reckoning", ""]
    md += pf._table(["profile", "variant", "course", "missions", "never trusted",
                     "first trusted s", "s on wheels alone", "abs scale error"],
                    [(x["profile"], x["variant"], x["course"], x["missions"],
                      x["never_trusted"], x["median_trusted_at_s"], x["median_bridged_s"],
                      x["median_abs_scale_error"]) for x in reckoning])
    md += ["", "## Wheel slip spells", ""]
    md += pf._table(["profile", "variant", "course", "missions", "spells", "mean abs slip"],
                    [(x["profile"], x["variant"], x["course"], x["missions"],
                      x["median_spells"], x["median_mean_abs_slip"]) for x in slips])
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
    ap.add_argument("--check", help="pace_k.py's runs.jsonl: fly the CHECKED missions again "
                                    "and compare")
    args = ap.parse_args(argv)
    courses = ps._names(args.courses, ps.COURSES, "course")
    profiles = ps._names(args.profiles, PROFILES, "profile")
    variants = ps._names(args.variants, VARIANTS, "variant")
    # outage45 and v0.15.0's reach are always flown: the rest are compared with them.
    profiles = [BASE_PROFILE] + [p for p in profiles if p != BASE_PROFILE]
    variants = [BASE_VARIANT] + [v for v in variants if v != BASE_VARIANT]
    seeds = list(range(args.first_seed, args.first_seed + args.seeds))
    os.makedirs(args.out_dir, exist_ok=True)
    started = time.monotonic()
    check = check_pace_k(args.check) if args.check else None
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
