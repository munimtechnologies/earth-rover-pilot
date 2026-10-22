#!/usr/bin/env python3
"""miniplus: what public LeRobot recordings say about the Earth Rover Mini+'s telemetry.

Every FrodoBots-2K study measured the older Earth Rover Zero. The Mini+ that
the Earth Rover Challenge now uses reports an `orientation` it computes on
board, and the SDK says neither which way it runs nor how often it updates,
nor the order and signs of the four `rpms` columns. earth-rover-pilot assumes
degrees clockwise from north and averages the four wheels. LeRobot's
`earthrover_mini_plus` robot records the SDK's /data fields at 10 fps (the
newest row of `gyros`, `mags`, `rpms`), and a few people have put such
recordings on the Hugging Face Hub. This reads every public one it finds
(table data only, no video) and measures:

- how often `orientation` and the GPS position change (hold intervals),
- which way `orientation` runs under a positive `angular` (turn windows),
- how fast it turns per unit of `angular`,
- the signs of the four wheel RPMs driving straight and turning in place,
- which gyroscope axis follows the turns,
- `orientation` against the GPS course on straight moving stretches, read
  clockwise and counter-clockwise.

    python miniplus.py --out-dir out

The rules for reading the result are in PREDICTION.md, written before the run.
Needs pyarrow to read parquet. By MV2 of Munim, Inc.; written with AI agents.
Apache-2.0. The recordings belong to their uploaders; only measurements are
written out, with each dataset's id and licence.
"""

from __future__ import annotations

import argparse
import io
import json
import math
import os
import statistics
import sys
import time
import urllib.parse
import urllib.request

__version__ = "0.1.0"

HF = "https://huggingface.co"
SEARCH_TERMS = ("earthrover", "earth-rover", "earth_rover", "earthrover_mini", "mini_plus",
                "frodobots", "rover_mini", "erm")
ROBOT_TYPE = "earthrover_mini_plus"
MAX_FILE_MB = 60

STATE_ALIASES = {
    "orientation": ("orientation", "orientation.deg"),
    "lat": ("gps_latitude", "gps.latitude"),
    "lon": ("gps_longitude", "gps.longitude"),
    "speed": ("speed",),
    "gyro_x": ("gyroscope_x",), "gyro_y": ("gyroscope_y",), "gyro_z": ("gyroscope_z",),
    "rpm0": ("wheel_rpm_0",), "rpm1": ("wheel_rpm_1",), "rpm2": ("wheel_rpm_2",), "rpm3": ("wheel_rpm_3",),
}
ACTION_ALIASES = {"linear": ("linear_velocity", "linear.vel"), "angular": ("angular_velocity", "angular.vel")}
RPMS = ("rpm0", "rpm1", "rpm2", "rpm3")
GYROS = ("gyro_x", "gyro_y", "gyro_z")

# Turn windows: WIN_S of commands of one sign, |mean| >= TURN_CMD, orientation
# compared LAG_S later at both ends.
WIN_S = 4.0
LAG_S = 1.0
TURN_CMD = 0.3
# Straight driving: |angular| below STRAIGHT_ANG, linear at least FORWARD_CMD.
STRAIGHT_ANG = 0.1
FORWARD_CMD = 0.3
# Spinning in place: |linear| below STILL_LIN, |angular| at least TURN_CMD.
STILL_LIN = 0.1
# GPS course: fixes at least COURSE_S apart and COURSE_M metres apart.
COURSE_S = 5.0
COURSE_M = 3.0
MIN_WINDOWS = 10
MIN_COURSE_PAIRS = 20


# --- helpers -------------------------------------------------------------------

def wrap180(d):
    return (d + 180.0) % 360.0 - 180.0


