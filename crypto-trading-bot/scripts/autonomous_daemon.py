#!/usr/bin/env python3
"""
Autonomous Trading Daemon
Runs the full agent pipeline + trading cycle every 4 hours.
Includes continuous position monitoring between cycles.
Designed to run as a persistent background process.

Usage:
    nohup python3 scripts/autonomous_daemon.py > logs/daemon.log 2>&1 &
"""

import sys
sys.path.insert(0, '/data/.openclaw/workspace/crypto-trading-bot/src')

import os
import time
import json
import logging
import signal
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from position_monitor import PositionMonitor

# Setup logging
log_dir = Path('/data/.openclaw/workspace/crypto-trading-bot/logs')
log_dir.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_dir / 'daemon.log'),
    ]
)
logger = logging.getLogger(__name__)

RUN_INTERVAL_SECONDS = 4 * 3600  # 4 hours
PID_FILE = Path('/tmp/jarvis_autonomous_daemon.pid')


def write_pid():
    PID_FILE.write_text(str(os.getpid()))


def remove_pid():
    PID_FILE.unlink(missing_ok=True)


def is_already_running():
    if not PID_FILE.exists():
        return False
    try:
        pid = int(PID_FILE.read_text().strip())
        os.kill(pid, 0)  # Check if process exists
        return True
    except (ValueError, OSError):
        return False


def run_pipeline(position_monitor):
    """Run one autonomous pipeline cycle with shared position monitor."""
    logger.info("=" * 60)
    logger.info("DAEMON: Starting autonomous pipeline cycle")
    logger.info("=" * 60)

    try:
        # Run the autonomous pipeline script
        result = subprocess.run(
            [
                sys.executable,
                '/data/.openclaw/workspace/crypto-trading-bot/scripts/autonomous_pipeline.py',
            ],
            capture_output=True,
            text=True,
            timeout=1200,  # 20 min max for full 3-asset pipeline
            env={
                **os.environ,
                'PYTHONPATH': '/data/.openclaw/workspace/crypto-trading-bot/src',
                'ALPACA_API_KEY': os.getenv('ALPACA_API_KEY', ''),
                'ALPACA_SECRET_KEY': os.getenv('ALPACA_SECRET_KEY', ''),
                'ALPACA_PAPER': os.getenv('ALPACA_PAPER', 'true'),
                'ALPACA_BASE_URL': os.getenv('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets'),
            }
        )

        if result.returncode == 0:
            logger.info("Pipeline cycle completed successfully")
        else:
            logger.error(f"Pipeline cycle failed: {result.stderr}")

        if result.stdout:
            for line in result.stdout.strip().split('\n')[-20:]:
                logger.info(f"[pipeline] {line}")

    except subprocess.TimeoutExpired:
        logger.error("Pipeline cycle timed out after 20 minutes")
    except Exception as e:
        logger.error(f"Pipeline cycle error: {e}", exc_info=True)


def signal_handler(signum, frame, position_monitor=None):
    logger.info(f"Received signal {signum}, shutting down...")
    if position_monitor:
        try:
            position_monitor.stop_background()
            logger.info("[Daemon] Position monitor stopped on shutdown")
        except Exception as e:
            logger.error(f"Error stopping position monitor: {e}")
    remove_pid()
    sys.exit(0)


def main():
    if is_already_running():
        logger.error("Daemon already running. Exiting.")
        sys.exit(1)

    write_pid()

    # Start position monitor ONCE — runs continuously between cycles
    position_monitor = PositionMonitor()
    position_monitor.start_background()
    logger.info("[Daemon] Position monitor background thread started (5-min intervals, runs 24/7)")

    signal.signal(signal.SIGTERM, lambda s, f: signal_handler(s, f, position_monitor))
    signal.signal(signal.SIGINT, lambda s, f: signal_handler(s, f, position_monitor))

    logger.info("=" * 60)
    logger.info("JARVIS AUTONOMOUS DAEMON STARTED")
    logger.info(f"Interval: {RUN_INTERVAL_SECONDS / 3600:.0f} hours")
    logger.info(f"PID: {os.getpid()}")
    logger.info(f"PID file: {PID_FILE}")
    logger.info("=" * 60)

    # Run immediately on start (position monitor already running)
    run_pipeline(position_monitor)

    while True:
        next_run = datetime.now(timezone.utc).timestamp() + RUN_INTERVAL_SECONDS
        next_run_str = datetime.fromtimestamp(next_run, timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
        logger.info(f"Next cycle at: {next_run_str} (position monitor keeps running)")
        time.sleep(RUN_INTERVAL_SECONDS)
        run_pipeline(position_monitor)


if __name__ == '__main__':
    main()
