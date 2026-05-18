# Project Architecture Proposal

**Proposed by:** Chief Architect (Agent Blueprint)  
**Reviewed by:** Jarvis  
**Status:** Approved by Jarvis  
**Date:** 2026-05-18

## Philosophy
- Modular, testable, production-quality.
- Deterministic risk controls are independent and code-based.
- AI agents provide recommendations, not final execution.
- Memory is persistent, auditable, and versioned.
- Paper trading only until CEO explicitly approves live trading.

## Directory Structure

```
/data/.openclaw/workspace/crypto-trading-bot/
├── config/
│   ├── alpaca.yaml              # Alpaca API config (paper trading)
│   ├── risk_limits.yaml         # Risk governor limits
│   └── assets.yaml              # Traded crypto assets
├── src/
│   ├── __init__.py
│   ├── main.py                  # Entry point
│   ├── orchestrator.py          # Trading decision pipeline orchestrator
│   ├── risk_governor.py         # Deterministic Risk Governor (code-based)
│   ├── broker/
│   │   ├── __init__.py
│   │   └── alpaca_client.py     # Alpaca API wrapper (paper only)
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base_agent.py        # Base class for recommendation agents
│   │   ├── technical_analysis.py    # Market Structure + Technical Agent
│   │   ├── fundamental_analysis.py  # Crypto Fundamental + On-chain Agent
│   │   ├── sentiment_analysis.py    # Sentiment + Narrative Agent
│   │   ├── risk_assessment.py       # Portfolio Risk + Execution Risk Agent
│   │   └── thesis_synthesis.py      # Investment Thesis + Strategy Synthesis Agent
│   ├── strategy/
│   │   ├── __init__.py
│   │   ├── strategy_engine.py       # Converts thesis to testable strategy
│   │   └── strategies/
│   │       └── __init__.py
│   ├── backtest/
│   │   ├── __init__.py
│   │   ├── backtest_engine.py
│   │   └── metrics.py
│   ├── data/
│   │   ├── __init__.py
│   │   ├── data_fetcher.py        # Market data retrieval
│   │   └── validators.py          # Data quality checks
│   ├── memory/
│   │   ├── __init__.py
│   │   ├── decision_log.py        # Decision audit trail
│   │   ├── mistake_log.py         # Recorded mistakes and lessons
│   │   └── experiment_log.py        # Self-evolution experiments
│   ├── qa/
│   │   ├── __init__.py
│   │   └── validators.py          # No-lookahead, data leakage checks
│   └── security/
│       ├── __init__.py
│       └── secrets_manager.py     # API key management
├── tests/
│   ├── __init__.py
│   ├── test_risk_governor.py
│   ├── test_alpaca_client.py
│   ├── test_data_fetcher.py
│   └── test_strategies.py
├── notebooks/
│   └── (exploratory analysis)
├── docs/
│   ├── architecture.md
│   ├── trading_decision_process.md
│   ├── self_evolution_policy.md
│   └── agent_prompts/
├── logs/
│   └── (runtime logs, trade logs, decision logs)
└── requirements.txt
```

## Core Modules

### 1. Risk Governor (`src/risk_governor.py`)
- Pure Python, no LLM dependency.
- Validates every order against deterministic rules.
- Configurable via `config/risk_limits.yaml`.
- Can trigger kill switch.
- Unit tested with 100% path coverage.

### 2. Broker Client (`src/broker/alpaca_client.py`)
- Wraps Alpaca API.
- Forces paper mode. Blocks live trading.
- Validates paper mode before every order.

### 3. Orchestrator (`src/orchestrator.py`)
- Runs the decision pipeline end-to-end.
- Collects recommendations from 5 agents.
- Passes to Risk Governor.
- Logs every step.
- CEO-reserved decisions blocked unless explicitly approved.

### 4. Memory System (`src/memory/`)
- Decision logs with timestamps, agents involved, recommendations, final decision.
- Mistake logs with root cause, fix, prevention.
- Experiment logs with hypothesis, test, result, keep/revert.

### 5. Backtesting (`src/backtest/`)
- Event-driven or vectorized backtest engine.
- Metrics: return, Sharpe, Sortino, max drawdown, Calmar, win rate, profit factor.
- Walk-forward validation.
- Fee and slippage simulation.

## Technology Stack
- **Language:** Python 3.13+
- **Broker API:** Alpaca Markets (paper trading)
- **Data:** Alpaca crypto data + optional external feeds
- **AI Agents:** OpenClaw sessions with assigned models
- **Testing:** pytest
- **Linting:** ruff, mypy
- **Secrets:** Environment variables + .env (gitignored)

## Data Flow
```
Market Data → Data Validation
→ Technical Agent → Fundamental Agent → Sentiment Agent → Risk Agent
→ Thesis Synthesis Agent
→ Strategy Engineering
→ Backtesting
→ QA Validation
→ Chief Architect Review (technical)
→ COO Workflow Confirmation
→ Jarvis Final Decision
→ CEO Informed
→ Risk Governor Check
→ Alpaca Paper Execution
→ Reconciliation
→ Memory Update
→ Self-Evolution Loop
```

## Security
- API keys in environment variables only.
- `.env` file gitignored.
- No secrets in logs or memory.
- Alpaca paper mode enforced in code.

## CEO-Reserved Gates
The following are hard-coded in orchestrator and require explicit CEO approval:
1. Switching from paper to live trading.
2. Increasing live-trading risk limits.
3. Disabling deterministic risk controls.
4. Sending secrets outside the system.
5. Deleting production data.
6. Any legal/financial irreversible action.
