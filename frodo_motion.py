#!/usr/bin/env python3
"""frodo_motion: how FrodoBots Earth Rovers actually move, measured from FrodoBots-2K.

The Earth Rover SDK doesn't say which way a positive `angular` turns the rover,
how fast it goes at a given command, or how late its GPS is. FrodoBots-2K
(about 2,000 hours of human-driven Earth Rover rides, CC BY-SA 4.0, FrodoBots
Lab) logs the driver's commands, the four wheel RPMs and GPS for every ride,
so the data can answer these questions.

The dataset comes as 24 zip files of 2 to 95 GB, mostly video. This script
reads only what it needs over HTTP range requests: each zip's central
directory, then the control and GPS CSVs of a sample of rides from every part.

For each ride it lines the commands up with GPS, at lags from -3 to 10 s:
- turning: the rate of change of the GPS course against the commanded
  angular. The sign of the correlation says which way a positive angular turns
  the rover; the lag with the strongest correlation is the delay from command
  to GPS.
- speed: GPS speed against the mean wheel RPM and against the commanded linear.
- wheel RPMs: whether they ever go negative (reversing, spinning in place).

    python frodo_motion.py --out-dir out --rides-per-part 12

Standard library only. By MV2 of Munim, Inc.; written with AI agents. Apache-2.0.
"""

from __future__ import annotations

import argparse
import bisect
import collections
import csv
import io
import json
import math
import os
import re
import struct
import sys
import time
import urllib.request
import zlib

__version__ = "0.1.0"

INDEX_URL = "https://frodobots-2k-dataset.s3.ap-southeast-1.amazonaws.com/complete-dataset.csv"
USER_AGENT = ("frodo-motion/%s (MV2 of Munim, Inc.; "
              "https://github.com/munimtechnologies/earth-rover-pilot)" % __version__)
LAGS = [x / 2.0 for x in range(-6, 21)]      # -3.0 .. 10.0 s, GPS behind control
RPM_LAGS = [x / 5.0 for x in range(0, 16)]   # 0.0 .. 3.0 s, RPM behind command
STRIDES = (1, 2, 3)                          # GPS fixes per course segment
KIND_RE = re.compile(r"(?:^|/)(control_data|gps_data|imu_data)_[^/]*\.csv$")
RIDE_RE = re.compile(r"ride_(\d+)_(\d{14})")
LIN_EDGES = (0.1, 0.3, 0.5, 0.7, 0.9, 1.01)
R_EARTH = 6371000.0

ZipEntry = collections.namedtuple("ZipEntry", "name method crc csize usize offset")


# --- HTTP -----------------------------------------------------------------

def _request(url, headers=None, method=None, expect=200, tries=4):
    """(headers, body) of a request that answers with status `expect`. The body
    is not read for HEAD or for any other status, so a server that ignores a
    Range header never sends a whole 95 GB part."""
    hdrs = {"User-Agent": USER_AGENT}
    hdrs.update(headers or {})
    delay = 2.0
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers=hdrs, method=method)
            with urllib.request.urlopen(req, timeout=90) as resp:
                if resp.status != expect:
                    raise RuntimeError("HTTP %s, expected %s" % (resp.status, expect))
                return resp.headers, resp.read() if method != "HEAD" else b""
        except Exception:
            if attempt == tries - 1:
                raise
            time.sleep(delay)
            delay *= 2


def http_size(url):
    headers, _ = _request(url, method="HEAD")
    return int(headers["Content-Length"])


def http_range(url, start, length):
    _, data = _request(url, {"Range": "bytes=%d-%d" % (start, start + length - 1)}, expect=206)
    if len(data) != length:
        raise RuntimeError("asked for %d bytes at %d, got %d" % (length, start, len(data)))
    return data


# --- Zip over range reads -------------------------------------------------

