"""
EA System — EMA + RSI Strategy
Entry: EMA8 crosses above EMA21, RSI(14) between 50-70
Exit: EMA8 crosses below EMA21, or 2% loss (via universal stop), or 3% profit (via universal stop)
BUG-FIXED: check_exit takes current_price for accurate P&L
"""

from typing import Dict, List, Optional
from indicators import ema, rsi, get_last_crossover


class EmaRsiStrategy:
    """Simple EMA crossover + RSI filter strategy for 15m crypto."""

    def __init__(self):
        self.ema_fast_period = 8
        self.ema_slow_period = 21
        self.rsi_period = 14
        self.rsi_min = 50
        self.rsi_max = 70
        self.stop_loss_pct = 0.02
        self.take_profit_pct = 0.03

    def check_entry(self, bars: List[Dict]) -> Optional[Dict]:
        """Check for LONG entry signal. Returns signal dict or None."""
        if len(bars) < max(self.ema_slow_period, self.rsi_period) + 2:
            return None

        closes = [b['close'] for b in bars]
        ema_fast = ema(closes, self.ema_fast_period)
        ema_slow = ema(closes, self.ema_slow_period)
        rsi_values = rsi(closes, self.rsi_period)

        if not ema_fast or not ema_slow or not rsi_values:
            return None

        cross = get_last_crossover(ema_fast, ema_slow)
        if cross != "CROSS_UP":
            return None

        current_rsi = rsi_values[-1]
        if not (self.rsi_min < current_rsi < self.rsi_max):
            return None

        return {
            'signal': 'LONG',
            'price': closes[-1],
            'ema_fast': ema_fast[-1],
            'ema_slow': ema_slow[-1],
            'rsi': current_rsi,
            'reason': 'ema8_cross_above_ema21_rsi_confirmed'
        }

    def check_exit(self, bars: List[Dict], entry_price: float, current_price: float) -> Optional[Dict]:
        """
        Check for exit signal.
        Uses live current_price for P&L, bars for EMA crossover.
        """
        pnl_pct = (current_price - entry_price) / entry_price

        # Hard stop (2%) — also enforced by universal monitor, kept for completeness
        if pnl_pct <= -self.stop_loss_pct:
            return {'signal': 'EXIT', 'price': current_price, 'pnl_pct': pnl_pct, 'reason': 'stop_loss_2pct'}

        # Take profit (3%)
        if pnl_pct >= self.take_profit_pct:
            return {'signal': 'EXIT', 'price': current_price, 'pnl_pct': pnl_pct, 'reason': 'take_profit_3pct'}

        # EMA cross down (uses bar data)
        if len(bars) >= max(self.ema_fast_period, self.ema_slow_period) + 2:
            closes = [b['close'] for b in bars]
            ema_fast = ema(closes, self.ema_fast_period)
            ema_slow = ema(closes, self.ema_slow_period)
            if ema_fast and ema_slow:
                cross = get_last_crossover(ema_fast, ema_slow)
                if cross == "CROSS_DOWN":
                    return {'signal': 'EXIT', 'price': current_price, 'pnl_pct': pnl_pct, 'reason': 'ema8_cross_below_ema21'}

        return None
