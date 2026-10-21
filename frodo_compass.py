#!/usr/bin/env python3
"""frodo_compass: does an Earth Rover's compass keep its dead reckoning on course?

earth-rover-pilot 0.10.0 carries the rover between GPS fixes with its wheels
along the pilot's heading: the compass plus a bias learned from the GPS
course on straight stretches (DeadReckoner use_course=False, chosen in the
simulator). On 449 recorded FrodoBots-2K rides, wheels along the last GPS
course missed the next fix 10 s later by a median 1.93 m (frodo_odometry.py),
but no study had used the compass on real rides. This one does, scoring
every predictor on the same anchor and target fixes:

- hold, gps_cv, odo_course, odo_cmd20: as in frodo_odometry.
- heading: wheels along the compass heading plus the bias the pilot's
  HeadingEstimator had learned by the anchor (use_course=False).
- turn30: wheels along the last GPS course, turned by as much as the compass
  has turned since once that is over 30 deg (use_course=True, turn_deg 30).
- turn0: the same, turned by every compass change.

FrodoBots-2K logs the raw magnetometer at 1 Hz without saying which axes are
horizontal or which way they run. A frame is a pair of axes and a handedness
(6 in all; a fixed rotation is part of the bias). Each ride's hard-iron offset
for a pair is the centre of a circle fitted to its samples over the whole
ride; a pair whose samples cover less than half the circle, or lie far from
it, is left out for that ride. The frame is chosen on the even-numbered rides
by the median heading error (compass plus bias against the GPS course over
the 3 s before each anchor) and the predictors are scored on the odd ones.

    python frodo_compass.py --out-dir out --rides-per-part 20

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

GPS_LAG_S = 1.5          # GPS behind the wheels (FINDINGS)
MPS_PER_RPM = 0.00668    # metres per second per mean wheel RPM (same)
CMD_LAG_S = 0.5          # turn behind the angular command (same)
CMD_GAIN = 20.0          # deg/s per unit of angular: frodo_odometry's best command gain
DT = 0.2                 # integration step, s
HORIZONS = (1, 2, 3, 5, 10, 20, 30)
BACK_S = 3.0             # the earlier fix that gives the starting course, this far back
BACK_TOL_S = 1.0
MOVE_MIN_M = 1.0         # over the back window, by GPS and by the wheels
HDG_MIN_M = 1.5          # heading errors only where the back window is at least this long
TARGET_TOL_S = 0.5
GYRO_MAX_AGE_S = 1.0
HOLD_EMPTY_S = 1.0       # a cell with no control rows keeps the last speed this long, then 0
COMPASS_GAP_S = 2.5      # interpolate between compass samples at most this far apart
COMPASS_NEAR_S = 1.0     # otherwise take the nearest sample within this
COVER_BINS = 36
COVER_MIN = 18           # a pair's samples must cover half the directions around its centre
CIRCLE_RMS_MAX = 0.35    # and lie near the circle: RMS distance from it over its radius
TURN_DEG = 30.0          # DeadReckoner.turn_deg
STRAIGHT_DEG = 10.0      # strata by the gyroscope's turn over the horizon, as in frodo_odometry
TURNING_DEG = 30.0
# rover_pilot 0.9.3 HeadingEstimator defaults (its compass-spread check is left out).
LEARN = {"min_move_m": 10.0, "min_points": 5, "min_speed_mps": 0.25, "settle_s": 1.0,
         "gain": 0.3, "max_angular": 0.1, "min_linear": 0.2}
FRAMES = {"%s%s%s" % ("xyz"[a], "xyz"[b], "+" if s > 0 else "-"): (a, b, s)
          for a, b in ((0, 1), (0, 2), (1, 2)) for s in (1, -1)}
REFS = ("hold", "gps_cv", "odo_course", "odo_cmd20")
KINDS = ("heading", "turn30", "turn0")
STRATA = ("all", "straight", "mild", "turning")
MIN_PAIRS = 200          # heading errors a frame needs on the even rides to be chosen
SWITCH_RATIO = 1.10      # heading over odo_course at 10 s above this: use_course=True


# --- Helpers ---------------------------------------------------------------

def wrap180(d):
    return (d + 180.0) % 360.0 - 180.0


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
    """A ride's wheel speed (m/s) on cells of DT seconds from the first control
    row (cell k covers [t0 + k DT, t0 + (k + 1) DT)), the commanded turn and,
    if there is a gyroscope, its turn (deg, counter-clockwise) from t0 to the
    start of each cell."""

    def __init__(self, control, gyro, dt=DT):
        self.dt = dt
        self.t0 = control[0][0]
        self.n = n = max(1, int((control[-1][0] - self.t0) / dt) + 1)
        sv, cv, sa, ca = [0.0] * n, [0] * n, [0.0] * n, [0] * n
        for t, _, ang, rpm in control:
            k = self.index(t)
            if 0 <= k < n and all(v is not None for v in rpm):
                sv[k] += sum(rpm) / 4.0 * MPS_PER_RPM
                cv[k] += 1
            k = self.index(t, CMD_LAG_S)
            if 0 <= k < n:
                sa[k] += ang
                ca[k] += 1
        self.v = []
        last, empty, hold = 0.0, 0, int(round(HOLD_EMPTY_S / dt))
        for k in range(n):
            if cv[k]:
                last, empty = sv[k] / cv[k], 0
            else:
                empty += 1
                if empty > hold:
                    last = 0.0
            self.v.append(last)
        self.cmd_yaw = cumulate([sa[k] / ca[k] if ca[k] else 0.0 for k in range(n)], dt)
        self.gyro_yaw = None
        self.gyro_bias = None
        if gyro and len(gyro) >= 20:
            gt = [g[0] for g in gyro]
            self.gyro_bias = statistics.median([g[1] for g in gyro])
            rate = []
            for k in range(n):
                j = nearest(gt, self.t0 + (k + 0.5) * dt, GYRO_MAX_AGE_S)
                rate.append(0.0 if j is None else gyro[j][1] - self.gyro_bias)
            self.gyro_yaw = cumulate(rate, dt)

    def index(self, t, shift=0.0):
        """The cell holding time t + shift (t - t0 first, so epoch times stay exact)."""
        return int(math.floor(((t - self.t0) + shift) / self.dt + 1e-6))

    def cell(self, t):
        """The cell boundary nearest to time t."""
        return int(round((t - self.t0) / self.dt))


def run(grid, k_start, k_ends, psi_of):
    """(east, north) moved from cell boundary k_start to each boundary in sorted
    k_ends, on course psi_of(k) (deg, clockwise from north) through cell k."""
    e = n = 0.0
    out, k = [], k_start
    for kend in k_ends:
        while k < kend:
            d = grid.v[k] * grid.dt
            if d:
                r = math.radians(psi_of(k))
                e += d * math.sin(r)
                n += d * math.cos(r)
            k += 1
        out.append((e, n))
    return out


# --- Compass ---------------------------------------------------------------

def solve3(m, r):
    """x with m x = r for a 3 x 3 m, by Gaussian elimination, or None if singular."""
    a = [list(m[i]) + [r[i]] for i in range(3)]
    scale = max(1.0, max(abs(a[i][j]) for i in range(3) for j in range(3)))
    for c in range(3):
        p = max(range(c, 3), key=lambda i: abs(a[i][c]))
        if abs(a[p][c]) < 1e-12 * scale:
            return None
        a[c], a[p] = a[p], a[c]
        for i in range(c + 1, 3):
            f = a[i][c] / a[c][c]
            for j in range(c, 4):
                a[i][j] -= f * a[c][j]
    x = [0.0] * 3
    for i in (2, 1, 0):
        x[i] = (a[i][3] - sum(a[i][j] * x[j] for j in range(i + 1, 3))) / a[i][i]
    return x


def calibrate(samples, a, b):
    """(info, centre): the hard-iron centre of magnetometer axes a and b (0-2 for
    x, y, z), the circle fitted to the samples by least squares (Kasa). info
    says whether the samples cover at least COVER_MIN of COVER_BINS directions
    around it and lie near it; centre is None when there is no circle."""
    if len(samples) < 20:
        return {"ok": False, "why": "few samples"}, None
    pa = [s[1 + a] for s in samples]
    pb = [s[1 + b] for s in samples]
    ma, mb = sum(pa) / len(pa), sum(pb) / len(pb)
    u = [x - ma for x in pa]
    v = [y - mb for y in pb]
    m = [[0.0] * 3 for _ in range(3)]
    r = [0.0] * 3
    for x, y in zip(u, v):
        row = (x, y, 1.0)
        q = -(x * x + y * y)
        for i in range(3):
            r[i] += row[i] * q
            for j in range(3):
                m[i][j] += row[i] * row[j]
    sol = solve3(m, r)
    if sol is None:
        return {"ok": False, "why": "singular"}, None
    cu, cv = -sol[0] / 2.0, -sol[1] / 2.0
    r2 = cu * cu + cv * cv - sol[2]
    if not r2 > 0:
        return {"ok": False, "why": "no circle"}, None
    radius = math.sqrt(r2)
    bins, sq = set(), 0.0
    for x, y in zip(u, v):
        ang = math.degrees(math.atan2(y - cv, x - cu)) % 360.0
        bins.add(int(ang * COVER_BINS / 360.0) % COVER_BINS)
        sq += (math.hypot(x - cu, y - cv) - radius) ** 2
    rms = math.sqrt(sq / len(u)) / radius
    info = {"centre": [_r(ma + cu, 2), _r(mb + cv, 2)], "radius": _r(radius, 2),
            "cover": len(bins), "rms": _r(rms)}
    info["ok"] = len(bins) >= COVER_MIN and rms <= CIRCLE_RMS_MAX
    if not info["ok"]:
        info["why"] = "cover" if len(bins) < COVER_MIN else "rms"
    return info, (ma + cu, mb + cv)


def compass_cells(grid, ct):
    """For each cell centre: (j0, j1, w) to interpolate the compass samples at
    sorted times ct, (j, j, 0) for the nearest one, or None if none is close."""
    out = []
    for k in range(grid.n):
        tc = grid.t0 + (k + 0.5) * grid.dt
        j = bisect.bisect_left(ct, tc)
        if 0 < j < len(ct) and ct[j] - ct[j - 1] <= COMPASS_GAP_S:
            out.append((j - 1, j, (tc - ct[j - 1]) / (ct[j] - ct[j - 1])))
        else:
            i = nearest(ct, tc, COMPASS_NEAR_S)
            out.append(None if i is None else (i, i, 0.0))
    return out


def frame_headings(samples, where, a, b, s, centre):
    """Compass heading (deg, [0, 360)) of frame (a, b, s) in each cell, or None."""
    ca, cb = centre
    h = [math.degrees(math.atan2(s * (x[1 + b] - cb), x[1 + a] - ca)) % 360.0 for x in samples]
    out = []
    for wj in where:
        if wj is None:
            out.append(None)
        else:
            j0, j1, w = wj
            out.append((h[j0] + w * wrap180(h[j1] - h[j0])) % 360.0)
    return out


def filled(hs):
    """hs with each None replaced by the heading before it (the first one at the start)."""
    last = next((h for h in hs if h is not None), None)
    out = []
    for h in hs:
        if h is not None:
            last = h
        out.append(last)
    return out


def fit_course(pts, min_speed):
    """Course (deg clockwise from north) of the line fitted to fixes [(t, e, n)]
    against time, or None if they don't move at min_speed."""
    t0 = pts[0][0]
    ts = [p[0] - t0 for p in pts]
    tm = sum(ts) / len(ts)
    var = sum((x - tm) ** 2 for x in ts)
    if var <= 0:
        return None
    ve = sum((x - tm) * p[1] for x, p in zip(ts, pts)) / var
    vn = sum((x - tm) * p[2] for x, p in zip(ts, pts)) / var
    if math.hypot(ve, vn) < min_speed:
        return None
    return math.degrees(math.atan2(ve, vn)) % 360.0


