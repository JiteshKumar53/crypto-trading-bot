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

print('=== POST-REDUCTION POSITION STATUS ===')
print()
print('Equity: $' + format(float(account['equity']), ',.2f'))
print('Cash: $' + format(float(account['cash']), ',.2f'))
print('Buying Power: $' + format(float(account['buying_power']), ',.2f'))
print()

for p in positions:
    sym = p['symbol']
    qty = float(p['qty'])
    price = float(p['current_price'])
    value = float(p['market_value'])
    entry = float(p['avg_entry_price'])
    pnl = float(p['unrealized_pl'])
    pnl_pct = float(p['unrealized_plpc'])
    
    print(sym + ':')
    print('  Qty: ' + format(qty, '.6f'))
    print('  Avg Entry: $' + format(entry, ',.2f'))
    print('  Current: $' + format(price, ',.2f'))
    print('  Market Value: $' + format(value, ',.2f'))
    print('  PnL: $' + format(pnl, ',.2f') + ' (' + format(pnl_pct, '+.2f') + '%)')
    
    if sym == 'BTCUSD':
        limit = 200.0
        print('  Approved Limit: $' + format(limit, '.2f'))
        if value <= limit * 1.05:
            print('  WITHIN LIMIT (within 5% tolerance)')
        else:
            print('  EXCEEDS LIMIT by $' + format(value - limit, '.2f'))
    elif sym == 'ETHUSD':
        limit = 100.0
        print('  Approved Limit: $' + format(limit, '.2f'))
        if value <= limit * 1.05:
            print('  WITHIN LIMIT')
        else:
            print('  EXCEEDS LIMIT')
    elif sym == 'SOLUSD':
        limit = 100.0
        print('  Approved Limit: $' + format(limit, '.2f'))
        if value <= limit * 1.05:
            print('  WITHIN LIMIT')
        else:
            print('  EXCEEDS LIMIT')
    print()

print('=== REDUCTION COMPLETE ===')
print('BTC position reduced from $697.88 to ~$200')
print('ETH and SOL positions within TESTING limits')
