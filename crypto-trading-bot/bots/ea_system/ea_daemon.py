"""
EA System — 15m Day Trading Daemon
Two modes: scan (entry signals) and monitor (position management)
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from alpaca_trade_api import REST
from indicators import ema, rsi, get_last_crossover
from strategy_ema_rsi import EmaRsiStrategy

# Load env
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env')
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

API_KEY = os.environ.get('ALPACA_API_KEY', '')
SECRET_KEY = os.environ.get('ALPACA_SECRET_KEY', '')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

MAX_POSITION_USD = 100.0
MAX_OPEN_TRADES = 3
DAILY_LOSS_CAP = 0.03  # 3%
ASSETS = ['BTC/USD', 'ETH/USD']
HEARTBEAT_FILE = 'bots/ea_system/logs/ea_heartbeat.json'


class EADaemon:
    def __init__(self):
        self.api = REST(API_KEY, SECRET_KEY, 'https://paper-api.alpaca.markets', api_version='v2')
        self.strategy = EmaRsiStrategy()
        os.makedirs('bots/ea_system/logs', exist_ok=True)
    
    def write_heartbeat(self, status, details=None, error=None):
        hb = {
            'last_check_utc': datetime.now(timezone.utc).isoformat(),
            'status': status,
            'details': details or {},
            'error': str(error) if error else None,
        }
        with open(HEARTBEAT_FILE, 'w') as f:
            json.dump(hb, f, indent=2)
    
    def fetch_bars(self, symbol, timeframe='15Min', limit=100):
        """Fetch latest bars from Alpaca."""
        end = datetime.now(timezone.utc)
        start = end - timedelta(hours=48)  # 48h of 15m bars = 192 bars
        
        try:
            bars = self.api.get_crypto_bars(
                symbol, timeframe=timeframe,
                start=start.isoformat(), end=end.isoformat(), limit=limit
            ).df
            
            if bars.empty:
                return []
            
            # Convert to list of dicts
            result = []
            for idx, row in bars.iterrows():
                result.append({
                    'timestamp': idx.isoformat() if hasattr(idx, 'isoformat') else str(idx),
                    'open': float(row['open']),
                    'high': float(row['high']),
                    'low': float(row['low']),
                    'close': float(row['close']),
                    'volume': float(row['volume']),
                })
            return result
        except Exception as e:
            logger.error(f"Error fetching bars for {symbol}: {e}")
            return []
    
    def get_open_positions(self):
        """Get current open positions."""
        try:
            positions = self.api.list_positions()
            return [{
                'symbol': p.symbol,
                'qty': float(p.qty),
                'avg_entry_price': float(p.avg_entry_price),
                'current_price': float(p.current_price),
                'unrealized_pl': float(p.unrealized_pl),
                'unrealized_plpc': float(p.unrealized_plpc),
            } for p in positions]
        except Exception as e:
            logger.error(f"Error listing positions: {e}")
            return []
    
    def place_order(self, symbol, side, qty, order_type='market'):
        """Place order on Alpaca paper."""
        try:
            order = self.api.submit_order(
                symbol=symbol,
                qty=qty,
                side=side,
                type=order_type,
                time_in_force='gtc'
            )
            logger.info(f"✅ ORDER PLACED: {side} {qty} {symbol}")
            return order
        except Exception as e:
            logger.error(f"❌ Order failed: {e}")
            return None
    
    def risk_check(self, positions):
        """Check if we can open new positions."""
        if len(positions) >= MAX_OPEN_TRADES:
            return False, "Max open trades reached"
        
        # Check daily P&L
        try:
            account = self.api.get_account()
            equity = float(account.equity)
            last_equity = float(account.last_equity)
            daily_pnl_pct = (equity - last_equity) / last_equity
            
            if daily_pnl_pct <= -DAILY_LOSS_CAP:
                return False, f"Daily loss cap hit: {daily_pnl_pct:.2%}"
        except Exception as e:
            logger.warning(f"Could not check daily P&L: {e}")
        
        return True, "OK"
    
    def scan(self):
        """Scan for entry signals."""
        logger.info("=" * 60)
        logger.info("🔍 EA SCAN — 15m Entry Signal Check")
        logger.info(f"Time: {datetime.now(timezone.utc).isoformat()}")
        logger.info("=" * 60)
        
        positions = self.get_open_positions()
        can_trade, reason = self.risk_check(positions)
        
        if not can_trade:
            logger.warning(f"⛔ Risk check failed: {reason}")
            self.write_heartbeat('RISK_BLOCKED', {'reason': reason})
            return
        
        active_symbols = {p['symbol'] for p in positions}
        scan_results = []
        
        for symbol in ASSETS:
            # Skip if already have position
            if symbol in active_symbols:
                logger.info(f"{symbol}: Already have position, skipping")
                continue
            
            # Fetch bars
            bars = self.fetch_bars(symbol)
            if not bars:
                logger.warning(f"{symbol}: No bars fetched")
                continue
            
            # Check signal
            signal = self.strategy.check_entry(bars)
            
            if signal:
                logger.info(f"🚀 {symbol}: SIGNAL — {signal['reason']}")
                logger.info(f"   Price: ${signal['price']:.2f}, EMA8: ${signal['ema_fast']:.2f}, EMA21: ${signal['ema_slow']:.2f}, RSI: {signal['rsi']:.1f}")
                
                # Calculate qty
                qty = MAX_POSITION_USD / signal['price']
                qty = round(qty, 6)
                
                if qty <= 0:
                    logger.warning(f"{symbol}: qty {qty} <= 0, skipping")
                    continue
                
                # Place order
                order = self.place_order(symbol, 'buy', qty)
                if order:
                    scan_results.append({
                        'symbol': symbol,
                        'side': 'buy',
                        'qty': qty,
                        'price': signal['price'],
                        'reason': signal['reason'],
                    })
            else:
                # Log current indicator values even if no signal
                closes = [b['close'] for b in bars]
                ema8 = ema(closes, 8)
                ema21 = ema(closes, 21)
                rsi_vals = rsi(closes, 14)
                if ema8 and ema21 and rsi_vals:
                    logger.info(f"{symbol}: No signal — EMA8 ${ema8[-1]:.2f} vs EMA21 ${ema21[-1]:.2f}, RSI {rsi_vals[-1]:.1f}")
        
        status = 'SIGNAL_FIRED' if scan_results else 'NO_SIGNAL'
        self.write_heartbeat(status, {
            'mode': 'scan',
            'positions': len(positions),
            'trades': scan_results,
        })
    
    def monitor(self):
        """Monitor open positions and manage exits."""
        logger.info("=" * 60)
        logger.info("👁️ EA MONITOR — Position Check")
        logger.info(f"Time: {datetime.now(timezone.utc).isoformat()}")
        logger.info("=" * 60)
        
        positions = self.get_open_positions()
        
        if not positions:
            logger.info("No open positions.")
            self.write_heartbeat('NO_POSITIONS', {'mode': 'monitor'})
            return
        
        exits = []
        for pos in positions:
            symbol = pos['symbol']
            entry_price = pos['avg_entry_price']
            current_price = pos['current_price']
            qty = pos['qty']
            pnl_pct = pos['unrealized_plpc']
            
            logger.info(f"{symbol}: Qty {qty}, Entry ${entry_price:.2f}, Current ${current_price:.2f}, P&L {pnl_pct:.2%}")
            
            # Fetch recent bars for exit check
            bars = self.fetch_bars(symbol)
            if not bars:
                continue
            
            # Check exit signal
            exit_signal = self.strategy.check_exit(bars, entry_price)
            
            if exit_signal:
                logger.info(f"🚨 {symbol}: EXIT — {exit_signal['reason']}, P&L {pnl_pct:.2%}")
                order = self.place_order(symbol, 'sell', qty)
                if order:
                    exits.append({
                        'symbol': symbol,
                        'side': 'sell',
                        'qty': qty,
                        'price': current_price,
                        'pnl_pct': pnl_pct,
                        'reason': exit_signal['reason'],
                    })
            else:
                logger.info(f"{symbol}: HOLD — P&L {pnl_pct:.2%}")
        
        status = 'EXITS_PLACED' if exits else 'HOLDING'
        self.write_heartbeat(status, {
            'mode': 'monitor',
            'positions': len(positions),
            'exits': exits,
        })


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['scan', 'monitor'], required=True)
    args = parser.parse_args()
    
    daemon = EADaemon()
    
    try:
        if args.mode == 'scan':
            daemon.scan()
        else:
            daemon.monitor()
    except Exception as e:
        logger.critical(f"🔥 UNHANDLED ERROR: {e}", exc_info=True)
        daemon.write_heartbeat('ERROR', error=e)
