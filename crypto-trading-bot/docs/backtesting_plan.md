# Backtesting Plan

**Version:** 1.0.0  
**Date:** 2026-05-18  
**Owner:** Backtesting + Validation Team

## Requirements

Before any paper-trading order logic is enabled:
1. Build or choose backtest engine
2. Run baseline buy-and-hold comparison
3. Run strategy comparison
4. Run walk-forward validation
5. Include fees and slippage
6. Check no-lookahead bias
7. Check data leakage
8. Produce report

## Backtest Engine Design

### Approach: Event-Driven Backtest
- Simulate order book events
- Handle partial fills
- Track cash and positions
- Support market and limit orders
- Include fee model

### Fee Model (Alpaca Paper Approximation)
- Commission: $0 (Alpaca commission-free)
- Slippage: 0.1% per trade (conservative estimate)
- Spread: variable by asset

### Data Requirements
- Minimum 2 years historical data
- Hourly bars minimum
- Prefer minute bars for precision
- Source: Alpaca crypto data API

## Required Metrics

| Metric | Description | Threshold for Approval |
|--------|-------------|------------------------|
| Total Return | Cumulative PnL | > buy-and-hold |
| Annualized Return | CAGR | > 0% minimum |
| Sharpe Ratio | Risk-adjusted return | > 1.0 preferred |
| Sortino Ratio | Downside-adjusted return | > 1.0 preferred |
| Max Drawdown | Peak-to-trough decline | < 5% (per risk limits) |
| Calmar Ratio | Return / Max Drawdown | > 1.0 preferred |
| Win Rate | % profitable trades | > 40% |
| Profit Factor | Gross profit / Gross loss | > 1.2 |
| Average Trade | Mean PnL per trade | > $0 |
| Number of Trades | Sample size | > 50 for statistical significance |
| Exposure Time | % time in market | < 80% (avoid overtrading) |
| Turnover | Annualized trading volume / portfolio value | < 20x |
| Worst Day | Largest single-day loss | < 2% (daily limit) |
| Worst Trade | Largest single-trade loss | < 2% |
| Regime-Specific Performance | Bull vs bear market | Both regimes positive |

## Validation Checks

### No-Lookahead Bias
- Strategy cannot use future data at decision time
- Indicators calculated only with past data
- Strict temporal ordering enforced

### Data Leakage
- No test data in training
- Walk-forward only
- No peeking at future returns

### Walk-Forward Validation
- Divide data into in-sample / out-of-sample
- Train on in-sample, test on out-of-sample
- Repeat with rolling windows
- Strategy must pass on multiple windows

## Implementation Plan

### Sprint 2 (Agent v1)
- Build backtest engine skeleton
- Implement data fetcher with historical data
- Run baseline buy-and-hold for BTC, ETH, SOL
- Calculate baseline metrics

### Sprint 3 (Strategy)
- Integrate strategy engine with backtest
- Run first strategy backtest
- Validate no-lookahead bias
- Produce metrics report

### Sprint 4 (Paper Trading)
- Compare backtest results with paper trading
- Reconcile discrepancies
- Refine slippage and fee models

## Approval Criteria

A strategy is approved for paper trading when:
1. All metrics above threshold
2. No-lookahead bias check passes
3. Walk-forward validation passes
4. Risk Governor checks pass on all simulated trades
5. QA signs off
6. Chief Architect reviews
7. COO confirms workflow
8. Jarvis approves
9. CEO informed
