#!/usr/bin/env python3
"""
Autonomous Trading Pipeline Runner
Runs the full agent pipeline + trading cycle automatically.
Designed for cron execution every 4 hours.

Usage:
    python3 scripts/autonomous_pipeline.py [--asset BTC/USD]
"""

import sys
sys.path.insert(0, '/data/.openclaw/workspace/crypto-trading-bot/src')

import os
import json
import logging
import argparse
from datetime import datetime, timezone
from pathlib import Path

from pipeline_controller_v2 import PipelineController
from agents.agent_runner import AgentRunner
from data.data_fetcher import DataFetcher
from broker.alpaca_client import AlpacaPaperClient
from dashboard import dashboard_generator as dg

# ENTRY LOCK: Check if new entries are halted
ENTRY_LOCK_PATH = Path('/data/.openclaw/workspace/crypto-trading-bot/ENTRY_LOCK')
if ENTRY_LOCK_PATH.exists():
    print("[ENTRY LOCK] NEW ENTRIES ARE HALTED. ENTRY_LOCK file exists.")
    print("[ENTRY LOCK] Cannot run pipeline until ENTRY_LOCK is removed.")
    print("[ENTRY LOCK] EA Core integration not yet complete.")
    exit(1)

# Setup logging
log_dir = Path('/data/.openclaw/workspace/crypto-trading-bot/logs')
log_dir.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_dir / 'autonomous_pipeline.log'),
    ]
)
logger = logging.getLogger(__name__)


def run_autonomous_cycle(asset: str = None):
    """Run one full autonomous trading cycle."""
    cycle_start = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    logger.info(f"=== AUTONOMOUS CYCLE START: {cycle_start} ===")

    try:
        # Initialize
        client = AlpacaPaperClient()
        controller = PipelineController(
            use_agents=True,
            use_backtest=True,
            use_risk_governor=True,
            paper_only=True,
        )

        # Run pipeline
        if asset:
            results = controller.run_cycle(asset)
        else:
            results = controller.run_cycle()

        # Update dashboard
        account = client.get_account()
        if account:
            dg.write_dashboard(account)
            logger.info("Dashboard updated")

        # Log summary
        logger.info(f"=== CYCLE COMPLETE ===")
        for sym, data in results.get('stages', {}).items():
            approved = data.get('approved', False)
            status = "APPROVED" if approved else "REJECTED/BLOCKED"
            logger.info(f"  {sym}: {status}")

        # Write cycle report
        report_path = log_dir / f"cycle_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w') as f:
            json.dump({
                'timestamp': cycle_start,
                'asset': asset,
                'results': {k: str(v) for k, v in results.items()},
            }, f, indent=2)

        return results

    except Exception as e:
        logger.error(f"Autonomous cycle failed: {e}", exc_info=True)
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--asset', default=None, help='Specific asset to trade')
    args = parser.parse_args()

    run_autonomous_cycle(args.asset)
