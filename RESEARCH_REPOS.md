# Research — GitHub Repos & Tools Reviewed

Reference list of every GitHub project discussed while analyzing how to improve
this project (2026-06-20). Verdicts reflect the deep analysis: the project's
binding constraint is **validated edge**, not more infrastructure.

## This project
- **JiteshKumar53/crypto-trading-bot** — branch `claude/dazzling-heisenberg-l34pyv`.

## "AutoHedge" family — VERDICT: skip
Same multi-agent shape as this bot, and crucially **no backtesting/validation** —
which is the exact gap that made this project unprofitable.

| Repo | Stars | Notes |
|------|------:|-------|
| The-Swarm-Corporation/AutoHedge | ~3.5k | Autonomous AI hedge fund, Swarms framework, Solana/Jupiter. Evaluated in depth → not useful. |
| charlesaurav13/AutoHedge | ~8 | Crypto fork (DeepSeek + Swarms, BTC/SOL/ETH). Less mature. |
| kgeoffrey/AutoHedge.jl | ~81 | Julia, options hedging/backtesting. |
| mohin-io/Decentralized-Autonomous-Hedge-Fund-AI-DAO | ~4 | RL + blockchain concept. |
| whitebaby/bitcoin-litecoin-hedge-autotrade | ~3 | Old JS bot. |
| tulasacra/AutoHedger | ~1 | C#. |
| andrea53013/Autonomus-Quant-HedgeFund | ~1 | — |
| RAFAELDCOELHO/autonomous-hedge-fund | ~1 | Multi-agent LLM (Kronos, FinGPT, TradingAgents). |
| meerahussain733/autonomous-ticket-arbitrage-hedge-fund | ~1 | — |
| jeaniususa/Citadail-Autonomous-Hedge-Fund-DAO | ~1 | — |

## NautilusTrader — VERDICT: adopt later, not now
Production-grade infra that cures the architectural root cause (backtest↔live
parity + realistic costs), but **no Alpaca** support and solves *infrastructure,
not edge*. Port to it only after 2–3 strategies pass the validation gate.

| Repo | Stars | Notes |
|------|------:|-------|
| nautechsystems/nautilus_trader | ~24k | Rust core / Python API, deterministic event-driven, backtest↔live parity, realistic fees/slippage. Crypto venues: Binance, Bybit, Coinbase, Kraken, OKX, dYdX, Hyperliquid + IBKR. LGPL-3.0. |
| woung717/nautilus-trader-cython-stubs | ~50 | Type stubs. |
| stefansimik/nautilus_trader_examples | ~48 | Examples (archived). |

## Tools / libraries recommended
- **freqtrade/freqtrade** — already in this repo; the one trustworthy backtester. Lean into it.
- **polakowo/vectorbt** — fast vectorized backtesting.
- **kernc/backtesting.py** — lightweight backtest engine.
- **twopirllc/pandas-ta**, **bukosabino/ta** — TA indicator libs. NOTE: both failed to build on numpy 2.x in this environment; the tournament uses pandas `ewm`/`rolling` instead.
- **TauricResearch/TradingAgents** — rigorous multi-agent LLM trading framework (the "done right" alternative to AutoHedge).

## Bottom line
No external repo solves the real problem (finding/validating edge). The most
useful "upgrades" were proven *measurement* tools (freqtrade) and the
in-repo validation gate + tournament built this session. NautilusTrader is the
right production home — but later, once edge is proven.
