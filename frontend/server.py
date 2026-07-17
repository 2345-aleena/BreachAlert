#!/usr/bin/env python3
"""
BreachAlert — local dev server.

Serves this folder over HTTP so the browser gets proper MIME types
(opening index.html directly via file:// breaks some features like
fetch() calls you'll add in later weeks).

Run:
    python server.py
Then open:
    http://localhost:8000
"""

import http.server
import socketserver
import webbrowser
import threading

PORT = 8000


class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Prevent aggressive browser caching while you're actively editing files
        self.send_header("Cache-Control", "no-store, must-revalidate")
        super().end_headers()

    def log_message(self, format, *args):
        # Slightly friendlier console output
        print(f"  → {args[0]} {args[1]}")


def open_browser():
    webbrowser.open(f"http://localhost:{PORT}")


if __name__ == "__main__":
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print("=" * 50)
        print("  BreachAlert dev server running")
        print(f"  → http://localhost:{PORT}")
        print("  → Press Ctrl+C to stop")
        print("=" * 50)
        threading.Timer(0.6, open_browser).start()
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")
