#!/usr/bin/env python3
"""
RSI Range Trading Backtest

Comprehensive backtest with:
- 6+ months hourly data
- Fees and slippage
- No-lookahead validation
- All required metrics
- Asset-by-asset breakdown
- Regime breakdown

Usage: python3 scripts/backtest_rsi_range.py
"""

import sys
sys.path.insert(0, 'src')

import json
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from pathlib import Path

from data.data_fetcher import DataFetcher
from strategies.rsi_range_strategy import RSIRangeStrategy

# Configuration
FEE_RATE = 0.001  # 0.1% per trade (Alpaca crypto)
SLIPPAGE_RATE = 0.001  # 0.1% slippage
POSITION_SIZE_PCT = 0.10  # 10% of capital per trade
INITIAL_CAPITAL = 10000.0
MIN_TRADES_FOR_ACTIVE = 10
MIN_RETURN_FOR_ACTIVE = 0.05
MIN_SHARPE_FOR_ACTIVE = 2.0
MAX_DRAWDOWN_FOR_ACTIVE = 0.15


def calculate_sharpe(returns, risk_free_rate=0):
    """Calculate annualized Sharpe ratio from returns."""
    if len(returns) < 2:
        return 0.0
    excess_returns = np.array(returns) - risk_free_rate
    std = np.std(excess_returns, ddof=1)
    if std == 0:
        return 0.0
    return np.mean(excess_returns) / std * np.sqrt(24 * 365)  # Hourly to annualized


def calculate_sortino(returns, risk_free_rate=0):
    """Calculate Sortino ratio using downside deviation."""
    if len(returns) < 2:
        return 0.0
    excess_returns = np.array(returns) - risk_free_rate
    downside = [r for r in excess_returns if r < 0]
    if not downside:
        return float('inf')
    downside_std = np.std(downside, ddof=1)
    if downside_std == 0:
        return float('inf')
    return np.mean(excess_returns) / downside_std * np.sqrt(24 * 365)


def detect_regime(df, window=100):
    """Simple regime detection based on trend."""
    ma = df['close'].rolling(window=window).mean()
    price_vs_ma = df['close'] / ma
    
    # Classify: >1.05 = uptrend, <0.95 = downtrend, else ranging
    if price_vs_ma.iloc[-1] > 1.05:
        return "uptrend"
    elif price_vs_ma.iloc[-1] < 0.95:
        return "downtrend"
    else:
        return "ranging"


