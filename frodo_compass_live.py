#!/usr/bin/env python3
"""frodo_compass_live: can an Earth Rover calibrate its compass while it drives?

frodo-compass-v1 found that on real FrodoBots-2K rides, wheels along the
compass heading plus a learned bias missed the GPS fix 10 s later by 0.835 of
what wheels along the last GPS course missed. But its hard-iron centre was
fitted to each ride's whole magnetometer record, which a pilot only has once
the ride is over. This study calibrates the ways a live pilot could, in frame
yz+ (chosen in v1 on 138 of 140 rides):

- raw: no hard-iron correction (centre 0, 0); only the learned bias.
- first1, first2, first5: the centre fitted to the first 1, 2 or 5 minutes of
  compass samples, once; no heading before then.
- running: refitted every minute to all samples so far, keeping the last
  centre that passed the coverage and circle checks; no heading before one did.
- full: the whole ride, as in v1 (not available live; the reference).

Each variant learns its own bias from its own headings (frodo_compass's
replay of the pilot's HeadingEstimator), so nothing it uses comes from after
the anchor, except for full. Anchors are the ones frodo_compass scores, at
least SCORE_AFTER_S after the first compass sample, on rides whose whole
record calibrates; each variant is paired with the last-GPS-course predictor
on the anchors where it has a heading, and all are compared on the anchors
where every variant has one.

    python frodo_compass_live.py --out-dir out --rides-per-part 30

Needs frodo_compass.py and frodo_motion.py next to it. Standard library only.
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

import frodo_compass as fc
import frodo_motion as fm

__version__ = "0.1.0"

FRAME = "yz+"            # chosen in frodo-compass-v1 on 138 of 140 rides
A, B, S = fc.FRAMES[FRAME]
WINDOWS_MIN = (1, 2, 5)  # fixed calibration windows that are scored
CAL_MIN = (1, 2, 5, 10)  # windows whose calibration success is counted
REFIT_S = 60.0           # the running fit is redone this often
SCORE_AFTER_S = 300.0    # anchors whose back fix is this long after the first compass sample
VARIANTS = ("raw", "first1", "first2", "first5", "running", "full")
REPORT_H = (5, 10, 30)
SAME_RATIO = 1.10        # a window within this of full at 10 s calibrates as well as full


# --- Live calibration ------------------------------------------------------

def before(samples, t):
    """The samples taken before time t."""
    return [s for s in samples if s[0] < t]


def heading_of(sample, centre):
    """FRAME's heading (deg, [0, 360)) of one sample about a hard-iron centre."""
    ca, cb = centre
    return math.degrees(math.atan2(S * (sample[1 + B] - cb), sample[1 + A] - ca)) % 360.0


def cell_time(grid, k):
    return grid.t0 + (k + 0.5) * grid.dt


def masked(heads, grid, t_from):
    """heads with None in every cell whose centre is before t_from."""
    return [None if cell_time(grid, k) < t_from else h for k, h in enumerate(heads)]


def running_centres(samples, t_end):
    """[(t, centre or None)] at the first sample + 1, 2, ... minutes before t_end:
    the last centre that passed the checks, fitted to all samples before t."""
    out, last = [], None
    t = samples[0][0] + REFIT_S
    while t < t_end:
        info, centre = fc.calibrate(before(samples, t), A, B)
        if info["ok"]:
            last = centre
        out.append((t, last))
        t += REFIT_S
    return out


def running_headings(samples, where, grid, cents):
    """Heading per cell about the centre the running fit had at that cell, or None."""
    ts = [c[0] for c in cents]
    out = []
    for k, wj in enumerate(where):
        i = bisect.bisect_right(ts, cell_time(grid, k)) - 1
        centre = cents[i][1] if i >= 0 else None
        if wj is None or centre is None:
            out.append(None)
        else:
            j0, j1, w = wj
            h0, h1 = heading_of(samples[j0], centre), heading_of(samples[j1], centre)
            out.append((h0 + w * fc.wrap180(h1 - h0)) % 360.0)
    return out


