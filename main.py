import sys
import os
import time
import json
import threading
import subprocess
import argparse
import csv
from datetime import datetime

try:
    from scapy.all import sniff, wrpcap, Dot11Beacon, Dot11ProbeResp, Dot11ProbeReq, Dot11, Dot11Deauth, EAPOL
except ImportError:
    print("[!] 'scapy' library is required. Install it using: pip install scapy")
    sys.exit(1)

try:
    from rich.live import Live
    from rich.table import Table
    from rich.layout import Layout
    from rich.panel import Panel
    from rich.console import Console
    from rich.text import Text
    from rich.align import Align
except ImportError:
    print("[!] 'rich' library is required. Install it using: pip install rich")
    sys.exit(1)

# CONFIGURATION
CHANNELS_2G = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]
CHANNELS_5G = [36, 40, 44, 48, 149, 153, 157, 161, 165]
DEFAULT_CHANNELS = [1, 6, 11, 36, 44, 48, 149, 153, 157, 161]

# State
discovered_aps = {}
hidden_ssids = {}
clients_tracked = {}
security_alerts = []
pcap_writer = None

console = Console()

def setup_args():
    parser = argparse.ArgumentParser(
        description="🛡️ HomeSync Wi-Fi Sentinel - Professional TUI Network Monitor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  sudo python3 main.py -i wlan0mon
  sudo python3 main.py -i wlan0mon --watchlist 00:11:22:33:44:55 AA:BB:CC:DD:EE:FF
  sudo python3 main.py -i wlan0mon --band 2.4G --pcap capture.pcap --export aps.csv
        """
    )
    parser.add_argument("-i", "--interface", default="wlan0mon", help="Monitor mode interface to use (default: wlan0mon)")
    parser.add_argument("-w", "--watchlist", nargs='+', default=[], help="List of MAC addresses to track in the Family Watchlist")
    parser.add_argument("-b", "--band", choices=['2.4G', '5G', 'ALL'], default='ALL', help="Wi-Fi bands to scan (default: ALL)")
    parser.add_argument("--pcap", type=str, help="Save all captured packets to a PCAP file")
    parser.add_argument("--export", type=str, help="Export discovered APs to a CSV or JSON file on exit")
    parser.add_argument("--demo-mode", action="store_true", help="Force demo mode even if root (useful for testing UI)")
    
    return parser.parse_args()

def channel_hopper(interface, channels):
    """Cycles through Wi-Fi channels to capture across spectrum."""
    while True:
        for channel in channels:
            try:
                subprocess.run(["iw", "dev", interface, "set", "channel", str(channel)], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                time.sleep(1)
            except Exception:
                time.sleep(1)

def log_alert(alert_type, message):
    timestamp = datetime.now().strftime('%H:%M:%S')
    security_alerts.insert(0, f"[{timestamp}] [bold red]{alert_type}[/bold red]: {message}")
    if len(security_alerts) > 10:
        security_alerts.pop()

def packet_handler(pkt):
    """Processes captured 802.11 management/data frames."""
    now = time.time()
    
    if pcap_writer:
        pcap_writer.write(pkt)

    if pkt.haslayer(Dot11Beacon):
        bssid = pkt.addr2
        ssid = pkt.info.decode(errors='ignore') if pkt.info else ""
        stats = pkt.getlayer(Dot11Beacon).network_stats()
        channel = stats.get('channel')
        rssi = pkt.dBm_AntSignal if hasattr(pkt, 'dBm_AntSignal') else -100
        
        is_hidden = False
        if not ssid or ssid == "\x00" * len(ssid):
            is_hidden = True
            ssid = hidden_ssids.get(bssid, "[HIDDEN]")

        if bssid not in discovered_aps:
            discovered_aps[bssid] = {"ssid": ssid, "mac": bssid, "rssi": rssi, "channel": channel, "hidden": is_hidden, "last_seen": now, "clients": set(), "beacon_count": 1}
        else:
            discovered_aps[bssid]["rssi"] = rssi
            discovered_aps[bssid]["last_seen"] = now
            discovered_aps[bssid]["beacon_count"] += 1
            if ssid and ssid != "[HIDDEN]":
                discovered_aps[bssid]["ssid"] = ssid
                discovered_aps[bssid]["hidden"] = False

    elif pkt.haslayer(Dot11ProbeResp):
        bssid = pkt.addr2
        ssid = pkt.info.decode(errors='ignore') if pkt.info else ""
        if ssid and bssid:
            hidden_ssids[bssid] = ssid
            if bssid in discovered_aps:
                discovered_aps[bssid]["ssid"] = ssid
                discovered_aps[bssid]["hidden"] = False

    elif pkt.haslayer(Dot11Deauth):
        log_alert("DEAUTH DETECTED", f"{pkt.addr2} -> {pkt.addr1}")

    elif pkt.haslayer(EAPOL):
        log_alert("WPA HANDSHAKE (EAPOL)", f"Captured for {pkt.addr2}")

    elif pkt.haslayer(Dot11ProbeReq) or pkt.haslayer(Dot11):
        client_mac = pkt.addr2
        ap_mac = pkt.addr1
        if client_mac and client_mac != "ff:ff:ff:ff:ff:ff" and not pkt.haslayer(Dot11Beacon):
            rssi = pkt.dBm_AntSignal if hasattr(pkt, 'dBm_AntSignal') else -100
            
            if client_mac in clients_tracked:
                clients_tracked[client_mac]["rssi"] = rssi
                clients_tracked[client_mac]["last_seen"] = now
            
            if ap_mac in discovered_aps and client_mac:
                 discovered_aps[ap_mac]["clients"].add(client_mac)
            if client_mac in discovered_aps and ap_mac:
                 discovered_aps[client_mac]["clients"].add(ap_mac)

def get_rssi_color(rssi):
    if rssi >= -50: return "bold green"
    if rssi >= -70: return "bold yellow"
    return "bold red"

def generate_ui(interface, watchlist):
    """Generates the Rich layout for the terminal."""
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="main", ratio=1)
    )
    layout["main"].split_row(
        Layout(name="networks", ratio=2),
        Layout(name="sidebar", ratio=1)
    )
    layout["sidebar"].split_column(
        Layout(name="watchlist", ratio=1),
        Layout(name="alerts", ratio=1)
    )

    # Header
    total_aps = len(discovered_aps)
    header_text = Text(f"🛡️  HomeSync Sentinel | IF: {interface} | APs: {total_aps} | Time: {datetime.now().strftime('%H:%M:%S')}", style="bold cyan")
    layout["header"].update(Panel(Align.center(header_text), style="blue", border_style="blue"))

    # Networks Table
    ap_table = Table(expand=True, show_edge=False, show_header=True, header_style="bold magenta")
    ap_table.add_column("SSID", style="cyan", no_wrap=True)
    ap_table.add_column("BSSID", style="dim white")
    ap_table.add_column("CH", justify="right", style="yellow")
    ap_table.add_column("RSSI", justify="right")
    ap_table.add_column("Clients", justify="right", style="green")
    ap_table.add_column("Status", justify="center")

    now = time.time()
    sorted_aps = sorted(discovered_aps.values(), key=lambda x: x['rssi'], reverse=True)[:20]
    for ap in sorted_aps:
        if now - ap["last_seen"] > 60: continue
        
        ssid_display = f"[bold red]{ap['ssid']}[/bold red]" if ap['hidden'] else ap['ssid']
        rssi_style = get_rssi_color(ap['rssi'])
        status = "[bold red]HIDDEN[/bold red]" if ap['hidden'] else "[green]VISIBLE[/green]"
        client_count = len(ap.get("clients", []))
        
        ap_table.add_row(
            ssid_display,
            ap['mac'],
            str(ap.get('channel', '?')),
            f"[{rssi_style}]{ap['rssi']} dBm[/{rssi_style}]",
            str(client_count),
            status
        )

    layout["networks"].update(Panel(ap_table, title="📡 Active Access Points", border_style="cyan"))

    # Watchlist Table
    watch_table = Table(expand=True, show_edge=False, header_style="bold magenta")
    watch_table.add_column("MAC Address", style="white")
    watch_table.add_column("RSSI", justify="right")
    watch_table.add_column("Status", justify="center")

    for mac in watchlist:
        if mac in clients_tracked:
            client = clients_tracked[mac]
            if now - client["last_seen"] < 30:
                rssi_style = get_rssi_color(client['rssi'])
                watch_table.add_row(
                    mac,
                    f"[{rssi_style}]{client['rssi']} dBm[/{rssi_style}]",
                    "● [bold green]ONLINE[/bold green]"
                )
            else:
                watch_table.add_row(mac, "[dim]---[/dim]", "○ [bold yellow]AWAY[/bold yellow]")
        else:
            watch_table.add_row(mac, "[dim]---[/dim]", "[dim]NOT SEEN[/dim]")

    layout["watchlist"].update(Panel(watch_table, title="👨‍👩‍👧 Family Watchlist", border_style="yellow"))

    # Alerts Panel
    alerts_text = "\n".join(security_alerts) if security_alerts else "[dim]No recent alerts.[/dim]"
    layout["alerts"].update(Panel(alerts_text, title="⚠️ Security Events", border_style="red"))
    
    return layout

def mock_data():
    """Generates fake data for demonstration."""
    import random
    discovered_aps["11:22:33:44:55:66"] = {"ssid": "SkyNet_5G", "mac": "11:22:33:44:55:66", "rssi": -45, "channel": 36, "hidden": False, "last_seen": time.time(), "clients": {"aa","bb"}}
    discovered_aps["AA:BB:CC:DD:EE:FF"] = {"ssid": "[HIDDEN]", "mac": "AA:BB:CC:DD:EE:FF", "rssi": -75, "channel": 11, "hidden": True, "last_seen": time.time(), "clients": set()}
    discovered_aps["DE:AD:BE:EF:00:11"] = {"ssid": "CoffeeShop_Guest", "mac": "DE:AD:BE:EF:00:11", "rssi": -85, "channel": 6, "hidden": False, "last_seen": time.time(), "clients": {"cc"}}
    
    clients_tracked["00:11:22:33:44:55"] = {"mac": "00:11:22:33:44:55", "rssi": -55, "last_seen": time.time()}

def export_results(filepath):
    print(f"[*] Exporting results to {filepath}")
    ext = filepath.split('.')[-1].lower()
    
    data = []
    for mac, ap in discovered_aps.items():
        data.append({
            "MAC": ap["mac"],
            "SSID": ap["ssid"],
            "Channel": ap.get("channel", "N/A"),
            "Last_RSSI": ap["rssi"],
            "Hidden": ap["hidden"],
            "Client_Count": len(ap.get("clients", []))
        })
        
    try:
        if ext == 'csv':
            with open(filepath, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=["MAC", "SSID", "Channel", "Last_RSSI", "Hidden", "Client_Count"])
                writer.writeheader()
                writer.writerows(data)
        else: # default json
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=4)
        print(f"[+] Successfully exported to {filepath}")
    except Exception as e:
        print(f"[-] Export failed: {e}")

def main():
    args = setup_args()
    
    if args.band == '2.4G':
        channels = CHANNELS_2G
    elif args.band == '5G':
        channels = CHANNELS_5G
    else:
        channels = DEFAULT_CHANNELS

    global pcap_writer
    if args.pcap:
        try:
            from scapy.all import PcapWriter
            pcap_writer = PcapWriter(args.pcap, append=True, sync=True)
            print(f"[*] PCAP logging enabled: {args.pcap}")
        except Exception as e:
            print(f"[-] Failed to setup PCAP writer: {e}")

    for mac in args.watchlist:
        clients_tracked[mac] = {"mac": mac, "rssi": -100, "last_seen": 0}

    is_root = (os.name == 'posix' and os.getuid() == 0)
    
    if args.demo_mode or not is_root:
        console.print("[bold yellow][!] Running in DEMO mode (Mock Data).[/bold yellow]")
        if not is_root:
             console.print("[dim]For actual live sniffing, run with: sudo python3 main.py[/dim]")
        # Setup mock watchlist
        if not args.watchlist:
            args.watchlist.append("00:11:22:33:44:55")
            clients_tracked["00:11:22:33:44:55"] = {"mac": "00:11:22:33:44:55", "rssi": -100, "last_seen": 0}
        time.sleep(2)
        mock_data()
    else:
        threading.Thread(target=channel_hopper, args=(args.interface, channels), daemon=True).start()
        threading.Thread(target=lambda: sniff(iface=args.interface, prn=packet_handler, store=0), daemon=True).start()

    with Live(generate_ui(args.interface, args.watchlist), refresh_per_second=2, screen=True) as live:
        try:
            while True:
                time.sleep(0.5)
                if args.demo_mode or not is_root:
                    import random
                    if "11:22:33:44:55:66" in discovered_aps: 
                        discovered_aps["11:22:33:44:55:66"]["rssi"] = random.randint(-60, -40)
                        discovered_aps["11:22:33:44:55:66"]["last_seen"] = time.time()
                    if "00:11:22:33:44:55" in args.watchlist:
                        if random.random() > 0.1: 
                            clients_tracked["00:11:22:33:44:55"]["rssi"] = random.randint(-80, -50)
                            clients_tracked["00:11:22:33:44:55"]["last_seen"] = time.time()
                    if random.random() > 0.95:
                        log_alert("SIMULATED DEAUTH", "AA:BB:CC -> DE:AD:BE")
                
                live.update(generate_ui(args.interface, args.watchlist))
        except KeyboardInterrupt:
            # Cleanup and exit cleanly
            pass

    console.print(f"\n[bold red]Shutting down HomeSync Sentinel...[/bold red]")
    if args.export:
        export_results(args.export)
    if pcap_writer:
        pcap_writer.close()
    sys.exit(0)

if __name__ == "__main__":
    main()
