#!/usr/bin/env python3
"""frodo_regap: is a real rover's first GPS fix after a gap safe to restart from?

pace-w (studies/pace-w/GRADE.md) found in simulation that starting
earth-rover-pilot's GPS average again from the first fix after a gap longer
than 3 s cut the worst position error through long outages from about 60 m to
10 m. But the simulator's first fix after a gap is as good as any other, and a
real receiver's may not be. This study measures that on FrodoBots-2K's
recorded rides, by replaying rover_pilot 0.19.0's own GpsFilter over each
ride's GPS log twice:

- keep: the shipped filter, which blends the first fix after a gap into the
  average from before it (alpha 0.3);
- restart: the same filter, except that the first new fix it accepts after a
  gap longer than max_age_s (3 s) starts the average again (pace-w's restart).

Each estimate is judged against a reference: where a constant-velocity line
fitted to the ride's new GPS positions 1.5 to 10.5 s later puts the rover (the
fix itself is not in the fit). The same reference is built for every 10th
ordinary fix (no gap in the 20 s before), so the first fix after a gap is
compared with an ordinary fix judged the same way. The rules for reading the
result are in studies/frodo-regap/PREDICTION.md, written before the run.

    python frodo_regap.py --out-dir out --rides-per-part 60

Needs frodo_motion.py (earth-rover-pilot v0.8.0) and rover_pilot.py (v0.19.0)
next to it. Standard library only.
By MV2 of Munim, Inc.; written with AI agents. Apache-2.0.
"""

from __future__ import annotations

import argparse
import bisect
import json
import math
import os
import random
import sys
import time

import frodo_motion as fm
import rover_pilot as rp

__version__ = "0.1.0"

GAP_S = 3.0              # GpsFilter.max_age_s: a longer wait loses the fix
GPS_LAG_S = 1.5          # GPS behind the wheels (frodo_motion, FINDINGS)
MPS_PER_RPM = 0.00668    # metres per second per mean wheel RPM (frodo_gps)
DROVE_M = 2.0            # a gap through which the wheels drove this far "drove"
REF_FROM_S, REF_TO_S = 1.5, 10.5   # the reference line uses new positions this long after the fix
REF_MIN_PTS = 4
REF_MIN_SPAN_S = 4.0
BASE_EVERY = 10          # every 10th eligible ordinary fix is a baseline fix
BASE_CLEAN_S = 20.0      # an ordinary fix has no gap (and no ride start) in the 20 s before
FAR_M = 5.0              # a fix this far from its reference is "far"
WORSE_M = 2.0            # restart this much further from the reference than keep is "worse"
E1_RATE = (1.0, 3.0)     # E1: gaps per hour, around frodo-gps-v4's 1.8
E1_MIN = 60              # and at least this many scored first fixes and baseline fixes
D1_RATIO_MAX = 1.5       # D1: median first-fix miss over median ordinary miss at most this
D1_FAR_MAX = 0.05        # and at most this share of first fixes far
D2_MIN = 20              # D2: at least this many scored gaps the wheels drove through,
D2_WORSE_MAX = 0.10      # restart's median miss below keep's, and at most this share worse


# --- The two filters ---------------------------------------------------------

class RestartGpsFilter(rp.GpsFilter):
    """rover_pilot's GpsFilter, except that the first new fix it accepts after
    a gap longer than max_age_s starts the average again from that fix. Which
    readings are accepted is unchanged."""

    def __init__(self, **kw):
        super().__init__(**kw)
        self.pending = False

    def update(self, lat, lon, t):
        if self.fix_t is not None and t - self.fix_t > self.max_age_s:
            self.pending = True
        got = super().update(lat, lon, t)
        if got is not None and self.pending:
            self.lat, self.lon = got
            self.pending = False
        return got


# --- Helpers -----------------------------------------------------------------

def pct(values, q):
    s = sorted(values)
    if not s:
        return None
    return s[int(round(q / 100.0 * (len(s) - 1)))]


def _r(x, nd=3):
    return None if x is None else round(x, nd)


def share(values, ok):
    return _r(sum(1 for v in values if ok(v)) / len(values), 4) if values else None


def new_positions(track):
    """The rows of track [(t, east, north)] whose position differs from the row before."""
    out = []
    for p in track:
        if not out or p[1] != out[-1][1] or p[2] != out[-1][2]:
            out.append(p)
    return out


