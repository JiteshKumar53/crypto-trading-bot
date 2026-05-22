"""
Smart EA Bot Company — Yahoo Finance Data Fetcher (via yfinance)
Fetches 1+ year of crypto data from Yahoo Finance (free, no API key).
"""

import yfinance as yf
from datetime import datetime, timezone
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

CRYPTO_SYMBOLS = {
    "BTCUSD": "BTC-USD",
    "ETHUSD": "ETH-USD",
    "SOLUSD": "SOL-USD",
}


def fetch_yahoo_bars(
    symbol: str,
    interval: str = "1h",
    period: str = "1y",
) -> List[Dict]:
    """
    Fetch historical bars from Yahoo Finance using yfinance.
    
    Args:
        symbol: Crypto symbol (e.g., "BTCUSD")
        interval: "1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo"
        period: "1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"
    
    Returns:
        List of bar dicts with timestamp, open, high, low, close, volume
    """
    yahoo_symbol = CRYPTO_SYMBOLS.get(symbol, symbol)
    
    try:
        ticker = yf.Ticker(yahoo_symbol)
        data = ticker.history(period=period, interval=interval)
        
        if data.empty:
            logger.warning(f"No data returned for {symbol}")
            return []
        
        bars = []
        for index, row in data.iterrows():
            # Handle MultiIndex columns from yfinance
            def get_value(col):
                val = row[col]
                if hasattr(val, 'values'):
                    return float(val.values[0])
                return float(val)
            
            bars.append({
                "timestamp": index.isoformat(),
                "open": get_value("Open"),
                "high": get_value("High"),
                "low": get_value("Low"),
                "close": get_value("Close"),
                "volume": int(get_value("Volume")),
            })
        
        logger.info(f"Fetched {len(bars)} bars for {symbol} ({interval} from Yahoo Finance)")
        return bars
        
    except Exception as e:
        logger.error(f"Error fetching {symbol}: {e}")
        return []


def fetch_4h_bars(symbol: str, period: str = "1y") -> List[Dict]:
    """Fetch 4h bars by resampling 1h data."""
    bars_1h = fetch_yahoo_bars(symbol, interval="1h", period=period)
    if len(bars_1h) < 4:
        return bars_1h
    
    # Resample 1h to 4h
    bars_4h = []
    for i in range(0, len(bars_1h) - 3, 4):
        chunk = bars_1h[i:i+4]
        bars_4h.append({
            "timestamp": chunk[0]["timestamp"],
            "open": chunk[0]["open"],
            "high": max(b["high"] for b in chunk),
            "low": min(b["low"] for b in chunk),
            "close": chunk[-1]["close"],
            "volume": sum(b["volume"] for b in chunk),
        })
    
    logger.info(f"Resampled {len(bars_1h)} 1h bars to {len(bars_4h)} 4h bars")
    return bars_4h


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    bars = fetch_yahoo_bars("BTCUSD", interval="1h", period="1y")
    if bars:
        print(f"Fetched {len(bars)} bars")
        print(f"Range: {bars[0]['timestamp']} → {bars[-1]['timestamp']}")
        print(f"Sample: {bars[0]}")
    else:
        print("No data fetched")
