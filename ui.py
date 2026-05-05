from rich.live import Live
from rich.table import Table
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from rich.console import Console

from state import state
from utils import resolve_oui, get_rssi_color, estimate_distance, get_freq_from_channel, generate_sparkline, is_mac_randomized
from datetime import datetime
import time

console = Console()

def generate_ui(interface, watchlist):
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="main", ratio=1)
    )
    
    # 3-column layout
    layout["main"].split_row(
        Layout(name="networks", ratio=4),
        Layout(name="sidebar", ratio=2),
        Layout(name="alerts_panel", ratio=2)
    )
    
    layout["sidebar"].split_column(
        Layout(name="watchlist", ratio=1),
        Layout(name="telemetry", size=8)
    )

    with state.lock:
        ap_count = len(state.discovered_aps)
        client_count = len(state.clients_tracked)
        nas = state.nas_score

    # -- HEADER --
    header_col = "red" if nas > 50 else ("yellow" if nas > 20 else "bold cyan")
    header_text = Text(f"🛡️ HomeSync Sentinel 2.0 | IF: {interface} | Threat Score: {nas}/100 | Time: {datetime.now().strftime('%H:%M:%S')}", style=header_col)
    layout["header"].update(Panel(Align.center(header_text), style="blue", border_style="blue"))

    # -- NETWORKS TABLE --
    ap_table = Table(expand=True, show_edge=False, header_style="bold magenta")
    for col in ["SSID", "BSSID / Vendor", "CH", "RSSI / Dist", "Signal", "Sec/WPS", "Data", "Clients"]:
        ap_table.add_column(col, justify="center" if col in ["Sec/WPS", "CH"] else "left")

    now = time.time()
    sorted_aps = []
    with state.lock:
        sorted_aps = sorted(state.discovered_aps.values(), key=lambda x: x['rssi'][-1] if x['rssi'] else -100, reverse=True)[:18]
        
    for ap in sorted_aps:
        if now - ap["last_seen"] > 60: continue
        
        ssid_display = f"[bold red]{ap['ssid']}[/bold red]" if ap['hidden'] else ap['ssid']
        current_rssi = ap['rssi'][-1] if ap['rssi'] else -100
        rssi_style = get_rssi_color(current_rssi)
        
        freq = get_freq_from_channel(ap.get('channel', '?'))
        dist = estimate_distance(current_rssi, freq)
        
        crypto_str = "/".join(ap["crypto"])
        if ap.get("wps"): crypto_str += "\n[red]+WPS[/red]"
        
        sparkline = generate_sparkline(ap['rssi'])
        
        client_count_str = str(len(ap.get("clients", [])))

        ap_table.add_row(
            ssid_display,
            f"{ap['mac']}\n[dim]{ap['vendor']}[/dim]",
            str(ap.get('channel', '?')),
            f"[{rssi_style}]{current_rssi} dBm[/{rssi_style}]\n[dim]~{dist}m[/dim]",
            f"[bold {rssi_style}]{sparkline}[/]",
            crypto_str,
            str(ap['data_frames']),
            client_count_str
        )

    layout["networks"].update(Panel(ap_table, title="📡 Active Access Points", border_style="cyan"))

    # -- WATCHLIST --
    watch_table = Table(expand=True, show_edge=False, header_style="bold magenta")
    watch_table.add_column("Target MAC", style="white")
    watch_table.add_column("Type/Probes", style="dim yellow")
    watch_table.add_column("Signal", justify="right")
    
    with state.lock:
        for mac in watchlist:
            if mac in state.clients_tracked:
                c = state.clients_tracked[mac]
                probes = ", ".join(list(c.get("probes", set()))[:2]) or "---"
                r_flag = "[red]R[/red] " if c.get("is_randomized") else ""
                
                if now - c["last_seen"] < 30:
                    current_rssi = c['rssi'][-1] if c['rssi'] else -100
                    dist = estimate_distance(current_rssi, 2412)
                    spark = generate_sparkline(c['rssi'])
                    color = get_rssi_color(current_rssi)
                    
                    watch_table.add_row(
                        f"{r_flag}{mac}\n[dim]{resolve_oui(mac)}[/dim]", 
                        str(probes), 
                        f"[{color}]{current_rssi} dBm[/{color}]\n[dim]~{dist}m[/dim]\n[bold {color}]{spark}[/]"
                    )
                else:
                    watch_table.add_row(f"{r_flag}{mac}\n[dim]{resolve_oui(mac)}[/dim]", probes, "○ [bold yellow]AWAY[/bold yellow]")
            else:
                r_flag = "[red]R[/red] " if is_mac_randomized(mac) else ""
                watch_table.add_row(f"{r_flag}{mac}\n[dim]{resolve_oui(mac)}[/dim]", "---", "[dim]NOT SEEN[/dim]")

    layout["watchlist"].update(Panel(watch_table, title="👨‍👩‍👧 Watchlist Target Radar", border_style="yellow"))

    # -- TELEMETRY --
    telemetry_ui = f"""
[bold cyan]Global Statistics[/bold cyan]
Total APs: {ap_count}
Total Clients: {client_count}
PCAP Writer: {"[green]Active[/green]" if state.pcap_writer else "[dim]Inactive[/dim]"}

[bold yellow]Threat Intel[/bold yellow]
Network Anomaly Score: {nas}/100
    """
    layout["telemetry"].update(Panel(telemetry_ui.strip(), title="📈 Telemetry", border_style="magenta"))

    # -- ALERTS --
    with state.lock:
        alerts_text = "\n\n".join(state.security_alerts) if state.security_alerts else "[dim]No recent events.[/dim]\n[dim]Awaiting handshakes, deauths, and rogue APs...[/dim]"
    layout["alerts_panel"].update(Panel(alerts_text, title="⚠️ Deep Packet Inspector", border_style="red"))
    
    return layout
