#!/usr/bin/env python3
"""Find out which way a rover's compass and turn commands run, before a mission.

The Earth Rover SDK describes /control's angular as "rotation speed left/right
(-1 to 1)" and shows /data's orientation as a bare number (128 in its example),
without saying which way is positive or what a full turn reads. The pilot
assumes compass degrees clockwise from north and a positive angular turning
right. If either is wrong, it turns away from every checkpoint.

calibrate() measures both with a short routine on open ground:

1. Spin in place (30 s at angular 0.4) and watch orientation. The spread of
   the readings gives its full-turn value (360, 256 or 2*pi), and the total
   turn gives the turn rate.
2. Drive straight (20 s at linear 0.4) and fit the GPS course.
3. Turn about 90 degrees with a positive angular, then drive straight again.

The change in GPS course over the turn says which way a positive angular
turns; the change in orientation over the same turn says whether orientation
runs clockwise. GPS course minus heading gives a starting compass bias.

The rover moves about 20 m in all. Standard library only.
By MV2 of Munim, Inc.; written with AI agents.
"""

from __future__ import annotations

import math
import time

import rover_pilot as rp

# The full-turn value of orientation that calibrate() can recognise, smallest first.
SCALES = (2.0 * math.pi, 256.0, 360.0)


def _number(value):
    try:
        x = float(value)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) else None


def unwrap_total(values, scale):
    """Total signed change along `values`, going the short way round between
    readings, and the largest change between two readings."""
    total, biggest = 0.0, 0.0
    for a, b in zip(values, values[1:]):
        d = (b - a + scale / 2.0) % scale - scale / 2.0
        total += d
        biggest = max(biggest, abs(d))
    return total, biggest


def detect_scale(values):
    """The full-turn value of orientation readings taken over at least one
    whole spin, or None if they don't show one."""
    if len(values) < 2:
        return None
    span = max(values) - min(values)
    for scale in SCALES:
        if span > 1.01 * scale or span < 0.75 * scale:
            continue
        total, _ = unwrap_total(values, scale)
        if abs(total) >= scale:
            return scale
    return None


def circular_mean_deg(degrees):
    s = sum(math.sin(math.radians(d)) for d in degrees)
    c = sum(math.cos(math.radians(d)) for d in degrees)
    return math.degrees(math.atan2(s, c)) % 360.0


def fit_course(points, min_move_m=3.0):
    """(course, speed) of a straight drive: course in degrees clockwise from
    north and speed in m/s, from a least-squares line through the (t, lat, lon)
    fixes. None if there are too few fixes or the rover hardly moved."""
    if len(points) < 4:
        return None
    t0, lat0, lon0 = points[0]
    ts, es, ns = [], [], []
    for t, lat, lon in points:
        e, n = rp.to_enu(lat0, lon0, lat, lon)
        ts.append(t - t0)
        es.append(e)
        ns.append(n)
    tm = sum(ts) / len(ts)
    var = sum((x - tm) ** 2 for x in ts)
    if var <= 0:
        return None
    ve = sum((x - tm) * e for x, e in zip(ts, es)) / var
    vn = sum((x - tm) * n for x, n in zip(ts, ns)) / var
    speed = math.hypot(ve, vn)
    if speed * (ts[-1] - ts[0]) < min_move_m:
        return None
    return math.degrees(math.atan2(ve, vn)) % 360.0, speed


