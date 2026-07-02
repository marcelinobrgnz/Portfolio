# Serve static files for drift report screenshots
# Usage: python scripts/serve_demo_proof.py
import http.server
import socketserver
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PORT = 8766

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

if __name__ == "__main__":
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Serving {ROOT} at http://127.0.0.1:{PORT}")
        httpd.serve_forever()
