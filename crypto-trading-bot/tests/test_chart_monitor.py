"""
Tests for Live Chart Monitoring Agent
Agent: Quality Assurance Team
"""

import pytest
import numpy as np
from datetime import datetime, timezone, timedelta
from chart_monitor.data_sources.base import Candle
from chart_monitor.chart_analyzer import ChartAnalyzer, TrendState, VolatilityState, MomentumState
from chart_monitor.live_chart_monitor import ChartObservationReporter


@pytest.fixture
def sample_candles():
    """Generate sample uptrend candles."""
    candles = []
    base_price = 100.0
    for i in range(50):
        trend = i * 0.5  # Gradual uptrend
        noise = np.sin(i * 0.5) * 2.0
        close = base_price + trend + noise
        high = close + abs(np.random.normal(1.0, 0.5))
        low = close - abs(np.random.normal(1.0, 0.5))
        open_price = close - np.random.normal(0, 0.5)
        
        candles.append(Candle(
            timestamp=datetime.now(timezone.utc) - timedelta(hours=50-i),
            open=open_price,
            high=high,
            low=low,
            close=close,
            volume=1000 + np.random.normal(0, 200),
            symbol="BTC/USD",
            timeframe="1h",
        ))
    return candles


@pytest.fixture
def ranging_candles():
    """Generate ranging candles."""
    candles = []
    for i in range(50):
        close = 100.0 + np.sin(i * 0.3) * 5.0  # Oscillate around 100
        high = close + 1.0
        low = close - 1.0
        
        candles.append(Candle(
            timestamp=datetime.now(timezone.utc) - timedelta(hours=50-i),
            open=close - 0.2,
            high=high,
            low=low,
            close=close,
            volume=1000,
            symbol="BTC/USD",
            timeframe="1h",
        ))
    return candles


class TestChartAnalyzer:
    """Test chart technical analysis functions."""
    
    def test_analyzer_initialization(self):
        analyzer = ChartAnalyzer()
        assert analyzer is not None
    
    def test_trend_detection_uptrend(self, sample_candles):
        analyzer = ChartAnalyzer()
        obs = analyzer.analyze(sample_candles, "BTC/USD", "1h")
        
        assert obs.symbol == "BTC/USD"
        assert obs.timeframe == "1h"
        assert obs.current_price > 0
        assert obs.trend_state in [TrendState.UPTREND, TrendState.CHOPPY]
        assert obs.candles_analyzed == 50
    
    def test_trend_detection_ranging(self, ranging_candles):
        analyzer = ChartAnalyzer()
        obs = analyzer.analyze(ranging_candles, "BTC/USD", "1h")
        
        # Ranging candles should be detected as ranging or choppy
        assert obs.trend_state in [TrendState.RANGING, TrendState.CHOPPY, TrendState.UNKNOWN]
    
    def test_support_resistance_detection(self, ranging_candles):
        analyzer = ChartAnalyzer()
        obs = analyzer.analyze(ranging_candles, "BTC/USD", "1h")
        
        # Should find support below current price
        if obs.nearest_support:
            assert obs.nearest_support < obs.current_price
        
        # Should find resistance above current price
        if obs.nearest_resistance:
            assert obs.nearest_resistance > obs.current_price
    
    def test_rsi_calculation(self, sample_candles):
        analyzer = ChartAnalyzer()
        obs = analyzer.analyze(sample_candles, "BTC/USD", "1h")
        
        # RSI should be between 0 and 100
        if obs.rsi_value is not None:
            assert 0 <= obs.rsi_value <= 100
    
    def test_volatility_detection(self, sample_candles):
        analyzer = ChartAnalyzer()
        obs = analyzer.analyze(sample_candles, "BTC/USD", "1h")
        
        # Should have some volatility state
        assert obs.volatility_state is not None
        assert obs.atr_value >= 0
    
    def test_position_context(self, sample_candles):
        analyzer = ChartAnalyzer()
        position = {
            "side": "long",
            "entry_price": 110.0,
            "qty": 1.0,
        }
        obs = analyzer.analyze(sample_candles, "BTC/USD", "1h", position)
        
        assert obs.open_position_affected is True
        assert obs.position_direction == "long"
        assert obs.position_entry_price == 110.0
        assert obs.position_pnl_pct is not None
    
    def test_recommendation_generation(self, sample_candles):
        analyzer = ChartAnalyzer()
        obs = analyzer.analyze(sample_candles, "BTC/USD", "1h")
        
        # Should have some recommendation
        assert obs.recommended_review_action is not None
        assert obs.confidence >= 0
        assert obs.confidence <= 1
        assert obs.reason is not None
    
    def test_insufficient_data(self):
        analyzer = ChartAnalyzer()
        candles = [
            Candle(
                timestamp=datetime.now(timezone.utc),
                open=100.0,
                high=101.0,
                low=99.0,
                close=100.5,
                volume=1000.0,
                symbol="BTC/USD",
                timeframe="1h",
            )
        ]
        obs = analyzer.analyze(candles, "BTC/USD", "1h")
        
        assert obs.trend_state == TrendState.UNKNOWN
        assert "Insufficient data" in obs.reason
    
    def test_observation_history(self, sample_candles):
        analyzer = ChartAnalyzer()
        
        # Analyze multiple times
        for _ in range(3):
            analyzer.analyze(sample_candles, "BTC/USD", "1h")
        
        history = analyzer.get_observation_history("BTC/USD", "1h", n=5)
        assert len(history) == 3
        assert history[0].symbol == "BTC/USD"


class TestChartObservationReporter:
    """Test observation reporting."""
    
    def test_markdown_report(self, sample_candles):
        analyzer = ChartAnalyzer()
        obs = analyzer.analyze(sample_candles, "BTC/USD", "1h")
        
        markdown = ChartObservationReporter.to_markdown(obs)
        assert "Chart Observation" in markdown
        assert "BTC/USD" in markdown
        assert obs.trend_state.value in markdown
    
    def test_pipeline_input(self, sample_candles):
        analyzer = ChartAnalyzer()
        obs = analyzer.analyze(sample_candles, "BTC/USD", "1h")
        
        pipeline_data = ChartObservationReporter.to_pipeline_input(obs)
        assert pipeline_data["agent"] == "LiveChartMonitor"
        assert pipeline_data["symbol"] == "BTC/USD"
        assert "observations" in pipeline_data
        assert "recommendation" in pipeline_data
