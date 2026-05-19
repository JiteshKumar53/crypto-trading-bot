#!/usr/bin/env python3
import requests

headers = {
    'APCA-API-KEY-ID': 'PKFL22AHRJSJ5HWYTWFSVXGZ35',
    'APCA-API-SECRET-KEY': 'HoCrCuzBAmVvn1LftSPxPczo4U5uGu9efjzssawneFmd'
}

resp = requests.get('https://paper-api.alpaca.markets/v2/positions', headers=headers)
positions = resp.json()
print('=== CURRENT POSITIONS ===')
for p in positions:
    entry = float(p['avg_entry_price'])
    current = float(p['current_price'])
    pct = (current - entry) / entry * 100
    print(f"  {p['symbol']}: entry=${entry:.2f} current=${current:.2f} change={pct:+.2f}% unrealized=${float(p['unrealized_pl']):,.2f}")

resp = requests.get('https://paper-api.alpaca.markets/v2/orders?status=all&limit=100', headers=headers)
orders = resp.json()
print(f"\n=== ALL ORDERS: {len(orders)} ===")
for o in orders:
    print(f"  {o['symbol']}: {o['side']} qty={o['qty']} filled={o.get('filled_qty','0')} @ ${o.get('filled_avg_price','N/A')} status={o['status']}")

filled = [o for o in orders if o['status'] == 'filled']
print(f"\n=== FILLED ORDERS: {len(filled)} ===")
for o in filled:
    print(f"  {o['symbol']}: {o['side']} qty={o['qty']} @ ${o.get('filled_avg_price','N/A')} on {o['created_at']}")

sells = [o for o in filled if o['side'] == 'sell']
print(f"\n=== SELL ORDERS: {len(sells)} ===")
for o in sells:
    print(f"  {o['symbol']}: {o['side']} qty={o['qty']} @ ${o.get('filled_avg_price','N/A')}")

resp = requests.get('https://paper-api.alpaca.markets/v2/account', headers=headers)
a = resp.json()
print(f"\n=== ACCOUNT ===")
print(f"  Portfolio: ${float(a['portfolio_value']):,.2f}")
print(f"  Cash: ${float(a['cash']):,.2f}")
