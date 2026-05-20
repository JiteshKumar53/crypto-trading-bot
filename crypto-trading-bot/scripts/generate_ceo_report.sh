#!/bin/bash
# CEO Report Generation Script
# This script generates a report and saves it locally.
# The assistant session must then deliver it to the CEO.

cd /data/.openclaw/workspace/crypto-trading-bot

# Load environment
export $(grep -v '^#' .env | grep '=' | xargs)

# Generate report
REPORT_OUTPUT=$(python3 src/ceo_reporting_watchdog.py --report-now 2>&1)
REPORT_STATUS=$?

# Save report with timestamp
TIMESTAMP=$(date -u +"%Y%m%d_%H%M%S")
echo "$REPORT_OUTPUT" > "logs/ceo_report_${TIMESTAMP}.txt"

# Write delivery request file
cat > logs/ceo_delivery_request.json <> EOFDELIVERY
{
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "report_file": "logs/ceo_report_${TIMESTAMP}.txt",
  "report_status": "$([ $REPORT_STATUS -eq 0 ] && echo 'generated' || echo 'failed')",
  "delivery_status": "pending",
  "requested_delivery": true,
  "next_report_due": "$(date -d '+30 minutes' -u +"%H:%M %Z")"
}
EOFDELIVERY

echo "Report generated: logs/ceo_report_${TIMESTAMP}.txt"
echo "Delivery requested: logs/ceo_delivery_request.json"
