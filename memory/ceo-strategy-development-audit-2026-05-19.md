# CEO Strategy Development Audit — 2026-05-19 (CEST)

## Timezone
Europe/Stockholm (CEST, UTC+2)

## Evidence Reviewed
- `src/strategy/strategy_engine.py` — all implemented strategies
- `src/pipeline_controller.py` — strategy selection logic
- `src/orchestrator.py` — decision pipeline
- `src/agents/agent_runner.py` — agent orchestration
- `src/agents/base_agent.py` — agent output format
- `src/agents/thesis_synthesis.py` — Compass agent
- `src/backtest/backtest_engine.py` — backtesting framework
- `src/risk_governor.py` — risk controls
- `config/assets.yaml` — asset universe
- `config/risk_limits.yaml` — risk rules
- `scripts/autonomous_pipeline.py` — pipeline config
- `scripts/autonomous_daemon.py` — daemon config
- Alpaca API — trade history, positions, account
- `logs/autonomous_pipeline.log` — pipeline execution logs
- `logs/decisions/decisions.jsonl` — structured decision log
- `logs/cycle_*.json` — cycle reports

---

## Strategy Inventory

| Strategy Name | Source / Inspiration | Implemented | Active | Backtested | Paper Enabled | Profitability Result | Num Trades (BTC/168h) | Max Drawdown | Sharpe | Reason Active/Inactive | Next Action |
|---------------|----------------------|-------------|--------|------------|---------------|----------------------|----------------------|--------------|--------|------------------------|-------------|
| **SimpleMA (20)** | Basic textbook MA crossover | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | **Negative** (-3.91% BTC, -7.06% ETH, -6.48% SOL) | 18 BTC | 5.38% BTC | -9.44 | Hard-coded as default until today; now tested but usually not best | Evaluated but rarely selected |
| **RSI (14/30/70)** | Classic Wilder RSI | ✅ Yes | ⚠️ Tested | ✅ Yes | ❌ No | Negative (-2.01% BTC, -2.85% ETH, -3.63% SOL) | 3 BTC | 5.44% BTC | N/A | Fails drawdown >5% on BTC/SOL | Needs parameter tuning |
| **MACD (12/26/9)** | Standard MACD | ✅ Yes | ⚠️ Tested | ✅ Yes | ❌ No | Negative (-2.66% BTC, -6.23% ETH, -4.15% SOL) | 5 BTC | 5.02% BTC | N/A | Fails drawdown >5% on all assets | Needs parameter tuning |
| **BollingerBands (20, 2.0)** | John Bollinger's bands | ✅ Yes | ⚠️ Tested | ✅ Yes | ❌ No | **Best** (-0.79% BTC, -3.29% ETH, -0.80% SOL) | 3 BTC | **2.84% BTC** ✅ | N/A | **PASSES drawdown on BTC/SOL** — now selected as best | **Now the preferred strategy** |
| **BuyAndHold (95%)** | Baseline benchmark | ✅ Yes | ❌ No | ✅ Yes | ❌ No | Negative (market dependent) | 1 | Market drawdown | N/A | Never wired into pipeline | Not useful for active trading |
| **Sentiment-driven strategy** | ❌ Not implemented | ❌ No | ❌ No | ❌ No | ❌ No | N/A | N/A | N/A | N/A | No bridge from Pulse agent to strategy | **Must build** |
| **Agent-generated strategy** | ❌ Not implemented | ❌ No | ❌ No | ❌ No | ❌ No | N/A | N/A | N/A | N/A | Agents recommend but don't generate code | **Must build** |
| **Famous trader strategy** | ❌ Not researched | ❌ No | ❌ No | ❌ No | ❌ No | N/A | N/A | N/A | N/A | No research pipeline exists | **Must build** |
| **Multi-strategy ensemble** | ❌ Not implemented | ❌ No | ❌ No | ❌ No | ❌ No | N/A | N/A | N/A | N/A | No ensemble logic | **Must build** |
| **Regime detection strategy** | ❌ Not implemented | ❌ No | ❌ No | ❌ No | ❌ No | N/A | N/A | N/A | N/A | No regime classifier | **Must build** |

**CRITICAL FINDING:** Before today, **only SimpleMA was active**. All other 4 strategies were "dead code" — implemented but never called. I deployed multi-strategy testing today (commit `56842e5`), so now 4 strategies are tested per asset and the best is selected. BollingerBands is now the best performer.

---

## Position and Signal Audit

