#!/bin/bash
# Generate CEO report every 30 minutes via cron
# Output goes to predictable file that CEO can read

cd /data/.openclaw/workspace/crypto-trading-bot

# Load env
export $(grep -v '^#' .env | grep '=' | xargs)

# Generate report and save to timestamped file
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
python3 src/ceo_reporting_watchdog.py --report-now > "logs/ceo_report_${TIMESTAMP}.txt" 2>&1

# Also write to "latest" file for easy access
cp "logs/ceo_report_${TIMESTAMP}.txt" "logs/ceo_report_LATEST.txt"

# Log delivery attempt
echo "$(date): Report generated: logs/ceo_report_${TIMESTAMP}.txt" >> logs/ceo_watchdog.log
