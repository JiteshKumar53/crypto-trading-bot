import re, json, os, sys
from datetime import datetime, timezone

# Parse daemon.log for actual executed trades
log_path = 'logs/daemon.log'
if not os.path.exists(log_path):
    print("No daemon.log found")
    sys.exit(1)

with open(log_path) as f:
    lines = f.readlines()

# Extract all EXIT EXECUTED events
exits = []
for line in lines:
    if 'EXIT EXECUTED' in line:
        # Parse: [POSITION MONITOR] EXIT EXECUTED: SELL_PARTIAL 0.009687221 BTCUSD reason=partial_profit_1 (+0.53%) order_id=...
        match = re.search(r'EXIT EXECUTED: (\w+) ([\d.eE+-]+) (\w+) reason=(\S+) .* order_id=(\S+)', line)
        if match:
            exit_type = match.group(1)  # SELL_PARTIAL, SELL_ALL, SELL_RUNNER
            qty = float(match.group(2))
            symbol = match.group(3)
            reason = match.group(4)
            order_id = match.group(5)
            
            # Try to get price from earlier in line
            price_match = re.search(r'@\s*\$?([\d.]+)', line)
            price = float(price_match.group(1)) if price_match else 0
            
            # Get timestamp from line start
            ts_match = re.match(r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2},\d+)', line)
            ts = ts_match.group(1) if ts_match else ''
            
            exits.append({
                'timestamp': ts,
                'type': exit_type,
                'symbol': symbol,
                'qty': qty,
                'price': price,
                'reason': reason,
                'order_id': order_id,
            })

# Extract EXIT FAILED events
failures = []
for line in lines:
    if 'EXIT FAILED' in line:
        ts_match = re.match(r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2},\d+)', line)
        ts = ts_match.group(1) if ts_match else ''
        
        # Try to find which symbol
        symbol_match = re.search(r'for\s+(\w+)', line)
        symbol = symbol_match.group(1) if symbol_match else 'unknown'
        
        failures.append({'timestamp': ts, 'symbol': symbol, 'line': line.strip()[:200]})

print("=" * 70)
print("CEO PROFITABILITY AUDIT - ACTUAL EXECUTED EXITS")
print("=" * 70)

print(f"\nTotal executed exits: {len(exits)}")
print(f"Total failed exits: {len(failures)}")

print("\n--- EXECUTED EXITS ---")
for e in exits:
    print(f"  {e['timestamp']}: {e['type']} {e['qty']:.8f} {e['symbol']} reason={e['reason']}")

print("\n--- FAILED EXITS (first 20) ---")
for f in failures[:20]:
    print(f"  {f['timestamp']}: {f['symbol']}")

# Now get actual realized PnL from these exits
# We need to match with entry prices from position state
# The entries are the open positions

# Get current positions for entry prices
position_state_path = 'logs/position_monitor_state.json'
entries = {}
if os.path.exists(position_state_path):
    import json
    with open(position_state_path) as f:
        positions = json.load(f)
    for sym, data in positions.items():
        entries[sym] = {
            'avg_entry': data.get('avg_entry_price', 0),
            'qty': data.get('qty', 0),
            'entry_time': data.get('entry_time', ''),
        }

print("\n--- CURRENT POSITIONS (still open) ---")
for sym, data in entries.items():
    print(f"  {sym}: qty={data['qty']:.6f}, avg_entry=${data['avg_entry']:.2f}, entry_time={data['entry_time'][:19]}")

# Calculate realized PnL from executed exits
# Note: We don't have actual fill prices from the log, so we'll estimate
# The partial sells happened at prices we can infer from the log

# Parse the actual sell prices from log entries
# The BTC partial at 12:24 was at current price $77380 at that time (from log)
# ETH sell at 10:54 was dust (2e-09) - essentially zero

print("\n--- REALIZED PnL ESTIMATES ---")

# BTC partial: sold 0.009687221 at ~$77,380 (current price at 12:24)
# Entry was $77,293.58 (from position state) - but wait, that might have been a different entry
# Actually the entry is the avg_entry_price from position state
btc_entry = entries.get('BTCUSD', {}).get('avg_entry', 0)
btc_qty_sold = 0.009687221
btc_sell_price_approx = 77380  # from log at that time
if btc_entry > 0:
    btc_pnl = (btc_sell_price_approx - btc_entry) * btc_qty_sold
    print(f"  BTC partial: bought ~${btc_entry:.2f}, sold ~${btc_sell_price_approx:.2f}, qty={btc_qty_sold}, PnL=~${btc_pnl:+.2f}")

# ETH: sold 2e-09 at unknown price - essentially zero PnL
eth_entry = entries.get('ETHUSD', {}).get('avg_entry', 0)
eth_qty_sold = 2e-09
print(f"  ETH sell: qty={eth_qty_sold} (DUST - essentially zero realized)")

print(f"\nTotal realized PnL (only BTC partial + dust ETH): ~${(btc_sell_price_approx - btc_entry) * btc_qty_sold if btc_entry > 0 else 0:+.2f}")

# Count partial sell trigger attempts
partial_triggers = sum(1 for line in lines if 'SELL_PARTIAL TRIGGERED' in line)
runner_triggers = sum(1 for line in lines if 'SELL_RUNNER TRIGGERED' in line)
all_triggers = sum(1 for line in lines if 'SELL_ALL TRIGGERED' in line)

print(f"\n--- EXIT TRIGGER COUNTS ---")
print(f"Partial profit triggers: {partial_triggers}")
print(f"Runner triggers: {runner_triggers}")
print(f"Full exit triggers: {all_triggers}")
print(f"Successful executions: {len(exits)}")
print(f"Failed executions: {len(failures)}")

# The key finding: Most partial sells failed because qty was too small
# This is because after rounding, the qty became dust

print(f"\n--- KEY FINDING ---")
print(f"Partial sells attempted but failed {len(failures)} times")
print(f"Most failures: 'order qty must be >= minimal qty'")
print(f"This means the system TRIED to take profits but couldn't execute")
print(f"Only {len(exits)} exits actually succeeded")

# Calculate what PnL we SHOULD have if all partial sells succeeded
# BTC: partial at +0.53% = $0.53 per $100 invested
# For $500 position: $2.65 partial profit
# ETH: partial at +0.65% to +1.05% = $3.25 to $5.25 on $500 position

print(f"\n--- MISSED PROFIT ESTIMATES ---")
# ETH had ~7 partial sell trigger attempts at ~+0.8% avg
eth_invested = 500  # approximate
eth_missed_pct = 0.8
eth_missed = eth_invested * eth_missed_pct / 100
print(f"ETH: ~7 partial triggers at ~+{eth_missed_pct}%, missed profit: ~${eth_missed:.2f} per trigger")
print(f"  Total missed ETH partial profits: ~${eth_missed * 7:.2f}")

# BTC: 1 partial succeeded, but how many failed?
btc_partial_fails = sum(1 for f in failures if f['symbol'] == 'BTCUSD')
print(f"BTC: 1 partial succeeded, {btc_partial_fails} BTC-related failures")

print("\n" + "=" * 70)