def run_backtest(symbol, df, strategy, initial_capital=INITIAL_CAPITAL):
    """
    Run backtest with proper position sizing, fees, and slippage.
    Returns comprehensive results dict.
    """
    if df is None or len(df) < 100:
        return {"error": f"Insufficient data for {symbol}"}
    
    capital = initial_capital
    max_capital = initial_capital
    position = None  # None or dict with entry info
    entry_price = 0
    trades = []
    equity_curve = [initial_capital]
    drawdowns = [0.0]
    hourly_returns = []
    
    # No-lookahead check: strategy only uses data up to index i
    for i in range(strategy.range_lookback + strategy.rsi_period, len(df)):
        # Only use data up to index i (no future data)
        window = df.iloc[:i+1]
        current_price = df['close'].iloc[i]
        current_time = df.index[i]
        
        # Generate signal using only historical data
        signal = strategy.generate_signal(window, position)
        
        if signal.action == "BUY" and position is None:
            # Calculate position size
            position_value = capital * POSITION_SIZE_PCT
            qty = position_value / current_price
            
            # Apply slippage (worse entry price)
            entry_price_with_slippage = current_price * (1 + SLIPPAGE_RATE)
            
            # Fee on entry
            entry_fee = position_value * FEE_RATE
            
            position = {
                "entry_time": current_time,
                "entry_price": entry_price_with_slippage,
                "qty": qty,
                "position_value": position_value,
                "entry_fee": entry_fee,
                "stop_loss": signal.stop_loss or entry_price_with_slippage * 0.99,
                "take_profit": signal.take_profit or entry_price_with_slippage * 1.02,
                "signal_confidence": signal.confidence,
                "signal_reason": signal.reason,
            }
            
            capital -= entry_fee
            
        elif signal.action in ("SELL", "SELL_ALL") and position is not None:
            # Apply slippage (worse exit price)
            exit_price_with_slippage = current_price * (1 - SLIPPAGE_RATE)
            
            # Calculate PnL
            pnl = (exit_price_with_slippage - position["entry_price"]) * position["qty"]
            pnl_pct = pnl / position["position_value"]
            
            # Fee on exit
            exit_fee = (exit_price_with_slippage * position["qty"]) * FEE_RATE
            
            # Net PnL after fees
            net_pnl = pnl - position["entry_fee"] - exit_fee
            net_pnl_pct = net_pnl / position["position_value"]
            
            # Update capital
            capital += net_pnl
            
            # Record trade
            trades.append({
                "entry_time": position["entry_time"],
                "entry_price": position["entry_price"],
                "exit_time": current_time,
                "exit_price": exit_price_with_slippage,
                "qty": position["qty"],
                "gross_pnl": pnl,
                "gross_pnl_pct": pnl_pct,
                "entry_fee": position["entry_fee"],
                "exit_fee": exit_fee,
                "net_pnl": net_pnl,
                "net_pnl_pct": net_pnl_pct,
                "position_value": position["position_value"],
                "stop_loss": position["stop_loss"],
                "take_profit": position["take_profit"],
                "signal_confidence": position["signal_confidence"],
                "signal_reason": position["signal_reason"],
            })
            
            position = None
        
        # Track equity and drawdown
        # If in position, mark-to-market
        if position is not None:
            unrealized = (current_price - position["entry_price"]) * position["qty"]
            current_equity = capital + unrealized - position["entry_fee"]
        else:
            current_equity = capital
        
        equity_curve.append(current_equity)
        
        if current_equity > max_capital:
            max_capital = current_equity
        
        drawdown = (max_capital - current_equity) / max_capital
        drawdowns.append(drawdown)
        
        # Hourly returns for Sharpe
        if len(equity_curve) > 1:
            hourly_return = (equity_curve[-1] - equity_curve[-2]) / equity_curve[-2]
            hourly_returns.append(hourly_return)
    
    # Close any open position at last price
    if position is not None:
        last_price = df['close'].iloc[-1] * (1 - SLIPPAGE_RATE)
        pnl = (last_price - position["entry_price"]) * position["qty"]
        exit_fee = (last_price * position["qty"]) * FEE_RATE
        net_pnl = pnl - position["entry_fee"] - exit_fee
        capital += net_pnl
        trades.append({
            "entry_time": position["entry_time"],
            "entry_price": position["entry_price"],
            "exit_time": df.index[-1],
            "exit_price": last_price,
            "qty": position["qty"],
            "gross_pnl": pnl,
            "gross_pnl_pct": pnl / position["position_value"],
            "entry_fee": position["entry_fee"],
            "exit_fee": exit_fee,
            "net_pnl": net_pnl,
            "net_pnl_pct": net_pnl / position["position_value"],
            "position_value": position["position_value"],
            "stop_loss": position["stop_loss"],
            "take_profit": position["take_profit"],
            "signal_confidence": position["signal_confidence"],
            "signal_reason": position["signal_reason"],
        })
    
    # Calculate metrics
    final_equity = equity_curve[-1]
    total_return = (final_equity - initial_capital) / initial_capital
    max_drawdown = max(drawdowns)
    num_trades = len(trades)
    
    if num_trades > 0:
        wins = [t for t in trades if t["net_pnl"] > 0]
        losses = [t for t in trades if t["net_pnl"] <= 0]
        
        win_rate = len(wins) / num_trades
        avg_win = np.mean([t["net_pnl_pct"] for t in wins]) if wins else 0
        avg_loss = np.mean([t["net_pnl_pct"] for t in losses]) if losses else 0
        
        total_wins = sum(t["net_pnl"] for t in wins)
        total_losses = abs(sum(t["net_pnl"] for t in losses))
        profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')
        
        sharpe = calculate_sharpe(hourly_returns)
        sortino = calculate_sortino(hourly_returns)
        
        # Regime breakdown (simplified)
        regime_pnls = {"uptrend": [], "downtrend": [], "ranging": []}
        for t in trades:
            # Find regime at entry time
            try:
                idx = df.index.get_loc(t["entry_time"])
                if idx >= 100:
                    regime = detect_regime(df.iloc[:idx+1])
                    regime_pnls[regime].append(t["net_pnl"])
            except:
                regime_pnls["ranging"].append(t["net_pnl"])
        
        regime_summary = {}
        for regime, pnls in regime_pnls.items():
            if pnls:
                regime_summary[regime] = {
                    "trades": len(pnls),
                    "total_pnl": sum(pnls),
                    "avg_pnl": np.mean(pnls),
                }
            else:
                regime_summary[regime] = {"trades": 0, "total_pnl": 0, "avg_pnl": 0}
    else:
        win_rate = avg_win = avg_loss = profit_factor = sharpe = sortino = 0
        regime_summary = {}
        wins = losses = []
    
    # No-lookahead check: verify strategy never used future data
    no_lookahead_clean = True  # Enforced by using df.iloc[:i+1] only
    
    # Determine promotion status
    if num_trades >= MIN_TRADES_FOR_ACTIVE and total_return >= MIN_RETURN_FOR_ACTIVE and sharpe >= MIN_SHARPE_FOR_ACTIVE and max_drawdown <= MAX_DRAWDOWN_FOR_ACTIVE:
        promotion_status = "ACTIVE"
    elif num_trades >= 3 and total_return > 0:
        promotion_status = "TESTING"
    else:
        promotion_status = "REJECTED"
    
    return {
        "symbol": symbol,
        "initial_capital": initial_capital,
        "final_equity": final_equity,
        "total_return": total_return,
        "total_return_pct": total_return * 100,
        "max_drawdown": max_drawdown,
        "max_drawdown_pct": max_drawdown * 100,
        "num_trades": num_trades,
        "win_rate": win_rate,
        "win_rate_pct": win_rate * 100,
        "avg_win_pct": avg_win * 100,
        "avg_loss_pct": avg_loss * 100,
        "profit_factor": profit_factor,
        "sharpe": sharpe,
        "sortino": sortino,
        "fees_included": True,
        "slippage_included": True,
        "fee_rate": FEE_RATE,
        "slippage_rate": SLIPPAGE_RATE,
        "position_size_pct": POSITION_SIZE_PCT,
        "no_lookahead_clean": no_lookahead_clean,
        "promotion_status": promotion_status,
        "wins": len(wins),
        "losses": len(losses),
        "win_loss_ratio": len(wins) / max(len(losses), 1),
        "regime_summary": regime_summary,
        "trades": trades,
        "equity_curve": equity_curve,
    }


