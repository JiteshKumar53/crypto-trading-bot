"""
RSI Range Trading Strategy
Agent: Strategy Research Team
Source: Kraken Learn / Experienced Crypto Traders

Entry: Price near support + RSI oversold (<30)
Exit: Price near resistance + RSI overbought (>70)
Stop-loss: Below support -1%
Take-profit: Near resistance -0.5%
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


class RSIRangeStrategy:
    """
    RSI Range Trading Strategy.
    
    Works best in ranging/sideways markets with clear support/resistance.
    Profits from mean reversion within established boundaries.
    
    Entry rules:
    - Price approaches support (bottom of range)
    - RSI(14) < 30 (oversold)
    - Enter long near support
    
    Exit rules:
    - Price approaches resistance (top of range)
    - RSI(14) > 70 (overbought)
    - Exit near resistance
    
    Stop-loss: Below support -1%
    Take-profit: Near resistance -0.5%
    """

    def __init__(
        self,
        rsi_period: int = 14,
        rsi_oversold: float = 30.0,
        rsi_overbought: float = 70.0,
        range_lookback: int = 24,  # 24 hours of data
        sl_buffer: float = 0.01,  # 1% below support
        tp_buffer: float = 0.005,  # 0.5% below resistance
        min_range_width: float = 0.02,  # Min 2% range width
    ):
        self.rsi_period = rsi_period
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought
        self.range_lookback = range_lookback
        self.sl_buffer = sl_buffer
        self.tp_buffer = tp_buffer
        self.min_range_width = min_range_width
        self.name = "RSI_Range_Trading"

    def calculate_rsi(self, closes: pd.Series) -> pd.Series:
        """Calculate RSI(14) for a series of close prices."""
        delta = closes.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def detect_range(self, df: pd.DataFrame) -> Optional[Tuple[float, float, float]]:
        """
        Detect support and resistance levels from recent data.
        
        Returns:
            (support, resistance, range_width_pct) or None if no clear range
        """
        if len(df) < self.range_lookback:
            return None
        
        recent = df.tail(self.range_lookback)
        support = recent['low'].min()
        resistance = recent['high'].max()
        
        range_width = (resistance - support) / support
        
        if range_width < self.min_range_width:
            return None  # Range too narrow, likely trending
        
        return support, resistance, range_width

    def generate_signal(self, df: pd.DataFrame, current_position: Optional[str] = None) -> Signal:
        """
        Generate trading signal based on RSI and range analysis.
        
        Args:
            df: DataFrame with OHLCV data
            current_position: "long", "short", or None
            
        Returns:
            Signal object with action, confidence, reason
        """
        if len(df) < self.range_lookback + self.rsi_period:
            return Signal("HOLD", 0.0, "Insufficient data")
        
        # Calculate RSI
        df['rsi'] = self.calculate_rsi(df['close'])
        current_rsi = df['rsi'].iloc[-1]
        current_price = df['close'].iloc[-1]
        
        # Detect range
        range_levels = self.detect_range(df)
        if range_levels is None:
            return Signal("HOLD", 0.1, "No clear range detected — may be trending")
        
        support, resistance, range_width = range_levels
        
        # Calculate position within range (0 = at support, 1 = at resistance)
        range_position = (current_price - support) / (resistance - support)
        
        # Entry signal: Near support + RSI oversold
        if current_position is None or current_position == "":
            if range_position <= 0.15 and current_rsi <= self.rsi_oversold:
                confidence = min(1.0, (self.rsi_oversold - current_rsi) / 20 + (0.15 - range_position) * 2)
                sl = support * (1 - self.sl_buffer)
                tp = resistance * (1 - self.tp_buffer)
                return Signal(
                    action="BUY",
                    confidence=confidence,
                    reason=f"RSI oversold ({current_rsi:.1f}) near support ({support:.2f}). Range: {range_width:.1%}",
                    entry_price=current_price,
                    stop_loss=sl,
                    take_profit=tp,
                )
        
        # Exit signal: Near resistance + RSI overbought (for long positions)
        elif current_position == "long":
            if range_position >= 0.85 and current_rsi >= self.rsi_overbought:
                confidence = min(1.0, (current_rsi - self.rsi_overbought) / 20 + (range_position - 0.85) * 2)
                return Signal(
                    action="SELL",
                    confidence=confidence,
                    reason=f"RSI overbought ({current_rsi:.1f}) near resistance ({resistance:.2f}). Range: {range_width:.1%}",
                )
            
            # Partial profit if near resistance but not yet overbought
            if range_position >= 0.75 and current_rsi >= 55:
                return Signal(
                    action="SELL_PARTIAL",
                    confidence=0.6,
                    reason=f"Near resistance ({range_position:.0%} of range). Consider partial profit.",
                )
        
        # No signal
        regime = "ranging" if range_width > 0.03 else "tight_range"
        return Signal(
            action="HOLD",
            confidence=0.3,
            reason=f"Price at {range_position:.0%} of range. RSI: {current_rsi:.1f}. Regime: {regime}",
        )

    def backtest(self, df: pd.DataFrame, initial_capital: float = 10000.0) -> Dict:
        """
        Backtest RSI Range Trading strategy on historical data.
        
        Args:
            df: DataFrame with OHLCV data
            initial_capital: Starting capital
            
        Returns:
            Dict with backtest results
        """
        df = df.copy()
        df['rsi'] = self.calculate_rsi(df['close'])
        
        capital = initial_capital
        position = None
        entry_price = 0
        trades = []
        equity_curve = [initial_capital]
        
        for i in range(self.range_lookback + self.rsi_period, len(df)):
            window = df.iloc[:i+1]
            current_price = df['close'].iloc[i]
            current_time = df.index[i] if hasattr(df.index[i], 'strftime') else i
            
            # Generate signal
            signal = self.generate_signal(window, position)
            
            if signal.action == "BUY" and position is None:
                # Enter long
                position = "long"
                entry_price = current_price
                sl = signal.stop_loss or entry_price * 0.99
                tp = signal.take_profit or entry_price * 1.02
                
                trades.append({
                    "entry_time": current_time,
                    "entry_price": entry_price,
                    "stop_loss": sl,
                    "take_profit": tp,
                    "signal_confidence": signal.confidence,
                })
                
            elif signal.action in ("SELL", "SELL_ALL") and position == "long":
                # Exit long
                pnl = current_price - entry_price
                pnl_pct = pnl / entry_price
                capital += pnl * (capital / entry_price) * 0.1  # Assume 10% position size
                
                trades[-1].update({
                    "exit_time": current_time,
                    "exit_price": current_price,
                    "pnl": pnl,
                    "pnl_pct": pnl_pct,
                })
                position = None
                entry_price = 0
            
            # Check stop-loss and take-profit
            if position == "long":
                if current_price <= trades[-1]["stop_loss"]:
                    pnl = trades[-1]["stop_loss"] - entry_price
                    pnl_pct = pnl / entry_price
                    capital += pnl * (capital / entry_price) * 0.1
                    trades[-1].update({
                        "exit_time": current_time,
                        "exit_price": trades[-1]["stop_loss"],
                        "pnl": pnl,
                        "pnl_pct": pnl_pct,
                        "exit_reason": "stop_loss",
                    })
                    position = None
                    entry_price = 0
                elif current_price >= trades[-1]["take_profit"]:
                    pnl = trades[-1]["take_profit"] - entry_price
                    pnl_pct = pnl / entry_price
                    capital += pnl * (capital / entry_price) * 0.1
                    trades[-1].update({
                        "exit_time": current_time,
                        "exit_price": trades[-1]["take_profit"],
                        "pnl": pnl,
                        "pnl_pct": pnl_pct,
                        "exit_reason": "take_profit",
                    })
                    position = None
                    entry_price = 0
            
            equity_curve.append(capital)
        
        # Calculate metrics
        closed_trades = [t for t in trades if "exit_time" in t]
        winning_trades = [t for t in closed_trades if t["pnl"] > 0]
        losing_trades = [t for t in closed_trades if t["pnl"] <= 0]
        
        total_return = (capital - initial_capital) / initial_capital
        win_rate = len(winning_trades) / len(closed_trades) if closed_trades else 0
        avg_win = np.mean([t["pnl_pct"] for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t["pnl_pct"] for t in losing_trades]) if losing_trades else 0
        
        profit_factor = (
            sum(t["pnl_pct"] for t in winning_trades) / abs(sum(t["pnl_pct"] for t in losing_trades))
            if losing_trades and sum(t["pnl_pct"] for t in losing_trades) != 0
            else float('inf')
        )
        
        equity_series = pd.Series(equity_curve)
        running_max = equity_series.expanding().max()
        drawdown = (equity_series - running_max) / running_max
        max_drawdown = drawdown.min()
        
        return {
            "strategy": self.name,
            "total_return": total_return,
            "total_trades": len(closed_trades),
            "win_rate": win_rate,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "profit_factor": profit_factor,
            "max_drawdown": max_drawdown,
            "final_capital": capital,
            "trades": closed_trades,
        }


if __name__ == "__main__":
    # Quick test
    print("RSI Range Trading Strategy loaded.")
    print("Usage: strategy = RSIRangeStrategy(); signal = strategy.generate_signal(df)")
