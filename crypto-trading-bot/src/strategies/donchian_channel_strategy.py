"""
Donchian Channel Breakout Strategy
Agent: Strategy Research Team
Source: CoinQuant/TradingView Research

Entry: Price breaks above N-period high (Donchian upper band)
Exit: Price falls below N-period low (Donchian lower band)

Best risk-adjusted performer from external research:
- Sharpe: 1.95
- Max Drawdown: 21.6%
- Profit Factor: 2.45
- Win Rate: 33.3% (but payoff ratio 4.90)
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class Signal:
    action: str  # "BUY", "SELL", "HOLD"
    confidence: float  # 0.0 to 1.0
    reason: str
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None


class DonchianChannelStrategy:
    """
    Donchian Channel Breakout Strategy.
    
    Classic Turtle Trading methodology adapted for crypto.
    
    Entry rules:
    - Long: Price closes above N-period highest high
    - Short: Price closes below N-period lowest low
    
    Exit rules:
    - Long: Price closes below N-period lowest low
    - Short: Price closes above N-period highest high
    
    Risk management:
    - Position sized by ATR for volatility-adjusted exposure
    - Stop loss at 2x ATR from entry
    """

    def __init__(
        self,
        channel_period: int = 20,
        atr_period: int = 14,
        risk_per_trade: float = 0.02,
        use_short: bool = False,  # Crypto: default long-only for safety
    ):
        self.channel_period = channel_period
        self.atr_period = atr_period
        self.risk_per_trade = risk_per_trade
        self.use_short = use_short
        self.name = f"Donchian_{channel_period}"

    def calculate_donchian(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate Donchian Channel bands (excluding current bar for breakout detection)."""
        df = df.copy()
        # Shift by 1 to exclude current bar — breakout when price exceeds PREVIOUS N-bar high
        df['dc_upper'] = df['high'].rolling(window=self.channel_period).max().shift(1)
        df['dc_lower'] = df['low'].rolling(window=self.channel_period).min().shift(1)
        df['dc_middle'] = (df['dc_upper'] + df['dc_lower']) / 2
        return df

    def calculate_atr(self, df: pd.DataFrame) -> pd.Series:
        """Calculate Average True Range."""
        high = df['high']
        low = df['low']
        close = df['close']
        
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=self.atr_period).mean()
        return atr

    def generate_signal(
        self, 
        df: pd.DataFrame, 
        current_position: Optional[str] = None,
        equity: float = 10000.0
    ) -> Signal:
        """
        Generate trading signal based on Donchian Channel breakout.
        
        Args:
            df: DataFrame with OHLCV data
            current_position: "long", "short", or None
            equity: Current account equity for position sizing
            
        Returns:
            Signal object with action, confidence, reason
        """
        if len(df) < self.channel_period + self.atr_period:
            return Signal("HOLD", 0.0, "Insufficient data")
        
        # Calculate indicators
        df = self.calculate_donchian(df)
        df['atr'] = self.calculate_atr(df)
        
        current_price = df['close'].iloc[-1]
        prev_price = df['close'].iloc[-2]
        prev_upper = df['dc_upper'].iloc[-2]
        prev_lower = df['dc_lower'].iloc[-2]
        current_upper = df['dc_upper'].iloc[-1]
        current_lower = df['dc_lower'].iloc[-1]
        atr = df['atr'].iloc[-1]
        
        # Breakout detection
        long_breakout = prev_price <= prev_upper and current_price > current_upper
        short_breakout = prev_price >= prev_lower and current_price < current_lower
        
        # Position sizing
        risk_amount = equity * self.risk_per_trade
        if atr > 0:
            position_size = risk_amount / (2 * atr)  # 2x ATR stop
        else:
            position_size = 0
        
        # Entry signals
        if current_position is None or current_position == "":
            if long_breakout:
                confidence = min(1.0, (current_price - current_upper) / atr if atr > 0 else 0.5)
                sl = current_price - 2 * atr
                tp = current_price + 4 * atr  # 2:1 reward/risk
                return Signal(
                    action="BUY",
                    confidence=confidence,
                    reason=f"Donchian breakout above {self.channel_period}-period high ({current_upper:.2f}). ATR: {atr:.2f}",
                    entry_price=current_price,
                    stop_loss=sl,
                    take_profit=tp,
                )
            
            if self.use_short and short_breakout:
                confidence = min(1.0, (current_lower - current_price) / atr if atr > 0 else 0.5)
                sl = current_price + 2 * atr
                tp = current_price - 4 * atr
                return Signal(
                    action="SELL",
                    confidence=confidence,
                    reason=f"Donchian breakdown below {self.channel_period}-period low ({current_lower:.2f}). ATR: {atr:.2f}",
                    entry_price=current_price,
                    stop_loss=sl,
                    take_profit=tp,
                )
        
        # Exit signals
        elif current_position == "long":
            if short_breakout:  # Exit on opposite signal
                return Signal(
                    action="SELL",
                    confidence=0.9,
                    reason=f"Exit long: Price broke below {self.channel_period}-period low ({current_lower:.2f})",
                    entry_price=current_price,
                )
        
        elif current_position == "short" and self.use_short:
            if long_breakout:
                return Signal(
                    action="BUY",
                    confidence=0.9,
                    reason=f"Exit short: Price broke above {self.channel_period}-period high ({current_upper:.2f})",
                    entry_price=current_price,
                )
        
        return Signal("HOLD", 0.0, "No Donchian signal")

    def get_parameters(self) -> Dict:
        """Get strategy parameters for optimization."""
        return {
            "channel_period": self.channel_period,
            "atr_period": self.atr_period,
            "risk_per_trade": self.risk_per_trade,
            "use_short": self.use_short,
        }

    def get_name(self) -> str:
        """Get strategy name."""
        return f"{self.name}::{self.channel_period}"
