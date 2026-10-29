#!/usr/bin/env python3
"""frodo_spin: how far a real Earth Rover turns for an in-place turn held T seconds.

RoboColosseum's Earth Rover bridge answers each observation, every 2 to 3 s,
with the command current at that instant and holds it until the next answer
(colosseum-policy-server, GeNIE baseline, merged 2026-10-29). Its README says
each answered in-place turn rotates the rover roughly 45 degrees. A pilot that
steers through such a bridge needs to know how far a held turn command really
turns the rover, including the time it takes to start and the coast after it.

earth-rover-pilot's figure for this (about 28 deg/s per unit of angular while
spinning in place, frodo_motion 0.2.0) comes from the gyroscope, read as deg/s
counter-clockwise, although frodo_motion's own units check against the GPS
course was inconclusive (-0.14). This study measures the turn without the
gyroscope: on FrodoBots-2K's recorded rides it finds in-place turns made from
rest and ended at rest (no forward drive and no turn command for PRE_S before
and POST_S after), and reads the calibrated compass (frame yz+ about the
ride's hard-iron centre, frodo_compass_live) once before the turn starts and
once after it has settled. Then:

- turn = g x |angular| x T + c, fitted by least squares (g in deg/s per unit,
  c the start-up and coast in deg), with a 95% interval resampling rides;
- the turn and the turn per unit per second for holds of 0.3-1, 1-2, 2-3 and
  3-5 s, so the cost of short pulses shows;
- the gyroscope's steady reading during the same turns against g, which
  checks whether it reads deg/s.

The rules for reading the result are in studies/frodo-spin/PREDICTION.md,
written before the run.

    python frodo_spin.py --out-dir out --rides-per-part 30

Needs frodo_motion.py (earth-rover-pilot v0.8.0), frodo_compass.py and
frodo_compass_live.py (0.1.0) next to it. Standard library only.
By MV2 of Munim, Inc.; written with AI agents. Apache-2.0.
"""

from __future__ import annotations

import argparse
import bisect
import json
import os
import random
import statistics
import sys
import time

import frodo_compass as fc
import frodo_compass_live as fl
import frodo_motion as fm

__version__ = "0.1.0"

STILL_LIN = 0.05      # |linear| below this: the wheels are not driving
SPIN_ANG = 0.3        # |angular| at least this: an in-place turn command
QUIET_ANG = 0.1       # |angular| below this: no turn command
ROW_GAP_S = 0.5       # control rows further apart than this break a span
MIN_ROWS = 3          # a quiet span needs at least this many rows
PRE_S = 1.5           # still and not turning for this long before the turn,
POST_S = 2.5          # and for this long after it
START_TOL_S = 0.2     # the heading before: the last compass sample up to this long after the start
SETTLE_S = 1.0        # the heading after: the first compass sample this long after the end
T_MIN, T_MAX = 0.3, 5.0
BACK_DEG = 60.0       # a turn read as more than 360 less this went the other way
SIGN_MIN_DEG = 10.0   # turns at least this big count in the sign check
GYRO_FROM_S = 0.8     # gyroscope samples from this long after the start count as steady
BINS = ((0.3, 1.0), (1.0, 2.0), (2.0, 3.0), (3.0, 5.0))
FULL_A = 0.8          # "full" turn commands: |angular| at least this
BIN_MIN = 10          # a bin needs this many turns for its median to count
E1_TURNS, E1_RIDES, E1_SIGN = 100, 40, 0.85
GYRO_RATIO = (0.75, 1.33)  # D1: gyroscope gain / compass gain inside this reads deg/s
PULSE_RATIO = 0.5     # D2: 0.3-1 s holds turn less than this share of 2-3 s holds' rate
MINIPLUS_GAIN = 48.0  # deg/s per unit the pilot assumes for a Mini+ (P7)


# --- Finding turns ---------------------------------------------------------

def spinning(r):
    return abs(r[1]) < STILL_LIN and abs(r[2]) >= SPIN_ANG