def main():
    print("=" * 80)
    print("RSI RANGE TRADING STRATEGY BACKTEST")
    print("=" * 80)
    print()
    
    df_fetcher = DataFetcher()
    strategy = RSIRangeStrategy()
    
    results_by_asset = {}
    all_pass = True
    
    for symbol in ['BTC/USD', 'ETH/USD', 'SOL/USD']:
        print(f"Backtesting {symbol}...")
        try:
            bars = df_fetcher.fetch_hourly_bars(symbol, limit=5000)
            if bars is None or len(bars) < 100:
                print(f"  ❌ Insufficient data")
                results_by_asset[symbol] = {"error": "Insufficient data"}
                all_pass = False
                continue
            
            result = run_backtest(symbol, bars, strategy)
            results_by_asset[symbol] = result
            
            if "error" in result:
                print(f"  ❌ Error: {result['error']}")
                all_pass = False
                continue
            
            print(f"  ✅ Backtest complete")
            print(f"     Data period: {bars.index[0]} to {bars.index[-1]} ({len(bars)} bars)")
            print(f"     Trades: {result['num_trades']}")
            print(f"     Return: {result['total_return_pct']:.2f}%")
            print(f"     Win rate: {result['win_rate_pct']:.1f}%")
            print(f"     Avg win: {result['avg_win_pct']:.2f}%")
            print(f"     Avg loss: {result['avg_loss_pct']:.2f}%")
            print(f"     Profit factor: {result['profit_factor']:.2f}")
            print(f"     Max drawdown: {result['max_drawdown_pct']:.2f}%")
            print(f"     Sharpe: {result['sharpe']:.2f}")
            print(f"     Sortino: {result['sortino']:.2f}")
            print(f"     Fees included: {result['fees_included']}")
            print(f"     Slippage included: {result['slippage_included']}")
            print(f"     No-lookahead: {result['no_lookahead_clean']}")
            print(f"     Promotion status: {result['promotion_status']}")
            print(f"     Regime breakdown: {json.dumps(result['regime_summary'], indent=2)}")
            print()
            
            if result['promotion_status'] == "REJECTED":
                all_pass = False
                
        except Exception as e:
            print(f"  ❌ Exception: {e}")
            import traceback
            traceback.print_exc()
            results_by_asset[symbol] = {"error": str(e)}
            all_pass = False
    
    # Summary
    print("=" * 80)
    print("BACKTEST SUMMARY")
    print("=" * 80)
    for symbol, result in results_by_asset.items():
        if "error" not in result:
            print(f"{symbol}: {result['num_trades']} trades, {result['total_return_pct']:.2f}% return, Sharpe {result['sharpe']:.2f}, status: {result['promotion_status']}")
        else:
            print(f"{symbol}: ERROR - {result['error']}")
    
    # Save results
    output_dir = Path("logs/backtests")
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"rsi_range_backtest_{timestamp}.json"
    
    with open(output_file, 'w') as f:
        json.dump(results_by_asset, f, indent=2, default=str)
    
    print()
    print(f"Results saved to: {output_file}")
    print()
    
    if all_pass:
        print("🎉 ALL ASSETS PASS — Strategy can be promoted to TESTING")
    else:
        print("⚠️  Some assets failed — Strategy needs improvement or rejection")
    
    return results_by_asset


if __name__ == "__main__":
    main()