def ref_at(changes, ctimes, row_times, t):
    """(east, north) where a constant-velocity line through the new positions
    REF_FROM_S to REF_TO_S after t puts the rover at t; None if there are fewer
    than REF_MIN_PTS of them, they span less than REF_MIN_SPAN_S, or the log
    has a gap over GAP_S between t and t + REF_TO_S."""
    i = bisect.bisect_right(ctimes, t + REF_FROM_S)
    j = bisect.bisect_right(ctimes, t + REF_TO_S)
    pts = changes[i:j]
    if len(pts) < REF_MIN_PTS or pts[-1][0] - pts[0][0] < REF_MIN_SPAN_S:
        return None
    rows = row_times[bisect.bisect_left(row_times, t):bisect.bisect_right(row_times, t + REF_TO_S)]
    if any(b - a > GAP_S for a, b in zip(rows, rows[1:])):
        return None
    tm = sum(p[0] for p in pts) / len(pts)
    stt = sum((p[0] - tm) ** 2 for p in pts)
    out = []
    for k in (1, 2):
        m = sum(p[k] for p in pts) / len(pts)
        slope = sum((p[0] - tm) * (p[k] - m) for p in pts) / stt
        out.append(m + slope * (t - tm))
    return out[0], out[1]


def drove_m(rpm, a, b):
    """Metres the wheels drove between GPS times a and b (GPS_LAG_S earlier
    on the wheels' clock), or None without wheel data."""
    m = rpm.mean(a - GPS_LAG_S, b - GPS_LAG_S)
    return None if m is None else m * MPS_PER_RPM * (b - a)


# --- One ride ----------------------------------------------------------------

def new_pool():
    return {"rides": [], "gps_s": 0.0, "gaps": []}


def analyse_ride(control, gps, pool, no=0):
    """Replay keep and restart over one ride's GPS; its first fixes after gaps
    and its baseline fixes are added to pool."""
    st = {"control_rows": len(control), "gps_rows": len(gps)}
    if len(control) < 50 or len(gps) < 20:
        st["skipped"] = "too little data"
        return st
    lat0, lon0 = gps[0][1], gps[0][2]

    def enu(lat, lon):
        return fm.to_enu(lat0, lon0, lat, lon)

    def miss(p, ref):
        return _r(math.hypot(p[0] - ref[0], p[1] - ref[1]))

    track = [(t,) + enu(la, lo) for t, la, lo in gps]
    row_t = [p[0] for p in track]
    changes = new_positions(track)
    ctimes = [p[0] for p in changes]
    full = [r for r in control if all(v is not None for v in r[3])]
    rpm = fm.Series([r[0] for r in full], [sum(abs(v) for v in r[3]) / 4.0 for r in full])
    keep, restart = rp.GpsFilter(), RestartGpsFilter()
    events, base, gaps = [], [], []
    gap = None          # the gap not yet closed by a new fix
    last_gap_t = None   # the reading that last found a gap
    eligible = 0
    for t, la, lo in gps:
        if keep.fix_t is not None and t - keep.fix_t > GAP_S:
            gaps.append(t - keep.fix_t)
            if gap is None:
                gap = {"start": keep.fix_t, "gap_s": 0.0, "raw": keep.raw}
            gap["gap_s"] = max(gap["gap_s"], t - keep.fix_t)
            last_gap_t = t
        got = keep.update(la, lo, t)
        restart.update(la, lo, t)
        if got is None:
            continue
        p = enu(got[0], got[1])
        if gap is not None:
            ev = {"no": no, "t": round(t - row_t[0], 1), "gap_s": round(gap["gap_s"], 1),
                  "since_s": round(t - gap["start"], 1)}
            d = drove_m(rpm, gap["start"], t)
            ev["drove_m"] = _r(d, 2)
            if gap["raw"] is not None:
                q = enu(gap["raw"][0], gap["raw"][1])
                ev["jump_m"] = _r(math.hypot(p[0] - q[0], p[1] - q[1]), 2)
            ref = ref_at(changes, ctimes, row_t, t)
            if ref is not None:
                ev["r_first_m"] = miss(p, ref)
                ev["keep_m"] = miss(enu(keep.lat, keep.lon), ref)
                ev["restart_m"] = miss(enu(restart.lat, restart.lon), ref)
            events.append(ev)
            gap = None
            continue
        if t - row_t[0] < BASE_CLEAN_S or (last_gap_t is not None and t - last_gap_t < BASE_CLEAN_S):
            continue
        eligible += 1
        if eligible % BASE_EVERY:
            continue
        ref = ref_at(changes, ctimes, row_t, t)
        if ref is not None:
            base.append({"r_m": miss(p, ref), "keep_m": miss(enu(keep.lat, keep.lon), ref)})
    span = row_t[-1] - row_t[0]
    st.update(gps_span_s=round(span, 1), gaps=len(gaps), first_fixes=len(events),
              first_fixes_scored=sum(1 for e in events if "r_first_m" in e), baseline=len(base))
    pool["rides"].append({"no": no, "events": events, "base": base})
    pool["gps_s"] += span
    pool["gaps"].extend(gaps)
    return st


