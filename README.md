# 🛡️ HomeSync Wi-Fi Sentinel (Advanced Python TUI Edition)
### Professional Parental Monitoring, Security Auditing & Network Surveillance

HomeSync is a high-density Wi-Fi surveillance tool designed strictly as a **Python Terminal User Interface (TUI)**. Built using the `rich` library and `scapy`, it bridges the gap between low-level packet sniffing and professional-grade visual monitoring directly in your terminal. It features deep packet inspection capabilities such as WPA handshake capture notification, Deauth attack detection, target tracking, and real-time visualization.

---

## 📸 TUI Dashboard Highlights & Capabilities
The terminal UI runs directly in your SSH session or local terminal, offering a split-pane "Mission Control" view:
- **📡 Surrounding Networks**: Live, color-coded feed of all Access Points, updated multiple times per second. Tracks connection count via active data-link layer inspection.
- **👨‍👩‍👧 Watchlist & Target Tracking**: A dedicated sidebar to monitor specific family devices or target clients via their MAC addresses to track when they enter or leave the radio bounds.
- **🚫 Hidden Network Detection**: Detects SSIDs that are marked as "Hidden" and automatically de-masks them if a client probes for them.
- **⚠️ Deep Packet Inspection & Security Alerts**: 
  - Detects **EAPOL Handshakes** (WPA/WPA2 4-Way Handshake intercepts).
  - Detects **Deauthentication Packets**, instantly flagging potential "Evil Twin" or DoS attacks.
- **💾 Packet Logging (PCAP)**: Stream raw `802.11` frames to a pcap file for later viewing in Wireshark.
- **📊 Offline Reporting**: Export all discovered networks and their statuses to CSV or JSON upon exit.

---

## 🛠️ System Architecture & Dependencies
This is a 100% Python project.

- **`scapy`**: For intercepting raw `802.11` management, control, and data frames.
- **`rich`**: For the beautiful, lightweight, and hardware-accelerated terminal interface.
- **Root Privileges**: Required to access hardware in monitor mode (`wlan0mon`, `wlp2s0mon`, etc).

---

## 🔌 Hardware Requirements
To capture Wi-Fi activity without being connected to a network, you **MUST** have a Wi-Fi adapter that supports **Monitor Mode** and **Packet Injection**.

### Recommended Chipsets:
- **Atheros AR9271** (Alfa AWUS036NHA) - *Gold standard for Linux*
- **Ralink RT3070** (Alfa AWUS036NH)
- **Realtek RTL8812AU** (Requires specific drivers)
- **Raspberry Pi 3/4/5** (Built-in chip supports monitor mode with `nexmon` patches)

---

## 📥 Installation

Ensure your system is updated and install the required system tools:
```bash
# Add essential system tracking tools
sudo apt update && sudo apt install aircrack-ng tcpdump python3-pip -y

# Install Python Requirements
pip3 install rich scapy
```

### 1. Enabling Monitor Mode
You must switch your interface to monitor mode before running the software.
```bash
# Locate your interface (usually wlan0)
iw dev

# Kill conflicting processes (NetworkManager, wpa_supplicant)
sudo airmon-ng check kill

# Start monitor mode
sudo airmon-ng start wlan0

# Verify interface name (usually wlan0mon or wlan0)
iwconfig
```

---

## 🚀 Usage & Deployment Tools

The `main.py` is equipped with a comprehensive CLI constructed via `argparse`, offering 100% working flags for professional auditing.

### Show Help Menu
Print all available arguments, filters, and features:
```bash
python3 main.py --help
```
*Output snippet:*
```text
options:
  -h, --help            show this help message and exit
  -i INTERFACE, --interface INTERFACE
                        Monitor mode interface to use (default: wlan0mon)
  -w WATCHLIST [WATCHLIST ...], --watchlist WATCHLIST [WATCHLIST ...]
                        List of MAC addresses to track in the Family Watchlist
  -b {2.4G,5G,ALL}, --band {2.4G,5G,ALL}
                        Wi-Fi bands to scan (default: ALL)
  --pcap PCAP           Save all captured packets to a PCAP file
  --export EXPORT       Export discovered APs to a CSV or JSON file on exit
  --demo-mode           Force demo mode even if root (useful for testing UI)
```

### Advanced Examples

**1. Track specific Devices (Parental Control Mode)**
Tracks devices via `-w` flag and uses default band sweeping.
```bash
sudo python3 main.py -i wlan0mon -w 00:11:22:33:44:55 AA:BB:CC:DD:EE:FF
```

**2. Audit Security with PCAP Saving (Red Team Mode)**
Saves everything to `capture.pcap` while detecting handshakes and deauths in the GUI.
```bash
sudo python3 main.py -i wlan0mon --pcap capture.pcap
```

**3. Narrow Band Scanning & Data Export**
Only sweep the `2.4GHz` bands (faster channel cycling) and export the list of APs when exiting (`Ctrl+C`).
```bash
sudo python3 main.py -i wlan0mon -b 2.4G --export my_scan.csv
```

---

## 📡 Advanced Functional Details

### Target Client Association Tracking
The sentinel doesn't just read beacons. It cross-references `Dot11` data frames and Probe Requests (`Dot11ProbeReq`) to build an active set of connected clients for each AP instance in real-time. This feeds the `Clients` column in the dashboard.

### Hidden SSID Detection (De-Masking)
SSIDs are often "hidden" by disabling beacon broadcasting (the SSID field contains null bytes `\x00`). HomeSync de-masks these actively in the terminal:
- It listens for **Probe Requests** from devices that have previously connected to the hidden network.
- It intercepts matching **Probe Responses** from the Access Point to confirm and reveal the network name in [Red] font on the dashboard.

### Security Alert Panel
A dedicated right-hand lower pane reads the raw packets and performs signature checks:
- Any `Dot11Deauth` packet renders an instant alert, highlighting the target MAC.
- Any `EAPOL` frame renders a WPA handshake alert, capturing the key negotiation vectors for the associated devices.

---

## ⚠️ Troubleshooting

- **No Packets Captured**: Ensure the interface is actually in `monitor` mode. Run `iwconfig` to verify. Using `--interface wlan0` will not work if the interface expects `wlan0mon`.
- **Permission Denied**: The script requires raw socket access; always use `sudo`.
- **Channel Hopping Stutter**: The app cycles through 2.4GHz and 5GHz channels continuously. If an AP flickers, it's because it broadcasts on a channel currently not being sniffed. Restrict hopping via `-b 2.4G` if you are only focused on 2.4GHz targets.

## ⚖️ Legal Disclaimer
This tool is intended for **Parental Control, Systems Auditing, and Authorized Personal Property Monitoring** only. Passively monitoring public Wi-Fi is generally legal for security research, but you should never attempt to intercept encrypted traffic or disrupt services without explicit permission from the network owner.

---
*Built tightly with Python 3 and Scapy | Providing visual intelligence for Linux terminal warriors.*