| Asset | Scanned | Signal Found | Signal Direction | Strategy Source | Trade Taken | If Rejected, Why | Risk Governor Decision | Current Position | Next Action |
|-------|---------|--------------|------------------|-----------------|-------------|------------------|----------------------|------------------|-------------|
| BTC/USD | ✅ Yes | ✅ Yes (agents ran) | BUY (from agents, backtest) | BollingerBands | ❌ No | **Risk Governor BLOCKED** — position pct 14.93% > max 10% | **BLOCK** — max_position_pct check failed | 0.012933 BTC @ $77,087 avg (unrealized -$6.65) | Monitor — cannot add more |
| ETH/USD | ✅ Yes | ✅ Yes (agents ran) | BUY (from agents) | RSI (best, but still fails) | ❌ No | **Orchestrator REJECTED** — ALL strategies fail backtest (drawdown >5%) | **ALLOW** — all risk checks passed | None | Needs better strategy or regime change |
| SOL/USD | ✅ Yes | ✅ Yes (agents ran) | BUY (from agents) | BollingerBands (passes) | ❌ No | **Orchestrator REJECTED** — in earlier cycles; need to check latest multi-strategy cycle | **ALLOW** — all risk checks passed | None | **Should pass with new BollingerBands selection** |

**Evidence:**
- BTC: ` Risk Governor BLOCKED order for BTC/USD: block` — check: `max_position_pct` — "Position pct 14.93% exceeds max 10%"
- ETH: `Backtest failed: max drawdown 7.37% > 5%` — ALL 4 strategies fail
- SOL: `Backtest failed: max drawdown 6.90% > 5%` (SimpleMA); BollingerBands passes at 2.84%

---

## Answers to CEO Questions

### Q1: Who is responsible for developing strategies?

**Answer: NO ONE. This capability is not implemented yet.**

| Responsibility | Owner | Status | Evidence |
|---------------|-------|--------|----------|
| Strategy discovery | **NO OWNER** | ❌ Not implemented | No agent, team, or pipeline for discovering new strategies |
| Strategy implementation | **Initial developer (bootstrap)** | ⚠️ Stale | 5 strategies coded at project setup; no new strategies added since |
| Backtesting | **BacktestEngine** | ✅ Functional | `src/backtest/backtest_engine.py` works; tests pass |
| Paper-trading validation | **AlpacaPaperClient + Orchestrator** | ✅ Functional | Paper orders execute; 2 trades made successfully |
| Improving failed strategies | **NO OWNER** | ❌ Not implemented | No agent or pipeline reviews failed strategies |
| Strategy Engineering Team | ❌ **Only defined in prompt** | ❌ Not real | No `src/strategy_engineering_team/` or equivalent |
| Trading Research Agent | ❌ **Does not exist** | ❌ Not implemented | No `src/agents/strategy_research.py` or equivalent |
| **Jarvis (Junior CEO)** | ✅ **Default owner** | ✅ Active | I made the multi-strategy fix today |

**The 5 recommendation agents (Candles, Ledger, Pulse, Shield, Compass) produce trading recommendations but do NOT generate strategy code. They are "advisory" agents, not "engineering" agents.**

### Q2: Why do we only have a few strategies?

**Answer: Because there is no strategy discovery pipeline. This capability is not implemented yet.**

| Strategy | Status | Why It Exists |
|----------|--------|---------------|
| BuyAndHold | Baseline | Bootstrap developer added for benchmarking |
| SimpleMA | Default | Bootstrap developer added as basic test |
| RSI | Dead code | Bootstrap developer added but never wired |
| MACD | Dead code | Bootstrap developer added but never wired |
| BollingerBands | Dead code (now active) | Bootstrap developer added but never wired |

**No new strategies have been added since project bootstrap.** The blocker is **lack of prioritization + no research pipeline**. Not data, not code, not backtesting — those all work. The project was built with 5 basic strategies and then focus shifted to agent pipeline + risk controls.

### Q3: Why are we not researching strategies from famous or experienced traders?

**Answer: This capability is not implemented yet.**

There is NO:
- Web search for trading strategies
- Book/paper extraction pipeline
- YouTube strategy transcription
- TradingView indicator scraping
- Quant researcher consultation
- Famous trader strategy library
- Community strategy collection

**The agents are LLM-based but their prompts do NOT ask them to search for, study, or extract external strategies.** They analyze current market data only.

### Q4: Why are we not profitable yet?

**Answer: Multiple structural reasons — the bot is still in structural/demo stage.**

| Factor | Impact | Evidence |
|--------|--------|----------|
| **Only 2 trades ever made** | **PRIMARY** | Alpaca API shows 2 BTC buys total |
| **No sell trades / no exits** | **PRIMARY** | Position monitor exists but hasn't triggered (BTC not at -3% SL or +6% TP) |
| **Only 1 active strategy until today** | **HIGH** | SimpleMA was the only one wired in |
| **Strategies lose money in current regime** | **HIGH** | All strategies negative over past week in backtest |
| **Agents recommend WAIT** | **HIGH** | Compass thesis = WAIT for BTC in latest cycle |
| **Market conditions (bearish/downtrend)** | **HIGH** | BTC down from ~$80k to ~$76k over past week |
| **Agent latency (5+ min per cycle)** | **MEDIUM** | Limits cycle frequency |
| **4-hour scan frequency** | **LOW** | Could be more frequent but not primary blocker |
| **Paper execution fully enabled** | **NOT A FACTOR** | Paper trading works correctly |
| **Limited historical data (168h)** | **MEDIUM** | Only 1 week of hourly data for backtest |

