# Weekly Ratio Bot v1 — Strategy Specification

## Thesis
The ETH/BTC ratio exhibits medium-term trend persistence on weekly timeframes. When ETH is outperforming BTC (ratio rising), the trend tends to continue due to sector rotation and momentum in crypto narratives. This bot captures relative momentum between the two largest crypto assets.

**Why this may have edge:**
- Crypto sector rotation is real (DeFi summer, NFT season, etc.)
- ETH and BTC have different use cases and investor bases
- Relative momentum is a documented phenomenon in asset pricing
- Weekly timeframe filters noise while capturing multi-week rotations

**Correlation to Trend Rider v5.6:** LOW. Trend Rider trades absolute price direction. Weekly Ratio trades relative performance. They may occasionally both be long ETH, but signals are driven by different factors.

---

## Entry Rules

### LONG (ETH outperforming BTC)
- Weekly ETH/BTC ratio closes above 20-week SMA
- Previous week's ratio was at or below 20-week SMA
- Stop loss: 20-week SMA * 0.95

### SHORT (BTC outperforming ETH)
- Weekly ETH/BTC ratio closes below 20-week SMA
- Previous week's ratio was at or above 20-week SMA
- Stop loss: 20-week SMA * 1.05

---

## Exit Rules
- Hold until opposite crossover
- No trailing stop (trend following)
- Max hold: 52 weeks (1 year)

---

## Risk Parameters
- Risk per trade: 0.5% equity
- Max position size: $200
- Max concurrent positions: 1 (this is a single-pair strategy)

---

## Expected Trade Frequency
- ~2-4 trades per year
- Hold time: 2-6 months per trade

---

## Kill Conditions
- 3 consecutive losing trades
- Drawdown > 15% from peak
- No signal for 12 months

---

## Data Requirements
- ETH/USD weekly closes
- BTC/USD weekly closes (same timestamps)
- Calculate ratio = ETH close / BTC close
- Minimum 2 years of weekly data

---

## Validation Gates
| Gate | Threshold |
|------|-----------|
| Profit factor | > 1.3 |
| Min trades | >= 10 |
| Max drawdown | < 20% |
| Walk-forward | 2/3 positive |
| Fee survival | Survives 1.5x fees |

---

## Fee Model
- 0.10% per side
- 0.05% slippage
