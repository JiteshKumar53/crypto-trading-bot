"""
Smart EA Bot Company — Data Fetcher
Fetch 5m OHLCV bars from Alpaca for backtesting and live trading.
"""

import os
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict

try:
    import alpaca_trade_api as tradeapi
except ImportError:
    tradeapi = None

logger = logging.getLogger(__name__)


class DataFetcher:
    """
    Fetch historical and live 5m bars from Alpaca.
    No complex preprocessing. Raw bars → strategy.
    """

    def __init__(self, paper: bool = True):
        self.api_key = os.getenv("ALPACA_API_KEY")
        self.secret_key = os.getenv("ALPACA_SECRET_KEY")
        self.base_url = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
        self.paper = paper

        if not self.api_key or not self.secret_key:
            raise ValueError("ALPACA_API_KEY and ALPACA_SECRET_KEY must be set")

        if tradeapi:
            self.api = tradeapi.REST(self.api_key, self.secret_key, self.base_url, api_version="v2")
        else:
            self.api = None
            logger.warning("alpaca-trade-api not installed. Running in mock mode.")

    def fetch_bars(
        self,
        symbol: str,
        timeframe: str = "5Min",
        limit: int = 1000,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> List[Dict]:
        """
        Fetch OHLCV bars for a symbol.
        Returns list of dicts: [{timestamp, open, high, low, close, volume}, ...]
        """
        if self.api is None:
            logger.error("Alpaca API not available")
            return []

        try:
            # Alpaca uses BTC/USD format
            bars = self.api.get_crypto_bars(
                symbol,
                tradeapi.TimeFrame(5, tradeapi.TimeFrameUnit.Minute),
                start=start.isoformat() if start else None,
                end=end.isoformat() if end else None,
                limit=limit,
            )

            result = []
            for bar in bars:
                result.append({
                    "timestamp": bar.timestamp.isoformat(),
                    "open": float(bar.open),
                    "high": float(bar.high),
                    "low": float(bar.low),
                    "close": float(bar.close),
                    "volume": float(bar.volume),
                })

            logger.info(f"Fetched {len(result)} bars for {symbol}")
            return result

        except Exception as e:
            logger.error(f"Failed to fetch bars for {symbol}: {e}")
            return []

    def fetch_latest_price(self, symbol: str) -> Optional[float]:
        """Fetch latest trade price for a symbol."""
        if self.api is None:
            return None

        try:
            trades = self.api.get_crypto_latest_trade(symbol)
            return float(trades.price)
        except Exception as e:
            logger.error(f"Failed to fetch price for {symbol}: {e}")
            return None
