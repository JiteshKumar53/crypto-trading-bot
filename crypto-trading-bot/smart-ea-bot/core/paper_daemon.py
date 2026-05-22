"""
Smart EA Bot Company — Paper Trading Daemon
Runs Trend Rider v5.6 on Alpaca paper trading.
Daily cycle: check 50-day SMA, place paper orders if signal.
"""

import os
import sys
import json
import time
import logging
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.yahoo_data_fetcher import fetch_yahoo_bars
from bots.trend_rider_v5_6.strategy import trend_rider_v5_6_strategy

# Alpaca
from alpaca_trade_api import REST

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
        self.equity = 10000.0
        self.max_order = 100.0
        self.assets = ['BTCUSD', 'ETHUSD']
        self.state_file = 'data/daemon_state.json'
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
    
    def check_signals(self):
        """Check for SMA cross signals."""
        signals = []
        
        for asset in self.assets:
            # Fetch last 60 days daily
            bars = fetch_yahoo_bars(asset, interval='1d', period='3mo')
            if len(bars) < 51:
                logger.warning(f"{asset}: insufficient data ({len(bars)} bars)")
                continue
            
            current_price = bars[-1]['close']
            prev_price = bars[-2]['close']
            sma50 = self.get_50sma(bars[:-1])  # SMA up to yesterday
            prev_sma50 = self.get_50sma(bars[:-2]) if len(bars) > 52 else sma50
            
            if sma50 is None:
                continue
            
            # Check crossover
            if current_price > sma50 and prev_price <= prev_sma50:
                signals.append({
                    'asset': asset,
                    'side': 'buy',
                    'price': current_price,
                    'sma50': sma50,
                    'reason': 'sma50_cross_long'
                })
                logger.info(f"{asset}: LONG signal — price {current_price:.2f} crossed above SMA50 {sma50:.2f}")
            elif current_price < sma50 and prev_price >= prev_sma50:
                signals.append({
                    'asset': asset,
                    'side': 'sell',
                    'price': current_price,
                    'sma50': sma50,
                    'reason': 'sma50_cross_short'
                })
                logger.info(f"{asset}: SHORT signal — price {current_price:.2f} crossed below SMA50 {sma50:.2f}")
            else:
                logger.info(f"{asset}: No signal — price {current_price:.2f}, SMA50 {sma50:.2f}")
        
        return signals
    
    def place_paper_order(self, signal):
        """Place paper order on Alpaca."""
        symbol = signal['asset']
        side = signal['side']
        price = signal['price']
        
        # Calculate qty for $100 max order
        qty = self.max_order / price
        qty = round(qty, 6)
        
        if qty <= 0:
            logger.warning(f"{symbol}: calculated qty {qty} <= 0, skipping")
            return
        
        # Alpaca uses BTCUSD not BTC/USD
        alpaca_symbol = symbol.replace('/', '')
        
        try:
            order = self.api.submit_order(
                symbol=alpaca_symbol,
                qty=qty,
                side=side,
                type='market',
                time_in_force='gtc'
            )
            logger.info(f"✅ ORDER PLACED: {side} {qty} {alpaca_symbol} @ ~${price:.2f}")
            return order
        except Exception as e:
            logger.error(f"❌ Order failed: {e}")
            return None
    
    def run_cycle(self):
        """Run one trading cycle."""
        logger.info("=" * 60)
        logger.info(f"🤖 Trend Rider v5.6 — Paper Trading Cycle")
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
            logger.info("No signals today.")
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
        logger.info("🏁 Trend Rider v5.6 Paper Daemon STARTED")
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
