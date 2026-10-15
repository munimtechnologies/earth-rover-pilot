#!/usr/bin/env python3
"""marathon: what beating the human Berkeley-Stanford time asks of an Earth Rover Mini+.

Human drivers took an Earth Rover Mini+ from UC Berkeley to Stanford, about
50 miles in seven legs, by remote control in 29 h 38 min (FrodoBots, Sept
2026). The earth-rovers-sdk README gives the Mini+ "12 km range per charge,
top speed 4 km/h". Put together:

- 50 miles is 80.5 km, so at its top speed a Mini+ needs at least 20.1 h of
  driving. The human time can therefore hold at most about 9.5 h of stops,
  however the legs and charging were arranged.
- Seven legs of 11.5 km each on a 12 km charge leave about 4% for anything
  driven beyond the route itself: detours, re-plans, back-up moves, weaving.
  A pilot whose path is more than about 1.04 times the route would run out
  of battery before the end of a leg, if the 12 km holds at its speed.
- Averaging the human pace with no stops at all needs 0.754 m/s made good,
  68% of the top speed.

    python marathon.py budget                 # the numbers above
    python marathon.py route check.json       # a --check-route summary against one charge
    python marathon.py pace summary.json      # pace_study.py results against the budget

`route` reads what `rover_pilot.py --check-route` prints (save it with > file).
`pace` reads pace_study.py's summary.json and says, per cruise, whether its
median speed made good beats the human time and whether its median path
ratio fits in a charge. The range is the README's figure, not a measurement:
how far a charge really goes at a given speed, on real pavement, is not known
yet. Standard library only. By MV2 of Munim, Inc.; written with AI agents.
Apache-2.0.
"""

from __future__ import annotations

import argparse
import json
import sys

__version__ = "0.1.0"

# The human benchmark (FrodoBots, Sept 2026): Berkeley to Stanford, 50 miles in
# seven legs, 29 h 38 min by remote control on an Earth Rover Mini+.
MARATHON_M = 50 * 1609.344
HUMAN_S = 29 * 3600 + 38 * 60
MARATHON_LEGS = 7
# earth-rovers-sdk README (v6.3), Mini+ chassis: "12 km range per charge, top speed 4 km/h".
MINIPLUS_TOP_MPS = 4.0 / 3.6
MINIPLUS_RANGE_M = 12000.0


def _r(x, nd=3):
    return None if x is None else round(x, nd)


def budget(distance_m=MARATHON_M, time_s=HUMAN_S, legs=MARATHON_LEGS,
           top_mps=MINIPLUS_TOP_MPS, range_m=MINIPLUS_RANGE_M):
    """What a rover with this top speed and range needs to beat `time_s` over
    `distance_m` driven in `legs` equal legs, one charge per leg."""
    leg_m = distance_m / legs
    pace = distance_m / time_s
    min_drive_s = distance_m / top_mps
    return {"distance_m": _r(distance_m, 1), "time_s": time_s, "human_pace_mps": _r(pace, 4),
            "legs": legs, "leg_m": _r(leg_m, 1), "range_m": range_m,
            "max_path_ratio": _r(range_m / leg_m, 4),
            "top_mps": _r(top_mps, 4), "min_drive_h": _r(min_drive_s / 3600.0, 2),
            "max_stops_h": _r((time_s - min_drive_s) / 3600.0, 2),
            "cruise_floor": _r(pace / top_mps, 4)}


def needed_made_good(stops_s=0.0, distance_m=MARATHON_M, time_s=HUMAN_S):
    """The speed made good (m/s) that beats `time_s` when `stops_s` of it is spent
    standing (charging, swaps, waiting); None if the stops alone use it up."""
    moving = time_s - stops_s
    return None if moving <= 0 else distance_m / moving


def stops_allowed_s(made_good_mps, distance_m=MARATHON_M, time_s=HUMAN_S):
    """Seconds of stops a rover making good this speed can afford and still beat
    `time_s` (negative: it is too slow even without stopping)."""
    if made_good_mps is None or made_good_mps <= 0:
        return None
    return time_s - distance_m / made_good_mps


def check_route(summary, range_m=MINIPLUS_RANGE_M):
    """A `rover_pilot.py --check-route` summary against one charge."""
    route_m = summary.get("route_m")
    straight_m = summary.get("straight_m")
    complete = bool(summary.get("ok"))
    out = {"complete": complete, "route_m": route_m, "straight_m": straight_m,
           "range_m": range_m}
    if route_m is None:
        return dict(out, fits_one_charge=None, reason="no route length in the summary")
    out.update(share_of_charge=_r(route_m / range_m), headroom_m=_r(range_m - route_m, 1),
               detour_ratio=_r(route_m / straight_m) if straight_m else None,
               fits_one_charge=route_m <= range_m)
    if not complete:
        out["reason"] = "some legs have no walkable route, so the length is a lower bound"
    elif route_m > range_m:
        out["reason"] = "the planned route is longer than one charge"
    else:
        out["reason"] = "the planned route fits one charge with %.0f m to spare" % (range_m - route_m)
    return out


def pace_verdicts(pace_summary, plan=None):
    """Per pace_study overview row (profile, variant, cruise; courses pooled):
    hours of driving the marathon would take at its median speed made good,
    the stops that leaves, and whether its median path ratio fits a charge."""
    plan = plan or budget()
    out = []
    for o in pace_summary.get("overview") or []:
        v = o.get("median_made_good_mps")
        ratio = o.get("median_path_ratio")
        allowed = stops_allowed_s(v)
        out.append({"profile": o.get("profile"), "variant": o.get("variant"),
                    "cruise": o.get("cruise"), "completed": o.get("completed"),
                    "runs": o.get("runs"), "made_good_mps": v,
                    "drive_h": _r(MARATHON_M / v / 3600.0, 2) if v else None,
                    "stops_allowed_h": _r(allowed / 3600.0, 2) if allowed is not None else None,
                    "beats_with_no_stops": bool(v) and v > plan["human_pace_mps"],
                    "path_ratio": ratio,
                    "path_fits_charge": None if ratio is None else ratio <= plan["max_path_ratio"]})
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("budget", help="what beating the human time asks of a Mini+")
    b.add_argument("--range-km", type=float, default=MINIPLUS_RANGE_M / 1000.0)
    b.add_argument("--top-kmh", type=float, default=MINIPLUS_TOP_MPS * 3.6)
    r = sub.add_parser("route", help="a saved --check-route summary against one charge")
    r.add_argument("file")
    r.add_argument("--range-km", type=float, default=MINIPLUS_RANGE_M / 1000.0)
    p = sub.add_parser("pace", help="pace_study.py summary.json against the budget")
    p.add_argument("file")
    ap.add_argument("--version", action="version", version=__version__)
    args = ap.parse_args(argv)
    if args.cmd == "budget":
        out = budget(top_mps=args.top_kmh / 3.6, range_m=args.range_km * 1000.0)
    elif args.cmd == "route":
        with open(args.file, encoding="utf-8") as f:
            out = check_route(json.load(f), range_m=args.range_km * 1000.0)
    else:
        with open(args.file, encoding="utf-8") as f:
            out = {"budget": budget(), "verdicts": pace_verdicts(json.load(f))}
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
