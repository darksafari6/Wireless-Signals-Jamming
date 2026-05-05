import sys
import os
import time
import threading
import subprocess
from datetime import datetime

try:
    from scapy.all import sniff, Dot11Beacon, Dot11ProbeResp, Dot11ProbeReq, Dot11
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
INTERFACE = "wlan0mon"
CHANNELS = [1, 6, 11, 36, 44, 48, 149, 153, 157, 161]

# State
discovered_aps = {}
hidden_ssids = {}
clients_tracked = {}
watchlist = ["00:11:22:33:44:55", "AA:BB:CC:DD:EE:FF"] # Example MACs

console = Console()

def channel_hopper():
    """Cycles through Wi-Fi channels to capture across spectrum."""
    while True:
        for channel in CHANNELS:
            try:
                subprocess.run(["iw", "dev", INTERFACE, "set", "channel", str(channel)], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                time.sleep(2)
            except Exception:
                time.sleep(1)

def packet_handler(pkt):
    """Processes captured 802.11 management frames."""
    now = time.time()
    
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

        discovered_aps[bssid] = {
            "ssid": ssid,
            "mac": bssid,
            "rssi": rssi,
            "channel": channel,
            "hidden": is_hidden,
            "last_seen": now
        }

    elif pkt.haslayer(Dot11ProbeResp):
        bssid = pkt.addr2
        ssid = pkt.info.decode(errors='ignore') if pkt.info else ""
        if ssid:
            hidden_ssids[bssid] = ssid
            if bssid in discovered_aps:
                discovered_aps[bssid]["ssid"] = ssid
                discovered_aps[bssid]["hidden"] = False

    elif pkt.haslayer(Dot11ProbeReq) or pkt.haslayer(Dot11):
        client_mac = pkt.addr2
        if client_mac and client_mac != "ff:ff:ff:ff:ff:ff":
            rssi = pkt.dBm_AntSignal if hasattr(pkt, 'dBm_AntSignal') else -100
            clients_tracked[client_mac] = {
                "mac": client_mac,
                "rssi": rssi,
                "last_seen": now
            }

def get_rssi_color(rssi):
    if rssi >= -50: return "bold green"
    if rssi >= -70: return "bold yellow"
    return "bold red"

def generate_ui():
    """Generates the Rich layout for the terminal."""
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="body")
    )
    layout["body"].split_row(
        Layout(name="networks", ratio=2),
        Layout(name="watchlist", ratio=1)
    )

    # Header
    header_text = Text(f"🛡️  HomeSync Wi-Fi Sentinel | Interface: {INTERFACE} | Time: {datetime.now().strftime('%H:%M:%S')}", style="bold cyan")
    layout["header"].update(Panel(Align.center(header_text), style="blue", border_style="blue"))

    # Networks Table
    ap_table = Table(expand=True, show_edge=False, show_header=True, header_style="bold magenta")
    ap_table.add_column("SSID", style="cyan", no_wrap=True)
    ap_table.add_column("BSSID", style="dim white")
    ap_table.add_column("CH", justify="right", style="yellow")
    ap_table.add_column("RSSI", justify="right")
    ap_table.add_column("Status", justify="center")

    now = time.time()
    # Sort APs by RSSI
    sorted_aps = sorted(discovered_aps.values(), key=lambda x: x['rssi'], reverse=True)[:25]
    for ap in sorted_aps:
        if now - ap["last_seen"] > 60: continue # Hide old ones
        
        ssid_display = f"[bold red]{ap['ssid']}[/bold red]" if ap['hidden'] else ap['ssid']
        rssi_style = get_rssi_color(ap['rssi'])
        status = "[bold red]HIDDEN[/bold red]" if ap['hidden'] else "[green]VISIBLE[/green]"
        
        ap_table.add_row(
            ssid_display,
            ap['mac'],
            str(ap.get('channel', '?')),
            f"[{rssi_style}]{ap['rssi']} dBm[/{rssi_style}]",
            status
        )

    layout["networks"].update(Panel(ap_table, title="📡 Surrounding Networks", border_style="cyan"))

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
                watch_table.add_row(mac, "[dim]---[/dim]", "○ [bold red]OFFLINE[/bold red]")
        else:
            watch_table.add_row(mac, "[dim]---[/dim]", "[dim]NOT SEEN[/dim]")

    layout["watchlist"].update(Panel(watch_table, title="👨‍👩‍👧 Family Watchlist", border_style="yellow"))
    
    return layout

def mock_data():
    """Generates fake data for demonstration when running without root/interface."""
    import random
    discovered_aps["11:22:33:44:55:66"] = {"ssid": "SkyNet_5G", "mac": "11:22:33:44:55:66", "rssi": -45, "channel": 36, "hidden": False, "last_seen": time.time()}
    discovered_aps["AA:BB:CC:DD:EE:FF"] = {"ssid": "[HIDDEN]", "mac": "AA:BB:CC:DD:EE:FF", "rssi": -75, "channel": 11, "hidden": True, "last_seen": time.time()}
    discovered_aps["DE:AD:BE:EF:00:11"] = {"ssid": "CoffeeShop_Guest", "mac": "DE:AD:BE:EF:00:11", "rssi": -85, "channel": 6, "hidden": False, "last_seen": time.time()}
    discovered_aps["99:88:77:66:55:44"] = {"ssid": "HomeNetwork", "mac": "99:88:77:66:55:44", "rssi": -52, "channel": 1, "hidden": False, "last_seen": time.time()}
    
    clients_tracked["00:11:22:33:44:55"] = {"mac": "00:11:22:33:44:55", "rssi": -55, "last_seen": time.time()}

def main():
    # If not running as root, we drop into Demo Mode
    is_root = (os.name == 'posix' and os.getuid() == 0)
    
    if not is_root:
        console.print("[bold yellow][!] Running in MOCK/DEMO mode (Not Root / No Interface).[/bold yellow]")
        console.print("[dim]For actual live sniffing, run with: sudo python3 main.py[/dim]")
        time.sleep(2)
        mock_data()
    else:
        # Start Channel Hopping Thread
        threading.Thread(target=channel_hopper, daemon=True).start()

        # Start Sniffing
        threading.Thread(target=lambda: sniff(iface=INTERFACE, prn=packet_handler, store=0), daemon=True).start()

    with Live(generate_ui(), refresh_per_second=2, screen=True) as live:
        try:
            while True:
                time.sleep(0.5)
                # Animate mock data randomly if in mock mode
                if not is_root:
                    import random
                    if "11:22:33:44:55:66" in discovered_aps: 
                        discovered_aps["11:22:33:44:55:66"]["rssi"] = random.randint(-60, -40)
                        discovered_aps["11:22:33:44:55:66"]["last_seen"] = time.time()
                    if "00:11:22:33:44:55" in clients_tracked:
                        if random.random() > 0.1: # 90% chance to stay online
                            clients_tracked["00:11:22:33:44:55"]["rssi"] = random.randint(-80, -50)
                            clients_tracked["00:11:22:33:44:55"]["last_seen"] = time.time()
                
                live.update(generate_ui())
        except KeyboardInterrupt:
            console.print("[bold red]Shutting down Sentinel...[/bold red]")
            sys.exit(0)

if __name__ == "__main__":
    main()
