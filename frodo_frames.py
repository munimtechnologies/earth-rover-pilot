#!/usr/bin/env python3
"""frodo_frames: how often the front-camera obstacle check sees phantoms on real FrodoBots-2K rides.

earth-rover-pilot's camera layer (free_space.py) was built on frames its own
simulator drew. A first pass (0.1.0) ran it on 11 front-camera frames of
FrodoBots-2K (CC BY-SA 4.0, FrodoBots Lab): it saw an obstacle within 5 m on
10 of them, most of them open paths. This version measures that properly,
using what the human driver did next as the label:

- From each ride it takes front-camera frames (stream uid_s_1000, 1024x576)
  at fixed offsets inside a few HLS segments. A segment's file name is its
  start time in UTC, so a frame's time is that plus the offset.
- It reads the ride's control log and, from each frame's time, integrates the
  wheel speed (0.00668 m/s per RPM, FINDINGS-frodobots-2k.md) until the driver
  turns (|angular| above 0.15, or 20 degrees of heading at 30 deg/s per unit),
  stops, reverses or 15 s pass. That distance is a lower bound on how far the
  way straight ahead was clear: the human drove it.
- It runs several variants of the scan on every frame (the default and ones
  that leave out the rover's body at the bottom, allow deeper shadows, take
  wider colour tolerances or need more rows before calling an obstacle).
- A phantom stop is a frame where the scan sees less than 1.2 m clear (the
  guard would turn in place) but the driver then drove at least 2 m straight;
  a phantom swerve is less than 5 m clear (the guard would bend or slow) when
  the driver drove at least 5.5 m straight.
- To check that the video and control clocks agree, it takes a second frame
  0.5 s after each one and correlates how much the image changed with the
  wheel speed, at clock offsets from -4 to 4 s.

    python frodo_frames.py --out-dir out --parts all --rides-per-part 2 --segments 4

Needs ffmpeg and Pillow. By MV2 of Munim, Inc.; written with AI agents. Apache-2.0.
"""

from __future__ import annotations

import argparse
import bisect
import collections
import datetime
import io
import json
import math
import os
import re
import subprocess
import sys
import tempfile
import time

import free_space
import frodo_motion as fm

__version__ = "0.2.0"

RIDE_RE = re.compile(r"ride_(\d+)_(\d{14})")
SEG_RE = re.compile(r"^(.*?)(\d+)\.ts$")
SEG_TIME_RE = re.compile(r"_(\d{17})\.ts$")
CONTROL_RE = re.compile(r"control_data_[^/]*\.csv$")
FRONT = "uid_s_1000__uid_e_video"
SAFE_M = 5.0   # VisionGuard's safe_m: less than this ahead and the pilot steers or slows
STOP_M = 1.2   # VisionGuard's stop_m: less than this and it turns in place
MPS_PER_RPM = 0.00668
MPS_PER_LINEAR = 0.79
PAIR_S = 0.5   # second frame for the clock check, this long after the first
LAGS = [x / 2.0 for x in range(-8, 9)]

VARIANTS = {
    "default": {},
    "skip3": {"skip_rows": 3},
    "skip5": {"skip_rows": 5},
    "shadow": {"lum_lo": 0.2, "lum_hi": 2.5},
    "wide": {"chroma_tol": 0.05, "max_tol": 0.12},
    "gap4": {"gap": 4},
    "skip3-shadow-gap4": {"skip_rows": 3, "lum_lo": 0.2, "lum_hi": 2.5, "gap": 4},
    "skip3-shadow-wide-gap4": {"skip_rows": 3, "lum_lo": 0.2, "lum_hi": 2.5,
                               "chroma_tol": 0.05, "max_tol": 0.12, "gap": 4},
}


def ride_key(name):
    m = RIDE_RE.search(name)
    return name[:m.end()] if m else None


def stream_of(base):
    """(stream prefix, segment number) of a .ts file name, or None."""
    m = SEG_RE.match(base)
    return (m.group(1), int(m.group(2))) if m else None


def seg_time(name):
    """UTC seconds since the epoch at which a segment named ..._YYYYmmddHHMMSSfff.ts starts."""
    m = SEG_TIME_RE.search(name)
    if not m:
        return None
    d = m.group(1)
    t = datetime.datetime.strptime(d[:14], "%Y%m%d%H%M%S").replace(tzinfo=datetime.timezone.utc)
    return t.timestamp() + int(d[14:]) / 1000.0


