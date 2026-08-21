#!/usr/bin/env python3
"""
News Background Loop — runs digests on schedule and polls for breaking alerts.

Mirrors bots/ea_system/ea_loop.py: a long-lived supervisor that shells out to
news_daemon.py, so a crash in one cycle cannot take down the schedule.
"""

import os
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

import config

LOGS_DIR = os.path.join(BASE_DIR, 'logs')
DAEMON_PATH = os.path.join(BASE_DIR, 'news_daemon.py')
PID_FILE = os.path.join(LOGS_DIR, 'news_loop.pid')

TICK_SECONDS = 30
DAEMON_TIMEOUT = 300


def log(msg):
    ts = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    try:
        with open(os.path.join(LOGS_DIR, 'news_loop.log'), 'a') as f:
            f.write(line + '\n')
    except OSError:
        pass


def run_mode(mode, label=None):
    """Run news_daemon.py in the given mode. Returns True on exit code 0."""
    cmd = [sys.executable, DAEMON_PATH, '--mode', mode]
    if label:
        cmd += ['--label', label]

    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
            cwd=BASE_DIR,
            timeout=DAEMON_TIMEOUT,
        )
        log(f"{mode.upper()} completed (exit {result.returncode})")
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        log(f"{mode.upper()} TIMEOUT after {DAEMON_TIMEOUT}s")
        return False
    except Exception as exc:
        log(f"{mode.upper()} ERROR: {exc}")
        return False


class Shutdown(Exception):
    """Raised by the SIGTERM handler so the cleanup in main() still runs."""


def _install_signal_handlers():
    """
    Turn SIGTERM into an exception.

    Without this, `kill` or a systemd stop skips the finally block and leaves a
    stale PID file behind, which makes the next start look like a live process.
    """
    def handler(signum, _frame):
        raise Shutdown(signal.Signals(signum).name)

    signal.signal(signal.SIGTERM, handler)


def parse_digest_times(raw_times):
    """Turn ["08:30", "16:30"] into [(8, 30), (16, 30)], skipping bad entries."""
    parsed = []
    for entry in raw_times:
        try:
            hour, minute = str(entry).split(':')
            parsed.append((int(hour), int(minute)))
        except (ValueError, AttributeError):
            log(f"Ignoring malformed digest time: {entry!r}")
    return sorted(parsed)


def digest_label(hour):
    """Name the digest after the part of the trading day it covers."""
    if hour < 9:
        return "Pre-Market Brief"
    if hour < 12:
        return "Morning Digest"
    if hour < 16:
        return "Midday Digest"
    return "Post-Close Wrap"


def due_digests(now_local, digest_times, fired):
    """
    Digest times that have passed today and have not fired yet.

    Keys are date-scoped, so each scheduled time fires at most once per day.
    """
    due = []
    for hour, minute in digest_times:
        key = f"{now_local.date().isoformat()}T{hour:02d}:{minute:02d}"
        if key in fired:
            continue
        if (now_local.hour, now_local.minute) >= (hour, minute):
            due.append((key, hour))
    return due


def main():
    os.makedirs(LOGS_DIR, exist_ok=True)

    try:
        cfg = config.load_config()
    except config.ConfigError as exc:
        log(f"CONFIG ERROR: {exc}")
        return 2

    tz = ZoneInfo(cfg["schedule"]["timezone"])
    digest_times = parse_digest_times(cfg["schedule"]["digest_times"])
    alert_interval = max(1, int(cfg["schedule"]["alert_poll_minutes"])) * 60
    weekdays_only = cfg["schedule"]["weekdays_only"]

    _install_signal_handlers()

    with open(PID_FILE, 'w') as f:
        f.write(str(os.getpid()))

    now_local = datetime.now(tz)
    # Times that already passed today are marked as fired, so a restart at
    # 16:45 does not immediately re-send the 16:30 digest. Anything missed
    # while the loop was down still appears in the next digest, because the
    # seen-ledger only suppresses headlines that were actually delivered.
    fired = {key for key, _ in due_digests(now_local, digest_times, set())}
    last_alert_poll = time.time() - alert_interval + 30

    log("=" * 60)
    log("NEWS LOOP STARTED")
    log(f"PID: {os.getpid()}")
    log(f"Timezone: {cfg['schedule']['timezone']}  (now {now_local:%Y-%m-%d %H:%M %Z})")
    log(f"Digests: {', '.join(f'{h:02d}:{m:02d}' for h, m in digest_times) or 'none'}")
    log(f"Alert poll: every {alert_interval // 60}min  ·  weekdays_only={weekdays_only}")
    log(f"Suppressed {len(fired)} digest slot(s) already past today")
    log("=" * 60)

    try:
        while True:
            now_local = datetime.now(tz)
            is_trading_day = not weekdays_only or now_local.weekday() < 5

            if is_trading_day:
                for key, hour in due_digests(now_local, digest_times, fired):
                    log(f"Digest due: {key}")
                    run_mode('digest', digest_label(hour))
                    fired.add(key)

                if time.time() - last_alert_poll >= alert_interval:
                    run_mode('alerts')
                    last_alert_poll = time.time()

            # Drop keys from previous days so `fired` cannot grow unbounded.
            today = now_local.date().isoformat()
            fired = {key for key in fired if key.startswith(today)}

            time.sleep(TICK_SECONDS)

    except KeyboardInterrupt:
        log("KeyboardInterrupt, shutting down...")
    except Shutdown as sig:
        log(f"{sig}, shutting down...")
    finally:
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
        log("NEWS LOOP STOPPED")

    return 0


if __name__ == '__main__':
    sys.exit(main())
