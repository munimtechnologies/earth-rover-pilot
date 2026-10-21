#!/usr/bin/env python3
"""frodo_blend_b: the held-out check of frodo_blend's 2 s GPS-course hold.

frodo-blend-a-v1 (frodo_blend.py 0.1.0, 146 FrodoBots-2K rides) found that
carrying an Earth Rover's wheels along the last GPS course for the first 2 s
after a fix, then along the live-calibrated compass with the difference fading
out over 2 s more (blend2), missed the GPS fix 10 s later by 0.930 of what the
compass alone missed (95% CI 0.917-0.953). The 2 s was chosen as the best of
three holds on those same rides, so this runs it again, unchanged, on rides
that sample did not contain, and scans the hold more finely:

- course, running: as in frodo_blend (the last GPS course; the running fit).
- hard1 .. hard4: the course for B = 1-4 s, then the compass with no shift.
- blend1 .. blend3: the course for B s, then the compass shifted onto the
  course at the switch, the shift fading out over the next B s.

Rides: in each part, the rides frodo_blend's sample did not pick (30 per part
by fm.pick_evenly), and of those 30 spread evenly. Everything else (anchors,
skip rules, calibration, scoring) is frodo_blend's, and a test checks that
this file's ride analysis gives frodo_blend's numbers exactly. The rules for
reading the result are in PREDICTION.md, written before the run.

    python frodo_blend_b.py --out-dir out --rides-per-part 30

Needs frodo_blend.py, frodo_compass.py, frodo_compass_live.py and
frodo_motion.py next to it. Standard library only.
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
import frodo_compass as fc
import frodo_compass_live as fl
import frodo_motion as fm

__version__ = "0.1.0"

# (name, seconds the course is held, fading shift)
VARIANTS = (("course", None, False), ("running", None, False),
            ("hard1", 1, False), ("hard2", 2, False), ("hard3", 3, False), ("hard4", 4, False),
            ("blend1", 1, True), ("blend2", 2, True), ("blend3", 3, True))
NAMES = tuple(v[0] for v in VARIANTS)
HOLDS = NAMES[2:]
REPORT_H = (1, 5, 10, 30)
FIRST_K = 30             # rides per part in frodo_blend's sample, left out here
ADOPTED = "blend2"       # frodo-blend-a-v1's choice, checked here
CHECK_MIN_PAIRS = 2000   # pairs at 10 s needed before anything is decided
CONFIRM_MAX = 0.97       # C1: blend2 / running at 10 s at most this, CI top below 1
COST_30S = 0.02          # C2: blend2 not worse than running at 30 s by more than this
SWITCH_MARGIN = 0.01     # S1: another hold replaces blend2 only if this much better at 10 s


def setting(name):
    """The pilot setting a variant stands for."""
    for v, hold, decay in VARIANTS:
        if v == name:
            if hold is None:
                return {"course_hold_s": 0.0}
            return {"course_hold_s": float(hold), "fade": decay}
    return None


# --- Rides -------------------------------------------------------------------

def held_out(usable, k, first_k=FIRST_K):
    """k rides spread evenly through those fm.pick_evenly(usable, first_k) leaves out."""
    first = set(fm.pick_evenly(usable, first_k))
    return fm.pick_evenly([r for r in sorted(usable) if r not in first], k)


def new_pool():
    return {"rides": [], "gps_s": 0.0}


def analyse_ride(control, gps, gyro, compass, pool, no=0, anchor_every=3, variants=VARIANTS):
    """frodo_blend.analyse_ride with the variants given as (name, hold_s, fade)."""
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

        psi = {}
        for name, hold, decay in variants:
            if name == "course":
                psi[name] = lambda k, p=psi0: p
            elif name == "running":
                psi[name] = comp
            else:
                psi[name] = fb.blended(psi0, comp, k_i, grid.dt, hold, decay)
        paths = {v: fc.run(grid, k_i, k_ends, f) for v, f in psi.items()}
        for idx, (k_j, h, j) in enumerate(targets):
            t_j, e_j, n_j = fixes[j]
            for name, _, _ in variants:
                p = paths[name][idx]
                add(("miss", name, h), math.hypot(e_i + p[0] - e_j, n_i + p[1] - n_j))
    span = gps[-1][0] - gps[0][0]
    st.update(gps_span_s=round(span, 1), fresh_fixes=len(fixes), anchors=anchors)
    pool["rides"].append({"no": no, "errs": errs})
    pool["gps_s"] += span
    return st


# --- Summary and report ------------------------------------------------------

def table(errs, names=NAMES):
    rows = []
    for h in fc.HORIZONS:
        mc = errs.get(("miss", "course", h))
        if not mc:
            continue
        cm = statistics.median(mc)
        rm = statistics.median(errs[("miss", "running", h)])
        for v in names:
            mv = errs[("miss", v, h)]
            m = statistics.median(mv)
            rows.append({"variant": v, "horizon_s": h, "n": len(mv), "median_m": fc._r(m),
                         "p90_m": fc._r(fc.pct(mv, 90)),
                         "over_course": fc._r(m / cm) if cm > 0 else None,
                         "over_running": fc._r(m / rm) if rm > 0 else None,
                         "beats_running": fc._r(sum(1 for a, c in
                                                    zip(mv, errs[("miss", "running", h)])
                                                    if a < c) / len(mv))})
    return rows


def boot(rides, h=10, reps=200, seed=1, names=NAMES):
    """95% intervals, resampling rides, of each variant's median miss h s ahead
    over the course predictor's and over the running fit's."""
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
        if not med.get("course") or not med.get("running"):
            continue
        for v in names[1:]:
            if v not in med:
                continue
            ratios.setdefault(v + "/course", []).append(med[v] / med["course"])
            if v != "running":
                ratios.setdefault(v + "/running", []).append(med[v] / med["running"])
    return {k: [fc._r(fc.pct(x, 2.5)), fc._r(fc.pct(x, 97.5))] for k, x in ratios.items()}


def decide(rows, ci):
    """The rules stated in PREDICTION.md before the run."""
    find = fb.find
    r = find(rows, "running", 10)
    if r is None or r["over_course"] is None:
        return {"check": {"ok": False, "why": "no running pairs at 10 s"}}
    ok = r["n"] >= CHECK_MIN_PAIRS
    out = {"check": {"ok": ok, "running_over_course_10s": r["over_course"], "pairs_10s": r["n"]}}
    if not ok:
        out["check"]["why"] = "fewer than %d pairs" % CHECK_MIN_PAIRS
        return out
    a10, a30, r30 = find(rows, ADOPTED, 10), find(rows, ADOPTED, 30), find(rows, "running", 30)
    band = ci.get(ADOPTED + "/running")
    out["adopted_over_running_10s"] = a10["over_running"] if a10 else None
    out["adopted_ci_10s"] = band
    c1 = (a10 is not None and a10["over_running"] is not None
          and a10["over_running"] <= CONFIRM_MAX + 1e-9 and band is not None and band[1] < 1.0)
    cost = (None if a30 is None or r30 is None or a30["over_course"] is None
            or r30["over_course"] is None else fc._r(a30["over_course"] - r30["over_course"]))
    out["cost_30s"] = cost
    c2 = cost is not None and cost <= COST_30S + 1e-9
    out["c1"], out["c2"] = c1, c2
    out["confirmed"] = c1 and c2
    pairs = {}
    for b in (1, 2, 3):
        hb, bb = find(rows, "hard%d" % b, 10), find(rows, "blend%d" % b, 10)
        if hb and bb and hb["over_course"] is not None and bb["over_course"] is not None:
            pairs["hard%d-blend%d" % (b, b)] = fc._r(hb["over_course"] - bb["over_course"])
    out["hard_minus_blend_10s"] = pairs
    holds = [x for x in (find(rows, v, 10) for v in HOLDS) if x and x["over_course"] is not None]
    best = min(holds, key=lambda x: x["over_course"], default=None)
    if best is not None:
        out["best"] = best["variant"]
        out["best_over_course_10s"] = best["over_course"]
    if not out["confirmed"]:
        out["default"] = "running"
        return out
    out["default"] = ADOPTED
    if best is not None and best["variant"] != ADOPTED:
        b30 = find(rows, best["variant"], 30)
        if (best["over_course"] <= a10["over_course"] - SWITCH_MARGIN + 1e-9 and b30
                and b30["over_course"] is not None
                and b30["over_course"] - r30["over_course"] <= COST_30S + 1e-9):
            out["default"] = best["variant"]
    out["setting"] = setting(out["default"])
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
    lines.append("%d held-out rides (%.1f hours of GPS) were scored, %d of them with pairs; "
                 "every variant is scored on the same anchors."
                 % (s["rides"], s["gps_hours"] or 0.0, s["rides_with_pairs"]))
    for h in REPORT_H:
        c = find(s["table"], "course", h)
        if c:
            lines.append("%d s ahead (%d pairs): course %.2f m; " % (h, c["n"], c["median_m"])
                         + "; ".join("%s %.2f m (x%s of course, x%s of running)"
                                     % (v, find(s["table"], v, h)["median_m"],
                                        find(s["table"], v, h)["over_course"],
                                        find(s["table"], v, h)["over_running"])
                                     for v in NAMES[1:]) + ".")
    if s["ci"]:
        lines.append("10 s ahead, 95%% CI of median-miss ratios (rides resampled): %s." % s["ci"])
    d = s["decision"]
    c = d["check"]
    if not c["ok"]:
        lines.append("Check (stated before the run) failed: %s (running / course at 10 s = %s on "
                     "%s pairs). Nothing is decided." % (c["why"], c.get("running_over_course_10s"),
                                                         c.get("pairs_10s")))
        return lines
    lines.append("Check: %d pairs at 10 s; running / course at 10 s = %s (frodo-blend-a-v1: "
                 "0.926)." % (c["pairs_10s"], c["running_over_course_10s"]))
    lines.append("Rule C1 (stated before the run): %s / running at 10 s = %s, CI %s; needs <= %s "
                 "with the CI's top below 1: %s." % (ADOPTED, d["adopted_over_running_10s"],
                                                     d["adopted_ci_10s"], CONFIRM_MAX,
                                                     "met" if d["c1"] else "not met"))
    lines.append("Rule C2 (stated before the run): %s minus running over course at 30 s = %s; "
                 "needs <= %s: %s." % (ADOPTED, d["cost_30s"], COST_30S,
                                       "met" if d["c2"] else "not met"))
    lines.append("Hard minus fading switch at the same hold, 10 s: %s." % d["hard_minus_blend_10s"])
    if "best" in d:
        lines.append("Best hold at 10 s: %s (x%s of course)." % (d["best"],
                                                                  d["best_over_course_10s"]))
    if d["confirmed"]:
        lines.append("Rule S1 (stated before the run): the pilot setting is %s %s."
                     % (d["default"], d["setting"]))
    else:
        lines.append("Not confirmed: the pilot keeps following the compass alone (running).")
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
              "settings": {"variants": VARIANTS, "first_k": FIRST_K, "adopted": ADOPTED,
                           "check_min_pairs": CHECK_MIN_PAIRS, "confirm_max": CONFIRM_MAX,
                           "cost_30s": COST_30S, "switch_margin": SWITCH_MARGIN,
                           "frodo_blend": fb.__version__, "frodo_compass": fc.__version__,
                           "frodo_compass_live": fl.__version__},
              "conclusions": lines, "results": s}
    with open(os.path.join(out_dir, "summary.json"), "w") as f:
        json.dump(result, f, indent=1)
    with open(os.path.join(out_dir, "rides.jsonl"), "w") as f:
        for r in rides:
            f.write(json.dumps(r) + "\n")
    md = ["# How long to trust the last GPS course: the held-out check (FrodoBots-2K)", "",
          "Generated by frodo_blend_b.py %s (earth-rover-pilot, MV2 of Munim, Inc.). Data: "
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


# --- Parts -------------------------------------------------------------------

def process_part(rz, label, rides_per_part, pool, rides_out, imu_max_mb=30.0, first_k=FIRST_K):
    rides = fm.group_rides(rz.entries(lambda name: name.lower().endswith(".csv")))
    usable = sorted(r for r, d in rides.items()
                    if "control_data" in d and "gps_data" in d and "imu_data" in d)
    chosen = held_out(usable, rides_per_part, first_k)
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
    ap.add_argument("--first-k", type=int, default=FIRST_K)
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
