# Lessons Learned

## Never delete — only append.

1. **5m timeframe has no retail edge in crypto after fees.**
   17 strategies tested. All failed at 5m. Fees and noise eat any edge.

2. **Simple beats complex.**
   50-day SMA outperformed every RSI+volume+ATR+MACD combination.
   12 indicators combined = worse than 1 SMA.

3. **Daily timeframe removes noise that killed 5m strategies.**
   Same logic, different timeframe = pass vs fail.

4. **Data source must match execution venue exactly.**
   Yahoo vs Alpaca: 0.03-0.54% variance. Crossover points shifted.
   Single source eliminates reconciliation risk.

5. **Hardcoded parameters are silent killers.**
   `data_fetcher.py` hardcoded to 5m despite accepting `timeframe` param.
   Cost: days of debugging, 17 failed strategies.

6. **Timezone handling breaks reconciliation silently.**
   `reconcile_alpaca_yahoo.py` used `dt.tz_localize(None)` causing 1-day offset.
   Cost: entire day of false mismatch reports.

7. **A daemon that dies when session ends is not a daemon.**
   First version: only runs while chat open.
   Real daemon: cron + heartbeat + error recovery + duplicate detection.

8. **17 honest rejections are worth more than 1 fake pass.**
   Every rejected strategy taught something real.
   Fake pass = blown account. Honest rejection = saved capital.

9. **Fee sensitivity is not optional.**
   A strategy with PF=1.58 at base fees can die at 2x fees.
   Always test fee doubling/tripling before considering viable.

10. **Unit tests must run before the first trade, not after.**
    Testing after deployment is not testing — it's damage control.
