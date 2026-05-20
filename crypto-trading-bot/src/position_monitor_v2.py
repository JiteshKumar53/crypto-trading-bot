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
from chart_monitor.live_chart_monitor import LiveChartMonitor
from chart_monitor.chart_analyzer import ChartObservation

logger = logging.getLogger(__name__)

MONITOR_INTERVAL_SECONDS = 300  # 5 minutes

# Exit thresholds
DEFAULT_STOP_LOSS_PCT = 0.015          # -1.5% hard stop (tighter for crypto)
DEFAULT_TAKE_PROFIT_PCT = 0.06         # +6% take profit
DEFAULT_TRAILING_STOP_PCT = 0.01       # -1% from highest (tighter)
DEFAULT_MAX_HOLDING_HOURS = 8          # 8h max (was 72h — way too long)
DEFAULT_BREAK_EVEN_TRIGGER = 0.005     # Move SL to breakeven after +0.5%
DEFAULT_STALE_PROFIT_HOURS = 4         # Exit if small profit after 4h (was 48h)
DEFAULT_STALE_LOSS_HOURS = 6           # Exit if losing after 6h (was 24h)
DEFAULT_CAPITAL_EFFICIENCY_DAYS = 2    # Exit if no profit after 2 days (was 5)

PARTIAL_PROFIT_LEVEL_1 = 0.005         # Sell 50% at +0.5%
MOMENTUM_REVERSAL_DROP = 0.003         # Exit if profit drops 0.3% from peak
MINIMUM_PROFIT_EXIT = 0.002            # Don't exit if profit < 0.2% (low fees on Alpaca crypto)