def bearing(lat1, lon1, lat2, lon2):
    """Initial bearing from point 1 to point 2: degrees, 0 = north, clockwise."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dl = math.radians(lon2 - lon1)
    y = math.sin(dl) * math.cos(p2)
    x = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)
    return math.degrees(math.atan2(y, x)) % 360.0


def metres(lat1, lon1, lat2, lon2):
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = (math.sin((p2 - p1) / 2) ** 2
         + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2)
    return 2 * r * math.asin(min(1.0, math.sqrt(a)))


def valid_fix(lat, lon):
    if lat is None or lon is None:
        return False
    if abs(lat) > 90 or abs(lon) > 180:
        return False
    return not (abs(lat) < 1e-6 and abs(lon) < 1e-6)


def unwrap(values):
    """Orientation in degrees, unwrapped across 0/360."""
    out = []
    for v in values:
        if not out:
            out.append(v)
        else:
            out.append(out[-1] + wrap180(v - out[-1]))
    return out


def change_intervals(ts, values, keep=None):
    """Seconds between consecutive changes of `values` (a run's first and last
    edges are not known, so only spans between two changes count). keep(i), if
    given, must hold at both changes."""
    changes = [i for i in range(1, len(values)) if values[i] != values[i - 1]]
    out = []
    for a, b in zip(changes, changes[1:]):
        if keep is None or (keep(a) and keep(b)):
            out.append(ts[b] - ts[a])
    return out


def pearson(xs, ys):
    if len(xs) < 3:
        return None
    mx, my = statistics.fmean(xs), statistics.fmean(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx <= 0 or syy <= 0:
        return None
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / math.sqrt(sxx * syy)


def circ_mean(degs):
    s = sum(math.sin(math.radians(d)) for d in degs)
    c = sum(math.cos(math.radians(d)) for d in degs)
    return math.degrees(math.atan2(s, c)) % 360.0


def median_or_none(xs, nd=3):
    return round(statistics.median(xs), nd) if xs else None


# --- one episode ---------------------------------------------------------------

def at(ts, t):
    """Index of the last frame at or before t, or None."""
    lo, hi = 0, len(ts)
    while lo < hi:
        mid = (lo + hi) // 2
        if ts[mid] <= t:
            lo = mid + 1
        else:
            hi = mid
    return lo - 1 if lo else None


def turn_windows(ep):
    """Non-overlapping WIN_S windows of one-signed |mean angular| >= TURN_CMD.
    Each: mean command, orientation change (unwrapped, LAG_S later), mean of each
    gyroscope axis over the shifted window."""
    ts, ang = ep["t"], ep["angular"]
    orient = ep.get("orientation")
    if not orient:
        return []
    uo = unwrap(orient)
    out = []
    i = 0
    n = len(ts)
    while i < n:
        if ts[-1] < ts[i] + WIN_S - 0.15:
            break
        j = at(ts, ts[i] + WIN_S)
        if ts[j] - ts[i] < WIN_S - 0.15:
            i += 1
            continue
        cmds = ang[i:j + 1]
        m = statistics.fmean(cmds)
        if abs(m) >= TURN_CMD and all(c * m > 0 for c in cmds):
            a = at(ts, ts[i] + LAG_S)
            b = at(ts, ts[j] + LAG_S)
            if a is not None and b is not None and b > a and ts[b] - ts[j] >= LAG_S - 0.15:
                w = {"cmd": m, "d_orient": uo[b] - uo[a], "seconds": ts[b] - ts[a]}
                for g in GYROS:
                    if ep.get(g):
                        w[g] = statistics.fmean(ep[g][a:b + 1])
                out.append(w)
                i = j + 1
                continue
        i += 1
    return out


def wheel_signs(ep, select):
    """Per wheel: counts of positive, negative and zero readings on frames where
    select(linear, angular) holds and the command has held for 1 s."""
    counts = {r: [0, 0, 0] for r in RPMS if ep.get(r)}
    ts = ep["t"]
    for k in range(len(ts)):
        a = at(ts, ts[k] - 1.0)
        if a is None:
            continue
        if not all(select(ep["linear"][q], ep["angular"][q]) for q in range(a, k + 1)):
            continue
        for r in counts:
            v = ep[r][k]
            counts[r][0 if v > 0 else 1 if v < 0 else 2] += 1
    return counts


def all_same_sign_frames(ep, select):
    """Frames (command held 1 s) where all four RPMs are non-zero: how many, and
    how many have all four with one sign."""
    if not all(ep.get(r) for r in RPMS):
        return 0, 0
    ts = ep["t"]
    n = same = 0
    for k in range(len(ts)):
        a = at(ts, ts[k] - 1.0)
        if a is None or not all(select(ep["linear"][q], ep["angular"][q]) for q in range(a, k + 1)):
            continue
        vals = [ep[r][k] for r in RPMS]
        if any(v == 0 for v in vals):
            continue
        n += 1
        if all(v > 0 for v in vals) or all(v < 0 for v in vals):
            same += 1
    return n, same


def course_pairs(ep):
    """Orientation against the GPS course on straight forward stretches: one
    pair per non-overlapping span of >= COURSE_S between distinct fixes that
    moved >= COURSE_M, with |angular| < STRAIGHT_ANG and linear >= FORWARD_CMD
    throughout. Orientation taken at the span's middle."""
    ts = ep["t"]
    if not ep.get("orientation") or not ep.get("lat"):
        return []
    fixes = []
    last = None
    for k in range(len(ts)):
        la, lo = ep["lat"][k], ep["lon"][k]
        if valid_fix(la, lo) and (la, lo) != last:
            fixes.append(k)
            last = (la, lo)
    out = []
    i = 0
    while i < len(fixes):
        a = fixes[i]
        j = i + 1
        while j < len(fixes) and ts[fixes[j]] - ts[a] < COURSE_S:
            j += 1
        if j >= len(fixes):
            break
        b = fixes[j]
        ok = all(abs(ep["angular"][q]) < STRAIGHT_ANG and ep["linear"][q] >= FORWARD_CMD
                 for q in range(a, b + 1))
        d = metres(ep["lat"][a], ep["lon"][a], ep["lat"][b], ep["lon"][b])
        if ok and d >= COURSE_M:
            mid = at(ts, (ts[a] + ts[b]) / 2.0)
            course = bearing(ep["lat"][a], ep["lon"][a], ep["lat"][b], ep["lon"][b])
            o = ep["orientation"][mid]
            out.append({"course": course, "orientation": o,
                        "cw": wrap180(course - o), "ccw": wrap180(course - (360.0 - o)),
                        "metres": d, "seconds": ts[b] - ts[a]})
            i = j
        else:
            i += 1
    return out


