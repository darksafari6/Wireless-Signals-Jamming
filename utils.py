import math

from constants import OUI_DICT

def resolve_oui(mac):
    if not mac: return "Unknown"
    return OUI_DICT.get(mac[:8].upper(), "Unknown")

def is_mac_randomized(mac):
    """
    Checks the Locally Administered bit to see if MAC is randomized
    (iOS 14+, Android 10+, Windows 10 randomization)
    """
    if not mac or len(mac) != 17: return False
    # Second hex character
    return mac[1].lower() in ['2', '6', 'a', 'e', 'A', 'E']

def estimate_distance(rssi, freq_mhz):
    if rssi == -100 or freq_mhz == 0: return "?"
    try:
        dist = 10.0 ** ((27.55 - (20 * math.log10(freq_mhz)) + abs(rssi)) / 20.0)
        return round(dist, 1)
    except: return "?"

def get_freq_from_channel(channel):
    try:
        ch = int(channel)
        if ch <= 14: return 2412 + (ch - 1) * 5
        elif ch >= 36: return 5000 + ch * 5
    except: pass
    return 2412

def get_rssi_color(rssi):
    if rssi >= -50: return "bold green"
    if rssi >= -70: return "bold yellow"
    return "bold red"

def generate_sparkline(history):
    """Generates a sparkline from a list of recent RSSI values."""
    if not history: return ""
    ticks = [' ', '▂', '▃', '▄', '▅', '▆', '▇', '█']
    # Map RSSI range, say -90 to -30 into 8 buckets
    line = ""
    for r in history[-10:]:  # Plot last 10
        if r <= -90: line += ticks[0]
        elif r >= -30: line += ticks[-1]
        else:
            # -90 is 0, -30 is 60 range. 
            idx = int(((r + 90) / 60) * 8)
            if idx >= 8: idx = 7
            if idx < 0: idx = 0
            line += ticks[idx]
    return line
