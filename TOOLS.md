# TOOLS.md - Local Notes

## Ollama Setup
- **Endpoint:** http://187.124.18.55:32768
- **Container:** ollama-on3l-ollama-1
- **Provider:** ollama
- **Auth:** api-key (key: "ollama")
- **Context Window:** 256000 tokens

## Available Models
| Model | Role | Agent |
|-------|------|-------|
| ollama/kimi-k2.6:cloud | Default, executive, technical analysis, thesis synthesis | Jarvis, Candles, Compass |
| ollama/deepseek-v4-pro:cloud | Deep architecture, long-context reasoning, COO, fundamental analysis, risk | Coda, Ledger, Shield |
| ollama/qwen3.5:cloud | Secondary reviewer, sentiment analysis, code generation | Blueprint, Pulse |
| ollama/glm-5.1:cloud | Backup |
| ollama/gemma4:31b-cloud | Backup |
| ollama/gpt-oss:120b-cloud | Backup |
| ollama/minimax-m2.7:cloud | Backup |

## Model Routing (Updated 2026-05-19)
- **Candles (Technical)**: deepseek-v4-pro:cloud — reliable, ~87s, handles OHLCV data
- **Ledger (Fundamental)**: deepseek-v4-pro:cloud — reliable, ~43s
- **Pulse (Sentiment)**: qwen3.5:cloud — moderate, ~77s
- **Shield (Risk)**: deepseek-v4-pro:cloud — reliable, ~40s
- **Compass (Thesis)**: deepseek-v4-pro:cloud — reliable, ~61s with 120s timeout
- **kimi-k2.6:cloud**: DEPRECATED — consistently times out at 180s regardless of data size

## Pipeline Runtime
- Full 5-agent sequential pipeline: ~5 minutes total
- Agent response times: 40-90s each
- Sequential execution required due to Ollama GPU contention
- **API Key:** PKFL22AHRJSJ5HWYTWFSVXGZ35
- **Secret:** [in .env]
- **Mode:** Paper only
- **Account:** $10,000
- **Assets:** BTC/USD, ETH/USD, SOL/USD
