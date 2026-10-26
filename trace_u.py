#!/usr/bin/env python3
"""trace_u: why did the stuck check's warm-up catch seed 388's blocked rover
12 s late, and why does a 5 s warm-up move again just after the block?
(a diagnostic, not a pre-registered study)

pace_u.py's record (studies/pace-u/GRADE.md) shows, on blocked30, seed 388's
first recovery move at 26.1 s with a 5 s warm-up and 31.0 s with 10 s,
against 14.2 s and 19.1 s on the other seeds, though its GPS stayed up until
664.5 s; the shipped check fired at 9.1 s as usual. Both are 11.9 s late,
which fits one clear of the stuck history at about 11.9 s. And with a 5 s
warm-up most blocked missions moved again at 34.2 s, 4.2 s after the block.
This flies those missions again and logs every call of the stuck check up
to UNTIL_S: whether the history was cleared since the call before, when the
warm-up started, the history's length, span, mean commanded speed and how
far the GPS average moved over it, the verdict, the pilot's stop and bridge
counters and whether a new GPS fix came in. It only reads: a test checks
that a traced mission's record is the same as an untraced one's, and each
mission is compared with pace_u.py's record of it (MISSIONS).

    python trace_u.py --out-dir out

Writes calls-<profile>-<variant>-<seed>.csv (one row per stuck check),
summary.json and report.md. Simulated rovers only. Standard library only.
By MV2 of Munim, Inc.; written with AI agents. Apache-2.0.
"""

from __future__ import annotations

import argparse
import contextlib
import csv
import json
import os
import sys

import pace_t as pt
import pace_u as pu
import rover_pilot as rp

__version__ = "0.1.0"

COURSE = "boulevard"
CRUISE = 0.8
UNTIL_S = 60.0
# (profile, variant, seed) -> (elapsed_s, recovery_t) in pace_u.py's record of
# the boulevard mission (studies/pace-u/runs-<profile>.jsonl): seed 388 on
# blocked30 and on quiet90 (the same mission without the block), seed 374
# with the 5 s warm-up's move at 34.2 s, and seed 373, caught 2 s later than
# most by every variant.
MISSIONS = {
    ("blocked30", "a0.3", 388): (1801.6, [9.1, 24.2]),
    ("blocked30", "warm5", 388): (1801.6, [26.1]),
    ("blocked30", "warm10", 388): (1801.6, [31.0]),
    ("quiet90", "a0.3", 388): (1801.6, [9.1]),
    ("quiet90", "warm10", 388): (1801.6, []),
    ("blocked30", "a0.3", 374): (1827.6, [9.1, 24.2]),
    ("blocked30", "warm5", 374): (1827.6, [14.2, 34.2]),
    ("blocked30", "warm10", 374): (1827.6, [19.1]),
    ("blocked30", "warm5", 373): (1771.6, [16.2]),
}
FIELDS = ("t", "gap_s", "cleared", "warm_from", "n", "span_s", "full", "mean_lin", "slow",
          "moved_m", "verdict", "linear", "new_fix", "recoveries", "telemetry_stops",
          "tip_stops", "bridged_s")
COUNTERS = ("recoveries", "telemetry_stops", "tip_stops", "bridged_s")


def _r(x, nd=3):
    return None if x is None else round(x, nd)


