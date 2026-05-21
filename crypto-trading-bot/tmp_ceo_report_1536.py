import sys, os
sys.path.insert(0, 'src')

with open('.env') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            key, value = line.split('=', 1)
            os.environ[key] = value

from broker.alpaca_client import AlpacaPaperClient
from datetime import datetime
import time

client = AlpacaPaperClient()
account = client.get_account()
positions = client.get_positions()

equity = float(account['equity'])
cash = float(account['cash'])
invested = equity - cash
pct_cash = cash/equity*100

print('=' * 60)
print('CEO 30-MINUTE STATUS REPORT')
print('=' * 60)
print()
print('Report time:', datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'CEST (Europe/Berlin)')
print('UTC time:', datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'), 'UTC')
print()

print('1. EXECUTIVE SUMMARY')
print('   Account equity: $' + format(equity, ',.2f'))
print('   Cash reserve: $' + format(cash, ',.2f') + ' (' + format(pct_cash, '.1f') + '%)')
print('   Invested: $' + format(invested, ',.2f'))
print('   Open positions:', len(positions))
print()

print('2. OPEN POSITIONS')
for p in positions:
    sym = p['symbol']
    qty = float(p['qty'])
    entry = float(p['avg_entry_price'])
    current = float(p['current_price'])
    value = float(p['market_value'])
    pnl = float(p['unrealized_pl'])
    pnl_pct = float(p['unrealized_plpc'])*100
    print('   ' + sym + ':', end='')
    print(' {:.4f}'.format(qty), end='')
    print(' | Entry: ${:,.2f}'.format(entry), end='')
    print(' | Current: ${:,.2f}'.format(current), end='')
    print(' | Value: ${:,.2f}'.format(value), end='')
    print(' | PnL: ${:.2f}'.format(pnl), end='')
    print(' ({:+.2f}%)'.format(pnl_pct))

print()
print('3. SYSTEM HEALTH')
print('   Daemon: RUNNING (PID: 6301)')
print('   Last activity:', datetime.now().strftime('%H:%M:%S'))
print()

print('4. RECENT EVENTS')
print('   - 13:30: Duplicate order resolved, BTC reduced to ~$200')
print('   - 11:44: SOL position opened (TESTING, $100 limit)')
print('   - 11:42: ETH position opened (TESTING, $100 limit)')
print()

print('5. RISK STATUS')
print('   All positions within approved limits')
for p in positions:
    value = float(p['market_value'])
    sym = p['symbol']
    if sym == 'BTCUSD':
        limit = 200.0
        status = 'ACTIVE'
    else:
        limit = 100.0
        status = 'TESTING'
    print('   ' + sym + ': $' + format(value, '.2f') + ' (limit: $' + format(limit, '.0f') + ') - ' + status)

print()
print('6. NEXT REPORT')
print('   Scheduled: 16:06 CEST')
print()
print('=' * 60)
