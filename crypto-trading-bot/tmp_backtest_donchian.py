"""
Quick Backtest Runner for Strategy Validation
Jarvis - Autonomous Backtesting
"""

import sys
sys.path.insert(0, '/data/.openclaw/workspace/crypto-trading-bot/src')

import logging
logging.basicConfig(level=logging.INFO)

from data.data_fetcher import DataFetcher
from strategies.donchian_channel_strategy import DonchianChannelStrategy
from backtest.backtest_engine import BacktestEngine

# Fetch data
fetcher = DataFetcher()
symbols = ["BTC/USD", "ETH/USD", "SOL/USD"]
results = {}

for symbol in symbols:
    print(f"\n{'='*60}")
    print(f"BACKTEST: Donchian Channel Breakout on {symbol}")
    print(f"{'='*60}")
    
    # Fetch 2000 hours of data for backtesting
    df = fetcher.fetch_hourly_bars(symbol, limit=2000)
    if df is None:
        print(f"  FAILED: Could not fetch data for {symbol}")
        continue
    
    print(f"  Data: {len(df)} bars fetched")
    
    # Initialize strategy
    strategy = DonchianChannelStrategy(channel_period=20, risk_per_trade=0.02)
    
    # Run backtest - engine expects a strategy function, not object
    from backtest.backtest_engine import BacktestEngine, Order, OrderSide
    
    backtest = BacktestEngine(
        initial_capital=10000.0,
        commission=0.0,  # Alpaca is commission-free
        slippage=0.001,  # 0.1% slippage
    )
    
    # Wrap strategy to match expected interface
    def strategy_fn(engine, timestamp, prices, data_slice):
        symbol_key = list(prices.keys())[0]
        current_position = None
        if symbol_key in engine.positions and engine.positions[symbol_key].qty > 0:
            current_position = "long"
        
        signal = strategy.generate_signal(data_slice, current_position, engine.equity)
        if signal.action == "BUY":
            qty = 0.1  # 10% of equity per trade
            return [Order(symbol=symbol_key, side=OrderSide.BUY, qty=qty, timestamp=timestamp)]
        elif signal.action == "SELL":
            pos = engine.positions.get(symbol_key)
            if pos and pos.qty > 0:
                return [Order(symbol=symbol_key, side=OrderSide.SELL, qty=pos.qty, timestamp=timestamp)]
        return []
    
    result = backtest.run(strategy_fn, df, symbol)
    results[symbol] = result
    
    if result:
        print(f"\n  RESULTS:")
        print(f"  Total Return: {result.total_return:.2%}")
        print(f"  Sharpe: {result.sharpe_ratio:.2f}")
        print(f"  Max Drawdown: {result.max_drawdown:.2%}")
        print(f"  Win Rate: {result.win_rate:.1%}")
        print(f"  Trades: {result.num_trades}")
        print(f"  Profit Factor: {result.profit_factor:.2f}")
        
        # Validation
        if result.num_trades < 10:
            print(f"  ⚠️  WARNING: Only {result.num_trades} trades - insufficient sample")
        if result.total_return < 0:
            print(f"  ❌ REJECTED: Negative return")
        elif result.sharpe_ratio < 1.0:
            print(f"  ⚠️  WARNING: Sharpe below 1.0")
        else:
            print(f"  ✅ PROMOTE TO TESTING")
    else:
        print(f"  FAILED: Backtest returned None")

print(f"\n{'='*60}")
print(f"SUMMARY")
print(f"{'='*60}")
for sym, res in results.items():
    if res:
        print(f"{sym}: Return={res.total_return:.2%}, Sharpe={res.sharpe_ratio:.2f}, Trades={res.num_trades}")
    else:
        print(f"{sym}: FAILED")