def calibration(samples, full_info, full_centre):
    """Per window of CAL_MIN minutes: whether its fit passes the checks and how far
    its centre lies from the whole ride's, over the whole ride's radius."""
    tc0, span = samples[0][0], samples[-1][0] - samples[0][0]
    out = {}
    for m in CAL_MIN:
        if span < m * 60.0:
            out[str(m)] = {"short": True}
            continue
        info, centre = fc.calibrate(before(samples, tc0 + m * 60.0), A, B)
        row = {"ok": info["ok"], "cover": info.get("cover"), "rms": info.get("rms")}
        if not info["ok"]:
            row["why"] = info.get("why")
        if centre is not None and full_centre is not None and full_info.get("radius"):
            row["centre_err"] = fc._r(math.hypot(centre[0] - full_centre[0],
                                                 centre[1] - full_centre[1]) / full_info["radius"])
        out[str(m)] = row
    return out


# --- One ride --------------------------------------------------------------

def new_pool():
    return {"rides": [], "cal": [], "gps_s": 0.0}


def analyse_ride(control, gps, gyro, compass, pool, no=0, anchor_every=3):
    """Stats for ride number `no`. Its calibration record goes to pool["cal"];
    its misses go to pool["rides"]: ("all", v, h) and ("course", v, h) line up
    on the anchors where variant v has a heading, ("common", v, h) and
    ("common_course", h) on the anchors where every variant has one, and
    ("full_at", v, h) holds full's misses on v's anchors, and ("hdg", v) and
    ("hdg_common", v) hold heading errors (deg)."""
    st = {"control_rows": len(control), "gps_rows": len(gps),
          "compass_samples": len(compass or [])}
    if len(control) < 50 or len(gps) < 20:
        st["skipped"] = "too little data"
        return st
    if not compass or len(compass) < 20:
        st["skipped"] = "no compass"
        return st
    tc0 = compass[0][0]
    full_info, full_centre = fc.calibrate(compass, A, B)
    st["full"] = full_info
    st["windows"] = calibration(compass, full_info, full_centre if full_info["ok"] else None)
    grid = fc.Grid(control, gyro)
    where = fc.compass_cells(grid, [c[0] for c in compass])
    cents = running_centres(compass, cell_time(grid, grid.n - 1))
    first_ok = next(((t - tc0) / 60.0 for t, c in cents if c is not None), None)
    st["running_first_ok_min"] = fc._r(first_ok, 2)
    pool["cal"].append({"no": no, "full_ok": full_info["ok"], "windows": st["windows"],
                        "running_first_ok_min": st["running_first_ok_min"]})
    if not full_info["ok"]:
        st["skipped"] = "whole ride does not calibrate"
        return st
    heads = {"raw": fc.frame_headings(compass, where, A, B, S, (0.0, 0.0)),
             "running": running_headings(compass, where, grid, cents),
             "full": fc.frame_headings(compass, where, A, B, S, full_centre)}
    for m in WINDOWS_MIN:
        info, centre = fc.calibrate(before(compass, tc0 + m * 60.0), A, B)
        if info["ok"]:
            heads["first%d" % m] = masked(fc.frame_headings(compass, where, A, B, S, centre),
                                          grid, tc0 + m * 60.0)
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
    full = {v: fc.filled(h) for v, h in heads.items() if v in fits}
    times = [x[0] for x in fixes]
    errs, anchors, common_anchors = {}, 0, 0

    def add(key, x):
        errs.setdefault(key, array.array("d")).append(x)

    for i in range(0, len(fixes), anchor_every):
        t_i, e_i, n_i = fixes[i]
        b = fc.nearest(times, t_i - fc.BACK_S, fc.BACK_TOL_S)
        if b is None or b >= i:
            continue
        t_b, e_b, n_b = fixes[b]
        if t_b - fc.GPS_LAG_S < tc0 + SCORE_AFTER_S + grid.dt:
            continue
        de, dn = e_i - e_b, n_i - n_b
        k_b, k_i = grid.cell(t_b - fc.GPS_LAG_S), grid.cell(t_i - fc.GPS_LAG_S)
        if k_b < 0 or k_i >= grid.n or math.hypot(de, dn) < fc.MOVE_MIN_M:
            continue
        if sum(grid.v[k_b:k_i]) * grid.dt < fc.MOVE_MIN_M:
            continue
        live = {}
        for v in VARIANTS:
            if v in fits and heads[v][k_b] is not None and heads[v][k_i] is not None:
                q = bisect.bisect_right(fits[v][0], t_i) - 1
                if q >= 0:
                    live[v] = fits[v][1][q]
        if "full" not in live:
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
        common = len(live) == len(VARIANTS)
        common_anchors += common
        psi0 = math.degrees(math.atan2(de, dn))
        k_ends = [x[0] for x in targets]
        k_mid = (k_b + k_i) // 2
        course = fc.run(grid, k_i, k_ends, lambda k: psi0)
        preds = {v: fc.run(grid, k_i, k_ends, lambda k, hf=full[v], bv=bias: hf[k] + bv)
                 for v, bias in live.items()}
        if math.hypot(de, dn) >= fc.HDG_MIN_M:
            for v, bias in live.items():
                x = abs(fc.wrap180(full[v][k_mid] + bias - psi0))
                add(("hdg", v), x)
                if common:
                    add(("hdg_common", v), x)
        for idx, (k_j, h, j) in enumerate(targets):
            t_j, e_j, n_j = fixes[j]
            mc = math.hypot(e_i + course[idx][0] - e_j, n_i + course[idx][1] - n_j)
            pf = preds["full"][idx]
            mf = math.hypot(e_i + pf[0] - e_j, n_i + pf[1] - n_j)
            if common:
                add(("common_course", h), mc)
            for v, ps in preds.items():
                mv = math.hypot(e_i + ps[idx][0] - e_j, n_i + ps[idx][1] - n_j)
                add(("all", v, h), mv)
                add(("course", v, h), mc)
                add(("full_at", v, h), mf)
                if common:
                    add(("common", v, h), mv)
    span = gps[-1][0] - gps[0][0]
    st.update(gps_span_s=round(span, 1), fresh_fixes=len(fixes), anchors=anchors,
              common_anchors=common_anchors, variants=sorted(heads))
    pool["rides"].append({"no": no, "errs": errs})
    pool["gps_s"] += span
    return st


