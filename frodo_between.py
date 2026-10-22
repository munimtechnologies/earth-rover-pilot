#!/usr/bin/env python3
"""frodo_between: what a live pilot's compass is worth between its 1 Hz reads.

The FrodoBots-2K compass studies (frodo_compass, frodo_compass_live,
frodo_blend, frodo_blend_b) give every 0.2 s cell a heading interpolated
between the compass samples on either side of it, so inside each gap they
use a sample up to a second in the future. A pilot driving the rover only
has the samples it has already read. This study scores, on the same rides,
anchors and running hard-iron fit as frodo_blend_b, headings a live pilot can
compute, each with the running fit's bias:

- interp: frodo_blend_b's running heading (interpolated; the reference).
- last: the latest compass sample at or before the cell, held.
- gyro05, gyro1: the latest sample turned by 0.5x or 1x the gyroscope's turn
  since it was read (the latest gyroscope sample's rate, at most
  GYRO_AGE_S old, less the median offset of the samples before scoring starts).
- cmd20: the latest sample turned by the angular command since it was read,
  at 20 deg/s per unit (frodo_odometry's best command gain).
- b2_<each>: v0.11.0's course hold on that heading (the last GPS course for
  2 s, then the heading with the difference fading out over 2 s more).
- course: the last GPS course.

Every variant uses the bias the running fit learned from the interpolated
headings, so the anchors are frodo_blend_b's exactly; a test checks that
course, interp and b2_interp give frodo_blend_b's course, running and blend2
misses. The rules for reading the result are in PREDICTION.md, written
before the run.

    python frodo_between.py --out-dir out --rides-per-part 30

Needs frodo_blend_b.py, frodo_blend.py, frodo_compass.py,
frodo_compass_live.py and frodo_motion.py next to it. Standard library only.
By MV2 of Munim, Inc.; written with AI agents. Apache-2.0.
"""

from __future__ import annotations

import argparse
import array
import bisect
import json
import math
import os
import random
import statistics
import sys
import time

import frodo_blend as fb
import frodo_blend_b as fbb
import frodo_compass as fc
import frodo_compass_live as fl
import frodo_motion as fm

__version__ = "0.1.0"

SOURCES = ("interp", "last", "gyro05", "gyro1", "cmd20")
NAMES = ("course",) + SOURCES + tuple("b2_" + s for s in SOURCES)
BETWEEN = ("gyro05", "gyro1", "cmd20")
HOLD_S = 2               # v0.11.0's course hold, faded (frodo_blend_b's blend2)
GYRO_AGE_S = 1.5         # a gyroscope sample older than this gives no turn
REPORT_H = (1, 5, 10, 30)
B_RUNNING_OVER_COURSE = 0.883   # frodo-blend-b-v2: running / course at 10 s
B_BLEND2_OVER_RUNNING = 0.944   # and blend2 / running at 10 s
REPRO_TOL = 0.002        # E1: interp and b2_interp must land this close to those
CHECK_MIN_PAIRS = 2000   # and on at least this many pairs at 10 s
ADOPT_MAX = 0.98         # D2: a between-read heading over last at 10 s at most this,
COST_30S = 0.02          # CI top below 1, and over course at 30 s no more than this above last
HOLD_MAX = 0.97          # D3: b2_last / last at 10 s at most this, CI top below 1


# --- Headings a live pilot can compute -----------------------------------------

def at(cum, grid, t):
    """The running total cum (one value per cell boundary) at time t, linear
    inside a cell and held at the ends."""
    x = min(max((t - grid.t0) / grid.dt, 0.0), len(cum) - 1.0)
    k = min(int(math.floor(x)), len(cum) - 2)
    return cum[k] + (x - k) * (cum[k + 1] - cum[k])


def last_reads(samples, grid, cents):
    """(headings, times): per cell, the heading of the latest compass sample at or
    before the cell centre about the centre the running fit had then, and that
    sample's time; None, None where there is no sample or no centre yet."""
    ct = [s[0] for s in samples]
    ts = [c[0] for c in cents]
    hs, tt = [], []
    for k in range(grid.n):
        tc = fl.cell_time(grid, k)
        j = bisect.bisect_right(ct, tc) - 1
        i = bisect.bisect_right(ts, tc) - 1
        centre = cents[i][1] if i >= 0 else None
        if j < 0 or centre is None:
            hs.append(None)
            tt.append(None)
        else:
            hs.append(fl.heading_of(samples[j], centre))
            tt.append(ct[j])
    return hs, tt


