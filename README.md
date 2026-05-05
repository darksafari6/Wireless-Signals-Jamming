# HomeSync Wi-Fi Monitor

A real-time Wi-Fi surveillance and parental control dashboard.

## 🚀 Overview
HomeSync is designed to provide a "Mission Control" view of your home network environment. It monitors beacon frames, detects hidden SSIDs (via probe analysis), and tracks the presence of specific family devices based on MAC addresses and signal strength (RSSI).

## 🛠 Features
- **Live Monitoring**: Real-time WebSocket stream of surrounding Wi-Fi activity.
- **Parental Control**: Track when specific devices (phones, laptops) enter or leave the home range.
- **Security Alerts**: Visual notification when hidden SSIDs or unusual network patterns are detected.
- **Signal Tracking**: Color-coded RSSI levels to gauge device proximity.

## 🔌 Hardware Integration (The Linux "Bridge")
To use this with real antenna data (scapy/aircrack-ng) on a Linux system, use the following Python snippet to pipe data to the server:

```python
# sensor.py
from scapy.all import *
import websocket # pip install websocket-client
import json

# Replace with your App URL
WS_URL = "ws://your-app-url:3000"

def packet_handler(pkt):
    if pkt.haslayer(Dot11Beacon):
        data = {
            "type": "wifi_update",
            "data": [{
                "ssid": pkt.info.decode(),
                "mac": pkt.addr2,
                "rssi": pkt.dBm_AntSignal,
                "type": "AP"
            }]
        }
        # Send to web dashboard
        # ws.send(json.dumps(data))

# Run on monitor-mode interface
# sniff(iface="wlan0mon", prn=packet_handler)
```

## 📦 Dependencies
- **Frontend**: Angular 21, Tailwind CSS 4, Lucide Icons, Angular Material.
- **Backend**: Node.js, Express, WS (WebSockets).
- **External (Recommended)**: Scapy, Aircrack-ng (for monitor mode data capture).

## 📖 Deployment
1. The app is pre-configured to run on port 3000.
2. The UI is built using a "Technical Dashboard" design language.
3. Use the **Watchlist** to add specific devices for tracking.
