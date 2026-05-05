import { Injectable, signal, PLATFORM_ID, inject } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';

export interface WifiDevice {
  ssid?: string;
  name?: string;
  mac: string;
  rssi: number;
  hidden?: boolean;
  channel?: number;
  type: 'AP' | 'Client';
  parentMac?: string;
  timestamp: string;
  present: boolean;
}

@Injectable({
  providedIn: 'root'
})
export class WifiService {
  private platformId = inject(PLATFORM_ID);
  devices = signal<WifiDevice[]>([]);
  targetMacs = signal<string[]>(['CC:BB:AA:33:22:11', 'DD:EE:FF:66:55:44']); // Mock targets
  
  private socket?: WebSocket;

  constructor() {
    if (isPlatformBrowser(this.platformId)) {
      this.connect();
    }
  }

  private connect() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    this.socket = new WebSocket(`${protocol}//${host}`);

    this.socket.onmessage = (event) => {
      const message = JSON.parse(event.data);
      if (message.type === 'wifi_update') {
        this.devices.set(message.data);
      }
    };

    this.socket.onclose = () => {
      console.log('WiFi socket closed. Reconnecting in 5s...');
      setTimeout(() => this.connect(), 5000);
    };
  }

  addTarget(mac: string) {
    if (!this.targetMacs().includes(mac)) {
      this.targetMacs.update(macs => [...macs, mac]);
    }
  }

  removeTarget(mac: string) {
    this.targetMacs.update(macs => macs.filter(m => m !== mac));
  }
}
