#!/bin/bash
# Install Jarvis CEO Reporting Watchdog as systemd service
set -e

echo "Installing Jarvis Reporting Watchdog..."

# Copy service file
sudo cp /data/.openclaw/workspace/crypto-trading-bot/scripts/jarvis-reporting-watchdog.service /etc/systemd/system/
sudo systemctl daemon-reload

# Enable and start
sudo systemctl enable jarvis-reporting-watchdog.service
sudo systemctl start jarvis-reporting-watchdog.service

# Check status
sleep 2
sudo systemctl status jarvis-reporting-watchdog.service --no-pager

echo "Watchdog installed. Logs: /data/.openclaw/workspace/crypto-trading-bot/logs/reporting_watchdog_service.log"
echo "Health: /data/.openclaw/workspace/crypto-trading-bot/logs/reporting_watchdog_health.json"
