#!/bin/bash
# EA System Health Check — Checks if ea_loop.py is running

PID_FILE="/data/.openclaw/workspace/crypto-trading-bot/bots/ea_system/logs/ea_loop.pid"
HEARTBEAT_FILE="/data/.openclaw/workspace/crypto-trading-bot/bots/ea_system/logs/ea_heartbeat.json"
ALERT_LOG="/data/.openclaw/workspace/crypto-trading-bot/bots/ea_system/logs/heartbeat_alerts.log"
MAX_AGE_HOURS=1

now_epoch=$(date -u +%s)

# Check if loop process is running
if [ -f "$PID_FILE" ]; then
    pid=$(cat "$PID_FILE")
    if ps -p "$pid" > /dev/null 2>&1; then
        loop_status="RUNNING (PID $pid)"
    else
        loop_status="DEAD (PID $pid not found)"
        echo "$(date -u '+%Y-%m-%dT%H:%M:%SZ') — ALERT: ea_loop.py is dead" >> "$ALERT_LOG"
    fi
else
    loop_status="NOT FOUND (no PID file)"
    echo "$(date -u '+%Y-%m-%dT%H:%M:%SZ') — ALERT: ea_loop.py PID file missing" >> "$ALERT_LOG"
fi

# Check heartbeat age
if [ -f "$HEARTBEAT_FILE" ]; then
    last_check=$(grep -o '"last_check_utc": "[^"]*"' "$HEARTBEAT_FILE" | sed 's/.*"\(.*\)".*/\1/')
    last_check_clean=$(echo "$last_check" | sed 's/+.*//' | sed 's/Z$//')
    last_epoch=$(date -u -d "$last_check_clean" +%s 2>/dev/null || echo "0")
    
    if [ "$last_epoch" != "0" ]; then
        age_seconds=$((now_epoch - last_epoch))
        age_hours=$(awk "BEGIN {printf \"%.1f\", $age_seconds / 3600}")
        
        if [ "$age_seconds" -gt $((MAX_AGE_HOURS * 3600)) ]; then
            hb_status="STALE (${age_hours}h ago)"
            echo "$(date -u '+%Y-%m-%dT%H:%M:%SZ') — ALERT: Heartbeat stale (${age_hours}h)" >> "$ALERT_LOG"
        else
            hb_status="OK (${age_hours}h ago)"
        fi
    else
        hb_status="UNPARSEABLE"
    fi
else
    hb_status="MISSING"
fi

echo "$(date -u '+%Y-%m-%dT%H:%M:%SZ') — Loop: $loop_status | Heartbeat: $hb_status"