def learn_bias(control, fixes, grid, heads, p=LEARN):
    """Replays the pilot's HeadingEstimator over a ride for every frame at once,
    one tick per control row: on straight stretches of at least min_move_m the
    course of a line fitted to the fixes, minus the mean compass heading, moves
    the bias `gain` of the way (the first one sets it). heads gives each
    frame's heading per cell (None where no compass sample is near).
    Returns [(t, {frame: bias})] after each fit, in time order."""
    names = list(heads)
    probe = heads[names[0]]
    bias = dict.fromkeys(names)
    out = []
    lp, since, fi = 0.0, None, 0
    pts, sums, ncomp = [], {f: [0.0, 0.0] for f in names}, 0
    for t, lin, ang, _ in control:
        new = None
        while fi < len(fixes) and fixes[fi][0] <= t:
            new = fixes[fi]
            fi += 1
        lp = 0.8 * lp + 0.2 * ang
        if lin < p["min_linear"] or abs(lp) > p["max_angular"]:
            since = None
            pts, sums, ncomp = [], {f: [0.0, 0.0] for f in names}, 0
            continue
        if since is None:
            since = t
            continue
        if t - since < p["settle_s"]:
            continue
        k = grid.index(t)
        if 0 <= k < grid.n and probe[k] is not None:
            for f in names:
                r = math.radians(heads[f][k])
                sums[f][0] += math.sin(r)
                sums[f][1] += math.cos(r)
            ncomp += 1
        if new is not None:
            pts.append(new)
        if len(pts) < p["min_points"]:
            continue
        if math.hypot(pts[-1][1] - pts[0][1], pts[-1][2] - pts[0][2]) < p["min_move_m"]:
            continue
        course = fit_course(pts, p["min_speed_mps"])
        if course is not None and ncomp:
            for f in names:
                measured = wrap180(course - math.degrees(math.atan2(sums[f][0], sums[f][1])))
                bias[f] = measured if bias[f] is None else \
                    wrap180(bias[f] + p["gain"] * wrap180(measured - bias[f]))
            out.append((t, dict(bias)))
        pts, sums, ncomp = [], {f: [0.0, 0.0] for f in names}, 0
    return out


