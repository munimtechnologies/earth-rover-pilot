#!/usr/bin/env python3
"""frodo_gps: how noisy an Earth Rover's GPS really is, measured from FrodoBots-2K.

The Earth Rover Challenge counts a checkpoint as reached within about 15 m
"allowing for noisy GPS", and earth-rover-pilot's simulator draws every fix
with fresh, independent 1.5 m noise. Neither says how a real rover's GPS
behaves. FrodoBots-2K logs every ride's GPS (about 1 Hz) next to the four wheel
RPMs (about 10 Hz), and the wheels say when the rover was really standing
still or driving straight, so the GPS error can be measured against them:

- standing still (all wheel RPMs 0 for 30 s or more): how far the reported
  position wanders, and how the wander grows with time (the mean squared
  displacement between fixes 1 to 300 s apart). Independent noise gives the
  same displacement at every lag; slowly drifting error grows with the lag.
  A Gauss-Markov model (per-axis sigma, correlation time T) is fitted to it.
  Still periods whose fixes spread more than 20 m (the GPS says the rover
  travelled while its wheels read 0: a wheel log or handling fault, not GPS
  noise) are counted and also left out of a second, "clean" fit (0.2.0).
  A fit is offered to the simulator only if it is close and its T lies
  inside the searched range, not on its edge (0.2.1).
- driving straight (both sides' wheels equal, no turn command, 10 s chunks):
  the sideways scatter of the fixes about a fitted line, and the GPS speed
  against the speed from the wheel RPMs.
- the whole ride: gaps with no fix, jumps faster than the rover can drive,
  and how often the reported position changes.

    python frodo_gps.py --out-dir out --rides-per-part 25

Needs frodo_motion.py (earth-rover-pilot) next to it. Standard library only.
By MV2 of Munim, Inc.; written with AI agents. Apache-2.0.
"""

from __future__ import annotations

import argparse
import bisect
import collections
import json
import math
import os
import random
import sys
import time

import frodo_motion as fm

__version__ = "0.2.1"

GPS_LAG_S = 1.5          # GPS behind the wheels (frodo_motion 0.2.0, FINDINGS)
MPS_PER_RPM = 0.00668    # metres per second per mean wheel RPM (same)
RPM_STILL = 1.0          # every wheel at most this many RPM: standing still
CMD_STILL = 0.05         # |linear| and |angular| at most this: no command
STILL_MIN_S = 30.0
STILL_MAX_S = 900.0      # longer still periods are cut to this, so one parked ride can't dominate
TRAVEL_M = 20.0          # a still period with a fix this far from its mean "travelled": left out of the clean fit
FIT_OK = 0.3             # a Gauss-Markov fit with a larger relative error is not offered to the simulator
T_RANGE_S = (0.5, 5000.0)  # correlation times searched; a fit on either end is not offered either
STRAIGHT_MIN_S = 12.0
STRAIGHT_MIN_RPM = 20.0  # about 0.13 m/s
STRAIGHT_SIDE_DIFF = 0.15
CHUNK_S = 10.0
TAUS = (1, 2, 5, 10, 20, 30, 60, 120, 300)
RADII = (2.0, 5.0, 10.0, 15.0)
JUMP_M = 5.0
JUMP_MPS = 3.0
GAP_S = 3.0
INTERVAL_EDGES = (0.6, 1.2, 2.5, 5.0)
SIM_NOISE_M = 1.5        # rover_pilot.SimRover's default: white noise per axis per fix


# --- Helpers ---------------------------------------------------------------

def enu_track(gps):
    """[(t, east, north)] in metres from the ride's first fix."""
    lat0, lon0 = gps[0][1], gps[0][2]
    return [(t,) + fm.to_enu(lat0, lon0, la, lo) for t, la, lo in gps]


