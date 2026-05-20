"""Generate live dashboard data file from Alpaca API."""

import os
import json
from datetime import datetime, timezone
from pathlib import Path

# Load env
env_file = Path(__file__).parent.parent / ".env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

from alpaca.trading.client import TradingClient

DASHBOARD_DATA_FILE = Path(__file__).parent.parent / "dashboard" / "live_data.json"

def generate_dashboard_data():
    try:
        client = TradingClient(
            os.environ['ALPACA_API_KEY'],
            os.environ['ALPACA_SECRET_KEY'],
            paper=True
        )
        
        account = client.get_account()
        positions = client.get_all_positions()
        
        data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "account": {
                "equity": float(account.equity),
                "cash": float(account.cash),
                "buying_power": float(account.buying_power),
            },
            "positions": [
                {
                    "symbol": p.symbol,
                    "qty": float(p.qty),
                    "entry_price": float(p.avg_entry_price),
                    "current_price": float(p.current_price),
                    "market_value": float(p.market_value),
                    "unrealized_pl": float(p.unrealized_pl),
                    "unrealized_pl_pct": (float(p.current_price) - float(p.avg_entry_price)) / float(p.avg_entry_price) * 100
                }
                for p in positions
            ],
            "status": {
                "trading_halted": True,
                "halt_reason": "Daily loss audit in progress",
                "new_entries_allowed": False,
                "open_positions_monitored": True,
            }
        }
        
        DASHBOARD_DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(DASHBOARD_DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        
        return data
    except Exception as e:
        error_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(e),
            "status": "failed"
        }
        with open(DASHBOARD_DATA_FILE, 'w') as f:
            json.dump(error_data, f, indent=2)
        return error_data

if __name__ == "__main__":
    result = generate_dashboard_data()
    print(json.dumps(result, indent=2))
