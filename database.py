import sqlite3
import os
import time

class DatabaseLogger:
    def __init__(self, db_path="homesync.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Networks Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS networks (
                    bssid TEXT PRIMARY KEY,
                    ssid TEXT,
                    channel INTEGER,
                    vendor TEXT,
                    first_seen REAL,
                    last_seen REAL,
                    encryption TEXT,
                    wps BOOLEAN
                )
            ''')
            # Clients Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS clients (
                    mac TEXT PRIMARY KEY,
                    vendor TEXT,
                    is_randomized BOOLEAN,
                    first_seen REAL,
                    last_seen REAL
                )
            ''')
            # Probes Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS probes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_mac TEXT,
                    ssid TEXT,
                    timestamp REAL,
                    UNIQUE(client_mac, ssid)
                )
            ''')
            # Security Events Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS security_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL,
                    event_type TEXT,
                    details TEXT
                )
            ''')
            conn.commit()

    def update_network(self, bssid, ssid, channel, vendor, encryption, wps, timestamp):
        enc_str = "/".join(encryption) if type(encryption) is list else str(encryption)
        with sqlite3.connect(self.db_path, timeout=5) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT first_seen FROM networks WHERE bssid = ?', (bssid,))
            row = cursor.fetchone()
            if row:
                cursor.execute('''
                    UPDATE networks 
                    SET ssid = ?, channel = ?, vendor = ?, last_seen = ?, encryption = ?, wps = ?
                    WHERE bssid = ?
                ''', (ssid, channel, vendor, timestamp, enc_str, wps, bssid))
            else:
                cursor.execute('''
                    INSERT INTO networks (bssid, ssid, channel, vendor, first_seen, last_seen, encryption, wps)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (bssid, ssid, channel, vendor, timestamp, timestamp, enc_str, wps))
            conn.commit()

    def update_client(self, mac, vendor, is_randomized, timestamp):
        with sqlite3.connect(self.db_path, timeout=5) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT first_seen FROM clients WHERE mac = ?', (mac,))
            if cursor.fetchone():
                cursor.execute('UPDATE clients SET last_seen = ? WHERE mac = ?', (timestamp, mac))
            else:
                cursor.execute('''
                    INSERT INTO clients (mac, vendor, is_randomized, first_seen, last_seen)
                    VALUES (?, ?, ?, ?, ?)
                ''', (mac, vendor, is_randomized, timestamp, timestamp))
            conn.commit()

    def log_probe(self, client_mac, ssid, timestamp):
        if not ssid: return
        with sqlite3.connect(self.db_path, timeout=5) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT OR IGNORE INTO probes (client_mac, ssid, timestamp) VALUES (?, ?, ?)', 
                           (client_mac, ssid, timestamp))
            conn.commit()

    def log_security_event(self, event_type, details, timestamp):
        with sqlite3.connect(self.db_path, timeout=5) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO security_events (timestamp, event_type, details) VALUES (?, ?, ?)',
                           (timestamp, event_type, details))
            conn.commit()
