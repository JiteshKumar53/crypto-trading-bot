"""
Smart EA Bot Company — Risk Governor
Deterministic risk limits. No configuration. Hard-coded safety.
"""

import logging
from typing import Dict, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class RiskGovernor:
    """
    Enforces hard-coded risk limits.
    Called before every order.
    """

    def __init__(self, max_positions_total: int = 2, max_positions_per_asset: int = 1,
                 risk_per_trade_pct: float = 0.25, daily_max_loss_pct: float = 1.0,
                 weekly_max_loss_pct: float = 3.0):
        self.max_positions_total = max_positions_total
        self.max_positions_per_asset = max_positions_per_asset
        self.risk_per_trade_pct = risk_per_trade_pct
        self.daily_max_loss_pct = daily_max_loss_pct
        self.weekly_max_loss_pct = weekly_max_loss_pct
        self.daily_pnl = 0.0
        self.weekly_pnl = 0.0
        self.last_reset = datetime.now(timezone.utc)

    def check_order(self, symbol: str, side: str, qty: float, price: float,
                    portfolio_value: float, current_positions: Dict) -> Dict:
        """
        Check if order passes all risk limits.
        Returns: {"allowed": bool, "reason": str}
        """
        # Check total positions
        if len(current_positions) >= self.max_positions_total:
            return {"allowed": False, "reason": f"Max total positions reached: {self.max_positions_total}"}

        # Check per-asset positions
        asset_positions = [p for p in current_positions.values() if p.get("symbol") == symbol]
        if len(asset_positions) >= self.max_positions_per_asset:
            return {"allowed": False, "reason": f"Max positions for {symbol} reached"}

        # Check position size
        order_value = qty * price
        max_order_value = portfolio_value * (self.risk_per_trade_pct / 100)
        if order_value > max_order_value:
            return {"allowed": False, "reason": f"Order value {order_value:.2f} > max {max_order_value:.2f}"}

        # Check daily loss limit
        if self.daily_pnl <= -portfolio_value * (self.daily_max_loss_pct / 100):
            return {"allowed": False, "reason": f"Daily loss limit reached: {self.daily_pnl:.2f}"}

        # Check weekly loss limit
        if self.weekly_pnl <= -portfolio_value * (self.weekly_max_loss_pct / 100):
            return {"allowed": False, "reason": f"Weekly loss limit reached: {self.weekly_pnl:.2f}"}

        return {"allowed": True, "reason": "All risk checks passed"}

    def update_pnl(self, pnl: float):
        """Update daily/weekly PnL tracking."""
        self.daily_pnl += pnl
        self.weekly_pnl += pnl

    def reset_daily(self):
        """Reset daily PnL (call at market open)."""
        self.daily_pnl = 0.0

    def reset_weekly(self):
        """Reset weekly PnL (call on Monday)."""
        self.weekly_pnl = 0.0