# --- Summary -----------------------------------------------------------------

def ratio_ci(rides, reps=200, seed=1):
    """95% interval, resampling rides, of median first-fix miss over median
    baseline miss."""
    if len(rides) < 2:
        return None
    rng = random.Random(seed)
    vals = []
    for _ in range(reps):
        sample = [rides[rng.randrange(len(rides))] for _ in rides]
        f = [e["r_first_m"] for r in sample for e in r["events"] if "r_first_m" in e]
        mb = pct([b["r_m"] for r in sample for b in r["base"]], 50)
        if f and mb:
            vals.append(pct(f, 50) / mb)
    return [_r(pct(vals, 2.5)), _r(pct(vals, 97.5))] if vals else None


def compare(events):
    keep = [e["keep_m"] for e in events]
    rest = [e["restart_m"] for e in events]
    diff = [e["restart_m"] - e["keep_m"] for e in events]
    return {"n": len(events), "median_keep_m": pct(keep, 50), "median_restart_m": pct(rest, 50),
            "p90_keep_m": pct(keep, 90), "p90_restart_m": pct(rest, 90),
            "share_restart_worse": share(diff, lambda x: x > WORSE_M),
            "share_restart_better": share(diff, lambda x: x < -WORSE_M)}


def decide(s):
    """The rules stated in PREDICTION.md before the run."""
    g, f, b, d = s["gaps"], s["first"], s["base"], s["drove"]
    chk = {"gaps_per_hour": g["per_hour"], "first_scored": f["n"], "base": b["n"]}
    out = {"check": chk}
    if g["per_hour"] is None or not E1_RATE[0] <= g["per_hour"] <= E1_RATE[1]:
        chk.update(ok=False, why="gaps per hour outside %s" % list(E1_RATE))
        return out
    if f["n"] < E1_MIN or b["n"] < E1_MIN:
        chk.update(ok=False, why="fewer than %d scored first fixes or baseline fixes" % E1_MIN)
        return out
    chk["ok"] = True
    ratio = s["ratio_median"]
    out["d1_first_fix_ok"] = (ratio is not None and ratio <= D1_RATIO_MAX + 1e-9
                              and f["share_far"] is not None and f["share_far"] <= D1_FAR_MAX + 1e-9)
    out["d2_restart_helps"] = (d["n"] >= D2_MIN and d["median_restart_m"] < d["median_keep_m"]
                               and d["share_restart_worse"] <= D2_WORSE_MAX + 1e-9)
    if not out["d1_first_fix_ok"]:
        out["verdict"] = ("the first fix after a gap is worse than an ordinary fix, so a restart "
                          "should wait for a second fix that agrees with it")
    elif out["d2_restart_helps"]:
        out["verdict"] = ("the recorded GPS backs a restart: the first fix after a gap is about as "
                          "good as an ordinary fix, and restarting from it lands nearer the "
                          "reference than keeping the average")
    else:
        out["verdict"] = ("the first fix after a gap is about as good as an ordinary fix, but "
                          "restarting from it does not land nearer the reference on recorded rides")
    return out


