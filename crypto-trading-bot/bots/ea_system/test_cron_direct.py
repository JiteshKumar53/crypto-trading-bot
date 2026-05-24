#!/usr/bin/env python3
"""Test if cron can execute Python that writes to a file directly."""
import os
from datetime import datetime, timezone

log_path = '/data/.openclaw/workspace/crypto-trading-bot/bots/ea_system/logs/cron_direct_test.log'
with open(log_path, 'a') as f:
    f.write(f"[{datetime.now(timezone.utc).isoformat()}] Direct write test from cron\n")
