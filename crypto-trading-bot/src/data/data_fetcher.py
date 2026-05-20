"""
Data Fetcher + Validator
Agent: Data Engineering Team

Fetches and validates market data from Alpaca.
Ensures data quality before passing to agents.
"""

import logging
from typing import Optional, Dict, List
from datetime import datetime, timedelta
import pandas as pd

try:
    from ..broker.alpaca_client import AlpacaPaperClient
except ImportError:
    from broker.alpaca_client import AlpacaPaperClient

logger = logging.getLogger(__name__)


class DataFetcher:
    """Fetches and validates crypto market data."""

    def __init__(self, client: Optional[AlpacaPaperClient] = None):
        self.client = client or AlpacaPaperClient()
        self._cache: Dict[str, pd.DataFrame] = {}

    def fetch_hourly_bars(
        self,
        symbol: str,
        limit: int = 100,
        validate: bool = True,
    ) -> Optional[pd.DataFrame]:
        """
        Fetch hourly bars for a crypto symbol.
        Uses explicit date range to ensure full historical data.
        Returns DataFrame or None if fetch/validation fails.
        """
        logger.info(f"Fetching {limit} hourly bars for {symbol}")

        try:
            # Use date range instead of just limit to get proper historical data
            from datetime import timezone
            from alpaca.data.requests import CryptoBarsRequest
            from alpaca.data.timeframe import TimeFrame
            end = datetime.now(timezone.utc)
            start = end - timedelta(hours=limit)

            request = CryptoBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=TimeFrame.Hour,
                start=start,
                end=end,
            )

            if self.client.data_client is None:
                logger.warning("Alpaca data client not initialized")
                return None

            bars = self.client.data_client.get_crypto_bars(request)
            df = bars.df if hasattr(bars, 'df') else None

            if df is None or df.empty:
                logger.warning(f"No data returned for {symbol}")
                return None

            if validate:
                if not self.validate_data(df, symbol):
                    logger.warning(f"Data validation failed for {symbol}")
                    return None

            self._cache[symbol] = df
            logger.info(f"Fetched {len(df)} bars for {symbol}")
            return df

        except Exception as e:
            logger.error(f"Failed to fetch data for {symbol}: {e}")
            return None

    def validate_data(self, df: pd.DataFrame, symbol: str) -> bool:
        """
        Validate data quality.
        Checks for missing values, zero prices, suspicious gaps.
        """
        required_columns = ["open", "high", "low", "close", "volume", "vwap"]

        # Check columns exist
        for col in required_columns:
            if col not in df.columns:
                logger.warning(f"Missing column {col} in {symbol} data")
                return False

        # Check for NaN values
        if df[required_columns].isnull().any().any():
            nan_count = df[required_columns].isnull().sum().sum()
            logger.warning(f"Found {nan_count} NaN values in {symbol} data")
            # Don't fail on small number of NaN, just warn
            if nan_count > len(df) * 0.1:  # >10% NaN
                return False

        # Check for zero or negative prices
        price_cols = ["open", "high", "low", "close", "vwap"]
        if (df[price_cols] <= 0).any().any():
            logger.warning(f"Zero or negative prices found in {symbol} data")
            return False

        # Check for logical ordering: high >= low
        if (df["high"] < df["low"]).any():
            logger.warning(f"High < Low found in {symbol} data")
            return False

        # Check OHLC consistency
        if (df["high"] < df[["open", "close"]].max(axis=1)).any():
            logger.warning(f"High < max(open, close) in {symbol} data")
            # This can happen with adjusted data, just warn

        if (df["low"] > df[["open", "close"]].min(axis=1)).any():
            logger.warning(f"Low > min(open, close) in {symbol} data")

        # Check for large gaps in timestamps
        if len(df) > 1:
            df_sorted = df.sort_index()
            if isinstance(df_sorted.index, pd.MultiIndex):
                timestamps = df_sorted.index.get_level_values(1).to_series()
            else:
                timestamps = pd.Series(df_sorted.index)
            time_diff = timestamps.diff().dropna()
            median_diff = time_diff.median()
            large_gaps = time_diff[time_diff > median_diff * 3]
            if len(large_gaps) > 0:
                logger.warning(
                    f"Found {len(large_gaps)} large time gaps in {symbol} data"
                )
                # Don't fail, just warn

        logger.info(f"Data validation passed for {symbol}")
        return True

    def get_latest_price(self, symbol: str) -> Optional[float]:
        """Get the latest closing price for a symbol.
        
        Uses cached data if available to avoid extra API calls.
        Falls back to fetching recent bars with a wider window for reliability.
        """
        # Try cache first (avoids extra API call, already fetched in pipeline)
        cached = self.get_cached(symbol)
        if cached is not None and not cached.empty:
            return float(cached["close"].iloc[-1])
        
        # Fallback: fetch more bars than needed for reliability
        df = self.fetch_hourly_bars(symbol, limit=24)
        if df is not None and not df.empty:
            return float(df["close"].iloc[-1])
        return None

    def get_cached(self, symbol: str) -> Optional[pd.DataFrame]:
        """Get cached data for a symbol."""
        return self._cache.get(symbol)

    def clear_cache(self):
        """Clear all cached data."""
        self._cache.clear()


class DataValidator:
    """Additional data validation utilities."""

    @staticmethod
    def check_lookahead_bias(df: pd.DataFrame, signal_timestamp: datetime) -> bool:
        """
        Check that no data after signal_timestamp is used.
        Returns True if no lookahead detected.
        """
        timestamps = df.index.get_level_values(1) if isinstance(df.index, pd.MultiIndex) else df.index
        future_data = timestamps[timestamps > signal_timestamp]
        if len(future_data) > 0:
            logger.error(f"Lookahead bias detected: {len(future_data)} future bars")
            return False
        return True

    @staticmethod
    def check_data_leakage(train_df: pd.DataFrame, test_df: pd.DataFrame) -> bool:
        """
        Check for data leakage between train and test sets.
        Returns True if no leakage detected.
        """
        train_timestamps = set(train_df.index.get_level_values(1) if isinstance(train_df.index, pd.MultiIndex) else train_df.index)
        test_timestamps = set(test_df.index.get_level_values(1) if isinstance(test_df.index, pd.MultiIndex) else test_df.index)

        overlap = train_timestamps & test_timestamps
        if overlap:
            logger.error(f"Data leakage detected: {len(overlap)} overlapping timestamps")
            return False
        return True
