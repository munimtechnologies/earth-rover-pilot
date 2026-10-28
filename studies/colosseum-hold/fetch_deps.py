"""Fetch the modules colosseum_hold.py imports (Apache-2.0) into this folder:
rover_pilot.py (must be 0.19.x), its helper modules, and
studies/colosseum-compat/colosseum_compat.py from earth-rover-pilot's main.
Also notes whether studies/colosseum-hold/PLAN.md is on main and whether this
folder's colosseum_hold.py matches main's copy. Writes fetched.json."""

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
}


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

for name, path in (("PLAN.md", "studies/colosseum-hold/PLAN.md"),
                   ("colosseum_hold.py", "studies/colosseum-hold/colosseum_hold.py")):
    try:
        data = get(BASE + path)
        fetched[name] = {"on_main": True, "sha256": sha(data)}
    except urllib.error.HTTPError as exc:
        fetched[name] = {"on_main": False, "error": exc.code}
with open("colosseum_hold.py", "rb") as f:
    local = sha(f.read())
fetched["colosseum_hold.py"]["local_sha256"] = local
fetched["colosseum_hold.py"]["same_as_main"] = fetched["colosseum_hold.py"].get("sha256") == local

with open("fetched.json", "w") as f:
    json.dump(fetched, f, indent=1)
print(json.dumps(fetched), flush=True)