def runs(rows, ok, min_s, max_gap=1.0):
    """[(start, end)] times of the stretches of rows where ok(row) holds,
    at least min_s long and with no gap over max_gap between rows."""
    out, start, prev = [], None, None
    for r in rows:
        t = r[0]
        if start is not None and (not ok(r) or t - prev > max_gap):
            if prev - start >= min_s:
                out.append((start, prev))
            start = None
        if ok(r):
            if start is None:
                start = t
            prev = t
    if start is not None and prev - start >= min_s:
        out.append((start, prev))
    return out


def is_still(r):
    return (abs(r[1]) <= CMD_STILL and abs(r[2]) <= CMD_STILL
            and all(v is not None and abs(v) <= RPM_STILL for v in r[3]))


def side_rpms(r):
    """Mean |RPM| of the left (rpm_1, rpm_3) and right (rpm_2, rpm_4) wheels."""
    a = [abs(v) for v in r[3]]
    return (a[0] + a[2]) / 2.0, (a[1] + a[3]) / 2.0


def is_straight(r):
    if r[1] < 0.2 or abs(r[2]) > CMD_STILL or any(v is None for v in r[3]):
        return False
    left, right = side_rpms(r)
    m = (left + right) / 2.0
    return m >= STRAIGHT_MIN_RPM and abs(left - right) <= STRAIGHT_SIDE_DIFF * m


def grid(track, t0, t1, step=1.0, max_age=GAP_S, times=None):
    """(east, north) on a grid from t0 to t1: the last fix at or before each
    time, or None if there is none or it is older than max_age. `times` may
    pass the track's times in, to save working them out on every call."""
    if times is None:
        times = [p[0] for p in track]
    out = []
    n = int(math.floor((t1 - t0) / step + 1e-9)) + 1
    for i in range(max(0, n)):
        t = t0 + i * step
        j = bisect.bisect_right(times, t) - 1
        if j < 0 or t - times[j] > max_age:
            out.append(None)
        else:
            out.append((track[j][1], track[j][2]))
    return out


def pct(values, q):
    s = sorted(values)
    if not s:
        return None
    return s[int(round(q / 100.0 * (len(s) - 1)))]


def _r(x, nd=3):
    return None if x is None else round(x, nd)


# --- Standing still --------------------------------------------------------

