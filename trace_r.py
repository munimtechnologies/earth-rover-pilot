#!/usr/bin/env python3
"""trace_r: what threw the pilot's position off on pace_r.py's outage90
boulevard mission, seed 313? (a diagnostic, not a pre-registered study)

pace_r.py's record (studies/pace-r/runs.jsonl) shows that on this mission the
shipped filter's position estimate was at worst 63.7 m from the rover while
the rover stayed within 7.7 m of the course, and that track-12's rover
followed an estimate up to 32.3 m off, up to 32.7 m from the course. This
flies the mission again with each of pace_r.py's variants and records, every
second of simulated time, where the rover is, whether its GPS is in an
outage, its latest GPS sample, the pilot's position estimate and its GPS
filter's state. It only reads: a test checks that a traced mission's record
is the same as an untraced one's, and --check compares each traced mission
with pace_r.py's record of it.

    python trace_r.py --out-dir out --check studies/pace-r/runs.jsonl

Writes trace-<variant>.csv (one row a second), summary.json and report.md.
Simulated rovers only. Standard library only. By MV2 of Munim, Inc.; written
with AI agents. Apache-2.0.
"""

from __future__ import annotations

import argparse
import contextlib
import csv
import json
import math
import os
import sys

import pace_e as pe
import pace_h as ph
import pace_l as pl
import pace_r as pr
import pace_study as ps
import rover_pilot as rp

__version__ = "0.1.0"

COURSE = "boulevard"
SEED = 313
PROFILE = "outage90"
CRUISE = 0.8
EVERY_S = 1.0
FAR_M = 8.0  # pace_o.py's "far" from the course
LOST_M = 10.0  # an estimate this far from the rover
WINDOW_S = 20.0  # rows kept in summary.json either side of the worst estimate
FIELDS = ("t", "outage", "true_n", "true_e", "offset_m", "fix_n", "fix_e", "est_n", "est_e",
          "err_m", "filter_n", "filter_e", "rejected", "restarts")


def _r(x, digits=2):
    return None if x is None else round(x, digits)


def _enu(sim, lat, lon):
    """(north, east) in metres of a latitude and longitude, or (None, None)
    when there is no fix."""
    if lat is None or lon is None or rp.parse_fix(lat, lon) is None:
        return None, None
    east, north = rp.to_enu(sim.lat0, sim.lon0, lat, lon)
    return north, east


def row(sim, pilot, points):
    """One row of FIELDS: the rover now, as the simulator and the pilot see it."""
    gps = getattr(sim, "gps", None)
    fix_n, fix_e = _enu(sim, gps[0], gps[1]) if gps else (None, None)
    pos = pilot.pos
    est_n, est_e = _enu(sim, pos[0], pos[1]) if pos is not None else (None, None)
    f = getattr(pilot, "gps", None)
    filt_n, filt_e = (_enu(sim, getattr(f, "lat", None), getattr(f, "lon", None))
                      if f is not None else (None, None))
    err = None if est_n is None else math.hypot(est_n - sim.north, est_e - sim.east)
    return {"t": _r(sim.t), "outage": bool(sim.in_outage(sim.t)),
            "true_n": _r(sim.north), "true_e": _r(sim.east),
            "offset_m": _r(pe.course_offset(points, sim.north, sim.east)),
            "fix_n": _r(fix_n), "fix_e": _r(fix_e), "est_n": _r(est_n), "est_e": _r(est_e),
            "err_m": _r(err), "filter_n": _r(filt_n), "filter_e": _r(filt_e),
            "rejected": getattr(f, "rejected", None), "restarts": getattr(f, "restarts", None)}


@contextlib.contextmanager
def _tracing(rows, points, every_s=EVERY_S):
    """While inside, every BridgePilot pace_i.fly builds is kept (the list
    yielded), and every rover pace_l.fly builds appends a row to `rows` every
    `every_s` of simulated time once that pilot exists. Only reads."""
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


def fly_traced(variant, course_name=COURSE, seed=SEED, profile=PROFILE, cruise=CRUISE):
    """pace_r.fly's mission with its rows; the record as pace_r.fly returns it."""
    rows = []
    with _tracing(rows, ps.COURSES[course_name]["points"]) as pilots:
        r = pr.fly(course_name, seed, profile, variant, cruise)
    if not pilots:
        raise RuntimeError("no BridgePilot was built, so nothing was traced")
    return r, rows


def intervals(rows, key, above):
    """Each run of consecutive rows whose `key` is above `above`: its first and
    last t, the peak and when, and the share of its rows in an outage."""
    out, cur = [], None
    for x in rows:
        v = x.get(key)
        if v is not None and v > above:
            if cur is None:
                cur = {"start": x["t"], "end": x["t"], "peak": v, "peak_t": x["t"], "rows": 0,
                       "in_outage": 0}
            cur["end"] = x["t"]
            cur["rows"] += 1
            cur["in_outage"] += 1 if x["outage"] else 0
            if v > cur["peak"]:
                cur["peak"], cur["peak_t"] = v, x["t"]
        elif cur is not None:
            out.append(cur)
            cur = None
    if cur is not None:
        out.append(cur)
    return [{"start": c["start"], "end": c["end"], "peak": c["peak"], "peak_t": c["peak_t"],
             "outage_share": round(c["in_outage"] / c["rows"], 3)} for c in out]


