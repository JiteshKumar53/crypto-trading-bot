import sys
sys.path.insert(0, 'src')
from alpaca.trading.client import TradingClient
import os

client = TradingClient(
    os.getenv('ALPACA_API_KEY'),
    os.getenv('ALPACA_SECRET_KEY'),
    paper=True,
)

print("=== ALL ORDERS (any status) ===")
# Get all orders including closed
orders = client.get_orders(filter=None)
print("Total orders:", len(orders))

for order in orders[:20]:
    print("{} {} {} @ {} status={} filled={} id={}".format(
        order.created_at,
        order.symbol,
        order.side,
        order.filled_avg_price or order.limit_price or 'N/A',
        order.status,
        order.filled_qty,
        order.id,
    ))

# Get positions
print("\n=== CURRENT POSITIONS ===")
positions = client.get_all_positions()
for p in positions:
    print("{}: qty={}, avg_entry=${}, current=${}, unrealized=${}".format(
        p.symbol, p.qty, p.avg_entry_price, p.current_price, p.unrealized_pl))
