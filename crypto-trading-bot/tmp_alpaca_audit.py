import sys
sys.path.insert(0, 'src')
from broker.alpaca_client import AlpacaPaperClient

client = AlpacaPaperClient()

print("=== ALPACA ORDER HISTORY ===")
orders = client.trading_client.get_orders()
print("Total orders:", len(orders))

buys = []
sells = []

for order in orders:
    side = str(order.side)
    symbol = order.symbol
    qty = float(order.qty) if order.qty else 0
    filled_qty = float(order.filled_qty) if order.filled_qty else 0
    filled_avg_price = float(order.filled_avg_price) if order.filled_avg_price else 0
    status = str(order.status)
    created_at = order.created_at.isoformat() if order.created_at else ''
    
    msg = "Order: {} {} qty={} filled={} @ ${:.2f} status={} time={}"
    print(msg.format(symbol, side, qty, filled_qty, filled_avg_price, status, created_at[:19]))
    
    if side.lower() == 'buy' and status.lower() == 'filled':
        buys.append({'symbol': symbol, 'qty': filled_qty, 'price': filled_avg_price, 'time': created_at})
    elif side.lower() == 'sell' and status.lower() == 'filled':
        sells.append({'symbol': symbol, 'qty': filled_qty, 'price': filled_avg_price, 'time': created_at})

print("\nFilled buys:", len(buys))
print("Filled sells:", len(sells))

# Match FIFO
from collections import defaultdict
buy_queues = defaultdict(list)
for b in buys:
    buy_queues[b['symbol']].append(b)

matched = []
for s in sells:
    symbol = s['symbol']
    if not buy_queues[symbol]:
        continue
    
    buy = buy_queues[symbol].pop(0)
    pnl = (s['price'] - buy['price']) * s['qty']
    pnl_pct = (s['price'] - buy['price']) / buy['price'] * 100 if buy['price'] > 0 else 0
    
    matched.append({
        'symbol': symbol,
        'buy_price': buy['price'],
        'sell_price': s['price'],
        'qty': s['qty'],
        'pnl': pnl,
        'pnl_pct': pnl_pct,
        'buy_time': buy['time'],
        'sell_time': s['time'],
    })

print("\nMatched trades:", len(matched))
wins = [m for m in matched if m['pnl'] > 0]
losses = [m for m in matched if m['pnl'] <= 0]

print("Wins:", len(wins), "Losses:", len(losses))
if wins:
    avg_win = sum(m['pnl'] for m in wins) / len(wins)
    avg_win_pct = sum(m['pnl_pct'] for m in wins) / len(wins)
    print("Avg win: ${:.2f} ({:.2f}%)".format(avg_win, avg_win_pct))
if losses:
    avg_loss = sum(m['pnl'] for m in losses) / len(losses)
    avg_loss_pct = sum(m['pnl_pct'] for m in losses) / len(losses)
    print("Avg loss: ${:.2f} ({:.2f}%)".format(avg_loss, avg_loss_pct))

total_pnl = sum(m['pnl'] for m in matched)
print("\nTotal realized PnL: ${:.2f}".format(total_pnl))

print("\n--- ALL MATCHED TRADES ---")
for m in matched:
    status = "WIN" if m['pnl'] > 0 else "LOSS"
    print("  {}: buy ${:.2f} -> sell ${:.2f}, qty={:.6f}, PnL=${:+.2f} ({:+.2f}%) [{}]".format(
        m['symbol'], m['buy_price'], m['sell_price'], m['qty'], m['pnl'], m['pnl_pct'], status))

print("\n--- BY SYMBOL ---")
for sym in set(m['symbol'] for m in matched):
    sym_trades = [m for m in matched if m['symbol'] == sym]
    sym_pnl = sum(m['pnl'] for m in sym_trades)
    sym_wins = len([m for m in sym_trades if m['pnl'] > 0])
    print("  {}: {} trades, ${:+.2f}, {}/{} wins".format(sym, len(sym_trades), sym_pnl, sym_wins, len(sym_trades)))

print("\n=== PROFITABILITY TARGET MATH ===")
print("Target: $30-50/day")
print("Current account: ~$10,000")
print("Required daily return: {:.2f}% - {:.2f}%".format(30/10000*100, 50/10000*100))

if matched:
    avg_trade_pnl = total_pnl / len(matched)
    print("Current avg PnL per trade: ${:.2f}".format(avg_trade_pnl))
    
    trades_needed_30 = 30 / abs(avg_trade_pnl) if avg_trade_pnl != 0 else float('inf')
    trades_needed_50 = 50 / abs(avg_trade_pnl) if avg_trade_pnl != 0 else float('inf')
    print("Trades needed/day for $30: {:.1f}".format(trades_needed_30))
    print("Trades needed/day for $50: {:.1f}".format(trades_needed_50))
    
    win_rate = len(wins) / len(matched) if matched else 0
    if wins and losses:
        win_loss_ratio = avg_win / abs(avg_loss)
        print("Win rate: {:.1f}%".format(win_rate*100))
        print("Win/loss ratio: {:.2f}".format(win_loss_ratio))
        
        ev = (win_rate * avg_win) - ((1 - win_rate) * abs(avg_loss))
        print("Expected value per trade: ${:.2f}".format(ev))
        
        if avg_loss != 0:
            kelly = win_rate - ((1 - win_rate) / win_loss_ratio)
            print("Kelly criterion (optimal bet size): {:.1f}% of bankroll".format(kelly*100))
