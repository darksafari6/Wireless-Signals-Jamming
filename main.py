import sys
import os
import time
import json
import threading
import argparse
import csv
from datetime import datetime

from state import state
from ui import generate_ui, console
from scanner import channel_hopper, packet_handler, threat_decay_loop
from constants import CHANNELS_2G, CHANNELS_5G, DEFAULT_CHANNELS
from utils import estimate_distance, get_freq_from_channel, is_mac_randomized

try:
    from scapy.all import sniff
    from rich.live import Live
except ImportError:
    print("[!] 'scapy' or 'rich' library is required. Install them.")
    sys.exit(1)

def setup_args():
    parser = argparse.ArgumentParser(
        description="🛡️ HomeSync Wi-Fi Sentinel - Professional TUI Network Monitor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-i", "--interface", default="wlan0mon", help="Monitor mode interface")
    parser.add_argument("-w", "--watchlist", nargs='+', default=[], help="MACs to track")
    parser.add_argument("-b", "--band", choices=['2.4G', '5G', 'ALL'], default='ALL')
    parser.add_argument("--pcap", type=str, help="Save to PCAP")
    parser.add_argument("--export", type=str, help="Export APs to CSV/JSON")
    parser.add_argument("--demo-mode", action="store_true", help="Force demo mode")
    return parser.parse_args()

def mock_data():
    import random
    with state.lock:
        state.discovered_aps["11:22:33:44:55:66"] = {"ssid": "SkyNet_5G", "mac": "11:22:33:44:55:66", "rssi": [-45], "channel": 36, "hidden": False, "last_seen": time.time(), "clients": {"aa"}, "crypto": ["WPA2"], "wps": True, "vendor": "Asus", "data_frames": 102}
        state.discovered_aps["AA:BB:CC:DD:EE:FF"] = {"ssid": "[HIDDEN]", "mac": "AA:BB:CC:DD:EE:FF", "rssi": [-75], "channel": 11, "hidden": True, "last_seen": time.time(), "clients": set(), "crypto": ["WEP"], "wps": False, "vendor": "Unknown", "data_frames": 10}
        state.clients_tracked["00:11:22:33:44:55"] = {"mac": "00:11:22:33:44:55", "rssi": [-55], "last_seen": time.time(), "probes": {"FreeWifi", "HomeNet"}, "is_randomized": False}
        state.clients_tracked["22:4E:AA:BB:11:22"] = {"mac": "22:4E:AA:BB:11:22", "rssi": [-65], "last_seen": time.time(), "probes": {"Cafe"}, "is_randomized": True}
        
    state.log_alert("BEACON FLOOD", "Denial of Service attack detected!", db_write=False)
    state.log_alert("ROGUE AP", "Multiple origins for 'SkyNet_5G'", db_write=False)
    state.log_alert("WPA HANDSHAKE (EAPOL)", "Captured for 11:22", db_write=False)

def export_results(filepath):
    print(f"[*] Exporting results to {filepath}")
    ext = filepath.split('.')[-1].lower()
    
    with state.lock:
        data = [{
            "MAC": ap["mac"], 
            "SSID": ap["ssid"], 
            "Dist_Meters": estimate_distance(ap["rssi"][-1] if ap["rssi"] else -100, get_freq_from_channel(ap.get("channel", 2412))), 
            "Crypto": "/".join(ap["crypto"]), 
            "WPS": ap["wps"],
            "Clients": len(ap.get("clients", []))
        } for ap in state.discovered_aps.values()]
        
    try:
        if ext == 'csv':
            with open(filepath, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=["MAC", "SSID", "Dist_Meters", "Crypto", "WPS", "Clients"])
                writer.writeheader()
                writer.writerows(data)
        else: # JSON
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=4)
        print(f"[+] Successfully exported to {filepath}")
    except Exception as e:
        print(f"[-] Export failed: {e}")

def main():
    args = setup_args()
    channels = CHANNELS_2G if args.band == '2.4G' else CHANNELS_5G if args.band == '5G' else DEFAULT_CHANNELS
    
    if args.pcap:
        try:
            from scapy.all import PcapWriter
            state.pcap_writer = PcapWriter(args.pcap, append=True, sync=True)
            print(f"[*] PCAP logging enabled: {args.pcap}")
        except Exception as e: print(f"[-] PCAP error: {e}")

    with state.lock:
        for mac in args.watchlist: 
            state.clients_tracked[mac] = {
                "mac": mac, "rssi": [], "last_seen": 0, "probes": set(),
                "is_randomized": is_mac_randomized(mac)
            }

    is_root = (os.name == 'posix' and os.getuid() == 0)
    if args.demo_mode or not is_root:
        console.print("[bold yellow][!] Running in DEMO mode (Mock Data).[/bold yellow]")
        if not args.watchlist:
            args.watchlist.extend(["00:11:22:33:44:55", "22:4E:AA:BB:11:22"])
            with state.lock:
                state.clients_tracked["00:11:22:33:44:55"] = {"mac": "00:11:22:33:44:55", "rssi": [-100], "last_seen": 0, "probes": set(), "is_randomized": False}
                state.clients_tracked["22:4E:AA:BB:11:22"] = {"mac": "22:4E:AA:BB:11:22", "rssi": [-100], "last_seen": 0, "probes": set(), "is_randomized": True}
        time.sleep(2)
        mock_data()
    else:
        threading.Thread(target=channel_hopper, args=(args.interface, channels), daemon=True).start()
        threading.Thread(target=lambda: sniff(iface=args.interface, prn=packet_handler, store=0), daemon=True).start()
        
    threading.Thread(target=threat_decay_loop, daemon=True).start()

    with Live(generate_ui(args.interface, args.watchlist), refresh_per_second=2, screen=True) as live:
        try:
            while True:
                time.sleep(0.5)
                if args.demo_mode or not is_root:
                    import random
                    with state.lock:
                        if "11:22:33:44:55:66" in state.discovered_aps: 
                            state.discovered_aps["11:22:33:44:55:66"]["rssi"].append(random.randint(-60, -40))
                            if len(state.discovered_aps["11:22:33:44:55:66"]["rssi"]) > 20: state.discovered_aps["11:22:33:44:55:66"]["rssi"].pop(0)
                            state.discovered_aps["11:22:33:44:55:66"]["last_seen"] = time.time()
                            
                        if "00:11:22:33:44:55" in args.watchlist and random.random() > 0.1: 
                            state.clients_tracked["00:11:22:33:44:55"]["rssi"].append(random.randint(-80, -50))
                            if len(state.clients_tracked["00:11:22:33:44:55"]["rssi"]) > 20: state.clients_tracked["00:11:22:33:44:55"]["rssi"].pop(0)
                            state.clients_tracked["00:11:22:33:44:55"]["last_seen"] = time.time()
                
                live.update(generate_ui(args.interface, args.watchlist))
        except KeyboardInterrupt: pass

    console.print(f"\n[bold red]Shutting down HomeSync Sentinel...[/bold red]")
    if args.export: export_results(args.export)
    if state.pcap_writer: state.pcap_writer.close()
    sys.exit(0)

if __name__ == "__main__":
    main()
