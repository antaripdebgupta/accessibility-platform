#!/usr/bin/env python3
"""
Minimal HTTP health server + Celery worker launcher.

This allows the Celery worker to run as a Render "Web Service" (free tier)
instead of a "Background Worker" (not available on free tier).

The health endpoint responds to Render's health checks while Celery runs
in the background processing tasks.
"""

import os
import subprocess
import sys
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# Health check port (Render assigns $PORT)
PORT = int(os.environ.get("PORT", 8001))


class HealthHandler(BaseHTTPRequestHandler):
    """Minimal health check handler."""

    def do_GET(self):
        if self.path in ("/health", "/", "/healthz"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status":"healthy","service":"celery-worker"}')
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Suppress default logging to reduce noise
        pass


def run_health_server():
    """Run the health check HTTP server."""
    server = HTTPServer(("0.0.0.0", PORT), HealthHandler)
    print(f"🩺 Health server listening on port {PORT}")
    server.serve_forever()


def run_celery_worker():
    """Run Celery worker as a subprocess."""
    print("Starting Celery worker...")
    cmd = [
        "celery",
        "-A", "tasks.celery_app",
        "worker",
        "--loglevel=info",
        "--concurrency=2",
        "-Q", "crawl,scan,report",
    ]
    # Run Celery and stream output
    process = subprocess.Popen(cmd, stdout=sys.stdout, stderr=sys.stderr)
    process.wait()
    print(f"Celery worker exited with code {process.returncode}")
    sys.exit(process.returncode)


if __name__ == "__main__":
    # Start health server in background thread
    health_thread = threading.Thread(target=run_health_server, daemon=True)
    health_thread.start()

    # Run Celery in main thread (blocking)
    run_celery_worker()
