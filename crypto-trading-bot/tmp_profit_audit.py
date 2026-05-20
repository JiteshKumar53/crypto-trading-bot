import sys, os
sys.path.insert(0, 'src')
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetOrdersRequest
from alpaca.trading.enums import QueryOrderStatus

client = TradingClient(
    os.getenv('ALPACA_API_KEY'),
    os.getenv('ALPACA_SECRET_KEY'),
    paper=True,
)

# Get ALL orders
req = GetOrdersRequest(status=QueryOrderStatus.ALL)
orders = client.get_orders(filter=req)

buys = []
sells = []
for o in orders:
    side = str(o.side)
    symbol = o.symbol
    qty = float(o.qty) if o.qty else 0
    filled = float(o.filled_qty) if o.filled_qty else 0
    price = float(o.filled_avg_price) if o.filled_avg_price else 0
    status = str(o.status)
    ts = o.created_at.isoformat() if o.created_at else ''
    
    if status.lower() == 'filled':
        if side.lower() == 'buy':
            buys.append({'symbol': symbol, 'qty': filled, 'price': price, 'time': ts})
        elif side.lower() == 'sell':
            sells.append({'symbol': symbol, 'qty': filled, 'price': price, 'time': ts})

print("=== PROFITABILITY AUDIT ===")
print("Total buys:", len(buys))
print("Total sells:", len(sells))

# Match FIFO
from collections import defaultdict
bq = defaultdict(list)
for b in buys:
    bq[b['symbol']].append(b)

matched = []
for s in sells:
    sym = s['symbol']
    if not bq[sym]:
        continue
    b = bq[sym].pop(0)
    pnl = (s['price'] - b['price']) * s['qty']
    pnl_pct = (s['price'] - b['price']) / b['price'] * 100 if b['price'] > 0 else 0
    matched.append({'symbol': sym, 'buy': b['price'], 'sell': s['price'], 'qty': s['qty'], 'pnl': pnl, 'pnl_pct': pnl_pct})

print("\nMatched trades:", len(matched))
wins = [m for m in matched if m['pnl'] > 0]
losses = [m for m in matched if m['pnl'] <= 0]
print("Wins:", len(wins), "Losses:", len(losses))

if wins:
    aw = sum(m['pnl'] for m in wins) / len(wins)
    print("Avg win: ${:.2f}".format(aw))
if losses:
    al = sum(m['pnl'] for m in losses) / len(losses)
    print("Avg loss: ${:.2f}".format(al))

total_pnl = sum(m['pnl'] for m in matched)
print("Total realized PnL: ${:.2f}".format(total_pnl))

for m in matched:
    s = 'WIN' if m['pnl'] > 0 else 'LOSS'
    print("  {}: buy ${:.2f} -> sell ${:.2f}, qty={:.4f}, PnL=${:+.2f} ({:+.2f}%) [{}]".format(
        m['symbol'], m['buy'], m['sell'], m['qty'], m['pnl'], m['pnl_pct'], s))

print("\n=== TARGET MATH ===")
print("Target: $30-50/day on $10,000")
print("Required daily return: {:.2f}% - {:.2f}%".format(30/10000*100, 50/10000*100))

if matched:
    avg_trade = total_pnl / len(matched)
    print("Avg PnL/trade: ${:.2f}".format(avg_trade))
    if avg_trade != 0:
        print("Trades/day for $30: {:.1f}".format(30/abs(avg_trade)))
        print("Trades/day for $50: {:.1f}".format(50/abs(avg_trade)))
    
    win_rate = len(wins)/len(matched)
    if wins and losses:
        wlr = (sum(m['pnl'] for m in wins)/len(wins)) / abs(sum(m['pnl'] for m in losses)/len(losses))
        print("Win rate: {:.1f}%".format(win_rate*100))
        print("Win/loss ratio: {:.2f}".format(wlr))
        
        avg_win = sum(m['pnl'] for m in wins)/len(wins)
        avg_loss = abs(sum(m['pnl'] for m in losses)/len(losses))
        ev = (win_rate * avg_win) - ((1-win_rate) * avg_loss)
        print("Expected value: ${:.2f}/trade".format(ev))
        
        if wlr > 0:
            kelly = win_rate - ((1-win_rate)/wlr)
            print("Kelly bet size: {:.1f}%".format(kelly*100))