# --- One ride --------------------------------------------------------------

def new_pool():
    return {"rides": [], "gps_s": 0.0}


def analyse_ride(control, gps, gyro, compass, pool, no=0, anchor_every=3):
    """Stats for ride number `no`; its misses ({(predictor, horizon, stratum): [m]},
    a frame's predictors named 'kind|frame') and heading errors go to pool."""
    st = {"control_rows": len(control), "gps_rows": len(gps),
          "gyro_samples": len(gyro or []), "compass_samples": len(compass or [])}
    if len(control) < 50 or len(gps) < 20:
        st["skipped"] = "too little data"
        return st
    if not compass or len(compass) < 20:
        st["skipped"] = "no compass"
        return st
    st["compass_range"] = [[_r(min(c[1 + i] for c in compass), 2),
                            _r(max(c[1 + i] for c in compass), 2)] for i in range(3)]
    grid = Grid(control, gyro)
    where = compass_cells(grid, [c[0] for c in compass])
    heads, cal = {}, {}
    for f, (a, b, s) in FRAMES.items():
        info, centre = calibrate(compass, a, b)
        cal[f] = info
        if info["ok"]:
            heads[f] = frame_headings(compass, where, a, b, s, centre)
    st["frames"] = cal
    if not heads:
        st["skipped"] = "no frame calibrates"
        return st
    fixes = fresh_fixes(gps)
    fits = learn_bias(control, fixes, grid, heads)
    st["bias_fits"] = len(fits)
    if not fits:
        st["skipped"] = "no straight stretch for the bias"
        return st
    fit_t = [x[0] for x in fits]
    full = {f: filled(h) for f, h in heads.items()}
    probe = heads[next(iter(heads))]
    times = [x[0] for x in fixes]
    cy = grid.cmd_yaw
    errs, anchors = {}, 0

    def add(key, x):
        errs.setdefault(key, array.array("d")).append(x)

    for i in range(0, len(fixes), anchor_every):
        t_i, e_i, n_i = fixes[i]
        q = bisect.bisect_right(fit_t, t_i) - 1
        if q < 0:
            continue
        b = nearest(times, t_i - BACK_S, BACK_TOL_S)
        if b is None or b >= i:
            continue
        t_b, e_b, n_b = fixes[b]
        de, dn = e_i - e_b, n_i - n_b
        k_b, k_i = grid.cell(t_b - GPS_LAG_S), grid.cell(t_i - GPS_LAG_S)
        if k_b < 0 or k_i >= grid.n or math.hypot(de, dn) < MOVE_MIN_M:
            continue
        if sum(grid.v[k_b:k_i]) * grid.dt < MOVE_MIN_M or probe[k_i] is None:
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
        k_ends = [x[0] for x in targets]
        k_mid = (k_b + k_i) // 2
        base = (cy[k_b] + cy[k_i]) / 2.0
        bias = fits[q][1]
        preds = {"odo_course": run(grid, k_i, k_ends, lambda k: psi0),
                 "odo_cmd20": run(grid, k_i, k_ends, lambda k: psi0 - CMD_GAIN * (
                     (cy[k] + cy[k + 1]) / 2.0 - base))}
        for f, hf in full.items():
            then = hf[k_mid]
            preds["heading|" + f] = run(grid, k_i, k_ends,
                                        lambda k, hf=hf, bf=bias[f]: hf[k] + bf)
            preds["turn0|" + f] = run(grid, k_i, k_ends,
                                      lambda k, hf=hf, th=then: psi0 + wrap180(hf[k] - th))
            preds["turn30|" + f] = run(grid, k_i, k_ends, lambda k, hf=hf, th=then: psi0 + (
                wrap180(hf[k] - th) if abs(wrap180(hf[k] - th)) > TURN_DEG else 0.0))
            if math.hypot(de, dn) >= HDG_MIN_M:
                add(("hdg|" + f, 0, "all"), abs(wrap180(then + bias[f] - psi0)))
        vx, vy = de / (t_i - t_b), dn / (t_i - t_b)
        for idx, (k_j, h, j) in enumerate(targets):
            t_j, e_j, n_j = fixes[j]
            stratum = None
            if grid.gyro_yaw is not None:
                turn = abs(grid.gyro_yaw[k_j] - grid.gyro_yaw[k_i])
                stratum = ("straight" if turn <= STRAIGHT_DEG else
                           "turning" if turn >= TURNING_DEG else "mild")
            out = {"hold": (e_i, n_i), "gps_cv": (e_i + vx * (t_j - t_i), n_i + vy * (t_j - t_i))}
            for name, ps in preds.items():
                out[name] = (e_i + ps[idx][0], n_i + ps[idx][1])
            for name, (pe, pn) in out.items():
                miss = math.hypot(pe - e_j, pn - n_j)
                add((name, h, "all"), miss)
                if stratum:
                    add((name, h, stratum), miss)
    span = gps[-1][0] - gps[0][0]
    st.update(gps_span_s=round(span, 1), fresh_fixes=len(fixes), anchors=anchors,
              frames_ok=sorted(heads), bias_last={f: _r(v, 1) for f, v in fits[-1][1].items()})
    pool["rides"].append({"no": no, "frames": sorted(heads), "errs": errs})
    pool["gps_s"] += span
    return st


