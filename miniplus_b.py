#!/usr/bin/env python3
"""miniplus_b: the Earth Rover Mini+'s conventions from public LeRobot recordings, second pass.

miniplus.py 0.1.0 (miniplus-v1) found 8 Mini+ datasets (16,939 frames) but
could grade almost nothing. Its turn windows needed 4 s of one-signed
`angular` of at least 0.3, and its wheel frames 1 s of a pure command, while
these recordings are keyboard teleop (a turn is sent as linear 0.3 with
angular +-1) and short autonomous runs with small commands. It also missed
the `imu.gyro.*` names and two robot_type spellings. No recording has a GPS
fix: latitude and longitude read the no-fix value 1000 throughout. This pass:

- works in frames, not seconds, so no float boundary decides a window;
- allows for the state arriving LAG_S after the command (the /data state
  refreshes about twice a second in these recordings);
- uses WIN_S windows of one-signed commands (zeros allowed) with |mean| >=
  TURN_CMD, and an orientation change of at least MIN_DEG;
- reads a forward frame as one whose command was linear >= FORWARD_CMD and
  |angular| < STRAIGHT_ANG from HOLD_S to LAG_S before it, and a turning frame
  as one whose angular was beyond SIDE_CMD over the same span, any linear;
- checks whether the four `wheel_rpm` columns are really two (rpm2 = rpm0,
  rpm3 = rpm1), which one is the right-hand side, and whether the SDK's
  `speed`, read as km/h, matches the wheels at 95 mm (0.00497 m/s per RPM);
- keeps only fields that change within an episode (a constant gyroscope or
  GPS is a missing sensor, not a reading);
- reports every dataset on its own as well as pooled.

    python miniplus_b.py --out-dir out

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
KNOWN = ("lilkm/earthrover-navigation", "lilkm/earthrover-test", "lilkm/earthrover-test-2",
         "lilkm/earthrover-test-3", "lilkm/earthrover-navigation-low-level-sdk",
         "AmitGMU/earthrover-navigation_20260610_165303", "dkuzmenko/earth-rover-mini-test-4",
         "cagataydev/scout-earthrover-ecot", "cagataydev/scout-earth-rover-mini-20260616-053232",
         "anirudhgudi/frodobots-lerobot-dataset")
SEARCH_TERMS = ("earthrover", "earth-rover", "earth_rover", "rover_mini", "rover-mini")
ROBOT_TYPES = ("earthrover_mini_plus", "earth_rover_mini_plus", "earth-rover-mini")
MAX_FILE_MB = 60

STATE_ALIASES = {
    "orientation": ("orientation", "orientation.deg", "heading_deg"),
    "lat": ("gps_latitude", "gps.latitude", "latitude"),
    "lon": ("gps_longitude", "gps.longitude", "longitude"),
    "speed": ("speed",),
    "gyro_x": ("gyroscope_x", "imu.gyro.x", "gyro_x"),
    "gyro_y": ("gyroscope_y", "imu.gyro.y", "gyro_y"),
    "gyro_z": ("gyroscope_z", "imu.gyro.z", "gyro_z"),
    "rpm0": ("wheel_rpm_0",), "rpm1": ("wheel_rpm_1",), "rpm2": ("wheel_rpm_2",), "rpm3": ("wheel_rpm_3",),
}
ACTION_ALIASES = {"linear": ("linear_velocity", "linear.vel", "linear"),
                  "angular": ("angular_velocity", "angular.vel", "angular")}
RPMS = ("rpm0", "rpm1", "rpm2", "rpm3")
GYROS = ("gyro_x", "gyro_y", "gyro_z")
TRACKED = ("orientation", "speed") + RPMS + GYROS

WIN_S = 2.0
LAG_S = 0.5
HOLD_S = 1.0
TURN_CMD = 0.2
MIN_DEG = 3.0
FORWARD_CMD = 0.3
STRAIGHT_ANG = 0.1
SIDE_CMD = 0.5
MIN_RPM = 20.0
MPS_PER_RPM = math.pi * 0.095 / 60.0  # 95 mm wheels (Earth Rover SDK README)
MIN_WINDOWS = 30
MIN_FORWARD = 30
MIN_SPEED_FRAMES = 50


# --- helpers -------------------------------------------------------------------

def wrap180(d):
    return (d + 180.0) % 360.0 - 180.0


def unwrap(values):
    """Orientation in degrees, unwrapped across 0/360."""
    out = []
    for v in values:
        out.append(v if not out else out[-1] + wrap180(v - out[-1]))
    return out


def valid_fix(lat, lon):
    if lat is None or lon is None or abs(lat) > 90 or abs(lon) > 180:
        return False
    return not (abs(lat) < 1e-6 and abs(lon) < 1e-6)


def pearson(xs, ys):
    if len(xs) < 3:
        return None
    mx, my = statistics.fmean(xs), statistics.fmean(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx <= 0 or syy <= 0:
        return None
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / math.sqrt(sxx * syy)


def slope(xs, ys):
    """Least-squares slope of ys on xs (with an intercept), or None."""
    if len(xs) < 3:
        return None
    mx, my = statistics.fmean(xs), statistics.fmean(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    if sxx <= 0:
        return None
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx


def median_or_none(xs, nd=3):
    return round(statistics.median(xs), nd) if xs else None


def share(a, n, nd=3):
    return round(a / n, nd) if n else None


def live(ep, key):
    """The field is present and changes within the episode."""
    v = ep.get(key)
    return bool(v) and any(x != v[0] for x in v)


def frames(fps, seconds):
    return int(round(seconds * fps))


# --- one episode ---------------------------------------------------------------

def windows(ep):
    """Non-overlapping WIN_S windows of commands. For each: mean angular,
    whether no two commands have opposite signs, the orientation change from
    LAG_S after its first frame to LAG_S after its end (unwrapped, degrees),
    the rate in deg/s, and each live gyroscope axis averaged over that span."""
    if not live(ep, "orientation"):
        return []
    fps = ep["fps"]
    nw, nl = max(1, frames(fps, WIN_S)), frames(fps, LAG_S)
    ang, uo = ep["angular"], unwrap(ep["orientation"])
    gy = [g for g in GYROS if live(ep, g)]
    out = []
    i = 0
    while i + nw + nl < len(ang):
        cmds = ang[i:i + nw]
        a, b = i + nl, i + nw + nl
        d = uo[b] - uo[a]
        w = {"cmd": statistics.fmean(cmds), "one_sign": not (any(c > 0 for c in cmds) and any(c < 0 for c in cmds)),
             "d": d, "rate": d * fps / nw}
        for g in gy:
            w[g] = statistics.fmean(ep[g][a:b + 1])
        out.append(w)
        i += nw
    return out


def qualifies(w):
    return w["one_sign"] and abs(w["cmd"]) >= TURN_CMD and abs(w["d"]) >= MIN_DEG


def held(ep, k, sel):
    """sel(linear, angular) held on every frame from HOLD_S to LAG_S before k."""
    fps = ep["fps"]
    lo, hi = k - frames(fps, HOLD_S), k - frames(fps, LAG_S)
    if lo < 0:
        return False
    return all(sel(ep["linear"][q], ep["angular"][q]) for q in range(lo, hi + 1))


def forward(lin, ang):
    return lin >= FORWARD_CMD and abs(ang) < STRAIGHT_ANG


def turning_left(lin, ang):
    return ang >= SIDE_CMD


def turning_right(lin, ang):
    return ang <= -SIDE_CMD


def wheels(ep):
    """Wheel counts for one episode, or None without four live-ish rpm columns."""
    if not all(ep.get(r) for r in RPMS) or not any(live(ep, r) for r in RPMS):
        return None
    out = {"moving": 0, "duplicated": 0, "forward": 0, "forward_all_nonzero": 0, "forward_one_sign": 0,
           "forward_all_positive": 0, "left": 0, "left_rpm1_higher": 0, "left_rpm0_higher": 0,
           "right": 0, "right_rpm1_higher": 0, "right_rpm0_higher": 0, "speed_ratios": []}
    has_speed = live(ep, "speed")
    for k in range(len(ep["t"])):
        v = [ep[r][k] for r in RPMS]
        if any(x != 0 for x in v):
            out["moving"] += 1
            if v[2] == v[0] and v[3] == v[1]:
                out["duplicated"] += 1
        if held(ep, k, forward):
            out["forward"] += 1
            if all(x != 0 for x in v):
                out["forward_all_nonzero"] += 1
                if all(x > 0 for x in v) or all(x < 0 for x in v):
                    out["forward_one_sign"] += 1
                if all(x > 0 for x in v):
                    out["forward_all_positive"] += 1
        for side, sel in (("left", turning_left), ("right", turning_right)):
            if any(x != 0 for x in v) and held(ep, k, sel):
                out[side] += 1
                if v[1] > v[0]:
                    out[side + "_rpm1_higher"] += 1
                elif v[0] > v[1]:
                    out[side + "_rpm0_higher"] += 1
        if has_speed and all(x > 0 for x in v) and ep["speed"][k] > 0:
            m = sum(v) / 4.0
            if m >= MIN_RPM:
                out["speed_ratios"].append((ep["speed"][k] / 3.6) / (m * MPS_PER_RPM))
    return out


def refresh_intervals(ep, keys):
    """Seconds between consecutive frames where any of keys changes."""
    keys = [k for k in keys if live(ep, k)]
    if not keys:
        return []
    ch = [i for i in range(1, len(ep["t"])) if any(ep[k][i] != ep[k][i - 1] for k in keys)]
    return [(b - a) / ep["fps"] for a, b in zip(ch, ch[1:])]


# --- reading the Hub -----------------------------------------------------------

def get_json(url, timeout=60):
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "miniplus_b/" + __version__}),
                                timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def get_bytes(url, timeout=180):
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "miniplus_b/" + __version__}),
                                timeout=timeout) as r:
        return r.read()


def find_datasets(log):
    ids = set(KNOWN)
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
    """rows: dicts with episode_index, frame_index, observation.state, action.
    One dict of lists per episode, sorted by frame; a field with any missing
    value in an episode is left out of that episode."""
    by = {}
    for r in rows:
        by.setdefault(int(r["episode_index"]), []).append(r)
    eps = []
    for e in sorted(by):
        rs = sorted(by[e], key=lambda r: int(r["frame_index"]))
        ep = {"episode": e, "fps": fps, "t": [int(r["frame_index"]) / float(fps) for r in rs]}
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
    keep = [c for c in ("episode_index", "frame_index", "observation.state", "action") if c in t.column_names]
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
    if info.get("robot_type") not in ROBOT_TYPES:
        meta["skipped"] = "robot_type %r" % info.get("robot_type")
        return meta, []
    cols = columns(info)
    if cols is None:
        meta["skipped"] = "no linear/angular action names"
        return meta, []
    fps = info.get("fps") or 10
    meta["fps"] = fps
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
    eps = episodes_from_rows(rows, cols, fps)
    meta["episodes"] = len(eps)
    meta["frames"] = sum(len(e["t"]) for e in eps)
    meta["live_fields"] = sorted({k for e in eps for k in TRACKED + ("lat", "lon") if live(e, k)})
    return meta, eps


# --- the analysis --------------------------------------------------------------

def summarise(eps):
    """Results for a list of episodes (one dataset, or all pooled)."""
    res = {"episodes": len(eps), "frames": sum(len(e["t"]) for e in eps)}
    lat_n = sum(len(e["lat"]) for e in eps if e.get("lat") and e.get("lon"))
    lat_ok = sum(1 for e in eps if e.get("lat") and e.get("lon")
                 for la, lo in zip(e["lat"], e["lon"]) if valid_fix(la, lo))
    res["gps"] = {"frames": lat_n, "valid_share": share(lat_ok, lat_n)}

    ref = [x for e in eps for x in refresh_intervals(e, TRACKED)]
    ori = [x for e in eps for x in refresh_intervals(e, ("orientation",))]
    res["refresh_s"] = {"median": median_or_none(ref), "n": len(ref)}
    res["orientation_change_s"] = {"median": median_or_none(ori), "n": len(ori)}

    ws = [w for e in eps for w in windows(e)]
    q = [w for w in ws if qualifies(w)]
    cw = sum(1 for w in q if w["d"] * w["cmd"] < 0)
    one = [w for w in ws if w["one_sign"]]
    s = slope([w["cmd"] for w in one], [w["rate"] for w in one])
    res["turns"] = {"windows": len(ws), "qualifying": len(q), "clockwise": cw, "counter_clockwise": len(q) - cw,
                    "share_clockwise": share(cw, len(q)),
                    "deg_per_s_per_unit": median_or_none([abs(w["rate"]) / abs(w["cmd"]) for w in q], 1),
                    "slope_deg_per_s_per_unit": None if s is None else round(s, 2)}
    gy = {}
    for g in GYROS:
        have = [w for w in ws if g in w]
        r = pearson([w[g] for w in have], [w["rate"] for w in have])
        ratio = [w[g] / w["rate"] for w in have if abs(w["rate"]) >= 5.0]
        gy[g] = {"n": len(have), "r_with_orientation_rate": None if r is None else round(r, 3),
                 "over_orientation_rate": median_or_none(ratio, 3)}
    res["gyroscope"] = gy

    tot = None
    for e in eps:
        c = wheels(e)
        if c is None:
            continue
        if tot is None:
            tot = {k: ([] if isinstance(v, list) else 0) for k, v in c.items()}
        for k, v in c.items():
            tot[k] = tot[k] + v
    if tot is None:
        res["wheels"] = None
    else:
        ratios = tot.pop("speed_ratios")
        tot["duplicated_share"] = share(tot["duplicated"], tot["moving"])
        tot["forward_one_sign_share"] = share(tot["forward_one_sign"], tot["forward_all_nonzero"])
        tot["left_rpm1_higher_share"] = share(tot["left_rpm1_higher"], tot["left"])
        tot["right_rpm0_higher_share"] = share(tot["right_rpm0_higher"], tot["right"])
        tot["speed_ratio"] = {"median": median_or_none(ratios), "n": len(ratios),
                              "q1": round(statistics.quantiles(ratios, n=4)[0], 3) if len(ratios) >= 4 else None,
                              "q3": round(statistics.quantiles(ratios, n=4)[2], 3) if len(ratios) >= 4 else None}
        res["wheels"] = tot
    return res


def analyse(datasets):
    """datasets: list of (meta, episodes). Per dataset and pooled results."""
    per = {m["id"]: summarise(es) for m, es in datasets if es}
    pooled = summarise([e for _, es in datasets for e in es])
    pooled["datasets"] = len(per)
    pooled["turn_datasets"] = sum(1 for r in per.values() if r["turns"]["qualifying"] > 0)
    return {"pooled": pooled, "per_dataset": per}


def decide(res):
    """The pre-stated rules (PREDICTION.md)."""
    p = res["pooled"]
    t = p["turns"]
    out = {}
    if t["qualifying"] >= MIN_WINDOWS and p["turn_datasets"] >= 2:
        if t["share_clockwise"] >= 0.8:
            out["D1"] = "clockwise: the pilot's default (orientation degrees clockwise) is consistent"
        elif t["share_clockwise"] <= 0.2:
            out["D1"] = "counter-clockwise: change the pilot's real-rover default next release"
        else:
            out["D1"] = "mixed: no change; --calibrate stays the way to find out"
    else:
        out["D1"] = "too few turn windows (%d from %d datasets): no change" % (t["qualifying"], p["turn_datasets"])
    w = p["wheels"]
    n = w["forward_all_nonzero"] if w else 0
    if n >= MIN_FORWARD:
        if w["forward_one_sign_share"] >= 0.9:
            out["D2"] = "all four wheels share a sign driving forward: averaging the four is right"
        else:
            out["D2"] = ("the wheels do not share a sign driving forward: dead_reckon's average of the "
                         "four must use signed sides; fix next release")
    else:
        out["D2"] = "too few forward frames with all wheels non-zero (%d): no change" % n
    sr = w["speed_ratio"] if w else {"median": None, "n": 0}
    if sr["n"] >= MIN_SPEED_FRAMES:
        if 0.8 <= sr["median"] <= 1.25:
            out["D3"] = "speed (km/h) matches the wheels at 95 mm: the 0.00497 m/s per RPM prior stays"
        else:
            out["D3"] = ("speed and wheels disagree at 95 mm (median ratio %.3f): document it; the pilot "
                         "keeps learning the scale from GPS" % sr["median"])
    else:
        out["D3"] = "too few frames for the speed check (%d): no change" % sr["n"]
    return out


def report(meta, res, dec):
    p = res["pooled"]
    lines = ["# Earth Rover Mini+ conventions, from public LeRobot recordings (second pass)", "",
             "Generated by miniplus_b.py %s (earth-rover-pilot, MV2 of Munim, Inc.). The recordings belong "
             "to their uploaders; only measurements are given here." % __version__, "",
             "## Datasets", "", "| dataset | licence | fps | episodes | frames | fields that change |",
             "|---|---|---|---|---|---|"]
    for m in meta:
        if m.get("episodes"):
            lines.append("| %s | %s | %s | %d | %d | %s |" % (m["id"], m.get("license"), m.get("fps"), m["episodes"],
                                                               m["frames"], ", ".join(m.get("live_fields", []))))
    skipped = [m for m in meta if not m.get("episodes")]
    lines += ["", "Skipped: %d (%s)." % (len(skipped), "; ".join(
        "%s: %s" % (m["id"], m.get("skipped", "no episodes")) for m in skipped[:25])), "",
        "## Per dataset", "",
        "| dataset | qualifying turns | clockwise share | deg/s per unit | refresh s | GPS valid share |",
        "|---|---|---|---|---|---|"]
    for ds, r in sorted(res["per_dataset"].items()):
        t = r["turns"]
        lines.append("| %s | %d | %s | %s | %s | %s |" % (ds, t["qualifying"], t["share_clockwise"],
                                                         t["deg_per_s_per_unit"], r["refresh_s"]["median"],
                                                         r["gps"]["valid_share"]))
    t = p["turns"]
    lines += ["", "## Pooled", "",
              "- %d datasets, %d episodes, %d frames." % (p["datasets"], p["episodes"], p["frames"]),
              "- turns: %d windows, %d qualifying from %d datasets; orientation fell on a left turn in %d, rose in %d "
              "(share clockwise %s); %s deg/s per unit of angular (slope over one-signed windows %s)." % (
                  t["windows"], t["qualifying"], p["turn_datasets"], t["clockwise"], t["counter_clockwise"],
                  t["share_clockwise"], t["deg_per_s_per_unit"], t["slope_deg_per_s_per_unit"]),
              "- state refresh: median %s s (n %d); orientation changes: median %s s (n %d)." % (
                  p["refresh_s"]["median"], p["refresh_s"]["n"], p["orientation_change_s"]["median"],
                  p["orientation_change_s"]["n"]),
              "- GPS: valid share %s of %d frames." % (p["gps"]["valid_share"], p["gps"]["frames"]),
              "- gyroscope: %s." % json.dumps(p["gyroscope"]),
              "- wheels: %s." % json.dumps(p["wheels"]),
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
    summary = {"version": __version__, "elapsed_s": round(time.time() - t0, 1),
               "datasets": [m for m in meta if m.get("episodes")],
               "skipped": len([m for m in meta if not m.get("episodes")]),
               "results": res, "decisions": dec,
               "settings": {"win_s": WIN_S, "lag_s": LAG_S, "hold_s": HOLD_S, "turn_cmd": TURN_CMD,
                            "min_deg": MIN_DEG, "forward_cmd": FORWARD_CMD, "straight_ang": STRAIGHT_ANG,
                            "side_cmd": SIDE_CMD, "min_rpm": MIN_RPM, "mps_per_rpm": MPS_PER_RPM,
                            "min_windows": MIN_WINDOWS, "min_forward": MIN_FORWARD,
                            "min_speed_frames": MIN_SPEED_FRAMES}}
    with open(os.path.join(args.out_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=1)
    text = report(meta, res, dec)
    with open(os.path.join(args.out_dir, "report.md"), "w", encoding="utf-8") as f:
        f.write(text)
    print(text, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