def summarise(pool, final=True):
    rides = pool["rides"]
    ev = [e for r in rides for e in r["events"]]
    base = [x for r in rides for x in r["base"]]
    scored = [e for e in ev if "r_first_m" in e]
    hours = pool["gps_s"] / 3600.0
    known = [e for e in ev if e.get("drove_m") is not None]
    drove = [e for e in scored if e.get("drove_m") is not None and e["drove_m"] >= DROVE_M]
    still = [e for e in scored if e.get("drove_m") is not None and e["drove_m"] < DROVE_M]
    gl = pool["gaps"]
    first = [e["r_first_m"] for e in scored]
    bm = [x["r_m"] for x in base]
    mb, mf = pct(bm, 50), pct(first, 50)
    return {
        "rides": len(rides), "gps_hours": _r(hours, 2),
        "gaps": {"n": len(gl), "per_hour": _r(len(gl) / hours, 2) if hours else None,
                 "median_s": _r(pct(gl, 50), 1), "p90_s": _r(pct(gl, 90), 1),
                 "first_fixes": len(ev),
                 "share_drove": share([e["drove_m"] for e in known], lambda x: x >= DROVE_M),
                 "median_jump_m": pct([e["jump_m"] for e in ev if "jump_m" in e], 50)},
        "first": {"n": len(first), "median_m": mf, "p90_m": pct(first, 90),
                  "share_far": share(first, lambda x: x > FAR_M)},
        "base": {"n": len(bm), "median_m": mb, "p90_m": pct(bm, 90),
                 "share_far": share(bm, lambda x: x > FAR_M),
                 "median_keep_m": pct([x["keep_m"] for x in base], 50),
                 "p90_keep_m": pct([x["keep_m"] for x in base], 90)},
        "ratio_median": _r(mf / mb) if mf is not None and mb else None,
        "ratio_ci95": ratio_ci(rides) if final else None,
        "drove": compare(drove), "still": compare(still),
    }


def conclusions(s, d):
    g, f, b = s["gaps"], s["first"], s["base"]
    if not s["rides"]:
        return []
    lines = ["%d rides, %.1f hours of GPS. The pilot's filter lost its fix (no reading for over "
             "%g s) %d times, %s an hour (median gap %s s, 90th percentile %s s); the wheels "
             "drove %g m or more through %s of the gaps that a new fix ended."
             % (s["rides"], s["gps_hours"] or 0.0, GAP_S, g["n"], g["per_hour"], g["median_s"],
                g["p90_s"], DROVE_M, g["share_drove"])]
    if f["n"] and b["n"]:
        lines.append("First new fix after a gap (%d scored): median %s m from its reference, 90th "
                     "percentile %s m, %s over %g m. Ordinary fixes (%d): median %s m, 90th "
                     "percentile %s m, %s over %g m. Ratio of medians %s (95%% CI %s)."
                     % (f["n"], f["median_m"], f["p90_m"], f["share_far"], FAR_M, b["n"],
                        b["median_m"], b["p90_m"], b["share_far"], FAR_M, s["ratio_median"],
                        s["ratio_ci95"]))
        lines.append("On ordinary fixes the shipped average sits a median %s m from the reference "
                     "(90th percentile %s m)." % (b["median_keep_m"], b["p90_keep_m"]))
    for name, label in (("drove", "Gaps the wheels drove through"), ("still", "Gaps the rover stood through")):
        c = s[name]
        if c["n"]:
            lines.append("%s (%d): keep a median %s m from the reference, restart %s m (90th "
                         "percentiles %s and %s m); restart over %g m worse in %s, over %g m "
                         "better in %s." % (label, c["n"], c["median_keep_m"], c["median_restart_m"],
                                           c["p90_keep_m"], c["p90_restart_m"], WORSE_M,
                                           c["share_restart_worse"], WORSE_M,
                                           c["share_restart_better"]))
    c = d["check"]
    if not c["ok"]:
        lines.append("Check E1 (stated before the run) failed: %s. Nothing is decided." % c["why"])
        return lines
    lines.append("D1 (stated before the run; ratio <= %s and share over %g m <= %s): %s. D2 "
                 "(restart's median below keep's on gaps driven through, share worse <= %s): %s."
                 % (D1_RATIO_MAX, FAR_M, D1_FAR_MAX, "met" if d["d1_first_fix_ok"] else "not met",
                    D2_WORSE_MAX, "met" if d["d2_restart_helps"] else "not met"))
    lines.append("Verdict: " + d["verdict"] + ".")
    return lines


