#!/usr/bin/env python3
"""frodo_odometry: can an Earth Rover's wheels and gyroscope bridge the gaps between GPS fixes?

An Earth Rover Zero logged a GPS fix about once a second; the Earth Rover
Mini+ that the challenge drives now reports telemetry about every 2 s, and
real receivers drop out. Between fixes a pilot can either hold the last fix
or dead-reckon from the wheel RPMs (10 Hz) and a heading. FrodoBots-2K logs
all of these for human-driven rides, so the choice can be measured instead of
guessed: from an anchor fix, each predictor says where the next fix 1 to 30 s
later will be, and its miss is the distance to that fix.

- hold: the anchor fix itself.
- gps_cv: the anchor plus the GPS velocity over the 3 s before it.
- odo_course: wheel distance along the last GPS course (anchor fix and the
  fix about 3 s before it).
- odo_gyro*: the same, turning the course with the gyroscope's x axis
  (degrees per second, counter-clockwise, its ride median removed) at gains
  1, 0.5 and 1.5; odo_gyro_flip turns it the wrong way, as a sign check.
- odo_cmd*: turning with the commanded angular, 20, 30 or 40 deg/s per unit,
  0.5 s after the command.

GPS shows where the rover was 1.5 s earlier (FINDINGS), so the wheels and
the gyroscope are integrated over the same shifted window. Anchors are taken
only while the rover moves (at least 1 m by GPS and by the wheels over the
3 s before). Every predictor is scored on the same anchor and target fixes,
which are themselves noisy, so no predictor can reach zero. Results are
pooled over all anchors and split by how far the gyroscope says the rover
turned over the horizon (straight up to 10 deg, turning from 30 deg).

    python frodo_odometry.py --out-dir out --rides-per-part 20

Needs frodo_motion.py (earth-rover-pilot) next to it. Standard library only.
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

import frodo_motion as fm

__version__ = "0.1.0"

GPS_LAG_S = 1.5          # GPS behind the wheels (frodo_motion 0.2.0, FINDINGS)
MPS_PER_RPM = 0.00668    # metres per second per mean wheel RPM (same)
CMD_LAG_S = 0.5          # gyroscope behind the angular command (same, spinning in place)
DT = 0.2                 # integration step, s
HORIZONS = (1, 2, 3, 5, 10, 20, 30)
BACK_S = 3.0             # the earlier fix that gives the starting course, this far back
BACK_TOL_S = 1.0
MOVE_MIN_M = 1.0         # over the back window, by GPS and by the wheels
TARGET_TOL_S = 0.5
GYRO_MAX_AGE_S = 1.0
HOLD_EMPTY_S = 1.0       # a cell with no control rows keeps the last speed this long, then 0
STRAIGHT_DEG = 10.0
TURN_DEG = 30.0
# name: (heading source, gain). Gains are deg/s per gyroscope unit or per unit of angular.
PREDICTORS = {
    "odo_course": ("none", 0.0),
    "odo_gyro": ("gyro", 1.0),
    "odo_gyro_x0.5": ("gyro", 0.5),
    "odo_gyro_x1.5": ("gyro", 1.5),
    "odo_gyro_flip": ("gyro", -1.0),
    "odo_cmd20": ("cmd", 20.0),
    "odo_cmd30": ("cmd", 30.0),
    "odo_cmd40": ("cmd", 40.0),
}
BASELINES = ("hold", "gps_cv")
NAMES = BASELINES + tuple(PREDICTORS)
STRATA = ("all", "straight", "mild", "turning")
GYRO_NAMES = tuple(n for n, (s, _) in PREDICTORS.items() if s == "gyro")
CMD_NAMES = tuple(n for n, (s, _) in PREDICTORS.items() if s == "cmd")


# --- Helpers ---------------------------------------------------------------

def nearest(times, target, tol):
    """Index of the time in sorted `times` nearest to target, if within tol, else None."""
    j = bisect.bisect_left(times, target)
    best = None
    for k in (j - 1, j):
        if 0 <= k < len(times) and abs(times[k] - target) <= tol + 1e-9:
            if best is None or abs(times[k] - target) < abs(times[best] - target):
                best = k
    return best


def fresh_fixes(gps):
    """[(t, east, north)] in metres from the first fix, keeping only fixes that
    differ from the one before (a receiver repeats its last fix between updates)."""
    lat0, lon0 = gps[0][1], gps[0][2]
    out = []
    for t, la, lo in gps:
        e, n = fm.to_enu(lat0, lon0, la, lo)
        if not out or e != out[-1][1] or n != out[-1][2]:
            out.append((t, e, n))
    return out


def cumulate(rate, dt):
    out = [0.0]
    for r in rate:
        out.append(out[-1] + r * dt)
    return out


def pct(values, q):
    s = sorted(values)
    if not s:
        return None
    return s[int(round(q / 100.0 * (len(s) - 1)))]


def _r(x, nd=3):
    return None if x is None else round(x, nd)


class Grid:
    """A ride's wheel speed (m/s) and turn rates on cells of DT seconds from the
    first control row: cell k covers [t0 + k DT, t0 + (k + 1) DT). yaw[src][k]
    is the turn (deg, counter-clockwise, at gain 1) from t0 to the start of cell k."""

    def __init__(self, control, gyro, dt=DT):
        self.dt = dt
        self.t0 = control[0][0]
        self.n = n = max(1, int((control[-1][0] - self.t0) / dt) + 1)
        sv, cv, sa, ca = [0.0] * n, [0] * n, [0.0] * n, [0] * n
        for t, _, ang, rpm in control:
            k = self._index(t)
            if 0 <= k < n and all(v is not None for v in rpm):
                sv[k] += sum(rpm) / 4.0 * MPS_PER_RPM
                cv[k] += 1
            k = self._index(t, CMD_LAG_S)
            if 0 <= k < n:
                sa[k] += ang
                ca[k] += 1
        self.v, self.empty_cells = [], 0
        last, empty, hold = 0.0, 0, int(round(HOLD_EMPTY_S / dt))
        for k in range(n):
            if cv[k]:
                last, empty = sv[k] / cv[k], 0
            else:
                empty += 1
                self.empty_cells += 1
                if empty > hold:
                    last = 0.0
            self.v.append(last)
        cmd = [sa[k] / ca[k] if ca[k] else 0.0 for k in range(n)]
        gt = [g[0] for g in gyro]
        self.gyro_bias = statistics.median([g[1] for g in gyro]) if gyro else 0.0
        rate = []
        for k in range(n):
            j = nearest(gt, self.t0 + (k + 0.5) * dt, GYRO_MAX_AGE_S)
            rate.append(0.0 if j is None else gyro[j][1] - self.gyro_bias)
        self.yaw = {"none": [0.0] * (n + 1), "gyro": cumulate(rate, dt), "cmd": cumulate(cmd, dt)}

    def _index(self, t, shift=0.0):
        """The cell holding time t + shift (t - t0 first, so epoch times stay exact)."""
        return int(math.floor(((t - self.t0) + shift) / self.dt + 1e-6))

    def cell(self, t):
        """The cell boundary nearest to time t."""
        return int(round((t - self.t0) / self.dt))


def dead_reckon(grid, src, gain, psi0, base, k_start, k_ends):
    """(east, north) moved from cell boundary k_start to each boundary in sorted
    k_ends, on course psi0 (deg, clockwise from north) when the source's yaw
    was `base`, turned by gain times the source's yaw since."""
    y = grid.yaw[src]
    e = n = 0.0
    out, k = [], k_start
    for kend in k_ends:
        while k < kend:
            psi = math.radians(psi0 - gain * ((y[k] + y[k + 1]) / 2.0 - base))
            d = grid.v[k] * grid.dt
            e += d * math.sin(psi)
            n += d * math.cos(psi)
            k += 1
        out.append((e, n))
    return out


