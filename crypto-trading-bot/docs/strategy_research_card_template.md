# STRATEGY RESEARCH CARD TEMPLATE

**Version:** 1.0.0  
**Created:** 2026-05-21 00:43 CEST  
**Purpose:** Structured format for evaluating every external strategy idea before implementation

---

## Strategy Name

[Short, descriptive name]

## Source

[URL, book title, trader name, video title, etc.]

## Source Type

- [ ] TradingView public strategy/indicator
- [ ] TradingView Pine Script (publicly accessible)
- [ ] Experienced trader (name/platform)
- [ ] Crypto market-structure trader
- [ ] Quant researcher (paper/blog)
- [ ] Public technical-analysis source
- [ ] GitHub open-source repo
- [ ] YouTube strategy explanation
- [ ] Trading book / classic concept
- [ ] Binance/crypto education
- [ ] Other recognized public source

## Market Type

- [ ] Trending markets
- [ ] Ranging/sideways markets
- [ ] High volatility
- [ ] Low volatility
- [ ] Specific: _______

## Best Asset

[Which asset this works best on, or "all" if universal]

## Best Timeframe

[1h, 4h, 1d, etc. — must match our operational capability]

## Entry Rules

1. [Specific condition]
2. [Specific condition]
3. [Specific condition]

## Exit Rules

1. [Specific condition]
2. [Specific condition]
3. [Specific condition]

## Stop-Loss

[Exact percentage or formula]

## Take-Profit

[Exact percentage or formula]

## Partial-Profit Logic

[If applicable: at what level, what percentage of position]

## Trailing-Stop Logic

[If applicable: activation level, trail percentage]

## Indicators Required

| Indicator | Parameters | Purpose |
|-----------|-----------|---------|
| [Name] | [Settings] | [What it does] |

## Best Regime

[Uptrend, downtrend, ranging, high volatility, etc.]

## Worst Regime

[When does this strategy fail?]

## Why It May Work

[Clear hypothesis for positive expectancy]

## Known Weaknesses

1. [Weakness]
2. [Weakness]
3. [Weakness]

## Risk Assessment

| Risk | Level | Mitigation |
|------|-------|------------|
| [Risk type] | High/Medium/Low | [How to reduce] |

## Implementation Complexity

- [ ] Simple (1-2 indicators, basic rules)
- [ ] Medium (3-4 indicators, conditional logic)
- [ ] Complex (5+ indicators, multi-timeframe, ML)

## Backtest Priority

- [ ] High — implement and backtest immediately
- [ ] Medium — queue for next backtest batch
- [ ] Low — research further before committing

## Jarvis Recommendation

[After initial research, what is the recommendation?]

---

## VALIDATION PIPELINE CHECKLIST

### Phase 1: Research (CEO-approved sources only)
- [ ] Source verified as public/recognized
- [ ] Rules extracted clearly
- [ ] Hypothesis documented
- [ ] Weaknesses identified
- [ ] Risk assessed

### Phase 2: Implementation
- [ ] Python implementation created
- [ ] Unit tests written
- [ ] No-lookahead check implemented
- [ ] Code reviewed

### Phase 3: Backtest
- [ ] 6+ months hourly data (BTC, ETH, SOL)
- [ ] Fees included (0.1%)
- [ ] Slippage included (0.1%)
- [ ] ≥10 trades per asset
- [ ] Return calculated
- [ ] Win rate calculated
- [ ] Average win/loss calculated
- [ ] Profit factor calculated
- [ ] Max drawdown calculated
- [ ] Sharpe/Sortino calculated
- [ ] Regime breakdown completed
- [ ] Asset-by-asset breakdown completed

### Phase 4: Evaluation
- [ ] Passes minimum thresholds:
  - Return > +5%
  - Win rate > 40%
  - Profit factor > 1.2
  - Max drawdown < 15%
  - Sharpe > 2.0
  - Sortino > 2.0
  - ≥10 trades
- [ ] No-lookahead clean
- [ ] Regime fit confirmed

### Phase 5: Promotion
- [ ] REJECTED if any threshold failed
- [ ] TESTING if passes but needs live confirmation
- [ ] ACTIVE only after live paper evidence confirms edge

### Phase 6: Live Testing (TESTING mode only)
- [ ] $100 max position size
- [ ] 1 max open position
- [ ] 5+ live trades minimum
- [ ] Live win rate tracked
- [ ] Live profit factor tracked
- [ ] Live Sharpe estimated

### Phase 7: ACTIVE Promotion (only after live evidence)
- [ ] Backtest results confirmed by live data
- [ ] Risk Governor approves
- [ ] CEO informed
- [ ] Strategy Validation Gate allows

---

## DECISION LOG

| Date | Decision | By | Reason |
|------|----------|-----|--------|
| | | | |

---

## FILES

- Research notes: `docs/strategy_research/[strategy_name]/`
- Implementation: `src/strategies/[strategy_name].py`
- Tests: `tests/test_[strategy_name].py`
- Backtest results: `logs/backtests/[strategy_name]_YYYYMMDD_HHMMSS.json`
- Strategy card: `docs/strategy_research_cards/[strategy_name].md`

---

**Rule: No strategy trades without completing ALL phases.**
**Rule: External claims are not proof. Our backtest is proof.**
**Rule: Memory without enforcement is not self-evolution.**
