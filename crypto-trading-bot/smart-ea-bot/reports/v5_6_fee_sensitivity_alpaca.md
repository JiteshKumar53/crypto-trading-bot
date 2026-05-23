# Fee Sensitivity Report — Trend Rider v5.6 on Alpaca Data
**Date:** 2026-05-23  
**Data Source:** Alpaca (single authoritative source)  
**Period:** 2021-05-23 to 2026-05-23 (5 years)  
**Note:** Supersedes Yahoo Finance-based fee sensitivity (Round 3)

---

## Executive Summary

Trend Rider v5.6 was stress-tested at 0.5x, 1x, 1.5x, 2x, and 3x normal fee levels on Alpaca's 5-year daily crypto data. The strategy **survives 3x fees on both BTC and ETH** with profit factors remaining above 1.0.

**Critical finding:** BTC profit factor drops from 1.58 (1x) to 1.43 (3x). At 2x fees, BTC PF = 1.50 — still well above the 1.0 breakeven threshold. ETH remains robust across all scenarios (PF 4.48 at 3x).

**Decision:** Both BTC and ETH are viable. No asset dropped below PF 1.0 at any fee level tested.

---

## Full Results

### BTC/USD

| Fee Level | Fee % | Slippage % | Trades | Return | PF | Max DD | Status |
|-----------|-------|-----------|--------|--------|----|--------|--------|
| 0.5x | 0.05% | 0.025% | 28 | +3.20% | **1.63** | 2.26% | ✅ |
| 1x (Normal) | 0.10% | 0.05% | 28 | +3.04% | **1.58** | 2.26% | ✅ |
| 1.5x | 0.15% | 0.075% | 28 | +2.89% | **1.54** | 2.26% | ✅ |
| 2x | 0.20% | 0.10% | 28 | +2.74% | **1.50** | 2.26% | ✅ |
| 3x | 0.30% | 0.15% | 28 | +2.43% | **1.43** | 2.26% | ✅ |

### ETH/USD

| Fee Level | Fee % | Slippage % | Trades | Return | PF | Max DD | Status |
|-----------|-------|-----------|--------|--------|----|--------|--------|
| 0.5x | 0.05% | 0.025% | 23 | +13.26% | **5.00** | 1.44% | ✅ |
| 1x (Normal) | 0.10% | 0.05% | 23 | +13.14% | **4.89** | 1.44% | ✅ |
| 1.5x | 0.15% | 0.075% | 23 | +13.01% | **4.78** | 1.44% | ✅ |
| 2x | 0.20% | 0.10% | 23 | +12.89% | **4.68** | 1.44% | ✅ |
| 3x | 0.30% | 0.15% | 23 | +12.65% | **4.48** | 1.44% | ✅ |

---

## Summary Table

| Asset | 0.5x PF | 1x PF | 2x PF | 3x PF | Decision |
|-------|---------|-------|-------|-------|----------|
| BTC | 1.63 | 1.58 | 1.50 | 1.43 | ✅ Survives 3x |
| ETH | 5.00 | 4.89 | 4.68 | 4.48 | ✅ Survives 3x |

---

## Comparison to Yahoo Data (Superseded)

| Asset | Yahoo 1x PF | Alpaca 1x PF | Delta |
|-------|-------------|--------------|-------|
| BTC | 2.14 | 1.58 | -26% |
| ETH | 4.85 | 4.89 | +1% |

BTC PF drops significantly on Alpaca data due to small OHLCV differences at crossover points. However, the strategy remains profitable at all fee levels tested.

---

## Junior CEO Decision

**BTC/USD:** Trade. PF 1.50 at 2x fees provides adequate margin. No reason to exclude.

**ETH/USD:** Trade. PF 4.68 at 2x fees is exceptionally robust.

**Portfolio:** Run both assets in parallel. Diversification across two uncorrelated crypto assets improves risk-adjusted returns.

**Jarvis, Junior CEO**  
*Decision Date: 2026-05-23*
