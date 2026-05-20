"""
Alpaca Data Source Implementation
Agent: Data Engineering Team

Implements DataSource interface for Alpaca Markets paper trading.
Uses Alpaca SDK for REST API and WebSocket streaming.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, AsyncIterator
import asyncio
import json

from .base import DataSource, Candle, Tick, SymbolInfo

logger = logging.getLogger(__name__)


class AlpacaDataSource(DataSource):
    """
    Alpaca Markets data source.
    Supports crypto and equities (crypto only for this project).
    """
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__("alpaca", config)
        self._client = None
        self._data_client = None
        self._stream = None
        self._latest_prices: Dict[str, Tick] = {}
    
    async def connect(self) -> bool:
        """Connect to Alpaca APIs."""
        try:
            from broker.alpaca_client import AlpacaPaperClient
            self._client = AlpacaPaperClient()
            
            # Test connection
            account = self._client.get_account()
            if account:
                self._connected = True
                logger.info(f"[AlpacaSource] Connected. Account equity: ${float(account['equity']):,.2f}")
                return True
            
        except Exception as e:
            logger.error(f"[AlpacaSource] Connection failed: {e}")
        
        return False
    
    async def disconnect(self):
        """Disconnect from Alpaca."""
        self._connected = False
        logger.info("[AlpacaSource] Disconnected")
    
    def get_symbols(self) -> List[SymbolInfo]:
        """Get available crypto symbols."""
        symbols = [
            SymbolInfo("BTC/USD", "Bitcoin", "crypto", "Alpaca", 1.0, 2, 6),
            SymbolInfo("ETH/USD", "Ethereum", "crypto", "Alpaca", 1.0, 2, 6),
            SymbolInfo("SOL/USD", "Solana", "crypto", "Alpaca", 1.0, 2, 6),
        ]
        return symbols
    
    def get_latest_price(self, symbol: str) -> Optional[float]:
        """Get latest price from Alpaca."""
        try:
            from data.data_fetcher import DataFetcher
            fetcher = DataFetcher(self._client)
            return fetcher.get_latest_price(symbol)
        except Exception as e:
            logger.warning(f"[AlpacaSource] Failed to get price for {symbol}: {e}")
            return None
    
    def get_ohlcv(
        self,
        symbol: str,
        timeframe: str = "1h",
        limit: int = 100,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> List[Candle]:
        """Get OHLCV candles from Alpaca."""
        try:
            from data.data_fetcher import DataFetcher
            fetcher = DataFetcher(self._client)
            
            # Convert timeframe string to bar limit
            tf_map = {"1m": 1, "5m": 5, "15m": 15, "1h": 60, "4h": 240, "1d": 1440}
            hours = tf_map.get(timeframe, 60)
            
            df = fetcher.fetch_hourly_bars(symbol, limit=limit)
            if df is None or df.empty:
                return []
            
            candles = []
            for idx, row in df.iterrows():
                ts = idx[1] if isinstance(idx, tuple) else idx
                candles.append(self.normalize_candle_data({
                    "timestamp": ts,
                    "open": row["open"],
                    "high": row["high"],
                    "low": row["low"],
                    "close": row["close"],
                    "volume": row["volume"],
                    "symbol": symbol,
                    "timeframe": timeframe,
                }))
            
            return [c for c in candles if c is not None]
            
        except Exception as e:
            logger.error(f"[AlpacaSource] Failed to get OHLCV for {symbol}: {e}")
            return []
    
    async def stream_prices(self, symbols: List[str]) -> AsyncIterator[Tick]:
        """
        Stream real-time prices via WebSocket.
        
        Note: Alpaca crypto streaming requires specific WebSocket setup.
        For now, we poll REST API as fallback.
        """
        logger.info(f"[AlpacaSource] Starting price stream for: {symbols}")
        
        # Fallback: poll REST API every 5 seconds
        while self._connected:
            for symbol in symbols:
                try:
                    price = self.get_latest_price(symbol)
                    if price:
                        tick = Tick(
                            timestamp=datetime.now(timezone.utc),
                            price=price,
                            size=0.0,
                            side="unknown",
                            symbol=symbol,
                        )
                        self._latest_prices[symbol] = tick
                        self._notify_callbacks(tick)
                        yield tick
                except Exception as e:
                    logger.warning(f"[AlpacaSource] Stream error for {symbol}: {e}")
            
            await asyncio.sleep(5)
    
    def normalize_candle_data(self, raw_data: Dict) -> Optional[Candle]:
        """Normalize Alpaca candle to standard format."""
        try:
            ts = raw_data.get("timestamp")
            if isinstance(ts, str):
                ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            elif not isinstance(ts, datetime):
                ts = datetime.now(timezone.utc)
            
            return Candle(
                timestamp=ts,
                open=float(raw_data["open"]),
                high=float(raw_data["high"]),
                low=float(raw_data["low"]),
                close=float(raw_data["close"]),
                volume=float(raw_data.get("volume", 0)),
                symbol=raw_data.get("symbol", ""),
                timeframe=raw_data.get("timeframe", "1h"),
            )
        except (KeyError, ValueError, TypeError) as e:
            logger.warning(f"[AlpacaSource] Failed to normalize candle: {e}")
            return None
    
    def normalize_tick_data(self, raw_data: Dict) -> Optional[Tick]:
        """Normalize Alpaca tick to standard format."""
        try:
            ts = raw_data.get("timestamp", datetime.now(timezone.utc))
            if isinstance(ts, str):
                ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            
            return Tick(
                timestamp=ts,
                price=float(raw_data["price"]),
                size=float(raw_data.get("size", 0)),
                side=raw_data.get("side", "unknown"),
                symbol=raw_data.get("symbol", ""),
            )
        except (KeyError, ValueError) as e:
            logger.warning(f"[AlpacaSource] Failed to normalize tick: {e}")
            return None
    
    def get_latest_cached_price(self, symbol: str) -> Optional[float]:
        """Get latest cached price."""
        tick = self._latest_prices.get(symbol)
        return tick.price if tick else None
