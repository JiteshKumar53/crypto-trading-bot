"""
Chart Technical Analyzer
Agent: Live Chart Monitoring + Market Visual Intelligence

Performs real-time technical analysis on OHLCV data:
- Trend detection
- Support/resistance levels
- Breakout/breakdown detection
- Volatility analysis
- Momentum reversal detection
- Volume anomaly detection
- Divergence detection
"""

import logging
import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timezone
from enum import Enum

from .data_sources.base import Candle

logger = logging.getLogger(__name__)


class TrendState(Enum):
    UPTREND = "uptrend"
    DOWNTREND = "downtrend"
    RANGING = "ranging"
    CHOPPY = "choppy"
    UNKNOWN = "unknown"


class VolatilityState(Enum):
    LOW = "low"           # Compression - potential for expansion
    NORMAL = "normal"
    HIGH = "high"         # Expansion - elevated risk
    EXPANDING = "expanding"
    COMPRESSING = "compressing"


class MomentumState(Enum):
    STRONG_BULLISH = "strong_bullish"
    BULLISH = "bullish"
    NEUTRAL = "neutral"
    BEARISH = "bearish"
    STRONG_BEARISH = "strong_bearish"
    DIVERGENT = "divergent"


@dataclass
class SupportResistance:
    """Support or resistance level."""
    price: float
    strength: int          # Number of touches
    type: str              # "support" or "resistance"
    first_touch: datetime
    last_touch: datetime
    is_active: bool = True


@dataclass
class ChartObservation:
    """Structured output from chart analysis."""
    timestamp: str
    timezone: str
    symbol: str
    timeframe: str
    current_price: float
    
    # Trend analysis (required)
    trend_state: TrendState
    trend_strength: float  # 0.0 to 1.0
    
    # Volatility (required)
    volatility_state: VolatilityState
    atr_value: float
    atr_percent: float
    
    # Momentum (required)
    momentum_status: MomentumState
    
    # Support/Resistance (optional, with defaults)
    support_levels: List[float] = field(default_factory=list)
    resistance_levels: List[float] = field(default_factory=list)
    nearest_support: Optional[float] = None
    nearest_resistance: Optional[float] = None
    
    # Breakouts (optional)
    breakout_detected: bool = False
    breakdown_detected: bool = False
    breakout_target: Optional[float] = None
    breakdown_target: Optional[float] = None
    
    # Reversal (optional)
    reversal_warning: bool = False
    reversal_type: str = ""  # "bullish" or "bearish"
    
    # Momentum details (optional)
    rsi_value: Optional[float] = None
    macd_value: Optional[float] = None
    macd_signal: Optional[float] = None
    
    # Volume (optional)
    volume_status: str = "normal"
    volume_anomaly: bool = False
    volume_vs_avg: float = 1.0  # Ratio to average
    
    # Position monitoring (optional)
    open_position_affected: bool = False
    position_direction: str = ""  # "long" or "short"
    position_entry_price: Optional[float] = None
    position_pnl_pct: Optional[float] = None
    
    # Recommendations (optional)
    recommended_review_action: str = "none"
    confidence: float = 0.0
    reason: str = ""
    risk_warning: str = ""
    suggested_next_step: str = ""
    
    # Metadata (optional)
    candles_analyzed: int = 0
    lookback_hours: int = 0


