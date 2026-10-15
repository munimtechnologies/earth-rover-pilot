#!/usr/bin/env python3
"""free_space: a front-camera check that keeps an Earth Rover off obstacles.

Each camera frame is shrunk to a small RGB grid (64 x 36 by default). The
ground just in front of the rover gives a colour model of the surface being
driven on. Every image column is scanned upward from the bottom until it stops
looking like that surface, and a flat-ground camera model turns that row into
a point (metres right, metres forward) on the ground. From those points the
guard works out how far the rover could drive in each direction without its
corridor touching anything it saw. Then it either leaves the pilot's heading
alone, bends it to the nearest clear direction, slows down, or turns in place
when nothing ahead is clear.

It sees colour, not depth. An obstacle the same colour as the ground (a grey
wall on grey pavement) is missed, and a change of surface (grass beside the
path, a painted line, a hard shadow edge) can read as an obstacle. On 493
recorded FrodoBots-2K front-camera frames (frodo_frames.py 0.2.0,
FINDINGS-frodobots-2k.md) the default settings saw an obstacle within 1.2 m
on 36% of the frames after which the human driver went on at least 2 m
straight: tree shadows, glare and the rover's own body at the bottom of the
frame. REAL_ROVER (leave out the body rows, accept deeper shadows and a wider
colour spread, and need four non-ground rows in a row) brought that to 8%.
How many real obstacles either setting misses is not measured. It is a cheap
first layer, meant to be replaced or backed by a learned model.

Standard library only. Decoding the SDK's JPEG frames needs Pillow
(decode_frame); the rest, including the simulator renderer, does not.
By MV2 of Munim, Inc.; written with AI agents. Apache-2.0.
"""

from __future__ import annotations

import io
import math
import random

__version__ = "0.5.0"

GROUND_GREY = (128, 128, 128)
HEDGE_GREEN = (60, 120, 50)
SKY_BLUE = (170, 200, 235)

# VisionGuard settings for a real Earth Rover's front camera. Of the eight
# settings frodo_frames.py ran on 493 FrodoBots-2K frames, this one saw the
# fewest phantom obstacles: a "stop" (under 1.2 m clear) on 9 of 110 frames
# after which the driver went at least 2 m straight (8%, 95% CI 4-15%; the
# defaults 36%, 27-45%) and a "swerve" (under 5 m) on 2 of 28 frames after
# which the driver went 5.5 m straight (7%, 2-23%; the defaults 79%, 61-90%).
# skip_rows leaves out the rover's body; lum_lo/lum_hi accept ground from 0.2
# to 2.5 times the patch brightness (shadows, glare); chroma_tol/max_tol allow
# a wider colour spread; gap needs four non-ground rows to call an obstacle.
REAL_ROVER = {"skip_rows": 3, "gap": 4,
              "scan_kw": {"lum_lo": 0.2, "lum_hi": 2.5, "chroma_tol": 0.05, "max_tol": 0.12}}


class Frame:
    """An RGB image: `pixels` holds width*height (r, g, b) tuples, row by row from the top."""

    __slots__ = ("width", "height", "pixels")

    def __init__(self, width, height, pixels):
        if len(pixels) != width * height:
            raise ValueError("expected %d pixels, got %d" % (width * height, len(pixels)))
        self.width = width
        self.height = height
        self.pixels = pixels

    def at(self, u, v):
        return self.pixels[v * self.width + u]


def decode_frame(data, width, height):
    """A Frame from JPEG/PNG/WebP bytes, shrunk to width x height. Needs Pillow."""
    from PIL import Image  # optional: only needed for real camera frames

    with Image.open(io.BytesIO(data)) as im:
        raw = im.convert("RGB").resize((width, height), Image.BOX).tobytes()
    return Frame(width, height, [tuple(raw[i:i + 3]) for i in range(0, len(raw), 3)])


# --- camera geometry ------------------------------------------------------

