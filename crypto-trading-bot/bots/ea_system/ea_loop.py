#!/usr/bin/env python3
"""
EA Background Loop — Runs scan/monitor on schedule.
Proper timing prevents startup burst collisions.
"""

import os
import sys
import time
import subprocess
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
DAEMON_PATH = os.path.join(BASE_DIR, 'ea_daemon.py')
PID_FILE = os.path.join(LOGS_DIR, 'ea_loop.pid')

SCAN_INTERVAL = 15 * 60   # 15 minutes
MONITOR_INTERVAL = 3 * 60  # 3 minutes

def log(msg):
    ts = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    # Also append to loop log
    try:
        with open(os.path.join(LOGS_DIR, 'ea_loop.log'), 'a') as f:
            f.write(line + '\n')
    except:
        pass

def run_mode(mode):
    """Run ea_daemon.py in given mode."""
    cmd = [sys.executable, DAEMON_PATH, '--mode', mode]
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
            cwd=BASE_DIR,
            timeout=120
        )
        log(f"{mode.upper()} completed (exit {result.returncode})")
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        log(f"{mode.upper()} TIMEOUT after 120s")
        return False
    except Exception as e:
        log(f"{mode.upper()} ERROR: {e}")
        return False

def main():
    os.makedirs(LOGS_DIR, exist_ok=True)
    
    # Write PID file
    with open(PID_FILE, 'w') as f:
        f.write(str(os.getpid()))
    
    now = time.time()
    # Don't run everything on startup — stagger them
    last_scan = now  # First scan after first interval passes
    last_monitor = now - MONITOR_INTERVAL + 15  # First monitor in 15s
    
    log("=" * 60)
    log("EA LOOP STARTED")
    log(f"PID: {os.getpid()}")
    log(f"First monitor in ~15s, first scan in ~15min")
    log("=" * 60)
    
    try:
        while True:
            now = time.time()
            
            # Monitor every 3 minutes
            if now - last_monitor >= MONITOR_INTERVAL:
                run_mode('monitor')
                last_monitor = now
            
            # Scan every 15 minutes
            if now - last_scan >= SCAN_INTERVAL:
                run_mode('scan')
                last_scan = now
            
            time.sleep(10)
            
    except KeyboardInterrupt:
        log("KeyboardInterrupt, shutting down...")
    finally:
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
        log("EA LOOP STOPPED")

if __name__ == '__main__':
    main()