def spread_about_episode_offset(pairs_by_ep, key):
    """Median |difference - that episode's circular mean difference| over all
    pairs, for episodes with at least 2 pairs."""
    devs = []
    for pairs in pairs_by_ep:
        if len(pairs) < 2:
            continue
        off = circ_mean([p[key] for p in pairs])
        devs.extend(abs(wrap180(p[key] - off)) for p in pairs)
    return median_or_none(devs, 2), len(devs)


# --- reading the Hub -----------------------------------------------------------

def get_json(url, timeout=60):
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "miniplus/" + __version__}),
                                timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def get_bytes(url, timeout=180):
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "miniplus/" + __version__}),
                                timeout=timeout) as r:
        return r.read()


def find_datasets(log):
    ids = set()
    for term in SEARCH_TERMS:
        try:
            for d in get_json(HF + "/api/datasets?search=" + urllib.parse.quote(term) + "&limit=200"):
                ids.add(d["id"])
        except Exception as exc:  # noqa: BLE001 - a failed search is logged, not fatal
            log("search %r failed: %s" % (term, exc))
    return sorted(ids)


def index_of(names, aliases):
    for a in aliases:
        if a in names:
            return names.index(a)
    return None


def columns(info):
    """Map our keys to (feature, index) from a LeRobot info.json, or None."""
    feats = info.get("features", {})
    st = (feats.get("observation.state") or {}).get("names") or []
    ac = (feats.get("action") or {}).get("names") or []
    if isinstance(st, dict):
        st = next(iter(st.values()), [])
    if isinstance(ac, dict):
        ac = next(iter(ac.values()), [])
    cols = {}
    for key, al in STATE_ALIASES.items():
        k = index_of(st, al)
        if k is not None:
            cols[key] = ("observation.state", k)
    for key, al in ACTION_ALIASES.items():
        k = index_of(ac, al)
        if k is not None:
            cols[key] = ("action", k)
    if "linear" not in cols or "angular" not in cols:
        return None
    return cols


def episodes_from_rows(rows, cols, fps):
    """rows: dicts with episode_index, frame_index, timestamp, observation.state,
    action. Returns one dict of lists per episode, sorted by frame."""
    by = {}
    for r in rows:
        by.setdefault(int(r["episode_index"]), []).append(r)
    eps = []
    for e in sorted(by):
        rs = sorted(by[e], key=lambda r: int(r["frame_index"]))
        ep = {"episode": e, "t": [int(r["frame_index"]) / float(fps) for r in rs]}
        for key, (feat, k) in cols.items():
            vals = []
            for r in rs:
                v = r.get(feat)
                x = float(v[k]) if v is not None and len(v) > k and v[k] is not None else None
                vals.append(x if x is not None and math.isfinite(x) else None)
            if all(x is not None for x in vals):
                ep[key] = vals
        if "linear" in ep and "angular" in ep:
            eps.append(ep)
    return eps