# --- Summary and report ----------------------------------------------------

def _share(a, n):
    return fc._r(a / n) if n else None


def _pc(x):
    return "n/a" if x is None else "%.0f%%" % (100.0 * x)


def cal_table(cal):
    rows = {}
    for m in CAL_MIN:
        key = str(m)
        long_ = [c for c in cal if not c["windows"][key].get("short")]
        good = [c for c in long_ if c["full_ok"]]
        errs = [c["windows"][key]["centre_err"] for c in good
                if c["windows"][key]["ok"] and c["windows"][key].get("centre_err") is not None]
        rows[key] = {"rides": len(long_),
                     "ok": _share(sum(1 for c in long_ if c["windows"][key]["ok"]), len(long_)),
                     "full_ok_rides": len(good),
                     "ok_when_full_ok": _share(sum(1 for c in good if c["windows"][key]["ok"]),
                                               len(good)),
                     "centre_err_median": fc._r(statistics.median(errs)) if errs else None,
                     "centre_err_p90": fc._r(fc.pct(errs, 90))}
    good = [c for c in cal if c["full_ok"]]
    first = [c["running_first_ok_min"] for c in good if c["running_first_ok_min"] is not None]
    rows["running"] = {"full_ok_rides": len(good), "ever_ok": len(first),
                       "first_ok_min_median": fc._r(statistics.median(first), 1) if first else None,
                       "first_ok_min_p75": fc._r(fc.pct(first, 75), 1),
                       "by_min": {str(m): _share(sum(1 for x in first if x <= m + 1e-6), len(good))
                                  for m in CAL_MIN}}
    return rows


