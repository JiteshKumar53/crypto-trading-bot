"""
Position Monitor — Continuous Open Position Supervision
Agent: Sentinel (Risk Governor extension)

Monitors open positions every 5 minutes:
- Unrealized PnL
- Drawdown from entry
- Holding time
- Stop-loss / take-profit / trailing stop triggers
- Auto-executes sell orders when thresholds hit

This capability was NOT implemented before 2026-05-19.
Added as critical safety gap fix.
"""

import os
import logging
import time
import threading
from typing import Dict, List, Optional
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass
from pathlib import Path

from broker.alpaca_client import AlpacaPaperClient
from risk_governor import RiskGovernor

logger = logging.getLogger(__name__)

MONITOR_INTERVAL_SECONDS = 300  # 5 minutes

# Default position-level risk rules
DEFAULT_STOP_LOSS_PCT = 0.03      # 3% stop-loss
DEFAULT_TAKE_PROFIT_PCT = 0.06    # 6% take-profit
DEFAULT_TRAILING_STOP_PCT = 0.02  # 2% trailing stop
DEFAULT_MAX_HOLDING_HOURS = 72    # 72 hours max holding time

# Partial profit-taking levels
PARTIAL_PROFIT_LEVEL_1 = 0.03     # Sell 50% at +3%
PARTIAL_PROFIT_LEVEL_2 = 0.06     # Sell remaining 50% at +6%


@dataclass
class PositionState:
    symbol: str
    qty: float
    avg_entry_price: float
    current_price: float
    market_value: float
    unrealized_pl: float
    unrealized_pl_pct: float
    entry_time: datetime
    holding_hours: float
    highest_price: float  # For trailing stop
    partial_sold: bool = False  # Whether 50% was already sold
    stop_triggered: bool = False
    take_profit_triggered: bool = False
    trailing_stop_triggered: bool = False
    time_exit_triggered: bool = False


