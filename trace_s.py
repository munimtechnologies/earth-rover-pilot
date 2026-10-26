#!/usr/bin/env python3
"""trace_s: why was restarting the GPS average slower on outage90 boulevard?
(a diagnostic, not a pre-registered study)

pace_s.py's record (studies/pace-s/runs.jsonl) shows restart slower than the
shipped filter (a0.3) on 6 of 24 outage90 boulevard seeds and faster on none
(p 0.031), which by pace-s's rule R2 keeps the shipped filter on a real
rover. Five of the six were 2-8 s slower; seed 338 was 94 s slower, with 80 s
more spent stopped. On quietdrift90 boulevard, seed 338 took 1917.6 s with
both filters. This flies those missions again with both filters and records,
every second of simulated time, where the rover is, the pilot's estimate,
the command the rover is applying, whether the GPS filter has a fresh fix,
the time bridged on the wheels, recovery moves, checkpoints reached and the
true distance to the next checkpoint. It only reads: a test checks that a
traced mission's record is the same as an untraced one's, and --check
compares each traced mission with pace_s.py's record of it.

    python trace_s.py --out-dir out --check studies/pace-s/runs.jsonl

Writes trace-<profile>-<variant>-<seed>.csv (one row a second), summary.json
and report.md. Simulated rovers only. Standard library only. By MV2 of
Munim, Inc.; written with AI agents. Apache-2.0.
"""

from __future__ import annotations

import argparse
import contextlib
import csv
import json
import math
import os
import sys

import pace_h as ph
import pace_l as pl
import pace_s as pz
import pace_study as ps
import rover_pilot as rp
import trace_r as tr

__version__ = "0.1.0"

COURSE = "boulevard"
CRUISE = 0.8
# (profile, seed): the six outage90 boulevard seeds on which restart was
# slower, and quietdrift90's seed 338, where both filters took 1917.6 s.
MISSIONS = (("outage90", 327), ("outage90", 328), ("outage90", 331), ("outage90", 337),
            ("outage90", 338), ("outage90", 339), ("quietdrift90", 338))
VARIANTS = ("a0.3", "restart")
EVERY_S = 1.0
STOP_S = 4.0  # a stop: this many seconds or more in a row with the rover told to stand
FIELDS = ("t", "outage", "true_n", "true_e", "offset_m", "fix_n", "fix_e", "est_n", "est_e",
          "err_m", "filter_n", "filter_e", "has_fix", "bridged_s", "lin", "ang", "recoveries",
          "reached", "cp_m", "restarts")


def row(sim, pilot, points):
    """trace_r.row's fields and what the rover is doing: the command it is
    applying, whether the GPS filter has a fresh fix, the seconds bridged on
    the wheels so far, recovery moves and checkpoints so far, and the true
    distance to the next checkpoint."""
    x = tr.row(sim, pilot, points)
    f = getattr(pilot, "gps", None)
    cp_m = None
    if sim.next_cp < len(sim.checkpoint_coords):
        n, e = tr._enu(sim, *sim.checkpoint_coords[sim.next_cp])
        if n is not None:
            cp_m = tr._r(math.hypot(n - sim.north, e - sim.east))
    x.pop("rejected")
    x.update(has_fix=None if f is None else bool(f.has_fix(sim.t)),
             bridged_s=tr._r(pilot.bridged_s, 1), lin=tr._r(sim.applied[0]),
             ang=tr._r(sim.applied[1]), recoveries=pilot.recoveries,
             reached=len(pilot.reached), cp_m=cp_m)
    return x


@contextlib.contextmanager
def _tracing(rows, points, every_s=EVERY_S):
    """As trace_r._tracing, with this module's row."""
    pilots = []
    saved_pilot, saved_rover = ph.BridgePilot, pl.SlipRover

    def pilot(*args, **kw):
        p = saved_pilot(*args, **kw)
        pilots.append(p)
        return p

    def rover(*args, **kw):
        sim = saved_rover(*args, **kw)
        sleep, due = sim.sleep, [0.0]

        def traced(seconds):
            if pilots and sim.t >= due[0]:
                rows.append(row(sim, pilots[-1], points))
                due[0] = sim.t + every_s
            sleep(seconds)

        sim.sleep = traced
        return sim

    ph.BridgePilot, pl.SlipRover = pilot, rover
    try:
        yield pilots
    finally:
        ph.BridgePilot, pl.SlipRover = saved_pilot, saved_rover


