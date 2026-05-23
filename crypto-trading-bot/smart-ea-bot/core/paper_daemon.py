"""
Smart EA Bot Company — Paper Trading Daemon v3.0 (Hardened)
Runs Trend Rider v5.6 using Alpaca as the single authoritative data source.
Hardened: heartbeat, retry, duplicate detection, error recovery.
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

# Constants
MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = 60
MAX_ORDER_USD = 100.0
MAX_POSITIONS = 2
HEARTBEAT_FILE = 'logs/daemon_heartbeat.json'
STATE_FILE = 'data/daemon_state.json'
MIN_BARS = 51


class PaperDaemon:
    """Hardened paper trading daemon for Trend Rider v5.6."""
    
    def __init__(self):
        self.api = REST(API_KEY, SECRET_KEY, 'https://paper-api.alpaca.markets', api_version='v2')
        self.fetcher = DataFetcher(paper=True)
        self.equity = 10000.0
        self.max_order = MAX_ORDER_USD
        self.assets = ['BTCUSD', 'ETHUSD']
        self.state_file = STATE_FILE
        self.heartbeat_file = HEARTBEAT_FILE
        os.makedirs('data', exist_ok=True)
        os.makedirs('logs', exist_ok=True)
    
    # ──────────────────────────────────────────────────────────────
    # State / Heartbeat
    # ──────────────────────────────────────────────────────────────
    
    def load_state(self):
        if os.path.exists(self.state_file):
            with open(self.state_file) as f:
                return json.load(f)
        return {'positions': {}, 'last_check': None}
    
    def save_state(self, state):
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2)
    
    def write_heartbeat(self, status, details=None, error=None):
        """Write heartbeat file after every check."""
        heartbeat = {
            'last_check_utc': datetime.now(timezone.utc).isoformat(),
            'status': status,  # OK | SIGNAL_FIRED | ERROR | SKIPPED
            'btc_price': details.get('btc_price') if details else None,
            'btc_sma50': details.get('btc_sma50') if details else None,
            'eth_price': details.get('eth_price') if details else None,
            'eth_sma50': details.get('eth_sma50') if details else None,
            'signal': details.get('signal', 'NONE') if details else 'NONE',
            'order_placed': details.get('order_placed', False) if details else False,
            'error_message': str(error) if error else None,
        }
        with open(self.heartbeat_file, 'w') as f:
            json.dump(heartbeat, f, indent=2)
        logger.info(f"💓 Heartbeat written: {status}")
    
    def check_duplicate_run(self):
        """Detect if daemon already ran today. If so, skip."""
        if not os.path.exists(self.heartbeat_file):
            return False
        
        with open(self.heartbeat_file) as f:
            hb = json.load(f)
        
        last_run = hb.get('last_check_utc')
        if not last_run:
            return False
        
        try:
            last_dt = datetime.fromisoformat(last_run.replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            hours_since = (now - last_dt).total_seconds() / 3600
            
            if hours_since < 20:
                logger.warning(f"⚠️ DUPLICATE RUN DETECTED: last run was {hours_since:.1f} hours ago. Skipping.")
                self.write_heartbeat('SKIPPED', details={'signal': 'NONE', 'order_placed': False})
                return True
            elif hours_since > 25:
                logger.warning(f"⚠️ MISSED PREVIOUS CHECK: last run was {hours_since:.1f} hours ago (>25h).")
            
        except Exception as e:
            logger.warning(f"Could not parse last heartbeat: {e}")
        
        return False
    
    # ──────────────────────────────────────────────────────────────
    # Data Fetching (with retry)
    # ──────────────────────────────────────────────────────────────
    
    def fetch_bars_with_retry(self, asset, timeframe='1Day', days_back=80, limit=100):
        """Fetch bars with retry on failure."""
        end = datetime.now(timezone.utc)
        start = end - timedelta(days=days_back)
        
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                bars = self.fetcher.fetch_bars(asset, timeframe=timeframe, start=start, end=end, limit=limit)
                
                if not bars:
                    logger.warning(f"{asset}: Empty data returned (attempt {attempt}/{MAX_RETRIES})")
                    if attempt < MAX_RETRIES:
                        time.sleep(RETRY_BACKOFF_SECONDS)
                        continue
                    return []
                
                if len(bars) < MIN_BARS:
                    logger.warning(f"{asset}: Insufficient bars ({len(bars)} < {MIN_BARS}) (attempt {attempt}/{MAX_RETRIES})")
                    if attempt < MAX_RETRIES:
                        time.sleep(RETRY_BACKOFF_SECONDS)
                        continue
                    return bars
                
                return bars
                
            except Exception as e:
                logger.error(f"{asset}: API failure (attempt {attempt}/{MAX_RETRIES}): {e}")
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_BACKOFF_SECONDS)
                else:
                    logger.error(f"{asset}: All {MAX_RETRIES} retries exhausted. Raising error.")
                    raise  # Re-raise so caller can catch and write ERROR heartbeat
        
        return []
    
    def prepare_bars(self, bars_raw):
        """Sort bars, remove incomplete current day, validate."""
        if not bars_raw:
            return []
        
        # Sort by timestamp
        bars_raw.sort(key=lambda b: b.get('timestamp', ''))
        
        # Remove current day if incomplete (daemon runs shortly after midnight UTC)
        today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        bars = [b for b in bars_raw if b.get('timestamp', '')[:10] != today]
        
        # Validate bar structure
        valid_bars = []
        for b in bars:
            if all(k in b for k in ('timestamp', 'open', 'high', 'low', 'close', 'volume')):
                try:
                    float(b['close'])
                    valid_bars.append(b)
                except (TypeError, ValueError):
                    logger.warning(f"Invalid close price in bar: {b}")
            else:
                logger.warning(f"Malformed bar missing fields: {b}")
        
        return valid_bars
    
    def compute_sma(self, bars, period=50):
        """Compute SMA. Return None if insufficient/invalid data."""
        if len(bars) < period + 1:
            return None, None
        
        try:
            closes = [float(b['close']) for b in bars]
            if any(c != c for c in closes):  # NaN check
                logger.error("NaN detected in close prices")
                return None, None
            
            current_sma = sum(closes[-period:]) / period
            prev_sma = sum(closes[-(period + 1):-1]) / period
            return current_sma, prev_sma
        except Exception as e:
            logger.error(f"SMA computation failed: {e}")
            return None, None
    
    # ──────────────────────────────────────────────────────────────
    # Signal Detection
    # ──────────────────────────────────────────────────────────────
    
    def check_signals(self):
        """Check for SMA cross signals. Hardened: handles all failure modes."""
        signals = []
        details = {
            'btc_price': None,
            'btc_sma50': None,
            'eth_price': None,
            'eth_sma50': None,
            'signal': 'NONE',
            'order_placed': False,
        }
        
        for asset in self.assets:
            # Fetch with retry
            bars_raw = self.fetch_bars_with_retry(asset)
            
            if not bars_raw:
                logger.error(f"{asset}: No data after retries. Skipping.")
                continue
            
            # Prepare and validate
            bars = self.prepare_bars(bars_raw)
            
            if len(bars) < MIN_BARS:
                logger.warning(f"{asset}: Insufficient completed bars ({len(bars)}). Skipping.")
                continue
            
            # Compute SMA
            sma50, prev_sma50 = self.compute_sma(bars)
            if sma50 is None:
                logger.error(f"{asset}: SMA computation failed. Skipping.")
                continue
            
            closes = [float(b['close']) for b in bars]
            current_price = closes[-1]
            prev_price = closes[-2]
            
            # Store for heartbeat
            if asset == 'BTCUSD':
                details['btc_price'] = current_price
                details['btc_sma50'] = sma50
            elif asset == 'ETHUSD':
                details['eth_price'] = current_price
                details['eth_sma50'] = sma50
            
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
                details['signal'] = f"{asset}_LONG"
                logger.info(f"{asset}: LONG signal — Price ${current_price:.2f}, SMA50 ${sma50:.2f}")
            elif current_price < sma50 and prev_price >= prev_sma50:
                signals.append({
                    'asset': asset,
                    'side': 'sell',
                    'price': current_price,
                    'sma50': sma50,
                    'reason': 'sma50_cross_short'
                })
                details['signal'] = f"{asset}_SHORT"
                logger.info(f"{asset}: SHORT signal — Price ${current_price:.2f}, SMA50 ${sma50:.2f}")
            else:
                logger.info(f"{asset}: No signal — Price ${current_price:.2f}, SMA50 ${sma50:.2f}")
        
        return signals, details
    
    # ──────────────────────────────────────────────────────────────
    # Order Execution
    # ──────────────────────────────────────────────────────────────
    
    def place_paper_order(self, signal):
        """Place paper order on Alpaca. Hardened: no retry, no double-fill risk."""
        symbol = signal['asset']
        side = signal['side']
        price = signal['price']
        
        # Validate position size
        qty = self.max_order / price
        qty = round(qty, 6)
        
        if qty <= 0:
            logger.warning(f"{symbol}: calculated qty {qty} <= 0, skipping")
            return None
        
        if qty * price > self.max_order * 1.01:  # 1% tolerance
            logger.warning(f"{symbol}: order value ${qty*price:.2f} exceeds max ${self.max_order}, skipping")
            return None
        
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
            
            log_trade(
                asset=symbol, side=side,
                signal_time=datetime.now(timezone.utc).isoformat(),
                expected_price=price,
                actual_fill_price=price,
                qty=qty,
                fees=0.0,
                regime_state={
                    "sma50_distance_pct": abs(signal['price'] - signal['sma50']) / signal['sma50'] * 100,
                    "trend_strength": "unknown",
                    "volatility_regime": "unknown",
                }
            )
            
            return order
        except Exception as e:
            logger.error(f"❌ Order failed: {e}. NO RETRY attempted (avoid double-fill).")
            return None
    
    # ──────────────────────────────────────────────────────────────
    # Main Cycle
    # ──────────────────────────────────────────────────────────────
    
    def run_cycle(self):
        """Run one hardened trading cycle."""
        logger.info("=" * 60)
        logger.info(f"🤖 Trend Rider v5.6 — Paper Trading Cycle v3.0")
        logger.info(f"Time: {datetime.now(timezone.utc).isoformat()}")
        logger.info("=" * 60)
        
        # Check for duplicate run
        if self.check_duplicate_run():
            return
        
        # Check existing positions
        positions = []
        try:
            positions = self.api.list_positions()
            logger.info(f"Current positions: {len(positions)}")
            for p in positions:
                logger.info(f"  {p.symbol}: {p.qty} @ avg ${p.avg_entry_price}")
        except Exception as e:
            logger.error(f"Error checking positions: {e}")
            positions = []
        
        # Check signals (hardened)
        try:
            signals, details = self.check_signals()
        except Exception as e:
            logger.error(f"Signal check failed: {e}")
            self.write_heartbeat('ERROR', error=e)
            return
        
        if not signals:
            logger.info("No valid signals today.")
            self.write_heartbeat('OK', details=details)
            return
        
        # Check max positions
        if len(positions) >= MAX_POSITIONS:
            logger.info(f"Max positions reached ({MAX_POSITIONS}), skipping new signals")
            self.write_heartbeat('OK', details=details)
            return
        
        # Execute signals
        orders_placed = 0
        for signal in signals:
            order = self.place_paper_order(signal)
            if order:
                orders_placed += 1
                details['order_placed'] = True
        
        if orders_placed > 0:
            self.write_heartbeat('SIGNAL_FIRED', details=details)
        else:
            self.write_heartbeat('OK', details=details)
    
    def run(self):
        """Main daemon loop."""
        logger.info("=" * 60)
        logger.info("🏁 Trend Rider v5.6 Paper Daemon v3.0 STARTED")
        logger.info("Features: Single-source Alpaca, heartbeat, retry, duplicate detection")
        logger.info("=" * 60)
        
        while True:
            try:
                self.run_cycle()
            except Exception as e:
                logger.critical(f"🔥 UNHANDLED CYCLE ERROR: {e}", exc_info=True)
                self.write_heartbeat('ERROR', error=e)
            
            # Sleep until next day
            now = datetime.now(timezone.utc)
            next_run = (now + timedelta(days=1)).replace(hour=0, minute=5, second=0, microsecond=0)
            sleep_seconds = (next_run - now).total_seconds()
            
            logger.info(f"Sleeping until {next_run.isoformat()} ({sleep_seconds/3600:.1f} hours)")
            time.sleep(sleep_seconds)


if __name__ == '__main__':
    daemon = PaperDaemon()
    daemon.run_cycle()  # Run once for testing
