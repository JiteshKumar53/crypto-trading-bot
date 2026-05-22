"""Test Alpaca crypto symbol formats"""
import os
from alpaca_trade_api import REST

# Load env
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

# Try different symbol formats
formats = ['BTCUSD', 'BTC/USD', 'BTC-USD', 'ETHUSD', 'ETH/USD', 'ETH-USD']

for sym in formats:
    try:
        bar = api.get_latest_bar(sym)
        print(f"✅ {sym}: ${bar.c:.2f}")
    except Exception as e:
        print(f"❌ {sym}: {str(e)[:60]}")

# Try crypto-specific API
print("\nTrying get_crypto_bars...")
try:
    bars = api.get_crypto_bars('BTCUSD', '1D', limit=1)
    for bar in bars:
        print(f"✅ get_crypto_bars BTCUSD: ${bar.c:.2f}")
except Exception as e:
    print(f"❌ get_crypto_bars: {str(e)[:80]}")
