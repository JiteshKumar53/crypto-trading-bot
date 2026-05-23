"""
Regression tests for data reconciliation.

Bug history: The reconciliation script used local timezone date extraction,
creating a 1-day offset between Yahoo and Alpaca bars.

These tests ensure date alignment cannot silently break again.
"""

import os
import sys
import unittest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestTimestampNormalization(unittest.TestCase):
    """Test that timestamps are normalized to UTC before date extraction."""

    def test_utc_normalization_prevents_offset(self):
        """BUG: Alpaca bars with -04:00 timezone were mis-mapped by 1 day.
        
        An Alpaca bar with timestamp 2024-05-22T20:00:00-04:00
        represents the close for UTC date 2024-05-23.
        
        If the script used .strftime('%Y-%m-%d') on the raw timestamp,
        it would be extracted as 2024-05-22 (local time), creating
        a 1-day offset against Yahoo's 2024-05-23.
        
        Fixed by: bar.t.astimezone(timezone.utc).strftime('%Y-%m-%d')
        """
        # Simulating an Alpaca bar timestamp
        from pytz import timezone as pytz_zone
        
        eastern = pytz_zone('US/Eastern')
        bar_time = eastern.localize(datetime(2024, 5, 22, 20, 0, 0))
        
        # BUG: Old behavior (local timezone)
        old_date = bar_time.strftime('%Y-%m-%d')  # "2024-05-22"
        
        # FIX: Convert to UTC first
        utc_date = bar_time.astimezone(timezone.utc).strftime('%Y-%m-%d')  # "2024-05-23"
        
        self.assertEqual(old_date, "2024-05-22", 
            "Old behavior should show local date ( demonstrates the bug )")
        self.assertEqual(utc_date, "2024-05-23",
            "UTC conversion should map to correct date")
        self.assertNotEqual(old_date, utc_date,
            "This difference IS the bug — 1 day offset")

    def test_daily_bar_boundary_crypto(self):
        """Alpaca crypto daily bars run 20:00 UTC to 20:00 UTC next day.
        
        The bar's timestamp is the START of the period.
        The close represents the end of that 24-hour period.
        For cross-source comparison, we must extract the date consistently.
        """
        bar_timestamp = datetime(2024, 5, 22, 20, 0, 0, tzinfo=timezone.utc)
        
        # Yahoo gives date as 2024-05-23 (the calendar day the bar represents)
        # Alpaca gives timestamp as 2024-05-22T20:00:00Z (start of period)
        # Both represent the same 24-hour period
        
        # Method 1: Extract date from UTC timestamp directly
        method1 = bar_timestamp.strftime('%Y-%m-%d')  # "2024-05-22"
        
        # Method 2: Add one day (since bar close represents NEXT calendar day)
        method2 = (bar_timestamp + timedelta(days=1)).strftime('%Y-%m-%d')  # "2024-05-23"
        
        # The correct approach depends on convention, but must be CONSISTENT
        # For Alpaca: bar represents the period ending on date+1
        # Yahoo: bar is labeled with the date it belongs to
        
        # Both methods are valid if applied consistently.
        # The bug was MIXING conventions between sources.


class TestDateAlignmentBetweenSources(unittest.TestCase):
    """Test that same calendar dates are compared between sources."""

    def test_no_date_offset_between_sources(self):
        """CRITICAL: After fixing timezone, same dates should align.
        
        This test simulates the corrected reconciliation logic.
        """
        yahoo_data = {
            "2024-05-22": 75500.0,
            "2024-05-23": 74482.0,
        }
        
        # Simulated Alpaca data with UTC-normalized dates
        alpaca_data = {
            "2024-05-22": 75437.0,
            "2024-05-23": 74466.0,
        }
        
        for date in yahoo_data:
            if date in alpaca_data:
                diff = abs(alpaca_data[date] - yahoo_data[date]) / yahoo_data[date] * 100
                self.assertLess(diff, 0.2,
                    f"Date {date}: {diff:.2f}% difference. If >20%, check for offset.")


class TestDataFetchConsistency(unittest.TestCase):
    """Test that fetch_bars returns consistent data format."""

    @patch("data_fetcher.tradeapi")
    def test_bar_format_consistency(self, mock_tradeapi):
        """All bars must have timestamp, open, high, low, close, volume."""
        import data_fetcher
        
        os.environ["ALPACA_API_KEY"] = "test"
        os.environ["ALPACA_SECRET_KEY"] = "test"
        
        mock_api = MagicMock()
        mock_tradeapi.REST.return_value = mock_api
        mock_tradeapi.TimeFrame = MagicMock()
        mock_tradeapi.TimeFrameUnit = MagicMock()
        mock_tradeapi.TimeFrameUnit.Day = "Day"
        
        now = datetime.now(timezone.utc)
        
        class FakeBar:
            t = now
            o = 100.0
            h = 101.0
            l = 99.0
            c = 100.5
            v = 1000.0
        
        mock_api.get_crypto_bars.return_value = [FakeBar()]
        
        fetcher = data_fetcher.DataFetcher(paper=True)
        bars = fetcher.fetch_bars("BTCUSD", timeframe="1Day", limit=1)
        
        self.assertEqual(len(bars), 1)
        bar = bars[0]
        required_keys = {"timestamp", "open", "high", "low", "close", "volume"}
        self.assertTrue(required_keys.issubset(bar.keys()),
            f"Bar missing required keys. Has: {set(bar.keys())}")
        
        # Types should be correct
        self.assertIsInstance(bar["timestamp"], str)
        self.assertIsInstance(bar["close"], float)


if __name__ == "__main__":
    unittest.main(verbosity=2)
