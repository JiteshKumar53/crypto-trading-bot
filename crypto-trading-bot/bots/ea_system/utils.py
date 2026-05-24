"""
Shared utilities for the EA system.
"""

def normalize_symbol(symbol: str) -> str:
    """
    Convert BTC/USD -> BTCUSD (no slash).
    BTCUSD stays BTCUSD.
    Used for internal storage (open_trades.json, etc.)
    """
    return symbol.replace("/", "")


def to_alpaca_symbol(symbol: str) -> str:
    """
    Convert BTCUSD -> BTC/USD for Alpaca API calls.
    BTC/USD stays BTC/USD.
    Supports BTCUSD, ETHUSD, SOLUSD, etc.
    """
    if "/" in symbol:
        return symbol
    # BTCUSD -> BTC/USD, ETHUSD -> ETH/USD, SOLUSD -> SOL/USD
    return f"{symbol[:-3]}/{symbol[-3:]}"
