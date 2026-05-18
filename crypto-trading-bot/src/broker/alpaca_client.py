"""
Alpaca Paper Trading Client
Agent: Broker Execution Team

Wraps Alpaca API for paper trading only.
Forces paper mode. Blocks live trading.
"""

import os
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class OrderResult:
    symbol: str
    side: str
    qty: float
    order_id: Optional[str]
    status: str
    filled_avg_price: Optional[float]
    timestamp: datetime
    paper_mode: bool
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.error is None and self.order_id is not None


class AlpacaPaperClient:
    """
    Alpaca paper trading client.
    NEVER connects to live trading endpoints.
    """

    def __init__(self):
        self.api_key = os.getenv("ALPACA_API_KEY")
        self.secret_key = os.getenv("ALPACA_SECRET_KEY")
        self.paper_mode = os.getenv("ALPACA_PAPER", "true").lower() == "true"
        self.base_url = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")

        if not self.api_key or not self.secret_key:
            raise ValueError("ALPACA_API_KEY and ALPACA_SECRET_KEY must be set")

        if not self.paper_mode:
            raise ValueError("ALPACA_PAPER must be true. Live trading requires CEO approval.")

        # Lazy import to avoid dependency issues during setup
        try:
            from alpaca.trading.client import TradingClient
            from alpaca.data import CryptoHistoricalDataClient
            self.trading_client = TradingClient(
                self.api_key, self.secret_key, paper=True
            )
            self.data_client = CryptoHistoricalDataClient(self.api_key, self.secret_key)
        except ImportError:
            logger.warning("alpaca-py not installed. Client will be unavailable.")
            self.trading_client = None
            self.data_client = None

    def is_paper(self) -> bool:
        """Confirm paper mode."""
        return self.paper_mode and self.base_url == "https://paper-api.alpaca.markets"

    def get_account(self) -> Optional[Dict]:
        """Fetch paper trading account info."""
        if not self.trading_client:
            return None
        try:
            account = self.trading_client.get_account()
            return {
                "id": account.id,
                "cash": float(account.cash),
                "portfolio_value": float(account.portfolio_value),
                "equity": float(account.equity),
                "buying_power": float(account.buying_power),
                "paper_mode": self.is_paper(),
            }
        except Exception as e:
            logger.error(f"Failed to fetch account: {e}")
            return None

    def get_positions(self) -> List[Dict]:
        """Fetch open positions."""
        if not self.trading_client:
            return []
        try:
            positions = self.trading_client.get_all_positions()
            return [
                {
                    "symbol": p.symbol,
                    "qty": float(p.qty),
                    "market_value": float(p.market_value),
                    "avg_entry_price": float(p.avg_entry_price),
                    "current_price": float(p.current_price),
                    "unrealized_pl": float(p.unrealized_pl),
                    "unrealized_plpc": float(p.unrealized_plpc),
                }
                for p in positions
            ]
        except Exception as e:
            logger.error(f"Failed to fetch positions: {e}")
            return []

    def get_open_orders(self) -> List[Dict]:
        """Fetch open orders."""
        if not self.trading_client:
            return []
        try:
            orders = self.trading_client.get_orders()
            return [
                {
                    "id": o.id,
                    "symbol": o.symbol,
                    "side": o.side.value,
                    "qty": float(o.qty),
                    "status": o.status.value,
                    "submitted_at": o.submitted_at,
                }
                for o in orders
            ]
        except Exception as e:
            logger.error(f"Failed to fetch open orders: {e}")
            return []

    def submit_order(
        self,
        symbol: str,
        side: str,
        qty: float,
        order_type: str = "market",
        time_in_force: str = "gtc",
    ) -> OrderResult:
        """
        Submit a paper order.
        Requires paper mode confirmation.
        """
        # Validate paper mode
        if not self.is_paper():
            return OrderResult(
                symbol=symbol,
                side=side,
                qty=qty,
                order_id=None,
                status="rejected",
                filled_avg_price=None,
                timestamp=datetime.utcnow(),
                paper_mode=False,
                error="Not in paper mode. Live trading requires CEO approval.",
            )

        if not self.trading_client:
            return OrderResult(
                symbol=symbol,
                side=side,
                qty=qty,
                order_id=None,
                status="rejected",
                filled_avg_price=None,
                timestamp=datetime.utcnow(),
                paper_mode=True,
                error="Alpaca client not initialized",
            )

        # Map crypto symbols to Alpaca format
        # Alpaca uses BTCUSD, ETHUSD, SOLUSD (no slash)
        alpaca_symbol = symbol.replace("/", "")

        try:
            from alpaca.trading.requests import MarketOrderRequest
            from alpaca.trading.enums import OrderSide, TimeInForce

            side_enum = OrderSide.BUY if side.lower() == "buy" else OrderSide.SELL
            tif_enum = TimeInForce.GTC if time_in_force.lower() == "gtc" else TimeInForce.IOC

            order_request = MarketOrderRequest(
                symbol=alpaca_symbol,
                qty=qty,
                side=side_enum,
                time_in_force=tif_enum,
            )

            order = self.trading_client.submit_order(order_request)

            logger.info(
                f"Paper order submitted: {side} {qty} {alpaca_symbol} "
                f"order_id={order.id}"
            )

            return OrderResult(
                symbol=symbol,
                side=side,
                qty=qty,
                order_id=order.id,
                status=order.status.value,
                filled_avg_price=float(order.filled_avg_price) if order.filled_avg_price else None,
                timestamp=datetime.utcnow(),
                paper_mode=True,
            )

        except Exception as e:
            logger.error(f"Failed to submit order: {e}")
            return OrderResult(
                symbol=symbol,
                side=side,
                qty=qty,
                order_id=None,
                status="rejected",
                filled_avg_price=None,
                timestamp=datetime.utcnow(),
                paper_mode=True,
                error=str(e),
            )

    def get_latest_crypto_bars(self, symbol: str, limit: int = 100):
        """Fetch latest crypto bars."""
        if not self.data_client:
            return None
        try:
            from alpaca.data.requests import CryptoBarsRequest
            from alpaca.data.timeframe import TimeFrame

            request = CryptoBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=TimeFrame.Hour,
                limit=limit,
            )
            bars = self.data_client.get_crypto_bars(request)
            return bars.df
        except Exception as e:
            logger.error(f"Failed to fetch crypto bars: {e}")
            return None
