# 🛡️ HomeSync Wi-Fi Sentinel (Python TUI Edition)
### Professional Parental Monitoring & Network Surveillance Dashboard

HomeSync is a high-density Wi-Fi surveillance tool designed strictly as a **Python Terminal User Interface (TUI)**. Built using the `rich` library and `scapy`, it bridges the gap between low-level packet sniffing and parent-friendly visual monitoring directly in your terminal. It allows you to track household device presence, monitor signal strength (RSSI), and detect hidden SSIDs used by unauthorized access points.

---

## 📸 TUI Dashboard Highlights
The terminal UI runs directly in your SSH session or local terminal, offering a split-pane "Mission Control" view:
- **📡 Surrounding Networks**: Live, color-coded feed of all Access Points, updated multiple times per second. Sorts automatically by signal strength (RSSI).
- **👨‍👩‍👧 Family Watchlist**: A dedicated sidebar to monitor specific family devices (phones, laptops) via their MAC addresses to track when they enter or leave the house.
- **🚫 Hidden Network Detection**: Detects SSIDs that are marked as "Hidden" and automatically de-masks them if a client probes for them.

---

## 🛠️ System Architecture & Dependencies
This is a 100% Python project.

- **`scapy`**: For intercepting raw 802.11 management frames (Beacons, Probes).
- **`rich`**: For the beautiful, lightweight, and hardware-accelerated terminal interface.
- **Root Privileges**: Required to access hardware in monitor mode.

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

Ensure your system is updated and install the required system tools:
```bash
# For Debian/Ubuntu/Pi OS
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

# Verify interface name (usually wlan0mon)
iwconfig
```

### 2. Configure the App
Edit `main.py` and modify the configuration block to suit your needs:
```python
# main.py
INTERFACE = "wlan0mon" # Set this to your monitor interface
watchlist = [
    "00:11:22:33:44:55", # Add your child's phone MAC
    "AA:BB:CC:DD:EE:FF"  # Add family laptop MAC
]
```

### 3. Running the Sentinel
Execute the Python script with root privileges to begin capturing packets and plotting the UI:
```bash
sudo python3 main.py
```
*(Note: If you run it without `sudo`, it will launch in a simulated Sandbox mode to preview the UI design without accessing hardware.)*

---

## 📡 Advanced Functional Details

### Hidden SSID Detection (De-Masking)
SSIDs are often "hidden" by disabling beacon broadcasting (the SSID field contains null bytes `\x00`). HomeSync de-masks these actively in the terminal:
- It listens for **Probe Requests** from devices that have previously connected to the hidden network.
- It intercepts matching **Probe Responses** from the Access Point to confirm and reveal the network name in Red font on the dashboard.

### Parental Control: MAC Tracking Logic
1.  Add the MAC to the **watchlist** array.
2.  **RSSI Thresholds (Proximity Estimation)**: 
    - `-30 to -50 dBm` (Green): The device is likely in the same room.
    - `-50 to -70 dBm` (Yellow): The device is in a neighboring room.
    - `-70 to -85 dBm` (Red): The device is near the edge of the house/yard.
    - `OFFLINE`: The device has left the premises or been turned off (timeout after 30 seconds of no packets).

---

## ⚠️ Troubleshooting
- **No Packets Captured**: Ensure the interface is actually in `monitor` mode. Run `iwconfig` to verify.
- **Permission Denied**: The script requires raw socket access; always use `sudo`.
- **Channel Hopping Stutter**: The app cycles through 2.4GHz and 5GHz channels continuously. If an AP flickers, it's because it broadcasts on a channel currently not being sniffed.

## ⚖️ Legal Disclaimer
This tool is intended for **Parental Control and Authorized Personal Property Monitoring** only. Passively monitoring public Wi-Fi is generally legal for security research, but you should never attempt to intercept encrypted traffic or disrupt services without explicit permission.
