import {
  AngularNodeAppEngine,
  createNodeRequestHandler,
  isMainModule,
  writeResponseToNodeResponse,
} from '@angular/ssr/node';
import express from 'express';
import {join} from 'node:path';
import {createServer} from 'node:http';
import {WebSocketServer, WebSocket} from 'ws';

const browserDistFolder = join(import.meta.dirname, '../browser');

const app = express();
const angularApp = new AngularNodeAppEngine();
const server = createServer(app);
const wss = new WebSocketServer({server});

// Mock Wi-Fi Data Generator
const mockDevices = [
  { ssid: 'Home_Plus_5G', mac: 'AA:BB:CC:11:22:33', rssi: -45, hidden: false, channel: 36, type: 'AP' },
  { ssid: 'Starlink_Guest', mac: 'FF:EE:DD:44:55:66', rssi: -62, hidden: false, channel: 6, type: 'AP' },
  { ssid: '<HIDDEN>', mac: '00:11:22:33:44:55', rssi: -70, hidden: true, channel: 11, type: 'AP' },
  { ssid: 'Neighbor_Wifi', mac: '99:88:77:66:55:44', rssi: -85, hidden: false, channel: 1, type: 'AP' },
  // Target devices for tracking
  { name: "Child's iPhone", mac: 'CC:BB:AA:33:22:11', rssi: -50, type: 'Client', parentMac: 'AA:BB:CC:11:22:33' },
  { name: "Personal Laptop", mac: 'DD:EE:FF:66:55:44', rssi: -55, type: 'Client', parentMac: 'AA:BB:CC:11:22:33' },
];

function generateWifiUpdate() {
  return mockDevices.map(device => {
    // Randomize RSSI slightly
    const flux = Math.floor(Math.random() * 5) - 2;
    const newRssi = Math.max(-100, Math.min(-30, device.rssi + flux));
    
    // Simulate device presence/absence
    const isPresent = Math.random() > 0.05; // 5% chance of appearing "offline" briefly
    
    return {
      ...device,
      rssi: newRssi,
      timestamp: new Date().toISOString(),
      present: isPresent
    };
  });
}

wss.on('connection', (ws) => {
  console.log('Client connected to Wi-Fi Stream');
  
  const interval = setInterval(() => {
    if (ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({
        type: 'wifi_update',
        data: generateWifiUpdate()
      }));
    }
  }, 2000);

  ws.on('close', () => clearInterval(interval));
});

/**
 * Serve static files from /browser
 */
app.use(
  express.static(browserDistFolder, {
    maxAge: '1y',
    index: false,
    redirect: false,
  }),
);

/**
 * Handle all other requests by rendering the Angular application.
 */
app.use((req, res, next) => {
  angularApp
    .handle(req)
    .then((response) =>
      response ? writeResponseToNodeResponse(response, res) : next(),
    )
    .catch(next);
});

/**
 * Start the server if this module is the main entry point, or it is ran via PM2.
 */
if (isMainModule(import.meta.url) || process.env['pm_id']) {
  const port = process.env['PORT'] || 3000;
  server.listen(port, () => {
    console.log(`Node Express server listening on http://localhost:${port}`);
  });
}

export const reqHandler = createNodeRequestHandler(app);
