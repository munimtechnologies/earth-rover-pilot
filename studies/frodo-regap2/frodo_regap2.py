#!/usr/bin/env python3
"""frodo_regap2: start the GPS average again only on a second fix that agrees?

frodo-regap-v1 (studies/frodo-regap/GRADE.md) found on FrodoBots-2K's
recorded rides that the first GPS fix after a gap of more than 3 s sits a
median 1.74 times as far from its reference as an ordinary fix, with 6.7% over
5 m. By its pre-stated rule a restart on a real rover must wait for a second
fix that agrees with the first. This study measures that rule on rides
frodo-regap-v1 did not read, by replaying rover_pilot 0.19.0's GpsFilter over
each ride's GPS log three times:

- keep: the shipped filter, which blends fixes after a gap into the average;
- restart: the first new fix after a gap starts the average again
  (frodo_regap.RestartGpsFilter, pace-w's restart);
- confirm: after a gap, the first new fix that agrees with the new fix before
  it (within AGREE_M + AGREE_MPS x the time between them) starts the average
  again; until then it averages as shipped.

Each is judged at the first and at the second new fix after each gap,
against frodo_regap's reference (a constant-velocity line through the ride's
new GPS positions 1.5 to 10.5 s later). The rules for reading the result are
in studies/frodo-regap2/PREDICTION.md, written before the run.

    python frodo_regap2.py --out-dir out --rides-per-part 80 --skip-first 60

Needs frodo_motion.py (earth-rover-pilot v0.8.0), rover_pilot.py (v0.19.0) and
frodo_regap.py (studies/frodo-regap, 0.1.0) next to it. Standard library only.
By MV2 of Munim, Inc.; written with AI agents. Apache-2.0.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time

import frodo_motion as fm
import frodo_regap as fr
import rover_pilot as rp

__version__ = "0.1.0"

GAP_S = fr.GAP_S         # 3 s without a reading loses the fix
DROVE_M = fr.DROVE_M     # 2 m: a gap the wheels drove through
FAR_M = fr.FAR_M         # 5 m from the reference is "far"
WORSE_M = fr.WORSE_M     # 2 m further than keep is "worse"
AGREE_M = 2.0            # confirm: two new fixes agree within this,
AGREE_MPS = 1.5          # plus this much per second between them
SKIP_FIRST = 60          # leave out the rides frodo-regap-v1 read (60 per part)
E1_RATE = fr.E1_RATE     # E1: gaps per hour in [1.0, 3.0]
E1_MIN = fr.E1_MIN       # and at least 60 scored second fixes and baseline fixes
D1_RATIO_MAX = fr.D1_RATIO_MAX
D1_FAR_MAX = fr.D1_FAR_MAX
D3_FAR_MAX = 0.05        # D3: confirm over 5 m at the second fix in at most this share
D4_MIN = 20              # D4: at least this many scored gaps driven through,
D4_WORSE_MAX = 0.10      # confirm's median below keep's, and at most this share worse
ARMS = ("keep", "restart", "confirm")


# --- The confirm filter ------------------------------------------------------

class ConfirmGpsFilter(rp.GpsFilter):
    """rover_pilot's GpsFilter, except that after a gap longer than max_age_s
    the first new fix that agrees with the new fix before it starts the
    average again. Until then it averages as shipped. Which readings are
    accepted is unchanged."""

    def __init__(self, agree_m=AGREE_M, agree_mps=AGREE_MPS, **kw):
        super().__init__(**kw)
        self.agree_m, self.agree_mps = agree_m, agree_mps
        self.pending = False
        self.cand = None      # (lat, lon, t) of the last new fix since the gap
        self.restarts = 0

    def update(self, lat, lon, t):
        if self.fix_t is not None and t - self.fix_t > self.max_age_s:
            self.pending, self.cand = True, None
        got = super().update(lat, lon, t)
        if got is None or not self.pending:
            return got
        if self.cand is not None:
            d = rp.haversine_m(self.cand[0], self.cand[1], got[0], got[1])
            if d <= self.agree_m + self.agree_mps * (t - self.cand[2]):
                self.lat, self.lon = got
                self.pending, self.cand = False, None
                self.restarts += 1
                return got
        self.cand = (got[0], got[1], t)
        return got


# --- One ride ----------------------------------------------------------------

def new_pool():
    return fr.new_pool()


def analyse_ride(control, gps, pool, no=0):
    """Replay keep, restart and confirm over one ride's GPS; its gaps, with
    each arm's miss at the first and second new fix after them, and its
    baseline fixes are added to pool."""
    st = {"control_rows": len(control), "gps_rows": len(gps)}
    if len(control) < 50 or len(gps) < 20:
        st["skipped"] = "too little data"
        return st
    lat0, lon0 = gps[0][1], gps[0][2]

    def enu(lat, lon):
        return fm.to_enu(lat0, lon0, lat, lon)

    def miss(p, ref):
        return fr._r(math.hypot(p[0] - ref[0], p[1] - ref[1]))

    track = [(t,) + enu(la, lo) for t, la, lo in gps]
    row_t = [p[0] for p in track]
    changes = fr.new_positions(track)
    ctimes = [p[0] for p in changes]
    full = [r for r in control if all(v is not None for v in r[3])]
    rpm = fm.Series([r[0] for r in full], [sum(abs(v) for v in r[3]) / 4.0 for r in full])
    filt = {"keep": rp.GpsFilter(), "restart": fr.RestartGpsFilter(), "confirm": ConfirmGpsFilter()}
    keep, confirm = filt["keep"], filt["confirm"]
    events, base, gaps = [], [], []
    gap = None          # the gap not yet closed by a new fix
    last_gap_t = None   # the reading that last found a gap
    after = None        # (event, t) whose second new fix is still to come
    open_ev = None      # (event, t) whose confirm restart is still to come
    eligible = 0
    for t, la, lo in gps:
        if keep.fix_t is not None and t - keep.fix_t > GAP_S:
            gaps.append(t - keep.fix_t)
            if gap is None:
                gap = {"start": keep.fix_t, "gap_s": 0.0, "raw": keep.raw}
            gap["gap_s"] = max(gap["gap_s"], t - keep.fix_t)
            last_gap_t = t
            after = open_ev = None
        n_before = confirm.restarts
        got = None
        for name in ARMS:
            g = filt[name].update(la, lo, t)
            if name == "keep":
                got = g
        if got is None:
            continue
        p = enu(got[0], got[1])
        restarted = confirm.restarts > n_before
        if gap is not None:
            ev = {"no": no, "t": round(t - row_t[0], 1), "gap_s": round(gap["gap_s"], 1),
                  "since_s": round(t - gap["start"], 1)}
            d = fr.drove_m(rpm, gap["start"], t)
            ev["drove_m"] = fr._r(d, 2)
            if gap["raw"] is not None:
                q = enu(gap["raw"][0], gap["raw"][1])
                ev["jump_m"] = fr._r(math.hypot(p[0] - q[0], p[1] - q[1]), 2)
            ref = fr.ref_at(changes, ctimes, row_t, t)
            if ref is not None:
                ev["r_first_m"] = miss(p, ref)
                for name in ARMS:
                    ev[name + "_m"] = miss(enu(filt[name].lat, filt[name].lon), ref)
            events.append(ev)
            gap = None
            after = open_ev = (ev, t)
            continue
        if after is not None:
            ev, t1 = after
            ev["dt2_s"] = round(t - t1, 1)
            ev["agree"] = restarted
            ref = fr.ref_at(changes, ctimes, row_t, t)
            if ref is not None:
                ev["r_second_m"] = miss(p, ref)
                for name in ARMS:
                    ev[name + "2_m"] = miss(enu(filt[name].lat, filt[name].lon), ref)
            after = None
        if open_ev is not None and restarted:
            ev, t1 = open_ev
            ev["confirm_after_s"] = round(t - t1, 1)
            open_ev = None
        if t - row_t[0] < fr.BASE_CLEAN_S or (last_gap_t is not None and t - last_gap_t < fr.BASE_CLEAN_S):
            continue
        eligible += 1
        if eligible % fr.BASE_EVERY:
            continue
        ref = fr.ref_at(changes, ctimes, row_t, t)
        if ref is not None:
            base.append({"r_m": miss(p, ref), "keep_m": miss(enu(keep.lat, keep.lon), ref)})
    span = row_t[-1] - row_t[0]
    st.update(gps_span_s=round(span, 1), gaps=len(gaps), first_fixes=len(events),
              first_fixes_scored=sum(1 for e in events if "r_first_m" in e),
              second_fixes=sum(1 for e in events if "dt2_s" in e),
              second_fixes_scored=sum(1 for e in events if "r_second_m" in e), baseline=len(base))
    pool["rides"].append({"no": no, "events": events, "base": base})
    pool["gps_s"] += span
    pool["gaps"].extend(gaps)
    return st


# --- Summary -----------------------------------------------------------------

def compare(events):
    """Each arm's miss at the second new fix after a gap."""
    out = {"n": len(events)}
    for name in ARMS:
        v = [e[name + "2_m"] for e in events]
        out["median_%s_m" % name] = fr.pct(v, 50)
        out["p90_%s_m" % name] = fr.pct(v, 90)
        out["share_%s_far" % name] = fr.share(v, lambda x: x > FAR_M)
    for name in ("restart", "confirm"):
        out["share_%s_worse" % name] = fr.share([e[name + "2_m"] - e["keep2_m"] for e in events],
                                                lambda x: x > WORSE_M)
    return out


