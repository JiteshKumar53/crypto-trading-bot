# Dual Momentum Bot v1 — Strategy Specification

## Thesis
Absolute momentum (trend following) and relative momentum (cross-asset selection) both work in crypto. By combining them — only holding an asset if it has both positive absolute momentum AND is the best-performing asset — we filter out weak trends and concentrate in the strongest.

**Why this may have edge:**
- Absolute momentum: Assets that went up tend to keep going up (documented in equities, crypto)
- Relative momentum: The best-performing asset often continues outperforming
- Dual momentum combines both filters, reducing false signals
- Monthly rebalancing avoids overtrading

**Correlation to Trend Rider v5.6:** MEDIUM. Both are momentum-based but Dual Momentum rotates between assets while Trend Rider holds one asset. They may disagree during regime changes.

---

## Entry Rules

### Step 1: Absolute Momentum Filter
- Calculate 12-month (252-day) return for each asset
- Only consider assets with positive 12-month return

### Step 2: Relative Momentum Selection
- Rank eligible assets by 12-month return
- Select top 1 asset

### Step 3: Entry
- Buy top asset at month-end close
- Hold for 1 month (21 trading days)
- Re-evaluate at next month-end

---

## Exit Rules
- Rebalance monthly: sell current position, buy new top asset
- If no asset has positive 12-month return, exit to cash (hold nothing)
- No stop loss (momentum strategy with monthly rebalancing)

---

## Risk Parameters
- Risk per trade: 0.5% equity
- Max position size: $200
- Max concurrent positions: 1 (single asset at a time)
- No leverage

---

## Expected Trade Frequency
- ~12 trades per year (monthly rebalancing)
- Hold time: ~1 month per position

---

## Kill Conditions
- Dual momentum underperforms buy-and-hold over 2 years
- All assets show negative momentum simultaneously (bear market)
- Monthly turnover exceeds 50% (excessive trading)

---

## Data Requirements
- BTC/USD daily closes (2+ years)
- ETH/USD daily closes (2+ years)
- SOL/USD daily closes (optional, if available)

---

## Validation Gates
| Gate | Threshold |
|------|-----------|
| Profit factor | > 1.3 |
| Min trades | >= 20 |
| Max drawdown | < 20% |
| Walk-forward | 2/3 positive |
| Fee survival | Survives 1.5x fees |
| Turnover | < 50% monthly |

---

## Fee Model
- 0.10% per side
- 0.05% slippage
- Important: Monthly rebalancing means ~24 trades/year, so fees matter
