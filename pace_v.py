#!/usr/bin/env python3
"""pace_v: a warm-up only after a stand, and blocks of many lengths, start and mid-route.

pace_u.py (studies/pace-u/GRADE.md) flew 5 s and 10 s warm-ups before the
stuck check judges. Both removed the false recovery move the shipped
Pilot._stuck makes about 9 s after nearly every start, but neither met its
pre-stated rule. trace_u.py (studies/pace-u/TRACE.md) found why:
  - a ~1 s stop with no fix (two GPS reports dropped in a row) clears the
    stuck history, and a warm-up after every clear starts again, so a
    blocked rover was caught 12 s late;
  - the GPS average needs about 6-7 s of real driving to move 1.5 m, so a
    verdict that falls in the first seconds after a block ends calls a free
    rover stuck; which variant pays depends on where its cycle meets the
    end of one fixed 30 s block.
The false alarm needs an average that has caught up with a STANDING rover.
pace_v.py flies a warm-up that comes only then: at the first check of a
mission and after a gap of STAND_S or more between checks with no recovery
move in it (a stop for a lost fix or stale telemetry, a hold at a
checkpoint). After a recovery move or a short stop the check judges as it
ships. Blocks are drawn per seed: 30-60 s long, at the start or starting
240-600 s into the mission. The seed-to-seed spread of the corner and
offset figures is measured on a second, disjoint seed set of the shipped
pilot, so the tolerances the rule uses come from it.

Variants (all v0.18.2's real-rover pilot as pace_u.py flies it):
  a0.3          GpsFilter and Pilot._stuck as they ship
  warm10        no stuck verdict until 10 s after the stuck history was
                last cleared (pace_u.py's warm10)
  warmstand10   no stuck verdict until 10 s after the first check or after
                a stand (as above); other clears leave a running warm-up as
                it is and add none
  a0.3:B        a0.3 on the second seed set, for the spread only
Profiles: pace_u.py's outage90, quiet90, quietdrift90 and quiet45, and
blockedstart and blockedmid (quiet90 with a block drawn per seed).

    python pace_v.py --out-dir out --first-seed 397 --seeds 24 --check-u studies/pace-u

With --check-u it first flies 8 of pace_u.py's missions again (three of
blocked30's through this module's own block, from 0 to 30 s) and compares
their times and recovery moves with pace_u.py's record. Simulated rovers
only, so the speeds are upper bounds. Standard library only.
By MV2 of Munim, Inc.; written with AI agents. Apache-2.0.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import math
import os
import random
import sys
import time

import dead_reckon as dr
import pace_d as pd
import pace_e as pe
import pace_f as pf
import pace_g as pg
import pace_h as ph
import pace_i as pi
import pace_j as pj
import pace_l as pl
import pace_n as pn
import pace_o as po
import pace_p as pp
import pace_q as pq
import pace_s as pz
import pace_study as ps
import pace_t as pt
import pace_u as pu
import rover_pilot as rp

__version__ = "0.1.0"

PROFILES = {
    "outage90": pt.PROFILES["outage90"],
    "quiet90": pt.PROFILES["quiet90"],
    "quietdrift90": pt.PROFILES["quietdrift90"],
    "quiet45": pt.PROFILES["quiet45"],
    "blockedstart": pt.PROFILES["quiet90"],
    "blockedmid": pt.PROFILES["quiet90"],
}
# The first is always flown.
BASE_PROFILE = next(iter(PROFILES))
# Profile -> ((first, last) start s, (shortest, longest) length s) of the
# block each seed draws: the rover can turn but not move inside it.
BLOCKS = {"blockedstart": ((0.0, 0.0), (30.0, 60.0)),
          "blockedmid": ((240.0, 600.0), (30.0, 60.0))}
BLOCKED = tuple(BLOCKS)
UNBLOCKED = tuple(p for p in PROFILES if p not in BLOCKS)
# (a, b): each variant on profile b against itself on profile a, paired by seed.
PROFILE_PAIRS = (("quiet90", "blockedstart"), ("quiet90", "blockedmid"))
WARMUP_S = 10.0
# A gap between stuck checks at least this long, with no recovery move in
# it, is a stand: the rover was stopped and the GPS average caught up with it.
STAND_S = 3.0
VARIANTS = {
    "a0.3": {"alpha": 0.3},
    "warm10": {"alpha": 0.3, "warmup_s": WARMUP_S, "warm": "always"},
    "warmstand10": {"alpha": 0.3, "warmup_s": WARMUP_S, "warm": "stand"},
    "a0.3:B": {"alpha": 0.3},
}
# The pilot as it ships; it is always flown.
BASE_VARIANT = next(iter(VARIANTS))
# The shipped pilot again on the second seed set: only the spread is read from it.
NOISE_VARIANT = "a0.3:B"
# (a, b): b against a, paired by seed per course.
PAIRS = (("a0.3", "warm10"), ("a0.3", "warmstand10"), ("warm10", "warmstand10"))
CRUISES = (0.8,)
# pace_u.py flew seeds 373-396; these start after them, and the second set after these.
FIRST_SEED = 397
FIRST_SEED_B = 421
# A blocked rover counts as caught by a recovery move within this many
# seconds of its block's start; a move within POST_S after the block ends
# was made by a rover that was free again.
CATCH_S = 30.0
POST_S = 10.0
# The tolerances the rule uses are the spread between the two seed sets of
# a0.3, rounded up to TOL_STEP_M, and never below these.
CORNER_TOL_MIN_M = 0.25
OFFSET_TOL_MIN_M = 0.5
TOL_STEP_M = 0.05
EARLY_S = pt.EARLY_S
SNAP_M = pz.SNAP_M
# --check-u: (pace_u.py's profile, variant, course, seed) -> (elapsed_s,
# recovery_t) in pace_u.py's record (studies/pace-u/runs-<profile>.jsonl):
# seed 388's late catch, two catches 2 s late, and three quiet missions.
CHECKED_U = {
    ("outage90", "a0.3", "boulevard", 373): (1757.6, [11.1]),
    ("outage90", "a0.3", "bayside", 387): (1427.6, []),
    ("quiet90", "a0.3", "boulevard", 373): (1755.6, [11.1]),
    ("quiet90", "warm10", "boulevard", 373): (1747.6, []),
    ("blocked30", "a0.3", "boulevard", 388): (1801.6, [9.1, 24.2]),
    ("blocked30", "warm10", "boulevard", 388): (1801.6, [31.0]),
    ("blocked30", "warm10", "blocks", 373): (1647.6, [21.1]),
    ("blocked30", "warm10", "boulevard", 374): (1827.6, [19.1]),
}
# pace_u.py's profiles as this module flies them: (profile, block).
AS_PACE_U = {"outage90": ("outage90", None), "quiet90": ("quiet90", None),
             "blocked30": ("quiet90", (0.0, 30.0))}
NO_STUCK = {"warmup_s": None, "warm": None, "recovery_t": None, "stands": None,
            "block": None, "block_outage": None, "first_outage_s": None}


def block_window(profile, seed):
    """[start, end] of the block this seed draws on `profile`, from a
    generator of its own (the rover's draws are unchanged); None if the
    profile has no block."""
    if profile not in BLOCKS:
        return None
    (lo, hi), (short, long_) = BLOCKS[profile]
    rng = random.Random("pace-v-%s-%d" % (profile, seed))
    start = round(rng.uniform(lo, hi), 1)
    return [start, round(start + rng.uniform(short, long_), 1)]


def outages(profile, seed):
    """The GPS outage windows a mission on `profile` draws, as OutageRover does."""
    p = PROFILES[profile]
    return pi.outage_windows(seed, float(p.get("outage_s", 0.0)), float(p.get("clear_s", 150.0)))


def overlaps(windows, a, b):
    """True if any (start, end) in `windows` overlaps [a, b)."""
    return any(s < b and e > a for s, e in windows)


@contextlib.contextmanager
def _known_profile(profile):
    """While inside, pace_l.fly knows the profile by name; a name it already
    knows is left as it is."""
    add = profile not in pl.PROFILES
    if add:
        pl.PROFILES[profile] = PROFILES[profile]
    try:
        yield
    finally:
        if add:
            del pl.PROFILES[profile]


@contextlib.contextmanager
def _blocking(window):
    """While inside, every simulated rover can turn but not move from
    window[0] until window[1] (sim time); with None, nothing changes."""
    if window is None:
        yield
        return
    start, end = window
    saved = rp.SimRover._step

    def _step(self):
        # SimRover._step moves the rover only if t >= blocked_until_s.
        self.blocked_until_s = end if start <= self.t < end else 0.0
        saved(self)

    rp.SimRover._step = _step
    try:
        yield
    finally:
        rp.SimRover._step = saved


@contextlib.contextmanager
def _warming(warmup_s, warm, times, stands):
    """While inside, every Pilot's stuck check gives no verdict until
    `warmup_s` after a warm-up began. With `warm` "always" one begins at
    every clear of the stuck history (pace_t._warming); with "stand" only
    at the first check and at a clear after a stand (a gap of STAND_S or
    more since the last check, with no recovery move in it), and a running
    warm-up is left as it is. With "never" there is none. The time of each
    verdict is appended to `times` and each stand's (last check, this check)
    to `stands`."""
    saved = rp.Pilot._stuck

    def _stuck(self, t, linear):
        h = self._history
        if not isinstance(h, pt.StuckHistory):
            h = self._history = pt.StuckHistory(h)
        last = getattr(self, "_last_check_t", None)
        recoveries = getattr(self, "recoveries", 0)
        stood = (last is not None and t - last >= STAND_S
                 and recoveries == self._last_check_recoveries)
        if stood:
            stands.append((last, t))
        self._last_check_t, self._last_check_recoveries = t, recoveries
        if h.cleared:
            h.cleared = False
            if warm == "always" or (warm == "stand" and (last is None or stood)):
                self._warm_from = t
        warm_from = getattr(self, "_warm_from", None)
        if warm_from is not None and t - warm_from < warmup_s:
            return False
        stuck = saved(self, t, linear)
        if stuck:
            times.append(t)
        return stuck

    rp.Pilot._stuck = _stuck
    try:
        yield
    finally:
        rp.Pilot._stuck = saved


def fly(course_name, seed, profile, variant, cruise, course=None, block="profile"):
    """One mission flown as pace_u.fly flies it, with the variant's warm-up
    and the profile's block (or `block`, [start, end] or None); the stuck
    record also gives every stand, the block, whether an outage overlapped
    its first CATCH_S and when the first outage began."""
    v = VARIANTS[variant]
    warmup_s = v.get("warmup_s", 0.0)
    warm = v.get("warm", "never")
    window = block_window(profile, seed) if block == "profile" else block
    made, times, stands = [], [], []
    with _known_profile(profile), pq._filtering(v, made), \
            _warming(warmup_s, warm, times, stands), _blocking(window):
        r = pp.fly(course_name, seed, profile, pq.FLOWN_AS, cruise, course=course)
    windows = outages(profile, seed)
    r["gps"] = {"filters": len(made),
                "restarts": sum(f.restarts for f in made) if v.get("track") else None}
    r["stuck"] = {"warmup_s": warmup_s, "warm": warm,
                  "recovery_t": [round(x, 1) for x in times],
                  "stands": [[round(a, 1), round(b, 1)] for a, b in stands],
                  "block": None if window is None else list(window),
                  "block_outage": (None if window is None
                                   else overlaps(windows, window[0], window[0] + CATCH_S)),
                  "first_outage_s": round(windows[0][0], 1) if windows else None}
    return r


def failed_run(exc):
    return dict(pz.failed_run(exc), stuck=dict(NO_STUCK))


def check_u(expected=None):
    """Fly pace_u.py's missions in `expected` (CHECKED_U by default) again,
    each profile as AS_PACE_U says, and compare each one's time and recovery
    moves with pace_u.py's record."""
    expected = CHECKED_U if expected is None else expected
    compared = 0
    different = []
    for (theirs, variant, course, seed), (elapsed, recovery_t) in sorted(expected.items()):
        profile, window = AS_PACE_U[theirs]
        got = json.loads(json.dumps(fly(course, seed, profile, variant, CRUISES[0],
                                        block=window)))
        compared += 1
        want = {"elapsed_s": elapsed, "recovery_t": list(recovery_t)}
        have = {"elapsed_s": got["elapsed_s"], "recovery_t": got["stuck"]["recovery_t"]}
        if have != want:
            different.append({"profile": theirs, "variant": variant, "course": course,
                              "seed": seed, "want": want, "got": have})
    return {"reference": "pace_u.py's runs", "compared": compared,
            "identical": compared - len(different), "different": different[:20]}


def pair_effects(runs):
    """pace_i.pair_effects with this study's PAIRS."""
    saved = pi.PAIRS
    pi.PAIRS = PAIRS
    try:
        return pi.pair_effects(runs)
    finally:
        pi.PAIRS = saved


def profile_effects(runs):
    """pace_j.profile_effects with this study's variants and PROFILE_PAIRS."""
    saved = pj.VARIANTS, pj.PROFILE_PAIRS
    pj.VARIANTS, pj.PROFILE_PAIRS = VARIANTS, PROFILE_PAIRS
    try:
        return pj.profile_effects(runs)
    finally:
        pj.VARIANTS, pj.PROFILE_PAIRS = saved


def stuck_rows(runs):
    """Per (profile, variant, cruise, course), over the completed missions:
    how many made a recovery move, how many moves in all, how many made
    their first before EARLY_S, how many moves came at or after EARLY_S
    (late), how many stands, and the median and latest first move."""
    rows = []
    for k, rs in sorted(pg._groups(runs).items()):
        ok = [r for r in rs if r["ok"]]
        times = [(r.get("stuck") or {}).get("recovery_t") or [] for r in ok]
        firsts = [x[0] for x in times if x]
        rows.append({"profile": k[0], "variant": k[1], "cruise": k[2], "course": k[3],
                     "missions": len(ok),
                     "with_recovery": sum(1 for r in ok if r["recoveries"] > 0),
                     "recoveries": sum(r["recoveries"] for r in ok),
                     "early": sum(1 for x in firsts if x < EARLY_S),
                     "late": sum(1 for x in times for y in x if y >= EARLY_S),
                     "stands": sum(len(r["stuck"].get("stands") or []) for r in ok),
                     "median_first_s": ps._median(firsts),
                     "latest_first_s": max(firsts) if firsts else None})
    return rows


def block_record(stuck):
    """For a mission's stuck record with a block [s, e]: the first recovery
    move in [s, s + CATCH_S), as seconds after s (None if none); whether
    the mission is eligible (no outage overlapped [s, s + CATCH_S) and no
    stand did); and how many moves began in [e, e + POST_S). None without
    a block."""
    block = stuck.get("block")
    if not block:
        return None
    s, e = block
    until = s + CATCH_S
    moves = stuck.get("recovery_t") or []
    caught = next((x for x in moves if s <= x < until), None)
    stood = overlaps(stuck.get("stands") or [], s, until)
    return {"caught_s": None if caught is None else round(caught - s, 1),
            "eligible": not stood and not stuck.get("block_outage"),
            "post": sum(1 for x in moves if e <= x < e + POST_S)}


def block_rows(runs):
    """Per (profile, variant, cruise, course) of a blocked profile, over the
    completed missions: how many were eligible, how many of those were
    caught within CATCH_S and how many were not (missed), how many were
    caught at all, the median and latest catch of the eligible ones, and the
    moves after the block (post) and the missions with one."""
    rows = []
    for k, rs in sorted(pg._groups(runs).items()):
        if k[0] not in BLOCKS:
            continue
        recs = [block_record(r["stuck"]) for r in rs if r["ok"]]
        recs = [x for x in recs if x is not None]
        eligible = [x for x in recs if x["eligible"]]
        catches = [x["caught_s"] for x in eligible if x["caught_s"] is not None]
        rows.append({"profile": k[0], "variant": k[1], "cruise": k[2], "course": k[3],
                     "missions": len(recs), "eligible": len(eligible),
                     "caught": len(catches), "missed": len(eligible) - len(catches),
                     "caught_any": sum(1 for x in recs if x["caught_s"] is not None),
                     "median_catch_s": ps._median(catches),
                     "latest_catch_s": max(catches) if catches else None,
                     "post": sum(x["post"] for x in recs),
                     "post_missions": sum(1 for x in recs if x["post"])})
    return rows


def _step_up(x):
    """x rounded up to a multiple of TOL_STEP_M."""
    return round(math.ceil(round(x / TOL_STEP_M, 6)) * TOL_STEP_M, 2)


def tolerances(corner, offsets):
    """The spread between BASE_VARIANT and NOISE_VARIANT (two disjoint seed
    sets of the same pilot): the largest difference in blocks corner p95_m
    over the profiles, and in p95_offset_m over every profile and course;
    each tolerance is its spread rounded up to TOL_STEP_M, never below its
    minimum. None where nothing could be compared."""
    def spread(rows, field, courses=None):
        a = {(x["profile"], x["course"]): x[field] for x in rows
             if x["variant"] == BASE_VARIANT}
        b = {(x["profile"], x["course"]): x[field] for x in rows
             if x["variant"] == NOISE_VARIANT}
        diffs = [abs(a[k] - b[k]) for k in a
                 if k in b and a[k] is not None and b[k] is not None
                 and (courses is None or k[1] in courses)]
        return round(max(diffs), 2) if diffs else None

    c = spread(corner, "p95_m", courses=("blocks",))
    o = spread(offsets, "p95_offset_m")
    return {"corner_spread_m": c,
            "corner_tol_m": None if c is None else max(CORNER_TOL_MIN_M, _step_up(c)),
            "offset_spread_m": o,
            "offset_tol_m": None if o is None else max(OFFSET_TOL_MIN_M, _step_up(o))}


def _check_u_line(c):
    return ("Check against pace_u.py's runs: %d compared, %d identical."
            % (c["compared"], c["identical"]))


def write_outputs(out_dir, runs, started, seeds, seeds_b, done, check_r=None):
    s = ps.summarise(runs)
    effects, tallies = pair_effects(runs)
    p_effects, p_tallies = profile_effects(runs)
    stuck = stuck_rows(runs)
    blocks = block_rows(runs)
    gps = pq.gps_rows(runs)
    worst = pz.worst_rows(runs)
    context = po.context_rows(runs)
    corner = pn.corner_rows(runs)
    maxes = pn.offset_max_rows(runs)
    offsets = pe.offset_rows(runs)
    headings_ = pd.heading_rows(runs)
    positions = pg.position_rows(runs)
    steering = ph.steer_rows(runs)
    tol = tolerances(corner, offsets)
    result = {"version": __version__, "pace_u": pu.__version__, "pace_t": pt.__version__,
              "pace_s": pz.__version__, "pace_q": pq.__version__, "pace_p": pp.__version__,
              "pace_study": ps.__version__, "rover_pilot": rp.__version__,
              "dead_reckon": dr.__version__, "done": done,
              "elapsed_s": round(time.monotonic() - started, 1), "seeds": seeds,
              "seeds_b": seeds_b,
              "human": {"marathon_m": ps.MARATHON_M, "time_s": ps.HUMAN_S,
                        "mps": round(ps.HUMAN_MPS, 4)},
              "profiles": PROFILES, "blocks": BLOCKS, "flown_as": pq.FLOWN_AS,
              "variants": VARIANTS, "stand_s": STAND_S, "catch_s": CATCH_S, "post_s": POST_S,
              "early_s": EARLY_S, "pairs": [list(x) for x in PAIRS],
              "profile_pairs": [list(x) for x in PROFILE_PAIRS], "cruises": list(CRUISES),
              "snap_m": SNAP_M, "corner_deg": pn.CORNER_DEG, "corner_m": pn.CORNER_M,
              "far_m": po.FAR_M, "runs": len(runs),
              "completed": sum(1 for r in runs if r["ok"]),
              "overview": s["overview"], "pair_effect": effects, "verdicts": tallies,
              "profile_effect": p_effects, "profile_verdicts": p_tallies, "stuck": stuck,
              "block": blocks, "tolerance": tol, "gps": gps, "worst": worst,
              "position": positions, "corner": corner, "offset": offsets,
              "offset_max": maxes, "context": context, "heading": headings_,
              "steer": steering, "check_u": check_r}
    with open(os.path.join(out_dir, "summary.json"), "w") as f:
        json.dump(result, f, indent=1)
    with open(os.path.join(out_dir, "runs.jsonl"), "w") as f:
        for r in runs:
            f.write(json.dumps(r) + "\n")
    md = ["# A warm-up only after a stand, and blocks of many lengths (simulated)",
          "",
          "pace_v.py %s (pace_u.py %s, pace_t.py %s, pace_q.py %s, pace_p.py %s, rover_pilot.py "
          "%s, dead_reckon.py %s), MV2 of Munim, Inc. Every mission is v0.18.2's real-rover pilot "
          "as pace_u.py flies it, with Pilot._stuck as it ships (a0.3), with no stuck verdict "
          "until %g s after every clear of the stuck history (warm10), or with that warm-up only "
          "at the first check and after a stand of %g s or more with no recovery move "
          "(warmstand10). Profiles: outage90, quiet90, quietdrift90 and quiet45 as in pace-u, "
          "and blockedstart and blockedmid (quiet90 with a block of 30-60 s drawn per seed, at "
          "the start or starting 240-600 s in). Seeds %s; a0.3:B is a0.3 on seeds %s, for the "
          "seed-to-seed spread. %d of %d missions completed. Simulated rovers only, so these "
          "speeds are upper bounds."
          % (__version__, pu.__version__, pt.__version__, pq.__version__, pp.__version__,
             rp.__version__, dr.__version__, WARMUP_S, STAND_S,
             "%d-%d" % (seeds[0], seeds[-1]) if seeds else "none",
             "%d-%d" % (seeds_b[0], seeds_b[-1]) if seeds_b else "none",
             result["completed"], len(runs)), ""]
    if check_r is not None:
        md += [_check_u_line(check_r), ""]
    md += ["## Tolerances from the spread between the two seed sets of a0.3", ""]
    md += pf._table(["figure", "spread m", "tolerance m"],
                    [("blocks corner p95", tol["corner_spread_m"], tol["corner_tol_m"]),
                     ("p95 offset", tol["offset_spread_m"], tol["offset_tol_m"])])
    md += ["", "## Overview (courses pooled)", ""]
    md += pf._table(["profile", "variant", "completed", "made good m/s (median)", "efficiency",
                     "runs beating 0.754", "path ratio", "share stopped"],
                    [(o["profile"], o["variant"], "%d/%d" % (o["completed"], o["runs"]),
                      o["median_made_good_mps"], o["median_efficiency"], o["beat_human_pace"],
                      o["median_path_ratio"], o["share_stopped"]) for o in s["overview"]])
    md += ["", "## Blocked rovers (caught: a recovery move within %g s of the block's start; "
           "eligible: no outage and no stand in that time; post: moves within %g s after the "
           "block)" % (CATCH_S, POST_S), ""]
    md += pf._table(["profile", "variant", "course", "missions", "eligible", "caught", "missed",
                     "caught at all", "median catch s", "latest catch s", "post moves",
                     "missions with one"],
                    [(x["profile"], x["variant"], x["course"], x["missions"], x["eligible"],
                      x["caught"], x["missed"], x["caught_any"], x["median_catch_s"],
                      x["latest_catch_s"], x["post"], x["post_missions"]) for x in blocks])
    md += ["", "## Recovery moves (first before %g s: at the start; late: moves at or after "
           "%g s)" % (EARLY_S, EARLY_S), ""]
    md += pf._table(["profile", "variant", "course", "missions", "with a recovery",
                     "recoveries", "first before %g s" % EARLY_S, "late", "stands",
                     "median first s", "latest first s"],
                    [(x["profile"], x["variant"], x["course"], x["missions"],
                      x["with_recovery"], x["recoveries"], x["early"], x["late"], x["stands"],
                      x["median_first_s"], x["latest_first_s"]) for x in stuck])
    md += ["", "## Pairs, same profile", "",
           "Faster / slower: courses where a paired sign test gives p < 0.05.", ""]
    md += pf._table(["profile", "variant", "against", "faster", "slower", "lost", "gained",
                     "largest median diff"],
                    [(t["profile"], t["variant"], t["against"],
                      "%d/%d" % (t["groups_faster"], t["groups"]), t["groups_slower"],
                      t["groups_lost"], t["groups_gained"], t["largest_median_diff_share"])
                     for t in tallies])
    md += [""]
    md += pf._table(["profile", "variant", "against", "course", "faster", "slower",
                     "median diff s", "share", "p"],
                    [(e["profile"], e["variant"], e["against"], e["course"], e["faster"],
                      e["slower"], e["median_time_diff_s"], e["median_time_diff_share"],
                      e["sign_test_p"]) for e in effects])
    md += ["", "## What the profile costs each variant", ""]
    md += pf._table(["variant", "profile", "against", "faster", "slower", "lost", "gained",
                     "largest median diff"],
                    [(t["variant"], t["profile"], t["against"],
                      "%d/%d" % (t["groups_faster"], t["groups"]), t["groups_slower"],
                      t["groups_lost"], t["groups_gained"], t["largest_median_diff_share"])
                     for t in p_tallies])
    md += ["", "## The pilot's worst idea of where it is, per mission (over %g m: thrown off)"
           % SNAP_M, ""]
    md += pf._table(["profile", "variant", "course", "missions", "median of max m",
                     "largest m", "missions over %g m" % SNAP_M],
                    [(x["profile"], x["variant"], x["course"], x["missions"],
                      x["median_max_m"], x["largest_m"], x["over_snap"]) for x in worst])
    md += ["", "## Where the pilot thinks it is, against where it is", ""]
    md += pf._table(["profile", "variant", "course", "missions", "median m", "p95 m"],
                    [(x["profile"], x["variant"], x["course"], x["missions"],
                      x["median_position_err_m"], x["p95_position_err_m"]) for x in positions])
    md += ["", "## Recovery moves and filter restarts (medians)", ""]
    md += pf._table(["profile", "variant", "course", "missions", "recoveries (median)",
                     "restarts (median)"],
                    [(x["profile"], x["variant"], x["course"], x["missions"],
                      x["median_recoveries"], x["median_restarts"]) for x in gps])
    md += ["", "## Near path corners (pace_n.py's record)", ""]
    md += pf._table(["profile", "variant", "course", "missions", "corners", "median m", "p95 m",
                     "max m", "median past m", "max past m"],
                    [(x["profile"], x["variant"], x["course"], x["missions"], x["corners"],
                      x["median_m"], x["p95_m"], x["max_m"], x["median_past_m"],
                      x["max_past_m"]) for x in corner])
    md += ["", "## Distance from the course while driving forward", ""]
    md += pf._table(["profile", "variant", "course", "missions", "median m", "p95 m"],
                    [(x["profile"], x["variant"], x["course"], x["missions"],
                      x["median_offset_m"], x["p95_offset_m"]) for x in offsets])
    md += ["", "## Largest distance from the course, and refused reports", ""]
    md += pf._table(["profile", "variant", "course", "missions", "median of max m",
                     "largest m", "refused", "missions refused"],
                    [(x["profile"], x["variant"], x["course"], x["missions"], x["median_max_m"],
                      x["largest_max_m"], x["refused"], x["missions_refused"]) for x in maxes])
    md += ["", "## Where the rover strays (true distance from the course by context; far: "
           "over %g m)" % po.FAR_M, ""]
    md += pf._table(["profile", "variant", "course", "context", "missions", "samples", "far",
                     "far share", "median m", "p95 m", "max m"],
                    [(x["profile"], x["variant"], x["course"], x["context"], x["missions"],
                      x["samples"], x["far"], x["far_share"], x["median_m"], x["p95_m"],
                      x["max_m"]) for x in context])
    md += ["", "## Heading error", ""]
    md += pf._table(["profile", "variant", "course", "missions", "median abs deg", "rms deg"],
                    [(x["profile"], x["variant"], x["course"], x["missions"],
                      x["median_abs_deg"], x["rms_deg"]) for x in headings_])
    md += ["", "## How hard the pilot steers", ""]
    md += pf._table(["profile", "variant", "course", "missions", "mean abs angular"],
                    [(x["profile"], x["variant"], x["course"], x["missions"],
                      x["median_mean_abs_angular"]) for x in steering])
    with open(os.path.join(out_dir, "report.md"), "w") as f:
        f.write("\n".join(md) + "\n")
    return result


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out-dir", default="out")
    ap.add_argument("--first-seed", type=int, default=FIRST_SEED)
    ap.add_argument("--first-seed-b", type=int, default=FIRST_SEED_B)
    ap.add_argument("--seeds", type=int, default=24, help="how many seeds in each set")
    ap.add_argument("--budget-min", type=float, default=180.0)
    ap.add_argument("--courses", help="comma-separated subset of: " + ",".join(ps.COURSES))
    ap.add_argument("--profiles", help="comma-separated subset of: " + ",".join(PROFILES))
    ap.add_argument("--variants", help="comma-separated subset of: " + ",".join(VARIANTS))
    ap.add_argument("--check-u", action="store_true",
                    help="fly CHECKED_U again and compare with pace_u.py's record")
    args = ap.parse_args(argv)
    courses = ps._names(args.courses, ps.COURSES, "course")
    profiles = ps._names(args.profiles, PROFILES, "profile")
    variants = ps._names(args.variants, VARIANTS, "variant")
    # outage90 and a0.3 are always flown: the rest are compared with them.
    profiles = [BASE_PROFILE] + [p for p in profiles if p != BASE_PROFILE]
    variants = [BASE_VARIANT] + [v for v in variants if v != BASE_VARIANT]
    seeds = list(range(args.first_seed, args.first_seed + args.seeds))
    seeds_b = (list(range(args.first_seed_b, args.first_seed_b + args.seeds))
               if NOISE_VARIANT in variants else [])
    os.makedirs(args.out_dir, exist_ok=True)
    started = time.monotonic()
    check_r = check_u() if args.check_u else None
    if check_r is not None:
        print(_check_u_line(check_r), flush=True)
    runs = []
    done = True
    for profile in profiles:
        for variant in variants:
            if time.monotonic() - started > args.budget_min * 60.0:
                done = False
                break
            for cruise in CRUISES:
                for course in courses:
                    for seed in (seeds_b if variant == NOISE_VARIANT else seeds):
                        try:
                            r = fly(course, seed, profile, variant, cruise)
                        except Exception as exc:
                            r = failed_run(exc)
                        r.update(profile=profile, variant=variant, cruise=cruise,
                                 course=course, seed=seed)
                        runs.append(r)
            print("%s / %s: %d runs so far, %.0f s"
                  % (profile, variant, len(runs), time.monotonic() - started), flush=True)
            write_outputs(args.out_dir, runs, started, seeds, seeds_b, False, check_r)
        if not done:
            break
    result = write_outputs(args.out_dir, runs, started, seeds, seeds_b, done, check_r)
    brief = None if check_r is None else {x: check_r[x] for x in ("compared", "identical")}
    print(json.dumps(dict(check_u=brief, completed=result["completed"], runs=result["runs"],
                          tolerance=result["tolerance"],
                          verdicts=[{k: v[k] for k in ("profile", "variant", "against",
                                                       "groups_faster", "groups_slower",
                                                       "groups_lost")}
                                    for v in result["verdicts"]],
                          block=[{k: x[k] for k in ("profile", "variant", "course", "eligible",
                                                    "missed", "median_catch_s", "post")}
                                 for x in result["block"]],
                          stuck=[{k: x[k] for k in ("profile", "variant", "course",
                                                    "with_recovery", "early", "late")}
                                 for x in result["stuck"]])), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
