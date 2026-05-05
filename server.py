import http.server
import socketserver

PORT = 3000

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        html = """
        <html>
        <head>
            <title>HomeSync TUI</title>
            <style>
                body { background-color: #0d1117; color: #c9d1d9; font-family: monospace; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }
                .container { text-align: center; border: 1px solid #30363d; padding: 40px; border-radius: 8px; background-color: #161b22; max-width: 600px;}
                h1 { color: #58a6ff; }
                code { background-color: #000; padding: 10px; display: inline-block; border-radius: 4px; color: #7ee787; font-size: 16px; margin-top: 20px;}
                p { line-height: 1.5; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🛡️ HomeSync Wi-Fi Sentinel</h1>
                <p>This project has been converted strictly to a <b>Python Terminal UI (TUI)</b> application as requested.</p>
                <div style="text-align: left; background: #000; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <span style="color: #ff7b72;">[INFO]</span> The frontend preview is disabled because this is a pure terminal application.<br><br>
                    To run the visually beautiful terminal dashboard, copy the code to your local machine and execute:
                </div>
                <code>pip install -r requirements.txt<br><br>sudo python3 main.py -h</code>
                <p><br>Note: For actual packet sniffing, you must run it locally with a monitor-mode compatible Wi-Fi adapter (e.g., wlan0mon).</p>
            </div>
        </body>
        </html>
        """
        self.wfile.write(html.encode())

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"Serving preview placeholder on port {PORT}")
    httpd.serve_forever()