# --- One ride --------------------------------------------------------------

def new_pool():
    return {"per_ride": [], "gps_s": 0.0}


def analyse_ride(control, gps, gyro, pool, ride=None, anchor_every=3):
    """Stats for one ride; its misses ({(predictor, horizon, stratum): [m]}) go to pool."""
    st = {"control_rows": len(control), "gps_rows": len(gps), "gyro_samples": len(gyro or [])}
    if len(control) < 50 or len(gps) < 20:
        st["skipped"] = "too little data"
        return st
    if not gyro or len(gyro) < 20:
        st["skipped"] = "no gyroscope"
        return st
    grid = Grid(control, gyro)
    fixes = fresh_fixes(gps)
    times = [f[0] for f in fixes]
    gyro_yaw = grid.yaw["gyro"]
    errs, anchors = {}, 0
    for i in range(0, len(fixes), anchor_every):
        t_i, e_i, n_i = fixes[i]
        b = nearest(times, t_i - BACK_S, BACK_TOL_S)
        if b is None or b >= i:
            continue
        t_b, e_b, n_b = fixes[b]
        de, dn = e_i - e_b, n_i - n_b
        k_b, k_i = grid.cell(t_b - GPS_LAG_S), grid.cell(t_i - GPS_LAG_S)
        if k_b < 0 or k_i > grid.n or math.hypot(de, dn) < MOVE_MIN_M:
            continue
        if sum(grid.v[k_b:k_i]) * grid.dt < MOVE_MIN_M:
            continue
        targets = []
        for h in HORIZONS:
            j = nearest(times, t_i + h, TARGET_TOL_S)
            if j is None or j <= i:
                continue
            k_j = grid.cell(times[j] - GPS_LAG_S)
            if k_j <= grid.n:
                targets.append((k_j, h, j))
        if not targets:
            continue
        targets.sort()
        anchors += 1
        psi0 = math.degrees(math.atan2(de, dn))
        k_ends = [t[0] for t in targets]
        preds = {}
        for name, (src, gain) in PREDICTORS.items():
            y = grid.yaw[src]
            preds[name] = dead_reckon(grid, src, gain, psi0, (y[k_b] + y[k_i]) / 2.0, k_i, k_ends)
        vx, vy = de / (t_i - t_b), dn / (t_i - t_b)
        for idx, (k_j, h, j) in enumerate(targets):
            t_j, e_j, n_j = fixes[j]
            turn = abs(gyro_yaw[k_j] - gyro_yaw[k_i])
            stratum = ("straight" if turn <= STRAIGHT_DEG else
                       "turning" if turn >= TURN_DEG else "mild")
            out = {"hold": (e_i, n_i), "gps_cv": (e_i + vx * (t_j - t_i), n_i + vy * (t_j - t_i))}
            for name, ps in preds.items():
                out[name] = (e_i + ps[idx][0], n_i + ps[idx][1])
            for name in NAMES:
                pe, pn = out[name]
                miss = math.hypot(pe - e_j, pn - n_j)
                for s in ("all", stratum):
                    errs.setdefault((name, h, s), array.array("d")).append(miss)
    span = gps[-1][0] - gps[0][0]
    st.update(gps_span_s=round(span, 1), fresh_fixes=len(fixes),
              fresh_per_s=_r(len(fixes) / span) if span > 0 else None, anchors=anchors,
              gyro_bias=_r(grid.gyro_bias), empty_cells=grid.empty_cells)
    pool["per_ride"].append(errs)
    pool["gps_s"] += span
    return st


