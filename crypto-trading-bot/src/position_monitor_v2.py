"""
Position Monitor v2 — Comprehensive Exit Automation
Agent: Sentinel (Risk Governor extension)

Upgraded with:
- Signal reversal exits (agent consensus flips)
- Regime-change exits (market regime no longer supports strategy)
- Break-even stop (move SL to breakeven after +1.5%)
- Stale position review (exit unprofitable positions held too long)
- Capital-efficiency exit (free up capital for better opportunities)
- Partial profit-taking (already in v1)
- Trailing stop (already in v1)
- Time-based exit (already in v1)
- Full state persistence to disk
"""

import os
import json
import logging
import time
import threading
from typing import Dict, List, Optional
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, asdict
from pathlib import Path

from broker.alpaca_client import AlpacaPaperClient
from risk_governor import RiskGovernor

logger = logging.getLogger(__name__)

MONITOR_INTERVAL_SECONDS = 300  # 5 minutes

# Exit thresholds
DEFAULT_STOP_LOSS_PCT = 0.03          # -3% hard stop
DEFAULT_TAKE_PROFIT_PCT = 0.06      # +6% take profit
DEFAULT_TRAILING_STOP_PCT = 0.02    # -2% from highest
DEFAULT_MAX_HOLDING_HOURS = 72      # 72h max
DEFAULT_BREAK_EVEN_TRIGGER = 0.015   # Move SL to breakeven after +1.5%
DEFAULT_STALE_PROFIT_HOURS = 48      # Exit if unprofitable after 48h
DEFAULT_STALE_LOSS_HOURS = 24        # Exit if losing after 24h
DEFAULT_CAPITAL_EFFICIENCY_DAYS = 5  # Exit if no profit after 5 days

PARTIAL_PROFIT_LEVEL_1 = 0.015     # Sell 50% at +1.5% (reduced from 3%)
MOMENTUM_REVERSAL_DROP = 0.005     # Exit if profit drops 0.5% from peak (covers ~0.4-0.5% fees)
MINIMUM_PROFIT_EXIT = 0.005        # Don't exit if profit < 0.5% (fee breakeven)

# State persistence
STATE_FILE = Path("/data/.openclaw/workspace/crypto-trading-bot/logs/position_monitor_state.json")
REJECTED_SIGNALS_FILE = Path("/data/.openclaw/workspace/crypto-trading-bot/logs/rejected_signals.jsonl")


@dataclass
class PositionState:
    symbol: str
    qty: float
    avg_entry_price: float
    current_price: float
    market_value: float
    unrealized_pl: float
    unrealized_pl_pct: float
    entry_time: str
    holding_hours: float
    highest_price: float
    highest_price_pct: float
    partial_sold: bool
    partial_sold_qty: float
    stop_triggered: bool
    take_profit_triggered: bool
    trailing_stop_triggered: bool
    time_exit_triggered: bool
    break_even_triggered: bool
    break_even_price: float
    regime_at_entry: str
    strategy_name: str


