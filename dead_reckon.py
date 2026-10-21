#!/usr/bin/env python3
"""dead_reckon: carries an Earth Rover's position between GPS fixes with its wheels.

On 449 FrodoBots-2K rides (frodo_odometry.py, FINDINGS-frodobots-2k.md) the
best way to predict the next GPS fix was wheel distance along the last GPS
course: its median miss was 24% smaller than the GPS's own velocity's at
10 s and 35% at 30 s, and turning by the gyroscope made it worse.
DeadReckoner does that inside the pilot:

- Wheel speed is the mean of the four /data `rpms` columns times metres per
  RPM. The default is the Earth Rover Mini+'s 95 mm wheels (SDK README); the
  Earth Rover Zeros of FrodoBots-2K measured 0.00668. The value is learned
  while driving: on straight stretches of about 20 s the distance between two
  GPS fixes is compared with what the wheels drove over the same time. Until
  `trust_after` such stretches have agreed with the prior (within
  `scale_range`), there is no estimate, so wheels that read zero, or whose
  columns cancel out, are never used.
- The course is the direction from the fix about 3 s before to the newest
  one. When the compass says the rover has turned more than `turn_deg` since,
  the course is turned by as much; before there is a course, the pilot's
  heading is used. With `use_course` off, the pilot's heading is always used.
- With `use_course` off and `course_hold_s` above 0 (default 0: off), a fix
  that brings a fresh course is followed along that course for
  `course_hold_s` from when the rover was there; right after a fix the GPS
  course beat the live compass on FrodoBots-2K (frodo_blend.py). Then the
  heading takes over; with `fade`, the difference at the switch fades out
  over another `course_hold_s`. position() follows a changing direction in
  steps between calls, so the pilot calls it every tick.
- A fix shows where the rover was `gps_lag_s` earlier (1.5 s on the recorded
  rides), so it is compared with the estimate for that time, and the estimate
  is moved `gain` of the way to it (1 = start again from every fix). A fix
  more than `reset_m` away is taken whole.
- With no fix for `max_s`, there is no estimate.

Rows of `rpms` carry the rover's own timestamps; the newest row of a reading
is taken as seen when the reading is, and the others that much earlier. A
reading served again from the SDK's cache adds nothing. Each wheel sample
holds for up to `hold_s`, then the wheels count as stopped.

Standard library only. By MV2 of Munim, Inc.; written with AI agents. Apache-2.0.
"""

from __future__ import annotations

import bisect
import collections
import math

__version__ = "0.2.0"

M_PER_DEG = 6371000.0 * math.pi / 180.0
# Metres per second per wheel RPM: the wheel's circumference over 60 s.
MINI_PLUS_MPS_PER_RPM = math.pi * 0.095 / 60.0  # 95 mm wheels, about 0.00497
ZERO_MPS_PER_RPM = 0.00668  # measured on the FrodoBots-2K rides (Earth Rover Zero)


def wrap180(angle_deg):
    """Angle in [-180, 180)."""
    return (angle_deg + 180.0) % 360.0 - 180.0