def quiet(r):
    return abs(r[1]) < STILL_LIN and abs(r[2]) < QUIET_ANG


def runs(control):
    """[(i, j)]: maximal runs control[i:j] of in-place turn rows of one sign,
    no two of them further apart than ROW_GAP_S."""
    out, i, n = [], 0, len(control)
    while i < n:
        if not spinning(control[i]):
            i += 1
            continue
        left = control[i][2] > 0
        j = i + 1
        while (j < n and spinning(control[j]) and (control[j][2] > 0) == left
               and control[j][0] - control[j - 1][0] <= ROW_GAP_S):
            j += 1
        out.append((i, j))
        i = j
    return out


def quiet_span(control, ts, t_a, t_b):
    """Whether the rows in [t_a, t_b] are all quiet, at least MIN_ROWS of them,
    with no gap over ROW_GAP_S between them or at either end."""
    i = bisect.bisect_left(ts, t_a)
    j = bisect.bisect_right(ts, t_b)
    rows = control[i:j]
    if len(rows) < MIN_ROWS:
        return False
    if rows[0][0] - t_a > ROW_GAP_S or t_b - rows[-1][0] > ROW_GAP_S:
        return False
    for k, r in enumerate(rows):
        if not quiet(r) or (k and r[0] - rows[k - 1][0] > ROW_GAP_S):
            return False
    return True


def find_turns(control):
    """[{t_on, t_off, dur_s, a}]: in-place turns of T_MIN to T_MAX s that start
    and end at rest. t_off is the first row after the turn; a is the mean
    angular of its rows."""
    ts = [r[0] for r in control]
    out = []
    for i, j in runs(control):
        if j >= len(ts) or ts[j] - ts[j - 1] > ROW_GAP_S:
            continue
        t_on, t_off = ts[i], ts[j]
        dur = t_off - t_on
        if not T_MIN <= dur <= T_MAX:
            continue
        if not quiet_span(control, ts, t_on - PRE_S, t_on - 1e-6):
            continue
        if not quiet_span(control, ts, t_off, t_off + POST_S):
            continue
        a = sum(r[2] for r in control[i:j]) / (j - i)
        out.append({"t_on": t_on, "t_off": t_off, "dur_s": dur, "a": a})
    return out


# --- Measuring them --------------------------------------------------------

def signed_turn(h0, h1, a):
    """The turn (deg) from compass heading h0 to h1 (headings run clockwise) in
    the direction commanded: a positive angular turns the rover left, counter-
    clockwise. In (-BACK_DEG, 360 - BACK_DEG]; negative went the other way."""
    ccw = (h0 - h1) % 360.0
    th = ccw if a > 0 else (360.0 - ccw) % 360.0
    return th - 360.0 if th > 360.0 - BACK_DEG else th


def turn_of(compass, ct, centre, turn):
    """(turn deg, heading before, heading after), or None without a compass
    sample before the start (within PRE_S) or after it settled (within POST_S)."""
    t_on, t_off = turn["t_on"], turn["t_off"]
    j0 = bisect.bisect_right(ct, t_on + START_TOL_S) - 1
    if j0 < 0 or ct[j0] < t_on - PRE_S:
        return None
    j1 = bisect.bisect_left(ct, t_off + SETTLE_S)
    if j1 >= len(ct) or ct[j1] > t_off + POST_S:
        return None
    h0 = fl.heading_of(compass[j0], centre)
    h1 = fl.heading_of(compass[j1], centre)
    return signed_turn(h0, h1, turn["a"]), h0, h1


def gyro_rate(gyro, gt, bias, turn):
    """Mean gyroscope x (less bias) from GYRO_FROM_S after the start to the end,
    in the commanded direction (positive x is counter-clockwise), or None."""
    k0 = bisect.bisect_left(gt, turn["t_on"] + GYRO_FROM_S)
    k1 = bisect.bisect_right(gt, turn["t_off"])
    xs = [gyro[k][1] - bias for k in range(k0, k1)]
    if not xs:
        return None
    m = sum(xs) / len(xs)
    return m if turn["a"] > 0 else -m


