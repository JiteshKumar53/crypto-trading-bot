"""
Trade dashboard web server (stdlib only).

Serves a single-page UI to inspect the Alpaca paper account: equity, cash,
open positions, open orders, and recent fills. Falls back gracefully to the
honest backtest results when the live connection is unavailable, and tells you
exactly *why* it's unavailable (egress not allowlisted / missing creds / auth).

Run:
    export ALPACA_API_KEY=...        # paper key (PK...), optional
    export ALPACA_SECRET_KEY=...
    python3 scripts/trade_ui_server.py            # -> http://localhost:8787

No third-party dependencies — works before alpaca-py / flask are installed.
Credentials are read from env vars only; nothing is written to disk or git.
"""

import json
import os
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HTML_FILE = ROOT.parent / "dashboard" / "index.html"
BACKTEST_FILE = ROOT.parent / "freqtrade_data" / "honest_backtest_results.json"

BASE_URL = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
PORT = int(os.getenv("TRADE_UI_PORT", "8787"))


def _alpaca_get(path: str):
    """Return (status, parsed_json_or_text). Raises only on network errors."""
    key = os.getenv("ALPACA_API_KEY")
    secret = os.getenv("ALPACA_SECRET_KEY")
    if not key or not secret:
        return None, "missing_credentials"
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
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        return e.code, body
    except Exception as e:  # noqa: BLE001
        return -1, str(e)


def _load_backtest():
    if BACKTEST_FILE.exists():
        try:
            return json.loads(BACKTEST_FILE.read_text())
        except Exception:  # noqa: BLE001
            return None
    return None


def build_payload() -> dict:
    """Assemble everything the UI needs in one JSON blob."""
    payload = {
        "base_url": BASE_URL,
        "live": {"connected": False, "reason": None},
        "account": None,
        "positions": [],
        "orders": [],
        "fills": [],
        "backtest": _load_backtest(),
    }

    status, account = _alpaca_get("/v2/account")

    if account == "missing_credentials":
        payload["live"]["reason"] = "ALPACA_API_KEY / ALPACA_SECRET_KEY not set in environment."
        return payload
    if status == -1:
        payload["live"]["reason"] = f"Network error reaching Alpaca: {account}"
        return payload
    if isinstance(account, str) and ("not in allowlist" in account or "host_not_allowed" in account):
        payload["live"]["reason"] = (
            "Network egress blocks Alpaca. Allowlist paper-api.alpaca.markets "
            "and data.alpaca.markets in the environment's egress settings."
        )
        return payload
    if status in (401, 403):
        payload["live"]["reason"] = f"Alpaca rejected credentials (HTTP {status})."
        return payload
    if status != 200 or not isinstance(account, dict):
        payload["live"]["reason"] = f"Unexpected Alpaca response (HTTP {status})."
        return payload

    # Connected
    payload["live"]["connected"] = True
    payload["account"] = {
        "id": account.get("id"),
        "status": account.get("status"),
        "equity": float(account.get("equity", 0)),
        "last_equity": float(account.get("last_equity", 0) or 0),
        "cash": float(account.get("cash", 0)),
        "buying_power": float(account.get("buying_power", 0)),
        "portfolio_value": float(account.get("portfolio_value", 0)),
    }

    ps, positions = _alpaca_get("/v2/positions")
    if ps == 200 and isinstance(positions, list):
        payload["positions"] = [
            {
                "symbol": p["symbol"],
                "qty": float(p["qty"]),
                "entry": float(p["avg_entry_price"]),
                "price": float(p["current_price"]),
                "market_value": float(p["market_value"]),
                "upl": float(p["unrealized_pl"]),
                "upl_pct": float(p["unrealized_plpc"]) * 100,
            }
            for p in positions
        ]

    os_, orders = _alpaca_get("/v2/orders?status=all&limit=50&direction=desc")
    if os_ == 200 and isinstance(orders, list):
        payload["orders"] = [
            {
                "symbol": o["symbol"],
                "side": o["side"],
                "qty": o.get("qty"),
                "type": o.get("type"),
                "status": o.get("status"),
                "submitted_at": o.get("submitted_at"),
                "filled_avg_price": o.get("filled_avg_price"),
            }
            for o in orders
        ]

    fs, fills = _alpaca_get("/v2/account/activities/FILL?page_size=50")
    if fs == 200 and isinstance(fills, list):
        payload["fills"] = [
            {
                "symbol": f.get("symbol"),
                "side": f.get("side"),
                "qty": f.get("qty"),
                "price": f.get("price"),
                "time": f.get("transaction_time"),
            }
            for f in fills
        ]

    return payload


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, content_type="application/json"):
        data = body.encode() if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path.startswith("/api/data"):
            try:
                self._send(200, json.dumps(build_payload()))
            except Exception as e:  # noqa: BLE001
                self._send(500, json.dumps({"error": str(e)}))
            return
        if self.path in ("/", "/index.html"):
            if HTML_FILE.exists():
                self._send(200, HTML_FILE.read_bytes(), "text/html; charset=utf-8")
            else:
                self._send(404, "dashboard/index.html not found")
            return
        self._send(404, "not found", "text/plain")

    def log_message(self, *args):  # quiet
        pass


def main():
    srv = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Trade dashboard running at http://localhost:{PORT}")
    print(f"  API: http://localhost:{PORT}/api/data")
    print("  Ctrl-C to stop.")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        srv.shutdown()


if __name__ == "__main__":
    main()