# --- Summary and report ----------------------------------------------------

def rides_with(pool, f, parity=None):
    return [r for r in pool["rides"]
            if f in r["frames"] and (parity is None or r["no"] % 2 == parity)]


def names_for(f):
    return REFS + tuple("%s|%s" % (k, f) for k in KINDS)


def pooled(rides, names):
    out = {}
    for r in rides:
        for key, v in r["errs"].items():
            if key[0] in names:
                out.setdefault(key, array.array("d")).extend(v)
    return out


def table(errs, names):
    """One row per (horizon, stratum, predictor), a frame's predictors under their
    kind. The lists of one horizon and stratum line up anchor by anchor."""
    rows = []
    for h in HORIZONS:
        for s in STRATA:
            course = errs.get(("odo_course", h, s))
            if not course:
                continue
            cm = statistics.median(course)
            for name in names:
                v = errs.get((name, h, s))
                if not v:
                    continue
                med = statistics.median(v)
                rows.append({
                    "horizon_s": h, "stratum": s, "predictor": name.split("|")[0], "n": len(v),
                    "median_m": _r(med), "p75_m": _r(pct(v, 75)), "p90_m": _r(pct(v, 90)),
                    "median_over_course": _r(med / cm) if cm > 0 else None,
                    "beats_course": _r(sum(1 for a, b in zip(v, course) if a < b) / len(v))})
    return rows


