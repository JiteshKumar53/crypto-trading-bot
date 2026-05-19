#!/bin/bash
# Jarvis Autonomous Daemon Startup Wrapper

# Load environment variables
cd /data/.openclaw/workspace/crypto-trading-bot
export ALPACA_API_KEY="PKFL22AHRJSJ5HWYTWFSVXGZ35"
export ALPACA_SECRET_KEY="$(grep ALPACA_SECRET_KEY .env | cut -d= -f2)"
export ALPACA_PAPER="true"
export ALPACA_BASE_URL="https://paper-api.alpaca.markets"
export PYTHONPATH="/data/.openclaw/workspace/crypto-trading-bot/src"

# Remove stale PID
rm -f /tmp/jarvis_autonomous_daemon.pid

# Start daemon
exec python3 scripts/autonomous_daemon.py >> logs/daemon.log 2>&1