def pick_evenly(items, k):
    if len(items) <= k:
        return list(items)
    return [items[(2 * j + 1) * len(items) // (2 * k)] for j in range(k)]


# --- what the driver did --------------------------------------------------

def wheel_speed(row):
    """Forward speed in m/s from a control row's signed RPMs (the command if none)."""
    rpms = [x for x in row[3] if x is not None]
    if rpms:
        return sum(rpms) / len(rpms) * MPS_PER_RPM
    return row[1] * MPS_PER_LINEAR


def wheel_motion(row):
    """How fast the wheels turn at all (spinning in place counts), m/s."""
    rpms = [abs(x) for x in row[3] if x is not None]
    if rpms:
        return sum(rpms) / len(rpms) * MPS_PER_RPM
    return abs(row[1]) * MPS_PER_LINEAR


def nearest(ctl, times, t, within_s=0.3):
    if not ctl:
        return None
    i = bisect.bisect_left(times, t)
    best = None
    for k in (i - 1, i):
        if 0 <= k < len(ctl) and abs(times[k] - t) <= within_s:
            if best is None or abs(times[k] - t) < abs(times[best] - t):
                best = k
    return None if best is None else ctl[best]


def drive_ahead(ctl, times, t, horizon_s=15.0, max_angular=0.15, max_turn_deg=20.0,
                yaw_dps=30.0, stop_mps=0.05, stop_s=1.0, max_dt=0.5, near_s=1.0):
    """Metres the driver drove straight on after time t, and why it ended; None without data."""
    i = bisect.bisect_left(times, t)
    if i >= len(ctl) or ctl[i][0] - t > near_s:
        return None
    dist = turn = still = 0.0
    ended = "end"
    while i < len(ctl):
        ti, lin, ang, _ = ctl[i]
        if ti > t + horizon_s:
            ended = "horizon"
            break
        if abs(ang) > max_angular:
            ended = "turn"
            break
        if lin < 0:
            ended = "reverse"
            break
        gap = (ctl[i + 1][0] if i + 1 < len(ctl) else ti) - ti
        if gap > 2.0:
            ended = "gap"
            break
        dt = min(gap, max_dt)
        v = wheel_speed(ctl[i])
        dist += max(0.0, v) * dt
        turn += ang * yaw_dps * dt
        if abs(turn) > max_turn_deg:
            ended = "curve"
            break
        still = still + dt if v < stop_mps else 0.0
        if still >= stop_s:
            ended = "stop"
            break
        i += 1
    return {"dist_m": round(dist, 2), "ended": ended}


def events(ctl, times, t):
    """Moving at t, then stopping or turning hard soon after: a hint (not proof) of an obstacle."""
    now = nearest(ctl, times, t)
    if now is None:
        return None
    lo, mid, hi = bisect.bisect_left(times, t), bisect.bisect_left(times, t + 0.5), \
        bisect.bisect_right(times, t + 3.0)
    after = [wheel_speed(r) for r in ctl[mid:hi]]
    turns = [abs(r[2]) for r in ctl[lo:bisect.bisect_right(times, t + 2.0)]]
    moving = wheel_speed(now) >= 0.2
    stopped = bool(after) and sum(after) / len(after) < 0.05
    hard_turn = bool(turns) and max(turns) >= 0.5
    return {"moving": moving, "stopped_after": stopped, "hard_turn_after": hard_turn,
            "event": moving and (stopped or hard_turn)}


# --- the clock check ------------------------------------------------------

def pearson(xs, ys):
    n = len(xs)
    if n < 10:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx <= 0 or syy <= 0:
        return None
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / math.sqrt(sxx * syy)


def clock_lag(samples, motion_at, lags=LAGS):
    """For each lag L, the correlation of image change with wheel motion at t + L.

    samples: [(ride, t, energy)]; motion_at(ride, t) -> m/s or None.
    Returns ({lag: {"r", "n"}}, best lag or None).
    """
    table, best, best_r = {}, None, None
    for lag in lags:
        xs, ys = [], []
        for ride, t, energy in samples:
            m = motion_at(ride, t + lag)
            if m is not None and energy is not None:
                xs.append(energy)
                ys.append(m)
        r = pearson(xs, ys)
        table[lag] = {"r": None if r is None else round(r, 3), "n": len(xs)}
        if r is not None and (best_r is None or r > best_r):
            best, best_r = lag, r
    return table, best


# --- the scan -------------------------------------------------------------

def check_variant(frame, camera, settings):
    s = dict(settings)
    skip = s.pop("skip_rows", 0)
    gap = s.pop("gap", 2)
    model = free_space.GroundModel.fit(free_space.ground_patch(frame, skip_rows=skip))
    points = free_space.scan(frame, camera, model, max_range_m=8.0, gap=gap, skip_rows=skip, **s)
    return {"clear": round(free_space.clearance(points, 0.0, 0.4, 8.0), 2), "cols": len(points)}


def image_change(a, b):
    """Mean absolute difference per channel between two frames of the same size, 0-255."""
    total = 0
    for p, q in zip(a.pixels, b.pixels):
        total += abs(p[0] - q[0]) + abs(p[1] - q[1]) + abs(p[2] - q[2])
    return total / (3.0 * len(a.pixels))


def wilson(k, n, z=1.96):
    if n == 0:
        return None
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return [round((c - h) / d, 3), round((c + h) / d, 3)]


def summarise(frames, key="drive"):
    out = {}
    d2 = [f for f in frames if f.get(key) and f[key]["dist_m"] >= 2.0]
    d55 = [f for f in d2 if f[key]["dist_m"] >= 5.5]
    ev = [f for f in frames if f.get("events") and f["events"]["event"]]
    for name in VARIANTS:
        stop = sum(1 for f in d2 if f["variants"][name]["clear"] < STOP_M)
        slow = sum(1 for f in d55 if f["variants"][name]["clear"] < SAFE_M)
        agree = sum(1 for f in d2 if f["variants"][name]["clear"]
                    >= min(f[key]["dist_m"], SAFE_M) - 0.5)
        blocked_ev = sum(1 for f in ev if f["variants"][name]["clear"] < SAFE_M)
        out[name] = {
            "drove_2m": len(d2), "phantom_stops": stop,
            "phantom_stop_rate": round(stop / len(d2), 3) if d2 else None,
            "phantom_stop_ci95": wilson(stop, len(d2)),
            "drove_5_5m": len(d55), "phantom_swerves": slow,
            "phantom_swerve_rate": round(slow / len(d55), 3) if d55 else None,
            "phantom_swerve_ci95": wilson(slow, len(d55)),
            "agrees_with_driver": round(agree / len(d2), 3) if d2 else None,
            "event_frames": len(ev),
            "blocked_on_event_frames": round(blocked_ev / len(ev), 3) if ev else None,
        }
    return out


# --- reading the rides ----------------------------------------------------

def run(cmd, timeout=120):
    p = subprocess.run(cmd, capture_output=True, timeout=timeout)
    return p.returncode, p.stdout, p.stderr.decode("utf-8", "replace")[-400:]


def grab(ts_path, offset_s, jpg_path):
    """JPEG bytes of the frame `offset_s` into a segment, or None."""
    if os.path.exists(jpg_path):
        os.remove(jpg_path)
    code, _, _ = run(["ffmpeg", "-v", "error", "-y", "-ss", "%.2f" % offset_s, "-i", ts_path,
                      "-frames:v", "1", "-q:v", "3", jpg_path])
    if code != 0 or not os.path.exists(jpg_path):
        return None
    with open(jpg_path, "rb") as f:
        return f.read()


def save_thumb(jpg, path):
    from PIL import Image
    with Image.open(io.BytesIO(jpg)) as im:
        im.convert("RGB").resize((320, 180)).save(path, quality=80)


def process_ride(rz, part, ride, entries, args, camera, tmp, out_dir):
    info = {"ride": ride}
    ctl_entry = next((e for e in entries if CONTROL_RE.search(e.name)), None)
    segs = []
    for e in entries:
        base = e.name.rsplit("/", 1)[-1]
        s = stream_of(base) if base.endswith(".ts") else None
        if s and FRONT in s[0]:
            segs.append((s[1], e))
    segs.sort()
    header, rows = fm.parse_csv(rz.read(ctl_entry))
    ctl = fm.load_control(header, rows)
    info.update(control_rows=len(ctl), front_segments=len(segs))
    if ctl:
        info["control_span"] = [ctl[0][0], ctl[-1][0]]
    if segs:
        info["video_span"] = [seg_time(segs[0][1].name), seg_time(segs[-1][1].name)]
    samples = []
    offsets = [float(x) for x in args.offsets.split(",")]
    for num, e in pick_evenly(segs, args.segments):
        if e.usize > args.max_seg_mb * (1 << 20):
            continue
        t0 = seg_time(e.name)
        if t0 is None:
            continue
        try:
            ts_path = os.path.join(tmp, "seg.ts")
            with open(ts_path, "wb") as f:
                f.write(rz.read(e))
        except Exception as exc:
            info.setdefault("errors", []).append("%s: %s" % (type(exc).__name__, exc))
            continue
        for off in offsets:
            a = grab(ts_path, off, os.path.join(tmp, "a.jpg"))
            if a is None:
                continue
            b = grab(ts_path, off + PAIR_S, os.path.join(tmp, "b.jpg"))
            fa = free_space.decode_frame(a, camera.width, camera.height)
            fb = free_space.decode_frame(b, camera.width, camera.height) if b else None
            tag = re.sub(r"[^A-Za-z0-9]+", "_", "%s_%d_%g" % (
                ride.rsplit("/", 1)[-1], num, off)).strip("_")
            save_thumb(a, os.path.join(out_dir, "frames", tag + ".jpg"))
            ground = free_space.GroundModel.fit(free_space.ground_patch(fa))
            samples.append({
                "part": part, "ride": ride, "segment": num, "offset_s": off,
                "t": round(t0 + off, 3), "thumb": tag + ".jpg",
                "energy": None if fb is None else round(image_change(fa, fb), 2),
                "ground_lum": round(ground.lum, 1),
                "variants": {name: check_variant(fa, camera, v) for name, v in VARIANTS.items()},
            })
    info["frames"] = len(samples)
    return info, samples, ctl


def label(frames, controls, lag=0.0, key="drive"):
    for f in frames:
        ctl, times = controls.get(f["ride"], ([], []))
        f[key] = drive_ahead(ctl, times, f["t"] + lag)
        if lag == 0.0:
            f["events"] = events(ctl, times, f["t"])


def write_outputs(out_dir, result, frames):
    with open(os.path.join(out_dir, "summary.json"), "w") as f:
        json.dump(result, f, indent=1)
    with open(os.path.join(out_dir, "frames.jsonl"), "w") as f:
        for fr in frames:
            f.write(json.dumps(fr) + "\n")


def report(result):
    lines = ["# Front-camera obstacle check on FrodoBots-2K: phantom obstacles",
             "",
             "frodo_frames.py %s, free_space.py %s, MV2 of Munim, Inc. Data: FrodoBots-2K, "
             "FrodoBots Lab, CC BY-SA 4.0. Frames: %d front-camera frames from %d rides; "
             "%d with control data at the frame's time."
             % (__version__, free_space.__version__, result["frames"], result["rides"],
                result["labelled"]),
             "",
             "Phantom stop: scan sees < 1.2 m clear, driver then drove >= 2 m straight. "
             "Phantom swerve: scan sees < 5 m clear, driver drove >= 5.5 m straight. "
             "Event frames: moving, then stopped or turned hard within 3 s (a hint of an "
             "obstacle, not proof).",
             "",
             "| variant | drove >= 2 m | phantom stops | 95% CI | drove >= 5.5 m | phantom swerves "
             "| 95% CI | agrees | blocked on event frames |",
             "|---|---|---|---|---|---|---|---|---|"]
    for name, s in result["by_variant"].items():
        lines.append("| %s | %d | %s | %s | %d | %s | %s | %s | %s |" % (
            name, s["drove_2m"], s["phantom_stop_rate"], s["phantom_stop_ci95"],
            s["drove_5_5m"], s["phantom_swerve_rate"], s["phantom_swerve_ci95"],
            s["agrees_with_driver"], s["blocked_on_event_frames"]))
    lines += ["", "Clock check (image change vs wheel motion at t + lag): best lag %s s"
              % result["clock_best_lag_s"], "",
              "| lag s | r | n |", "|---|---|---|"]
    for lag, row in result["clock_lag"].items():
        lines.append("| %s | %s | %s |" % (lag, row["r"], row["n"]))
    return "\n".join(lines) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--index-url", default=fm.INDEX_URL)
    ap.add_argument("--parts", default="all", help="comma-separated part numbers, or all")
    ap.add_argument("--rides-per-part", type=int, default=2)
    ap.add_argument("--segments", type=int, default=4, help="front-camera segments read per ride")
    ap.add_argument("--offsets", default="2,7,12", help="seconds into each segment to take frames")
    ap.add_argument("--min-segments", type=int, default=6,
                    help="prefer rides with at least this many front-camera segments")
    ap.add_argument("--max-seg-mb", type=float, default=30.0)
    ap.add_argument("--max-cd-mb", type=float, default=800.0)
    ap.add_argument("--budget-min", type=float, default=150.0)
    ap.add_argument("--out-dir", default="out")
    args = ap.parse_args(argv)
    os.makedirs(os.path.join(args.out_dir, "frames"), exist_ok=True)
    started = time.monotonic()
    camera = free_space.Camera()
    parts, frames, controls = [], [], {}
    try:
        index = fm.read_index(args.index_url)
    except Exception as exc:
        parts.append({"error": "index: %s: %s" % (type(exc).__name__, exc)})
        index = []
    if args.parts != "all":
        keep = {int(p) for p in args.parts.split(",") if p.strip()}
        index = [(n, u) for n, u in index if n in keep]
    done = True
    with tempfile.TemporaryDirectory() as tmp:
        for n, url in index:
            label_ = "output_rides_%d" % n
            if time.monotonic() - started > args.budget_min * 60.0:
                parts.append({"part": label_, "skipped": "time budget"})
                done = False
                continue
            info = {"part": label_, "rides_checked": []}
            try:
                rz = fm.RemoteZip(fm.http_size(url), lambda s, k, u=url: fm.http_range(u, s, k))
                if rz.cd_size > args.max_cd_mb * (1 << 20):
                    info["skipped"] = "central directory %d bytes" % rz.cd_size
                else:
                    rides = collections.defaultdict(list)
                    for e in rz.entries():
                        key = ride_key(e.name)
                        if key:
                            rides[key].append(e)

                    def front_count(es):
                        return sum(1 for e in es if e.name.endswith(".ts") and FRONT in e.name)
                    usable = sorted(k for k, es in rides.items() if front_count(es)
                                    and any(CONTROL_RE.search(e.name) for e in es))
                    long_ = [k for k in usable if front_count(rides[k]) >= args.min_segments]
                    info.update(rides=len(rides), usable=len(usable), long=len(long_))
                    for ride in pick_evenly(long_ or usable, args.rides_per_part):
                        try:
                            rinfo, samples, ctl = process_ride(rz, label_, ride, rides[ride], args,
                                                               camera, tmp, args.out_dir)
                        except Exception as exc:
                            rinfo, samples, ctl = {"ride": ride, "error": "%s: %s" % (
                                type(exc).__name__, exc)}, [], []
                        info["rides_checked"].append(rinfo)
                        frames.extend(samples)
                        controls[ride] = (ctl, [r[0] for r in ctl])
                info["bytes_read"] = rz.bytes_read
            except Exception as exc:
                info["error"] = "%s: %s" % (type(exc).__name__, exc)
            parts.append(info)
            print("%s: %d frames so far, %.0f s" % (label_, len(frames),
                                                    time.monotonic() - started), flush=True)

    def motion_at(ride, t):
        ctl, times = controls.get(ride, ([], []))
        row = nearest(ctl, times, t)
        return None if row is None else wheel_motion(row)

    pairs = [(f["ride"], f["t"] + PAIR_S / 2.0, f["energy"]) for f in frames]
    lag_table, best_lag = clock_lag(pairs, motion_at)
    label(frames, controls)
    if best_lag not in (None, 0.0):
        label(frames, controls, lag=best_lag, key="drive_at_best_lag")
    result = {"version": __version__, "free_space": free_space.__version__, "done": done,
              "data": "FrodoBots-2K, FrodoBots Lab, CC BY-SA 4.0",
              "elapsed_s": round(time.monotonic() - started, 1),
              "bytes_read": sum(p.get("bytes_read", 0) for p in parts),
              "rides": sum(len(p.get("rides_checked", [])) for p in parts),
              "frames": len(frames), "labelled": sum(1 for f in frames if f.get("drive")),
              "ended": dict(collections.Counter(f["drive"]["ended"] for f in frames
                                                if f.get("drive"))),
              "variants": VARIANTS, "by_variant": summarise(frames),
              "clock_lag": {str(k): v for k, v in lag_table.items()},
              "clock_best_lag_s": best_lag, "parts": parts}
    if best_lag not in (None, 0.0):
        result["by_variant_at_best_lag"] = summarise(frames, key="drive_at_best_lag")
    write_outputs(args.out_dir, result, frames)
    text = report(result)
    with open(os.path.join(args.out_dir, "report.md"), "w") as f:
        f.write(text)
    print(text, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
