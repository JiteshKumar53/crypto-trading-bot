"""
EA System — Bollinger Band Bounce Strategy (15m)
Entry: price touches lower BB, RSI < 35 (oversold)
Exit: price reaches middle band OR 2% stop
BUG-FIXED: check_exit takes current_price for accurate P&L
"""

from typing import Dict, List, Optional
from indicators import sma, rsi, bollinger_bands


class BollingerStrategy:
    """Mean reversion strategy using Bollinger Bands."""

    def __init__(self):
        self.bb_period = 20
        self.bb_std = 2.0
        self.rsi_period = 14
        self.rsi_max = 35
        self.stop_loss_pct = 0.02
        self.take_profit_pct = 0.02

    def check_entry(self, bars: List[Dict]) -> Optional[Dict]:
        """Check for LONG entry signal on lower BB touch + RSI oversold."""
        if len(bars) < max(self.bb_period, self.rsi_period) + 2:
            return None

        closes = [b['close'] for b in bars]
        rsi_vals = rsi(closes, self.rsi_period)
        upper, middle, lower = bollinger_bands(closes, self.bb_period, self.bb_std)

        if not rsi_vals or not lower:
            return None

        current_price = closes[-1]
        current_rsi = rsi_vals[-1]
        current_lower = lower[-1]

        # Price at or below lower band (within 0.1%)
        if current_price > current_lower * 1.001:
            return None

        if current_rsi >= self.rsi_max:
            return None

        return {
            'signal': 'LONG',
            'price': current_price,
            'bb_lower': current_lower,
            'bb_middle': middle[-1] if middle else None,
            'rsi': current_rsi,
            'reason': 'bb_lower_touch_rsi_oversold'
        }

    def check_exit(self, bars: List[Dict], entry_price: float, current_price: float) -> Optional[Dict]:
        """
        Check for exit signal.
        Uses live current_price for stops/targets, bars for BB calculation.
        """
        pnl_pct = (current_price - entry_price) / entry_price

        # Stop loss (uses LIVE price)
        if pnl_pct <= -self.stop_loss_pct:
            return {'signal': 'EXIT', 'price': current_price, 'pnl_pct': pnl_pct, 'reason': 'bb_stop_loss_2pct'}

        # Take profit (uses LIVE price)
        if pnl_pct >= self.take_profit_pct:
            return {'signal': 'EXIT', 'price': current_price, 'pnl_pct': pnl_pct, 'reason': 'bb_take_profit_2pct'}

        # Exit at middle band (uses bar data)
        if len(bars) >= self.bb_period + 2:
            closes = [b['close'] for b in bars]
            _, middle, _ = bollinger_bands(closes, self.bb_period, self.bb_std)
            if middle and current_price >= middle[-1]:
                return {'signal': 'EXIT', 'price': current_price, 'pnl_pct': pnl_pct, 'reason': 'bb_middle_band_reached'}

        return None