def still_window(pts):
    """Spread and displacement sums of the positions of a rover standing
    still, given on a 1 s grid (None = no fix)."""
    good = [p for p in pts if p is not None]
    if len(good) < 10:
        return None
    me = sum(p[0] for p in good) / len(good)
    mn = sum(p[1] for p in good) / len(good)
    r = [math.hypot(p[0] - me, p[1] - mn) for p in good]
    msd = {}
    for tau in TAUS:
        s, c = 0.0, 0
        for i in range(len(pts) - tau):
            a, b = pts[i], pts[i + tau]
            if a is not None and b is not None:
                s += (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2
                c += 1
        if c:
            msd[tau] = (s, c)
    return {"n": len(good), "missing": len(pts) - len(good),
            "r_rms": math.sqrt(sum(x * x for x in r) / len(r)), "r_max": max(r),
            "frozen": max(r) < 0.05, "travelled": max(r) > TRAVEL_M,
            "beyond": {R: sum(1 for x in r if x > R) for R in RADII}, "msd": msd}


def merge_msd(msds):
    tot = {}
    for m in msds:
        for tau, (s, c) in m.items():
            a = tot.setdefault(tau, [0.0, 0])
            a[0] += s
            a[1] += c
    return {tau: (a[0], a[1]) for tau, a in tot.items()}


def pooled_msd(msds):
    """{lag: mean squared displacement, m^2} over every pair in every window."""
    return {tau: s / c for tau, (s, c) in merge_msd(msds).items() if c > 0}


def fit_gauss_markov(msd):
    """(sigma per axis m, T s, relative RMS error) of
    msd(t) = 4 sigma^2 (1 - exp(-t / T)) fitted to {t: msd}, each lag weighted
    by its relative error; None if there is nothing to fit."""
    rows = [(t, m) for t, m in sorted(msd.items()) if m > 0]
    if len(rows) < 2:
        return None
    best = None
    for k in range(61):
        T = T_RANGE_S[0] * 10 ** (k / 15.0)   # 0.5 s .. 5000 s
        g = [1.0 - math.exp(-t / T) for t, _ in rows]
        num = sum(gi / m for gi, (_, m) in zip(g, rows))
        den = sum(gi * gi / (m * m) for gi, (_, m) in zip(g, rows))
        a = num / den
        err = math.sqrt(sum(((m - a * gi) / m) ** 2 for gi, (_, m) in zip(g, rows)) / len(rows))
        if best is None or err < best[2]:
            best = (math.sqrt(a / 4.0), T, err)
    return best


def fit_ok(gm):
    """Whether a fit ({"T_s", "relative_rms_error"}) may be offered to the
    simulator: close enough, and with T inside the searched range. A T on
    either end means the data want a correlation time the model can't give
    (still shrinking or still growing at the edge), so sigma means little."""
    return gm["relative_rms_error"] <= FIT_OK and T_RANGE_S[0] < gm["T_s"] < T_RANGE_S[1]


# --- Driving straight ------------------------------------------------------

def line_fit(times, pts):
    """(sideways RMS m, along-track speed m/s) of points fitted with one
    straight line (total least squares) and a constant speed along it."""
    n = len(pts)
    me = sum(p[0] for p in pts) / n
    mn = sum(p[1] for p in pts) / n
    sxx = sum((p[0] - me) ** 2 for p in pts) / n
    syy = sum((p[1] - mn) ** 2 for p in pts) / n
    sxy = sum((p[0] - me) * (p[1] - mn) for p in pts) / n
    half = (sxx + syy) / 2.0
    d = math.sqrt(((sxx - syy) / 2.0) ** 2 + sxy * sxy)
    lam2 = max(0.0, half - d)
    ang = 0.5 * math.atan2(2.0 * sxy, sxx - syy)
    ux, uy = math.cos(ang), math.sin(ang)
    proj = [(p[0] - me) * ux + (p[1] - mn) * uy for p in pts]
    tm = sum(times) / n
    stt = sum((t - tm) ** 2 for t in times)
    slope = sum((t - tm) * q for t, q in zip(times, proj)) / stt if stt > 0 else 0.0
    return math.sqrt(lam2), abs(slope)


# --- One ride --------------------------------------------------------------

def new_pool():
    return {"windows": [], "ride_msd": [], "ride_msd_clean": [], "ride_msd_moving": [],
            "chunks": [], "jumps": 0, "jumps_still": 0,
            "jump_sizes": [], "gaps": 0, "gap_s": 0.0, "gps_s": 0.0, "rows": 0, "changes": 0,
            "intervals": collections.Counter(), "beyond": collections.Counter(), "samples": 0,
            "beyond_clean": collections.Counter(), "samples_clean": 0}


def interval_bin(dt):
    for e in INTERVAL_EDGES:
        if dt <= e:
            return "<=%g s" % e
    return ">%g s" % INTERVAL_EDGES[-1]


def analyse_ride(control, gps, pool, ride=None):
    """Stats for one ride; its windows, chunks and counts are added to `pool`."""
    st = {"control_rows": len(control), "gps_rows": len(gps)}
    if len(control) < 50 or len(gps) < 20:
        st["skipped"] = "too little data"
        return st
    track = enu_track(gps)
    times = [p[0] for p in track]
    span = track[-1][0] - track[0][0]
    st["gps_span_s"] = round(span, 1)
    st["region"] = [round(gps[0][1]), round(gps[0][2])]

    # The whole ride: gaps, position changes and jumps.
    gaps = [(b[0] - a[0]) for a, b in zip(track, track[1:]) if b[0] - a[0] > GAP_S]
    changes = [track[0]]
    for p in track[1:]:
        if p[1] != changes[-1][1] or p[2] != changes[-1][2]:
            changes.append(p)
    still_runs = runs(control, is_still, 5.0)
    still_starts = [a for a, _ in still_runs]

    def rover_still(t):
        j = bisect.bisect_right(still_starts, t - GPS_LAG_S) - 1
        return j >= 0 and still_runs[j][1] >= t - GPS_LAG_S

    jumps = jumps_still = 0
    for a, b in zip(changes, changes[1:]):
        dt = b[0] - a[0]
        pool["intervals"][interval_bin(dt)] += 1
        d = math.hypot(b[1] - a[1], b[2] - a[2])
        if d > JUMP_M and d > JUMP_MPS * dt:
            jumps += 1
            pool["jump_sizes"].append(d)
            if rover_still(b[0]):
                jumps_still += 1
    st.update(gaps=len(gaps), gap_s=round(sum(gaps), 1), position_changes=len(changes) - 1,
              jumps=jumps, jumps_while_still=jumps_still)
    pool["gaps"] += len(gaps)
    pool["gap_s"] += sum(gaps)
    pool["gps_s"] += span
    pool["rows"] += len(track)
    pool["changes"] += len(changes) - 1
    pool["jumps"] += jumps
    pool["jumps_still"] += jumps_still

    # Standing still. GPS at time T shows where the rover was at T - GPS_LAG_S,
    # so a rover still from a to b shows still fixes from a + lag to b + lag;
    # a margin is left at both ends.
    ride_msds, clean_msds, moving_msds, n_win, n_travelled = [], [], [], 0, 0
    for a, b in runs(control, is_still, STILL_MIN_S):
        g0 = a + GPS_LAG_S + 1.5
        g1 = min(b + GPS_LAG_S - 0.5, g0 + STILL_MAX_S)
        w = still_window(grid(track, g0, g1, times=times))
        if w is None:
            continue
        n_win += 1
        ride_msds.append(w["msd"])
        for R, k in w["beyond"].items():
            pool["beyond"][R] += k
        pool["samples"] += w["n"]
        if w["travelled"]:
            n_travelled += 1
        else:
            clean_msds.append(w["msd"])
            for R, k in w["beyond"].items():
                pool["beyond_clean"][R] += k
            pool["samples_clean"] += w["n"]
            if not w["frozen"]:
                moving_msds.append(w["msd"])
        pool["windows"].append({"ride": ride, "duration_s": round(g1 - g0, 1), "n": w["n"],
                                "missing": w["missing"], "r_rms": _r(w["r_rms"]),
                                "r_max": _r(w["r_max"]), "frozen": w["frozen"],
                                "travelled": w["travelled"],
                                "rms_by_lag": {str(tau): _r(math.sqrt(s / c))
                                               for tau, (s, c) in sorted(w["msd"].items())}})
    if ride_msds:
        pool["ride_msd"].append(merge_msd(ride_msds))
    if clean_msds:
        pool["ride_msd_clean"].append(merge_msd(clean_msds))
    if moving_msds:
        pool["ride_msd_moving"].append(merge_msd(moving_msds))
    st["still_windows"] = n_win
    st["still_windows_travelled"] = n_travelled

    # Driving straight, in 10 s chunks.
    full = [r for r in control if all(v is not None for v in r[3])]
    rpm_s = fm.Series([r[0] for r in full], [sum(abs(v) for v in r[3]) / 4.0 for r in full])
    n_chunks = 0
    for a, b in runs(control, is_straight, STRAIGHT_MIN_S):
        c0, g1 = a + GPS_LAG_S + 1.0, b + GPS_LAG_S
        while c0 + CHUNK_S <= g1 + 1e-9:
            pts = grid(track, c0, c0 + CHUNK_S, times=times)
            ts = [c0 + i for i, p in enumerate(pts) if p is not None]
            good = [p for p in pts if p is not None]
            rpm = rpm_s.mean(c0 - GPS_LAG_S, c0 + CHUNK_S - GPS_LAG_S)
            if len(good) >= 8 and rpm:
                lateral, v_gps = line_fit(ts, good)
                v_odo = rpm * MPS_PER_RPM
                pool["chunks"].append({"lateral_m": lateral, "v_gps": v_gps, "v_odo": v_odo,
                                       "ratio": v_gps / v_odo})
                n_chunks += 1
            c0 += CHUNK_S
    st["straight_chunks"] = n_chunks
    return st


# --- Summary and report ----------------------------------------------------

def boot(ride_msds, reps=200, seed=1):
    """95% intervals, resampling rides, for the RMS displacement at each lag
    and for the fitted sigma and T."""
    if len(ride_msds) < 2:
        return {}, None, None
    rng = random.Random(seed)
    per, sig, tt = {}, [], []
    for _ in range(reps):
        sample = [ride_msds[rng.randrange(len(ride_msds))] for _ in ride_msds]
        m = pooled_msd(sample)
        for tau, v in m.items():
            per.setdefault(tau, []).append(math.sqrt(v))
        f = fit_gauss_markov(m)
        if f:
            sig.append(f[0])
            tt.append(f[1])
    ci = {tau: [_r(pct(v, 2.5)), _r(pct(v, 97.5))] for tau, v in per.items()}
    return (ci, [_r(pct(sig, 2.5)), _r(pct(sig, 97.5))] if sig else None,
            [_r(pct(tt, 2.5), 1), _r(pct(tt, 97.5), 1)] if tt else None)


def msd_summary(ride_msds):
    """(RMS displacement rows, Gauss-Markov fit or None) of a list of rides' msd sums."""
    msd = pooled_msd(ride_msds)
    merged = merge_msd(ride_msds)
    ci, sig_ci, t_ci = boot(ride_msds)
    rows = [{"lag_s": tau, "rms_m": _r(math.sqrt(msd[tau])), "ci95": ci.get(tau),
             "pairs": merged[tau][1]} for tau in TAUS if tau in msd]
    f = fit_gauss_markov(msd)
    gm = None if f is None else {
        "sigma_m": _r(f[0]), "sigma_ci95": sig_ci, "T_s": _r(f[1], 1), "T_ci95": t_ci,
        "relative_rms_error": _r(f[2])}
    return rows, gm


def summarise(pool):
    out = {}
    hours = pool["gps_s"] / 3600.0
    out["gps"] = {"hours": _r(hours, 2), "rows": pool["rows"],
                  "rows_per_s": _r(pool["rows"] / pool["gps_s"], 2) if pool["gps_s"] else None,
                  "position_changes_per_s": _r(pool["changes"] / pool["gps_s"], 3) if pool["gps_s"] else None,
                  "change_intervals": dict(pool["intervals"]),
                  "gaps_over_3s": pool["gaps"], "gap_hours": _r(pool["gap_s"] / 3600.0, 2),
                  "gaps_per_hour": _r(pool["gaps"] / hours, 2) if hours else None,
                  "jumps": pool["jumps"], "jumps_while_still": pool["jumps_still"],
                  "jumps_per_hour": _r(pool["jumps"] / hours, 2) if hours else None,
                  "jump_size_m": {"median": _r(pct(pool["jump_sizes"], 50), 1),
                                  "p90": _r(pct(pool["jump_sizes"], 90), 1),
                                  "max": _r(max(pool["jump_sizes"]), 1) if pool["jump_sizes"] else None}}
    wins = pool["windows"]
    moving = [w for w in wins if not w["frozen"]]
    still = {"windows": len(wins), "rides": len(pool["ride_msd"]),
             "hours": _r(sum(w["duration_s"] for w in wins) / 3600.0, 2),
             "frozen_windows": len(wins) - len(moving),
             "r_rms_m": {"median": pct([w["r_rms"] for w in wins], 50),
                         "p75": pct([w["r_rms"] for w in wins], 75),
                         "p90": pct([w["r_rms"] for w in wins], 90)},
             "r_rms_m_not_frozen": {"median": pct([w["r_rms"] for w in moving], 50),
                                    "p90": pct([w["r_rms"] for w in moving], 90)},
             "r_max_m": {"median": pct([w["r_max"] for w in wins], 50),
                         "p90": pct([w["r_max"] for w in wins], 90)},
             "share_beyond_m": {str(R): _r(pool["beyond"][R] / pool["samples"], 4)
                                for R in RADII} if pool["samples"] else {}}
    still["rms_displacement_m"], still["gauss_markov"] = msd_summary(pool["ride_msd"])
    travelled = [w for w in wins if w["travelled"]]
    clean = {"travel_m": TRAVEL_M, "windows_left_out": len(travelled),
             "rides_left_out": len({w["ride"] for w in travelled}),
             "windows": len(wins) - len(travelled), "rides": len(pool["ride_msd_clean"]),
             "share_beyond_m": {str(R): _r(pool["beyond_clean"][R] / pool["samples_clean"], 4)
                                for R in RADII} if pool["samples_clean"] else {}}
    clean["rms_displacement_m"], clean["gauss_markov"] = msd_summary(pool["ride_msd_clean"])
    clean["not_frozen"] = dict(zip(("rms_displacement_m", "gauss_markov"),
                                   msd_summary(pool["ride_msd_moving"])))
    clean["not_frozen"]["rides"] = len(pool["ride_msd_moving"])
    still["clean"] = clean
    out["still"] = still
    ch = pool["chunks"]
    lat = [c["lateral_m"] for c in ch]
    ratio = [c["ratio"] for c in ch]
    out["straight"] = {"chunks": len(ch),
                       "lateral_rms_m": _r(math.sqrt(sum(x * x for x in lat) / len(lat))) if lat else None,
                       "lateral_m": {"median": _r(pct(lat, 50)), "p90": _r(pct(lat, 90))},
                       "gps_over_wheel_speed": {"median": _r(pct(ratio, 50)), "p25": _r(pct(ratio, 25)),
                                                "p75": _r(pct(ratio, 75))},
                       "wheel_speed_mps_median": _r(pct([c["v_odo"] for c in ch], 50))}
    return out


def conclusions(s):
    lines = []
    g, st, sr = s["gps"], s["still"], s["straight"]
    if g.get("hours"):
        lines.append(
            "GPS log: %.1f hours. The log has %.2f rows a second, but the reported position changes "
            "%.2f times a second. %d gaps of over 3 s (%.1f an hour). %d jumps of over 5 m faster "
            "than 3 m/s (%.2f an hour; %d while the wheels were still; median size %s m, largest %s m)."
            % (g["hours"], g["rows_per_s"] or 0, g["position_changes_per_s"] or 0, g["gaps_over_3s"],
               g["gaps_per_hour"] or 0, g["jumps"], g["jumps_per_hour"] or 0, g["jumps_while_still"],
               g["jump_size_m"]["median"], g["jump_size_m"]["max"]))
    if st["windows"]:
        rows = {r["lag_s"]: r for r in st["rms_displacement_m"]}
        lines.append(
            "Standing still: %d periods of 30 s or more (%.1f hours, %d rides). The position "
            "wandered %.2f m RMS about its mean in the median period (90th percentile %.2f m); "
            "%d periods never moved at all. %.1f%% of still fixes were over 5 m from their "
            "period's mean and %.1f%% over 10 m."
            % (st["windows"], st["hours"], st["rides"], st["r_rms_m"]["median"],
               st["r_rms_m"]["p90"], st["frozen_windows"],
               100 * st["share_beyond_m"].get("5.0", 0), 100 * st["share_beyond_m"].get("10.0", 0)))
        if 1 in rows and 60 in rows:
            lines.append(
                "The wander grows with time: the RMS distance between two fixes of a still rover is "
                "%.2f m 1 s apart, %s m 10 s apart and %.2f m 60 s apart. Independent noise like the "
                "simulator's (%.1f m per axis) would give %.2f m at every lag."
                % (rows[1]["rms_m"], rows[10]["rms_m"] if 10 in rows else "?", rows[60]["rms_m"],
                   SIM_NOISE_M, 2 * SIM_NOISE_M))
        gm = st["gauss_markov"]
        if gm:
            lines.append(
                "Fitted as a Gauss-Markov error: %.2f m per axis (95%% CI %s), correlation time "
                "%.0f s (95%% CI %s), relative fit error %.2f."
                % (gm["sigma_m"], gm["sigma_ci95"], gm["T_s"], gm["T_ci95"], gm["relative_rms_error"]))
        cl = st["clean"]
        crows = {r["lag_s"]: r["rms_m"] for r in cl["rms_displacement_m"]}
        cgm = cl["gauss_markov"]
        if crows:
            lines.append(
                "Leaving out %d still periods in %d rides whose fixes spread over %g m (the GPS says the "
                "rover travelled while its wheels read 0: a wheel log or handling fault, not GPS noise): "
                "%d periods in %d rides; %.1f%% of still fixes over 5 m from their period's mean. RMS "
                "distance between fixes %s m 1 s apart, %s m 10 s, %s m 60 s and %s m 300 s apart.%s"
                % (cl["windows_left_out"], cl["rides_left_out"], cl["travel_m"], cl["windows"], cl["rides"],
                   100 * cl["share_beyond_m"].get("5.0", 0), crows.get(1, "?"), crows.get(10, "?"),
                   crows.get(60, "?"), crows.get(300, "?"),
                   "" if not cgm else
                   " Fitted: %.2f m per axis (95%% CI %s), correlation time %.0f s (95%% CI %s), "
                   "relative fit error %.2f%s."
                   % (cgm["sigma_m"], cgm["sigma_ci95"], cgm["T_s"], cgm["T_ci95"],
                      cgm["relative_rms_error"],
                      "" if fit_ok(cgm) else
                      " (too poor a fit to offer the simulator)"
                      if cgm["relative_rms_error"] > FIT_OK else
                      " (correlation time on the edge of the %g-%g s searched, so not offered "
                      "to the simulator)" % T_RANGE_S)))
    if sr["chunks"]:
        lines.append(
            "Driving straight: %d chunks of 10 s at a median %.2f m/s by the wheels. The fixes "
            "scatter %.2f m RMS sideways about a straight line (median chunk %.2f m, 90th "
            "percentile %.2f m). GPS speed is %.2f times the wheel speed in the median chunk "
            "(middle half %.2f to %.2f)."
            % (sr["chunks"], sr["wheel_speed_mps_median"], sr["lateral_rms_m"],
               sr["lateral_m"]["median"], sr["lateral_m"]["p90"],
               sr["gps_over_wheel_speed"]["median"], sr["gps_over_wheel_speed"]["p25"],
               sr["gps_over_wheel_speed"]["p75"]))
    return lines


def write_outputs(out_dir, parts, rides, pool, started):
    s = summarise(pool)
    lines = conclusions(s)
    gm = s["still"]["clean"]["gauss_markov"]
    result = {"version": __version__, "data": "FrodoBots-2K, FrodoBots Lab, CC BY-SA 4.0",
              "elapsed_s": round(time.monotonic() - started, 1), "parts": parts,
              "rides_sampled": len(rides),
              "rides_analysed": sum(1 for r in rides if "error" not in r and "skipped" not in r),
              "ride_errors": sum(1 for r in rides if "error" in r),
              "bytes_read": sum(p.get("bytes_read", 0) for p in parts),
              "conclusions": lines, "results": s,
              "sim_suggestion": None if not gm else {
                  "gps_noise_m": gm["sigma_m"], "gps_noise_tau_s": gm["T_s"],
                  "fit_ok": fit_ok(gm)}}
    with open(os.path.join(out_dir, "summary.json"), "w") as f:
        json.dump(result, f, indent=1)
    with open(os.path.join(out_dir, "rides.jsonl"), "w") as f:
        for r in rides:
            f.write(json.dumps(r) + "\n")
    with open(os.path.join(out_dir, "windows.jsonl"), "w") as f:
        for w in pool["windows"]:
            f.write(json.dumps(w) + "\n")
    md = ["# How noisy an Earth Rover's GPS is, measured from FrodoBots-2K", "",
          "Generated by frodo_gps.py %s (earth-rover-pilot, MV2 of Munim, Inc.). Data: FrodoBots-2K "
          "by FrodoBots Lab, CC BY-SA 4.0." % __version__, "",
          "Rides sampled: %d, analysed: %d, errors: %d. Downloaded: %.1f MB."
          % (result["rides_sampled"], result["rides_analysed"], result["ride_errors"],
             result["bytes_read"] / 1e6), "", "## Findings", ""]
    md += ["- " + line for line in lines] or ["- Nothing to report."]
    tables = (("All still periods", s["still"].get("rms_displacement_m") or []),
              ("Clean: still periods that travelled over %g m left out" % TRAVEL_M,
               s["still"]["clean"]["rms_displacement_m"]),
              ("Clean and not frozen", s["still"]["clean"]["not_frozen"]["rms_displacement_m"]))
    for title, rows in tables:
        if rows:
            md += ["", "## RMS displacement of a still rover's fixes: %s" % title, "",
                   "| lag s | RMS m | 95% CI (rides resampled) | pairs |", "|---|---|---|---|"]
            md += ["| %s | %s | %s | %s |" % (r["lag_s"], r["rms_m"], r["ci95"], r["pairs"]) for r in rows]
    with open(os.path.join(out_dir, "report.md"), "w") as f:
        f.write("\n".join(md) + "\n")
    return result


# --- Parts -----------------------------------------------------------------

def process_part(rz, label, rides_per_part, pool, rides_out):
    rides = fm.group_rides(rz.entries(lambda name: name.lower().endswith(".csv")))
    usable = sorted(r for r, d in rides.items() if "control_data" in d and "gps_data" in d)
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
            ch, cr = fm.parse_csv(rz.read(d["control_data"]))
            gh, gr = fm.parse_csv(rz.read(d["gps_data"]))
            st.update(analyse_ride(fm.load_control(ch, cr), fm.load_gps(gh, gr), pool,
                                   st.get("ride_id")))
        except Exception as exc:
            st["error"] = "%s: %s" % (type(exc).__name__, exc)
        rides_out.append(st)
    info["bytes_read"] = rz.bytes_read
    return info


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--index-url", default=fm.INDEX_URL)
    ap.add_argument("--parts", default="all", help="comma-separated part numbers, or all")
    ap.add_argument("--rides-per-part", type=int, default=25)
    ap.add_argument("--budget-min", type=float, default=150.0)
    ap.add_argument("--max-cd-mb", type=float, default=800.0)
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
            info = process_part(rz, label, args.rides_per_part, pool, rides)
        except Exception as exc:
            info = {"part": label, "error": "%s: %s" % (type(exc).__name__, exc)}
        info["seconds"] = round(time.monotonic() - t0, 1)
        parts.append(info)
        print("%s: %s" % (label, info), flush=True)
        write_outputs(args.out_dir, parts, rides, pool, started)
    result = write_outputs(args.out_dir, parts, rides, pool, started)
    print("\n".join(result["conclusions"]) or "no conclusions", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