def gyro_offset(gyro, t_end):
    """Median gyroscope x reading before t_end (of every sample if fewer than 20)."""
    early = [g[1] for g in gyro if g[0] < t_end]
    if len(early) < 20:
        early = [g[1] for g in gyro]
    return statistics.median(early) if early else 0.0


def causal_rates(grid, gyro, offset, max_age=GYRO_AGE_S):
    """Turn rate (deg/s, counter-clockwise) in each cell: the latest gyroscope
    sample at or before the cell centre less offset, or 0 if none is max_age new."""
    gt = [g[0] for g in gyro]
    out = []
    for k in range(grid.n):
        tc = fl.cell_time(grid, k)
        j = bisect.bisect_right(gt, tc) - 1
        out.append(gyro[j][1] - offset if j >= 0 and tc - gt[j] <= max_age + 1e-9 else 0.0)
    return out


def between(hs, tt, grid, cum, gain):
    """Per cell: the last read hs turned by gain times the counter-clockwise turn
    in cum from its time tt to the cell centre (headings run clockwise)."""
    out = []
    for k, (h, t) in enumerate(zip(hs, tt)):
        if h is None:
            out.append(None)
        else:
            turn = at(cum, grid, fl.cell_time(grid, k)) - at(cum, grid, t)
            out.append((h - gain * turn) % 360.0)
    return out


def with_fallback(hs, base):
    """fc.filled(hs), with base's heading in any cell still empty."""
    return [b if h is None else h for h, b in zip(fc.filled(hs), base)]


# --- One ride ------------------------------------------------------------------

def new_pool():
    return {"rides": [], "gps_s": 0.0}


def analyse_ride(control, gps, gyro, compass, pool, no=0, anchor_every=3):
    """frodo_blend_b.analyse_ride's anchors, scoring NAMES."""
    st = {"control_rows": len(control), "gps_rows": len(gps),
          "compass_samples": len(compass or [])}
    if len(control) < 50 or len(gps) < 20:
        st["skipped"] = "too little data"
        return st
    if not compass or len(compass) < 20:
        st["skipped"] = "no compass"
        return st
    tc0 = compass[0][0]
    full_info, full_centre = fc.calibrate(compass, fl.A, fl.B)
    if not full_info["ok"]:
        st["skipped"] = "whole ride does not calibrate"
        return st
    grid = fc.Grid(control, gyro)
    where = fc.compass_cells(grid, [c[0] for c in compass])
    cents = fl.running_centres(compass, fl.cell_time(grid, grid.n - 1))
    heads = {"running": fl.running_headings(compass, where, grid, cents),
             "full": fc.frame_headings(compass, where, fl.A, fl.B, fl.S, full_centre)}
    fixes = fc.fresh_fixes(gps)
    fits = {}
    for v, h in heads.items():
        got = fc.learn_bias(control, fixes, grid, {v: h})
        if got:
            fits[v] = ([x[0] for x in got], [x[1][v] for x in got])
    st["bias_fits"] = {v: len(f[0]) for v, f in fits.items()}
    if "full" not in fits:
        st["skipped"] = "no straight stretch for the bias"
        return st
    if "running" not in fits:
        st["skipped"] = "running fit learns no bias"
        return st
    hr = fc.filled(heads["running"])
    last_h, last_t = last_reads(compass, grid, cents)
    offset = gyro_offset(gyro or [], tc0 + fl.SCORE_AFTER_S)
    gyro_cum = fc.cumulate(causal_rates(grid, gyro or [], offset), grid.dt)
    src = {"interp": hr, "last": with_fallback(last_h, hr),
           "gyro05": with_fallback(between(last_h, last_t, grid, gyro_cum, 0.5), hr),
           "gyro1": with_fallback(between(last_h, last_t, grid, gyro_cum, 1.0), hr),
           "cmd20": with_fallback(between(last_h, last_t, grid, grid.cmd_yaw, fc.CMD_GAIN), hr)}
    st["gyro_offset"] = fc._r(offset)
    times = [x[0] for x in fixes]
    errs, anchors = {}, 0

    def add(key, x):
        errs.setdefault(key, array.array("d")).append(x)

    for i in range(0, len(fixes), anchor_every):
        t_i, e_i, n_i = fixes[i]
        b = fc.nearest(times, t_i - fc.BACK_S, fc.BACK_TOL_S)
        if b is None or b >= i:
            continue
        t_b, e_b, n_b = fixes[b]
        if t_b - fc.GPS_LAG_S < tc0 + fl.SCORE_AFTER_S + grid.dt:
            continue
        de, dn = e_i - e_b, n_i - n_b
        k_b, k_i = grid.cell(t_b - fc.GPS_LAG_S), grid.cell(t_i - fc.GPS_LAG_S)
        if k_b < 0 or k_i >= grid.n or math.hypot(de, dn) < fc.MOVE_MIN_M:
            continue
        if sum(grid.v[k_b:k_i]) * grid.dt < fc.MOVE_MIN_M:
            continue
        live = {}
        for v in ("full", "running"):
            if heads[v][k_b] is not None and heads[v][k_i] is not None:
                q = bisect.bisect_right(fits[v][0], t_i) - 1
                if q >= 0:
                    live[v] = fits[v][1][q]
        if len(live) < 2:
            continue
        targets = []
        for h in fc.HORIZONS:
            j = fc.nearest(times, t_i + h, fc.TARGET_TOL_S)
            if j is None or j <= i:
                continue
            k_j = grid.cell(times[j] - fc.GPS_LAG_S)
            if k_j <= grid.n:
                targets.append((k_j, h, j))
        if not targets:
            continue
        targets.sort()
        anchors += 1
        psi0 = math.degrees(math.atan2(de, dn))
        k_ends = [x[0] for x in targets]
        bias = live["running"]

        def comp_of(hs, bv=bias):
            def comp(k):
                return hs[min(k, len(hs) - 1)] + bv
            return comp

        psi = {"course": lambda k, p=psi0: p}
        for s in SOURCES:
            comp = comp_of(src[s])
            psi[s] = comp
            psi["b2_" + s] = fb.blended(psi0, comp, k_i, grid.dt, HOLD_S, True)
        paths = {v: fc.run(grid, k_i, k_ends, f) for v, f in psi.items()}
        for idx, (k_j, h, j) in enumerate(targets):
            t_j, e_j, n_j = fixes[j]
            for name in NAMES:
                p = paths[name][idx]
                add(("miss", name, h), math.hypot(e_i + p[0] - e_j, n_i + p[1] - n_j))
    span = gps[-1][0] - gps[0][0]
    st.update(gps_span_s=round(span, 1), fresh_fixes=len(fixes), anchors=anchors)
    pool["rides"].append({"no": no, "errs": errs})
    pool["gps_s"] += span
    return st