def pooled(rides):
    out = {}
    for r in rides:
        for key, v in r["errs"].items():
            out.setdefault(key, array.array("d")).extend(v)
    return out


def pair(v, c):
    mv, mc = statistics.median(v), statistics.median(c)
    return {"n": len(v), "median_m": fc._r(mv), "p90_m": fc._r(fc.pct(v, 90)),
            "course_median_m": fc._r(mc), "over_course": fc._r(mv / mc) if mc > 0 else None,
            "beats_course": fc._r(sum(1 for a, b in zip(v, c) if a < b) / len(v))}


def miss_rows(errs):
    rows = []
    for h in fc.HORIZONS:
        for v in VARIANTS:
            mv, mc = errs.get(("all", v, h)), errs.get(("course", v, h))
            if mv:
                row = dict(set="all", variant=v, horizon_s=h, **pair(mv, mc))
                fa = statistics.median(errs[("full_at", v, h)])
                row["over_full"] = fc._r(statistics.median(mv) / fa) if fa > 0 else None
                rows.append(row)
        cc = errs.get(("common_course", h))
        if not cc:
            continue
        full = errs.get(("common", "full", h))
        fm_ = statistics.median(full) if full else 0.0
        for v in VARIANTS:
            mv = errs.get(("common", v, h))
            if mv:
                row = dict(set="common", variant=v, horizon_s=h, **pair(mv, cc))
                row["over_full"] = fc._r(statistics.median(mv) / fm_) if fm_ > 0 else None
                rows.append(row)
    return rows


def find(rows, which, v, h):
    for r in rows:
        if r["set"] == which and r["variant"] == v and r["horizon_s"] == h:
            return r
    return None


def hdg_rows(errs):
    out = {}
    for which in ("hdg", "hdg_common"):
        for v in VARIANTS:
            x = errs.get((which, v))
            if x:
                out["%s|%s" % (which, v)] = {"n": len(x),
                                             "median_deg": fc._r(statistics.median(x), 1),
                                             "p90_deg": fc._r(fc.pct(x, 90), 1)}
    return out


def boot(rides, h=10, reps=200, seed=1):
    """95% intervals, resampling rides, of each variant's median miss h s ahead over
    the course predictor's and over full's on the common anchors, and of the
    running variant's over the course predictor's on all its anchors."""
    if len(rides) < 2:
        return {}
    rng = random.Random(seed)
    ratios = {}
    for _ in range(reps):
        sample = [rides[rng.randrange(len(rides))] for _ in rides]
        rv = [x for r in sample for x in r["errs"].get(("all", "running", h), ())]
        rc = [x for r in sample for x in r["errs"].get(("course", "running", h), ())]
        if rv and statistics.median(rc) > 0:
            ratios.setdefault("running/course (all)", []).append(
                statistics.median(rv) / statistics.median(rc))
        for m in WINDOWS_MIN:
            v = "first%d" % m
            wv = [x for r in sample for x in r["errs"].get(("all", v, h), ())]
            wf = [x for r in sample for x in r["errs"].get(("full_at", v, h), ())]
            if wv and statistics.median(wf) > 0:
                ratios.setdefault(v + "/full (own anchors)", []).append(
                    statistics.median(wv) / statistics.median(wf))
        cc = [x for r in sample for x in r["errs"].get(("common_course", h), ())]
        if not cc or statistics.median(cc) <= 0:
            continue
        cm = statistics.median(cc)
        fv = [x for r in sample for x in r["errs"].get(("common", "full", h), ())]
        fmed = statistics.median(fv) if fv else 0.0
        for v in VARIANTS:
            vv = [x for r in sample for x in r["errs"].get(("common", v, h), ())]
            if not vv:
                continue
            mv = statistics.median(vv)
            ratios.setdefault(v + "/course", []).append(mv / cm)
            if v != "full" and fmed > 0:
                ratios.setdefault(v + "/full", []).append(mv / fmed)
    return {k: [fc._r(fc.pct(x, 2.5)), fc._r(fc.pct(x, 97.5))] for k, x in ratios.items()}