def new_pool():
    return {"rides": []}


def analyse_ride(control, gyro, compass, pool, no=0):
    """The ride's measured in-place turns, added to pool."""
    st = {"control_rows": len(control), "compass_samples": len(compass or [])}
    if len(control) < 50:
        st["skipped"] = "too little data"
        return st
    turns = find_turns(control)
    st["turns_found"] = len(turns)
    if not turns:
        st["skipped"] = "no in-place turn from rest"
        return st
    if not compass or len(compass) < 20:
        st["skipped"] = "no compass"
        return st
    info, centre = fc.calibrate(compass, fl.A, fl.B)
    st["calibration"] = {k: info.get(k) for k in ("cover", "rms", "radius")}
    if not info["ok"]:
        st["skipped"] = "compass does not calibrate"
        return st
    ct = [c[0] for c in compass]
    gt = [g[0] for g in gyro or []]
    bias = statistics.median([g[1] for g in gyro]) if gyro and len(gyro) >= 20 else None
    events = []
    for turn in turns:
        got = turn_of(compass, ct, centre, turn)
        if got is None:
            continue
        e = {"no": no, "t": round(turn["t_on"] - control[0][0], 1),
             "dur_s": round(turn["dur_s"], 2), "a": round(turn["a"], 3),
             "turn_deg": round(got[0], 1)}
        if bias is not None:
            g = gyro_rate(gyro, gt, bias, turn)
            if g is not None:
                e["gyro_dps"] = round(g, 2)
        events.append(e)
    st["turns"] = len(events)
    pool["rides"].append({"no": no, "events": events})
    return st


# --- Summary ---------------------------------------------------------------

def fit(events):
    """(g, c): least squares turn_deg = g * |a| * dur_s + c, or (None, None)."""
    xs = [abs(e["a"]) * e["dur_s"] for e in events]
    ys = [e["turn_deg"] for e in events]
    if len(xs) < 3:
        return None, None
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    if sxx <= 0:
        return None, None
    g = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
    return g, my - g * mx


def gyro_gain(events):
    """Least squares through the origin of the steady gyroscope rate on |a|."""
    pairs = [(abs(e["a"]), e["gyro_dps"]) for e in events if "gyro_dps" in e]
    sxx = sum(x * x for x, _ in pairs)
    return (sum(x * y for x, y in pairs) / sxx if sxx > 0 else None), len(pairs)


def sign_share(events):
    big = [e["turn_deg"] for e in events if abs(e["turn_deg"]) >= SIGN_MIN_DEG]
    return fc._r(sum(1 for x in big if x > 0) / len(big)) if big else None


def in_bin(e, lo, hi):
    return lo <= e["dur_s"] < hi or (hi == BINS[-1][1] and e["dur_s"] == hi)


def bin_rows(events):
    rows = []
    for lo, hi in BINS:
        sel = [e for e in events if in_bin(e, lo, hi)]
        th = [e["turn_deg"] for e in sel]
        rate = [e["turn_deg"] / (abs(e["a"]) * e["dur_s"]) for e in sel]
        full = [e["turn_deg"] for e in sel if abs(e["a"]) >= FULL_A]
        rows.append({"dur_s": [lo, hi], "n": len(sel), "median_deg": fc.pct(th, 50),
                     "p10_deg": fc.pct(th, 10), "p90_deg": fc.pct(th, 90),
                     "median_rate": fc._r(fc.pct(rate, 50), 2),
                     "full_n": len(full), "full_median_deg": fc.pct(full, 50)})
    return rows


