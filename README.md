# 🛡️ HomeSync Wi-Fi Sentinel (Enterprise Python Edition)
### Professional Device Tracking, Threat Hunting & Network Telemetry

HomeSync is a high-density Wi-Fi surveillance platform designed entirely in Python. By utilizing `scapy`, `rich`, and `sqlite3`, it acts as a standalone Terminal User Interface (TUI) monitor that operates autonomously without any heavy web servers.

---

## 🔥 Key Enterprise Features (v2.0)
The Sentinel spans multiple highly optimized, threaded `.py` files and features real-time logging, math computations, and active threat scoring.

1. **📊 Persistent SQLite Database**: All seen networks, clients, probe requests, and security logs are recorded into `homesync.db`, offering complete historic querying beyond the memory session.
2. **📉 Network Anomaly Score (NAS)**: Dynamically computes a 0-100 Threat Score based on active EAPOLs, Beacon Floods, Rogue APs, and Deauth attacks, decaying organically over time.
3. **🔋 Sparkline Telemetry UI**: Visually graphs Signal Strength (RSSI) in the terminal directly using ` ▂▃▄▅▆▇█` to easily see if a target is approaching or retreating.
4. **🎭 MAC Randomization Detection**: Checks the IEEE Locally Administered Bit (U/L) to explicitly flag randomized iOS / Android tracking MAC addresses in [Red].
5. **📱 Massive Manufacturer OUI Dictionary**: Built-in definitions resolving vendors (Ubiquiti, Apple, Cisco, Huawei, etc.) on the fly.
6. **📏 Dynamic Distance Estimation**: Live Math computations resolving Free-Space Path Loss (FSPL) using channel frequencies to guess proximity in meters `(~8.4m)`.
7. **🔐 WPS / Encryption Scraper**: Probes the raw Information Elements inside frame beacons to assess and surface exact network security protocols (`WPA2/WPS`).
8. **🦇 Rogue AP / Evil Twin Tracker**: Alerts you natively if multiple MAC addresses broadcast the identical `SSID` with varying encryption headers within a 15-second window.
9. **🕵️ Target Heatmapping & Probes**: Uncovers Hidden SSIDs actively, while tracking specific devices and mapping their previously connected networks via explicit Probe Requests.
10. **🗃 Modular Thread-Safe Architecture**: Rebuilt entirely with `Mutex Locks` handling context injection natively between UI render threads and packet interception threads.

---

## 🛠️ Architecture & Files
- `main.py`: Entry CLI parser and TUI initializer.
- `scanner.py`: Background thread routines for `scapy` deep packet interception.
- `database.py`: Zero-config SQLite schema and connection pooling.
- `ui.py`: Multi-panel, responsive terminal render loop using `rich`.
- `state.py`: Global atomic context dictionary with thread `Lock()`.
- `utils.py`: Distance math, anomaly logic, and OUI resolution.
- `constants.py`: Fixed IEEE definitions and channels.

---

## 📥 Installation

```bash
# Add essential system tracking tools
sudo apt update && sudo apt install aircrack-ng tcpdump python3-pip sqlite3 -y

# Install Python Requirements
pip3 install -r requirements.txt
```

### 1. Enabling Monitor Mode
You must switch your interface to monitor mode before running the software.
```bash
sudo airmon-ng check kill
sudo airmon-ng start wlan0
iwconfig  # Usually assigns to wlan0mon or remains wlan0
```

---

## 🚀 Usage & Deployment

### Show Help Menu & Options
```bash
python3 main.py --help
```

### 1. The Home Guardian (Parental Control)
Track specific family devices and persist everything to the local database.
```bash
sudo python3 main.py -i wlan0mon -w 00:11:22:33:44:55 F4:F5:E8:AA:BB:CC
```

### 2. High-Density Security Audit (Red Team)
Monitor only the 5GHz spectrum, log all frames to PCAP, export final snapshot to JSON, and let the Threat Score algorithm detect MDK4 attacks.
```bash
sudo python3 main.py -i wlan0mon -b 5G --pcap capture.pcap --export result.json
```

### 3. Database Inspecting
Once stopped, explore your retained environment statistics using standard SQL:
```bash
sqlite3 homesync.db "SELECT * FROM security_events;"
sqlite3 homesync.db "SELECT * FROM clients WHERE is_randomized=1;"
```

---

## ⚠️ Known Linux Caveats & Troubleshooting
- **Flickering Data**: High AP count with `python-rich` may cause redraw jitter. Adjust the `refresh_per_second` variable in `main.py` if your terminal emulator is slow.
- **Permission Denied**: `scapy` raw sockets require `sudo`.
- **Sandbox Mode**: For UI testing, running it without `sudo` forces mock data.

---
*Command the spectrum natively through the Linux terminal.*
