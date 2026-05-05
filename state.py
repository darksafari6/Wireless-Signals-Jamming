import threading
from collections import defaultdict
from database import DatabaseLogger
from datetime import datetime

class AppState:
    def __init__(self):
        self.lock = threading.Lock()
        
        self.discovered_aps = {}
        self.hidden_ssids = {}
        self.clients_tracked = {}
        self.security_alerts = []
        
        self.beacon_flood_tracker = []
        self.ssid_bssid_map = defaultdict(set)
        self.last_evil_alert = 0
        
        self.pcap_writer = None
        
        # Ble tracking stub
        self.ble_devices = {}
        
        # Threat score 0-100
        self.nas_score = 0
        
        self.db = DatabaseLogger("homesync.db")
        
    def log_alert(self, alert_type, message, db_write=True):
        ts_pretty = datetime.now().strftime('%H:%M:%S')
        ts_unix = datetime.now().timestamp()
        
        with self.lock:
            self.security_alerts.insert(0, f"[{ts_pretty}] [bold red]{alert_type}[/bold red]: {message}")
            if len(self.security_alerts) > 15: 
                self.security_alerts.pop()
            
            if db_write:
                self.db.log_security_event(alert_type, message, ts_unix)
                
            # Increase Threat Score temporarily
            self.nas_score = min(100, self.nas_score + 15)

    def decay_threat_score(self):
        with self.lock:
            if self.nas_score > 0:
                self.nas_score = max(0, self.nas_score - 1)

state = AppState()
