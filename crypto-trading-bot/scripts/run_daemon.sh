#!/bin/bash
# Smart EA Bot Daemon Wrapper
# Loads environment and runs daemon with logging
# Run from repo root: bash scripts/run_daemon.sh

set -e

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
LOG_DIR="$REPO_DIR/logs"
DAEMON_DIR="$REPO_DIR/smart-ea-bot/core"

mkdir -p "$LOG_DIR"

echo "$(date -u '+%Y-%m-%dT%H:%M:%SZ') — Starting daemon"

cd "$DAEMON_DIR"
python3 paper_daemon.py >> "$LOG_DIR/daemon.log" 2>> "$LOG_DIR/daemon_error.log"

exit_code=$?
echo "$(date -u '+%Y-%m-%dT%H:%M:%SZ') — Daemon exited with code $exit_code"