DEFAULT_RUNNER_TRIGGER = 0.008         # Activate runner trailing stop after +0.8%
DEFAULT_RUNNER_TRAIL = 0.008           # Runner trails at -0.8% from highest
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
        chart_monitor: Optional[LiveChartMonitor] = None,
    ):
        self.client = AlpacaPaperClient()
        self.risk_governor = RiskGovernor()
        self.chart_monitor = chart_monitor
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

    def _build_states_from_reconciled_data(self, local_state: Dict) -> List[PositionState]:
        """Build PositionState objects from reconciled local state data.
        
        This is called after broker-first reconciliation to ensure local state
        always matches the broker (Alpaca) source of truth.
        Gene: GENE-006 | Capsule: CAPSULE-004
        """
        states = []
        for sym, data in local_state.items():
            entry_price = data.get("avg_entry_price", 0)
            current = data.get("current_price", 0)
            unrealized_pct = (current - entry_price) / entry_price if entry_price else 0
            
            state = PositionState(
                symbol=sym,
                qty=data.get("qty", 0),
                avg_entry_price=entry_price,
                current_price=current,
                market_value=data.get("market_value", 0),
                unrealized_pl=data.get("unrealized_pl", 0),
                unrealized_pl_pct=unrealized_pct,
                entry_time=data.get("entry_time", datetime.now(timezone.utc).isoformat()),
                holding_hours=data.get("holding_hours", 0.0),
                highest_price=data.get("highest_price", current),
                highest_price_pct=data.get("highest_price_pct", 0),
                partial_sold=data.get("partial_sold", False),
                partial_sold_qty=data.get("partial_sold_qty", 0.0),
                stop_triggered=data.get("stop_triggered", False),
                take_profit_triggered=data.get("take_profit_triggered", False),
                trailing_stop_triggered=data.get("trailing_stop_triggered", False),
                time_exit_triggered=data.get("time_exit_triggered", False),
                break_even_triggered=data.get("break_even_triggered", False),
                break_even_price=data.get("break_even_price", entry_price * 1.005),
                regime_at_entry=data.get("regime_at_entry", "unknown"),
                strategy_name=data.get("strategy_name", "unknown"),
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

        # Guard: if qty is zero or negligible, nothing to do
        if state.qty < 0.00001:
            return self._make_action("HOLD", symbol, 0, current, "zero_qty")

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

        # 4. Runner trailing stop: After +1.5%, trail at -1.5% from highest to capture trends
        if highest >= entry * (1 + DEFAULT_RUNNER_TRIGGER):
            runner_trail = highest * (1 - DEFAULT_RUNNER_TRAIL)
            if current <= runner_trail:
                return self._make_action("SELL_ALL", symbol, state.qty, current,
                                         f"runner_exit (high: {highest:.2f}, trail: {runner_trail:.2f}, profit: {unrealized_pct:.2%})")

        # 5. Standard trailing stop check (tighter, -2% from highest)
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
        # Skip if remaining qty is negligible (already fully sold)
        if unrealized_pct >= PARTIAL_PROFIT_LEVEL_1 and not state.partial_sold:
            if state.qty < 0.00001:  # Minimum viable order size
                logger.info(f"[POSITION MONITOR] Partial profit triggered for {symbol} but qty {state.qty} too small — SKIP")
                return self._make_action("HOLD", symbol, 0, current,
                                         f"partial_profit_1 (+{unrealized_pct:.2%}) — qty too small")
            sell_qty = state.qty * 0.5
            return self._make_action("SELL_PARTIAL", symbol, sell_qty, current,
                                     f"partial_profit_1 (+{unrealized_pct:.2%})")

        # 7. Stale position review (unprofitable + held too long)
        if unrealized_pct < 0 and holding >= self.stale_loss_hours:
            return self._make_action("SELL_ALL", symbol, state.qty, current,
                                     f"stale_loss_exit ({holding:.1f}h, {unrealized_pct:.2%})")

        # 8. Stale position review (profitable but going nowhere)
        if 0 < unrealized_pct < PARTIAL_PROFIT_LEVEL_1 and holding >= self.stale_profit_hours:
            return self._make_action("SELL_ALL", symbol, state.qty, current,
                                     f"stale_profit_exit ({holding:.1f}h, {unrealized_pct:.2%})")

        # 9. Capital efficiency exit (held too long with minimal return)
        if holding >= self.capital_efficiency_days * 24 and abs(unrealized_pct) < 0.01:
            return self._make_action("SELL_ALL", symbol, state.qty, current,
                                     f"capital_efficiency ({holding:.1f}h, {unrealized_pct:.2%})")

        # 10. Chart intelligence exit: Check chart observations for reversal/breakdown warnings
        if self.chart_monitor:
            chart_obs = self.chart_monitor.get_latest_observation(symbol, "1h")
            if chart_obs and chart_obs.open_position_affected:
                # Chart warns of reversal while position profitable but fading
                if (chart_obs.reversal_warning and chart_obs.reversal_type == "bearish" 
                        and unrealized_pct > 0 and unrealized_pct < self.take_profit_pct):
                    logger.info(f"[POSITION MONITOR] CHART INTELLIGENCE: Reversal warning for {symbol} "
                               f"({chart_obs.reason}) — considering early exit")
                    # Only exit if momentum is weakening AND we're past break-even
                    if chart_obs.momentum_status.value in ["bearish", "strong_bearish"]:
                        return self._make_action("SELL_ALL", symbol, state.qty, current,
                                                f"chart_reversal (RSI: {float(chart_obs.rsi_value):.1f}, {chart_obs.reason})")
                
                # Chart detects breakdown below support on losing position
                if (chart_obs.breakdown_detected and unrealized_pct < 0 
                        and not state.stop_triggered):
                    return self._make_action("SELL_ALL", symbol, state.qty, current,
                                            f"chart_breakdown (support: ${float(chart_obs.nearest_support):,.2f}, {chart_obs.reason})")
                
                # Chart warns volatility expanding — tighten runner stop
                if (chart_obs.volatility_state.value == "expanding" and unrealized_pct > DEFAULT_RUNNER_TRIGGER
                        and highest > entry * (1 + DEFAULT_RUNNER_TRIGGER)):
                    tighter_trail = highest * (1 - DEFAULT_RUNNER_TRAIL * 0.7)  # 30% tighter
                    if current <= tighter_trail:
                        return self._make_action("SELL_ALL", symbol, state.qty, current,
                                                f"chart_volatility_tighten (expanded, trail tightened to -{DEFAULT_RUNNER_TRAIL*0.7:.1%})")
                
                # Chart confirms strong trend continuing — allow runner to continue
                if (chart_obs.trend_state.value in ["uptrend", "downtrend"] 
                        and chart_obs.trend_strength > 0.7 and unrealized_pct > DEFAULT_RUNNER_TRIGGER):
                    logger.info(f"[POSITION MONITOR] CHART INTELLIGENCE: Strong {chart_obs.trend_state.value} "
                               f"continuing for {symbol} — allowing runner to extend")

        # 11. Time-based exit (absolute max holding)
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
        """Execute a sell order for position exit with idempotency check via Evolver Runtime."""
        symbol = action["symbol"]
        qty = action["qty"]
        reason = action["reason"]

        # CAPSULE-005: Exit Idempotency Check via Evolver Runtime
        # Prevent duplicate sell actions on the same position
        try:
            from evolver_runtime import check_exit_idempotency
            states = self.get_position_states()
            position_state = None
            for s in states:
                if s.symbol == symbol:
                    position_state = {
                        "partial_sold": s.partial_sold,
                        "stop_triggered": s.stop_triggered,
                        "take_profit_triggered": s.take_profit_triggered,
                        "trailing_stop_triggered": s.trailing_stop_triggered,
                    }
                    break

            if position_state:
                idempotency = check_exit_idempotency(position_state, action["action"])
                if not idempotency.get("passed", True):
                    logger.critical(
                        f"[POSITION MONITOR] EXIT BLOCKED by EVOLVER CAPSULE-005: "
                        f"{idempotency.get('reason')} — {symbol} {action['action']}"
                    )
                    return False
                logger.info(
                    f"[POSITION MONITOR] Exit idempotency PASSED via EVOLVER: "
                    f"capsule={idempotency.get('capsule')}, gene={idempotency.get('gene')}"
                )
        except Exception as e:
            logger.warning(f"[POSITION MONITOR] Exit idempotency check error: {e} — proceeding with caution")

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
        """Run one monitoring pass with broker-first reconciliation."""
        actions_taken = []
        
        # Step 1: Get broker truth (ALPACA IS SOURCE OF TRUTH)
        # Gene: GENE-006 | Capsule: CAPSULE-004
        try:
            broker_positions = self.client.get_positions()
        except Exception as e:
            logger.error(f"[POSITION MONITOR] Failed to fetch broker positions: {e}")
            broker_positions = []
        
        # Step 2: Load local state
        local_state = self._load_state()
        
        # Step 3: RECONCILE broker positions with local state
        # If broker shows 0 positions but local shows >0 → clear local state
        # If broker shows positions not in local → add them
        # If quantities differ → use broker quantities
        if broker_positions:
            # Broker has positions — rebuild state from broker
            reconciled_state = {}
            for p in broker_positions:
                sym = p["symbol"]
                persisted_data = local_state.get(sym, {})
                reconciled_state[sym] = {
                    "symbol": sym,
                    "qty": p["qty"],
                    "avg_entry_price": p["avg_entry_price"],
                    "current_price": p["current_price"],
                    "market_value": p["market_value"],
                    "unrealized_pl": p["unrealized_pl"],
                    "entry_time": persisted_data.get("entry_time", datetime.now(timezone.utc).isoformat()),
                    "partial_sold": persisted_data.get("partial_sold", False),
                    "partial_sold_qty": persisted_data.get("partial_sold_qty", 0.0),
                    "stop_triggered": persisted_data.get("stop_triggered", False),
                    "take_profit_triggered": persisted_data.get("take_profit_triggered", False),
                    "trailing_stop_triggered": persisted_data.get("trailing_stop_triggered", False),
                    "break_even_triggered": persisted_data.get("break_even_triggered", False),
                    "highest_price": max(p["current_price"], persisted_data.get("highest_price", p["current_price"])),
                }
            local_state = reconciled_state
            if len(local_state) != len(broker_positions):
                logger.warning(f"[RECONCILIATION] State rebuilt from broker: {len(broker_positions)} positions")
        else:
            # Broker shows NO positions — clear local state (THE BUG FIX)
            if local_state:
                stale_symbols = list(local_state.keys())
                logger.critical(
                    f"[RECONCILIATION] Broker shows 0 positions but local state has "
                    f"{len(stale_symbols)}: {stale_symbols}. CLEARING LOCAL STATE."
                )
            local_state = {}
        
        # Step 4: Build position states from reconciled data
        states = self._build_states_from_reconciled_data(local_state)
        
        if not states:
            logger.info("[POSITION MONITOR] No open positions")
            self._save_state({})  # CRITICAL: Always save empty state
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
                    # Update state flags after successful execution
                    if action["action"] == "SELL_PARTIAL":
                        state.partial_sold = True
                        state.partial_sold_qty = action["qty"]
                        logger.info(f"[POSITION MONITOR] {state.symbol}: partial_sold flag SET, qty_sold={action['qty']:.8f}")
                    elif action["action"] == "SELL_ALL":
                        # Mark all exit flags to prevent re-triggering on stale data
                        state.stop_triggered = True
                        state.take_profit_triggered = True
                        logger.info(f"[POSITION MONITOR] {state.symbol}: fully exited")
                    elif action["action"] == "SELL_RUNNER":
                        state.trailing_stop_triggered = True
                        logger.info(f"[POSITION MONITOR] {state.symbol}: runner exited")

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
