# Specialist Team Definitions

**Defined by:** Jarvis  
**Date:** 2026-05-18

## 1. Market Structure + Technical Analysis Team
- **Lead Agent:** Agent Candles
- **Model:** ollama run kimi-k2.6:cloud
- **Responsibilities:**
  - Identify support/resistance, liquidity zones, swing highs/lows
  - Calculate EMAs (20, 50, 100, 200), RSI, MACD, Bollinger Bands, ATR, VWAP
  - Detect divergences, break of structure, liquidity sweeps
  - Recommend entry zones, invalidation levels, stop-loss, take-profit
  - Output structured technical recommendation report
- **Why:** Kimi K2.6 is strong at pattern recognition and technical analysis reasoning.

## 2. Crypto Fundamental + On-chain Analysis Team
- **Lead Agent:** Agent Ledger
- **Model:** ollama run deepseek-v4-pro:cloud
- **Responsibilities:**
  - Analyze tokenomics, on-chain metrics, network health
  - Evaluate ecosystem strength, developer activity, competitive moat
  - Track upcoming events (upgrades, unlocks, governance, regulatory)
  - Output structured fundamental recommendation report
- **Why:** DeepSeek V4 Pro excels at structured data analysis and comprehensive research synthesis.

## 3. Sentiment + Narrative + Catalyst Analysis Team
- **Lead Agent:** Agent Pulse
- **Model:** ollama run qwen3.5:397b-cloud
- **Responsibilities:**
  - Research current crypto news and social sentiment
  - Analyze market narratives, institutional vs retail mood
  - Track derivatives sentiment (funding rates, open interest, liquidations)
  - Identify sentiment extremes and news-based risks
  - Output structured sentiment recommendation report
- **Why:** Qwen 3.5 397B has strong multilingual and contextual understanding for news/sentiment analysis.

## 4. Portfolio Risk + Execution Risk Assessment Team
- **Lead Agent:** Agent Shield
- **Model:** ollama run deepseek-v4-pro:cloud
- **Responsibilities:**
  - Build risk matrix for every asset and strategy
  - Analyze volatility, correlation, drawdown scenarios
  - Assess liquidity, slippage, execution, data, model risks
  - Recommend position sizing and max exposure
  - Output structured risk recommendation report
- **Why:** DeepSeek V4 Pro's structured reasoning is ideal for risk assessment frameworks.

## 5. Investment Thesis + Strategy Synthesis Team
- **Lead Agent:** Agent Compass
- **Model:** ollama run kimi-k2.6:cloud
- **Responsibilities:**
  - Synthesize all 4 recommendation reports into unified thesis
  - Create bull case, bear case, catalyst timeline
  - Recommend entry, stop-loss, profit targets, position sizing
  - Define invalidation conditions and what would change the thesis
  - Output structured thesis recommendation report
- **Why:** Kimi K2.6 strong at synthesis and strategic reasoning.

## 6. Strategy Engineering Team
- **Lead:** Chief Architect (Agent Blueprint) + Agent Candles support
- **Model:** ollama run qwen3.5:397b-cloud
- **Responsibilities:**
  - Convert thesis into testable strategy logic
  - Implement strategy modules
  - Ensure no lookahead bias
  - Coordinate with Backtesting and QA teams

## 7. Backtesting + Validation Team
- **Lead:** Agent Blueprint + deterministic code
- **Responsibilities:**
  - Run backtest engine
  - Calculate metrics (Sharpe, Sortino, max drawdown, etc.)
  - Walk-forward validation
  - Compare vs buy-and-hold baseline
  - Check for data leakage

## 8. Broker Execution Team
- **Lead:** Alpaca Client module (code-based)
- **Responsibilities:**
  - Execute paper orders via Alpaca API
  - Validate paper mode before every order
  - Fetch account, positions, open orders
  - Reconcile executions
  - Log all orders and results

## 9. Security + Secrets Team
- **Lead:** Agent Vault (code-based + manual review)
- **Responsibilities:**
  - Manage API keys via environment variables
  - Audit secret handling
  - Review deployment safety
  - Block secrets in logs and memory

## 10. QA + Testing Team
- **Lead:** pytest + Agent Blueprint
- **Responsibilities:**
  - Unit tests for all modules
  - Integration tests for pipeline
  - No-lookahead bias detection
  - Data leakage checks
  - Test coverage reporting

## 11. Memory + Self-Evolution Team
- **Lead:** Agent Echo (Jarvis + memory system)
- **Responsibilities:**
  - Maintain decision logs
  - Maintain mistake and lesson logs
  - Run self-evolution experiments
  - Track hypotheses, results, keep/revert decisions

## 12. Dashboard + Monitoring Team
- **Lead:** Agent Watchtower (code-based dashboards)
- **Responsibilities:**
  - Monitor positions, PnL, risk metrics
  - Alert on anomalies
  - Display agent recommendation status
  - Track system health

## 13. Documentation Team
- **Lead:** Agent Scribe (all agents contribute)
- **Responsibilities:**
  - Maintain architecture docs
  - Maintain agent prompt docs
  - Maintain API docs
  - Maintain decision logs

## Model Assignment Summary
| Agent/Team | Model | Reason |
|------------|-------|--------|
| Jarvis | kimi-k2.6:cloud | Executive decision making |
| COO (Coda) | deepseek-v4-pro:cloud | Planning, coordination |
| Chief Architect (Blueprint) | qwen3.5:397b-cloud | Architecture, code |
| Technical (Candles) | kimi-k2.6:cloud | Pattern recognition |
| Fundamental (Ledger) | deepseek-v4-pro:cloud | Research synthesis |
| Sentiment (Pulse) | qwen3.5:397b-cloud | Contextual understanding |
| Risk (Shield) | deepseek-v4-pro:cloud | Structured risk analysis |
| Thesis (Compass) | kimi-k2.6:cloud | Strategic synthesis |
| Strategy Engineering | qwen3.5:397b-cloud | Code generation |
| Risk Governor (Sentinel) | Code-based | Deterministic safety |