# --- Summary and report ----------------------------------------------------

def pooled(per_ride):
    out = {}
    for errs in per_ride:
        for key, v in errs.items():
            out.setdefault(key, array.array("d")).extend(v)
    return out


def table(pool_errs):
    """One row per (horizon, stratum, predictor). The lists of one horizon and
    stratum line up anchor by anchor, so shares of wins are paired."""
    rows = []
    for h in HORIZONS:
        for s in STRATA:
            hold = pool_errs.get(("hold", h, s))
            if not hold:
                continue
            course = pool_errs.get(("odo_course", h, s))
            hold_med = statistics.median(hold)
            for name in NAMES:
                v = pool_errs.get((name, h, s))
                if not v:
                    continue
                med = statistics.median(v)
                rows.append({
                    "horizon_s": h, "stratum": s, "predictor": name, "n": len(v),
                    "median_m": _r(med), "p75_m": _r(pct(v, 75)), "p90_m": _r(pct(v, 90)),
                    "median_over_hold": _r(med / hold_med) if hold_med > 0 else None,
                    "beats_hold": _r(sum(1 for a, b in zip(v, hold) if a < b) / len(v)),
                    "beats_course": _r(sum(1 for a, b in zip(v, course) if a < b) / len(v))
                    if course else None})
    return rows


def find(rows, name, h, stratum="all"):
    for r in rows:
        if r["predictor"] == name and r["horizon_s"] == h and r["stratum"] == stratum:
            return r
    return None


def best_of(rows, names, h=10, stratum="turning", min_n=30):
    cand = [find(rows, n, h, stratum) for n in names]
    cand = [r for r in cand if r is not None and r["n"] >= min_n]
    return min(cand, key=lambda r: r["median_m"])["predictor"] if cand else None


