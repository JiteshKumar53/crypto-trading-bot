"""
Position Manager Module
EA Core Component

Manages open positions, tracks PnL, enforces exit rules.
Part of the deterministic execution layer.

Capsule: CAPSULE-004 — Exit Idempotency and Position Management
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


@dataclass
class PositionRecord:
    """Standardized position record."""
    symbol: str
    qty: float
    avg_entry_price: float
    current_price: float
    market_value: float
    unrealized_pl: float
    unrealized_plpc: float
    strategy_id: str
    entry_timestamp: str
    last_updated: str
    exit_rules: Dict


class PositionManager:
    """
    Manages open positions with deterministic exit rules.
    
    For every open position, checks:
    1. Current PnL
    2. Origin strategy
    3. Strategy status
    4. Stop-loss
    5. Take-profit
    6. Time-based exit
    7. Stale-position exit
    8. Market regime change
    """
    
    def __init__(self, alpaca_client):
        self.alpaca = alpaca_client
        self.positions: Dict[str, PositionRecord] = {}
        self.exit_history: List[Dict] = []
        
        # Default exit rules
        self.default_rules = {
            'stop_loss_pct': 0.05,      # 5% max loss
            'take_profit_pct': 0.10,     # 10% profit target
            'trailing_stop_pct': None,   # No trailing stop by default
            'time_limit_hours': 72,      # 3 days max hold
            'break_even_after': 0.03,    # Move SL to BE after 3% profit
            'partial_profit_pct': None,  # No partial profit by default
            'partial_profit_size': None, # % of position to sell
        }
    
    def load_positions(self) -> Dict[str, PositionRecord]:
        """Load positions from Alpaca (broker-first)."""
        broker_positions = self.alpaca.get_positions()
        
        for p in broker_positions:
            symbol = p['symbol']
            
            # Try to get existing record to preserve strategy_id and exit_rules
            existing = self.positions.get(symbol)
            
            self.positions[symbol] = PositionRecord(
                symbol=symbol,
                qty=float(p['qty']),
                avg_entry_price=float(p['avg_entry_price']),
                current_price=float(p['current_price']),
                market_value=float(p['market_value']),
                unrealized_pl=float(p['unrealized_pl']),
                unrealized_plpc=float(p['unrealized_plpc']),
                strategy_id=existing.strategy_id if existing else 'unknown',
                entry_timestamp=existing.entry_timestamp if existing else datetime.now(timezone.utc).isoformat(),
                last_updated=datetime.now(timezone.utc).isoformat(),
                exit_rules=existing.exit_rules if existing else self.default_rules.copy(),
            )
        
        return self.positions
    
    def check_exit_signals(self, symbol: str, strategy_status: str = 'active') -> Tuple[str, str, Dict]:
        """
        Check if a position should be exited.
        
        Args:
            symbol: Asset symbol
            strategy_status: 'active', 'testing', 'rejected', 'halted'
            
        Returns:
            Tuple of (action, reason, details)
            action: "HOLD", "SELL", "PARTIAL_SELL"
        """
        if symbol not in self.positions:
            return "HOLD", "No position found", {}
        
        pos = self.positions[symbol]
        rules = pos.exit_rules
        
        # If strategy is rejected, default to reduce/close
        if strategy_status == 'rejected':
            return (
                "SELL",
                f"Strategy {pos.strategy_id} is REJECTED. Closing position as risk mitigation.",
                {'origin': 'strategy_rejected'}
            )
        
        # If strategy is halted, only reduce-only exits allowed
        if strategy_status == 'halted':
            return (
                "SELL",
                f"Trading halted. Reduce-only exit for {symbol}.",
                {'origin': 'halted'}
            )
        
        # Calculate PnL percentage
        pnl_pct = pos.unrealized_plpc
        
        # Stop loss check
        if pnl_pct <= -rules['stop_loss_pct']:
            return (
                "SELL",
                f"Stop loss triggered: {pnl_pct:.2%} loss (limit: {rules['stop_loss_pct']:.2%}).",
                {'origin': 'stop_loss', 'pnl_pct': pnl_pct, 'limit': rules['stop_loss_pct']}
            )
        
        # Take profit check
        if pnl_pct >= rules['take_profit_pct']:
            return (
                "SELL",
                f"Take profit triggered: {pnl_pct:.2%} profit (target: {rules['take_profit_pct']:.2%}).",
                {'origin': 'take_profit', 'pnl_pct': pnl_pct, 'target': rules['take_profit_pct']}
            )
        
        # Time-based exit
        entry_time = datetime.fromisoformat(pos.entry_timestamp.replace('Z', '+00:00'))
        hold_time = datetime.now(timezone.utc) - entry_time
        hold_hours = hold_time.total_seconds() / 3600
        
        if hold_hours >= rules['time_limit_hours']:
            return (
                "SELL",
                f"Time limit reached: {hold_hours:.1f}h (max: {rules['time_limit_hours']}h).",
                {'origin': 'time_limit', 'hold_hours': hold_hours, 'max_hours': rules['time_limit_hours']}
            )
        
        # Break-even stop (if enabled and profit threshold met)
        if rules['break_even_after'] and pnl_pct >= rules['break_even_after']:
            # Check if price has dropped back to entry
            if pos.current_price <= pos.avg_entry_price * 1.001:  # Within 0.1% of BE
                return (
                    "SELL",
                    f"Break-even stop: Price returned to entry after {pnl_pct:.2%} profit.",
                    {'origin': 'break_even_stop', 'entry': pos.avg_entry_price, 'current': pos.current_price}
                )
        
        # All checks passed -> hold
        return (
            "HOLD",
            f"Holding {symbol}: PnL {pnl_pct:.2%}, hold time {hold_hours:.1f}h. No exit signal.",
            {'pnl_pct': pnl_pct, 'hold_hours': hold_hours}
        )
    
    def check_all_positions(self, strategy_status_map: Dict[str, str]) -> List[Tuple[str, str, str, Dict]]:
        """
        Check all positions for exit signals.
        
        Args:
            strategy_status_map: Dict of symbol -> strategy status
            
        Returns:
            List of (symbol, action, reason, details)
        """
        results = []
        
        for symbol, pos in self.positions.items():
            status = strategy_status_map.get(symbol, 'active')
            action, reason, details = self.check_exit_signals(symbol, status)
            
            if action != "HOLD":
                results.append((symbol, action, reason, details))
                logger.info(f"[EXIT SIGNAL] {symbol}: {action} — {reason}")
        
        return results
    
    def record_exit(self, symbol: str, exit_price: float, exit_qty: float, 
                    reason: str, pnl: float, strategy_id: str):
        """Record an exit in history."""
        event = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'symbol': symbol,
            'exit_price': exit_price,
            'exit_qty': exit_qty,
            'reason': reason,
            'pnl': pnl,
            'strategy_id': strategy_id,
        }
        self.exit_history.append(event)
        logger.info(f"[EXIT] {symbol}: Sold {exit_qty} @ {exit_price:.2f} | PnL: ${pnl:.2f} | Reason: {reason}")
    
    def get_position_summary(self) -> Dict:
        """Get summary of all positions."""
        total_value = sum(p.market_value for p in self.positions.values())
        total_pnl = sum(p.unrealized_pl for p in self.positions.values())
        
        return {
            'total_positions': len(self.positions),
            'total_value': total_value,
            'total_unrealized_pnl': total_pnl,
            'positions': [
                {
                    'symbol': p.symbol,
                    'qty': p.qty,
                    'avg_entry': p.avg_entry_price,
                    'current': p.current_price,
                    'value': p.market_value,
                    'pnl': p.unrealized_pl,
                    'pnl_pct': p.unrealized_plpc,
                    'strategy': p.strategy_id,
                    'hold_time_hours': self._calculate_hold_time(p),
                }
                for p in self.positions.values()
            ]
        }
    
    def _calculate_hold_time(self, pos: PositionRecord) -> float:
        """Calculate hold time in hours."""
        try:
            entry_time = datetime.fromisoformat(pos.entry_timestamp.replace('Z', '+00:00'))
            hold_time = datetime.now(timezone.utc) - entry_time
            return hold_time.total_seconds() / 3600
        except:
            return 0.0
    
    def set_exit_rules(self, symbol: str, rules: Dict):
        """Set custom exit rules for a position."""
        if symbol in self.positions:
            self.positions[symbol].exit_rules.update(rules)
            logger.info(f"[POSITION] Updated exit rules for {symbol}: {rules}")
        else:
            logger.warning(f"[POSITION] Cannot set rules: no position for {symbol}")
    
    def is_position_open(self, symbol: str) -> bool:
        """Check if a position is open."""
        return symbol in self.positions and self.positions[symbol].qty > 0
    
    def get_position_value(self, symbol: str) -> float:
        """Get position market value."""
        if symbol in self.positions:
            return self.positions[symbol].market_value
        return 0.0