def decide(rows):
    """The rules stated in PREDICTION.md before the run."""
    out = {}
    r = find(rows, "all", "running", 10)
    if r and r["over_course"] is not None:
        out["running_over_course_10s"] = r["over_course"]
        out["live_compass"] = ("keeps the gain" if r["over_course"] <= 1.0 else
                               "loses to the course" if r["over_course"] > fc.SWITCH_RATIO
                               else "no clear gain")
    out["shortest_window_min"] = None
    for m in WINDOWS_MIN:
        r = find(rows, "all", "first%d" % m, 10)
        if r and r["over_full"] is not None and r["over_full"] <= SAME_RATIO:
            out["shortest_window_min"] = m
            break
    return out


def summarise(pool, final=True):
    errs = pooled(pool["rides"])
    rows = miss_rows(errs)
    return {"cal_rides": len(pool["cal"]), "rides": len(pool["rides"]),
            "rides_with_common": sum(1 for r in pool["rides"]
                                     if r["errs"].get(("common_course", 10))),
            "gps_hours": fc._r(pool["gps_s"] / 3600.0, 2),
            "calibration": cal_table(pool["cal"]), "table": rows, "headings": hdg_rows(errs),
            "decision": decide(rows), "ci": boot(pool["rides"]) if final else {}}


def _row(r):
    return "n/a" if r is None else "%.2f m" % r["median_m"]


