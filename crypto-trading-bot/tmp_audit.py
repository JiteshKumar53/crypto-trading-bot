import sys, json

trades = []
for line in sys.stdin:
    try:
        d = json.loads(line.strip())
        # Only include actual trading decisions (buys/sells with execution)
        if d.get('decision_type') == 'autonomous_jarvis' and d.get('result') in ['PENDING_EXECUTION', 'EXECUTED', 'FILLED']:
            trades.append(d)
    except:
        pass

print(f'Total trading decisions: {len(trades)}')

# Extract executed orders from order_details
executed_orders = []
for t in trades:
    od = t.get('order_details', {})
    if od and od.get('order_id'):
        executed_orders.append({
            'symbol': od.get('symbol', t.get('title', '').split()[-1] if t.get('title') else 'unknown'),
            'side': od.get('side', 'buy'),
            'qty': float(od.get('qty', 0)),
            'price': float(od.get('price', 0)),
            'order_id': od.get('order_id'),
            'timestamp': t.get('timestamp'),
        })

print(f'Orders with details: {len(executed_orders)}')
for o in executed_orders[:10]:
    print(f\"  {o['symbol']} {o['side']} {o['qty']} @ {o['price']}\")
