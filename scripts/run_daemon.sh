#!/bin/bash
# Smart EA Bot Daemon Wrapper
# Loads environment and runs daemon with logging

set -e

LOG_DIR="/data/.openclaw/workspace/logs"
DAEMON_DIR="/data/.openclaw/workspace/crypto-trading-bot/smart-ea-bot/core"

echo "$(date -u '+%Y-%m-%dT%H:%M:%SZ') — Starting daemon"

cd "$DAEMON_DIR"
python3 paper_daemon.py >> "$LOG_DIR/daemon.log" 2>> "$LOG_DIR/daemon_error.log"

exit_code=$?
echo "$(date -u '+%Y-%m-%dT%H:%M:%SZ') — Daemon exited with code $exit_code"
