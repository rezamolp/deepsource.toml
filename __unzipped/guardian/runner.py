import os
import sys
import subprocess
import time

WATCHED_DIRS = ["services", "handlers", "utils", "guardian_tests"]
PROCESS = None

def run_bot():
    global PROCESS
    if PROCESS:
        PROCESS.terminate()
    print("🚀 اجرای ربات...")
    PROCESS = subprocess.Popen([sys.executable, 'main.py'])

def watch():
    mtimes = {}
    while True:
        changed = False
        for d in WATCHED_DIRS:
            for root, _, files in os.walk(d):
                for f in files:
                    if f.endswith(".py"):
                        path = os.path.join(root, f)
                        try:
                            mtime = os.path.getmtime(path)
                        except FileNotFoundError:
                            continue
                        if path not in mtimes:
                            mtimes[path] = mtime
                        elif mtime != mtimes[path]:
                            mtimes[path] = mtime
                            print(f"🔄 تغییر در {path} → ری‌استارت ربات")
                            changed = True
        if changed:
            if PROCESS:
                print("⛔ توقف ربات قبلی...")
                PROCESS.terminate()
                time.sleep(1)
            run_bot()
        time.sleep(2)

if __name__ == "__main__":
    run_bot()
    watch()

# ID6: simple /healthz ping
import http.server, socketserver, threading

def _start_healthcheck():
    class Handler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            if self.path == '/healthz':
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'OK')
            else:
                self.send_response(404)
                self.end_headers()
    threading.Thread(target=lambda: socketserver.TCPServer(('0.0.0.0',8080), Handler).serve_forever(), daemon=True).start()

_start_healthcheck()
