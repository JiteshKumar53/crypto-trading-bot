"""
EA System — VWAP Reversion Strategy (15m) — LONG ONLY
Entry long: price drops more than 1% below VWAP AND RSI < 40
Exit: price returns to VWAP OR 1.5% stop OR 1.5% TP
BUG-FIXED: check_exit now takes current_price to avoid stale bar data
"""

from typing import Dict, List, Optional
from indicators import vwap, rsi


class VwapStrategy:
    """VWAP mean reversion strategy. LONG ONLY."""

    def __init__(self):
        self.rsi_period = 14
        self.rsi_max = 40
        self.vwap_deviation_pct = 0.01  # 1% below VWAP
        self.stop_loss_pct = 0.015
        self.take_profit_pct = 0.015

    def check_entry(self, bars: List[Dict]) -> Optional[Dict]:
        """Check for LONG entry on VWAP deviation."""
        if len(bars) < max(self.rsi_period, 5) + 2:
            return None

        closes = [b['close'] for b in bars]
        highs = [b['high'] for b in bars]
        lows = [b['low'] for b in bars]
        volumes = [b['volume'] for b in bars]

        vwaps = vwap(highs, lows, closes, volumes)
        rsi_vals = rsi(closes, self.rsi_period)

        if not vwaps or not rsi_vals:
            return None

        current_price = closes[-1]
        current_vwap = vwaps[-1]
        current_rsi = rsi_vals[-1]

        deviation = (current_vwap - current_price) / current_vwap
        if deviation <= self.vwap_deviation_pct:
            return None

        if current_rsi >= self.rsi_max:
            return None

        return {
            'signal': 'LONG',
            'price': current_price,
            'vwap': current_vwap,
            'rsi': current_rsi,
            'deviation_pct': round(deviation, 4),
            'reason': 'vwap_below_deviation_rsi_oversold'
        }

    def check_exit(self, bars: List[Dict], entry_price: float, current_price: float) -> Optional[Dict]:
        """
        Check for exit signal.
        Uses live current_price for stops/targets, bars for VWAP calculation.
        Returns exit dict or None.
        """
        pnl_pct = (current_price - entry_price) / entry_price

        # Hard stop (uses LIVE price)
        if pnl_pct <= -self.stop_loss_pct:
            return {'signal': 'EXIT', 'price': current_price, 'pnl_pct': pnl_pct, 'reason': 'vwap_stop_loss'}

        # Take profit (uses LIVE price)
        if pnl_pct >= self.take_profit_pct:
            return {'signal': 'EXIT', 'price': current_price, 'pnl_pct': pnl_pct, 'reason': 'vwap_take_profit'}

        # Price returned to VWAP (uses bar data for VWAP calc)
        if len(bars) >= 5:
            highs = [b['high'] for b in bars]
            lows = [b['low'] for b in bars]
            closes = [b['close'] for b in bars]
            volumes = [b['volume'] for b in bars]
            vwaps = vwap(highs, lows, closes, volumes)
            if vwaps and current_price >= vwaps[-1]:
                return {'signal': 'EXIT', 'price': current_price, 'pnl_pct': pnl_pct, 'reason': 'vwap_returned_to_mean'}

        return None