class PositionMonitor:
    """
    Continuous position monitoring.
    Runs in background thread or called on schedule.
    """

    def __init__(
        self,
        stop_loss_pct: float = DEFAULT_STOP_LOSS_PCT,
        take_profit_pct: float = DEFAULT_TAKE_PROFIT_PCT,
        trailing_stop_pct: float = DEFAULT_TRAILING_STOP_PCT,
        max_holding_hours: float = DEFAULT_MAX_HOLDING_HOURS,
    ):
        self.client = AlpacaPaperClient()
        self.risk_governor = RiskGovernor()
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.trailing_stop_pct = trailing_stop_pct
        self.max_holding_hours = max_holding_hours
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._state_file = Path("/data/.openclaw/workspace/crypto-trading-bot/logs/position_monitor_state.json")

    def get_position_states(self) -> List[PositionState]:
        """Fetch and enrich all open positions with monitoring data."""
        positions = self.client.get_positions()
        states = []
        for p in positions:
            state = PositionState(
                symbol=p["symbol"],
                qty=p["qty"],
                avg_entry_price=p["avg_entry_price"],
                current_price=p["current_price"],
                market_value=p["market_value"],
                unrealized_pl=p["unrealized_pl"],
                unrealized_pl_pct=p["unrealized_plpc"],
                entry_time=self._estimate_entry_time(p["symbol"]),
                holding_hours=0.0,
                highest_price=p["current_price"],
            )
            state.holding_hours = (datetime.now(timezone.utc) - state.entry_time).total_seconds() / 3600
            state.highest_price = self._load_highest_price(p["symbol"], p["current_price"])
            state.partial_sold = self._load_partial_sold(p["symbol"])
            states.append(state)
        return states

    def _estimate_entry_time(self, symbol: str) -> datetime:
        """Estimate entry time from filled orders."""
        try:
            from alpaca.trading.requests import GetOrdersRequest
            from alpaca.trading.enums import QueryOrderStatus
            orders = self.client.trading_client.get_orders(
                filter=GetOrdersRequest(status=QueryOrderStatus.ALL)
            )
            for o in orders:
                if o.symbol == symbol and o.side.value == "buy" and o.status.value == "filled":
                    return o.filled_at.astimezone(timezone.utc) if o.filled_at else datetime.now(timezone.utc)
        except Exception as e:
            logger.warning(f"Could not fetch order history for {symbol}: {e}")
        return datetime.now(timezone.utc) - timedelta(hours=24)  # Fallback

    def _load_highest_price(self, symbol: str, current: float) -> float:
        """Load highest price seen for trailing stop."""
        # Simple in-memory tracking. In production, persist to file.
        return max(current, current)  # Placeholder — will enhance

    def _load_partial_sold(self, symbol: str) -> bool:
        """Check if partial profit was already taken."""
        return False  # Placeholder — will enhance with state persistence

    def check_position(self, state: PositionState) -> Optional[Dict]:
        """
        Check a single position against all exit rules.
        Returns action dict if exit triggered, None otherwise.
        """
        symbol = state.symbol
        unrealized_pct = state.unrealized_pl_pct
        current = state.current_price
        highest = state.highest_price

        # 1. Stop-loss check
        if unrealized_pct <= -self.stop_loss_pct and not state.stop_triggered:
            logger.warning(
                f"[POSITION MONITOR] STOP-LOSS TRIGGERED for {symbol}: "
                f"unrealized {unrealized_pct:.2%} <= -{self.stop_loss_pct:.0%}"
            )
            return {
                "action": "SELL_ALL",
                "reason": f"stop_loss ({unrealized_pct:.2%})",
                "symbol": symbol,
                "qty": state.qty,
                "trigger_price": current,
            }

        # 2. Take-profit check
        if unrealized_pct >= self.take_profit_pct and not state.take_profit_triggered:
            logger.warning(
                f"[POSITION MONITOR] TAKE-PROFIT TRIGGERED for {symbol}: "
                f"unrealized {unrealized_pct:.2%} >= +{self.take_profit_pct:.0%}"
            )
            return {
                "action": "SELL_ALL",
                "reason": f"take_profit ({unrealized_pct:.2%})",
                "symbol": symbol,
                "qty": state.qty,
                "trigger_price": current,
            }

        # 3. Trailing stop check
        if highest > state.avg_entry_price:
            trail_price = highest * (1 - self.trailing_stop_pct)
            if current <= trail_price and not state.trailing_stop_triggered:
                logger.warning(
                    f"[POSITION MONITOR] TRAILING STOP TRIGGERED for {symbol}: "
                    f"price {current:.2f} <= trail {trail_price:.2f} (high: {highest:.2f})"
                )
                return {
                    "action": "SELL_ALL",
                    "reason": f"trailing_stop (high: {highest:.2f}, trail: {trail_price:.2f})",
                    "symbol": symbol,
                    "qty": state.qty,
                    "trigger_price": current,
                }

        # 4. Max holding time check
        if state.holding_hours >= self.max_holding_hours and not state.time_exit_triggered:
            logger.warning(
                f"[POSITION MONITOR] TIME EXIT TRIGGERED for {symbol}: "
                f"held {state.holding_hours:.1f}h >= {self.max_holding_hours}h"
            )
            return {
                "action": "SELL_ALL",
                "reason": f"max_holding_time ({state.holding_hours:.1f}h)",
                "symbol": symbol,
                "qty": state.qty,
                "trigger_price": current,
            }

        # 5. Partial profit-taking: Level 1 (+3%)
        if unrealized_pct >= PARTIAL_PROFIT_LEVEL_1 and not state.partial_sold:
            sell_qty = state.qty * 0.5
            logger.info(
                f"[POSITION MONITOR] PARTIAL PROFIT 1 for {symbol}: "
                f"selling 50% ({sell_qty:.6f}) at +{unrealized_pct:.2%}"
            )
            return {
                "action": "SELL_PARTIAL",
                "reason": f"partial_profit_1 (+{unrealized_pct:.2%})",
                "symbol": symbol,
                "qty": sell_qty,
                "trigger_price": current,
            }

        return None

    def execute_exit(self, action: Dict) -> bool:
        """Execute a sell order for position exit."""
        symbol = action["symbol"]
        qty = action["qty"]
        reason = action["reason"]

        try:
            result = self.client.submit_order(
                symbol=symbol,
                side="sell",
                qty=qty,
            )
            if result.success:
                logger.info(
                    f"[POSITION MONITOR] EXIT EXECUTED: {action['action']} {qty} {symbol} "
                    f"reason={reason} order_id={result.order_id}"
                )
                # Update Risk Governor state
                self.risk_governor.update_after_trade(
                    symbol=symbol,
                    realized_pnl=0,  # Will be updated on fill confirmation
                    portfolio_value=self.client.get_account()["portfolio_value"],
                )
                return True
            else:
                logger.error(f"[POSITION MONITOR] EXIT FAILED: {result.error}")
                return False
        except Exception as e:
            logger.error(f"[POSITION MONITOR] EXIT ERROR: {e}")
            return False

    def monitor_once(self) -> List[Dict]:
        """Run one monitoring pass. Returns list of actions taken."""
        actions_taken = []
        states = self.get_position_states()

        if not states:
            logger.info("[POSITION MONITOR] No open positions to monitor")
            return actions_taken

        logger.info(f"[POSITION MONITOR] Checking {len(states)} open positions")

        for state in states:
            logger.info(
                f"  {state.symbol}: qty={state.qty:.6f}, "
                f"entry=${state.avg_entry_price:.2f}, current=${state.current_price:.2f}, "
                f"unrealized={state.unrealized_pl_pct:.2%}, "
                f"held={state.holding_hours:.1f}h"
            )

            action = self.check_position(state)
            if action:
                success = self.execute_exit(action)
                if success:
                    actions_taken.append(action)

        return actions_taken

    def start_background(self):
        """Start continuous background monitoring thread."""
        if self._running:
            logger.warning("Position monitor already running")
            return

        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        logger.info(f"[POSITION MONITOR] Background monitoring started (interval: {MONITOR_INTERVAL_SECONDS}s)")

    def stop_background(self):
        """Stop background monitoring thread."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("[POSITION MONITOR] Background monitoring stopped")

    def _monitor_loop(self):
        """Background monitoring loop."""
        while self._running:
            try:
                self.monitor_once()
            except Exception as e:
                logger.error(f"[POSITION MONITOR] Loop error: {e}", exc_info=True)
            time.sleep(MONITOR_INTERVAL_SECONDS)


def run_position_monitor_check():
    """One-shot position monitor check (for cron or manual call)."""
    monitor = PositionMonitor()
    return monitor.monitor_once()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    monitor = PositionMonitor()
    actions = monitor.monitor_once()
    if actions:
        print(f"Actions taken: {actions}")
    else:
        print("No actions needed")
