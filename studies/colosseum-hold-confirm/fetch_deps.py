"""Fetch everything colosseum-hold-confirm runs from earth-rover-pilot's main
(Apache-2.0): rover_pilot.py (must be 0.19.x), its helper modules,
studies/colosseum-compat/colosseum_compat.py, and studies/colosseum-hold's
colosseum_hold.py and test_colosseum_hold.py, so the study code is main's own.
Also notes whether studies/colosseum-hold-confirm/PLAN.md is on main.
Writes fetched.json."""

import hashlib
import json
import re
import sys
import urllib.error
import urllib.request

BASE = "https://raw.githubusercontent.com/munimtechnologies/earth-rover-pilot/main/"
MODULES = {
    "rover_pilot.py": "rover_pilot.py",
    "dead_reckon.py": "dead_reckon.py",
    "free_space.py": "free_space.py",
    "calibrate.py": "calibrate.py",
    "route_planner.py": "route_planner.py",
    "colosseum_compat.py": "studies/colosseum-compat/colosseum_compat.py",
    "colosseum_hold.py": "studies/colosseum-hold/colosseum_hold.py",
    "test_colosseum_hold.py": "studies/colosseum-hold/test_colosseum_hold.py",
}
HOLD_SHA256 = "1d54b068e77297bca07166e6187c13c314a39d17c75ea99e93b93ea9a6e99a19"


def get(url):
    req = urllib.request.Request(url, headers={"Cache-Control": "no-cache"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


def sha(data):
    return hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()


fetched = {}
for name, path in MODULES.items():
    data = get(BASE + path)
    with open(name, "wb") as f:
        f.write(data)
    m = re.search(rb'^__version__ = "([^"]+)"', data, re.M)
    version = m.group(1).decode() if m else None
    if name == "rover_pilot.py" and not (version or "").startswith("0.19."):
        sys.exit("rover_pilot.py on main is %s, not 0.19.x" % version)
    fetched[name] = {"path": path, "version": version, "sha256": sha(data)}
    print("fetched", path, version, flush=True)

# colosseum-hold-v1 flew this exact file; the confirmation must fly it too.
fetched["colosseum_hold.py"]["same_as_hold_v1"] = fetched["colosseum_hold.py"]["sha256"] == HOLD_SHA256
if not fetched["colosseum_hold.py"]["same_as_hold_v1"]:
    sys.exit("colosseum_hold.py on main differs from the file colosseum-hold-v1 flew")

try:
    data = get(BASE + "studies/colosseum-hold-confirm/PLAN.md")
    fetched["PLAN.md"] = {"on_main": True, "sha256": sha(data)}
except urllib.error.HTTPError as exc:
    fetched["PLAN.md"] = {"on_main": False, "error": exc.code}

with open("fetched.json", "w") as f:
    json.dump(fetched, f, indent=1)
print(json.dumps(fetched), flush=True)
