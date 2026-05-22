"""
Smart EA Bot Company — Divergence Alert System
Compares paper trading performance to backtest expectations.
Flags YELLOW/RED when paper diverges from backtest.
"""

import json
import os
import statistics
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

LOG_DIR = "data/paper_logs"


class DivergenceAlert:
    """
    Tracks paper-vs-backtest divergence.
    
    Alert Levels:
    - GREEN: Paper PF >= 60% of backtest PF
    - YELLOW: Paper PF < 60% of backtest PF (30-day rolling)
    - RED: Paper PF < 1.0 (60-day rolling)
    """
    
    def __init__(self, backtest_pf_btc: float = 2.14, backtest_pf_eth: float = 4.85):
        self.backtest_pf = {"BTCUSD": backtest_pf_btc, "ETHUSD": backtest_pf_eth}
        self.yellow_threshold = 0.60  # 60% of backtest
        self.red_threshold = 1.0  # PF < 1.0
        self.rolling_window_30 = 30
        self.rolling_window_60 = 60
    
    def load_trades(self, days: int = 60) -> List[Dict]:
        """Load recent paper trades."""
        trades = []
        
        # Load from current and previous month files
        for month_offset in range(2):
            month = datetime.now(timezone.utc) - timedelta(days=month_offset * 30)
            log_file = os.path.join(LOG_DIR, f"trades_{month.strftime('%Y%m')}.jsonl")
            
            if not os.path.exists(log_file):
                continue
            
            with open(log_file) as f:
                for line in f:
                    trade = json.loads(line.strip())
                    trade_date = datetime.fromisoformat(trade["timestamp"]).date()
                    if (datetime.now(timezone.utc).date() - trade_date).days <= days:
                        trades.append(trade)
        
        return trades
    
    def calculate_paper_pf(self, trades: List[Dict]) -> Optional[float]:
        """Calculate profit factor from paper trades."""
        gross_profit = sum(t["pnl"] for t in trades if t.get("pnl", 0) > 0)
        gross_loss = abs(sum(t["pnl"] for t in trades if t.get("pnl", 0) < 0))
        
        if gross_loss == 0:
            return float('inf') if gross_profit > 0 else 0
        
        return gross_profit / gross_loss
    
    def check_divergence(self) -> Dict:
        """
        Check divergence and return alert status.
        
        Returns:
            {
                "status": "GREEN" | "YELLOW" | "RED",
                "reason": str,
                "paper_pf_30d": float,
                "paper_pf_60d": float,
                "backtest_pf": float,
                "ratio_30d": float,
                "trades_30d": int,
                "trades_60d": int,
            }
        """
        trades_30d = self.load_trades(days=30)
        trades_60d = self.load_trades(days=60)
        
        paper_pf_30d = self.calculate_paper_pf(trades_30d)
        paper_pf_60d = self.calculate_paper_pf(trades_60d)
        
        # Use average backtest PF
        avg_backtest_pf = sum(self.backtest_pf.values()) / len(self.backtest_pf)
        
        ratio_30d = paper_pf_30d / avg_backtest_pf if avg_backtest_pf > 0 else 0
        
        # Determine status
        if paper_pf_60d < self.red_threshold and len(trades_60d) >= 3:
            status = "RED"
            reason = f"Paper PF {paper_pf_60d:.2f} < 1.0 over 60 days ({len(trades_60d)} trades)"
        elif ratio_30d < self.yellow_threshold and len(trades_30d) >= 2:
            status = "YELLOW"
            reason = f"Paper PF {paper_pf_30d:.2f} is {ratio_30d*100:.0f}% of backtest ({len(trades_30d)} trades)"
        else:
            status = "GREEN"
            reason = "Paper performance within expected bounds"
        
        result = {
            "status": status,
            "reason": reason,
            "paper_pf_30d": round(paper_pf_30d, 2) if paper_pf_30d != float('inf') else "inf",
            "paper_pf_60d": round(paper_pf_60d, 2) if paper_pf_60d != float('inf') else "inf",
            "backtest_pf": round(avg_backtest_pf, 2),
            "ratio_30d": round(ratio_30d, 2),
            "trades_30d": len(trades_30d),
            "trades_60d": len(trades_60d),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        
        # Log result
        log_file = os.path.join(LOG_DIR, "divergence_alerts.jsonl")
        os.makedirs(LOG_DIR, exist_ok=True)
        with open(log_file, "a") as f:
            f.write(json.dumps(result) + "\n")
        
        if status == "RED":
            logger.error(f"🚨 DIVERGENCE ALERT — {status}: {reason}")
        elif status == "YELLOW":
            logger.warning(f"⚠️ DIVERGENCE ALERT — {status}: {reason}")
        else:
            logger.info(f"✅ Divergence check — {status}: {reason}")
        
        return result


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    alert = DivergenceAlert()
    result = alert.check_divergence()
    print(json.dumps(result, indent=2))