# --- Summary and report --------------------------------------------------------

def _ratio(a, b):
    return fc._r(a / b) if b > 0 else None


def table(errs, names=NAMES):
    rows = []
    for h in fc.HORIZONS:
        if not errs.get(("miss", "course", h)):
            continue
        med = {v: statistics.median(errs[("miss", v, h)]) for v in names}
        for v in names:
            mv = errs[("miss", v, h)]
            rows.append({"variant": v, "horizon_s": h, "n": len(mv), "median_m": fc._r(med[v]),
                         "p90_m": fc._r(fc.pct(mv, 90)),
                         "over_course": _ratio(med[v], med["course"]),
                         "over_last": _ratio(med[v], med["last"]),
                         "over_interp": _ratio(med[v], med["interp"])})
    return rows


def boot(rides, h=10, reps=200, seed=1, names=NAMES):
    """95% intervals, resampling rides, of median-miss ratios h s ahead: each
    variant over course, last and interp, and each hold over its own heading."""
    if len(rides) < 2:
        return {}
    rng = random.Random(seed)
    ratios = {}
    for _ in range(reps):
        sample = [rides[rng.randrange(len(rides))] for _ in rides]
        med = {}
        for v in names:
            x = [y for r in sample for y in r["errs"].get(("miss", v, h), ())]
            if x:
                med[v] = statistics.median(x)
        if not med.get("course") or not med.get("last") or not med.get("interp"):
            continue
        for v in names[1:]:
            if v not in med:
                continue
            ratios.setdefault(v + "/course", []).append(med[v] / med["course"])
            if v != "last":
                ratios.setdefault(v + "/last", []).append(med[v] / med["last"])
            if v != "interp":
                ratios.setdefault(v + "/interp", []).append(med[v] / med["interp"])
        for s in SOURCES:
            if s not in ("last", "interp") and med.get(s) and "b2_" + s in med:
                ratios.setdefault("b2_%s/%s" % (s, s), []).append(med["b2_" + s] / med[s])
    return {k: [fc._r(fc.pct(x, 2.5)), fc._r(fc.pct(x, 97.5))] for k, x in ratios.items()}


