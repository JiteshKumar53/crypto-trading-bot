"""
Position Tracker with SL/TP
Agent: Jarvis (Junior CEO)

Tracks:
- Entry price, entry time, entry reason
- Stop-loss level
- Take-profit level  
- Max allowed loss on trade
- Current unrealized P/L
- Exit rule (when to close)
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)

TRACKER_FILE = Path('/data/.openclaw/workspace/crypto-trading-bot/logs/position_tracker.json')

DEFAULT_SL_PCT = 0.02   # 2% stop-loss
DEFAULT_TP_PCT = 0.05  # 5% take-profit


def load_tracker() -> Dict:
    """Load position tracker state."""
    if TRACKER_FILE.exists():
        with open(TRACKER_FILE, 'r') as f:
            return json.load(f)
    return {'positions': {}}


def save_tracker(tracker: Dict):
    """Save position tracker state."""
    TRACKER_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(TRACKER_FILE, 'w') as f:
        json.dump(tracker, f, indent=2, default=str)


def record_entry(symbol: str, entry_price: float, qty: float, reason: str = "EA Core signal"):
    """Record a new position entry."""
    tracker = load_tracker()
    
    sl_price = entry_price * (1 - DEFAULT_SL_PCT)
    tp_price = entry_price * (1 + DEFAULT_TP_PCT)
    max_loss = (entry_price - sl_price) * qty
    
    tracker['positions'][symbol] = {
        'entry_price': round(entry_price, 2),
        'entry_time': datetime.now(timezone.utc).isoformat(),
        'qty': round(qty, 6),
        'entry_reason': reason,
        'stop_loss': round(sl_price, 2),
        'take_profit': round(tp_price, 2),
        'max_allowed_loss': round(max_loss, 2),
        'exit_rule': f'Stop-loss at ${sl_price:,.2f} (-{DEFAULT_SL_PCT*100:.0f}%) OR take-profit at ${tp_price:,.2f} (+{DEFAULT_TP_PCT*100:.0f}%)',
        'status': 'OPEN',
    }
    
    save_tracker(tracker)
    logger.info(f"[TRACKER] Recorded entry for {symbol}: ${entry_price:,.2f} x {qty}")


def record_exit(symbol: str, exit_price: float, exit_reason: str = "stop_or_tp"):
    """Record a position exit."""
    tracker = load_tracker()
    
    if symbol not in tracker['positions']:
        logger.warning(f"[TRACKER] No entry record for {symbol}")
        return
    
    pos = tracker['positions'][symbol]
    entry_price = pos['entry_price']
    qty = pos['qty']
    realized_pnl = (exit_price - entry_price) * qty
    
    pos['exit_price'] = round(exit_price, 2)
    pos['exit_time'] = datetime.now(timezone.utc).isoformat()
    pos['exit_reason'] = exit_reason
    pos['realized_pnl'] = round(realized_pnl, 2)
    pos['realized_pnl_pct'] = round((exit_price - entry_price) / entry_price * 100, 2)
    pos['status'] = 'CLOSED'
    
    save_tracker(tracker)
    logger.info(f"[TRACKER] Recorded exit for {symbol}: ${exit_price:,.2f} | PnL: ${realized_pnl:+.2f}")


def get_position_status(symbol: str) -> Optional[Dict]:
    """Get current tracked position status."""
    tracker = load_tracker()
    return tracker['positions'].get(symbol)


def get_all_positions() -> Dict[str, Dict]:
    """Get all tracked positions."""
    tracker = load_tracker()
    return tracker['positions']


def check_exit_conditions(symbol: str, current_price: float) -> Optional[str]:
    """Check if position should be exited. Returns exit reason or None."""
    pos = get_position_status(symbol)
    if not pos or pos.get('status') != 'OPEN':
        return None
    
    sl = pos.get('stop_loss')
    tp = pos.get('take_profit')
    
    if sl and current_price <= sl:
        return 'stop_loss'
    if tp and current_price >= tp:
        return 'take_profit'
    
    return None


def generate_position_report() -> str:
    """Generate a position tracking report."""
    from broker.alpaca_client import AlpacaPaperClient
    
    tracker = load_tracker()
    positions = tracker['positions']
    
    client = AlpacaPaperClient()
    alpaca_positions = {p['symbol']: p for p in client.get_positions()}
    
    lines = [
        "---",
        "",
        "# POSITION TRACKER REPORT",
        "",
        f"**Report time:** {datetime.now(timezone.utc).isoformat()}",
        "",
    ]
    
    open_positions = [s for s, p in positions.items() if p.get('status') == 'OPEN']
    closed_positions = [s for s, p in positions.items() if p.get('status') == 'CLOSED']
    
    lines.extend([
        "## OPEN POSITIONS",
        "",
    ])
    
    if open_positions:
        for symbol in open_positions:
            pos = positions[symbol]
            current = alpaca_positions.get(symbol, {})
            current_price = float(current.get('current_price', 0)) if current else 0
            
            entry_price = pos['entry_price']
            qty = pos['qty']
            unrealized = (current_price - entry_price) * qty if current_price else 0
            unrealized_pct = ((current_price - entry_price) / entry_price * 100) if current_price and entry_price else 0
            
            lines.extend([
                f"### {symbol}",
                f"- **Status:** 🟢 OPEN",
                f"- **Entry price:** ${entry_price:,.2f}",
                f"- **Current price:** ${current_price:,.2f}" if current_price else "- **Current price:** [unavailable]",
                f"- **Qty:** {qty}",
                f"- **Entry reason:** {pos['entry_reason']}",
                f"- **Entry time:** {pos['entry_time']}",
                f"- **Stop-loss:** ${pos['stop_loss']:,.2f} (-{DEFAULT_SL_PCT*100:.0f}%)",
                f"- **Take-profit:** ${pos['take_profit']:,.2f} (+{DEFAULT_TP_PCT*100:.0f}%)",
                f"- **Max allowed loss:** ${pos['max_allowed_loss']:,.2f}",
                f"- **Unrealized P/L:** ${unrealized:+.2f} ({unrealized_pct:+.2f}%)",
                f"- **Exit rule:** {pos['exit_rule']}",
                "",
            ])
    else:
        lines.append("No open positions tracked.\n")
    
    lines.extend([
        "## CLOSED POSITIONS",
        "",
    ])
    
    if closed_positions:
        lines.append("| Symbol | Entry | Exit | PnL | Reason |")
        lines.append("|--------|-------|------|-----|--------|")
        for symbol in closed_positions:
            pos = positions[symbol]
            lines.append(
                f"| {symbol} | ${pos['entry_price']:,.2f} | ${pos['exit_price']:,.2f} | "
                f"${pos['realized_pnl']:+.2f} ({pos['realized_pnl_pct']:+.2f}%) | {pos['exit_reason']} |"
            )
    else:
        lines.append("No closed positions.\n")
    
    lines.extend([
        "---",
        "*Position Tracker — SL/TP monitoring active*",
        "",
    ])
    
    return "\n".join(lines)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    print(generate_position_report())
