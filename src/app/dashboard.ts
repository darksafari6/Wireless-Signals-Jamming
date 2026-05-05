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
    <div class="h-screen flex flex-col bg-[#0f172a] text-[#cbd5e1] font-mono overflow-hidden">
      <!-- Header -->
      <header class="bg-[#1e293b] border-b border-[#334155] px-5 py-3 flex justify-between items-center z-50 shrink-0">
        <div class="flex items-center gap-4">
          <span class="font-bold text-white text-lg tracking-tight">WIFI-SENTINEL</span>
          <span class="text-[#64748b] text-[10px] hidden sm:inline">v1.2.0-STABLE | AI STUDIO BUILD | PASSTHRU: ON</span>
        </div>
        <div class="flex items-center gap-4">
          <div class="badge">ADAPTER: eth0 (mon)</div>
          <div class="badge">MODE: PASSIVE</div>
          <div class="hidden md:flex items-center gap-2 text-[10px] text-[#94a3b8]">
            <div class="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse"></div>
            CAPTURE ACTIVE: 2.4/5GHz
          </div>
        </div>
      </header>

      <div class="flex flex-1 overflow-hidden">
        <!-- Sidebar -->
        <aside class="w-[300px] bg-[#111827] border-r border-[#334155] flex flex-col shrink-0 overflow-y-auto p-4 custom-scrollbar">
          <section class="mb-8">
            <h2 class="text-[10px] uppercase tracking-[0.2em] font-bold text-[#64748b] mb-4">Parental Watchlist</h2>
            
            <div class="space-y-2">
              @for (target of trackedDevices(); track target.mac) {
                <div class="bg-[#1e293b] border-l-4 border-red-500 p-3 flex justify-between items-start group shadow-lg">
                  <div class="min-w-0">
                    <div class="text-[11px] font-bold text-white truncate">{{ target.name || 'Unknown Device' }}</div>
                    <div class="text-[9px] text-[#94a3b8] font-mono mt-0.5">{{ target.mac }}</div>
                    
                    <div class="flex items-center gap-2 mt-2">
                      @if (target.present) {
                        <span class="text-[9px] text-[#10b981] flex items-center gap-1 font-bold">
                          <div class="w-1 h-1 rounded-full bg-[#10b981]"></div> IN RANGE
                        </span>
                      } @else {
                        <span class="text-[9px] text-[#64748b] flex items-center gap-1 font-bold">
                          <div class="w-1 h-1 rounded-full bg-[#64748b]"></div> OFFLINE
                        </span>
                      }
                    </div>
                  </div>
                  <div class="text-right shrink-0">
                    <div class="text-[10px] font-bold" [class]="getRssiColor(target.rssi, true)">{{ target.rssi }} dBm</div>
                    <button (click)="wifi.removeTarget(target.mac)" class="opacity-0 group-hover:opacity-100 text-[#475569] hover:text-red-400 p-1 transition-all mt-1">
                      <lucide-icon [name]="Trash2" class="w-3.5 h-3.5"></lucide-icon>
                    </button>
                  </div>
                </div>
              }

              @if (isAddingTarget()) {
                <div class="bg-[#1e293b] border border-[#334155] p-3 space-y-2">
                  <input #macInput type="text" placeholder="MAC ADDR..." class="w-full bg-[#0f172a] border border-[#334155] text-[10px] px-2 py-1.5 focus:outline-none focus:border-blue-500 text-white">
                  <div class="flex justify-end gap-2">
                     <button (click)="isAddingTarget.set(false)" class="text-[9px] text-[#64748b] hover:text-white uppercase font-bold">Cancel</button>
                     <button (click)="wifi.addTarget(macInput.value); isAddingTarget.set(false)" class="bg-[#3b82f6] text-white text-[9px] px-2 py-1 font-bold uppercase">Add</button>
                  </div>
                </div>
              } @else {
                <button (click)="isAddingTarget.set(true)" class="w-full border border-dashed border-[#334155] hover:border-[#475569] py-2 text-[10px] text-[#64748b] hover:text-[#94a3b8] transition-colors uppercase font-bold">
                  + Add Watch Device
                </button>
              }
            </div>
          </section>

          <section class="mt-auto pt-4 border-t border-[#334155]">
            <h2 class="text-[10px] uppercase tracking-[0.2em] font-bold text-[#64748b] mb-4">Event Log</h2>
            <div class="space-y-1.5 max-h-[200px] overflow-y-auto pr-2 custom-scrollbar">
               @for (ap of accessPoints().slice(0, 5); track ap.mac) {
                 <div class="text-[9px] text-[#94a3b8] border-b border-[#1e293b] pb-1">
                   [{{ ap.timestamp | date:'HH:mm:ss' }}] SEEN AP: {{ ap.ssid || 'HIDDEN' }} ({{ ap.rssi }} dBm)
                 </div>
               }
            </div>
            <button class="w-full bg-[#3b82f6]/10 hover:bg-[#3b82f6]/20 text-[#3b82f6] text-[9px] font-bold py-2 mt-4 transition-colors uppercase border border-[#3b82f6]/20">
              Download CSV Records
            </button>
          </section>
        </aside>

        <!-- Main Workspace -->
        <main class="flex-1 flex flex-col p-4 gap-4 overflow-hidden">
          
          <!-- AP Panel -->
          <div class="panel flex-1 flex flex-col overflow-hidden shadow-2xl">
            <div class="panel-header shrink-0">
               <span>DISCOVERED ACCESS POINTS</span>
               <span>TOTAL: {{ accessPoints().length }}</span>
            </div>
            <div class="flex-1 overflow-auto custom-scrollbar">
              <table class="w-full border-collapse text-[11px] text-left">
                <thead class="sticky top-0 bg-[#334155] text-white z-10 shadow-sm border-b border-[#475569]">
                  <tr>
                    <th class="p-2 font-bold uppercase tracking-wider">SSID</th>
                    <th class="p-2 font-bold uppercase tracking-wider">BSSID (MAC)</th>
                    <th class="p-2 font-bold uppercase tracking-wider">CH</th>
                    <th class="p-2 font-bold uppercase tracking-wider">Signal Strength</th>
                    <th class="p-2 font-bold uppercase tracking-wider">Enc</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-[#1e293b]">
                  @for (ap of accessPoints(); track ap.mac) {
                    <tr class="hover:bg-white/5 transition-colors group">
                      <td class="p-2">
                         <div class="flex items-center gap-2">
                           <span [class.text-amber-500]="ap.hidden" class="font-bold">{{ ap.ssid || '[HIDDEN]' }}</span>
                           @if (ap.hidden) {
                             <span class="text-[8px] bg-amber-500/10 text-amber-500 px-1 border border-amber-500/20 font-black">HIDDEN</span>
                           }
                         </div>
                      </td>
                      <td class="p-2 font-mono text-[#94a3b8]">{{ ap.mac }}</td>
                      <td class="p-2 text-[#64748b]">{{ ap.channel || '-' }}</td>
                      <td class="p-2">
                        <div class="flex items-center gap-3">
                          <div class="w-16 h-1.5 bg-[#334155] relative grow max-w-[80px]">
                            <div class="absolute h-full left-0 top-0 transition-all duration-500" 
                                 [style.width.%]="calculateRssiPercent(ap.rssi)"
                                 [style.background-color]="getRssiHex(ap.rssi)"></div>
                          </div>
                          <span class="font-bold min-w-[40px]" [class]="getRssiColor(ap.rssi, true)">{{ ap.rssi }} <span class="text-[9px] font-normal opacity-50 uppercase tracking-tighter">dBm</span></span>
                        </div>
                      </td>
                      <td class="p-2 text-[#64748b]">WPA2/WPA3</td>
                    </tr>
                  }
                </tbody>
              </table>
            </div>
          </div>

          <!-- Terminal Panel -->
          <div class="panel h-[220px] flex flex-col shrink-0 shadow-inner">
            <div class="panel-header bg-[#111827] border-b border-[#334155]">
               <div class="flex items-center gap-2">
                  <div class="w-2 h-2 rounded-full bg-red-500 animate-pulse shadow-[0_0_8px_rgba(239,68,68,0.5)]"></div>
                  <span>LIVE CAPTURE MONITOR</span>
               </div>
               <span class="text-[#22c55e] text-[9px] font-mono">SCAPY_STDOUT_PIPE</span>
            </div>
            <div class="flex-1 bg-black p-3 font-mono text-[10px] text-[#22c55e] overflow-y-auto leading-relaxed custom-scrollbar selection:bg-[#22c55e]/30 selection:text-black">
               <div>[SYSTEM] INITIALIZING WIFI-SENTINEL INTERFACE...</div>
               <div>[SUCCESS] INTERFACE eth0 SWITCHED TO MONITOR MODE</div>
               <div>[CONFIG] CHANNEL HOPPLING LIST: [1, 6, 11, 36, 44, 149, 161]</div>
               @for (ap of accessPoints(); track ap.mac; let idx = $index) {
                 <div>
                    <span class="text-zinc-600">[{{ ap.timestamp | date:'HH:mm:ss.ms' }}]</span> 
                    <span class="text-blue-400"> CAPTURE:</span> 
                    BEACON FROM <span class="text-white">{{ ap.mac }}</span> | 
                    SSID: <span class="text-white">{{ ap.ssid || '[HIDDEN]' }}</span> | 
                    SIG: <span [class]="getRssiColor(ap.rssi, true)">{{ ap.rssi }}dBm</span>
                 </div>
               }
               <div class="animate-pulse">_</div>
            </div>
            <div class="bg-[#111827] border-t border-[#334155] px-3 py-1 flex justify-between items-center text-[9px] text-[#64748b]">
               <span>PID: 14293</span>
               <span>BUFFER: 4.2MB</span>
               <span>FCS: OK</span>
            </div>
          </div>

        </main>
      </div>

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

  calculateRssiPercent(rssi: number) {
    // -100 to -30 range
    const percent = Math.max(0, Math.min(100, ((rssi + 100) / 70) * 100));
    return percent;
  }

  getRssiHex(rssi: number) {
    if (rssi > -50) return '#10b981'; // emerald
    if (rssi > -70) return '#3b82f6'; // blue
    if (rssi > -85) return '#f59e0b'; // amber
    return '#ef4444'; // red
  }

  getRssiColor(rssi: number, isTextOnly = false) {
    if (rssi > -50) return isTextOnly ? 'text-[#10b981]' : 'text-[#10b981]';
    if (rssi > -70) return isTextOnly ? 'text-[#3b82f6]' : 'text-[#3b82f6]';
    if (rssi > -85) return isTextOnly ? 'text-[#f59e0b]' : 'text-[#f59e0b]';
    return isTextOnly ? 'text-[#ef4444]' : 'text-[#ef4444]';
  }
}
