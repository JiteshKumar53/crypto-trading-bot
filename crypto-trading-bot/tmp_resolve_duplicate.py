import sys, os
sys.path.insert(0, 'src')

with open('.env') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            key, value = line.split('=', 1)
            os.environ[key] = value

from broker.alpaca_client import AlpacaPaperClient

client = AlpacaPaperClient()
account = client.get_account()
positions = client.get_positions()

print('=== DUPLICATE ORDER RESOLUTION ===')
print()

# Find BTC position
btc_pos = None
for p in positions:
    if p['symbol'] == 'BTCUSD':
        btc_pos = p
        break

if not btc_pos:
    print('ERROR: No BTC position found')
    exit(1)

current_qty = float(btc_pos['qty'])
current_value = float(btc_pos['market_value'])
current_price = float(btc_pos['current_price'])
avg_entry = float(btc_pos['avg_entry_price'])
approved_limit = 200.0

print(f'Current BTC position: {current_qty:.8f} BTC')
print(f'Current value: ${current_value:.2f}')
print(f'Current price: ${current_price:.2f}')
print(f'Avg entry: ${avg_entry:.2f}')
print(f'Approved limit: ${approved_limit:.2f}')
print()

if current_value <= approved_limit:
    print('Position already within limit. No action needed.')
    exit(0)

excess_value = current_value - approved_limit
target_qty = approved_limit / current_price
excess_qty = current_qty - target_qty

print(f'Excess value: ${excess_value:.2f}')
print(f'Target qty for $200 limit: {target_qty:.6f} BTC')
print(f'Excess qty to sell: {excess_qty:.6f} BTC')
print()

# Submit reduce-only sell order
print('Submitting reduce-only SELL order for excess...')
order = client.submit_order(
    symbol='BTCUSD',
    side='sell',
    qty=round(excess_qty, 6)
)

if order.success:
    print(f'Order submitted: {order.order_id}')
    print(f'Status: {order.status}')
    print(f'Filled qty: {order.filled_qty}')
    print(f'Filled avg price: {order.filled_avg_price}')
    
    # Calculate realized PnL
    if order.filled_avg_price:
        realized_pnl = (float(order.filled_avg_price) - avg_entry) * float(order.filled_qty)
        print(f'Realized PnL from reduction: ${realized_pnl:.2f}')
    else:
        realized_pnl = 0
        print('Realized PnL: pending fill')
    
    print()
    print('=== ORDER CONFIRMED ===')
    print(f'Order ID: {order.order_id}')
    print(f'Quantity sold: {order.filled_qty}')
    print(f'Final position should be: ~${approved_limit:.2f}')
else:
    print(f'ERROR: Order failed: {order.error}')
    exit(1)