def outages(rows):
    """(first t, last t) of each run of rows in an outage."""
    out, start, last = [], None, None
    for x in rows:
        if x["outage"]:
            start = x["t"] if start is None else start
            last = x["t"]
        elif start is not None:
            out.append([start, last])
            start = None
    if start is not None:
        out.append([start, last])
    return out


def window(rows, key, half_s=WINDOW_S):
    """The rows within half_s of the row where `key` peaks."""
    xs = [x for x in rows if x.get(key) is not None]
    if not xs:
        return []
    peak = max(xs, key=lambda x: x[key])["t"]
    return [x for x in rows if abs(x["t"] - peak) <= half_s]


def load_record(path):
    ref = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                r = json.loads(line)
                ref[(r["profile"], r["variant"], r["cruise"], r["course"], r["seed"])] = r
    return ref


def compare(record, want):
    """The fields of pace_r.py's record that the traced mission doesn't match."""
    got = json.loads(json.dumps(record))
    return sorted(k for k in want if k not in ("profile", "variant", "cruise", "course", "seed")
                  and got.get(k) != want[k])


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out-dir", default="out")
    ap.add_argument("--variants", help="comma-separated subset of: " + ",".join(pr.VARIANTS))
    ap.add_argument("--check", help="pace_r.py's runs.jsonl: compare each traced mission with it")
    args = ap.parse_args(argv)
    variants = ps._names(args.variants, pr.VARIANTS, "variant")
    os.makedirs(args.out_dir, exist_ok=True)
    ref = load_record(args.check) if args.check else None
    result = {"version": __version__, "pace_r": pr.__version__, "rover_pilot": rp.__version__,
              "course": COURSE, "seed": SEED, "profile": PROFILE, "cruise": CRUISE,
              "every_s": EVERY_S, "far_m": FAR_M, "lost_m": LOST_M, "variants": {}}
    md = ["# What threw the pilot's position off on outage90 boulevard, seed 313? (simulated)", "",
          "trace_r.py %s (pace_r.py %s, rover_pilot.py %s), MV2 of Munim, Inc. A diagnostic, not a "
          "pre-registered study: pace_r.py's mission flown again with each variant, one row a "
          "second of simulated time (trace-<variant>.csv)."
          % (__version__, pr.__version__, rp.__version__), ""]
    for variant in variants:
        r, rows = fly_traced(variant)
        name = "trace-%s.csv" % variant
        with open(os.path.join(args.out_dir, name), "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=FIELDS)
            w.writeheader()
            for x in rows:
                w.writerow({k: ("" if x[k] is None else x[k]) for k in FIELDS})
        key = (PROFILE, variant, CRUISE, COURSE, SEED)
        check = None
        if ref is not None:
            want = ref.get(key)
            check = {"found": want is not None,
                     "different": compare(r, want) if want is not None else None}
        errs = [x["err_m"] for x in rows if x["err_m"] is not None]
        offs = [x["offset_m"] for x in rows if x["offset_m"] is not None]
        v = {"rows": len(rows), "csv": name, "check": check,
             "record": {k: r.get(k) for k in ("ok", "elapsed_s", "made_good_mps", "recoveries",
                                               "offset", "position_err", "gps", "outage")},
             "max_err_m": max(errs) if errs else None,
             "max_offset_m": max(offs) if offs else None,
             "outages": outages(rows),
             "far": intervals(rows, "offset_m", FAR_M),
             "lost": intervals(rows, "err_m", LOST_M),
             "around_worst_estimate": window(rows, "err_m")}
        result["variants"][variant] = v
        md += ["## %s" % variant, "",
               "%d rows; made good %s m/s; largest estimate error %s m, largest distance from the "
               "course %s m (one row a second)." % (len(rows), r.get("made_good_mps"),
                                                    v["max_err_m"], v["max_offset_m"])]
        if check is not None:
            md += ["Against pace_r.py's record: %s." % (
                "not in the record" if not check["found"] else
                "identical" if not check["different"] else
                "differs in " + ", ".join(check["different"]))]
        md += ["", "Outages (first and last second): %s" % (
            "; ".join("%g-%g" % (a, b) for a, b in v["outages"]) or "none"), ""]
        for label, xs in (("Further than %g m from the course" % FAR_M, v["far"]),
                          ("Estimate further than %g m from the rover" % LOST_M, v["lost"])):
            md += ["%s:" % label, ""]
            md += ["- %g-%g s, peak %g m at %g s, %.0f%% in an outage"
                   % (x["start"], x["end"], x["peak"], x["peak_t"], 100 * x["outage_share"])
                   for x in xs] or ["- never"]
            md += [""]
        print("%s: %d rows, max err %s m, max offset %s m, check %s"
              % (variant, len(rows), v["max_err_m"], v["max_offset_m"], check), flush=True)
    with open(os.path.join(args.out_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, indent=1)
    with open(os.path.join(args.out_dir, "report.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
