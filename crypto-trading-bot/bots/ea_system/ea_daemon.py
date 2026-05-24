"""
EA System — 15m Day Trading Daemon
Two modes: scan (entry signals) and monitor (position management)
Multi-strategy: EMA+RSI, Bollinger, RSI Scalp, VWAP
All strategies LONG ONLY (Alpaca crypto does not support shorts)
Attribution: each trade tagged with strategy name for performance tracking
BUG-FIXED: strategy tagging, symbol normalization, live price, file paths
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime, timezone, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(BASE_DIR))

from alpaca_trade_api import REST
from indicators import ema, rsi
from strategy_ema_rsi import EmaRsiStrategy
from strategy_bollinger import BollingerStrategy
from strategy_rsi_scalp import RsiScalpStrategy
from strategy_vwap import VwapStrategy

# ─── Load env ───────────────────────────────────────────────────────────────
env_path = os.path.join(BASE_DIR, '..', '..', '.env')
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

# Alpaca SDK v2 uses APCA_API_KEY_ID
os.environ['APCA_API_KEY_ID'] = os.environ.get('ALPACA_API_KEY', '')
os.environ['APCA_API_SECRET_KEY'] = os.environ.get('ALPACA_SECRET_KEY', '')

API_KEY = os.environ.get('ALPACA_API_KEY', '')
SECRET_KEY = os.environ.get('ALPACA_SECRET_KEY', '')

# ─── Logging ────────────────────────────────────────────────────────────────
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
os.makedirs(LOGS_DIR, exist_ok=True)

log_file = os.path.join(LOGS_DIR, 'ea_daemon.log')
handler = logging.FileHandler(log_file, mode='a')
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[handler, logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# ─── Config ──────────────────────────────────────────────────────────────────
MAX_POSITION_USD = 100.0
MAX_OPEN_TRADES = 3
MAX_TRADES_PER_DAY = 20
DAILY_LOSS_CAP = 0.03
COOLDOWN_MINUTES = 30
ASSETS = ['BTCUSD', 'ETHUSD']

LOGS_DIR = os.path.join(BASE_DIR, 'logs')
OPEN_TRADES_FILE = os.path.join(BASE_DIR, 'open_trades.json')
CLOSED_TRADES_FILE = os.path.join(BASE_DIR, 'closed_trades.json')
HEARTBEAT_FILE = os.path.join(LOGS_DIR, 'ea_heartbeat.json')
COOLDOWN_FILE = os.path.join(LOGS_DIR, 'ea_cooldown.json')

STRATEGY_PRIORITY = ['rsi_scalp', 'bollinger', 'vwap', 'ema_rsi']

from utils import normalize_symbol, to_alpaca_symbol

# normalize_symbol: BTC/USD -> BTCUSD (for internal storage)
# to_alpaca_symbol: BTCUSD -> BTC/USD (for Alpaca API calls)


class EADaemon:
    def __init__(self):
        self.api = REST(API_KEY, SECRET_KEY, 'https://paper-api.alpaca.markets', api_version='v2')
        self.strategies = {
            'ema_rsi': EmaRsiStrategy(),
            'bollinger': BollingerStrategy(),
            'rsi_scalp': RsiScalpStrategy(),
            'vwap': VwapStrategy(),
        }
        os.makedirs(LOGS_DIR, exist_ok=True)
        logger.info(f"LOGS_DIR: {LOGS_DIR}")
        logger.info(f"OPEN_TRADES_FILE: {OPEN_TRADES_FILE}")
        logger.info(f"CLOSED_TRADES_FILE: {CLOSED_TRADES_FILE}")

    # ─── File I/O ──────────────────────────────────────────────────────────────

    def _load_json(self, filepath):
        if not os.path.exists(filepath):
            return {"trades": []}
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, Exception):
            return {"trades": []}

    def _save_json(self, filepath, data):
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

    # ─── Open Trades (Strategy Tagging) ────────────────────────────────────────

    def add_open_trade(self, trade):
        """Add a new open trade. MUST succeed before order is placed."""
        data = self._load_json(OPEN_TRADES_FILE)
        data['trades'].append(trade)
        self._save_json(OPEN_TRADES_FILE, data)
        logger.info(f"📝 Trade logged: {trade['id']} ({trade['pair']}) via {trade['strategy']}")

    def remove_open_trade(self, trade_id):
        """Remove trade from open_trades (called on exit)."""
        data = self._load_json(OPEN_TRADES_FILE)
        data['trades'] = [t for t in data['trades'] if t['id'] != trade_id]
        self._save_json(OPEN_TRADES_FILE, data)

    def get_open_trade(self, symbol):
        """Find the most recent OPEN trade for this symbol."""
        data = self._load_json(OPEN_TRADES_FILE)
        for t in reversed(data['trades']):
            if t.get('status') == 'OPEN' and t.get('pair') == symbol:
                return t
        return None

    def add_closed_trade(self, trade):
        """Move trade to closed_trades.json with exit details."""
        data = self._load_json(CLOSED_TRADES_FILE)
        data['trades'].append(trade)
        self._save_json(CLOSED_TRADES_FILE, data)

    # ─── Heartbeat ───────────────────────────────────────────────────────────────

    def write_heartbeat(self, status, details=None, error=None):
        hb = {
            'last_check_utc': datetime.now(timezone.utc).isoformat(),
            'status': status,
            'details': details or {},
            'error': str(error) if error else None,
        }
        self._save_json(HEARTBEAT_FILE, hb)

    # ─── Cooldown ──────────────────────────────────────────────────────────────

    def get_cooldowns(self):
        return self._load_json(COOLDOWN_FILE)

    def set_cooldown(self, symbol):
        data = self.get_cooldowns()
        data[symbol] = (datetime.now(timezone.utc) + timedelta(minutes=COOLDOWN_MINUTES)).isoformat()
        self._save_json(COOLDOWN_FILE, data)

    def is_on_cooldown(self, symbol):
        data = self.get_cooldowns()
        key = symbol
        if key not in data:
            return False
        end_time = datetime.fromisoformat(data[key])
        if datetime.now(timezone.utc) >= end_time:
            return False
        remaining = (end_time - datetime.now(timezone.utc)).total_seconds() / 60
        logger.info(f"⏳ {key} on cooldown: {remaining:.0f} min remaining")
        return True

    # ─── Risk Governor ───────────────────────────────────────────────────────────

    def get_today_trade_count(self):
        today_utc = datetime.now(timezone.utc).date()
        count = 0
        data = self._load_json(OPEN_TRADES_FILE)
        for t in data['trades']:
            try:
                trade_time = datetime.fromisoformat(t['entry_time'].replace('Z', '+00:00'))
                if trade_time.date() == today_utc:
                    count += 1
            except:
                pass
        closed = self._load_json(CLOSED_TRADES_FILE)
        for t in closed['trades']:
            try:
                trade_time = datetime.fromisoformat(t['entry_time'].replace('Z', '+00:00'))
                if trade_time.date() == today_utc:
                    count += 1
            except:
                pass
        return count

    def risk_check(self, positions):
        if len(positions) >= MAX_OPEN_TRADES:
            return False, "Max open trades reached"
        today_count = self.get_today_trade_count()
        if today_count >= MAX_TRADES_PER_DAY:
            return False, f"Max daily trades: {today_count}/{MAX_TRADES_PER_DAY}"
        try:
            account = self.api.get_account()
            equity = float(account.equity)
            last_equity = float(account.last_equity)
            daily_pnl_pct = (equity - last_equity) / last_equity
            if daily_pnl_pct <= -DAILY_LOSS_CAP:
                return False, f"Daily loss cap: {daily_pnl_pct:.2%}"
        except Exception as e:
            logger.warning(f"Could not check daily P&L: {e}")
        return True, "OK"

    # ─── Data ────────────────────────────────────────────────────────────────────

    def fetch_bars(self, symbol, timeframe='15Min', limit=100):
        # Alpaca bar API needs BTC/USD format
        api_symbol = to_alpaca_symbol(symbol)
        end = datetime.now(timezone.utc)
        start = end - timedelta(hours=48)
        try:
            bars = self.api.get_crypto_bars(
                api_symbol, timeframe=timeframe,
                start=start.isoformat(), end=end.isoformat(), limit=limit
            ).df
            if bars.empty:
                return []
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
        try:
            positions = self.api.list_positions()
            return [{
                'symbol': normalize_symbol(p.symbol),  # BTCUSD -> BTCUSD (identity)
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
        # symbol is already BTCUSD (no slash) — used directly for Alpaca orders
        try:
            order = self.api.submit_order(
                symbol=symbol, qty=qty, side=side, type=order_type, time_in_force='gtc'
            )
            logger.info(f"✅ ORDER PLACED: {side} {qty} {symbol}")
            return order
        except Exception as e:
            logger.error(f"❌ Order failed: {e}")
            return None

    # ─── Scan ───────────────────────────────────────────────────────────────────

    def scan(self):
        logger.info("=" * 60)
        logger.info("🔍 EA SCAN — 15m Multi-Strategy Entry Check")
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
        strategy_results = {}

        for symbol in ASSETS:
            strategy_results[symbol] = {}
            if symbol in active_symbols:
                logger.info(f"{symbol}: Already have position — skipping")
                strategy_results[symbol] = {'status': 'HAS_POSITION'}
                continue

            if self.is_on_cooldown(symbol):
                strategy_results[symbol] = {'status': 'COOLDOWN'}
                continue

            bars = self.fetch_bars(symbol)
            if not bars:
                logger.warning(f"{symbol}: No bars fetched")
                strategy_results[symbol] = {'status': 'NO_BARS'}
                continue

            # Check all strategies by priority
            signal_found = False
            for strategy_name in STRATEGY_PRIORITY:
                strategy = self.strategies[strategy_name]
                signal = strategy.check_entry(bars)
                if signal:
                    strategy_results[symbol][strategy_name] = 'SIGNAL'
                    logger.info(f"🚀 {symbol}: SIGNAL ({strategy_name}) — {signal['reason']}")
                    for k, v in signal.items():
                        if k not in ('signal', 'reason'):
                            logger.info(f"   {k}: {v:.2f}" if isinstance(v, float) else f"   {k}: {v}")

                    qty = MAX_POSITION_USD / signal['price']
                    qty = round(qty, 6)
                    if qty <= 0:
                        logger.warning(f"{symbol}: qty {qty} <= 0, skipping")
                        continue

                    # CRITICAL: Write trade metadata BEFORE placing order
                    trade_id = f"trade_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
                    trade_meta = {
                        'id': trade_id,
                        'pair': symbol,
                        'strategy': strategy_name,
                        'direction': 'LONG',
                        'entry_price': round(signal['price'], 2),
                        'entry_time': datetime.now(timezone.utc).isoformat(),
                        'size_usd': MAX_POSITION_USD,
                        'qty': qty,
                        'status': 'OPEN',
                    }
                    self.add_open_trade(trade_meta)

                    order = self.place_order(symbol, 'buy', qty)
                    if order:
                        scan_results.append({
                            'symbol': symbol,
                            'side': 'buy',
                            'qty': qty,
                            'price': signal['price'],
                            'reason': signal['reason'],
                            'strategy': strategy_name,
                            'trade_id': trade_id,
                        })
                    else:
                        # Order failed — remove from open trades
                        self.remove_open_trade(trade_id)
                        logger.error(f"❌ Order failed for {symbol}, trade {trade_id} removed from open_trades")

                    signal_found = True
                    break
                else:
                    strategy_results[symbol][strategy_name] = 'NO_SIGNAL'

            if not signal_found:
                closes = [b['close'] for b in bars]
                ema8_vals = ema(closes, 8)
                ema21_vals = ema(closes, 21)
                rsi_vals = rsi(closes, 14)
                if ema8_vals and ema21_vals and rsi_vals:
                    logger.info(
                        f"{symbol}: No signal — "
                        f"EMA8 ${ema8_vals[-1]:.2f} vs EMA21 ${ema21_vals[-1]:.2f}, "
                        f"RSI {rsi_vals[-1]:.1f}"
                    )

        status = 'SIGNAL_FIRED' if scan_results else 'NO_SIGNAL'
        self.write_heartbeat(status, {
            'mode': 'scan',
            'positions': len(positions),
            'trades': scan_results,
            'strategy_results': strategy_results,
        })

    # ─── Monitor ─────────────────────────────────────────────────────────────────

    def monitor(self):
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
            symbol = pos['symbol']  # Already normalized to BTC/USD
            entry_price = pos['avg_entry_price']
            current_price = pos['current_price']  # LIVE price from Alpaca
            qty = pos['qty']
            pnl_pct = pos['unrealized_plpc']

            logger.info(
                f"{symbol}: Qty {qty:.6f}, Entry ${entry_price:.2f}, "
                f"Current ${current_price:.2f}, P&L {pnl_pct:.2%}"
            )

            # 1. UNIVERSAL HARD STOP — uses LIVE price (no bars needed)
            if pnl_pct <= -0.02:
                logger.info(f"🚨 {symbol}: EXIT (universal hard stop) — P&L {pnl_pct:.2%}")
                order = self.place_order(symbol, 'sell', qty)
                if order:
                    trade_info = self.get_open_trade(symbol)
                    if trade_info:
                        trade_info['status'] = 'CLOSED'
                        trade_info['exit_price'] = round(current_price, 2)
                        trade_info['exit_time'] = datetime.now(timezone.utc).isoformat()
                        trade_info['exit_reason'] = 'universal_hard_stop_2pct'
                        trade_info['pnl_pct'] = round(pnl_pct, 4)
                        trade_info['pnl_usd'] = round(pnl_pct * trade_info['size_usd'], 2)
                        self.add_closed_trade(trade_info)
                        self.remove_open_trade(trade_info['id'])

                    exits.append({
                        'symbol': symbol, 'side': 'sell', 'qty': qty,
                        'price': current_price, 'pnl_pct': pnl_pct,
                        'reason': 'universal_hard_stop_2pct', 'strategy': 'universal'
                    })
                    self.set_cooldown(symbol)
                continue

            # 2. STRATEGY-SPECIFIC EXIT — needs bar data for indicators
            trade_info = self.get_open_trade(symbol)
            if not trade_info:
                logger.warning(f"🚨 {symbol}: ALERT — No strategy attribution in open_trades.json. Skipping strategy exit.")
                logger.info(f"{symbol}: HOLD (no attribution) — P&L {pnl_pct:.2%}")
                continue

            strategy_name = trade_info.get('strategy')
            if strategy_name not in self.strategies:
                logger.warning(f"🚨 {symbol}: ALERT — Unknown strategy '{strategy_name}'. Skipping strategy exit.")
                logger.info(f"{symbol}: HOLD (unknown strategy) — P&L {pnl_pct:.2%}")
                continue

            bars = self.fetch_bars(symbol)
            if not bars:
                logger.warning(f"{symbol}: No bars for strategy exit check — HOLD")
                continue

            strategy = self.strategies[strategy_name]
            exit_signal = strategy.check_exit(bars, entry_price, current_price)
            if exit_signal:
                logger.info(
                    f"🚨 {symbol}: EXIT ({strategy_name}) — "
                    f"{exit_signal['reason']}, P&L {pnl_pct:.2%}"
                )
                order = self.place_order(symbol, 'sell', qty)
                if order:
                    trade_info['status'] = 'CLOSED'
                    trade_info['exit_price'] = round(current_price, 2)
                    trade_info['exit_time'] = datetime.now(timezone.utc).isoformat()
                    trade_info['exit_reason'] = exit_signal['reason']
                    trade_info['pnl_pct'] = round(pnl_pct, 4)
                    trade_info['pnl_usd'] = round(pnl_pct * trade_info['size_usd'], 2)
                    self.add_closed_trade(trade_info)
                    self.remove_open_trade(trade_info['id'])

                    exits.append({
                        'symbol': symbol, 'side': 'sell', 'qty': qty,
                        'price': current_price, 'pnl_pct': pnl_pct,
                        'reason': exit_signal['reason'], 'strategy': strategy_name
                    })
                continue

            logger.info(f"{symbol}: HOLD ({strategy_name}) — P&L {pnl_pct:.2%}")

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
