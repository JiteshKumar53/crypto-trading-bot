"""
Dashboard Generator
Agent: Jarvis / COO coordination

Generates a self-contained HTML dashboard for monitoring the trading system.
Reads decision logs and account state to produce real-time views.
"""

import json
import os
import glob
from datetime import datetime, timezone
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

DASHBOARD_DIR = "dashboard"
DECISION_LOG_DIR = "logs/decisions"


def load_decisions(limit: int = 50) -> List[Dict]:
    """Load recent decisions from JSONL files."""
    decisions = []
    jsonl_files = glob.glob(f"{DECISION_LOG_DIR}/*.jsonl")
    for filepath in jsonl_files:
        try:
            with open(filepath, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            decisions.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
        except Exception:
            continue
    # Sort by timestamp desc, take latest
    decisions.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return decisions[:limit]


def generate_dashboard_html(account_state: Optional[Dict] = None, agent_status: Optional[Dict] = None) -> str:
    """Generate self-contained HTML dashboard."""
    decisions = load_decisions(50)
    
    # Parse decisions for display
    rows = []
    for d in decisions:
        ts = d.get("timestamp", "N/A")[:19]
        decision_type = d.get("decision_type", "N/A")
        maker = d.get("decision_maker", "N/A")
        title = d.get("title", "N/A")
        result = d.get("result", "N/A")
        
        # Color code results
        result_class = "result-neutral"
        if result in ["APPROVED", "AUTHORIZED", "SPRINT_4_COMPLETE", "PASS", "success"]:
            result_class = "result-success"
        elif result in ["REJECTED", "FAIL", "error", "ERROR"]:
            result_class = "result-fail"
        
        rows.append(f"""
            <tr>
                <td>{ts}</td>
                <td>{decision_type}</td>
                <td>{maker}</td>
                <td>{title}</td>
                <td class="{result_class}">{result}</td>
            </tr>
        """)
    
    # Account state section
    if account_state:
        account_html = f"""
        <div class="section">
            <h2>Account State</h2>
            <div class="cards">
                <div class="card">
                    <div class="card-value">${account_state.get('portfolio_value', 0):,.2f}</div>
                    <div class="card-label">Portfolio Value</div>
                </div>
                <div class="card">
                    <div class="card-value">${account_state.get('cash', 0):,.2f}</div>
                    <div class="card-label">Cash</div>
                </div>
                <div class="card">
                    <div class="card-value">${account_state.get('buying_power', 0):,.2f}</div>
                    <div class="card-label">Buying Power</div>
                </div>
                <div class="card">
                    <div class="card-value">{account_state.get('open_positions', 0)}</div>
                    <div class="card-label">Open Positions</div>
                </div>
            </div>
        </div>
        """
    else:
        account_html = """
        <div class="section">
            <h2>Account State</h2>
            <p>Account state not available. Dashboard refreshes automatically when connected to Alpaca.</p>
        </div>
        """
    
    # Agent status section
    if agent_status:
        agent_rows = []
        for agent_name, status in agent_status.items():
            status_class = "result-success" if status == "operational" else "result-fail"
            agent_rows.append(f"""
                <tr>
                    <td>{agent_name}</td>
                    <td class="{status_class}">{status}</td>
                </tr>
            """)
        agent_html = f"""
        <div class="section">
            <h2>Agent Status</h2>
            <table>
                <thead>
                    <tr><th>Agent</th><th>Status</th></tr>
                </thead>
                <tbody>
                    {''.join(agent_rows)}
                </tbody>
            </table>
        </div>
        """
    else:
        agent_html = """
        <div class="section">
            <h2>Agent Status</h2>
            <p>Agent status not yet captured. Will populate during next pipeline run.</p>
        </div>
        """
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🦊 Jarvis Trading Dashboard</title>
    <style>
        :root {{
            --bg: #0a0e17;
            --surface: #111827;
            --surface-light: #1f2937;
            --text: #e5e7eb;
            --text-muted: #9ca3af;
            --accent: #10b981;
            --accent-fail: #ef4444;
            --accent-warn: #f59e0b;
            --border: #374151;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg);
            color: var(--text);
            margin: 0;
            padding: 20px;
            line-height: 1.5;
        }}
        h1 {{
            margin: 0 0 10px 0;
            font-size: 24px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .subtitle {{
            color: var(--text-muted);
            margin-bottom: 20px;
            font-size: 14px;
        }}
        .section {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
        }}
        .section h2 {{
            margin-top: 0;
            font-size: 16px;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        .cards {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
        }}
        .card {{
            background: var(--surface-light);
            border-radius: 6px;
            padding: 15px;
            text-align: center;
        }}
        .card-value {{
            font-size: 24px;
            font-weight: bold;
            color: var(--accent);
        }}
        .card-label {{
            font-size: 12px;
            color: var(--text-muted);
            margin-top: 5px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }}
        th, td {{
            padding: 10px 12px;
            text-align: left;
            border-bottom: 1px solid var(--border);
        }}
        th {{
            color: var(--text-muted);
            font-weight: 600;
            text-transform: uppercase;
            font-size: 11px;
            letter-spacing: 0.05em;
        }}
        tr:hover {{
            background: var(--surface-light);
        }}
        .result-success {{ color: var(--accent); }}
        .result-fail {{ color: var(--accent-fail); }}
        .result-warn {{ color: var(--accent-warn); }}
        .result-neutral {{ color: var(--text-muted); }}
        .meta {{
            color: var(--text-muted);
            font-size: 12px;
            margin-top: 20px;
            text-align: center;
        }}
        .status-badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
        }}
        .status-paper {{
            background: rgba(16, 185, 129, 0.1);
            color: var(--accent);
            border: 1px solid var(--accent);
        }}
        @media (max-width: 600px) {{
            body {{ padding: 10px; }}
            .cards {{ grid-template-columns: repeat(2, 1fr); }}
        }}
    </style>
</head>
<body>
    <h1>🦊 Jarvis Trading Dashboard</h1>
    <div class="subtitle">
        Crypto AI Trading System | Paper Trading Mode 
        <span class="status-badge status-paper">PAPER</span>
        | Auto-refresh: 30s
    </div>

    {account_html}

    {agent_html}

    <div class="section">
        <h2>Decision Log (Latest 50)</h2>
        <table>
            <thead>
                <tr>
                    <th>Timestamp</th>
                    <th>Type</th>
                    <th>Decision Maker</th>
                    <th>Title</th>
                    <th>Result</th>
                </tr>
            </thead>
            <tbody>
                {''.join(rows) if rows else '<tr><td colspan="5" style="text-align:center;color:var(--text-muted)">No decisions logged yet</td></tr>'}
            </tbody>
        </table>
    </div>

    <div class="meta">
        Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')} | 
        <a href="?" style="color:var(--accent)">Refresh Now</a> | 
        <a href="../logs/decisions/decisions.jsonl" style="color:var(--accent)">Raw Logs</a>
    </div>

    <script>
        // Auto-refresh every 30 seconds
        setInterval(function() {{
            location.reload();
        }}, 30000);
    </script>
</body>
</html>"""
    
    return html


def write_dashboard(account_state: Optional[Dict] = None, agent_status: Optional[Dict] = None) -> str:
    """Generate dashboard HTML and write to file. Returns filepath."""
    html = generate_dashboard_html(account_state, agent_status)
    os.makedirs(DASHBOARD_DIR, exist_ok=True)
    filepath = f"{DASHBOARD_DIR}/index.html"
    with open(filepath, 'w') as f:
        f.write(html)
    logger.info(f"[Dashboard] Written to {filepath}")
    return filepath


def get_account_state_from_alpaca(alpaca_client) -> Dict:
    """Fetch current account state from Alpaca client."""
    try:
        account = alpaca_client.get_account()
        positions = alpaca_client.get_positions()
        return {
            "portfolio_value": account.get("portfolio_value", 0),
            "cash": account.get("cash", 0),
            "buying_power": account.get("buying_power", 0),
            "open_positions": len(positions),
            "position_details": [
                {
                    "symbol": p.get("symbol", "N/A"),
                    "qty": p.get("qty", 0),
                    "market_value": p.get("market_value", 0),
                }
                for p in positions
            ],
        }
    except Exception as e:
        logger.error(f"[Dashboard] Failed to fetch account state: {e}")
        return {
            "portfolio_value": 0,
            "cash": 0,
            "buying_power": 0,
            "open_positions": 0,
            "error": str(e),
        }


if __name__ == "__main__":
    import sys
    sys.path.insert(0, 'src')
    from broker.alpaca_client import AlpacaPaperClient
    
    client = AlpacaPaperClient()
    account = get_account_state_from_alpaca(client)
    filepath = write_dashboard(account, None)
    print(f"Dashboard generated: {filepath}")
