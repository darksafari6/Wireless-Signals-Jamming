import sys
import os
import time
import json
import threading
import subprocess
from scapy.all import *

# CONFIGURATION
INTERFACE = "wlan0mon"  # Your monitor mode interface
CHANNELS = [1, 6, 11, 36, 44, 48, 149, 153, 157, 161] # 2.4GHz and 5GHz
DASHBOARD_URL = "http://localhost:3000/api/wifi-update" # Or use WebSockets

# State tracking
discovered_aps = {}
hidden_ssids = {} # Map BSSID to resolved SSID from Probes

def channel_hopper():
    """Cycles through Wi-Fi channels to capture across spectrum."""
    while True:
        for channel in CHANNELS:
            try:
                subprocess.run(["iw", "dev", INTERFACE, "set", "channel", str(channel)], check=True)
                time.sleep(2) # Stay on channel for 2 seconds
            except Exception as e:
                print(f"[!] Error switching to channel {channel}: {e}")

def packet_handler(pkt):
    """Processes captured 802.11 management frames."""
    
    # 1. Access Point Detection (Beacon Frames)
    if pkt.haslayer(Dot11Beacon):
        bssid = pkt.addr2
        ssid = pkt.info.decode(errors='ignore')
        stats = pkt.getlayer(Dot11Beacon).network_stats()
        channel = stats.get('channel')
        rssi = pkt.dBm_AntSignal if hasattr(pkt, 'dBm_AntSignal') else -100
        
        is_hidden = False
        if not ssid or ssid == "\x00" * len(ssid):
            is_hidden = True
            ssid = hidden_ssids.get(bssid, "[HIDDEN]")

        discovered_aps[bssid] = {
            "ssid": ssid,
            "mac": bssid,
            "rssi": rssi,
            "channel": channel,
            "hidden": is_hidden,
            "type": "AP",
            "timestamp": time.time()
        }

    # 2. Hidden SSID De-masking (Probe Responses)
    elif pkt.haslayer(Dot11ProbeResp):
        bssid = pkt.addr2
        ssid = pkt.info.decode(errors='ignore')
        if ssid:
            hidden_ssids[bssid] = ssid
            if bssid in discovered_aps:
                discovered_aps[bssid]["ssid"] = ssid
                discovered_aps[bssid]["hidden"] = False

    # 3. Client Device Tracking (Probe Requests / Data Frames)
    elif pkt.haslayer(Dot11ProbeReq) or pkt.haslayer(Dot11):
        client_mac = pkt.addr2
        # Filter out multi-cast/broadcast and APs
        if client_mac and client_mac != "ff:ff:ff:ff:ff:ff":
            rssi = pkt.dBm_AntSignal if hasattr(pkt, 'dBm_AntSignal') else -100
            # Track as client
            discovered_aps[client_mac] = {
                "mac": client_mac,
                "rssi": rssi,
                "type": "Client",
                "timestamp": time.time()
            }

def main():
    if os.getuid() != 0:
        print("[!] Script must be run as root (sudo)")
        sys.exit(1)

    print(f"[*] Starting Wi-Fi Sentinel on {INTERFACE}...")
    print(f"[*] Monitoring Channels: {CHANNELS}")

    # Start Channel Hopping Thread
    threading.Thread(target=channel_hopper, daemon=True).start()

    # Start Sniffing
    try:
        sniff(iface=INTERFACE, prn=packet_handler, store=0)
    except KeyboardInterrupt:
        print("\n[*] Shutting down...")
        sys.exit(0)

if __name__ == "__main__":
    main()
