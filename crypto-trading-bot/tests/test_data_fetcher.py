"""
Tests for Data Fetcher
Agent: Data Engineering Team
"""

import pytest
import sys
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from data.data_fetcher import DataFetcher, DataValidator


@pytest.fixture
def sample_data():
    """Create sample valid OHLCV data."""
    dates = pd.date_range("2026-05-01", periods=10, freq="h")
    df = pd.DataFrame({
        "open": [100.0] * 10,
        "high": [105.0] * 10,
        "low": [95.0] * 10,
        "close": [102.0] * 10,
        "volume": [1000.0] * 10,
        "vwap": [101.0] * 10,
    }, index=dates)
    return df


def test_validate_good_data(sample_data):
    fetcher = DataFetcher.__new__(DataFetcher)
    # Add multi-index to match Alpaca format
    sample_data.index = pd.MultiIndex.from_product([["TEST/USD"], sample_data.index])
    assert fetcher.validate_data(sample_data, "TEST/USD") is True


def test_validate_missing_column(sample_data):
    fetcher = DataFetcher.__new__(DataFetcher)
    bad_data = sample_data.drop(columns=["volume"])
    assert fetcher.validate_data(bad_data, "TEST/USD") is False


def test_validate_zero_prices(sample_data):
    fetcher = DataFetcher.__new__(DataFetcher)
    bad_data = sample_data.copy()
    bad_data.loc[bad_data.index[0], "close"] = 0
    assert fetcher.validate_data(bad_data, "TEST/USD") is False


def test_validate_high_less_than_low(sample_data):
    fetcher = DataFetcher.__new__(DataFetcher)
    bad_data = sample_data.copy()
    bad_data.loc[bad_data.index[0], "high"] = 90
    bad_data.loc[bad_data.index[0], "low"] = 110
    assert fetcher.validate_data(bad_data, "TEST/USD") is False


def test_check_lookahead_bias(sample_data):
    signal_time = pd.Timestamp("2026-05-01 05:00:00")
    # Add multi-index structure to match Alpaca format
    sample_data.index = pd.MultiIndex.from_product([["TEST/USD"], sample_data.index])
    # The signal is at 05:00, and data goes up to 09:00, so there ARE future bars
    # This should detect lookahead bias → return False
    assert DataValidator.check_lookahead_bias(sample_data, signal_time) is False


def test_check_no_lookahead_bias(sample_data):
    signal_time = pd.Timestamp("2026-05-01 10:00:00")
    sample_data.index = pd.MultiIndex.from_product([["TEST/USD"], sample_data.index])
    # Signal is after all data, no lookahead → return True
    assert DataValidator.check_lookahead_bias(sample_data, signal_time) is True


def test_check_data_leakage(sample_data):
    train = sample_data.iloc[:5]
    test = sample_data.iloc[5:]
    # Add multi-index structure
    train.index = pd.MultiIndex.from_product([["TEST/USD"], train.index])
    test.index = pd.MultiIndex.from_product([["TEST/USD"], test.index])
    assert DataValidator.check_data_leakage(train, test) is True
