#!/usr/bin/env python3
"""earth-rover-pilot: a GPS waypoint pilot for the FrodoBots Earth Rover SDK.

It drives an Earth Rover through the checkpoints of an SDK mission (the format
the Earth Rover Challenge uses) and reports each one with /checkpoint-reached.
What it adds over a plain bearing-follower:

- GPS readings are checked: the rover's no-fix value (1000), 0/0, NaN and
  implausible jumps are dropped, and the rest are smoothed.
- The compass bias is learned while driving: on straight stretches a line is
  fitted through the GPS fixes, and its direction (the true course) is compared
  with the mean compass reading over the same stretch. How well the fixes lie
  on that line is measured too; a stretch bent by drifting GPS error can be
  left out (max_residual_m) and straighter stretches trusted more (weigh).
  On a real rover a stretch counts from 20 m rather than 10 m (since v0.17.0:
  in simulation its fits were about 2.3 times less wrong, pace_m.py).
- Checkpoints are reported from inside a margin of the 15 m tolerance, retried
  when refused, and the last one only after a settled stop. A report that gets
  no answer is checked against the server's checkpoint list before retrying.
- Optionally, each leg follows a walkable route planned on OpenStreetMap
  (route_planner.py) instead of heading straight for the checkpoint, and
  every remaining leg can be planned and checked before driving (--check-route).
  On a real rover the path follower aims 16 m ahead along the route rather
  than 8 m (since v0.18.0: in simulation it was faster on every course and
  ran less far past corners, pace_n.py).
- Optionally, the front camera (free_space.py) bends the heading around
  obstacles in the way and slows or stops the rover when nothing is clear.
  A real rover's camera is read with free_space.REAL_ROVER, the settings that
  saw the fewest phantom obstacles on recorded FrodoBots-2K front frames
  (frodo_frames.py); the simulator keeps the VisionGuard defaults.
- Which way orientation and angular run can be measured on the rover first
  (calibrate.py, --calibrate) and applied to the mission (--calibration).
  Without a calibration, a real rover is driven with a positive angular
  turning left, as the FrodoBots-2K rides show (FINDINGS-frodobots-2k.md).
- A real rover is steered with the gains that did best for a rover that turns
  like the recorded ones (ROVER_STEERING, from gain_study.py); the simulator
  keeps the Steering class defaults.
- Optionally, a late GPS fix is moved forward by the driving commanded since
  it was taken (--gps-lag); on the FrodoBots-2K rides the GPS runs about
  1.5 s behind the wheels.
- On a real rover, while the GPS has no fresh fix, the position is carried
  from the last fix by the wheel RPMs along the compass-corrected heading
  (dead_reckon.py), and the rover drives on through GPS outages of up to 120 s
  instead of stopping (--dead-reckon-gaps, the default on a real rover since
  v0.15.0: through simulated GPS outages of 15 s and 45 s it was 6.3-7.2%
  faster and slower nowhere, pace_i.py; carrying the position 120 s rather
  than 30 s after the last fix since v0.16.0, pace_k.py, and still faster
  with wheels that slip and a compass that drifts, pace_l.py). The wheels
  are used only once straight stretches have checked them against the GPS.
  For 2 s after each fix the position follows the fresh GPS course, then
  the heading, the difference fading out over 2 s more (frodo_blend.py,
  frodo_blend_b.py).
  --dead-reckon steers by the wheels whenever it can (the real-rover default
  from v0.10.0 to v0.13.0, which made the pilot weave on a clean GPS,
  pace_g.py, pace_h.py), and --no-dead-reckon by the smoothed GPS alone, so
  the rover stops while the GPS is out (v0.14.0's default).
- On a real rover the compass is smoothed over its readings (--smooth-heading;
  --no-smooth-heading turns it off, and the simulator keeps it off unless
  asked): each new reading moves the heading only 0.3 of the way from the last
  estimate, after turning that estimate by the angular commanded since. On a
  simulated Mini+ with 10 degrees of compass noise this won back most of the
  time the noise cost (pace_c.py); without it the compass-bias learner stops
  once the noise reaches about 6 degrees (pace_e.py); and on fresh seeds it was
  slower in none of 33 groups, with rovers turning slower, faster or later
  than it assumes and a -60 degree compass error (pace_f.py).
- The SDK keeps serving the last telemetry it got, so a rover whose link has
  dropped still shows a GPS fix. When no new telemetry has come in for 5 s
  (the /data timestamp stays the same, or GET /status says so), the rover is
  stopped until it is back (TelemetryWatch, --telemetry-timeout).
- A rover that has tipped over is stopped: the direction of gravity in the
  accelerometer is learned in the first seconds of the mission, and once it
  has pointed more than 50 degrees away from that for a second the rover is
  stopped until it is upright again (TipWatch, --tip-angle).
- Being stuck (driving with no GPS progress) triggers a back-up-and-turn move.
- Each leg is summed up (time, reports, recoveries) in the result and the log.
- A built-in simulator (command latency, GPS noise, delay and dropouts, compass
  bias, obstacles and a rendered front camera) lets the whole loop be tested
  without a rover; --sim-real makes it move like the rovers in FrodoBots-2K.

Standard library only. By MV2 of Munim, Inc.; written with AI agents.
"""

from __future__ import annotations

import argparse
import base64
import collections
import json
import math
import random
import sys
import time
import urllib.error
import urllib.request

__version__ = "0.18.3"

EARTH_RADIUS_M = 6371000.0
M_PER_DEG = EARTH_RADIUS_M * math.pi / 180.0
NO_FIX = 1000.0  # lat/lon the rover reports when it has no GPS fix
# The SDK can hold the final /checkpoint-reached for up to 12 s while it
# confirms the rover has stopped (SAFETY_STOP_CONFIRM_TIMEOUT_S), so wait longer.
REPORT_TIMEOUT_S = 20.0
# Stop the rover when no new telemetry has come in for this long. An Earth
# Rover Mini+ reports every 2 s (SDK README), so one late or lost report
# (a 4 s gap) doesn't stop it, and two in a row do.
TELEMETRY_TIMEOUT_S = 5.0
# Stop the rover when its accelerometer says it has tipped over: gravity more
# than this many degrees from where it pointed when the mission began, for
# TIP_HOLD_S. A kerb or a ramp tilts a rover by 10 to 20 degrees; on its side
# it is 90 away. 0 turns the check off.
TIP_ANGLE_DEG = 50.0
TIP_HOLD_S = 1.0

# (north_m, east_m) of each checkpoint from the start, for --simulate.
DEMO_MISSION = [(40.0, 30.0), (85.0, -5.0), (60.0, -60.0), (10.0, -40.0)]
# (north_m, east_m, radius_m) hedges on the first two legs, for --simulate --obstacles.
DEMO_OBSTACLES = [(20.3, 14.6, 1.0), (62.5, 12.0, 1.0)]
# For --simulate --sim-quirks: orientation reads 0-255 counter-clockwise and a
# positive angular turns left.
SIM_QUIRKS = {"orientation_scale": 256.0, "orientation_clockwise": False, "angular_sign": -1.0}
# For --simulate --sim-real: move like the rovers in FrodoBots-2K
# (FINDINGS-frodobots-2k.md): 0.79 m/s per unit of linear, wheels 0.8 s behind
# the command and GPS 1.5 s behind the wheels. The gyroscope puts the yaw rate
# at about 30 deg/s per unit of angular; the simulator's own 60 deg/s is kept
# here so earlier studies stay comparable, and the studies set 20 to 45 themselves.
SIM_REAL = {"max_speed_mps": 0.79, "latency_s": 0.8, "gps_delay_s": 1.5}
# What to assume on a real rover without --calibration. A positive angular
# turns it left: on 279 FrodoBots-2K rides the GPS course turned against the
# commanded angular 440 times to 57 (FINDINGS-frodobots-2k.md), and the SDK's
# ROS2 bridge and LeRobot's Earth Rover driver both send a left turn as a
# positive angular. Orientation is still assumed to be degrees clockwise.
ROVER_DEFAULTS = {"angular_right_positive": False}
# Steering for a real rover. gain_study.py flew 24 gain settings x 3 missions
# x 30 seeds on a simulated rover that moves like the recorded ones, turning at
# 20, 30 or 45 deg/s per unit. At the same cruise, letting angular reach 1.0
# (not 0.6) and turning in place only above 90 deg (not 60) was faster in all
# 9 mission/turn-rate groups (sign test p < 0.05 in each, about 3% overall) and
# needed a third fewer back-up moves; nothing was lost (FINDINGS-frodobots-2k.md).
ROVER_STEERING = {"max_angular": 1.0, "turn_in_place_deg": 90.0}
# pace_study.py (v0.10.0): on a Mini+ stand-in, cruise 0.6 never made the human
# Berkeley-Stanford pace (0.754 m/s), 0.8 made it on every course with about 3.9 h
# left for stops, and 1.0 widened corner-heavy paths to the battery limit.
# Simulated only: measure range at this cruise before a real marathon.
MARATHON = dict(ROVER_STEERING, cruise=0.8)
# dead_reckon_study.py (v0.10.0): carrying the position along the pilot's
# compass-corrected heading, rather than the last GPS course, gave the smallest
# position error and the fastest missions on every simulated rover and GPS
# error model tried. Simulated only.
# frodo_blend.py and frodo_blend_b.py (v0.11.0): on recorded FrodoBots-2K rides
# the fresh GPS course beat the live compass for the first 2-3 s after a fix.
# Holding it 2 s, then fading to the heading over 2 s more, missed the fix 10 s
# later by 0.944x the heading alone on 145 held-out rides (95% CI 0.915-0.962),
# with no cost at 30 s. Measured on the Earth Rover Zero's raw compass only.
# pace_g.py and pace_h.py (v0.14.0): on a simulated Mini+ with a clean GPS,
# starting again from every fix made the position jump and the pilot weave,
# 1.2-6.7% slower than without dead reckoning, so it is off by default on a
# real rover too (use_dead_reckoning). Used only while the GPS had no fresh
# fix (dead_reckon_gaps), it kept the saving through GPS gaps and cost nothing
# on a clean GPS, but lost to the default on one course. Simulated only.
# pace_i.py (v0.15.0): through GPS outages of 15 s and 45 s, used only while
# the GPS had no fresh fix it was 6.3-7.2% faster than without dead reckoning
# on every course and slower on none, also on a clean GPS, so the command
# line uses it that way on a real rover (use_dead_reckon_gaps). Simulated only.
DEAD_RECKON = {"use_course": False, "course_hold_s": 2.0, "fade": True}
# pace_k.py (v0.16.0): bridging GPS outages with the reckoner carrying the
# position 60 s after the last fix was 3.3-4.7% faster than 30 s on every
# course through 45 s outages, also with fixes wandering before them, and
# 120 s was 5.8-6.8% faster than 30 s through 90 s outages; slower nowhere,
# identical with 15 s outages. So the command line's bridging reckoner uses
# 120 s (--dead-reckon keeps dead_reckon.py's 30 s). pace_l.py (v0.16.1):
# with wheels reading up to 15% off and a drifting compass, 120 s was still
# 2.1-2.7% faster than 60 s through 90 s outages and slower nowhere. Not
# yet measured on a real rover.
BRIDGE_MAX_S = 120.0
# pace_c.py (v0.12.0): on a simulated Mini+ with 10 degrees of compass noise,
# HeadingSmoother with these settings was faster in all 6 cruise x course groups
# (2.1-2.5%; 0.874 against 0.855 m/s made good at cruise 0.8) and cost nothing
# with 3 degrees. 48 deg/s per unit of angular and 0.5 s latency are the Mini+'s,
# from public recordings; --calibration's yaw_dps_at_full replaces the rate.
# pace_f.py (v0.13.0): on 1,584 missions on fresh seeds it was slower in none of
# 33 profile x course groups, with the rover turning at 32 or 64 deg/s, commands
# landing after 1.0 s or a -60 deg compass error, so the command line turns it
# on for a real rover (use_smooth_heading). Simulated only.
SMOOTH_HEADING = {"gain": 0.3, "yaw_dps": 48.0, "lag_s": 0.5}
# pace_m.py (v0.17.0): on a simulated Mini+ each of the compass-bias
# learner's fits over a 10 m stretch was about 9 deg off the bias that would
# have cancelled the compass error. Over 20 m stretches the fits were about
# 2.3 times less wrong but a third as many: the heading was truer on a steady
# compass error (median 1.6-1.7 deg against 2.9-3.1) and about 1 deg less
# true on a drifting one. It was slower and lost nowhere, and faster on 3 of
# 9 profile x course groups (by at most 0.22%), so the command line gives a
# real rover's learner these settings (make_heading). Simulated only.
HEADING_LEARNER = {"min_move_m": 20.0}
# pace_n.py (v0.18.0): on a simulated Mini+ following a planned path, the
# 8 m lookahead ran a median 4.3 m past each right-angle corner and 16 m
# 1.7-2.2 m. 16 m was faster on every course with a steady and a drifting
# compass (3.6-3.9% on city blocks, 0.3-1.2% elsewhere) and slower nowhere,
# and its 95th-percentile distance from the course stayed within 0.5 m of
# 8 m's (with a drifting compass it holds the rover a little further to one
# side), so the command line gives a real rover's path follower this
# lookahead (Pilot.path_lookahead_m). Simulated only; it matters only with
# --osm or --fetch-osm.
# pace_o.py (v0.18.1): with the study planner going round each checkpoint
# corner instead of cutting across it, 16 m was still faster than 8 m on
# every course (5.4-6.2% on city blocks). 24 m was faster again but turned
# before each corner and ran up to 1.6 m further from the course near
# corners, so 16 m stays.
# pace_p.py (v0.18.2): aiming 24 m ahead on straights and 16 m within 24 m
# of a turn went round corners like 16 m but kept none of 24 m's city-blocks
# saving, and on straights it only held the rover further from the course,
# so a real rover keeps this plain lookahead.
PATH_LOOKAHEAD_M = 16.0


