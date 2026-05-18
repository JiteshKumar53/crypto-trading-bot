#!/usr/bin/env python3
"""
Crypto Trading Bot — Main Entry Point
Junior CEO: Jarvis
CEO: Jitesh Kumar

This script initializes the trading system and runs the decision pipeline.
All trading is paper trading only.
Live trading requires explicit CEO approval.
"""

import os
import sys
import yaml
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from orchestrator import TradingOrchestrator
from risk_governor import RiskGovernor
from broker.alpaca_client import AlpacaPaperClient
from memory.decision_log import DecisionLog

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/trading_bot.log"),
    ],
)
logger = logging.getLogger(__name__)


def load_config(path: str) -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)


def main():
    logger.info("=" * 60)
    logger.info("Crypto Trading Bot Starting")
    logger.info("Mode: PAPER TRADING ONLY")
    logger.info("Junior CEO: Jarvis")
    logger.info("CEO: Jitesh Kumar")
    logger.info("=" * 60)

    # Load configs
    config_dir = Path(__file__).parent.parent / "config"
    risk_config = load_config(config_dir / "risk_limits.yaml")
    assets_config = load_config(config_dir / "assets.yaml")
    alpaca_config = load_config(config_dir / "alpaca.yaml")

    # Verify paper mode
    if risk_config["mode"] != "paper" or alpaca_config["mode"] != "paper":
        logger.error("System not in paper mode. Aborting.")
        logger.error("Live trading requires explicit CEO approval.")
        sys.exit(1)

    logger.info("Paper mode verified.")
    logger.info(f"Assets: {[a['symbol'] for a in assets_config['assets']]}")
    logger.info(f"Risk limits: max_allocation={risk_config['account']['max_allocation_per_asset']:.0%}")

    # Initialize components
    try:
        risk_governor = RiskGovernor()
        orchestrator = TradingOrchestrator(risk_governor)
        decision_log = DecisionLog()
        logger.info("Core components initialized.")
    except Exception as e:
        logger.error(f"Failed to initialize components: {e}")
        sys.exit(1)

    # Try to initialize Alpaca client (requires env vars)
    try:
        alpaca = AlpacaPaperClient()
        account = alpaca.get_account()
        if account:
            logger.info(f"Alpaca paper account connected: ${account['portfolio_value']:.2f}")
        else:
            logger.warning("Alpaca client initialized but account info unavailable.")
    except ValueError as e:
        logger.warning(f"Alpaca client not available: {e}")
        logger.info("Set ALPACA_API_KEY and ALPACA_SECRET_KEY environment variables.")
        alpaca = None
    except Exception as e:
        logger.warning(f"Alpaca client initialization failed: {e}")
        alpaca = None

    logger.info("System ready for trading pipeline.")
    logger.info("Waiting for trading signals...")

    # Main loop placeholder
    # In production, this would listen for signals and run the pipeline
    logger.info("To run a trade through the full pipeline, use the orchestrator.run_pipeline() method.")

    # Example: Print current decision log
    decisions = decision_log.get_recent(5)
    if decisions:
        logger.info(f"Recent decisions: {len(decisions)}")
    else:
        logger.info("No decisions logged yet.")


if __name__ == "__main__":
    main()
