# Track B — Pipeline Expansion

## Candidate 1: Weekly Ratio Bot v1
- **Thesis:** Ratio of two crypto assets reverts to mean over weekly timeframe
- **Status:** Concept only — strategy_spec.md needed
- **Assets:** TBD (likely BTC/ETH ratio or BTC/altcoin pairs)
- **Data source:** Alpaca
- **Kill conditions:** Ratio trending (not mean-reverting)

## Candidate 2: Dual Momentum Bot v1
- **Thesis:** Absolute + relative momentum selects best-performing crypto asset monthly
- **Status:** Concept only — strategy_spec.md needed
- **Assets:** BTC, ETH, SOL (ranked by momentum)
- **Data source:** Alpaca
- **Kill conditions:** All assets negative momentum (stay in cash)

## Dependencies
- [ ] freqtrade repo study — crash recovery patterns
- [ ] vectorbt repo study — faster backtesting engine
- [ ] v5.6 paper observation results (90 days)

## Status: SPECS NEEDED BEFORE BACKTESTING