class Camera:
    """A pinhole camera `height_m` above flat ground, tilted down by `pitch_deg`.

    Rover frame: x is metres to the right, y metres forward, z metres up.
    Bearings are degrees clockwise from straight ahead, like compass headings.
    The defaults are guesses for the Earth Rover's front camera; measure them.
    """

    def __init__(self, width=64, height=36, hfov_deg=90.0, height_m=0.35, pitch_deg=5.0):
        self.width = width
        self.height = height
        self.hfov_deg = hfov_deg
        self.height_m = height_m
        self.pitch_deg = pitch_deg
        self.f = (width / 2.0) / math.tan(math.radians(hfov_deg) / 2.0)
        self._sin_p = math.sin(math.radians(pitch_deg))
        self._cos_p = math.cos(math.radians(pitch_deg))
        self.rays = [[self._ray(u, v) for v in range(height)] for u in range(width)]
        self.ground = [[self._ground(*self.rays[u][v]) for v in range(height)]
                       for u in range(width)]

    def _ray(self, u, v):
        a = (u + 0.5 - self.width / 2.0) / self.f
        b = (v + 0.5 - self.height / 2.0) / self.f
        return a, self._cos_p - b * self._sin_p, -self._sin_p - b * self._cos_p

    def _ground(self, x, y, z):
        if z >= -1e-9:
            return None  # at or above the horizon
        s = self.height_m / -z
        return x * s, y * s

    def ray(self, u, v):
        """(x, y, z) direction of the ray through the centre of pixel (u, v)."""
        return self.rays[u][v]

    def ground_point(self, u, v):
        """(x, y) metres where pixel (u, v) meets flat ground, or None above the horizon."""
        return self.ground[u][v]


# --- ground colour --------------------------------------------------------

def _features(rgb):
    r, g, b = rgb
    s = r + g + b + 1.0
    return r / s, g / s, s / 3.0


class GroundModel:
    """The colour of the surface being driven on: chromaticity, spread and brightness."""

    def __init__(self, cr, cg, lum, spread=0.0):
        self.cr = cr
        self.cg = cg
        self.lum = lum
        self.spread = spread

    @classmethod
    def fit(cls, pixels):
        feats = [_features(p) for p in pixels]
        n = float(len(feats))
        cr = sum(f[0] for f in feats) / n
        cg = sum(f[1] for f in feats) / n
        lum = sum(f[2] for f in feats) / n
        spread = math.sqrt(sum((f[0] - cr) ** 2 + (f[1] - cg) ** 2 for f in feats) / n)
        return cls(cr, cg, lum, spread)

    def matcher(self, chroma_tol=0.035, max_tol=0.08, lum_lo=0.45, lum_hi=1.8):
        """A function rgb -> True if the pixel looks like this ground (shadows allowed)."""
        tol = min(max_tol, chroma_tol + 3.0 * self.spread)
        cr, cg, lo, hi = self.cr, self.cg, lum_lo * self.lum, lum_hi * self.lum

        def matches(rgb):
            r, g, l = _features(rgb)
            return abs(r - cr) <= tol and abs(g - cg) <= tol and lo <= l <= hi
        return matches

    def close_to(self, other, chroma_tol=0.035, max_tol=0.08):
        tol = min(max_tol, chroma_tol + 3.0 * max(self.spread, other.spread))
        ratio = other.lum / self.lum
        return (abs(self.cr - other.cr) <= tol and abs(self.cg - other.cg) <= tol
                and 0.6 <= ratio <= 1.6)

    def blend(self, other, alpha):
        return GroundModel(self.cr + alpha * (other.cr - self.cr),
                           self.cg + alpha * (other.cg - self.cg),
                           self.lum + alpha * (other.lum - self.lum),
                           self.spread + alpha * (other.spread - self.spread))


def ground_patch(frame, rows=3, width_frac=0.4, skip_rows=0):
    """Pixels of the bottom-centre band: the ground the rover is about to drive on.

    `skip_rows` bottom rows are left out first (where the rover's own body shows).
    """
    half = max(1, int(frame.width * width_frac / 2))
    mid = frame.width // 2
    bottom = frame.height - skip_rows
    return [frame.at(u, v) for v in range(bottom - rows, bottom)
            for u in range(mid - half, mid + half)]


# --- free space -----------------------------------------------------------

