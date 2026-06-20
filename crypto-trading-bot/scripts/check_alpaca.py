"""
Alpaca paper-account connectivity check.

Usage:
    export ALPACA_API_KEY=...        # paper key (PK...)
    export ALPACA_SECRET_KEY=...
    python3 scripts/check_alpaca.py

Requires the environment's network egress to allowlist:
    paper-api.alpaca.markets
    data.alpaca.markets

Reads credentials from env vars ONLY — never hardcode or commit secrets.
Uses the stdlib (urllib) so it works even before alpaca-py is installed.
"""

import json
import os
import sys
import urllib.error
import urllib.request

BASE_URL = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")


def _get(path: str, key: str, secret: str) -> tuple[int, str]:
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        headers={
            "APCA-API-KEY-ID": key,
            "APCA-API-SECRET-KEY": secret,
            "accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


def main() -> int:
    key = os.getenv("ALPACA_API_KEY")
    secret = os.getenv("ALPACA_SECRET_KEY")
    paper = os.getenv("ALPACA_PAPER", "true").lower() == "true"

    if not key or not secret:
        print("FAIL: ALPACA_API_KEY / ALPACA_SECRET_KEY not set in environment.")
        return 2
    if not paper:
        print("REFUSE: ALPACA_PAPER is not 'true'. This check is paper-only.")
        return 2
    if "paper" not in BASE_URL:
        print(f"REFUSE: base URL is not a paper endpoint: {BASE_URL}")
        return 2

    print(f"Checking {BASE_URL} (key {key[:6]}…) ...")
    status, body = _get("/v2/account", key, secret)

    if status == 200:
        acct = json.loads(body)
        print("CONNECTED ✓  paper account")
        print(f"  account id     : {acct.get('id')}")
        print(f"  status         : {acct.get('status')}")
        print(f"  equity         : ${float(acct.get('equity', 0)):,.2f}")
        print(f"  cash           : ${float(acct.get('cash', 0)):,.2f}")
        print(f"  buying power   : ${float(acct.get('buying_power', 0)):,.2f}")
        print(f"  portfolio value: ${float(acct.get('portfolio_value', 0)):,.2f}")

        ps, pbody = _get("/v2/positions", key, secret)
        if ps == 200:
            positions = json.loads(pbody)
            print(f"  open positions : {len(positions)}")
            for p in positions:
                print(f"    - {p['symbol']}: qty={p['qty']} "
                      f"mv=${float(p['market_value']):,.2f} "
                      f"uPL=${float(p['unrealized_pl']):,.2f}")
        return 0

    if status in (401, 403) and ("not in allowlist" in body or "host_not_allowed" in body):
        print("BLOCKED: network egress is not allowlisting Alpaca.")
        print(f"  {body.strip()}")
        print("  -> Add paper-api.alpaca.markets and data.alpaca.markets to egress settings.")
        return 3
    if status in (401, 403):
        print(f"AUTH FAILED (HTTP {status}): credentials rejected by Alpaca.")
        print(f"  {body.strip()}")
        return 4

    print(f"UNEXPECTED (HTTP {status}): {body.strip()}")
    return 5


if __name__ == "__main__":
    sys.exit(main())
