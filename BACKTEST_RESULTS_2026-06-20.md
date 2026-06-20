# Honest Backtest Results — After Fixing the Measurement Layer

**Date:** 2026-06-20
**Companion to:** `DEEP_ANALYSIS_2026-06-20.md`
**Run with:** `python3 crypto-trading-bot/scripts/run_honest_backtest.py`
**Data:** Binance 15m OHLCV, BTC/USDT + ETH/USDT, Jan 2024 → May 2026 (~82k bars each — the project's own on-disk data)
**Costs applied:** commission **0.10%/side** + slippage **0.05%/side** (previously: **zero**)
**Metrics:** corrected FIFO round-trip PnL + timeframe-aware annualization (previously: broken)

---

## What changed in the code

| File | Before | After |
|------|--------|-------|
| `src/backtest/metrics.py` | `win_rate` = % of fills that are sells; `profit_factor` = sell_notional ÷ buy_notional; PnL matching unimplemented (`pass`); Sharpe hardcoded to hourly (×4.9 inflation on daily) | Real FIFO buy→sell matching, PnL net of fees; correct win rate / profit factor / expectancy / max-consecutive-losses; annualization inferred from bar spacing |
| `src/backtest/backtest_engine.py` | `commission = 0.0` ("Alpaca is commission-free") | `commission = 0.001` realistic default; new honest fields on `BacktestResult` |
| `scripts/run_honest_backtest.py` | — | New cost-aware backtest harness + buy-and-hold benchmark |

All 22 tests that touch this code pass. (The other 28 failures in the suite are pre-existing and unrelated — broken risk-governor/leaderboard/pipeline modules.)

---

## Results

| Strategy | Asset | Total Return | CAGR | Sharpe | Max DD | Closed Trades | Win % | Profit Factor | Fees Paid |
|----------|-------|-------------:|-----:|-------:|-------:|--------------:|------:|--------------:|----------:|
| **EMA8/21 + RSI 15m** *(the "LIVE" strategy)* | BTC | **−99.55%** | −90.1% | −7.42 | 99.6% | 2002 | 20.0% | 0.51 | $7,405 |
| **SMA50 crossover 15m** *(SimpleSMA15m)* | BTC | **−99.98%** | −97.4% | −10.27 | 100% | 3122 | 11.9% | 0.44 | $7,364 |
| SMA50 crossover **daily** *(Trend Rider v5.x)* | BTC | +32.81% | +12.9% | 0.59 | 25.8% | 23 | 21.7% | 1.27 | $546 |
| Buy & Hold *(benchmark)* | BTC | **+86.37%** | +30.5% | 0.79 | 51.9% | — | — | — | $10 |
| **EMA8/21 + RSI 15m** | ETH | **−99.45%** | −89.2% | −5.64 | 99.5% | 1962 | 21.8% | 0.63 | $8,893 |
| **SMA50 crossover 15m** | ETH | **−99.94%** | −95.9% | −6.70 | 99.9% | 3058 | 13.5% | 0.54 | $8,572 |
| SMA50 crossover **daily** | ETH | +62.11% | +22.9% | 0.71 | 29.4% | 17 | 23.5% | 1.67 | $363 |
| Buy & Hold *(benchmark)* | ETH | +3.36% | +1.4% | 0.36 | 65.1% | — | — | — | $10 |

(Starting capital $10,000. Full machine-readable output in `freqtrade_data/honest_backtest_results.json`.)

---

## What this proves

1. **The shipped 15m strategies are catastrophic, and fees are the murder weapon.** The EMA/RSI strategy that `MEMORY.md` and `TEAM_ACTIVITY_REPORT.md` describe as **LIVE** loses essentially the entire account (−99.5%). It paid **$7,400–$8,900 in fees on a $10,000 account** — it churned the balance away in commissions. With the old zero-fee engine this damage was invisible. This is the direct, quantified reason the bot was unprofitable.

2. **Low win rate + over-trading + real costs = guaranteed loss.** 11–22% win rates with ~2,000–3,100 round trips and PF < 0.65. No risk control survives that turnover at 0.15%/round-trip cost.

3. **The only positive strategy (daily SMA) still doesn't beat buying and holding BTC.** Daily SMA on BTC made +32.8% while simply holding BTC made +86.4%. The old broken metrics reported this strategy at PF 1.58 (BTC) / 4.89 (ETH); corrected, it's PF 1.27 / 1.67 — the inflated "edge" was bull-market beta, exactly as the analysis predicted.

4. **Where the daily strategy *did* add value, it was risk reduction, not return.** On ETH it beat buy-and-hold (+62% vs +3%) and roughly halved drawdown (29% vs 65%) by sitting out downtrends. That is the one genuinely defensible behavior in the whole system — trend-following as a drawdown filter, not an alpha source.

---

## Verdict

- **Do not paper- or live-trade any 15m strategy in this repo.** They are negative-expectancy after realistic costs by a wide margin.
- **The daily SMA strategy is at best a defensive overlay**, not a profit engine, and loses to HODL on BTC. It does not justify the 29k-LOC machine built around it.
- The corrected measurement layer is now the project's most valuable asset: any future strategy must clear **buy-and-hold, net of these fees**, on this harness before it goes anywhere near capital.

## Reproduce

```bash
cd crypto-trading-bot
pip install pandas numpy pyarrow
python3 scripts/run_honest_backtest.py
```
