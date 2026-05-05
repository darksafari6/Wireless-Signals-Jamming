import time
import subprocess
from state import state
from utils import resolve_oui, is_mac_randomized

try:
    from scapy.all import sniff, Dot11Beacon, Dot11ProbeResp, Dot11ProbeReq, Dot11, Dot11Deauth, Dot11Auth, Dot11AssoReq, Dot11Elt, EAPOL
except ImportError:
    pass

def channel_hopper(interface, channels):
    while True:
        for channel in channels:
            try:
                subprocess.run(["iw", "dev", interface, "set", "channel", str(channel)], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                time.sleep(1)
            except:
                time.sleep(1)

def threat_decay_loop():
    while True:
        time.sleep(5)
        state.decay_threat_score()

def packet_handler(pkt):
    now = time.time()
    
    with state.lock:
        if state.pcap_writer: 
            state.pcap_writer.write(pkt)

    if pkt.type == 2: # Data frame
        with state.lock:
            for m in (getattr(pkt, 'addr1', None), getattr(pkt, 'addr2', None), getattr(pkt, 'addr3', None)):
                if m and m in state.discovered_aps:
                    state.discovered_aps[m]["data_frames"] += 1
                    state.discovered_aps[m]["last_seen"] = now

    if pkt.haslayer(Dot11Auth): state.log_alert("AUTH ATTEMPT", f"{pkt.addr2} -> {pkt.addr1}")
    elif pkt.haslayer(Dot11AssoReq): state.log_alert("ASSOC REQUEST", f"{pkt.addr2} -> {pkt.addr1}")
    elif pkt.haslayer(Dot11Deauth): state.log_alert("DEAUTH DETECTED", f"{pkt.addr2} -> {pkt.addr1}")
    elif pkt.haslayer(EAPOL): state.log_alert("WPA HANDSHAKE (EAPOL)", f"Captured for {pkt.addr2}")
    
    if pkt.type == 0 and pkt.subtype == 10:
        state.log_alert("DISASSOCIATION", f"Kick: {pkt.addr2} -> {pkt.addr1}")

    if pkt.haslayer(Dot11Beacon):
        handle_beacon(pkt, now)
    elif pkt.haslayer(Dot11ProbeResp):
        handle_probe_resp(pkt, now)
    elif pkt.haslayer(Dot11ProbeReq) or pkt.haslayer(Dot11):
        handle_client_traffic(pkt, now)

def handle_beacon(pkt, now):
    bssid = pkt.addr2
    if not getattr(pkt, 'info', None): return
    ssid = pkt.info.decode(errors='ignore')
    
    with state.lock:
        state.beacon_flood_tracker.append(now)
        while state.beacon_flood_tracker and state.beacon_flood_tracker[0] < now - 5:
            state.beacon_flood_tracker.pop(0)
        # Anomaly threshold: 300 beacons in 5 sec
        if len(state.beacon_flood_tracker) > 300 and len(state.beacon_flood_tracker) % 100 == 0:
            state.log_alert("BEACON FLOOD", "High volume AP spam/MDK4 detected!")

    try:
        stats = pkt[Dot11Beacon].network_stats()
        channel = stats.get('channel', '?')
        crypto = list(stats.get('crypto', set())) or ['OPN']
    except:
        channel, crypto = '?', ['OPN']
    
    wps = False
    try:
        p = pkt[Dot11Elt]
        while isinstance(p, Dot11Elt):
            if p.ID == 221 and p.info.startswith(b'\x00P\xf2\x04'):
                wps = True
            p = p.payload
    except: pass
        
    rssi = pkt.dBm_AntSignal if hasattr(pkt, 'dBm_AntSignal') else -100
    
    with state.lock:
        is_hidden = False
        if not ssid or ssid == "\x00" * len(ssid):
            is_hidden = True
            ssid = state.hidden_ssids.get(bssid, "[HIDDEN]")

        if ssid and not is_hidden and ssid != "[HIDDEN]":
            state.ssid_bssid_map[ssid].add(bssid)
            if len(state.ssid_bssid_map[ssid]) > 2 and now - state.last_evil_alert > 15:
                # Same SSID on >2 MACs might mean Enterprise or Evil Twin. We flag as anomaly.
                state.log_alert("ROGUE AP", f"Multiple origins for '{ssid}'")
                state.last_evil_alert = now

        if bssid not in state.discovered_aps:
            state.discovered_aps[bssid] = {
                "ssid": ssid, "mac": bssid, "rssi": [rssi], "channel": channel, 
                "hidden": is_hidden, "last_seen": now, "clients": set(), 
                "beacon_count": 1, "crypto": crypto, "wps": wps,
                "data_frames": 0, "vendor": resolve_oui(bssid)
            }
        else:
            state.discovered_aps[bssid]["rssi"].append(rssi)
            if len(state.discovered_aps[bssid]["rssi"]) > 20:
                state.discovered_aps[bssid]["rssi"].pop(0)
            
            state.discovered_aps[bssid].update({"last_seen": now, "crypto": crypto, "wps": wps})
            state.discovered_aps[bssid]["beacon_count"] += 1
            if ssid and ssid != "[HIDDEN]":
                state.discovered_aps[bssid]["ssid"] = ssid
                state.discovered_aps[bssid]["hidden"] = False
                
        # Fire to DB in background (lightly throttled by the db wrapper's commit)
        state.db.update_network(bssid, ssid, channel, resolve_oui(bssid), crypto, wps, now)

def handle_probe_resp(pkt, now):
    bssid, ssid = pkt.addr2, getattr(pkt, 'info', b'').decode(errors='ignore')
    if ssid and bssid:
        with state.lock:
            state.hidden_ssids[bssid] = ssid
            if bssid in state.discovered_aps:
                state.discovered_aps[bssid].update({"ssid": ssid, "hidden": False})

def handle_client_traffic(pkt, now):
    client_mac, ap_mac = pkt.addr2, pkt.addr1
    if client_mac and client_mac != "ff:ff:ff:ff:ff:ff" and not pkt.haslayer(Dot11Beacon):
        rssi = pkt.dBm_AntSignal if hasattr(pkt, 'dBm_AntSignal') else -100
        
        req_ssid = getattr(pkt, 'info', b'').decode(errors='ignore') if pkt.haslayer(Dot11ProbeReq) else ""

        with state.lock:
            if client_mac in state.clients_tracked:
                state.clients_tracked[client_mac]["rssi"].append(rssi)
                if len(state.clients_tracked[client_mac]["rssi"]) > 20: 
                    state.clients_tracked[client_mac]["rssi"].pop(0)

                state.clients_tracked[client_mac]["last_seen"] = now
                if req_ssid: 
                    state.clients_tracked[client_mac]["probes"].add(req_ssid)
                    state.db.log_probe(client_mac, req_ssid, now)

            if ap_mac in state.discovered_aps and client_mac: 
                state.discovered_aps[ap_mac]["clients"].add(client_mac)
                
            # Log client base tracking into DB (throttle slightly if needed, but sqlite handles it ok with minimal load)
            if client_mac in state.clients_tracked:
                state.db.update_client(client_mac, resolve_oui(client_mac), is_mac_randomized(client_mac), now)
