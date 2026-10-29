"""Fetch the modules colosseum_compat.py imports (Apache-2.0) into this folder:
rover_pilot.py and dead_reckon.py from earth-rover-pilot's main, which must be
0.19.x (0.19.1 changed only documentation). Also notes whether
studies/colosseum-compat/PLAN.md is on main yet. Writes fetched.json."""

import hashlib
import json
import re
import sys
import urllib.error
import urllib.request

BASE = "https://raw.githubusercontent.com/munimtechnologies/earth-rover-pilot/main/"


def get(url):
    req = urllib.request.Request(url, headers={"Cache-Control": "no-cache"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


fetched = {}
for name in ("rover_pilot.py", "dead_reckon.py"):
    data = get(BASE + name)
    with open(name, "wb") as f:
        f.write(data)
    m = re.search(rb'^__version__ = "([^"]+)"', data, re.M)
    version = m.group(1).decode() if m else None
    if name == "rover_pilot.py" and not (version or "").startswith("0.19."):
        sys.exit("rover_pilot.py on main is %s, not 0.19.x" % version)
    fetched[name] = {"version": version, "sha256": hashlib.sha256(data).hexdigest()}
    print("fetched", name, version, flush=True)

try:
    plan = get(BASE + "studies/colosseum-compat/PLAN.md").replace(b"\r\n", b"\n")
    fetched["PLAN.md"] = {"on_main": True, "sha256": hashlib.sha256(plan).hexdigest()}
except urllib.error.HTTPError as exc:
    fetched["PLAN.md"] = {"on_main": False, "error": exc.code}

with open("fetched.json", "w") as f:
    json.dump(fetched, f, indent=1)
print(json.dumps(fetched), flush=True)