def read_parquet(data):
    import pyarrow.parquet as pq
    t = pq.read_table(io.BytesIO(data))
    keep = [c for c in ("episode_index", "frame_index", "timestamp", "observation.state", "action")
            if c in t.column_names]
    return t.select(keep).to_pylist()


def load_dataset(ds, log):
    """(meta, episodes) for one Hub dataset, or (meta-with-reason, [])."""
    meta = {"id": ds}
    try:
        info = get_json(HF + "/datasets/" + ds + "/resolve/main/meta/info.json")
    except Exception as exc:  # noqa: BLE001
        meta["skipped"] = "no meta/info.json (%s)" % type(exc).__name__
        return meta, []
    meta["robot_type"] = info.get("robot_type")
    if info.get("robot_type") != ROBOT_TYPE:
        meta["skipped"] = "robot_type %r" % info.get("robot_type")
        return meta, []
    cols = columns(info)
    if cols is None:
        meta["skipped"] = "no linear/angular action names"
        return meta, []
    meta["fps"] = info.get("fps")
    meta["fields"] = sorted(cols)
    try:
        card = get_json(HF + "/api/datasets/" + ds)
    except Exception as exc:  # noqa: BLE001
        meta["skipped"] = "no file list (%s)" % type(exc).__name__
        return meta, []
    lic = (card.get("cardData") or {}).get("license")
    meta["license"] = lic if lic else "not stated"
    files = sorted(s["rfilename"] for s in card.get("siblings", [])
                   if s["rfilename"].startswith("data/") and s["rfilename"].endswith(".parquet"))
    rows = []
    for f in files:
        try:
            data = get_bytes(HF + "/datasets/" + ds + "/resolve/main/" + f)
        except Exception as exc:  # noqa: BLE001
            log("%s %s: %s" % (ds, f, exc))
            continue
        if len(data) > MAX_FILE_MB * 1e6:
            log("%s %s: too large" % (ds, f))
            continue
        rows.extend(read_parquet(data))
    meta["files"] = len(files)
    eps = episodes_from_rows(rows, cols, info.get("fps") or 10)
    meta["episodes"] = len(eps)
    meta["frames"] = sum(len(e["t"]) for e in eps)
    return meta, eps


# --- the analysis --------------------------------------------------------------

