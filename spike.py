"""Inject one clearly labelled TEST spike into a node's channel: a fire drill for the alerting.

It reads the node's latest real reading, multiplies the gas readings (CO, smoke, LPG)
by a factor, and sends it with the ThingSpeak status "TEST SPIKE", so the reading is
recorded as a test and the dashboard labels it "[test injection]".

Usage:  python spike.py <node> [factor]      e.g.  python spike.py 2  (small leak, x1.25)   or   python spike.py 2 3  (big leak)
"""
import os
import sys
import time
import requests

# node number -> (ThingSpeak channel ID, name of that channel's write key)
CHANNELS = {
    1: (3518861, "TS_WRITE_KEY"),
    2: (3518882, "TS_WRITE_KEY_2"),
    3: (3519225, "TS_WRITE_KEY_3"),
}
GAS_FIELDS = ("field3", "field4", "field5")   # co, smoke, lpg
DEFAULT_FACTOR = 1.25   # small leak: under the fixed limits, but unusual for the node
ENV_FILE = ".env"
UPDATE_URL = "https://api.thingspeak.com/update"


def load_env(path):
    """Read KEY=value lines from a .env file into os.environ (same as replay.py)."""
    if not os.path.exists(path):
        return
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


# ---- arguments ----
if len(sys.argv) not in (2, 3) or not sys.argv[1].isdigit() or int(sys.argv[1]) not in CHANNELS:
    raise SystemExit("Usage: python spike.py <node number: 1, 2 or 3> [factor, default 1.25]")
node = int(sys.argv[1])
try:
    factor = float(sys.argv[2]) if len(sys.argv) == 3 else DEFAULT_FACTOR
except ValueError:
    raise SystemExit("factor must be a number, e.g. 1.25")
if factor <= 1:
    raise SystemExit("factor must be greater than 1")

channel_id, key_var = CHANNELS[node]
if channel_id is None:
    raise SystemExit(f"Set Node {node}'s channel ID in CHANNELS at the top of spike.py first.")

load_env(ENV_FILE)
api_key = os.environ.get(key_var)
if not api_key:
    raise SystemExit(f"{key_var} not found. Add it to {ENV_FILE}.")

# ---- read the latest real reading so the other fields stay realistic ----
try:
    last = requests.get(f"https://api.thingspeak.com/channels/{channel_id}/feeds/last.json",
                        timeout=10).json()
except (requests.RequestException, ValueError) as e:
    raise SystemExit(f"Couldn't read the latest reading: {e}")
if not isinstance(last, dict) or not all(last.get(f) for f in GAS_FIELDS):
    raise SystemExit("No readable data on that channel. Is it public, and is replay.py running?")

payload = {"api_key": api_key, "status": "TEST SPIKE"}
for n in range(1, 8):
    if last.get(f"field{n}") is not None:
        payload[f"field{n}"] = last[f"field{n}"]
for f in GAS_FIELDS:
    payload[f] = round(float(last[f]) * factor, 6)

print(f"[Node {node}] Injecting TEST spike (gas x{factor}): "
      f"co={payload['field3']} smoke={payload['field4']} lpg={payload['field5']}")

# ---- send; retry while the 15 s rate limit (shared with replay.py) blocks it ----
for attempt in range(15):
    try:
        entry = requests.get(UPDATE_URL, params=payload, timeout=10).text.strip()
    except requests.RequestException as e:
        entry = "0"
        print(f"[Node {node}] Network error: {e}")
    if entry != "0":
        print(f"[Node {node}] Spike accepted as entry {entry}. Watch the dashboard within ~15 s.")
        break
    time.sleep(2)
else:
    raise SystemExit(f"[Node {node}] Rejected 15 times in a row. Try again in a few seconds.")