def summarise(pool, final=True):
    rides = pool["rides"]
    ev = [e for r in rides for e in r["events"]]
    base = [x for r in rides for x in r["base"]]
    hours = pool["gps_s"] / 3600.0
    known = [e for e in ev if e.get("drove_m") is not None]
    s1 = [e for e in ev if "r_first_m" in e]
    t2 = [e for e in ev if "dt2_s" in e]
    s2 = [e for e in ev if "r_second_m" in e]
    both = [e for e in s2 if "r_first_m" in e]
    drove = [e for e in s2 if e.get("drove_m") is not None and e["drove_m"] >= DROVE_M]
    still = [e for e in s2 if e.get("drove_m") is not None and e["drove_m"] < DROVE_M]
    far = [e for e in s1 if e["r_first_m"] > FAR_M and "dt2_s" in e]
    waits = [e["confirm_after_s"] for e in ev if "confirm_after_s" in e]
    gl = pool["gaps"]
    first = [e["r_first_m"] for e in s1]
    bm = [x["r_m"] for x in base]
    mb, mf = fr.pct(bm, 50), fr.pct(first, 50)
    return {
        "rides": len(rides), "gps_hours": fr._r(hours, 2),
        "gaps": {"n": len(gl), "per_hour": fr._r(len(gl) / hours, 2) if hours else None,
                 "median_s": fr._r(fr.pct(gl, 50), 1), "p90_s": fr._r(fr.pct(gl, 90), 1),
                 "first_fixes": len(ev),
                 "share_drove": fr.share([e["drove_m"] for e in known], lambda x: x >= DROVE_M)},
        "first": {"n": len(first), "median_m": mf, "p90_m": fr.pct(first, 90),
                  "share_far": fr.share(first, lambda x: x > FAR_M),
                  "median_keep_m": fr.pct([e["keep_m"] for e in s1], 50),
                  "median_restart_m": fr.pct([e["restart_m"] for e in s1], 50),
                  "median_confirm_m": fr.pct([e["confirm_m"] for e in s1], 50)},
        "base": {"n": len(bm), "median_m": mb, "p90_m": fr.pct(bm, 90),
                 "share_far": fr.share(bm, lambda x: x > FAR_M)},
        "ratio_median": fr._r(mf / mb) if mf is not None and mb else None,
        "ratio_ci95": fr.ratio_ci(rides) if final else None,
        "second": {"n": len(t2), "median_dt2_s": fr.pct([e["dt2_s"] for e in t2], 50),
                   "share_agree": fr.share([e["agree"] for e in t2], bool),
                   "paired": len(both),
                   "median_r_first_m": fr.pct([e["r_first_m"] for e in both], 50),
                   "median_r_second_m": fr.pct([e["r_second_m"] for e in both], 50)},
        "confirm": {"n": len(waits), "median_after_s": fr.pct(waits, 50),
                    "p90_after_s": fr.pct(waits, 90),
                    "share_within_10s": fr.share([e.get("confirm_after_s") for e in t2],
                                                 lambda x: x is not None and x <= 10.0)},
        "at2": compare(s2), "drove2": compare(drove), "still2": compare(still),
        "far_first": {"n": len(far), "share_refused": fr.share([e["agree"] for e in far], lambda a: not a)},
    }


