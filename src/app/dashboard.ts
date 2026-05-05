import { ChangeDetectionStrategy, Component, inject, computed, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { WifiService, WifiDevice } from './wifi';
import { MatIconModule } from '@angular/material/icon';
import { LucideAngularModule, Shield, Wifi, Users, Signal, AlertTriangle, Search, Trash2, Plus } from 'lucide-angular';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, MatIconModule, LucideAngularModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="min-h-screen bg-zinc-950 text-zinc-100 font-sans selection:bg-emerald-500/30">
      <!-- Nav -->
      <nav class="border-b border-zinc-800/50 bg-zinc-900/50 backdrop-blur-xl sticky top-0 z-50">
        <div class="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div class="flex items-center gap-3">
            <div class="bg-emerald-500/10 p-2 rounded-lg">
              <lucide-icon [name]="Shield" class="w-6 h-6 text-emerald-400"></lucide-icon>
            </div>
            <h1 class="text-xl font-medium tracking-tight bg-gradient-to-br from-white to-zinc-400 bg-clip-text text-transparent">HomeSync</h1>
          </div>
          
          <div class="flex items-center gap-6 text-sm text-zinc-400 font-medium">
            <span class="flex items-center gap-2"><div class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div> Monitoring Live</span>
            <span class="hidden md:flex items-center gap-2 border-l border-zinc-800 pl-6"><lucide-icon [name]="Wifi" class="w-4 h-4"></lucide-icon> 2.4/5GHz Active</span>
          </div>
        </div>
      </nav>

      <main class="max-w-7xl mx-auto px-6 py-8 grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        <!-- Left Panel: Critical Watchlist -->
        <div class="lg:col-span-1 space-y-6">
          <header class="flex items-center justify-between">
            <h2 class="text-xs uppercase tracking-[0.2em] font-semibold text-zinc-500">Family Watchlist</h2>
            <button (click)="isAddingTarget.set(true)" class="p-1 hover:bg-zinc-800 rounded transition-colors">
              <lucide-icon [name]="Plus" class="w-4 h-4 text-zinc-400"></lucide-icon>
            </button>
          </header>

          @for (target of trackedDevices(); track target.mac) {
            <div class="group relative bg-zinc-900/40 border border-zinc-800 hover:border-zinc-700/50 rounded-2xl p-5 transition-all duration-300">
              <div class="flex items-start justify-between mb-4">
                <div class="flex items-center gap-4">
                  <div class="p-3 rounded-xl bg-zinc-800/50 group-hover:bg-zinc-800 transition-colors">
                    <lucide-icon [name]="Users" class="w-5 h-5 text-zinc-300"></lucide-icon>
                  </div>
                  <div>
                    <h3 class="font-medium text-zinc-100">{{ target.name || 'Unknown Device' }}</h3>
                    <p class="text-[10px] font-mono text-zinc-500">{{ target.mac }}</p>
                  </div>
                </div>
                <div [class]="getRssiColor(target.rssi)" class="px-2.5 py-1 rounded-full text-[10px] font-bold border flex items-center gap-1.5 shadow-sm">
                  <lucide-icon [name]="Signal" class="w-3 h-3"></lucide-icon>
                  {{ target.rssi }} dBm
                </div>
              </div>

              <div class="flex items-center justify-between text-xs">
                <div class="flex items-center gap-2">
                  @if (target.present) {
                    <span class="text-emerald-400 font-medium flex items-center gap-1.5">
                      <div class="w-1.5 h-1.5 rounded-full bg-emerald-500"></div> Present
                    </span>
                  } @else {
                    <span class="text-zinc-500 font-medium flex items-center gap-1.5">
                      <div class="w-1.5 h-1.5 rounded-full bg-zinc-700"></div> Away
                    </span>
                  }
                </div>
                <button (click)="wifi.removeTarget(target.mac)" class="opacity-0 group-hover:opacity-100 text-zinc-500 hover:text-red-400 transition-all p-1">
                  <lucide-icon [name]="Trash2" class="w-4 h-4"></lucide-icon>
                </button>
              </div>
            </div>
          }

          @if (isAddingTarget()) {
             <div class="bg-zinc-900 border border-emerald-500/30 rounded-2xl p-4 animate-in fade-in slide-in-from-top-2 duration-300">
                <input #macInput type="text" placeholder="Enter MAC Address..." class="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-2 text-sm focus:outline-none focus:border-emerald-500/50 transition-colors mb-2">
                <div class="flex justify-end gap-2">
                   <button (click)="isAddingTarget.set(false)" class="px-3 py-1 text-xs text-zinc-400 hover:text-zinc-200">Cancel</button>
                   <button (click)="wifi.addTarget(macInput.value); isAddingTarget.set(false)" class="px-3 py-1 text-xs bg-emerald-600 text-white rounded-lg hover:bg-emerald-500 transition-colors">Add Device</button>
                </div>
             </div>
          }
        </div>

        <!-- Right Panel: Network Activity -->
        <div class="lg:col-span-2 space-y-4">
          <header class="flex items-center justify-between px-2">
             <div class="space-y-1">
                <h2 class="text-xs uppercase tracking-[0.2em] font-semibold text-zinc-500">Surrounding Networks</h2>
                <p class="text-[10px] text-zinc-600 font-mono">Capturing beacons from all access points in range</p>
             </div>
             <div class="text-[10px] font-mono text-zinc-500 flex items-center gap-4">
                <span>{{ accessPoints().length }} APs Found</span>
                <span>CH: 1, 6, 11, 36, 44...</span>
             </div>
          </header>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            @for (ap of accessPoints(); track ap.mac) {
              <div class="bg-zinc-900/30 border border-zinc-800/60 rounded-xl p-4 flex items-center gap-4 group transition-all hover:bg-zinc-900/50">
                <div class="w-10 h-10 rounded-full border border-zinc-800 flex items-center justify-center bg-zinc-950 text-zinc-400 group-hover:text-emerald-400 transition-colors">
                  <lucide-icon [name]="Wifi" class="w-5 h-5"></lucide-icon>
                </div>
                <div class="flex-1 min-w-0">
                  <div class="flex items-center gap-2">
                    <h4 class="text-sm font-medium truncate text-zinc-100">{{ ap.ssid || 'Unknown Network' }}</h4>
                    @if (ap.hidden) {
                      <span class="bg-amber-500/10 text-amber-500 text-[8px] uppercase tracking-wider font-extrabold px-1.5 py-0.5 rounded border border-amber-500/20">Hidden</span>
                    }
                  </div>
                  <div class="flex items-center gap-3 text-[10px] font-mono text-zinc-500 mt-0.5">
                    <span>{{ ap.mac }}</span>
                    <span>CH {{ ap.channel }}</span>
                  </div>
                </div>
                <div class="text-right">
                  <div [class]="getRssiColor(ap.rssi, true)" class="text-xs font-mono font-bold">{{ ap.rssi }} <span class="text-[10px] opacity-70">dBm</span></div>
                </div>
              </div>
            }
          </div>

          <!-- Alert Context -->
          @if (hiddenAlerts().length > 0) {
            <div class="mt-8 p-4 bg-amber-500/5 border border-amber-500/20 rounded-2xl flex items-start gap-4">
              <div class="bg-amber-500/10 p-2 rounded-lg">
                <lucide-icon [name]="AlertTriangle" class="w-5 h-5 text-amber-500"></lucide-icon>
              </div>
              <div>
                <h4 class="text-sm font-medium text-amber-200">Hidden SSID Activity Detected</h4>
                <p class="text-xs text-zinc-500 mt-1">We are analyzing probe request patterns to map hidden networks. Tracking {{ hiddenAlerts().length }} obfuscated beacons.</p>
              </div>
            </div>
          }
        </div>
      </main>

      <!-- Stats Bar -->
      <footer class="fixed bottom-0 w-full border-t border-zinc-800/50 bg-zinc-950/80 backdrop-blur-md">
        <div class="max-w-7xl mx-auto px-6 h-12 flex items-center justify-between text-[10px] font-mono text-zinc-500">
           <div class="flex items-center gap-6">
              <span class="flex items-center gap-2 truncate max-w-[200px]"><div class="w-1.5 h-1.5 rounded-full bg-blue-500"></div> Scanner: Physical eth0 (Monitor)</span>
              <span class="hidden sm:inline">Logging: data/wifi_activity.csv</span>
           </div>
           <div class="flex items-center gap-4">
              <span>Up: 01h 45m</span>
              <span class="text-zinc-600">v1.2.0-stable</span>
           </div>
        </div>
      </footer>
    </div>
  `,
})
export class Dashboard {
  wifi = inject(WifiService);
  isAddingTarget = signal(false);

  // Icons
  Shield = Shield; Wifi = Wifi; Users = Users; Signal = Signal; AlertTriangle = AlertTriangle; Search = Search; Trash2 = Trash2; Plus = Plus;

  trackedDevices = computed(() => {
    const targets = this.wifi.targetMacs();
    return this.wifi.devices()
      .filter(d => targets.includes(d.mac))
      .sort((a, b) => b.rssi - a.rssi);
  });

  accessPoints = computed(() => {
    return this.wifi.devices()
      .filter(d => d.type === 'AP')
      .sort((a, b) => b.rssi - a.rssi);
  });

  hiddenAlerts = computed(() => {
    return this.accessPoints().filter(ap => ap.hidden);
  });

  getRssiColor(rssi: number, isTextOnly = false) {
    if (rssi > -50) return isTextOnly ? 'text-emerald-400' : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20 shadow-emerald-500/5';
    if (rssi > -70) return isTextOnly ? 'text-blue-400' : 'bg-blue-500/10 text-blue-400 border-blue-500/20 shadow-blue-500/5';
    if (rssi > -85) return isTextOnly ? 'text-amber-400' : 'bg-amber-500/10 text-amber-400 border-amber-500/20 shadow-amber-500/5';
    return isTextOnly ? 'text-red-400' : 'bg-red-500/10 text-red-500 border-red-500/20 shadow-red-500/5';
  }
}