class ChartAnalyzer:
    """
    Real-time chart technical analyzer.
    Processes candle data and generates structured observations.
    """
    
    def __init__(self):
        self._observation_history: Dict[str, List[ChartObservation]] = {}
        self._sr_levels: Dict[str, List[SupportResistance]] = {}
        logger.info("[ChartAnalyzer] Initialized")
    
    def analyze(
        self,
        candles: List[Candle],
        symbol: str,
        timeframe: str,
        current_position: Optional[Dict] = None,
    ) -> ChartObservation:
        """
        Analyze a series of candles and generate observation.
        
        Args:
            candles: List of Candle objects (oldest first)
            symbol: Trading pair
            timeframe: e.g., "1h", "4h"
            current_position: Optional dict with entry_price, qty, side
        
        Returns:
            ChartObservation with full analysis
        """
        if len(candles) < 20:
            return self._empty_observation(symbol, timeframe, "Insufficient data")
        
        prices = np.array([c.close for c in candles])
        highs = np.array([c.high for c in candles])
        lows = np.array([c.low for c in candles])
        volumes = np.array([c.volume for c in candles])
        current_price = prices[-1]
        
        # Build observation
        obs = ChartObservation(
            timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            timezone="Europe/Stockholm",
            symbol=symbol,
            timeframe=timeframe,
            current_price=current_price,
            trend_state=self._detect_trend(prices),
            trend_strength=self._trend_strength(prices),
            volatility_state=self._detect_volatility(prices, highs, lows),
            atr_value=self._atr(highs, lows, prices, 14),
            atr_percent=(self._atr(highs, lows, prices, 14) / current_price) * 100,
            support_levels=self._find_support_levels(candles),
            resistance_levels=self._find_resistance_levels(candles),
            nearest_support=self._nearest_support(current_price, candles),
            nearest_resistance=self._nearest_resistance(current_price, candles),
            breakout_detected=self._detect_breakout(candles),
            breakdown_detected=self._detect_breakdown(candles),
            reversal_warning=self._detect_reversal(candles),
            reversal_type=self._reversal_type(candles),
            momentum_status=self._detect_momentum(prices, volumes),
            rsi_value=self._rsi(prices, 14),
            macd_value=self._macd(prices)[0][-1] if len(prices) > 26 else None,
            macd_signal=self._macd(prices)[1][-1] if len(prices) > 26 else None,
            volume_status=self._volume_status(volumes),
            volume_anomaly=self._volume_anomaly(volumes),
            volume_vs_avg=np.mean(volumes[-5:]) / np.mean(volumes[-20:]) if len(volumes) >= 20 else 1.0,
            candles_analyzed=len(candles),
            lookback_hours=len(candles) * self._timeframe_minutes(timeframe) // 60,
        )
        
        # Check position impact
        if current_position:
            obs.open_position_affected = True
            obs.position_direction = current_position.get("side", "long")
            obs.position_entry_price = current_position.get("entry_price")
            if obs.position_entry_price:
                obs.position_pnl_pct = ((current_price - obs.position_entry_price) 
                                          / obs.position_entry_price * 100)
        
        # Generate recommendations
        obs = self._generate_recommendations(obs, candles)
        
        # Store in history
        key = f"{symbol}_{timeframe}"
        if key not in self._observation_history:
            self._observation_history[key] = []
        self._observation_history[key].append(obs)
        
        # Keep only last 100 observations
        self._observation_history[key] = self._observation_history[key][-100:]
        
        return obs
    
    def _empty_observation(self, symbol: str, timeframe: str, reason: str) -> ChartObservation:
        """Create empty observation when data is insufficient."""
        return ChartObservation(
            timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            timezone="Europe/Stockholm",
            symbol=symbol,
            timeframe=timeframe,
            current_price=0.0,
            trend_state=TrendState.UNKNOWN,
            trend_strength=0.0,
            volatility_state=VolatilityState.NORMAL,
            atr_value=0.0,
            atr_percent=0.0,
            momentum_status=MomentumState.NEUTRAL,
            reason=reason,
            confidence=0.0,
        )
    
    # === TECHNICAL ANALYSIS METHODS ===
    
    def _detect_trend(self, prices: np.ndarray) -> TrendState:
        """Detect trend using moving averages."""
        if len(prices) < 50:
            return TrendState.UNKNOWN
        
        sma20 = np.mean(prices[-20:])
        sma50 = np.mean(prices[-50:])
        current = prices[-1]
        
        # Calculate price slope over last 20 candles
        x = np.arange(20)
        slope = np.polyfit(x, prices[-20:], 1)[0]
        
        if current > sma20 > sma50 and slope > 0:
            return TrendState.UPTREND
        elif current < sma20 < sma50 and slope < 0:
            return TrendState.DOWNTREND
        elif abs(slope / current) < 0.001:  # Flat slope
            return TrendState.RANGING
        else:
            return TrendState.CHOPPY
    
    def _trend_strength(self, prices: np.ndarray) -> float:
        """Calculate trend strength 0.0-1.0 using ADX-like measure."""
        if len(prices) < 20:
            return 0.0
        
        returns = np.diff(prices[-20:]) / prices[-20:-1]
        directional = np.abs(np.sum(returns))
        total = np.sum(np.abs(returns))
        
        if total == 0:
            return 0.0
        
        return min(directional / total, 1.0)
    
    def _detect_volatility(self, prices: np.ndarray, highs: np.ndarray, lows: np.ndarray) -> VolatilityState:
        """Detect volatility regime."""
        if len(prices) < 20:
            return VolatilityState.NORMAL
        
        atr_current = self._atr(highs, lows, prices, 14)
        atr_prev = self._atr(highs[:-5], lows[:-5], prices[:-5], 14) if len(prices) > 19 else atr_current
        
        if atr_prev == 0:
            return VolatilityState.NORMAL
        
        atr_ratio = atr_current / atr_prev
        atr_pct = atr_current / prices[-1] * 100
        
        if atr_pct < 0.5:
            return VolatilityState.LOW
        elif atr_pct > 3.0:
            return VolatilityState.HIGH
        elif atr_ratio > 1.3:
            return VolatilityState.EXPANDING
        elif atr_ratio < 0.7:
            return VolatilityState.COMPRESSING
        else:
            return VolatilityState.NORMAL
    
    def _atr(self, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int) -> float:
        """Calculate Average True Range."""
        if len(highs) < period + 1:
            return 0.0
        
        tr1 = highs[1:] - lows[1:]
        tr2 = np.abs(highs[1:] - closes[:-1])
        tr3 = np.abs(lows[1:] - closes[:-1])
        tr = np.maximum(np.maximum(tr1, tr2), tr3)
        
        return float(np.mean(tr[-period:]))
    
    def _find_support_levels(self, candles: List[Candle], touches_required: int = 2) -> List[float]:
        """Find support levels (price lows that bounce)."""
        if len(candles) < 30:
            return []
        
        lows = [c.low for c in candles]
        supports = []
        
        # Simple method: find local minima
        for i in range(2, len(lows) - 2):
            if lows[i] <= lows[i-1] and lows[i] <= lows[i-2] and lows[i] <= lows[i+1] and lows[i] <= lows[i+2]:
                # Check if this level was tested again
                level = lows[i]
                touches = 1
                for j in range(i + 1, len(lows)):
                    if abs(lows[j] - level) / level < 0.005:  # Within 0.5%
                        touches += 1
                
                if touches >= touches_required:
                    supports.append(level)
        
        # Return top 3 strongest supports below current price
        current = candles[-1].close
        supports_below = sorted([s for s in supports if s < current], reverse=True)
        return supports_below[:3]
    
    def _find_resistance_levels(self, candles: List[Candle], touches_required: int = 2) -> List[float]:
        """Find resistance levels (price highs that reject)."""
        if len(candles) < 30:
            return []
        
        highs = [c.high for c in candles]
        resistances = []
        
        for i in range(2, len(highs) - 2):
            if highs[i] >= highs[i-1] and highs[i] >= highs[i-2] and highs[i] >= highs[i+1] and highs[i] >= highs[i+2]:
                level = highs[i]
                touches = 1
                for j in range(i + 1, len(highs)):
                    if abs(highs[j] - level) / level < 0.005:
                        touches += 1
                
                if touches >= touches_required:
                    resistances.append(level)
        
        current = candles[-1].close
        resistances_above = sorted([r for r in resistances if r > current])
        return resistances_above[:3]
    
    def _nearest_support(self, current_price: float, candles: List[Candle]) -> Optional[float]:
        """Find nearest support below current price."""
        supports = self._find_support_levels(candles)
        return supports[0] if supports else None
    
    def _nearest_resistance(self, current_price: float, candles: List[Candle]) -> Optional[float]:
        """Find nearest resistance above current price."""
        resistances = self._find_resistance_levels(candles)
        return resistances[0] if resistances else None
    
    def _detect_breakout(self, candles: List[Candle]) -> bool:
        """Detect if price is breaking above resistance."""
        if len(candles) < 10:
            return False
        
        resistances = self._find_resistance_levels(candles[:-5])  # Exclude recent candles
        if not resistances:
            return False
        
        current = candles[-1].close
        prev_close = candles[-2].close
        nearest_res = resistances[0]
        
        # Breakout: previous close below resistance, current above
        return prev_close < nearest_res * 1.002 and current > nearest_res * 1.002
    
    def _detect_breakdown(self, candles: List[Candle]) -> bool:
        """Detect if price is breaking below support."""
        if len(candles) < 10:
            return False
        
        supports = self._find_support_levels(candles[:-5])
        if not supports:
            return False
        
        current = candles[-1].close
        prev_close = candles[-2].close
        nearest_sup = supports[0]
        
        return prev_close > nearest_sup * 0.998 and current < nearest_sup * 0.998
    
    def _detect_reversal(self, candles: List[Candle]) -> bool:
        """Detect potential reversal patterns."""
        if len(candles) < 5:
            return False
        
        # Check for engulfing candle or doji
        last = candles[-1]
        prev = candles[-2]
        
        # Bullish engulfing
        bullish_engulfing = (last.close > last.open and prev.close < prev.open and
                            last.close > prev.open and last.open < prev.close)
        
        # Bearish engulfing
        bearish_engulfing = (last.close < last.open and prev.close > prev.open and
                            last.close < prev.open and last.open > prev.close)
        
        # Doji (small body)
        body = abs(last.close - last.open)
        range_ = last.high - last.low
        doji = body / range_ < 0.1 if range_ > 0 else False
        
        return bullish_engulfing or bearish_engulfing or doji
    
    def _reversal_type(self, candles: List[Candle]) -> str:
        """Determine reversal direction."""
        if len(candles) < 3:
            return ""
        
        trend = self._detect_trend(np.array([c.close for c in candles]))
        
        if trend == TrendState.DOWNTREND:
            return "bullish"
        elif trend == TrendState.UPTREND:
            return "bearish"
        
        return ""
    
    def _detect_momentum(self, prices: np.ndarray, volumes: np.ndarray) -> MomentumState:
        """Detect momentum state using RSI and price action."""
        rsi = self._rsi(prices, 14)
        
        if rsi is None:
            return MomentumState.NEUTRAL
        
        if rsi > 70:
            return MomentumState.STRONG_BULLISH
        elif rsi > 55:
            return MomentumState.BULLISH
        elif rsi < 30:
            return MomentumState.STRONG_BEARISH
        elif rsi < 45:
            return MomentumState.BEARISH
        else:
            return MomentumState.NEUTRAL
    
    def _rsi(self, prices: np.ndarray, period: int = 14) -> Optional[float]:
        """Calculate Relative Strength Index."""
        if len(prices) < period + 1:
            return None
        
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        return 100.0 - (100.0 / (1.0 + rs))
    
    def _macd(self, prices: np.ndarray, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[np.ndarray, np.ndarray]:
        """Calculate MACD line and signal line."""
        if len(prices) < slow + signal:
            return np.array([]), np.array([])
        
        ema_fast = self._ema(prices, fast)
        ema_slow = self._ema(prices, slow)
        
        macd_line = ema_fast - ema_slow
        signal_line = self._ema(macd_line, signal)
        
        return macd_line, signal_line
    
    def _ema(self, data: np.ndarray, period: int) -> np.ndarray:
        """Calculate Exponential Moving Average."""
        alpha = 2.0 / (period + 1)
        ema = np.zeros_like(data)
        ema[0] = data[0]
        
        for i in range(1, len(data)):
            ema[i] = alpha * data[i] + (1 - alpha) * ema[i-1]
        
        return ema
    
    def _volume_status(self, volumes: np.ndarray) -> str:
        """Classify volume status."""
        if len(volumes) < 20:
            return "normal"
        
        avg = np.mean(volumes[-20:])
        current = volumes[-1]
        ratio = current / avg if avg > 0 else 1.0
        
        if ratio > 2.0:
            return "very_high"
        elif ratio > 1.5:
            return "high"
        elif ratio < 0.5:
            return "low"
        else:
            return "normal"
    
    def _volume_anomaly(self, volumes: np.ndarray, threshold: float = 2.5) -> bool:
        """Detect unusual volume spikes."""
        if len(volumes) < 20:
            return False
        
        avg = np.mean(volumes[-20:-1])
        current = volumes[-1]
        
        return avg > 0 and current / avg > threshold
    
    def _timeframe_minutes(self, timeframe: str) -> int:
        """Convert timeframe string to minutes."""
        mapping = {
            "1m": 1, "5m": 5, "15m": 15, "30m": 30,
            "1h": 60, "2h": 120, "4h": 240, "6h": 360, "8h": 480, "12h": 720,
            "1d": 1440, "3d": 4320, "1w": 10080,
        }
        return mapping.get(timeframe, 60)
    
    def _generate_recommendations(
        self,
        obs: ChartObservation,
        candles: List[Candle],
    ) -> ChartObservation:
        """Generate actionable recommendations."""
        
        reasons = []
        warnings = []
        actions = []
        confidence_factors = []
        
        # Breakout check
        if obs.breakout_detected:
            reasons.append(f"Breakout above resistance at ${obs.nearest_resistance:,.2f}")
            confidence_factors.append(0.7)
            if obs.momentum_status in [MomentumState.BULLISH, MomentumState.STRONG_BULLISH]:
                actions.append("Consider adding to position or opening new long")
                confidence_factors.append(0.2)
        
        if obs.breakdown_detected:
            reasons.append(f"Breakdown below support at ${obs.nearest_support:,.2f}")
            confidence_factors.append(0.7)
            warnings.append("Stop-loss may be triggered")
        
        # Reversal check
        if obs.reversal_warning:
            reasons.append(f"Potential {obs.reversal_type} reversal detected")
            confidence_factors.append(0.5)
            if obs.open_position_affected:
                if obs.reversal_type == "bearish" and obs.position_direction == "long":
                    actions.append("Consider partial profit-taking or tighten stop")
                    warnings.append("Momentum weakening on open long position")
                elif obs.reversal_type == "bullish" and obs.position_direction == "short":
                    actions.append("Consider closing short position")
        
        # Momentum divergence
        if obs.momentum_status == MomentumState.DIVERGENT:
            reasons.append("Price/momentum divergence detected")
            confidence_factors.append(0.6)
            warnings.append("Trend may be losing strength")
        
        # Volume anomaly
        if obs.volume_anomaly:
            reasons.append(f"Volume spike: {obs.volume_vs_avg:.1f}x average")
            confidence_factors.append(0.4)
        
        # Volatility
        if obs.volatility_state == VolatilityState.EXPANDING:
            warnings.append("Volatility expanding — widen stops or reduce position size")
        elif obs.volatility_state == VolatilityState.COMPRESSING:
            reasons.append("Volatility compression — potential breakout brewing")
            confidence_factors.append(0.3)
        
        # Position monitoring
        if obs.open_position_affected and obs.position_pnl_pct is not None:
            if obs.position_pnl_pct > 2.0 and obs.momentum_status in [
                MomentumState.NEUTRAL, MomentumState.BEARISH
            ]:
                actions.append("Profit + momentum fading — consider trailing stop")
                warnings.append("Don't let profit evaporate")
            elif obs.position_pnl_pct < -2.0 and obs.trend_state == TrendState.DOWNTREND:
                warnings.append("Position underwater and trend against you — review urgently")
        
        # Compile final recommendation
        obs.reason = "; ".join(reasons) if reasons else "No significant signals"
        obs.risk_warning = "; ".join(warnings) if warnings else "Normal risk level"
        obs.suggested_next_step = "; ".join(actions) if actions else "Continue monitoring"
        obs.confidence = min(sum(confidence_factors), 0.95) if confidence_factors else 0.3
        
        # Override review action based on priority
        if warnings and obs.open_position_affected:
            obs.recommended_review_action = "urgent_review"
        elif obs.breakout_detected or obs.breakdown_detected:
            obs.recommended_review_action = "review_immediately"
        elif obs.reversal_warning:
            obs.recommended_review_action = "review_soon"
        elif reasons:
            obs.recommended_review_action = "monitor_closely"
        else:
            obs.recommended_review_action = "none"
        
        return obs
    
    def get_observation_history(self, symbol: str, timeframe: str, n: int = 10) -> List[ChartObservation]:
        """Get recent observation history."""
        key = f"{symbol}_{timeframe}"
        history = self._observation_history.get(key, [])
        return history[-n:] if history else []
