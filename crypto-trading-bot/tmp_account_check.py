import sys
sys.path.insert(0, 'src')
from broker.alpaca_client import AlpacaPaperClient
client = AlpacaPaperClient()
account = client.get_account()
equity = float(account['equity'])
cash = float(account['cash'])
bp = float(account['buying_power'])
positions = client.get_positions()
print('=== LIVE ACCOUNT SNAPSHOT ===')
print(f'Equity: ${equity:,.2f}')
print(f'Cash: ${cash:,.2f}')
print(f'Buying Power: ${bp:,.2f}')
print(f'Positions: {len(positions)}')
total_mv = 0
for p in positions:
    mv = float(p['market_value'])
    total_mv += mv
    entry = float(p['avg_entry_price'])
    current = float(p['current_price'])
    qty = float(p['qty'])
    unrealized = float(p['unrealized_pl'])
    unrealized_pct = float(p['unrealized_plpc']) * 100
    print(f"  {p['symbol']}: qty={qty:.6f}, entry=${entry:,.2f}, current=${current:,.2f}, unrealized=${unrealized:+.2f} ({unrealized_pct:+.2f}%)")
print(f'Total Invested: ${total_mv:,.2f}')
print(f'Reserve %: {(cash/equity)*100:.1f}%')