def decide(s):
    """The rules stated in PREDICTION.md before the run."""
    g, f, b, a, d = s["gaps"], s["first"], s["base"], s["at2"], s["drove2"]
    chk = {"gaps_per_hour": g["per_hour"], "second_scored": a["n"], "base": b["n"]}
    out = {"check": chk}
    if g["per_hour"] is None or not E1_RATE[0] <= g["per_hour"] <= E1_RATE[1]:
        chk.update(ok=False, why="gaps per hour outside %s" % list(E1_RATE))
        return out
    if a["n"] < E1_MIN or b["n"] < E1_MIN:
        chk.update(ok=False, why="fewer than %d scored second fixes or baseline fixes" % E1_MIN)
        return out
    chk["ok"] = True
    ratio = s["ratio_median"]
    out["d1_fails_again"] = not (ratio is not None and ratio <= D1_RATIO_MAX + 1e-9
                                 and f["share_far"] is not None and f["share_far"] <= D1_FAR_MAX + 1e-9)
    out["d3_confirm_safe"] = (a["share_confirm_far"] <= D3_FAR_MAX + 1e-9
                              and a["share_confirm_far"] <= a["share_restart_far"] + 1e-9)
    out["d4_confirm_helps"] = (d["n"] >= D4_MIN and d["median_confirm_m"] < d["median_keep_m"]
                               and d["share_confirm_worse"] <= D4_WORSE_MAX + 1e-9)
    if out["d3_confirm_safe"] and out["d4_confirm_helps"]:
        out["verdict"] = ("a restart that waits for a second agreeing fix is safe and lands nearer "
                          "than the shipped average on recorded rides, so it earns a pre-registered "
                          "simulated trial against the shipped average")
    elif out["d4_confirm_helps"]:
        out["verdict"] = ("waiting for a second agreeing fix lands nearer on average but still leaves "
                          "too many estimates far off, so a real rover keeps the average")
    else:
        out["verdict"] = ("waiting for a second agreeing fix does not land nearer the reference than "
                          "the shipped average on recorded rides, so a real rover keeps the average")
    return out