def boot(per_ride, reps=200, seed=1):
    """95% intervals, resampling rides, for each predictor's median miss and its
    ratio to holding the last fix, per horizon (all anchors)."""
    if len(per_ride) < 2:
        return {}
    rng = random.Random(seed)
    meds, ratios = {}, {}
    for _ in range(reps):
        sample = [per_ride[rng.randrange(len(per_ride))] for _ in per_ride]
        for h in HORIZONS:
            hold = [x for r in sample for x in r.get(("hold", h, "all"), ())]
            if not hold:
                continue
            hm = statistics.median(hold)
            for name in NAMES:
                v = [x for r in sample for x in r.get((name, h, "all"), ())]
                if not v:
                    continue
                m = statistics.median(v)
                meds.setdefault((name, h), []).append(m)
                if hm > 0:
                    ratios.setdefault((name, h), []).append(m / hm)
    return {"%s|%d" % key: {"median_ci95": [_r(pct(v, 2.5)), _r(pct(v, 97.5))],
                            "ratio_ci95": [_r(pct(ratios[key], 2.5)), _r(pct(ratios[key], 97.5))]
                            if key in ratios else None}
            for key, v in meds.items()}


def summarise(pool, final=True):
    rows = table(pooled(pool["per_ride"]))
    hold_all = [r["n"] for r in rows if r["predictor"] == "hold" and r["stratum"] == "all"]
    return {"rides": len(pool["per_ride"]), "gps_hours": _r(pool["gps_s"] / 3600.0, 2),
            "anchor_targets": sum(hold_all), "table": rows,
            "best_gyro_gain_10s_turning": best_of(rows, GYRO_NAMES),
            "best_cmd_gain_10s_turning": best_of(rows, CMD_NAMES),
            "ci": boot(pool["per_ride"]) if final else {}}


def _m(row):
    return "n/a" if row is None else "%.2f" % row["median_m"]


def conclusions(s):
    rows, lines = s["table"], []
    if not s["anchor_targets"]:
        return lines
    lines.append("%d rides (%.1f hours of GPS); %d anchor-to-target pairs while the rover was moving."
                 % (s["rides"], s["gps_hours"] or 0.0, s["anchor_targets"]))
    for h in (2, 5, 10, 30):
        r = {n: find(rows, n, h) for n in NAMES}
        if r["hold"] is None:
            continue
        ci = s["ci"].get("odo_gyro|%d" % h)
        lines.append(
            "%d s ahead (all anchors): holding the last fix misses the next fix by a median %s m; "
            "GPS constant velocity %s m; wheels on the last GPS course %s m; wheels + gyroscope "
            "%s m%s; wheels + command at 30 deg/s per unit %s m."
            % (h, _m(r["hold"]), _m(r["gps_cv"]), _m(r["odo_course"]), _m(r["odo_gyro"]),
               " (95%% CI %s, rides resampled)" % ci["median_ci95"] if ci else "",
               _m(r["odo_cmd30"])))
    for h in (5, 10):
        r = {n: find(rows, n, h, "turning") for n in NAMES}
        if r["hold"] is None:
            continue
        lines.append(
            "%d s ahead while turning 30 deg or more (%d pairs): hold %s m, GPS constant velocity "
            "%s m, wheels on the last course %s m, wheels + gyroscope %s m (turned the wrong way: "
            "%s m), wheels + command %s m."
            % (h, r["hold"]["n"], _m(r["hold"]), _m(r["gps_cv"]), _m(r["odo_course"]),
               _m(r["odo_gyro"]), _m(r["odo_gyro_flip"]), _m(r["odo_cmd30"])))
    if s["best_gyro_gain_10s_turning"] or s["best_cmd_gain_10s_turning"]:
        lines.append("Best heading gain 10 s ahead while turning: %s among the gyroscope gains, "
                     "%s among the command gains."
                     % (s["best_gyro_gain_10s_turning"], s["best_cmd_gain_10s_turning"]))
    return lines