def row(pilot, t, linear, cleared, verdict, last):
    """One stuck check as the pilot saw it, read after Pilot._stuck ran (and
    before a verdict's recovery move clears the history)."""
    h = pilot._history
    raw = getattr(pilot.gps, "raw", None)
    span = h[-1][0] - h[0][0] if h else None
    mean = sum(y[3] for y in h) / len(h) if h else None
    x = {"t": _r(t), "gap_s": _r(t - last["t"]) if "t" in last else None,
         "cleared": bool(cleared), "warm_from": _r(getattr(pilot, "_warm_from", None)),
         "n": len(h), "span_s": _r(span),
         "full": span is not None and span >= 0.9 * pilot.stuck_window_s,
         "mean_lin": _r(mean), "slow": mean is not None and mean < 0.4 * pilot.steering.cruise,
         "moved_m": _r(rp.haversine_m(h[0][1], h[0][2], pilot.gps.lat, pilot.gps.lon)) if h else None,
         "verdict": bool(verdict), "linear": _r(linear),
         "new_fix": raw is not None and raw != last.get("raw"),
         "recoveries": pilot.recoveries, "telemetry_stops": pilot.telemetry_stops,
         "tip_stops": pilot.tip_stops, "bridged_s": _r(pilot.bridged_s, 1)}
    last["t"], last["raw"] = t, raw
    return x


@contextlib.contextmanager
def _logging(calls, until_s=UNTIL_S):
    """While inside, pace_t._warming's stuck check also appends a row to
    `calls` for every call up to until_s; its verdicts are unchanged."""
    saved_warming = pt._warming

    @contextlib.contextmanager
    def warming(warmup_s, times):
        with saved_warming(warmup_s, times):
            inner = rp.Pilot._stuck
            last = {}

            def _stuck(self, t, linear):
                cleared = getattr(self._history, "cleared", True)
                verdict = inner(self, t, linear)
                if t <= until_s:
                    calls.append(row(self, t, linear, cleared, verdict, last))
                return verdict

            rp.Pilot._stuck = _stuck
            try:
                yield
            finally:
                rp.Pilot._stuck = inner

    pt._warming = warming
    try:
        yield
    finally:
        pt._warming = saved_warming


def fly_traced(profile, variant, seed, course_name=COURSE, cruise=CRUISE, until_s=UNTIL_S):
    """pace_u.fly's mission with its stuck-check rows; the record as
    pace_u.fly returns it."""
    calls = []
    with _logging(calls, until_s):
        r = pu.fly(course_name, seed, profile, variant, cruise)
    return r, calls


def clears(calls):
    """The calls at which the history had been cleared since the call before:
    t, the gap since that call, whether a new fix came in, and how much each
    of the pilot's counters went up meanwhile (None at the first call)."""
    out, prev = [], None
    for x in calls:
        if x["cleared"]:
            d = {"t": x["t"], "gap_s": x["gap_s"], "new_fix": x["new_fix"]}
            for k in COUNTERS:
                d[k] = None if prev is None else _r(x[k] - prev[k], 1)
            out.append(d)
        prev = x
    return out


def held(calls):
    """Calls with a full window but no verdict, as runs of consecutive such
    calls: first and last t, how many, and how many were too slow (mean
    commanded speed under 0.4 of cruise) rather than having moved."""
    out, cur = [], None
    for x in calls + [None]:
        if x is not None and x["full"] and not x["verdict"]:
            if cur is None:
                cur = {"start": x["t"], "end": x["t"], "calls": 0, "slow": 0,
                       "least_moved_m": x["moved_m"]}
            cur["end"] = x["t"]
            cur["calls"] += 1
            cur["slow"] += 1 if x["slow"] else 0
            cur["least_moved_m"] = min(cur["least_moved_m"], x["moved_m"])
        elif cur is not None:
            out.append(cur)
            cur = None
    return out


def each_second(calls, start_s=0.0, end_s=40.0):
    """The first call in each whole second from start_s to end_s."""
    out, seen = [], set()
    for x in calls:
        s = int(x["t"])
        if start_s <= x["t"] <= end_s and s not in seen:
            seen.add(s)
            out.append(x)
    return out