def scan(frame, camera, model, max_range_m=8.0, gap=2, skip_rows=0, **tol):
    """Obstacle points seen in `frame`: one (x, y) per blocked column, in metres.

    Each column is followed up from the bottom while it looks like ground. A
    column that reaches `max_range_m` or the horizon is clear. Where `gap`
    rows in a row stop looking like ground, the last ground pixel below them
    is taken as the obstacle's foot (slightly nearer than the real foot).
    The bottom `skip_rows` rows are not looked at.
    """
    matches = model.matcher(**tol)
    first = frame.height - 1 - skip_rows
    points = []
    for u in range(frame.width):
        ground = camera.ground[u]
        last, misses, hit = None, 0, False
        for v in range(first, -1, -1):
            gp = ground[v]
            if gp is None:
                break
            if matches(frame.at(u, v)):
                misses, last = 0, gp
                if math.hypot(gp[0], gp[1]) >= max_range_m:
                    break
            else:
                misses += 1
                if misses >= gap:
                    hit = True
                    break
        if hit:
            points.append(last if last is not None else ground[first])
    return points


def clearance(points, bearing_deg, half_width_m=0.4, max_range_m=8.0):
    """How far the rover can drive along `bearing_deg` before its corridor meets a point."""
    th = math.radians(bearing_deg)
    dx, dy = math.sin(th), math.cos(th)
    best = max_range_m
    for x, y in points:
        along = x * dx + y * dy
        if along <= 0.0 or along >= best:
            continue
        if abs(x * dy - y * dx) <= half_width_m:
            best = along
    return best


class VisionGuard:
    """Bends the pilot's heading error away from what the front camera sees.

    `source()` returns a Frame of the camera's size, or None when no frame is
    available. It is called at most every `period_s`; a scan older than
    `stale_s` is not trusted, and the pilot is slowed to `blind_scale` instead.
    `skip_rows`, `gap` and `scan_kw` (colour tolerances for GroundModel.matcher)
    are passed to the ground patch and the scan; REAL_ROVER holds the ones
    measured for a real rover's camera.
    """

    def __init__(self, source, camera=None, period_s=0.2, stale_s=1.0, half_width_m=0.4,
                 safe_m=5.0, stop_m=1.2, max_range_m=8.0, step_deg=5.0, edge_deg=5.0,
                 commit_s=2.0, switch_penalty_deg=30.0, turn_s=1.5, blind_scale=0.5,
                 refit_after=15, model_alpha=0.2, skip_rows=0, gap=2, scan_kw=None):
        self.source = source
        self.camera = camera or Camera()
        self.period_s = period_s
        self.stale_s = stale_s
        self.half_width_m = half_width_m
        self.safe_m = safe_m
        self.stop_m = stop_m
        self.max_range_m = max_range_m
        self.edge_deg = edge_deg
        self.commit_s = commit_s
        self.switch_penalty_deg = switch_penalty_deg
        self.turn_s = turn_s
        self.blind_scale = blind_scale
        self.refit_after = refit_after
        self.model_alpha = model_alpha
        self.skip_rows = skip_rows
        self.gap = gap
        self.scan_kw = dict(scan_kw or {})
        half = self.camera.hfov_deg / 2.0 - edge_deg
        n = int(math.floor(half / step_deg))
        self.half_view_deg = n * step_deg
        self.candidates = [k * step_deg for k in range(-n, n + 1)]
        self.model = None
        self.points = None
        self.clear_ahead = None
        self.frames = 0
        self.failures = 0
        self.avoidances = 0
        self.stops = 0
        self.refits = 0
        self._odd = 0
        self._fetch_t = None
        self._scan_t = None
        self._side = 0
        self._side_t = None
        self._turn_until = None

    def stats(self):
        return {"frames": self.frames, "failures": self.failures,
                "avoidances": self.avoidances, "stops": self.stops, "refits": self.refits}

    def _update_model(self, frame):
        patch = GroundModel.fit(ground_patch(frame, skip_rows=self.skip_rows))
        if self.model is None:
            self.model = patch
        elif self.model.close_to(patch):
            self.model = self.model.blend(patch, self.model_alpha)
            self._odd = 0
        else:
            # The ground ahead looks different. Either something is in front of
            # the rover or the surface changed; only a lasting change is learned.
            self._odd += 1
            if self._odd >= self.refit_after:
                self.model = patch
                self.refits += 1
                self._odd = 0

    def _update(self, t):
        if self._fetch_t is not None and t - self._fetch_t < self.period_s:
            return
        self._fetch_t = t
        try:
            frame = self.source()
        except Exception:  # a camera problem must not stop the pilot; it drives slower instead
            frame = None
        if frame is not None and (frame.width, frame.height) != (self.camera.width,
                                                                 self.camera.height):
            frame = None
        if frame is None:
            self.failures += 1
        else:
            self.frames += 1
            self._update_model(frame)
            self.points = scan(frame, self.camera, self.model, max_range_m=self.max_range_m,
                               gap=self.gap, skip_rows=self.skip_rows, **self.scan_kw)
            self._scan_t = t
        if self._scan_t is not None and t - self._scan_t > self.stale_s:
            self.points = None

    def _clear(self, bearing):
        return clearance(self.points, bearing, self.half_width_m, self.max_range_m)

    def advise(self, t, error_deg, distance_m=math.inf):
        """(error_deg, speed_scale) to steer by instead of the pilot's own heading error."""
        self._update(t)
        if self._turn_until is not None and t < self._turn_until:
            return self._side * 90.0, 0.0
        if self.points is None:
            self.clear_ahead = None
            return error_deg, self.blind_scale
        need = min(self.safe_m, max(self.stop_m, distance_m))
        want = max(-self.half_view_deg, min(self.half_view_deg, error_deg))
        self.clear_ahead = self._clear(want)
        if self.clear_ahead >= need:
            return error_deg, 1.0
        committed = self._side_t is not None and t - self._side_t < self.commit_s
        clear = {th: self._clear(th) for th in self.candidates}
        best, best_cost = None, math.inf
        for th, c in clear.items():
            if c < need:
                continue
            cost = abs(th - want)
            side = 1 if th > want else -1
            if committed and self._side and side != self._side:
                cost += self.switch_penalty_deg
            if cost < best_cost:
                best, best_cost = th, cost
        if best is None:
            best = max(clear, key=lambda th: (clear[th], -abs(th - want)))
            if clear[best] < self.stop_m:
                if not committed or not self._side:
                    right = sum(c for th, c in clear.items() if th > 0)
                    left = sum(c for th, c in clear.items() if th < 0)
                    self._side = 1 if right > left else -1
                self._side_t = t
                self._turn_until = t + self.turn_s
                self.stops += 1
                return self._side * 90.0, 0.0
        self._side = 1 if best > want else -1
        self._side_t = t
        self.avoidances += 1
        return best, max(0.3, min(1.0, clear[best] / need))