def boot(rides, reps=200, seed=1):
    """95% interval of g, resampling rides with turns."""
    rides = [r for r in rides if r["events"]]
    if len(rides) < 2:
        return None
    rng = random.Random(seed)
    gs = []
    for _ in range(reps):
        sample = [rides[rng.randrange(len(rides))] for _ in rides]
        g, _ = fit([e for r in sample for e in r["events"]])
        if g is not None:
            gs.append(g)
    return [fc._r(fc.pct(gs, 2.5), 2), fc._r(fc.pct(gs, 97.5), 2)] if gs else None


def summarise(pool, final=True):
    rides = pool["rides"]
    ev = [e for r in rides for e in r["events"]]
    g, c = fit(ev)
    gg, gn = gyro_gain(ev)
    return {"rides": len(rides), "rides_with_turns": sum(1 for r in rides if r["events"]),
            "turns": len(ev), "median_dur_s": fc.pct([e["dur_s"] for e in ev], 50),
            "median_abs_a": fc.pct([abs(e["a"]) for e in ev], 50),
            "gain": fc._r(g, 2), "offset_deg": fc._r(c, 2),
            "gain_ci95": boot(rides) if final else None,
            "sign_share": sign_share(ev), "bins": bin_rows(ev),
            "gyro_gain": fc._r(gg, 2), "gyro_n": gn,
            "gyro_over_gain": fc._r(gg / g) if gg is not None and g else None,
            "held_2_5s_full_deg": fc._r(g * 2.5 + c, 1) if g is not None else None,
            "held_2_5s_half_deg": fc._r(g * 0.5 * 2.5 + c, 1) if g is not None else None}


def decide(s):
    """The rules stated in PREDICTION.md before the run."""
    chk = {"turns": s["turns"], "rides_with_turns": s["rides_with_turns"],
           "sign_share": s["sign_share"]}
    out = {"check": chk}
    if s["turns"] < E1_TURNS or s["rides_with_turns"] < E1_RIDES:
        chk.update(ok=False, why="fewer than %d turns or %d rides" % (E1_TURNS, E1_RIDES))
        return out
    if s["sign_share"] is None or s["sign_share"] < E1_SIGN:
        chk.update(ok=False, why="sign share below %s" % E1_SIGN)
        return out
    if s["gain"] is None or s["gain"] <= 0:
        chk.update(ok=False, why="no positive gain")
        return out
    chk["ok"] = True
    r = s["gyro_over_gain"]
    out["d1_gyro_reads_dps"] = r is not None and GYRO_RATIO[0] <= r <= GYRO_RATIO[1]
    short, mid = s["bins"][0], s["bins"][2]
    if short["n"] >= BIN_MIN and mid["n"] >= BIN_MIN and mid["median_rate"]:
        out["d2_pulses_cost"] = short["median_rate"] < PULSE_RATIO * mid["median_rate"]
    else:
        out["d2_pulses_cost"] = None
    return out


