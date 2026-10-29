"""Fetch the modules frodo_regap2.py imports (Apache-2.0) into this folder:
frodo_motion.py from earth-rover-pilot v0.8.0, rover_pilot.py from v0.19.0 and
frodo_regap.py (0.1.0) from main's studies/frodo-regap. Then wait until
studies/frodo-regap2/PREDICTION.md is on main, and check that the
frodo_regap2.py and test_frodo_regap2.py committed beside it are the ones
here, so the study runs the code that was pre-registered. Writes fetched.json."""

import hashlib
import json
import re
import sys
import time
import urllib.error
import urllib.request

BASE = "https://raw.githubusercontent.com/munimtechnologies/earth-rover-pilot/"
STUDY = "main/studies/frodo-regap2/"
WAIT_MIN = 240


def get(url):
    req = urllib.request.Request(url, headers={"Cache-Control": "no-cache"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


def norm(data):
    return data.replace(b"\r\n", b"\n")


fetched = {}
for ref, name, want in (("v0.8.0/", "frodo_motion.py", None), ("v0.19.0/", "rover_pilot.py", "0.19.0"),
                        ("main/studies/frodo-regap/", "frodo_regap.py", "0.1.0")):
    data = get(BASE + ref + name)
    with open(name, "wb") as f:
        f.write(data)
    m = re.search(rb'^__version__ = "([^"]+)"', data, re.M)
    version = m.group(1).decode() if m else None
    if want and version != want:
        sys.exit("%s at %s is %s, not %s" % (name, ref, version, want))
    fetched[name] = {"ref": ref.rstrip("/"), "version": version,
                     "sha256": hashlib.sha256(norm(data)).hexdigest()}
    print("fetched", ref, name, version, flush=True)

deadline = time.monotonic() + WAIT_MIN * 60
while True:
    try:
        pred = get(BASE + STUDY + "PREDICTION.md")
        break
    except urllib.error.HTTPError as exc:
        if exc.code != 404 or time.monotonic() > deadline:
            sys.exit("PREDICTION.md not on main: %s" % exc)
        print("PREDICTION.md not on main yet; waiting", flush=True)
        time.sleep(300)
fetched["PREDICTION.md"] = {"sha256": hashlib.sha256(norm(pred)).hexdigest()}

for name in ("frodo_regap2.py", "test_frodo_regap2.py"):
    with open(name, "rb") as f:
        here = norm(f.read())
    there = norm(get(BASE + STUDY + name))
    if here != there:
        sys.exit("%s here differs from the pre-registered copy on main" % name)
    fetched[name] = {"sha256": hashlib.sha256(here).hexdigest(), "same_as_main": True}
    print(name, "matches main", flush=True)

with open("fetched.json", "w") as f:
    json.dump(fetched, f, indent=1)
print(json.dumps(fetched), flush=True)