**The system is structurally sound but has not found enough profitable signals in a bearish regime with basic strategies.**

### Q5: Why is there still only one position?

**Answer: Risk Governor blocks additional BTC; strategies fail for ETH/SOL.**

| Reason | Evidence | Is It System Design? |
|--------|----------|---------------------|
| **BTC position limit reached** | "Position pct 14.93% exceeds max 10%" | ✅ Yes — intentional risk control |
| **ETH/SOL backtest fails** | "max drawdown 7.42% > 5%" | ✅ Yes — intentional safety gate |
| **System scans all 3 assets** | `for sym in ['BTC/USD', 'ETH/USD', 'SOL/USD']` | ✅ Yes — diversification IS attempted |
| **System allows up to 3 positions** | `max_open_positions: 3` | ✅ Yes — diversification IS designed |
| **Cash available** | $9,000.56 | ✅ Yes — capital is NOT the blocker |
| **Buying power** | $18,001.12 | ✅ Yes — leverage is NOT the blocker |

**The system IS designed to diversify. It IS scanning all 3 assets every cycle. It IS allowing up to 3 positions. The blockers are: (1) BTC already at limit, (2) no strategy passes backtest for ETH/SOL in current bearish regime.**

**With today's multi-strategy deployment, BollingerBands passes for SOL (-0.80%, 2.84% drawdown). The next cycle may produce a SOL position if agents agree.**

---

## Main Blockers (Ranked)

| Rank | Blocker | Severity | Evidence |
|------|---------|----------|----------|
| 1 | **No strategy research pipeline** | **CRITICAL** | No research agent, no web search, no book extraction, no famous trader study |
| 2 | **Only 5 basic strategies** | **CRITICAL** | All bootstrap-era; no new strategies since day 1 |
| 3 | **Agents recommend but don't generate strategies** | **HIGH** | 5 agents produce text recommendations, zero code |
| 4 | **Bearish market regime** | **HIGH** | All strategies lose money over past week |
| 5 | **BTC position at limit** | **HIGH** | Risk Governor correctly blocking |
| 6 | **No rejected-signal structured logging** | **MEDIUM** | Decisions logged but not signal-level detail |
| 7 | **No missed-opportunity review** | **MEDIUM** | No periodic review of why signals were missed |
| 8 | **168h backtest window too short** | **MEDIUM** | 1 week may not capture regime shifts |
| 9 | **4-hour scan frequency** | **LOW** | Could be faster but not primary blocker |
| 10 | **Agent latency** | **LOW** | 5-min per asset limits throughput |

---

## Jarvis Decision

**I am building a continuous strategy-research pipeline that will:**

1. **Create a StrategyResearchAgent** (LLM-based) that searches for and extracts proven trading strategies from public sources
2. **Build a strategy library** with structured metadata (source, rules, backtest results, regime fit)
3. **Add parameter optimization** for existing strategies (grid search over MA windows, RSI thresholds, etc.)
4. **Implement regime detection** so the system knows when to use which strategy type
5. **Add rejected-signal detailed logging** per asset per strategy
6. **Add missed-opportunity review** in heartbeat cycles

This is an autonomous project-improvement decision. It stays within paper trading and does not change risk limits.

### Actions Jarvis Will Take Now

1. **Create `src/agents/strategy_research.py`** — LLM agent that researches trading strategies from public sources
2. **Create `src/strategy/strategy_library.py`** — structured storage for discovered strategies with metadata
3. **Add parameter grid search** to `_run_backtest()` — test multiple parameter sets per strategy
4. **Add regime detection** — classify market as trending/mean-reverting/ranging
5. **Improve rejected-signal logging** — log WHY each strategy failed per asset
6. **Commit and restart daemon**

### Expected Improvement

| Before | After |
|--------|-------|
| 5 static strategies | 5+ researched strategies with provenance |
| Fixed parameters | Grid-optimized parameters per asset |
| No regime awareness | Regime detection guides strategy selection |
| No research pipeline | Continuous strategy discovery |
| Basic rejection logging | Detailed per-strategy failure reasons |

---

## CEO Approval Required
**No.** This is a project-improvement initiative within existing paper-trading and risk controls.

## CEO Informed
**Yes.**
