#!/usr/bin/env python3
import sys
sys.path.insert(0, '/data/.openclaw/workspace/crypto-trading-bot/src')
from agents.agent_runner import AgentRunner
from data.data_fetcher import DataFetcher
from broker.alpaca_client import AlpacaPaperClient
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')

print('=== Fetching data ===')
client = AlpacaPaperClient()
fetcher = DataFetcher(client)
df = fetcher.fetch_hourly_bars('BTC/USD', limit=168)
price = fetcher.get_latest_price('BTC/USD')

# Build OHLCV summary — use last 20 bars for technical agent (168 is too much for 1T model)
summary = "Latest 20 hourly bars (most recent first):\n"
for i in range(min(20, len(df))):
    row = df.iloc[-(i+1)]
    ts = str(df.index.get_level_values(1)[-(i+1)]) if hasattr(df.index, 'get_level_values') else str(df.index[-(i+1)])
    summary += f"  {ts}: O={row['open']:.2f} H={row['high']:.2f} L={row['low']:.2f} C={row['close']:.2f} V={row['volume']:.2f}\n"

summary += f"""
Weekly stats:
  Range: ${df['low'].min():,.2f} - ${df['high'].max():,.2f}
  Avg volume: {df['volume'].mean():,.0f}
  Total volume: {df['volume'].sum():,.0f}
  Current close: ${df['close'].iloc[-1]:,.2f}
"""

print(summary[:500])
print('...')

print('\n=== RUNNING AGENT PIPELINE ===')
runner = AgentRunner()
results = runner.run_pipeline(
    asset='BTC/USD',
    current_price=price,
    portfolio_value=10000,
    current_position_value=994,
    ohlcv_summary=summary,
)

print('\n=== RESULTS ===')
for key in ['technical', 'fundamental', 'sentiment', 'risk', 'thesis']:
    rec = results[key]
    print(f'{key.upper()}: {rec.recommendation} (confidence: {rec.confidence}, cached: {rec.cached})')
    if rec.warnings:
        print(f'  Warning: {rec.warnings[:150]}')

print(f'\nErrors: {results["errors"]}')
print(f'All succeeded: {results["all_agents_succeeded"]}')