def find(rows, name, h, stratum="all"):
    for r in rows:
        if r["predictor"] == name and r["horizon_s"] == h and r["stratum"] == stratum:
            return r
    return None


def frame_stats(pool, min_pairs=MIN_PAIRS):
    """(chosen frame, per-frame heading errors on the even and odd rides, how
    often each frame has the lowest median heading error within a ride)."""
    stats = {}
    for f in FRAMES:
        row = {"rides_ok": len(rides_with(pool, f))}
        for label, parity in (("cal", 0), ("test", 1)):
            v = [x for r in rides_with(pool, f, parity)
                 for x in r["errs"].get(("hdg|" + f, 0, "all"), ())]
            row[label + "_n"] = len(v)
            row[label + "_median_deg"] = _r(statistics.median(v), 1) if v else None
            row[label + "_p90_deg"] = _r(pct(v, 90), 1)
        stats[f] = row
    ok = [f for f in FRAMES if stats[f]["cal_n"] >= min_pairs]
    chosen = min(ok, key=lambda f: stats[f]["cal_median_deg"]) if ok else None
    winners = {}
    for r in pool["rides"]:
        meds = {}
        for f in r["frames"]:
            v = r["errs"].get(("hdg|" + f, 0, "all"), ())
            if len(v) >= 10:
                meds[f] = statistics.median(v)
        if meds:
            w = min(meds, key=meds.get)
            winners[w] = winners.get(w, 0) + 1
    return chosen, stats, winners