def write_outputs(out_dir, parts, rides, pool, started, final=True):
    s = summarise(pool, final)
    lines = conclusions(s)
    result = {"version": __version__, "data": "FrodoBots-2K, FrodoBots Lab, CC BY-SA 4.0",
              "done": final, "elapsed_s": round(time.monotonic() - started, 1), "parts": parts,
              "rides_sampled": len(rides),
              "rides_analysed": sum(1 for r in rides if "error" not in r and "skipped" not in r),
              "ride_errors": sum(1 for r in rides if "error" in r),
              "bytes_read": sum(p.get("bytes_read", 0) for p in parts),
              "settings": {"gps_lag_s": GPS_LAG_S, "mps_per_rpm": MPS_PER_RPM,
                           "cmd_lag_s": CMD_LAG_S, "dt_s": DT, "back_s": BACK_S,
                           "move_min_m": MOVE_MIN_M, "predictors": PREDICTORS,
                           "strata_deg": [STRAIGHT_DEG, TURN_DEG]},
              "conclusions": lines, "results": s}
    with open(os.path.join(out_dir, "summary.json"), "w") as f:
        json.dump(result, f, indent=1)
    with open(os.path.join(out_dir, "rides.jsonl"), "w") as f:
        for r in rides:
            f.write(json.dumps(r) + "\n")
    md = ["# Dead reckoning between GPS fixes on Earth Rovers, measured from FrodoBots-2K", "",
          "Generated by frodo_odometry.py %s (earth-rover-pilot, MV2 of Munim, Inc.). Data: "
          "FrodoBots-2K by FrodoBots Lab, CC BY-SA 4.0." % __version__, "",
          "Rides sampled: %d, analysed: %d, errors: %d. Downloaded: %.1f MB."
          % (result["rides_sampled"], result["rides_analysed"], result["ride_errors"],
             result["bytes_read"] / 1e6), "", "## Findings", ""]
    md += ["- " + line for line in lines] or ["- Nothing to report."]
    for stratum in STRATA:
        present = [h for h in HORIZONS if find(s["table"], "hold", h, stratum)]
        if not present:
            continue
        md += ["", "## Median miss (m), %s anchors" % stratum, "",
               "| predictor | " + " | ".join("%d s" % h for h in present) + " |",
               "|---|" + "---|" * len(present)]
        md += ["| %s | " % name + " | ".join(_m(find(s["table"], name, h, stratum)) for h in present)
               + " |" for name in NAMES]
        md += ["| pairs | " + " | ".join(str(find(s["table"], "hold", h, stratum)["n"])
                                          for h in present) + " |"]
    if s["ci"]:
        md += ["", "## Median miss over holding the last fix, 95% CI (rides resampled), all anchors",
               "", "| predictor | horizon s | ratio CI |", "|---|---|---|"]
        md += ["| %s | %d | %s |" % (name, h, s["ci"]["%s|%d" % (name, h)]["ratio_ci95"])
               for name in ("gps_cv", "odo_course", "odo_gyro", "odo_cmd30") for h in HORIZONS
               if "%s|%d" % (name, h) in s["ci"]]
    with open(os.path.join(out_dir, "report.md"), "w") as f:
        f.write("\n".join(md) + "\n")
    return result


# --- Parts -----------------------------------------------------------------

def process_part(rz, label, rides_per_part, pool, rides_out, gyro_max_mb=40.0):
    rides = fm.group_rides(rz.entries(lambda name: name.lower().endswith(".csv")))
    usable = sorted(r for r, d in rides.items()
                    if "control_data" in d and "gps_data" in d and "imu_data" in d)
    chosen = fm.pick_evenly(usable, rides_per_part)
    info = {"part": label, "zip_bytes": rz.size, "rides_usable": len(usable),
            "rides_sampled": len(chosen)}
    for ride in chosen:
        d = rides[ride]
        st = {"part": label}
        m = fm.RIDE_RE.search(ride)
        if m:
            st["ride_id"], st["ride_time"] = m.group(1), m.group(2)
        try:
            if d["imu_data"].usize > gyro_max_mb * (1 << 20):
                st["skipped"] = "IMU file of %d bytes" % d["imu_data"].usize
            else:
                ih, ir = fm.parse_csv(rz.read(d["imu_data"]))
                ch, cr = fm.parse_csv(rz.read(d["control_data"]))
                gh, gr = fm.parse_csv(rz.read(d["gps_data"]))
                st.update(analyse_ride(fm.load_control(ch, cr), fm.load_gps(gh, gr),
                                       fm.load_imu(ih, ir), pool, st.get("ride_id")))
        except Exception as exc:
            st["error"] = "%s: %s" % (type(exc).__name__, exc)
        rides_out.append(st)
    info["bytes_read"] = rz.bytes_read
    return info


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--index-url", default=fm.INDEX_URL)
    ap.add_argument("--parts", default="all", help="comma-separated part numbers, or all")
    ap.add_argument("--rides-per-part", type=int, default=20)
    ap.add_argument("--budget-min", type=float, default=120.0)
    ap.add_argument("--max-cd-mb", type=float, default=800.0)
    ap.add_argument("--gyro-max-mb", type=float, default=40.0)
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
            info = process_part(rz, label, args.rides_per_part, pool, rides, args.gyro_max_mb)
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