def zip64_values(usize, csize, offset, extra):
    """Sizes and offset of a central directory entry, taking the ones stored
    as 0xFFFFFFFF from its zip64 extra field."""
    k = 0
    while k + 4 <= len(extra):
        tag, size = struct.unpack_from("<HH", extra, k)
        if tag == 1:
            vals, q = extra[k + 4:k + 4 + size], 0
            if usize == 0xFFFFFFFF:
                usize = struct.unpack_from("<Q", vals, q)[0]
                q += 8
            if csize == 0xFFFFFFFF:
                csize = struct.unpack_from("<Q", vals, q)[0]
                q += 8
            if offset == 0xFFFFFFFF:
                offset = struct.unpack_from("<Q", vals, q)[0]
            break
        k += 4 + size
    return usize, csize, offset


class RemoteZip:
    """Reads a zip file through fetch(start, length), without downloading it."""

    def __init__(self, size, fetch):
        self.size, self.fetch = size, fetch
        self.bytes_read = 0
        self.cd_offset, self.cd_size, self.count = self._find_directory()

    def _read(self, start, length):
        data = self.fetch(start, length)
        self.bytes_read += len(data)
        return data

    def _find_directory(self):
        tail_len = min(self.size, 22 + 65535 + 20)
        tail = self._read(self.size - tail_len, tail_len)
        pos = tail.rfind(b"PK\x05\x06")
        if pos < 0 or pos + 22 > len(tail):
            raise ValueError("no end-of-central-directory record")
        _, _, _, _, count, cd_size, cd_offset, _ = struct.unpack("<4sHHHHIIH", tail[pos:pos + 22])
        if count == 0xFFFF or cd_size == 0xFFFFFFFF or cd_offset == 0xFFFFFFFF:
            loc = pos - 20
            if loc < 0 or tail[loc:loc + 4] != b"PK\x06\x07":
                raise ValueError("zip64 locator missing")
            _, _, rec_offset, _ = struct.unpack("<4sIQI", tail[loc:loc + 20])
            rec = self._read(rec_offset, 56)
            if rec[:4] != b"PK\x06\x06":
                raise ValueError("zip64 end record missing")
            _, _, _, _, _, _, _, count, cd_size, cd_offset = struct.unpack("<4sQHHIIQQQQ", rec)
        return cd_offset, cd_size, count

    def entries(self, want=None, chunk=8 << 20):
        """Yield a ZipEntry for each name that want(name) accepts (every name
        if want is None), reading the central directory chunk by chunk."""
        state = {"buf": b"", "i": 0, "pos": self.cd_offset}
        end = self.cd_offset + self.cd_size

        def need(n):
            while len(state["buf"]) - state["i"] < n:
                if state["pos"] >= end:
                    return False
                take = min(chunk, end - state["pos"])
                state["buf"] = state["buf"][state["i"]:] + self._read(state["pos"], take)
                state["i"] = 0
                state["pos"] += take
            return True

        while need(46):
            buf, i = state["buf"], state["i"]
            head = struct.unpack_from("<4sHHHHHHIIIHHHHHII", buf, i)
            if head[0] != b"PK\x01\x02":
                raise ValueError("bad central directory entry")
            n_len, e_len, c_len = head[10], head[11], head[12]
            if not need(46 + n_len + e_len + c_len):
                raise ValueError("central directory cut short")
            buf, i = state["buf"], state["i"]
            j = i + 46
            name = buf[j:j + n_len].decode("utf-8", "replace")
            extra = buf[j + n_len:j + n_len + e_len]
            state["i"] = j + n_len + e_len + c_len
            if want is not None and not want(name):
                continue
            usize, csize, offset = zip64_values(head[9], head[8], head[16], extra)
            yield ZipEntry(name, head[4], head[7], csize, usize, offset)

    def read(self, entry, slack=1024):
        """The uncompressed bytes of one entry, checked against its CRC."""
        length = min(30 + len(entry.name.encode("utf-8")) + slack + entry.csize,
                     self.size - entry.offset)
        data = self._read(entry.offset, length)
        if data[:4] != b"PK\x03\x04":
            raise ValueError("bad local header for %s" % entry.name)
        n_len, e_len = struct.unpack_from("<HH", data, 26)
        start = 30 + n_len + e_len
        if start + entry.csize > len(data):
            data += self._read(entry.offset + len(data), start + entry.csize - len(data))
        comp = data[start:start + entry.csize]
        if entry.method == 0:
            raw = comp
        elif entry.method == 8:
            d = zlib.decompressobj(-15)
            raw = d.decompress(comp) + d.flush()
        else:
            raise ValueError("compression method %d not supported" % entry.method)
        if zlib.crc32(raw) & 0xFFFFFFFF != entry.crc:
            raise ValueError("CRC mismatch for %s" % entry.name)
        return raw


