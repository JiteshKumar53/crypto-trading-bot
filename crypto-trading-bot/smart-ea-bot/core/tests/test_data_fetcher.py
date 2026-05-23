"""
Regression tests for data_fetcher.py

Bug history: The timeframe parameter was ignored and hardcoded to 5m.
These tests ensure the bug cannot return silently.
"""

import os
import sys
import unittest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

# Ensure parent is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_fetcher import DataFetcher


class MockBar:
    """Mock Alpaca bar object."""
    def __init__(self, ts, o, h, l, c, v):
        self.t = ts
        self.o = o
        self.h = h
        self.l = l
        self.c = c
        self.v = v


class TestDataFetcherTimeframe(unittest.TestCase):
    """Test that data_fetcher respects timeframe parameter."""

    def setUp(self):
        os.environ["ALPACA_API_KEY"] = "test_key"
        os.environ["ALPACA_SECRET_KEY"] = "test_secret"

    @patch("data_fetcher.tradeapi")
    def test_daily_timeframe_returns_daily_bars(self, mock_tradeapi):
        """BUG: timeframe='1Day' was ignored. Fixed 2026-05-23.
        
        This test verifies that passing timeframe='1Day' results in
        TimeFrame(1, Day) being passed to Alpaca's get_crypto_bars.
        """
        mock_api = MagicMock()
        mock_tradeapi.REST.return_value = mock_api
        mock_tradeapi.TimeFrame = MagicMock()
        mock_tradeapi.TimeFrameUnit = MagicMock()
        mock_tradeapi.TimeFrameUnit.Day = "Day"
        mock_tradeapi.TimeFrameUnit.Minute = "Minute"
        mock_tradeapi.TimeFrameUnit.Hour = "Hour"
        
        # Mock bars
        now = datetime.now(timezone.utc)
        mock_bar = MockBar(now, 100.0, 101.0, 99.0, 100.5, 1000)
        mock_api.get_crypto_bars.return_value = [mock_bar]

        fetcher = DataFetcher(paper=True)
        bars = fetcher.fetch_bars("BTCUSD", timeframe="1Day", limit=10)

        # Assert TimeFrame was called with Day unit
        mock_tradeapi.TimeFrame.assert_called_once()
        call_args = mock_tradeapi.TimeFrame.call_args
        self.assertEqual(call_args[0][1], "Day", 
            f"Expected TimeFrameUnit.Day but got {call_args[0][1]}")
        self.assertEqual(len(bars), 1)

    @patch("data_fetcher.tradeapi")
    def test_5min_timeframe_returns_5min_bars(self, mock_tradeapi):
        """Default timeframe should still be 5Min."""
        mock_api = MagicMock()
        mock_tradeapi.REST.return_value = mock_api
        mock_tradeapi.TimeFrame = MagicMock()
        mock_tradeapi.TimeFrameUnit = MagicMock()
        mock_tradeapi.TimeFrameUnit.Day = "Day"
        mock_tradeapi.TimeFrameUnit.Minute = "Minute"
        
        now = datetime.now(timezone.utc)
        mock_bar = MockBar(now, 100.0, 101.0, 99.0, 100.5, 1000)
        mock_api.get_crypto_bars.return_value = [mock_bar]

        fetcher = DataFetcher(paper=True)
        bars = fetcher.fetch_bars("BTCUSD", timeframe="5Min", limit=10)

        call_args = mock_tradeapi.TimeFrame.call_args
        self.assertEqual(call_args[0][1], "Minute")

    @patch("data_fetcher.tradeapi")
    def test_timeframe_parameter_not_ignored(self, mock_tradeapi):
        """CRITICAL REGRESSION: Previously timeframe was hardcoded to 5Min.
        
        This test calls fetch_bars with '1Day' and verifies the internal
        TimeFrame construction receives the Day unit, not Minute.
        """
        mock_api = MagicMock()
        mock_tradeapi.REST.return_value = mock_api
        mock_tradeapi.TimeFrame = MagicMock()
        mock_tradeapi.TimeFrameUnit = MagicMock()
        mock_tradeapi.TimeFrameUnit.Day = "Day"
        mock_tradeapi.TimeFrameUnit.Minute = "Minute"
        mock_tradeapi.TimeFrameUnit.Hour = "Hour"
        
        now = datetime.now(timezone.utc)
        mock_bar = MockBar(now, 100.0, 101.0, 99.0, 100.5, 1000)
        mock_api.get_crypto_bars.return_value = [mock_bar]

        fetcher = DataFetcher(paper=True)
        
        # Call with 1Day
        fetcher.fetch_bars("BTCUSD", timeframe="1Day", limit=10)
        day_call = mock_tradeapi.TimeFrame.call_args
        self.assertEqual(day_call[0][1], "Day")
        
        # Call with 1h
        mock_tradeapi.TimeFrame.reset_mock()
        fetcher.fetch_bars("BTCUSD", timeframe="1h", limit=10)
        hour_call = mock_tradeapi.TimeFrame.call_args
        self.assertEqual(hour_call[0][1], "Hour")


class TestDataFetcherSymbolFormatting(unittest.TestCase):
    """Test symbol formatting for Alpaca."""

    def setUp(self):
        os.environ["ALPACA_API_KEY"] = "test_key"
        os.environ["ALPACA_SECRET_KEY"] = "test_secret"

    @patch("data_fetcher.tradeapi")
    def test_btcusd_converted_to_btc_usd(self, mock_tradeapi):
        """BTCUSD should be converted to BTC/USD for Alpaca API."""
        mock_api = MagicMock()
        mock_tradeapi.REST.return_value = mock_api
        mock_tradeapi.TimeFrame = MagicMock()
        mock_tradeapi.TimeFrameUnit = MagicMock()
        mock_tradeapi.TimeFrameUnit.Day = "Day"
        
        now = datetime.now(timezone.utc)
        mock_bar = MockBar(now, 100.0, 101.0, 99.0, 100.5, 1000)
        mock_api.get_crypto_bars.return_value = [mock_bar]

        fetcher = DataFetcher(paper=True)
        fetcher.fetch_bars("BTCUSD", timeframe="1Day", limit=10)

        # Check the symbol passed to get_crypto_bars
        call_args = mock_api.get_crypto_bars.call_args
        symbol_passed = call_args[0][0]
        self.assertEqual(symbol_passed, "BTC/USD")


if __name__ == "__main__":
    unittest.main(verbosity=2)