def analyse(datasets):
    """datasets: list of (meta, episodes). Returns the results dict."""
    eps = [(m["id"], e) for m, es in datasets for e in es]
    res = {"datasets": len([1 for m, es in datasets if es]), "episodes": len(eps),
           "frames": sum(len(e["t"]) for _, e in eps),
           "seconds": round(sum(e["t"][-1] - e["t"][0] for _, e in eps if e["t"]), 1)}

    # Orientation range and hold intervals.
    allo = [v for _, e in eps for v in e.get("orientation", [])]
    res["orientation_min"] = round(min(allo), 3) if allo else None
    res["orientation_max"] = round(max(allo), 3) if allo else None
    res["orientation_integer_share"] = (round(sum(1 for v in allo if v == int(v)) / len(allo), 3)
                                        if allo else None)
    hold_all, hold_turn, gps_hold = [], [], []
    stale = total = 0
    for _, e in eps:
        if e.get("orientation"):
            hold_all += change_intervals(e["t"], e["orientation"])
            hold_turn += change_intervals(e["t"], e["orientation"],
                                          keep=lambda i, e=e: abs(e["angular"][i]) >= TURN_CMD)
        if e.get("lat"):
            fix = [(la, lo) for la, lo in zip(e["lat"], e["lon"])]
            gps_hold += change_intervals(e["t"], fix)
        keys = [k for k in ("orientation", "lat", "lon", "speed") + GYROS + RPMS if e.get(k)]
        for k in range(1, len(e["t"])):
            total += 1
            if keys and all(e[q][k] == e[q][k - 1] for q in keys):
                stale += 1
    res["orientation_hold_s"] = {"median": median_or_none(hold_all), "n": len(hold_all)}
    res["orientation_hold_turning_s"] = {"median": median_or_none(hold_turn), "n": len(hold_turn)}
    res["gps_hold_s"] = {"median": median_or_none(gps_hold), "n": len(gps_hold)}
    res["frames_all_fields_repeated"] = round(stale / total, 3) if total else None

    # Turn windows.
    wins = [dict(w, dataset=d) for d, e in eps for w in turn_windows(e)]
    cw = [w for w in wins if w["d_orient"] * w["cmd"] < 0]
    ccw = [w for w in wins if w["d_orient"] * w["cmd"] > 0]
    rates = [abs(w["d_orient"]) / (abs(w["cmd"]) * w["seconds"]) for w in wins if w["seconds"] > 0]
    res["turn_windows"] = {
        "n": len(wins), "datasets": len({w["dataset"] for w in wins}),
        "positive_cmd": sum(1 for w in wins if w["cmd"] > 0),
        "orientation_falls_on_left_turn": len(cw), "orientation_rises_on_left_turn": len(ccw),
        "share_clockwise": round(len(cw) / len(wins), 3) if wins else None,
        "deg_per_s_per_unit": median_or_none(rates, 1),
    }
    gy = {}
    for g in GYROS:
        xs = [w[g] / w["cmd"] for w in wins if g in w]
        ys = [w["d_orient"] / w["seconds"] for w in wins if g in w]
        pr = pearson([w[g] for w in wins if g in w], ys)
        ratio = [w[g] / (w["d_orient"] / w["seconds"]) for w in wins
                 if g in w and abs(w["d_orient"]) / w["seconds"] > 5]
        gy[g] = {"n": len(ys), "r_with_orientation_rate": None if pr is None else round(pr, 3),
                 "per_unit_cmd": median_or_none(xs, 2), "over_orientation_rate": median_or_none(ratio, 3)}
    res["gyroscope"] = gy

    # Wheels.
    straight = lambda lin, ang: lin >= FORWARD_CMD and abs(ang) < STRAIGHT_ANG  # noqa: E731
    left = lambda lin, ang: abs(lin) < STILL_LIN and ang >= TURN_CMD  # noqa: E731
    right = lambda lin, ang: abs(lin) < STILL_LIN and ang <= -TURN_CMD  # noqa: E731
    wheels = {}
    for name, sel in (("forward", straight), ("spin_left", left), ("spin_right", right)):
        tot = {r: [0, 0, 0] for r in RPMS}
        n = same = 0
        for _, e in eps:
            for r, c in wheel_signs(e, sel).items():
                for q in range(3):
                    tot[r][q] += c[q]
            a, b = all_same_sign_frames(e, sel)
            n += a
            same += b
        wheels[name] = {"signs_pos_neg_zero": tot, "frames_all_nonzero": n,
                        "all_one_sign": same, "share_one_sign": round(same / n, 3) if n else None}
    res["wheels"] = wheels

    # Orientation against the GPS course.
    by_ep = [course_pairs(e) for _, e in eps]
    pairs = [p for ps in by_ep for p in ps]
    cw_spread, cw_n = spread_about_episode_offset(by_ep, "cw")
    ccw_spread, ccw_n = spread_about_episode_offset(by_ep, "ccw")
    res["course"] = {"pairs": len(pairs), "episodes": sum(1 for ps in by_ep if ps),
                     "raw_median_abs_cw": median_or_none([abs(p["cw"]) for p in pairs], 1),
                     "raw_median_abs_ccw": median_or_none([abs(p["ccw"]) for p in pairs], 1),
                     "spread_cw": cw_spread, "spread_ccw": ccw_spread, "spread_pairs": cw_n}
    return res


def decide(res):
    """The pre-stated rules (PREDICTION.md)."""
    tw = res["turn_windows"]
    out = {}
    if tw["n"] >= MIN_WINDOWS and tw["datasets"] >= 2 and tw["share_clockwise"] is not None:
        if tw["share_clockwise"] >= 0.8:
            out["D1"] = "clockwise: the pilot's default (orientation degrees clockwise) is consistent"
        elif tw["share_clockwise"] <= 0.2:
            out["D1"] = "counter-clockwise: change the pilot's real-rover default next release"
        else:
            out["D1"] = "mixed: no change; --calibrate stays the way to find out"
    else:
        out["D1"] = "too few turn windows (%d from %d datasets): no change" % (tw["n"], tw["datasets"])
    fw = res["wheels"]["forward"]
    if fw["frames_all_nonzero"] >= 50 and fw["share_one_sign"] is not None:
        if fw["share_one_sign"] >= 0.9:
            out["D2"] = "all four wheels share a sign driving forward: averaging the four is right"
        else:
            out["D2"] = ("the wheels do not share a sign driving forward: dead_reckon's average of the "
                         "four must use signed sides; fix next release")
    else:
        out["D2"] = "too few forward frames with all wheels non-zero (%d): no change" % fw["frames_all_nonzero"]
    return out