def conclusions(s):
    lines = []
    if not s["cal_rides"]:
        return lines
    c = s["calibration"]
    lines.append("%d rides had a magnetometer record; in frame %s the whole record calibrates on "
                 "%d; %d rides (%.1f hours of GPS) were scored, %d of them with anchors where "
                 "every variant has a heading." % (s["cal_rides"], FRAME,
                                                  c["running"]["full_ok_rides"], s["rides"],
                                                  s["gps_hours"] or 0.0, s["rides_with_common"]))
    for m in CAL_MIN:
        r = c[str(m)]
        lines.append("First %d min: calibrates on %s of the %d rides that long (%s of the %d whose "
                     "whole record calibrates); its centre lies a median %s of the radius from the "
                     "whole-record centre (90th percentile %s)."
                     % (m, _pc(r["ok"]), r["rides"], _pc(r["ok_when_full_ok"]), r["full_ok_rides"],
                        r["centre_err_median"], r["centre_err_p90"]))
    r = c["running"]
    lines.append("Running fit: of the %d rides whose whole record calibrates, it has a centre by "
                 "minute 1, 2, 5, 10 on %s; first centre at a median minute %s (75th percentile %s)."
                 % (r["full_ok_rides"], ", ".join(_pc(r["by_min"][str(m)]) for m in CAL_MIN),
                    r["first_ok_min_median"], r["first_ok_min_p75"]))
    rows = s["table"]
    for h in REPORT_H:
        parts = []
        for v in VARIANTS:
            x = find(rows, "all", v, h)
            if x:
                parts.append("%s %.2f m vs course %.2f m (x%s; x%s of full; %d pairs)"
                             % (v, x["median_m"], x["course_median_m"], x["over_course"],
                                x["over_full"], x["n"]))
        if parts:
            lines.append("%d s ahead, each variant on the anchors where it has a heading: %s."
                         % (h, "; ".join(parts)))
        cc = find(rows, "common", "full", h)
        if cc:
            lines.append("%d s ahead, the %d pairs where every variant has a heading: course %.2f m; "
                         % (h, cc["n"], cc["course_median_m"]) + "; ".join(
                             "%s %s (x%s of course, x%s of full)"
                             % (v, _row(find(rows, "common", v, h)),
                                (find(rows, "common", v, h) or {}).get("over_course"),
                                (find(rows, "common", v, h) or {}).get("over_full"))
                             for v in VARIANTS) + ".")
    hd = s["headings"]
    for which, label in (("hdg", "where each variant has a heading"),
                         ("hdg_common", "where every variant has one")):
        got = ["%s %s / %s (%d)" % (v, hd[which + "|" + v]["median_deg"],
                                    hd[which + "|" + v]["p90_deg"], hd[which + "|" + v]["n"])
               for v in VARIANTS if which + "|" + v in hd]
        if got:
            lines.append("Heading error at the anchor, deg (median / 90th percentile (n)), anchors "
                         "%s: %s." % (label, ", ".join(got)))
    if s["ci"]:
        lines.append("10 s ahead, 95%% CI of median-miss ratios (rides resampled): %s." % s["ci"])
    d = s["decision"]
    if "live_compass" in d:
        lines.append("Rule D1 (stated before the run): running fit over course at 10 s = %s, so "
                     "the live compass %s." % (d["running_over_course_10s"], d["live_compass"]))
    lines.append("Rule D2 (stated before the run): shortest fixed window within x%.2f of the whole "
                 "record at 10 s, on the anchors where it has a heading: %s." % (
                     SAME_RATIO, "none" if d["shortest_window_min"] is None
                     else "%d min" % d["shortest_window_min"]))
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
              "settings": {"frame": FRAME, "windows_min": WINDOWS_MIN, "cal_min": CAL_MIN,
                           "refit_s": REFIT_S, "score_after_s": SCORE_AFTER_S,
                           "same_ratio": SAME_RATIO, "switch_ratio": fc.SWITCH_RATIO,
                           "frodo_compass": fc.__version__},
              "conclusions": lines, "results": s}
    with open(os.path.join(out_dir, "summary.json"), "w") as f:
        json.dump(result, f, indent=1)
    with open(os.path.join(out_dir, "rides.jsonl"), "w") as f:
        for r in rides:
            f.write(json.dumps(r) + "\n")
    md = ["# Calibrating an Earth Rover's compass while it drives, measured from FrodoBots-2K", "",
          "Generated by frodo_compass_live.py %s (earth-rover-pilot, MV2 of Munim, Inc.). Data: "
          "FrodoBots-2K by FrodoBots Lab, CC BY-SA 4.0." % __version__, "",
          "Rides sampled: %d, analysed: %d, errors: %d, skipped: %s. Downloaded: %.1f MB."
          % (result["rides_sampled"], result["rides_analysed"], result["ride_errors"], skipped,
             result["bytes_read"] / 1e6), "", "## Findings", ""]
    md += ["- " + line for line in lines] or ["- Nothing to report."]
    present = [h for h in fc.HORIZONS if find(s["table"], "common", "full", h)]
    if present:
        md += ["", "## Median miss (m), anchors where every variant has a heading", "",
               "| variant | " + " | ".join("%d s" % h for h in present) + " |",
               "|---|" + "---|" * len(present)]
        md += ["| course | " + " | ".join("%.2f" % find(s["table"], "common", "full", h)
                                          ["course_median_m"] for h in present) + " |"]
        md += ["| %s | " % v + " | ".join(_row(find(s["table"], "common", v, h))[:-2]
                                          if find(s["table"], "common", v, h) else "n/a"
                                          for h in present) + " |" for v in VARIANTS]
        md += ["| pairs | " + " | ".join(str(find(s["table"], "common", "full", h)["n"])
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