def fly_traced(profile, variant, seed, course_name=COURSE, cruise=CRUISE):
    """pace_s.fly's mission with its rows; the record as pace_s.fly returns it."""
    rows = []
    with _tracing(rows, ps.COURSES[course_name]["points"]) as pilots:
        r = pz.fly(course_name, seed, profile, variant, cruise)
    if not pilots:
        raise RuntimeError("no BridgePilot was built, so nothing was traced")
    return r, rows


def stops(rows, least_s=STOP_S):
    """Each run of consecutive rows in which the rover applies no motion,
    lasting at least least_s: when it starts and ends, how much of it is in an
    outage, and at its first row whether the filter had a fresh fix, the
    checkpoints reached and the true distance to the next one."""
    out, cur = [], None
    for x in rows + [None]:
        still = x is not None and x["lin"] == 0 and x["ang"] == 0
        if still:
            if cur is None:
                cur = {"start": x["t"], "end": x["t"], "rows": 0, "in_outage": 0,
                       "has_fix": x["has_fix"], "reached": x["reached"], "cp_m": x["cp_m"]}
            cur["end"] = x["t"]
            cur["rows"] += 1
            cur["in_outage"] += 1 if x["outage"] else 0
        elif cur is not None:
            if cur["end"] - cur["start"] + EVERY_S >= least_s:
                out.append({"start": cur["start"], "end": cur["end"],
                            "outage_share": round(cur["in_outage"] / cur["rows"], 3),
                            "has_fix": cur["has_fix"], "reached": cur["reached"],
                            "cp_m": cur["cp_m"]})
            cur = None
    return out


def changes(rows, key):
    """The rows at which `key` goes up: t, the new value, whether in an
    outage, whether the filter had a fresh fix, the estimate's error and the
    true distance to the next checkpoint."""
    out, last = [], None
    for x in rows:
        v = x.get(key)
        if v is not None and last is not None and v > last:
            out.append({"t": x["t"], key: v, "outage": x["outage"], "has_fix": x["has_fix"],
                        "err_m": x["err_m"], "cp_m": x["cp_m"]})
        if v is not None:
            last = v
    return out