def report(meta, res, dec):
    tw, c = res["turn_windows"], res["course"]
    lines = ["# Earth Rover Mini+ telemetry, from public LeRobot recordings", "",
             "Generated by miniplus.py %s (earth-rover-pilot, MV2 of Munim, Inc.). The recordings belong "
             "to their uploaders; only measurements are given here." % __version__, "",
             "## Datasets", "", "| dataset | licence | episodes | frames | fields |", "|---|---|---|---|---|"]
    for m in meta:
        if m.get("episodes"):
            lines.append("| %s | %s | %d | %d | %s |" % (m["id"], m.get("license"), m["episodes"],
                                                          m["frames"], ", ".join(m.get("fields", []))))
    skipped = [m for m in meta if not m.get("episodes")]
    lines += ["", "Searched and skipped: %d (%s)." % (len(skipped), "; ".join(
        "%s: %s" % (m["id"], m.get("skipped", "no episodes")) for m in skipped[:40])), "",
        "## Results", "",
        "- %d datasets, %d episodes, %d frames, %.0f s." % (res["datasets"], res["episodes"], res["frames"],
                                                           res["seconds"]),
        "- orientation range %s to %s (%s of readings whole numbers); hold between changes: median %s s "
        "(n %d), while turning %s s (n %d)." % (res["orientation_min"], res["orientation_max"],
                                                res["orientation_integer_share"],
                                                res["orientation_hold_s"]["median"], res["orientation_hold_s"]["n"],
                                                res["orientation_hold_turning_s"]["median"],
                                                res["orientation_hold_turning_s"]["n"]),
        "- GPS position hold: median %s s (n %d). Frames with every field repeated: %s." % (
            res["gps_hold_s"]["median"], res["gps_hold_s"]["n"], res["frames_all_fields_repeated"]),
        "- turn windows: %d (%d datasets, %d with positive angular); orientation fell on a left turn in %d, "
        "rose in %d (share clockwise %s); %s deg/s per unit of angular." % (
            tw["n"], tw["datasets"], tw["positive_cmd"], tw["orientation_falls_on_left_turn"],
            tw["orientation_rises_on_left_turn"], tw["share_clockwise"], tw["deg_per_s_per_unit"]),
        "- gyroscope: %s." % json.dumps(res["gyroscope"]),
        "- wheels: %s." % json.dumps(res["wheels"]),
        "- orientation vs GPS course: %d pairs from %d episodes; raw median |course - orientation| %s deg "
        "read clockwise, %s read counter-clockwise; spread about each episode's offset %s (cw) vs %s (ccw) "
        "on %d pairs." % (c["pairs"], c["episodes"], c["raw_median_abs_cw"], c["raw_median_abs_ccw"],
                          c["spread_cw"], c["spread_ccw"], c["spread_pairs"]),
        "", "## Decisions (stated before the run)", ""]
    lines += ["- %s: %s" % (k, v) for k, v in sorted(dec.items())]
    return "\n".join(lines) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--datasets", default="", help="comma-separated Hub ids instead of searching")
    args = ap.parse_args(argv)
    os.makedirs(args.out_dir, exist_ok=True)
    t0 = time.time()

    def log(msg):
        print(msg, flush=True)

    ids = [d for d in args.datasets.split(",") if d] or find_datasets(log)
    log("candidates: %d" % len(ids))
    loaded = []
    for ds in ids:
        meta, eps = load_dataset(ds, log)
        log("%s: %s" % (ds, meta.get("skipped") or "%d episodes, %d frames" % (meta["episodes"], meta["frames"])))
        loaded.append((meta, eps))
    res = analyse(loaded)
    dec = decide(res)
    meta = [m for m, _ in loaded]
    summary = {"version": __version__, "elapsed_s": round(time.time() - t0, 1), "datasets": meta,
               "results": res, "decisions": dec,
               "settings": {"win_s": WIN_S, "lag_s": LAG_S, "turn_cmd": TURN_CMD, "straight_ang": STRAIGHT_ANG,
                            "forward_cmd": FORWARD_CMD, "still_lin": STILL_LIN, "course_s": COURSE_S,
                            "course_m": COURSE_M, "min_windows": MIN_WINDOWS}}
    with open(os.path.join(args.out_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=1)
    text = report(meta, res, dec)
    with open(os.path.join(args.out_dir, "report.md"), "w", encoding="utf-8") as f:
        f.write(text)
    print(text, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