# --- a synthetic camera for the simulator ---------------------------------

def _ray_circle(x, y, cx, cy, r):
    """Smallest s > 0 where s*(x, y) is on the circle, or None."""
    a = x * x + y * y
    b = -2.0 * (x * cx + y * cy)
    c = cx * cx + cy * cy - r * r
    disc = b * b - 4.0 * a * c
    if disc < 0.0 or a == 0.0:
        return None
    s = (-b - math.sqrt(disc)) / (2.0 * a)
    return s if s > 0.0 else None


def make_noise(seed=0, amplitude=6, n=4099):
    """A table of per-channel colour offsets the renderer cycles through."""
    rng = random.Random(seed)
    return [(rng.randint(-amplitude, amplitude), rng.randint(-amplitude, amplitude),
             rng.randint(-amplitude, amplitude)) for _ in range(n)]


def render(camera, obstacles, ground=GROUND_GREY, sky=SKY_BLUE, noise=None, offset=0,
           draw_range_m=20.0):
    """A synthetic frame: flat ground of one colour and upright cylinders on it.

    `obstacles` are (x, y, radius, height, (r, g, b)) in the rover frame.
    Obstacles farther than `draw_range_m` are left out.
    """
    near = [o for o in obstacles if o[1] > -o[2] and math.hypot(o[0], o[1]) - o[2] < draw_range_m]
    h = camera.height_m
    pixels = []
    k = offset
    for v in range(camera.height):
        for u in range(camera.width):
            x, y, z = camera.rays[u][v]
            if z < 0.0:
                colour, dist = ground, h / -z
            else:
                colour, dist = sky, math.inf
            for ox, oy, r, oh, col in near:
                s = _ray_circle(x, y, ox, oy, r)
                if s is not None and s < dist and 0.0 <= h + z * s <= oh:
                    colour, dist = col, s
            if noise:
                n = noise[k % len(noise)]
                k += 1
                colour = (min(255, max(0, colour[0] + n[0])), min(255, max(0, colour[1] + n[1])),
                          min(255, max(0, colour[2] + n[2])))
            pixels.append(colour)
    return Frame(camera.width, camera.height, pixels)
