"""
Smart EA Bot Company — Paper Trading Attribution Logger
Tracks every paper trade with full attribution data.
"""

import json
import os
from datetime import datetime, timezone
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

LOG_DIR = "data/paper_logs"
os.makedirs(LOG_DIR, exist_ok=True)


def log_trade(
    asset: str,
    side: str,
    signal_time: str,
    expected_price: float,
    actual_fill_price: float,
    qty: float,
    fees: float,
    regime_state: Dict,
) -> None:
    """Log a single paper trade with full attribution."""
    
    slippage_bps = ((actual_fill_price - expected_price) / expected_price) * 10000 if expected_price > 0 else 0
    
    trade_record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "asset": asset,
        "side": side,
        "signal_time": signal_time,
        "expected_price": round(expected_price, 2),
        "actual_fill_price": round(actual_fill_price, 2),
        "slippage_bps": round(slippage_bps, 2),
        "qty": round(qty, 6),
        "fees": round(fees, 4),
        "regime": {
            "sma50_distance_pct": round(regime_state.get("sma50_distance_pct", 0), 4),
            "trend_strength": regime_state.get("trend_strength", "unknown"),
            "volatility_regime": regime_state.get("volatility_regime", "unknown"),
        },
    }
    
    log_file = os.path.join(LOG_DIR, f"trades_{datetime.now(timezone.utc).strftime('%Y%m')}.jsonl")
    with open(log_file, "a") as f:
        f.write(json.dumps(trade_record) + "\n")
    
    logger.info(f"📊 Trade logged: {side} {asset} @ {actual_fill_price:.2f} (slippage: {slippage_bps:.1f} bps)")


def log_daily_reconciliation(
    date: str,
    paper_pnl: float,
    backtest_expected_pnl: float,
    divergence_pct: float,
    regime_summary: Dict,
) -> None:
    """Log daily reconciliation between paper and backtest."""
    
    record = {
        "date": date,
        "paper_pnl": round(paper_pnl, 4),
        "backtest_expected_pnl": round(backtest_expected_pnl, 4),
        "divergence_pct": round(divergence_pct, 4),
        "regime_summary": regime_summary,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    
    log_file = os.path.join(LOG_DIR, "daily_reconciliation.jsonl")
    with open(log_file, "a") as f:
        f.write(json.dumps(record) + "\n")
    
    status = "🟢" if abs(divergence_pct) < 5 else "🟡" if abs(divergence_pct) < 10 else "🔴"
    logger.info(f"{status} Daily reconciliation: divergence {divergence_pct:.2f}%")


def get_recent_trades(days: int = 30) -> list:
    """Get recent trades for divergence analysis."""
    trades = []
    log_file = os.path.join(LOG_DIR, f"trades_{datetime.now(timezone.utc).strftime('%Y%m')}.jsonl")
    
    if not os.path.exists(log_file):
        return trades
    
    with open(log_file) as f:
        for line in f:
            trade = json.loads(line.strip())
            trade_date = datetime.fromisoformat(trade["timestamp"]).date()
            if (datetime.now(timezone.utc).date() - trade_date).days <= days:
                trades.append(trade)
    
    return trades
