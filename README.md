# 🛡️ HomeSync Wi-Fi Sentinel
### Professional Parental Monitoring & Network Surveillance Dashboard

HomeSync is a high-density Wi-Fi surveillance tool designed for **Linux (BlackArch, Kali, Raspberry Pi OS)**. It bridges the gap between low-level packet sniffing and parent-friendly visual monitoring. It allows you to track household device presence, monitor signal strength (RSSI), and detect hidden SSIDs used by unauthorized access points.

---

## 🛠️ System Architecture
The project operates in two layers:
1.  **The Engine (Python/Scapy)**: A backend script running in `monitor mode` that captures raw 802.11 management frames.
2.  **The Interface (Angular/Node.js)**: A high-density "Mission Control" dashboard that visualizes network activity and device tracks.

---

## 🔌 Hardware Requirements
To capture Wi-Fi activity without being connected to a network, you **MUST** have a Wi-Fi adapter that supports **Monitor Mode** and **Packet Injection**.

### Recommended Chipsets:
- **Atheros AR9271** (Alfa AWUS036NHA) - *Gold standard for Linux*
- **Ralink RT3070** (Alfa AWUS036NH)
- **Realtek RTL8812AU** (Requires specific drivers)
- **Raspberry Pi 3/4/5** (Built-in chip supports monitor mode with `nexmon` patches)

---

## 📥 Installation & Setup

### 1. Preparing the Linux System
Ensure your system is updated and install the required tools:
```bash
# For Debian/Ubuntu/Pi OS
sudo apt update && sudo apt install aircrack-ng tcpdump python3-scapy -y

# For BlackArch/Arch Linux
sudo pacman -S aircrack-ng tcpdump python-scapy
```

### 2. Enabling Monitor Mode
You must switch your interface to monitor mode before running the software.
```bash
# Locate your interface (usually wlan0)
iw dev

# Kill conflicting processes
sudo airmon-ng check kill

# Start monitor mode
sudo airmon-ng start wlan0

# Verify interface name (usually wlan0mon)
iwconfig
```

### 3. Deploying the Dashboard
The dashboard provides the visual "Watchlist" and live log feed.
```bash
# Install Node.js dependencies
npm install

# Build the Angular application
npm run build

# Start the server
npm run start
```

### 4. Running the Sniffer
Execute the Python script with root privileges to begin capturing packets:
```bash
sudo python3 sentinel.py
```

---

## 📡 Advanced Features

### Hidden SSID Detection
SSIDs are often "hidden" by disabling beacon broadcasting. HomeSync de-masks these by:
- Listening for **Probe Requests** from devices that have previously connected to the hidden network.
- Capturing **Probe Responses** from the Access Point to confirm the network name.

### Parental Control: MAC Tracking
1.  Locate your child's phone/laptop MAC address in the "Surrounding Networks" table.
2.  Add the MAC to the **Family Watchlist** on the sidebar.
3.  **RSSI Thresholds**: 
    - `-30 to -50 dBm`: The device is likely in the same room.
    - `-70 to -85 dBm`: The device is near the edge of the house/yard.
    - `Offline`: The device has left the premises or been turned off.

---

## ⚠️ Troubleshooting
- **No Packets Captured**: Ensure the interface is actually in `monitor` mode (Run `iwconfig`).
- **Permission Denied**: Python script `sentinel.py` requires raw socket access; always use `sudo`.
- **Channel Issues**: If capturing is slow, ensure `sentinel.py` is hopping across both 2.4GHz and 5GHz channels.

## ⚖️ Legal Disclaimer
This tool is intended for **Parental Control and Authorized Personal Property Monitoring** only. Passively monitoring public Wi-Fi is generally legal for security research, but you should never attempt to intercept encrypted traffic or disrupt services (jamming) without explicit permission.

---
*Built with Angular 21, Python 3, and Scapy | Designed for Modern Linux Security Distributions.*