class DeadReckoner:
    """Wheel distance along the last GPS course, from the last fix to now.

    Feed it every tick with wheels() and update(); position() gives the
    estimate. stats() says what it learned.
    """

    def __init__(self, mps_per_rpm=MINI_PLUS_MPS_PER_RPM, gps_lag_s=1.5, gain=1.0,
                 learn_scale=True, trust_after=2, max_s=30.0, hold_s=3.0,
                 use_course=True, course_s=3.0, course_tol_s=1.5, min_course_m=1.0,
                 turn_deg=30.0, scale_s=20.0, scale_tol_s=2.0, scale_min_m=5.0,
                 straight_deg=15.0, scale_range=(0.5, 2.0), reset_m=15.0,
                 course_hold_s=0.0, fade=True):
        self.prior = float(mps_per_rpm)
        self.mps_per_rpm = self.prior
        self.gps_lag_s = gps_lag_s
        self.gain = gain
        self.learn_scale = learn_scale
        self.trust_after = trust_after
        self.max_s = max_s
        self.hold_s = hold_s
        self.use_course = use_course
        self.course_s = course_s
        self.course_tol_s = course_tol_s
        self.min_course_m = min_course_m
        self.turn_deg = turn_deg
        self.scale_s = scale_s
        self.scale_tol_s = scale_tol_s
        self.scale_min_m = scale_min_m
        self.straight_deg = straight_deg
        self.scale_range = scale_range
        self.reset_m = reset_m
        self.course_hold_s = float(course_hold_s)
        self.fade = fade
        self.keep_s = max_s + gps_lag_s + scale_s + scale_tol_s + 5.0
        self.fixes = 0
        self.resets = 0
        self.scale_samples = 0
        self.scale_rejects = 0
        self._num = self._den = 0.0
        self._scale_last_t = None
        self._origin = None
        # Wheel samples: time, mean RPM, and RPM-seconds from the first kept sample.
        self._st, self._sr, self._sc = [], [], []
        self._row_ts = None
        self._fix_hist = collections.deque()  # (seen t, east, north) of each new fix
        self._compass = collections.deque()   # (t, compass)
        self._anchor = None  # (t, east, north): the estimate at time t
        self._dir = None     # course the estimate moves on from the anchor
        self._course = None  # (course_deg, compass when it was measured)
        self._hold = None    # (time the hold ends, the fresh course held until then)
        self._shift = None   # heading's shift onto the held course at the switch
        self._heading = None
        self._fix_t = None

    # --- wheels -----------------------------------------------------------

    def wheels(self, t, rows):
        """Feed one /data reading's `rpms` rows ([rpm x 4, timestamp]), seen at t."""
        if not isinstance(rows, (list, tuple)):
            return
        stamped, plain = [], []
        for row in rows:
            if not isinstance(row, (list, tuple)) or len(row) < 4:
                continue
            try:
                vals = [float(v) for v in row[:4]]
            except (TypeError, ValueError):
                continue
            if not all(math.isfinite(v) for v in vals):
                continue
            ts = None
            if len(row) >= 5:
                try:
                    ts = float(row[4])
                except (TypeError, ValueError):
                    ts = None
                if ts is not None and not math.isfinite(ts):
                    ts = None
            (plain if ts is None else stamped).append((ts, sum(vals) / 4.0))
        if stamped:
            stamped.sort()
            if self._row_ts is not None and stamped[-1][0] < self._row_ts - 60.0:
                self._row_ts = None  # the rover's clock started again
            new = [r for r in stamped if self._row_ts is None or r[0] > self._row_ts]
            if not new:
                return  # the same reading again
            newest = new[-1][0]
            self._row_ts = newest
            for ts, rpm in new:
                self._add(t - (newest - ts), rpm)
        elif plain:
            self._add(t, sum(r for _, r in plain) / len(plain))

    def _add(self, t, rpm):
        if self._st:
            t = max(t, self._st[-1])
            s = self._st[-1]
            cum = self._sc[-1] + self._sr[-1] * (min(t, s + self.hold_s) - s)
        else:
            cum = 0.0
        self._st.append(t)
        self._sr.append(rpm)
        self._sc.append(cum)

    def _rpm_s(self, t):
        """RPM-seconds the wheels turned from the first kept sample up to time t."""
        i = bisect.bisect_right(self._st, t) - 1
        if i < 0:  # before the first kept sample: no driving counted
            return self._sc[0] if self._sc else 0.0
        s = self._st[i]
        return self._sc[i] + self._sr[i] * (min(t, s + self.hold_s) - s)

    def distance(self, a, b):
        """Metres the wheels drove from time a to time b (negative if b is before a)."""
        return (self._rpm_s(b) - self._rpm_s(a)) * self.mps_per_rpm

    # --- GPS and compass --------------------------------------------------

    def update(self, t, new_fix, compass=None, heading=None):
        """Feed one tick: the new GPS fix (lat, lon) seen at t, or None; the compass
        reading (to notice turns) and the pilot's heading estimate, each None if unknown."""
        self._heading = heading
        if compass is not None:
            self._compass.append((t, compass))
        self._prune(t)
        if new_fix is None:
            return
        self.fixes += 1
        if self._origin is None:
            self._origin = (float(new_fix[0]), float(new_fix[1]))
        e, n = self._en(new_fix[0], new_fix[1])
        self._fix_hist.append((t, e, n))
        self._learn_scale(t, e, n)
        course = self._measure_course(t, e, n)
        if course is not None or self._course is None or self._course[1] is None:
            self._course = course
        tf = t - self.gps_lag_s  # when the rover was where this fix says
        if self._anchor is None:
            self._anchor = (tf, e, n)
        else:
            pe, pn = self._at(tf)
            de, dn = e - pe, n - pn
            g = self.gain
            if math.hypot(de, dn) > self.reset_m:
                g = 1.0
                self.resets += 1
            self._anchor = (tf, pe + g * de, pn + g * dn)
        self._hold = self._shift = None
        if self.course_hold_s > 0 and not self.use_course and course is not None:
            self._hold = (tf + self.course_hold_s, course[0])
        self._dir = self._direction(tf)
        self._fix_t = t

    def _prune(self, t):
        cut = t - self.keep_s
        while len(self._compass) > 1 and self._compass[0][0] < cut:
            self._compass.popleft()
        while len(self._fix_hist) > 1 and self._fix_hist[0][0] < cut:
            self._fix_hist.popleft()
        j = bisect.bisect_left(self._st, cut) - 1
        if j > 200:
            del self._st[:j], self._sr[:j], self._sc[:j]

    def _nearest_fix(self, target, tol):
        """The kept fix (before the newest) seen nearest to time target, if within tol."""
        best = None
        for k in range(len(self._fix_hist) - 1):
            f = self._fix_hist[k]
            if abs(f[0] - target) <= tol and (best is None or abs(f[0] - target) < abs(best[0] - target)):
                best = f
        return best

    def _compass_at(self, t, tol=2.0):
        best = None
        for s, c in self._compass:
            if abs(s - t) <= tol and (best is None or abs(s - t) < abs(best[0] - t)):
                best = (s, c)
        return None if best is None else best[1]

    def _measure_course(self, t, e, n):
        """(course, compass then) from the fix about course_s before to (e, n), or None."""
        p = self._nearest_fix(t - self.course_s, self.course_tol_s)
        if p is None or math.hypot(e - p[1], n - p[2]) < self.min_course_m:
            return None
        course = math.degrees(math.atan2(e - p[1], n - p[2])) % 360.0
        return course, self._compass_at((t + p[0]) / 2.0 - self.gps_lag_s)

    def _learn_scale(self, t, e, n):
        """Compare a straight ~scale_s stretch by GPS with the wheels over the same time."""
        if not self.learn_scale:
            return
        p = self._nearest_fix(t - self.scale_s, self.scale_tol_s)
        if p is None or (self._scale_last_t is not None and p[0] < self._scale_last_t):
            return
        a, b = p[0] - self.gps_lag_s, t - self.gps_lag_s
        rpm_s = self._rpm_s(b) - self._rpm_s(a)
        if rpm_s * self.prior < self.scale_min_m:
            return  # too short, or backwards
        seen = [c for s, c in self._compass if a <= s <= b]
        if len(seen) < 2 or any(abs(wrap180(c - seen[0])) > self.straight_deg for c in seen):
            return  # not straight, or no compass to tell
        self._scale_last_t = t
        ratio = math.hypot(e - p[1], n - p[2]) / rpm_s
        lo, hi = self.scale_range
        if not lo * self.prior <= ratio <= hi * self.prior:
            self.scale_rejects += 1
            return
        self._num += math.hypot(e - p[1], n - p[2])
        self._den += rpm_s
        self.scale_samples += 1
        self.mps_per_rpm = self._num / self._den

    # --- the estimate -----------------------------------------------------

    @property
    def trusted(self):
        return not self.learn_scale or self.scale_samples >= self.trust_after

    def _direction(self, t=None):
        if self.use_course and self._course is not None:
            course, then = self._course
            now = self._compass[-1][1] if self._compass else None
            if then is not None and now is not None:
                turn = wrap180(now - then)
                if abs(turn) > self.turn_deg:
                    return (course + turn) % 360.0
            return course
        if self._hold is not None and t is not None:
            until, course = self._hold
            if t < until:
                return course
            if self.fade and self._heading is not None:
                if self._shift is None:  # the first look after the switch
                    self._shift = wrap180(course - self._heading)
                f = 1.0 - (t - until) / self.course_hold_s
                if f > 0:
                    return (self._heading + f * self._shift) % 360.0
        return self._heading

    def _at(self, t):
        """(east, north) of the estimate at time t."""
        ta, e, n = self._anchor
        if self._dir is None:
            return e, n
        d = self.distance(ta, t)
        r = math.radians(self._dir)
        return e + d * math.sin(r), n + d * math.cos(r)

    def position(self, t):
        """(lat, lon) the rover is estimated to be at, at time t, or None while there
        is no estimate: no fix yet, none for max_s, or the wheels not yet trusted."""
        if self._anchor is None or self._fix_t is None or t - self._fix_t > self.max_s:
            return None
        if not self.trusted:
            return None
        if self._hold is not None and self._anchor[0] < self._hold[0] <= t:
            # The hold ended since the last look: follow the course up to the switch.
            e, n = self._at(self._hold[0])
            self._anchor = (self._hold[0], e, n)
            self._dir = self._direction(self._hold[0])
        d = self._direction(t)
        if d != self._dir:  # turned: carry on from here on the new course
            e, n = self._at(t)
            self._anchor, self._dir = (t, e, n), d
        return self._latlon(*self._at(t))

    def stats(self):
        return {"trusted": self.trusted, "mps_per_rpm": round(self.mps_per_rpm, 6),
                "prior_mps_per_rpm": round(self.prior, 6), "scale_samples": self.scale_samples,
                "scale_rejects": self.scale_rejects, "fixes": self.fixes, "resets": self.resets}

    # --- local frame ------------------------------------------------------

    def _en(self, lat, lon):
        lat0, lon0 = self._origin
        return ((float(lon) - lon0) * M_PER_DEG * math.cos(math.radians(lat0)),
                (float(lat) - lat0) * M_PER_DEG)

    def _latlon(self, e, n):
        lat0, lon0 = self._origin
        return lat0 + n / M_PER_DEG, lon0 + e / (M_PER_DEG * math.cos(math.radians(lat0)))