def diverged(a, b, tol_m=0.01):
    """The first t at which two traces' rovers are more than tol_m apart (rows
    matched by position in the list), or None."""
    for x, y in zip(a, b):
        if x["t"] != y["t"]:
            return x["t"]
        if math.hypot(x["true_n"] - y["true_n"], x["true_e"] - y["true_e"]) > tol_m:
            return x["t"]
    return None


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out-dir", default="out")
    ap.add_argument("--missions", help="comma-separated profile:seed, default: "
                    + ",".join("%s:%d" % m for m in MISSIONS))
    ap.add_argument("--check", help="pace_s.py's runs.jsonl: compare each traced mission with it")
    args = ap.parse_args(argv)
    missions = MISSIONS
    if args.missions:
        missions = tuple((p, int(s)) for p, s in (m.split(":") for m in args.missions.split(",")))
    os.makedirs(args.out_dir, exist_ok=True)
    ref = tr.load_record(args.check) if args.check else None
    result = {"version": __version__, "pace_s": pz.__version__, "trace_r": tr.__version__,
              "rover_pilot": rp.__version__, "course": COURSE, "cruise": CRUISE,
              "every_s": EVERY_S, "stop_s": STOP_S, "missions": []}
    md = ["# Why was restarting the GPS average slower on outage90 boulevard? (simulated)", "",
          "trace_s.py %s (pace_s.py %s, rover_pilot.py %s), MV2 of Munim, Inc. A diagnostic, not "
          "a pre-registered study: pace_s.py's missions flown again with both GPS filters, one "
          "row a second of simulated time (trace-<profile>-<variant>-<seed>.csv). A stop is %g s "
          "or more with the rover told to stand." % (__version__, pz.__version__, rp.__version__,
                                                     STOP_S), ""]
    for profile, seed in missions:
        traces = {}
        m = {"profile": profile, "seed": seed, "variants": {}}
        md += ["## %s, seed %d" % (profile, seed), ""]
        for variant in VARIANTS:
            r, rows = fly_traced(profile, variant, seed)
            traces[variant] = rows
            name = "trace-%s-%s-%d.csv" % (profile, variant, seed)
            with open(os.path.join(args.out_dir, name), "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=FIELDS)
                w.writeheader()
                for x in rows:
                    w.writerow({k: ("" if x[k] is None else x[k]) for k in FIELDS})
            check = None
            if ref is not None:
                want = ref.get((profile, variant, CRUISE, COURSE, seed))
                check = {"found": want is not None,
                         "different": tr.compare(r, want) if want is not None else None}
            errs = [x["err_m"] for x in rows if x["err_m"] is not None]
            v = {"rows": len(rows), "csv": name, "check": check,
                 "record": {k: r.get(k) for k in ("ok", "elapsed_s", "made_good_mps",
                                                   "recoveries", "time_s", "position_err",
                                                   "gps", "outage")},
                 "max_err_m": max(errs) if errs else None,
                 "outages": tr.outages(rows), "stops": stops(rows),
                 "recoveries": changes(rows, "recoveries"),
                 "checkpoints": changes(rows, "reached")}
            m["variants"][variant] = v
            md += ["### %s" % variant, "",
                   "%d rows; %s s; %s recoveries; time stopped %s s; largest estimate error %s m."
                   % (len(rows), r.get("elapsed_s"), r.get("recoveries"),
                      (r.get("time_s") or {}).get("stopped"), v["max_err_m"])]
            if check is not None:
                md += ["Against pace_s.py's record: %s." % (
                    "not in the record" if not check["found"] else
                    "identical" if not check["different"] else
                    "differs in " + ", ".join(check["different"]))]
            md += ["", "Outages (first and last second): %s" % (
                "; ".join("%g-%g" % (a, b) for a, b in v["outages"]) or "none"), "",
                "Checkpoints reached at: %s" % (
                    ", ".join("%g s" % x["t"] for x in v["checkpoints"]) or "none"), "",
                "Stops:", ""]
            md += ["- %g-%g s, %.0f%% in an outage, fresh fix at its start: %s, %s checkpoints "
                   "reached, %s m from the next" % (x["start"], x["end"], 100 * x["outage_share"],
                                                    x["has_fix"], x["reached"], x["cp_m"])
                   for x in v["stops"]] or ["- none"]
            md += ["", "Recovery moves:", ""]
            md += ["- at %g s, %s, fresh fix: %s, estimate %s m off, %s m from the next "
                   "checkpoint" % (x["t"], "in an outage" if x["outage"] else "with sky",
                                   x["has_fix"], x["err_m"], x["cp_m"])
                   for x in v["recoveries"]] or ["- none"]
            md += [""]
            print("%s %s %d: %d rows, %s s, check %s" % (profile, variant, seed, len(rows),
                                                         r.get("elapsed_s"), check), flush=True)
        a, b = (m["variants"][x]["record"]["elapsed_s"] for x in VARIANTS)
        m["diff_s"] = None if a is None or b is None else round(b - a, 1)
        m["diverged_t"] = diverged(traces[VARIANTS[0]], traces[VARIANTS[1]])
        md += ["%s minus %s: %s s; the rovers first part at %s s." % (
            VARIANTS[1], VARIANTS[0], m["diff_s"], m["diverged_t"]), ""]
        result["missions"].append(m)
    with open(os.path.join(args.out_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, indent=1)
    with open(os.path.join(args.out_dir, "report.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
