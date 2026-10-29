"""Fetch everything frodo-spin-v2 runs (Apache-2.0) into this folder:
frodo_motion.py from earth-rover-pilot v0.8.0, frodo_compass.py and
frodo_compass_live.py (0.1.0) from main, and the pre-registered
studies/frodo-spin/frodo_spin.py and test_frodo_spin.py from main. Stop if
frodo_spin.py is not the file frodo-spin-v1 ran, and wait until
studies/frodo-spin/PLAN-v2.md is on main, so the larger sample runs exactly
the pre-registered code under a plan written before it. Writes fetched.json.
By MV2 of Munim, Inc.; written with AI agents. Apache-2.0."""

import hashlib
import json
import re
import sys
import time
import urllib.error
import urllib.request

BASE = "https://raw.githubusercontent.com/munimtechnologies/earth-rover-pilot/"
STUDY = "main/studies/frodo-spin/"
WAIT_MIN = 240
# frodo_spin.py and test_frodo_spin.py as frodo-spin-v1 ran them (its summary.json "fetched").
V1_SHA256 = {"frodo_spin.py": "194b3bca8e5f1133abe6742b92b073df9248ffc1daa9da9ed9f90c2e7c8672b0",
             "test_frodo_spin.py": "7fbc1bb0b16902f921ebe571b0a2d770b323cb65e957b414a8d190da928d2f48"}


def get(url):
    req = urllib.request.Request(url, headers={"Cache-Control": "no-cache"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


def norm(data):
    return data.replace(b"\r\n", b"\n")


fetched = {}
for ref, name, want in (("v0.8.0/", "frodo_motion.py", "0.2.0"), ("main/", "frodo_compass.py", "0.1.0"),
                        ("main/", "frodo_compass_live.py", "0.1.0")):
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

for name, want in V1_SHA256.items():
    data = norm(get(BASE + STUDY + name))
    sha = hashlib.sha256(data).hexdigest()
    if sha != want:
        sys.exit("%s on main is %s, not the file frodo-spin-v1 ran (%s)" % (name, sha, want))
    with open(name, "wb") as f:
        f.write(data)
    fetched[name] = {"ref": "main/studies/frodo-spin", "sha256": sha, "same_as_v1": True}
    print(name, "matches frodo-spin-v1", flush=True)

deadline = time.monotonic() + WAIT_MIN * 60
while True:
    try:
        plan = get(BASE + STUDY + "PLAN-v2.md")
        break
    except urllib.error.HTTPError as exc:
        if exc.code != 404 or time.monotonic() > deadline:
            sys.exit("PLAN-v2.md not on main: %s" % exc)
        print("PLAN-v2.md not on main yet; waiting", flush=True)
        time.sleep(300)
fetched["PLAN-v2.md"] = {"on_main": True, "sha256": hashlib.sha256(norm(plan)).hexdigest()}
pred = get(BASE + STUDY + "PREDICTION.md")
fetched["PREDICTION.md"] = {"sha256": hashlib.sha256(norm(pred)).hexdigest()}

with open("fetched.json", "w") as f:
    json.dump(fetched, f, indent=1)
print(json.dumps(fetched), flush=True)