def decide(rows, ci):
    """The rules stated in PREDICTION.md before the run."""
    find = fb.find
    i10, c10 = find(rows, "interp", 10), find(rows, "b2_interp", 10)
    if i10 is None or i10["over_course"] is None:
        return {"check": {"ok": False, "why": "no pairs at 10 s"}}
    chk = {"pairs_10s": i10["n"], "interp_over_course_10s": i10["over_course"],
           "b2_interp_over_interp_10s": c10["over_interp"] if c10 else None}
    out = {"check": chk}
    if i10["n"] < CHECK_MIN_PAIRS:
        chk.update(ok=False, why="fewer than %d pairs" % CHECK_MIN_PAIRS)
        return out
    b2 = chk["b2_interp_over_interp_10s"]
    if (abs(i10["over_course"] - B_RUNNING_OVER_COURSE) > REPRO_TOL + 1e-9 or b2 is None
            or abs(b2 - B_BLEND2_OVER_RUNNING) > REPRO_TOL + 1e-9):
        chk.update(ok=False, why="does not reproduce frodo-blend-b-v2")
        return out
    chk["ok"] = True
    l10, l30 = find(rows, "last", 10), find(rows, "last", 30)
    out["last_over_interp_10s"] = l10["over_interp"]
    out["last_over_interp_30s"] = l30["over_interp"] if l30 else None
    out["last_over_course_10s"] = l10["over_course"]
    gains = {}
    for v in BETWEEN:
        x10, x30 = find(rows, v, 10), find(rows, v, 30)
        band = ci.get(v + "/last")
        cost = (None if x30 is None or l30 is None or x30["over_course"] is None
                or l30["over_course"] is None else fc._r(x30["over_course"] - l30["over_course"]))
        passes = (x10 is not None and x10["over_last"] is not None
                  and x10["over_last"] <= ADOPT_MAX + 1e-9 and band is not None
                  and band[1] < 1.0 and cost is not None and cost <= COST_30S + 1e-9)
        gains[v] = {"over_last_10s": x10["over_last"] if x10 else None, "ci": band,
                    "cost_30s": cost, "passes": passes}
    out["between"] = gains
    passing = [v for v in BETWEEN if gains[v]["passes"]]
    out["build"] = min(passing, key=lambda v: gains[v]["over_last_10s"]) if passing else None
    h10, band = find(rows, "b2_last", 10), ci.get("b2_last/last")
    out["hold_over_last_10s"] = h10["over_last"] if h10 else None
    out["hold_ci_10s"] = band
    out["hold_stays"] = (h10 is not None and h10["over_last"] is not None
                         and h10["over_last"] <= HOLD_MAX + 1e-9
                         and band is not None and band[1] < 1.0)
    return out


def summarise(pool, final=True):
    errs = {}
    for r in pool["rides"]:
        for key, v in r["errs"].items():
            errs.setdefault(key, array.array("d")).extend(v)
    rows = table(errs)
    ci = boot(pool["rides"]) if final else {}
    return {"rides": len(pool["rides"]),
            "rides_with_pairs": sum(1 for r in pool["rides"] if r["errs"]),
            "gps_hours": fc._r(pool["gps_s"] / 3600.0, 2), "table": rows,
            "decision": decide(rows, ci), "ci": ci}


