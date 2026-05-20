import sys, json, os
from datetime import datetime, timezone

# Read all decisions
all_decisions = []
for line in sys.stdin:
    try:
        d = json.loads(line.strip())
        all_decisions.append(d)
    except:
        pass

print("=" * 60)
print("CEO PROFITABILITY AUDIT")
print("=" * 60)

# Find actual executed buy orders
buys = []
sells = []
for d in all_decisions:
    od = d.get('order_details', {})
    if not od or not od.get('order_id'):
        continue
    
    side = od.get('side', '').lower()
    record = {
        'symbol': od.get('symbol', 'unknown'),
        'qty': float(od.get('qty', 0)),
        'price': float(od.get('price', 0)),
        'timestamp': d.get('timestamp', ''),
        'order_id': od.get('order_id'),
        'decision_id': d.get('decision_id', ''),
    }
    
    if side == 'buy':
        buys.append(record)
    elif side == 'sell':
        sells.append(record)

print(f"\nTOTAL EXECUTED BUYS: {len(buys)}")
print(f"TOTAL EXECUTED SELLS: {len(sells)}")

# Group by symbol
print("\n--- BUY ORDERS ---")
for b in buys:
    print(f"  {b['symbol']}: qty={b['qty']:.6f}, price=${b['price']:.2f}, time={b['timestamp'][:19]}")

print("\n--- SELL ORDERS ---")
for s in sells:
    print(f"  {s['symbol']}: qty={s['qty']:.6f}, price=${s['price']:.2f}, time={s['timestamp'][:19]}")

# Match buys to sells for PnL (naive FIFO)
print("\n--- MATCHED TRADES (FIFO) ---")
from collections import defaultdict
buy_queues = defaultdict(list)
for b in buys:
    buy_queues[b['symbol']].append(b.copy())

matched = []
for s in sells:
    symbol = s['symbol']
    if not buy_queues[symbol]:
        continue
    
    buy = buy_queues[symbol].pop(0)
    qty = min(buy['qty'], s['qty'])
    pnl = (s['price'] - buy['price']) * qty
    pnl_pct = (s['price'] - buy['price']) / buy['price'] * 100
    
    matched.append({
        'symbol': symbol,
        'buy_price': buy['price'],
        'sell_price': s['price'],
        'qty': qty,
        'pnl': pnl,
        'pnl_pct': pnl_pct,
        'buy_time': buy['timestamp'],
        'sell_time': s['timestamp'],
    })

print(f"Matched trades: {len(matched)}")
wins = [m for m in matched if m['pnl'] > 0]
losses = [m for m in matched if m['pnl'] <= 0]

print(f"Wins: {len(wins)}, Losses: {len(losses)}")
if wins:
    avg_win = sum(m['pnl'] for m in wins) / len(wins)
    avg_win_pct = sum(m['pnl_pct'] for m in wins) / len(wins)
    print(f"Avg win: ${avg_win:.2f} ({avg_win_pct:.2f}%)")
if losses:
    avg_loss = sum(m['pnl'] for m in losses) / len(losses)
    avg_loss_pct = sum(m['pnl_pct'] for m in losses) / len(losses)
    print(f"Avg loss: ${avg_loss:.2f} ({avg_loss_pct:.2f}%)")

total_pnl = sum(m['pnl'] for m in matched)
print(f"Total realized PnL: ${total_pnl:.2f}")

# By symbol
print("\n--- BY SYMBOL ---")
for sym in set(m['symbol'] for m in matched):
    sym_trades = [m for m in matched if m['symbol'] == sym]
    sym_pnl = sum(m['pnl'] for m in sym_trades)
    sym_wins = len([m for m in sym_trades if m['pnl'] > 0])
    print(f"  {sym}: {len(sym_trades)} trades, ${sym_pnl:+.2f}, {sym_wins}/{len(sym_trades)} wins")

print("\n" + "=" * 60)
