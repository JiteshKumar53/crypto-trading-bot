import sys, os
sys.path.insert(0, 'src')
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetOrdersRequest
from alpaca.trading.enums import QueryOrderStatus
from datetime import datetime, timedelta, timezone

client = TradingClient(
    os.getenv('ALPACA_API_KEY'),
    os.getenv('ALPACA_SECRET_KEY'),
    paper=True,
)

# Try getting orders from last 7 days
end = datetime.now(timezone.utc)
start = end - timedelta(days=7)

print("Querying orders from", start.isoformat(), "to", end.isoformat())

req = GetOrdersRequest(
    status=QueryOrderStatus.ALL,
    after=start,
    until=end,
)
orders = client.get_orders(filter=req)
print("Orders found:", len(orders))

for o in orders[:50]:
    print("{} {} {} qty={} filled={} @ {} status={}".format(
        o.created_at.isoformat()[:19] if o.created_at else 'N/A',
        o.symbol,
        o.side,
        o.qty,
        o.filled_qty,
        o.filled_avg_price,
        o.status,
    ))

if not orders:
    print("\nNo orders returned. Trying without filter...")
    orders2 = client.get_orders()
    print("Orders without filter:", len(orders2))
    for o in orders2[:10]:
        print("  {} {} status={}".format(o.symbol, o.side, o.status))