def boot(rides, f, h=10, reps=200, seed=1):
    """95% intervals, resampling rides, of each predictor's median miss h s ahead
    over odo_course's (all anchors)."""
    if len(rides) < 2:
        return {}
    rng = random.Random(seed)
    names = ("gps_cv", "odo_cmd20") + tuple("%s|%s" % (k, f) for k in KINDS)
    ratios = {}
    for _ in range(reps):
        sample = [rides[rng.randrange(len(rides))] for _ in rides]
        course = [x for r in sample for x in r["errs"].get(("odo_course", h, "all"), ())]
        if not course:
            continue
        cm = statistics.median(course)
        if cm <= 0:
            continue
        for name in names:
            v = [x for r in sample for x in r["errs"].get((name, h, "all"), ())]
            if v:
                ratios.setdefault(name.split("|")[0], []).append(statistics.median(v) / cm)
    return {k: [_r(pct(v, 2.5)), _r(pct(v, 97.5))] for k, v in ratios.items()}


def decide(rows):
    """The rules stated in PREDICTION.md before the run."""
    out = {}
    c, hd = find(rows, "odo_course", 10), find(rows, "heading", 10)
    if c and hd and c["median_m"] > 0:
        ratio = hd["median_m"] / c["median_m"]
        out["heading_over_course_10s"] = _r(ratio)
        out["default"] = "use_course=True" if ratio > SWITCH_RATIO else "use_course=False"
    ct, t30 = find(rows, "odo_course", 10, "turning"), find(rows, "turn30", 10, "turning")
    if ct and t30 and ct["median_m"] > 0:
        ratio = t30["median_m"] / ct["median_m"]
        out["turn30_over_course_10s_turning"] = _r(ratio)
        out["turn_rule"] = ("helps" if ratio < 0.95 else "hurts" if ratio > 1.05
                            else "no clear effect")
    return out


