import sys, os
from datetime import datetime, timezone
sys.path.insert(0, 'src')

with open('.env') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            key, value = line.split('=', 1)
            os.environ[key] = value

from broker.alpaca_client import AlpacaPaperClient
from alpaca.trading.requests import GetOrdersRequest
from alpaca.trading.enums import QueryOrderStatus

client = AlpacaPaperClient()

# Recent orders
req = GetOrdersRequest(status=QueryOrderStatus.ALL, limit=10)
orders = client.trading_client.get_orders(req)

print('=== RECENT ORDERS (last 10) ===')
today = datetime.now(timezone.utc).date()
for o in orders:
    if o.submitted_at and o.submitted_at.date() == today:
        print(o.submitted_at.strftime('%H:%M:%S') + ' | ' + o.symbol + ' ' + o.side.value + ' | ' + str(o.filled_qty) + '/' + str(o.qty) + ' @ ' + str(o.filled_avg_price) + ' | Status: ' + o.status.value)

print()
print('=== CURRENT POSITIONS ===')
positions = client.get_positions()
for p in positions:
    print(p['symbol'] + ': ' + str(p['qty']) + ' @ $' + format(float(p['current_price']), ',.2f') + ' = $' + format(float(p['market_value']), ',.2f'))

print()
print('=== ACCOUNT ===')
account = client.get_account()
print('Equity: $' + format(float(account['equity']), ',.2f'))
print('Cash: $' + format(float(account['cash']), ',.2f'))