def conclusions(s, d):
    if not s["turns"]:
        return []
    lines = ["%d in-place turns from rest to rest on %d rides (median hold %s s, median "
             "|angular| %s). Least squares: turn = %s deg/s x |angular| x seconds %+.1f deg "
             "(95%% CI of the gain, rides resampled: %s). Turned the commanded way in %s of "
             "turns of %g deg or more."
             % (s["turns"], s["rides_with_turns"], s["median_dur_s"], s["median_abs_a"],
                s["gain"], s["offset_deg"] or 0.0, s["gain_ci95"], s["sign_share"],
                SIGN_MIN_DEG)]
    for b in s["bins"]:
        if b["n"]:
            lines.append("Held %g-%g s (%d): median turn %s deg (10th-90th percentile %s-%s), "
                         "%s deg/s per unit; with |angular| >= %g (%d): median %s deg."
                         % (b["dur_s"][0], b["dur_s"][1], b["n"], b["median_deg"], b["p10_deg"],
                            b["p90_deg"], b["median_rate"], FULL_A, b["full_n"],
                            b["full_median_deg"]))
    if s["held_2_5s_full_deg"] is not None:
        lines.append("By the fit, a turn command held 2.5 s (one RoboColosseum observation) "
                     "turns the rover %s deg at angular 1 and %s deg at 0.5."
                     % (s["held_2_5s_full_deg"], s["held_2_5s_half_deg"]))
    lines.append("Gyroscope x during the same turns (%d): %s units per unit of angular, %s times "
                 "the compass gain." % (s["gyro_n"], s["gyro_gain"], s["gyro_over_gain"]))
    k = d["check"]
    if not k["ok"]:
        lines.append("Check E1 (stated before the run) failed: %s. Nothing is decided." % k["why"])
        return lines
    lines.append("D1: the gyroscope %s deg/s (gyro / compass gain %s, needs %s to %s)."
                 % ("reads" if d["d1_gyro_reads_dps"] else "does not read", s["gyro_over_gain"],
                    GYRO_RATIO[0], GYRO_RATIO[1]))
    lines.append("D2: short pulses %s (0.3-1 s holds below %s of the 2-3 s holds' rate per "
                 "unit)." % ({True: "cost turn", False: "do not cost much turn",
                              None: "not decided (too few turns)"}[d["d2_pulses_cost"]],
                             PULSE_RATIO))
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
              "settings": {"still_lin": STILL_LIN, "spin_ang": SPIN_ANG, "quiet_ang": QUIET_ANG,
                           "row_gap_s": ROW_GAP_S, "pre_s": PRE_S, "post_s": POST_S,
                           "start_tol_s": START_TOL_S, "settle_s": SETTLE_S,
                           "t_range": [T_MIN, T_MAX], "back_deg": BACK_DEG,
                           "gyro_from_s": GYRO_FROM_S, "full_a": FULL_A, "bin_min": BIN_MIN,
                           "e1": [E1_TURNS, E1_RIDES, E1_SIGN], "gyro_ratio": list(GYRO_RATIO),
                           "pulse_ratio": PULSE_RATIO, "frame": fl.FRAME,
                           "frodo_motion": fm.__version__, "frodo_compass": fc.__version__,
                           "frodo_compass_live": fl.__version__},
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
    md = ["# How far a real Earth Rover turns for an in-place turn held T seconds (FrodoBots-2K)",
          "", "Generated by frodo_spin.py %s (earth-rover-pilot, MV2 of Munim, Inc.). Data: "
          "FrodoBots-2K by FrodoBots Lab, CC BY-SA 4.0." % __version__, "",
          "Rides sampled: %d, analysed: %d, errors: %d, skipped: %s. Downloaded: %.1f MB."
          % (result["rides_sampled"], result["rides_analysed"], result["ride_errors"], skipped,
             result["bytes_read"] / 1e6), "", "## Findings", ""]
    md += ["- " + line for line in lines] or ["- Nothing to report."]
    with open(os.path.join(out_dir, "report.md"), "w") as f:
        f.write("\n".join(md) + "\n")
    return result


# --- Parts -----------------------------------------------------------------

def process_part(rz, label, rides_per_part, pool, rides_out, imu_max_mb=30.0):
    rides = fm.group_rides(rz.entries(lambda name: name.lower().endswith(".csv")))
    usable = sorted(r for r, d in rides.items() if "control_data" in d and "imu_data" in d)
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
                ch, cr = fm.parse_csv(rz.read(d["control_data"]))
                control = fm.load_control(ch, cr)
                if not find_turns(control):
                    st.update(control_rows=len(control), turns_found=0,
                              skipped="no in-place turn from rest")
                else:
                    ih, ir = fm.parse_csv(rz.read(d["imu_data"]))
                    st.update(analyse_ride(control, fm.load_imu(ih, ir, "gyroscope"),
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
    ap.add_argument("--budget-min", type=float, default=150.0)
    ap.add_argument("--max-cd-mb", type=float, default=800.0)
    ap.add_argument("--imu-max-mb", type=float, default=30.0)
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
            info = process_part(rz, label, args.rides_per_part, pool, rides, args.imu_max_mb)
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