def _cell(v):
    return "" if v is None else ("yes" if v is True else "no" if v is False else v)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out-dir", default="out")
    ap.add_argument("--missions", help="comma-separated profile:variant:seed, default: all of "
                    "MISSIONS")
    args = ap.parse_args(argv)
    missions = list(MISSIONS)
    if args.missions:
        missions = [(p, v, int(s)) for p, v, s in (m.split(":") for m in args.missions.split(","))]
    os.makedirs(args.out_dir, exist_ok=True)
    result = {"version": __version__, "pace_u": pu.__version__, "pace_t": pt.__version__,
              "rover_pilot": rp.__version__, "course": COURSE, "cruise": CRUISE,
              "until_s": UNTIL_S, "missions": []}
    md = ["# Why was seed 388's blocked rover caught 12 s late with a warm-up? (simulated)", "",
          "trace_u.py %s (pace_u.py %s, rover_pilot.py %s), MV2 of Munim, Inc. A diagnostic, not "
          "a pre-registered study: pace_u.py's %s missions flown again, logging every call of the "
          "stuck check up to %g s (calls-<profile>-<variant>-<seed>.csv). A clear is a call whose "
          "history was cleared since the call before; held means a full window with no verdict."
          % (__version__, pu.__version__, rp.__version__, COURSE, UNTIL_S), ""]
    all_same = True
    for profile, variant, seed in missions:
        r, calls = fly_traced(profile, variant, seed)
        name = "calls-%s-%s-%d.csv" % (profile, variant, seed)
        with open(os.path.join(args.out_dir, name), "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=FIELDS)
            w.writeheader()
            for x in calls:
                w.writerow({k: ("" if x[k] is None else x[k]) for k in FIELDS})
        stuck = r.get("stuck") or {}
        want = MISSIONS.get((profile, variant, seed))
        got = (r.get("elapsed_s"), stuck.get("recovery_t"))
        same = None if want is None else (got[0] == want[0] and got[1] == want[1])
        all_same = all_same and same is not False
        m = {"profile": profile, "variant": variant, "seed": seed, "csv": name,
             "calls": len(calls), "elapsed_s": got[0], "recovery_t": got[1],
             "first_outage_s": stuck.get("first_outage_s"), "warmup_s": stuck.get("warmup_s"),
             "as_recorded": same, "clears": clears(calls), "held": held(calls)}
        result["missions"].append(m)
        md += ["## %s, %s, seed %d" % (profile, variant, seed), "",
               "%d calls up to %g s; %s s; recovery moves at %s; first outage at %s s; against "
               "pace_u.py's record: %s." % (
                   len(calls), UNTIL_S, got[0], got[1], m["first_outage_s"],
                   "not in MISSIONS" if same is None else "identical" if same else
                   "DIFFERENT (recorded %s)" % (want,)), "",
               "Clears:", ""]
        md += ["- at %s s, %s s after the call before, new fix: %s; meanwhile recoveries +%s, "
               "telemetry stops +%s, tip stops +%s, bridged +%s s" % (
                   x["t"], x["gap_s"], x["new_fix"], x["recoveries"], x["telemetry_stops"],
                   x["tip_stops"], x["bridged_s"]) for x in m["clears"]] or ["- none"]
        md += ["", "Held (full window, no verdict):", ""]
        md += ["- %s-%s s: %d calls, %d too slow, least moved %s m" % (
            x["start"], x["end"], x["calls"], x["slow"], x["least_moved_m"])
            for x in m["held"]] or ["- none"]
        md += ["", "| t | gap s | cleared | warm from | n | span s | mean lin | moved m | verdict "
               "| linear | new fix | bridged s |", "|" + "---|" * 12]
        md += ["| %s |" % " | ".join(str(_cell(x[k])) for k in (
            "t", "gap_s", "cleared", "warm_from", "n", "span_s", "mean_lin", "moved_m",
            "verdict", "linear", "new_fix", "bridged_s")) for x in each_second(calls)]
        md += [""]
        print("%s %s %d: %d calls, %s s, %s, as recorded: %s" % (
            profile, variant, seed, len(calls), got[0], got[1], same), flush=True)
    result["all_as_recorded"] = all_same
    with open(os.path.join(args.out_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, indent=1)
    with open(os.path.join(args.out_dir, "report.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")
    return 0 if all_same else 1


if __name__ == "__main__":
    sys.exit(main())
