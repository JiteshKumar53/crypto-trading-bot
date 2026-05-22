"""Test Alpaca crypto symbols v2"""
import os
from alpaca_trade_api import REST

env_path = '/data/.openclaw/workspace/crypto-trading-bot/.env'
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

API_KEY = os.environ.get('ALPACA_API_KEY')
SECRET_KEY = os.environ.get('ALPACA_SECRET_KEY')

api = REST(API_KEY, SECRET_KEY, 'https://paper-api.alpaca.markets', api_version='v2')

# Try the exact format from error message: BTC/USD
print("Testing get_crypto_bars with BTC/USD...")
try:
    bars = api.get_crypto_bars('BTC/USD', '1D', limit=1)
    for bar in bars:
        print(f"✅ BTC/USD: ${bar.c:.2f}")
except Exception as e:
    print(f"❌ BTC/USD: {str(e)[:100]}")

print("\nTesting get_crypto_bars with ETH/USD...")
try:
    bars = api.get_crypto_bars('ETH/USD', '1D', limit=1)
    for bar in bars:
        print(f"✅ ETH/USD: ${bar.c:.2f}")
except Exception as e:
    print(f"❌ ETH/USD: {str(e)[:100]}")

# Try getting crypto snapshot
print("\nTesting get_crypto_snapshot...")
try:
    snap = api.get_crypto_snapshot('BTC/USD')
    print(f"✅ BTC/USD snapshot: daily_bar=${snap.daily_bar.c:.2f}")
except Exception as e:
    print(f"❌ snapshot: {str(e)[:100]}")

# List available crypto assets
print("\nTrying to list crypto assets...")
try:
    assets = api.list_assets(asset_class='crypto')
    for a in assets[:5]:
        print(f"  {a.symbol}")
except Exception as e:
    print(f"❌ list_assets: {str(e)[:100]}")