# --- geometry -------------------------------------------------------------

def clamp(x, lo=-1.0, hi=1.0):
    return max(lo, min(hi, x))


def wrap180(angle_deg):
    """Angle in [-180, 180)."""
    return (angle_deg + 180.0) % 360.0 - 180.0


def haversine_m(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(min(1.0, math.sqrt(a)))


def bearing_deg(lat1, lon1, lat2, lon2):
    """Initial bearing from point 1 to point 2: 0 = north, clockwise."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dl = math.radians(lon2 - lon1)
    x = math.sin(dl) * math.cos(p2)
    y = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)
    return math.degrees(math.atan2(x, y)) % 360.0


def offset_latlon(lat, lon, north_m, east_m):
    """The point north_m / east_m metres from (lat, lon); fine over a few km."""
    return (lat + north_m / M_PER_DEG,
            lon + east_m / (M_PER_DEG * math.cos(math.radians(lat))))


def to_enu(lat0, lon0, lat, lon):
    """(east, north) metres of (lat, lon) from (lat0, lon0)."""
    return ((lon - lon0) * M_PER_DEG * math.cos(math.radians(lat0)),
            (lat - lat0) * M_PER_DEG)


def densify(points, step_m=2.0):
    """The polyline `points` with extra points so none are more than step_m apart."""
    out = [tuple(points[0])]
    for (lat0, lon0), (lat1, lon1) in zip(points, points[1:]):
        n = max(1, int(math.ceil(haversine_m(lat0, lon0, lat1, lon1) / step_m)))
        for k in range(1, n + 1):
            f = k / n
            out.append((lat0 + f * (lat1 - lat0), lon0 + f * (lon1 - lon0)))
    return out


def parse_fix(lat, lon):
    """(lat, lon) as floats, or None for missing, no-fix or nonsense values."""
    try:
        lat, lon = float(lat), float(lon)
    except (TypeError, ValueError):
        return None
    if not (math.isfinite(lat) and math.isfinite(lon)):
        return None
    if abs(lat) > 90.0 or abs(lon) > 180.0:  # includes the 1000 no-fix value
        return None
    if lat == 0.0 and lon == 0.0:
        return None
    return lat, lon


def parse_heading(value):
    """Compass heading in degrees [0, 360), or None."""
    try:
        h = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(h):
        return None
    return h % 360.0


class Conventions:
    """How a rover's /data orientation and /control angular run.

    The defaults match the built-in simulator: orientation in degrees
    clockwise from north, and a positive angular turning right. On a real rover
    without a calibration the pilot uses rover_conventions() instead.
    calibrate.py measures them on the rover; bias_deg, if known, is the
    compass offset to start from before the pilot has learned its own.
    """

    def __init__(self, orientation_scale=360.0, orientation_clockwise=True,
                 angular_right_positive=True, bias_deg=None):
        self.orientation_scale = float(orientation_scale)
        self.orientation_clockwise = bool(orientation_clockwise)
        self.angular_right_positive = bool(angular_right_positive)
        self.bias_deg = None if bias_deg is None else float(bias_deg)

    @classmethod
    def from_dict(cls, d):
        return cls(d.get("orientation_scale", 360.0), d.get("orientation_clockwise", True),
                   d.get("angular_right_positive", True), d.get("bias_deg"))

    def heading(self, value):
        """An orientation reading as degrees [0, 360) clockwise from north, or None."""
        try:
            h = float(value)
        except (TypeError, ValueError):
            return None
        if not math.isfinite(h):
            return None
        if self.orientation_scale != 360.0:
            h = h * 360.0 / self.orientation_scale
        if not self.orientation_clockwise:
            h = -h
        return h % 360.0

    def angular(self, angular):
        """The /control angular that turns the way `angular` (positive = right) means."""
        return angular if self.angular_right_positive else 0.0 - angular


def rover_conventions():
    """The conventions to drive a real rover with when it hasn't been calibrated."""
    return Conventions.from_dict(ROVER_DEFAULTS)


# --- estimation -----------------------------------------------------------

# pace_q.py (v0.18.3): with GPS as quiet as recorded Earth Rovers' (0.22 m),
# alpha 0.3 leaves the pilot a median 6.3-6.4 m behind the rover. alpha 0.6,
# raw fixes and an alpha-beta tracker cut that to 2.1-3.4 m and were 3-4%
# faster on city blocks, but each turned before the corners, so by the
# pre-stated rule a real rover keeps alpha 0.3.
class GpsFilter:
    """Drops bad GPS readings and smooths the good ones."""

    def __init__(self, alpha=0.3, max_speed_mps=3.0, jump_slack_m=10.0,
                 max_age_s=3.0, reset_after=3):
        self.alpha = alpha
        self.max_speed_mps = max_speed_mps
        self.jump_slack_m = jump_slack_m
        self.max_age_s = max_age_s
        self.reset_after = reset_after
        self.lat = self.lon = None  # smoothed position
        self.raw = None             # last accepted raw reading
        self.raw_t = None
        self.fix_t = None           # last time a valid reading was seen
        self.rejected = 0
        self._last_rejected = None

    def update(self, lat, lon, t):
        """Feed one telemetry reading; returns it if it is a new accepted fix."""
        fix = parse_fix(lat, lon)
        if fix is None:
            return None
        if fix == self.raw:
            self.fix_t = t
            return None
        if self.raw is not None:
            dt = max(t - self.raw_t, 1e-3)
            jump = haversine_m(self.raw[0], self.raw[1], fix[0], fix[1])
            if jump > self.max_speed_mps * dt + self.jump_slack_m:
                if fix != self._last_rejected:
                    self._last_rejected = fix
                    self.rejected += 1
                if self.rejected < self.reset_after:
                    return None
                self.lat = self.lon = None  # the old fix was the bad one
        self.rejected = 0
        self._last_rejected = None
        self.raw, self.raw_t, self.fix_t = fix, t, t
        if self.lat is None:
            self.lat, self.lon = fix
        else:
            self.lat += self.alpha * (fix[0] - self.lat)
            self.lon += self.alpha * (fix[1] - self.lon)
        return fix

    def has_fix(self, t):
        return (self.lat is not None and self.fix_t is not None
                and t - self.fix_t <= self.max_age_s)


class TelemetryWatch:
    """Notices when the rover's telemetry has stopped coming in.

    The SDK caches the last telemetry it got and /data keeps serving it, so a
    rover whose link has dropped still shows a GPS fix, and GpsFilter takes
    each repeat as the fix still holding. A reading counts as new when its
    /data timestamp changes; readings without a timestamp leave that check
    out. `age`, if given, returns the SDK's own seconds since the last
    telemetry message (GET /status telemetry_age_s, or None) and is asked at
    most every `poll_s`. A timeout of 0 turns the watch off.
    """

    def __init__(self, timeout_s=TELEMETRY_TIMEOUT_S, age=None, poll_s=1.0):
        self.timeout_s = timeout_s
        self.age = age
        self.poll_s = poll_s
        self.stamp = None    # last /data timestamp seen
        self.stamp_t = None  # when it was first seen
        self.sdk_age = None  # last telemetry_age_s the SDK gave
        self._poll_t = None

    def update(self, t, stamp):
        """Feed one /data reading's timestamp, seen at t."""
        try:
            stamp = float(stamp)
        except (TypeError, ValueError):
            stamp = None
        if stamp is not None and math.isfinite(stamp) and stamp != self.stamp:
            self.stamp, self.stamp_t = stamp, t
        if self.age is not None and (self._poll_t is None or t - self._poll_t >= self.poll_s):
            self._poll_t = t
            self.sdk_age = self.age()

    def since(self, t):
        """Seconds since the timestamp last changed, or None if there is none."""
        return None if self.stamp_t is None else t - self.stamp_t

    def stale(self, t):
        if self.timeout_s <= 0:
            return False
        since = self.since(t)
        if since is not None and since > self.timeout_s:
            return True
        return self.sdk_age is not None and self.sdk_age > self.timeout_s


class TipWatch:
    """Notices when the rover has tipped over, from its accelerometer.

    /data `accels` holds rows of [x, y, z, timestamp]; in the SDK README's
    example one axis reads about 1 while the rover stands, so the unit is g.
    The README doesn't say which axis points up, and neither the GPS nor the
    camera can tell that a rover is on its side (one recorded frame, turned
    90 degrees, read as clear ground), so the watch learns the direction
    gravity has during the first `learn_s` seconds of readings and calls the
    rover tipped once gravity has pointed more than `angle_deg` away from it
    for `hold_s`. It is upright again as soon as the angle is back under.
    Readings whose size is far from 1 g (a knock, a drop, or another unit)
    are left out; readings above 5 are taken as m/s^2. angle_deg 0 turns it
    off, and a rover that reports no `accels` (the simulator) is never tipped.
    """

    def __init__(self, angle_deg=TIP_ANGLE_DEG, hold_s=TIP_HOLD_S, learn_s=3.0,
                 min_g=0.5, max_g=1.5):
        self.angle_deg = angle_deg
        self.hold_s = hold_s
        self.learn_s = learn_s
        self.min_g = min_g
        self.max_g = max_g
        self.up = None       # unit vector gravity had when it was learned
        self.angle = None    # degrees between gravity now and `up`
        self.samples = 0     # readings accepted
        self.tipped = False
        self._learn_t0 = None
        self._sum = [0.0, 0.0, 0.0]
        self._over_since = None

    @staticmethod
    def gravity(accels):
        """The mean (x, y, z) of the rows of a /data `accels` list, in g, or None."""
        if not isinstance(accels, (list, tuple)):
            return None
        sums, n = [0.0, 0.0, 0.0], 0
        for row in accels:
            if not isinstance(row, (list, tuple)) or len(row) < 3:
                continue
            try:
                x, y, z = float(row[0]), float(row[1]), float(row[2])
            except (TypeError, ValueError):
                continue
            if not (math.isfinite(x) and math.isfinite(y) and math.isfinite(z)):
                continue
            sums[0] += x
            sums[1] += y
            sums[2] += z
            n += 1
        if n == 0:
            return None
        g = [s / n for s in sums]
        if math.sqrt(sum(v * v for v in g)) > 5.0:  # m/s^2, not g
            g = [v / 9.80665 for v in g]
        return tuple(g)

    def update(self, t, accels):
        """Feed one /data reading's `accels`, seen at t; returns True while tipped."""
        if self.angle_deg <= 0:
            return False
        g = self.gravity(accels)
        if g is None:
            return self.tipped
        size = math.sqrt(sum(v * v for v in g))
        if not (self.min_g <= size <= self.max_g):
            return self.tipped
        unit = tuple(v / size for v in g)
        self.samples += 1
        if self.up is None:
            if self._learn_t0 is None:
                self._learn_t0 = t
            for k in range(3):
                self._sum[k] += unit[k]
            if t - self._learn_t0 < self.learn_s:
                return False
            total = math.sqrt(sum(v * v for v in self._sum))
            if total <= 0:
                return False
            self.up = tuple(v / total for v in self._sum)
        dot = max(-1.0, min(1.0, sum(a * b for a, b in zip(unit, self.up))))
        self.angle = math.degrees(math.acos(dot))
        if self.angle > self.angle_deg:
            if self._over_since is None:
                self._over_since = t
            if t - self._over_since >= self.hold_s:
                self.tipped = True
        else:
            self._over_since = None
            self.tipped = False
        return self.tipped


class BatteryLog:
    """How much charge a mission has used and how far it has driven.

    /data `battery` is the charge level; the SDK README's examples read 100
    and 87 and give no unit, so it is taken as a percent and values outside
    0-100 are left out. Distance is summed from GPS fixes, counting a step only
    once the rover is `step_m` from the last point counted, so GPS jitter while
    it stands still doesn't add up (bends are cut slightly short). m_per_pct is
    metres driven per percent used, given once at least `min_used_pct` has gone
    (the level comes in whole percents); range_left_m spreads it over the
    charge left. A rover that reports no `battery` (the simulator) leaves all
    of it None except driven_m.
    """

    def __init__(self, step_m=3.0, min_used_pct=2.0):
        self.step_m = step_m
        self.min_used_pct = min_used_pct
        self.start = None    # first charge level seen
        self.level = None    # latest charge level
        self.driven_m = 0.0
        self._anchor = None  # last fix counted

    def update(self, battery, fix):
        """Feed one /data reading's `battery` and its parsed (lat, lon) fix or None."""
        if isinstance(battery, bool):
            battery = None
        try:
            battery = float(battery)
        except (TypeError, ValueError):
            battery = None
        if battery is not None and math.isfinite(battery) and 0.0 <= battery <= 100.0:
            if self.start is None:
                self.start = battery
            self.level = battery
        if fix is None:
            return
        if self._anchor is None:
            self._anchor = fix
            return
        step = haversine_m(self._anchor[0], self._anchor[1], fix[0], fix[1])
        if step >= self.step_m:
            self.driven_m += step
            self._anchor = fix

    def result(self):
        used = None if self.start is None else self.start - self.level
        m_per_pct = (self.driven_m / used
                     if used is not None and used >= self.min_used_pct else None)
        return {
            "start_pct": self.start,
            "end_pct": self.level,
            "used_pct": None if used is None else round(used, 1),
            "driven_m": round(self.driven_m, 1),
            "m_per_pct": None if m_per_pct is None else round(m_per_pct, 1),
            "range_left_m": (None if m_per_pct is None
                             else round(m_per_pct * self.level)),
        }


class LagCompensator:
    """Moves a late GPS fix forward by the driving commanded since it was taken.

    A fix first seen at fix_t shows where the rover was gps_lag_s earlier, and
    a command moves the rover cmd_latency_s after it is sent, so the rover has
    since driven what was commanded between fix_t - gps_lag_s - cmd_latency_s
    and now - cmd_latency_s. Each unit of linear is taken as speed_mps.
    """

    def __init__(self, gps_lag_s, cmd_latency_s=0.8, speed_mps=0.79, keep_s=10.0):
        self.gps_lag_s = gps_lag_s
        self.cmd_latency_s = cmd_latency_s
        self.speed_mps = speed_mps
        self.keep_s = gps_lag_s + cmd_latency_s + keep_s
        self._cmds = collections.deque()

    def record(self, t, linear, heading_deg):
        """A command sent at t while the heading was heading_deg (None if unknown)."""
        self._cmds.append((t, linear, heading_deg))
        while len(self._cmds) > 1 and self._cmds[1][0] < t - self.keep_s:
            self._cmds.popleft()

    def offset(self, t, fix_t):
        """(north_m, east_m) the rover has driven that the fix seen at fix_t doesn't show."""
        a = fix_t - self.gps_lag_s - self.cmd_latency_s
        b = t - self.cmd_latency_s
        north = east = 0.0
        cmds = list(self._cmds)
        for k, (t0, linear, heading) in enumerate(cmds):
            t1 = cmds[k + 1][0] if k + 1 < len(cmds) else t
            lo, hi = max(t0, a), min(t1, b)
            if hi <= lo or heading is None or linear == 0.0:
                continue
            d = linear * self.speed_mps * (hi - lo)
            r = math.radians(heading)
            north += d * math.cos(r)
            east += d * math.sin(r)
        return north, east


class HeadingEstimator:
    """Compass heading corrected by a bias learned from GPS course over ground.

    On each straight stretch of at least min_move_m a line is fitted through
    the GPS fixes against time; its direction is the course, and the course
    minus the mean compass reading is one measurement of the bias. `last_fit`
    records each fit's length, number of fixes and residual (the RMS distance
    of the fixes from the line, across it). Drifting GPS error bends the line:
    with `max_residual_m` set, a stretch whose residual is above it is left
    out (counted in `rejected_fits`); with `weigh`, the bias is the weighted
    circular mean of every measurement, each weighted by (length / residual)
    squared, instead of a running update with `gain`. Both are off by default.
    """

    def __init__(self, min_move_m=10.0, min_points=5, min_speed_mps=0.25,
                 settle_s=1.0, gain=0.3, max_angular=0.1, min_linear=0.2,
                 max_spread=0.985, course_ttl_s=5.0, max_residual_m=None, weigh=False):
        self.min_move_m = min_move_m
        self.min_points = min_points
        self.min_speed_mps = min_speed_mps
        self.settle_s = settle_s
        self.gain = gain
        self.max_angular = max_angular
        self.min_linear = min_linear
        self.max_spread = max_spread
        self.course_ttl_s = course_ttl_s
        self.max_residual_m = max_residual_m
        self.weigh = weigh
        self.bias = 0.0  # added to the compass reading
        self.calibrations = 0
        self.rejected_fits = 0
        self.last_fit = None
        self.last_course = None
        self.last_course_t = None
        self._angular_lp = 0.0
        self._straight_since = None
        self._w_sin = self._w_cos = 0.0
        self._reset_segment()

    def _reset_segment(self):
        self._pts = []
        self._sin = self._cos = 0.0
        self._n = 0

    def update(self, t, new_fix, compass, linear, angular):
        """Feed one tick: a new GPS fix (or None), the compass and the command being driven."""
        self._angular_lp = 0.8 * self._angular_lp + 0.2 * angular
        if linear < self.min_linear or abs(self._angular_lp) > self.max_angular:
            self._straight_since = None
            self._reset_segment()
            return
        if self._straight_since is None:
            self._straight_since = t
            return
        if t - self._straight_since < self.settle_s:
            return
        if compass is not None:
            r = math.radians(compass)
            self._sin += math.sin(r)
            self._cos += math.cos(r)
            self._n += 1
        if new_fix is not None:
            self._pts.append((t, new_fix[0], new_fix[1]))
        if len(self._pts) < self.min_points:
            return
        _, lat0, lon0 = self._pts[0]
        _, lat1, lon1 = self._pts[-1]
        if haversine_m(lat0, lon0, lat1, lon1) < self.min_move_m:
            return
        self._fit(t)
        self._reset_segment()

    def _fit(self, t):
        t0, lat0, lon0 = self._pts[0]
        ts, es, ns = [], [], []
        for ti, lat, lon in self._pts:
            e, n = to_enu(lat0, lon0, lat, lon)
            ts.append(ti - t0)
            es.append(e)
            ns.append(n)
        tm = sum(ts) / len(ts)
        var = sum((x - tm) ** 2 for x in ts)
        if var <= 0:
            return
        ve = sum((x - tm) * e for x, e in zip(ts, es)) / var
        vn = sum((x - tm) * n for x, n in zip(ts, ns)) / var
        speed = math.hypot(ve, vn)
        if speed < self.min_speed_mps:
            return
        course = math.degrees(math.atan2(ve, vn)) % 360.0
        self.last_course, self.last_course_t = course, t
        # How well the fixes lie on the line: their RMS distance from it, across
        # it. The fitted line passes through the mean fix at the mean time.
        em, nm = sum(es) / len(es), sum(ns) / len(ns)
        across = [((e - em) * vn - (n - nm) * ve) / speed for e, n in zip(es, ns)]
        residual = math.sqrt(sum(d * d for d in across) / len(across))
        length = speed * (ts[-1] - ts[0])
        self.last_fit = {"points": len(ts), "length_m": round(length, 1),
                         "residual_m": round(residual, 2)}
        if self._n == 0:
            return
        if self.max_residual_m is not None and residual > self.max_residual_m:
            self.rejected_fits += 1
            return  # the fixes don't lie on a line: drifting GPS, not a course
        if math.hypot(self._sin, self._cos) / self._n < self.max_spread:
            return  # the compass wandered too much on this stretch
        compass_mean = math.degrees(math.atan2(self._sin, self._cos)) % 360.0
        measured = wrap180(course - compass_mean)
        if self.weigh:
            # A stretch's measurement is trusted by how long and how straight
            # it was: a 10 m stretch with 0.5 m of scatter counts 16 times one
            # with 2 m of scatter.
            w = (length / max(residual, 0.5)) ** 2
            r = math.radians(measured)
            self._w_sin += w * math.sin(r)
            self._w_cos += w * math.cos(r)
            self.bias = wrap180(math.degrees(math.atan2(self._w_sin, self._w_cos)))
        elif self.calibrations == 0:
            self.bias = measured
        else:
            self.bias = wrap180(self.bias + self.gain * wrap180(measured - self.bias))
        self.calibrations += 1

    def heading(self, compass, t):
        """Best heading estimate in degrees, or None if there is nothing to go on."""
        if compass is not None:
            return (compass + self.bias) % 360.0
        if self.last_course is not None and t - self.last_course_t <= self.course_ttl_s:
            return self.last_course
        return None


class HeadingSmoother:
    """Smooths the compass over its readings without lagging behind turns.

    A reading is new when the /data timestamp changes (without a timestamp,
    when the reading does). On each new reading the estimate is first turned
    by the angular commanded since the last one (yaw_dps per unit, each
    command taking effect lag_s after it is sent; a positive angular turns
    clockwise, as the Pilot's own commands do), then moved `gain` of the way
    towards the reading, across north the short way. Between readings the
    estimate is held. With gain 1 every reading comes back unchanged; with
    yaw_dps 0 it is a plain exponential average, which lags behind turns.
    Readings are degrees clockwise (Conventions.heading), before the learned
    compass bias. This is pace_c.py's HeadingSmoother, moved inside the pilot.
    """

    def __init__(self, gain=0.3, yaw_dps=48.0, lag_s=0.5, keep_s=10.0):
        self.gain = float(gain)
        self.yaw_dps = float(yaw_dps)
        self.lag_s = float(lag_s)
        self.keep_s = keep_s
        self.readings = 0
        self._cmds = collections.deque()
        self._est = None
        self._est_t = None
        self._ts = None
        self._reading = None

    def record(self, t, angular):
        """An angular command (positive = right) sent at t."""
        self._cmds.append((t, float(angular)))
        while len(self._cmds) > 1 and self._cmds[1][0] < t - self.keep_s:
            self._cmds.popleft()

    def _commanded(self, a, b, end_t):
        """Integral over [a, b] of the angular commanded, the last held to end_t."""
        total = 0.0
        cmds = list(self._cmds)
        for k, (t0, angular) in enumerate(cmds):
            t1 = cmds[k + 1][0] if k + 1 < len(cmds) else end_t
            lo, hi = max(t0, a), min(t1, b)
            if hi > lo:
                total += angular * (hi - lo)
        return total

    def update(self, t, compass, timestamp=None):
        """The smoothed heading after this reading (None if there is no reading)."""
        if compass is None:
            return None
        if self._est is None:
            self._est = compass % 360.0
        else:
            new = timestamp != self._ts if timestamp is not None else compass != self._reading
            if not new:
                return self._est
            turn = 0.0
            if self.yaw_dps:
                turn = self.yaw_dps * self._commanded(self._est_t - self.lag_s,
                                                      t - self.lag_s, t)
            pred = self._est + turn
            self._est = (pred + self.gain * wrap180(compass - pred)) % 360.0
        self.readings += 1
        self._ts, self._reading, self._est_t = timestamp, compass, t
        return self._est

    def stats(self):
        return {"gain": self.gain, "yaw_dps": self.yaw_dps, "lag_s": self.lag_s,
                "readings": self.readings}


def make_smoother(calibration=None):
    """The HeadingSmoother --smooth-heading drives with: SMOOTH_HEADING, with the
    turn rate --calibrate measured (yaw_dps_at_full) when the calibration has a
    usable one."""
    kw = dict(SMOOTH_HEADING)
    try:
        yaw = float((calibration or {}).get("yaw_dps_at_full"))
    except (TypeError, ValueError):
        yaw = None
    if yaw is not None and math.isfinite(yaw) and yaw > 0:
        kw["yaw_dps"] = yaw
    return HeadingSmoother(**kw)


# --- control --------------------------------------------------------------

class Steering:
    """Turns distance and heading error into an SDK (linear, angular) command.

    Positive angular turns right (clockwise); Conventions converts it for a
    rover that turns the other way.
    """

    def __init__(self, cruise=0.6, kp=1.0 / 60.0, max_angular=0.6,
                 turn_in_place_deg=60.0, slow_radius_m=8.0):
        self.cruise = cruise
        self.kp = kp
        self.max_angular = max_angular
        self.turn_in_place_deg = turn_in_place_deg
        self.slow_radius_m = slow_radius_m

    def command(self, distance_m, error_deg):
        angular = clamp(self.kp * error_deg, -self.max_angular, self.max_angular)
        if abs(error_deg) > self.turn_in_place_deg:
            return 0.0, angular
        linear = self.cruise * max(0.25, math.cos(math.radians(error_deg)))
        if distance_m < self.slow_radius_m:
            linear *= max(0.5, distance_m / self.slow_radius_m)
        return clamp(linear), angular


def make_steering(simulate, cruise=None, max_angular=None, turn_in_place_deg=None,
                  marathon=False):
    """The Steering the command line drives with: ROVER_STEERING on a real rover
    or with marathon, the class defaults in the simulator, and either overridden
    by the options given. cruise defaults to 0.6, or MARATHON's with marathon."""
    kw = {} if simulate and not marathon else dict(ROVER_STEERING)
    if max_angular is not None:
        kw["max_angular"] = max_angular
    if turn_in_place_deg is not None:
        kw["turn_in_place_deg"] = turn_in_place_deg
    if cruise is None:
        cruise = MARATHON["cruise"] if marathon else 0.6
    return Steering(cruise=cruise, **kw)


def make_vision(source, camera, simulate, plain=False):
    """The free_space.VisionGuard the command line drives with: free_space.REAL_ROVER
    on a real rover, the class defaults in the simulator or with `plain`."""
    import free_space
    kw = {} if simulate or plain else dict(free_space.REAL_ROVER)
    return free_space.VisionGuard(source, camera=camera, **kw)


class PathFollower:
    """Pure pursuit along a planned path.

    It aims at the point `lookahead_m` ahead of the rover's place on the path,
    and only moves forward along it, so a path that doubles back is still
    followed in order.
    """

    def __init__(self, points, lookahead_m=8.0, search_m=60.0, step_m=2.0):
        self.points = densify(points, step_m)
        self.lookahead_n = max(1, int(round(lookahead_m / step_m)))
        self.window = max(2, int(round(search_m / step_m)))
        self.i = 0

    def target(self, lat, lon):
        """The (lat, lon) to steer at, and the rover's distance from the path."""
        end = min(len(self.points), self.i + self.window)
        best, best_d = self.i, math.inf
        for k in range(self.i, end):
            d = haversine_m(lat, lon, *self.points[k])
            if d < best_d:
                best, best_d = k, d
        self.i = best
        return self.points[min(len(self.points) - 1, best + self.lookahead_n)], best_d


class Pilot:
    """Flies an SDK mission: steer to each checkpoint in turn and report it.

    `planner`, if given, is called as planner(lat, lon, checkpoint_lat,
    checkpoint_lon) at the start of each leg and returns a list of (lat, lon)
    points to follow, or None to head straight for the checkpoint.

    `vision`, if given, is called as vision.advise(t, error_deg, distance_m)
    while driving forward and returns the (error_deg, speed_scale) to use
    instead (free_space.VisionGuard).

    `conventions` (Conventions) says how this rover's orientation and angular
    run; by default, degrees clockwise and positive angular turning right.

    `gps_lag_s`, if above 0, is how late the GPS is: the rover's position is
    then taken as the last fix moved forward by the driving commanded since
    (LagCompensator, with `cmd_latency_s` and `speed_mps_at_full`) instead of
    the smoothed fixes.

    `telemetry_timeout_s`: the rover is stopped while no new telemetry has
    come in for longer than this (TelemetryWatch; 0 = off). If the rover has a
    telemetry_age() method (SdkClient: GET /status), that is asked too.

    `tip_angle_deg`: the rover is stopped while its accelerometer shows gravity
    more than this far from where it pointed at the start (TipWatch; 0 = off).

    `dead_reckon`, if given (dead_reckon.DeadReckoner), carries the position
    from the last GPS fix by the wheels instead of smoothing the fixes, and
    keeps the rover going through a GPS dropout while it has an estimate
    (checkpoints are reported only with a fix). Not together with gps_lag_s.

    `dead_reckon_gaps`: with dead_reckon, steer by the wheels' estimate only
    while the GPS has no fresh fix, and by the smoothed GPS otherwise.

    `smooth_heading`, if given (HeadingSmoother), smooths the compass over
    its readings before anything uses it: the bias fit, the heading steered
    by and dead reckoning.

    `path_lookahead_m` (an attribute, 8 m): how far ahead along a planned
    path the rover aims (PathFollower's lookahead_m). The command line sets
    a real rover's to PATH_LOOKAHEAD_M.
    """

    def __init__(self, rover, clock=time.monotonic, sleep=time.sleep,
                 steering=None, rate_hz=10.0, report_radius_m=10.0,
                 hold_radius_m=3.0, retry_s=2.0, settle_s=1.5,
                 stuck_window_s=10.0, stuck_min_move_m=1.5, planner=None,
                 replan_m=30.0, replan_s=30.0, vision=None, conventions=None,
                 gps_lag_s=0.0, cmd_latency_s=0.8, speed_mps_at_full=0.79,
                 telemetry_timeout_s=TELEMETRY_TIMEOUT_S, tip_angle_deg=TIP_ANGLE_DEG,
                 dead_reckon=None, log=None, smooth_heading=None,
                 dead_reckon_gaps=False):
        self.rover = rover
        self.clock = clock
        self.sleep = sleep
        self.steering = steering or Steering()
        self.period = 1.0 / rate_hz
        self.report_radius_m = report_radius_m
        self.hold_radius_m = hold_radius_m
        self.retry_s = retry_s
        self.settle_s = settle_s
        self.stuck_window_s = stuck_window_s
        self.stuck_min_move_m = stuck_min_move_m
        self.planner = planner
        self.replan_m = replan_m
        self.replan_s = replan_s
        self.vision = vision
        self.conventions = conventions or Conventions()
        self.lag = (LagCompensator(gps_lag_s, cmd_latency_s, speed_mps_at_full)
                    if gps_lag_s > 0 else None)
        if dead_reckon is not None and self.lag is not None:
            raise ValueError("use gps_lag_s or dead_reckon, not both")
        self.dr = dead_reckon
        self.dr_gaps_only = dead_reckon_gaps
        self.smoother = smooth_heading
        self.bridged_s = 0.0  # seconds driven on the wheels' estimate alone
        self.log = log
        self.gps = GpsFilter()
        self.heading = HeadingEstimator()
        if self.conventions.bias_deg is not None:
            self.heading.bias = self.conventions.bias_deg
        self.telemetry = TelemetryWatch(telemetry_timeout_s, getattr(rover, "telemetry_age", None))
        self.telemetry_stops = 0
        self.tip = TipWatch(tip_angle_deg)
        self.tip_stops = 0
        self.battery = BatteryLog()
        self.cmd = (0.0, 0.0)
        self.pos = (None, None)
        self.reached = []
        self.legs = []
        self.reports = 0
        self.recoveries = 0
        self.plans = 0
        self.path = None
        self.path_lookahead_m = 8.0
        self._path_seq = None
        self._plan_t = None
        self._history = collections.deque()
        self._maneuver = []
        self._last_log_t = None
        self._leg_t0 = None
        self._leg_m = None
        self._leg_reports = 0
        self._leg_recoveries = 0
        self._heading_now = None
        self._telemetry_ok = True
        self._upright = True

    def send(self, linear, angular):
        self.cmd = (linear, angular)
        if self.lag is not None:
            self.lag.record(self.clock(), linear, self._heading_now)
        if self.smoother is not None:
            self.smoother.record(self.clock(), angular)
        self.rover.control(linear, self.conventions.angular(angular))

    def stop(self):
        self.send(0.0, 0.0)

    def _wait(self, tick):
        self.sleep(max(0.0, self.period - (self.clock() - tick)))

    def _settled_stop(self):
        end = self.clock() + self.settle_s
        while self.clock() < end:
            tick = self.clock()
            self.stop()
            self._wait(tick)

    def _log(self, event, **fields):
        if self.log:
            self.log(dict({"t": round(self.clock(), 2), "event": event}, **fields))

    def _telemetry_stale(self, t):
        """True while the rover's telemetry has stopped coming in; logs each change."""
        stale = self.telemetry.stale(t)
        if stale == self._telemetry_ok:
            self._telemetry_ok = not stale
            if stale:
                self.telemetry_stops += 1
                since = self.telemetry.since(t)
                self._log("telemetry-stale", since_s=None if since is None else round(since, 1),
                          sdk_age_s=self.telemetry.sdk_age)
            else:
                self._log("telemetry-back")
        return stale

    def _tipped(self, t, accels):
        """True while the accelerometer says the rover is on its side; logs each change."""
        tipped = self.tip.update(t, accels)
        if tipped == self._upright:
            self._upright = not tipped
            if tipped:
                self.tip_stops += 1
                self._log("tipped", angle_deg=round(self.tip.angle, 1))
            else:
                self._log("upright")
        return tipped

    def _position(self, t):
        """Where the rover is taken to be: the smoothed GPS or, with gps_lag_s,
        the last fix moved forward by the driving commanded since it was seen,
        or with dead_reckon, the wheels' estimate whenever it has one (with
        dead_reckon_gaps, only while the GPS has no fresh fix)."""
        if self.dr is not None:
            pos = self.dr.position(t)
            if pos is not None and not (self.dr_gaps_only and self.gps.has_fix(t)):
                return pos
        if self.lag is None or self.gps.raw is None:
            return self.gps.lat, self.gps.lon
        north, east = self.lag.offset(t, self.gps.raw_t)
        return offset_latlon(self.gps.raw[0], self.gps.raw[1], north, east)

    def _start_leg(self):
        self._leg_t0, self._leg_m = self.clock(), None
        self._leg_reports, self._leg_recoveries = self.reports, self.recoveries

    def _finish_leg(self, seq):
        """Sum up the leg that just ended at checkpoint `seq`, and start the next one."""
        leg = {"seq": seq, "elapsed_s": round(self.clock() - self._leg_t0, 1),
               "straight_m": None if self._leg_m is None else round(self._leg_m, 1),
               "reports": self.reports - self._leg_reports,
               "recoveries": self.recoveries - self._leg_recoveries,
               "battery_pct": self.battery.level}
        self.legs.append(leg)
        self._log("checkpoint", **leg)
        self._start_leg()

    def _stuck(self, t, linear):
        # Measured on the GPS itself: a predicted position would always move.
        h = self._history
        h.append((t, self.gps.lat, self.gps.lon, linear))
        while t - h[0][0] > self.stuck_window_s:
            h.popleft()
        if t - h[0][0] < 0.9 * self.stuck_window_s:
            return False
        if sum(x[3] for x in h) / len(h) < 0.4 * self.steering.cruise:
            return False
        return haversine_m(h[0][1], h[0][2], self.gps.lat, self.gps.lon) < self.stuck_min_move_m

    def _start_recovery(self, t):
        self.recoveries += 1
        turn = 0.6 if self.recoveries % 2 else -0.6
        self._maneuver = [(t + 2.0, -0.4, 0.0), (t + 3.5, 0.0, turn), (t + 6.0, 0.5, 0.0)]
        self._history.clear()
        self._log("recovery", n=self.recoveries)

    def _plan(self, t, seq, lat, lon):
        self._path_seq, self._plan_t = seq, t
        try:
            points = self.planner(self.pos[0], self.pos[1], lat, lon)
        except Exception as e:  # a failed plan must not stop the rover; it heads straight on
            points = None
            self._log("plan-failed", seq=seq, error=str(e))
        self.path = (PathFollower(points, lookahead_m=self.path_lookahead_m)
                     if points and len(points) >= 2 else None)
        self.plans += 1
        self._log("plan", seq=seq, points=len(points) if points else 0)

    def _aim(self, t, seq, lat, lon):
        """Where to steer now: a point along the planned path, or the checkpoint itself."""
        if self.planner is None:
            return lat, lon
        stale = self._plan_t is not None and t - self._plan_t >= self.replan_s
        if self._path_seq != seq or (self.path is None and stale):
            self._plan(t, seq, lat, lon)
        if self.path is None:
            return lat, lon
        aim, off = self.path.target(*self.pos)
        if off > self.replan_m and stale:
            self._plan(t, seq, lat, lon)
            if self.path is None:
                return lat, lon
            aim, _ = self.path.target(*self.pos)
        return aim

    def _steer(self, t, distance, aim_lat, aim_lon, heading):
        while self._maneuver and t >= self._maneuver[0][0]:
            self._maneuver.pop(0)
        if self._maneuver:
            return self._maneuver[0][1], self._maneuver[0][2]
        if distance < self.hold_radius_m:
            self._history.clear()
            return 0.0, 0.0
        if heading is None:
            # No compass and no recent course: drive straight to learn one from GPS.
            error, scale = 0.0, 0.5
        else:
            target = bearing_deg(self.pos[0], self.pos[1], aim_lat, aim_lon)
            error, scale = wrap180(target - heading), 1.0
        if self.vision is not None and abs(error) <= self.steering.turn_in_place_deg:
            error, seen = self.vision.advise(t, error, distance)
            scale *= seen
        linear, angular = self.steering.command(distance, error)
        linear *= scale
        if self._stuck(t, linear):
            self._start_recovery(t)
            return self._maneuver[0][1], self._maneuver[0][2]
        return linear, angular

    def _confirmed(self, seq):
        """After a report got no answer, ask the server whether it counted anyway."""
        _, latest = self.rover.checkpoints()
        return latest >= seq

    def _result(self, ok, reason, t0, total):
        out = {
            "ok": ok,
            "reason": reason,
            "reached": list(self.reached),
            "checkpoints": total,
            "reports": self.reports,
            "recoveries": self.recoveries,
            "plans": self.plans,
            "elapsed_s": round(self.clock() - t0, 1),
            "compass_bias_deg": round(self.heading.bias, 1),
            "calibrations": self.heading.calibrations,
            "telemetry_stops": self.telemetry_stops,
            "tip_stops": self.tip_stops,
            "battery": self.battery.result(),
            "legs": list(self.legs),
        }
        if self.vision is not None:
            out["vision"] = self.vision.stats()
        if self.dr is not None:
            out["dead_reckon"] = dict(self.dr.stats(), bridged_s=round(self.bridged_s, 1))
        if self.smoother is not None:
            out["smooth_heading"] = self.smoother.stats()
        return out

    def run(self, start=True, timeout_s=3600.0):
        t0 = self.clock()
        try:
            if start and not self.rover.start_mission():
                return self._result(False, "start-mission failed", t0, 0)
            checkpoints, latest = self.rover.checkpoints()
            remaining = [c for c in checkpoints if c[0] > latest]
            total = len(remaining)
            if not remaining:
                return self._result(False, "no checkpoints left (is MISSION_SLUG set?)", t0, 0)
            next_try = t0
            self._start_leg()
            while remaining:
                tick = self.clock()
                if tick - t0 > timeout_s:
                    return self._result(False, "timeout", t0, total)
                data = self.rover.data() or {}
                self.telemetry.update(tick, data.get("timestamp"))
                new_fix = self.gps.update(data.get("latitude"), data.get("longitude"), tick)
                compass = self.conventions.heading(data.get("orientation"))
                if self.smoother is not None:
                    compass = self.smoother.update(tick, compass, data.get("timestamp"))
                self.heading.update(tick, new_fix, compass, *self.cmd)
                self._heading_now = self.heading.heading(compass, tick)
                if self.dr is not None:
                    self.dr.wheels(tick, data.get("rpms"))
                    self.dr.update(tick, new_fix, compass, self._heading_now)
                stale = self._telemetry_stale(tick)
                tipped = self._tipped(tick, data.get("accels"))
                self.battery.update(data.get("battery"),
                                    parse_fix(data.get("latitude"), data.get("longitude")))
                # Through a GPS dropout the wheels' estimate keeps the rover going.
                bridging = (self.dr is not None and self.gps.lat is not None
                            and not self.gps.has_fix(tick)
                            and self.dr.position(tick) is not None)
                if stale or tipped or not (self.gps.has_fix(tick) or bridging):
                    self._history.clear()
                    self.stop()
                    self._wait(tick)
                    continue
                if bridging:
                    self._history.clear()  # the GPS stands still, the rover doesn't
                    self.bridged_s += self.period
                seq, target_lat, target_lon = remaining[0]
                self.pos = self._position(tick)
                distance = haversine_m(self.pos[0], self.pos[1], target_lat, target_lon)
                if self.lag is None and self.gps.raw is not None:
                    distance = min(distance, haversine_m(self.gps.raw[0], self.gps.raw[1],
                                                         target_lat, target_lon))
                if self._leg_m is None:
                    self._leg_m = distance
                if distance <= self.report_radius_m and tick >= next_try and not bridging:
                    if len(remaining) == 1:
                        self._settled_stop()
                    res = self.rover.checkpoint_reached()
                    self.reports += 1
                    if not res.get("ok") and res.get("status") == 0 and self._confirmed(seq):
                        res = dict(res, ok=True)
                    if res.get("ok"):
                        remaining.pop(0)
                        self.reached.append(seq)
                        self._finish_leg(seq)
                        if res.get("mission_completed") or not remaining:
                            self.stop()
                            return self._result(True, "mission completed", t0, total)
                        continue
                    self._log("refused", seq=seq, status=res.get("status"),
                              server_distance_m=res.get("distance"))
                    next_try = self.clock() + self.retry_s
                aim_lat, aim_lon = self._aim(tick, seq, target_lat, target_lon)
                linear, angular = self._steer(tick, distance, aim_lat, aim_lon, self._heading_now)
                self.send(linear, angular)
                if self._last_log_t is None or tick - self._last_log_t >= 1.0:
                    self._last_log_t = tick
                    fields = {}
                    if self.vision is not None and self.vision.clear_ahead is not None:
                        fields["clear_m"] = round(self.vision.clear_ahead, 1)
                    self._log("tick", seq=seq, lat=round(self.gps.lat, 7),
                              lon=round(self.gps.lon, 7), dist_m=round(distance, 1),
                              bias=round(self.heading.bias, 1),
                              cmd=[round(linear, 2), round(angular, 2)], **fields)
                self._wait(tick)
            return self._result(True, "mission completed", t0, total)
        finally:
            self.stop()


def check_route(rover, planner, clock=time.monotonic, sleep=time.sleep, fix_timeout_s=10.0):
    """Plan every remaining leg from where the rover is now, without driving it.

    Returns (summary, legs): a summary to print, and route_planner.plan_legs'
    legs with their points (for legs_geojson). Nothing is sent to the rover.
    """
    import route_planner
    end = clock() + fix_timeout_s
    while True:
        data = rover.data() or {}
        fix = parse_fix(data.get("latitude"), data.get("longitude"))
        if fix is not None:
            break
        if clock() >= end:
            return {"ok": False, "reason": "no GPS fix"}, []
        sleep(0.5)
    checkpoints, latest = rover.checkpoints()
    remaining = [c for c in checkpoints if c[0] > latest]
    if not remaining:
        return {"ok": False, "reason": "no checkpoints left (is MISSION_SLUG set?)"}, []
    legs = route_planner.plan_legs(planner, fix, remaining)
    routed = [leg for leg in legs if leg["route_m"] is not None]
    missing = len(legs) - len(routed)
    summary = {
        "ok": missing == 0,
        "reason": ("every leg has a walkable route" if missing == 0
                   else "%d of %d legs have no walkable route" % (missing, len(legs))),
        "start": [round(fix[0], 7), round(fix[1], 7)],
        "legs": [{k: v for k, v in leg.items() if k != "points"} for leg in legs],
        "straight_m": round(sum(leg["straight_m"] for leg in legs), 1),
        "route_m": round(sum(leg["route_m"] for leg in routed), 1),
    }
    return summary, legs


# --- the SDK over HTTP ----------------------------------------------------

def _json(raw):
    try:
        out = json.loads((raw or b"{}").decode("utf-8") or "{}")
    except (ValueError, UnicodeDecodeError):
        return {}
    if isinstance(out, list):
        return {"items": out}
    return out if isinstance(out, dict) else {}


def _find_key(obj, key):
    if isinstance(obj, dict):
        if key in obj:
            return obj[key]
        obj = list(obj.values())
    if isinstance(obj, list):
        for item in obj:
            found = _find_key(item, key)
            if found is not None:
                return found
    return None


class SdkClient:
    """Talks to a running earth-rovers-sdk server (default http://localhost:8000)."""

    def __init__(self, base_url="http://localhost:8000", timeout=5.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _req(self, method, path, body=None, timeout=None):
        data = None if body is None else json.dumps(body).encode("utf-8")
        req = urllib.request.Request(self.base_url + path, data=data, method=method,
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=timeout or self.timeout) as resp:
                return resp.status, _json(resp.read())
        except urllib.error.HTTPError as e:
            return e.code, _json(e.read())
        except (urllib.error.URLError, OSError, ValueError):
            return 0, {}

    def data(self):
        status, body = self._req("GET", "/data")
        return body if status == 200 else {}

    def telemetry_age(self):
        """Seconds since the SDK last got telemetry from the rover (GET /status
        telemetry_age_s), or None if it doesn't say (no telemetry yet, or an
        SDK without /status)."""
        status, body = self._req("GET", "/status", timeout=2.0)
        if status != 200:
            return None
        age = body.get("telemetry_age_s")
        if isinstance(age, bool):
            return None
        try:
            age = float(age)
        except (TypeError, ValueError):
            return None
        return age if math.isfinite(age) else None

    def control(self, linear, angular):
        self._req("POST", "/control", {"command": {
            "linear": round(clamp(linear), 3), "angular": round(clamp(angular), 3), "lamp": 0}})

    def front_image(self):
        """The latest front-camera frame as encoded image bytes (JPEG by default), or None."""
        status, body = self._req("GET", "/v2/front", timeout=2.0)
        frame = body.get("front_frame") if status == 200 else None
        if not isinstance(frame, str) or not frame:
            return None
        if frame.startswith("data:"):
            frame = frame.split(",", 1)[-1]
        try:
            return base64.b64decode(frame)
        except ValueError:
            return None

    def missions(self):
        """The missions GET /missions lists for this bot (each with slug,
        distance_in_m and checkpoints_count), or None if the call failed."""
        status, body = self._req("GET", "/missions")
        if status != 200:
            return None
        for key in ("missions", "items", "data"):
            if isinstance(body.get(key), list):
                return [m for m in body[key] if isinstance(m, dict)]
        return []

    def start_mission(self):
        status, _ = self._req("POST", "/start-mission", {})
        return status == 200

    def checkpoints(self):
        _, body = self._req("GET", "/checkpoints-list")
        out = []
        for cp in body.get("checkpoints_list") or []:
            try:
                out.append((int(cp["sequence"]), float(cp["latitude"]), float(cp["longitude"])))
            except (KeyError, TypeError, ValueError):
                continue
        out.sort()
        try:
            latest = int(body.get("latest_scanned_checkpoint") or 0)
        except (TypeError, ValueError):
            latest = 0
        return out, latest

    def checkpoint_reached(self):
        status, body = self._req("POST", "/checkpoint-reached", {},
                                 timeout=max(self.timeout, REPORT_TIMEOUT_S))
        if status == 200:
            return {"ok": True, "status": 200, "distance": None,
                    "mission_completed": bool(body.get("mission_completed"))}
        distance = _find_key(body, "proximate_distance_to_checkpoint")
        try:
            distance = float(distance)
        except (TypeError, ValueError):
            distance = None
        return {"ok": False, "status": status, "distance": distance, "mission_completed": False}


class SdkCamera:
    """Frame source for free_space.VisionGuard: the SDK's front camera, shrunk (needs Pillow)."""

    def __init__(self, client, camera):
        self.client = client
        self.camera = camera

    def __call__(self):
        import free_space
        data = self.client.front_image()
        if data is None:
            return None
        return free_space.decode_frame(data, self.camera.width, self.camera.height)


# --- simulator ------------------------------------------------------------

class SimRover:
    """Offline stand-in for the SDK: a skid-steer rover with the usual troubles.

    Commands take effect after `latency_s`; GPS updates every `gps_period_s`
    with noise and occasional no-fix readings, showing where the rover was
    `gps_delay_s` earlier; the compass is off by `compass_error_deg`.
    Checkpoints are judged on the reported GPS, like the real server, and the
    last one is refused (503) unless the rover is stopped.
    `obstacles` are (north_m, east_m, radius_m) hedges the rover can't drive
    through; camera_frame() renders what its front camera would see.
    By default orientation reads degrees clockwise and a positive angular
    turns right; `orientation_scale`, `orientation_clockwise` and
    `angular_sign` (-1 turns left) make a rover that doesn't.
    It reports no accelerometer, so the tip watch never fires on it.
    With `wheel_mps_per_rpm` it reports `rpms` rows like an Earth Rover's
    ([rpm x 4, timestamp], the left and right wheels at the commanded speed and
    turn, `wheel_track_m` apart), sent together every `rpm_period_s`.
    """

    def __init__(self, checkpoints_m, seed=0, start=(37.8719, -122.2585),
                 heading_deg=200.0, max_speed_mps=1.2, max_yaw_dps=60.0,
                 latency_s=0.5, gps_noise_m=1.5, gps_period_s=1.0,
                 gps_dropout=0.05, compass_error_deg=-25.0, compass_noise_deg=3.0,
                 tolerance_m=15.0, dt=0.1, blocked_until_s=0.0, obstacles=(),
                 rover_radius_m=0.2, obstacle_height_m=1.0, orientation_scale=360.0,
                 orientation_clockwise=True, angular_sign=1.0, gps_delay_s=0.0,
                 wheel_mps_per_rpm=None, wheel_track_m=0.2, rpm_period_s=0.0):
        self.rng = random.Random(seed)
        self.seed = seed
        self.lat0, self.lon0 = start
        self.checkpoint_coords = [offset_latlon(self.lat0, self.lon0, n, e)
                                  for n, e in checkpoints_m]
        self.heading = heading_deg % 360.0
        self.max_speed_mps = max_speed_mps
        self.max_yaw_dps = max_yaw_dps
        self.latency_s = latency_s
        self.gps_noise_m = gps_noise_m
        self.gps_period_s = gps_period_s
        self.gps_dropout = gps_dropout
        self.gps_delay_s = gps_delay_s
        self.compass_error = compass_error_deg
        self.compass_noise_deg = compass_noise_deg
        self.tolerance_m = tolerance_m
        self.dt = dt
        self.blocked_until_s = blocked_until_s
        self.obstacles = list(obstacles)
        self.rover_radius_m = rover_radius_m
        self.obstacle_height_m = obstacle_height_m
        self.orientation_scale = orientation_scale
        self.orientation_clockwise = orientation_clockwise
        self.angular_sign = angular_sign
        self.wheel_mps_per_rpm = wheel_mps_per_rpm
        self.wheel_track_m = wheel_track_m
        self.rpm_period_s = rpm_period_s
        self.rpms = []  # the wheel rows data() serves
        self._rpm_rows = []
        self._rpm_sent_t = 0.0
        self.contacts = 0  # steps on which an obstacle stopped the rover
        self.min_gap = math.inf  # closest the rover's centre came to an obstacle's edge
        self.travelled = 0.0  # metres driven
        self.t = 0.0
        self.east = self.north = 0.0
        self.queue = collections.deque()
        self.applied = (0.0, 0.0)
        self.last_cmd_t = 0.0
        self.next_cp = 0
        self.reverse_seen = False
        self._noise = None
        self._frames = 0
        self._track = collections.deque([(0.0, 0.0, 0.0)])  # (t, north, east) for gps_delay_s
        self._sample_gps()

    def _delayed_position(self):
        """(north, east) where the rover was gps_delay_s ago."""
        if self.gps_delay_s <= 0:
            return self.north, self.east
        cutoff = self.t - self.gps_delay_s + 1e-9
        while len(self._track) > 1 and self._track[1][0] <= cutoff:
            self._track.popleft()
        _, north, east = self._track[0]
        return north, east

    def _sample_gps(self):
        north, east = self._delayed_position()
        if self.rng.random() < self.gps_dropout:
            self.gps = (NO_FIX, NO_FIX)
        else:
            self.gps = offset_latlon(self.lat0, self.lon0,
                                     north + self.rng.gauss(0, self.gps_noise_m),
                                     east + self.rng.gauss(0, self.gps_noise_m))
        self._next_gps_t = self.t + self.gps_period_s

    def _hits_obstacle(self, north, east):
        """True if moving to (north, east) would push the rover into an obstacle."""
        for on, oe, r in self.obstacles:
            d = math.hypot(north - on, east - oe)
            if d < r + self.rover_radius_m and d < math.hypot(self.north - on, self.east - oe):
                return True
        return False

    def _step(self):
        while self.queue and self.queue[0][0] <= self.t:
            _, linear, angular = self.queue.popleft()
            self.applied = (linear, angular)
        if self.t - self.last_cmd_t > 3.0:  # the SDK's dead-man stop
            self.applied = (0.0, 0.0)
        linear, angular = self.applied
        if linear < 0:
            self.reverse_seen = True
        self.heading = (self.heading + self.angular_sign * angular * self.max_yaw_dps * self.dt) % 360.0
        if self.t >= self.blocked_until_s:
            v = linear * self.max_speed_mps * self.dt
            r = math.radians(self.heading)
            north, east = self.north + v * math.cos(r), self.east + v * math.sin(r)
            if self._hits_obstacle(north, east):
                self.contacts += 1
            else:
                self.north, self.east = north, east
                self.travelled += abs(v)
        for on, oe, r in self.obstacles:
            self.min_gap = min(self.min_gap, math.hypot(self.north - on, self.east - oe) - r)
        self.t += self.dt
        if self.wheel_mps_per_rpm:
            self._wheel_row(linear, angular)
        if self.gps_delay_s > 0:
            self._track.append((self.t, self.north, self.east))
        if self.t >= self._next_gps_t - 1e-9:
            self._sample_gps()

    def _wheel_row(self, linear, angular):
        """Record the wheels' RPM now; send the rows every rpm_period_s."""
        v = linear * self.max_speed_mps
        # Turning right (clockwise) runs the left wheels faster.
        w = (math.radians(self.angular_sign * angular * self.max_yaw_dps)
             * self.wheel_track_m / 2.0)
        left = round((v + w) / self.wheel_mps_per_rpm, 2)
        right = round((v - w) / self.wheel_mps_per_rpm, 2)
        self._rpm_rows.append([left, right, left, right, round(self.t, 3)])
        if self.t - self._rpm_sent_t >= self.rpm_period_s - 1e-9:
            self.rpms, self._rpm_rows = self._rpm_rows, []
            self._rpm_sent_t = self.t

    # clock/sleep replace time.monotonic/time.sleep for the Pilot
    def clock(self):
        return self.t

    def sleep(self, seconds):
        for _ in range(max(1, int(round(seconds / self.dt)))):
            self._step()

    # the SDK surface the Pilot uses
    def control(self, linear, angular):
        self.last_cmd_t = self.t
        self.queue.append((self.t + self.latency_s, clamp(float(linear)), clamp(float(angular))))

    def data(self):
        compass = (self.heading + self.compass_error
                   + self.rng.gauss(0, self.compass_noise_deg)) % 360.0
        if not self.orientation_clockwise:
            compass = -compass % 360.0
        if self.orientation_scale != 360.0:
            compass = compass * self.orientation_scale / 360.0
        out = {"latitude": self.gps[0], "longitude": self.gps[1], "orientation": compass,
               "gps_signal": 0 if self.gps[0] == NO_FIX else 30, "timestamp": self.t}
        if self.wheel_mps_per_rpm:
            out["rpms"] = [list(r) for r in self.rpms]
        return out

    def camera_frame(self, camera):
        """What the front camera sees now: grey ground, green hedges, a little noise."""
        import free_space
        if self._noise is None:
            self._noise = free_space.make_noise(seed=self.seed)
        r = math.radians(self.heading)
        cos_h, sin_h = math.cos(r), math.sin(r)
        rel = []
        for on, oe, radius in self.obstacles:
            dn, de = on - self.north, oe - self.east
            rel.append((de * cos_h - dn * sin_h, de * sin_h + dn * cos_h, radius,
                        self.obstacle_height_m, free_space.HEDGE_GREEN))
        self._frames += 1
        return free_space.render(camera, rel, noise=self._noise, offset=self._frames * 997)

    def start_mission(self):
        return True

    def checkpoints(self):
        return ([(i + 1, lat, lon) for i, (lat, lon) in enumerate(self.checkpoint_coords)],
                self.next_cp)

    def checkpoint_reached(self):
        total = len(self.checkpoint_coords)
        if self.next_cp >= total:
            return {"ok": False, "status": 400, "distance": None, "mission_completed": True}
        fix = parse_fix(*self.gps)
        if fix is None:
            return {"ok": False, "status": 400, "distance": None, "mission_completed": False}
        if self.next_cp == total - 1 and self.applied != (0.0, 0.0):
            return {"ok": False, "status": 503, "distance": None, "mission_completed": False}
        distance = haversine_m(fix[0], fix[1], *self.checkpoint_coords[self.next_cp])
        if distance > self.tolerance_m:
            return {"ok": False, "status": 400, "distance": distance, "mission_completed": False}
        self.next_cp += 1
        return {"ok": True, "status": 200, "distance": None,
                "mission_completed": self.next_cp == total}


# --- command line ---------------------------------------------------------

def use_dead_reckoning(dead_reckon, simulate, gps_lag):
    """--dead-reckon / --no-dead-reckon if given; otherwise on for a real rover,
    unless --gps-lag asks for the other correction, and off in the simulator.
    Since v0.15.0 the default steers by it only while the GPS has no fresh fix
    (use_dead_reckon_gaps; pace_i.py's rule R1)."""
    if dead_reckon is not None:
        return dead_reckon
    return not simulate and gps_lag <= 0


def use_dead_reckon_gaps(dead_reckon_gaps, asked, dead_reckon):
    """--dead-reckon-gaps if given; otherwise on whenever dead reckoning is on
    without --dead-reckon or --no-dead-reckon given (`asked` is None): the
    real-rover default since v0.15.0. --dead-reckon still steers by the wheels
    whenever it can, as v0.13.0's pilot did."""
    if dead_reckon_gaps:
        return True
    return asked is None and bool(dead_reckon)


def use_smooth_heading(smooth_heading, simulate):
    """--smooth-heading / --no-smooth-heading if given; otherwise on for a real
    rover and off in the simulator, so the simulator flies as before (pace_f.py)."""
    if smooth_heading is not None:
        return smooth_heading
    return not simulate


def make_heading(conventions=None):
    """A real rover's compass-bias learner: a HeadingEstimator with
    HEADING_LEARNER's settings (pace_m.py's rule R2), starting from the
    calibration's bias when it has one, as the Pilot starts its own."""
    heading = HeadingEstimator(**HEADING_LEARNER)
    if conventions is not None and conventions.bias_deg is not None:
        heading.bias = conventions.bias_deg
    return heading


def main(argv=None):
    p = argparse.ArgumentParser(
        description="GPS waypoint pilot for the FrodoBots Earth Rover SDK.")
    p.add_argument("--sdk", default="http://localhost:8000",
                   help="URL of the running earth-rovers-sdk server")
    p.add_argument("--simulate", action="store_true",
                   help="fly the built-in demo mission in the simulator instead")
    p.add_argument("--seed", type=int, default=1, help="simulator random seed")
    p.add_argument("--obstacles", action="store_true",
                   help="(simulator) put two hedges on the demo route")
    p.add_argument("--sim-quirks", action="store_true",
                   help="(simulator) orientation reads 0-255 counter-clockwise and a "
                        "positive angular turns left")
    p.add_argument("--sim-real", action="store_true",
                   help="(simulator) move like the rovers in FrodoBots-2K: 0.79 m/s at full "
                        "linear, commands 0.8 s late and GPS 1.5 s behind the wheels")
    p.add_argument("--list-missions", action="store_true",
                   help="print the missions the SDK lists for this bot (GET /missions) and exit")
    p.add_argument("--no-start", action="store_true",
                   help="don't call /start-mission (resume a mission already running)")
    p.add_argument("--cruise", type=float, default=None,
                   help="cruise linear command, 0-1 (default 0.6, or 0.8 with --marathon)")
    p.add_argument("--max-angular", type=float, default=None,
                   help="largest angular command, 0-1 (default: 1.0 on a real rover, "
                        "0.6 in the simulator)")
    p.add_argument("--turn-in-place", type=float, default=None,
                   help="turn in place when the heading error is above this many degrees "
                        "(default: 90 on a real rover, 60 in the simulator)")
    p.add_argument("--marathon", action="store_true",
                   help="long-mission preset from pace_study.py: cruise 0.8 and the real-rover "
                        "steering, also in the simulator; measure range at this cruise first")
    p.add_argument("--report-radius", type=float, default=10.0,
                   help="report a checkpoint from this many metres (server tolerance is 15)")
    p.add_argument("--gps-lag", type=float, default=0.0,
                   help="seconds the GPS runs behind the rover (FrodoBots-2K: about 1.5); "
                        "each fix is moved forward by the driving commanded since, assuming "
                        "0.79 m/s at full linear and commands 0.8 s late (0 = off)")
    p.add_argument("--dead-reckon", dest="dead_reckon", action="store_true", default=None,
                   help="carry the position from the last GPS fix by the wheel RPMs along "
                        "the compass-corrected heading and drive on through GPS dropouts of "
                        "up to 30 s; used once straight stretches have checked the wheels "
                        "against the GPS, and steer by it whenever it can (default: on for a "
                        "real rover, but steered by only through GPS gaps as --dead-reckon-gaps; "
                        "off in the simulator)")
    p.add_argument("--no-dead-reckon", dest="dead_reckon", action="store_false",
                   help="steer on the smoothed GPS fixes alone; the rover stops while the GPS "
                        "is out (the real-rover default in v0.14.0)")
    p.add_argument("--dead-reckon-gaps", action="store_true",
                   help="dead reckoning as --dead-reckon, but steered by only while the GPS "
                        "has no fresh fix, and by the smoothed GPS otherwise (the default on a "
                        "real rover since v0.15.0: through simulated GPS outages it was faster "
                        "on every course and slower on none, pace_i.py); since v0.16.0 the "
                        "wheels carry the position up to 120 s after the last fix, not 30 s "
                        "(pace_k.py)")
    p.add_argument("--mps-per-rpm", type=float, default=None,
                   help="with --dead-reckon, metres per second per wheel RPM to start from "
                        "(default: the Earth Rover Mini+'s 95 mm wheels, 0.00497); it is "
                        "learned while driving")
    p.add_argument("--smooth-heading", dest="smooth_heading", action="store_true",
                   default=None,
                   help="smooth the compass over its readings, turning the estimate by the "
                        "angular commanded since each one (pace_c.py to pace_f.py: on a "
                        "simulated Mini+ it kept the compass bias learned under noise and "
                        "was slower in no group); the turn rate comes from --calibration if "
                        "it has one, otherwise 48 deg/s per unit of angular (default: on for "
                        "a real rover, off in the simulator)")
    p.add_argument("--no-smooth-heading", dest="smooth_heading", action="store_false",
                   help="steer on each compass reading as it comes")
    p.add_argument("--telemetry-timeout", type=float, default=TELEMETRY_TIMEOUT_S,
                   help="stop the rover while no new telemetry has come in for this many "
                        "seconds: the /data timestamp stays the same, or GET /status gives a "
                        "higher telemetry_age_s (0 = off)")
    p.add_argument("--tip-angle", type=float, default=TIP_ANGLE_DEG,
                   help="stop the rover while its accelerometer shows gravity more than this "
                        "many degrees from where it pointed when the mission began, i.e. it "
                        "has tipped over (0 = off)")
    p.add_argument("--osm", help="plan each leg on this saved Overpass JSON "
                                 "(see: python route_planner.py fetch)")
    p.add_argument("--fetch-osm", action="store_true",
                   help="plan each leg on OpenStreetMap paths fetched from Overpass as needed")
    p.add_argument("--check-route", action="store_true",
                   help="don't drive: plan every remaining leg from the rover's position "
                        "(needs --osm or --fetch-osm) and print a summary")
    p.add_argument("--route-out", help="with --check-route, also write the legs as GeoJSON here")
    p.add_argument("--calibrate", action="store_true",
                   help="don't run the mission: spin in place, drive two short straights and "
                        "work out which way orientation and angular run (the rover moves "
                        "about 20 m; needs open ground)")
    p.add_argument("--calibration-out", help="with --calibrate, save a successful result here")
    p.add_argument("--calibration", help="drive with the conventions saved by "
                                         "--calibrate --calibration-out (without it, a real "
                                         "rover is driven with a positive angular turning left)")
    p.add_argument("--vision", action="store_true",
                   help="steer around obstacles seen by the front camera (a real rover needs "
                        "Pillow: pip install pillow). Experimental: a real rover's camera is "
                        "read with free_space.REAL_ROVER, which on recorded FrodoBots-2K "
                        "frames still saw a phantom obstacle on about 1 in 12 clear paths, "
                        "and how many real obstacles it misses is not measured yet")
    p.add_argument("--vision-plain", action="store_true",
                   help="with --vision on a real rover, use the VisionGuard defaults instead "
                        "of free_space.REAL_ROVER (they see far more phantom obstacles)")
    p.add_argument("--camera-fov", type=float, default=90.0,
                   help="front camera horizontal field of view, degrees")
    p.add_argument("--camera-height", type=float, default=0.35,
                   help="front camera height above the ground, metres")
    p.add_argument("--camera-pitch", type=float, default=5.0,
                   help="front camera downward tilt, degrees")
    p.add_argument("--timeout", type=float, default=3600.0, help="give up after this many seconds")
    p.add_argument("--log", help="append a JSON-lines log of the run to this file")
    p.add_argument("--version", action="version", version=__version__)
    args = p.parse_args(argv)
    if args.dead_reckon_gaps:
        if args.dead_reckon is False:
            p.error("--dead-reckon-gaps and --no-dead-reckon don't go together")
        args.dead_reckon = True
    if args.dead_reckon and args.gps_lag > 0:
        p.error("--dead-reckon and --gps-lag don't go together")
    asked = args.dead_reckon
    args.dead_reckon = use_dead_reckoning(args.dead_reckon, args.simulate, args.gps_lag)
    args.dead_reckon_gaps = use_dead_reckon_gaps(args.dead_reckon_gaps, asked,
                                                 args.dead_reckon)
    args.smooth_heading = use_smooth_heading(args.smooth_heading, args.simulate)

    if args.list_missions:
        if args.simulate:
            p.error("--list-missions needs a real SDK server")
        missions = SdkClient(args.sdk).missions()
        print(json.dumps({"ok": missions is not None, "missions": missions or []}, indent=2))
        return 0 if missions is not None else 1

    planner = None
    if args.osm or args.fetch_osm:
        import route_planner
        osm = None
        if args.osm:
            with open(args.osm, encoding="utf-8") as f:
                osm = json.load(f)
        planner = route_planner.OsmPlanner(osm=osm, fetch=args.fetch_osm)
    if args.check_route and planner is None:
        p.error("--check-route needs --osm or --fetch-osm")

    conventions = None
    saved = None
    if args.calibration:
        with open(args.calibration, encoding="utf-8") as f:
            saved = json.load(f)
        if not isinstance(saved, dict) or not saved.get("ok"):
            p.error("%s is not a successful calibration" % args.calibration)
        conventions = Conventions.from_dict(saved)
    elif not args.simulate:
        conventions = rover_conventions()

    camera = None
    if args.vision and not (args.check_route or args.calibrate):
        import free_space
        if not args.simulate:
            try:
                import PIL  # noqa: F401
            except ImportError:
                print("--vision on a real rover needs Pillow: pip install pillow", file=sys.stderr)
                return 2
        camera = free_space.Camera(hfov_deg=args.camera_fov, height_m=args.camera_height,
                                   pitch_deg=args.camera_pitch)

    log_file = open(args.log, "a", encoding="utf-8") if args.log else None

    def log(record):
        if log_file:
            log_file.write(json.dumps(record) + "\n")

    try:
        steering = make_steering(args.simulate, args.cruise, args.max_angular, args.turn_in_place,
                                 marathon=args.marathon)
        if args.simulate:
            sim_kw = {}
            if args.sim_quirks:
                sim_kw.update(SIM_QUIRKS)
            if args.sim_real:
                sim_kw.update(SIM_REAL)
            if args.dead_reckon:
                import dead_reckon
                sim_kw["wheel_mps_per_rpm"] = dead_reckon.MINI_PLUS_MPS_PER_RPM
            rover = SimRover(DEMO_MISSION, seed=args.seed,
                             obstacles=DEMO_OBSTACLES if args.obstacles else (), **sim_kw)
            clock, sleep = rover.clock, rover.sleep
            source = (lambda: rover.camera_frame(camera)) if camera else None
        else:
            rover = SdkClient(args.sdk)
            clock, sleep = time.monotonic, time.sleep
            source = SdkCamera(rover, camera) if camera else None
        if args.check_route:
            result, legs = check_route(rover, planner, clock=clock, sleep=sleep)
            if args.route_out and legs:
                import route_planner
                with open(args.route_out, "w", encoding="utf-8") as f:
                    json.dump(route_planner.legs_geojson(legs), f)
        elif args.calibrate:
            import calibrate
            if not args.simulate:
                print("calibrating: the rover spins in place for 30 to 90 s (until it has "
                      "turned a whole circle), then drives straight for 20 s, turns about "
                      "90 degrees and drives 20 s more", file=sys.stderr)
            result = calibrate.calibrate(rover, clock=clock, sleep=sleep)
            if args.calibration_out and result["ok"]:
                with open(args.calibration_out, "w", encoding="utf-8") as f:
                    json.dump(result, f, indent=2)
        else:
            vision = (make_vision(source, camera, args.simulate, args.vision_plain)
                      if camera else None)
            reckoner = None
            if args.dead_reckon:
                import dead_reckon
                dr_kw = dict(DEAD_RECKON)
                if args.dead_reckon_gaps:
                    dr_kw["max_s"] = BRIDGE_MAX_S
                if args.mps_per_rpm is not None:
                    dr_kw["mps_per_rpm"] = args.mps_per_rpm
                reckoner = dead_reckon.DeadReckoner(**dr_kw)
            pilot = Pilot(rover, clock=clock, sleep=sleep, steering=steering,
                          report_radius_m=args.report_radius, planner=planner, vision=vision,
                          conventions=conventions, gps_lag_s=args.gps_lag,
                          telemetry_timeout_s=args.telemetry_timeout,
                          tip_angle_deg=args.tip_angle, dead_reckon=reckoner, log=log,
                          smooth_heading=make_smoother(saved) if args.smooth_heading else None,
                          dead_reckon_gaps=args.dead_reckon_gaps)
            if not args.simulate:
                pilot.heading = make_heading(conventions)
                pilot.path_lookahead_m = PATH_LOOKAHEAD_M
            result = pilot.run(start=not args.no_start, timeout_s=args.timeout)
            if args.simulate and args.obstacles:
                result["sim_contacts"] = rover.contacts
    except KeyboardInterrupt:
        print("interrupted; stop sent to the rover", file=sys.stderr)
        return 130
    finally:
        if log_file:
            log_file.close()
    print(json.dumps(result, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
