#!/bin/bash
# Smart EA Bot Health Check Script
# Checks if daemon heartbeat is recent

HEARTBEAT_FILE="/data/.openclaw/workspace/crypto-trading-bot/bots/ea_system/logs/ea_heartbeat.json"
ALERT_LOG="/data/.openclaw/workspace/crypto-trading-bot/bots/ea_system/logs/heartbeat_alerts.log"
MAX_AGE_HOURS=1

now_epoch=$(date -u +%s)

if [ ! -f "$HEARTBEAT_FILE" ]; then
    echo "$(date -u '+%Y-%m-%dT%H:%M:%SZ') — CRITICAL ALERT: Heartbeat file not found at $HEARTBEAT_FILE" >> "$ALERT_LOG"
    exit 1
fi

# Extract last_check_utc from JSON
last_check=$(grep -o '"last_check_utc": "[^"]*"' "$HEARTBEAT_FILE" | sed 's/.*"\(.*\)".*/\1/')

if [ -z "$last_check" ]; then
    echo "$(date -u '+%Y-%m-%dT%H:%M:%SZ') — CRITICAL ALERT: Cannot parse last_check_utc from heartbeat" >> "$ALERT_LOG"
    exit 1
fi

# Convert ISO timestamp to epoch seconds
last_check_clean=$(echo "$last_check" | sed 's/+.*//' | sed 's/Z$//')
last_epoch=$(date -u -d "$last_check_clean" +%s 2>/dev/null || echo "0")

if [ "$last_epoch" = "0" ]; then
    echo "$(date -u '+%Y-%m-%dT%H:%M:%SZ') — CRITICAL ALERT: Cannot parse timestamp: $last_check" >> "$ALERT_LOG"
    exit 1
fi

age_seconds=$((now_epoch - last_epoch))
# Use awk instead of bc for floating point
age_hours=$(awk "BEGIN {printf \"%.1f\", $age_seconds / 3600}")

if [ "$age_seconds" -gt $((MAX_AGE_HOURS * 3600)) ]; then
    echo "$(date -u '+%Y-%m-%dT%H:%M:%SZ') — ALERT: Last heartbeat was ${age_hours}h ago (>${MAX_AGE_HOURS}h threshold)" >> "$ALERT_LOG"
    exit 1
else
    echo "$(date -u '+%Y-%m-%dT%H:%M:%SZ') — OK: Heartbeat ${age_hours}h ago"
    exit 0
fi
