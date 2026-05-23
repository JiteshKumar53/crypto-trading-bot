"""
Smart EA Bot Company — Paper Trading Daemon v2.0
Runs Trend Rider v5.6 using Alpaca as the single authoritative data source.
Daily cycle: fetch daily bars from Alpaca, compute 50-day SMA, place paper orders if signal.
"""

import os
import sys
import json
import time
import logging
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.data_fetcher import DataFetcher
from core.attribution_logger import log_trade

# Alpaca
from alpaca_trade_api import REST, TimeFrame, TimeFrameUnit

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load env
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env')
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

API_KEY = os.environ.get('ALPACA_API_KEY')
SECRET_KEY = os.environ.get('ALPACA_SECRET_KEY')

class PaperDaemon:
    def __init__(self):
        self.api = REST(API_KEY, SECRET_KEY, 'https://paper-api.alpaca.markets', api_version='v2')
        self.fetcher = DataFetcher(paper=True)
        self.equity = 10000.0
        self.max_order = 100.0
        self.assets = ['BTCUSD', 'ETHUSD']
        self.state_file = 'data/daemon_state.json'
        self.price_tolerance = 0.02  # 2% max difference (legacy, now same source)
        os.makedirs('data', exist_ok=True)
        
    def load_state(self):
        if os.path.exists(self.state_file):
            with open(self.state_file) as f:
                return json.load(f)
        return {'positions': {}, 'last_check': None}
    
    def save_state(self, state):
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2)
    
    def get_50sma(self, bars):
        closes = [b['close'] for b in bars]
        if len(closes) < 50:
            return None
        return sum(closes[-50:]) / 50
    
    def validate_price(self, yahoo_price, alpaca_price, asset):
        """Validate Alpaca price matches Yahoo within tolerance."""
        if alpaca_price is None or yahoo_price is None:
            logger.warning(f"{asset}: Missing price data (Yahoo: {yahoo_price}, Alpaca: {alpaca_price})")
            return False, "missing_data"
        
        diff_pct = abs(alpaca_price - yahoo_price) / yahoo_price
        
        if diff_pct > self.price_tolerance:
            logger.warning(f"🚨 PRICE MISMATCH: {asset}")
            logger.warning(f"   Yahoo: ${yahoo_price:.2f}, Alpaca: ${alpaca_price:.2f} ({diff_pct*100:.2f}% diff)")
            return False, f"price_mismatch_{diff_pct*100:.2f}pct"
        
        logger.info(f"✅ Price validated: {diff_pct*100:.2f}% diff (within {self.price_tolerance*100}%)")
        return True, "ok"
    
    def check_signals(self):
        """Check for SMA cross signals using Alpaca daily data as authoritative source."""
        signals = []
        
        for asset in self.assets:
            alpaca_symbol = asset[:3] + '/' + asset[3:]
            
            # Fetch daily bars from Alpaca (single authoritative source)
            end = datetime.now(timezone.utc)
            start = end - timedelta(days=80)
            bars_raw = self.fetcher.fetch_bars(
                asset, timeframe="1Day", start=start, end=end, limit=100
            )
            
            if len(bars_raw) < 51:
                logger.warning(f"{asset}: insufficient data ({len(bars_raw)} bars)")
                continue
            
            # Sort by timestamp
            bars_raw.sort(key=lambda b: b['timestamp'])
            
            # Remove current day if incomplete
            today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
            bars = [b for b in bars_raw if b['timestamp'][:10] != today]
            
            if len(bars) < 51:
                logger.warning(f"{asset}: insufficient completed bars ({len(bars)} bars)")
                continue
            
            closes = [b['close'] for b in bars]
            current_price = closes[-1]
            prev_price = closes[-2]
            
            # Compute SMA50
            sma50 = sum(closes[-50:]) / 50
            prev_sma50 = sum(closes[-51:-1]) / 50
            
            logger.info(f"{asset}: Price ${current_price:,.2f}, SMA50 ${sma50:,.2f}, Prev SMA50 ${prev_sma50:,.2f}")
            
            # Check crossover
            if current_price > sma50 and prev_price <= prev_sma50:
                signals.append({
                    'asset': asset,
                    'side': 'buy',
                    'price': current_price,
                    'sma50': sma50,
                    'reason': 'sma50_cross_long'
                })
                logger.info(f"{asset}: LONG signal — Price ${current_price:.2f}, SMA50 ${sma50:.2f}")
            elif current_price < sma50 and prev_price >= prev_sma50:
                signals.append({
                    'asset': asset,
                    'side': 'sell',
                    'price': current_price,
                    'sma50': sma50,
                    'reason': 'sma50_cross_short'
                })
                logger.info(f"{asset}: SHORT signal — Price ${current_price:.2f}, SMA50 ${sma50:.2f}")
            else:
                logger.info(f"{asset}: No signal — Price ${current_price:.2f}, SMA50 ${sma50:.2f}")
        
        return signals
    
    def place_paper_order(self, signal):
        """Place paper order on Alpaca."""
        symbol = signal['asset']
        side = signal['side']
        price = signal['price']  # Use Alpaca price (single source)
        
        # Calculate qty for $100 max order
        qty = self.max_order / price
        qty = round(qty, 6)
        
        if qty <= 0:
            logger.warning(f"{symbol}: calculated qty {qty} <= 0, skipping")
            return
        
        # Alpaca crypto uses BTC/USD (with slash)
        alpaca_symbol = symbol[:3] + '/' + symbol[3:]
        
        try:
            order = self.api.submit_order(
                symbol=alpaca_symbol,
                qty=qty,
                side=side,
                type='market',
                time_in_force='gtc'
            )
            logger.info(f"✅ ORDER PLACED: {side} {qty} {alpaca_symbol} @ ~${price:.2f}")
            
            # Log trade with attribution
            log_trade(
                asset=symbol, side=side,
                signal_time=datetime.now(timezone.utc).isoformat(),
                expected_price=price,
                actual_fill_price=price,
                qty=qty,
                fees=0.0,  # Will be updated on fill
                regime_state={
                    "sma50_distance_pct": abs(signal['price'] - signal['sma50']) / signal['sma50'] * 100,
                    "trend_strength": "unknown",
                    "volatility_regime": "unknown",
                }
            )
            
            return order
        except Exception as e:
            logger.error(f"❌ Order failed: {e}")
            return None
    
    def run_cycle(self):
        """Run one trading cycle."""
        logger.info("=" * 60)
        logger.info(f"🤖 Trend Rider v5.6 — Paper Trading Cycle v1.1")
        logger.info(f"Time: {datetime.now(timezone.utc).isoformat()}")
        logger.info("=" * 60)
        
        # Check existing positions
        try:
            positions = self.api.list_positions()
            logger.info(f"Current positions: {len(positions)}")
            for p in positions:
                logger.info(f"  {p.symbol}: {p.qty} @ avg ${p.avg_entry_price}")
        except Exception as e:
            logger.error(f"Error checking positions: {e}")
            positions = []
        
        # Check signals
        signals = self.check_signals()
        
        if not signals:
            logger.info("No valid signals today.")
            return
        
        # Execute signals (max 2 positions)
        if len(positions) >= 2:
            logger.info("Max positions reached (2), skipping new signals")
            return
        
        for signal in signals:
            self.place_paper_order(signal)
    
    def run(self):
        """Main daemon loop."""
        logger.info("=" * 60)
        logger.info("🏁 Trend Rider v5.6 Paper Daemon v2.0 STARTED")
        logger.info("Features: Single-source Alpaca data for backtest + live")
        logger.info("=" * 60)
        
        while True:
            try:
                self.run_cycle()
            except Exception as e:
                logger.error(f"Cycle error: {e}", exc_info=True)
            
            # Sleep until next day (check once per day for daily strategy)
            now = datetime.now(timezone.utc)
            next_run = (now + timedelta(days=1)).replace(hour=0, minute=5, second=0, microsecond=0)
            sleep_seconds = (next_run - now).total_seconds()
            
            logger.info(f"Sleeping until {next_run.isoformat()} ({sleep_seconds/3600:.1f} hours)")
            time.sleep(sleep_seconds)


if __name__ == '__main__':
    daemon = PaperDaemon()
    daemon.run_cycle()  # Run once for testing
