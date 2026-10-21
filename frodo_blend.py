#!/usr/bin/env python3
"""frodo_blend: when should an Earth Rover stop trusting its last GPS course?

frodo-compass-live-v1 found that on real FrodoBots-2K rides, wheels along the
live-calibrated compass heading (the running fit, frame yz+, learned bias)
missed the GPS fix 10 s later by 0.926 of what wheels along the last GPS
course missed, and by 0.687 at 30 s. Right after a fix the course is fresh and
has no mount bias, so this study holds the course for the first B seconds
after the anchor fix and switches to the compass after that:

- course: the last GPS course throughout (baseline, as in live-v1).
- running: live-v1's running compass fit plus its learned bias, unchanged.
- blend2, blend5, blend10: the course for B = 2, 5, 10 s, then the running
  heading shifted onto the course at the switch, the shift fading linearly to
  nothing over the next B seconds (no jump in heading at the switch).
- hard5: the course for 5 s, then the running heading with no shift.

Every variant is scored on the same anchors (those where live-v1 scores the
running fit), so course and running reproduce live-v1's running rows and check
that the copied code is unchanged. Nothing used comes from after the anchor.

    python frodo_blend.py --out-dir out --rides-per-part 30

Needs frodo_compass.py, frodo_compass_live.py and frodo_motion.py next to it.
Standard library only. By MV2 of Munim, Inc.; written with AI agents. Apache-2.0.
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

import frodo_compass as fc
import frodo_compass_live as fl
import frodo_motion as fm

__version__ = "0.1.0"

BLEND_S = (2, 5, 10)     # course held this long, then the compass with a fading shift
HARD_S = 5               # course held this long, then the compass with no shift
VARIANTS = ("course", "running") + tuple("blend%d" % b for b in BLEND_S) + ("hard%d" % HARD_S,)
REPORT_H = (5, 10, 30)
LIVE_V1_10S = 0.926      # running / course at 10 s in frodo-compass-live-v1
CHECK_TOL = 0.02         # E2: running / course at 10 s must land this close to live-v1
CHECK_MIN_PAIRS = 2000   # and on at least this many pairs at 10 s
ADOPT_MARGIN = 0.03      # D1: a blend beats running at 10 s by at least this
COST_30S = 0.02          # and is not worse than running at 30 s by more than this
SAME_SWITCH = 0.01       # D2: hard5 this close to blend5 at 10 s: ship the hard switch


# --- The blend --------------------------------------------------------------

def blended(psi0, comp, k_i, dt, b_s, decay=True):
    """Heading (deg) for cell k: the GPS course psi0 in the cells that start less
    than b_s seconds after boundary k_i, then comp(k). With decay, comp is first
    shifted onto psi0 at the switch and the shift fades linearly to nothing
    over the next b_s seconds."""
    k_s = k_i + int(math.ceil(b_s / dt - 1e-9))
    off = fc.wrap180(psi0 - comp(k_s)) if decay else 0.0

    def psi(k):
        if k < k_s:
            return psi0
        f = max(0.0, 1.0 - (k - k_s) * dt / b_s) if decay else 0.0
        return (comp(k) + f * off) % 360.0
    return psi


# --- One ride --------------------------------------------------------------

def new_pool():
    return {"rides": [], "gps_s": 0.0}


def analyse_ride(control, gps, gyro, compass, pool, no=0, anchor_every=3):
    """Stats for ride number `no`; its misses go to pool["rides"] as
    ("miss", v, h), every variant on the same anchors."""
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

        def comp(k, bv=bias):
            return hr[min(k, len(hr) - 1)] + bv

        psi = {"course": lambda k: psi0, "running": comp}
        for bs in BLEND_S:
            psi["blend%d" % bs] = blended(psi0, comp, k_i, grid.dt, bs)
        psi["hard%d" % HARD_S] = blended(psi0, comp, k_i, grid.dt, HARD_S, decay=False)
        paths = {v: fc.run(grid, k_i, k_ends, f) for v, f in psi.items()}
        for idx, (k_j, h, j) in enumerate(targets):
            t_j, e_j, n_j = fixes[j]
            for v in VARIANTS:
                p = paths[v][idx]
                add(("miss", v, h), math.hypot(e_i + p[0] - e_j, n_i + p[1] - n_j))
    span = gps[-1][0] - gps[0][0]
    st.update(gps_span_s=round(span, 1), fresh_fixes=len(fixes), anchors=anchors)
    pool["rides"].append({"no": no, "errs": errs})
    pool["gps_s"] += span
    return st


# --- Summary and report ----------------------------------------------------

def table(errs):
    rows = []
    for h in fc.HORIZONS:
        mc = errs.get(("miss", "course", h))
        if not mc:
            continue
        cm = statistics.median(mc)
        rm = statistics.median(errs[("miss", "running", h)])
        for v in VARIANTS:
            mv = errs[("miss", v, h)]
            m = statistics.median(mv)
            rows.append({"variant": v, "horizon_s": h, "n": len(mv), "median_m": fc._r(m),
                         "p90_m": fc._r(fc.pct(mv, 90)),
                         "over_course": fc._r(m / cm) if cm > 0 else None,
                         "over_running": fc._r(m / rm) if rm > 0 else None,
                         "beats_course": fc._r(sum(1 for a, c in zip(mv, mc) if a < c)
                                               / len(mv))})
    return rows


def find(rows, v, h):
    for r in rows:
        if r["variant"] == v and r["horizon_s"] == h:
            return r
    return None


def boot(rides, h=10, reps=200, seed=1):
    """95% intervals, resampling rides, of each variant's median miss h s ahead
    over the course predictor's and over the running fit's."""
    if len(rides) < 2:
        return {}
    rng = random.Random(seed)
    ratios = {}
    for _ in range(reps):
        sample = [rides[rng.randrange(len(rides))] for _ in rides]
        med = {}
        for v in VARIANTS:
            x = [y for r in sample for y in r["errs"].get(("miss", v, h), ())]
            if x:
                med[v] = statistics.median(x)
        if not med.get("course") or not med.get("running"):
            continue
        for v in VARIANTS[1:]:
            ratios.setdefault(v + "/course", []).append(med[v] / med["course"])
            if v != "running":
                ratios.setdefault(v + "/running", []).append(med[v] / med["running"])
    return {k: [fc._r(fc.pct(x, 2.5)), fc._r(fc.pct(x, 97.5))] for k, x in ratios.items()}


def decide(rows):
    """The rules stated in PREDICTION.md before the run."""
    r = find(rows, "running", 10)
    if r is None or r["over_course"] is None:
        return {"check": {"ok": False, "why": "no running pairs at 10 s"}}
    ok = r["n"] >= CHECK_MIN_PAIRS and abs(r["over_course"] - LIVE_V1_10S) <= CHECK_TOL + 1e-9
    out = {"check": {"ok": ok, "running_over_course_10s": r["over_course"], "pairs_10s": r["n"]}}
    if not ok:
        out["check"]["why"] = ("fewer than %d pairs" % CHECK_MIN_PAIRS
                               if r["n"] < CHECK_MIN_PAIRS else "does not reproduce live-v1")
        return out
    blends = [find(rows, "blend%d" % b, 10) for b in BLEND_S]
    best = min((x for x in blends if x and x["over_course"] is not None),
               key=lambda x: x["over_course"], default=None)
    if best is None:
        out["default"] = "running"
        return out
    out["best_blend"] = best["variant"]
    out["best_over_course_10s"] = best["over_course"]
    r30, b30 = find(rows, "running", 30), find(rows, best["variant"], 30)
    cost = (None if r30 is None or b30 is None or r30["over_course"] is None
            or b30["over_course"] is None else fc._r(b30["over_course"] - r30["over_course"]))
    out["cost_30s"] = cost
    gain = best["over_course"] <= r["over_course"] - ADOPT_MARGIN + 1e-9
    out["default"] = (best["variant"] if gain and cost is not None and cost <= COST_30S + 1e-9
                      else "running")
    h5, b5 = find(rows, "hard%d" % HARD_S, 10), find(rows, "blend%d" % HARD_S, 10)
    if h5 and b5 and h5["over_course"] is not None and b5["over_course"] is not None:
        out["hard_minus_blend_10s"] = fc._r(h5["over_course"] - b5["over_course"])
        out["switch"] = ("hard" if abs(out["hard_minus_blend_10s"]) <= SAME_SWITCH + 1e-9
                         else "fading shift")
    return out


def summarise(pool, final=True):
    errs = {}
    for r in pool["rides"]:
        for key, v in r["errs"].items():
            errs.setdefault(key, array.array("d")).extend(v)
    rows = table(errs)
    return {"rides": len(pool["rides"]),
            "rides_with_pairs": sum(1 for r in pool["rides"] if r["errs"]),
            "gps_hours": fc._r(pool["gps_s"] / 3600.0, 2), "table": rows,
            "decision": decide(rows), "ci": boot(pool["rides"]) if final else {}}


def conclusions(s):
    lines = []
    if not s["rides_with_pairs"]:
        return lines
    lines.append("%d rides (%.1f hours of GPS) were scored, %d of them with pairs; every variant "
                 "is scored on the same anchors." % (s["rides"], s["gps_hours"] or 0.0,
                                                     s["rides_with_pairs"]))
    for h in REPORT_H:
        c = find(s["table"], "course", h)
        if c:
            lines.append("%d s ahead (%d pairs): course %.2f m; " % (h, c["n"], c["median_m"])
                         + "; ".join("%s %.2f m (x%s of course, x%s of running)"
                                     % (v, find(s["table"], v, h)["median_m"],
                                        find(s["table"], v, h)["over_course"],
                                        find(s["table"], v, h)["over_running"])
                                     for v in VARIANTS[1:]) + ".")
    if s["ci"]:
        lines.append("10 s ahead, 95%% CI of median-miss ratios (rides resampled): %s." % s["ci"])
    d = s["decision"]
    c = d["check"]
    if not c["ok"]:
        lines.append("Check E2 (stated before the run) failed: %s (running / course at 10 s = %s "
                     "on %s pairs; live-v1 had %s). No default changes."
                     % (c["why"], c.get("running_over_course_10s"), c.get("pairs_10s"),
                        LIVE_V1_10S))
        return lines
    lines.append("Check E2: running / course at 10 s = %s on %d pairs reproduces live-v1 (%s)."
                 % (c["running_over_course_10s"], c["pairs_10s"], LIVE_V1_10S))
    if "best_blend" in d:
        lines.append("Rule D1 (stated before the run): best blend at 10 s is %s (x%s of course), "
                     "cost at 30 s vs running %s, so the default is %s."
                     % (d["best_blend"], d["best_over_course_10s"], d["cost_30s"], d["default"]))
    if "switch" in d:
        lines.append("Rule D2 (stated before the run): hard%d minus blend%d at 10 s = %s, so the "
                     "switch to ship is the %s." % (HARD_S, HARD_S, d["hard_minus_blend_10s"],
                                                   d["switch"]))
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
              "settings": {"frame": fl.FRAME, "blend_s": BLEND_S, "hard_s": HARD_S,
                           "refit_s": fl.REFIT_S, "score_after_s": fl.SCORE_AFTER_S,
                           "live_v1_10s": LIVE_V1_10S, "check_tol": CHECK_TOL,
                           "check_min_pairs": CHECK_MIN_PAIRS, "adopt_margin": ADOPT_MARGIN,
                           "cost_30s": COST_30S, "same_switch": SAME_SWITCH,
                           "frodo_compass": fc.__version__, "frodo_compass_live": fl.__version__},
              "conclusions": lines, "results": s}
    with open(os.path.join(out_dir, "summary.json"), "w") as f:
        json.dump(result, f, indent=1)
    with open(os.path.join(out_dir, "rides.jsonl"), "w") as f:
        for r in rides:
            f.write(json.dumps(r) + "\n")
    md = ["# When to stop trusting the last GPS course, measured from FrodoBots-2K", "",
          "Generated by frodo_blend.py %s (earth-rover-pilot, MV2 of Munim, Inc.). Data: "
          "FrodoBots-2K by FrodoBots Lab, CC BY-SA 4.0." % __version__, "",
          "Rides sampled: %d, analysed: %d, errors: %d, skipped: %s. Downloaded: %.1f MB."
          % (result["rides_sampled"], result["rides_analysed"], result["ride_errors"], skipped,
             result["bytes_read"] / 1e6), "", "## Findings", ""]
    md += ["- " + line for line in lines] or ["- Nothing to report."]
    present = [h for h in fc.HORIZONS if find(s["table"], "course", h)]
    if present:
        md += ["", "## Median miss (m), the same anchors for every variant", "",
               "| variant | " + " | ".join("%d s" % h for h in present) + " |",
               "|---|" + "---|" * len(present)]
        md += ["| %s | " % v + " | ".join("%.2f" % find(s["table"], v, h)["median_m"]
                                          for h in present) + " |" for v in VARIANTS]
        md += ["| pairs | " + " | ".join(str(find(s["table"], "course", h)["n"])
                                          for h in present) + " |"]
    with open(os.path.join(out_dir, "report.md"), "w") as f:
        f.write("\n".join(md) + "\n")
    return result


# --- Parts -----------------------------------------------------------------

def process_part(rz, label, rides_per_part, pool, rides_out, imu_max_mb=30.0):
    rides = fm.group_rides(rz.entries(lambda name: name.lower().endswith(".csv")))
    usable = sorted(r for r, d in rides.items()
                    if "control_data" in d and "gps_data" in d and "imu_data" in d)
    chosen = fm.pick_evenly(usable, rides_per_part)
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
            info = process_part(rz, label, args.rides_per_part, pool, rides, args.imu_max_mb)
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