def group_rides(entries):
    """{ride folder: {kind: ZipEntry}} for the control, GPS and IMU CSVs.
    If a ride has two files of one kind, the larger one is kept."""
    rides = {}
    for e in entries:
        m = KIND_RE.search(e.name)
        if not m:
            continue
        slot = rides.setdefault(e.name[:m.start()], {})
        old = slot.get(m.group(1))
        if old is None or e.usize > old.usize:
            slot[m.group(1)] = e
    return rides


def pick_evenly(keys, k):
    keys = sorted(keys)
    if len(keys) <= k:
        return keys
    return [keys[(2 * j + 1) * len(keys) // (2 * k)] for j in range(k)]


# --- CSV loading ----------------------------------------------------------

def parse_csv(raw):
    rows = list(csv.reader(io.StringIO(raw.decode("utf-8-sig", "replace"))))
    if not rows:
        return [], []
    return [h.strip() for h in rows[0]], rows[1:]


def number(s):
    try:
        x = float(s)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) else None


def norm_t(t):
    """Seconds since the epoch, from seconds, milliseconds or microseconds."""
    if t > 1e14:
        return t / 1e6
    if t > 1e11:
        return t / 1e3
    return t


def column(header, *names):
    for n in names:
        if n in header:
            return header.index(n)
    return None


def _cell(row, k):
    return number(row[k]) if k is not None and k < len(row) else None


def load_control(header, rows):
    """[(t, linear, angular, [rpm_1..rpm_4])] sorted by time; a missing RPM is None."""
    it = column(header, "timestamp")
    il = column(header, "linear", "speed")
    ia = column(header, "angular")
    ir = [column(header, "rpm_%d" % k) for k in (1, 2, 3, 4)]
    if it is None or il is None or ia is None:
        raise ValueError("control columns not found in %s" % header)
    out = []
    for row in rows:
        t, lin, ang = _cell(row, it), _cell(row, il), _cell(row, ia)
        if t is None or lin is None or ang is None:
            continue
        out.append((norm_t(t), lin, ang, [_cell(row, k) for k in ir]))
    out.sort(key=lambda r: r[0])
    return out


def load_gps(header, rows):
    """[(t, lat, lon)] sorted by time, without no-fix values or repeated times."""
    it = column(header, "timestamp")
    ila = column(header, "latitude", "lat")
    ilo = column(header, "longitude", "lon", "lng")
    if it is None or ila is None or ilo is None:
        raise ValueError("GPS columns not found in %s" % header)
    fixes = []
    for row in rows:
        t, lat, lon = _cell(row, it), _cell(row, ila), _cell(row, ilo)
        if t is None or lat is None or lon is None:
            continue
        if abs(lat) > 90 or abs(lon) > 180 or (abs(lat) < 1e-6 and abs(lon) < 1e-6):
            continue
        fixes.append((norm_t(t), lat, lon))
    fixes.sort()
    out = []
    for f in fixes:
        if not out or f[0] > out[-1][0]:
            out.append(f)
    return out


# --- Statistics -----------------------------------------------------------

class Series:
    """Mean of a time series over any window, from prefix sums."""

    def __init__(self, times, values):
        self.t = list(times)
        self.cum = [0.0]
        for v in values:
            self.cum.append(self.cum[-1] + v)

    def mean(self, a, b):
        i = bisect.bisect_left(self.t, a)
        j = bisect.bisect_right(self.t, b)
        if j <= i:
            return None
        return (self.cum[j] - self.cum[i]) / (j - i)


class Acc:
    """Running sums for a correlation, a slope through the origin and a sign test."""

    __slots__ = ("n", "sx", "sy", "sxx", "syy", "sxy", "agree", "disagree")

    def __init__(self):
        self.n = self.agree = self.disagree = 0
        self.sx = self.sy = self.sxx = self.syy = self.sxy = 0.0

    def add(self, x, y, xmin=None, ymin=None):
        self.n += 1
        self.sx += x
        self.sy += y
        self.sxx += x * x
        self.syy += y * y
        self.sxy += x * y
        if xmin is not None and abs(x) >= xmin and abs(y) >= ymin:
            if (x > 0) == (y > 0):
                self.agree += 1
            else:
                self.disagree += 1

    def merge(self, other):
        for name in self.__slots__:
            setattr(self, name, getattr(self, name) + getattr(other, name))

    def corr(self):
        if self.n < 3:
            return None
        vx = self.n * self.sxx - self.sx ** 2
        vy = self.n * self.syy - self.sy ** 2
        if vx <= 0 or vy <= 0:
            return None
        return (self.n * self.sxy - self.sx * self.sy) / math.sqrt(vx * vy)

    def slope0(self):
        return self.sxy / self.sxx if self.sxx > 0 else None

    def as_dict(self):
        c, s = self.corr(), self.slope0()
        return {"n": self.n, "corr": None if c is None else round(c, 4),
                "slope0": None if s is None else round(s, 5),
                "agree": self.agree, "disagree": self.disagree}


class Bins:
    """Mean and spread of GPS speed for bands of commanded linear."""

    def __init__(self):
        k = len(LIN_EDGES) - 1
        self.n, self.s, self.ss = [0] * k, [0.0] * k, [0.0] * k

    def add(self, x, y):
        for i in range(len(self.n)):
            if LIN_EDGES[i] <= x < LIN_EDGES[i + 1]:
                self.n[i] += 1
                self.s[i] += y
                self.ss[i] += y * y
                return

    def merge(self, other):
        for i in range(len(self.n)):
            self.n[i] += other.n[i]
            self.s[i] += other.s[i]
            self.ss[i] += other.ss[i]

    def as_list(self):
        out = []
        for i, n in enumerate(self.n):
            mean = self.s[i] / n if n else None
            sd = math.sqrt(max(0.0, self.ss[i] / n - mean * mean)) if n else None
            out.append({"linear": "%.1f-%.1f" % (LIN_EDGES[i], min(LIN_EDGES[i + 1], 1.0)), "n": n,
                        "mean_mps": None if mean is None else round(mean, 3),
                        "sd_mps": None if sd is None else round(sd, 3)})
        return out


def to_enu(lat0, lon0, lat, lon):
    k = math.pi / 180.0 * R_EARTH
    return (lon - lon0) * k * math.cos(math.radians(lat0)), (lat - lat0) * k


def wrap180(d):
    return (d + 180.0) % 360.0 - 180.0


def _mean(values):
    return round(sum(values) / len(values), 2) if values else None


def best_lag(by_lag, min_n=100):
    """The lag whose correlation is strongest, with its numbers, or None."""
    best = None
    for lag, acc in by_lag.items():
        c = acc.corr()
        if acc.n < min_n or c is None:
            continue
        if best is None or abs(c) > abs(best[1]):
            best = (lag, c, acc)
    if best is None:
        return None
    out = {"lag_s": best[0]}
    out.update(best[2].as_dict())
    return out


def analyse_ride(control, gps, pooled, bins):
    """Stats for one ride; its samples are added to `pooled` ({(family, stride,
    lag): Acc}) and `bins` ({(stride, lag): Bins})."""
    st = {"control_rows": len(control), "gps_fixes": len(gps)}
    if len(control) < 50 or len(gps) < 20:
        st["skipped"] = "too little data"
        return st
    ts = [r[0] for r in control]
    lin = [r[1] for r in control]
    ang = [r[2] for r in control]
    span = ts[-1] - ts[0]
    st.update(duration_s=round(span, 1),
              control_hz=round((len(ts) - 1) / span, 2) if span > 0 else None,
              linear_range=[min(lin), max(lin)], angular_range=[min(ang), max(ang)],
              gps_start_minus_control_start_s=round(gps[0][0] - ts[0], 1),
              gps_span_s=round(gps[-1][0] - gps[0][0], 1))

    full = [r for r in control if all(v is not None for v in r[3])]
    st["rpm_rows"] = len(full)
    st["rpm_negative_rows"] = sum(1 for r in full if min(r[3]) < 0)
    rev = [r for r in full if r[1] <= -0.2]
    st["reverse_rows"] = len(rev)
    st["reverse_mean_rpm"] = _mean([sum(r[3]) / 4.0 for r in rev])
    spin = [r for r in full if abs(r[1]) < 0.05 and abs(r[2]) >= 0.3]
    st["spin_rows"] = len(spin)
    st["spin_mean_left_rpm"] = _mean([(r[3][0] + r[3][2]) / 2.0 for r in spin])
    st["spin_mean_right_rpm"] = _mean([(r[3][1] + r[3][3]) / 2.0 for r in spin])
    st["spin_opposite_sides"] = sum(1 for r in spin
                                    if (r[3][0] + r[3][2]) * (r[3][1] + r[3][3]) < 0)

    local, local_bins = {}, {}

    def acc(key):
        a = local.get(key)
        if a is None:
            a = local[key] = Acc()
        return a

    lin_s, ang_s = Series(ts, lin), Series(ts, ang)
    rpm_s = Series([r[0] for r in full], [sum(abs(v) for v in r[3]) / 4.0 for r in full]) \
        if full else None
    cmd_s = Series(ts, [max(abs(a), abs(b)) for a, b in zip(lin, ang)])

    gt = [g[0] for g in gps]
    pts = [to_enu(gps[0][1], gps[0][2], g[1], g[2]) for g in gps]
    for s in STRIDES:
        segs = []
        for k in range(len(gps) - s):
            dt = gt[k + s] - gt[k]
            if not 0.5 * s <= dt <= 2.5 * s:
                segs.append(None)
                continue
            de, dn = pts[k + s][0] - pts[k][0], pts[k + s][1] - pts[k][1]
            segs.append((dt, math.hypot(de, dn), math.degrees(math.atan2(de, dn))))
        for k, seg in enumerate(segs):
            if seg is None:
                continue
            dt, dist, head = seg
            v = dist / dt
            for lag in LAGS:
                a, b = gt[k] - lag, gt[k + s] - lag
                c = lin_s.mean(a, b)
                if c is not None:
                    acc(("speed_lin", s, lag)).add(c, v)
                    local_bins.setdefault((s, lag), Bins()).add(c, v)
                if rpm_s is not None:
                    r = rpm_s.mean(a, b)
                    if r is not None:
                        acc(("speed_rpm", s, lag)).add(r, v)
            if k + s >= len(segs):
                continue
            nxt = segs[k + s]
            if nxt is None or dist < 0.8 * s or nxt[1] < 0.8 * s:
                continue
            # Course rate, clockwise positive, between the middles of two chords.
            w = wrap180(nxt[2] - head) / ((gt[k + 2 * s] - gt[k]) / 2.0)
            for lag in LAGS:
                c = ang_s.mean((gt[k] + gt[k + s]) / 2.0 - lag,
                               (gt[k + s] + gt[k + 2 * s]) / 2.0 - lag)
                if c is not None:
                    acc(("turn", s, lag)).add(c, w, 0.2, 5.0)

    if rpm_s is not None:
        for idx in range(0, len(full), 2):
            t = full[idx][0]
            y = sum(abs(v) for v in full[idx][3]) / 4.0
            for lag in RPM_LAGS:
                c = cmd_s.mean(t - lag - 0.15, t - lag + 0.15)
                if c is not None:
                    acc(("rpm_lag", 0, lag)).add(c, y)

    for fam in ("turn", "speed_rpm"):
        st[fam + "_best"] = best_lag({lag: local[(fam, 2, lag)] for lag in LAGS
                                      if (fam, 2, lag) in local}, min_n=20)
    for key, a in local.items():
        pooled.setdefault(key, Acc()).merge(a)
    for key, b in local_bins.items():
        bins.setdefault(key, Bins()).merge(b)
    return st


# --- Parts, summary and report ---------------------------------------------

def process_part(rz, label, rides_per_part, pooled, bins, rides_out, imu_per_part=1):
    kinds, exts = collections.Counter(), collections.Counter()

    def want(name):
        base = name.rsplit("/", 1)[-1]
        ext = base.rsplit(".", 1)[-1].lower() if "." in base else ""
        exts[ext] += 1
        if ext != "csv":
            return False
        m = re.match(r"^(.*?)_\d", base)
        kinds[m.group(1) if m else base] += 1
        return True

    rides = group_rides(rz.entries(want))
    usable = sorted(r for r, d in rides.items() if "control_data" in d and "gps_data" in d)
    chosen = pick_evenly(usable, rides_per_part)
    info = {"part": label, "zip_bytes": rz.size, "entries": rz.count,
            "central_directory_bytes": rz.cd_size, "csv_kinds": dict(kinds.most_common(20)),
            "extensions": dict(exts.most_common(12)), "rides_with_csvs": len(rides),
            "rides_usable": len(usable), "rides_sampled": len(chosen), "samples": {}}
    for i, ride in enumerate(chosen):
        d = rides[ride]
        st = {"part": label, "ride": ride}
        m = RIDE_RE.search(ride)
        if m:
            st["ride_id"], st["ride_time"] = m.group(1), m.group(2)
        try:
            ch, cr = parse_csv(rz.read(d["control_data"]))
            gh, gr = parse_csv(rz.read(d["gps_data"]))
            if i == 0:
                info["samples"]["control"] = [ch] + cr[:3]
                info["samples"]["gps"] = [gh] + gr[:3]
            st.update(analyse_ride(load_control(ch, cr), load_gps(gh, gr), pooled, bins))
        except Exception as exc:
            st["error"] = "%s: %s" % (type(exc).__name__, exc)
        if i < imu_per_part and "imu_data" in d and d["imu_data"].usize <= 40 << 20:
            try:
                ih, ir = parse_csv(rz.read(d["imu_data"]))
                info["samples"].setdefault("imu", []).append(
                    [ih] + [[c[:300] for c in row] for row in ir[:3]] + [["rows", len(ir)]])
            except Exception as exc:
                info["samples"]["imu_error"] = "%s: %s" % (type(exc).__name__, exc)
        rides_out.append(st)
    info["bytes_read"] = rz.bytes_read
    return info


def summarise(pooled, bins, min_n=100):
    tables = {}
    for (fam, s, lag), acc in pooled.items():
        row = {"lag_s": lag}
        row.update(acc.as_dict())
        tables.setdefault(fam, {}).setdefault(str(s), []).append(row)
    out = {}
    for fam, by_stride in tables.items():
        out[fam] = {}
        for s, rows in by_stride.items():
            rows.sort(key=lambda r: r["lag_s"])
            by_lag = {lag: a for (f, st, lag), a in pooled.items() if f == fam and str(st) == s}
            out[fam][s] = {"best": best_lag(by_lag, min_n), "table": rows}
    lin_best = (out.get("speed_lin", {}).get("2") or {}).get("best")
    if lin_best and (2, lin_best["lag_s"]) in bins:
        out["speed_by_linear"] = {"stride": 2, "lag_s": lin_best["lag_s"],
                                  "bins": bins[(2, lin_best["lag_s"])].as_list()}
    return out


def rpm_sign_totals(rides):
    keys = ("rpm_rows", "rpm_negative_rows", "reverse_rows", "spin_rows", "spin_opposite_sides")
    return {k: sum(r.get(k) or 0 for r in rides) for k in keys}


def conclusions(summary, totals):
    lines = []

    def best(fam, s="2"):
        return ((summary.get(fam) or {}).get(s) or {}).get("best")

    turn = best("turn")
    if turn:
        side = "left (counter-clockwise)" if turn["corr"] < 0 else "right (clockwise)"
        lines.append(
            "Turning: the GPS course rate follows the commanded angular most closely at a lag of "
            "%.1f s (r = %.3f, n = %d; signs agree in %d samples and disagree in %d). On these rides "
            "a positive angular turned the rover %s, at about %.1f deg/s per unit of angular while "
            "driving (clockwise positive)."
            % (turn["lag_s"], turn["corr"], turn["n"], turn["agree"], turn["disagree"], side,
               turn["slope0"] or 0.0))
    sp = best("speed_rpm")
    if sp:
        k = sp["slope0"] or 0.0
        lines.append(
            "GPS delay: GPS speed follows the mean wheel RPM most closely when the GPS is taken "
            "%.1f s after the control log (r = %.3f, n = %d). Speed per RPM (through the origin) "
            "is %.5f m/s, an effective wheel radius of %.3f m."
            % (sp["lag_s"], sp["corr"], sp["n"], k, k * 60.0 / (2.0 * math.pi)))
    sl = best("speed_lin")
    if sl:
        lines.append(
            "Speed per command: %.2f m/s per unit of commanded linear (through the origin), at a "
            "lag of %.1f s (r = %.3f, n = %d)." % (sl["slope0"] or 0.0, sl["lag_s"], sl["corr"], sl["n"]))
    rl = best("rpm_lag", "0")
    if rl:
        lines.append("Wheel response: the mean wheel RPM follows the command size most closely "
                     "%.1f s later (r = %.3f, n = %d)." % (rl["lag_s"], rl["corr"], rl["n"]))
    if totals.get("rpm_rows"):
        lines.append(
            "Wheel RPM sign: %d of %d control rows have a negative RPM. Rows commanding reverse "
            "(linear <= -0.2): %d. Spin-in-place rows (|linear| < 0.05, |angular| >= 0.3): %d, of "
            "which %d show the two sides turning in opposite directions."
            % (totals["rpm_negative_rows"], totals["rpm_rows"], totals["reverse_rows"],
               totals["spin_rows"], totals["spin_opposite_sides"]))
    return lines


def write_outputs(out_dir, parts, rides, summary, started):
    totals = rpm_sign_totals(rides)
    lines = conclusions(summary, totals)
    analysed = [r for r in rides if "error" not in r and "skipped" not in r]
    result = {"version": __version__, "data": "FrodoBots-2K, FrodoBots Lab, CC BY-SA 4.0",
              "elapsed_s": round(time.monotonic() - started, 1), "parts": parts,
              "rides_sampled": len(rides), "rides_analysed": len(analysed),
              "ride_errors": sum(1 for r in rides if "error" in r),
              "bytes_read": sum(p.get("bytes_read", 0) for p in parts),
              "rpm_sign": totals, "conclusions": lines, "results": summary}
    with open(os.path.join(out_dir, "summary.json"), "w") as f:
        json.dump(result, f, indent=1)
    with open(os.path.join(out_dir, "rides.jsonl"), "w") as f:
        for r in rides:
            f.write(json.dumps(r) + "\n")
    md = ["# How FrodoBots Earth Rovers move, measured from FrodoBots-2K", "",
          "Generated by frodo_motion.py %s (earth-rover-pilot, MV2 of Munim, Inc.). Data: "
          "FrodoBots-2K by FrodoBots Lab, CC BY-SA 4.0. Human-driven rides from the Earth Rovers "
          "game; the SDK's /control may map commands differently." % __version__, "",
          "Parts read: %d. Rides sampled: %d, analysed: %d, errors: %d. Downloaded: %.1f MB."
          % (sum(1 for p in parts if "error" not in p and "skipped" not in p), len(rides),
             len(analysed), result["ride_errors"], result["bytes_read"] / 1e6), "", "## Findings", ""]
    md += ["- " + line for line in lines] or ["- No result reached the minimum sample size."]
    for fam, s in (("turn", "2"), ("speed_rpm", "2"), ("speed_lin", "2"), ("rpm_lag", "0")):
        rows = ((summary.get(fam) or {}).get(s) or {}).get("table") or []
        if rows:
            md += ["", "## %s (stride %s)" % (fam, s), "", "| lag s | n | r | slope | agree | disagree |",
                   "|---|---|---|---|---|---|"]
            md += ["| %s | %s | %s | %s | %s | %s |" % (r["lag_s"], r["n"], r["corr"], r["slope0"],
                                                       r["agree"], r["disagree"]) for r in rows]
    if summary.get("speed_by_linear"):
        md += ["", "## GPS speed by commanded linear", "", "| linear | n | mean m/s | sd |", "|---|---|---|---|"]
        md += ["| %s | %s | %s | %s |" % (b["linear"], b["n"], b["mean_mps"], b["sd_mps"])
               for b in summary["speed_by_linear"]["bins"]]
    with open(os.path.join(out_dir, "report.md"), "w") as f:
        f.write("\n".join(md) + "\n")
    return result


def read_index(url):
    _, data = _request(url)
    rows = list(csv.DictReader(io.StringIO(data.decode("utf-8-sig"))))
    out = []
    for r in rows:
        r = {(k or "").strip(): (v or "").strip() for k, v in r.items()}
        if r.get("url") and r.get("part", "").isdigit():
            out.append((int(r["part"]), r["url"]))
    return sorted(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--index-url", default=INDEX_URL)
    ap.add_argument("--parts", default="all", help="comma-separated part numbers, or all")
    ap.add_argument("--rides-per-part", type=int, default=12)
    ap.add_argument("--imu-per-part", type=int, default=1)
    ap.add_argument("--budget-min", type=float, default=140.0)
    ap.add_argument("--max-cd-mb", type=float, default=800.0)
    ap.add_argument("--out-dir", default="out")
    args = ap.parse_args(argv)
    os.makedirs(args.out_dir, exist_ok=True)
    started = time.monotonic()
    parts, rides, pooled, bins = [], [], {}, {}
    try:
        index = read_index(args.index_url)
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
            rz = RemoteZip(http_size(url), lambda s, k, u=url: http_range(u, s, k))
            if rz.cd_size > args.max_cd_mb * (1 << 20):
                parts.append({"part": label, "skipped": "central directory %d bytes" % rz.cd_size})
                continue
            info = process_part(rz, label, args.rides_per_part, pooled, bins, rides, args.imu_per_part)
        except Exception as exc:
            info = {"part": label, "error": "%s: %s" % (type(exc).__name__, exc)}
        info["seconds"] = round(time.monotonic() - t0, 1)
        parts.append(info)
        print("%s: %s" % (label, {k: v for k, v in info.items() if k != "samples"}), flush=True)
        write_outputs(args.out_dir, parts, rides, summarise(pooled, bins), started)
    result = write_outputs(args.out_dir, parts, rides, summarise(pooled, bins), started)
    print("\n".join(result["conclusions"]) or "no conclusions", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