def summarise(pool, final=True, min_pairs=MIN_PAIRS):
    chosen, stats, winners = frame_stats(pool, min_pairs)
    res = {"rides": len(pool["rides"]), "gps_hours": _r(pool["gps_s"] / 3600.0, 2),
           "frames": stats, "ride_winners": winners, "chosen_frame": chosen,
           "test_rides": 0, "table": [], "decision": {}, "ci": {}, "table_all_rides": []}
    if chosen:
        names = names_for(chosen)
        test = rides_with(pool, chosen, 1)
        rows = table(pooled(test, names), names)
        res.update(test_rides=len(test), table=rows, decision=decide(rows),
                   ci=boot(test, chosen) if final else {})
        res["table_all_rides"] = [r for r in table(pooled(rides_with(pool, chosen), names), names)
                                  if r["stratum"] == "all"]
    return res


def _m(row):
    return "n/a" if row is None else "%.2f" % row["median_m"]


def conclusions(s):
    lines = []
    if not s["rides"]:
        return lines
    lines.append("%d rides (%.1f hours of GPS) had a magnetometer frame that calibrates and a "
                 "learned bias." % (s["rides"], s["gps_hours"] or 0.0))
    ok = {f: v["rides_ok"] for f, v in s["frames"].items() if v["rides_ok"]}
    lines.append("Rides on which each frame calibrates: %s; frame with the lowest median heading "
                 "error within each ride: %s." % (ok, s["ride_winners"]))
    f = s["chosen_frame"]
    if not f:
        lines.append("No frame had enough heading errors on the even rides to be chosen.")
        return lines
    fs = s["frames"][f]
    lines.append("Chosen frame on the even rides: %s, median heading error %s deg (90th percentile "
                 "%s); on the odd rides %s deg (90th percentile %s), over %d test rides."
                 % (f, fs["cal_median_deg"], fs["cal_p90_deg"], fs["test_median_deg"],
                    fs["test_p90_deg"], s["test_rides"]))
    rows = s["table"]
    for h in (2, 5, 10, 30):
        r = {n: find(rows, n, h) for n in REFS + KINDS}
        if r["odo_course"] is None:
            continue
        lines.append("%d s ahead (odd rides, all anchors): wheels on the last GPS course %s m; "
                     "wheels on compass + learned bias %s m; course turned by the compass over "
                     "30 deg %s m, by every compass change %s m; command turn %s m; GPS constant "
                     "velocity %s m; hold %s m."
                     % (h, _m(r["odo_course"]), _m(r["heading"]), _m(r["turn30"]), _m(r["turn0"]),
                        _m(r["odo_cmd20"]), _m(r["gps_cv"]), _m(r["hold"])))
    for h in (5, 10):
        r = {n: find(rows, n, h, "turning") for n in REFS + KINDS}
        if r["odo_course"] is None:
            continue
        lines.append("%d s ahead while turning 30 deg or more (%d pairs): course %s m, compass "
                     "heading %s m, turn30 %s m, turn0 %s m, command %s m."
                     % (h, r["odo_course"]["n"], _m(r["odo_course"]), _m(r["heading"]),
                        _m(r["turn30"]), _m(r["turn0"]), _m(r["odo_cmd20"])))
    if s["ci"]:
        lines.append("10 s ahead, median miss over the course predictor's, 95%% CI (rides "
                     "resampled): %s." % s["ci"])
    d = s["decision"]
    if "default" in d:
        lines.append("Rule (stated before the run): compass heading over course at 10 s = %s, so "
                     "DeadReckoner's default should be %s." % (d["heading_over_course_10s"],
                                                              d["default"]))
    if "turn_rule" in d:
        lines.append("Turning the course by the compass over 30 deg, 10 s ahead while turning: "
                     "%s of the course predictor's miss (%s)."
                     % (d["turn30_over_course_10s_turning"], d["turn_rule"]))
    return lines


