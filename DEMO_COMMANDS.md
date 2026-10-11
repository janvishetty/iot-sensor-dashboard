# IoT Dashboard: Demo Commands

All commands, in order. Each tab: open with `Cmd + T`, paste one block, press Enter.

---

## 1. Start everything (15–20 minutes before presenting)

**Tab 1: web server**
```bash
cd ~/iot-dashboard && python3 -m http.server 8000
```

**Tab 2: Node 1**
```bash
cd ~/iot-dashboard && source venv/bin/activate && python replay.py 1
```

**Tab 3: Node 2**
```bash
cd ~/iot-dashboard && source venv/bin/activate && python replay.py 2
```

**Tab 4: Node 3**
```bash
cd ~/iot-dashboard && source venv/bin/activate && python replay.py 3
```

**Tab 5: keep the Mac awake** (keep the charger in and the lid open)
```bash
caffeinate -is
```

**Open in Chrome:**
```
http://localhost:8000/dashboard.html
```

Check: all 3 node cards show green dots. The cards say "building baseline…" for the first ~3 minutes, then show z-scores.

---

## 2. Alert demo

**Tab 6: setup** (do this once)
```bash
cd ~/iot-dashboard && source venv/bin/activate
```

### Node 1
```bash
python spike.py 1        # small leak: amber only (fixed limits miss it)
```
```bash
python spike.py 1 3      # big leak: red + amber
```

### Node 2
```bash
python spike.py 2        # small leak: amber only
```
```bash
python spike.py 2 3      # big leak: red + amber
```

Wait about 30 seconds between two spikes on the **same** node. Different nodes can go back to back.
A few "Rejected (rate limit?)" lines before "Spike accepted" are normal.

### Node goes offline / comes back
1. Press `Ctrl + C` in the **Tab 2** (Node 1) window
2. Wait about 75 seconds → event log: **"Node 1 stopped reporting"**, dot turns yellow
3. Restart it in the same tab:
```bash
python replay.py 1
```
4. Within about 15 seconds → event log: **"Node 1 back online"**, dot turns green

(Same for Node 2: Tab 3, `python replay.py 2`)

Don't refresh the page during the demo, or the event log clears.

---

## 3. Suggested demo order

1. Show the fleet view and switch between Node 1 / 2 / 3
2. `python spike.py 1` → "amber, but no red: the fixed limit missed it, the anomaly detector caught it"
3. `python spike.py 2 3` → "big leak: both layers fire"
4. Stop Node 1 → "stopped reporting" → restart → "back online"

---

## 4. Useful links

- Dashboard (on this laptop): http://localhost:8000/dashboard.html
- Dashboard (online, any device, needs GitHub Pages turned on): https://janvishetty.github.io/iot-sensor-dashboard/dashboard.html
- Node 1 raw cloud data: https://thingspeak.mathworks.com/channels/3518861
- Node 2 raw cloud data: https://thingspeak.mathworks.com/channels/3518882
- Node 3 raw cloud data: https://thingspeak.mathworks.com/channels/3519225
- Code: https://github.com/janvishetty/iot-sensor-dashboard

---

## 5. If something goes wrong

**"Address already in use" in Tab 1**: an old server is still running:
```bash
lsof -ti :8000 | xargs kill
```
then run the Tab 1 command again.

**Replays keep printing "Rejected" over and over**: another copy is running on the same node:
```bash
pkill -f replay.py
```
then restart Tabs 2–4.

**"TS_WRITE_KEY not found"**: you're not in the project folder, or `.env` is missing:
```bash
cd ~/iot-dashboard && ls -a
```
(`.env` should be in the list)

**Dashboard shows old version**: hard refresh with `Cmd + Shift + R`.

**No internet on college Wi-Fi**: switch to your phone's hotspot.

---

## 6. Stop everything

Press `Ctrl + C` in each tab, or run this in any tab:
```bash
pkill -f replay.py; pkill -f http.server; pkill caffeinate
```

---

## 7. Save changes to GitHub

```bash
cd ~/iot-dashboard && git add . && git commit -m "Update" && git push
```