def calibrate(rover, clock=time.monotonic, sleep=time.sleep, spin_s=30.0, drive_s=20.0,
              linear=0.4, angular=0.4, settle_s=2.0, rate_hz=10.0, fix_timeout_s=30.0):
    """Run the routine on `rover` (SdkClient or SimRover) and return a dict.

    On success it has ok=True and the keys rover_pilot.Conventions.from_dict
    reads: orientation_scale, orientation_clockwise, angular_right_positive
    and bias_deg. It also has the measured turn rate and speed at full command.
    Commands go to the rover as they are, without any conventions applied.
    """
    period = 1.0 / rate_hz
    out = {"ok": False}

    def fail(reason):
        out["reason"] = reason
        return out

    def drive(lin, ang, seconds):
        samples = []
        end = clock() + seconds
        while clock() < end:
            tick = clock()
            rover.control(lin, ang)
            samples.append((tick, rover.data() or {}))
            sleep(max(0.0, period - (clock() - tick)))
        return samples

    def straight(samples, scale):
        start = samples[0][0] + settle_s
        points, degrees, last = [], [], None
        for t, data in samples:
            if t < start:
                continue
            fix = rp.parse_fix(data.get("latitude"), data.get("longitude"))
            if fix is not None and fix != last:
                points.append((t, fix[0], fix[1]))
                last = fix
            value = _number(data.get("orientation"))
            if value is not None:
                degrees.append(value * 360.0 / scale)
        fit = fit_course(points)
        if fit is None or not degrees:
            return None
        return fit[0], fit[1], circular_mean_deg(degrees)

    try:
        end = clock() + fix_timeout_s
        while True:
            data = rover.data() or {}
            if rp.parse_fix(data.get("latitude"), data.get("longitude")) is not None:
                break
            if clock() >= end:
                return fail("no GPS fix")
            rover.control(0.0, 0.0)
            sleep(0.5)

        spin = drive(0.0, angular, spin_s)
        raw = [v for v in (_number(d.get("orientation")) for _, d in spin) if v is not None]
        scale = detect_scale(raw)
        if scale is None:
            return fail("orientation did not show one full turn while spinning in place; "
                        "spin for longer, or check that /data has orientation")
        total, step = unwrap_total(raw, scale)
        if step > scale / 3.0:
            return fail("orientation jumped by more than a third of a turn between readings; "
                        "spin more slowly")
        spin_deg = total * 360.0 / scale
        yaw_dps = abs(spin_deg) / max(spin[-1][0] - spin[0][0], 1e-6)
        out.update(orientation_scale=scale, spin_deg=round(spin_deg, 1),
                   yaw_dps_at_full=round(yaw_dps / angular, 1))

        first = drive(linear, 0.0, drive_s)
        drive(0.0, angular, min(10.0, 90.0 / yaw_dps))
        second = drive(linear, 0.0, drive_s)
        rover.control(0.0, 0.0)

        a, b = straight(first, scale), straight(second, scale)
        if a is None or b is None:
            return fail("the rover did not drive far enough in a straight line to fit "
                        "a GPS course")
        turn_deg = rp.wrap180(b[0] - a[0])
        orientation_turn_deg = rp.wrap180(b[2] - a[2])
        out.update(turn_deg=round(turn_deg, 1), orientation_turn_deg=round(orientation_turn_deg, 1),
                   speed_mps_at_full=round((a[1] + b[1]) / 2.0 / linear, 2))
        if abs(turn_deg) < 30.0:
            return fail("the GPS course changed by only %.0f degrees over the turn" % turn_deg)
        if abs(orientation_turn_deg) < 30.0:
            return fail("orientation changed by only %.0f degrees over the turn"
                        % orientation_turn_deg)
        if (spin_deg > 0) != (orientation_turn_deg > 0):
            return fail("orientation turned one way while spinning and the other way "
                        "over the 90-degree turn")
        right = turn_deg > 0
        clockwise = (orientation_turn_deg > 0) == right
        offsets = []
        for course, _, mean in (a, b):
            heading = mean if clockwise else -mean
            offsets.append(rp.wrap180(course - heading))
        out.update(ok=True, orientation_clockwise=clockwise, angular_right_positive=right,
                   bias_deg=round(rp.wrap180(circular_mean_deg(offsets)), 1))
        out["reason"] = "orientation: full turn %s, %s; a positive angular turns %s" % (
            "2*pi" if scale < 7 else "%g" % scale,
            "clockwise" if clockwise else "counter-clockwise", "right" if right else "left")
        return out
    finally:
        rover.control(0.0, 0.0)