def write_outputs(out_dir, parts, rides, pool, started, final=True, min_pairs=MIN_PAIRS):
    s = summarise(pool, final, min_pairs)
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
              "settings": {"gps_lag_s": GPS_LAG_S, "mps_per_rpm": MPS_PER_RPM,
                           "cmd_gain": CMD_GAIN, "dt_s": DT, "back_s": BACK_S,
                           "hdg_min_m": HDG_MIN_M, "cover_min": COVER_MIN,
                           "circle_rms_max": CIRCLE_RMS_MAX, "turn_deg": TURN_DEG,
                           "learn": LEARN, "min_pairs": min_pairs, "switch_ratio": SWITCH_RATIO},
              "conclusions": lines, "results": s}
    with open(os.path.join(out_dir, "summary.json"), "w") as f:
        json.dump(result, f, indent=1)
    with open(os.path.join(out_dir, "rides.jsonl"), "w") as f:
        for r in rides:
            f.write(json.dumps(r) + "\n")
    md = ["# Compass heading for dead reckoning on Earth Rovers, measured from FrodoBots-2K", "",
          "Generated by frodo_compass.py %s (earth-rover-pilot, MV2 of Munim, Inc.). Data: "
          "FrodoBots-2K by FrodoBots Lab, CC BY-SA 4.0." % __version__, "",
          "Rides sampled: %d, analysed: %d, errors: %d, skipped: %s. Downloaded: %.1f MB."
          % (result["rides_sampled"], result["rides_analysed"], result["ride_errors"], skipped,
             result["bytes_read"] / 1e6), "", "## Findings", ""]
    md += ["- " + line for line in lines] or ["- Nothing to report."]
    md += ["", "## Magnetometer frames", "",
           "| frame | rides ok | even: n | even: median deg | odd: n | odd: median deg | odd: p90 deg |",
           "|---|---|---|---|---|---|---|"]
    md += ["| %s | %d | %d | %s | %d | %s | %s |" % (f, v["rides_ok"], v["cal_n"], v["cal_median_deg"],
                                                    v["test_n"], v["test_median_deg"], v["test_p90_deg"])
           for f, v in s["frames"].items()]
    for stratum in STRATA:
        present = [h for h in HORIZONS if find(s["table"], "odo_course", h, stratum)]
        if not present:
            continue
        md += ["", "## Median miss (m), odd rides, %s anchors, frame %s" % (stratum, s["chosen_frame"]),
               "", "| predictor | " + " | ".join("%d s" % h for h in present) + " |",
               "|---|" + "---|" * len(present)]
        md += ["| %s | " % name + " | ".join(_m(find(s["table"], name, h, stratum)) for h in present)
               + " |" for name in REFS + KINDS]
        md += ["| pairs | " + " | ".join(str(find(s["table"], "odo_course", h, stratum)["n"])
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
    ap.add_argument("--rides-per-part", type=int, default=20)
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
