"""
EA System — RSI Scalp Strategy (15m)
Entry: RSI drops below 25 then crosses back above 30 (oversold recovery)
Exit: RSI returns to 50 OR 1.5% stop OR 2% TP
BUG-FIXED: check_exit now takes current_price for accurate P&L
"""

from typing import Dict, List, Optional
from indicators import rsi


class RsiScalpStrategy:
    """RSI-based scalp strategy for quick mean-reversion trades. LONG ONLY."""

    def __init__(self):
        self.rsi_period = 14
        self.oversold_entry = 25
        self.oversold_trigger = 30
        self.exit_rsi_target = 50
        self.stop_loss_pct = 0.015
        self.take_profit_pct = 0.02

    def check_entry(self, bars: List[Dict]) -> Optional[Dict]:
        """Check for LONG entry based on RSI oversold recovery."""
        if len(bars) < self.rsi_period + 5:
            return None

        closes = [b['close'] for b in bars]
        rsi_vals = rsi(closes, self.rsi_period)

        if len(rsi_vals) < 5:
            return None

        current_price = closes[-1]
        current_rsi = rsi_vals[-1]
        prev_rsi = rsi_vals[-2]

        if prev_rsi < self.oversold_entry and current_rsi > self.oversold_trigger:
            return {
                'signal': 'LONG',
                'price': current_price,
                'rsi': current_rsi,
                'reason': 'rsi_oversold_recovery'
            }

        return None

    def check_exit(self, bars: List[Dict], entry_price: float, current_price: float) -> Optional[Dict]:
        """
        Check for exit signal.
        Uses live current_price for stops/targets, bars for RSI calculation.
        """
        pnl_pct = (current_price - entry_price) / entry_price

        # Hard stop (uses LIVE price)
        if pnl_pct <= -self.stop_loss_pct:
            return {'signal': 'EXIT', 'price': current_price, 'pnl_pct': pnl_pct, 'reason': 'rsi_scalp_stop_loss'}

        # Take profit (uses LIVE price)
        if pnl_pct >= self.take_profit_pct:
            return {'signal': 'EXIT', 'price': current_price, 'pnl_pct': pnl_pct, 'reason': 'rsi_scalp_take_profit'}

        # RSI reached 50 (uses bar data)
        if len(bars) >= self.rsi_period + 2:
            closes = [b['close'] for b in bars]
            rsi_vals = rsi(closes, self.rsi_period)
            if rsi_vals and rsi_vals[-1] >= self.exit_rsi_target:
                return {'signal': 'EXIT', 'price': current_price, 'pnl_pct': pnl_pct, 'reason': 'rsi_reached_50'}

        return None