def conclusions(s):
    lines = []
    if not s["rides_with_pairs"]:
        return lines
    find = fb.find
    lines.append("%d rides (%.1f hours of GPS) were scored, %d of them with pairs; every "
                 "variant is scored on the same anchors."
                 % (s["rides"], s["gps_hours"] or 0.0, s["rides_with_pairs"]))
    for h in REPORT_H:
        c = find(s["table"], "course", h)
        if c:
            lines.append("%d s ahead (%d pairs): course %.2f m; " % (h, c["n"], c["median_m"])
                         + "; ".join("%s %.2f m (x%s of last, x%s of interp)"
                                     % (v, find(s["table"], v, h)["median_m"],
                                        find(s["table"], v, h)["over_last"],
                                        find(s["table"], v, h)["over_interp"])
                                     for v in NAMES[1:]) + ".")
    if s["ci"]:
        lines.append("10 s ahead, 95%% CI of median-miss ratios (rides resampled): %s." % s["ci"])
    d = s["decision"]
    c = d["check"]
    if not c["ok"]:
        lines.append("Check E1 (stated before the run) failed: %s (interp / course at 10 s = %s, "
                     "b2_interp / interp = %s, on %s pairs). Nothing is decided."
                     % (c["why"], c.get("interp_over_course_10s"),
                        c.get("b2_interp_over_interp_10s"), c.get("pairs_10s")))
        return lines
    lines.append("Check E1: %d pairs at 10 s; interp / course = %s and b2_interp / interp = %s "
                 "(frodo-blend-b-v2: %s and %s)." % (c["pairs_10s"], c["interp_over_course_10s"],
                                                    c["b2_interp_over_interp_10s"],
                                                    B_RUNNING_OVER_COURSE, B_BLEND2_OVER_RUNNING))
    lines.append("D1: the compass a live pilot reads (last) misses the fix 10 s later by x%s of "
                 "the interpolated compass, x%s at 30 s; last / course at 10 s = %s."
                 % (d["last_over_interp_10s"], d["last_over_interp_30s"],
                    d["last_over_course_10s"]))
    lines.append("D2 (stated before the run): between-read headings over last at 10 s, needing "
                 "<= %s with the CI's top below 1 and no more than %s worse at 30 s: %s; build: %s."
                 % (ADOPT_MAX, COST_30S, d["between"], d["build"]))
    lines.append("D3 (stated before the run): b2_last / last at 10 s = %s, CI %s; needs <= %s "
                 "with the CI's top below 1: %s." % (d["hold_over_last_10s"], d["hold_ci_10s"],
                                                     HOLD_MAX,
                                                     "met" if d["hold_stays"] else "not met"))
    return lines


def write_outputs(out_dir, parts, rides, pool, started, final=True):
    s = summarise(pool, final)
    lines = conclusions(s)
    skipped = {}
    for r in rides:
        if "skipped" in r:
            skipped[r["skipped"]] = skipped.get(r["skipped"], 0) + 1
    result = {"version": __version__, "data": "FrodoBots-2K, FrodoBots Lab, CC BY-SA 4.0",
              "done": final, "elapsed_s": round(time.monotonic() - started, 1), "parts": parts,
              "rides_sampled": len(rides),
              "rides_analysed": sum(1 for r in rides if "error" not in r and "skipped" not in r),
              "ride_errors": sum(1 for r in rides if "error" in r), "rides_skipped": skipped,
              "bytes_read": sum(p.get("bytes_read", 0) for p in parts),
              "settings": {"names": NAMES, "between": BETWEEN, "hold_s": HOLD_S,
                           "gyro_age_s": GYRO_AGE_S, "repro_tol": REPRO_TOL,
                           "check_min_pairs": CHECK_MIN_PAIRS, "adopt_max": ADOPT_MAX,
                           "cost_30s": COST_30S, "hold_max": HOLD_MAX,
                           "frodo_blend_b": fbb.__version__, "frodo_blend": fb.__version__,
                           "frodo_compass": fc.__version__,
                           "frodo_compass_live": fl.__version__},
              "conclusions": lines, "results": s}
    with open(os.path.join(out_dir, "summary.json"), "w") as f:
        json.dump(result, f, indent=1)
    with open(os.path.join(out_dir, "rides.jsonl"), "w") as f:
        for r in rides:
            f.write(json.dumps(r) + "\n")
    md = ["# The compass between its 1 Hz reads, as a live pilot sees it (FrodoBots-2K)", "",
          "Generated by frodo_between.py %s (earth-rover-pilot, MV2 of Munim, Inc.). Data: "
          "FrodoBots-2K by FrodoBots Lab, CC BY-SA 4.0." % __version__, "",
          "Rides sampled: %d, analysed: %d, errors: %d, skipped: %s. Downloaded: %.1f MB."
          % (result["rides_sampled"], result["rides_analysed"], result["ride_errors"], skipped,
             result["bytes_read"] / 1e6), "", "## Findings", ""]
    md += ["- " + line for line in lines] or ["- Nothing to report."]
    present = [h for h in fc.HORIZONS if fb.find(s["table"], "course", h)]
    if present:
        md += ["", "## Median miss (m), the same anchors for every variant", "",
               "| variant | " + " | ".join("%d s" % h for h in present) + " |",
               "|---|" + "---|" * len(present)]
        md += ["| %s | " % v + " | ".join("%.2f" % fb.find(s["table"], v, h)["median_m"]
                                          for h in present) + " |" for v in NAMES]
        md += ["| pairs | " + " | ".join(str(fb.find(s["table"], "course", h)["n"])
                                          for h in present) + " |"]
    with open(os.path.join(out_dir, "report.md"), "w") as f:
        f.write("\n".join(md) + "\n")
    return result