def write_outputs(out_dir, parts, rides, pool, started, final=True, fetched=None):
    s = summarise(pool, final)
    d = decide(s)
    lines = conclusions(s, d)
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
              "settings": {"gap_s": GAP_S, "gps_lag_s": GPS_LAG_S, "mps_per_rpm": MPS_PER_RPM,
                           "drove_m": DROVE_M, "ref_s": [REF_FROM_S, REF_TO_S],
                           "ref_min_pts": REF_MIN_PTS, "ref_min_span_s": REF_MIN_SPAN_S,
                           "base_every": BASE_EVERY, "base_clean_s": BASE_CLEAN_S, "far_m": FAR_M,
                           "worse_m": WORSE_M, "e1_rate": list(E1_RATE), "e1_min": E1_MIN,
                           "d1_ratio_max": D1_RATIO_MAX, "d1_far_max": D1_FAR_MAX,
                           "d2_min": D2_MIN, "d2_worse_max": D2_WORSE_MAX,
                           "rover_pilot": rp.__version__, "frodo_motion": fm.__version__},
              "fetched": fetched, "conclusions": lines, "results": s, "decision": d}
    with open(os.path.join(out_dir, "summary.json"), "w") as f:
        json.dump(result, f, indent=1)
    with open(os.path.join(out_dir, "rides.jsonl"), "w") as f:
        for r in rides:
            f.write(json.dumps(r) + "\n")
    with open(os.path.join(out_dir, "events.jsonl"), "w") as f:
        for r in pool["rides"]:
            for e in r["events"]:
                f.write(json.dumps(e) + "\n")
    md = ["# The first GPS fix after a gap, on recorded Earth Rover rides (FrodoBots-2K)", "",
          "Generated by frodo_regap.py %s (earth-rover-pilot, MV2 of Munim, Inc.) with "
          "rover_pilot %s's GpsFilter. Data: FrodoBots-2K by FrodoBots Lab, CC BY-SA 4.0."
          % (__version__, rp.__version__), "",
          "Rides sampled: %d, analysed: %d, errors: %d, skipped: %s. Downloaded: %.1f MB."
          % (result["rides_sampled"], result["rides_analysed"], result["ride_errors"], skipped,
             result["bytes_read"] / 1e6), "", "## Findings", ""]
    md += ["- " + line for line in lines] or ["- Nothing to report."]
    with open(os.path.join(out_dir, "report.md"), "w") as f:
        f.write("\n".join(md) + "\n")
    return result


# --- Parts -------------------------------------------------------------------

def process_part(rz, label, rides_per_part, pool, rides_out):
    rides = fm.group_rides(rz.entries(lambda name: name.lower().endswith(".csv")))
    usable = sorted(r for r, d in rides.items() if "control_data" in d and "gps_data" in d)
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
            ch, cr = fm.parse_csv(rz.read(d["control_data"]))
            gh, gr = fm.parse_csv(rz.read(d["gps_data"]))
            st.update(analyse_ride(fm.load_control(ch, cr), fm.load_gps(gh, gr), pool, no))
        except Exception as exc:
            st["error"] = "%s: %s" % (type(exc).__name__, exc)
        rides_out.append(st)
    info["bytes_read"] = rz.bytes_read
    return info


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--index-url", default=fm.INDEX_URL)
    ap.add_argument("--parts", default="all", help="comma-separated part numbers, or all")
    ap.add_argument("--rides-per-part", type=int, default=60)
    ap.add_argument("--budget-min", type=float, default=150.0)
    ap.add_argument("--max-cd-mb", type=float, default=800.0)
    ap.add_argument("--fetched", default="fetched.json", help="fetch_deps.py's record, if any")
    ap.add_argument("--out-dir", default="out")
    args = ap.parse_args(argv)
    os.makedirs(args.out_dir, exist_ok=True)
    fetched = None
    if os.path.exists(args.fetched):
        with open(args.fetched) as f:
            fetched = json.load(f)
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
        write_outputs(args.out_dir, parts, rides, pool, started, final=False, fetched=fetched)
    result = write_outputs(args.out_dir, parts, rides, pool, started, final=True, fetched=fetched)
    print("\n".join(result["conclusions"]) or "no conclusions", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
