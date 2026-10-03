import os
import sys
import time
import requests
import pandas as pd

# ---- node table: node number -> (device MAC, name of that channel's write key) ----
NODES = {
    1: ("b8:27:eb:bf:9d:51", "TS_WRITE_KEY"),     # stable, warm
    2: ("1c:bf:ce:15:ec:4d", "TS_WRITE_KEY_2"),   # variable temp/humidity
    3: ("00:0f:00:70:91:0a", "TS_WRITE_KEY_3"),   # stable, cooler
}

# ---- config ----
CSV_FILE = "iot_telemetry_data.csv"
ENV_FILE = ".env"
INTERVAL = 16   # seconds between sends (free plan minimum is 15, per channel)
STEP = 20       # send every 20th row (~1 min of original data per send)
URL = "https://api.thingspeak.com/update"


def load_env(path):
    """Read KEY=value lines from a .env file into os.environ (no extra packages needed)."""
    if not os.path.exists(path):
        return
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            # a key already exported in the terminal takes priority over the file
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


# ---- pick node from command line ----
if len(sys.argv) != 2 or not sys.argv[1].isdigit() or int(sys.argv[1]) not in NODES:
    raise SystemExit("Usage: python replay.py <node number: 1, 2 or 3>")
node = int(sys.argv[1])
DEVICE, KEY_VAR = NODES[node]

load_env(ENV_FILE)
API_KEY = os.environ.get(KEY_VAR)
if not API_KEY:
    raise SystemExit(f"{KEY_VAR} not found. Add it to {ENV_FILE} or run: export {KEY_VAR}=your_key")

# ---- load + prep data ----
df = pd.read_csv(CSV_FILE)
df = df[df["device"] == DEVICE].sort_values("ts").reset_index(drop=True)
df["light"] = df["light"].astype(int)
df["motion"] = df["motion"].astype(int)
df = df.iloc[::STEP]
print(f"[Node {node}] Loaded {len(df)} rows for device {DEVICE}")

# ---- replay loop ----
try:
    while True:
        for _, row in df.iterrows():
            payload = {
                "api_key": API_KEY,
                "field1": round(row["temp"], 2),
                "field2": round(row["humidity"], 2),
                "field3": row["co"],
                "field4": row["smoke"],
                "field5": row["lpg"],
                "field6": row["light"],
                "field7": row["motion"],
            }

            while True:
                try:
                    r = requests.get(URL, params=payload, timeout=10)
                    entry = r.text.strip()
                except requests.RequestException as e:
                    entry = "0"
                    print(f"[Node {node}] Network error: {e}")

                if entry != "0":
                    original_time = pd.to_datetime(row["ts"], unit="s")
                    print(f"[Node {node}] entry {entry} | original time {original_time} | "
                          f"temp={payload['field1']} hum={payload['field2']}")
                    break
                print(f"[Node {node}] Rejected (rate limit?), retrying...")
                time.sleep(INTERVAL)

            time.sleep(INTERVAL)

        print(f"[Node {node}] Reached end of dataset, looping again...")
except KeyboardInterrupt:
    print(f"\n[Node {node}] Stopped.")