# --- Parts ---------------------------------------------------------------------

def process_part(rz, label, rides_per_part, pool, rides_out, imu_max_mb=30.0,
                 first_k=fbb.FIRST_K):
    rides = fm.group_rides(rz.entries(lambda name: name.lower().endswith(".csv")))
    usable = sorted(r for r, d in rides.items()
                    if "control_data" in d and "gps_data" in d and "imu_data" in d)
    chosen = fbb.held_out(usable, rides_per_part, first_k)
    info = {"part": label, "zip_bytes": rz.size, "rides_usable": len(usable),
            "rides_sampled": len(chosen)}
    for ride in chosen:
        d = rides[ride]
        no = len(rides_out)
        st = {"part": label, "no": no}
        m = fm.RIDE_RE.search(ride)
        if m:
            st["ride_id"], st["ride_time"] = m.group(1), m.group(2)
        try:
            if d["imu_data"].usize > imu_max_mb * (1 << 20):
                st["skipped"] = "IMU file of %d bytes" % d["imu_data"].usize
            else:
                ih, ir = fm.parse_csv(rz.read(d["imu_data"]))
                ch, cr = fm.parse_csv(rz.read(d["control_data"]))
                gh, gr = fm.parse_csv(rz.read(d["gps_data"]))
                st.update(analyse_ride(fm.load_control(ch, cr), fm.load_gps(gh, gr),
                                       fm.load_imu(ih, ir, "gyroscope"),
                                       fm.load_imu(ih, ir, "compass"), pool, no))
        except Exception as exc:
            st["error"] = "%s: %s" % (type(exc).__name__, exc)
        rides_out.append(st)
    info["bytes_read"] = rz.bytes_read
    return info


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--index-url", default=fm.INDEX_URL)
    ap.add_argument("--parts", default="all", help="comma-separated part numbers, or all")
    ap.add_argument("--rides-per-part", type=int, default=30)
    ap.add_argument("--first-k", type=int, default=fbb.FIRST_K)
    ap.add_argument("--budget-min", type=float, default=120.0)
    ap.add_argument("--max-cd-mb", type=float, default=800.0)
    ap.add_argument("--imu-max-mb", type=float, default=30.0)
    ap.add_argument("--out-dir", default="out")
    args = ap.parse_args(argv)
    os.makedirs(args.out_dir, exist_ok=True)
    started = time.monotonic()
    parts, rides, pool = [], [], new_pool()
    try:
        index = fm.read_index(args.index_url)
    except Exception as exc:
        parts.append({"error": "index: %s: %s" % (type(exc).__name__, exc)})
        index = []
    if args.parts != "all":
        keep = {int(p) for p in args.parts.split(",") if p.strip()}
        index = [(n, u) for n, u in index if n in keep]
    for n, url in index:
        label = "output_rides_%d" % n
        if time.monotonic() - started > args.budget_min * 60.0:
            parts.append({"part": label, "skipped": "time budget"})
            continue
        t0 = time.monotonic()
        try:
            rz = fm.RemoteZip(fm.http_size(url), lambda s, k, u=url: fm.http_range(u, s, k))
            if rz.cd_size > args.max_cd_mb * (1 << 20):
                parts.append({"part": label, "skipped": "central directory %d bytes" % rz.cd_size})
                continue
            info = process_part(rz, label, args.rides_per_part, pool, rides, args.imu_max_mb,
                                args.first_k)
        except Exception as exc:
            info = {"part": label, "error": "%s: %s" % (type(exc).__name__, exc)}
        info["seconds"] = round(time.monotonic() - t0, 1)
        parts.append(info)
        print("%s: %s" % (label, info), flush=True)
        write_outputs(args.out_dir, parts, rides, pool, started, final=False)
    result = write_outputs(args.out_dir, parts, rides, pool, started, final=True)
    print("\n".join(result["conclusions"]) or "no conclusions", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