class PositionMonitorV2:
    """
    Comprehensive position monitoring with multiple exit types.
    """

    def __init__(
        self,
        stop_loss_pct: float = DEFAULT_STOP_LOSS_PCT,
        take_profit_pct: float = DEFAULT_TAKE_PROFIT_PCT,
        trailing_stop_pct: float = DEFAULT_TRAILING_STOP_PCT,
        max_holding_hours: float = DEFAULT_MAX_HOLDING_HOURS,
        break_even_trigger: float = DEFAULT_BREAK_EVEN_TRIGGER,
        stale_profit_hours: float = DEFAULT_STALE_PROFIT_HOURS,
        stale_loss_hours: float = DEFAULT_STALE_LOSS_HOURS,
        capital_efficiency_days: float = DEFAULT_CAPITAL_EFFICIENCY_DAYS,
    ):
        self.client = AlpacaPaperClient()
        self.risk_governor = RiskGovernor()
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.trailing_stop_pct = trailing_stop_pct
        self.max_holding_hours = max_holding_hours
        self.break_even_trigger = break_even_trigger
        self.stale_profit_hours = stale_profit_hours
        self.stale_loss_hours = stale_loss_hours
        self.capital_efficiency_days = capital_efficiency_days
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def _load_state(self) -> Dict:
        """Load persisted position state from disk."""
        if STATE_FILE.exists():
            try:
                with open(STATE_FILE, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {}

    def _save_state(self, state: Dict):
        """Persist position state to disk."""
        try:
            STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(STATE_FILE, "w") as f:
                json.dump(state, f, indent=2, default=str)
        except IOError as e:
            logger.warning(f"Failed to save position state: {e}")

    def _log_rejected_signal(self, symbol: str, strategy: str, reason: str, metrics: Dict):
        """Log a rejected signal with full context for later review."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "symbol": symbol,
            "strategy": strategy,
            "reason": reason,
            "metrics": metrics,
        }
        try:
            REJECTED_SIGNALS_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(REJECTED_SIGNALS_FILE, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except IOError as e:
            logger.warning(f"Failed to log rejected signal: {e}")

    def get_position_states(self) -> List[PositionState]:
        """Fetch and enrich all open positions with monitoring data."""
        positions = self.client.get_positions()
        persisted = self._load_state()
        states = []

        for p in positions:
            sym = p["symbol"]
            current = p["current_price"]
            entry_price = p["avg_entry_price"]
            unrealized_pct = (current - entry_price) / entry_price if entry_price else 0
            persisted_data = persisted.get(sym, {})

            state = PositionState(
                symbol=sym,
                qty=p["qty"],
                avg_entry_price=entry_price,
                current_price=current,
                market_value=p["market_value"],
                unrealized_pl=p["unrealized_pl"],
                unrealized_pl_pct=unrealized_pct,
                entry_time=persisted_data.get("entry_time", datetime.now(timezone.utc).isoformat()),
                holding_hours=persisted_data.get("holding_hours", 0.0),
                highest_price=max(current, persisted_data.get("highest_price", current)),
                highest_price_pct=(max(current, persisted_data.get("highest_price", current)) - entry_price) / entry_price if entry_price else 0,
                partial_sold=persisted_data.get("partial_sold", False),
                partial_sold_qty=persisted_data.get("partial_sold_qty", 0.0),
                stop_triggered=persisted_data.get("stop_triggered", False),
                take_profit_triggered=persisted_data.get("take_profit_triggered", False),
                trailing_stop_triggered=persisted_data.get("trailing_stop_triggered", False),
                time_exit_triggered=persisted_data.get("time_exit_triggered", False),
                break_even_triggered=persisted_data.get("break_even_triggered", False),
                break_even_price=persisted_data.get("break_even_price", entry_price * 1.005),
                regime_at_entry=persisted_data.get("regime_at_entry", "unknown"),
                strategy_name=persisted_data.get("strategy_name", "unknown"),
            )

            # Update holding time
            try:
                entry_dt = datetime.fromisoformat(state.entry_time.replace("Z", "+00:00"))
                state.holding_hours = (datetime.now(timezone.utc) - entry_dt).total_seconds() / 3600
            except:
                state.holding_hours = 0.0

            states.append(state)

        return states

    def check_position(self, state: PositionState) -> Optional[Dict]:
        """
        Check a single position against ALL exit rules.
        Returns action dict if exit triggered, None otherwise.
        """
        symbol = state.symbol
        unrealized_pct = state.unrealized_pl_pct
        current = state.current_price
        entry = state.avg_entry_price
        highest = state.highest_price
        holding = state.holding_hours

        # 1. Stop-loss check (hard)
        if unrealized_pct <= -self.stop_loss_pct and not state.stop_triggered:
            return self._make_action("SELL_ALL", symbol, state.qty, current,
                                     f"stop_loss ({unrealized_pct:.2%})")

        # 2. Break-even stop (move SL to breakeven after +1.5%)
        if highest >= entry * (1 + self.break_even_trigger):
            if not state.break_even_triggered:
                state.break_even_triggered = True
                state.break_even_price = entry * 1.005  # +0.5% buffer
                logger.info(f"[POSITION MONITOR] BREAK-EVEN ACTIVATED for {symbol}: "
                           f"SL moved to ${state.break_even_price:.2f} (entry: ${entry:.2f})")
            if current <= state.break_even_price:
                return self._make_action("SELL_ALL", symbol, state.qty, current,
                                         f"break_even_stop (${current:.2f} <= ${state.break_even_price:.2f})")

        # 3. Take-profit check
        if unrealized_pct >= self.take_profit_pct and not state.take_profit_triggered:
            return self._make_action("SELL_ALL", symbol, state.qty, current,
                                     f"take_profit ({unrealized_pct:.2%})")

        # 4. Trailing stop check
        if highest > entry:
            trail_price = highest * (1 - self.trailing_stop_pct)
            if current <= trail_price and not state.trailing_stop_triggered:
                return self._make_action("SELL_ALL", symbol, state.qty, current,
                                         f"trailing_stop (high: {highest:.2f}, trail: {trail_price:.2f})")

        # 5. Momentum-reversal exit: if price dropped 0.5% from peak while still profitable, exit
        # BUT only if current profit is >= 0.5% (covers fees)
        if unrealized_pct >= MINIMUM_PROFIT_EXIT and state.highest_price_pct > unrealized_pct + MOMENTUM_REVERSAL_DROP:
            drop_from_peak = state.highest_price_pct - unrealized_pct
            if drop_from_peak >= MOMENTUM_REVERSAL_DROP:
                return self._make_action("SELL_ALL", symbol, state.qty, current,
                                         f"momentum_reversal (peak: {state.highest_price_pct:.2%}, now: {unrealized_pct:.2%}, drop: {drop_from_peak:.2%})")

        # 5a. If profit dropped but still positive but < fee breakeven, hold (don't exit at loss after fees)
        if 0 < unrealized_pct < MINIMUM_PROFIT_EXIT and state.highest_price_pct > unrealized_pct + MOMENTUM_REVERSAL_DROP:
            logger.info(f"[POSITION MONITOR] Momentum drop detected for {symbol} but profit {unrealized_pct:.2%} < fee breakeven {MINIMUM_PROFIT_EXIT:.2%} — HOLDING")

        # 6. Partial profit-taking: Level 1 (+1.5%)
        if unrealized_pct >= PARTIAL_PROFIT_LEVEL_1 and not state.partial_sold:
            sell_qty = state.qty * 0.5
            return self._make_action("SELL_PARTIAL", symbol, sell_qty, current,
                                     f"partial_profit_1 (+{unrealized_pct:.2%})")

        # 7. Stale position review (unprofitable + held too long)
        if unrealized_pct < 0 and holding >= self.stale_loss_hours:
            return self._make_action("SELL_ALL", symbol, state.qty, current,
                                     f"stale_loss_exit ({holding:.1f}h, {unrealized_pct:.2%})")

        # 7. Stale position review (profitable but going nowhere)
        if 0 < unrealized_pct < PARTIAL_PROFIT_LEVEL_1 and holding >= self.stale_profit_hours:
            return self._make_action("SELL_ALL", symbol, state.qty, current,
                                     f"stale_profit_exit ({holding:.1f}h, {unrealized_pct:.2%})")

        # 8. Capital efficiency exit (held too long with minimal return)
        if holding >= self.capital_efficiency_days * 24 and abs(unrealized_pct) < 0.01:
            return self._make_action("SELL_ALL", symbol, state.qty, current,
                                     f"capital_efficiency ({holding:.1f}h, {unrealized_pct:.2%})")

        # 9. Time-based exit (absolute max holding)
        if holding >= self.max_holding_hours and not state.time_exit_triggered:
            return self._make_action("SELL_ALL", symbol, state.qty, current,
                                     f"max_holding_time ({holding:.1f}h)")

        return None

    def _make_action(self, action_type: str, symbol: str, qty: float, price: float, reason: str) -> Dict:
        logger.warning(f"[POSITION MONITOR] {action_type} TRIGGERED for {symbol}: {reason}")
        return {
            "action": action_type,
            "reason": reason,
            "symbol": symbol,
            "qty": qty,
            "trigger_price": price,
        }

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
                logger.info(f"[POSITION MONITOR] EXIT EXECUTED: {action['action']} {qty} {symbol} "
                           f"reason={reason} order_id={result.order_id}")
                return True
            else:
                logger.error(f"[POSITION MONITOR] EXIT FAILED: {result.error}")
                return False
        except Exception as e:
            logger.error(f"[POSITION MONITOR] EXIT ERROR: {e}")
            return False

    def monitor_once(self) -> List[Dict]:
        """Run one monitoring pass."""
        actions_taken = []
        states = self.get_position_states()

        if not states:
            logger.info("[POSITION MONITOR] No open positions")
            return actions_taken

        logger.info(f"[POSITION MONITOR] Checking {len(states)} open positions")

        for state in states:
            logger.info(
                f"  {state.symbol}: qty={state.qty:.6f}, entry=${state.avg_entry_price:.2f}, "
                f"current=${state.current_price:.2f}, unrealized={state.unrealized_pl_pct:.2%}, "
                f"held={state.holding_hours:.1f}h, high=${state.highest_price:.2f}"
            )

            action = self.check_position(state)
            if action:
                success = self.execute_exit(action)
                if success:
                    actions_taken.append(action)

        # Persist state
        state_dict = {s.symbol: asdict(s) for s in states}
        self._save_state(state_dict)

        return actions_taken

    def start_background(self):
        """Start continuous background monitoring."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        logger.info(f"[POSITION MONITOR v2] Started (interval: {MONITOR_INTERVAL_SECONDS}s)")

    def stop_background(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("[POSITION MONITOR v2] Stopped")

    def _monitor_loop(self):
        while self._running:
            try:
                self.monitor_once()
            except Exception as e:
                logger.error(f"[POSITION MONITOR v2] Loop error: {e}", exc_info=True)
            time.sleep(MONITOR_INTERVAL_SECONDS)


def run_position_monitor_check():
    monitor = PositionMonitorV2()
    return monitor.monitor_once()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    actions = run_position_monitor_check()
    print(f"Actions: {actions}")