def conclusions(s, d):
    g, f, b, c, w = s["gaps"], s["first"], s["base"], s["second"], s["confirm"]
    if not s["rides"]:
        return []
    lines = ["%d rides, %.1f hours of GPS. The pilot's filter lost its fix (no reading for over "
             "%g s) %d times, %s an hour (median gap %s s, 90th percentile %s s); the wheels "
             "drove %g m or more through %s of the gaps that a new fix ended."
             % (s["rides"], s["gps_hours"] or 0.0, GAP_S, g["n"], g["per_hour"], g["median_s"],
                g["p90_s"], DROVE_M, g["share_drove"])]
    if f["n"] and b["n"]:
        lines.append("First new fix after a gap (%d scored): median %s m from its reference, %s "
                     "over %g m. Ordinary fixes (%d): median %s m, %s over %g m. Ratio of medians "
                     "%s (95%% CI %s)." % (f["n"], f["median_m"], f["share_far"], FAR_M, b["n"],
                                          b["median_m"], b["share_far"], FAR_M, s["ratio_median"],
                                          s["ratio_ci95"]))
    if c["n"]:
        lines.append("%d gaps had a second new fix before the next gap (a median %s s after the "
                     "first); it agreed with the first in %s of them. Where both were scored (%d), "
                     "the first sat a median %s m from its reference and the second %s m. Confirm "
                     "started the average again a median %s s after the first fix (90th percentile "
                     "%s s), within 10 s in %s of these gaps."
                     % (c["n"], c["median_dt2_s"], c["share_agree"], c["paired"],
                        c["median_r_first_m"], c["median_r_second_m"], w["median_after_s"],
                        w["p90_after_s"], w["share_within_10s"]))
    for name, label in (("at2", "All gaps"), ("drove2", "Gaps the wheels drove through"),
                        ("still2", "Gaps the rover stood through")):
        a = s[name]
        if a["n"]:
            lines.append("%s, at the second fix (%d): keep a median %s m from the reference, "
                         "restart %s m, confirm %s m; over %g m: %s, %s and %s; more than %g m worse "
                         "than keep: restart %s, confirm %s."
                         % (label, a["n"], a["median_keep_m"], a["median_restart_m"],
                            a["median_confirm_m"], FAR_M, a["share_keep_far"],
                            a["share_restart_far"], a["share_confirm_far"], WORSE_M,
                            a["share_restart_worse"], a["share_confirm_worse"]))
    if s["far_first"]["n"]:
        lines.append("First fixes over %g m off with a second fix: %d; confirm refused %s of them "
                     "at the second fix." % (FAR_M, s["far_first"]["n"], s["far_first"]["share_refused"]))
    k = d["check"]
    if not k["ok"]:
        lines.append("Check E1 (stated before the run) failed: %s. Nothing is decided." % k["why"])
        return lines
    lines.append("D1 again (ratio <= %s and share over %g m <= %s): %s. D3 (confirm over %g m at "
                 "the second fix in at most %s, and no more often than restart): %s. D4 (on gaps "
                 "driven through, confirm's median below keep's and more than %g m worse in at "
                 "most %s): %s."
                 % (D1_RATIO_MAX, FAR_M, D1_FAR_MAX, "fails again" if d["d1_fails_again"] else "met",
                    FAR_M, D3_FAR_MAX, "met" if d["d3_confirm_safe"] else "not met", WORSE_M,
                    D4_WORSE_MAX, "met" if d["d4_confirm_helps"] else "not met"))
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
              "settings": {"gap_s": GAP_S, "drove_m": DROVE_M, "far_m": FAR_M, "worse_m": WORSE_M,
                           "agree_m": AGREE_M, "agree_mps": AGREE_MPS, "e1_rate": list(E1_RATE),
                           "e1_min": E1_MIN, "d1_ratio_max": D1_RATIO_MAX, "d1_far_max": D1_FAR_MAX,
                           "d3_far_max": D3_FAR_MAX, "d4_min": D4_MIN, "d4_worse_max": D4_WORSE_MAX,
                           "rover_pilot": rp.__version__, "frodo_motion": fm.__version__,
                           "frodo_regap": fr.__version__},
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
    md = ["# Restarting the GPS average on a second agreeing fix, on recorded Earth Rover rides "
          "(FrodoBots-2K)", "",
          "Generated by frodo_regap2.py %s (earth-rover-pilot, MV2 of Munim, Inc.) with "
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

def choose(usable, rides_per_part, skip_first):
    """rides_per_part rides spread evenly through those left after leaving
    out the skip_first that frodo_motion.pick_evenly would pick first."""
    done = set(fm.pick_evenly(usable, skip_first)) if skip_first > 0 else set()
    return fm.pick_evenly([r for r in usable if r not in done], rides_per_part)


def process_part(rz, label, rides_per_part, pool, rides_out, skip_first=SKIP_FIRST):
    rides = fm.group_rides(rz.entries(lambda name: name.lower().endswith(".csv")))
    usable = sorted(r for r, d in rides.items() if "control_data" in d and "gps_data" in d)
    chosen = choose(usable, rides_per_part, skip_first)
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
    ap.add_argument("--skip-first", type=int, default=SKIP_FIRST)
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
            info = process_part(rz, label, args.rides_per_part, pool, rides, args.skip_first)
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
