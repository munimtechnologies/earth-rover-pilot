"""Fetch the modules colosseum_rate.py imports from earth-rover-pilot's main
(Apache-2.0): rover_pilot.py (must be 0.19.x), its helper modules,
studies/colosseum-compat/colosseum_compat.py and
studies/colosseum-hold/colosseum_hold.py, which must be the file
colosseum-hold-v1 and colosseum-hold-confirm-v1 flew. Waits (up to 30 min)
for studies/colosseum-rate/PLAN.md to be on main and stops if it isn't, and
notes whether this folder's colosseum_rate.py matches main's copy. Writes
fetched.json."""

import hashlib
import json
import re
import sys
import time
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

# The bridge must be the one the two earlier studies flew.
fetched["colosseum_hold.py"]["same_as_hold_v1"] = fetched["colosseum_hold.py"]["sha256"] == HOLD_SHA256
if not fetched["colosseum_hold.py"]["same_as_hold_v1"]:
    sys.exit("colosseum_hold.py on main differs from the file colosseum-hold-v1 flew")

# Nothing flies before the plan is public: wait up to 30 min for it on main.
for attempt in range(21):
    try:
        data = get(BASE + "studies/colosseum-rate/PLAN.md")
        fetched["PLAN.md"] = {"on_main": True, "sha256": sha(data), "waited_s": attempt * 90}
        break
    except urllib.error.HTTPError as exc:
        if exc.code != 404 or attempt == 20:
            sys.exit("studies/colosseum-rate/PLAN.md is not on main (%s)" % exc.code)
        print("PLAN.md not on main yet; waiting 90 s", flush=True)
        time.sleep(90)

try:
    data = get(BASE + "studies/colosseum-rate/colosseum_rate.py")
    fetched["colosseum_rate.py"] = {"on_main": True, "sha256": sha(data)}
except urllib.error.HTTPError as exc:
    fetched["colosseum_rate.py"] = {"on_main": False, "error": exc.code}
with open("colosseum_rate.py", "rb") as f:
    local = sha(f.read())
fetched["colosseum_rate.py"]["local_sha256"] = local
fetched["colosseum_rate.py"]["same_as_main"] = fetched["colosseum_rate.py"].get("sha256") == local

with open("fetched.json", "w") as f:
    json.dump(fetched, f, indent=1)
print(json.dumps(fetched), flush=True)
