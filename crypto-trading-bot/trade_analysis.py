#!/usr/bin/env python3
"""Trade frequency and exit performance analysis for CEO review."""

import requests
import json
from datetime import datetime, timezone

api_key = 'PKFL22AHRJSJ5HWYTWFSVXGZ35'
secret_key = 'HoCrCuzBAmVvn1LftSPxPczo4U5uGu9efjzssawneFmd'

headers = {'APCA-API-KEY-ID': api_key, 'APCA-API-SECRET-KEY': secret_key}

# Get all orders
orders = requests.get('https://paper-api.alpaca.markets/v2/orders?status=all&limit=100', headers=headers).json()
print('=== ALL TRADES ===')
for o in orders:
    print(f"  {o['symbol']}: {o['side']} qty={o['qty']} @ ${o.get('filled_avg_price','N/A')} status={o['status']} {o['created_at']}")

# Analyze by date
trades_by_day = {}
for o in orders:
    if o['status'] == 'filled':
        day = o['created_at'][:10]
        if day not in trades_by_day:
            trades_by_day[day] = []
        trades_by_day[day].append(o)

print(f'\n=== TRADES BY DAY ===')
for day, day_trades in sorted(trades_by_day.items()):
    buys = [t for t in day_trades if t['side'] == 'buy']
    sells = [t for t in day_trades if t['side'] == 'sell']
    print(f"  {day}: {len(day_trades)} total ({len(buys)} buys, {len(sells)} sells)")

# Get positions
positions = requests.get('https://paper-api.alpaca.markets/v2/positions', headers=headers).json()
print(f'\n=== OPEN POSITIONS: {len(positions)} ===')
for p in positions:
    entry = float(p['avg_entry_price'])
    current = float(p['current_price'])
    pct = (current - entry) / entry * 100
    print(f"  {p['symbol']}: entry=${entry:.2f} current=${current:.2f} change={pct:+.2f}% unrealized=${float(p['unrealized_pl']):,.2f}")

# Account
account = requests.get('https://paper-api.alpaca.markets/v2/account', headers=headers).json()
print(f"\n=== ACCOUNT ===")
print(f"  Portfolio: ${float(account['portfolio_value']):,.2f}")
print(f"  Cash: ${float(account['cash']):,.2f}")

# Risk limits
print(f"\n=== RISK GOVERNOR LIMITS ===")
print("  Max daily loss: 2%")
print("  Max open positions: 3")
print("  Max allocation per asset: 10%")
print("  Max total exposure: 30%")
print("  Max consecutive losses: 3")
print("  Cooldown after kill switch: 24h")
print("  No leverage")

# Fee estimate
print(f"\n=== FEE IMPACT ===")
print("  Alpaca crypto fees: 0.15% maker, 0.25% taker")
print("  Round-trip (buy+sell): ~0.40% - 0.50%")
print("  Per $500 trade: ~$2.00 - $2.50")
print("  Per $1000 trade: ~$4.00 - $5.00")

# Trade frequency analysis
print(f"\n=== TRADE FREQUENCY ANALYSIS ===")
total_filled = len([o for o in orders if o['status'] == 'filled'])
print(f"  Total filled orders: {total_filled}")
print(f"  Days active: {len(trades_by_day)}")
if trades_by_day:
    avg_per_day = total_filled / len(trades_by_day)
    print(f"  Average trades per day: {avg_per_day:.1f}")
    max_per_day = max(len(t) for t in trades_by_day.values())
    print(f"  Max trades in one day: {max_per_day}")

print(f"\n=== RECOMMENDATIONS ===")
print("  Safe daily limit: 3-6 trades (1-2 per asset)")
print("  Current: ~2-3 trades/day average")
print("  Overtrading threshold: >10 trades/day")
print("  Fee breakeven: need >0.5% profit per trade to cover fees")
