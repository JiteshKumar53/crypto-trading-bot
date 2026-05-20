"""
Pluggable Data Source Interface
Agent: Data Engineering Team

Standardized interface for all market data sources.
New exchanges/brokers can be added by implementing this interface.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Callable, AsyncIterator
from datetime import datetime
import asyncio


@dataclass
class Candle:
    """Standardized OHLCV candle."""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    symbol: str
    timeframe: str


@dataclass
class Tick:
    """Standardized price tick."""
    timestamp: datetime
    price: float
    size: float
    side: str  # "buy" or "sell"
    symbol: str


@dataclass
class SymbolInfo:
    """Standardized symbol metadata."""
    symbol: str
    name: str
    asset_type: str  # "crypto", "stock", "index", etc.
    exchange: str
    min_order_size: float
    price_precision: int
    qty_precision: int
    is_active: bool = True


class DataSource(ABC):
    """
    Abstract base class for all market data sources.
    
    Implementations: AlpacaSource, HyperliquidSource, BinanceSource, etc.
    """
    
    def __init__(self, name: str, config: Optional[Dict] = None):
        self.name = name
        self.config = config or {}
        self._connected = False
        self._callbacks: List[Callable] = []
    
    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection to data source."""
        pass
    
    @abstractmethod
    async def disconnect(self):
        """Close connection."""
        pass
    
    @abstractmethod
    def get_symbols(self) -> List[SymbolInfo]:
        """Get list of available symbols."""
        pass
    
    @abstractmethod
    def get_latest_price(self, symbol: str) -> Optional[float]:
        """Get latest price for a symbol."""
        pass
    
    @abstractmethod
    def get_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 100,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> List[Candle]:
        """
        Get OHLCV candles.
        
        Args:
            symbol: Trading pair (e.g., "BTC/USD")
            timeframe: e.g., "1m", "5m", "1h", "4h", "1d"
            limit: Number of candles to fetch
            start: Start datetime (optional)
            end: End datetime (optional)
        """
        pass
    
    @abstractmethod
    async def stream_prices(self, symbols: List[str]) -> AsyncIterator[Tick]:
        """
        Subscribe to real-time price stream.
        
        Yields Tick objects as prices arrive.
        """
        pass
    
    @abstractmethod
    def normalize_candle_data(self, raw_data: Dict) -> Optional[Candle]:
        """Convert raw candle data from source to standard Candle format."""
        pass
    
    @abstractmethod
    def normalize_tick_data(self, raw_data: Dict) -> Optional[Tick]:
        """Convert raw tick data from source to standard Tick format."""
        pass
    
    def register_price_callback(self, callback: Callable[[Tick], None]):
        """Register callback for price updates."""
        self._callbacks.append(callback)
    
    def _notify_callbacks(self, tick: Tick):
        """Notify all registered callbacks."""
        for callback in self._callbacks:
            try:
                callback(tick)
            except Exception:
                pass
    
    @property
    def is_connected(self) -> bool:
        return self._connected


class DataSourceRegistry:
    """
    Registry for managing multiple data sources.
    """
    
    def __init__(self):
        self._sources: Dict[str, DataSource] = {}
        self._default_source: Optional[str] = None
    
    def register(self, source: DataSource, make_default: bool = False):
        """Register a data source."""
        self._sources[source.name] = source
        if make_default or self._default_source is None:
            self._default_source = source.name
    
    def get(self, name: Optional[str] = None) -> DataSource:
        """Get a data source by name or default."""
        source_name = name or self._default_source
        if source_name not in self._sources:
            raise KeyError(f"Data source '{source_name}' not registered")
        return self._sources[source_name]
    
    def list_sources(self) -> List[str]:
        """List all registered source names."""
        return list(self._sources.keys())
    
    def remove(self, name: str):
        """Remove a data source."""
        if name in self._sources:
            del self._sources[name]
            if self._default_source == name:
                self._default_source = next(iter(self._sources), None)


# Global registry instance
_registry = DataSourceRegistry()


def get_registry() -> DataSourceRegistry:
    """Get the global data source registry."""
    return _registry
