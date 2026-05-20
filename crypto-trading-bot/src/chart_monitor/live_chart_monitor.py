"""
Live Chart Monitoring Agent
Agent: Market Visual Intelligence Team

Continuously monitors live charts across multiple assets and timeframes.
Generates structured observations for the trading pipeline.
"""

import logging
import asyncio
import json
from dataclasses import asdict
from typing import Dict, List, Optional
from datetime import datetime, timezone
from pathlib import Path

from .data_sources.base import DataSource, get_registry
from .data_sources.alpaca_source import AlpacaDataSource
from .chart_analyzer import ChartAnalyzer, ChartObservation

logger = logging.getLogger(__name__)


class LiveChartMonitor:
    """
    Live Chart Monitoring Agent.
    
    Monitors charts continuously, analyzes them, and feeds observations
    into the trading decision pipeline.
    """
    
    DEFAULT_SYMBOLS = ["BTC/USD", "ETH/USD", "SOL/USD"]
    DEFAULT_TIMEFRAMES = ["1h", "4h"]
    MONITOR_INTERVAL_SECONDS = 60  # How often to analyze each chart
    
    def __init__(self, data_source: Optional[DataSource] = None):
        self.analyzer = ChartAnalyzer()
        self.data_source = data_source
        self._running = False
        self._observations_file = Path("/data/.openclaw/workspace/crypto-trading-bot/logs/chart_observations.jsonl")
        self._observations_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Current positions for context
        self._positions: Dict[str, Dict] = {}
        
        logger.info("[LiveChartMonitor] Initialized")
    
    async def initialize(self):
        """Initialize data source connection."""
        if self.data_source is None:
            self.data_source = AlpacaDataSource()
            await self.data_source.connect()
        
        # Register with global registry
        registry = get_registry()
        registry.register(self.data_source, make_default=True)
        
        logger.info("[LiveChartMonitor] Data source connected")
    
    async def run_monitoring_loop(
        self,
        symbols: Optional[List[str]] = None,
        timeframes: Optional[List[str]] = None,
    ):
        """
        Run continuous monitoring loop.
        
        Args:
            symbols: List of symbols to monitor (default: BTC, ETH, SOL)
            timeframes: List of timeframes (default: 1h, 4h)
        """
        symbols = symbols or self.DEFAULT_SYMBOLS
        timeframes = timeframes or self.DEFAULT_TIMEFRAMES
        
        self._running = True
        logger.info(f"[LiveChartMonitor] Starting monitoring: {symbols} @ {timeframes}")
        
        while self._running:
            try:
                for symbol in symbols:
                    for timeframe in timeframes:
                        await self._analyze_and_log(symbol, timeframe)
                        await asyncio.sleep(1)  # Brief pause between analyses
                
                await asyncio.sleep(self.MONITOR_INTERVAL_SECONDS)
                
            except Exception as e:
                logger.error(f"[LiveChartMonitor] Monitoring error: {e}")
                await asyncio.sleep(5)
    
    async def analyze_once(
        self,
        symbol: str,
        timeframe: str = "1h",
    ) -> Optional[ChartObservation]:
        """
        Run a single analysis for a symbol/timeframe.
        
        Returns:
            ChartObservation or None if analysis fails
        """
        return await self._analyze_and_log(symbol, timeframe)
    
    async def _analyze_and_log(
        self,
        symbol: str,
        timeframe: str,
    ) -> Optional[ChartObservation]:
        """Analyze a chart and log the observation."""
        try:
            # Fetch candles
            candles = self.data_source.get_ohlcv(symbol, timeframe, limit=100)
            if not candles:
                logger.warning(f"[LiveChartMonitor] No candles for {symbol} {timeframe}")
                return None
            
            # Get current position info
            position = self._positions.get(symbol.replace("/", ""))
            
            # Analyze
            obs = self.analyzer.analyze(candles, symbol, timeframe, position)
            
            # Log to file
            self._log_observation(obs)
            
            # Log to console if significant
            if obs.recommended_review_action != "none":
                logger.info(
                    f"[LiveChartMonitor] {symbol} {timeframe}: "
                    f"{obs.trend_state.value} | "
                    f"RSI={obs.rsi_value:.1f} | "
                    f"Action={obs.recommended_review_action}"
                )
            
            return obs
            
        except Exception as e:
            logger.error(f"[LiveChartMonitor] Analysis failed for {symbol}: {e}")
            return None
    
    def _log_observation(self, obs: ChartObservation):
        """Persist observation to JSONL file."""
        try:
            # Convert enum values to strings
            data = asdict(obs)
            data["trend_state"] = obs.trend_state.value if obs.trend_state else "unknown"
            data["volatility_state"] = obs.volatility_state.value if obs.volatility_state else "unknown"
            data["momentum_status"] = obs.momentum_status.value if obs.momentum_status else "unknown"
            
            with open(self._observations_file, "a") as f:
                f.write(json.dumps(data, default=str) + "\n")
        except Exception as e:
            logger.warning(f"[LiveChartMonitor] Failed to log observation: {e}")
    
    def update_positions(self, positions: Dict[str, Dict]):
        """Update current positions for context-aware analysis."""
        self._positions = positions
        logger.info(f"[LiveChartMonitor] Positions updated: {len(positions)} open")
    
    def get_latest_observation(self, symbol: str, timeframe: str) -> Optional[ChartObservation]:
        """Get the most recent observation for a symbol/timeframe."""
        history = self.analyzer.get_observation_history(symbol, timeframe, n=1)
        return history[0] if history else None
    
    def get_all_latest_observations(self) -> Dict[str, ChartObservation]:
        """Get latest observations for all monitored symbols/timeframes."""
        result = {}
        for symbol in self.DEFAULT_SYMBOLS:
            for timeframe in self.DEFAULT_TIMEFRAMES:
                obs = self.get_latest_observation(symbol, timeframe)
                if obs:
                    result[f"{symbol}_{timeframe}"] = obs
        return result
    
    def stop(self):
        """Stop monitoring loop."""
        self._running = False
        logger.info("[LiveChartMonitor] Stopping")
    
    @property
    def is_running(self) -> bool:
        return self._running


class ChartObservationReporter:
    """
    Generates human-readable and structured reports from chart observations.
    Used for feeding into the trading pipeline and for dashboard display.
    """
    
    @staticmethod
    def to_markdown(obs: ChartObservation) -> str:
        """Convert observation to markdown report."""
        lines = [
            f"## 📊 Chart Observation: {obs.symbol} ({obs.timeframe})",
            f"**Time:** {obs.timestamp} ({obs.timezone})",
            f"**Price:** ${obs.current_price:,.2f}",
            "",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Trend | {obs.trend_state.value} (strength: {obs.trend_strength:.2f}) |",
            f"| Volatility | {obs.volatility_state.value} (ATR: {obs.atr_percent:.2f}%) |",
            f"| Momentum | {obs.momentum_status.value} (RSI: {obs.rsi_value:.1f}) |",
            f"| Volume | {obs.volume_status} ({obs.volume_vs_avg:.2f}x avg) |",
            "",
        ]
        
        if obs.nearest_support:
            lines.append(f"**Support:** ${obs.nearest_support:,.2f}")
        if obs.nearest_resistance:
            lines.append(f"**Resistance:** ${obs.nearest_resistance:,.2f}")
        
        if obs.breakout_detected:
            lines.append(f"⚠️ **BREAKOUT DETECTED** above ${obs.nearest_resistance:,.2f}")
        if obs.breakdown_detected:
            lines.append(f"⚠️ **BREAKDOWN DETECTED** below ${obs.nearest_support:,.2f}")
        if obs.reversal_warning:
            lines.append(f"⚠️ **REVERSAL WARNING:** {obs.reversal_type}")
        
        if obs.open_position_affected:
            lines.extend([
                "",
                f"**Open Position:** {obs.position_direction} @ ${obs.position_entry_price:,.2f}",
                f"**Current PnL:** {obs.position_pnl_pct:+.2f}%",
            ])
        
        lines.extend([
            "",
            f"**Recommendation:** {obs.recommended_review_action}",
            f"**Confidence:** {obs.confidence:.0%}",
            f"**Reason:** {obs.reason}",
            f"**Risk Warning:** {obs.risk_warning}",
            f"**Next Step:** {obs.suggested_next_step}",
        ])
        
        return "\n".join(lines)
    
    @staticmethod
    def to_pipeline_input(obs: ChartObservation) -> Dict:
        """Convert observation to pipeline-compatible dict."""
        return {
            "agent": "LiveChartMonitor",
            "timestamp": obs.timestamp,
            "symbol": obs.symbol,
            "timeframe": obs.timeframe,
            "observations": {
                "trend": obs.trend_state.value,
                "trend_strength": obs.trend_strength,
                "volatility": obs.volatility_state.value,
                "momentum": obs.momentum_status.value,
                "rsi": obs.rsi_value,
                "support": obs.nearest_support,
                "resistance": obs.nearest_resistance,
                "breakout": obs.breakout_detected,
                "breakdown": obs.breakdown_detected,
                "reversal_warning": obs.reversal_warning,
                "volume_anomaly": obs.volume_anomaly,
            },
            "recommendation": {
                "action": obs.recommended_review_action,
                "confidence": obs.confidence,
                "reason": obs.reason,
                "risk": obs.risk_warning,
            },
            "position_context": {
                "affected": obs.open_position_affected,
                "direction": obs.position_direction,
                "pnl_pct": obs.position_pnl_pct,
            } if obs.open_position_affected else None,
        }
